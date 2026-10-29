import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from g1_elf_versions import version_names,compare
class ElfVersionContracts(unittest.TestCase):
    def matrix(self,version='LIBC'):
        return [{'guest':'/init','physical':'/init','version_info':"Version needs section '.gnu.version_r':\n  File: libc.so Cnt: 1\n  Name: LIBC Flags: none\n",'dependencies':[{'needed':'libc.so','candidates':[{'physical':'/libc.so'}]}]}, {'guest':'/libc.so','physical':'/libc.so','version_info':"Version definition section '.gnu.version_d':\n  Name: "+version+' Flags: none\n','dependencies':[]}]
    def test_versions_match(self):self.assertEqual(compare(self.matrix())['unresolved'],[])
    def test_missing_version(self):self.assertEqual(compare(self.matrix('OTHER'))['unresolved'][0]['missing'],['LIBC'])
    def test_missing_provider_inventory(self):self.assertTrue(compare(self.matrix()[:1])['unresolved'])
    def test_symbol_listing_does_not_define_versions(self):self.assertEqual(version_names('Version symbols section x:\n Name: LIBC'),(set(),{}))
