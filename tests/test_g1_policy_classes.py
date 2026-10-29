import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from g1_policy_classes import compare,parse_setools
class PolicyClassContracts(unittest.TestCase):
    def test_common_permissions_and_userspace_separation(self):
        classes=' class file\ninherits file\n{\nwatch\n}\n class property_service\n{ set }\n class process2\n{ nnp_transition }\n'
        common=' common file\n{ read write }\n';kernel='{ "file", { "read", "write", NULL } },'
        r=compare(classes,common,kernel);self.assertEqual(r['permissions_absent_from_mapped_kernel_classes'],{'file':['watch']});self.assertEqual(r['userspace_classes_separated'],['property_service']);self.assertEqual(r['policy_classes_without_kernel_mapping'],['process2'])
    def test_missing_inherited_common_is_error(self):
        with self.assertRaises(ValueError):compare(' class file\ninherits missing\n',' common other\n{ read }','{ "file", { "read", NULL } }')
    def test_empty_parser_rejected(self):
        with self.assertRaises(ValueError):parse_setools('no inventory','class')
