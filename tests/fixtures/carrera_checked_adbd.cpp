#include <cassert>
#include <cstring>
#include "q-init-types/result.h"
#include "q-init-types/builtin_arguments.h"
#include "q-init-types/android-base/unique_fd.h"
#include "carrera_functionfs_target.h"
#include "carrera_functionfs_alias.h"

static int properties = 0, opens = 0, starts = 0;
static std::string config = "adb", configfs = "0";
namespace android { namespace base {
std::string GetProperty(const std::string& name, const std::string&) {
    ++properties;
    return name == "sys.usb.config" ? config : configfs;
}
} namespace init {
// Exact constant from pinned init/subcontext.cpp; no SELinux is executed here.
const std::string kInitContext = "u:r:init:s0";
static Result<Success> do_start(const BuiltinArguments& args) {
    ++starts;
    assert(args.args == std::vector<std::string>({"start", "adbd"}));
    return Success();
}
static int RejectedOpen(const char*, int) {
    ++opens;
    errno = EACCES;
    return -1;
}
// Only the glue's /dev open is injected. Native helper bodies above compiled
// unchanged. No real service start, sysfs write or successful mount is tested.
#define open RejectedOpen
#include "carrera_checked_adbd.inc"
#undef open
} }

int main() {
    using namespace android::init;
    for (const std::string& context : {std::string(), std::string("u:r:vendor_init:s0"),
         std::string("u:r:init:s0:extra"), std::string("u:r:init:s0\0suffix", 18)}) {
        auto result = do_carrera_checked_adbd(BuiltinArguments({"carrera_checked_adbd"}, context));
        assert(!result && properties == 0 && opens == 0 && starts == 0);
    }
    auto arguments = do_carrera_checked_adbd(BuiltinArguments({"carrera_checked_adbd", "adbd"}, kInitContext));
    assert(!arguments && properties == 0 && opens == 0 && starts == 0);
    config = "mtp,adb";
    auto mode = do_carrera_checked_adbd(BuiltinArguments({"carrera_checked_adbd"}, kInitContext));
    assert(!mode && opens == 0 && starts == 0);
    config = "adb"; configfs = "1";
    mode = do_carrera_checked_adbd(BuiltinArguments({"carrera_checked_adbd"}, kInitContext));
    assert(!mode && opens == 0 && starts == 0);
    configfs = "0";
    auto failure = do_carrera_checked_adbd(BuiltinArguments({"carrera_checked_adbd"}, kInitContext));
    assert(!failure && failure.error_errno() == EACCES && opens == 1 && starts == 0);
}
