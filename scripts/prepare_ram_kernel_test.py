#!/usr/bin/env python3
"""Prepare a LOCAL TWRP/kernel diagnostic candidate. Never boots or flashes it."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from boot_inspect import align, inspect
from build_kernel import config_values
from elf_audit import sha256

PROJECT=Path(__file__).resolve().parents[1]
OFFICIAL_BYTES=25040896
OFFICIAL_SHA256='a60b7392b9eeb3c2e8ac69310f20de67d8f24c60f5eb117488f83b5e16b7fb87'


def pack(header,kernel,ramdisk):
    header=bytearray(header)
    if len(header)!=2048 or header[:8]!=b'ANDROID!' or not 64<=len(kernel)<32*1024**2:
        raise ValueError('Unexpected legacy header or kernel size')
    struct.pack_into('<I',header,8,len(kernel))
    sha=hashlib.sha1()
    for data in (kernel,ramdisk,b''):
        sha.update(data);sha.update(struct.pack('<I',len(data)))
    header[576:608]=sha.digest()+bytes(12)
    result=bytes(header)
    for data in (kernel,ramdisk):
        result+=data+bytes(align(len(data),2048)-len(data))
    return result


def replace_kernel(original,kernel):
    old=inspect(original)
    if not old['legacy_sha1_id_matches'] or old['page_size']!=2048 or old['components']['second']['bytes'] or old['tail']['bytes']:
        raise ValueError('Unsupported source recovery layout, tail or SHA1')
    c=old['components'];k=c['kernel'];r=c['ramdisk']
    previous=original[k['offset']:k['offset']+k['bytes']]
    ramdisk=original[r['offset']:r['offset']+r['bytes']]
    if previous[56:60]!=b'ARMd' or kernel[56:60]!=b'ARMd' or previous[8:32]!=kernel[8:32]:
        raise ValueError('Kernel load offset/size/flags differ from the recovery ABI')
    if pack(original[:2048],previous,ramdisk)!=original:
        raise ValueError('Legacy format roundtrip is not bit-identical')
    result=pack(original[:2048],kernel,ramdisk)
    if len(result)>33554432:
        raise ValueError('Candidate exceeds the known recovery geometry')
    new=inspect(result)
    if not new['legacy_sha1_id_matches'] or new['components']['ramdisk']['sha256']!=r['sha256']:
        raise ValueError('Candidate integrity check failed')
    return result,new


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--recovery-dump',type=Path,required=True)
    p.add_argument('--kernel-directory',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():p.error('Output directory must be new')
    original=a.recovery_dump.read_bytes()[:OFFICIAL_BYTES]
    if hashlib.sha256(original).hexdigest()!=OFFICIAL_SHA256:
        raise ValueError('Recovery prefix differs from official Carrera TWRP 2.8.7.0')
    folder=a.kernel_directory
    report=json.loads((folder/'android10-diagnostic-build-report.json').read_text())
    image=folder/'android10-diagnostic.Image';config=folder/'android10-diagnostic.config'
    lock=json.loads((PROJECT/'sources.lock.json').read_text())
    touch=json.loads((PROJECT/'configs/kernel-touch-update.json').read_text())
    expected=next(x['commit']for x in lock['repositories']if x['directory']=='kernel-hi3635')
    if (report.get('status')!='IMAGE_COMPILED_OFFLINE' or report.get('profile')!='android10-diagnostic'
            or report.get('kernel_commit')!=expected or report.get('touchscreen_framework_fw_update_enabled')is not False
            or report.get('touchscreen_patch_sha256')!=touch['patch_sha256']):
        raise ValueError('Unexpected diagnostic kernel provenance or firmware control')
    if image.is_symlink() or config.is_symlink() or sha256(image)!=report.get('image_sha256') or sha256(config)!=report.get('effective_config_sha256'):
        raise ValueError('Kernel/config checksum mismatch')
    actual=config_values(config)
    requested=config_values(PROJECT/'configs/android10-diagnostic.fragment')
    if any(actual.get(k,'n')!=v for k,v in requested.items()):
        raise ValueError('Diagnostic kernel configuration mismatch')
    result,meta=replace_kernel(original,image.read_bytes())
    a.out.mkdir(parents=True)
    candidate=a.out/'twrp-diagnostic-ram-test.img'
    candidate.write_bytes(result)
    summary={'status':'LOCAL_KERNEL_RAM_BOOT_CANDIDATE_NOT_TESTED',
             'rom_built':False,'android_q_boot_tested':False,'hardware_boot_tested':False,
             'recovery_partition_update_required':False,'flash_commands_executed':False,
             'source_official_recovery_sha256':OFFICIAL_SHA256,'source_recovery_bytes':OFFICIAL_BYTES,
             'kernel_sha256':report['image_sha256'],'kernel_commit':expected,
             'touchscreen_framework_fw_update_enabled':False,'bytes':len(result),'sha256':sha256(candidate),
             'legacy_sha1_matches':meta['legacy_sha1_id_matches'],
             'ramdisk_preserved_sha256':meta['components']['ramdisk']['sha256'],
             'note':'Existing TWRP ramdisk/cmdline retained only for a kernel diagnostic; not a ROM or a persistent recovery update. Fastboot RAM boot support still unverified.'}
    (a.out/'report.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
