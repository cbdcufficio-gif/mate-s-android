"""Run the unchanged upstream decision function; policy/mount interfaces are stubs."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class SelinuxExecContract(unittest.TestCase):
    def test_pinned_function_digest(self):
        text = (ROOT/'tests/fixtures/selinux_nnp_nosuid.c').read_text()
        body = text[text.index('static int check_nnp_nosuid('):]
        metadata = json.loads((ROOT/'docs/G1-SELINUX-EXEC-SOURCES.json').read_text())
        self.assertEqual(hashlib.sha256(body.encode()).hexdigest(), metadata['function_sha256'])

    @unittest.skipUnless(shutil.which('cc'), 'host C compiler required')
    def test_permission_masks_fallbacks_and_errno(self):
        header = r'''
#include <assert.h>
#include <errno.h>
#include <stddef.h>
#include <stdio.h>
typedef unsigned int u32;
#define LSM_UNSAFE_NO_NEW_PRIVS 1
#define PROCESS2__NNP_TRANSITION 1
#define PROCESS2__NOSUID_TRANSITION 2
#define SECCLASS_PROCESS2 9
struct mount { int suid; };
struct file { struct { struct mount *mnt; } f_path; };
struct linux_binprm { int unsafe; struct file *file; };
struct task_security_struct { u32 sid; };
static int selinux_policycap_nnp_nosuid_transition;
static int allowed, bounded, av_calls, bound_calls;
static u32 requested;
static int mnt_may_suid(struct mount *m) { return m->suid; }
static int avc_has_perm(u32 old, u32 new, int cls, u32 av, void *audit) {
    assert(old == 10 && new == 20 && cls == SECCLASS_PROCESS2 && !audit);
    av_calls++; requested=av;
    return (av & ~allowed) ? -EACCES : 0;
}
static int security_bounded_transition(u32 old, u32 new) {
    assert(old == 10 && new == 20); bound_calls++;
    return bounded ? 0 : -EPERM;
}
'''
        main = r'''
int main(void) {
 int cases=0;
 for(int nnp=0;nnp<2;nnp++) for(int nosuid=0;nosuid<2;nosuid++)
 for(int same=0;same<2;same++) for(int cap=0;cap<2;cap++)
 for(int mask=0;mask<4;mask++) for(int bound=0;bound<2;bound++) {
    struct mount m={ !nosuid }; struct file f={ { &m } };
    struct linux_binprm b={ nnp, &f };
    struct task_security_struct old={10}, next={same?10:20};
    selinux_policycap_nnp_nosuid_transition=cap; allowed=mask; bounded=bound;
    av_calls=bound_calls=0; requested=0;
    int bypass=same || (!nnp && !nosuid);
    unsigned int needed=(nnp?1:0)|(nosuid?2:0);
    int policy_allow=cap && ((mask & needed)==needed);
    int expected=(bypass || policy_allow || bound)?0:(nnp?-EPERM:-EACCES);
    assert(check_nnp_nosuid(&b,&old,&next)==expected);
    assert(av_calls==(!bypass && cap));
    assert(bound_calls==(!bypass && !policy_allow));
    if(av_calls) assert(requested==needed);
    cases++;
 }
 printf("%d decision cases passed\n",cases);
 return 0;
}
'''
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory); source=p/'fixture.c'; binary=p/'fixture'
            source.write_text(header+(ROOT/'tests/fixtures/selinux_nnp_nosuid.c').read_text()+main)
            subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror',str(source),'-o',str(binary)],check=True,capture_output=True)
            result=subprocess.run([str(binary)],check=True,capture_output=True,text=True)
            self.assertEqual(result.stdout.strip(),'128 decision cases passed')

    @unittest.skipUnless(shutil.which('cc'), 'host C compiler required')
    def test_mount_namespace_restrictions(self):
        text = (ROOT/'tests/fixtures/selinux_mnt_may_suid.c').read_text()
        body = text[text.index('bool mnt_may_suid('):]
        meta = json.loads((ROOT/'docs/G1-SELINUX-EXEC-SOURCES.json').read_text())
        self.assertEqual(hashlib.sha256(body.encode()).hexdigest(), meta['mount_function_sha256'])
        header = r'''
#include <assert.h>
#include <stdbool.h>
#define MNT_NOSUID 2
struct super_block { int s_user_ns; };
struct vfsmount { unsigned int mnt_flags; struct super_block *mnt_sb; int ours; };
static struct vfsmount *real_mount(struct vfsmount *m) { return m; }
static int check_mnt(struct vfsmount *m) { return m->ours; }
static int current_in_userns(int ns) { return ns; }
'''
        main = r'''
int main(void) {
 for(int nosuid=0;nosuid<2;nosuid++) for(int ours=0;ours<2;ours++)
 for(int userns=0;userns<2;userns++) {
   struct super_block sb={userns};
   struct vfsmount m={nosuid?MNT_NOSUID:0,&sb,ours};
   assert(mnt_may_suid(&m)==(!nosuid && ours && userns));
   if(!nosuid && (!ours || !userns)) assert(!(m.mnt_flags & MNT_NOSUID));
 }
 return 0;
}
'''
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory); source=p/'mount.c'; binary=p/'mount'
            source.write_text(header+text+main)
            subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror',str(source),'-o',str(binary)],check=True,capture_output=True)
            subprocess.run([str(binary)],check=True,capture_output=True)
