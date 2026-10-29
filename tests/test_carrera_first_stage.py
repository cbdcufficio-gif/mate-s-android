import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('g1_first_stage',ROOT/'scripts/g1_first_stage_probe.py')
probe=importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

class FirstStageCandidateSafety(unittest.TestCase):
    def setUp(self):
        self.old=json.loads((ROOT/'docs/G1-PUBLIC-CONFIG-RESULT.json').read_text())['configs']['/fstab.hi3635']['text']
    def test_only_system_flag_changes_and_userdata_bytes_survive(self):
        new=probe.candidate(self.old)
        oldrows=self.old.splitlines()
        newrows=new.splitlines()
        self.assertEqual(len(oldrows),len(newrows))
        changed=[(a,b) for a,b in zip(oldrows,newrows) if a!=b]
        self.assertEqual(len(changed),1)
        self.assertEqual(changed[0][1],changed[0][0]+',first_stage_mount')
        self.assertIn('encryptable=footer',new)
    def test_missing_or_duplicate_system_is_rejected(self):
        row=next(l for l in self.old.splitlines() if l.split() and not l.startswith('#') and l.split()[1]=='/system')
        for text in (self.old.replace(row+'\n',''),self.old+row+'\n'):
            with self.assertRaises(ValueError): probe.candidate(text)
    def test_unexpected_flags_are_not_silently_overwritten(self):
        with self.assertRaises(ValueError): probe.candidate(probe.candidate(self.old))
        with self.assertRaises(ValueError): probe.candidate(self.old.replace('wait\n','wait,formattable\n'))
    def test_malformed_fstab_is_rejected(self):
        with self.assertRaises(ValueError): probe.candidate(self.old+'/dev/unknown /data ext4\n')
