# Contributing to MyDevFactory

Thanks for improving an open skill for engineering accountability.

## What makes a good contribution?

- A reproducible agent failure (missed invariant, misleading test, broken handoff, excess ceremony).
- A smaller or clearer workflow that improves real delivery.
- A stack-specific review reference that remains optional.
- Documentation that helps a first-time user install and run the skill.

## Before opening a PR

1. Open an issue for a substantial behavior change and describe the problem and expected outcome.
2. Make one focused change; avoid requiring any particular coding-agent vendor.
3. Keep the primary `SKILL.md` concise and reference supporting files by relative paths.
4. Verify `SKILL.md` frontmatter and links. If your change affects examples, mark hypothetical output as illustrative.
5. Include a **before / after prompt and observable evidence** where possible.
6. Protect private code, tokens, customer information, and incident details.
7. Add a short release note at the top of `README.md` in the same PR. Use the target version for the change. If it is still in development, add it under `## What's new in vX.Y.Z (unreleased)`, above the latest released notes. Keep the first line on the latest installable version until the release is ready.

## Pull request checklist

- [ ] Existing agents, third-party skills and documents are preserved.
- [ ] Every role required by the selected route runs and records evidence. Missing or blank roles are recorded as skipped.
- [ ] No test/review/external action is described as performed unless evidenced.
- [ ] Urgent work uses shorter checks and keeps every gate required by the selected route.
- [ ] Changes do not weaken explicit human approval for irreversible actions.
- [ ] Added files and instructions are documented in README.
- [ ] The README release notes show what this change adds or fixes under its target version.

## Community

Be respectful and specific. Disagreement about architectural approaches is welcome; personal attacks are not. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

We welcome issue reports and PRs. Merging remains at the maintainers' discretion.

## Changing pins and releasing

Pins live in [`install/pins.txt`](install/pins.txt): one full 40-character commit SHA per line, not a branch or tag. Keep the names in [`install/agents.txt`](install/agents.txt) in sync. `EJ_PINS` selects another pins file and `EJ_RAW_ROOT` changes the raw download host, which is useful for testing.

The canonical project configuration is `.mydevfactory.json`. Legacy `.engineering-workflow.json` files are copied byte for byte when the new file is absent; both are retained, and the new file takes precedence. The installer selects either name from historical pinned commits.

The installer checks out the resolved hub commit before passing its local tree to the skills CLI. It records the commit in the scope's `.engineering-judgment/skill-pin.json` and removes the CLI's matching temporary-source project lock entry. Update with the installer, including for installations made with older CLI lock entries; generic `skills update` cannot follow the temporary checkout.

The config rename requires a release pin to a commit containing the updated skill: historical pins contain a skill that still reads the legacy filename. Complete the post-merge pin bump before releasing this rename. The installer can retrieve defaults from older pins, but that does not update the old skill.

For a hub release, align `VERSION`, `skills/mydevfactory/SKILL.md` metadata and the changelog with the release version. Set the hub line in `install/pins.txt` to the verified source commit for that version and commit the pin bump. A commit cannot pin itself, so use a separate source commit. Tag the pin-bump commit (for example `v3.5.0`). In the same pin update, put the release version on the first line of `README.md`, remove its unreleased label and check that the install and update commands point to an existing release tag or verified full commit SHA for that version. Keep public install commands pinned. When an agent release merges, replace that agent's SHA with its release commit.

`--ref` and `EJ_REF` accept a tag, a full commit SHA, or a branch. A branch or tag is resolved to a commit SHA before download, including a branch name that contains a slash. The user README recommends a tag or a full SHA.

Check a pin change before you publish it:

```bash
python3 scripts/validate_skill.py
bash tests/installer_e2e.sh          # Linux and macOS
```

```powershell
python scripts/validate_skill.py
pwsh -File tests/installer_e2e.ps1   # Windows, PowerShell 5.1 or 7
```

Both need network access to the pinned commits and Node.js 22.20 or later.
