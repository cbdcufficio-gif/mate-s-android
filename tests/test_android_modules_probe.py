import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from android_modules_probe import inventory, main, REQUIRED

class ModuleEvidence(unittest.TestCase):
    def test_no_local_sync(self):
        with patch.dict(os.environ,{'GITHUB_ACTIONS':'false'}):
            with self.assertRaises(SystemExit): main()
    def test_missing_outputs_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,'missing'): inventory(Path(d))
    def test_symlinks_do_not_count_as_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'target').write_bytes(b'not ELF')
            for name in REQUIRED:(root/name).symlink_to(root/'target')
            with self.assertRaisesRegex(ValueError,'missing'): inventory(root)

if __name__=='__main__':unittest.main()
