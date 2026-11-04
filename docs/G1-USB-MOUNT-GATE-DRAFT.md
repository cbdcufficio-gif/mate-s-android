# Mount-success gate: design pending implementation

An experimental orchestration header now models preparation, mount,
verification, alias write/readback and service start with explicit early
failure returns. The host fault-injection harness covers all 64 combinations
of operation failure. This tests sequencing only: all operations are injected,
there is no syscall/Q adapter, no verified filesystem observation and no
product integration. It must not be counted as a successful mount or as closing
the mount gate. Next implementation work is the concrete checked adapter.

The experimental target checker now uses real openat(O_NOFOLLOW|O_DIRECTORY)
and fstatfs on the returned descriptor. It rejects missing targets, symlinks,
invalid parent descriptors and a real host filesystem other than FunctionFS.
A 1000-iteration rejection test under a 64-descriptor limit checks cleanup.
No successful FunctionFS mount is exercised. Parent identity, mount source,
label, later pathname reopening by adbd and lifecycle still require concrete
validation; this checker alone is not the full adapter or startup gate.

The rc sequence cannot establish success by placing a property write or a
start command after mount: pinned Q continues after command failure. A
separate exec followed by start in the same action has the same issue.

Candidate boundary: one operation owns preparation and validates success
before requesting adbd start. It must reject an existing non-FunctionFS
mount, unexpected mount source/target, symlinked target, mount failure or
alias write failure. It must not publish a success token on any failure.
The generic adbd start path must not bypass this operation.

A filesystem check alone has a check/use race. The design must retain the
verified directory handle and define who can change that mount during the
handoff. A cached global ready property does not establish a current mount
or transport generation. Stale ready events remain a separate gate before
gadget enable, even if preparation succeeded.

Alternatives still to evaluate against pinned Q code:

- Dedicated checked init operation: direct error propagation, but introduces
  an init extension and requires explicit tests of service start semantics.
- Small preparation helper: preserves upstream init but requires an explicit
  executable label/domain, control-property authority, lifecycle and failure
  reporting; cannot be installed by copying a shell script into init rc.

Before selection, use a discriminating fixture with failed mount, wrong fs,
symlink, failed alias and successful preparation. No test may equate mocked
observations with actual Huawei mount or policy enforcement. No helper,
property grant or rc import is implemented by this draft.

## Next implementation slice

Pinned Q init/builtins.cpp defines do_mount as Result<Success>. The ordinary
dispatcher discards failure for sequencing, but a dedicated preparation
operation can inspect each result before invoking subsequent steps. Explore
this bounded option first: mkdir/target validation, mount, verify observed
filesystem and alias, then request adbd start only on success. Do not change
global dispatcher error semantics. This avoids requiring a new executable
domain or control-property grant for a helper, while still requiring a source
patch and an init compilation check before use.

The fixture must inject failure at each step and assert zero start calls;
the successful case must assert exactly one start after verification. All
adbd start paths in the selected mode must route through this operation.
The gadget-ready gate and endpoint lifetime are distinct and remain open.

The pinned Q BuiltinArguments constructor accepts a vector of arguments and
a context reference; nested calls must retain the caller context lifetime.
BuiltinFunction returns Result<Success>. A candidate checked operation can
therefore propagate do_mkdir/do_mount/do_write/do_start failures internally,
without changing the global command dispatcher. Validation must reject
symlinked target components before mounting and verify the resulting fs type
through an opened directory handle before the start request. The preparation
operation must remain unavailable to unrelated untrusted rc subcontexts.

## Verified host subphase, 4 November

Run41828619636/job126569721641 at03a42733b8ed33cf8ad4ae1e84225c6afdbcfc4c passed154/154 tests, zero skips,12.253s. Checksums and pinned-source/patch/policy/USB checks passed. Review found no blocker within the explicitly experimental scope. The sequencing matrix and real host rejection/cleanup subphase is complete; the mount-success gate remains open. Next: concrete checked Q adapter, parent/source/alias validation and lifecycle handling, followed by a bounded compilation check. Another equivalent model fixture or full Android build would not resolve this gap.

## Parent-anchor work in progress

OpenCarreraFunctionfsFromDev now resolves usb-ffs and adb through held directory descriptors with O_NOFOLLOW and O_DIRECTORY on each component. The caller still must supply a verified /dev descriptor. Real host tests reject a missing parent, a parent symlink that would otherwise reach adb, wrong filesystem and invalid root descriptor; repeated two-component rejection exercises cleanup under the existing descriptor limit. This is a native path-validation primitive, not the Q adapter: ownership/labels, mount source, context guard, alias and lifecycle remain unimplemented. Do not import rc or publish another equivalent sequencing-only CI.

Pinned Q Command::InvokeFunc passes the vendor caller context even when a builtin map entry is false (execution in init). A dedicated privileged operation must explicitly reject non-init origin before side effects; false is not authorization. Existing Q class_start_post_data/class_reset_post_data show args.context comparison against kInitContext. Public source inputs and hashes are retained locally outside the repository.

## Mount identity snapshot, work in progress

The native checker now compares a held directory descriptor st_dev against a unique mountinfo record with exact target, root, filesystem and source. The FunctionFS wrapper fixes these to /dev/usb-ffs/adb, root /, functionfs and adb after the existing fstatfs check. Missing, malformed, incomplete, oversized and duplicate target records fail closed. This is a snapshot: st_dev is not a mount-instance identifier, bind mounts or detached descriptors need lifecycle handling, and later adbd pathname access is not bound by this check. No Q adapter or caller-context guard has been installed.

Host fixture exercises an actual root filesystem mount-table match and wrong source/type rejection, plus explicitly synthetic FunctionFS records for format/device/root/ambiguity errors. Synthetic success is not FunctionFS mount evidence. The initial test incorrectly assumed /proc had a unique mount entry; this restricted host has two stacked entries. The fixture now uses its real unique root mount for positive host evidence, preserving rejection of ambiguous entries. Q compilation and Huawei mount/policy remain unverified.

## Alias I/O primitive, work in progress

Pinned Huawei android.c (G1-USB-ALIAS-SOURCE.json) rejects alias writes with -EBUSY when dev->enabled; show emits the current value plus newline, protected by the same mutex. This is static source evidence, not an executed callback. WriteAndVerifyCarreraFunctionfsAlias uses an already verified f_ffs directory descriptor, opens aliases with O_NOFOLLOW, requires sysfs, performs one write of adb and exact readback adb plus newline, and propagates any failure without retry. The caller identity, f_ffs device identity and competing privileged writers remain prerequisites.

Real host tests reject missing/symlink/non-sysfs targets, verify a hardlinked backing file is unchanged and repeat failure1000times under64-descriptor limit. No successful sysfs write or Huawei EBUSY callback is tested. Parent/mount/alias primitives still need the Q caller-context guard, lifecycle and bounded Q compilation before product use.

## Q glue prototype: host compilation, not installed

The unregistered carrera_checked_adbd.inc body uses actual Q Result, BuiltinArguments and unique_fd types. It rejects non-init context and arguments before property/path access, restricts legacy adb-only mode, holds /dev and FunctionFS descriptors through the start request, traverses the inferred canonical Huawei sysfs path without following components, writes/readbacks aliases and rechecks live mount identity plus device/inode before do_start. It validates an existing mount rather than proving an earlier mount command succeeded.

Host compilation uses pinned Q headers without changing their bodies. The guard fixture substitutes properties, the first /dev open and do_start; it verifies vendor/empty/extended/NUL-suffixed context rejection before accesses, argument/mode rejection, and propagated EACCES with zero starts. Later native success branches are compiled, not executed by this fixture. No full Q init binary, successful sysfs/FunctionFS operation, service transport or enforcing boot is proved. Source-check CI now compares all three headers and the init context constant against pinned public bytes.

Lifecycle requirement before registration/import: identify and constrain every competing legacy adbd start and gadget enable path; establish that no privileged mount/alias writer can replace the validated objects during the asynchronous adbd open. A held fd and device/inode recheck do not establish this. Confirm canonical sysfs path and effective labels on the candidate. No parser map entry, rc import or gadget enable has been changed.

Source-copy correction: saving through the patch tool had appended one extra newline to Huawei android.c and Q source copies. Removed that added byte, recorded corrected SHA in G1-USB-ALIAS-SOURCE.json, and added upstream byte comparison. This did not alter any tested kernel function; the old cached-source digest must not be presented as upstream digest.
