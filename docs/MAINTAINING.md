# Research, release and feedback loop

## Choose a problem before writing a tool

Keep the decision in `docs/RESEARCH.md`: original user reports from more than one venue, inspected competing projects, the exact gap, and a falsifiable benefit. Record closed/resolved reports accurately. A broad existing solution is a reason to narrow the workflow or contribute upstream, not a reason to claim there are no competitors.

## Publish a version through the tested path

Use the official GitHub CLI with its normal account authorization. Do not put tokens in scripts or commit configuration. On a machine where browsers use a system proxy but command-line clients do not, pass that existing proxy through the command's `HTTPS_PROXY`/`HTTP_PROXY` environment; do not disable TLS or change network protections.

1. Update both `pyproject.toml` and `skill_artifact_check.__version__`, the changelog, and `docs/releases/VERSION.md`.
2. Commit and push the intended source. Inspect CI for the exact commit and fix real failures.
3. Create the matching `vVERSION` tag and push it. The tag-triggered workflow runs the six OS/Python combinations, builds wheels, installs the CLI, checks tag/version agreement, and publishes a prerelease with wheel/source ZIP assets only after success.
4. Verify the actual release page and asset inventory. Never move an already published tag to silently replace a broken version; ship a corrected version.

The workflow publishes **alpha prereleases**. A stable release is a separate product decision requiring evidence from real use.

## Share once, then listen

After the release exists, share a concrete example in a relevant show-and-tell category whose current rules permit it. Disclose affiliation and AI assistance. Explain the scope and mention the stronger existing alternatives. Record the actual discussion URL outside the source tree; do not count a draft as promotion or a posted link as adoption.

For this project, Agent Skills' Show and tell is relevant. Check its current contribution guidance before posting. Do not submit this utility as a skill-executing client or advertise it in unrelated bug threads.

Use subsequent issue reports and discussion replies to decide the next change. Track useful discrepancies, false positives and successful integrations rather than manufactured stars or traffic. Do not schedule unattended posting or paid promotion without separate authorization.
