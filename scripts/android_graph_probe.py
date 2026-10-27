#!/usr/bin/env python3
"""Bounded public-source Android sync and real build-graph probe on disposable CI."""
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time
from remote_preflight import COMMIT
from android_locked_manifest import install_lock, verify_synced

ROOT = Path('out/android-graph')
REPORT = ROOT / 'report.json'

def guarded(argv, cwd, log, seconds, reserve=20*1024**3):
    start = time.monotonic()
    reason = None
    with log.open('w') as stream:
        process = subprocess.Popen(argv, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT,
                                   start_new_session=True,
                                   env={**os.environ, 'GIT_TERMINAL_PROMPT': '0',
                                        'USE_CCACHE': '1' if (os.environ.get('MATES_USE_CCACHE') == '1'
                                        and os.environ.get('GITHUB_ACTIONS') == 'true'
                                        and os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted') else '0',
                                        'BUILD_NUMBER': 'mates-probe'})
        while process.poll() is None:
            if shutil.disk_usage(cwd).free < reserve:
                reason = 'DISK_RESERVE_REACHED'
            elif time.monotonic()-start >= seconds:
                reason = 'TIME_BUDGET_REACHED'
            if reason:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                break
            time.sleep(3)
    return {'returncode': process.returncode, 'stop_reason': reason,
            'seconds': round(time.monotonic()-start, 1),
            'free_bytes': shutil.disk_usage(cwd).free}

def main():
    if os.environ.get('GITHUB_ACTIONS') != 'true' or os.environ.get('RUNNER_ENVIRONMENT') != 'github-hosted':
        raise SystemExit('Only disposable GitHub-hosted runner allowed; no local Android download')
    ROOT.mkdir(parents=True, exist_ok=False)
    tree = (ROOT / 'source').resolve()
    tree.mkdir()
    report = {'manifest_commit': COMMIT, 'status': 'RUNNING', 'stages': {},
              'rom_built': False, 'proprietary_files_uploaded': False,
              'purpose': 'Real generic Android build graph, not Carrera ROM',
              'initial_free_bytes': shutil.disk_usage(tree).free}
    stages = [
        ('init', ['repo', 'init', '-u', 'https://github.com/LineageOS/android.git', '-b', COMMIT,
                  '--depth=1', '--no-clone-bundle', '--groups=default,-darwin'], 180),
        ('sync', ['repo', 'sync', '--no-manifest-update', '-c', '-j4', '--no-clone-bundle', '--no-tags', '--fail-fast'], 1200),
        ('graph', ['bash', '-c', 'set -eo pipefail; source build/envsetup.sh; lunch lineage_arm64-userdebug; m -j2 nothing'], 600),
    ]
    try:
        for name, argv, seconds in stages:
            report['status'] = name.upper() + '_RUNNING'
            REPORT.write_text(json.dumps(report, indent=2)+'\n')
            result = guarded(argv, tree, ROOT/(name+'.log'), seconds)
            report['stages'][name] = result
            if result['returncode'] or result['stop_reason']:
                report['status'] = name.upper() + '_FAILED'
                break
            if name == 'init':
                report['source_lock']=install_lock(tree)
            if name == 'sync':
                with (ROOT/'resolved-manifest.xml').open('w') as stream:
                    subprocess.run(['repo', 'manifest', '-r'], cwd=tree, stdout=stream, check=True, timeout=60)
                report['synced_lock']=verify_synced((ROOT/'resolved-manifest.xml').read_bytes())
                if os.environ.get('MATES_SYNC_ONLY')=='1':
                    report['status']='PINNED_ANDROID_SYNC_PASSED'
                    break
        else:
            report['status'] = 'GENERIC_BUILD_GRAPH_PASSED'
    except Exception as error:
        report['status'] = 'PROBE_ERROR'
        report['error'] = str(error)
    finally:
        REPORT.write_text(json.dumps(report, indent=2)+'\n')
        print(REPORT.read_text())
    return 0 if report['status'] in ('GENERIC_BUILD_GRAPH_PASSED','PINNED_ANDROID_SYNC_PASSED') else 1

if __name__ == '__main__':
    raise SystemExit(main())
