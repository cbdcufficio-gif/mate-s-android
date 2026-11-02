"""Inspect actual ext4 bytes; no guest init or hardware is executed."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from g1_bootstrap_probe import Image
from g1_init_inventory import capture

class InitInventory(unittest.TestCase):
    @unittest.skipUnless(shutil.which('mke2fs') and shutil.which('debugfs'), 'ext4 tools required')
    def test_actual_ext4_inventory_preserves_text_and_reports_links(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / 'root'
            nested = root / 'system/etc/init/hw'
            nested.mkdir(parents=True)
            text = 'on boot\n    mount functionfs adb /dev/usb-ffs/adb\n'
            (root / 'init.rc').write_text('import /system/etc/init/hw/usb.rc\n')
            (nested / 'usb.rc').write_text(text)
            (nested / 'ignored.img').write_bytes(b'not evidence')
            (nested / 'linked.rc').symlink_to('/init.rc')
            raw = base / 'image.ext4'
            with raw.open('wb') as stream:
                stream.truncate(16 * 1024 * 1024)
            subprocess.run(['mke2fs', '-q', '-t', 'ext4', '-F', '-d', str(root), str(raw)], check=True, capture_output=True)
            out = base / 'out'
            out.mkdir()
            result = capture(Image(raw, out))
            files = {row['path']: row for row in result['files']}
            self.assertEqual(set(files), {'/init.rc', '/system/etc/init/hw/usb.rc'})
            self.assertEqual(files['/system/etc/init/hw/usb.rc']['text'], text)
            self.assertIn({'path': '/system/etc/init/hw/linked.rc', 'type': 'symlink'}, result['unresolved'])
            self.assertFalse(result['runtime_imports_resolved'])
