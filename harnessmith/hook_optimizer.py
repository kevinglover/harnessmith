"""Reviewed optimization for repeated Spec Kit extension-hook contracts."""

from __future__ import annotations

import hashlib
import re
from typing import Dict, List, Sequence, Set, Tuple

from .errors import SkillCompilerError
from .model import Section, SkillIR


FALLBACK_PATH = "references/extension-hooks-fallback.md"
SCRIPT_PATH = "scripts/resolve-extension-hooks.py"


def optimize_extension_hooks(
    ir: SkillIR,
    body: str,
    references: Dict[str, str],
    target: str,
) -> Tuple[
    str,
    Dict[str, str],
    Dict[str, str],
    List[Dict[str, object]],
    Set[str],
]:
    """Replace the reviewed Spec Kit hook contracts with a resolver + fallback."""

    before = _unique_hook_section(ir.sections, "before")
    after = _unique_hook_section(ir.sections, "after")
    before_event = _event_name(before, "before")
    after_event = _event_name(after, "after")
    if before_event.removeprefix("before_") != after_event.removeprefix("after_"):
        raise SkillCompilerError(
            "extension-hook events do not describe the same workflow: %s, %s"
            % (before_event, after_event)
        )

    documents = {"SKILL.md": body, **references}
    transforms: List[Dict[str, object]] = []
    for phase, section, event in (
        ("before", before, before_event),
        ("after", after, after_event),
    ):
        output, source_text = _containing_document(documents, section)
        replacement = _hook_directive(section, event, phase)
        documents[output] = documents[output].replace(source_text, replacement, 1)
        transforms.append(
            {
                "type": "resolve-extension-hooks",
                "phase": phase,
                "event": event,
                "source_heading": section.heading,
                "source_lines": [section.start_line, section.end_line],
                "source_sha256": _sha256(section.text),
                "replacement_sha256": _sha256(replacement),
                "output": output,
                "fallback": FALLBACK_PATH,
                "script": SCRIPT_PATH,
            }
        )

    fallback = _fallback_reference(ir, (before, after))
    if FALLBACK_PATH in documents:
        raise SkillCompilerError("hook fallback path collides with generated output")
    documents[FALLBACK_PATH] = fallback

    optimized_body = documents.pop("SKILL.md")
    optimized_references = {
        path: _ensure_final_newline(content) for path, content in documents.items()
    }
    scripts = {SCRIPT_PATH: _resolver_script(target)}
    return optimized_body, optimized_references, scripts, transforms, {FALLBACK_PATH}


def expected_extracted_section(ir: SkillIR, section: Section) -> str:
    """Return an extracted section after reviewed nested hook replacements."""

    expected = section.text
    nested = [
        candidate
        for candidate in ir.sections
        if section.start_offset <= candidate.start_offset < section.end_offset
        and candidate is not section
        and "extension hooks" in candidate.heading.lower()
    ]
    for candidate in sorted(nested, key=lambda item: item.start_offset, reverse=True):
        phase = "before" if "before_" in candidate.text else "after"
        event = _event_name(candidate, phase)
        replacement = _hook_directive(candidate, event, phase)
        expected = expected.replace(candidate.text, replacement, 1)
    return expected


def _unique_hook_section(sections: Sequence[Section], phase: str) -> Section:
    marker = re.compile(r"hooks\.%s_[a-z0-9_-]+" % phase)
    candidates = [
        section
        for section in sections
        if marker.search(section.text)
        and (
            (phase == "before" and section.heading == "Pre-Execution Checks")
            or (phase == "after" and "extension hooks" in section.heading.lower())
        )
    ]
    if len(candidates) != 1:
        raise SkillCompilerError(
            "expected exactly one reviewed %s extension-hook section; found %d"
            % (phase, len(candidates))
        )
    return candidates[0]


def _event_name(section: Section, phase: str) -> str:
    matches = sorted(set(re.findall(r"hooks\.(%s_[a-z0-9_-]+)" % phase, section.text)))
    if len(matches) != 1:
        raise SkillCompilerError(
            "expected one %s hook event in '%s'; found %s"
            % (phase, section.heading, matches)
        )
    return matches[0]


def _containing_document(
    documents: Dict[str, str], section: Section
) -> Tuple[str, str]:
    matches: List[Tuple[str, str]] = []
    normalized = _ensure_final_newline(section.text)
    for path, content in documents.items():
        for candidate in (section.text, normalized):
            count = content.count(candidate)
            if count:
                matches.extend([(path, candidate)] * count)
                break
    if len(matches) != 1:
        raise SkillCompilerError(
            "hook section '%s' occurs %d times after extraction"
            % (section.heading, len(matches))
        )
    return matches[0]


def _hook_directive(section: Section, event: str, phase: str) -> str:
    heading = section.text.splitlines(keepends=True)[0].rstrip("\r\n")
    anchor = "pre-execution-checks" if phase == "before" else _slug(section.heading)
    if phase == "after":
        return (
            "%s\n\n"
            "After reporting, run the same packaged hook resolver for event `%s`. "
            "Apply the status rules in Pre-Execution Checks; wait for every "
            "mandatory hook before finishing. On `unavailable`, read [the original "
            "after hook contract](%s#%s) completely and follow it.\n\n"
            % (heading, event, FALLBACK_PATH, anchor)
        )
    return (
        "%s\n\n"
        "From the project root, run the packaged [hook resolver](%s) as `python3 "
        "<resolved-script-path> %s --project-root .`; resolve the path relative to "
        "this `SKILL.md`. The resolver is read-only. Use these rules for both calls:\n\n"
        "- `missing` or `none`: continue silently.\n"
        "- `ok`: emit decoded `message` exactly; execute each mandatory `invocation` "
        "and wait before continuing; never execute `skipped_conditions`.\n"
        "- `invalid`: report `error`, state that no hooks—including mandatory "
        "hooks—were checked, then continue.\n"
        "- `unavailable`: read [the original before hook contract](%s#%s) "
        "completely and follow it.\n\n"
        % (heading, SCRIPT_PATH, event, FALLBACK_PATH, anchor)
    )


def _fallback_reference(ir: SkillIR, sections: Sequence[Section]) -> str:
    hashes = ", ".join("%s:%s" % (section.heading, _sha256(section.text)) for section in sections)
    note = (
        "<!-- Generated fallback from `%s` (%s). Read only when the resolver "
        "reports `unavailable`. -->\n\n" % (ir.source_id, hashes)
    )
    intro = (
        "# Extension hook fallback contract\n\n"
        "Use only the section for the current phase. These are the exact canonical "
        "instructions replaced by the deterministic resolver on its normal path.\n\n"
    )
    section_text = "\n".join(
        _ensure_final_newline(section.text) for section in sections
    )
    return _ensure_final_newline(note + intro + section_text)


def _resolver_script(target: str) -> str:
    template = r'''#!/usr/bin/env python3
"""Resolve one Spec Kit hook event without modifying project files."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


TARGET = "__TARGET__"
EVENT_RE = re.compile(r"^(before|after)_[a-z0-9_-]+$")
KEY_RE = re.compile(r"^([A-Za-z0-9_-]+):\s*(.*)$")


class InvalidConfig(ValueError):
    pass


class UnsupportedYaml(ValueError):
    pass


def _strip_comment(value: str) -> str:
    single = False
    double = False
    index = 0
    while index < len(value):
        char = value[index]
        if char == "'" and not double:
            if single and index + 1 < len(value) and value[index + 1] == "'":
                index += 2
                continue
            single = not single
        elif char == '"' and not single and (index == 0 or value[index - 1] != "\\"):
            double = not double
        elif char == "#" and not single and not double:
            if index == 0 or value[index - 1].isspace():
                return value[:index].rstrip()
        index += 1
    if single or double:
        raise InvalidConfig("unterminated quoted scalar")
    return value.rstrip()


def _scalar(raw: str):
    value = _strip_comment(raw).strip()
    if not value:
        raise UnsupportedYaml("nested or block values require a full YAML parser")
    if value.startswith('"'):
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            raise InvalidConfig(str(exc)) from exc
    if value.startswith("'"):
        if not value.endswith("'") or len(value) < 2:
            raise InvalidConfig("unterminated single-quoted scalar")
        return value[1:-1].replace("''", "'")
    if value[0] in "[{&*!|>":
        raise UnsupportedYaml("flow, tagged, anchored, or block YAML requires PyYAML")
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "~"}:
        return None
    if re.fullmatch(r"-?[0-9]+", value):
        return int(value)
    return value


def _field(text: str):
    match = KEY_RE.match(text)
    if not match:
        raise InvalidConfig("expected a key/value hook field: %s" % text)
    return match.group(1), _scalar(match.group(2))


def _significant(text: str):
    result = []
    for number, raw in enumerate(text.splitlines(), 1):
        if raw.startswith("\t") or "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise InvalidConfig("tabs are not valid indentation (line %d)" % number)
        content = raw.lstrip(" ")
        if not content or content.startswith("#"):
            continue
        result.append((number, len(raw) - len(content), _strip_comment(content)))
    return result


def _manual_event(text: str, event: str):
    lines = _significant(text)
    if text.lstrip().startswith("{"):
        raise UnsupportedYaml("flow-style root mappings require PyYAML")
    hooks_rows = [row for row in lines if row[1] == 0 and row[2] == "hooks:"]
    if not hooks_rows:
        quoted_hooks = re.compile(r"^[\"']hooks[\"']\s*:")
        if any(row[1] == 0 and quoted_hooks.match(row[2]) for row in lines):
            raise UnsupportedYaml("quoted mapping keys require PyYAML")
        return []
    if len(hooks_rows) != 1:
        raise InvalidConfig("duplicate top-level hooks mapping")
    hooks_number = hooks_rows[0][0]
    start = next(index for index, row in enumerate(lines) if row[0] == hooks_number)
    hooks_indent = lines[start][1]
    event_index = None
    event_indent = None
    event_tail = ""
    for index in range(start + 1, len(lines)):
        _, indent, content = lines[index]
        if indent <= hooks_indent:
            break
        match = KEY_RE.match(content)
        if match and match.group(1) == event:
            event_index = index
            event_indent = indent
            event_tail = match.group(2).strip()
            break
    if event_index is None or event_indent is None:
        quoted_event = re.compile(r"^[\"']%s[\"']\s*:" % re.escape(event))
        if any(row[1] > hooks_indent and quoted_event.match(row[2]) for row in lines[start + 1 :]):
            raise UnsupportedYaml("quoted mapping keys require PyYAML")
        return []
    if event_tail in {"[]", "null", "~"}:
        return []
    if event_tail:
        raise UnsupportedYaml("inline hook collections require PyYAML")

    entries = []
    current = None
    item_indent = None
    for _, indent, content in lines[event_index + 1 :]:
        if indent <= hooks_indent:
            break
        mapping = KEY_RE.match(content)
        if indent == event_indent and mapping and not content.startswith("-"):
            break
        if content == "-" or content.startswith("- "):
            if indent < event_indent:
                break
            if item_indent is None:
                item_indent = indent
            elif indent != item_indent:
                raise InvalidConfig("inconsistent hook list indentation")
            if current is not None:
                entries.append(current)
            current = {}
            remainder = content[1:].strip()
            if remainder:
                if remainder[0] in "[{":
                    raise UnsupportedYaml("flow-style hook mappings require PyYAML")
                key, value = _field(remainder)
                current[key] = value
            continue
        if current is None or item_indent is None:
            raise UnsupportedYaml("hook event is not a block list")
        if indent <= item_indent:
            break
        key, value = _field(content)
        if key in current:
            raise InvalidConfig("duplicate hook field: %s" % key)
        current[key] = value
    if current is not None:
        entries.append(current)
    return entries


def _load_event(text: str, event: str):
    try:
        import yaml  # type: ignore
    except ImportError:
        return _manual_event(text, event)
    try:
        data = yaml.safe_load(text)
    except Exception as exc:
        raise InvalidConfig(str(exc)) from exc
    if data is None:
        return []
    if not isinstance(data, dict):
        raise InvalidConfig("configuration root must be a mapping")
    hooks = data.get("hooks", {})
    if hooks is None:
        return []
    if not isinstance(hooks, dict):
        raise InvalidConfig("hooks must be a mapping")
    entries = hooks.get(event, [])
    if entries is None:
        return []
    if not isinstance(entries, list) or not all(isinstance(item, dict) for item in entries):
        raise InvalidConfig("hooks.%s must be a list of mappings" % event)
    return entries


def _text_field(hook, key: str, required: bool = False) -> str:
    value = hook.get(key, "")
    if value is None and not required:
        return ""
    if not isinstance(value, str) or (required and not value.strip()):
        raise InvalidConfig("hook field '%s' must be a non-empty string" % key)
    return value.strip()


def _invocation(command: str) -> str:
    skill_name = command.replace(".", "-")
    return ("$" if TARGET == "codex" else "/") + skill_name


def _message(event: str, hooks) -> str:
    before = event.startswith("before_")
    lines = []
    for hook in hooks:
        lines.extend(["## Extension Hooks", ""])
        if hook["optional"]:
            label = "Optional Pre-Hook" if before else "Optional Hook"
            lines.append("**%s**: %s" % (label, hook["extension"]))
            lines.append("Command: `%s`" % hook["invocation"])
            lines.append("Description: %s" % hook["description"])
            lines.extend(
                ["", "Prompt: %s" % hook["prompt"], "To execute: `%s`" % hook["invocation"], ""]
            )
        else:
            label = "Automatic Pre-Hook" if before else "Automatic Hook"
            lines.append("**%s**: %s" % (label, hook["extension"]))
            lines.append("Executing: `%s`" % hook["invocation"])
            lines.extend(["EXECUTE_COMMAND: %s" % hook["command"], ""])
    return "\n".join(lines).rstrip()


def _emit(status: str, **values) -> None:
    payload = {"status": status, **values}
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("event")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    if not EVENT_RE.fullmatch(args.event):
        _emit("invalid", error="invalid hook event: %s" % args.event)
        return 0

    config = args.project_root / ".specify" / "extensions.yml"
    if not config.is_file():
        _emit("missing", event=args.event)
        return 0
    try:
        text = config.read_text(encoding="utf-8")
        entries = _load_event(text, args.event)
    except UnsupportedYaml as exc:
        _emit("unavailable", event=args.event, error=str(exc))
        return 0
    except (InvalidConfig, OSError, UnicodeError) as exc:
        _emit("invalid", event=args.event, error=str(exc))
        return 0

    resolved = []
    skipped_conditions = 0
    try:
        for hook in entries:
            if hook.get("enabled") is False:
                continue
            condition = hook.get("condition")
            if condition is not None and str(condition).strip():
                skipped_conditions += 1
                continue
            optional = hook.get("optional", True)
            if not isinstance(optional, bool):
                raise InvalidConfig("hook field 'optional' must be a boolean")
            command = _text_field(hook, "command", required=True)
            resolved.append(
                {
                    "extension": _text_field(hook, "extension", required=True),
                    "command": command,
                    "invocation": _invocation(command),
                    "optional": optional,
                    "description": _text_field(hook, "description"),
                    "prompt": _text_field(hook, "prompt"),
                }
            )
    except InvalidConfig as exc:
        _emit("invalid", event=args.event, error=str(exc))
        return 0

    if not resolved:
        _emit("none", event=args.event, skipped_conditions=skipped_conditions)
        return 0
    _emit(
        "ok",
        event=args.event,
        hooks=resolved,
        message=_message(args.event, resolved),
        skipped_conditions=skipped_conditions,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''
    return template.replace("__TARGET__", target)


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _ensure_final_newline(text: str) -> str:
    return text.rstrip("\n") + "\n"
