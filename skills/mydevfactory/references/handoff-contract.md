# Agent delegation, review, and handoff contracts

Every request goes to a **fresh agent** and is self-contained: it names the role, the PRD and slice file paths, the files the agent may change, and what to return. Exact prompt skeletons and the transition rules are in `kanban-protocol.md`. In Fix and Audit modes (no `prd/`), use the same contracts with a task card instead of a slice file.

## Analyst request

Give it the request, the developer's answers so far, domain docs, and relevant code paths, not a pre-written solution. It follows `analyst-playbook.md`.

- **Writes:** the PRD file, the slice files, `CONTEXT.md` and ADRs. Never production code or tests.
- **Returns:** the files written, and open questions, each with a recommended answer. It never asks the developer directly.
- **Data check** (data/report/metric slices): metric definitions vs. the requirement, expected vs. actual results on known sample data, aggregation/rounding/time-zone/null findings, row counts before and after migrations, with the exact queries and their output, written into the slice file's QA notes. Never writes to shared or production data.

## Implementation specialist request

One part of one slice:

- **Role and slice:** `backend` or `frontend`, and the slice file path.
- **Contract:** from the slice file. Build against it and never change it silently; raise a question instead.
- **Owned files:** only the part's Owned files and their tests.
- **Proof required:** the part's test commands and the slice's acceptance criteria, including the negative case.
- **Notes to act on:** Review notes, QA notes and Change requests addressed to this part.
- **Updates:** its own `Part status` (`Developing` → `Developed` only after its tests passed), its part's `Evidence:` block (`command | exit code | key output`), and one History line. Needs a file outside Owned files → return a question, don't edit it.
- **Returns:** changed files, assumptions, commands + output + exit code, known untested scenarios, questions.

Do not commit, push, merge, deploy, or overwrite unrelated changes.

## Independent reviewer request

Give the reviewer the diff range, the **original changed files**, the slice file (Contract, acceptance criteria) and the PRD, not a developer's summary.

- **Writes its own verdict into the slice file**: PASS or FAIL per part, then findings in severity order (`severity | file:line | failure scenario | evidence | what must be done`), each marked `blocking` or `follow-up` (only blocking findings fail a part; from round 2, review only the previous findings and the fix range, see `kanban-protocol.md`, "Review rounds"), implicit assumptions and scope changes, and what the passing tests do and do **not** establish. Also one History line.
- **Never** edits source code, tests, or any file other than the slice file.

## Independent security review request

Give securitycode the candidate diff, original files, contract, and relevant check output. Ask it to inspect security-sensitive paths and trust boundaries, then return its own PASS, FAIL or NOT RUN with inspected scope, locations, impact, remediation and limits. It edits no files. The orchestrator records the returned text in Security review notes and sends findings to the owning developer.

## QA request

Give QA the slice file, the changed files, and the exact build/test/run commands.

- **Runs** the existing build and test suites, then exercises the running feature against each acceptance criterion: happy path, edge cases, failure paths, and loading/empty/error states for UI.
- **Writes its own verdict into the slice file**: PASS or FAIL, the table `criterion | how checked | PASS / FAIL / NOT RUN | evidence`, defects with reproduction steps, criteria with no automated test, and one History line.
- **Never** writes code: no tests and no fixes. Defects and missing tests go back to the owning developer, and enabled review, securitycode and QA agents check the updated candidate.

## Enforcing write scope

Before every agent run, the orchestrator records HEAD and `git status --porcelain`; afterwards it checks `git diff --name-only <base sha>` plus new untracked files against what that role may write, and never touches paths that were already dirty before the run. Out-of-scope changes are reverted, logged in History as a violation, and the step gets one corrective re-run with a fresh agent; a second violation blocks the slice and asks the developer. If a mapped reviewer or QA agent can't write files at all, the orchestrator writes its returned verdict verbatim, labelled `Verdict by <agent>, recorded by orchestrator`.

If a named role cannot be dispatched, record the blocker. Only roles disabled in the project JSON may be recorded as SKIPPED.

## Integration owner

The orchestrator merges `Completed` slices and verifies shared API contracts, overlapping edits, build/test impact and user journeys on the combined code. Parallel writing is safe only in separate worktrees, or with clearly non-overlapping Owned files. Every finding returns to the owning developer for fixes.

## Final status

- `SIGNED OFF (ACCEPT)`: all slices or the Fix task passed the workflow and integration checks and were accepted by the developer after the Walkthrough. Still **not** deployment approval.
- `REJECTED`: the developer rejected the sign-off; the reason is recorded in the PRD.
- `BLOCKED`: an unresolved question, or a slice that hit the retry cap.
- `NOT VERIFIED`: code exists but the required evidence is missing.
- In Audit mode, `READY FOR HUMAN REVIEW` means an evidenced candidate for the developer's review.
