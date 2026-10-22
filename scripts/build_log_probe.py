"""Build original target liblog for a link-only experiment, no fake host logger."""
import hashlib
import io
from pathlib import Path
import tarfile
import urllib.request

SHA = "6d27634866be5b646a8cea1f9abeae902fd831e5"
SOURCES = """config_read config_write log_event_list log_event_write logger_lock
logger_name logger_read logger_write logprint stderr_write event_tag_map log_time
properties pmsg_reader pmsg_writer logd_reader logd_writer""".split()

def fetch_core(root):
    url = "https://codeload.github.com/LineageOS/android_system_core/tar.gz/" + SHA
    with urllib.request.urlopen(url, timeout=45) as stream:
        data = stream.read(32 * 1024**2 + 1)
    if len(data) > 32 * 1024**2:
        raise ValueError("Core archive budget exceeded")
    total = count = 0
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        for member in archive:
            relative = Path(*Path(member.name).parts[1:])
            if not member.isfile() or not any(str(relative).startswith(p) for p in
                    ("liblog/", "libcutils/include/", "libsystem/include/", "base/include/")):
                continue
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("Unsafe archive path")
            total += member.size
            count += 1
            if total > 8 * 1024**2 or count > 1000:
                raise ValueError("Core extraction budget exceeded")
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.extractfile(member).read())
    return {"url": url, "commit": SHA, "bytes": total,
            "archive_sha256": hashlib.sha256(data).hexdigest()}

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
