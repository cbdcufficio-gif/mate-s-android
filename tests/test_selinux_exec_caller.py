"""Unchanged upstream exec caller and helper with explicit kernel-interface stubs."""
import hashlib,json,shutil,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ExecCaller(unittest.TestCase):
    @unittest.skipUnless(shutil.which('cc'),'host C compiler required')
    def test_explicit_automatic_fallback_and_remaining_permissions(self):
        caller=(ROOT/'tests/fixtures/selinux_exec_caller.c').read_text()
        meta=json.loads((ROOT/'docs/G1-SELINUX-EXEC-SOURCES.json').read_text())
        body=caller[caller.index('static int selinux_bprm_set_creds('):]
        self.assertEqual(hashlib.sha256(body.encode()).hexdigest(),meta['exec_caller_function_sha256'])
        helper=(ROOT/'tests/fixtures/selinux_nnp_nosuid.c').read_text()
        harness=(ROOT/'tests/fixtures/selinux_exec_caller_harness.c.in').read_text()
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory);source=p/'caller.c';binary=p/'caller'
            source.write_text(harness.replace('/*HELPER*/',helper).replace('/*CALLER*/',caller))
            subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror',str(source),'-o',str(binary)],check=True,capture_output=True)
            subprocess.run([str(binary)],check=True,capture_output=True)
