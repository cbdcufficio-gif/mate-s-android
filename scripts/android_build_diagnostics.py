#!/usr/bin/env python3
"""Bounded public CI diagnostics; allowlisted files, no images or source trees."""
import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess

MARKER='MATES_PUBLIC_DIAGNOSTICS_V1'
MAX_INPUT=32*1024**2
MAX_TOTAL=16*1024**2


def collect(root, destination):
    destination.mkdir(parents=True,exist_ok=False)
    names=['report.json','carrera-report.json','carrera-system-report.json','resolved-manifest.xml',
           'ccache-before-cleanup.log','ccache-environment.log']
    names += [p+'.log' for p in ('init','sync','graph','webview-lfs-arm','webview-lfs-arm64','carrera','carrera-system')]
    files=[(root/name,name) for name in names]
    files += [(root/'source/out'/p,'ninja-'+p.replace('/','-')) for p in ('.ninja_log','soong/.ninja_log')]
    inventory=[]
    for file,name in files:
        if not file.is_file() or file.is_symlink():continue
        size=file.stat().st_size
        with file.open('rb') as stream:
            if size<=MAX_INPUT:data=stream.read(MAX_INPUT)
            else:
                data=stream.read(MAX_INPUT//2)+b'\nDIAGNOSTIC_MIDDLE_TRUNCATED\n'
                stream.seek(-MAX_INPUT//2,2);data+=stream.read(MAX_INPUT//2)
        target=destination/(name+'.gz')
        with target.open('wb') as raw:
            with gzip.GzipFile(filename='',fileobj=raw,mode='wb',compresslevel=1,mtime=0) as gz:gz.write(data)
        inventory.append({'name':name,'input_bytes':size,'truncated':size>MAX_INPUT,'sha256':hashlib.sha256(data).hexdigest()})
        if sum(x.stat().st_size for x in destination.iterdir())>MAX_TOTAL:raise ValueError('Diagnostic archive budget exceeded')
    (destination/'inventory.json').write_text(json.dumps({'marker':MARKER,'files':inventory,'max_input_per_file':MAX_INPUT,'max_total_bytes':MAX_TOTAL,'retention_days':7},indent=2)+'\n')
    (destination/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in sorted(destination.iterdir())))
    if sum(x.stat().st_size for x in destination.iterdir())>MAX_TOTAL:raise ValueError('Diagnostic archive budget exceeded')


def publish(destination):
    repo=os.environ['GITHUB_REPOSITORY']
    run=os.environ['GITHUB_RUN_ID']
    # Delete only this tool's marked diagnostic releases after seven days.
    result=subprocess.run(['gh','api',f'repos/{repo}/releases','--paginate','--slurp'],check=True,stdout=subprocess.PIPE,text=True,timeout=60)
    cutoff=datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=7)
    for page in json.loads(result.stdout):
        for release in page:
            tag=release['tag_name']
            if not tag.startswith('carrera-build-diagnostics-') or MARKER not in (release.get('body') or '') or not release['prerelease']:continue
            created=datetime.datetime.fromisoformat(release['created_at'].replace('Z','+00:00'))
            if created<cutoff:subprocess.run(['gh','release','delete',tag,'--yes','--repo',repo],check=True,timeout=30)
    subprocess.run(['gh','release','create','carrera-build-diagnostics-'+run,*map(str,sorted(destination.iterdir())),
                    '--repo',repo,'--target',os.environ['GITHUB_SHA'],'--prerelease','--title','Carrera public build diagnostics '+run,
                    '--notes',MARKER+'; public allowlisted diagnostics only; maximum16MiB; expires after7days, cleaned by the next diagnostic publication. No Android images or source tree.'],check=True,timeout=180)


if __name__=='__main__':
    if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('RUNNER_ENVIRONMENT')!='github-hosted':raise SystemExit('Public disposable CI only')
    dest=Path('out/public-build-diagnostics');collect(Path('out/android-graph'),dest)
    publish(dest)
