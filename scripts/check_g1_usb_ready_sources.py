#!/usr/bin/env python3
"""Recheck immutable public Q USB source and report the readiness boundary."""
import hashlib,json,subprocess
from g1_usb_ready_contract import ROOT,LOCK,load_fixtures,inspect

def main():
    lock=json.loads(LOCK.read_text());files=load_fixtures()
    for name,row in lock['files'].items():
        endpoint=f"repos/{lock['repository']}/contents/{name}?ref={lock['revision']}"
        data=subprocess.check_output(['gh','api','-H','Accept: application/vnd.github.raw+json',endpoint],timeout=45)
        if len(data)>2*1024*1024 or hashlib.sha256(data).hexdigest()!=row['sha256']:
            raise ValueError('Pinned USB source digest mismatch: '+name)
    print(json.dumps(inspect(files),indent=2))
if __name__=='__main__':main()
