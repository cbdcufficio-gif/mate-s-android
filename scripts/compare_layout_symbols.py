#!/usr/bin/env python3
"""Compare selected vendor imports to measured Q relocatable object symbols."""
import argparse
import json
from pathlib import Path
import re
from elf_audit import Elf, sha256

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--graphics", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    if a.out.exists():
        p.error("Output must be new")
    report = json.loads(a.report.read_text())
    if not report.get("implementation_compile_passed"):
        p.error("Successful implementation compilation report required")
    providers = {arch: set() for arch in ("arm", "arm64")}
    for obj in report["implementation_objects"]:
        for line in obj["symbols"].splitlines():
            cols = line.split()
            if len(cols) >= 2 and cols[1] in ("T", "W", "D", "V", "B", "R"):
                providers[obj["arch"]].add(cols[0])
    results = []
    for path in sorted(a.graphics.rglob("*.so")):
        elf = Elf(path)
        arch = "arm" if elf.bits == 32 else "arm64"
        if elf.machine != (40 if arch == "arm" else 183):
            p.error("Expected ARM ELF")
        names = sorted({s["name"] for s in elf.symbols() if s["undefined"] and
                        re.search(r"(6Region|7String8|10VectorImpl|12SharedBuffer)", s["name"])})
        results.append({"path": str(path.relative_to(a.graphics)), "sha256": sha256(path),
                        "arch": arch, "selected_imports": names,
                        "missing_from_compiled_objects": sorted(set(names) - providers[arch])})
    if not results:
        p.error("No libraries found")
    output = {"scope": "Selected class names in relocatable objects only; not dynamic exports, "
                      "symbol versions, namespace resolution, link closure or runtime proof",
              "runtime_tested": False, "report_sha256": sha256(a.report), "libraries": results,
              "selected_import_occurrences": sum(len(x["selected_imports"]) for x in results)}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with a.out.open("x") as stream:
        json.dump(output, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"libraries": len(results), "imports": output["selected_import_occurrences"],
                      "missing": sum(len(x["missing_from_compiled_objects"]) for x in results)}))

if __name__ == "__main__":
    main()
