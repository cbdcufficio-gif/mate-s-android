#!/usr/bin/env python3
"""Publish verified public G0/G1 evidence to main using an optimistic Git update."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

REPO = 'cbdcufficio-gif/mate-s-android'
SOURCE = '6bd26d624218507b49008158c8fab0272f29bf56'
REVIEW_SOURCE = 'd5f708441acc8587670aa47ba047fd772318ad4c'
REVIEW_RUN = 40724596747
TAG = 'carrera-public-system-review-40696459171'

def api(path, method='GET', data=None):
    cmd = ['gh','api','repos/'+REPO+'/'+path,'--method',method]
    if data is not None: cmd += ['--input','-']
    return json.loads(subprocess.check_output(cmd,input=json.dumps(data).encode() if data is not None else None))

def digest(data):
    return hashlib.sha256(data).hexdigest()

def main():
    assert os.environ.get('GITHUB_ACTIONS')=='true' and os.environ.get('RUNNER_ENVIRONMENT')=='github-hosted'
    assert os.environ['GITHUB_REPOSITORY']==REPO
    ci=api('actions/runs/'+str(REVIEW_RUN))
    assert ci['status']=='completed' and ci['conclusion']=='success' and ci['head_sha']==REVIEW_SOURCE
    release=api('releases/tags/'+TAG)
    assert release['target_commitish']==REVIEW_SOURCE
    assert sum(a['size'] for a in release['assets'])<2*1024**2
    assert {a['name'] for a in release['assets']}=={'public-system-review.json','g1-public-config.json','README.txt','SHA256SUMS'}
    root=Path('out/final-review');root.mkdir(parents=True)
    subprocess.run(['gh','release','download',TAG,'--repo',REPO,'--dir',str(root)],check=True)
    sums={}
    for line in (root/'SHA256SUMS').read_text().splitlines():
        h,name=line.split('  ',1)
        assert name in {'public-system-review.json','g1-public-config.json','README.txt'} and name not in sums and re.fullmatch('[0-9a-f]{64}',h)
        sums[name]=h
        assert digest((root/name).read_bytes())==h
    assert len(sums)==3
    for asset in release['assets']:
        data=(root/asset['name']).read_bytes()
        assert len(data)==asset['size'] and asset['digest']=='sha256:'+digest(data)
    report=json.loads((root/'public-system-review.json').read_text())
    g1=json.loads((root/'g1-public-config.json').read_text())
    assert report['status']=='PUBLIC_CARRERA_SYSTEM_AND_RAMDISK_BUILT'
    assert report['source_commit']==SOURCE and report['run_id']==40696459171 and report['review_run_id']==REVIEW_RUN
    assert report['release_digests_verified_on_bytes'] and len(report['independent_ext4_module_digests'])==14
    assert report['launch_api_verified_from_image']==22 and not report['system_image_rootdir_contents_verified']
    assert g1['review_commit']==REVIEW_SOURCE and g1['source_commit']==SOURCE
    assert g1['status']=='PUBLIC_G1_STATIC_INPUTS_CAPTURED'
    report['review_release']=release['html_url']
    report['finalization_run_id']=int(os.environ['GITHUB_RUN_ID'])
    report['finalization_commit']=os.environ['GITHUB_SHA']
    report['review_evidence_sha256']=digest((root/'public-system-review.json').read_bytes())
    report['g1_evidence_sha256']=digest((root/'g1-public-config.json').read_bytes())
    state=json.loads(Path('docs/PORTING-STATE.json').read_text())
    assert state['current_ci']['run_id']==40696459171
    state['current_ci'].update(status_at_direction_update='completed',conclusion='success',
                               evidence_review_run_id=REVIEW_RUN,evidence_review_source=REVIEW_SOURCE,
                               review_release=release['html_url'])
    state['g0_result']='docs/CARRERA-SYSTEM-RESULT.json'
    state['g1_public_configuration']='docs/G1-PUBLIC-CONFIG-RESULT.json'
    for gate in state['gates']:
        if gate['id']=='G0':
            gate.update(state='verified_public_base',evidence_run=REVIEW_RUN,
                        next='G1 static mount/linker/APEX/kernel-policy contracts; no further generic G0 rebuild')
        elif gate['id']=='G1':
            gate.update(state='in_progress',evidence='docs/G1-PUBLIC-CONFIG-RESULT.json',
                        next='Resolve Q root-with-system and first-stage mount contract, then effective linker/APEX and kernel-policy compatibility')
    state['evidence_limits']['system_module_bytes']='14 real modules independently re-extracted from release ext4 and SHA256 checked on public runner'
    state['evidence_limits']['rootdir_runtime']='not verified; system_image_rootdir_contents_verified remains false'
    state['automation_handoff']='G0 monitor complete; public G1 inputs captured; no hardware or complete ROM claimed'
    configs=g1['configs']
    linkers={p:x['sha256'] for p,x in configs.items() if '/ld.config' in p}
    ramnames={x['name'] for x in g1['ramdisk_entries']}
    summary={
        'api':g1['vendor_build_properties'].get('ro.product.first_api_level'),
        'linker_files':linkers,'apex_listing':g1['apex_listing'],
        'ramdisk_has_init_rc':'init.rc' in ramnames,'ramdisk_has_init':'init' in ramnames,
        'fstab':configs['/fstab.hi3635']['text'],
        'ld_config_text':{p:x['text'] for p,x in configs.items() if '/ld.config' in p},
        'init_hi3635':configs.get('/init.hi3635.rc',{}).get('text'),
        'init_root_import_and_mount_lines':[line for line in configs.get('/init.rc',{}).get('text','').splitlines()
            if any(s in line for s in ('import ','mount_all','apex','/system','/vendor','selinux'))]}
    tests=report['tests']
    text=(
        '# G0 verificato; primi input effettivi G1 — 28 ottobre 2026\n\n'
        'Sistema [40696459171](https://github.com/'+REPO+'/actions/runs/40696459171), '
        'job 122844429122, sorgente `'+SOURCE+'`: successo.\n'
        'Review indipendente ['+str(REVIEW_RUN)+'](https://github.com/'+REPO+'/actions/runs/'+str(REVIEW_RUN)+'), '
        'commit `'+REVIEW_SOURCE+'`, runner pubblico ubuntu-22.04, senza sync o rebuild Android.\n\n'
        'Verificati sui byte tutti i sette asset della release, SHA256SUMS e digest server, '
        'gzip e immagine sparse, manifest (794 progetti fissati, 778 selezionati), '
        'API22 da build.prop, ramdisk cpio e tre file rootdir. '
        'Tutti i 14 moduli reali estratti nuovamente da ext4 hanno digest identici '
        'al report e all\'archivio moduli. Diagnostica entro 16 MiB, inventory e checksum '
        'verificati, zero file troncati.\n'
        'Suite sulla review: '+str(tests['run'])+' test, '+str(tests['passed'])+' passati, '
        +str(tests['skipped'])+' saltati; checksum repository verificati.\n\n'
        'Marker `PUBLIC_CARRERA_SYSTEM_AND_RAMDISK_BUILT` confermato. '
        'G0 chiude solo la base pubblica. `system_image_rootdir_contents_verified=false` '
        'rimane invariato; symlink vendor verificato nello staging della build, '
        'nessuna prova mount/runtime, boot o ROM.\n\n'
        'G1: catturati dall\'immagine reale linker, proprietà, APEX, init/fstab e '
        'inventory ramdisk in [G1-PUBLIC-CONFIG-RESULT.json](G1-PUBLIC-CONFIG-RESULT.json). '
        'Il filesystem è `q-root-with-system`; la fstab minima monta ancora '
        'la partizione su /system senza first_stage_mount. Un montaggio legacy di questa immagine su /system collocherebbe '
        'i contenuti di piattaforma sotto /system/system: va risolto il '
        'contratto first-stage/switch-root prima del boot. Non è un guasto hardware osservato.\n\n'
        'Prossima azione concreta: fixture Q first-stage/init con il layout reale, '
        'selezione mount/switch-root motivata dal sorgente fissato, poi APEX/linker '
        'e policy rispetto alla configurazione kernel effettiva. Niente nuovo ciclo '
        'G0, blob privati o prova telefono; G2 resta successivo.\n'
    )
    blockers=Path('docs/BUILD-BLOCKERS.md').read_text()
    lines=blockers.splitlines()
    for i,line in enumerate(lines):
        if line.startswith('| G0 |'):
            lines[i]='| G0 | Chiuso: base pubblica verificata sui byte, non ROM | Sistema40696459171; review40724596747; CARRERA-SYSTEM-RESULT.json |'
        if line.startswith('| G1 |'):
            lines[i]='| G1 | Layout q-root-with-system contro mount legacy /system; kernel/policy e overlay incompleti | G1-PUBLIC-CONFIG-RESULT.json: fixture first-stage/switch-root, linker/APEX effettivi, closure essenziale |'
    handoff=(
        '# Handoff verificabile — 28 ottobre 2026\n\n'+text.split('\n\n',1)[1]+
        '\n## Limiti e coordinamento\n\n'
        'Il controllo ricorrente G0 può essere disattivato: la condizione attesa è stata verificata. '
        'Questo handoff non chiude G1/G2 e non afferma un blocco di tutto il lavoro pubblico: '
        'la prossima attività è l\'esperimento statico first-stage sopra, senza telefono. '
        'Prima di modificare rileggere main, i run e gli altri writer. '
        'Preservare manifest, cache unica, riserva 8 GiB, budget 18000s, timeout350min, '
        'guardie /vendor/SELinux/ELF/touch e nessuna spesa. '
        'Nessun flash, erase, format, restore, reboot o fastboot boot autorizzato.\n'
    )
    files={
        'docs/CARRERA-SYSTEM-RESULT.json':json.dumps(report,indent=2)+'\n',
        'docs/G1-PUBLIC-CONFIG-RESULT.json':json.dumps(g1,indent=2)+'\n',
        'docs/PORTING-STATE.json':json.dumps(state,indent=2)+'\n',
        'docs/STATUS.md':text+'\n---\n\n'+Path('docs/STATUS.md').read_text(),
        'docs/BUILD-BLOCKERS.md':'\n'.join(lines)+'\n',
        'docs/HANDOFF-2026-10-28.md':handoff}
    sums={}
    for line in Path('SHA256SUMS').read_text().splitlines():
        h,path=line.split('  ',1)
        assert path not in sums
        sums[path]=h
    for path,content in files.items(): sums[path]=digest(content.encode())
    files['SHA256SUMS']=''.join(h+'  '+path+'\n' for path,h in sorted(sums.items()))
    for path,content in files.items(): Path(path).write_text(content)
    subprocess.run(['sha256sum','-c','SHA256SUMS'],check=True)
    branch=api('branches/main')
    assert branch['commit']['sha']==os.environ['GITHUB_SHA'],'Another writer changed main; stop rather than overwrite'
    tree=api('git/trees','POST',{'base_tree':branch['commit']['commit']['tree']['sha'],
        'tree':[{'path':path,'mode':'100644','type':'blob','content':content} for path,content in files.items()]})
    commit=api('git/commits','POST',{'message':'Close public G0 with independent byte verification and hand off effective G1 mount inputs',
        'tree':tree['sha'],'parents':[os.environ['GITHUB_SHA']]})
    api('git/refs/heads/main','PATCH',{'sha':commit['sha'],'force':False})
    print('G0_VERIFIED_HANDOFF_COMMIT='+commit['sha'])
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    main()
