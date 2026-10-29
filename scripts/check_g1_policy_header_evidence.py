#!/usr/bin/env python3
"""Recheck small immutable public G0 policy evidence on the disposable runner."""
import hashlib,json,subprocess,tempfile
from pathlib import Path
from g1_selinux_policy_header import inspect_g0
from g1_policy_classes import parse_setools
ROOT=Path(__file__).resolve().parents[1]
REPO='cbdcufficio-gif/mate-s-android'
COMMON_SHA='cf61edd3da0e9912c0b451e57ad8a6c2bfb86bbb0c3024e33b62f47be6680d89'

def main():
    with tempfile.TemporaryDirectory() as directory:
        p=Path(directory)
        for tag,name in [('carrera-g1-bootstrap-40869967507','g0-sepolicy'),('carrera-g1-captured-review-40871087407','policy-common.txt')]:
            subprocess.run(['gh','release','download',tag,'--repo',REPO,'--pattern',name,'--dir',str(p)],check=True,timeout=120)
        result=inspect_g0((p/'g0-sepolicy').read_bytes())
        common=(p/'policy-common.txt').read_bytes()
        if hashlib.sha256(common).hexdigest()!=COMMON_SHA:raise ValueError('Policy common evidence digest mismatch')
        perms=parse_setools(common.decode(),'common')['socket']['permissions']
        expected=json.loads((ROOT/'docs/G1-SELINUX-G0-HEADER-RESULT.json').read_text())
        if result['header']!=expected['header'] or result['policy_sha256']!=expected['policy_sha256']:raise ValueError('Policy header differs from evidence')
        for key in ('recv_msg','send_msg'):
            if (key in perms)!=expected['socket_common_has_'+key]:raise ValueError('Socket common evidence mismatch')
        print(json.dumps({'status':'PUBLIC_G0_POLICY_HEADER_BYTES_VERIFIED','policy_sha256':result['policy_sha256'],'header':result['header'],'socket_common_sha256':COMMON_SHA,'runtime_policy_loaded':False},indent=2))
if __name__=='__main__':main()
