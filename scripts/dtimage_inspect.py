#!/usr/bin/env python3
"""Read-only Huawei HSDT/FDT metadata inspection; never selects or installs a DTB."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

MAGIC = b'\xd0\x0d\xfe\xed'
MAX_IMAGE = 64 * 1024 * 1024


def parse_fdt(data, offset=0):
    """Validate v17 FDT boundaries/tokens and return selected root metadata."""
    def require(condition, reason):
        if not condition:
            raise ValueError(reason)
    require(0 <= offset <= len(data) - 40, 'truncated FDT header')
    magic, total, st, strings, reserve, version, compat, cpu, ns, nt = struct.unpack_from('>10I', data, offset)
    require(magic == 0xd00dfeed and version == 17 and compat <= 17, 'unsupported FDT header')
    require(40 <= total <= len(data) - offset, 'truncated FDT payload')
    b = memoryview(data)[offset:offset + total]
    require(st >= 40 and st % 4 == 0 and nt >= 4 and nt % 4 == 0 and st + nt <= total, 'invalid structure range')
    require(strings >= 40 and strings + ns <= total, 'invalid strings range')
    require(st + nt <= strings or strings + ns <= st, 'overlapping FDT blocks')
    require(reserve >= 40 and reserve % 8 == 0, 'invalid reserve map')
    rend = reserve
    while True:
        require(rend + 16 <= total, 'unterminated reserve map')
        address, size = struct.unpack_from('>QQ', b, rend)
        rend += 16
        if address == size == 0:
            break
    for start, size in ((st, nt), (strings, ns)):
        require(rend <= start or start + size <= reserve, 'overlapping reserve map')
    string_table = bytes(b[strings:strings + ns])
    p, end, stack, root_seen, root_done = st, st + nt, [], False, False
    props, ended = {}, False
    while p < end:
        require(p + 4 <= end, 'truncated token')
        token = struct.unpack_from('>I', b, p)[0]
        p += 4
        if token == 1:
            require(not root_done, 'multiple root nodes')
            remaining = bytes(b[p:end])
            nul = remaining.find(b'\0')
            require(nul >= 0, 'unterminated node name')
            name = remaining[:nul]
            if not stack:
                require(not root_seen and name == b'', 'invalid root node')
                root_seen = True
            else:
                require(bool(name) and b'/' not in name, 'invalid node name')
            stack.append(set())
            p = (p + nul + 4) & ~3
            require(p <= end, 'truncated node padding')
        elif token == 2:
            require(bool(stack), 'unbalanced END_NODE')
            stack.pop()
            if not stack:
                root_done = True
        elif token == 3:
            require(bool(stack) and p + 8 <= end, 'invalid property header')
            length, nameoff = struct.unpack_from('>II', b, p)
            p += 8
            require(p + length <= end and nameoff < ns, 'property outside block')
            nameend = string_table.find(b'\0', nameoff)
            require(nameend >= 0, 'unterminated property name')
            name = string_table[nameoff:nameend].decode('ascii')
            require(bool(name) and name not in stack[-1], 'duplicate/empty property')
            stack[-1].add(name)
            if len(stack) == 1 and name in ('hisi,boardid', 'model', 'compatible'):
                props[name] = bytes(b[p:p + length])
            p = (p + length + 3) & ~3
            require(p <= end, 'truncated property padding')
        elif token == 4:
            pass
        elif token == 9:
            require(root_done and not stack, 'premature END')
            require(not any(b[p:end]), 'data after END')
            ended = True
            break
        else:
            raise ValueError('unknown FDT token')
    require(ended, 'missing FDT END')
    result = {'offset': offset, 'totalsize': total, 'sha256': hashlib.sha256(b).hexdigest(),
              'version': version, 'last_compatible_version': compat, 'boot_cpuid_phys': cpu}
    for name in ('model', 'compatible'):
        if name in props:
            require(props[name].endswith(b'\0'), 'unterminated root string')
            result[name] = props[name][:-1].decode('utf-8').split('\0')
    if 'hisi,boardid' in props:
        require(len(props['hisi,boardid']) == 16, 'unexpected boardid length')
        result['boardid'] = list(struct.unpack('>4I', props['hisi,boardid']))
    return result


def inspect(data, active_boardid):
    if len(data) > MAX_IMAGE or len(data) < 12 or data[:4] != b'HSDT':
        raise ValueError('invalid or oversized HSDT image')
    version, count = struct.unpack_from('<II', data, 4)
    if version != 1 or not 1 <= count <= 4096 or 12 + count * 24 > len(data):
        raise ValueError('unsupported HSDT header/table')
    candidates, rejected = {}, []
    offset = data.find(MAGIC)
    while offset >= 0:
        try:
            candidates[offset] = parse_fdt(data, offset)
        except (ValueError, UnicodeError) as error:
            rejected.append({'offset': offset, 'error': str(error)})
        offset = data.find(MAGIC, offset + 4)
    entries, ranges, table_end = [], [], 12 + count * 24
    for index in range(count):
        raw = data[12 + index * 24:36 + index * 24]
        size, offset = struct.unpack_from('<II', raw, 8)
        fdt = candidates.get(offset)
        if offset < table_end or not fdt or not size or offset + size > len(data) or fdt['totalsize'] > size:
            raise ValueError(f'unproven table layout at entry {index}')
        boardid = list(raw[:4])
        if fdt.get('boardid') != boardid:
            raise ValueError(f'table/root boardid mismatch at entry {index}')
        if any(offset < stop and start < offset + size for start, stop in ranges):
            raise ValueError('overlapping table payloads')
        ranges.append((offset, offset + size))
        entries.append({'index': index, 'boardid': boardid, 'offset': offset,
                        'allocated_size': size, 'fdt_size': fdt['totalsize'],
                        'unknown_bytes_4_7': raw[4:8].hex(),
                        'unknown_bytes_16_23': raw[16:24].hex()})
    referenced = {entry['offset']: entry['index'] for entry in entries}
    for offset, fdt in candidates.items():
        fdt['table_index'] = referenced.get(offset)
        fdt['classification'] = 'table_referenced' if offset in referenced else 'unreferenced_scan_candidate'
        fdt['matches_active_boardid'] = fdt.get('boardid') == active_boardid
    return {'status': 'STATIC_METADATA_ONLY', 'image_bytes': len(data),
            'image_sha256': hashlib.sha256(data).hexdigest(), 'hsdt_version': version,
            'declared_count': count, 'validated_table_entries': len(entries),
            'table_layout': 'inferred 24-byte records from offset 12; all payloads and boardids validated',
            'unknown_table_fields': ['bytes4..7', 'bytes16..23'],
            'active_boardid': active_boardid, 'candidates': list(candidates.values()),
            'rejected_magic_hits': rejected, 'entries': entries,
            'matching_offsets': [o for o, f in candidates.items() if f['matches_active_boardid']],
            'dtb_selected': False, 'bootloader_selection_proven': False,
            'hardware_tested': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image', type=Path, required=True)
    p.add_argument('--active-boardid-hex', required=True, help='16 bytes as read from live root hisi,boardid')
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    try:
        board = bytes.fromhex(a.active_boardid_hex)
        if len(board) != 16 or a.image.stat().st_size > MAX_IMAGE:
            raise ValueError('invalid boardid or oversized input')
        report = inspect(a.image.read_bytes(), list(struct.unpack('>4I', board)))
        with a.out.open('x') as stream:
            json.dump(report, stream, indent=2)
            stream.write('\n')
        print(json.dumps({key: report[key] for key in ('status', 'validated_table_entries', 'matching_offsets')}))
    except (OSError, ValueError) as error:
        p.exit(1, f'STOP: {error}\n')


if __name__ == '__main__':
    main()
