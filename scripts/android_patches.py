#!/usr/bin/env python3
"""Apply the reviewed public HWC adapter patch only to the exact source bytes."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

PROJECT = Path(__file__).resolve().parents[1]
TARGET = Path('hardware/interfaces/graphics/composer/2.1/utils/hwc2on1adapter/HWC2On1Adapter.cpp')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply_patches(source):
    source = Path(source).resolve(strict=True)
    lock, = json.loads((PROJECT/'configs/android-patches.json').read_text())
    patch = PROJECT/'patches/android/0001-hwc1-null-callbacks.patch'
    target = source/TARGET
    if any(p.is_symlink() for p in (target, *target.parents) if p != source.parent):
        raise ValueError('Symlink in Android patch target')
    if patch.is_symlink() or digest(patch) != lock['patch_sha256']:
        raise ValueError('Android patch checksum mismatch')
    before = digest(target)
    if before == lock['after_sha256']:
        return [dict(lock, status='ALREADY_APPLIED')]
    if before != lock['before_sha256']:
        raise ValueError('Unexpected Android adapter source; refusing to patch')
    # Patch a temporary copy first: a rejected patch never changes the source.
    with tempfile.TemporaryDirectory(prefix='mates-hwc-') as directory:
        work = Path(directory)
        relative = Path(lock['path'])
        if relative != Path(*TARGET.parts[2:]):
            raise ValueError('Unexpected Android patch path')
        candidate = work/relative
        candidate.parent.mkdir(parents=True)
        shutil.copyfile(target, candidate)
        subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-i', str(patch)],
                       cwd=work, check=True, capture_output=True, text=True, timeout=15)
        if digest(candidate) != lock['after_sha256']:
            raise ValueError('Patched Android adapter checksum mismatch')
        target.write_bytes(candidate.read_bytes())
    return [dict(lock, status='APPLIED')]
