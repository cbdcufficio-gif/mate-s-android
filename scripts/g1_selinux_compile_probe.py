#!/usr/bin/env python3
"""Compile only the experimental SELinux object on disposable public CI."""
import json,os,shutil,subprocess
from pathlib import Path
from build_kernel import apply_fragment,config_values,verify_source_changes
from g1_contract_common import ROOT,guard,sha


def command(argv,timeout=300):
    print('+', ' '.join(map(str,argv)),flush=True)
    subprocess.run(argv,check=True,timeout=timeout,env={**os.environ,'LC_ALL':'C'})


def main():
    guard()
    if shutil.disk_usage(ROOT).free < 12*1024**3:
        raise ValueError('Insufficient space for bounded kernel source probe')
    out=ROOT/'out/g1-selinux-compile';out.mkdir(parents=True,exist_ok=False)
    lock=json.loads((ROOT/'sources.lock.json').read_text());repos={x['directory']:x for x in lock['repositories']}
    for key in ('kernel-hi3635','gcc49'):
        row=repos[key];p=out/key;p.mkdir();command(['git','init','-q',str(p)])
        command(['git','-C',str(p),'fetch','--depth=1',row['url'],row['commit']],600)
        command(['git','-C',str(p),'checkout','--detach','--quiet','FETCH_HEAD'])
        actual=subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip()
        if actual!=row['commit']:raise ValueError('Pinned checkout mismatch: '+key)
    kernel=out/'kernel-hi3635';gcc=out/'gcc49/bin/aarch64-linux-android-gcc'
    if sha(gcc.read_bytes())!=lock['toolchain_gcc_sha256']:raise ValueError('Compiler digest mismatch')
    stock=ROOT/'configs/stock-b321.config'
    if sha(stock.read_bytes())!=lock['stock_config_sha256']:raise ValueError('Stock config mismatch')
    for name in ('0001-fix-immersion-header-path.patch','0002-gate-touchscreen-framework-firmware-update.patch'):
        command(['git','-C',str(kernel),'apply',str(ROOT/'patches/kernel'/name)])
    verify_source_changes(kernel)
    candidate=ROOT/'patches/experimental/selinux-nnp-nosuid-candidate.patch'
    expected=json.loads((ROOT/'docs/G1-SELINUX-CANDIDATE-SOURCES.json').read_text())
    if repos['kernel-hi3635']['commit']!=expected['kernel_commit']:raise ValueError('Candidate source revision mismatch')
    for name,digest in expected['original_sha256'].items():
        if sha((kernel/name).read_bytes())!=digest:raise ValueError('Candidate base digest mismatch: '+name)
    command(['git','-C',str(kernel),'apply','--check',str(candidate)])
    command(['git','-C',str(kernel),'apply',str(candidate)])
    changed=subprocess.check_output(['git','-C',str(kernel),'diff','--name-only'],text=True).splitlines()
    # The existing touch guard verified the only pre-candidate changes; enforce exact patch paths independently.
    patchpaths=subprocess.check_output(['git','-C',str(kernel),'diff','--name-only','--','security/selinux'],text=True).splitlines()
    if set(patchpaths)!=set(expected['original_sha256']):raise ValueError('Unexpected SELinux patch paths')
    build=out/'build';build.mkdir();config=build/'.config';shutil.copyfile(stock,config)
    apply_fragment(config,ROOT/'configs/android10-diagnostic.fragment')
    base=['make','-C',str(kernel),'O='+str(build),'ARCH=arm64','CROSS_COMPILE='+str(gcc)[:-3],'HOSTCFLAGS=-fcommon']
    command(base+['olddefconfig'])
    actual=config_values(config);fragment=config_values(ROOT/'configs/android10-diagnostic.fragment')
    for key,value in fragment.items():
        if actual.get(key,'n')!=value:raise ValueError('Diagnostic fragment changed: '+key)
    if actual.get('CONFIG_HUAWEI_TS_FW_UPDATE','n')!='n' or actual.get('CONFIG_USER_NS','n')!='n':raise ValueError('Required config guard changed')
    command(base+['-j2','security/selinux/'],900)
    obj=build/'security/selinux/selinux.o'
    if not obj.is_file() or not obj.stat().st_size:raise ValueError('SELinux object missing')
    if (build/'arch/arm64/boot/Image').exists():raise ValueError('Unexpected kernel image produced')
    report={'status':'EXPERIMENTAL_SELINUX_OBJECT_COMPILED','kernel_revision':repos['kernel-hi3635']['commit'],'compiler_revision':repos['gcc49']['commit'],'compiler_sha256':sha(gcc.read_bytes()),'patch_sha256':sha(candidate.read_bytes()),'config_sha256':sha(config.read_bytes()),'selinux_object_sha256':sha(obj.read_bytes()),'selinux_object_size':obj.stat().st_size,'kernel_image_built':False,'policy_runtime_verified':False,'hardware_boot_verified':False,'full_source_paths_changed':changed,'note':'Object compilation alone does not verify policy load, security semantics, linking, boot or hardware.'}
    print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':main()
