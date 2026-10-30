"""Run the unchanged Q property matching function against competing USB actions."""
import shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from g1_first_stage_probe import function
from g1_usb_ready_contract import load_fixtures
class UsbTriggerContract(unittest.TestCase):
    @unittest.skipUnless(shutil.which('g++'),'host C++ compiler required')
    def test_added_ready_action_does_not_override_generic_action(self):
        original=function(load_fixtures()['init/action.cpp'],'bool Action::CheckPropertyTriggers(')
        harness=(ROOT/'tests/fixtures/q_usb_init_trigger_harness.cpp.in').read_text().replace('__PINNED_CHECK_PROPERTY_TRIGGERS__',original)
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory);source=p/'trigger.cpp';binary=p/'trigger';source.write_text(harness)
            result=subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(source),'-o',str(binary)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            subprocess.run([str(binary)],check=True,capture_output=True)
