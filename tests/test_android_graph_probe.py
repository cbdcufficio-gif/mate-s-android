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

class CompilerCacheOptIn(unittest.TestCase):
    def test_cache_requires_explicit_disposable_runner_opt_in(self):
        for hosted, enabled, expected in [('true','1','1'), ('true','0','0'), ('false','1','0')]:
            with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {
                'GITHUB_ACTIONS':hosted,'RUNNER_ENVIRONMENT':'github-hosted','MATES_USE_CCACHE':enabled
            }), patch('android_graph_probe.subprocess.Popen') as start:
                start.return_value.poll.return_value = 0
                start.return_value.returncode = 0
                guarded(['unused'],directory,Path(directory)/'log',1,0)
                self.assertEqual(start.call_args.kwargs['env']['USE_CCACHE'], expected)
