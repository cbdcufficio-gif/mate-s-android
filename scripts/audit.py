#!/usr/bin/env python3
"""Read-only Android-port inventory. No mount, su, reboot or partition writes."""
import argparse, subprocess, pathlib, json, hashlib, shutil, platform
p=argparse.ArgumentParser();p.add_argument('--serial',required=True);p.add_argument('--out',required=True);a=p.parse_args()
o=pathlib.Path(a.out);o.mkdir(parents=True,exist_ok=False)
if not shutil.which('adb'): raise SystemExit('Installare adb; nessuna acquisizione eseguita')
commands={
 'mounts':'cat /proc/mounts',
 'stock-properties':'for f in /system/build.prop /system/system/build.prop /vendor/build.prop /system/vendor/build.prop; do echo "=== $f"; if [ -r "$f" ]; then cat "$f"; else echo MISSING_OR_UNMOUNTED; fi; done',
 'hal-inventory':'for p in /system/lib/hw /system/lib64/hw /system/vendor/lib/hw /system/vendor/lib64/hw /vendor/lib/hw /vendor/lib64/hw /system/lib/egl /system/lib64/egl; do echo "=== $p"; ls -l "$p"; done',
 'vendor-layout':'ls -ld /system /system/vendor /vendor; ls -l /system/lib/lib*ril* /system/lib64/lib*ril* /system/lib/lib*gralloc* /system/lib64/lib*gralloc*',
 'kernel':'uname -a; cat /proc/cmdline',
}
status={}
for name,cmd in commands.items():
 try:
  r=subprocess.run(['adb','-s',a.serial,'shell',cmd],capture_output=True,timeout=45)
  (o/(name+'.txt')).write_bytes(r.stdout+r.stderr)
  status[name]={'returncode':r.returncode,'note':'Old adbd may return zero on missing files; inspect text.'}
 except subprocess.TimeoutExpired: status[name]={'error':'timeout'}
host={'machine':platform.machine(),'free_bytes':shutil.disk_usage(o).free,'meminfo':pathlib.Path('/proc/meminfo').read_text()}
(o/'host.json').write_text(json.dumps(host,indent=2));(o/'status.json').write_text(json.dumps(status,indent=2))
files=sorted(o.iterdir());(o/'SHA256SUMS').write_text(''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+f.name+'\n' for f in files))
print(o.resolve());print('Missing /system files do not mean absent blobs: system may be unmounted. No mount attempted.')
