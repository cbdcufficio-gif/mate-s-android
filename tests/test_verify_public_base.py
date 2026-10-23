import gzip
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from verify_public_base import verify, FILES


def fixture(root):
    for name in FILES:(root/name).write_bytes(b'fixture')
    image=gzip.compress(b'generic public base')
    (root/'generic-q-system.img.gz').write_bytes(image)
    common={'product':'lineage_arm64-userdebug','rom_built':False,'carrera_built':False,'hardware_tested':False}
    system={**common,'status':'PUBLIC_GENERIC_SYSTEM_IMAGE_BUILT','proprietary_huawei_inputs':False,
            'compressed_image':{'bytes':len(image),'sha256':hashlib.sha256(image).hexdigest()}}
    (root/'system-report.json').write_text(json.dumps(system))
    (root/'modules-report.json').write_text(json.dumps({**common,'status':'PUBLIC_GRAPHICS_MODULES_BUILT','proprietary_inputs':False}))
    checksum(root)

def checksum(root):
    (root/'SHA256SUMS').write_text(''.join(hashlib.sha256((root/n).read_bytes()).hexdigest()+'  '+n+'\n' for n in sorted(FILES)))

class PublicBaseChecks(unittest.TestCase):
    def test_success_does_not_imply_hardware_or_authenticity(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);fixture(p);r=verify(p)
            self.assertFalse(r['hardware_compatibility_verified']);self.assertFalse(r['authenticity_verified'])
    def test_modified_asset_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);fixture(p);(p/'resolved-manifest.xml').write_text('changed')
            with self.assertRaises(ValueError):verify(p)
    def test_duplicate_checksum_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);fixture(p);s=p/'SHA256SUMS';s.write_text(s.read_text()+s.read_text().splitlines()[0]+'\n')
            with self.assertRaises(ValueError):verify(p)
    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);fixture(p);f=p/'PUBLIC-BASE-README.txt';f.unlink();f.symlink_to('/etc/hosts')
            with self.assertRaises(ValueError):verify(p)
    def test_rom_claim_rejected_even_with_matching_hashes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);fixture(p);f=p/'system-report.json';j=json.loads(f.read_text());j['rom_built']=True;f.write_text(json.dumps(j));checksum(p)
            with self.assertRaises(ValueError):verify(p)

if __name__=='__main__':unittest.main()
