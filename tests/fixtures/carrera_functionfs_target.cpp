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
    close(parent);
}
