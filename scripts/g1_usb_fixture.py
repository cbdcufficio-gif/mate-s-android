"""Compile unchanged pinned Q selector/handle/fallback bodies with explicit stubs."""
import subprocess
from pathlib import Path
from g1_contract_common import ROOT,source,function,sha

def trigger_fixture(text):
    actions={};current=None
    for raw in text.splitlines():
        line=raw.split('#',1)[0].rstrip()
        if line.startswith('on '):current=line[3:];actions[current]=[]
        elif line.startswith((' ','\t')) and line.strip() and current is not None:actions[current].append(line.strip())
    commands=actions['property:sys.usb.config=adb && property:sys.usb.configfs=0']
    enabled=next(i for i,c in enumerate(commands) if c=='write /sys/class/android_usb/android0/enable 1')
    started=commands.index('start adbd')
    assert enabled<started, 'Pinned generic fallback order changed; reassess Carrera integration'
    off=actions['property:sys.usb.config=none && property:sys.usb.configfs=0']
    assert 'stop adbd' in off and 'write /sys/class/android_usb/android0/enable 0' in off
    # Proposed Carrera ordering is a state-machine fixture only, not installed init.
    def candidate(prepared,ready):return ['start adbd']+(['enable gadget'] if prepared and ready else [])
    assert 'enable gadget' not in candidate(True,False)
    assert 'enable gadget' not in candidate(False,True)
    assert candidate(True,True)==['start adbd','enable gadget']
    return {'status':'PINNED_Q_GENERIC_USB_ORDER_CAPTURED','source_sha256':sha(text.encode()),'generic_action':commands,'generic_enables_before_adbd':True,'candidate_state_cases':['prepared without ready stays disabled','ready without mount/aliases stays disabled','prepared and ready enables after adbd'],'limitation':'Generic action parsed as a fixture; no Android init engine executed. Carrera override, labels and property triggers not installed'}

def execute(directory):
    triggers=trigger_fixture(source('rootdir/init.usb.rc'))
    modern=source('adb/daemon/usb.cpp');legacy=source('adb/daemon/usb_legacy.cpp');ffs=source('adb/daemon/usb_ffs.cpp')
    init=function(modern,'void usb_init()');handle=function(legacy,'usb_handle* create_usb_handle(')
    fallback=function(ffs,'if (adb_write(control.get(), &v2_descriptor, sizeof(v2_descriptor)) < 0)')
    text=(ROOT/'tests/fixtures/q_usb_compat_harness.cpp.in').read_text()
    text=text.replace('__USB_INIT__',init).replace('__CREATE_HANDLE__',handle).replace('__DESCRIPTOR_FALLBACK__',fallback)
    cpp=directory/'usb.cpp';cpp.write_text(text);binary=directory/'usb-fixture'
    subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
    return {'status':'PINNED_Q_USB_COMPAT_FIXTURE_PASSED','sources':{'usb.cpp':sha(modern.encode()),'usb_legacy.cpp':sha(legacy.encode()),'usb_ffs.cpp':sha(ffs.encode())},'cases':['default nonblocking path','explicit legacy path','persistent property overrides read-only property','sync read/write selected without AIO initialization','default AIO path','v2 descriptor succeeds','v2 failure then v1 succeeds','both descriptor versions fail'],'trigger_fixture':triggers,'properties_applied':False,'hardware_usb_verified':False,'limitations':['Property/thread/endpoint/descriptor syscall interfaces stubbed','No USB request transferred, no target kernel or complete init-trigger execution']}
