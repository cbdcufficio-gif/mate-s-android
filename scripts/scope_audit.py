#!/usr/bin/env python3
"""Audit an ELF DT_NEEDED closure against explicitly supplied build library dirs."""
import argparse
import json
from pathlib import Path
import sys
from elf_audit import Elf, resolve_symbols


def audit(consumer_path, library_dirs):
    consumer = Elf(consumer_path).report()
    candidates, invalid = {}, []
    for folder in library_dirs:
        if not folder.is_dir():
            raise ValueError(f'Library directory absent: {folder}')
        for path in sorted(folder.rglob('*.so')):
            if path.is_symlink():
                continue
            try:
                report = Elf(path).report()
            except ValueError as error:
                invalid.append({'file': str(path), 'error': str(error)})
                continue
            if (report['bits'], report['machine']) != (consumer['bits'], consumer['machine']):
                continue
            name = report['soname'] or path.name
            reports = candidates.setdefault(name, [])
            if not any(r['report']['sha256'] == report['sha256'] for r in reports):
                reports.append({'file': str(path), 'report': report})
    selected, missing, ambiguous = {}, [], {}
    pending = list(consumer['needed'])
    seen = set()
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        providers = candidates.get(name, [])
        if not providers:
            missing.append(name)
        elif len(providers) != 1:
            ambiguous[name] = [r['file'] for r in providers]
        else:
            selected[name] = providers[0]
            pending.extend(providers[0]['report']['needed'])
    providers = {name: value['report'] for name, value in selected.items()}
    checked = {'consumer': resolve_symbols(consumer, providers)}
    for name, provider in providers.items():
        checked[name] = resolve_symbols(provider, providers)
    return {'status': 'STATIC_SCOPE_REPORT_ONLY', 'consumer': str(consumer_path),
            'consumer_sha256': consumer['sha256'], 'bits': consumer['bits'],
            'library_dirs': [str(d) for d in library_dirs],
            'missing_needed': sorted(missing), 'ambiguous_sonames': ambiguous,
            'selected': {k: {'file': v['file'], 'sha256': v['report']['sha256']}
                         for k, v in selected.items()}, 'symbols': checked,
            'invalid_elfs': invalid,
            'warning': 'Only explicit DT_NEEDED closure; process-global lookup order, Android '
                       'namespaces, relocation semantics, C++ layout and runtime behavior untested'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--consumer', type=Path, required=True)
    parser.add_argument('--library-dir', type=Path, action='append', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error('Output exists')
    try:
        report = audit(args.consumer, args.library_dir)
        with args.out.open('x') as stream:
            json.dump(report, stream, indent=2)
    except (OSError, ValueError) as error:
        print(f'STOP: {error}', file=sys.stderr)
        return 1
    print(f'Missing dependencies: {len(report["missing_needed"])}; '
          f'ambiguous SONAMEs: {len(report["ambiguous_sonames"])}')
    print(args.out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
