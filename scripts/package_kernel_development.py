#!/usr/bin/env python3
"""Retain verified public-source kernel outputs; no boot image or phone commands."""
import json
from pathlib import Path
import shutil
from elf_audit import sha256

ROOT=Path(__file__).resolve().parents[1]


def main():
    assets=ROOT/'out/kernel-public-assets'
    if assets.exists():
        raise ValueError('Choose a new kernel asset directory')
    inputs=[]
    for profile,enabled in (('stock',True),('android10-diagnostic',False)):
        folder=ROOT/('out/kernel-'+profile)
        report_path=folder/'build-report.json'
        report=json.loads(report_path.read_text())
        if report.get('status')!='IMAGE_COMPILED_OFFLINE' or report.get('profile')!=profile:
            raise ValueError('Kernel did not compile: '+profile)
        if any(report.get(k)is not False for k in ('phone_access','boot_image_created','hardware_boot_tested')):
            raise ValueError('Unexpected kernel report scope')
        if report.get('touchscreen_framework_fw_update_enabled')is not enabled:
            raise ValueError('Unexpected touchscreen update control')
        image=folder/'arch/arm64/boot/Image';config=folder/'.config'
        for path,key in ((image,'image_sha256'),(config,'effective_config_sha256')):
            if path.is_symlink() or sha256(path)!=report.get(key):
                raise ValueError('Kernel output changed after verification')
        if image.stat().st_size!=report.get('image_size') or not 1024*1024<image.stat().st_size<32*1024**2:
            raise ValueError('Unexpected kernel size')
        with image.open('rb')as stream:
            if stream.read(64)[56:60]!=b'ARMd':
                raise ValueError('Expected an ARM64 Image')
        inputs.extend(((image,profile+'.Image'),(config,profile+'.config'),
                       (report_path,profile+'-build-report.json')))
    assets.mkdir()
    for path,name in inputs:shutil.copyfile(path,assets/name)
    (assets/'README.txt').write_text(
        'Public Hi3635 kernel development outputs. NOT A ROM. DO NOT FLASH THESE RAW IMAGES.\n'
        'No boot/recovery ramdisk, DTB, modem or Huawei dump is included. No hardware boot verified.\n'
        'The diagnostic profile disables the reviewed touchscreen framework update paths; other driver writes remain to be audited.\n'
        'Stock profile preserves the framework firmware updater and is not the diagnostic boot candidate.\n'
        'Corresponding source revision, compiler, patches and effective configuration are recorded in the reports and repository.\n')
    (assets/'SHA256SUMS').write_text(''.join(sha256(p)+'  '+p.name+'\n'for p in sorted(assets.iterdir())))
    print('Verified public kernel development outputs: '+str(assets))


if __name__=='__main__':main()
