#!/usr/bin/env python3
"""Execute five real patched Q adapter bodies with a host-only behavioral facade.

This tests callback dispatch and state changes, never Android/Huawei ABI or IO.
"""
from pathlib import Path
import argparse, hashlib, json, os, subprocess

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source',type=Path,required=True)
parser.add_argument('--out',type=Path,required=True)
parser.add_argument('--compiler',default='c++')
args=parser.parse_args()
lock,=json.loads((Path(__file__).resolve().parents[1]/'configs/android-patches.json').read_text())
source=args.source.read_text()
if hashlib.sha256(args.source.read_bytes()).hexdigest()!=lock['after_sha256']:
 raise SystemExit('Callback tests require the exact patched upstream source')
root=args.out
root.mkdir(parents=True,exist_ok=False)
def method(signature):
 start=source.index(signature);brace=source.index('{',start);depth=1;end=brace+1
 while depth:
  if source[end]=='{':depth+=1
  elif source[end]=='}':depth-=1
  end+=1
 return source[start:end]
preamble=r'''
#include <cassert>
#include <cstdint>
#include <memory>
#include <mutex>
#include <vector>
#include <set>
#define ALOGE(...) ((void)0)
#define ALOGV(...) ((void)0)
#define ALOGV_IF(...) ((void)0)
using hwc2_config_t=uint32_t;
using android_color_mode_t=int;
constexpr int HAL_COLOR_MODE_NATIVE=0,HWC_ERROR=-1;
constexpr int HWC_FRAMEBUFFER=0,HWC_SKIP_LAYER=1,HWC_IS_CURSOR_LAYER=2,HWC_SIDEBAND=3;
enum class Error {None,BadConfig,Unsupported,BadLayer,NotValidated};
enum class Composition {Client,Device,SolidColor,Cursor,Sideband};
struct hwc_layer_1_t {int compositionType=99,flags=0,hints=0;};
struct Hardware {
 int (*getActiveConfig)(Hardware*,int)=nullptr;
 int (*setActiveConfig)(Hardware*,int,int)=nullptr;
 int (*setCursorPositionAsync)(Hardware*,int,int,int)=nullptr;
};
struct HWC2On1Adapter {
 Hardware *mHwc1Device;
 int mHwc1MinorVersion=4;
 int getHwc1MinorVersion(){return mHwc1MinorVersion;}
 Hardware* getHwc1Device(){return mHwc1Device;}
 struct Display {
  struct Config {
   uint32_t id;
   Error getHwc1IdForColorMode(int,uint32_t* value)const{*value=id;return Error::None;}
   bool hasHwc1Id(int value)const{return value==static_cast<int>(id);}
   int getId()const{return id;}
   Error getColorModeForHwc1Id(int,int* value)const{*value=HAL_COLOR_MODE_NATIVE;return Error::None;}
  };
  HWC2On1Adapter &mDevice;
  std::recursive_mutex mStateMutex;
  std::vector<std::shared_ptr<const Config>> mConfigs;
  std::shared_ptr<const Config> mActiveConfig;
  int mActiveColorMode=0,mHwc1Id=0,mId=1;
  bool changes=false;
  std::set<int> mColorModes{0,1};
  auto getConfig(uint32_t id)const{return id<mConfigs.size()?mConfigs[id]:nullptr;}
  HWC2On1Adapter& getDevice(){return mDevice;}
  int getHwc1Id(){return mHwc1Id;}
  bool hasChanges(){return changes;}
  bool hasColorTransform(){return false;}
  Error setActiveConfig(hwc2_config_t);
  Error setColorMode(android_color_mode_t);
  void initializeActiveConfig();
 };
 struct Layer {
  Display &mDisplay;
  Composition mCompositionType=Composition::Cursor;
  bool mHasUnsupportedPlaneAlpha=false;
  bool hasUnsupportedBackgroundColor(){return false;}
  Error setCursorPosition(int32_t,int32_t);
  void applyCompositionType(hwc_layer_1_t&);
 };
};
'''
methods=[method(s) for s in ['Error HWC2On1Adapter::Display::setActiveConfig(', 'Error HWC2On1Adapter::Display::setColorMode(', 'void HWC2On1Adapter::Display::initializeActiveConfig(', 'Error HWC2On1Adapter::Layer::setCursorPosition(', 'void HWC2On1Adapter::Layer::applyCompositionType(']]
tests=r'''
int calls=0,result=0,last=-1;
int setter(Hardware*,int,int config){++calls;last=config;return result;}
int getter(Hardware*,int){return HWC_ERROR;}
int cursor(Hardware*,int,int x,int y){++calls;last=x+y;return 0;}
int main(){
 Hardware hw;
 HWC2On1Adapter device{&hw};
 HWC2On1Adapter::Display d{device};
 d.mConfigs={std::make_shared<HWC2On1Adapter::Display::Config>(HWC2On1Adapter::Display::Config{0}),std::make_shared<HWC2On1Adapter::Display::Config>(HWC2On1Adapter::Display::Config{1})};
 d.initializeActiveConfig();assert(d.mActiveConfig==d.mConfigs[0]);
 assert(d.setActiveConfig(0)==Error::None);
 assert(d.setActiveConfig(1)==Error::BadConfig);
 assert(d.setActiveConfig(99)==Error::BadConfig);
 assert(d.mActiveConfig==d.mConfigs[0]&&calls==0);
 assert(d.setColorMode(0)==Error::None);
 assert(d.setColorMode(1)==Error::Unsupported&&d.mActiveColorMode==0);
 hw.setActiveConfig=setter;result=-1;
 assert(d.setActiveConfig(1)==Error::BadConfig&&d.mActiveConfig==d.mConfigs[0]);
 assert(d.setColorMode(1)==Error::Unsupported&&d.mActiveColorMode==0);
 result=0;assert(d.setActiveConfig(1)==Error::None&&d.mActiveConfig==d.mConfigs[1]&&last==1);
 assert(d.setColorMode(1)==Error::None&&d.mActiveColorMode==1);
 d.mActiveConfig.reset();hw.getActiveConfig=getter;hw.setActiveConfig=nullptr;
 d.initializeActiveConfig();assert(!d.mActiveConfig);
 hw.setActiveConfig=setter;result=-1;d.initializeActiveConfig();assert(!d.mActiveConfig);
 result=0;d.initializeActiveConfig();assert(d.mActiveConfig==d.mConfigs[0]);
 HWC2On1Adapter::Layer layer{d};
 int oldCalls=calls;
 assert(layer.setCursorPosition(1,2)==Error::BadLayer&&calls==oldCalls);
 hwc_layer_1_t state;layer.applyCompositionType(state);
 assert(state.compositionType==HWC_FRAMEBUFFER&&(state.flags&HWC_SKIP_LAYER)&&!(state.hints&HWC_IS_CURSOR_LAYER));
 hw.setCursorPositionAsync=cursor;state={};layer.applyCompositionType(state);
 assert((state.hints&HWC_IS_CURSOR_LAYER)&&!(state.flags&HWC_SKIP_LAYER));
 assert(layer.setCursorPosition(1,2)==Error::None&&calls==oldCalls+1&&last==3);
 d.changes=true;assert(layer.setCursorPosition(1,2)==Error::NotValidated);
 d.changes=false;layer.mCompositionType=Composition::Client;
 assert(layer.setCursorPosition(1,2)==Error::BadLayer);
}
'''
cpp=root/'callback_contract.cpp';cpp.write_text(preamble+'\n'.join(methods)+tests)
subprocess.run([args.compiler,'-std=c++17','-Wall','-Wextra','-Wno-missing-field-initializers','-fsanitize=address,undefined','-fno-sanitize-recover=all',str(cpp),'-o',str(root/'callback_contract')],check=True)
subprocess.run([str((root/'callback_contract').resolve())],check=True,env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0'})
report={'status':'CALLBACK_BEHAVIOR_PASSED','function_bodies':5,'source_sha256':lock['after_sha256'],'address_and_undefined_sanitizers':True,'hardware_tested':False,'vendor_abi_tested':False}
(root/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
