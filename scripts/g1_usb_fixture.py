"""Compile unchanged pinned Q selector/handle/fallback bodies with explicit stubs."""
import subprocess
from pathlib import Path
from g1_contract_common import ROOT,source,function,sha

def execute(directory):
    modern=source('adb/daemon/usb.cpp');legacy=source('adb/daemon/usb_legacy.cpp');ffs=source('adb/daemon/usb_ffs.cpp')
    init=function(modern,'void usb_init()');handle=function(legacy,'usb_handle* create_usb_handle(')
    fallback=function(ffs,'if (adb_write(control.get(), &v2_descriptor, sizeof(v2_descriptor)) < 0)')
    text=(ROOT/'tests/fixtures/q_usb_compat_harness.cpp.in').read_text()
    text=text.replace('__USB_INIT__',init).replace('__CREATE_HANDLE__',handle).replace('__DESCRIPTOR_FALLBACK__',fallback)
    cpp=directory/'usb.cpp';cpp.write_text(text);binary=directory/'usb-fixture'
    subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
    return {'status':'PINNED_Q_USB_COMPAT_FIXTURE_PASSED','sources':{'usb.cpp':sha(modern.encode()),'usb_legacy.cpp':sha(legacy.encode()),'usb_ffs.cpp':sha(ffs.encode())},'cases':['default nonblocking path','explicit legacy path','persistent property overrides read-only property','sync read/write selected without AIO initialization','default AIO path','v2 descriptor succeeds','v2 failure then v1 succeeds','both descriptor versions fail'],'properties_applied':False,'hardware_usb_verified':False,'limitations':['Property/thread/endpoint/descriptor syscall interfaces stubbed','No USB request transferred, no target kernel or complete init-trigger execution']}
