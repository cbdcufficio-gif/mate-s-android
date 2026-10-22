#!/usr/bin/env python3
"""Bounded static VNDK dependency audit; no Android loader or runtime claim."""
import base64
import hashlib
import json
from pathlib import Path
import urllib.request
from elf_audit import Elf, resolve_symbols

COMMIT = "2e659f04a7cde964415c82dd7507610769165408"
BASE = "https://android.googlesource.com/platform/prebuilts/vndk/v29/+/" + COMMIT + "/"
BOUNDARY = {"libc.so", "libm.so", "libdl.so", "liblog.so"}
ARCHES = {"arm": ("arm/arch-arm-armv7-a-neon/shared/", 40),
          "arm64": ("arm64/arch-arm64-armv8-a/shared/", 183)}

def read(url, limit):
    with urllib.request.urlopen(url, timeout=40) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError("Download limit exceeded")
    return data

def main():
    root = Path("out/vndk-closure")
    root.mkdir(parents=True, exist_ok=False)
    result = {"commit": COMMIT, "runtime_tested": False,
              "android_namespace_verified": False, "architectures": [],
              "boundary_not_audited": sorted(BOUNDARY)}
    total = 0
    try:
        for arch, (prefix, machine) in ARCHES.items():
            dest = root / arch
            dest.mkdir()
            index = {}
            for group in ("vndk-sp", "vndk-core"):
                path = prefix + group + "/"
                listing = json.loads(read(BASE + path + "?format=JSON", 512 * 1024).decode()[5:])
                for item in listing["entries"]:
                    if item["type"] == "blob" and item["name"].endswith(".so"):
                        if item["name"] in index:
                            raise ValueError("Ambiguous provider name")
                        index[item["name"]] = (path + item["name"], item["id"])
            reports, provenance, missing, boundary = {}, {}, set(), set()
            todo = ["libbacktrace.so"]
            while todo:
                name = todo.pop()
                if name in reports or name in missing:
                    continue
                if name in BOUNDARY:
                    boundary.add(name)
                    continue
                if name not in index:
                    missing.add(name)
                    continue
                if len(reports) >= 24:
                    raise ValueError("Provider count limit exceeded")
                relative, expected = index[name]
                url = BASE + relative + "?format=TEXT"
                encoded = read(url, 12 * 1024**2)
                data = base64.b64decode(encoded, validate=True)
                total += len(data)
                if total > 32 * 1024**2:
                    raise ValueError("Total provider budget exceeded")
                blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
                if blob != expected:
                    raise ValueError("Git blob mismatch")
                path = dest / name
                path.write_bytes(data)
                elf = Elf(path)
                if elf.machine != machine or elf.dynamic()["soname"] != name:
                    raise ValueError("Provider architecture or SONAME mismatch")
                report = elf.report()
                reports[name] = report
                provenance[name] = {"url": url, "git_blob": blob,
                                    "sha256": report["sha256"], "bytes": len(data),
                                    "needed": report["needed"]}
                todo.extend(report["needed"])
            coverage = {}
            for name, consumer in reports.items():
                reachable, pending = set(), list(consumer["needed"])
                while pending:
                    target = pending.pop()
                    if target in reachable or target not in reports or target == name:
                        continue
                    reachable.add(target)
                    pending.extend(reports[target]["needed"])
                checks = resolve_symbols(consumer, {n: reports[n] for n in reachable})["results"]
                unmatched = [x for x in checks if not x["candidate_providers"] and not x["weak"]]
                coverage[name] = {"reachable_supplied_providers": sorted(reachable),
                    "imports_checked": len(checks), "unmatched_strong_imports": len(unmatched),
                    "unmatched_examples": unmatched[:12],
                    "warning": "Unmatched includes absent system boundary providers; not proof of broken library"}
            result["architectures"].append({"arch": arch, "providers": provenance,
                "missing_nonboundary_libraries": sorted(missing),
                "encountered_boundary": sorted(boundary), "static_symbol_coverage": coverage})
        result["status"] = "STATIC_AUDIT_COMPLETED"
    except Exception as error:
        result["status"] = "AUDIT_FAILED"
        result["error"] = str(error)
    result["downloaded_provider_bytes"] = total
    (root / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)
    return int(result["status"] != "STATIC_AUDIT_COMPLETED")

if __name__ == "__main__":
    raise SystemExit(main())
