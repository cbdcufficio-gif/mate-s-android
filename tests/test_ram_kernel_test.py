from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from prepare_ram_kernel_test import pack,replace_kernel
from boot_inspect import inspect
from test_boot_inspect import image


class LocalKernelCandidate(unittest.TestCase):
    def original(self):
        fixture=image();info=inspect(fixture);r=info['components']['ramdisk']
        kernel=bytearray(128);kernel[56:60]=b'ARMd'
        struct.pack_into('<Q',kernel,8,0x680000)
        return pack(fixture[:2048],kernel,fixture[r['offset']:r['offset']+r['bytes']]),bytes(kernel)

    def test_roundtrip_and_changed_kernel_preserve_ramdisk(self):
        original,kernel=self.original()
        same,_=replace_kernel(original,kernel);self.assertEqual(same,original)
        modified=kernel+bytes(2048)
        candidate,meta=replace_kernel(original,modified)
        self.assertTrue(meta['legacy_sha1_id_matches'])
        self.assertEqual(meta['components']['kernel']['bytes'],len(modified))
        self.assertEqual(meta['components']['ramdisk']['sha256'],inspect(original)['components']['ramdisk']['sha256'])

    def test_unknown_tail_rejected(self):
        original,kernel=self.original()
        with self.assertRaisesRegex(ValueError,'tail'):replace_kernel(original+b'x',kernel)

    def test_different_kernel_offset_rejected(self):
        original,kernel=self.original();kernel=bytearray(kernel)
        struct.pack_into('<Q',kernel,8,0x80000)
        with self.assertRaisesRegex(ValueError,'ABI'):replace_kernel(original,kernel)

    def test_corrupt_source_id_rejected(self):
        original,kernel=self.original();original=bytearray(original);original[576]^=1
        with self.assertRaisesRegex(ValueError,'SHA1'):replace_kernel(original,kernel)
