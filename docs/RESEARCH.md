# Opportunity assessment — 2026-11-11

**2026-11-14 follow-up:** [Same-input comparison and release-baseline case](RELEASE_BASELINE.md).
Direct diff detected every synthetic payload change in the three sampled sources;
skil's lock verification also rejected changed content in a separate control.
The independent detection-value hypothesis is not supported by these checks.
The remaining question is workflow convenience and actionable output, not missing
byte-comparison technology. The historical assessment below records the original decision.

## Decision

Build a small offline **Skill artifact parity checker**: compare the package or accessible installed copy against the directory the author actually edited. The initial benefit is fewer stale/wrong release artifacts and clearer evidence when reporting an update problem.

This is an under-served lightweight workflow hypothesis, not a claim that no tools can solve it. Demand evidence is qualitative; no representative frequency survey or user interviews have been completed. Shipping an alpha and measuring actual adoption is the next validation step.

## User evidence

- [Claude Code issue #46844](https://github.com/anthropics/claude-code/issues/46844): a reporter describes a save/replace operation packaging an older host copy rather than the edited working copy. This motivates comparing the actual artifact, not trusting a successful save message. It is a user report, not an independently reproduced platform defect.
- [Skill delivery issue #96064](https://github.com/anthropics/claude-code/issues/96064): reported stale instruction/script content after an update. An accessible-copy comparison can expose drift, but cannot inspect a remote application's internal loaded state.
- [Humanizer issue #224](https://github.com/blader/humanizer/issues/224): a repository ZIP containing a deliberate symlink was rejected by the GUI uploader; duplicating SKILL.md created another packaging problem. The issue is **closed** and has an upstream fix; this project does not advertise it as an unresolved Humanizer bug. It illustrates why a source repository ZIP and a release artifact are different objects.
- [Reddit: reliably updating skills](https://www.reddit.com/r/claude/comments/1sl82hu/how_to_get_claude_to_update_skills_reliably/): users describe inconsistent update workflows and confusion about where edits were saved.
- [Reddit: update button / packaging workflow](https://www.reddit.com/r/ClaudeAI/comments/1qentbr/skills_not_updating_claude_skills_update_button/): discussion points toward explicit working copies and packaging, rather than assuming saving changed an installed skill.

Evidence covers GitHub and Reddit for the selected workflow. Cursor's forum was also reviewed for the rejected MCP opportunity. Search coverage is not evidence of market size, and no usage or conversion numbers are claimed.

## Directions rejected after comparison

| Direction | Evidence and existing solutions | Decision |
| --- | --- | --- |
| Cross-client MCP configuration management | [Reddit demand](https://www.reddit.com/r/mcp/comments/1kb920q), [conforme](https://github.com/maxgfr/conforme), [APM](https://microsoft.github.io/apm/consumer/install-mcp-servers/) | Multiple substantial implementations; avoid another generic sync tool. |
| MCP diagnostics / safe reporting | [Cursor support requests](https://forum.cursor.com/t/my-cursor-cannot-use-any-mcp-tools/112752), [MCP-Doctor](https://github.com/stephenywilson/MCP-Doctor/), [mcp_doctor](https://github.com/Tinkora/mcp_doctor) | Offline diagnostics and redaction already covered; not a strong standalone gap. |
| Skill structure / broken references | [skill-validator](https://github.com/agent-ecosystem/skill-validator) | Existing dedicated validation; do not reimplement full YAML or Markdown validation. |
| Skill upstream updates with local modifications | [Vercel issue #455](https://github.com/vercel-labs/skills/issues/455), [skills-check-updates](https://github.com/irekrog/skills-check-updates) | A purpose-built project already exists; avoid duplicating its update/merge contract. |
| Artifact verification | [skil](https://github.com/domehahn/skil) includes archive verification using lockfile manifests and package digests | Significant overlap. Prefer skil when its broader governance fits. Test a narrower no-manifest, standard-library-only comparison utility instead. |

Repository feature comparisons are based on public documentation inspected on the assessment date, not a benchmark of those projects. “Mature” was not inferred from star counts.

## Acceptance for this initial candidate

- Compare directories, ZIP and `.skill` inputs by exact bytes, without extracting or executing anything.
- Distinguish changed/missing/extra payloads; normalize one wrapper only.
- Fail clearly for unreadable inputs and ambiguous/unsafe archive structures.
- Publish JSON and human output, deterministic tests, clear limits, bilingual usage documentation.
- Publish a public GitHub repository and a release only after an authenticated publishing route is available.
- Promote with a concrete reproducible example and disclose affiliation. Do not mass-comment on old issues, promise bug fixes in third-party clients, buy engagement, or claim comprehensive safety.

## Validation and next market test

Local regression fixtures model stale content, missing helpers, multi-skill ZIPs, symlinks and malformed archives. They establish this tool's behavior, not successful upload into Claude or fixes to upstream products.

After publication, invite skill authors to try the release gate on their own *non-private* staged artifacts. Track reports of actionable discrepancies versus false positives, successful integrations, and requests for features already covered by competitors. If existing tools are consistently preferred, contribute this workflow upstream rather than growing another platform.

## Format references

[Agent Skills specification](https://agentskills.io/specification) describes the skill directory and SKILL.md structure. [Claude's authoring guide](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills) documents the packaging workflow. This utility checks frontmatter delimiters only; it does not claim full specification compliance or future client compatibility.
