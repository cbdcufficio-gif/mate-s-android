"""Use real ext4 fixture bytes, not mocked debugfs path results."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import android_carrera_system_probe as probe

PUBLIC_MODULE_PATHS = [
    "system/lib/libutilscallstack.so",
    "system/lib64/libutilscallstack.so",
    "system/vendor/bin/hw/android.hardware.graphics.allocator@2.0-service",
    "system/vendor/bin/hw/android.hardware.graphics.composer@2.1-service",
    "system/vendor/lib/hw/android.hardware.graphics.allocator@2.0-impl.so",
    "system/vendor/lib/hw/android.hardware.graphics.composer@2.1-impl.so",
    "system/vendor/lib/hw/android.hardware.graphics.mapper@2.0-impl.so",
    "system/vendor/lib/libhwc2on1adapter.so",
    "system/vendor/lib/libhwc2onfbadapter.so",
    "system/vendor/lib64/hw/android.hardware.graphics.allocator@2.0-impl.so",
    "system/vendor/lib64/hw/android.hardware.graphics.composer@2.1-impl.so",
    "system/vendor/lib64/hw/android.hardware.graphics.mapper@2.0-impl.so",
    "system/vendor/lib64/libhwc2on1adapter.so",
    "system/vendor/lib64/libhwc2onfbadapter.so"
]

@unittest.skipUnless(shutil.which('mke2fs') and shutil.which('debugfs'),'requires ext4 host tools')
class SystemFilesystemLayouts(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)
        self.tree=self.base/'tree'
        self.tree.mkdir()
        self.work=self.base/'work'
        self.work.mkdir()
        patcher=patch.object(probe,'ROOT',self.work)
        patcher.start()
        self.addCleanup(patcher.stop)
    def fixture(self,layout):
        prefix=self.tree/'system' if layout=='q-root-with-system' else self.tree
        modules=[]
        for rel,payload in (('lib/libpublic.so',b'public ARM32 fixture'),
                            ('vendor/lib64/libpublic.so',b'public ARM64 fixture')):
            path=prefix/rel
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(payload)
            modules.append({'path':'system/'+rel,'sha256':hashlib.sha256(payload).hexdigest()})
        return modules
    def image(self):
        path=self.base/'system.img'
        with path.open('wb') as stream:stream.truncate(16*1024**2)
        subprocess.run(['mke2fs','-q','-F','-t','ext4','-d',str(self.tree),str(path)],
                       check=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        return path
    def test_legacy_paths_verify_actual_bytes(self):
        modules=self.fixture('legacy-system-root')
        report=probe.verify_modules_in_system_image(self.base,self.image(),modules)
        self.assertEqual(report['modules_verified'],2)
        self.assertEqual(report['layout_evidence']['layout'],'legacy-system-root')
        self.assertEqual(report['modules'][1]['path'],'/vendor/lib64/libpublic.so')
    def test_pinned_q_nested_system_paths_verify_actual_bytes(self):
        modules=self.fixture('q-root-with-system')
        report=probe.verify_modules_in_system_image(self.base,self.image(),modules)
        self.assertEqual(report['modules_verified'],2)
        self.assertEqual(report['layout_evidence']['layout'],'q-root-with-system')
        self.assertEqual(report['modules'][1]['path'],'/system/vendor/lib64/libpublic.so')
        self.assertFalse(report['layout_evidence']['runtime_mounts_verified'])
    def test_wrong_digest_still_rejected_in_nested_layout(self):
        modules=self.fixture('q-root-with-system')
        modules[0]['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'hash differs'):
            probe.verify_modules_in_system_image(self.base,self.image(),modules)
    def test_missing_file_still_rejected_in_nested_layout(self):
        modules=self.fixture('q-root-with-system')
        (self.tree/'system/lib/libpublic.so').unlink()
        with self.assertRaisesRegex(ValueError,'missing from system ext4'):
            probe.verify_modules_in_system_image(self.base,self.image(),modules)
    def test_ambiguous_dual_layout_rejected(self):
        modules=self.fixture('q-root-with-system')
        (self.tree/'lib').mkdir()
        with self.assertRaisesRegex(ValueError,'Ambiguous'):
            probe.verify_modules_in_system_image(self.base,self.image(),modules)
    def test_system_symlink_rejected(self):
        modules=self.fixture('legacy-system-root')
        os.symlink('lib',self.tree/'system')
        with self.assertRaisesRegex(ValueError,'Ambiguous'):
            probe.verify_modules_in_system_image(self.base,self.image(),modules)
    def test_unknown_filesystem_layout_rejected(self):
        with self.assertRaisesRegex(ValueError,'Ambiguous'):
            probe.verify_modules_in_system_image(self.base,self.image(),[])
    def test_vendor_guard_remains_required(self):
        modules=self.fixture('q-root-with-system')
        with self.assertRaisesRegex(ValueError,'No public vendor module'):
            probe.verify_modules_in_system_image(self.base,self.image(),modules[:1])


    def public_inventory_fixture(self,layout):
        modules=[]
        for staged in PUBLIC_MODULE_PATHS:
            relative=staged if layout=='q-root-with-system' else staged.removeprefix('system/')
            path=self.tree/relative
            path.parent.mkdir(parents=True,exist_ok=True)
            payload=('Public synthetic fixture for '+staged).encode()
            path.write_bytes(payload)
            modules.append({'path':staged,'sha256':hashlib.sha256(payload).hexdigest()})
        return modules
    def test_all_production_module_names_in_real_ext4_both_layouts(self):
        for layout in ('legacy-system-root','q-root-with-system'):
            with self.subTest(layout=layout):
                shutil.rmtree(self.tree)
                self.tree.mkdir()
                modules=self.public_inventory_fixture(layout)
                report=probe.verify_modules_in_system_image(self.base,self.image(),modules)
                self.assertEqual(report['modules_verified'],14)
                self.assertEqual(report['layout_evidence']['layout'],layout)
                self.assertEqual({x['sha256'] for x in report['modules']},
                                 {x['sha256'] for x in modules})
                self.assertTrue(any('@2.0-service' in x['path'] for x in report['modules']))
    def test_versioned_hidl_service_digest_mismatch_rejected(self):
        modules=self.public_inventory_fixture('q-root-with-system')
        modules[2]['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'hash differs'):
            probe.verify_modules_in_system_image(self.base,self.image(),modules)

class ImagePathGuards(unittest.TestCase):
    def test_safe_mapping_is_explicit_for_both_layouts(self):
        self.assertEqual(probe.system_image_path('system/lib/libx.so','q-root-with-system'),
                         '/system/lib/libx.so')
        self.assertEqual(probe.system_image_path('system/lib/libx.so','legacy-system-root'),
                         '/lib/libx.so')
        for path in ('system/../libx.so','/system/libx.so','system/lib/a;quit.so', 'system/vendor/bin/hw/a@2.0 service',
                     'system/vendor/bin/hw/a@2.0'+chr(10)+'quit', 'system/lib/a\".so',
                     'system/lib/a\\\\.so', 'system/lib/a$(quit).so', 'system/lib/a*.so'):
            with self.assertRaises(ValueError):
                probe.system_image_path(path,'q-root-with-system')
        with self.assertRaisesRegex(ValueError,'Unsupported'):
            probe.system_image_path('system/lib/libx.so','unknown')

if __name__=='__main__':unittest.main()
