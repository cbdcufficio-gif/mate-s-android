#!/usr/bin/env python3
"""Test real touchscreen framework callback bodies with update flag on/off.

Host-only control flow test. No device access, kernel ABI or firmware execution.
"""
import argparse,hashlib,json,subprocess,os
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--source',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
p.add_argument('--compiler',default='cc')
a=p.parse_args()
lock=json.loads((Path(__file__).resolve().parents[1]/'configs/kernel-touch-update.json').read_text())
row=next(r for r in lock['files'] if r['path'].endswith('.c'))
if hashlib.sha256(a.source.read_bytes()).hexdigest()!=row['after_sha256']:
 raise SystemExit('Requires the exact reviewed patched touchscreen source')
source=a.source.read_text()
a.out.mkdir(parents=True,exist_ok=False)
def body(signature):
 start=source.index(signature);i=source.index('{',start)+1;depth=1
 while depth:
  if source[i]=='{':depth+=1
  elif source[i]=='}':depth-=1
  i+=1
 return source[start:i]
functions='\n'.join(body(s)for s in ['static inline int ts_fw_update_boot(', 'static inline int ts_fw_update_sd(', 'static ssize_t ts_fw_update_sd_store('])
preamble=r'''#include <assert.h>
#include <errno.h>
#include <string.h>
#include <sys/types.h>
#define NO_ERR 0
#define TS_FW_UPDATE_SD 1
#define LONG_LONG_SYNC_TIMEOUT 1
#define IS_ENABLED(x) (x)
#define TS_LOG_INFO(...) ((void)0)
#define TS_LOG_ERR(...) ((void)0)
struct device {int unused;};
struct device_attribute {int unused;};
struct ts_cmd_node {int command;struct {struct {struct {char fw_name[128];}firmware_info;}pub_params;}cmd_param;};
struct ops {int (*chip_fw_update_boot)(char*);int (*chip_fw_update_sd)(void);};
struct ts_device_data {struct ops *ops;};
struct {struct ts_device_data *chip_data;}g_ts_data;
static int boot_calls,sd_calls,queued;
static int put_one_cmd(struct ts_cmd_node *cmd,int timeout){++queued;return 0;}
static int boot_update(char *name){++boot_calls;return -7;}
static int sd_update(void){++sd_calls;return -9;}
'''
tests=r'''
int main(void){
 struct ops ops={boot_update,sd_update};
 struct ts_device_data dev={&ops};
 struct ts_cmd_node cmd={0},out={0};
 g_ts_data.chip_data=&dev;
 assert(ts_fw_update_boot(&cmd,&out)==(CONFIG_HUAWEI_TS_FW_UPDATE?-7:-EOPNOTSUPP));
 assert(ts_fw_update_sd(&cmd,&out)==(CONFIG_HUAWEI_TS_FW_UPDATE?-9:-EOPNOTSUPP));
 assert(ts_fw_update_sd_store(0,0,"1",1)==(CONFIG_HUAWEI_TS_FW_UPDATE?1:-EOPNOTSUPP));
 assert(boot_calls==CONFIG_HUAWEI_TS_FW_UPDATE);
 assert(sd_calls==CONFIG_HUAWEI_TS_FW_UPDATE);
 assert(queued==CONFIG_HUAWEI_TS_FW_UPDATE);
 return 0;
}
'''
c=a.out/'callbacks.c';c.write_text(preamble+functions+tests)
for enabled in (0,1):
 binary=a.out/('callbacks-'+str(enabled))
 subprocess.run([a.compiler,'-std=gnu89','-Wall','-Wextra','-Wno-unused-parameter',
  '-fsanitize=address,undefined','-fno-sanitize-recover=all',
  '-DCONFIG_HUAWEI_TS_FW_UPDATE='+str(enabled),str(c),'-o',str(binary)],check=True)
 subprocess.run([str(binary.resolve())],check=True,env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0'})
print(json.dumps({'status':'TOUCHSCREEN_FW_GUARD_BEHAVIOR_PASSED','real_function_bodies':3,
 'flag_values_tested':[0,1],'disabled_callbacks_and_queue_calls':0,
 'source_sha256':row['after_sha256'],'hardware_tested':False}))
