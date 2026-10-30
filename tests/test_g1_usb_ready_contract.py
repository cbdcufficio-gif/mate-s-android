import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from g1_usb_ready_contract import inspect,load_fixtures
class UsbReadyContract(unittest.TestCase):
    def test_real_pinned_sources_have_early_ready_and_global_reset(self):
        result=inspect(load_fixtures());self.assertTrue(result['ready_written_before_bulk_endpoint_opens']);self.assertTrue(result['global_adbd_stopped_trigger_resets_ready']);self.assertFalse(result['legacy_none_action_resets_ready_explicitly'])
    def test_missing_stop_reset_is_rejected(self):
        f=load_fixtures();f['rootdir/init.usb.configfs.rc']=f['rootdir/init.usb.configfs.rc'].replace('on property:init.svc.adbd=stopped\n    setprop sys.usb.ffs.ready 0','on property:init.svc.adbd=stopped\n    setprop sys.usb.state none')
        with self.assertRaises(ValueError):inspect(f)
    def test_legacy_enable_after_start_is_detected(self):
        f=load_fixtures();s=f['rootdir/init.usb.rc'];a='    write /sys/class/android_usb/android0/enable 1\n    start adbd';self.assertIn(a,s);f['rootdir/init.usb.rc']=s.replace(a,'    start adbd\n    write /sys/class/android_usb/android0/enable 1',1)
        with self.assertRaises(ValueError):inspect(f)
