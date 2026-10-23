/* Native ARM64 read-only kernel diagnostics. No libc or persistent writes.
 * Syscall numbers: Linux asm-generic unistd; ioctl ABI: Linux binder.h/fb.h.
 * This is a kernel interface probe, not an Android Q HAL or ROM test.
 */
typedef unsigned long ulong;
static long call(long nr, long a, long b, long c, long d) {
    register long x8 __asm__("x8") = nr;
    register long x0 __asm__("x0") = a;
    register long x1 __asm__("x1") = b;
    register long x2 __asm__("x2") = c;
    register long x3 __asm__("x3") = d;
    __asm__ volatile("svc #0" : "+r"(x0) : "r"(x8), "r"(x1), "r"(x2), "r"(x3) : "memory", "cc");
    return x0;
}
void *memset(void *p, int value, ulong size) {
    volatile unsigned char *out = p;
    for (ulong i = 0; i < size; ++i) out[i] = (unsigned char)value;
    return p;
}
static void text(const char *s) {
    ulong len = 0;
    while (s[len]) ++len;
    while (len) {
        long n = call(64, 1, (long)s, len, 0);
        if (n <= 0) return;
        s += n; len -= n;
    }
}
static void number(const char *key, long value) {
    char buf[32]; ulong i = sizeof(buf) - 1;
    buf[i] = 0;
    int negative = value < 0;
    ulong n = negative ? 0UL - (ulong)value : (ulong)value;
    do { buf[--i] = '0' + n % 10; n /= 10; } while (n);
    if (negative) buf[--i] = '-';
    text(key); text("="); text(buf + i); text("\n");
}
static long open_readonly(const char *path) {
    return call(56, -100, (long)path, 0x80000, 0); /* O_RDONLY | O_CLOEXEC */
}
static void binder(const char *path) {
    long fd = open_readonly(path);
    number(path, fd);
    if (fd < 0) return;
    int version = -1;
    long result = call(29, fd, 0xc0046209UL, (long)&version, 0);
    number("binder_version_ioctl", result);
    if (!result) number("binder_protocol", version);
    call(57, fd, 0, 0, 0);
}
static void run(void) {
    char uts[6][65];
    long result = call(160, (long)uts, 0, 0, 0);
    number("uname", result);
    if (!result) {
        text("release="); text(uts[2]); text("\nmachine="); text(uts[4]); text("\n");
    }
    binder("/dev/binder"); binder("/dev/hwbinder"); binder("/dev/vndbinder");
    long fd = open_readonly("/dev/graphics/fb0");
    number("framebuffer_open", fd);
    if (fd >= 0) {
        unsigned int values[64]; /* Larger than the 160-byte fb_var_screeninfo. */
        result = call(29, fd, 0x4600, (long)values, 0);
        number("framebuffer_get_var", result);
        if (!result) {
            number("xres", values[0]); number("yres", values[1]); number("bpp", values[6]);
        }
        call(57, fd, 0, 0, 0);
    }
    const char *paths[] = {"/dev/ion", "/dev/mali0"};
    for (ulong i = 0; i < 2; ++i) {
        fd = open_readonly(paths[i]); number(paths[i], fd);
        if (fd >= 0) call(57, fd, 0, 0, 0);
    }
    unsigned char random_byte;
    number("getrandom_nonblock", call(278, (long)&random_byte, 1, 1, 0));
    fd = call(279, (long)"mates_probe", 1, 0, 0);
    number("memfd_create", fd);
    if (fd >= 0) call(57, fd, 0, 0, 0);
}
__attribute__((noreturn)) void _start(void) {
    run();
    call(93, 0, 0, 0, 0);
    __builtin_unreachable();
}
