#include <cassert>
#include <fcntl.h>
#include <unistd.h>
#include "carrera_mount_identity.h"

int main() {
    const int fd = open("/", O_RDONLY | O_DIRECTORY | O_CLOEXEC);
    assert(fd >= 0);
    // The restricted host may have stacked /proc mounts. Use the actual root
    // record for positive host evidence; duplicate mountpoints are rejected.
    std::ifstream records("/proc/self/mountinfo");
    std::string line, type, source;
    unsigned roots = 0;
    while (std::getline(records, line)) {
        std::istringstream fields(line);
        std::string id, parent, device, root, target, options, field;
        assert(fields >> id >> parent >> device >> root >> target >> options);
        if (target != "/") continue;
        assert(root == "/");
        ++roots;
        while (fields >> field) { if (field == "-") break; }
        assert(fields >> type >> source);
    }
    assert(roots == 1);
    std::ifstream actual("/proc/self/mountinfo");
    assert(CarreraMountIdentityInTable(fd, "/", type, source, actual));
    std::ifstream wrong_source("/proc/self/mountinfo");
    assert(!CarreraMountIdentityInTable(fd, "/", type, source + "-wrong", wrong_source));
    std::ifstream wrong_type("/proc/self/mountinfo");
    assert(!CarreraMountIdentityInTable(fd, "/", type + "-wrong", source, wrong_type));
    assert(!CarreraFunctionfsMountIdentity(fd));
    struct stat metadata;
    assert(fstat(fd, &metadata) == 0);
    const std::string device = std::to_string(major(metadata.st_dev)) + ":" +
                               std::to_string(minor(metadata.st_dev));
    const std::string entry = "10 1 " + device + " / /dev/usb-ffs/adb rw shared:2 - functionfs adb rw\n";
    std::istringstream synthetic(entry);
    assert(CarreraMountIdentityInTable(fd, "/dev/usb-ffs/adb", "functionfs", "adb", synthetic));
    // Above is synthetic metadata parsing, not an actual FunctionFS mount.
    for (const std::string& text : {entry + entry, entry.substr(0, entry.size() - 1),
         std::string("broken\n"),
         std::string("10 1 999:999 / /dev/usb-ffs/adb rw - functionfs adb rw\n"),
         std::string("10 1 ") + device + " /subdir /dev/usb-ffs/adb rw - functionfs adb rw\n",
         std::string(65537, 'x')}) {
        std::istringstream invalid(text);
        assert(!CarreraMountIdentityInTable(fd, "/dev/usb-ffs/adb", "functionfs", "adb", invalid));
    }
    std::istringstream empty;
    assert(!CarreraMountIdentityInTable(-1, "/proc", "proc", "proc", empty));
    close(fd);
}
