import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from android_graph_probe import guarded, main

class GraphGuard(unittest.TestCase):
    def test_local_download_refused(self):
        with patch.dict(os.environ, {'GITHUB_ACTIONS':'false'}):
            with self.assertRaises(SystemExit): main()
    def test_time_budget_stops_process(self):
        with tempfile.TemporaryDirectory() as d:
            r=guarded([sys.executable,'-c','import time;time.sleep(60)'],d,Path(d)/'log',0,0)
            self.assertEqual(r['stop_reason'],'TIME_BUDGET_REACHED')
            self.assertIsNotNone(r['returncode'])
    def test_disk_reserve_stops_process(self):
        with tempfile.TemporaryDirectory() as d:
            r=guarded([sys.executable,'-c','import time;time.sleep(60)'],d,Path(d)/'log',60,10**30)
            self.assertEqual(r['stop_reason'],'DISK_RESERVE_REACHED')
            self.assertIsNotNone(r['returncode'])

if __name__=='__main__':unittest.main()
