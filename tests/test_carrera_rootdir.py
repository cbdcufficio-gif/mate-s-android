from pathlib import Path
import unittest
import os
import sys
import tempfile
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
DEVICE=ROOT/'device/huawei/carrera'

def entries(path):
    return [l.split() for l in path.read_text().splitlines() if l.strip() and not l.lstrip().startswith('#')]

class CarreraRootdirContract(unittest.TestCase):
    def test_observed_partition_mapping_and_mounts(self):
        rows=entries(DEVICE/'rootdir/fstab.hi3635')
        self.assertTrue(all(len(r)==5 for r in rows))
        actual={r[1]:(r[0].rsplit('/',1)[-1],r[2]) for r in rows}
        self.assertEqual(actual,{'/system':('system','ext4'),'/cache':('cache','ext4'),'/data':('userdata','ext4')})
        self.assertTrue(all(r[0].startswith('/dev/block/platform/hi_mci.0/by-name/') for r in rows))
    def test_preserves_legacy_encryption_without_autoformat(self):
        rows=entries(DEVICE/'rootdir/fstab.hi3635')
        data=next(r for r in rows if r[1]=='/data')
        self.assertIn('encryptable=footer',data[4].split(','))
        self.assertIn('latemount',data[4].split(','))
        for row in rows:
            self.assertFalse(any(x.startswith(('formattable','forceencrypt','fileencryption','resize')) for x in row[4].split(',')))
        self.assertIn('ro',next(r for r in rows if r[1]=='/system')[3].split(','))
    def test_mounts_system_early_and_userdata_late(self):
        rows=entries(DEVICE/'rootdir/fstab.hi3635')
        flags={r[1]:set(r[4].split(',')) for r in rows}
        self.assertNotIn('latemount',flags['/system'])
        self.assertNotIn('latemount',flags['/cache'])
        self.assertIn('latemount',flags['/data'])
        actions=entries(DEVICE/'rootdir/init.hi3635.rc')
        self.assertEqual(actions,[
            ['on','fs'],['mount_all','/fstab.hi3635','--early'],
            ['on','late-fs'],['mount_all','/fstab.hi3635','--late']])
    def test_separate_system_layout_is_not_switched_to_system_as_root(self):
        board=(DEVICE/'BoardConfig.mk').read_text()
        self.assertIn('BOARD_BUILD_SYSTEM_ROOT_IMAGE := false',board)
        system=next(r for r in entries(DEVICE/'rootdir/fstab.hi3635') if r[1]=='/system')
        self.assertNotIn('first_stage_mount',system[4].split(','))
        self.assertIn('TARGET_COPY_OUT_VENDOR := system/vendor',board)
    def test_public_system_probe_requires_legacy_vendor_symlink(self):
        sys.path.insert(0,str(ROOT/'scripts'))
        from android_carrera_system_probe import verify_legacy_vendor_link,system_image_path
        self.assertEqual(system_image_path('system/vendor/lib64/libcomposer.so'),
                         '/vendor/lib64/libcomposer.so')
        for unsafe in ('vendor/lib/libx.so','system/../outside.so','/system/lib/libx.so',
                       'system/vendor/lib64/a;quit.so'):
            with self.assertRaises(ValueError):system_image_path(unsafe)
        with tempfile.TemporaryDirectory() as tmp:
            product=Path(tmp);(product/'root').mkdir()
            os.symlink('/system/vendor',product/'root'/'vendor')
            self.assertEqual(verify_legacy_vendor_link(product),
                             {'path':'root/vendor','target':'/system/vendor'})
            (product/'root'/'vendor').unlink()
            os.symlink('/wrong/vendor',product/'root'/'vendor')
            with self.assertRaisesRegex(ValueError,'Unexpected legacy'):
                verify_legacy_vendor_link(product)
            (product/'root'/'vendor').unlink()
            with self.assertRaisesRegex(ValueError,'missing'):
                verify_legacy_vendor_link(product)
    def test_hardware_permission_metadata(self):
        actual={r[0]:r[1:] for r in entries(DEVICE/'rootdir/ueventd.hi3635.rc')}
        for name in ('binder','hwbinder','vndbinder'):
            self.assertEqual(actual['/dev/'+name],['0666','root','root'])
        self.assertEqual(actual['/dev/ion'],['0664','system','system'])
        self.assertEqual(actual['/dev/mali0'],['0666','system','system'])
        self.assertEqual(actual['/dev/graphics/fb2'],['0660','system','system'])
    def test_root_copy_destinations_match_hardware(self):
        s=(DEVICE/'device.mk').read_text()
        for name in ('fstab.hi3635','init.hi3635.rc','ueventd.hi3635.rc'):
            self.assertIn('$(DEVICE_PATH)/rootdir/'+name+':root/'+name,s)
            self.assertIn('$(DEVICE_PATH)/rootdir/'+name+':$(TARGET_COPY_OUT_RAMDISK)/'+name,s)


class PublicProbeIsolation(unittest.TestCase):
    def test_normal_product_still_requires_huawei_inputs(self):
        s=(DEVICE/'device.mk').read_text()
        expected='ifneq ($(TARGET_PRODUCT),lineage_carrera_public)\n$(call inherit-product, vendor/huawei/carrera-graphics/carrera-graphics.mk)\nendif'
        self.assertIn(expected,s)
    def test_public_product_is_explicit_and_not_default(self):
        p=(DEVICE/'lineage_carrera_public.mk').read_text()
        self.assertIn('PRODUCT_NAME := lineage_carrera_public',p)
        self.assertIn('device/huawei/carrera/lineage_carrera.mk',p)
        self.assertIn('lineage_carrera-userdebug',(DEVICE/'AndroidProducts.mk').read_text())

    def test_probe_refuses_local_android_download(self):
        sys.path.insert(0,str(ROOT/'scripts'))
        from android_carrera_probe import main
        with patch.dict(os.environ,{'GITHUB_ACTIONS':'false'}):
            with self.assertRaises(SystemExit): main()

    def test_system_probe_refuses_local_android_download(self):
        sys.path.insert(0,str(ROOT/'scripts'))
        from android_carrera_system_probe import main
        with patch.dict(os.environ,{'GITHUB_ACTIONS':'false'}):
            with self.assertRaises(SystemExit): main()

if __name__=='__main__':unittest.main()
