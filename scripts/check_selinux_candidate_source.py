#!/usr/bin/env python3
"""Check the draft against pinned public source; never touch a kernel checkout."""
import hashlib,json,subprocess,tempfile,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
META=json.loads((ROOT/'docs/G1-SELINUX-CANDIDATE-SOURCES.json').read_text())
PATCH=ROOT/'patches/experimental/selinux-nnp-nosuid-candidate.patch'
BASE='https://raw.githubusercontent.com/hi3635-dev/android_kernel_huawei_liszt/'+META['kernel_commit']+'/'

def functions(text):
    a=text.index('static bool carrera_mnt_may_suid(')
    b=text.index('\nstatic int selinux_bprm_secureexec(',a)
    return text[a:b].rstrip()

def main():
    with tempfile.TemporaryDirectory() as directory:
        p=Path(directory)
        for name,digest in META['original_sha256'].items():
            with urllib.request.urlopen(BASE+name,timeout=30) as response:
                data=response.read(2*1024*1024+1)
            if len(data)>2*1024*1024 or hashlib.sha256(data).hexdigest()!=digest:
                raise ValueError('Pinned source digest mismatch: '+name)
            target=p/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        subprocess.run(['git','apply','--check',str(PATCH)],cwd=p,check=True)
        subprocess.run(['git','apply',str(PATCH)],cwd=p,check=True)
        source=(p/'security/selinux/hooks.c').read_text()
        harness=(ROOT/'tests/fixtures/selinux_huawei_candidate_harness.c').read_text()
        a=harness.index('static bool carrera_mnt_may_suid(')
        b=harness.index('\nstatic int run_case(',a)
        if functions(source)!=harness[a:b].rstrip():
            raise ValueError('Tested candidate hooks do not match actual applied patch')
        print('Pinned source checksums, patch application, and exact candidate hook correspondence passed; no kernel build or runtime test.')
if __name__=='__main__':main()
