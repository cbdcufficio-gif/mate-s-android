#!/usr/bin/env python3
"""Run a real Android module build in a separately synced local LineageOS 17.1 tree."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

# All shell code is constant. User paths are supplied only through cwd/env/argv.
BUILD = '''set -eo pipefail
source build/envsetup.sh
lunch lineage_carrera-userdebug
m -j"$MATES_JOBS" libion_huawei gralloc.hi3635 libGLES_mali hwcomposer.hi3635 \
    libutilscallstack \
    android.hardware.graphics.allocator@2.0-impl android.hardware.graphics.allocator@2.0-service \
    android.hardware.graphics.mapper@2.0-impl \
    android.hardware.graphics.composer@2.1-impl android.hardware.graphics.composer@2.1-service
'''


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--android-root', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True, help='new directory for build log/report')
    p.add_argument('--jobs', type=int, default=2)
    p.add_argument('--min-free-gib', type=int, default=60,
                   help='preflight budget, not a guarantee of total Android build space')
    a = p.parse_args()
    tree = a.android_root.resolve()
    out = a.out.resolve()
    if out.exists() or not 1 <= a.jobs <= 8 or a.min_free_gib < 1:
        p.error('New output, jobs 1..8 and positive disk budget required')
    for relative in ['build/envsetup.sh', 'device/huawei/carrera/BoardConfig.mk',
                     'vendor/huawei/carrera-graphics/Android.bp']:
        if not (tree / relative).is_file():
            p.error(f'Missing local source: {relative}')
    free = shutil.disk_usage(tree).free
    if free < a.min_free_gib * 1024 ** 3:
        p.error(f'Free disk {free // 1024**3} GiB below selected budget; no build started')
    out.mkdir(parents=True)
    report = {'status': 'BUILD_RUNNING', 'jobs': a.jobs, 'free_bytes_at_start': free,
              'android_root': str(tree), 'boot_image_created': False,
              'rom_built': False, 'hardware_tested': False}
    with (out / 'build.log').open('w') as log:
        result = subprocess.run(['bash', '-c', BUILD], cwd=tree, stdout=log,
                                stderr=subprocess.STDOUT,
                                env={**os.environ, 'MATES_JOBS': str(a.jobs)})
    report['returncode'] = result.returncode
    report['status'] = 'MODULE_BUILD_PASSED' if result.returncode == 0 else 'MODULE_BUILD_FAILED'
    (out / 'build-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(out / 'build-report.json')
    return result.returncode


if __name__ == '__main__':
    sys.exit(main())
