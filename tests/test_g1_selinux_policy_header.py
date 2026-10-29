import struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from g1_selinux_policy_header import MAGIC,parse_header,inspect_g0
class PolicyHeader(unittest.TestCase):
    def header(self,flags):return struct.pack('<II',MAGIC,8)+b'SE Linux'+struct.pack('<IIII',30,flags,8,7)
    def test_flags_are_distinct_and_little_endian(self):
        for flags in range(8):
            p=parse_header(self.header(flags));self.assertEqual(p['mls'],bool(flags&1));self.assertEqual(p['reject_unknown'],bool(flags&2));self.assertEqual(p['allow_unknown'],bool(flags&4))
    def test_bad_or_truncated_header_rejected(self):
        for data in [b'',self.header(1)[:10],self.header(1)[:-1],b'bad!'+self.header(1)[4:],self.header(1)[:8]+b'badbytes'+self.header(1)[16:]]:
            with self.subTest(data=data),self.assertRaises(ValueError):parse_header(data)
    def test_g0_requires_full_verified_digest(self):
        with self.assertRaises(ValueError):inspect_g0(self.header(1))
