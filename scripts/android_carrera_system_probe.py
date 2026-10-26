#!/usr/bin/env python3
"""Build the public Carrera system/ramdisk pair, without proprietary Huawei inputs."""
import gzip
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from android_graph_probe import ROOT,guarded
from android_modules_probe import MODULES,REQUIRED,inventory
from android_patches import apply_patches
from android_system_probe import image_metadata,MAX_ASSET
from elf_audit import sha256


def system_build_jobs(cpus, memory_bytes):
    # Leave a core and at least 4 GiB per build slot on the standard runner.
    return 3 if cpus >= 4 and memory_bytes >= 12*1024**3 else 2


def system_image_path(staged_path):
    relative=Path(staged_path)
    if relative.is_absolute() or '..' in relative.parts or not relative.parts or relative.parts[0]!='system':
        raise ValueError('Unsafe or unexpected module path in system staging')
    if any(not re.fullmatch(r'[A-Za-z0-9_.+-]+',part) for part in relative.parts):
        raise ValueError('Unexpected character in public module path')
    return '/'+str(relative.relative_to('system'))


def verify_legacy_vendor_link(product):
    link=product/'root'/'vendor'
    if not link.is_symlink():
        raise ValueError('Legacy product root is missing the /vendor symlink')
    target=os.readlink(link)
    if target!='/system/vendor':
        raise ValueError('Unexpected legacy /vendor symlink target: '+target)
    return {'path':'root/vendor','target':target}


def verify_modules_in_system_image(source,image,modules):
    debugfs=shutil.which('debugfs')
    if not debugfs:
        raise ValueError('debugfs is required to inspect the Carrera system ext4 image')
    metadata=image_metadata(image)
    with tempfile.TemporaryDirectory(prefix='carrera-ext4-',dir=ROOT) as temp:
        raw=image
        if metadata['format']=='android_sparse':
            expanded=metadata['expanded_bytes']
            if shutil.disk_usage(ROOT).free < expanded+8*1024**3:
                raise ValueError('Insufficient free space to inspect system ext4 while retaining 8 GiB')
            simg2img=source/'out/host/linux-x86/bin/simg2img'
            if not simg2img.is_file():
                raise ValueError('Android simg2img host tool is missing')
            raw=Path(temp)/'system.raw.img'
            subprocess.run([str(simg2img),str(image),str(raw)],check=True,timeout=180)
        with raw.open('rb') as stream:
            stream.seek(1024+56)
            if stream.read(2)!=b'\x53\xef':
                raise ValueError('System image is not an ext4 filesystem')
        extracted=[]
        for index,item in enumerate(modules):
            image_path=system_image_path(item['path'])
            destination=Path(temp)/f'module-{index}.bin'
            command=f'dump {image_path} {destination}'
            result=subprocess.run([debugfs,'-R',command,str(raw)],stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT,text=True,timeout=60)
            if result.returncode or not destination.is_file() or 'File not found' in result.stdout:
                raise ValueError('Public module is missing from system ext4: '+image_path)
            digest=sha256(destination)
            if digest!=item['sha256']:
                raise ValueError('Public module hash differs inside system ext4: '+image_path)
            extracted.append({'path':image_path,'sha256':digest})
    if not extracted or not any(item['path'].startswith('/vendor/') for item in extracted):
        raise ValueError('No public vendor module verified inside system ext4')
    return {'filesystem':'ext4','format':metadata['format'],'modules_verified':len(extracted),
            'modules':extracted}


def main():
    if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('RUNNER_ENVIRONMENT')!='github-hosted':
        raise SystemExit('Disposable public runner only; no local Android sync')
    result=subprocess.run([sys.executable,str(Path(__file__).with_name('android_carrera_probe.py'))])
    if result.returncode:return result.returncode
    report={'status':'CARRERA_PUBLIC_SYSTEM_BUILD_RUNNING','product':'lineage_carrera_public-userdebug',
            'rom_built':False,'hardware_tested':False,'proprietary_huawei_inputs':False,
            'system_image_rootdir_contents_verified':False}
    report_path=ROOT/'carrera-system-report.json'
    try:
        source=(ROOT/'source').resolve()
        report['source_patches']=apply_patches(source)
        cpus=os.cpu_count() or 1
        memory=os.sysconf('SC_PHYS_PAGES')*os.sysconf('SC_PAGE_SIZE')
        jobs=system_build_jobs(cpus,memory)
        report['build_resources']={'cpus':cpus,'memory_bytes':memory,'jobs':jobs}
        command=('set -eo pipefail; source build/envsetup.sh; lunch lineage_carrera_public-userdebug; '
                 f'm -j{jobs} '+' '.join(MODULES)+' systemimage simg2img')
        report_path.write_text(json.dumps(report,indent=2)+'\n')
        report['build']=guarded(['bash','-c',command],source,ROOT/'carrera-system.log',seconds=18000,reserve=8*1024**3)
        if report['build']['returncode'] or report['build']['stop_reason']:
            report['status']='CARRERA_PUBLIC_SYSTEM_BUILD_FAILED'
        else:
            rel=Path((ROOT/'carrera-product-path.txt').read_text().strip())
            if rel.is_absolute() or '..'in rel.parts:raise ValueError('Unsafe product path')
            product=(source/rel).resolve(strict=True);product.relative_to(source/'out')
            report['legacy_vendor_link']=verify_legacy_vendor_link(product)
            image=product/'system.img'
            if image.is_symlink():raise ValueError('Unexpected image symlink')
            report['image']=image_metadata(image)
            expanded=report['image'].get('expanded_bytes',report['image']['bytes'])
            if expanded>2684354560:raise ValueError('System image exceeds Carrera system partition')
            report['installed_public_modules']=[x for x in inventory(product)if x['path'].startswith('system/')]
            if REQUIRED-{Path(x['path']).name for x in report['installed_public_modules']}:
                raise ValueError('Requested public modules are not all installed in system staging')
            report['system_image_modules']=verify_modules_in_system_image(source,image,report['installed_public_modules'])
            report['rootdir_staging']=[]
            for name in ('fstab.hi3635','init.hi3635.rc','ueventd.hi3635.rc'):
                original=Path(__file__).resolve().parents[1]/'device/huawei/carrera/rootdir'/name
                installed=product/'root'/name
                if installed.is_symlink() or sha256(installed)!=sha256(original):
                    raise ValueError('Carrera system root staging mismatch: '+name)
                report['rootdir_staging'].append({'name':name,'sha256':sha256(installed)})
            ramdisk_report=json.loads((ROOT/'carrera-report.json').read_text())
            ramdisk=product/'ramdisk.img'
            if sha256(ramdisk)!=ramdisk_report['ramdisk_sha256']:
                raise ValueError('Ramdisk changed after cpio verification')
            report['ramdisk_sha256']=sha256(ramdisk)
            report['resolved_manifest_sha256']=sha256(ROOT/'resolved-manifest.xml')
            assets=ROOT/'carrera-system-assets';assets.mkdir()
            compressed=assets/'carrera-public-system.img.gz'
            with image.open('rb')as src,compressed.open('xb')as dst:
                with gzip.GzipFile(filename='',mode='wb',fileobj=dst,compresslevel=1,mtime=0)as gz:
                    shutil.copyfileobj(src,gz,1024*1024)
            if compressed.stat().st_size>=MAX_ASSET:raise ValueError('Release asset exceeds size limit')
            report['compressed_image']={'bytes':compressed.stat().st_size,'sha256':sha256(compressed)}
            with tarfile.open(assets/'public-graphics-modules.tar.gz','w:gz')as tar:
                for item in report['installed_public_modules']:
                    file=product/item['path']
                    if file.is_symlink() or product not in file.resolve().parents or sha256(file)!=item['sha256']:
                        raise ValueError('Module changed after verification')
                    tar.add(file,arcname=item['path'],recursive=False)
            shutil.copyfile(ramdisk,assets/'ramdisk.img')
            shutil.copyfile(ROOT/'resolved-manifest.xml',assets/'resolved-manifest.xml')
            report['status']='PUBLIC_CARRERA_SYSTEM_AND_RAMDISK_BUILT'
            (assets/'carrera-system-report.json').write_text(json.dumps(report,indent=2)+'\n')
            (assets/'README.txt').write_text('Public Carrera Android Q userspace development pair. NOT A COMPLETE ROM. DO NOT FLASH.\n'
                'No Huawei proprietary HALs, kernel or DTB included. No hardware boot or enforcing policy verified.\n'
                f"Ramdisk cpio/rootdir checked; read-only ext4 inspection matched {report['system_image_modules']['modules_verified']} public graphics module hashes.\n"
                'Complete early mount, vendor hardware services, policy and boot integration before any installation.\n')
            (assets/'SHA256SUMS').write_text(''.join(sha256(p)+'  '+p.name+'\n'for p in sorted(assets.iterdir())))
    except Exception as error:
        report.update(status='CARRERA_PUBLIC_SYSTEM_VERIFICATION_FAILED',error=str(error))
    report_path.write_text(json.dumps(report,indent=2)+'\n');print(report_path.read_text())
    return 0 if report['status']=='PUBLIC_CARRERA_SYSTEM_AND_RAMDISK_BUILT' else 1


if __name__=='__main__':raise SystemExit(main())
