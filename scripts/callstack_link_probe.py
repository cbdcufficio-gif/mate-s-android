#!/usr/bin/env python3
"""Link original Q CallStack against an authentic Q VNDK backtrace provider."""
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request
from elf_audit import Elf
from shared_link_probe import BASE, run

BACKTRACE = {
    "arm": ("arm/arch-arm-armv7-a-neon/shared/vndk-sp/libbacktrace.so",
            "4d5838ca0607f5dbaa69e47cef22d3278933d3bb", 40),
    "arm64": ("arm64/arch-arm64-armv8-a/shared/vndk-sp/libbacktrace.so",
              "233fd23e42982e2421365d84cf04086025cd4671", 183),
}

def main():
    if subprocess.call([sys.executable, "scripts/shared_link_probe.py"]):
        return 1
    root = Path("out/callstack-link")
    root.mkdir()
    core = Path("out/shared-link/core")
    result = run(["git", "-C", core, "sparse-checkout", "add", "libutils", "libbacktrace/include"])
    if result.returncode:
        raise RuntimeError(result.stdout)
    binpath = Path(os.environ["ANDROID_NDK_HOME"]) / "toolchains/llvm/prebuilt/linux-x86_64/bin"
    report = {"rom_built": False, "hardware_tested": False,
              "runtime_unwinding_tested": False, "transitive_provider_closure_verified": False,
              "platform_module_built": False, "architectures": []}
    try:
        for arch, (relative, expected, machine) in BACKTRACE.items():
            dest = root / arch
            dest.mkdir()
            url = BASE + relative + "?format=TEXT"
            with urllib.request.urlopen(url, timeout=45) as response:
                encoded = response.read(8 * 1024**2 + 1)
            if len(encoded) > 8 * 1024**2:
                raise ValueError("Provider budget exceeded")
            data = base64.b64decode(encoded, validate=True)
            blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
            if blob != expected:
                raise ValueError("Backtrace Git blob mismatch")
            provider = dest / "libbacktrace.so"
            provider.write_bytes(data)
            elf = Elf(provider)
            if elf.machine != machine:
                raise ValueError("Wrong backtrace architecture")
            triple = "armv7a-linux-androideabi" if arch == "arm" else "aarch64-linux-android"
            compiler = binpath / (triple + "29-clang++")
            flags = ["-fPIC", "-std=c++17", "-nostdinc++", "-fno-exceptions", "-fno-rtti",
                     "-Iout/platform-cxx/include"]
            for inc in ("libutils/include", "liblog/include", "libbacktrace/include"):
                flags.append("-I" + str(core / inc))
            entry = {"arch": arch, "provider_url": url, "provider_git_blob": blob,
                     "provider_sha256": hashlib.sha256(data).hexdigest(),
                     "provider_bytes": len(data), "compiles": []}
            objects = []
            for source in ("CallStack.cpp", "Printer.cpp"):
                obj = dest / (source + ".o")
                compile_result = run([compiler, *flags, "-c", core / "libutils" / source, "-o", obj])
                entry["compiles"].append({"source": source, "returncode": compile_result.returncode,
                                          "diagnostic": compile_result.stdout})
                if compile_result.returncode == 0:
                    objects.append(obj)
            if len(objects) != 2:
                entry["returncode"] = 1
                report["architectures"].append(entry)
                continue
            output = dest / "libmates_callstack_probe.so"
            deps = Path("out/shared-link") / arch
            command = [compiler, "-shared", "-nostdlib++", "-Wl,-z,defs",
                       "-Wl,-soname,libmates_callstack_probe.so", *objects,
                       provider, deps / "libmates_graphics_probe.so", deps / "liblog.so",
                       deps / "libc++.so", "-o", output]
            link = run(command)
            entry.update({"returncode": link.returncode, "link_diagnostic": link.stdout,
                          "command": list(map(str, command))})
            if link.returncode == 0:
                entry["output_sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
                entry["dynamic_metadata"] = run([binpath / "llvm-readelf", "-d", "--version-info", output]).stdout
                entry["exported_symbols"] = run([binpath / "llvm-nm", "-D", "--defined-only", output]).stdout
                entry["provider_dynamic_metadata"] = run([binpath / "llvm-readelf", "-d", "--version-info", provider]).stdout
            report["architectures"].append(entry)
        report["status"] = ("CALLSTACK_LINK_PASSED" if len(report["architectures"]) == 2 and
            all(x["returncode"] == 0 for x in report["architectures"]) else "CALLSTACK_LINK_FAILED")
    except Exception as error:
        report["status"] = "EXPERIMENT_FAILED"
        report["error"] = str(error)
    (root / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)
    return int(report["status"] != "CALLSTACK_LINK_PASSED")

if __name__ == "__main__":
    raise SystemExit(main())
