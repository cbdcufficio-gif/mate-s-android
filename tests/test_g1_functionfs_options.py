"""Pinned Huawei parser; synthetic ID mapping, no kernel mount executed."""
import hashlib
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
class FunctionfsOptions(unittest.TestCase):
    @unittest.skipUnless(shutil.which('cc'), 'host C compiler required')
    def test_pinned_huawei_options_and_rejection_cases(self):
        fixture=ROOT/'tests/fixtures/huawei_ffs_parse_opts.c'
        self.assertEqual(hashlib.sha256(fixture.read_bytes()).hexdigest(), 'c9f1603a09ebf30ff44df05bf528f4e4cb2d43e738a529b4f93ce3785b61d724')
        body=fixture.read_text()
        harness=(ROOT/'tests/fixtures/huawei_ffs_opts_harness.c.in').read_text().replace('__PINNED_FUNCTION__',body)
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'options.c';binary=Path(directory)/'options'
            source.write_text(harness)
            subprocess.run(['cc','-Wall','-Wextra','-Werror',str(source),'-o',str(binary)],check=True,capture_output=True)
            subprocess.run([str(binary)],check=True,capture_output=True)
