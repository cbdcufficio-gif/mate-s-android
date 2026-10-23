#!/usr/bin/env python3
"""Compile actual public Android Q graphics modules on a disposable CI runner."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from android_graph_probe import ROOT, guarded
from elf_audit import Elf, sha256

MODULES = [
    'libutilscallstack', 'libhwc2on1adapter', 'libhwc2onfbadapter',
    'android.hardware.graphics.allocator@2.0-impl',
    'android.hardware.graphics.allocator@2.0-service',
    'android.hardware.graphics.mapper@2.0-impl',
    'android.hardware.graphics.composer@2.1-impl',
    'android.hardware.graphics.composer@2.1-service',
]
# Names here describe installed files, never synthetic replacements.
REQUIRED = {name + ('' if name.endswith('-service') else '.so') for name in MODULES}


def inventory(product):
    files = []
    for file in sorted(product.rglob('*')):
        if file.name not in REQUIRED or not file.is_file() or file.is_symlink():
            continue
        elf = Elf(file)
        dynamic = elf.dynamic()
        files.append({'path': str(file.relative_to(product)), 'bytes': file.stat().st_size,
                      'sha256': sha256(file), 'bits': elf.bits, 'machine': elf.machine,
                      'needed': dynamic['needed'], 'soname': dynamic['soname'],
                      'callstack_mali_exports': sorted(s['name'] for s in elf.symbols()
                         if not s['undefined'] and s['name'] in (
                             '_ZN7android9CallStackC1EPKci', '_ZN7android9CallStackD1Ev'))})
    missing = sorted(REQUIRED - {Path(f['path']).name for f in files})
    if missing:
        raise ValueError('Requested installed ELF files missing: ' + ', '.join(missing))
    if any(f['machine'] not in (40, 183) for f in files):
        raise ValueError('Unexpected target architecture')
    if not any(f['bits'] == 64 for f in files):
        raise ValueError('No ARM64 ELF output')
    return files


def main():
    if os.environ.get('GITHUB_ACTIONS') != 'true' or os.environ.get('RUNNER_ENVIRONMENT') != 'github-hosted':
        raise SystemExit('Only disposable GitHub-hosted runner allowed')
    result = subprocess.run([sys.executable, str(Path(__file__).with_name('android_graph_probe.py'))])
    if result.returncode:
        return result.returncode
    report_file = ROOT / 'modules-report.json'
    report = {'status': 'MODULE_BUILD_RUNNING', 'modules': MODULES,
              'product': 'lineage_arm64-userdebug', 'rom_built': False,
              'carrera_built': False, 'hardware_tested': False,
              'proprietary_inputs': False}
    report_file.write_text(json.dumps(report, indent=2)+'\n')
    try:
        source = (ROOT / 'source').resolve()
        # All command text is constant; MODULES is a fixed allowlist above.
        command = ('set -eo pipefail; source build/envsetup.sh; lunch lineage_arm64-userdebug; '
                   'get_build_var PRODUCT_OUT > "$MATES_PRODUCT_PATH"; m -j2 ' + ' '.join(MODULES))
        os.environ['MATES_PRODUCT_PATH'] = str((ROOT/'product-path.txt').resolve())
        report['build'] = guarded(['bash', '-c', command], source, ROOT/'modules.log',
                                  seconds=2700, reserve=12*1024**3)
        if report['build']['returncode'] or report['build']['stop_reason']:
            report['status'] = 'MODULE_BUILD_FAILED'
        else:
            relative = Path((ROOT/'product-path.txt').read_text().strip())
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError('Unexpected product output path')
            product = (source / relative).resolve(strict=True)
            product.relative_to(source / 'out')
            report['files'] = inventory(product)
            report['status'] = 'PUBLIC_GRAPHICS_MODULES_BUILT'
        manifest = ROOT/'resolved-manifest.xml'
        report['resolved_manifest_sha256'] = sha256(manifest)
    except Exception as error:
        report['status'] = 'MODULE_VERIFICATION_FAILED'
        report['error'] = str(error)
    finally:
        report_file.write_text(json.dumps(report, indent=2)+'\n')
        print(report_file.read_text())
    return 0 if report['status'] == 'PUBLIC_GRAPHICS_MODULES_BUILT' else 1

if __name__ == '__main__':
    raise SystemExit(main())
