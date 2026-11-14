# Skill Artifact Check

**Did the skill you shipped contain the changes you made?**

An offline, zero-runtime-dependency CLI that compares a `.skill`/ZIP release or an installed skill folder against the source you intended to ship. It names missing, extra, and changed files without printing their contents.

[Downloads](https://github.com/xudukongju/skill-artifact-check/releases) · [中文说明](README.zh-CN.md) · [Why this exists](docs/RESEARCH.md) · [Report contract](docs/REPORT.md)

```text
FAIL  skill-artifact-check
wrapped-zip | 2 files | 234 bytes
  changed "SKILL.md"
  missing "scripts/helper.py"
Rebuild from the intended source or inspect the installed copy. No files were modified.
```

Illustrative output; counts depend on the supplied artifact.

## Try it without installing anything

Requires Python 3.10 or newer. Download this project's source, enter its directory, then run:

```sh
python3 skill_artifact_check.py examples/demo
python3 -m zipfile -c /tmp/demo.skill examples/demo
python3 skill_artifact_check.py /tmp/demo.skill --source examples/demo
```

Use a new output path if `/tmp/demo.skill` already exists. On Windows, use `py` instead of `python3` and an available temporary path.

For your own skill:

```sh
# Before upload: compare the release with the intended, clean payload.
python3 skill_artifact_check.py ./dist/my-skill.skill --source ./staging/my-skill

# After installation: compare the installed copy with the intended source.
python3 skill_artifact_check.py ./installed/my-skill --source ./my-skill --json

# Compare two downloaded artifacts, ignoring their single wrapper-folder names.
python3 skill_artifact_check.py ./downloaded.skill --source ./expected.zip
```

Optional installation from a local checkout: `python3 -m pip install .`, then use `skill-artifact-check`. Runtime uses only the standard library; pip may fetch the setuptools build dependency. There is no published PyPI package yet.

If your packager excludes development files, comparing against the raw working
directory can flag intentional omissions. [Choose the release baseline](docs/RELEASE_BASELINE.md)
for a runnable example and measured comparisons with direct diff and skil.

## What it checks

- Exact file bytes, including binary assets and line endings: stale instructions, missing helpers, unexpected files.
- Root `SKILL.md`, UTF-8 encoding, frontmatter delimiters, and accidental nested skills.
- ZIP duplicate names, traversal paths, symlinks, special files, case/Unicode collisions, and Windows-reserved paths.
- Common release debris: `.env*`, `.git`, `__MACOSX`, `.DS_Store`, and `__pycache__`.
- Read limits: 10,000 entries, 16 MiB per file, 128 MiB total uncompressed, 160 MiB ZIP container.

One wrapper folder is normalized away. Flat ZIPs are also inspectable; use a single named folder when packaging for clients whose upload guide requires it. Empty directories, timestamps, compression settings, executable bits and wrapper names are not compared. No ignores are implicit: prepare a clean staging folder if the repository contains unrelated material.

## Use it as a release gate

```sh
python3 skill_artifact_check.py dist/my-skill.zip --source staging/my-skill --json
```

Exit codes: **0** = selected checks passed and, if requested, payloads match; **1** = findings or drift; **2** = unreadable/unsupported/unsafe input or CLI usage error. A structure-only pass does not establish parity; pass `--source` for that.

The JSON report has stable `schema_version: 1`. Shell redirection may save it to a file. The CLI itself never modifies inputs, extracts archives, starts skill scripts, discovers private configuration, or accesses the network.

## Pair it with existing tools

Use [skill-validator](https://github.com/agent-ecosystem/skill-validator) for YAML/spec/content checks, [skills-check-updates](https://github.com/irekrog/skills-check-updates) for upstream updates and preserving local changes, and [skil](https://github.com/domehahn/skil) for a broader security and artifact-verification workflow. This tool is a small standalone payload check for people who do not need a manifest, lockfile or security platform.

It cannot fix a client's upload/cache bug, prove that a running agent loaded the files, detect all secrets, or certify a skill's safety. File paths appear in reports; review those before sharing. Read stable local snapshots, not directories being changed by another process.

## Development

```sh
python3 -m unittest discover -s tests -v
```

MIT licensed. Contributions should include a failing fixture and regression test. Use synthetic content in issues; do not attach credentials or private skill archives. Version 0.1.0 is an initial alpha. The [CI workflow](https://github.com/xudukongju/skill-artifact-check/actions/workflows/ci.yml) tests Linux, macOS and Windows on Python 3.10 and 3.12. Implementation, tests and documentation were primarily authored with Codex.
