# A successful packager can still deliver an empty ZIP

The data-context-extractor packager in [knowledge-work-plugins issue 1298](https://github.com/anthropics/knowledge-work-plugins/issues/1298)
validates the source successfully, but its hidden-file filter includes ancestors
outside the skill directory. Under `.claude/skills`, every file is omitted.
The original reporter identified this mechanism; this case adds an executable
delivery-and-recovery check, rather than another implementation of their fix.

## Reproduce the actual script, not a simulated packager

Requires Python 3.10+. Download and inspect this
[fixed upstream script revision](https://github.com/anthropics/knowledge-work-plugins/blob/e91a134584eb798bac7fb0379358006a2b63b965/data/skills/data-context-extractor/scripts/package_data_skill.py),
then run from a checkout of this repository:

```sh
python3 examples/reproduce_empty_package.py /path/to/package_data_skill.py
```

The supplied script is **executed**, not sandboxed: only use a reviewed script you
trust. The example supplies synthetic files in a fresh temporary directory, passes
no account credentials, and deletes only its own temporary fixture. It never
reads your installed skills. If your temporary path has a dot-prefixed ancestor,
choose an existing non-hidden location with `--temp-root /path/to/temp-parent`.
On Windows, `py` can replace `python3`.

Expected results for the linked revision:

| Input | Packager exit | ZIP entries | Independent byte comparison | This CLI's gate exit |
| --- | --- | --- | --- | --- |
| Visible directory | 0 | 2 | Match | 0 |
| Same files under `.claude/skills` | 0 | 0 | Different | 1 |
| Same source copied to non-hidden staging | 0 | 2 | Match | 0 |

The expected file set is created independently, **not extracted from the delivered
ZIP**. The source also contains an internal `.local-only` sentinel: both successful
outputs must still omit it. A future corrected packager may pass the hidden-parent
case too; the runner reports that as a match rather than demanding a bug forever.

The existing CI runs this case against the pinned upstream file on all of its
OS/Python combinations. A download failure is a failed check, not silently skipped
evidence. The runtime CLI remains offline; only this integration setup downloads
the reviewed test subject.

## Recover a real package without changing the packager

Copy your intended source to a new staging directory with no dot-prefixed resolved
ancestors, then use the same packager. For macOS/Linux, the following creates a
fresh output location instead of overwriting an existing archive:

```sh
stage=$(mktemp -d /tmp/data-skill-stage.XXXXXX)
cp -R /absolute/path/to/acme-analyst "$stage/acme-analyst"
python3 /path/to/package_data_skill.py "$stage/acme-analyst" "$stage/out"
python3 -m zipfile -l "$stage/out/acme-analyst.zip"
```

Keep the temporary output until you have checked and copied it to its destination.
Listing the ZIP with Python's standard library already detects this zero-entry
failure; our CLI is optional, useful if you want named missing files and a nonzero
gate against a reviewed expected payload.

For parity, compare with your **intended release files**, not the entire development
directory. See [release-baseline selection](RELEASE_BASELINE.md). In our fixture,
the full development tree contains `.local-only`; treating it as expected delivery
would contradict the packager's intentional exclusion.

## Why switching packagers requires another check

The skill-creator packager at [revision 2c5958e](https://github.com/anthropics/skills/blob/2c5958ecac7cee2b583967a2c4981d0f4a75c579/skills/skill-creator/scripts/package_skill.py)
successfully packaged the hidden-parent fixture, but included `.local-only` as a
third file. It fixes the empty-output symptom with a different exclusion policy.
That is not evidence of real user data exposure; it is a reason to review the
intended payload before substituting tools.

The verified recovery instructions were [shared on the original issue](https://github.com/anthropics/knowledge-work-plugins/issues/1298#issuecomment-6904466556).
User confirmation and upstream resolution remain separate from these reproducible
tests. Example, analysis and integration authored with Codex assistance.
