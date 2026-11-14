"""Run three synthetic release checks without installing or changing a skill."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile


CLI = Path(__file__).resolve().parents[1] / 'skill_artifact_check.py'


def check(label, artifact, source, expected_exit, expected_changes):
    proc = subprocess.run(
        [sys.executable, str(CLI), str(artifact), '--source', str(source), '--json'],
        capture_output=True, text=True, check=False,
    )
    report = json.loads(proc.stdout)
    if proc.returncode != expected_exit or report.get('changes') != expected_changes:
        raise RuntimeError(f'{label}: unexpected result: {proc.returncode}, {report}')
    print(json.dumps({'case': label, 'exit': proc.returncode,
                      'changes': report['changes']}, sort_keys=True))


def main():
    with tempfile.TemporaryDirectory(prefix='skill-release-baseline-') as temp:
        root = Path(temp)
        source = root / 'working'; source.mkdir()
        (source / 'SKILL.md').write_text(
            '---\nname: release-demo\ndescription: A synthetic release fixture.\n---\n',
            encoding='utf-8')
        (source / 'helper.txt').write_text('current helper\n', encoding='utf-8')
        (source / 'evals').mkdir()
        (source / 'evals/local.txt').write_text('local evaluation only\n', encoding='utf-8')

        # This fixture's explicit policy: ship instructions and helper, not evals.
        stage = root / 'staging'; stage.mkdir()
        for name in ('SKILL.md', 'helper.txt'):
            shutil.copyfile(source / name, stage / name)

        archive = root / 'release.skill'
        with zipfile.ZipFile(archive, 'w') as z:
            for path in sorted(stage.iterdir()):
                z.write(path, 'release-demo/' + path.name)

        check('wrong-baseline', archive, source, 1,
              [{'path': 'evals/local.txt', 'state': 'missing'}])
        check('intended-payload', archive, stage, 0, [])

        # Keep the old artifact, then edit a file that IS intended for delivery.
        (stage / 'helper.txt').write_text('updated helper\n', encoding='utf-8')
        check('stale-delivery', archive, stage, 1,
              [{'path': 'helper.txt', 'state': 'changed'}])


if __name__ == '__main__':
    main()
