#!/usr/bin/env python3
"""Measure a build host and inspect pinned manifests; never sync Android."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import urllib.request
import xml.etree.ElementTree as ET

COMMIT = 'c7b3d4b65b79e2e0d6a891547ad138e1fcdafb56'
BASE = f'https://raw.githubusercontent.com/LineageOS/android/{COMMIT}/'
LIMIT = 2 * 1024 ** 2


def safe_path(name):
    p = PurePosixPath(name)
    if not name or p.is_absolute() or '..' in p.parts or '\\' in name:
        raise ValueError('Unsafe manifest path')
    return p


def inspect_manifest(fetch):
    documents, elements, visiting = {}, [], set()

    def visit(name):
        safe_path(name)
        if not name.endswith('.xml') or name in visiting:
            raise ValueError('Invalid include or include cycle')
        if name in documents:
            raise ValueError('Repeated include requires manual review')
        if len(documents) >= 16:
            raise ValueError('Manifest document budget exceeded')
        visiting.add(name)
        data = fetch(name)
        if len(data) > LIMIT or b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
            raise ValueError('Oversized XML or forbidden DTD/entity')
        root = ET.fromstring(data)
        if root.tag != 'manifest':
            raise ValueError('Expected manifest root')
        documents[name] = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
        for child in root:
            if child.tag == 'include':
                # Includes resolve from manifest repository root, as repo does.
                if set(child.attrib) != {'name'}:
                    raise ValueError('Include attributes require manual review')
                visit(child.attrib['name'])
            else:
                elements.append(child)
        visiting.remove(name)

    visit('default.xml')
    defaults, remotes = {}, {}
    for node in elements:
        if node.tag == 'default':
            if defaults:
                raise ValueError('Multiple defaults')
            defaults = dict(node.attrib)
        elif node.tag == 'remote':
            name = node.attrib['name']
            if name in remotes:
                raise ValueError('Duplicate remote')
            remotes[name] = dict(node.attrib)
        elif node.tag not in ('project', 'repo-hooks', 'notice', 'manifest-server'):
            raise ValueError(f'Unsupported manifest operation: {node.tag}')
    projects, paths = [], set()
    for node in elements:
        if node.tag != 'project':
            continue
        if any(c.tag not in ('copyfile', 'linkfile', 'annotation') for c in node):
            raise ValueError('Nested project/operation requires manual review')
        name = node.attrib['name']
        path = node.get('path', name)
        safe_path(name)
        safe_path(path)
        if path in paths:
            raise ValueError('Duplicate project path')
        paths.add(path)
        remote = node.get('remote', defaults.get('remote'))
        if remote not in remotes:
            raise ValueError(f'Unknown remote for {path}')
        revision = node.get('revision', remotes[remote].get('revision', defaults.get('revision')))
        if not revision:
            raise ValueError(f'Missing revision for {path}')
        projects.append({'path': path, 'name': name, 'remote': remote,
                         'revision': revision, 'commit_pinned': bool(re.fullmatch(r'[0-9a-fA-F]{40}', revision)),
                         'groups': node.get('groups', '').split(',')})
    return {'documents': documents, 'remotes': remotes, 'projects': projects,
            'project_count': len(projects),
            'unfrozen_project_count': sum(not p['commit_pinned'] for p in projects),
            'projects_per_remote': dict(Counter(p['remote'] for p in projects)),
            'warning': 'Manifest inventory only; no dependency-complete pruned build or project sizes measured'}


def resources(path):
    disk = shutil.disk_usage(path)
    ram = None
    meminfo = Path('/proc/meminfo')
    if meminfo.is_file():
        values = dict(line.split(':', 1) for line in meminfo.read_text().splitlines())
        ram = int(values['MemTotal'].split()[0]) * 1024
    limit = None
    for file in ('/sys/fs/cgroup/memory.max', '/sys/fs/cgroup/memory/memory.limit_in_bytes'):
        try:
            value = Path(file).read_text().strip()
            if value.isdecimal():
                limit = int(value)
                break
        except OSError:
            pass
    effective = min(v for v in (ram, limit) if v is not None) if ram is not None or limit is not None else None
    return {'disk_free_bytes': disk.free, 'disk_total_bytes': disk.total,
            'ram_total_bytes': ram, 'cgroup_memory_limit_bytes': limit,
            'effective_ram_bytes': effective, 'cpu_count': os.cpu_count(),
            'github_actions': os.environ.get('GITHUB_ACTIONS') == 'true'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--manifest-dir', type=Path, help='Read previously fetched XML; no network')
    p.add_argument('--probe-path', type=Path, default=Path.cwd())
    p.add_argument('--min-free-gib', type=int, default=160)
    a = p.parse_args()
    if a.min_free_gib < 1 or a.out.exists():
        p.error('Positive disk budget and new output directory required')
    a.out.mkdir(parents=True)
    report = {'status': 'PRECHECK_ONLY', 'manifest_commit': COMMIT,
              'full_sync_allowed': False, 'rom_built': False, 'hardware_tested': False,
              'budget_note': '160 GiB default is a planning threshold, not measured Android 10 demand'}
    try:
        report['resources'] = r = resources(a.probe_path)
        report['resource_budget_satisfied'] = (r['disk_free_bytes'] >= a.min_free_gib * 1024**3
            and r['effective_ram_bytes'] is not None and r['effective_ram_bytes'] >= 15 * 1024**3)
        report['minimum_free_gib'] = a.min_free_gib
        report['minimum_effective_ram_gib'] = 15

        def fetch(name):
            if a.manifest_dir:
                root = a.manifest_dir.resolve(strict=True)
                file = (root / name).resolve(strict=True)
                if root not in file.parents or file.stat().st_size > LIMIT:
                    raise ValueError('Fixture escapes root or exceeds budget')
                return file.read_bytes()
            with urllib.request.urlopen(BASE + name, timeout=25) as response:
                return response.read(LIMIT + 1)

        report['manifest'] = inspect_manifest(fetch)
    except (OSError, ValueError, KeyError, ET.ParseError) as error:
        report['status'] = 'PRECHECK_FAILED'
        report['error'] = str(error)
        report['resource_budget_satisfied'] = False
    (a.out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    summary = ['# Mate S remote preflight', '', f'Status: {report["status"]}',
               '', 'Full Android sync: disabled. ROM built: no. Hardware tested: no.',
               '', f'Resource planning budget satisfied: {report.get("resource_budget_satisfied", False)}.']
    if 'resources' in report:
        summary += [f'Free disk: {report["resources"]["disk_free_bytes"] / 1024**3:.1f} GiB.']
    if 'manifest' in report:
        m = report['manifest']
        summary += [f'Projects: {m["project_count"]}; revisions not frozen to SHA: {m["unfrozen_project_count"]}.']
    if 'error' in report:
        summary += ['Manifest/resource check failed; inspect report.json.']
    (a.out / 'summary.md').write_text('\n'.join(summary) + '\n')
    print(json.dumps({k: report[k] for k in ('status', 'full_sync_allowed', 'resource_budget_satisfied')}))
    return 1 if report['status'] == 'PRECHECK_FAILED' else 0


if __name__ == '__main__':
    sys.exit(main())
