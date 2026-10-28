import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import android_carrera_system_probe as probe

class PhaseBudgetAndCache(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.base=Path(self.temp.name)
        self.root=self.base/'android-graph'
        self.root.mkdir()
        self.cache=self.base/'ccache'
        self.cache.mkdir()
        (self.cache/'entry').write_bytes(b'public cache fixture')
        self.root_patch=patch.object(probe,'ROOT',self.root)
        self.root_patch.start()
        self.env=patch.dict(os.environ,{'MATES_USE_CCACHE':'1','CCACHE_DIR':str(self.cache)})
        self.env.start()
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(self.root_patch.stop)
        self.addCleanup(self.env.stop)
    def stats(self,*args,**kwargs):
        kwargs['stdout'].write('cache stats saved\n')
        return SimpleNamespace(returncode=0)
    def result(self,code=0,reason=None):
        return {'returncode':code,'stop_reason':reason,'seconds':10,'free_bytes':20*1024**3}
    def test_dependencies_finish_and_stats_persist_before_cache_release(self):
        report={}
        commands=[]
        def run(argv,cwd,log,**kwargs):
            commands.append(argv[-1])
            if len(commands)==1:
                self.assertTrue(self.cache.is_dir())
                self.assertIn('installed-file-list',argv[-1])
                self.assertNotIn(' systemimage ',argv[-1])
            else:
                self.assertFalse(self.cache.exists())
                self.assertEqual((self.root/'ccache-before-cleanup.log').read_text(),'cache stats saved\n')
                self.assertIn(' systemimage ',argv[-1])
                self.assertNotIn('snod',argv[-1])
            self.assertEqual(kwargs['reserve'],8*1024**3)
            return self.result()
        with patch.object(probe,'guarded',side_effect=run),patch.object(probe.subprocess,'run',side_effect=self.stats):
            result=probe.build_system_phases(self.base,3,report)
        self.assertEqual(result['returncode'],0)
        self.assertEqual(len(commands),2)
        self.assertTrue(report['compiler_cache_removed_before_system_image'])
        self.assertEqual(len(json.loads((self.root/'carrera-system-report.json').read_text())['build_phases']),2)
    def test_failed_dependencies_preserve_cache_and_never_assemble(self):
        for result in (self.result(1),self.result(-15,'DISK_RESERVE_REACHED')):
            with patch.object(probe,'guarded',return_value=result) as run,patch.object(probe.subprocess,'run',side_effect=self.stats):
                actual=probe.build_system_phases(self.base,3,{})
            self.assertEqual(actual['stop_reason'],result['stop_reason'])
            self.assertEqual(run.call_count,1)
            self.assertTrue(self.cache.exists())
    def test_second_phase_uses_remaining_budget(self):
        with patch.object(probe,'guarded',return_value=self.result()) as run,patch.object(probe.subprocess,'run',side_effect=self.stats),patch.object(probe.time,'monotonic',side_effect=[100,100,175,180]):
            probe.build_system_phases(self.base,3,{},budget=100)
        self.assertEqual([x.kwargs['seconds'] for x in run.call_args_list],[100,25])
    def test_expired_budget_never_starts_image_command(self):
        with patch.object(probe,'guarded',return_value=self.result()) as run,patch.object(probe.subprocess,'run',side_effect=self.stats),patch.object(probe.time,'monotonic',side_effect=[100,100,201,202]):
            result=probe.build_system_phases(self.base,3,{},budget=100)
        self.assertEqual(run.call_count,1)
        self.assertEqual(result['stop_reason'],'TIME_BUDGET_REACHED')
    def test_cache_path_mismatch_preserves_cache(self):
        with patch.dict(os.environ,{'CCACHE_DIR':str(self.base/'wrong')}),patch.object(probe,'guarded',return_value=self.result()) as run,patch.object(probe.subprocess,'run',side_effect=self.stats):
            with self.assertRaisesRegex(ValueError,'Unexpected compiler cache'):
                probe.build_system_phases(self.base,3,{})
        self.assertEqual(run.call_count,1)
        self.assertTrue(self.cache.exists())
    def test_statistics_failure_prevents_cache_removal(self):
        with patch.object(probe,'guarded',return_value=self.result()) as run,patch.object(probe.subprocess,'run',return_value=SimpleNamespace(returncode=1)):
            with self.assertRaisesRegex(ValueError,'statistics'):
                probe.build_system_phases(self.base,3,{})
        self.assertEqual(run.call_count,1)
        self.assertTrue(self.cache.exists())

if __name__=='__main__':unittest.main()
