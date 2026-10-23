import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from android_patches import PROJECT, TARGET, apply_patches


class AndroidPatchGuards(unittest.TestCase):
    def test_different_upstream_source_is_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)/TARGET
            target.parent.mkdir(parents=True)
            target.write_bytes(b'upstream source changed\n')
            with self.assertRaisesRegex(ValueError, 'Unexpected Android adapter source'):
                apply_patches(directory)
            self.assertEqual(target.read_bytes(), b'upstream source changed\n')

    def test_symlink_target_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root/TARGET
            target.parent.mkdir(parents=True)
            actual = root/'unchanged'
            actual.write_text('unchanged')
            target.symlink_to(actual)
            with self.assertRaisesRegex(ValueError, 'Symlink'):
                apply_patches(root)
            self.assertEqual(actual.read_text(), 'unchanged')

    def test_already_patched_source_is_not_modified(self):
        lock, = json.loads((PROJECT/'configs/android-patches.json').read_text())
        original_digest = __import__('android_patches').digest
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)/TARGET
            target.parent.mkdir(parents=True)
            target.write_text('stand-in for idempotence guard')
            def digest(path):
                return lock['after_sha256'] if path == target else original_digest(path)
            with patch('android_patches.digest', side_effect=digest):
                result = apply_patches(directory)
            self.assertEqual(result[0]['status'], 'ALREADY_APPLIED')
            self.assertEqual(target.read_text(), 'stand-in for idempotence guard')
