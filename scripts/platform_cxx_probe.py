#!/usr/bin/env python3
"""Fetch bounded, unmodified platform libc++ headers and compile only."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import urllib.request

SHA = "0dfca9975f466d77ebb15f4d3cf4442b15384ae4"
URL = "https://codeload.github.com/LineageOS/android_external_libcxx/tar.gz/" + SHA

def main():
    root = Path("out/platform-cxx")
    root.mkdir(parents=True, exist_ok=False)
    with urllib.request.urlopen(URL, timeout=60) as stream:
        data = stream.read(32 * 1024**2 + 1)
    if len(data) > 32 * 1024**2:
        raise ValueError("Archive budget exceeded")
    total = count = 0
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        for member in archive:
            parts = Path(member.name).parts
            if len(parts) < 3 or parts[1] != "include" or not member.isfile():
                continue
            relative = Path(*parts[2:])
            if ".." in relative.parts or relative.is_absolute():
                raise ValueError("Unsafe path")
            total += member.size
            count += 1
            if total > 16 * 1024**2 or count > 2000:
                raise ValueError("Header budget exceeded")
            target = root / "include" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.extractfile(member).read())
    provenance = {"commit": SHA, "url": URL,
                  "archive_sha256": hashlib.sha256(data).hexdigest(),
                  "header_count": count, "header_bytes": total,
                  "linked": False, "platform_abi_proven": False}
    (root / "provenance.json").write_text(json.dumps(provenance, indent=2))
    print(json.dumps(provenance), flush=True)
    import os
    return subprocess.call(["python3", "scripts/header_layout.py", "--ndk",
        os.environ["ANDROID_NDK_HOME"], "--platform-cxx", str(root / "include"),
        "--out", "out/platform-layout"])

if __name__ == "__main__":
    raise SystemExit(main())
