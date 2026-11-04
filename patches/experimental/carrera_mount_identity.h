#pragma once
#include <fstream>
#include <sstream>
#include <string>
#include <sys/stat.h>
#include <sys/sysmacros.h>

// Snapshot check only: matching st_dev does not identify a mount instance.
// A held descriptor can outlive a detached mount. Callers still need a mount
// lifecycle/namespace contract before passing a pathname to another process.
inline bool CarreraMountIdentityInTable(int fd, const std::string& target,
                                       const std::string& type,
                                       const std::string& source,
                                       std::istream& table) {
    struct stat metadata;
    if (fstat(fd, &metadata) < 0 || !S_ISDIR(metadata.st_mode)) return false;
    const std::string device = std::to_string(major(metadata.st_dev)) + ":" +
                               std::to_string(minor(metadata.st_dev));
    unsigned matches = 0;
    std::size_t bytes = 0;
    std::string line;
    while (std::getline(table, line)) {
        if (table.eof()) return false; // incomplete final kernel record
        // Bound parsing work; unexpectedly large tables fail closed.
        bytes += line.size() + 1;
        if (bytes > 1024 * 1024 || line.size() > 65536) return false;
        std::istringstream fields(line);
        std::string id, parent, entry_device, root, mountpoint, options;
        if (!(fields >> id >> parent >> entry_device >> root >> mountpoint >> options))
            return false;
        std::string field;
        bool separator = false;
        while (fields >> field) {
            if (field == "-") { separator = true; break; }
        }
        std::string entry_type, entry_source, super_options, trailing;
        if (!separator || !(fields >> entry_type >> entry_source >> super_options) ||
            (fields >> trailing)) return false;
        if (mountpoint != target) continue;
        // Reject stacked/ambiguous entries rather than guessing the visible one.
        if (++matches != 1 || root != "/" || entry_device != device ||
            entry_type != type || entry_source != source) return false;
    }
    return table.eof() && !table.bad() && matches == 1;
}

inline bool CarreraFunctionfsMountIdentity(int fd) {
    std::ifstream table("/proc/self/mountinfo");
    if (!table.is_open()) return false;
    return CarreraMountIdentityInTable(fd, "/dev/usb-ffs/adb", "functionfs", "adb", table);
}
