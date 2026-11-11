import contextlib
import io
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile

import skill_artifact_check as sac

SKILL = b'---\nname: demo\ndescription: Test skill.\n---\nUse references/guide.md.\n'


class ArtifactsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'SKILL.md').write_bytes(SKILL)

    def zip(self, entries, name='test.skill'):
        target = self.root / name
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
                for path, content in entries:
                    if isinstance(path, str):
                        # ZipInfo normalizes backslashes on Windows and truncates
                        # NULs. Preserve raw fixture bytes to test the reader,
                        # rather than accidentally testing a sanitized archive.
                        info = zipfile.ZipInfo(path)
                        info.filename = path
                        info.orig_filename = path
                        info.compress_type = zipfile.ZIP_DEFLATED
                        path = info
                    z.writestr(path, content)
        return target

    def test_wrapped_parity(self):
        archive = self.zip([('demo/SKILL.md', SKILL)])
        report = sac.check(archive, self.source)
        self.assertTrue(report['ok'])
        self.assertEqual(report['layout'], 'wrapped-zip')

    def test_flat_parity(self):
        self.assertTrue(sac.check(self.zip([('SKILL.md', SKILL)]), self.source)['ok'])

    def test_archive_to_archive(self):
        a = self.zip([('demo/SKILL.md', SKILL)], 'a.zip')
        b = self.zip([('SKILL.md', SKILL)], 'b.zip')
        self.assertTrue(sac.check(a, b)['ok'])

    def test_stale_missing_extra(self):
        (self.source / 'helper.py').write_text('new helper')
        archive = self.zip([('demo/SKILL.md', SKILL + b'old'), ('demo/old.txt', b'old')])
        self.assertEqual(sac.check(archive, self.source)['changes'], [
            {'path': 'SKILL.md', 'state': 'changed'}, {'path': 'helper.py', 'state': 'missing'},
            {'path': 'old.txt', 'state': 'extra'}])

    def test_binary_exactness(self):
        (self.source / 'asset.bin').write_bytes(b'\x00\xff')
        archive = self.zip([('SKILL.md', SKILL), ('asset.bin', b'\x00\xfe')])
        self.assertEqual(sac.check(archive, self.source)['changes'][0]['state'], 'changed')

    def test_line_endings_not_normalized(self):
        archive = self.zip([('SKILL.md', SKILL.replace(b'\n', b'\r\n'))])
        self.assertFalse(sac.check(archive, self.source)['ok'])

    def test_empty_directory_ignored(self):
        archive = self.zip([('demo/SKILL.md', SKILL), ('demo/empty/', b'')])
        self.assertTrue(sac.check(archive, self.source)['ok'])

    def test_unsafe_names(self):
        for name in ['../escape', '/absolute', 'a/../../escape', 'a\\b', 'C:/file', 'a//b', './a', 'CON.txt', 'a.','a/aux','a\x1bb']:
            with self.subTest(name=name):
                with self.assertRaises(sac.ArtifactError):
                    sac.check(self.zip([('SKILL.md', SKILL), (name, b'x')]))

    def test_unsafe_fixture_preserves_raw_names(self):
        for name in ['a\\b', 'a\x00b']:
            with self.subTest(name=name):
                archive = self.zip([('SKILL.md', SKILL), (name, b'x')])
                self.assertEqual(archive.read_bytes().count(name.encode()), 2)
                with zipfile.ZipFile(archive) as z:
                    self.assertEqual(z.infolist()[1].orig_filename, name)
                with self.assertRaises(sac.ArtifactError):
                    sac.check(archive)

    def test_duplicate_members(self):
        with self.assertRaises(sac.ArtifactError):
            sac.check(self.zip([('SKILL.md', SKILL), ('SKILL.md', b'other')]))

    def test_case_collision(self):
        with self.assertRaises(sac.ArtifactError):
            sac.check(self.zip([('SKILL.md', SKILL), ('skill.md', SKILL)]))

    def test_implicit_directory_collision(self):
        with self.assertRaises(sac.ArtifactError):
            sac.check(self.zip([('SKILL.md', SKILL), ('A/x', b''), ('a/y', b'')]))

    def test_unicode_collision(self):
        with self.assertRaises(sac.ArtifactError):
            sac.check(self.zip([('SKILL.md', SKILL), ('caf\u00e9', b''), ('cafe\u0301', b'')]))

    def test_file_directory_collision(self):
        with self.assertRaises(sac.ArtifactError):
            sac.check(self.zip([('SKILL.md', SKILL), ('a', b''), ('a/b', b'')]))

    def test_archive_symlink(self):
        link = zipfile.ZipInfo('link')
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        with self.assertRaises(sac.ArtifactError):
            sac.check(self.zip([('SKILL.md', SKILL), (link, b'/etc/passwd')]))

    def test_directory_symlink(self):
        try:
            (self.source / 'link').symlink_to(self.source / 'SKILL.md')
        except OSError:
            self.skipTest('Symlinks unavailable')
        with self.assertRaises(sac.ArtifactError):
            sac.check(self.source)

    def test_root_symlink(self):
        link = self.root / 'link'
        try:
            link.symlink_to(self.source, target_is_directory=True)
        except OSError:
            self.skipTest('Symlinks unavailable')
        with self.assertRaises(sac.ArtifactError):
            sac.check(link)

    def test_wrong_wrapper_depth(self):
        result = sac.check(self.zip([('repo/skills/demo/SKILL.md', SKILL)]))
        self.assertIn('missing-skill', [f['code'] for f in result['findings']])

    def test_multiple_skills(self):
        result = sac.check(self.zip([('demo/SKILL.md', SKILL), ('demo/other/SKILL.md', SKILL)]))
        self.assertIn('nested-skill', [f['code'] for f in result['findings']])

    def test_hygiene(self):
        for name in ['.env', '.env.local', '.git/config', '__MACOSX/data', '__pycache__/a.pyc', '.DS_Store']:
            with self.subTest(name=name):
                report = sac.check(self.zip([('SKILL.md', SKILL), (name, b'private')]))
                self.assertIn('release-hygiene', [f['code'] for f in report['findings']])

    def test_invalid_utf8(self):
        self.assertEqual(sac.check(self.zip([('SKILL.md', b'\xff')]))['findings'][0]['code'], 'skill-encoding')

    def test_bom(self):
        self.assertFalse(sac.check(self.zip([('SKILL.md', b'\xef\xbb\xbf' + SKILL)]))['ok'])

    def test_missing_frontmatter(self):
        self.assertFalse(sac.check(self.zip([('SKILL.md', b'hello')]))['ok'])

    def test_empty_zip(self):
        self.assertFalse(sac.check(self.zip([]))['ok'])

    def test_corrupt_zip(self):
        bad = self.root / 'bad.zip'
        bad.write_bytes(b'not a zip')
        with self.assertRaises(sac.ArtifactError):
            sac.check(bad)

    def test_absent_input(self):
        with self.assertRaises(sac.ArtifactError):
            sac.check(self.root / 'absent')

    def test_file_limit(self):
        with patch.object(sac, 'MAX_FILE', 5):
            for source in [self.source, self.zip([('SKILL.md', SKILL)])]:
                with self.assertRaises(sac.ArtifactError):
                    sac.check(source)

    def test_total_limit(self):
        with patch.object(sac, 'MAX_TOTAL', 5):
            for source in [self.source, self.zip([('SKILL.md', SKILL)])]:
                with self.assertRaises(sac.ArtifactError):
                    sac.check(source)

    def test_entry_limit(self):
        with patch.object(sac, 'MAX_ENTRIES', 0):
            for source in [self.source, self.zip([('SKILL.md', SKILL)])]:
                with self.assertRaises(sac.ArtifactError):
                    sac.check(source)

    def test_archive_size_limit(self):
        with patch.object(sac, 'MAX_ARCHIVE', 5):
            with self.assertRaises(sac.ArtifactError):
                sac.check(self.zip([('SKILL.md', SKILL)]))

    def test_report_omits_contents(self):
        secret = b'EXAMPLE_PRIVATE_CONTENT_93812'
        archive = self.zip([('SKILL.md', SKILL + secret)])
        report = sac.check(archive, self.source)
        self.assertNotIn(secret.decode(), sac.render(report) + json.dumps(report))

    def test_source_invalid_even_if_matching(self):
        (self.source / 'SKILL.md').write_bytes(b'bad')
        report = sac.check(self.source, self.source)
        self.assertFalse(report['ok'])
        self.assertEqual({f['side'] for f in report['findings']}, {'source', 'artifact'})

    def test_cli_json_exit_codes(self):
        for args, expected in [([str(self.source), '--json'], 0),
                               ([str(self.zip([])), '--json'], 1),
                               ([str(self.root / 'absent'), '--json'], 2)]:
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(sac.main(args), expected)
            self.assertEqual(json.loads(out.getvalue())['schema_version'], 1)

    def test_subprocess_entry_point(self):
        result = subprocess.run([sys.executable, str(Path(sac.__file__)), str(self.source), '--source', str(self.source), '--json'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['ok'])

    def test_scripts_never_execute(self):
        (self.source / 'danger.py').write_text('raise RuntimeError("must not execute")')
        self.assertTrue(sac.check(self.source, self.source)['ok'])


if __name__ == '__main__':
    unittest.main()
