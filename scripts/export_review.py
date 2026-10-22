#!/usr/bin/env python3
"""Export selected metadata only, never proprietary libraries or phone user data."""
import argparse
from pathlib import Path
import tarfile
import sys
from elf_audit import sha256


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--graphics', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    source = a.graphics.resolve(strict=True)
    if a.out.exists():
        p.error('Output already exists')
    names = ['preparation.json', 'Android.bp', 'carrera-graphics.mk', 'SHA256SUMS']
    files = [source / n for n in names]
    if any(not f.is_file() or f.is_symlink() or f.stat().st_size > 16 * 1024**2 for f in files):
        p.error('Missing, symlinked or unexpectedly large metadata')
    with tarfile.open(a.out, 'x:gz') as archive:
        for file in files:
            archive.add(file, arcname=file.name, recursive=False)
    print(a.out.resolve())
    print('SHA256:', sha256(a.out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
