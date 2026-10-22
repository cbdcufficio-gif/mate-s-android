#!/usr/bin/env python3
"""Bounded, static ELF inspection. Never loads or executes inspected binaries."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct


class ElfError(ValueError):
    pass


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


class Elf:
    def __init__(self, path):
        self.path = Path(path)
        if self.path.stat().st_size > 128 * 1024 * 1024:
            raise ElfError('ELF exceeds 128 MiB inspection limit')
        self.data = self.path.read_bytes()
        if len(self.data) < 16 or self.data[:4] != b'\x7fELF':
            raise ElfError('Not a raw ELF file')
        ident = self.data[:16]
        if ident[4] not in (1, 2) or ident[5] != 1 or ident[6] != 1:
            raise ElfError('Only ELF32/ELF64 little-endian version 1 supported')
        self.bits = 32 if ident[4] == 1 else 64
        fmt = '<HHIIIIIHHHHHH' if self.bits == 32 else '<HHIQQQIHHHHHH'
        header = self.unpack(fmt, 16)
        (self.type, self.machine, _, self.entry, phoff, shoff, self.flags,
         _, phentsize, phnum, shentsize, shnum, shstrndx) = header
        if shnum == 0 or shstrndx == 0xffff or phnum == 0xffff:
            raise ElfError('Missing or extended ELF tables require manual inspection')
        if shnum > 16384 or phnum > 4096:
            raise ElfError('Unreasonable ELF table count')
        self.sections = []
        shfmt = '<IIIIIIIIII' if self.bits == 32 else '<IIQQQQIIQQ'
        if shentsize != struct.calcsize(shfmt):
            raise ElfError('Unexpected section header size')
        self.slice(shoff, shnum * shentsize)
        for index in range(shnum):
            values = self.unpack(shfmt, shoff + index * shentsize)
            sec = dict(zip(('name_offset', 'type', 'flags', 'address', 'offset',
                            'size', 'link', 'info', 'align', 'entsize'), values))
            if sec['type'] != 8:
                self.slice(sec['offset'], sec['size'])
            self.sections.append(sec)
        if shstrndx >= shnum:
            raise ElfError('Invalid section string table')
        strings = self.section_bytes(self.sections[shstrndx])
        for sec in self.sections:
            sec['name'] = self.string(strings, sec['name_offset'])
        phfmt = '<IIIIIIII' if self.bits == 32 else '<IIQQQQQQ'
        if phnum and phentsize != struct.calcsize(phfmt):
            raise ElfError('Unexpected program header size')
        self.slice(phoff, phnum * phentsize)
        self.loads = []
        for index in range(phnum):
            p = self.unpack(phfmt, phoff + index * phentsize)
            if self.bits == 32:
                kind, offset, vaddr, _, filesz, memsz, flags, align = p
            else:
                kind, flags, offset, vaddr, _, filesz, memsz, align = p
            self.slice(offset, filesz)
            if kind == 1:
                if filesz > memsz:
                    raise ElfError('PT_LOAD filesz exceeds memsz')
                if align not in (0, 1) and (align & (align - 1) or
                                             (vaddr - offset) % align):
                    raise ElfError('Invalid PT_LOAD alignment')
                self.loads.append((offset, filesz, vaddr, memsz, flags))

    def slice(self, offset, size):
        if offset < 0 or size < 0 or offset > len(self.data) or size > len(self.data) - offset:
            raise ElfError('ELF range outside file')
        return self.data[offset:offset + size]

    def unpack(self, fmt, offset):
        return struct.unpack(fmt, self.slice(offset, struct.calcsize(fmt)))

    @staticmethod
    def string(table, offset):
        if offset >= len(table):
            raise ElfError('String offset outside table')
        end = table.find(b'\0', offset)
        if end < 0:
            raise ElfError('Unterminated ELF string')
        return table[offset:end].decode('utf-8', errors='strict')

    def section_bytes(self, section):
        return self.slice(section['offset'], section['size'])

    def linked_strings(self, section):
        if section['link'] >= len(self.sections):
            raise ElfError('Invalid linked string table')
        return self.section_bytes(self.sections[section['link']])

    def dynamic(self):
        result = {'needed': [], 'soname': None, 'rpath': None, 'runpath': None}
        for sec in self.sections:
            if sec['type'] != 6:
                continue
            fmt = '<iI' if self.bits == 32 else '<qQ'
            stride = struct.calcsize(fmt)
            if sec['size'] % stride:
                raise ElfError('Truncated dynamic table')
            strings = self.linked_strings(sec)
            for pos in range(0, sec['size'], stride):
                tag, value = self.unpack(fmt, sec['offset'] + pos)
                if tag == 0:
                    break
                if tag == 1:
                    result['needed'].append(self.string(strings, value))
                elif tag in (14, 15, 29):
                    result[{14: 'soname', 15: 'rpath', 29: 'runpath'}[tag]] = self.string(strings, value)
        return result

    def version_names(self):
        versions = {}
        for sec in self.sections:
            if sec['type'] not in (0x6ffffffe, 0x6ffffffd):
                continue
            strings = self.linked_strings(sec)
            pos, seen = 0, set()
            while pos < sec['size']:
                if pos in seen:
                    raise ElfError('Cyclic version records')
                seen.add(pos)
                if sec['type'] == 0x6ffffffe:
                    if pos + 16 > sec['size']:
                        raise ElfError('Truncated version requirement header')
                    version, count, fileoff, aux, nxt = self.unpack('<HHIII', sec['offset'] + pos)
                    if version != 1:
                        raise ElfError('Unsupported version requirement format')
                    provider = self.string(strings, fileoff)
                    ap = pos + aux
                    for _ in range(count):
                        if ap < pos or ap + 16 > sec['size']:
                            raise ElfError('Version requirement outside section')
                        _, _, index, name, anext = self.unpack('<IHHII', sec['offset'] + ap)
                        versions[index & 0x7fff] = (self.string(strings, name), provider)
                        if not anext:
                            break
                        ap += anext
                else:
                    if pos + 20 > sec['size']:
                        raise ElfError('Truncated version definition header')
                    version, _, index, _, _, aux, nxt = self.unpack('<HHHHIII', sec['offset'] + pos)
                    if version != 1:
                        raise ElfError('Unsupported version definition format')
                    if pos + aux + 8 > sec['size']:
                        raise ElfError('Version definition outside section')
                    name, _ = self.unpack('<II', sec['offset'] + pos + aux)
                    versions[index & 0x7fff] = (self.string(strings, name), None)
                if not nxt:
                    break
                if nxt < 16 or pos + nxt >= sec['size']:
                    raise ElfError('Invalid next version record')
                pos += nxt
        return versions

    def symbols(self):
        result, versions = [], self.version_names()
        for section_index, sec in enumerate(self.sections):
            if sec['type'] != 11:
                continue
            fmt = '<IIIBBH' if self.bits == 32 else '<IBBHQQ'
            stride = struct.calcsize(fmt)
            if sec['entsize'] != stride or sec['size'] % stride:
                raise ElfError('Invalid dynamic symbol table')
            strings = self.linked_strings(sec)
            versym = next((s for s in self.sections if s['type'] == 0x6fffffff
                           and s['link'] == section_index), None)
            count = sec['size'] // stride
            if versym and versym['size'] < count * 2:
                raise ElfError('Truncated symbol version table')
            for index in range(1, count):
                values = self.unpack(fmt, sec['offset'] + index * stride)
                if self.bits == 32:
                    name, value, size, info, other, ndx = values
                else:
                    name, info, other, ndx, value, size = values
                raw_version = self.unpack('<H', versym['offset'] + index * 2)[0] if versym else 1
                version_index = raw_version & 0x7fff
                version, provider = versions.get(version_index, (None, None)) if version_index > 1 else (None, None)
                if version_index > 1 and version is None:
                    raise ElfError('Unknown symbol version index')
                if 0 < ndx < 0xff00:
                    if ndx >= len(self.sections):
                        raise ElfError('Dynamic symbol has invalid section index')
                    target_section = self.sections[ndx]
                    identity = {'name': target_section['name'], 'type': target_section['type'],
                                'offset_in_section': value - target_section['address']}
                else:
                    identity = {'special_index': ndx}
                result.append({'name': self.string(strings, name), 'size': size,
                               'value': value, 'section': identity,
                               'bind': info >> 4, 'type': info & 15, 'visibility': other & 3,
                               'undefined': ndx == 0, 'version': version,
                               'version_hidden': bool(raw_version & 0x8000),
                               'version_provider': provider})
        return result

    def payload_hashes(self):
        # Intentionally exclude loader metadata modified by patchelf.
        names = {'.text', '.rodata', '.data', '.data.rel.ro', '.bss', '.init', '.fini'}
        result = [{'name': s['name'], 'size': s['size'], 'type': s['type'],
                   'sha256': None if s['type'] == 8 else
                   hashlib.sha256(self.section_bytes(s)).hexdigest()}
                  for s in self.sections if s['name'] in names or s['flags'] & 4]
        # Keep every occurrence: ELF permits duplicate section names.
        return sorted(result, key=lambda item: json.dumps(item, sort_keys=True))

    def report(self):
        return {'sha256': hashlib.sha256(self.data).hexdigest(), 'size': len(self.data),
                'bits': self.bits, 'machine': self.machine, 'type': self.type,
                'flags': self.flags, **self.dynamic(), 'symbols': self.symbols(),
                'payload_sections': self.payload_hashes(),
                'warning': 'Static structure only; no class-layout, loader or hardware proof'}


def verify_patch(original, patched, expected_needed, expected_soname, provider_renames=None):
    a, b = Elf(original), Elf(patched)
    if (a.bits, a.machine, a.type, a.flags, a.entry) != (b.bits, b.machine, b.type, b.flags, b.entry):
        raise ElfError('Patch changed ELF identity or entry point')
    if a.payload_hashes() != b.payload_hashes():
        raise ElfError('Patch changed program/data payload sections')
    def canonical(elf, renames):
        symbols = elf.symbols()
        for symbol in symbols:
            if symbol['undefined']:
                symbol['version_provider'] = renames.get(symbol['version_provider'], symbol['version_provider'])
        return Counter(json.dumps(s, sort_keys=True) for s in symbols)
    if canonical(a, provider_renames or {}) != canonical(b, {}):
        raise ElfError('Patch changed dynamic symbol/version declarations')
    dyn = b.dynamic()
    if Counter(dyn['needed']) != Counter(expected_needed) or dyn['soname'] != expected_soname:
        raise ElfError('Unexpected DT_NEEDED or SONAME after patch')
    if (a.dynamic()['rpath'], a.dynamic()['runpath']) != (dyn['rpath'], dyn['runpath']):
        raise ElfError('Unexpected RPATH change')
    return b.report()


def resolve_symbols(consumer, providers):
    """Partial static scope analysis; never equates union coverage to Android loading."""
    imports = [s for s in consumer['symbols'] if s['undefined'] and s['bind'] in (1, 2)]
    results = []
    for symbol in imports:
        candidates = []
        for name, provider in providers.items():
            if (provider['bits'], provider['machine']) != (consumer['bits'], consumer['machine']):
                continue
            for export in provider['symbols']:
                if export['undefined'] or export['bind'] not in (1, 2, 10) or export['visibility'] not in (0, 3):
                    continue
                if export['name'] != symbol['name']:
                    continue
                if symbol['version'] and export['version'] != symbol['version']:
                    continue
                if symbol['version_provider'] and provider.get('soname') != symbol['version_provider']:
                    continue
                if not symbol['version'] and export['version_hidden']:
                    continue
                candidates.append(name)
                break
        results.append({'symbol': symbol['name'], 'version': symbol['version'],
                        'required_provider': symbol['version_provider'],
                        'weak': symbol['bind'] == 2, 'candidate_providers': candidates,
                        'status': 'scope_candidate' if candidates else 'not_in_supplied_scope'})
    return {'results': results, 'warning': 'Caller must supply actual namespace/DT_NEEDED scope; '
            'symbol interposition, relocations and C++ layout remain unverified'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error('Output already exists')
    report = Elf(args.file).report()
    with args.out.open('x') as stream:
        json.dump(report, stream, indent=2)
    print(args.out)


if __name__ == '__main__':
    main()
