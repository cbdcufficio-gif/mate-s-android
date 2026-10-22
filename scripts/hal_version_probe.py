#!/usr/bin/env python3
"""Read constant hw_module_t fields without loading a proprietary HAL."""
import argparse
import json
from pathlib import Path
import struct
from elf_audit import Elf, sha256

def inspect(path):
    elf = Elf(path)
    hmi = [s for s in elf.symbols() if s["name"] == "HMI" and not s["undefined"]]
    result = {"path": path.name, "sha256": sha256(path), "bits": elf.bits,
              "hardware_tested": False, "device_api_version": "NOT_DETERMINED"}
    if not hmi:
        return {**result, "status": "NO_HMI_EXPORT"}
    if len(hmi) != 1 or hmi[0]["size"] < 8 or hmi[0]["type"] != 1:
        raise ValueError("Ambiguous or undersized HMI object")
    address = hmi[0]["value"]
    offsets = {off + address - va for off, size, va, _, _ in elf.loads
               if va <= address and address + 8 <= va + size}
    if len(offsets) != 1:
        return {**result, "status": "HMI_NOT_UNIQUELY_FILE_BACKED",
                "warning": "Cannot read initialized module fields statically; inspect initialization code"}
    tag, module, hal = struct.unpack("<IHH", elf.slice(offsets.pop(), 8))
    if tag != 0x48574d54:
        raise ValueError("Unexpected HARDWARE_MODULE_TAG")
    return {**result, "status": "STATIC_MODULE_FIELDS_READ", "tag": hex(tag),
            "module_api_raw": hex(module), "module_api_major": module >> 8,
            "module_api_minor": module & 255, "hal_api_raw": hex(hal),
            "warning": "Module version is not the device API version returned by HAL open"}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--graphics", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    if a.out.exists():
        p.error("Output must be new")
    files = sorted(a.graphics.rglob("*.so"))
    if not files:
        p.error("No libraries")
    results = []
    for path in files:
        report = inspect(path)
        report["path"] = str(path.relative_to(a.graphics))
        results.append(report)
    with a.out.open("x") as stream:
        json.dump({"runtime_tested": False, "libraries": results}, stream, indent=2)
        stream.write("\n")
    print(json.dumps([r for r in results if r["status"] != "NO_HMI_EXPORT"]))

if __name__ == "__main__":
    main()
