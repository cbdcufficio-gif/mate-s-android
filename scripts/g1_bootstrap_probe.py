#!/usr/bin/env python3
"""G1 cache/root and bootstrap contracts using immutable public G0 bytes."""
import json,os,posixpath,re,subprocess,tempfile
from pathlib import Path
from elf_audit import Elf
from g1_contract_common import ROOT,guard,source,function,sha,suite,publish
from review_public_system import download,bounded_gzip

class Image:
    def __init__(self,raw,out):self.raw=raw;self.out=out;self.counter=0;self.nodes={};self.extracted={}
    def command(self,cmd):return subprocess.check_output(['debugfs','-R',cmd,str(self.raw)],stderr=subprocess.STDOUT,text=True,timeout=60)
    def stat(self,path):
        if not re.fullmatch(r'/[A-Za-z0-9_./+@-]*',path) or '..' in path.split('/'):raise ValueError('Unsafe guest path')
        if path in self.nodes:return self.nodes[path]
        text=self.command('stat '+path);m=re.search(r'Type:\s+(\w+)',text)
        self.nodes[path]={'type':m[1] if m else None,'text':text}
        return self.nodes[path]
    def read(self,path,required=True):
        if path in self.extracted:return self.extracted[path]
        node=self.stat(path)
        if node['type'] is None:
            if required:raise ValueError('Missing public file '+path)
            return None
        self.counter+=1;p=self.out/f'file-{self.counter}'
        self.command('dump '+path+' '+str(p))
        if not p.is_file():
            if required:raise ValueError('Unable to extract '+path)
            return None
        if p.stat().st_size>128*1024**2:raise ValueError('Extracted file budget exceeded')
        self.extracted[path]=p
        return p
    def link(self,path):
        node=self.stat(path)
        if node['type']!='symlink':return None
        m=re.search(r'Fast link dest:\s*"([^"]+)"',node['text'])
        if m:return m[1]
        file=self.read(path);return file.read_bytes().decode().rstrip('\x00')
    def canonical(self,path,apex):
        chain=[]
        for _ in range(24):
            for name,directory in apex.items():
                prefix='/apex/'+name
                if path==prefix or path.startswith(prefix+'/'):path='/system/apex/'+directory+path[len(prefix):];break
            parts=path.strip('/').split('/');changed=False
            for i in range(len(parts)):
                prefix='/'+ '/'.join(parts[:i+1]);target=self.link(prefix)
                if target is not None:
                    chain.append({'path':prefix,'target':target})
                    nextpath=target if target.startswith('/') else posixpath.join(posixpath.dirname(prefix),target)
                    path=posixpath.normpath(posixpath.join(nextpath,*parts[i+1:]));changed=True;break
            if not changed:return path,chain
        raise ValueError('Guest symlink cycle/budget')

def default_paths(config,bits):
    section=None;values=[]
    for line in config.splitlines():
        line=line.split('#',1)[0].strip()
        if line.startswith('['):section=line.strip('[]')
        m=re.fullmatch(r'namespace.default.search.paths\s*(\+?=)\s*(.*)',line)
        if m and section=='legacy':
            if m[1]=='=':values=[]
            values+=m[2].replace('${LIB}','lib64' if bits==64 else 'lib').split(':')
    return values

def main():
    guard();os.chdir(ROOT);subprocess.run(['sha256sum','-c','SHA256SUMS'],check=True)
    out=ROOT/'out/g1-bootstrap';out.mkdir(parents=True,exist_ok=False);evidence=out/'evidence';evidence.mkdir()
    from g1_usb_fixture import execute
    usb=execute(out)
    tests=suite();pair=out/'pair';release,assets=download('carrera-public-system-40696459171',pair,800*1024**2)
    import gzip,shutil
    if shutil.disk_usage(out).free<8*1024**3+2*2684354560:raise ValueError('Reserve8GiB plus image inspection budget')
    sparse=out/'system.sparse.img'
    with gzip.open(pair/'carrera-public-system.img.gz','rb') as src,sparse.open('xb') as dst:
        count=0
        while block:=src.read(1024**2):
            count+=len(block)
            if count>2684354560:raise ValueError('Image exceeds geometry')
            dst.write(block)
    raw=out/'system.raw.img';subprocess.run(['simg2img',str(sparse),str(raw)],check=True,timeout=180)
    image=Image(raw,out);link=image.link('/cache')
    if link!='/data/cache':raise ValueError('Unexpected actual G0 cache link: '+str(link))
    mk=source('rootdir/Android.mk');match=re.search(r'ifdef BOARD_CACHEIMAGE_FILE_SYSTEM_TYPE\n.*?\nendif',mk,re.S)
    if not match or 'mkdir -p $(TARGET_ROOT_OUT)/cache' not in match[0] or 'ln -sf /data/cache' not in match[0]:raise ValueError('Upstream staging contract changed')
    # Execute the unchanged conditional/commands with GNU make on a small fixture.
    block=match[0]
    for kind in ('old','candidate'):
        directory=out/kind
        make=f'TARGET_ROOT_OUT := {directory}\n'+('BOARD_CACHEIMAGE_FILE_SYSTEM_TYPE := ext4\n' if kind=='candidate' else '')+'LOCAL_POST_INSTALL_CMD := true\n'+block+'\nall:\n\tmkdir -p $(TARGET_ROOT_OUT)\n\t$(LOCAL_POST_INSTALL_CMD)\n'
        path=out/(kind+'.mk');path.write_text(make);subprocess.run(['make','-f',str(path)],check=True)
    if not (out/'old/cache').is_symlink() or not (out/'candidate/cache').is_dir() or (out/'candidate/cache').is_symlink():raise ValueError('Staging fixture failed')
    import urllib.request
    build_pins={'core/Makefile': '3579ea7fc8b120fd9ce25f6a0f1ce78b88822d3823250e9adf32825d04ee655e', 'core/board_config.mk': '80cd356aa25090d3d8260ce722a1a25d291d6c56565295d58c5ad578fb6b14c4'}
    build_sources={}
    for name,digest in build_pins.items():
        with urllib.request.urlopen('https://raw.githubusercontent.com/LineageOS/android_build/71a47798ac090b81c6b7db0b5c470f1fa3e604cd/'+name,timeout=45) as response:data=response.read(1024**2)
        if sha(data)!=digest:raise ValueError('Build source contract changed: '+name)
        build_sources[name]=data.decode()
    rules=build_sources['core/board_config.mk']
    cache_rule=rules[rules.index('# Are we building a cache image'):rules.index('.KATI_READONLY := BUILDING_CACHE_IMAGE')]
    cache_make=out/'cache-target.mk'
    cache_make.write_text('BOARD_CACHEIMAGE_FILE_SYSTEM_TYPE := ext4\n'+cache_rule+'\nall:\n\t@test "$(BUILDING_CACHE_IMAGE)" = true\n\t@test -z "$(BOARD_CACHEIMAGE_PARTITION_SIZE)"\n')
    subprocess.run(['make','-f',str(cache_make)],check=True)
    build_contract={'source_sha256':build_pins,'cache_image_enabled_by_default_with_flag':True,'cache_image_geometry_not_declared':True,'cache_image_build_not_requested':True,'limitation':'Only systemimage/installed-file-list current goals reviewed; cache.img/droid packaging requires separately verified Carrera geometry, no full Kati graph executed'}
    fs=source('fs_mgr/fs_mgr.cpp');body=function(fs,'static int __mount(')
    harness=(ROOT/'tests/fixtures/q_cache_mount_harness.cpp.in').read_text().replace('__UPSTREAM_FUNCTION__',body)
    cpp=out/'cache.cpp';cpp.write_text(harness);binary=out/'cache-fixture'
    subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(binary)],check=True);subprocess.run([str(binary)],check=True)
    host=subprocess.check_output(['sudo','unshare','--mount','--propagation','private','bash',str(ROOT/'tests/fixtures/g1_cache_readonly.sh')],text=True,timeout=90)
    if 'HOST_READONLY_CACHE_FIXTURE_PASSED' not in host:raise ValueError('Host readonly test failed')
    g1=json.loads((ROOT/'docs/G1-PUBLIC-CONFIG-RESULT.json').read_text());config=image.read('/system/etc/ld.config.txt').read_text()
    apex={};manifests=[]
    listing=image.command('ls -p /system/apex')
    for name in re.findall(r'^/\d+/\d+/\d+/\d+/([^/]+)/',listing,re.M):
        if name in ('.','..'):continue
        p='/system/apex/'+name;node=image.stat(p)
        if node['type']!='directory':raise ValueError('Non-flattened or unexpected APEX '+p)
        manifest=image.read(p+'/apex_manifest.json',required=False)
        if manifest is None:raise ValueError('No JSON APEX manifest: '+p)
        data=json.loads(manifest.read_text());logical=data['name']
        if logical in apex:raise ValueError('Duplicate APEX manifest name')
        apex[logical]=name;manifests.append({'directory':name,'name':logical,'version':data.get('version'),'sha256':sha(manifest.read_bytes())})
    if apex.get('com.android.runtime')!='com.android.runtime.release':raise ValueError('Runtime APEX mapping changed')
    props={**g1.get('build_properties',{}),**g1.get('vendor_build_properties',{})}
    for name in ('/default.prop','/system/etc/prop.default','/system/build.prop','/system/vendor/build.prop'):
        p=image.read(name,False)
        if p:
            for line in p.read_text().splitlines():
                if '=' in line and not line.startswith('#'):k,v=line.split('=',1);props[k]=v
    selected_props={k:v for k,v in props.items() if k in ('ro.apex.updatable','ro.adb.secure','persist.sys.usb.config','ro.product.first_api_level')}
    apex_property_limit = selected_props.get('ro.apex.updatable') not in ('false','0')
    roots=['/system/bin/init','/system/bin/apexd','/system/bin/adbd','/system/bin/bootstrap/linker','/system/bin/bootstrap/linker64','/apex/com.android.runtime/bin/linker','/apex/com.android.runtime/bin/linker64']
    roots += ['/system/'+lib+'/bootstrap/'+name for lib in ('lib','lib64') for name in ('libc.so','libdl.so','libm.so')]
    matrix=[];seen=set();queue=list(roots);blockers=[]
    if apex_property_limit:blockers.append({'property':'ro.apex.updatable','observed':selected_props.get('ro.apex.updatable'),'reason':'Absent/non-false property; source default and effective runtime need validation'})
    while queue:
        guest=queue.pop(0)
        if guest in seen:continue
        seen.add(guest)
        if len(seen)>160:raise ValueError('Bootstrap closure budget exceeded')
        actual,chain=image.canonical(guest,apex);file=image.read(actual,False)
        if file is None:
            blockers.append({'path':guest,'reason':'missing ELF input'});continue
        elf=Elf(file);dynamic=elf.dynamic();ph=subprocess.check_output(['readelf','-W','-l',str(file)],text=True)
        m=re.search(r'Requesting program interpreter:\s*([^\]]+)\]',ph);interpreter=m[1] if m else None
        if interpreter and interpreter not in seen:queue.append(interpreter)
        paths=[]
        for value in (dynamic.get('runpath'),dynamic.get('rpath')):
            if value:paths+=value.replace('$ORIGIN',posixpath.dirname(guest)).replace('${ORIGIN}',posixpath.dirname(guest)).split(':')
        if '/bootstrap/' in guest:paths+=[posixpath.dirname(guest),'/system/'+('lib64' if elf.bits==64 else 'lib')+'/bootstrap']
        if guest.startswith('/apex/com.android.runtime/'):
            paths+=['/apex/com.android.runtime/'+('lib64' if elf.bits==64 else 'lib')]
        paths+=default_paths(config,elf.bits)
        providers=[]
        for needed in dynamic['needed']:
            candidates=[]
            for directory in dict.fromkeys(paths):
                target,links=image.canonical(directory+'/'+needed,apex);provider=image.read(target,False)
                if provider is not None:
                    parsed=Elf(provider)
                    if parsed.bits==elf.bits and parsed.machine==elf.machine:candidates.append({'guest':directory+'/'+needed,'physical':target,'sha256':sha(provider.read_bytes()),'symlinks':links})
            row={'needed':needed,'candidates':candidates}
            if not candidates:blockers.append({'consumer':guest,'needed':needed,'reason':'no provider in modeled search paths; linked namespace/dlopen not fully modeled'})
            else:queue.append(candidates[0]['guest'])
            providers.append(row)
        versions=subprocess.check_output(['readelf','-W','-V',str(file)],text=True)
        matrix.append({'guest':guest,'physical':actual,'symlinks':chain,'sha256':sha(file.read_bytes()),'bits':elf.bits,'machine':elf.machine,'interpreter':interpreter,**dynamic,'version_info':versions,'search_paths':list(dict.fromkeys(paths)),'dependencies':providers,'resolution_scope':'Candidate paths only; ELF symbol versions and linked namespace runtime acceptance not proven'})
    policy=image.read('/sepolicy');shutil.copyfile(policy,evidence/'g0-sepolicy')
    polcaps=subprocess.check_output(['seinfo',str(policy),'--polcap'],text=True,stderr=subprocess.STDOUT)
    classes=subprocess.check_output(['seinfo',str(policy),'--class','-x'],text=True,stderr=subprocess.STDOUT)
    (evidence/'policy-capabilities.txt').write_text(polcaps);(evidence/'policy-classes.txt').write_text(classes)
    (evidence/'ld.config.txt').write_text(config)
    report={'status':'PUBLIC_G1_BOOTSTRAP_CONTRACTS_CAPTURED','source_run':40696459171,'probe_run':int(os.environ['GITHUB_RUN_ID']),'source_commit':os.environ['GITHUB_SHA'],'g0_assets':assets,'cache':{'actual_g0_type':'symlink','actual_g0_target':link,'candidate_type':'directory','staging_source_sha256':sha(mk.encode()),'mount_source_sha256':sha(fs.encode()),'source_function_fixture':'passed with syscall stubs','host_readonly_fixture':host.strip(),'candidate_board_flag':'BOARD_CACHEIMAGE_FILE_SYSTEM_TYPE := ext4','candidate_not_rebuilt':True,'build_contract':build_contract},'usb_fixture':usb,'properties':selected_props,'apex':manifests,'bootstrap_elf':matrix,'unresolved_contracts':blockers,'policy_sha256':sha(policy.read_bytes()),'tests':tests,'hardware_boot_verified':False,'runtime_mounts_verified':False,'limitations':['Immutable G0 retains previous fstab/cache staging','Host readonly ext4 is Linux runner, not Huawei','ELF candidate paths do not certify loader namespace, symbol-version acceptance or runtime','No target APEX activation, policy enforcement or USB proof']}
    (evidence/'g1-bootstrap.json').write_text(json.dumps(report,indent=2)+'\n');publish(evidence,'carrera-g1-bootstrap-'+os.environ['GITHUB_RUN_ID'],'Carrera G1 root/cache and bootstrap contracts')
    print(json.dumps({'status':report['status'],'cache':report['cache'],'apex':manifests,'elf_count':len(matrix),'unresolved_count':len(blockers)},indent=2))
if __name__=='__main__':main()
