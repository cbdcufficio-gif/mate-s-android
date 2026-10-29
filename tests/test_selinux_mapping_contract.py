"""Exercise unchanged Huawei mapping and decisions using a synthetic process2 policy."""
import hashlib,json,shutil,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class MappingContract(unittest.TestCase):
    @unittest.skipUnless(shutil.which('cc'),'host C compiler required')
    def test_name_to_policy_value_and_unknowns(self):
        fixture=(ROOT/'tests/fixtures/selinux_huawei_mapping.c').read_text()
        body=fixture[fixture.index('static int selinux_set_mapping('):]
        meta=json.loads((ROOT/'docs/G1-SELINUX-EXEC-SOURCES.json').read_text())
        self.assertEqual(hashlib.sha256(body.encode()).hexdigest(),meta['huawei_mapping_functions_sha256'])
        harness=(ROOT/'tests/fixtures/selinux_mapping_harness.c.in').read_text().replace('/*FUNCTIONS*/',fixture)
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory);source=p/'mapping.c';binary=p/'mapping';source.write_text(harness)
            compiled=subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-Wno-address',str(source),'-o',str(binary)],capture_output=True,text=True)
            self.assertEqual(compiled.returncode,0,compiled.stderr)
            subprocess.run([str(binary)],check=True,capture_output=True)
