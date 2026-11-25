# Routing matrix and risk levels

Adapt to the current codebase. Select a route before dispatch using `workflow-evidence.md`. Risk, scope and mode determine the required roles.

| Situation | Discovery and planning | Implementation | Review and learning |
| --- | --- | --- | --- |
| L0: copy/format-only edit | Short task card | Scoped change | Relevant deterministic check on the single-owner copy route |
| L1: localized bug | Reproduce; short intent; existing task | Owning specialist; focused tests | Independent reviewer and targeted regression test on a single-layer fix route |
| L1: new feature or cross-stack change | Analyst writes `prd/<prd-name>/` PRD + slice files (converts existing specs) | Board: fresh developer per part against the slice Contract | Reviewer → securitycode → QA per slice; integration check; Walkthrough sign-off |
| L2: auth, sensitive data, migrations, retries, payments | Explicit invariants, known failure scenarios, human decision for irreversible choices | Controlled scope, safe handoffs, failure-path tests | QA covers failure paths and invariants; per-slice Walkthrough sign-off; human release gate |
| Data/report/metric change | Analyst confirms metric definitions and expected results on known data | Owning specialist; queries and transformations under test | Analyst read-only data check with exact queries and output; reviewer |
| Existing `prd/` board | Do **not** regenerate; rebuild board from slice files | Resume next ready slice | Review, security review, QA, sign-off |
| Walkthrough | Read diff, PRD and slices | None; change requests go back to the board | Step-by-step walkthrough, then ACCEPT / REJECT |
| Audit only | No PRD | No implementation unless requested | Enabled reviewer and securitycode review the original diff and actual test output |
| Drill | Use real source and current diff | No code generation until requested | Question, human answer, evidence-based feedback (the only mode with quiz questions) |
| Deadline | Only minimal intent | Smallest shippable slice | Selected route with one fix round; flag unverified behavior |

**Risk guide**

- **L0:** formatting, documentation, harmless text changes with no behavior impact.
- **L1:** ordinary behavior change with bounded rollback.
- **L2:** money, authorization, personal data, irreversible writes, schema migration, concurrent external side effects, or multi-tenant boundaries.

The scope may increase the risk. The developer, not the model alone, owns consequential risk acceptance.

**Decision questions**

1. Is the problem already defined in existing project docs? Reuse them.
2. Which behavior must remain invariant, and what would falsify the proposed fix?
3. Are the mapped agents (analyst, backend, frontend, reviewer, securitycode, qa) really callable or merely named in `.mydevfactory.json`?
4. What codepaths and interface contracts could the change affect?
5. What did actual checks prove, and what did they miss?
6. What would you need to defend this change to its maintainer?

Do not confuse **implemented**, **verified**, **reviewed**, and **released**.
