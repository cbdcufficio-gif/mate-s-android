"""Compile original Huawei genheaders and compare baseline to candidate classmap."""
import hashlib,json,re,shutil,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class GenheadersContract(unittest.TestCase):
    @unittest.skipUnless(shutil.which('cc'),'host C compiler required')
    def test_original_generator_with_candidate_process2(self):
        src=ROOT/'tests/fixtures/selinux-genheaders'
        meta=json.loads((ROOT/'docs/G1-SELINUX-EXEC-SOURCES.json').read_text())['huawei_genheaders_sources_sha256']
        for name,digest in meta.items(): self.assertEqual(hashlib.sha256((src/name).read_bytes()).hexdigest(),digest)
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)
            for name in meta: shutil.copyfile(src/name,p/name)
            subprocess.run(['cc','-std=gnu99',str(p/'genheaders.c'),'-o',str(p/'genheaders')],check=True,capture_output=True)
            subprocess.run([str(p/'genheaders'),str(p/'flask.h'),str(p/'perms.h')],check=True,capture_output=True)
            baseline=(p/'flask.h').read_text();perms=(p/'perms.h').read_text()
            self.assertNotIn('SECCLASS_PROCESS2',baseline);self.assertNotIn('PROCESS2__',perms)
            source=(src/'classmap.h').read_text(); sentinel='\t{ NULL }'
            self.assertEqual(source.count(sentinel),1)
            candidate=source.replace(sentinel,'\t{ "process2", { "nnp_transition", "nosuid_transition", NULL } },\n'+sentinel)
            (p/'classmap.h').write_text(candidate)
            subprocess.run(['cc','-std=gnu99',str(p/'genheaders.c'),'-o',str(p/'genheaders')],check=True,capture_output=True)
            subprocess.run([str(p/'genheaders'),str(p/'flask.h'),str(p/'perms.h')],check=True,capture_output=True)
            flask=(p/'flask.h').read_text();perms2=(p/'perms.h').read_text()
            def defines(s): return dict(re.findall(r'^#define\s+(\w+)\s+(0x[0-9a-fA-F]+UL|\d+)$',s,re.M))
            old=defines(baseline);new=defines(flask);oldperm=defines(perms);newperm=defines(perms2)
            for key in old:self.assertEqual(new[key],old[key],key)
            for key in oldperm:self.assertEqual(newperm[key],oldperm[key],key)
            self.assertEqual(int(new['SECCLASS_PROCESS2']), 51)
            self.assertEqual(int(newperm['PROCESS2__NNP_TRANSITION'][:-2],16),1)
            self.assertEqual(int(newperm['PROCESS2__NOSUID_TRANSITION'][:-2],16),2)
