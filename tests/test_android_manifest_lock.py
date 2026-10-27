import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from android_manifest_lock import select_revision

class ManifestLockTests(unittest.TestCase):
    def test_branch_and_peeled_tag(self):
        a='a'*40;b='b'*40
        self.assertEqual(select_revision(a+'\trefs/heads/q\n','q'),a)
        self.assertEqual(select_revision(a+'\trefs/tags/q\n'+b+'\trefs/tags/q^{}\n','refs/tags/q'),b)
    def test_ambiguous_missing_invalid(self):
        for rows in ['', 'a'*40+'\trefs/heads/q\n'+'b'*40+'\trefs/tags/q\n','bad\trefs/heads/q\n']:
            with self.assertRaises(ValueError):select_revision(rows,'q')
