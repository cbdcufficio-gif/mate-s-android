// Include inside android::init in builtins.cpp, after do_start. Experimental;
// not registered or installed. Requires the native Carrera headers first.
// This validates an existing mount, not the outcome of an earlier mount call.
static Result<Success> do_carrera_checked_adbd(const BuiltinArguments& args) {
    if (args.context != kInitContext) {
        return Error() << "Carrera USB preparation requires init caller context";
    }
    if (args.size() != 1) return Error() << "Carrera USB preparation takes no arguments";
    if (android::base::GetProperty("sys.usb.config", "") != "adb" ||
        android::base::GetProperty("sys.usb.configfs", "") != "0") {
        return Error() << "Carrera USB preparation requires legacy adb-only mode";
    }
    android::base::unique_fd dev(open("/dev", O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC));
    if (dev < 0) return ErrnoError() << "open /dev failed";
    android::base::unique_fd target(OpenCarreraFunctionfsWithIdentity(dev.get()));
    if (target < 0) return ErrnoError() << "FunctionFS mount identity rejected";

    android::base::unique_fd sys(open("/sys", O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC));
    if (sys < 0) return ErrnoError() << "open /sys failed";
    struct statfs filesystem;
    if (fstatfs(sys.get(), &filesystem) < 0) return ErrnoError() << "stat sysfs failed";
    if (filesystem.f_type != 0x62656572) return Error() << "unexpected /sys filesystem";
    // Pinned Huawei creates android0 in android_usb class and f_ffs beneath it.
    // Canonical path must be confirmed on the candidate before installation.
    for (const char* component : {"devices", "virtual", "android_usb", "android0", "f_ffs"}) {
        const int next = openat(sys.get(), component,
                                O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
        if (next < 0) return ErrnoError() << "open canonical f_ffs path failed";
        sys.reset(next);
    }
    if (!WriteAndVerifyCarreraFunctionfsAlias(sys.get())) {
        return ErrnoError() << "FunctionFS alias write/readback failed";
    }
    // Reobserve the live pathname after alias I/O while retaining the first fd.
    // Same device/inode is a snapshot check, not a mount-instance/lifetime proof.
    android::base::unique_fd current(OpenCarreraFunctionfsWithIdentity(dev.get()));
    if (current < 0) return ErrnoError() << "FunctionFS recheck failed";
    struct stat before, after;
    if (fstat(target.get(), &before) < 0 || fstat(current.get(), &after) < 0)
        return ErrnoError() << "stat FunctionFS directories failed";
    if (before.st_dev != after.st_dev || before.st_ino != after.st_ino)
        return Error() << "FunctionFS pathname changed during preparation";
    // All held descriptors survive through this request. adbd opens its own
    // pathname later; lifecycle and competing activation paths remain open.
    return do_start(BuiltinArguments({"start", "adbd"}, args.context));
}
