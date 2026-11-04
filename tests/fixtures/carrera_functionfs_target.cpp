#include <cassert>
#include <sys/resource.h>
#include <sys/stat.h>
#include "carrera_functionfs_target.h"
int main(int argc,char** argv) {
    assert(argc==2);
    int parent=open(argv[1],O_RDONLY|O_DIRECTORY|O_CLOEXEC);
    assert(parent>=0);
    assert(OpenCarreraFunctionfsTarget(parent)<0); // missing target
    assert(symlinkat("/tmp",parent,"adb")==0);
    assert(OpenCarreraFunctionfsTarget(parent)<0); // symlink must not be followed
    assert(unlinkat(parent,"adb",0)==0);
    assert(mkdirat(parent,"adb",0700)==0);
    struct rlimit limit={64,64};
    assert(setrlimit(RLIMIT_NOFILE,&limit)==0);
    for(int i=0;i<1000;++i) {
        assert(OpenCarreraFunctionfsTarget(parent)<0); // actual host fs, no mock
        assert(errno==ENODEV);
    }
    assert(OpenCarreraFunctionfsTarget(-1)<0);
    assert(OpenCarreraFunctionfsFromDev(parent)<0); // missing parent component
    assert(symlinkat(".",parent,"usb-ffs")==0);
    // A followed symlink would reach the existing ordinary adb directory and
    // produce ENODEV. O_NOFOLLOW|O_DIRECTORY must reject it before fstatfs.
    assert(OpenCarreraFunctionfsFromDev(parent)<0);
    assert(errno==ENOTDIR || errno==ELOOP);
    assert(unlinkat(parent,"usb-ffs",0)==0);
    assert(mkdirat(parent,"usb-ffs",0700)==0);
    int usb_parent=openat(parent,"usb-ffs",O_RDONLY|O_DIRECTORY|O_CLOEXEC);
    assert(usb_parent>=0);
    assert(mkdirat(usb_parent,"adb",0700)==0);
    close(usb_parent);
    for(int i=0;i<1000;++i) {
        assert(OpenCarreraFunctionfsFromDev(parent)<0);
        assert(errno==ENODEV); // both real components opened, wrong host fs
    }
    assert(OpenCarreraFunctionfsFromDev(-1)<0);
    close(parent);
}
