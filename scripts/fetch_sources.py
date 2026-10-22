#!/usr/bin/env python3
"""Fetch exact public source revisions into a NEW local directory. No phone access."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

PROJECT = Path(__file__).resolve().parents[1]


def command(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--group', choices=['kernel', 'metadata', 'all'], default='kernel')
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    out = args.out.resolve()
    if out.exists():
        p.error('Choose a new output directory; existing clones are never reset')
    lock = json.loads((PROJECT / 'sources.lock.json').read_text())
    selected = [r for r in lock['repositories'] if args.group == 'all' or args.group in r['groups']]
    out.mkdir(parents=True)
    state = {'status': 'INCOMPLETE', 'sources': []}
    try:
        for source in selected:
            dest = out / source['directory']
            command(['git', 'init', '-q', str(dest)])
            command(['git', '-C', str(dest), 'remote', 'add', 'origin', source['url']])
            command(['git', '-C', str(dest), 'fetch', '--depth=1', 'origin', source['commit']])
            command(['git', '-C', str(dest), 'checkout', '--detach', '-q', 'FETCH_HEAD'])
            actual = subprocess.check_output(['git', '-C', str(dest), 'rev-parse', 'HEAD'], text=True).strip()
            if actual != source['commit']:
                raise RuntimeError('Fetched revision mismatch')
            if source['directory'] == 'kernel-hi3635':
                patch = PROJECT / 'patches/kernel/0001-fix-immersion-header-path.patch'
                command(['git', '-C', str(dest), 'apply', '--check', str(patch)])
                command(['git', '-C', str(dest), 'apply', str(patch)])
            state['sources'].append({'directory': source['directory'], 'commit': actual})
        state['status'] = 'FETCHED'
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        state['error'] = str(error)
        (out / 'fetch-report.json').write_text(json.dumps(state, indent=2) + '\n')
        print(f'STOP: {error}', file=sys.stderr)
        return 1
    (out / 'fetch-report.json').write_text(json.dumps(state, indent=2) + '\n')
    print(out / 'fetch-report.json')
    return 0


if __name__ == '__main__':
    sys.exit(main())
