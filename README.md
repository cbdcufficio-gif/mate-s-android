# Huawei Mate S — Android 10+ port

Experimental source project for Huawei Mate S CRR-L09 / Carrera / Kirin 935.
The goal is a complete usable Android 10 or newer ROM. **No installable ROM,
bootable boot.img, or successful hardware boot is provided yet.**

## What exists

- Kernel 3.10.86 stock and Android 10 diagnostic builds recorded offline.
- Carrera userspace product skeleton for LineageOS 17.1.
- Hash-locked static ELF tooling for graphics candidates in ARM32 and ARM64.
- Read-only HAL/RIL inventory and bounded manifest/resource preflight.
- Public standard-runner CI with no Android source sync, paid runner, cache,
  artifact storage, LFS, Packages or credentials required.

Remote checks completed: [preflight](https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/39841220576)
and [capacity plus ARM32/ARM64 tests](https://github.com/cbdcufficio-gif/mate-s-android/actions/runs/39842020143).
The disposable runner provided 4 CPUs, approximately 16 GB RAM and 105.1 GiB free
after reclaiming unused SDKs and installing cross compilers. All 21 tool tests
passed without skips. This is not an Android module or ROM build.

The kernel source uses a Liszt repository as a reference. This does not make
Liszt, GRACE or Honor 7 images/DTBs compatible with Carrera. Keep the verified
Carrera stock DTB; packaging remains a separate unverified task.

## Next milestone

Measure the remote host, then establish the Android 10 native build and graphics
ABI. Source presence and symbol coverage do not prove driver functionality.
The complete ROM additionally needs init/mount configuration, SELinux enforcing,
HAL integration, Huawei boot packaging and the hardware acceptance matrix.

Read [the technical and zero-cost plan](docs/ZERO-COST-PLAN.md),
[source references](SOURCES.md), and [hardware matrix](docs/HARDWARE-MATRIX.md).
The [ABI investigation](docs/ABI-REVIEW.md) records the specific graphics contracts
still needing proof; [session evidence](docs/SESSION-20261022.json) records results.

## Small checks

The preflight downloads only bounded manifest XML from a pinned LineageOS commit:

```sh
python3 scripts/remote_preflight.py --out out/preflight-01
python3 -m unittest discover -s tests -p 'test_*.py'
```

It reports planning budgets, never authorizes a complete checkout, and never
claims a ROM was built. A missing cross compiler skips the synthetic ARM build
test; host-only tests still run. GitHub Actions records results in job logs and
the job summary. A green preflight is not a green Android build.

For local static inspection of an already extracted firmware (no phone access):

```sh
python3 scripts/prepare_graphics.py --stock-system /path/to/stock/system --out generated/graphics-01
python3 scripts/stock_inventory.py --stock-system /path/to/stock/system --graphics generated/graphics-01 --out out/stock-inventory-01.json
```

Stock inputs must match `configs/stock-elf-lock.json`. Proprietary libraries,
firmware dumps, backups and generated candidates stay outside GitHub. The public
source package is selected using an explicit allowlist, not a recursive upload.

## External models and validation

FreeLLMAPI is used for alternative designs, code drafts and independent reviews.
It provides text inference, not an Android compilation server. Model claims are
checked against primary source code and actual tests. Rejected claims include a
drop-in non-Treble GSI, mandatory gralloc4 for all Q ports, and version-property
changes being a real Android upgrade. See [review decisions](docs/REVIEWS.md).

None of the provided scripts flashes partitions, reboots the phone or locks the
bootloader. Kernel touchscreen firmware-update behavior must be reviewed before
a new kernel can be considered for hardware testing.

Original tools and recipes: MIT. Kernel configuration/patch: GPL-2.0; see
[license notes](LICENSE-NOTES.md). External sources retain their own licenses.
