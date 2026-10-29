#!/usr/bin/env python3
"""Generate the pinned diagnostic .config only, and inventory actual G0 policy."""
import argparse,difflib,json,os,re,shutil,subprocess
from pathlib import Path
from build_kernel import apply_fragment,config_values,verify_source_changes
from g1_contract_common import ROOT,guard,sha,suite,publish,api

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--bootstrap-tag',required=True);args=parser.parse_args()
    if not re.fullmatch(r'carrera-g1-bootstrap-\d+',args.bootstrap_tag):raise ValueError('Unexpected bootstrap provenance')
    guard();os.chdir(ROOT);out=ROOT/'out/g1-kernel-policy';out.mkdir(parents=True,exist_ok=False);evidence=out/'evidence';evidence.mkdir();sources=out/'sources';sources.mkdir()
    lock=json.loads((ROOT/'sources.lock.json').read_text());repos={x['directory']:x for x in lock['repositories']}
    for key in ('kernel-hi3635','gcc49'):
        row=repos[key];p=sources/key;p.mkdir();subprocess.run(['git','init','-q',str(p)],check=True)
        subprocess.run(['git','-C',str(p),'fetch','--depth=1',row['url'],row['commit']],check=True,timeout=600)
        subprocess.run(['git','-C',str(p),'checkout','--detach','--quiet','FETCH_HEAD'],check=True)
        if subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip()!=row['commit']:raise ValueError('Pinned source mismatch')
    kernel=sources/'kernel-hi3635';compiler=sources/'gcc49/bin/aarch64-linux-android-gcc'
    if sha(compiler.read_bytes())!=lock['toolchain_gcc_sha256']:raise ValueError('Compiler digest mismatch')
    if sha((ROOT/'configs/stock-b321.config').read_bytes())!=lock['stock_config_sha256']:raise ValueError('Stock config mismatch')
    for name in ('0001-fix-immersion-header-path.patch','0002-gate-touchscreen-framework-firmware-update.patch'):
        subprocess.run(['git','-C',str(kernel),'apply',str(ROOT/'patches/kernel'/name)],check=True)
    touch=verify_source_changes(kernel)
    output=out/'config-only';output.mkdir();config=output/'.config';shutil.copyfile(ROOT/'configs/stock-b321.config',config);apply_fragment(config,ROOT/'configs/android10-diagnostic.fragment');requested=config.read_text()
    command=['make','-C',str(kernel),'O='+str(output),'ARCH=arm64','CROSS_COMPILE='+str(compiler)[:-3],'HOSTCFLAGS=-fcommon','olddefconfig']
    with (evidence/'olddefconfig.log').open('w') as log:subprocess.run(command,check=True,stdout=log,stderr=subprocess.STDOUT,timeout=300,env={**os.environ,'LC_ALL':'C'})
    actual=config_values(config);fragment=config_values(ROOT/'configs/android10-diagnostic.fragment')
    for key,value in fragment.items():
        if actual.get(key,'n')!=value:raise ValueError('Fragment lost: '+key)
    if actual.get('CONFIG_HUAWEI_TS_FW_UPDATE','n')!='n':raise ValueError('Touch update guard lost')
    stock=config_values(ROOT/'configs/stock-b321.config')
    for key in ('CONFIG_FB_3635','CONFIG_MALI_MIDGARD','CONFIG_FINGERPRINT','CONFIG_IMMERSION','CONFIG_BACKLIGHT_10000','CONFIG_GRACE_SELECT_2A_1A_AC'):
        if actual.get(key,'n')!=stock.get(key,'n'):raise ValueError('Hardware config drift: '+key)
    shutil.copyfile(config,evidence/'diagnostic.config');(evidence/'requested-to-effective.diff').write_text(''.join(difflib.unified_diff(requested.splitlines(True),config.read_text().splitlines(True),fromfile='requested',tofile='effective')))
    release=api('releases/tags/'+args.bootstrap_tag)
    allowed={'g0-sepolicy','policy-capabilities.txt','policy-classes.txt','g1-bootstrap.json','SHA256SUMS'}
    if sum(a['size'] for a in release['assets'] if a['name'] in allowed)>16*1024**2:raise ValueError('Policy input budget')
    inputs=out/'bootstrap-inputs';inputs.mkdir()
    cmd=['gh','release','download',args.bootstrap_tag,'--repo',os.environ['GITHUB_REPOSITORY'],'--dir',str(inputs)]
    for name in sorted(allowed):cmd+=['--pattern',name]
    subprocess.run(cmd,check=True,timeout=120)
    sums=dict((name,digest) for digest,name in (x.split('  ',1) for x in (inputs/'SHA256SUMS').read_text().splitlines()))
    for name in allowed-{'SHA256SUMS'}:
        if sha((inputs/name).read_bytes())!=sums[name]:raise ValueError('Bootstrap evidence digest mismatch')
    bootstrap=json.loads((inputs/'g1-bootstrap.json').read_text())
    if bootstrap['source_run']!=40696459171 or sha((inputs/'g0-sepolicy').read_bytes())!=bootstrap['policy_sha256']:raise ValueError('Policy provenance mismatch')
    polcaps=subprocess.check_output(['seinfo',str(inputs/'g0-sepolicy'),'--polcap'],text=True)
    classes=subprocess.check_output(['seinfo',str(inputs/'g0-sepolicy'),'--class','-x'],text=True)
    (evidence/'policy-capabilities.txt').write_text(polcaps);(evidence/'policy-classes.txt').write_text(classes)
    texts={name:(kernel/name).read_text() for name in ['security/selinux/include/security.h','security/selinux/ss/services.c','security/selinux/hooks.c','security/selinux/include/classmap.h','kernel/nsproxy.c','kernel/seccomp.c','drivers/usb/gadget/android.c','drivers/usb/gadget/f_fs.c']}
    caps=[x for x in re.findall(r'^\s+([a-z][a-z0-9_]+)\s*$',polcaps,re.M)]
    if not caps:raise ValueError('Unable to parse actual policy capabilities')
    mapping={'network_peer_controls':'NETPEER','open_perms':'OPENPERM','extended_socket_class':'EXTSOCKCLASS','nnp_nosuid_transition':'NNP_NOSUID_TRANSITION'}
    comparisons=[]
    for name in caps:
        token=mapping.get(name);declared=bool(token and 'POLICYDB_CAPABILITY_'+token in texts['security/selinux/include/security.h'])
        comparisons.append({'policycap':name,'kernel_enum_present':declared,'semantic_compatibility_verified':False,'action':'Review parser, classmap and hooks; scoped upstream backport with positive/negative target tests' if not declared else 'Verify generated configuration and target enforcement'})
    active_classes=re.findall(r'^\s*class\s+(\w+)',classes,re.M)
    classmap=texts['security/selinux/include/classmap.h'];mapped=set(re.findall(r'\{\s*"([a-z0-9_]+)"',classmap))
    capabilities={key:actual.get(key,'n') for key in ['CONFIG_SECCOMP','CONFIG_SECCOMP_FILTER','CONFIG_SECURITY_SELINUX','CONFIG_SECURITY_SELINUX_POLICYDB_VERSION_MAX','CONFIG_NAMESPACES','CONFIG_USB_G_ANDROID','CONFIG_USB_FUNCTIONFS','CONFIG_NETFILTER_XT_MATCH_QTAGUID','CONFIG_ANDROID_LOW_MEMORY_KILLER','CONFIG_MEMCG','CONFIG_BLK_DEV_LOOP','CONFIG_PSTORE','CONFIG_PSTORE_RAM']}
    report={'status':'PUBLIC_G1_KERNEL_CONFIG_POLICY_CAPTURED','probe_run':int(os.environ['GITHUB_RUN_ID']),'source_commit':os.environ['GITHUB_SHA'],'kernel_commit':repos['kernel-hi3635']['commit'],'compiler_commit':repos['gcc49']['commit'],'compiler_sha256':lock['toolchain_gcc_sha256'],'effective_config_sha256':sha(config.read_bytes()),'touch_patch_sha256':touch['patch_sha256'],'command':command,'policy_sha256':bootstrap['policy_sha256'],'bootstrap_release':args.bootstrap_tag,'effective_config':capabilities,'actual_policycaps':caps,'policycap_comparison':comparisons,'policy_classes_without_kernel_classmap_entry':sorted(set(active_classes)-mapped),'kernel_source_sha256':{name:sha(text.encode()) for name,text in texts.items()},'source_observations':{'mount_namespace_implementation_present':'copy_mnt_ns' in texts['kernel/nsproxy.c'],'seccomp_tsync_implementation_present':'seccomp_sync_threads' in texts['kernel/seccomp.c'],'legacy_gadget_includes_functionfs':'#include "f_fs.c"' in texts['drivers/usb/gadget/android.c']},'tests':suite(),'image_compiled':False,'hardware_boot_verified':False,'enforcing_compatibility_verified':False,'limitations':['Policycap/class-name inventories are not permission/hook semantic validation','No target kernel policy load or denial tests executed','olddefconfig only; no Image compiled']}
    (evidence/'g1-kernel-policy.json').write_text(json.dumps(report,indent=2)+'\n');publish(evidence,'carrera-g1-kernel-policy-'+os.environ['GITHUB_RUN_ID'],'Carrera generated config and policy contract inventory');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
