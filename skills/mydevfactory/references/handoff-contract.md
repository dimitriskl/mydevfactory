# Agent delegation, review, and handoff contracts

Every request goes to a **fresh agent** and is self-contained: name the role, phase, slice or task card path, relevant PRD path, allowed files, required output and exact scope. Pass file pointers and targeted instructions, not copied PRDs or repeated logs. Agents read the relevant slice contract and phase-specific notes; expand to the PRD, source or prior evidence when needed for their task. Exact prompt skeletons and the transition rules are in `kanban-protocol.md`. In Fix mode, use the task card instead of a slice file. Dispatch the enabled analyst, reviewer and QA with explicit read-only assignments: the analyst returns intent, acceptance criteria, checks and questions; reviewer and QA return their complete verdicts and evidence. The orchestrator records each response verbatim on the card, identifying its author. Never ask these roles to create `prd/` or write the Fix card unless their definitions explicitly permit it. In Audit mode use the applicable read-only contracts.

## Analyst request

Give it the request, the developer's answers so far, domain docs, and relevant code paths, not a pre-written solution. It follows `analyst-playbook.md`.

- **Writes:** the PRD file, the slice files, `CONTEXT.md` and ADRs. Never production code or tests.
- **Returns:** the files written, and open questions, each with a recommended answer. It never asks the developer directly.
- **Data check** (data/report/metric slices): metric definitions vs. the requirement, expected vs. actual results on known sample data, aggregation/rounding/time-zone/null findings, row counts before and after migrations, with the exact queries and their output, written into the slice file's QA notes. Never writes to shared or production data.

## Implementation specialist request

Assign one backend or frontend part, its slice file, owned files, tests and addressed review, QA and change notes. Implement against its Contract without silently changing it. Set `Developing`, then `Developed` only after tests pass; record `command | exit code | key output` and one History line. Ask before editing outside Owned files. Return changed files, assumptions, evidence references, untested scenarios and questions. Do not commit, push, merge, deploy or overwrite unrelated changes.

## Independent reviewer request

Provide the diff range, original changed files, slice Contract and criteria, and a PRD pointer, not a developer summary. The reviewer writes its own per-part verdict, severity-ordered findings (`severity | file:line | failure scenario | evidence | what must be done`), assumptions, scope changes, limits of passing tests and one History line. Mark findings `blocking` or `follow-up`; only blocking findings fail a part. Later rounds use the fix range and previous findings (`kanban-protocol.md`, "Review rounds"). Do not edit source, tests or other files.

## Independent security review request

Give securitycode the candidate diff, original files, contract, and relevant check output. Ask it to inspect security-sensitive paths and trust boundaries, then return its own PASS, FAIL or NOT RUN with inspected scope, locations, impact, remediation and limits. It edits no files. The orchestrator records the returned text in Security review notes and sends findings to the owning developer.

## QA request

Provide the slice file, changed files and exact build/test/run commands. QA runs checks and exercises every criterion, including happy, edge and failure paths and UI loading/empty/error states. It records its own verdict, `criterion | how checked | PASS / FAIL / NOT RUN | evidence`, reproduction steps, criteria without automated tests and one History line. QA writes no code; return defects and missing tests to the developer and rerun enabled review, securitycode and QA on the updated candidate.

## Enforcing write scope

Before each run, record HEAD and `git status --porcelain`. Afterwards compare `git diff --name-only <base sha>` and new untracked files with the role's allowed scope. Never touch previously dirty paths. Revert out-of-scope changes, log the violation and allow one corrective fresh run; a second violation blocks the slice and requires the developer. If reviewer or QA cannot write its verdict, record it verbatim as `Verdict by <agent>, recorded by orchestrator`. An unavailable named role blocks; only configuration-disabled roles are SKIPPED.

## Integration owner

The orchestrator merges `Completed` slices and verifies shared API contracts, overlapping edits, build/test impact and user journeys on the combined code. Parallel writing is safe only in separate worktrees, or with clearly non-overlapping Owned files. Every finding returns to the owning developer for fixes.

## Final status

- `SIGNED OFF (ACCEPT)`: all slices or the Fix task passed the workflow and integration checks and were accepted by the developer after the Walkthrough. Still **not** deployment approval.
- `REJECTED`: the developer rejected the sign-off; the reason is recorded in the PRD.
- `BLOCKED`: an unresolved question, or a slice that hit the retry cap.
- `NOT VERIFIED`: code exists but the required evidence is missing.
- In Audit mode, `READY FOR HUMAN REVIEW` means an evidenced candidate for the developer's review.

## UI evidence

**UI evidence.** For a meaningful user-facing UI change, QA exercises the key flow using available browser or computer-use tools in a safe test environment. Capture a concise before/after screenshot or short recording when useful; label the flow, environment and result, and link artifacts in the QA evidence. Redact sensitive data. If the prior state, tools or environment are unavailable, record that fact and mark the affected check NOT RUN; never imply a screenshot proves untested behavior. For non-visual or trivial changes, record why visual evidence is unnecessary.


## Handoff report

For a PR or Ship handoff, produce a concise **merge-risk card**, grounded in the actual diff and evidence. For each dimension report low / medium / high / unknown, a reason and evidence: verification; alignment with the request; impact and sensitive paths; rollback difficulty and procedure; and production error detection. Use unknown when evidence is missing. Highlight the most consequential rating and unknowns; do not average away a high risk or present the card as approval. State the top areas for the human to review, practical mitigations, unverified checks, and any decision needed. Keep the slice's L0–L2 classification: it determines workflow depth and is distinct from this PR-level assessment. Where a PR template exists, include or link the card without publishing it unless requested.

**Review learning (optional).** With the developer's agreement and project policy, record missed defects, false positives, regressions and reverts as sanitized examples with expected findings and evidence. Periodically compare reviewer performance on these cases and, where available, review time and rounds. Record unavailable metrics as unknown; do not infer reviewer accuracy from an LLM score alone. Use the results to propose changes for human review; do not silently alter review rules.


Use the short form (5 lines in Deadline) or this normal form:

1. `Delivered`: the PRD and slices, with file/commit references.
2. `Agents actually used`: analyst, specialists, reviewer, securitycode and QA by name, with each outcome or configuration-based skip.
3. `Evidence`: exact commands, exit codes, meaningful output, the QA per-criterion results, criteria with no automated test, and **what each check proves**.
4. `Open risks`: assumptions, remaining findings, blind spots (`The strongest test proved X; it did not prove Y.`), rollback concerns.
5. `Judgment`: one consequential decision and who made it; include or link the merge-risk card for a PR or Ship handoff.
6. `Status`: `SIGNED OFF (ACCEPT)` / `REJECTED` / `BLOCKED` / `NOT VERIFIED`. Never "ready to deploy".

End every handoff with a clear next action: name the next ready slice and continue when authorized; otherwise ask the user for the specific decision or input needed. When the requested work is complete and no action is required, explicitly say it is finished. Distinguish slice status from overall feature status.

Do not call tests PASS without running them. Do not silently push, merge into `main`, publish, drop databases or change credentials.


## Model selection details

Use the host's current `/model` list and supported agent models. For Claude Code offer available `fable`, `opus`, `sonnet` and `haiku` aliases; availability varies and aliases do not promise exact versions ([model overview](https://platform.claude.com/docs/en/models/overview), [subagent model selection](https://code.claude.com/docs/en/sub-agents#choose-a-model)). For Codex offer available Codex models. Write persistent choices to `.mydevfactory.json` and show the change; per-run overrides stay temporary. Ask again only for an empty value or a requested change. If a model or effort is rejected, use the session value and report it honestly.

## Analysis instructions

For Full feature, the analyst follows `analyst-playbook.md`, investigates code and domain docs, returns consequential questions with recommendations, and writes the PRD and thin vertical slices from the templates. Ask questions in chat, record answers and dispatch a fresh analyst to continue. Check each slice contract, owned files, test commands and negative criterion before starting; request corrections when necessary. Convert existing specifications into the board without duplication. Follow the Fix read-only contract above.
