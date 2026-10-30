import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from g1_usb_legacy_candidate import patched_candidate,verify,ENABLE
class UsbLegacyCandidate(unittest.TestCase):
    def test_only_ready_action_changes(self):
        old,new=patched_candidate();r=verify(old,new);self.assertTrue(r['unrelated_actions_unchanged']);self.assertFalse(r['runtime_usb_verified'])
    def test_unrelated_action_change_is_rejected(self):
        old,new=patched_candidate();changed=new.replace('idProduct 2d00','idProduct 2d99',1);self.assertNotEqual(new,changed)
        with self.assertRaises(ValueError):verify(old,changed)
    def test_ready_enable_removed_is_rejected(self):
        old,new=patched_candidate();where=new.index('on property:sys.usb.ffs.ready=1 && property:sys.usb.config=adb');changed=new[:where]+new[where:].replace(ENABLE,'write /sys/class/android_usb/android0/enable 0',1)
        with self.assertRaises(ValueError):verify(old,changed)
