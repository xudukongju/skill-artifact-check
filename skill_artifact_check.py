"""Offline, read-only parity checks for Agent Skill release artifacts."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import stat
import sys
import unicodedata
import zipfile
import zlib

__version__ = '0.1.0'
MAX_ENTRIES = 10000
MAX_FILE = 16 * 1024 * 1024
MAX_TOTAL = 128 * 1024 * 1024
MAX_ARCHIVE = 160 * 1024 * 1024


class ArtifactError(Exception):
    """An input cannot be inspected completely."""


@dataclass
class Artifact:
    files: dict[str, bytes]
    layout: str
    findings: list[dict]


def finding(code, path, message):
    return {'code': code, 'path': path, 'message': message}


def validate_path(name):
    """Reject ambiguous or nonportable names before reading archive members."""
    if not name or '\\' in name or any(ord(c) < 32 or ord(c) == 127 for c in name):
        raise ArtifactError('Unsafe or ambiguous member name.')
    parts = name.split('/')
    for part in parts:
        if part in ('', '.', '..') or part.endswith((' ', '.')) or re.search(r'[<>:"|?*]', part):
            raise ArtifactError('Unsafe or nonportable member path.')
        if part.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL', *('COM'+str(i) for i in range(1, 10)), *('LPT'+str(i) for i in range(1, 10))}:
            raise ArtifactError('Reserved device name in artifact.')
    return name


def validate_names(entries):
    seen = {}
    types = dict(entries)
    for name, is_dir in entries:
        validate_path(name)
        # Include implicit directories to catch A/x versus a/y on macOS/Windows.
        parts = name.split('/')
        for i in range(1, len(parts) + 1):
            prefix = '/'.join(parts[:i])
            key = unicodedata.normalize('NFC', prefix).casefold()
            previous = seen.setdefault(key, prefix)
            if previous != prefix:
                raise ArtifactError('Case or Unicode-normalization collision in artifact.')
            if i < len(parts) and prefix in types and not types[prefix]:
                raise ArtifactError('File/directory collision in artifact.')


def inspect_files(files, layout):
    findings = []
    if 'SKILL.md' not in files:
        findings.append(finding('missing-skill', 'SKILL.md', 'Select one skill folder containing SKILL.md.'))
    for name, data in sorted(files.items()):
        if name != 'SKILL.md' and name.split('/')[-1] == 'SKILL.md':
            findings.append(finding('nested-skill', name, 'One upload artifact should contain one skill; split this bundle.'))
        parts = name.split('/')
        if any(p in {'.git', '.env', '.DS_Store', '__MACOSX', '__pycache__'} or p.startswith('.env.') for p in parts):
            findings.append(finding('release-hygiene', name, 'Remove local metadata or environment files from the release staging folder.'))
        if name == 'SKILL.md':
            try:
                text = data.decode('utf-8')
            except UnicodeDecodeError:
                findings.append(finding('skill-encoding', name, 'SKILL.md must be UTF-8.'))
                continue
            if text.startswith('\ufeff'):
                findings.append(finding('skill-bom', name, 'Save UTF-8 without a byte-order mark.'))
            lines = text.splitlines()
            if not lines or lines[0] != '---' or '---' not in lines[1:]:
                findings.append(finding('frontmatter-boundary', name, 'Add YAML frontmatter delimited by ---; use a spec validator for field validation.'))
    return Artifact(files, layout, findings)


def load_directory(root):
    files, entries, total = {}, [], 0
    def visit(directory, prefix=''):
        nonlocal total
        with os.scandir(directory) as iterator:
            for entry in iterator:
                name = prefix + entry.name
                info = entry.stat(follow_symlinks=False)
                is_dir = stat.S_ISDIR(info.st_mode)
                entries.append((name, is_dir))
                if len(entries) > MAX_ENTRIES:
                    raise ArtifactError('Entry limit exceeded (10000).')
                validate_path(name)
                if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
                    raise ArtifactError('Symbolic links and reparse points are not supported; stage regular files explicitly.')
                if is_dir:
                    visit(entry.path, name + '/')
                elif stat.S_ISREG(info.st_mode):
                    if info.st_size > MAX_FILE:
                        raise ArtifactError('File size limit exceeded (16 MiB).')
                    with open(entry.path, 'rb') as stream:
                        data = stream.read(MAX_FILE + 1)
                    total += len(data)
                    if len(data) > MAX_FILE or total > MAX_TOTAL:
                        raise ArtifactError('Uncompressed size limit exceeded.')
                    files[name] = data
                else:
                    raise ArtifactError('Only regular files and directories are supported.')
    visit(root)
    validate_names(entries)
    return inspect_files(files, 'directory')


def load_zip(path):
    files, entries, total = {}, [], 0
    if path.stat().st_size > MAX_ARCHIVE:
        raise ArtifactError('Archive size limit exceeded (160 MiB).')
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        if len(members) > MAX_ENTRIES:
            raise ArtifactError('Entry limit exceeded (10000).')
        seen = set()
        for item in members:
            if item.orig_filename != item.filename:
                raise ArtifactError('ZIP member name contains a NUL byte.')
            name = item.filename[:-1] if item.is_dir() else item.filename
            validate_path(name)
            if name in seen:
                raise ArtifactError('Duplicate ZIP member name.')
            seen.add(name)
            mode = item.external_attr >> 16
            kind = stat.S_IFMT(mode)
            if kind not in (0, stat.S_IFREG, stat.S_IFDIR) or (kind == stat.S_IFDIR and not item.is_dir()) or (kind == stat.S_IFREG and item.is_dir()):
                raise ArtifactError('ZIP contains a symbolic link, special file, or inconsistent file type.')
            if item.flag_bits & 1:
                raise ArtifactError('Encrypted ZIP members are not supported.')
            if item.file_size > MAX_FILE:
                raise ArtifactError('File size limit exceeded (16 MiB).')
            total += item.file_size
            if total > MAX_TOTAL:
                raise ArtifactError('Uncompressed size limit exceeded (128 MiB).')
            entries.append((name, item.is_dir()))
        validate_names(entries)
        for item in members:
            if not item.is_dir():
                with archive.open(item) as stream:
                    data = stream.read(MAX_FILE + 1)
                if len(data) != item.file_size or len(data) > MAX_FILE:
                    raise ArtifactError('ZIP member size mismatch.')
                files[item.filename] = data
    layout = 'flat-zip'
    # Strip exactly one wrapper, never search recursively for a convenient SKILL.md.
    roots = {name.split('/')[0] for name in files}
    if len(roots) == 1 and files and all('/' in name for name in files):
        wrapper = next(iter(roots))
        files = {name[len(wrapper) + 1:]: data for name, data in files.items()}
        layout = 'wrapped-zip'
    return inspect_files(files, layout)


def load(path):
    path = Path(path)
    try:
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ArtifactError('Input must not be a symbolic link or reparse point.')
        if stat.S_ISDIR(info.st_mode):
            return load_directory(path)
        if not stat.S_ISREG(info.st_mode):
            raise ArtifactError('Input must be a regular ZIP file or a directory.')
        return load_zip(path)
    except (OSError, zipfile.BadZipFile, NotImplementedError, RuntimeError, EOFError, RecursionError, zlib.error) as exc:
        # Do not print exception contents: ZIPs/paths may carry terminal escapes or secrets.
        raise ArtifactError('Cannot fully read input (%s). Check access and ZIP integrity.' % type(exc).__name__) from None


def check(path, source=None):
    actual = load(path)
    issues = [{**issue, 'side': 'artifact'} for issue in actual.findings]
    changes = []
    result = {'schema_version': 1, 'tool_version': __version__, 'layout': actual.layout,
              'file_count': len(actual.files), 'byte_count': sum(map(len, actual.files.values())),
              'findings': issues, 'changes': changes, 'comparison': source is not None}
    if source is not None:
        expected = load(source)
        issues.extend({**issue, 'side': 'source'} for issue in expected.findings)
        for name in sorted(expected.files.keys() | actual.files.keys()):
            if name not in actual.files:
                state = 'missing'
            elif name not in expected.files:
                state = 'extra'
            elif actual.files[name] != expected.files[name]:
                state = 'changed'
            else:
                continue
            changes.append({'path': name, 'state': state})
    result['ok'] = not issues and not changes
    return result


def render(result):
    lines = [('PASS' if result['ok'] else 'FAIL') + '  skill-artifact-check',
             '%s | %d files | %d bytes' % (result['layout'], result['file_count'], result['byte_count'])]
    for issue in result['findings']:
        lines.append('  %s [%s] %s: %s' % (issue['side'], issue['code'], json.dumps(issue['path'], ensure_ascii=True), issue['message']))
    for change in result['changes']:
        lines.append('  %-7s %s' % (change['state'], json.dumps(change['path'], ensure_ascii=True)))
    if result['comparison']:
        lines.append('Byte-for-byte payload match.' if not result['changes'] else 'Rebuild from the intended source or inspect the installed copy. No files were modified.')
    else:
        lines.append('Structure checked. Add --source to detect stale or missing payloads.')
    lines.append('Scope: payload/layout only; YAML fields, safety, and runtime loading are not certified.')
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('artifact', help='ZIP/.skill archive or a skill directory to inspect')
    parser.add_argument('--source', help='Expected skill directory or ZIP; compare every file byte-for-byte')
    parser.add_argument('--json', action='store_true', help='Machine-readable output (schema_version 1)')
    args = parser.parse_args(argv)
    try:
        result = check(args.artifact, args.source)
    except ArtifactError as exc:
        result = {'schema_version': 1, 'tool_version': __version__, 'ok': False, 'error': str(exc)}
        print(json.dumps(result) if args.json else 'ERROR  ' + str(exc))
        return 2
    print(json.dumps(result, ensure_ascii=True, indent=2) if args.json else render(result))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
