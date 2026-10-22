#!/usr/bin/env python3
"""Inventory already extracted stock HALs, without executing or copying blobs."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys
from elf_audit import Elf, ElfError, sha256


def inventory(stock, graphics=None):
    stock = stock.resolve(strict=True)
    index = defaultdict(list)
    records, rejected = {}, []
    for file in sorted(stock.rglob('*.so')):
        relative = file.relative_to(stock).as_posix()
        if file.is_symlink() or any(p.is_symlink() for p in file.parents if p != stock):
            rejected.append({'path': relative, 'reason': 'symlink'})
            continue
        try:
            elf = Elf(file)
            dynamic = elf.dynamic()
            if (elf.bits, elf.machine, elf.type) not in ((32, 40, 3), (64, 183, 3)):
                raise ElfError('Not an ARM32/ARM64 shared library')
            record = {'path': relative, 'sha256': sha256(file), 'bytes': file.stat().st_size,
                      'bits': elf.bits, 'machine': elf.machine, **dynamic}
            records[relative] = record
            index[(elf.bits, dynamic['soname'] or file.name)].append(record)
        except (OSError, ValueError) as error:
            rejected.append({'path': relative, 'reason': str(error)})

    def dependencies(record):
        result = []
        for name in record['needed']:
            providers = index.get((record['bits'], name), [])
            unique = {p['sha256'] for p in providers}
            result.append({'name': name, 'stock_candidates': [p['path'] for p in providers],
                           'status': 'not_in_snapshot' if not providers else
                           'ambiguous' if len(unique) > 1 else 'present_in_snapshot'})
        return result

    hals = []
    for relative, record in records.items():
        if '/hw/' not in relative and 'ril' not in Path(relative).name.lower():
            continue
        symbols = Elf(stock / relative).symbols()
        imports = [s for s in symbols if s['undefined'] and s['bind'] in (1, 2)]
        hals.append({**record, 'dependencies': dependencies(record),
                     'hal_module_info_exported': any(s['name'] == 'HMI' and not s['undefined'] for s in symbols),
                     'strong_import_count': sum(s['bind'] == 1 for s in imports),
                     'cxx_imports': sorted({s['name'] for s in imports if s['name'].startswith('_Z')}),
                     'android10_runtime': 'UNTESTED'})
    candidates = []
    if graphics:
        state = json.loads((graphics / 'preparation.json').read_text())
        for record in state['files']:
            relative = Path(record['output'])
            file = (graphics / relative).resolve(strict=True)
            if relative.is_absolute() or '..' in relative.parts or graphics.resolve() not in file.parents:
                raise ValueError('Unsafe graphics candidate path')
            if sha256(file) != record['candidate_sha256']:
                raise ValueError('Graphics candidate hash mismatch')
            e = Elf(file).report()
            candidates.append({'path': relative.as_posix(), 'sha256': e['sha256'], 'bits': e['bits'],
                               'dependencies': dependencies(e),
                               'cxx_imports': sorted({s['name'] for s in e['symbols']
                                   if s['undefined'] and s['name'].startswith('_Z')}),
                               'android10_runtime': 'UNTESTED'})
    return {'status': 'STATIC_STOCK_INVENTORY_ONLY', 'rom_built': False,
            'stock_library_count': len(records), 'libraries': list(records.values()),
            'hal_and_ril_count': len(hals), 'hal_and_ril': hals,
            'graphics_candidates': candidates, 'rejected': rejected,
            'warning': 'Candidate search ignores Android namespaces and lookup order; snapshot '
                       'presence is not loading proof or Android 10 compatibility. Missing means '
                       'absent from this extraction, not necessarily absent from the firmware.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-system', type=Path, required=True)
    p.add_argument('--graphics', type=Path)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    if a.out.exists():
        p.error('Output already exists')
    try:
        report = inventory(a.stock_system, a.graphics)
        a.out.parent.mkdir(parents=True, exist_ok=True)
        with a.out.open('x') as stream:
            json.dump(report, stream, indent=2)
    except (OSError, ValueError) as error:
        print(f'STOP: {error}', file=sys.stderr)
        return 1
    print(json.dumps({k: report[k] for k in ('status', 'stock_library_count', 'hal_and_ril_count')}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
