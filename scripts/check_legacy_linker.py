#!/usr/bin/env python3
"""Check the intended legacy default namespace policy, not actual Android loading."""
import argparse
import hashlib
import json
from pathlib import Path
import re

def inspect(path):
    data = path.read_bytes()
    section = None
    values = {}
    routes = []
    for raw in data.decode().splitlines():
        line = raw.split("#", 1)[0].strip()
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
            continue
        match = re.fullmatch(r"([\w.]+)\s*(\+?=)\s*(.*)", line)
        if not match:
            continue
        key, op, value = match.groups()
        if section is None and key == "dir.legacy":
            routes.append(value)
        if section != "legacy":
            continue
        values[key] = (values.get(key, "") + ":" + value) if op == "+=" else value
    paths = values.get("namespace.default.search.paths", "").split(":")
    checks = {
        "legacy_routes_system_vendor": all(p in routes for p in ("/system", "/vendor")),
        "legacy_default_not_isolated": values.get("namespace.default.isolated") == "false",
        "system_vendor_search_paths": all(p in paths for p in ("/system/${LIB}", "/vendor/${LIB}")),
    }
    return {"status": "LEGACY_POLICY_MATCH" if all(checks.values()) else "POLICY_REVIEW_REQUIRED",
            "sha256": hashlib.sha256(data).hexdigest(), "checks": checks,
            "search_paths": paths, "runtime_loading_proven": False,
            "warning": "Use the final generated config; service namespace, mounts, APEX and ELF ABI remain unverified"}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    if a.out.exists():
        p.error("Output must be new")
    report = inspect(a.config)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with a.out.open("x") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps(report))
    return int(report["status"] != "LEGACY_POLICY_MATCH")

if __name__ == "__main__":
    raise SystemExit(main())
