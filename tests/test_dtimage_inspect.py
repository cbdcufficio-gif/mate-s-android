"""Synthetic parser tests; no Huawei payload is included."""
import struct
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from dtimage_inspect import inspect, parse_fdt


def fdt(board=(1, 4, 7, 6)):
    strings = b'hisi,boardid\0model\0compatible\0'
    body = struct.pack('>I', 1) + b'\0' * 4
    for name, value in ((b'hisi,boardid', struct.pack('>4I', *board)),
                        (b'model', b'test\0'), (b'compatible', b'test,board\0')):
        body += struct.pack('>III', 3, len(value), strings.index(name)) + value
        body += b'\0' * (-len(body) % 4)
    body += struct.pack('>II', 2, 9)
    header = struct.pack('>10I', 0xd00dfeed, 56 + len(body) + len(strings),
                         56, 56 + len(body), 40, 17, 16, 0, len(strings), len(body))
    return header + b'\0' * 16 + body + strings


def image():
    payload = fdt()
    entry = bytes((1, 4, 7, 6)) + b'\0' * 4 + struct.pack('<II', len(payload), 64) + b'\0' * 8
    return b'HSDT' + struct.pack('<II', 1, 1) + entry + b'\0' * 28 + payload


class FdtTests(unittest.TestCase):
    def test_root_values(self):
        result = parse_fdt(fdt())
        self.assertEqual(result['boardid'], [1, 4, 7, 6])
        self.assertEqual(result['compatible'], ['test,board'])

    def test_truncated_header_and_payload(self):
        for data in (b'', fdt()[:39], fdt()[:-1]):
            with self.subTest(length=len(data)), self.assertRaises(ValueError):
                parse_fdt(data)

    def test_invalid_property_name_offset(self):
        data = bytearray(fdt())
        struct.pack_into('>I', data, 72, 0xffffffff)
        with self.assertRaisesRegex(ValueError, 'property outside'):
            parse_fdt(data)

    def test_property_length_outside_structure(self):
        data = bytearray(fdt())
        struct.pack_into('>I', data, 68, 0xffffffff)
        with self.assertRaisesRegex(ValueError, 'property outside'):
            parse_fdt(data)

    def test_overlapping_blocks(self):
        data = bytearray(fdt())
        struct.pack_into('>I', data, 12, 60)
        with self.assertRaisesRegex(ValueError, 'overlapping'):
            parse_fdt(data)

    def test_unbalanced_structure(self):
        data = bytearray(fdt())
        struct.pack_into('>I', data, 56, 2)
        with self.assertRaisesRegex(ValueError, 'unbalanced'):
            parse_fdt(data)

    def test_missing_end(self):
        data = bytearray(fdt())
        end = struct.unpack_from('>I', data, 12)[0]
        struct.pack_into('>I', data, end - 4, 4)
        with self.assertRaisesRegex(ValueError, 'missing FDT END'):
            parse_fdt(data)

    def test_unreferenced_candidate_not_promoted(self):
        report = inspect(image() + b'\0' * 4 + fdt((1, 8, 9, 0)), [1, 4, 7, 6])
        self.assertEqual(report['validated_table_entries'], 1)
        self.assertEqual(report['matching_offsets'], [64])
        self.assertEqual(report['candidates'][1]['classification'], 'unreferenced_scan_candidate')
        self.assertFalse(report['dtb_selected'])

    def test_boardid_mismatch_rejects_table_hypothesis(self):
        data = bytearray(image())
        data[12] = 2
        with self.assertRaisesRegex(ValueError, 'boardid mismatch'):
            inspect(data, [1, 4, 7, 6])

    def test_table_overrun(self):
        with self.assertRaisesRegex(ValueError, 'unproven table'):
            inspect(image()[:-1], [1, 4, 7, 6])

    def test_trailing_bad_magic_recorded(self):
        report = inspect(image() + b'\xd0\x0d\xfe\xed', [1, 4, 7, 6])
        self.assertEqual(len(report['rejected_magic_hits']), 1)


if __name__ == '__main__':
    unittest.main()
