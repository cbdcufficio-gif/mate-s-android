# Mate S porting working instructions

Read `docs/PORTING-DIRECTION.md` and `docs/PORTING-STATE.json` before continuing.
They define the current direction and milestone state. `docs/STATUS.md` retains
dated history; old claims of missing builds or queued runs are not current facts.
Verify live CI state and the checkout before changing anything.

## Scope and ownership
- Target Huawei Carrera CRR-L09, first proving a coherent Android Q system.
  Prefer the rebuilt Huawei 3.10 BSP, Carrera DT/firmware and targeted backports.
  Kernel version alone does not prove missing capabilities.
- One agent owns the active build repair. Antigravity task-28 was reported as
  following run 40231781220 at the direction update. Check for successor runs
  and concurrent commits before intervention; do not queue duplicate builds.
- Preserve untracked files and other agents' edits. In particular, the local
  make_carrera_boot.py helper and its fixture test are not validated Carrera
  packaging and must not become the production boot path.

## Evidence and next milestone
- A public system/ramdisk build excludes Huawei HALs and kernel/DTB: it is a
  development input, not a bootable ROM. Capture commit, resolved manifest,
  report and asset hashes before advancing.
- The current verifier checks module bytes inside ext4 and separately checks
  root/vendor in root staging. Do not claim the root symlink or all rootdir
  contents were verified inside ext4 or at runtime.
- Gate order: public artifact -> coherent final configuration/ABI -> correct
  boot packaging and recovery -> Q kernel/init/authenticated ADB -> UI/input
  -> hardware/security/stability acceptance. Do not infer one gate from another.
- Launch API is Android 5.1/API22; acquired B321 stock is Android6/API23.
  A tested API22 correction is staged in docs/deferred/carrera-launch-api22.patch.
  Archive the current run as built at API23; apply/review the patch before the
  next deliberate Carrera build, refreshing checksum hunks if main has moved.
- Never copy the whole stock framework/ART/bionic/libbinder over Q. Legacy
  libraries need a verified private dependency closure or an explicit IPC/ABI
  bridge. Keep ARM32/ARM64 services separate.

## Constraints and validation
- No local full Android sync/build. Use disposable standard public CI runners;
  keep Huawei blobs, dumps, firmware, credentials and personal data local.
  FreeLLMAPI reviews public inputs only and is not build or hardware evidence.
- Preserve /vendor, SELinux/neverallow, ELF, size and touchscreen firmware guards.
  Do not retry the rejected fastboot boot or add automatic flash/erase/format,
  restore or reboot actions. Persistent tests need correct images and an
  established recovery path within the user's authorization.
- For code changes run the relevant tests and `python3 -m unittest discover tests`.
  Report tests run, passed and skipped separately. Update SHA256SUMS for changed
  tracked files and new public source/document files; do not hash private outputs.
- Make bounded changes for an identified cause. Update milestone evidence, not
  an invented completion percentage. A compiler pass, lshal entry or LLM answer
  does not close a hardware acceptance test.

