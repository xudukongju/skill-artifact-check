"""Exercise a reviewed data packager on synthetic inputs, including recovery.

Usage: python examples/reproduce_empty_package.py /path/to/package_data_skill.py
The supplied script is executed, not sandboxed. Only use a script you trust.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

CHECKER = Path(__file__).resolve().parents[1] / 'skill_artifact_check.py'
FILES = {'SKILL.md': b'---\nname: acme-analyst\ndescription: Synthetic packaging test.\n---\nRead references/metrics.md.\n',
         'references/metrics.md': b'Synthetic metric definition.\n'}


def run_case(label, source, output, expected, packager, env):
    proc = subprocess.run([sys.executable, str(packager), str(source), str(output)],
                          env=env, cwd=source.parent, capture_output=True, text=True, timeout=30)
    archive = output / 'acme-analyst.zip'
    if proc.returncode != 0 or not archive.is_file():
        raise RuntimeError(f'{label}: packager failed or did not create the expected ZIP')
    with zipfile.ZipFile(archive) as z:
        members = z.namelist()
        contents = {name: z.read(name) for name in members}
    wanted = {'acme-analyst/' + name: data for name, data in FILES.items()}
    if len(members) != len(contents):
        raise RuntimeError(f'{label}: duplicate entries')
    exact = contents == wanted
    gate = subprocess.run([sys.executable, str(CHECKER), str(archive), '--source', str(expected), '--json'],
                          env=env, capture_output=True, text=True, timeout=30)
    report = json.loads(gate.stdout)
    if exact != (gate.returncode == 0):
        raise RuntimeError(f'{label}: gate and independent byte comparison disagree')
    if label != 'hidden-parent' and not exact:
        raise RuntimeError(f'{label}: recovery/control payload differs from expectation')
    print(json.dumps({'case': label, 'packager_exit': proc.returncode, 'entries': len(members),
                      'payload_matches': exact, 'gate_exit': gate.returncode,
                      'gate_error': report.get('error'), 'changes': report.get('changes', [])}))
    return exact


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('packager', type=Path, help='Reviewed local package_data_skill.py')
    parser.add_argument('--temp-root', type=Path, help='Existing directory with no hidden ancestors')
    args = parser.parse_args()
    packager = args.packager.resolve()
    if not packager.is_file():
        parser.error('packager must be an existing file')
    base = (args.temp_root or Path(tempfile.gettempdir())).resolve()
    if any(part.startswith('.') for part in base.parts):
        parser.error('temporary root has a dot-prefixed ancestor; choose --temp-root elsewhere')
    with tempfile.TemporaryDirectory(prefix='skill-package-case-', dir=base) as temp:
        root = Path(temp)
        env = {k: os.environ[k] for k in ('PATH', 'SYSTEMROOT', 'WINDIR') if k in os.environ}
        env.update(HOME=str(root), TMPDIR=str(root), TMP=str(root), TEMP=str(root),
                   PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1')
        visible = root / 'visible/acme-analyst'
        expected = root / 'expected/acme-analyst'
        for directory in (visible, expected):
            for name, data in FILES.items():
                path = directory / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
        (visible / '.local-only').write_bytes(b'Excluded synthetic sentinel.\n')
        hidden = root / '.claude/skills/acme-analyst'
        staged = root / 'staging/acme-analyst'
        shutil.copytree(visible, hidden)
        shutil.copytree(hidden, staged)
        for label, source in [('visible-control', visible), ('hidden-parent', hidden),
                              ('staged-recovery', staged)]:
            run_case(label, source, root / ('out-' + label), expected, packager, env)


if __name__ == '__main__':
    main()
