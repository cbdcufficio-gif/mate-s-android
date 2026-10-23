#!/usr/bin/env python3
"""Build the tiny static ARM64 kernel query probe; never accesses the phone."""
import argparse
import json
from pathlib import Path
import struct
import subprocess
from elf_audit import sha256


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--compiler',default='clang-19')
    p.add_argument('--linker',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():p.error('Output directory must be new')
    source=Path(__file__).resolve().parents[1]/'native/kernel_readonly_probe.c'
    # Preserve ld.lld's basename: resolving its symlink to lld changes driver mode.
    linker=a.linker.absolute()
    if not linker.is_file():p.error('Linker does not exist')
    a.out.mkdir(parents=True)
    binary=a.out/'kernel-readonly-probe'
    command=[a.compiler,'--target=aarch64-linux-gnu','-std=c11','-Os','-ffreestanding',
             '-fno-builtin','-fno-stack-protector','-nostdlib','-static','-fno-pie',
             '--ld-path='+str(linker),'-Wl,-e,_start',
             '-Wl,--build-id=none','-Wall','-Wextra','-Werror',str(source),'-o',str(binary)]
    subprocess.run(command,check=True,timeout=60)
    data=binary.read_bytes()
    if data[:6]!=b'\x7fELF\x02\x01' or struct.unpack_from('<H',data,18)[0]!=183:
        raise ValueError('Not an ARM64 ELF executable')
    phoff=struct.unpack_from('<Q',data,32)[0];phents,phnum=struct.unpack_from('<HH',data,54)
    if any(struct.unpack_from('<I',data,phoff+i*phents)[0]==3 for i in range(phnum)):
        raise ValueError('Unexpected dynamic interpreter')
    report={'status':'STATIC_ARM64_PROBE_BUILT','source_sha256':sha256(source),
            'binary_sha256':sha256(binary),'bytes':len(data),'phone_access':False}
    (a.out/'build-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':main()
