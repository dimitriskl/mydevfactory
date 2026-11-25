#!/usr/bin/env python3
"""Check recorded MyDevFactory role evidence for a candidate revision."""

import argparse
import json
from pathlib import Path
import re
import sys


ROLES = ("analyst", "backend", "frontend", "reviewer", "securitycode", "qa")
ROUTES = {
    "full": ROLES,
    "copy-backend": ("backend",),
    "copy-frontend": ("frontend",),
    "fix-backend": ("backend", "reviewer"),
    "fix-frontend": ("frontend", "reviewer"),
}
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
    unknown = agents.keys() - set(ROLES)
    if unknown:
        raise ValueError(f"unknown configured role(s): {', '.join(sorted(unknown))}")

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


def evidence_rows(lines):
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


def check_evidence(names, rows, revision, route):
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
        if role not in ROUTES[route]:
            raise ValueError(f"{role} is outside route {route}")
        if result != "PASS" and not (route == "full" and role in ("backend", "frontend") and result == "NOT APPLICABLE"):
            raise ValueError(f"{role} requires a passing result, found {result or '(empty)'}")
        if reviewed_revision != revision:
            raise ValueError(f"{role} evidence is for a different revision")
        if evidence in ("", "-", "—"):
            raise ValueError(f"{role} requires evidence")
        completed.append(role)

    required = [role for role in ROUTES[route] if role in names]
    missing = set(required) - seen
    if missing:
        raise ValueError(f"missing configured role evidence: {', '.join(sorted(missing))}")
    if completed != required:
        raise ValueError(f"configured roles must run in order: {' → '.join(required)}")


def check_route_record(lines, route):
    # Older cards had no route header and always used the full workflow.
    recorded = [line for line in lines if line.startswith("Route:")]
    if route == "full" and not recorded:
        return
    prefix = f"Route: {route} | "
    if (len(recorded) != 1 or not recorded[0].startswith(prefix)
            or recorded[0][len(prefix):].strip() in ("", "<reason>")):
        raise ValueError(f"expected one 'Route: {route} | <reason>' matching the trusted route")
    if route != "full":
        expected_risk = "L0" if route.startswith("copy-") else "L1"
        if [line for line in lines if line.startswith("Risk:")] != [f"Risk: {expected_risk}"]:
            raise ValueError(f"{route} requires Risk: {expected_risk}")
        checks = [line for line in lines if line.startswith("Route check:")]
        fields = checks[0][len("Route check:"):].strip().rsplit(" | ", 2) if len(checks) == 1 else []
        if (len(fields) != 3 or fields[1] != "exit 0"
                or fields[0].strip() in ("", "<command>")
                or fields[2].strip() in ("", "<observed result>")):
            raise ValueError("short route requires 'Route check: <command> | exit 0 | <observed result>'")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--route", choices=ROUTES, default="full")
    parser.add_argument("--plan", action="store_true", help="validate configuration and list dispatches before work starts")
    parser.add_argument("--card", type=Path)
    parser.add_argument("--revision")
    args = parser.parse_args()

    try:
        names = configured_roles(args.config)
        required = [role for role in ROUTES[args.route] if role in names]
        if args.route != "full" and len(required) != len(ROUTES[args.route]):
            raise ValueError(f"{args.route} requires configured {' and '.join(ROUTES[args.route])}")
        if args.plan:
            if args.card is not None or args.revision is not None:
                parser.error("--plan cannot verify a card or revision")
            print(f"{args.route}: {', '.join(required) or '(no configured roles)'}")
            return 0
        if args.card is None or args.revision is None:
            parser.error("verification requires --card and --revision")
        if not args.revision.strip():
            raise ValueError("revision must not be blank")
        lines = args.card.read_text(encoding="utf-8-sig").splitlines()
        check_route_record(lines, args.route)
        check_evidence(names, evidence_rows(lines), args.revision, args.route)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"OK: workflow evidence covers {len(required)} configured role(s) for {args.revision} ({args.route})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
