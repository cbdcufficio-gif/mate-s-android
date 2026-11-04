#!/usr/bin/env python3
"""Recheck immutable public Q USB source and report the readiness boundary."""
import hashlib,json,subprocess
from g1_usb_ready_contract import ROOT,LOCK,load_fixtures,inspect
from g1_first_stage_probe import function

def main():
    lock=json.loads(LOCK.read_text());files=load_fixtures()
    for name,row in lock['files'].items():
        endpoint=f"repos/{lock['repository']}/contents/{name}?ref={lock['revision']}"
        data=subprocess.check_output(['gh','api','-H','Accept: application/vnd.github.raw+json',endpoint],timeout=45)
        if len(data)>2*1024*1024 or hashlib.sha256(data).hexdigest()!=row['sha256']:
            raise ValueError('Pinned USB source digest mismatch: '+name)
    endpoint='repos/hi3635-dev/android_kernel_huawei_liszt/contents/drivers/usb/gadget/f_fs.c?ref=3fe1625bed89c034996842c1af696ba9bc50d8a9'
    data=subprocess.check_output(['gh','api','-H','Accept: application/vnd.github.raw+json',endpoint],timeout=45)
    if len(data)>2*1024*1024 or hashlib.sha256(data).hexdigest()!='220024748f2f28e4f63f2e1ad8f26b71a269047b639fdbbe8a2d3d740350b788':
        raise ValueError('Pinned Huawei FunctionFS source digest mismatch')
    actual=function(data.decode(),'static int ffs_fs_parse_opts(').strip()
    if actual!=(ROOT/'tests/fixtures/huawei_ffs_parse_opts.c').read_text().strip():
        raise ValueError('Huawei FunctionFS parser differs from fixture')
    print(json.dumps(inspect(files),indent=2))
    print('PINNED_HUAWEI_FUNCTIONFS_PARSER_VERIFIED')
    adapter=json.loads((ROOT/'docs/G1-USB-ADAPTER-SOURCES.json').read_text())
    for name,row in adapter['files'].items():
        endpoint=f"repos/{adapter['repository']}/contents/{name}?ref={adapter['revision']}"
        data=subprocess.check_output(['gh','api','-H','Accept: application/vnd.github.raw+json',endpoint],timeout=45)
        if len(data)>2*1024*1024 or hashlib.sha256(data).hexdigest()!=row['sha256']:
            raise ValueError('Pinned Q adapter source digest mismatch: '+name)
        if 'fixture' in row and data!=(ROOT/row['fixture']).read_bytes():
            raise ValueError('Q adapter header differs from fixture: '+name)
        if 'required_line' in row and row['required_line'] not in data.decode().splitlines():
            raise ValueError('Q init context constant mismatch')
    alias=json.loads((ROOT/'docs/G1-USB-ALIAS-SOURCE.json').read_text())
    endpoint=f"repos/{alias['repository']}/contents/{alias['path']}?ref={alias['revision']}"
    data=subprocess.check_output(['gh','api','-H','Accept: application/vnd.github.raw+json',endpoint],timeout=45)
    if len(data)>2*1024*1024 or hashlib.sha256(data).hexdigest()!=alias['sha256']:
        raise ValueError('Pinned Huawei alias source digest mismatch')
    print('PINNED_Q_ADAPTER_HEADERS_AND_HUAWEI_ALIAS_VERIFIED')
if __name__=='__main__':main()
