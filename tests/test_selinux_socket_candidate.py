"""Host-only proposed socket class selection; networking and policy are stubs."""
import shutil,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class SocketCandidate(unittest.TestCase):
    @unittest.skipUnless(shutil.which('cc'),'host C compiler required')
    def test_family_protocol_and_capability_paths(self):
        source=ROOT/'tests/fixtures/selinux_huawei_socket_candidate_harness.c'
        with tempfile.TemporaryDirectory() as directory:
            binary=Path(directory)/'socket'
            compiled=subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror',str(source),'-o',str(binary)],capture_output=True,text=True)
            self.assertEqual(compiled.returncode,0,compiled.stderr)
            subprocess.run([str(binary)],check=True,capture_output=True)
