"""Host-only candidate exec path; policy and target kernel are not exercised."""
import shutil,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class IntegratedCandidate(unittest.TestCase):
    @unittest.skipUnless(shutil.which('cc'),'host C compiler required')
    def test_candidate_exec_contract_and_capability_failure(self):
        source=(ROOT/'tests/fixtures/selinux_huawei_candidate_harness.c').read_text()
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory);s=p/'candidate.c';b=p/'candidate';s.write_text(source)
            subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror',str(s),'-o',str(b)],check=True,capture_output=True)
            subprocess.run([str(b)],check=True,capture_output=True)
    @unittest.skipUnless(shutil.which('cc'),'host C compiler required')
    def test_user_namespace_fails_closed(self):
        source=(ROOT/'tests/fixtures/selinux_huawei_candidate_harness.c').read_text()
        source=source[:source.index('int main(void) {')]+'''int main(void) {
 struct vfsmount m={0,1}; assert(!carrera_mnt_may_suid(&m)); return 0;
}
'''
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory);s=p/'candidate.c';b=p/'candidate';s.write_text(source)
            subprocess.run(['cc','-std=c99','-DCONFIG_USER_NS','-Wall','-Wextra','-Werror','-Wno-unused-function',str(s),'-o',str(b)],check=True,capture_output=True)
            subprocess.run([str(b)],check=True,capture_output=True)
