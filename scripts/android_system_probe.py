#!/usr/bin/env python3
"""Build and retain a public generic Q system image; never a flashable Carrera ROM."""
import gzip
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
from android_graph_probe import ROOT, guarded
from elf_audit import sha256

MAX_ASSET = 2 * 1024**3


def image_metadata(path):
    size = path.stat().st_size
    with path.open('rb') as stream:
        header = stream.read(28)
    if size < 28:
        raise ValueError('Truncated system image')
    result = {'bytes': size, 'sha256': sha256(path), 'format': 'raw_or_unknown'}
    if struct.unpack_from('<I', header)[0] == 0xed26ff3a:
        magic, major, minor, hdr, chunk, block, blocks, chunks, crc = struct.unpack('<IHHHHIIII', header)
        if major != 1 or hdr < 28 or hdr > size or chunk < 12 or not block or block % 4 or not blocks or not chunks:
            raise ValueError('Invalid sparse header')
        result.update(format='android_sparse', expanded_bytes=block*blocks,
                      chunks=chunks, sparse_major=major, sparse_minor=minor,
                      fits_carrera_system_partition=block*blocks <= 2684354560)
    return result


def main():
    if os.environ.get('GITHUB_ACTIONS') != 'true' or os.environ.get('RUNNER_ENVIRONMENT') != 'github-hosted':
        raise SystemExit('Only public disposable GitHub-hosted runner allowed')
    module_script = Path(__file__).with_name('android_modules_probe.py')
    result = subprocess.run([sys.executable, str(module_script)])
    if result.returncode:
        return result.returncode
    source = (ROOT/'source').resolve()
    report_path = ROOT/'system-report.json'
    report = {'status': 'SYSTEM_BUILD_RUNNING', 'product': 'lineage_arm64-userdebug',
              'carrera_built': False, 'rom_built': False, 'hardware_tested': False,
              'proprietary_huawei_inputs': False}
    report_path.write_text(json.dumps(report, indent=2)+'\n')
    try:
        command = ('set -eo pipefail; source build/envsetup.sh; '
                   'lunch lineage_arm64-userdebug; m -j2 systemimage')
        report['build'] = guarded(['bash','-c',command], source, ROOT/'system.log',
                                  seconds=7200, reserve=8*1024**3)
        if report['build']['returncode'] or report['build']['stop_reason']:
            report['status'] = 'SYSTEM_BUILD_FAILED'
        else:
            relative = Path((ROOT/'product-path.txt').read_text().strip())
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError('Unsafe product path')
            product = (source/relative).resolve(strict=True)
            product.relative_to(source/'out')
            image = product/'system.img'
            if image.is_symlink():
                raise ValueError('Unexpected image symlink')
            report['image'] = image_metadata(image)
            report['resolved_manifest_sha256'] = sha256(ROOT/'resolved-manifest.xml')
            assets = ROOT/'public-base-assets'
            assets.mkdir()
            compressed = assets/'generic-q-system.img.gz'
            with image.open('rb') as src, compressed.open('xb') as dst:
                with gzip.GzipFile(filename='',mode='wb',fileobj=dst,compresslevel=1,mtime=0) as gz:
                    shutil.copyfileobj(src,gz,1024*1024)
            if compressed.stat().st_size >= MAX_ASSET:
                raise ValueError('Compressed asset exceeds GitHub release per-file limit')
            report['compressed_image'] = {'bytes': compressed.stat().st_size,'sha256':sha256(compressed)}
            report['status'] = 'PUBLIC_GENERIC_SYSTEM_IMAGE_BUILT'
            (assets/'PUBLIC-BASE-README.txt').write_text(
                'Generic LineageOS 17.1 / Android Q public-source build base.\n'
                'NOT A HUAWEI MATE S ROM. DO NOT FLASH TO THE PHONE.\n'
                'No Carrera init, policy or complete Huawei hardware integration has been validated.\n'
                'No boot, recovery, DTB, modem, userdata or Huawei proprietary file is included.\n'
                'Use only as a development input after architecture, configuration, ABI and partition review.\n'
                'Resolved source manifest and image SHA256 are included. No hardware test performed.\n')
            shutil.copyfile(ROOT/'resolved-manifest.xml',assets/'resolved-manifest.xml')
            shutil.copyfile(ROOT/'modules-report.json',assets/'modules-report.json')
            (assets/'system-report.json').write_text(json.dumps(report,indent=2)+'\n')
            sums=''.join(sha256(f)+'  '+f.name+'\n' for f in sorted(assets.iterdir()))
            (assets/'SHA256SUMS').write_text(sums)
    except Exception as error:
        report['status']='SYSTEM_IMAGE_VERIFICATION_FAILED'
        report['error']=str(error)
    finally:
        report_path.write_text(json.dumps(report,indent=2)+'\n')
        print(report_path.read_text())
    return 0 if report['status']=='PUBLIC_GENERIC_SYSTEM_IMAGE_BUILT' else 1

if __name__=='__main__':
    raise SystemExit(main())
