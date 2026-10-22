#!/usr/bin/env python3
"""Install a reviewed module-only Carrera overlay into a local Android source tree."""
import argparse
import json
from pathlib import Path
import shutil
import sys
from elf_audit import sha256

PROJECT = Path(__file__).resolve().parents[1]


def install(android, graphics):
    android = Path(android).resolve(strict=True)
    graphics = Path(graphics).resolve(strict=True)
    if not (android / 'build/envsetup.sh').is_file():
        raise ValueError('Not a synced Android source tree: build/envsetup.sh absent')
    if not (android / 'vendor/lineage/config/common_full_phone.mk').is_file():
        raise ValueError('LineageOS vendor source not present')
    report = json.loads((graphics / 'preparation.json').read_text())
    if report.get('status') != 'OFFLINE_CANDIDATE_PREPARED' or len(report.get('files', [])) != 8:
        raise ValueError('Incomplete or incompatible graphics preparation')
    for record in report['files']:
        relative = Path(record['output'])
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Unsafe prepared file path')
        file = graphics / relative
        if file.is_symlink() or graphics not in file.resolve().parents:
            raise ValueError('Prepared file escapes the graphics directory')
        if sha256(file) != record['candidate_sha256']:
            raise ValueError(f'Candidate hash mismatch: {relative}')
    # Verify recipe/metadata checksums as well as the binary hashes.
    for line in (graphics / 'SHA256SUMS').read_text().splitlines():
        digest, relative = line.split('  ', 1)
        file = graphics / relative
        if Path(relative).is_absolute() or '..' in Path(relative).parts or file.is_symlink():
            raise ValueError('Unsafe checksum path')
        if graphics not in file.resolve().parents or sha256(file) != digest:
            raise ValueError(f'Prepared tree checksum mismatch: {relative}')
    device_out = android / 'device/huawei/carrera'
    graphics_out = android / 'vendor/huawei/carrera-graphics'
    for dest in (device_out, graphics_out):
        if dest.exists() or dest.is_symlink():
            raise ValueError(f'Refusing to overwrite existing target: {dest}')
        if android not in dest.resolve().parents:
            raise ValueError('Target parent symlink escapes Android tree')
    # Copies are local; no build, mount, ADB or device operation occurs here.
    for source, dest in ((PROJECT / 'device/huawei/carrera', device_out), (graphics, graphics_out)):
        if any(p.is_symlink() for p in source.rglob('*')):
            raise ValueError('Overlay input contains symlinks')
    device_out.parent.mkdir(parents=True, exist_ok=True)
    graphics_out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(PROJECT / 'device/huawei/carrera', device_out)
    shutil.copytree(graphics, graphics_out)
    return {'status': 'LOCAL_MODULE_OVERLAY_INSTALLED', 'device': str(device_out),
            'graphics': str(graphics_out), 'android_build_tested': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--android-root', type=Path, required=True)
    p.add_argument('--graphics', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    a = p.parse_args()
    if a.report.exists():
        p.error('Report already exists')
    try:
        result = install(a.android_root, a.graphics)
        with a.report.open('x') as stream:
            json.dump(result, stream, indent=2)
    except (OSError, ValueError) as error:
        print(f'STOP: {error}', file=sys.stderr)
        return 1
    print(a.report)
    return 0


if __name__ == '__main__':
    sys.exit(main())
