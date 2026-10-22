#!/usr/bin/env python3
"""Compile original Android header layouts, never link or execute target code."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.request

TYPES = ["Region", "CallStack", "VectorImpl", "SharedBuffer", "String8", "Rect", "Point"]
HEADERS = ["ui/Region.h", "utils/CallStack.h", "utils/VectorImpl.h",
           "utils/SharedBuffer.h", "utils/String8.h", "ui/Rect.h", "ui/Point.h"]
ROOTS = {
    "m": [("core", "include"), ("native", "include"), ("core", "libutils"),
          ("native", "libs/ui"),
          ("core", "libbacktrace/include"), ("core", "liblog/include")],
    "q": [("core", "libutils/include"), ("native", "libs/ui/include"),
          ("native", "libs/math/include"), ("native", "libs/arect/include"),
          ("core", "libcutils/include"),
          ("core", "libsystem/include"), ("core", "liblog/include"),
          ("core", "base/include"), ("native", "libs/nativebase/include"),
          ("native", "libs/nativewindow/include"), ("core", "include"),
          ("core", "libutils"), ("native", "libs/ui"), ("core", "libbacktrace/include")],
}

def run(argv):
    return subprocess.run(argv, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, timeout=120)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ndk", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    lock = json.loads(Path("configs/layout-sources.json").read_text())
    binpath = a.ndk / "toolchains/llvm/prebuilt/linux-x86_64/bin"
    report = {"rom_built": False, "hardware_tested": False,
              "historical_vendor_abi_proven": False, "sources": [], "results": {},
              "implementation_objects": [],
              "toolchain": (a.ndk / "source.properties").read_text()}
    total = 0
    try:
        for version in ("m", "q"):
            dest = a.out / version
            dest.mkdir()
            seen = set()
            def fetch(header):
                nonlocal total
                if header in seen:
                    return
                if ".." in Path(header).parts or Path(header).is_absolute():
                    raise ValueError("Unsafe include")
                seen.add(header)
                for repo_key, root in ROOTS[version]:
                    item = lock[repo_key + "_" + version]
                    path = root + "/" + header
                    # SharedBuffer was private in some trees.
                    if root == "libutils" and header == "utils/SharedBuffer.h":
                        path = "libutils/SharedBuffer.h"
                    url = "https://raw.githubusercontent.com/" + item["repo"] + "/" + item["sha"] + "/" + path
                    try:
                        with urllib.request.urlopen(url, timeout=30) as response:
                            data = response.read(256 * 1024 + 1)
                    except urllib.error.HTTPError as e:
                        if e.code == 404:
                            continue
                        raise
                    if len(data) > 256 * 1024 or total + len(data) > 2 * 1024 * 1024:
                        raise ValueError("Header download budget exceeded")
                    total += len(data)
                    target = dest / header
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data)
                    report["sources"].append({"version": version, "include": header,
                        "url": url, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
                    # Fetch Android internal includes. Standard headers come from NDK.
                    for inc in re.findall(r'^\s*#\s*include\s*[<"]([^>"]+)[>"]', data.decode(), re.M):
                        if inc in ("SharedBuffer.h", "VectorImpl.h") or inc.startswith(("utils/", "ui/", "math/", "cutils/", "log/",
                                           "android-base/", "android/", "backtrace/",
                                           "system/", "nativebase/", "nativewindow/")):
                            fetch(inc)
                    return
                raise RuntimeError("Missing original header: " + version + "/" + header)
            for header in HEADERS:
                fetch(header)
            source = dest / "probe.cpp"
            source.write_text("\n".join('#include <' + h + '>' for h in HEADERS) +
                '\nextern "C" {\n' + "\n".join(
                    "unsigned char " + kind + "_" + t + "[" + op + "(android::" + t + ")];"
                    for t in TYPES for kind, op in (("size", "sizeof"), ("align", "alignof"))) + "\n}\n")
            for arch, triple in (("arm", "armv7a-linux-androideabi"), ("arm64", "aarch64-linux-android")):
                api = "23" if version == "m" else "29"
                obj = dest / (arch + ".o")
                result = run([str(binpath / (triple + api + "-clang++")), "-std=c++17",
                              "-fno-rtti", "-fno-exceptions",
                              "-Xclang", "-fdump-record-layouts", "-I" + str(dest),
                              "-c", str(source), "-o", str(obj)])
                (dest / (arch + ".log")).write_text(result.stdout)
                print("RECORD_LAYOUT " + version + "/" + arch + "\n" + result.stdout)
                if result.returncode:
                    raise RuntimeError(version + "/" + arch + ": " + result.stdout)
                nm = run([str(binpath / "llvm-nm"), "-S", "--defined-only", str(obj)])
                if nm.returncode:
                    raise RuntimeError(nm.stdout)
                values = {}
                for line in nm.stdout.splitlines():
                    cols = line.split()
                    if len(cols) == 4 and re.fullmatch(r"(size|align)_\w+", cols[3]):
                        values[cols[3]] = int(cols[1], 16)
                if len(values) != len(TYPES) * 2:
                    raise RuntimeError("Incomplete object symbol measurements")
                report["results"][version + "_" + arch] = values
            # Original Q implementations, compiled to relocatable objects only.
            # Linking, dependency closure and Huawei runtime behavior remain untested.
            if version == "q":
                for cpp in ("Region.cpp", "VectorImpl.cpp", "SharedBuffer.cpp", "String8.cpp"):
                    fetch(cpp)
                    for arch, triple in (("arm", "armv7a-linux-androideabi"), ("arm64", "aarch64-linux-android")):
                        obj = dest / (cpp + "." + arch + ".o")
                        result = run([str(binpath / (triple + "29-clang++")), "-std=c++17",
                                      "-fPIC", "-fno-rtti", "-fno-exceptions", "-I" + str(dest),
                                      "-c", str(dest / cpp), "-o", str(obj)])
                        print("IMPLEMENTATION " + cpp + "/" + arch + "\n" + result.stdout)
                        entry = {"source": cpp, "arch": arch, "returncode": result.returncode}
                        if result.returncode == 0:
                            symbols = run([str(binpath / "llvm-nm"), "-P", str(obj)])
                            entry["symbols"] = symbols.stdout
                            entry["sha256"] = hashlib.sha256(obj.read_bytes()).hexdigest()
                        else:
                            entry["error"] = result.stdout
                        report["implementation_objects"].append(entry)
        report["equal_sizes_and_alignments"] = {
            arch: report["results"]["m_" + arch] == report["results"]["q_" + arch]
            for arch in ("arm", "arm64")}
        report["status"] = "HEADER_LAYOUT_MEASURED"
    except Exception as exc:
        report["status"] = "EXPERIMENT_FAILED"
        report["error"] = str(exc)
    report["downloaded_header_bytes"] = total
    (a.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return int(report["status"] == "EXPERIMENT_FAILED")

if __name__ == "__main__":
    raise SystemExit(main())
