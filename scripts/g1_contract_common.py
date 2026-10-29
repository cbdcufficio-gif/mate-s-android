"""Shared bounded public G1 experiment helpers; no device access."""
import hashlib,json,os,re,subprocess,urllib.request
from pathlib import Path
from g1_first_stage_probe import function
ROOT=Path(__file__).resolve().parents[1]
REPO='cbdcufficio-gif/mate-s-android'
CORE='6d27634866be5b646a8cea1f9abeae902fd831e5'

def sha(data):return hashlib.sha256(data).hexdigest()
def run(argv,**kw):return subprocess.check_output(list(map(str,argv)),text=True,timeout=kw.pop('timeout',120),**kw)
def api(path):return json.loads(run(['gh','api','repos/'+REPO+'/'+path]))
def guard():
    if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('RUNNER_ENVIRONMENT')!='github-hosted' or os.environ.get('GITHUB_REPOSITORY')!=REPO:raise ValueError('Disposable public CI only')
    if api('branches/main')['commit']['sha']!=os.environ['GITHUB_SHA']:raise ValueError('Concurrent main writer')
    runs=api('actions/runs?per_page=30')['workflow_runs']
    if any(r['status'] in ('queued','in_progress','waiting','pending','requested') and r['name']=='Mate S public Carrera system and ramdisk' for r in runs):raise ValueError('System build already active')
def source(path):
    rows=json.loads((ROOT/'docs/REVIEW-2026-10-29-SOURCES.json').read_text())['files']
    row=next(x for x in rows if x['repository']=='LineageOS/android_system_core' and x['path']==path)
    url=f'https://raw.githubusercontent.com/{row["repository"]}/{row["revision"]}/{path}'
    with urllib.request.urlopen(url,timeout=45) as response:data=response.read(1024**2+1)
    if len(data)>1024**2 or sha(data)!=row['sha256']:raise ValueError('Pinned source digest mismatch: '+path)
    return data.decode()
def suite():
    p=subprocess.run(['python3','-m','unittest','discover','tests'],capture_output=True,text=True)
    print(p.stdout);print(p.stderr);p.check_returncode()
    total=int(re.search(r'Ran (\d+) tests?',p.stderr)[1]);m=re.search(r'OK \(skipped=(\d+)\)',p.stderr);skipped=int(m[1]) if m else 0
    return {'run':total,'passed':total-skipped,'skipped':skipped}
def publish(directory,tag,title):
    guard()
    files=sorted(directory.iterdir())
    if any(p.is_symlink() or not p.is_file() for p in files):raise ValueError('Unexpected evidence entry')
    if sum(p.stat().st_size for p in files)>16*1024**2:raise ValueError('Evidence budget exceeded')
    (directory/'SHA256SUMS').write_text(''.join(sha(p.read_bytes())+'  '+p.name+'\n' for p in files))
    subprocess.run(['gh','release','create',tag,*map(str,sorted(directory.iterdir())),'--repo',REPO,'--target',os.environ['GITHUB_SHA'],'--prerelease','--title',title,'--notes','Public static/host-fixture evidence only. No target boot, Android execution or hardware acceptance.'],check=True,timeout=180)
