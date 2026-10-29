"""Unchanged loaders: ABI positions, all transitions, and removal on reload."""
import hashlib,json,shutil,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class PolicycapReload(unittest.TestCase):
    @unittest.skipUnless(shutil.which('cc'),'host C compiler required')
    def test_original_loaders_exhaustive_reload(self):
        meta=json.loads((ROOT/'docs/G1-SELINUX-EXEC-SOURCES.json').read_text())
        for label,width in [('huawei',2),('upstream',6)]:
            with self.subTest(source=label):
                loader=(ROOT/f'tests/fixtures/selinux_{label}_policycaps.c').read_text()
                body=loader[loader.index('static void security_load_policycaps(void)'):]
                self.assertEqual(hashlib.sha256(body.encode()).hexdigest(),meta[label+'_policycaps_function_sha256'])
                enum=(ROOT/f'tests/fixtures/selinux_{label}_policycap_enum.h').read_text()
                self.assertEqual(hashlib.sha256(enum[enum.index('enum {'):].encode()).hexdigest(),meta[label+'_policycap_enum_sha256'])
                header=r'''
#include <assert.h>
#include <stddef.h>
#define ARRAY_SIZE(a) (sizeof(a)/sizeof((a)[0]))
#define pr_info(...) ((void)0)
struct ebitmap_node { int unused; };
struct ebitmap { unsigned int bits; };
static struct { struct ebitmap policycaps; } policydb;
static int ebitmap_get_bit(struct ebitmap *b, unsigned int i) { return (b->bits>>i)&1; }
#define ebitmap_for_each_positive_bit(map,node,i) for((node)=NULL,(void)(node),(i)=0;(i)<8;(i)++) if(ebitmap_get_bit((map),(i)))
static int selinux_policycap_netpeer,selinux_policycap_openperm;
'''
                if label=='upstream':
                    header+='static int selinux_policycap_extsockclass,selinux_policycap_alwaysnetwork,selinux_policycap_cgroupseclabel,selinux_policycap_nnp_nosuid_transition;\nstatic const char *selinux_policycap_names[6];\n'
                variables=['netpeer','openperm']+(['extsockclass','alwaysnetwork','cgroupseclabel','nnp_nosuid_transition'] if width==6 else [])
                checks=''.join(f'assert(selinux_policycap_{name}==(int)((after>>{i})&1));' for i,name in enumerate(variables))
                main='int main(void) { assert(POLICYDB_CAPABILITY_NETPEER==0 && POLICYDB_CAPABILITY_OPENPERM==1);'
                if width==6:main+='assert(POLICYDB_CAPABILITY_EXTSOCKCLASS==2 && POLICYDB_CAPABILITY_ALWAYSNETWORK==3 && POLICYDB_CAPABILITY_CGROUPSECLABEL==4 && POLICYDB_CAPABILITY_NNP_NOSUID_TRANSITION==5);'
                main+='for(unsigned int before=0;before<256;before++) for(unsigned int after=0;after<256;after++) { policydb.policycaps.bits=before;security_load_policycaps();policydb.policycaps.bits=after;security_load_policycaps();'+checks+'} return 0;}'
                with tempfile.TemporaryDirectory() as directory:
                    p=Path(directory);s=p/'reload.c';b=p/'reload';s.write_text(header+enum+loader+main)
                    compiled=subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror',str(s),'-o',str(b)],capture_output=True,text=True)
                    self.assertEqual(compiled.returncode,0,compiled.stderr)
                    subprocess.run([str(b)],check=True,capture_output=True)
