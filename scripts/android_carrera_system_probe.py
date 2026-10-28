#!/usr/bin/env python3
"""Build the public Carrera system/ramdisk pair, without proprietary Huawei inputs."""
import gzip
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import struct
import sys
import tarfile
import tempfile
import time
from android_graph_probe import ROOT,guarded
from android_modules_probe import MODULES,REQUIRED,inventory
from android_patches import apply_patches
from android_system_probe import image_metadata,MAX_ASSET
from elf_audit import sha256


def system_build_jobs(cpus, memory_bytes):
    # Leave a core and at least 4 GiB per build slot on the standard runner.
    return 3 if cpus >= 4 and memory_bytes >= 12*1024**3 else 2


def system_image_path(staged_path, layout='legacy-system-root'):
    relative=Path(staged_path)
    if relative.is_absolute() or '..' in relative.parts or not relative.parts or relative.parts[0]!='system':
        raise ValueError('Unsafe or unexpected module path in system staging')
    if any(not re.fullmatch(r'[A-Za-z0-9_.+-]+',part) for part in relative.parts):
        raise ValueError('Unexpected character in public module path')
    if layout=='legacy-system-root':
        return '/'+str(relative.relative_to('system'))
    if layout=='q-root-with-system':
        return '/'+str(relative)
    raise ValueError('Unsupported system image layout')


def verify_legacy_vendor_link(product):
    link=product/'root'/'vendor'
    if not link.is_symlink():
        raise ValueError('Legacy product root is missing the /vendor symlink')
    target=os.readlink(link)
    if target!='/system/vendor':
        raise ValueError('Unexpected legacy /vendor symlink target: '+target)
    return {'path':'root/vendor','target':target}


def sparse_expansion_budget(image):
    """Bound RAW/FILL writes; pinned simg2img seeks over DONT_CARE holes."""
    size=image.stat().st_size
    with image.open('rb') as stream:
        header=stream.read(28)
        if len(header)!=28:
            raise ValueError('Truncated Android sparse header')
        magic,major,minor,file_header,chunk_header,block_size,total_blocks,chunks,checksum=struct.unpack('<IHHHHIIII',header)
        if magic!=0xed26ff3a or major!=1 or file_header<28 or chunk_header<12 or not block_size or block_size%4:
            raise ValueError('Unsupported Android sparse geometry')
        expanded=block_size*total_blocks
        if expanded>2684354560 or file_header>size:
            raise ValueError('Sparse output exceeds Carrera system geometry')
        stream.seek(file_header)
        output_blocks=0
        allocated=0
        kinds={'raw':0,'fill':0,'dont_care':0,'crc32':0}
        for index in range(chunks):
            start=stream.tell()
            data=stream.read(chunk_header)
            if len(data)!=chunk_header:
                raise ValueError('Truncated Android sparse chunk header')
            kind,reserved,blocks,total_size=struct.unpack('<HHII',data[:12])
            length=blocks*block_size
            if kind==0xcac1:
                expected=chunk_header+length
                allocated+=length
                kinds['raw']+=1
            elif kind==0xcac2:
                expected=chunk_header+4
                allocated+=length  # Count even zero FILL: simg2img writes it.
                kinds['fill']+=1
            elif kind==0xcac3:
                expected=chunk_header
                kinds['dont_care']+=1
            elif kind==0xcac4 and blocks==0:
                expected=chunk_header+4
                kinds['crc32']+=1
            else:
                raise ValueError('Unsupported Android sparse chunk type')
            if total_size!=expected or start+total_size>size:
                raise ValueError('Truncated or inconsistent Android sparse chunk')
            output_blocks+=blocks
            if output_blocks>total_blocks:
                raise ValueError('Android sparse output block count exceeded')
            stream.seek(start+total_size)
        if output_blocks!=total_blocks or stream.tell()!=size:
            raise ValueError('Android sparse chunk totals or file length differ')
    fragment=os.statvfs(ROOT).f_frsize
    if fragment<=0 or fragment>1024**2:
        raise ValueError('Unsupported host filesystem allocation unit')
    # Account for extent rounding/metadata and delayed-allocation slack.
    slack=64*1024**2+2*max(fragment,4096)*(chunks+1)
    return {'logical_bytes':expanded,'raw_and_fill_bytes':allocated,
            'dont_care_bytes':expanded-allocated,'chunk_types':kinds,
            'allocation_slack_bytes':slack,'allocation_budget_bytes':allocated+slack,
            'reserve_bytes':8*1024**3,'host_fragment_bytes':fragment}


def inspect_system_image_layout(debugfs, raw):
    """Identify the filesystem layout; this does not certify runtime mounts."""
    observed={}
    for path in ('/system','/lib'):
        result=subprocess.run([debugfs,'-R','stat '+path,str(raw)],stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT,text=True,timeout=60)
        if result.returncode:
            raise ValueError('Cannot inspect system ext4 directory: '+path)
        match=re.search(r'Type:\s+([A-Za-z]+)',result.stdout)
        if match:
            observed[path]=match.group(1)
        elif 'File not found' in result.stdout:
            observed[path]='absent'
        else:
            raise ValueError('Unrecognized system ext4 directory metadata: '+path)
    if observed=={'/system':'directory','/lib':'absent'}:
        layout='q-root-with-system'
    elif observed=={'/system':'absent','/lib':'directory'}:
        layout='legacy-system-root'
    else:
        raise ValueError('Ambiguous or unsupported system ext4 layout: '+str(observed))
    listing=subprocess.run([debugfs,'-R','ls -p /',str(raw)],stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT,text=True,timeout=60)
    if listing.returncode:
        raise ValueError('Cannot inventory system ext4 root')
    return {'layout':layout,'directory_types':observed,
            'root_listing':listing.stdout[:8192],'runtime_mounts_verified':False}


def verify_modules_in_system_image(source,image,modules):
    # Child conversion runs inside the Android source tree, not the caller cwd.
    source=Path(source).resolve(strict=True)
    image=Path(image).resolve(strict=True)
    debugfs=shutil.which('debugfs')
    if not debugfs:
        raise ValueError('debugfs is required to inspect the Carrera system ext4 image')
    metadata=image_metadata(image)
    with tempfile.TemporaryDirectory(prefix='carrera-ext4-',dir=ROOT.resolve()) as temp:
        raw=image
        space=None
        if metadata['format']=='android_sparse':
            space=sparse_expansion_budget(image)
            space['free_bytes_before']=shutil.disk_usage(ROOT).free
            space_path=ROOT/'carrera-ext4-space.json'
            space_path.write_text(json.dumps(space,indent=2)+'\n')
            if space['free_bytes_before'] < space['allocation_budget_bytes']+8*1024**3:
                raise ValueError('Insufficient physical space to inspect sparse ext4 while retaining 8 GiB')
            simg2img=source/'out/host/linux-x86/bin/simg2img'
            if not simg2img.is_file():
                raise ValueError('Android simg2img host tool is missing')
            raw=Path(temp)/'system.raw.img'
            space['converter_cwd']=str(source)
            space['converter_input']=str(image)
            space['converter_output']=str(raw)
            space_path.write_text(json.dumps(space,indent=2)+'\n')
            conversion=guarded([str(simg2img),str(image),str(raw)],source,
                               ROOT/'carrera-ext4-convert.log',seconds=180,reserve=8*1024**3)
            space['conversion']=conversion
            if conversion['returncode'] or conversion['stop_reason']:
                space_path.write_text(json.dumps(space,indent=2)+'\n')
                raise ValueError('Sparse ext4 conversion failed: '+str(conversion))
            with raw.open('rb') as stream:
                os.fsync(stream.fileno())
            space['actual_allocated_bytes']=raw.stat().st_blocks*512
            space['free_bytes_after']=shutil.disk_usage(ROOT).free
            space_path.write_text(json.dumps(space,indent=2)+'\n')
            if raw.stat().st_size!=space['logical_bytes'] or space['actual_allocated_bytes']>space['allocation_budget_bytes']:
                raise ValueError('Sparse ext4 allocation exceeded its validated budget')
            if space['free_bytes_after']<8*1024**3:
                raise ValueError('Sparse ext4 conversion did not retain 8 GiB')
        with raw.open('rb') as stream:
            stream.seek(1024+56)
            if stream.read(2)!=b'\x53\xef':
                raise ValueError('System image is not an ext4 filesystem')
        layout_evidence=inspect_system_image_layout(debugfs,raw)
        layout=layout_evidence['layout']
        extracted=[]
        for index,item in enumerate(modules):
            image_path=system_image_path(item['path'],layout)
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
    vendor_prefix=system_image_path('system/vendor',layout)+'/'
    if not extracted or not any(item['path'].startswith(vendor_prefix) for item in extracted):
        raise ValueError('No public vendor module verified inside system ext4')
    return {'filesystem':'ext4','format':metadata['format'],'modules_verified':len(extracted),
            'layout_evidence':layout_evidence,'expansion_space':space,'modules':extracted}


def build_system_phases(source, jobs, report, budget=18000):
    """Finish installed dependencies before releasing cache for image assembly.

    Q core/Makefile makes installed-file-list depend on FULL_SYSTEMIMAGE_DEPS.
    The second phase retains normal systemimage dependencies (never snod).
    Both phases share one wall-clock budget and the unchanged 8 GiB reserve.
    """
    started=time.monotonic()
    report['build_phases']=[]
    prefix='set -eo pipefail; source build/envsetup.sh; lunch lineage_carrera_public-userdebug; '
    def persist():
        (ROOT/'carrera-system-report.json').write_text(json.dumps(report,indent=2)+'\n')
    def phase(name, targets, log):
        remaining=budget-(time.monotonic()-started)
        if remaining<=0:
            result={'returncode':-15,'stop_reason':'TIME_BUDGET_REACHED',
                    'seconds':0,'free_bytes':shutil.disk_usage(ROOT).free}
        else:
            result=guarded(['bash','-c',prefix+f'm -j{jobs} '+targets], source,
                           ROOT/log, seconds=remaining, reserve=8*1024**3)
        report['build_phases'].append({'name':name,**result})
        persist()
        return result
    prepared=phase('installed_dependencies',
                   ' '.join(MODULES)+' installed-file-list simg2img',
                   'carrera-system-prepare.log')
    if os.environ.get('MATES_USE_CCACHE')=='1':
        with (ROOT/'ccache-before-cleanup.log').open('w') as stats:
            captured=subprocess.run(['ccache','--show-stats','--verbose'],stdout=stats,
                                    stderr=subprocess.STDOUT,check=False,timeout=30)
        if captured.returncode:
            raise ValueError('Compiler cache statistics could not be saved')
    if prepared['returncode'] or prepared['stop_reason']:
        return {**prepared,'seconds':round(time.monotonic()-started,1)}
    if os.environ.get('MATES_USE_CCACHE')=='1':
        cache=ROOT.parent/'ccache'
        if cache.is_symlink() or not cache.is_dir() or Path(os.environ.get('CCACHE_DIR','')).resolve()!=cache.resolve():
            raise ValueError('Unexpected compiler cache path')
        before=shutil.disk_usage(ROOT).free
        shutil.rmtree(cache)
        after=shutil.disk_usage(ROOT).free
        report['compiler_cache_removed_before_system_image']=True
        report['compiler_cache_reclaim']={'free_bytes_before':before,'free_bytes_after':after,
                                          'observed_free_delta_bytes':after-before}
        persist()
    built=phase('system_image',
                ' '.join(MODULES)+' systemimage simg2img',
                'carrera-system.log')
    return {**built,'seconds':round(time.monotonic()-started,1)}


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
        report_path.write_text(json.dumps(report,indent=2)+'\n')
        report['build']=build_system_phases(source,jobs,report)
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
