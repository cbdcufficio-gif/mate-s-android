import sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from g1_bootstrap_probe import Image,default_paths
from g1_contract_common import guard
from g1_usb_fixture import trigger_fixture
class G1Contracts(unittest.TestCase):
    def test_namespace_default_order_and_bitness(self):
        text='[other]\nnamespace.default.search.paths = /wrong\n[legacy]\nnamespace.default.search.paths = /system/${LIB}\nnamespace.default.search.paths += /vendor/${LIB}\n'
        self.assertEqual(default_paths(text,64),['/system/lib64','/vendor/lib64'])
        self.assertEqual(default_paths(text,32),['/system/lib','/vendor/lib'])
    def test_path_rejects_traversal_delimiters(self):
        image=Image(Path('/fake'),Path('/tmp'))
        for path in ['/../secret','/a;dump','/space file']:
            with self.assertRaises(ValueError):image.stat(path)
    def test_symlink_loop_and_apex_resolution(self):
        image=Image(Path('/fake'),Path('/tmp'))
        with patch.object(image,'link',side_effect=lambda p:'/b' if p=='/a' else '/a' if p=='/b' else None):
            with self.assertRaises(ValueError):image.canonical('/a',{})
        with patch.object(image,'link',return_value=None):
            self.assertEqual(image.canonical('/system/bin/../lib64/libc.so',{})[0],'/system/lib64/libc.so')
            self.assertEqual(image.canonical('/apex/com.android.runtime/lib64/libc.so',{'com.android.runtime':'com.android.runtime.release'})[0],'/system/apex/com.android.runtime.release/lib64/libc.so')
    def test_usb_generic_order_and_candidate_readiness(self):
        text='on property:sys.usb.config=adb && property:sys.usb.configfs=0\n    write /sys/class/android_usb/android0/enable 1\n    start adbd\non property:sys.usb.config=none && property:sys.usb.configfs=0\n    stop adbd\n    write /sys/class/android_usb/android0/enable 0\n'
        self.assertTrue(trigger_fixture(text)['generic_enables_before_adbd'])
        with self.assertRaises(AssertionError):trigger_fixture(text.replace('    write /sys/class/android_usb/android0/enable 1\n    start adbd','    start adbd\n    write /sys/class/android_usb/android0/enable 1'))
    def test_ci_guard_rejects_local(self):
        with patch.dict('os.environ',{},clear=True):
            with self.assertRaises(ValueError):guard()
