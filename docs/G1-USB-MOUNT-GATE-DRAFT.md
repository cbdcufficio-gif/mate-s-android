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
