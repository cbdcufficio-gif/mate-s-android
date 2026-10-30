"""Verify an experimental init USB patch in a temporary tree; no device writes."""
import hashlib,subprocess,tempfile
from pathlib import Path
from g1_usb_ready_contract import ROOT,actions,load_fixtures
PATCH=ROOT/'patches/experimental/lineage-q-usb-ready-candidate.patch'
CONFIG='property:sys.usb.config=adb && property:sys.usb.configfs=0'
READY='property:sys.usb.ffs.ready=1 && property:sys.usb.config=adb && property:sys.usb.configfs=0'
ENABLE='write /sys/class/android_usb/android0/enable 1'
STATE='setprop sys.usb.state ${sys.usb.config}'

def patched_candidate():
    original=load_fixtures()['rootdir/init.usb.rc']
    with tempfile.TemporaryDirectory() as directory:
        root=Path(directory);path=root/'system/core/rootdir/init.usb.rc';path.parent.mkdir(parents=True);path.write_text(original)
        subprocess.run(['git','apply','--check',str(PATCH)],cwd=root,check=True,capture_output=True)
        subprocess.run(['git','apply',str(PATCH)],cwd=root,check=True,capture_output=True)
        return original,path.read_text()

def verify(original,candidate):
    old=actions(original);new=actions(candidate)
    if set(new)!=set(old)|{READY}:raise ValueError('Unexpected action added or removed')
    for name in old:
        if name!=CONFIG and old[name]!=new[name]:raise ValueError('Unrelated USB action changed: '+name)
    expected=[x for x in old[CONFIG] if x not in (ENABLE,STATE)]
    if new[CONFIG]!=expected:raise ValueError('Unexpected legacy setup command change')
    if new[READY]!=[ENABLE,STATE]:raise ValueError('Unexpected ready-stage commands')
    if candidate.count('service adbd ')!=1 or candidate.split('service adbd ',1)[1].split('\non ',1)[0]!=original.split('service adbd ',1)[1].split('\non ',1)[0]:raise ValueError('ADB service altered')
    return {'status':'EXPERIMENTAL_USB_INIT_ACTION_SOURCE_CHECKED','patch_sha256':hashlib.sha256(PATCH.read_bytes()).hexdigest(),'generic_early_enable_removed_in_candidate':True,'unrelated_actions_unchanged':True,'installed_to_product':False,'runtime_usb_verified':False,'limitations':['Property action scheduling and ready reset races unverified','Ready indicates descriptors, not successful bulk endpoints','No FunctionFS mount/alias, authentication or hardware test']}

def main():
    import json
    old,new=patched_candidate();print(json.dumps(verify(old,new),indent=2))
if __name__=='__main__':main()
