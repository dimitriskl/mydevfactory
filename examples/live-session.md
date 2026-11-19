# Example: one change, not a ceremony

*Illustrative interaction; no production system was inspected.*

**Developer:** Use mydevfactory in Fix + Deadline mode. I have 30 minutes to stop duplicate orders when an external provider retries webhooks.

**Agent:** `Risk: high (duplicate external side effects). Goal: at most one ERP order per external order. No new PRD: the existing bug report is enough. Reserve time for duplicate-delivery and failure-path checks. Need one decision: can the remote API accept an idempotency key?`

The coding specialist then works on a bounded patch. The orchestration skill requires evidence rather than the claim *tests pass*.

**Example handoff:**
- `Delivered`: idempotency guard at the persistence boundary
- `Actually invoked`: analyst, backend, frontend (applicability check), reviewer, securitycode, QA
- `Proved`: 2 deliveries of the same event lead to 1 persisted order in a controlled test
- `Not proved`: two workers racing; ERP commit followed by local crash
- `Consequence`: production release requires a concurrency check or explicit residual-risk decision

## Full feature example

**Developer:** Use mydevfactory in Full feature mode. Add invoice approval in a C# API and Angular UI. Ask me only what is unclear.

**Agent:** The analyst reads the code and an existing issue, asks one question (how to prevent simultaneous approvals, with a recommended answer), and writes `prd/invoice-approval/` with two slices. Fresh backend and frontend agents build slice 001 against its Contract. The reviewer fails round 1 (audit row not in the same transaction) and writes why into the slice file; after the fix it passes, securitycode checks the updated diff and passes, and QA passes all four criteria. The orchestrator merges the slice, runs the integration check, then walks the developer through six steps in **Walkthrough** before the Developer sign-off. See the [resulting files](prd/invoice-approval/).

## A role is disabled in the project

**Developer:** Use mydevfactory in Auto mode. Implement a small UI validation fix.

**Agent:** The project has no frontend mapping and uses a generalist in the backend role. MyDevFactory records frontend as SKIPPED and gives the generalist the task. Configured reviewer, securitycode, and QA roles still run before integration.
