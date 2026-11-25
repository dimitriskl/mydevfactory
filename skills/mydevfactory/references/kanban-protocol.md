# Kanban protocol — PRD folders, statuses and orchestration

The orchestrator is the **main session running this skill**. It never writes production code while a callable specialist exists. Each role is a kanban column, and every step is done by a **fresh agent** that works from the files alone. The files are the board: they hold the full record of what was asked, decided, built, reviewed and tested.

## Folder layout

```
<project root>/
  prd/
    <prd-name>/                    ← kebab-case, e.g. invoice-approval
      <prd-name>.md                ← the PRD (templates/prd.md)
      prd-tasks/
        001-<slice-name>.md        ← one vertical slice per file (templates/slice.md)
        002-<slice-name>.md
```

`prd/` is committed with the code. One slice file = one thin vertical slice = one demoable piece of value. A slice that touches backend and frontend has one part for each, built against the slice's **Contract**. A single-layer slice has one part.

## Statuses

Use these exact strings.

- **Part status** (in each `Backend part` / `Frontend part`): `To do` → `Developing` → `Developed`.
- **Slice status** (header `Status:`): `To do` → `In development` → `In review` → `In security review` → `In QA` → `Completed`, plus `Blocked: needs clarification`.

A status that is **not in the transition table** (for example, hand-edited) is invalid: stop and ask the developer what it should be. Never guess.

For scheduling, `Completed` means the slice passed its workflow gates. It releases dependents only after it is accepted and the combined checks and integration have succeeded in every target repository. Track that outcome in the run record. A finished worktree on its own does not release a dependency.

The orchestrator adds a History line for **every** status move it makes (`orchestrator | <from> → <to> | <reason>`), so the board can be rebuilt from the files alone.

## Transition table

Every allowed move. Any other move is invalid and the orchestrator rejects it.

| From | Event | To | Set by |
| --- | --- | --- | --- |
| Part `To do` | developer starts | Part `Developing` | developer |
| Part `Developing` | done with evidence | Part `Developed` | developer |
| Slice `To do` | first part starts | `In development` | orchestrator |
| Slice `In development` | all parts `Developed` | `In review` | orchestrator |
| `In review` | reviewer PASS or role disabled in JSON | `In security review` | orchestrator |
| `In security review` | securitycode PASS or role disabled in JSON | `In QA` | orchestrator |
| `In security review` | securitycode FAIL | affected part(s) `To do`, slice `In development` | orchestrator |
| `In review` | reviewer FAIL | failed part(s) `To do`, slice `In development` | orchestrator |
| `In QA` | QA PASS or role disabled in JSON, and workflow evidence check passes | `Completed` | orchestrator |
| `In QA` | QA FAIL | affected part(s) `To do`, slice `In development` | orchestrator |
| Open slice, including a resumed one | earlier required evidence missing or invalidated | earliest applicable stage with missing or stale evidence | orchestrator (record reason and preserve history) |
| any | open question | `Blocked: needs clarification`, header `Blocked from: <status> · question: <ref>` | orchestrator |
| `Blocked: needs clarification` | developer answered | the status in `Blocked from:` (then clear that line) | orchestrator |
| any | 3rd failure | `Blocked: needs clarification` with `Blocked from:` (escalate) | orchestrator |
| `Completed` | merge/integration check fails | owning part(s) `To do`, slice `In development` (counts as failure) | orchestrator |
| `Completed` | developer change request (Walkthrough) | changed part(s) `To do`, slice `In development` | orchestrator |

## Who writes what

| Role | May write | Never writes |
| --- | --- | --- |
| analyst | PRD file, slice files, `CONTEXT.md`, ADRs in `docs/adr/` | production code, tests |
| backend / frontend | its part's **Owned files** and their tests; its own `Part status` and `Evidence:` block; one History line | other parts, slice `Status:`, verdicts, the Contract |
| reviewer | **only the slice file**: its verdict, `Review notes`, one History line | source code, tests, any other file |
| securitycode | evidence report returned to orchestrator for `Security review notes` and History | all files, external systems |
| qa | **only the slice file**: its verdict, `QA notes`, one History line | source code, tests, any other file |
| orchestrator | slice `Status:`, `Failures:`, `Questions & answers`, `Change requests`, the PRD `Slices` index, integration records and `Developer sign-off` | production code (while a specialist is callable) |

The orchestrator moves a slice only after checking the evidence is written in the file: the part's `Evidence:` block (`command | exit code | key output`) for `Developed`, a verdict with findings for review, security verdict with scope and limitations, and a per-criterion table for QA. Use the applicable role decisions and checker in `workflow-evidence.md`.

## Fresh agent prompts

Every run is a **fresh agent**. Never rely on conversation history, because Codex does not guarantee a clean context. On Codex, set `fork_turns="none"` for each fresh dispatch when supported, so the agent does not inherit the full conversation. Every prompt is self-contained and includes: role, the slice file path, the PRD path, the files it may change, the update rules from "Who writes what", and what to return. For agents able to write their evidence, request at most 10 lines: status, files changed, key evidence and questions; other details go in the slice or PRD. Read-only agents must return the complete verdict and evidence needed for verbatim recording, without a line cap. All agents write locations as `path/from/repo/root.ext:line`.

- **Analyst:** the request, the developer's answers so far, domain docs, relevant code paths. Do the work in `references/analyst-playbook.md`. Return the files written and the open questions, each with a recommended answer.
- **Backend / frontend:** "Implement only your part of `<slice file>` against its Contract. Read the slice Contract and relevant Review/QA notes and Change requests addressed to your part; consult the PRD or other referenced files when more context is needed. Set your part to `Developing`; when every test command passed, fill your part's `Evidence:` block (`command | exit code | key output`) and set it to `Developed`. Add one History line. If you need a file outside your Owned files, stop and return a question instead of editing it. Return: changed files, concise evidence references, assumptions, questions. Do not commit or stage."
- **Reviewer:** "Review the diff `<range>` for `<slice file>` against its Contract and acceptance criteria. Edit only this slice file: verdict, Review notes, History. Write PASS or FAIL per part, with `severity | file:line | failure scenario | what must be done`, and what the green checks don't prove. Mark each finding `blocking` or `follow-up`; FAIL only on a blocking finding. From round 2, start with the previous findings, affected callers and the fix range `<last reviewed sha>..<candidate sha>`. Report newly demonstrated blocking defects wherever found (see the Review rounds section)."
- **Securitycode:** "Review the candidate diff and relevant files for security. Return PASS, FAIL or NOT RUN with inspected scope, any evidence-backed findings, recommended remediation and limits. Do not edit files."
- **QA:** "Run the build and test commands, then exercise the feature against every acceptance criterion: happy path, edge, failure, and loading/empty/error states for UI. Edit only this slice file: verdict, QA notes table, criteria with no automated test, History. Write no code."

If a mapped reviewer or QA agent can't write files, the orchestrator records its returned verdict verbatim, labelled `Verdict by <agent>, recorded by orchestrator`. For Fix, apply the selected route to these prompts. Dispatch a selected analyst read-only to return intent, criteria, checks and questions; dispatch reviewer and QA read-only to return their complete verdicts and evidence. The orchestrator records these verbatim in the task card with their authors. Do not ask them to create `prd/` or write the card unless their definitions explicitly permit it; adapt the prompts above accordingly.

## Questions

Agents stop only when something is unclear and changes what gets built. A subagent can't talk to the developer, so it **returns** its questions. The orchestrator then:

1. Sets the slice to `Blocked: needs clarification` and writes `Blocked from: <previous status> · question: <ref>` in its header (for the analyst, the question's `Blocks` column names the affected slices).
2. Asks the developer **in chat, one question at a time**, with the recommended answer. Start the message with **🟥 REPLY REQUIRED** on its own line. Attribute the question to the agent that raised it using `<color> <role> [<model>, <effort>] (<agent name>) · Question n/N`. Bold the question itself. Count every question in the current batch in N. If an answer raises new questions, update the total and say how many were added.
3. Records the question and answer: analyst questions in the PRD `Open questions & answers`, all others in the slice `Questions & answers`.
4. Restores the status in `Blocked from:`, clears that line, and dispatches a fresh agent.

## Retry cap

`Failures: n/3` counts review FAILs, security review FAILs, QA FAILs and post-merge check failures together. On the **3rd** failure, set `Blocked: needs clarification`, summarise the three rounds for the developer, and wait.

## Review rounds

Review → fix → re-review loops are the most expensive part of a slice, so every round must close findings, not reopen the review. These rules apply to the reviewer, securitycode and QA.

- **Blocking or follow-up.** Mark every finding `blocking` or `follow-up`. A finding is **blocking** only when it has a concrete failure scenario and the change breaks the Contract or an acceptance criterion, has a correctness, security or data-loss defect, or lacks a test an acceptance criterion requires. Everything else is a **follow-up**: naming, style, wording, optional hardening, refactors, and tests beyond the criteria. A part FAILs only on a blocking finding. Follow-ups are listed in the notes, shown in the handoff, and never start a fix round.
- **Round 1 is complete.** The first run of each role reports every blocking finding it can find, in one pass. Do not hold findings back for a later round.
- **Later rounds check the fix, not the whole slice.** From round 2, give the agent the previous round's findings and the **fix range** `<last reviewed sha>..<candidate sha>`. Confirm each previous blocking finding is fixed and follow the fix into affected callers. Report any evidenced blocking defect in the candidate under the same criteria as round 1, including a violated contract or invariant outside the fix range. Explain in one sentence how the later review found it. QA reruns the failed criteria and the full test commands.
- **Record the range.** Each round's header names what was reviewed: `Round n · <agent> · reviewed <base>..<sha>`.

## Branches and commits

- **Before dispatching the analyst** (and on every resume), identify the main worktree for the board and use **`feature/<prd-name>`** there. Create it from the current branch or switch to it if it exists. If it is already checked out, use that worktree. Record `Base: <branch>@<sha>` in the PRD header. For a feature spanning multiple repositories, also record each repository's main worktree and local integration branch as described in `parallel-worktrees.md`.
- If the working tree has **uncommitted** changes at that point, ask the developer to choose: **stash** them (`git stash push -u -m mydevfactory`), **commit** them on their current branch first, or **stop**. Never start agents on top of the developer's uncommitted work.
- If the current branch is `main`, say so in the same question; the feature branch is still created from it.
- After each verified step, the orchestrator commits on the current work branch with the message `<prd-or-slice-id> <column>: <result>` (the analysis step included), so git history mirrors the board. Agents don't commit or stage.
- Serial slices are built directly on `feature/<prd-name>`; only parallel slices get their own worktree branch.
- Never commit to `main`, never merge into `main`, never push.

## Parallel worktrees

Within a slice, the **parts run one after another** in role order (backend, then frontend). Follow `parallel-worktrees.md` to select ready, independent slices, create isolated worktrees and dispatch their agents concurrently. This is the orchestrator's decision within the authorized scope. Keep the PRD `Slices` index current in the main worktree. The isolated slice file is the source of truth for that slice until integration succeeds.

## After merge

For a serial slice, run the build, tests and contract checks on the **combined** code in the main worktree and record the verified revision and outcome. Apply its sign-off gate before unlocking dependencies. If the checks fail, reopen the owning parts and count the failure toward the retry cap. For a parallel slice, follow the acceptance, verification, promotion and cleanup steps in `parallel-worktrees.md`. Never report the slice as integrated before all its targets have passed.

## Resume

A new session rebuilds the board from the files, never from memory:

1. Read every `prd/*/prd-tasks/*.md` header (`Status:`, `Blocked by:`, `Failures:`) and each part status.
2. Read the integration run record and run `git worktree list --porcelain` in each involved repository. Match temporary branches and paths to slices and use each active worktree's copy of the slice file. Reconcile pending promotions and cleanup before dispatching again. For worktrees from older runs, use the existing branch name and card to identify the slice, then verify the base, scope and evidence before registering it. Leave unrecognized worktrees and branches alone.
3. Add the Workflow evidence section to open cards or slices that predate it. Keep older reports in the notes. Validate evidence against the trusted role map, contract, acceptance criteria and candidate. Return an open slice to the earliest required stage without valid evidence and record why in History.
4. Report the board concisely, including slices awaiting acceptance, integration or cleanup. Reuse verified work and continue with the next ready batch. For older completed slices without a run record, verify the commits are present in the integration branches and check the existing sign-off and combined evidence before releasing dependents. Run missing checks against the existing code.

## Context checkpoints

Models get less reliable as their context fills; past about 40% used, they start to miss earlier decisions. Two rules keep every agent below that line:

- **One job, one fresh agent.** A job is the analysis, one part of one slice, one review, security review or QA run. Every **new job** starts in a fresh agent; a job is never handed to an agent that already did another one.
- **Auto-compact at 40% while a job runs.** If an agent (the orchestrator included) reaches 40% context used before its job is done, it compacts and continues the same job. It is not replaced mid-job.

Auto-compaction is a host setting; the skill can't change it from markdown. In Phase 0, check once whether it is set and, if not, tell the developer the exact setting:

- **Claude Code:** environment variable `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=40`, exported in the shell before starting (applies to the main session and its subagents).
- **Codex CLI:** `model_auto_compact_token_limit` in `~/.codex/config.toml` or the project's `.codex/config.toml`, set to 40% of the model's context window (for example `160000` for a 400,000-token window). Custom agents inherit it unless their own file overrides it.

So compaction loses nothing, the files are the memory:

1. **Checkpoints:** after the analysis, after each slice reaches `Completed`, after each merge, and before the Walkthrough, make sure every status, verdict, answer and History line is in the files, then print `⚪ orchestrator [<model>, <effort>]: checkpoint · board saved`.
2. Agents write progress into their slice file as they go (part status, `Evidence:`, History), not only at the end.
3. After any compaction, follow "Resume": rebuild the board from the files, never from what the summary remembers. A compacted agent re-reads its slice file before continuing.

Keep command output small: show only the lines that prove a result (exit code, test summary), never full logs.

## Verdict enforcement

**Before every dispatch**, add the dispatch History line first. Run `python3 <skill-dir>/scripts/dispatch_snapshot.py capture` in the worktree. Keep its printed private temporary directory outside the worktree until the scope check and any correction finish. It holds HEAD, staged-content identity, and the contents and modes of dirty tracked and non-ignored untracked files. If capture fails, resolve the cause before running the agent.

**After the agent returns**, compare against that snapshot:

1. Run `python3 <skill-dir>/scripts/dispatch_snapshot.py compare <snapshot-directory>`. A changed HEAD or index blocks the verdict. Preserve the tree and inspect the discrepancy.
2. The JSON list contains paths changed since dispatch, including additional edits to previously dirty files. An empty list means the compared worktree contents match. If a path may also have been edited concurrently, pause before attributing or undoing its changes.
3. **Scope check:** every changed path must be allowed for the role ("Who writes what"): no path for securitycode, the slice file for reviewer and QA, the part's Owned files and their tests for developers.
4. **Section check:** for a card already dirty at dispatch, look up its numbered backup in `snapshot.json` and compare it to the live card with `git diff --no-index -- <backup> <card>` (exit 1 means differences). For a previously clean tracked card use the captured HEAD. Check that only allowed sections changed and History only gained lines at the end.

On a violation:

- Discard the invalid verdict. Restore only changes attributable to the agent using the captured bytes, symlink target or absence for previously dirty paths and the captured HEAD for originally clean tracked files. Preserve staged contents. If ownership is uncertain or the file changed again, keep both versions and ask the developer. Remove the private snapshot after the comparison and any correction are complete.
- Add a History line `orchestrator | violation | <agent> changed <files>; reverted`.
- Allow **one corrective re-run** with a fresh agent and an explicit warning. A second violation on the same step sets `Blocked: needs clarification` and asks the developer (for example, the Owned files list may be missing a file the part really needs).

Remove the private snapshot after a successful scope check as well. Violations do not count toward `Failures:`, but they are capped as above, so no loop runs forever.
