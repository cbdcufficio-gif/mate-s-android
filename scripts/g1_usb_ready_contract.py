"""Inspect pinned Android Q USB readiness source; no USB device accessed."""
import hashlib,json
from pathlib import Path
from g1_first_stage_probe import function
ROOT=Path(__file__).resolve().parents[1]
LOCK=ROOT/'docs/G1-USB-Q-SOURCE-LOCK.json'

def actions(text):
    result={};current=None
    for raw in text.splitlines():
        line=raw.split('#',1)[0].rstrip()
        if line.startswith('on '):
            current=line[3:]
            if current in result:raise ValueError('Duplicate init action: '+current)
            result[current]=[]
        elif line.startswith((' ','\t')) and line.strip() and current is not None:result[current].append(line.strip())
        elif line and not line.startswith((' ','\t')):current=None
    return result

def inspect(files):
    root=files['rootdir/init.rc']
    if 'import /init.usb.rc' not in root or 'import /init.usb.configfs.rc' not in root:raise ValueError('Missing pinned USB imports')
    legacy=actions(files['rootdir/init.usb.rc'])
    conf=actions(files['rootdir/init.usb.configfs.rc'])
    on=legacy['property:sys.usb.config=adb && property:sys.usb.configfs=0']
    off=legacy['property:sys.usb.config=none && property:sys.usb.configfs=0']
    if on.index('write /sys/class/android_usb/android0/enable 1')>=on.index('start adbd'):raise ValueError('Legacy ordering changed')
    manager=function(files['init/action_manager.cpp'],'void ActionManager::ExecuteOneCommand()')
    if 'for (const auto& action : actions_)' not in manager or 'current_executing_actions_.emplace(action.get())' not in manager:raise ValueError('Init action queue semantics changed')
    stopped=conf['property:init.svc.adbd=stopped']
    if 'setprop sys.usb.ffs.ready 0' not in stopped:raise ValueError('Missing unconditional adbd stop reset')
    body=function(files['adb/daemon/usb_ffs.cpp'],'bool open_functionfs(')
    if body.count('SetProperty("sys.usb.ffs.ready", "1")')!=1:raise ValueError('Unexpected readiness writes')
    marker='SetProperty("sys.usb.ffs.ready", "1")'
    strings='adb_write(control.get(), &strings, sizeof(strings))'
    bulkout='bulk_out.reset(adb_open(USB_FFS_ADB_OUT, O_RDONLY))'
    bulkin='bulk_in.reset(adb_open(USB_FFS_ADB_IN, O_WRONLY))'
    if not (body.index(strings)<body.index(marker)<body.index(bulkout)<body.index(bulkin)):raise ValueError('FunctionFS readiness ordering changed')
    if 'if (out_control->get() < 0)' not in body[:body.index(marker)]:raise ValueError('Control endpoint reuse branch missing')
    return {'status':'PINNED_Q_USB_READINESS_SOURCE_REVIEWED','generic_legacy_enables_before_start':True,'ready_written_after_descriptors_and_strings':True,'ready_written_before_bulk_endpoint_opens':True,'ready_written_only_when_control_reinitialized':True,'global_adbd_stopped_trigger_resets_ready':True,'configfs_file_imported_by_init_rc':True,'all_matching_actions_are_enqueued':True,'legacy_none_action_resets_ready_explicitly':'setprop sys.usb.ffs.ready 0' in off,'limitations':['Static source ordering only; no init scheduling or property service executed','Descriptor readiness alone does not prove bulk endpoints, USB transport or authenticated shell']}

def load_fixtures():
    lock=json.loads(LOCK.read_text());files={}
    for name,row in lock['files'].items():
        data=(ROOT/row['fixture']).read_bytes()
        if hashlib.sha256(data).hexdigest()!=row['sha256']:raise ValueError('Fixture digest mismatch: '+name)
        files[name]=data.decode()
    return files
