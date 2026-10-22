#!/usr/bin/env python3
"""Read-only legacy boot/ramdisk inventory. Never extracts archive paths or runs blobs."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import struct
import zlib

LIMIT = 64 * 1024 * 1024

def digest(data):
    return hashlib.sha256(data).hexdigest()

def align(n, a):
    return (n + a - 1) // a * a

def cpio_entries(data):
    pos, seen, result = 0, set(), []
    while pos + 110 <= len(data) and len(result) < 20000:
        h = data[pos:pos + 110]
        if h[:6] not in (b'070701', b'070702'):
            raise ValueError('Unsupported or malformed newc archive')
        f = [int(h[6 + n*8:14 + n*8], 16) for n in range(13)]
        mode, size, namesize = f[1], f[6], f[11]
        if not 1 <= namesize <= 4096 or pos + 110 + namesize > len(data):
            raise ValueError('Invalid archive name length')
        rawname = data[pos + 110:pos + 110 + namesize]
        if rawname[-1:] != b'\0' or b'\0' in rawname[:-1]:
            raise ValueError('Invalid archive name')
        name = rawname[:-1].decode('utf-8', 'strict')
        start = align(pos + 110 + namesize, 4)
        end = start + size
        if end > len(data):
            raise ValueError('Truncated archive entry')
        body = data[start:end]
        pos = align(end, 4)
        if h[:6] == b'070702' and (sum(body) & 0xffffffff) != f[12]:
            raise ValueError('CPIO checksum mismatch')
        if name == 'TRAILER!!!':
            if size or any(data[pos:]):
                raise ValueError('Nonzero data after archive trailer')
            return result
        if PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts or name in seen:
            raise ValueError('Unsafe or duplicate archive name')
        seen.add(name)
        row = {'name': name, 'mode': oct(mode), 'bytes': size, 'sha256': digest(body)}
        base = PurePosixPath(name).name
        if stat.S_ISREG(mode) and size <= 256*1024 and (base.startswith(('init.', 'fstab', 'ueventd')) or base == 'default.prop'):
            row['text'] = body.decode('utf-8', 'strict')
        result.append(row)
    raise ValueError('Missing archive trailer or entry limit exceeded')

def inspect(data):
    if not 1632 <= len(data) <= LIMIT or data[:8] != b'ANDROID!':
        raise ValueError('Invalid boot magic/length')
    v = struct.unpack_from('<10I', data, 8)
    page = v[7]
    if page not in (2048, 4096, 8192, 16384) or v[8] != 0:
        raise ValueError('Only legacy zero-word40 images supported')
    offset, chunks, parts = page, [], {}
    for name, size in zip(('kernel', 'ramdisk', 'second'), (v[0], v[2], v[4])):
        if offset + align(size, page) > len(data):
            raise ValueError('Component exceeds boot image')
        body = data[offset:offset + size]
        chunks.append(body)
        parts[name] = {'offset': offset, 'bytes': size, 'sha256': digest(body)}
        offset += align(size, page)
    sha = hashlib.sha1()
    for body in chunks:
        sha.update(body)
        sha.update(struct.pack('<I', len(body)))
    dec = zlib.decompressobj(31)
    raw = dec.decompress(chunks[1], LIMIT + 1)
    if len(raw) > LIMIT or not dec.eof or dec.unused_data or dec.unconsumed_tail:
        raise ValueError('Ramdisk limit, truncation or additional gzip data')
    entries = cpio_entries(raw)
    return {'status': 'STATIC_INSPECTION_ONLY', 'bytes': len(data), 'sha256': digest(data),
            'page_size': page, 'kernel_addr': v[1], 'ramdisk_addr': v[3],
            'second_addr': v[5], 'tags_addr': v[6], 'components': parts,
            'legacy_sha1_id_matches': sha.digest() == data[576:596],
            'tail': {'offset': offset, 'bytes': len(data)-offset,
                     'nonzero_bytes': sum(b != 0 for b in data[offset:]), 'sha256': digest(data[offset:])},
            'ramdisk_uncompressed_bytes': len(raw), 'ramdisk_entries': entries,
            'firmware_authenticity_verified': False, 'hardware_boot_tested': False}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True, help='New LOCAL JSON; may contain proprietary init text')
    a = p.parse_args()
    if a.image.stat().st_size > LIMIT:
        p.error('Image size exceeds limit')
    report = inspect(a.image.read_bytes())
    with a.out.open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'ramdisk_entries'}, indent=2))

if __name__ == '__main__':
    main()
