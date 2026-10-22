#!/usr/bin/env python3
"""Prepare fresh local graphics candidates from hash-locked stock files; no ADB."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from elf_audit import Elf, ElfError, sha256, verify_patch

PROJECT = Path(__file__).resolve().parents[1]
MODULES = {
    'libion_huawei': ('{arch}/libion.so', '', 'libion_huawei.so'),
    'gralloc.hi3635': ('{arch}/hw/gralloc.hi3635.so', 'hw', 'gralloc.hi3635.so'),
    'libGLES_mali': ('vendor/{arch}/egl/libGLES_mali.so', 'egl', 'libGLES_mali.so'),
    'hwcomposer.hi3635': ('{arch}/hw/hwcomposer.hi3635.so', 'hw', 'hwcomposer.hi3635.so'),
}


def run(*argv):
    result = subprocess.run(list(map(str, argv)), capture_output=True, text=True,
                            env={**os.environ, 'LC_ALL': 'C'})
    if result.returncode:
        raise RuntimeError(f'{argv[0]} failed ({result.returncode}): {result.stderr[-3000:]}')
    return result.stdout.strip()


def validate_input(stock, relative, expected, bits):
    path = stock / relative
    if not path.is_file() or path.is_symlink():
        raise ValueError(f'Missing input or symlink: {path}')
    # Reject symlinked parent paths too, even if they point inside the input root.
    cursor = path
    while cursor != stock:
        if cursor.is_symlink():
            raise ValueError(f'Symlink input component: {cursor}')
        cursor = cursor.parent
    if sha256(path) != expected['sha256'] or path.stat().st_size != expected['size']:
        raise ValueError(f'Input does not match the acquired B321 lock: {path}')
    elf = Elf(path)
    if (elf.bits, elf.machine, elf.type) != (bits, 40 if bits == 32 else 183, 3):
        raise ElfError(f'Wrong ELF architecture/type: {path}')
    if not elf.loads or not elf.symbols():
        raise ElfError(f'No loadable segments/dynamic symbols: {path}')
    return path, elf


def blueprint(modules):
    blocks = ['// Generated experimental prebuilts. Keep default ELF checks enabled.\n']
    for name, arches in modules.items():
        subdir = MODULES[name][1]
        block = ['cc_prebuilt_library_shared {', f'    name: "{name}",',
                 '    vendor: true,', '    compile_multilib: "both",',
                 '    stl: "none",', '    system_shared_libs: [],',
                 '    strip: { none: true },']
        if subdir:
            block.append(f'    relative_install_path: "{subdir}",')
        block.append('    arch: {')
        for arch, info in arches.items():
            dependencies = info['needed']
            if any('/' in d or not d.endswith('.so') for d in dependencies):
                raise ValueError('Unmapped library name; manual Soong mapping needed')
            block.extend([f'        {arch}: {{',
                          f'            srcs: {json.dumps([info["src"]])},',
                          f'            shared_libs: {json.dumps([d[:-3] for d in dependencies])},',
                          '        },'])
        block.extend(['    },', '}', ''])
        blocks.append('\n'.join(block))
    return '\n'.join(blocks)


def prepare(stock, output, lock_path, patchelf='patchelf'):
    stock = Path(stock).resolve(strict=True)
    output = Path(output).resolve()
    lock = json.loads(Path(lock_path).read_text())
    if output.exists():
        raise ValueError('Output already exists; choose a fresh directory')
    if output == stock or stock in output.parents:
        raise ValueError('Output must be outside the stock directory')
    inputs = []
    for module, (pattern, subdir, filename) in MODULES.items():
        for arch, bits in [('lib', 32), ('lib64', 64)]:
            relative = pattern.format(arch=arch)
            expected = lock.get('system/' + relative)
            if not expected:
                raise ValueError(f'No trusted hash for {relative}')
            source, elf = validate_input(stock, relative, expected, bits)
            inputs.append((module, arch, subdir, filename, relative, source, elf))
    tool_version = run(patchelf, '--version')
    output.mkdir(parents=True)
    state = {'status': 'INCOMPLETE', 'patchelf': tool_version, 'files': [],
             'warning': 'No Android compilation, loader test or hardware execution performed'}
    report_path = output / 'preparation.json'
    report_path.write_text(json.dumps(state, indent=2) + '\n')
    generated = {module: {} for module in MODULES}
    try:
        for module, arch, subdir, filename, relative, source, original in inputs:
            destination = output / 'proprietary' / arch / subdir / filename
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            dynamic = original.dynamic()
            expected_needed = list(dynamic['needed'])
            expected_soname = dynamic['soname']
            if module == 'libion_huawei':
                expected_soname = 'libion_huawei.so'
                run(patchelf, '--set-soname', expected_soname, destination)
            elif module == 'gralloc.hi3635':
                if expected_needed.count('libion.so') != 1:
                    raise ElfError('Expected exactly one stock gralloc libion dependency')
                expected_needed = ['libion_huawei.so' if n == 'libion.so' else n
                                   for n in expected_needed]
                run(patchelf, '--replace-needed', 'libion.so', 'libion_huawei.so', destination)
            elif module == 'libGLES_mali' and 'libutilscallstack.so' not in expected_needed:
                expected_needed.append('libutilscallstack.so')
                run(patchelf, '--add-needed', 'libutilscallstack.so', destination)
            renames = {'libion.so': 'libion_huawei.so'} if module == 'gralloc.hi3635' else {}
            checked = verify_patch(source, destination, expected_needed, expected_soname, renames)
            if sha256(source) != lock['system/' + relative]['sha256']:
                raise ElfError('Original input changed during preparation')
            rel_dest = destination.relative_to(output).as_posix()
            generated[module]['arm' if arch == 'lib' else 'arm64'] = {
                'src': rel_dest, 'needed': expected_needed}
            state['files'].append({'source': 'system/' + relative, 'output': rel_dest,
                                   'original_sha256': lock['system/' + relative]['sha256'],
                                   'candidate_sha256': checked['sha256'],
                                   'elf': checked})
        (output / 'Android.bp').write_text(blueprint(generated))
        (output / 'carrera-graphics.mk').write_text(
            '# Include only in reviewed Carrera build; not a full HAL integration.\n'
            'PRODUCT_PACKAGES += ' + ' '.join(MODULES) + ' libutilscallstack\n')
        (output / '.gitignore').write_text('proprietary/\n')
        (output / 'README.md').write_text(
            '# Experimental graphics candidates\n\n'
            'SONAME separation does not guarantee symbol isolation. CallStack/Region '
            'layouts, Android linker namespaces, vendor API availability, GPU and '
            'gralloc/fence ABI remain unverified. No fake shim or disabled ELF check '
            'is supplied. A passing structural check is not a passing loader test.\n')
        state['status'] = 'OFFLINE_CANDIDATE_PREPARED'
        report_path.write_text(json.dumps(state, indent=2) + '\n')
        paths = sorted(p for p in output.rglob('*') if p.is_file() and p.name != 'SHA256SUMS')
        (output / 'SHA256SUMS').write_text(''.join(
            f'{sha256(p)}  {p.relative_to(output).as_posix()}\n' for p in paths))
    except Exception as error:
        state['error'] = str(error)
        report_path.write_text(json.dumps(state, indent=2) + '\n')
        raise
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock-system', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--lock', type=Path, default=PROJECT / 'configs/stock-elf-lock.json')
    parser.add_argument('--patchelf', default='patchelf')
    args = parser.parse_args()
    try:
        result = prepare(args.stock_system, args.out, args.lock, args.patchelf)
    except (OSError, ValueError, RuntimeError, ElfError) as error:
        print(f'STOP: {error}', file=sys.stderr)
        return 1
    print(f'PREPARAZIONE: {result["status"]}; ELF verificati: {len(result["files"])}')
    print(f'REPORT: {args.out.resolve() / "preparation.json"}')
    print('Nessuna prova di compilazione o avvio Android implicita.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
