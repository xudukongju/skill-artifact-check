# Report contract v1

Successful inspection produces JSON with:

- `schema_version`: integer `1`.
- `tool_version`: package version.
- `ok`: no findings and no payload differences.
- `layout`: `directory`, `flat-zip` or `wrapped-zip` for the inspected artifact.
- `file_count`, `byte_count`: actual payload totals, after wrapper normalization.
- `comparison`: whether `--source` was supplied.
- `findings`: objects with `code`, `path`, `message`, and `side` (`source` or `artifact`).
- `changes`: objects with `path` and `state` (`changed`, `missing`, `extra`), sorted by path. Direction is always actual artifact relative to expected source.

An input that cannot be fully inspected returns exit 2 and only `schema_version`, `tool_version`, `ok: false`, `error`. Do not interpret partial evidence as a pass. Invalid CLI syntax is handled by argparse on stderr with exit 2, not a JSON report.

Content bytes and absolute input paths are omitted. Member paths remain visible and might themselves be sensitive. Text output quotes paths with JSON escaping to prevent terminal control sequences being rendered. A filename secret is not redacted.

For v1, empty directory entries and permission bits are ignored in parity comparisons. Findings can fail an otherwise byte-identical comparison. Limits are implementation safety bounds, not official upload limits.
