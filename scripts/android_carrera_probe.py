#!/usr/bin/env python3
"""Build source-only Carrera graph and ramdisk; no Huawei files or phone access."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zlib
from android_graph_probe import ROOT, guarded
from boot_inspect import cpio_entries, LIMIT
from elf_audit import sha256

PROJECT = Path(__file__).resolve().parents[1]
FILES = ('fstab.hi3635','init.hi3635.rc','ueventd.hi3635.rc')


def main():
    if os.environ.get('GITHUB_ACTIONS') != 'true' or os.environ.get('RUNNER_ENVIRONMENT') != 'github-hosted':
        raise SystemExit('Only disposable public GitHub-hosted runner allowed')
    if subprocess.run([sys.executable,str(PROJECT/'scripts/android_graph_probe.py')]).returncode:
        return 1
    report_path = ROOT/'carrera-report.json'
    report = {'status':'CARRERA_PUBLIC_BUILD_RUNNING','product':'lineage_carrera_public-userdebug',
              'proprietary_inputs':False,'boot_image_created':False,'rom_built':False,'hardware_tested':False}
    try:
        source = (ROOT/'source').resolve()
        device = PROJECT/'device/huawei/carrera'
        target = source/'device/huawei/carrera'
        if target.exists() or target.is_symlink() or any(p.is_symlink() for p in device.rglob('*')):
            raise ValueError('Unexpected existing overlay or source symlink')
        shutil.copytree(device,target)
        os.environ['MATES_PRODUCT_PATH'] = str((ROOT/'carrera-product-path.txt').resolve())
        cmd = ('set -eo pipefail; source build/envsetup.sh; lunch lineage_carrera_public-userdebug; '
               'test "$(get_build_var PRODUCT_SHIPPING_API_LEVEL)" = 23; '
               'get_build_var PRODUCT_OUT > "$MATES_PRODUCT_PATH"; m -j2 host_init_verifier ramdisk')
        report['build'] = guarded(['bash','-c',cmd],source,ROOT/'carrera.log',seconds=1800,reserve=12*1024**3)
        if report['build']['returncode'] or report['build']['stop_reason']:
            report['status']='CARRERA_PUBLIC_BUILD_FAILED'
        else:
            rel = Path((ROOT/'carrera-product-path.txt').read_text().strip())
            if rel.is_absolute() or '..' in rel.parts:
                raise ValueError('Unsafe product output path')
            product = (source/rel).resolve(strict=True)
            product.relative_to(source/'out')
            verifier = source/'out/host/linux-x86/bin/host_init_verifier'
            env = {**os.environ,'LD_LIBRARY_PATH':str(source/'out/host/linux-x86/lib64')}
            subprocess.run([str(verifier),str(target/'rootdir/init.hi3635.rc')],env=env,check=True,timeout=30)
            ramdisk = product/'ramdisk.img'
            if ramdisk.is_symlink() or ramdisk.stat().st_size > LIMIT:
                raise ValueError('Unexpected ramdisk output')
            dec = zlib.decompressobj(31)
            data = dec.decompress(ramdisk.read_bytes(),LIMIT+1)
            if len(data)>LIMIT or not dec.eof or dec.unused_data or dec.unconsumed_tail:
                raise ValueError('Unsupported ramdisk compression/size')
            entries = {e['name']:e for e in cpio_entries(data)}
            report['rootdir'] = []
            for name in FILES:
                original = device/'rootdir'/name
                installed = product/'root'/name
                expected = sha256(original)
                if installed.is_symlink() or sha256(installed)!=expected or entries.get(name,{}).get('sha256')!=expected:
                    raise ValueError('Rootdir file not preserved in ramdisk: '+name)
                report['rootdir'].append({'name':name,'sha256':expected})
            report.update(status='CARRERA_PUBLIC_RAMDISK_BUILT',native_init_parser_passed=True,
                          ramdisk_bytes=ramdisk.stat().st_size,ramdisk_sha256=sha256(ramdisk),
                          resolved_manifest_sha256=sha256(ROOT/'resolved-manifest.xml'))
            assets = ROOT/'carrera-public-assets';assets.mkdir()
            shutil.copyfile(ramdisk,assets/'ramdisk.img')
            shutil.copyfile(ROOT/'resolved-manifest.xml',assets/'resolved-manifest.xml')
            (assets/'carrera-report.json').write_text(json.dumps(report,indent=2)+'\n')
            (assets/'README.txt').write_text('Source-only Carrera development ramdisk. NOT A ROM. DO NOT FLASH OR BOOT.\n'
                'No kernel, DTB or Huawei proprietary modules. Device SELinux/HAL integration and hardware boot remain unverified.\n'
                'The normal Carrera product still requires locally verified Huawei inputs.\n')
            (assets/'SHA256SUMS').write_text(''.join(sha256(p)+'  '+p.name+'\n' for p in sorted(assets.iterdir())))
    except Exception as error:
        report.update(status='CARRERA_PUBLIC_VERIFICATION_FAILED',error=str(error))
    report_path.write_text(json.dumps(report,indent=2)+'\n')
    print(report_path.read_text())
    return 0 if report['status']=='CARRERA_PUBLIC_RAMDISK_BUILT' else 1

if __name__=='__main__':
    raise SystemExit(main())
