import hashlib
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import android_carrera_system_probe as probe

def sparse_bytes(skip=4096,fill=2,kind=0xcac3):
    block=4096
    raw=b'A'*block
    fill_value=struct.pack('<I',0x12345678)
    chunks=[
        struct.pack('<HHII',0xcac1,0,1,12+len(raw))+raw,
        struct.pack('<HHII',0xcac2,0,fill,16)+fill_value,
        struct.pack('<HHII',kind,0,skip,12)]
    return struct.pack('<IHHHHIIII',0xed26ff3a,1,0,28,12,block,1+fill+skip,len(chunks),0)+b''.join(chunks)

class SparseAllocationBudget(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)
        self.image=self.base/'system.sparse.img'
        patcher=patch.object(probe,'ROOT',self.base)
        patcher.start()
        self.addCleanup(patcher.stop)
    def write(self,data):
        self.image.write_bytes(data)
        return self.image
    def test_holes_excluded_but_fill_fully_budgeted(self):
        budget=probe.sparse_expansion_budget(self.write(sparse_bytes()))
        self.assertEqual(budget['raw_and_fill_bytes'],3*4096)
        self.assertEqual(budget['dont_care_bytes'],4096*4096)
        self.assertEqual(budget['reserve_bytes'],8*1024**3)
        self.assertGreaterEqual(budget['allocation_slack_bytes'],64*1024**2)
        self.assertEqual(budget['chunk_types'],{'raw':1,'fill':1,'dont_care':1,'crc32':0})
    def test_dense_fill_is_not_mistaken_for_holes(self):
        budget=probe.sparse_expansion_budget(self.write(sparse_bytes(skip=0,fill=100)))
        self.assertEqual(budget['raw_and_fill_bytes'],budget['logical_bytes'])
    def test_truncated_payload_and_unknown_chunk_rejected(self):
        for data in (sparse_bytes()[:-1],sparse_bytes(kind=0x9999)):
            with self.assertRaises(ValueError):
                probe.sparse_expansion_budget(self.write(data))
    def test_output_block_mismatch_and_trailing_data_rejected(self):
        data=bytearray(sparse_bytes())
        struct.pack_into('<I',data,16,1)
        for value in (bytes(data),sparse_bytes()+b'trailing'):
            with self.assertRaises(ValueError):
                probe.sparse_expansion_budget(self.write(value))
    def test_expanded_partition_limit_remains_enforced(self):
        with self.assertRaisesRegex(ValueError,'geometry'):
            probe.sparse_expansion_budget(self.write(sparse_bytes(skip=1000000)))

    @unittest.skipUnless(shutil.which('simg2img'),'requires reference simg2img')
    def test_converter_holes_physical_allocation_and_complete_bytes(self):
        self.write(sparse_bytes(skip=32768))
        raw=self.base/'system.raw.img'
        budget=probe.sparse_expansion_budget(self.image)
        subprocess.run(['simg2img',str(self.image),str(raw)],check=True)
        self.assertEqual(raw.stat().st_size,budget['logical_bytes'])
        self.assertLess(raw.stat().st_blocks*512,raw.stat().st_size//10)
        self.assertLessEqual(raw.stat().st_blocks*512,budget['allocation_budget_bytes'])
        digest=hashlib.sha256()
        digest.update(b'A'*4096)
        digest.update(struct.pack('<I',0x12345678)*(2*4096//4))
        zero=b'\0'*(1024**2)
        for index in range(128):digest.update(zero)
        actual=hashlib.sha256()
        with raw.open('rb') as stream:
            for data in iter(lambda:stream.read(1024**2),b''):actual.update(data)
        self.assertEqual(actual.digest(),digest.digest())
        print('SPARSE_REFERENCE_MEASURED',raw.stat().st_size,raw.stat().st_blocks*512,budget['allocation_budget_bytes'])

    @unittest.skipUnless(all(shutil.which(t) for t in ('mke2fs','debugfs','img2simg','simg2img')),'requires ext4 and sparse tools')
    def test_real_sparse_ext4_conversion_verifies_all_module_hashes(self):
        tree=self.base/'tree'
        lib=tree/'system/lib'
        vendor=tree/'system/vendor/lib64'
        lib.mkdir(parents=True)
        vendor.mkdir(parents=True)
        modules=[]
        for name in ('system/lib/libpublic.so','system/vendor/lib64/libpublic.so'):
            path=tree/name
            path.write_bytes(name.encode())
            modules.append({'path':name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        original=self.base/'original.img'
        with original.open('wb') as stream:stream.truncate(128*1024**2)
        subprocess.run(['mke2fs','-q','-F','-t','ext4','-d',str(tree),str(original)],check=True,
                       stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        subprocess.run(['img2simg',str(original),str(self.image)],check=True)
        binary=self.base/'out/host/linux-x86/bin/simg2img'
        binary.parent.mkdir(parents=True)
        os.symlink(shutil.which('simg2img'),binary)
        report=probe.verify_modules_in_system_image(self.base,self.image,modules)
        self.assertEqual(report['modules_verified'],2)
        self.assertEqual(report['layout_evidence']['layout'],'q-root-with-system')
        self.assertEqual(report['expansion_space']['conversion']['returncode'],0)
        self.assertGreaterEqual(report['expansion_space']['free_bytes_after'],8*1024**3)
        self.assertLessEqual(report['expansion_space']['actual_allocated_bytes'],
                             report['expansion_space']['allocation_budget_bytes'])

    @unittest.skipUnless(all(shutil.which(t) for t in ('mke2fs','debugfs','img2simg','simg2img')),'requires ext4 and sparse tools')
    def test_relative_report_root_with_different_android_child_cwd(self):
        # Production topology: ROOT is relative, while conversion cwd is source/.
        previous=Path.cwd()
        with tempfile.TemporaryDirectory() as workspace:
            try:
                os.chdir(workspace)
                root=Path('out/android-graph')
                android=root/'source'
                tree=root/'fixture'
                modules=[]
                for name in ('system/lib/libpublic.so','system/vendor/lib64/libpublic.so'):
                    path=tree/name
                    path.parent.mkdir(parents=True,exist_ok=True)
                    path.write_bytes(name.encode())
                    modules.append({'path':name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
                original=root/'original.img'
                with original.open('wb') as stream:stream.truncate(128*1024**2)
                subprocess.run(['mke2fs','-q','-F','-t','ext4','-d',str(tree),str(original)],
                               check=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
                image=android/'out/target/product/carrera/system.img'
                image.parent.mkdir(parents=True)
                subprocess.run(['img2simg',str(original),str(image)],check=True)
                binary=android/'out/host/linux-x86/bin/simg2img'
                binary.parent.mkdir(parents=True)
                os.symlink(shutil.which('simg2img'),binary)
                with patch.object(probe,'ROOT',root):
                    report=probe.verify_modules_in_system_image(android.resolve(),image.resolve(),modules)
                self.assertEqual(report['modules_verified'],2)
                self.assertEqual(report['layout_evidence']['layout'],'q-root-with-system')
                space=report['expansion_space']
                self.assertEqual(space['conversion']['returncode'],0)
                self.assertEqual(space['converter_cwd'],str(android.resolve()))
                self.assertEqual(space['converter_input'],str(image.resolve()))
                self.assertTrue(Path(space['converter_output']).is_absolute())
                self.assertTrue((root/'carrera-ext4-space.json').is_file())
                self.assertGreaterEqual(space['free_bytes_after'],8*1024**3)
                print('RELATIVE_ROOT_DIFFERENT_CWD_REAL_EXT4_VERIFIED',report['modules_verified'])
            finally:
                os.chdir(previous)


if __name__=='__main__':unittest.main()
