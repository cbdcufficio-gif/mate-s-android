#!/usr/bin/env python3
"""Read-only consistency checks for the generic public Q base; never ROM acceptance."""
import argparse
import json
from pathlib import Path
import re
import sys
from elf_audit import sha256

FILES = {'PUBLIC-BASE-README.txt','resolved-manifest.xml','modules-report.json',
         'system-report.json','generic-q-system.img.gz','public-graphics-modules.tar.gz'}


def verify(root):
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Input must be a real directory')
    if {p.name for p in root.iterdir()} != FILES | {'SHA256SUMS'}:
        raise ValueError('Expected exactly the six release assets and SHA256SUMS')
    for name in FILES | {'SHA256SUMS'}:
        p = root/name
        if p.is_symlink() or not p.is_file():
            raise ValueError('Symlink or non-file asset')
        limit = 2*1024**3 if name.endswith(('.gz',)) else 2*1024**2
        if not 0 < p.stat().st_size < limit:
            raise ValueError('Asset size outside limits')
    sums = {}
    for line in (root/'SHA256SUMS').read_text().splitlines():
        m = re.fullmatch(r'([a-f0-9]{64})  ([A-Za-z0-9_.-]+)',line)
        if not m or m[2] not in FILES or m[2] in sums:
            raise ValueError('Invalid, duplicate or unsafe checksum entry')
        sums[m[2]] = m[1]
    if sums.keys() != FILES:
        raise ValueError('Incomplete checksums')
    for name, digest in sums.items():
        if sha256(root/name) != digest:
            raise ValueError('Checksum mismatch: '+name)
    system = json.loads((root/'system-report.json').read_text())
    modules = json.loads((root/'modules-report.json').read_text())
    if system.get('status') != 'PUBLIC_GENERIC_SYSTEM_IMAGE_BUILT' or system.get('product') != 'lineage_arm64-userdebug':
        raise ValueError('Unexpected system product or build status')
    if modules.get('status') != 'PUBLIC_GRAPHICS_MODULES_BUILT' or modules.get('product') != 'lineage_arm64-userdebug':
        raise ValueError('Unexpected module product or build status')
    for report, proprietary in ((system,'proprietary_huawei_inputs'),(modules,'proprietary_inputs')):
        if any(report.get(k) is not False for k in ('rom_built','carrera_built','hardware_tested',proprietary)):
            raise ValueError('Report scope is not the generic public base')
    compressed = system.get('compressed_image',{})
    image = root/'generic-q-system.img.gz'
    if compressed.get('bytes') != image.stat().st_size or compressed.get('sha256') != sums[image.name]:
        raise ValueError('Compressed image metadata mismatch')
    return {'status':'PUBLIC_BASE_CHECKSUMS_VERIFIED','hardware_compatibility_verified':False,
            'authenticity_verified':False,'note':'Self-consistent local hashes are not a trusted signature or ROM validation.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory',type=Path,required=True)
    a = p.parse_args()
    try:
        print(json.dumps(verify(a.directory)))
    except (OSError,ValueError,KeyError,TypeError) as error:
        print('STOP: '+str(error),file=sys.stderr)
        return 1
    return 0

if __name__=='__main__':
    raise SystemExit(main())
