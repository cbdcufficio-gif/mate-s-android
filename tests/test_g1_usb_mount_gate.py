"""Experimental sequencing and real host rejection; no successful USB mount."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(shutil.which('g++'),'host C++ compiler required')
class UsbMountGate(unittest.TestCase):
    def run_fixture(self,name,with_target=False):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory);binary=base/'fixture'
            subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',
                '-I',str(ROOT/'patches/experimental'),
                str(ROOT/'tests/fixtures'/name),'-o',str(binary)],
                check=True,capture_output=True)
            args=[str(binary)]
            if with_target:
                target=base/'target';target.mkdir();args.append(str(target))
            subprocess.run(args,check=True,capture_output=True,timeout=15)
    def test_all_fault_combinations_prevent_later_start(self):
        self.run_fixture('carrera_usb_prepare_gate.cpp')
    def test_real_host_rejects_missing_symlink_and_wrong_filesystem(self):
        self.run_fixture('carrera_functionfs_target.cpp',True)
    def test_mount_identity_snapshot_and_ambiguous_records(self):
        self.run_fixture('carrera_mount_identity.cpp')
    def test_alias_rejects_symlink_and_non_sysfs_without_writing(self):
        self.run_fixture('carrera_functionfs_alias.cpp',True)
