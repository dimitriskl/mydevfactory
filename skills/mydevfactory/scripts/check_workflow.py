#!/usr/bin/env python3
"""Check recorded MyDevFactory role evidence for a candidate revision."""

import argparse
import json
from pathlib import Path
import re
import sys


ROLES = ("analyst", "backend", "frontend", "reviewer", "securitycode", "qa")
HEADER = ["Role", "Agent", "Result", "Revision", "Evidence"]
SECTION = "## Workflow evidence"


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def configured_roles(path):
    config = json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_keys)
    agents = config.get("agents") if isinstance(config, dict) else None
    if not isinstance(agents, dict):
        raise ValueError("config must contain an agents object")

    names = {}
    for role in ROLES:
        mapping = agents.get(role)
        if mapping is None or (isinstance(mapping, str) and not mapping.strip()):
            continue
        if not isinstance(mapping, dict):
            raise ValueError(f"agents.{role} must be an object or null")
        name = mapping.get("name")
        if name is None:
            continue
        if not isinstance(name, str):
            raise ValueError(f"agents.{role}.name must be a string or null")
        if name.strip():
            names[role] = name.strip()
    return names


def cells(line):
    line = line.strip()
    if not line.startswith("|") or not line.endswith("|"):
        raise ValueError("expected a Markdown table row in Workflow evidence")
    fields = [field.strip() for field in re.split(r"(?<!\\)\|", line[1:-1])]
    if len(fields) != len(HEADER):
        raise ValueError("expected five columns in a Workflow evidence row")
    return fields


def evidence_rows(path):
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    headings = [index for index, line in enumerate(lines) if line.rstrip() == SECTION]
    if len(headings) != 1:
        raise ValueError(f"expected exactly one {SECTION} section")

    section = []
    for line in lines[headings[0] + 1:]:
        if re.match(r"^#{1,2}\s", line):
            break
        if line.strip():
            section.append(line)
    if len(section) < 2 or cells(section[0]) != HEADER:
        raise ValueError(f"expected the Workflow evidence columns: {', '.join(HEADER)}")
    if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells(section[1])):
        raise ValueError("invalid Workflow evidence table divider")
    return [cells(line) for line in section[2:]]


def check_evidence(names, rows, revision):
    seen = set()
    completed = []
    for role, agent, result, reviewed_revision, evidence in rows:
        if role not in ROLES:
            raise ValueError(f"unknown workflow role: {role}")
        if role in seen:
            raise ValueError(f"duplicate workflow evidence for {role}")
        seen.add(role)
        expected_agent = names.get(role)
        if expected_agent is None:
            if result != "SKIPPED":
                raise ValueError(f"{role} is disabled and can only be recorded as SKIPPED")
            continue
        if agent != expected_agent:
            raise ValueError(f"{role} must record configured agent {expected_agent}")
        if result != "PASS" and not (role in ("backend", "frontend") and result == "NOT APPLICABLE"):
            raise ValueError(f"{role} requires a passing result, found {result or '(empty)'}")
        if reviewed_revision != revision:
            raise ValueError(f"{role} evidence is for a different revision")
        if evidence in ("", "-", "—"):
            raise ValueError(f"{role} requires evidence")
        completed.append(role)

    missing = names.keys() - seen
    if missing:
        raise ValueError(f"missing configured role evidence: {', '.join(sorted(missing))}")
    if completed != list(names):
        raise ValueError(f"configured roles must run in order: {' → '.join(names)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--card", required=True, type=Path)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()

    try:
        if not args.revision.strip():
            raise ValueError("revision must not be blank")
        names = configured_roles(args.config)
        check_evidence(names, evidence_rows(args.card), args.revision)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"OK: workflow evidence covers {len(names)} configured role(s) for {args.revision}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
