#!/usr/bin/env python3
"""Build a diagnostic Image locally, never a boot/recovery image or flash package."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from elf_audit import sha256

PROJECT = Path(__file__).resolve().parents[1]


def apply_fragment(config_path, fragment_path):
    original = config_path.read_text().splitlines()
    values = {}
    for line in fragment_path.read_text().splitlines():
        if line.startswith('CONFIG_') and '=' in line:
            values[line.split('=', 1)[0]] = line
        elif line.startswith('# CONFIG_') and line.endswith(' is not set'):
            values[line.split()[1]] = line
    def key(line):
        if line.startswith('CONFIG_'):
            return line.split('=', 1)[0]
        if line.startswith('# CONFIG_'):
            return line.split()[1]
        return None
    kept = [line for line in original if key(line) not in values]
    config_path.write_text('\n'.join(kept + list(values.values())) + '\n')


def config_values(path):
    result = {}
    for line in Path(path).read_text().splitlines():
        if line.startswith('CONFIG_') and '=' in line:
            key, value = line.split('=', 1)
            result[key] = value
        elif line.startswith('# CONFIG_') and line.endswith(' is not set'):
            result[line.split()[1]] = 'n'
    return result


def build(source, cross_prefix, output, profile, jobs):
    source, output = Path(source).resolve(strict=True), Path(output).resolve()
    lock = json.loads((PROJECT / 'sources.lock.json').read_text())
    expected = next(r['commit'] for r in lock['repositories'] if r['directory'] == 'kernel-hi3635')
    commit = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    if commit != expected:
        raise ValueError('Kernel revision is not the tested locked revision')
    patch = PROJECT / 'patches/kernel/0001-fix-immersion-header-path.patch'
    # Require exactly the tested source change, not arbitrary pre-existing edits.
    diff = subprocess.check_output(['git', '-C', str(source), 'diff', '--binary'], text=True)
    if diff.strip() != patch.read_text().strip():
        raise ValueError('Source changes differ from the tested Immersion header patch')
    untracked = subprocess.check_output(['git', '-C', str(source), 'ls-files', '--others', '--exclude-standard'], text=True)
    if untracked.strip():
        raise ValueError('Untracked source files: review them before building')
    if output.exists() or source == output or source in output.parents:
        raise ValueError('Choose a NEW output directory outside the kernel source')
    compiler = Path(str(cross_prefix) + 'gcc').resolve(strict=True)
    toolchain_root = compiler.parent.parent
    compiler_commit = subprocess.check_output(
        ['git', '-C', str(toolchain_root), 'rev-parse', 'HEAD'], text=True).strip()
    expected_compiler = next(r['commit'] for r in lock['repositories'] if r['directory'] == 'gcc49')
    if compiler_commit != expected_compiler:
        raise ValueError('Toolchain revision is not locked')
    if subprocess.run(['git', '-C', str(toolchain_root), 'diff', '--quiet', 'HEAD']).returncode:
        raise ValueError('Tracked toolchain files were modified')
    # Pin the executable as well as the repo ref; a modified binary cannot pass by HEAD alone.
    if sha256(compiler) != lock['toolchain_gcc_sha256']:
        raise ValueError('Compiler executable hash mismatch')
    if not shutil.which('bc'):
        raise ValueError('bc is required inside the build environment')
    if not 1 <= jobs <= 16:
        raise ValueError('jobs must be 1..16')
    output.mkdir(parents=True)
    config = output / '.config'
    stock = PROJECT / 'configs/stock-b321.config'
    if sha256(stock) != lock['stock_config_sha256']:
        raise ValueError('Stock hardware configuration hash mismatch')
    shutil.copyfile(stock, config)
    if profile == 'android10-diagnostic':
        apply_fragment(config, PROJECT / 'configs/android10-diagnostic.fragment')
    prefix = str(compiler)[:-3]
    base = ['make', '-C', str(source), 'O=' + str(output), 'ARCH=arm64',
            'CROSS_COMPILE=' + prefix, 'HOSTCFLAGS=-fcommon']
    report = {'status': 'INCOMPLETE', 'profile': profile, 'kernel_commit': commit,
              'patch_sha256': sha256(patch), 'stock_config_sha256': sha256(stock),
              'toolchain_commit': compiler_commit, 'compiler_sha256': sha256(compiler),
              'commands': [base + ['olddefconfig'], base + ['-j' + str(jobs), 'Image']],
              'phone_access': False, 'boot_image_created': False,
              'hardware_boot_tested': False}
    env = {**os.environ, 'LC_ALL': 'C', 'KBUILD_BUILD_USER': 'builder',
           'KBUILD_BUILD_HOST': 'mates', 'KBUILD_BUILD_TIMESTAMP': 'Thu Oct 22 00:00:00 UTC 2026'}
    try:
        with (output / 'build.log').open('w') as log:
            subprocess.run(report['commands'][0], check=True, stdout=log, stderr=subprocess.STDOUT, env=env)
            if profile == 'android10-diagnostic':
                requested = config_values(PROJECT / 'configs/android10-diagnostic.fragment')
                actual = config_values(config)
                for key, value in requested.items():
                    if actual.get(key, 'n') != value:
                        raise ValueError(f'Kernel configuration did not retain {key}={value}')
                report['requested_fragment_verified'] = requested
            stock_values, actual = config_values(stock), config_values(config)
            hardware = ['CONFIG_FB_3635', 'CONFIG_MALI_MIDGARD', 'CONFIG_FINGERPRINT',
                        'CONFIG_IMMERSION', 'CONFIG_BACKLIGHT_10000', 'CONFIG_GRACE_SELECT_2A_1A_AC']
            for key in hardware:
                if actual.get(key, 'n') != stock_values.get(key, 'n'):
                    raise ValueError(f'Hardware configuration unexpectedly changed: {key}')
            subprocess.run(report['commands'][1], check=True, stdout=log, stderr=subprocess.STDOUT, env=env)
        image = output / 'arch/arm64/boot/Image'
        header = image.read_bytes()[:64]
        if header[56:60] != b'ARMd':
            raise ValueError('Output is not an ARM64 Image')
        report.update(status='IMAGE_COMPILED_OFFLINE', image_sha256=sha256(image),
                      image_size=image.stat().st_size, effective_config_sha256=sha256(config))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        report['error'] = str(error)
        (output / 'build-report.json').write_text(json.dumps(report, indent=2) + '\n')
        raise
    (output / 'build-report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--cross-prefix', required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--profile', choices=['stock', 'android10-diagnostic'], default='stock')
    p.add_argument('--jobs', type=int, default=4)
    a = p.parse_args()
    try:
        result = build(a.source, a.cross_prefix, a.out, a.profile, a.jobs)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f'STOP: {error}', file=sys.stderr)
        return 1
    print(result['status'], result['image_sha256'])
    print(a.out.resolve() / 'build-report.json')
    return 0


if __name__ == '__main__':
    sys.exit(main())
