import gzip
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import android_build_diagnostics as diag
class PublicDiagnosticsTests(unittest.TestCase):
    def test_allowlist_truncation_and_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'input';root.mkdir();out=Path(d)/'output'
            (root/'carrera-system.log').write_bytes(b'A'*100+b'B'*100)
            (root/'private.img').write_bytes(b'secret');(root/'report.json').symlink_to(root/'private.img')
            with patch.object(diag,'MAX_INPUT',32):diag.collect(root,out)
            files=json.loads((out/'inventory.json').read_text())['files']
            self.assertEqual(len(files),1);self.assertTrue(files[0]['truncated'])
            self.assertIn(b'DIAGNOSTIC_MIDDLE_TRUNCATED',gzip.decompress((out/'carrera-system.log.gz').read_bytes()))
            self.assertFalse((out/'private.img.gz').exists())
