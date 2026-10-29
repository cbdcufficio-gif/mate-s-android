#!/usr/bin/env python3
"""Review small captured public evidence only; no Android image or kernel clone."""
import json,os,re,subprocess,urllib.request
from pathlib import Path
from g1_contract_common import ROOT,guard,api,sha,suite,publish
from g1_elf_versions import compare as version_compare
from g1_policy_classes import compare as policy_compare

def get_evidence(tag,out):
    release=api('releases/tags/'+tag);out.mkdir()
    assets=release['assets'];names={a['name'] for a in assets}
    if len(names)!=len(assets) or not all(re.fullmatch('[A-Za-z0-9_.-]+',name) for name in names):raise ValueError('Unsafe evidence names')
    if sum(x['size'] for x in assets)>16*1024**2:raise ValueError('Small evidence limit exceeded')
    subprocess.run(['gh','release','download',tag,'--repo',os.environ['GITHUB_REPOSITORY'],'--dir',str(out)],check=True,timeout=120)
    sums=dict((name,digest) for digest,name in (x.split('  ',1) for x in (out/'SHA256SUMS').read_text().splitlines()))
    if set(sums)!=names-{'SHA256SUMS'}:raise ValueError('Incomplete evidence checksum coverage')
    for a in assets:
        file=out/a['name']
        if file.is_symlink() or file.stat().st_size!=a['size']:raise ValueError('Asset changed')
        if file.name in sums and sha(file.read_bytes())!=sums[file.name]:raise ValueError('Evidence digest mismatch')
    return release

def main():
    guard();os.chdir(ROOT);subprocess.run(['sha256sum','-c','SHA256SUMS'],check=True)
    out=ROOT/'out/g1-captured-review';out.mkdir(parents=True,exist_ok=False);evidence=out/'evidence';evidence.mkdir()
    br=get_evidence('carrera-g1-bootstrap-40869967507',out/'bootstrap');kr=get_evidence('carrera-g1-kernel-policy-40870457480',out/'kernel')
    bootstrap=json.loads((out/'bootstrap/g1-bootstrap.json').read_text());kernel=json.loads((out/'kernel/g1-kernel-policy.json').read_text())
    for j,r,id in [(bootstrap,br,40869967507),(kernel,kr,40870457480)]:
        run=api('actions/runs/'+str(id))
        if run['conclusion']!='success' or run['head_sha']!=j['source_commit'] or r['target_commitish']!=j['source_commit']:raise ValueError('Evidence run/release provenance mismatch')
    policy=out/'bootstrap/g0-sepolicy'
    if sha(policy.read_bytes())!=kernel['policy_sha256']:raise ValueError('Policies differ')
    common=subprocess.check_output(['seinfo',str(policy),'--common','-x'],text=True)
    classmap='security/selinux/include/classmap.h';url='https://raw.githubusercontent.com/hi3635-dev/android_kernel_huawei_liszt/'+kernel['kernel_commit']+'/'+classmap
    with urllib.request.urlopen(url,timeout=45) as stream:data=stream.read(1024**2)
    if sha(data)!=kernel['kernel_source_sha256'][classmap]:raise ValueError('Kernel classmap digest mismatch')
    path=out/'classmap.h';path.write_bytes(data);expanded=subprocess.check_output(['gcc','-E','-P','-x','c',str(path)],text=True)
    classes=policy_compare((out/'bootstrap/policy-classes.txt').read_text(),common,expanded)
    versions=version_compare(bootstrap['bootstrap_elf'])
    (evidence/'policy-common.txt').write_text(common)
    (evidence/'elf-version-contracts.json').write_text(json.dumps(versions,indent=2)+'\n')
    (evidence/'policy-permission-contracts.json').write_text(json.dumps(classes,indent=2)+'\n')
    result={'status':'PUBLIC_G1_CAPTURED_CONTRACTS_REVIEWED','probe_run':int(os.environ['GITHUB_RUN_ID']),'source_commit':os.environ['GITHUB_SHA'],'bootstrap_run':40869967507,'kernel_run':40870457480,'input_digests_verified_on_bytes':True,'elf_versions':versions,'policy_classes':classes,'tests':suite(),'hardware_boot_verified':False,'runtime_linker_verified':False,'enforcing_compatibility_verified':False}
    (evidence/'g1-captured-review.json').write_text(json.dumps(result,indent=2)+'\n');publish(evidence,'carrera-g1-captured-review-'+os.environ['GITHUB_RUN_ID'],'Carrera G1 small static contract review');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
