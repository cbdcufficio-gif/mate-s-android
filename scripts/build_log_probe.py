"""Build original target liblog for a link-only experiment, no fake host logger."""
import hashlib
import io
from pathlib import Path
import tarfile
import urllib.request
import subprocess

SHA = "6d27634866be5b646a8cea1f9abeae902fd831e5"
SOURCES = """config_read config_write log_event_list log_event_write logger_lock
logger_name logger_read logger_write logprint stderr_write event_tag_map log_time
properties pmsg_reader pmsg_writer logd_reader logd_writer""".split()

def fetch_core(root):
    url = "https://github.com/LineageOS/android_system_core.git"
    root.mkdir()
    commands = [
        ["git", "init", str(root)],
        ["git", "-C", str(root), "remote", "add", "origin", url],
        ["git", "-C", str(root), "fetch", "--depth=1", "--filter=blob:none", "origin", SHA],
        ["git", "-C", str(root), "sparse-checkout", "set", "liblog",
         "libcutils/include", "libsystem/include", "base/include"],
        ["git", "-C", str(root), "checkout", "--detach", "FETCH_HEAD"],
    ]
    for command in commands:
        result = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=120)
        if result.returncode:
            raise RuntimeError(result.stdout)
    actual = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"],
                                     text=True).strip()
    if actual != SHA:
        raise ValueError("Pinned source commit mismatch")
    total = sum(p.stat().st_size for p in root.rglob("*")
                if p.is_file() and ".git" not in p.relative_to(root).parts)
    if total > 8 * 1024**2:
        raise ValueError("Sparse source budget exceeded")
    return {"url": url, "commit": SHA, "source_bytes": total,
            "transfer": "shallow blob-filtered sparse checkout"}

def build(root, dest, compiler, provider, run):
    flags = ["-fPIC", "-std=c++17", "-nostdinc++", "-fno-exceptions", "-fno-rtti",
             "-DLIBLOG_LOG_TAG=1006", "-DSNET_EVENT_LOG_TAG=1397638484",
             "-Iout/platform-cxx/include"]
    for inc in ("liblog/include", "liblog", "libcutils/include", "base/include", "libsystem/include"):
        flags.append("-I" + str(root / inc))
    objects = []
    for name in SOURCES:
        obj = dest / (name + ".o")
        result = run([compiler, *flags, "-c", root / "liblog" / (name + ".cpp"), "-o", obj])
        if result.returncode:
            return {"status": "COMPILE_FAILED", "source": name, "diagnostic": result.stdout}
        objects.append(obj)
    output = dest / "liblog.so"
    result = run([compiler, "-shared", "-nostdlib++", "-Wl,-z,defs",
                  "-Wl,-soname,liblog.so", "-Wl,--version-script=" + str(root / "liblog/liblog.map.txt"),
                  *objects, provider, "-o", output])
    return {"status": "LINK_PASSED" if result.returncode == 0 else "LINK_FAILED",
            "objects_compiled": len(objects), "diagnostic": result.stdout,
            "path": str(output), "sha256": hashlib.sha256(output.read_bytes()).hexdigest()
            if result.returncode == 0 else None}
