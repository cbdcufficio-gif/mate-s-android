#!/usr/bin/env python3
"""Strict shared link experiment; never an installable libui/libutils replacement."""
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request
from elf_audit import Elf
from build_log_probe import fetch_core, build

COMMIT = "2e659f04a7cde964415c82dd7507610769165408"
BASE = "https://android.googlesource.com/platform/prebuilts/vndk/v29/+/" + COMMIT + "/"
PROVIDERS = {
    "arm": ("arm/arch-arm-armv7-a-neon/shared/vndk-sp/libc++.so",
            "aaea72cc802c1eb1f6a1115dc44752463653d378", 40),
    "arm64": ("arm64/arch-arm64-armv8-a/shared/vndk-sp/libc++.so",
              "5646444f49c25f49e3492771cb66d2c886fa7016", 183),
}

def run(argv):
    return subprocess.run(list(map(str, argv)), text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, timeout=120)

def main():
    if subprocess.call([sys.executable, "scripts/platform_cxx_probe.py"]):
        return 1
    root = Path("out/shared-link")
    root.mkdir(parents=True, exist_ok=False)
    binpath = Path(os.environ["ANDROID_NDK_HOME"]) / "toolchains/llvm/prebuilt/linux-x86_64/bin"
    report = {"rom_built": False, "hardware_tested": False,
              "replacement_library_built": False, "architectures": [],
              "provider_commit": COMMIT,
              "link_scope": "Real VNDK29 libc++; original Q liblog; NDK API29 C stubs and modern compiler runtime"}
    try:
        core = root / "core"
        report["log_source"] = fetch_core(core)
        for arch, (relative, expected_blob, machine) in PROVIDERS.items():
            dest = root / arch
            dest.mkdir()
            url = BASE + relative + "?format=TEXT"
            with urllib.request.urlopen(url, timeout=45) as response:
                encoded = response.read(8 * 1024**2 + 1)
            if len(encoded) > 8 * 1024**2:
                raise ValueError("Provider download budget exceeded")
            data = base64.b64decode(encoded, validate=True)
            actual_blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
            if actual_blob != expected_blob:
                raise ValueError("Pinned provider Git blob mismatch")
            provider = dest / "libc++.so"
            provider.write_bytes(data)
            elf = Elf(provider)
            if elf.machine != machine:
                raise ValueError("Wrong provider architecture")
            triple = "armv7a-linux-androideabi" if arch == "arm" else "aarch64-linux-android"
            compiler = binpath / (triple + "29-clang++")
            # Confirm -z defs is actually enforced with a deliberate missing symbol.
            negative = dest / "negative.cpp"
            negative.write_text('extern "C" void mates_deliberately_missing();\n'
                                'extern "C" void probe(){ mates_deliberately_missing(); }\n')
            strict = ["-shared", "-fPIC", "-nostdlib++", "-Wl,-z,defs"]
            control = run([compiler, *strict, negative, "-o", dest / "negative.so"])
            if control.returncode == 0 or "mates_deliberately_missing" not in control.stdout:
                raise ValueError("Strict unresolved-symbol negative control failed")
            combined = Path("out/platform-layout/q") / (arch + "-combined.o")
            output = dest / "libmates_graphics_probe.so"
            log_result = build(core, dest, compiler, provider, run)
            if log_result["status"] != "LINK_PASSED":
                report["architectures"].append({"arch": arch, "returncode": 1,
                    "log_build": log_result, "negative_control_rejected": True})
                continue
            command = [compiler, *strict, "-Wl,-soname,libmates_graphics_probe.so",
                       combined, provider, dest / "liblog.so", "-o", output]
            link = run(command)
            entry = {"arch": arch, "returncode": link.returncode,
                     "diagnostic": link.stdout, "command": list(map(str, command)),
                     "negative_control_rejected": True, "provider_url": url,
                     "log_build": log_result,
                     "provider_git_blob": actual_blob,
                     "provider_sha256": hashlib.sha256(data).hexdigest(),
                     "provider_bytes": len(data)}
            if link.returncode == 0:
                entry["output_sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
                entry["dynamic_metadata"] = run([binpath / "llvm-readelf", "-d", "--version-info", output]).stdout
                entry["undefined_dynamic_symbols"] = run([binpath / "llvm-nm", "-D", "-u", output]).stdout
            report["architectures"].append(entry)
        report["status"] = ("SHARED_LINK_PASSED" if
            all(x["returncode"] == 0 for x in report["architectures"]) else "SHARED_LINK_FAILED")
    except Exception as error:
        report["status"] = "EXPERIMENT_FAILED"
        report["error"] = str(error)
    (root / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)
    return int(report["status"] != "SHARED_LINK_PASSED")

if __name__ == "__main__":
    raise SystemExit(main())
