#!/bin/bash
# Runs only inside an isolated disposable runner mount namespace.
set -euo pipefail
work=$(mktemp -d)
trap 'umount "$work/mount/cache" 2>/dev/null || true; umount "$work/mount" 2>/dev/null || true; rm -rf "$work"' EXIT
mkdir -p "$work/root/cache" "$work/mount"
ln -s /data/cache "$work/root/old-cache"
truncate -s 32M "$work/root.img"
mkfs.ext4 -q -F -d "$work/root" "$work/root.img"
mount -o loop,ro "$work/root.img" "$work/mount"
python3 - "$work/mount" <<'PY'
import errno,os,sys
root=sys.argv[1]
assert os.readlink(root+'/old-cache')=='/data/cache'
try:os.unlink(root+'/old-cache')
except OSError as e:assert e.errno==errno.EROFS
else:raise AssertionError('Readonly unlink unexpectedly succeeded')
assert os.path.isdir(root+'/cache') and not os.path.islink(root+'/cache')
PY
mount -t tmpfs -o size=1m none "$work/mount/cache"
umount "$work/mount/cache"
echo HOST_READONLY_CACHE_FIXTURE_PASSED
