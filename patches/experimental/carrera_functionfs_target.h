#pragma once
#include <cerrno>
#include <fcntl.h>
#include <sys/vfs.h>
#include <unistd.h>

// parent_fd must already identify the verified /dev/usb-ffs directory.
// Returns an owned descriptor, or -1. Does not certify mount source, labels,
// endpoint readiness, or the pathname subsequently opened by adbd.
inline int OpenCarreraFunctionfsTarget(int parent_fd) {
    const int fd = openat(parent_fd, "adb", O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
    if (fd < 0) return -1;
    struct statfs filesystem;
    if (fstatfs(fd, &filesystem) < 0) {
        const int saved = errno;
        close(fd);
        errno = saved;
        return -1;
    }
    // Huawei f_fs.c, pinned kernel 3fe1625: FUNCTIONFS_MAGIC.
    if (filesystem.f_type != 0x0a647361) {
        close(fd);
        errno = ENODEV;
        return -1;
    }
    return fd;
}
