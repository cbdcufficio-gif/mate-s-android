import sys
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import android_locked_manifest as lock
class LockedManifestTests(unittest.TestCase):
    def test_reviewed_lock(self):
        data=lock.LOCK.read_bytes();self.assertEqual(len(lock.project_revisions(data)),794)
        selected=ET.fromstring(data)
        for node in list(selected.findall('project')):
            if set(node.get('groups','').split(',')) & {'notdefault','darwin'}:selected.remove(node)
        self.assertEqual(lock.verify_synced(ET.tostring(selected))['selected_projects'],778)
        root=ET.fromstring(data);root.find('project').set('revision','0'*40)
        with self.assertRaises(ValueError):lock.verify_synced(ET.tostring(root))
    def test_invalid(self):
        for xml in [b'<manifest><include name="x"/></manifest>',b'<manifest/>',b'<manifest><project name="x" revision="main"/></manifest>']:
            with self.assertRaises(ValueError):lock.project_revisions(xml)
    def test_install_and_digest(self):
        with tempfile.TemporaryDirectory() as d:
            tree=Path(d);p=tree/'.repo/manifests/default.xml';p.parent.mkdir(parents=True);p.write_text('<manifest/>')
            lock.install_lock(tree);self.assertEqual(p.read_bytes(),lock.LOCK.read_bytes())
            with patch.object(lock,'DIGEST','0'*64):
                with self.assertRaises(ValueError):lock.install_lock(tree)
