import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from android_system_probe import image_metadata, main

class SystemImageEvidence(unittest.TestCase):
    def test_local_build_refused(self):
        with patch.dict(os.environ,{'GITHUB_ACTIONS':'false'}):
            with self.assertRaises(SystemExit): main()
    def test_truncated_image_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'system.img';p.write_bytes(b'bad')
            with self.assertRaises(ValueError): image_metadata(p)
    def test_sparse_geometry_is_not_assumed_to_fit_phone(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'system.img'
            p.write_bytes(struct.pack('<IHHHHIIII',0xed26ff3a,1,0,28,12,4096,1000000,1,0))
            r=image_metadata(p)
            self.assertEqual(r['expanded_bytes'],4096000000)
            self.assertFalse(r['fits_carrera_system_partition'])
    def test_invalid_sparse_header_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'system.img'
            p.write_bytes(struct.pack('<IHHHHIIII',0xed26ff3a,1,0,28,12,0,100,1,0))
            with self.assertRaises(ValueError):image_metadata(p)

if __name__=='__main__':unittest.main()
