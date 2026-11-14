# Before comparing a release, choose what should ship

A correctly built package can differ from its working directory. Local evaluations,
Python caches and development files may be deliberately excluded. Comparing the
package against the entire working directory then reports real byte differences
that are not release defects.

**Use the intended release payload as the baseline, not automatically the folder
you last edited.** Keep that baseline independent of the delivered artifact:
unpacking the delivered ZIP and using it as its own reference proves nothing.

## Try the distinction locally

From this repository, with Python 3.10+:

```sh
python3 examples/release_baseline.py
```

The script uses its own temporary directory and synthetic files, calls the actual
CLI, checks the results, and removes only its temporary fixture. Expected cases:

| Case | Exit | Meaning |
| --- | --- | --- |
| `wrong-baseline` | 1 | An evaluation file was intentionally not shipped. The working directory is the wrong expectation. |
| `intended-payload` | 0 | The archive matches the explicitly selected staging files. |
| `stale-delivery` | 1 | A selected helper changed after packaging. Rebuild and compare again. |

For a real release, review the inclusion/exclusion policy, prepare the staging
directory from the intended source revision, build, then compare the actual output:

```sh
python3 skill_artifact_check.py dist/my-skill.skill --source staging/my-skill --json
```

Do not add ignores merely to turn an unexplained failure green. If your packager
already defines the expected payload reliably, reuse that policy rather than
maintaining an unrelated list. Neither a matching package nor a lockfile proves
that the selected files are sufficient for the user's task.

## What the existing alternatives actually did

Local observations on 2026-11-14, macOS arm64, Python 3.12, Skill Artifact Check
0.1.0 and the official skil 0.6.0 binary. These are bounded correctness probes,
not speed measurements or reports of defects in the sampled projects.

| Public source inspected | Exact revision | Scope actually exercised |
| --- | --- | --- |
| [Humanizer](https://github.com/blader/humanizer/tree/b48c832f0f809c1b5658edbb838c2521b72f2413) | `b48c832` | Ran its package validator successfully; compared the root skill payload. Its README includes a repository-ZIP upload route. |
| [Anthropic skill-creator](https://github.com/anthropics/skills/tree/2c5958ecac7cee2b583967a2c4981d0f4a75c579/skills/skill-creator) | `2c5958e` | Ran its actual packager and compared the resulting `.skill` file. |
| [Superpowers writing-plans](https://github.com/obra/superpowers/tree/22f0b463e7a5e579904dd6211a520321035526f7/skills/writing-plans) | `22f0b46` | Compared this individual skill's files, not the whole plugin installation. |

For each of the three payloads, a matching ZIP and another ZIP with one synthetic
comment appended to `SKILL.md` were generated. Both `diff -qr` on the corresponding
directories and Skill Artifact Check accepted all three matches and detected all
three changes. **There was no unique byte-change detection advantage over diff.**
These deliberately introduced changes are controls, not upstream failures.

`skil compare` accepted those changes. That command compares capability/security
drift, not byte identity; treating its acceptance as a missed integrity defect
would be the wrong comparison. In a separate integrity control, `skil package build`
built its upstream `clean-skill` fixture, and `skil lock verify` accepted the original
archive and rejected changed content at the same path. That test used a synthetic
lock with the build-produced digests; it did not test signatures or provenance.
Building unmodified Humanizer through skil's package command required a skill
contract that the sampled source did not contain. See [skil](https://github.com/domehahn/skil/releases/tag/v0.6.0)
for its broader workflow.

The actual skill-creator packager intentionally omitted three Python cache files
created by importing its scripts. Comparing that package to the raw working tree
reported those files as missing. Comparing it to a separately prepared staging
tree following the packager's explicit exclusion policy passed, as did direct diff:
18 files, 224,992 payload bytes. The omission was correct packaging, not lost code.

## Which approach to use

- Already have two trusted, unpacked payload directories? `diff -qr expected actual`
  already answers byte parity. An extra tool may add no value.
- Already use skil contracts and locks? Use that integrity workflow; this CLI is
  not a replacement for its security controls.
- Have a ZIP and an intended payload, want named changes/JSON without extraction
  or a manifest? This CLI offers that narrower interface, plus its documented
  structural checks. Whether the convenience merits another release step remains
  a user-workflow question.

For feedback, the useful question is: **what defines the files you intend to ship,
and which step currently checks the delivered artifact against that expectation?**
A description or synthetic reproduction is enough; do not share private archives.

Maintainer-authored with AI assistance. No independent user trials or adoption
are established by these checks.
