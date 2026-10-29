#!/usr/bin/env python3
"""Pinned Q first-stage host experiment; no full sync, image build or device I/O."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
REPO='cbdcufficio-gif/mate-s-android'
REV='6d27634866be5b646a8cea1f9abeae902fd831e5'
FSTAB='device/huawei/carrera/rootdir/fstab.hi3635'
HASHES={
'init/first_stage_mount.cpp':'6f7733c05f474bb1475b0cd7e76babfb587050d11edff56842d0f3274ce497fa',
'init/first_stage_init.cpp':'6431c82fd0aa5bdec517b9872a368ce0b93c76ceca3471c4ac1716be2815e4ff',
'fs_mgr/fs_mgr_fstab.cpp':'9b0f65618fad1bf943b8883e1ea2324a9d4e3596a0e0167bf3fc61bcb513f650',
'fs_mgr/fs_mgr.cpp':'6e42159dffd82b570c924923c6841f98b3366800041d29ffbf83b1e48f1df0ee',
'init/devices.cpp':'7262d5c5dda920c4d09b06f77e027331baefda47d585463acd5531547f1b96c0'}

def digest(data):
    return hashlib.sha256(data).hexdigest()

def function(text,signature):
    start=text.index(signature)
    brace=text.index('{',start)
    depth=0
    for i in range(brace,len(text)):
        if text[i]=='{': depth+=1
        elif text[i]=='}':
            depth-=1
            if depth==0: return text[start:i+1]
    raise ValueError('Unclosed upstream function')

def candidate(text):
    lines=text.splitlines(keepends=True)
    selected=0
    for i,line in enumerate(lines):
        if not line.strip() or line.lstrip().startswith('#'): continue
        row=line.split()
        if len(row)!=5: raise ValueError('Expected five fstab fields')
        if row[1]=='/system':
            selected+=1
            if row[4]!='wait': raise ValueError('Unexpected G0 system flags')
            lines[i]=line.rstrip('\n')+',first_stage_mount\n'
    if selected!=1: raise ValueError('Expected exactly one system partition')
    return ''.join(lines)

def suite():
    p=subprocess.run(['python3','-m','unittest','discover','tests'],capture_output=True,text=True)
    print(p.stdout,end=''); print(p.stderr,end=''); p.check_returncode()
    m=re.search(r'Ran (\d+) tests?',p.stderr); assert m
    skip=re.search(r'OK \(skipped=(\d+)\)',p.stderr)
    total,skipped=int(m[1]),int(skip[1]) if skip else 0
    return {'run':total,'passed':total-skipped,'skipped':skipped}

def api(path,method='GET',data=None):
    cmd=['gh','api','repos/'+REPO+'/'+path,'--method',method]
    if data is not None: cmd+=['--input','-']
    return json.loads(subprocess.check_output(cmd,input=json.dumps(data).encode() if data is not None else None))

def main():
    assert os.environ.get('GITHUB_ACTIONS')=='true'
    assert os.environ.get('RUNNER_ENVIRONMENT')=='github-hosted'
    assert os.environ.get('GITHUB_REPOSITORY')==REPO
    os.chdir(ROOT)
    assert api('branches/main')['commit']['sha']==os.environ['GITHUB_SHA'],'Concurrent writer'
    runs=api('actions/workflows/android-carrera-system.yml/runs?per_page=10')['workflow_runs']
    assert not any(r['status'] in ('queued','in_progress','waiting','pending','requested') for r in runs)
    assert digest((ROOT/'configs/android-resolved-manifest.xml').read_bytes())=='b30f6d479b321cab00305b1c9a31450d0a8940138996e7e25cf27f7a0146f845'
    sources={}
    for path,expected in HASHES.items():
        url='https://raw.githubusercontent.com/LineageOS/android_system_core/'+REV+'/'+path
        with urllib.request.urlopen(url,timeout=60) as response: data=response.read(300000)
        assert digest(data)==expected,path
        sources[path]=data.decode()
    g1=json.loads((ROOT/'docs/G1-PUBLIC-CONFIG-RESULT.json').read_text())
    assert g1['source_run']==40696459171
    old=g1['configs']['/fstab.hi3635']['text']
    assert digest(old.encode())==g1['configs']['/fstab.hi3635']['sha256']
    new=candidate(old)
    assert (ROOT/FSTAB).read_text()==old,'Product changed'
    before=suite()
    signatures=[
        ('init/first_stage_mount.cpp','static Fstab ReadFirstStageFstab()'),
        ('init/first_stage_mount.cpp','bool FirstStageMount::TrySwitchSystemAsRoot()'),
        ('fs_mgr/fs_mgr_fstab.cpp','std::set<std::string> ExtraBootDevices('),
        ('init/devices.cpp','std::vector<std::string> DeviceHandler::GetBlockDeviceSymlinks(')]
    extracted=[function(sources[path],sig) for path,sig in signatures]
    fsall=function(sources['fs_mgr/fs_mgr.cpp'],'int fs_mgr_mount_all(')
    assert 'current_entry.fs_mgr_flags.first_stage_mount &&' in fsall
    assert '(!current_entry.fs_mgr_flags.formattable ||' in fsall
    assert 'current_entry.mount_point == "/" || current_entry.mount_point == "/system"' in fsall
    mounts=function(sources['init/first_stage_mount.cpp'],'bool FirstStageMount::MountPartitions()')
    assert 'if (!TrySwitchSystemAsRoot()) return false;' in mounts
    assert 'if (current->mount_point == "/system")' in mounts
    init=sources['init/first_stage_init.cpp']
    assert init.index('if (!DoFirstStageMount())')<init.index('const char* path = "/system/bin/init"')
    assert 'CheckFlag("first_stage_mount", first_stage_mount)' in sources['fs_mgr/fs_mgr_fstab.cpp']
    with tempfile.TemporaryDirectory(prefix='g1-first-stage-') as name:
        tmp=Path(name)
        (tmp/'old.fstab').write_text(old); (tmp/'candidate.fstab').write_text(new)
        harness=(ROOT/'tests/fixtures/q_first_stage_harness.cpp.in').read_text()
        (tmp/'harness.cpp').write_text(harness.replace('__UPSTREAM_FUNCTIONS__','\n\n'.join(extracted)))
        subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(tmp/'harness.cpp'),'-o',str(tmp/'fixture')],check=True)
        result=subprocess.check_output([str(tmp/'fixture'),str(tmp/'old.fstab'),str(tmp/'candidate.fstab')],text=True)
        assert result.strip()=='PINNED_Q_FIRST_STAGE_FIXTURE_PASS'
    root_paths=set(re.findall(r'^/\d+/[0-7]+/\d+/\d+/([^/]+)/',g1['root_listing'],re.M))
    assert {'system','init.rc','init','sepolicy','vendor','apex','fstab.hi3635'}<=root_paths
    assert 'import /init.'+'$'+'{ro.hardware}.rc' in g1['configs']['/init.rc']['text']
    assert '/apex/com.android.runtime/'+'$'+'{LIB}' in g1['configs']['/system/etc/ld.config.txt']['text']
    assert 'com.android.runtime.release' in g1['apex_listing']
    # Only the tested candidate is applied; immutable G0 evidence stays unchanged.
    (ROOT/FSTAB).write_text(new)
    testpath=ROOT/'tests/test_carrera_rootdir.py'
    text=testpath.read_text()
    target="self.assertNotIn('first_stage_mount',system[4].split(','))"
    assert target in text
    text=text.replace('def test_separate_system_layout_is_not_switched_to_system_as_root(self):',
                      'def test_ramdisk_first_stage_switches_to_q_image_root(self):')
    testpath.write_text(text.replace(target,"self.assertIn('first_stage_mount',system[4].split(','))"))
    after=suite()
    report={
        'status':'PUBLIC_G1_FIRST_STAGE_SOURCE_FIXTURE_PASSED',
        'run_id':int(os.environ['GITHUB_RUN_ID']),'source_commit':os.environ['GITHUB_SHA'],
        'android_system_core_revision':REV,'upstream_sha256':HASHES,
        'executed_upstream_functions':[sig for _,sig in signatures],
        'g0_fstab_sha256':digest(old.encode()),'candidate_fstab_sha256':digest(new.encode()),
        'product_change':'Only system: wait -> wait,first_stage_mount; BoardConfig stays false',
        'fixture_cases':['G0 fallback selects nothing and never switches',
            'candidate selects only system and switches exactly once',
            'mount failure returns false without switch-root','DT fstab overrides fallback file',
            'boot-device extraction returns hi_mci.0',
            'synthetic system uevent yields exact platform by-name path',
            'unrecognized platform yields no links'],
        'source_contracts':['mount_all skips non-formattable first-stage entries',
            'mount_all skips root and system','first-stage loop skips already mounted system',
            'first-stage completes before exec /system/bin/init','Q parser recognizes first_stage_mount'],
        'path_evidence':'G0 root inventory and captured init/linker/APEX; simulated mount/switch-root',
        'tests_before':before,'tests_after':after,
        'runtime_mounts_verified':False,'system_image_rootdir_contents_verified':False,
        'hardware_boot_verified':False,'full_android_rebuild_started':False,
        'limitations':['Host C++ fixture: parser, mount, switch-root and platform discovery stubbed',
            'Real DT fstab precedence and androidboot.hardware/boot_devices remain private metadata checks',
            'No execution of Q init binary or kernel mount/security/APEX namespace',
            'G0 release retains original fstab; rebuilt ramdisk/system still required',
            'Kernel-policy, essential ELF closure, APEX activation and vendor overlay remain G1',
            'Huawei boot container, dtimage, stock tail and recovery remain G2']}
    (ROOT/'docs/G1-FIRST-STAGE-RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
    handoff=(
        '# G1 first-stage: fixture Q verificata — 29 ottobre 2026\n\n'
        'Run ['+os.environ['GITHUB_RUN_ID']+'](https://github.com/'+REPO+'/actions/runs/'+os.environ['GITHUB_RUN_ID']+'), input '+os.environ['GITHUB_SHA']+'.\n\n'
        'Quattro funzioni del sorgente Q fissato '+REV+' compilate ed eseguite con corpi invariati. '
        'La fixture riproduce il filtro vuoto G0 e verifica candidato, switch singolo, '
        'fallimento mount, precedenza DT e by-name su uevent sintetico. '
        'Parser, mount, switch-root e rilevamento piattaforma sono stub: nessuna prova kernel/init reale.\n\n'
        'Applicata solo first_stage_mount alla riga system dopo la prova; cache, userdata/encryptable=footer, '
        'BoardConfig e guardie invariati. Q salta system nel ciclo successivo; mount_all salta i mount '
        'del primo stadio non formattabili. G0 resta immutato: rebuild deliberato dopo il completamento G1.\n\n'
        'Suite prima/dopo '+str(before['run'])+'/'+str(after['run'])+'; dopo '+str(after['passed'])+
        ' passati, '+str(after['skipped'])+' saltati. SHA256SUMS verificato prima della pubblicazione.\n\n'
        'Prossima azione: closure ELF essenziale, flattened APEX e capability/config effettiva del kernel '
        'diagnostico rispetto alla policy. Prima del boot confermare in privato DT fstab, androidboot.hardware '
        'e piattaforma reale. G2 richiede byte stock privati per dtimage/coda e recupero. '
        'Nessun boot/ROM attestato; G1 aperto.\n')
    paths=[FSTAB,'tests/test_carrera_rootdir.py','docs/G1-FIRST-STAGE-RESULT.json',
        'docs/HANDOFF-2026-10-29.md','docs/STATUS.md','docs/PORTING-STATE.json','docs/BUILD-BLOCKERS.md']
    (ROOT/'docs/HANDOFF-2026-10-29.md').write_text(handoff)
    status=ROOT/'docs/STATUS.md'; status.write_text(handoff+'\n---\n\n'+status.read_text())
    statepath=ROOT/'docs/PORTING-STATE.json'; state=json.loads(statepath.read_text())
    state['g1_first_stage']={'result':'docs/G1-FIRST-STAGE-RESULT.json','run_id':report['run_id'],
        'status':report['status'],'hardware_boot_verified':False}
    for gate in state['gates']:
        if gate['id']=='G1':
            gate['next']='Essential ELF/APEX and kernel-policy; confirm DT/cmdline privately; rebuild after G1 closure'
            gate['evidence']='docs/G1-FIRST-STAGE-RESULT.json'
    statepath.write_text(json.dumps(state,indent=2)+'\n')
    blockers=ROOT/'docs/BUILD-BLOCKERS.md'; lines=blockers.read_text().splitlines()
    for i,line in enumerate(lines):
        if line.startswith('| G1 |'):
            lines[i]='| G1 | First-stage provato su funzioni Q; DT reale/kernel-policy/APEX/overlay incompleti | G1-FIRST-STAGE-RESULT.json; closure essenziale, capability effettive e DT/cmdline privati |'
    blockers.write_text('\n'.join(lines)+'\n')
    sums={}
    for line in (ROOT/'SHA256SUMS').read_text().splitlines():
        h,path=line.split('  ',1); assert path not in sums; sums[path]=h
    for path in paths: sums[path]=digest((ROOT/path).read_bytes())
    (ROOT/'SHA256SUMS').write_text(''.join(h+'  '+p+'\n' for p,h in sorted(sums.items())))
    subprocess.run(['sha256sum','-c','SHA256SUMS'],check=True)
    branch=api('branches/main')
    assert branch['commit']['sha']==os.environ['GITHUB_SHA'],'Another writer changed main'
    tree=api('git/trees','POST',{'base_tree':branch['commit']['commit']['tree']['sha'],
        'tree':[{'path':p,'mode':'100644','type':'blob','content':(ROOT/p).read_text()} for p in paths+['SHA256SUMS']]})
    commit=api('git/commits','POST',{'message':'Validate pinned Q first-stage fixture and select system before switch-root',
        'tree':tree['sha'],'parents':[os.environ['GITHUB_SHA']]})
    api('git/refs/heads/main','PATCH',{'sha':commit['sha'],'force':False})
    print('G1_FIRST_STAGE_VERIFIED_COMMIT='+commit['sha'])
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
