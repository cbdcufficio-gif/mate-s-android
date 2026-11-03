# Huawei FunctionFS mount options

Source: hi3635-dev/android_kernel_huawei_liszt, commit
3fe1625bed89c034996842c1af696ba9bc50d8a9, drivers/usb/gadget/f_fs.c.
Full source SHA256: 220024748f2f28e4f63f2e1ad8f26b71a269047b639fdbbe8a2d3d740350b788.
The CI USB source check compares this digest and the unchanged extracted
ffs_fs_parse_opts body against the host fixture.

The host fixture checks uid/gid 2000 in both orders, invalid numeric input,
missing equals, unknown options, trailing comma and unmapped synthetic IDs.
Mapping and kstrtoul are host stubs: this does not exercise kernel namespace
mapping, mount, SELinux or USB hardware.

patches/experimental/init.carrera-functionfs.rc is not imported by the
product. It prepares directories, mount and alias only. Effective policy,
init scheduling, mount failure handling, readiness race and authenticated
ADB remain open. No personal key or insecure ADB setting is included.

The unchanged Q ActionManager::ExecuteOneCommand fixture dispatches the next
command after a simulated first-command failure. Command execution is stubbed;
the production Action::ExecuteCommand returns void and logs errors. Thus a
sequence of mount followed by alias write does not itself gate later commands
on successful mount. No successful mount signal is inferred from this rc.
