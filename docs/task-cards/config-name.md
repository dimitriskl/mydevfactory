# Fix: Canonical configuration name

## Contract

Use `.mydevfactory.json` as the canonical project configuration. Preserve the default JSON contents. When only `.engineering-workflow.json` exists, copy its exact bytes to the canonical name and retain the legacy file. If both exist, leave both untouched and use the canonical file. Resolve historical pinned configurations from the checked-out hub commit, failing if neither name exists or the selected file is empty. Preserve installer state paths.

## Evidence

`python scripts/validate_skill.py`: passed. PowerShell real-network installer suite with Node 22.23.4: 132 passed, 0 failed, including historical pin, legacy byte preservation, and both-file precedence. The final Bash real-network installer suite with Node 22.23.4 passed 133 checks with no failures. Both suites used the existing npm cache. The current pin predates the rename; new-name pinned checkout and missing-config checkout cases have not been exercised.

## Release requirement

After merging, bump the hub pin to a commit containing the renamed skill using the existing release process. The current historical pin contains a skill that still reads the legacy name; retrieving its default configuration does not make that skill recognize the new name. Do not claim end-to-end discovery with that pin.

## Independent review and QA
Reviewer senior-code-reviewer: PASS against 64e9675, no actionable findings; safe as unreleased change, pin bump required before release.
QA qa-automation-engineer: validator exit 0; unittest discover -s tests -p '*validat*.py' -v exit 0 (3 tests); git diff --check exit 0. Default JSON byte-identical to baseline (934 bytes). Active reference and migration-test inspection found no defect. Installer suites are backend evidence (132 PS / 133 Bash), not independently repeated. New-name-only checkout and missing/empty checkout negative cases NOT RUN. No visual UI applicable.
Status: READY FOR HUMAN REVIEW; release not authorized or performed.
Risk: verification medium (stated gaps); alignment low (requested rename); impact medium (project configuration discovery); rollback low (revert feature, legacy settings retained); detection medium (installer messages/validation, no runtime monitoring).
