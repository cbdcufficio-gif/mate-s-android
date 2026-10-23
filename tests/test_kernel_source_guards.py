import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import build_kernel


class ReviewedKernelSources(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.project=self.root/'project';self.source=self.root/'source'
        (self.project/'patches/kernel').mkdir(parents=True)
        (self.project/'configs').mkdir()
        self.source.mkdir()
        self.immersion='drivers/huawei_platform/immersion/tspdrv.c'
        self.immersion_diff='reviewed immersion diff\n'
        (self.project/'patches/kernel/0001-fix-immersion-header-path.patch').write_text(self.immersion_diff)
        patchfile=self.project/'patches/kernel/touch.patch';patchfile.write_text('reviewed touch patch\n')
        self.paths=['drivers/huawei_platform/touthscreen/Kconfig','drivers/huawei_platform/touthscreen/huawei_touchscreen.c']
        rows=[]
        for path in self.paths:
            f=self.source/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_text('reviewed '+path)
            rows.append({'path':path,'after_sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
        (self.project/'configs/kernel-touch-update.json').write_text(json.dumps({
            'patch':str(patchfile.relative_to(self.project)),
            'patch_sha256':hashlib.sha256(patchfile.read_bytes()).hexdigest(),'files':rows}))
        self.changed=[self.immersion,*self.paths]
        def git(argv,**kwargs):
            return '\n'.join(self.changed) if '--name-only' in argv else self.immersion_diff
        self.patches=[patch.object(build_kernel,'PROJECT',self.project),
                      patch.object(build_kernel.subprocess,'check_output',side_effect=git)]
        for p in self.patches:p.start();self.addCleanup(p.stop)

    def test_exact_reviewed_changes_accepted(self):
        self.assertEqual(len(build_kernel.verify_source_changes(self.source)['files']),2)

    def test_extra_tracked_change_rejected(self):
        self.changed.append('drivers/android/binder.c')
        with self.assertRaisesRegex(ValueError,'patch paths'):
            build_kernel.verify_source_changes(self.source)

    def test_touchscreen_body_tamper_rejected(self):
        (self.source/self.paths[1]).write_text('unreviewed source')
        with self.assertRaisesRegex(ValueError,'Touchscreen source'):
            build_kernel.verify_source_changes(self.source)

    def test_patch_tamper_rejected(self):
        (self.project/'patches/kernel/touch.patch').write_text('other patch')
        with self.assertRaisesRegex(ValueError,'patch checksum'):
            build_kernel.verify_source_changes(self.source)

    def test_source_symlink_rejected(self):
        f=self.source/self.paths[1];data=f.read_bytes();f.unlink()
        other=self.root/'other';other.write_bytes(data);f.symlink_to(other)
        with self.assertRaisesRegex(ValueError,'Touchscreen source'):
            build_kernel.verify_source_changes(self.source)
