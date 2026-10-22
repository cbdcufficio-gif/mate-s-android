import copy
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from elf_audit import Elf, ElfError, resolve_symbols, sha256, verify_patch
from prepare_graphics import prepare
from scope_audit import audit


def compile_so(cc, directory, name, code, dependencies=(), versioned=False):
    source = directory / (name + '.c')
    source.write_text(code)
    output = directory / name
    command = [cc, '-shared', '-fPIC', '-nostdlib', '-Wl,--build-id=none',
               '-Wl,--hash-style=both', '-Wl,-soname,' + name, str(source),
               '-L' + str(directory)]
    if versioned:
        script = directory / 'exports.map'
        script.write_text('VENDOR_1 { global: api; local: *; };\n')
        command.append('-Wl,--version-script=' + str(script))
    command += ['-l:' + d for d in dependencies]
    command += ['-o', str(output)]
    subprocess.run(command, check=True, capture_output=True)
    return output


class ElfTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cc = shutil.which('cc')
        if not self.cc:
            self.skipTest('C compiler required for real ELF fixtures')
        self.provider = compile_so(self.cc, self.root, 'libprovider.so',
                                   'int api(void) {return 7;}', versioned=True)
        self.consumer = compile_so(self.cc, self.root, 'libconsumer.so',
                                   'extern int api(void); int call(void) {return api();}',
                                   ['libprovider.so'])

    def test_versioned_import_and_provider(self):
        consumer = Elf(self.consumer).report()
        imported = next(s for s in consumer['symbols'] if s['name'] == 'api')
        self.assertTrue(imported['undefined'])
        self.assertEqual(imported['version'], 'VENDOR_1')
        self.assertEqual(imported['version_provider'], 'libprovider.so')
        scope = resolve_symbols(consumer, {'libprovider.so': Elf(self.provider).report()})
        found = next(s for s in scope['results'] if s['symbol'] == 'api')
        self.assertEqual(found['candidate_providers'], ['libprovider.so'])

    def test_symbol_version_mismatch_is_not_resolved(self):
        provider = Elf(self.provider).report()
        for symbol in provider['symbols']:
            symbol['version'] = 'WRONG_VERSION'
        results = resolve_symbols(Elf(self.consumer).report(), {'provider': provider})
        found = next(s for s in results['results'] if s['symbol'] == 'api')
        self.assertEqual(found['candidate_providers'], [])

    def test_other_architecture_not_used(self):
        provider = copy.deepcopy(Elf(self.provider).report())
        provider['machine'] = 183
        results = resolve_symbols(Elf(self.consumer).report(), {'provider': provider})
        self.assertTrue(all(not r['candidate_providers'] for r in results['results']))

    def test_corrupt_section_table_rejected(self):
        bad = self.root / 'bad.so'
        data = bytearray(self.provider.read_bytes())
        if data[4] == 2:
            struct.pack_into('<Q', data, 40, len(data) + 4096)
        else:
            struct.pack_into('<I', data, 32, len(data) + 4096)
        bad.write_bytes(data)
        with self.assertRaises(ElfError):
            Elf(bad)

    def test_executable_code_tamper_detected(self):
        bad = self.root / 'tampered.so'
        elf = Elf(self.provider)
        section = next(s for s in elf.sections if s['name'] == '.text')
        data = bytearray(elf.data)
        data[section['offset']] ^= 1
        bad.write_bytes(data)
        with self.assertRaisesRegex(ElfError, 'payload'):
            verify_patch(self.provider, bad, elf.dynamic()['needed'], elf.dynamic()['soname'])

    def test_duplicate_payload_names_are_not_collapsed(self):
        elf = Elf(self.provider)
        section = next(s for s in elf.sections if s['name'] == '.text')
        before = elf.payload_hashes()
        elf.sections.append(dict(section))
        after = elf.payload_hashes()
        self.assertEqual(len(after), len(before) + 1)
        self.assertEqual(sum(s['name'] == '.text' for s in after), 2)

    def test_exported_entrypoint_tamper_detected(self):
        original = Elf(self.provider)
        table = next(s for s in original.sections if s['type'] == 11)
        strings = original.linked_strings(table)
        data = bytearray(original.data)
        for index in range(1, table['size'] // table['entsize']):
            offset = table['offset'] + index * table['entsize']
            name = struct.unpack_from('<I', data, offset)[0]
            if original.string(strings, name) == 'api':
                value_offset = offset + (4 if original.bits == 32 else 8)
                fmt = '<I' if original.bits == 32 else '<Q'
                value = struct.unpack_from(fmt, data, value_offset)[0]
                struct.pack_into(fmt, data, value_offset, value + 4)
                break
        else:
            self.fail('Fixture has no api export')
        corrupted = self.root / 'bad-entrypoint.so'
        corrupted.write_bytes(data)
        with self.assertRaisesRegex(ElfError, 'symbol'):
            verify_patch(self.provider, corrupted, original.dynamic()['needed'], original.dynamic()['soname'])

    def test_partial_scope_reports_missing_dependency(self):
        empty = self.root / 'empty'
        empty.mkdir()
        report = audit(self.consumer, [empty])
        self.assertIn('libprovider.so', report['missing_needed'])
        self.assertEqual(report['status'], 'STATIC_SCOPE_REPORT_ONLY')

    def test_duplicate_sonames_are_ambiguous(self):
        other = self.root / 'other'
        other.mkdir()
        compile_so(self.cc, other, 'libprovider.so', 'int api(void) {return 8;}', versioned=True)
        report = audit(self.consumer, [self.root])
        self.assertIn('libprovider.so', report['ambiguous_sonames'])

    def test_patch_rename_preserves_payload_and_versions(self):
        tool = os.environ.get('MATES_PATCHELF') or shutil.which('patchelf')
        if not tool:
            self.skipTest('patchelf unavailable')
        patched = self.root / 'renamed-consumer.so'
        shutil.copyfile(self.consumer, patched)
        subprocess.run([tool, '--replace-needed', 'libprovider.so', 'libprivate.so',
                        str(patched)], check=True, capture_output=True)
        report = verify_patch(self.consumer, patched, ['libprivate.so'], 'libconsumer.so',
                              {'libprovider.so': 'libprivate.so'})
        imported = next(s for s in report['symbols'] if s['name'] == 'api')
        self.assertEqual(imported['version_provider'], 'libprivate.so')


class CrossGraphicsTests(unittest.TestCase):
    def test_full_prepare_real_arm32_arm64_and_idempotence_guard(self):
        compilers = {
            'lib': os.environ.get('MATES_TEST_CC_ARM'),
            'lib64': os.environ.get('MATES_TEST_CC_ARM64'),
        }
        tool = os.environ.get('MATES_PATCHELF') or shutil.which('patchelf')
        if not tool or not all(compilers.values()):
            self.skipTest('ARM32/ARM64 compilers and patchelf required for cross fixtures')
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            stock = root / 'system'
            lock = {}
            for arch, cc in compilers.items():
                lib = stock / arch
                lib.mkdir(parents=True)
                ion = compile_so(cc, lib, 'libion.so', 'int api(void) {return 42;}')
                utils = compile_so(cc, lib, 'libutils.so', 'int core(void) {return 1;}')
                gralloc = compile_so(cc, lib, 'gralloc.hi3635.so',
                                     'extern int api(void); int alloc(void) {return api();}', ['libion.so'])
                (lib / 'hw').mkdir()
                gralloc.rename(lib / 'hw' / gralloc.name)
                hwc = compile_so(cc, lib, 'hwcomposer.hi3635.so',
                                 'extern int core(void); int HMI(void) {return core();}', ['libutils.so'])
                hwc.rename(lib / 'hw' / hwc.name)
                mali = compile_so(cc, lib, 'libGLES_mali.so',
                                  'extern int core(void); int eglGetDisplay(void) {return core();}', ['libutils.so'])
                dest = stock / 'vendor' / arch / 'egl'
                dest.mkdir(parents=True)
                mali.rename(dest / mali.name)
            for path in stock.rglob('*.so'):
                lock['system/' + path.relative_to(stock).as_posix()] = {
                    'size': path.stat().st_size, 'sha256': sha256(path)}
            lock_path = root / 'lock.json'
            lock_path.write_text(json.dumps(lock))
            before = {p: sha256(p) for p in stock.rglob('*.so')}
            alias = root / 'stock-alias'
            alias.symlink_to(stock, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'outside the stock'):
                prepare(stock, alias / 'generated', lock_path, tool)
            self.assertFalse((stock / 'generated').exists())
            output = root / 'generated'
            report = prepare(stock, output, lock_path, tool)
            self.assertEqual(report['status'], 'OFFLINE_CANDIDATE_PREPARED')
            self.assertEqual(len(report['files']), 8)
            self.assertEqual(before, {p: sha256(p) for p in stock.rglob('*.so')})
            self.assertEqual({Elf(output / r['output']).machine for r in report['files']}, {40, 183})
            self.assertNotIn('check_elf_files: false', (output / 'Android.bp').read_text())
            with self.assertRaisesRegex(ValueError, 'Output already exists'):
                prepare(stock, output, lock_path, tool)
            first = stock / 'lib' / 'libion.so'
            first.write_bytes(first.read_bytes() + b'changed')
            with self.assertRaisesRegex(ValueError, 'does not match'):
                prepare(stock, root / 'other', lock_path, tool)


if __name__ == '__main__':
    unittest.main()
