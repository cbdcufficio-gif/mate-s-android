import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from android_webview_preflight import parse_pointer, prepare_webview, verify_apk


class WebViewInputs(unittest.TestCase):
    def test_committed_pointer_contract(self):
        digest = 'a' * 64
        self.assertEqual(parse_pointer(('version https://git-lfs.github.com/spec/v1\noid sha256:' + digest + '\nsize 42\n').encode()), (digest, 42))
        for data in (b'not a pointer', b'version https://other.example/spec/v1\n', b''):
            with self.assertRaises(ValueError):
                parse_pointer(data)

    def test_valid_zip_requires_matching_hash_and_size(self):
        with tempfile.TemporaryDirectory() as directory:
            apk = Path(directory) / 'webview.apk'
            with zipfile.ZipFile(apk, 'w') as stream:
                stream.writestr('AndroidManifest.xml', b'fixture manifest')
            data = apk.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            self.assertTrue(verify_apk(apk, digest, len(data))['zip_crc_verified'])
            with self.assertRaises(ValueError):
                verify_apk(apk, '0' * 64, len(data))
            with self.assertRaises(ValueError):
                verify_apk(apk, digest, len(data) + 1)
            apk.write_bytes(b'not an APK')
            with self.assertRaises(zipfile.BadZipFile):
                verify_apk(apk, hashlib.sha256(apk.read_bytes()).hexdigest(), apk.stat().st_size)

    def test_no_local_download(self):
        with patch.dict(os.environ, {'GITHUB_ACTIONS': 'false'}), patch('android_webview_preflight.subprocess.check_output') as command:
            with self.assertRaises(ValueError):
                prepare_webview(Path('/not-used'))
            command.assert_not_called()
