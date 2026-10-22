import gzip
import hashlib
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from boot_inspect import cpio_entries, inspect, align


def entry(name, data=b'', mode=0o100644):
    name = name.encode() + b'\0'
    fields = [0, mode, 0, 0, 1, 0, len(data), 0, 0, 0, 0, len(name), 0]
    h = b'070701' + ''.join(f'{n:08x}' for n in fields).encode() + name
    h += b'\0' * (align(len(h), 4)-len(h))
    h += data
    return h + b'\0' * (align(len(h), 4)-len(h))


def image():
    k = b'kernel fixture'
    r = gzip.compress(entry('default.prop', b'ro.secure=1\n') + entry('TRAILER!!!'))
    h = bytearray(2048)
    h[:8] = b'ANDROID!'
    struct.pack_into('<10I', h, 8, len(k), 0, len(r), 0, 0, 0, 0, 2048, 0, 0)
    sha = hashlib.sha1()
    for d in (k, r, b''):
        sha.update(d); sha.update(struct.pack('<I', len(d)))
    h[576:596] = sha.digest()
    for d in (k, r):
        h.extend(d + b'\0' * (align(len(d), 2048)-len(d)))
    return bytes(h)

class BootInspection(unittest.TestCase):
    def test_valid_sha_and_text(self):
        r = inspect(image())
        self.assertTrue(r['legacy_sha1_id_matches'])
        self.assertEqual(r['ramdisk_entries'][0]['text'], 'ro.secure=1\n')
    def test_truncated_component_rejected(self):
        with self.assertRaises(ValueError): inspect(image()[:-2048])
    def test_kernel_tampering_reported(self):
        b = bytearray(image()); b[2048] ^= 1
        self.assertFalse(inspect(b)['legacy_sha1_id_matches'])
    def test_traversal_rejected(self):
        with self.assertRaises(ValueError): cpio_entries(entry('../bad')+entry('TRAILER!!!'))
    def test_trailer_required(self):
        with self.assertRaises(ValueError): cpio_entries(entry('ok'))
    def test_nonzero_tail_rejected(self):
        with self.assertRaises(ValueError): cpio_entries(entry('TRAILER!!!')+b'x')

if __name__ == '__main__': unittest.main()
