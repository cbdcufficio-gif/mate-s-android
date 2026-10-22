import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from remote_preflight import inspect_manifest


class ManifestTests(unittest.TestCase):
    def test_remote_revision_precedence_and_include(self):
        fixtures = {
            'default.xml': b'<manifest><remote name="gh"/><remote name="aosp" revision="tag-q"/>'
                           b'<default remote="gh" revision="branch-q"/>'
                           b'<project name="one"/><include name="snippets/x.xml"/></manifest>',
            'snippets/x.xml': b'<manifest><project name="two" remote="aosp"/>'
                              b'<project name="three" revision="0123456789012345678901234567890123456789"/></manifest>'}
        r = inspect_manifest(fixtures.__getitem__)
        self.assertEqual([p['revision'] for p in r['projects']],
                         ['branch-q', 'tag-q', '0123456789012345678901234567890123456789'])
        self.assertEqual(r['unfrozen_project_count'], 2)
        self.assertEqual(len(r['documents']), 2)

    def test_cycle_traversal_entity_and_unsupported_edits(self):
        for xml in [b'<manifest><include name="default.xml"/></manifest>',
                    b'<manifest><include name="../outside.xml"/></manifest>',
                    b'<!DOCTYPE manifest [<!ENTITY a "hello">]><manifest/>',
                    b'<manifest><remove-project name="x"/></manifest>',
                    b'<manifest><project name="x"><project name="y"/></project></manifest>']:
            with self.subTest(xml=xml), self.assertRaises(ValueError):
                inspect_manifest(lambda name: xml)


if __name__ == '__main__':
    unittest.main()
