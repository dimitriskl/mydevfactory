# Task card — securitycode workflow

- User outcome: Publish a dedicated defensive security reviewer and run every configured MyDevFactory role on development tasks.
- Risk: L1. The user clarified that an absent or empty JSON role disables only its step.
- Accept when Claude Code and Codex definitions parse, securitycode is installable from its GitHub pin, and current evidence is required for each enabled role before the workflow completes.
- Negative cases: a blank role is skipped, a configured role cannot be marked skipped, and a stale or failing security verdict blocks completion.
- Implementation: backend owns the skill, agent package and checks. The frontend role verifies applicability. There are no application UI changes.
- Status: READY FOR HUMAN REVIEW

## Verification

- Candidate commit: `c34b18d07bded5fe69274be27df5a08dd8ffb041`.
- Analysis confirmed the task scope and acceptance criteria. Backend implemented the agent package and workflow checker. Frontend found no applicable application UI work.
- Independent code review passed. A separate agent used the published Securitycode instructions and confirmed that the trusted-role fix resolved its finding. The baseline role map for this run does not list Securitycode.
- Independent QA passed all acceptance criteria. All 14 tests and the skill validator passed. The validator, Linux installer, and Windows installer jobs passed on the candidate in [GitHub Actions](https://github.com/dimitriskl/mydevfactory/actions/runs/44468618793).
- A fresh Windows project install at the candidate commit loaded both Securitycode agent definitions, the default model and effort for each host, and the checker. A blank role passed the installed checker without evidence. The checker rejected missing evidence for enabled roles.
- Live named-agent dispatch and model selection for both hosts remain unverified. The checker validates evidence format, order and revision. The host must dispatch the agents and verify their reports.
- Developer Walkthrough and sign-off are pending.
