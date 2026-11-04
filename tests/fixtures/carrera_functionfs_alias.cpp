#include <cassert>
#include <string>
#include <sys/resource.h>
#include <sys/stat.h>
#include "carrera_functionfs_alias.h"

int main(int argc, char** argv) {
    assert(argc == 2);
    const int parent = open(argv[1], O_RDONLY | O_DIRECTORY | O_CLOEXEC);
    assert(parent >= 0);
    assert(!WriteAndVerifyCarreraFunctionfsAlias(parent));
    assert(symlinkat("value", parent, "aliases") == 0);
    const int value = openat(parent, "value", O_RDWR | O_CREAT | O_EXCL | O_CLOEXEC, 0600);
    assert(value >= 0);
    assert(write(value, "original", 8) == 8);
    assert(!WriteAndVerifyCarreraFunctionfsAlias(parent));
    assert(errno == ELOOP);
    assert(unlinkat(parent, "aliases", 0) == 0);
    assert(linkat(parent, "value", parent, "aliases", 0) == 0);
    struct rlimit limit = {64, 64};
    assert(setrlimit(RLIMIT_NOFILE, &limit) == 0);
    for (int i = 0; i < 1000; ++i) {
        assert(!WriteAndVerifyCarreraFunctionfsAlias(parent));
        assert(errno == ENODEV); // host fs rejected before any write
    }
    char content[9] = {};
    assert(pread(value, content, 8, 0) == 8);
    assert(std::string(content) == "original");
    assert(!WriteAndVerifyCarreraFunctionfsAlias(-1));
    close(value);
    close(parent);
}
