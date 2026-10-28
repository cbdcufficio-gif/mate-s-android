#!/usr/bin/env python3
"""Verify the public G0 release on a disposable runner; inspect G1 without rebuilding."""
import base64
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import unittest
import zlib
from boot_inspect import cpio_entries, LIMIT
from android_locked_manifest import verify_synced, DIGEST

RUN = 40696459171
SOURCE = '6bd26d624218507b49008158c8fab0272f29bf56'
REPO = os.environ.get('GITHUB_REPOSITORY', '')
ROOT = Path('out/public-system-review')
DEST = ROOT/'evidence'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def api(path, method='GET', data=None):
    command = ['gh','api','repos/'+REPO+'/'+path,'--method',method]
    if data is not None:
        command += ['--input','-']
    return json.loads(subprocess.check_output(command, input=json.dumps(data).encode() if data is not None else None))

def download(tag, dest, bound):
    release = api('releases/tags/'+tag)
    assert release['target_commitish'] == SOURCE
    names = [a['name'] for a in release['assets']]
    assert len(names) == len(set(names)) and all(re.fullmatch(r'[A-Za-z0-9_.-]+',n) for n in names)
    assert sum(a['size'] for a in release['assets']) <= bound
    dest.mkdir(parents=True)
    subprocess.run(['gh','release','download',tag,'--repo',REPO,'--dir',str(dest)],check=True)
    files = {p.name:p for p in dest.iterdir()}
    assert set(files) == set(names)
    sums = {}
    for line in files['SHA256SUMS'].read_text().splitlines():
        digest, name = line.split('  ',1)
        assert re.fullmatch('[0-9a-f]{64}',digest) and name in files and name not in sums
        sums[name] = digest
    assert set(sums) == set(names)-{'SHA256SUMS'}
    verified = []
    for asset in release['assets']:
        path = files[asset['name']]
        digest = sha(path)
        assert path.stat().st_size == asset['size']
        assert asset.get('digest') == 'sha256:'+digest
        if path.name in sums:
            assert digest == sums[path.name]
        verified.append({'name':path.name,'bytes':path.stat().st_size,'sha256':digest})
    return release, verified

def bounded_gzip(path, limit):
    with gzip.open(path,'rb') as stream:
        data = stream.read(limit+1)
    assert len(data) <= limit
    return data

def main():
    assert os.environ.get('GITHUB_ACTIONS') == 'true' and os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted'
    assert REPO == 'cbdcufficio-gif/mate-s-android'
    run = api('actions/runs/'+str(RUN))
    jobs = api('actions/runs/'+str(RUN)+'/jobs')['jobs']
    assert run['head_sha'] == SOURCE and run['status'] == 'completed' and run['conclusion'] == 'success'
    assert jobs and all(j['conclusion']=='success' for j in jobs)
    tests = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover('tests'))
    assert tests.wasSuccessful()
    subprocess.run(['sha256sum','-c','SHA256SUMS'],check=True)
    DEST.mkdir(parents=True)
    pair = ROOT/'pair'
    release, assets = download('carrera-public-system-'+str(RUN),pair,800*1024**2)
    assert {a['name'] for a in assets} == {'carrera-public-system.img.gz','ramdisk.img','public-graphics-modules.tar.gz','carrera-system-report.json','resolved-manifest.xml','SHA256SUMS','README.txt'}
    system = json.loads((pair/'carrera-system-report.json').read_text())
    assert system['status'] == 'PUBLIC_CARRERA_SYSTEM_AND_RAMDISK_BUILT'
    assert system['rom_built'] is False and system['hardware_tested'] is False and system['proprietary_huawei_inputs'] is False
    assert system['system_image_rootdir_contents_verified'] is False
    assert system['legacy_vendor_link']['target'] == '/system/vendor'
    assert system['compressed_image']['sha256'] == sha(pair/'carrera-public-system.img.gz')
    assert system['ramdisk_sha256'] == sha(pair/'ramdisk.img')
    assert system['resolved_manifest_sha256'] == sha(pair/'resolved-manifest.xml')
    sync = verify_synced((pair/'resolved-manifest.xml').read_bytes())
    assert sync['selected_projects'] == 778 and sync['locked_projects'] == 794
    diagnostics = ROOT/'diagnostics'
    diag_release, diag_assets = download('carrera-build-diagnostics-'+str(RUN),diagnostics,16*1024**2)
    inventory = json.loads((diagnostics/'inventory.json').read_text())
    assert inventory['marker'] == 'MATES_PUBLIC_DIAGNOSTICS_V1'
    decoded = {}
    for item in inventory['files']:
        data = bounded_gzip(diagnostics/(item['name']+'.gz'),32*1024**2)
        assert hashlib.sha256(data).hexdigest() == item['sha256']
        assert not item['truncated'] and len(data) == item['input_bytes']
        decoded[item['name']] = data
    assert decoded['carrera-system-report.json'] == (pair/'carrera-system-report.json').read_bytes()
    ram = json.loads(decoded['carrera-report.json'])
    graph = json.loads(decoded['report.json'])
    assert ram['status'] == 'CARRERA_PUBLIC_RAMDISK_BUILT' and ram['native_init_parser_passed']
    assert ram['ramdisk_sha256'] == sha(pair/'ramdisk.img')
    assert len(ram['webview_inputs']) == 2 and all(x['zip_crc_verified'] for x in ram['webview_inputs'])
    dec = zlib.decompressobj(31)
    data = dec.decompress((pair/'ramdisk.img').read_bytes(),LIMIT+1)
    assert len(data)<=LIMIT and dec.eof and not dec.unused_data and not dec.unconsumed_tail
    entries = {e['name']:e for e in cpio_entries(data)}
    for row in ram['rootdir']:
        assert entries[row['name']]['sha256'] == row['sha256']
    modules = system['installed_public_modules']
    assert len(modules) == 14
    with tarfile.open(pair/'public-graphics-modules.tar.gz','r:gz') as tar:
        members = tar.getmembers()
        assert len(members)==14 and {m.name for m in members}=={m['path'] for m in modules}
        for item in modules:
            member = tar.getmember(item['path'])
            assert member.isfile() and member.size == item['bytes']
            assert hashlib.sha256(tar.extractfile(member).read()).hexdigest()==item['sha256']
    assert shutil.disk_usage(ROOT).free > 8*1024**3 + 2*2684354560
    sparse = ROOT/'system.sparse.img'
    with gzip.open(pair/'carrera-public-system.img.gz','rb') as src, sparse.open('xb') as dst:
        count = 0
        while True:
            block = src.read(1024*1024)
            if not block: break
            count += len(block)
            assert count <= 2684354560
            dst.write(block)
    assert sparse.stat().st_size == system['image']['bytes'] and sha(sparse)==system['image']['sha256']
    raw = ROOT/'system.raw.img'
    subprocess.run(['simg2img',str(sparse),str(raw)],check=True,timeout=120)
    assert raw.stat().st_size == 2684354560
    def dump(path, required=True):
        assert re.fullmatch(r'/[A-Za-z0-9_./+@-]+',path)
        target = ROOT/'extract.bin'
        target.unlink(missing_ok=True)
        result = subprocess.run(['debugfs','-R','dump '+path+' '+str(target),str(raw)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,check=True,timeout=30)
        if not target.is_file():
            if required: raise ValueError('Missing ext4 file '+path+': '+result.stdout)
            return None
        assert target.stat().st_size <= 4*1024**2
        return target.read_bytes()
    def ls(path):
        return subprocess.check_output(['debugfs','-R','ls -p '+path,str(raw)],stderr=subprocess.STDOUT,text=True,timeout=30)
    checked = []
    for item in modules:
        path = '/'+item['path']
        digest = hashlib.sha256(dump(path)).hexdigest()
        assert digest == item['sha256']
        checked.append({'path':path,'sha256':digest})
    props = dump('/system/build.prop').decode()
    propmap = dict(line.split('=',1) for line in props.splitlines() if line and not line.startswith('#') and '=' in line)
    # Pinned Q core/Makefile removes first_api_level from system build.prop and installs it in vendor.
    vendor_props = dump('/system/vendor/build.prop').decode()
    vendormap = dict(line.split('=',1) for line in vendor_props.splitlines() if line and not line.startswith('#') and '=' in line)
    assert vendormap['ro.product.first_api_level'] == '22'
    configs = {}
    for path in ('/init.rc','/init.environ.rc','/init.hi3635.rc','/fstab.hi3635','/default.prop',
                 '/system/etc/ld.config.txt','/system/etc/ld.config.vndk_lite.txt','/system/etc/ld.config.legacy.txt',
                 '/system/etc/prop.default','/system/etc/init/apexd.rc','/system/etc/init/zygote.zygote64_32.rc'):
        content = dump(path,required=False)
        if content is not None:
            configs[path] = {'sha256':hashlib.sha256(content).hexdigest(),'text':content.decode()}
    assert '/fstab.hi3635' in configs
    apex = ls('/system/apex')
    g1 = {'status':'PUBLIC_G1_STATIC_INPUTS_CAPTURED','source_run':RUN,'source_commit':SOURCE,
          'review_run':os.environ['GITHUB_RUN_ID'],'review_commit':os.environ['GITHUB_SHA'],
          'build_properties':propmap,'vendor_build_properties':vendormap,'launch_api_property_path':'/system/vendor/build.prop','configs':configs,'apex_listing':apex,
          'root_listing':ls('/'),'system_etc_listing':ls('/system/etc'),
          'ramdisk_entries':list(entries.values()),
          'limitations':['Static public artifacts only; no Huawei overlay','No kernel capability or policy compatibility established',
                         'Mount layout q-root-with-system requires coherent root/init/mount design before boot',
                         'No runtime namespace/APEX/ADB or hardware validation','system_image_rootdir_contents_verified remains false']}
    (DEST/'g1-public-config.json').write_text(json.dumps(g1,indent=2)+'\n')
    evidence = {'schema_version':1,'status':system['status'],'run_id':RUN,'job_ids':[j['id'] for j in jobs],
                'source_commit':SOURCE,'release':release['html_url'],'review_run_id':int(os.environ['GITHUB_RUN_ID']),
                'review_commit':os.environ['GITHUB_SHA'],'release_digests_verified_on_bytes':True,
                'assets':assets,'diagnostic_assets':diag_assets,'diagnostic_inventory':inventory,
                'manifest_lock_sha256':DIGEST,'sync_verification':sync,'launch_api_verified_from_image':22,
                'system_report':system,'ramdisk_report':ram,'graph_report':graph,
                'independent_ext4_module_digests':checked,'system_image_rootdir_contents_verified':False,
                'vendor_symlink_scope':'Original build staging only; root listing is static evidence, not runtime',
                'tests':{'run':tests.testsRun,'passed':tests.testsRun-len(tests.skipped),'skipped':len(tests.skipped)},
                'rom_built':False,'hardware_tested':False}
    (DEST/'public-system-review.json').write_text(json.dumps(evidence,indent=2)+'\n')
    (DEST/'README.txt').write_text('G0 public bytes verified; G1 static input capture only. Not a ROM; no hardware boot.\n')
    (DEST/'SHA256SUMS').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in sorted(DEST.iterdir())))
    print(json.dumps({'status':evidence['status'],'review_run':os.environ['GITHUB_RUN_ID'],'assets':assets,'api':22,'modules':len(checked),'tests':evidence['tests'],'g1_configs':list(configs),'apex_listing':apex},indent=2))

if __name__ == '__main__':
    main()
