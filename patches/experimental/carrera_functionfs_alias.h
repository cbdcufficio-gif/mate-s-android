#pragma once
#include <cerrno>
#include <fcntl.h>
#include <sys/vfs.h>
#include <unistd.h>

// Caller must supply the verified f_ffs sysfs directory descriptor. This does
// not certify its device identity or prevent another privileged alias writer.
// Never call from an untrusted init subcontext. No retries on write failure.
inline bool WriteAndVerifyCarreraFunctionfsAlias(int ffs_directory) {
    const int fd = openat(ffs_directory, "aliases", O_RDWR | O_NOFOLLOW | O_CLOEXEC);
    if (fd < 0) return false;
    bool ok = false;
    int error = 0;
    struct statfs filesystem;
    if (fstatfs(fd, &filesystem) < 0) {
        error = errno;
    } else if (filesystem.f_type != 0x62656572) { // SYSFS_MAGIC
        error = ENODEV;
    } else {
        const ssize_t written = write(fd, "adb", 3);
        if (written != 3) {
            error = written < 0 ? errno : EIO;
        } else if (lseek(fd, 0, SEEK_SET) < 0) {
            error = errno;
        } else {
            char value[5];
            const ssize_t count = read(fd, value, sizeof(value));
            // Pinned Huawei ffs_aliases_show emits the value plus one newline.
            ok = count == 4 && value[0] == 'a' && value[1] == 'd' &&
                 value[2] == 'b' && value[3] == '\n';
            if (!ok) error = count < 0 ? errno : EIO;
        }
    }
    close(fd);
    if (!ok) errno = error;
    return ok;
}
