from pathlib import Path
import unittest
import os
import sys
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
        for row in rows:
            self.assertFalse(any(x.startswith(('formattable','forceencrypt','fileencryption','resize')) for x in row[4].split(',')))
        self.assertIn('ro',next(r for r in rows if r[1]=='/system')[3].split(','))
    def test_init_has_only_the_reviewed_mount_action(self):
        self.assertEqual(entries(DEVICE/'rootdir/init.hi3635.rc'),[['on','fs'],['mount_all','/fstab.hi3635']])
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

if __name__=='__main__':unittest.main()
