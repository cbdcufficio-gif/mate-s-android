#!/usr/bin/env python3
"""Conservative, offline source inspection. Does not build or touch the device.

Verified presence means the listed source evidence exists, not that a feature is
compiled, secure, complete, or compatible with any Android release. This is not a
C preprocessor; conditional compilation still requires build/runtime validation.
"""
import argparse
import json
from pathlib import Path
import re

STATUSES = ('verifiedpresent', 'absent', 'unknown', 'tentative')


def uncomment(text):
    """Remove C comments while preserving line numbers and string literals."""
    pattern = r'("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')|/\*[\s\S]*?\*/|//[^\n]*'
    return re.sub(pattern, lambda m: m.group(1) if m.group(1) else '\n' * m.group(0).count('\n'), text)


def read_config(path):
    values = {}
    for number, line in enumerate(Path(path).read_text().splitlines(), 1):
        match = re.fullmatch(r'(CONFIG_\w+)=(.*)', line)
        disabled = re.fullmatch(r'# (CONFIG_\w+) is not set', line)
        if match:
            values[match[1]] = {'value': match[2], 'line': number}
        elif disabled:
            values[disabled[1]] = {'value': 'n', 'line': number}
    return values


class Inspector:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.cache = {}

    def code(self, relative):
        if relative not in self.cache:
            path = self.root / relative
            try:
                # Never follow a source symlink outside the supplied source tree.
                path.resolve().relative_to(self.root)
                self.cache[relative] = uncomment(path.read_text(errors='replace')) if path.is_file() else None
            except (OSError, ValueError):
                self.cache[relative] = None
        return self.cache[relative]

    def find(self, relative, pattern):
        code = self.code(relative)
        match = re.search(pattern, code, re.M) if code is not None else None
        return {'path': relative, 'line': code[:match.start()].count('\n') + 1 if match else None,
                'matched': bool(match), 'readable': code is not None,
                'text': match[0][:240] if match else None}

    def check(self, requirements, note):
        evidence = [self.find(path, regex) for path, regex in requirements]
        if all(item['matched'] for item in evidence):
            status = 'verifiedpresent'
        elif any(not item['readable'] for item in evidence):
            status = 'unknown'
        elif any(item['matched'] for item in evidence):
            status = 'tentative'
        else:
            status = 'absent'
        return {'status': status, 'note': note, 'evidence': evidence}


def audit(source, config):
    scan = Inspector(source)
    cfg = read_config(config)
    binder = 'drivers/android/binder.c'
    header = 'include/uapi/linux/android/binder.h'
    checks = {}
    checks['binder_multiple_devices'] = scan.check([
        ('drivers/Makefile', r'obj-\$\(CONFIG_ANDROID\)\s*\+=\s*android/'),
        ('drivers/android/Makefile', r'obj-\$\(CONFIG_ANDROID_BINDER_IPC\)\s*\+=\s*binder\.o'),
        ('drivers/android/Kconfig', r'default\s+"binder,hwbinder,vndbinder"'),
        (binder, r'misc_register\s*\(&binder_device->miscdev\)'),
        (binder, r'while\s*\(\(device_name\s*=\s*strsep\(&device_names,\s*","\)\)\)'),
        (binder, r'init_binder_device\s*\(device_name\)')],
        'Checks the existing multi-device implementation and build references; inspect the resolved configuration and device permissions separately.')
    checks['binder_protocol8'] = scan.check([
        (header, r'#ifdef\s+BINDER_IPC_32BIT[\s\S]*?#else\s*#define\s+BINDER_CURRENT_PROTOCOL_VERSION\s+8'),
        (binder, r'put_user\w*\s*\(BINDER_CURRENT_PROTOCOL_VERSION'),
        ('drivers/android/Kconfig', r'depends on !64BIT && ANDROID_BINDER_IPC')],
        'Protocol 8 is the non-legacy source branch. IPC_32BIT is the old wire ABI, not ordinary COMPAT application support.')
    checks['binder_scatter_gather'] = scan.check([
        (header, r'BC_TRANSACTION_SG\s*='), (header, r'BC_REPLY_SG\s*='),
        (binder, r'case BC_TRANSACTION_SG\s*:'), (binder, r'case BC_REPLY_SG\s*:')],
        'Checks UAPI commands and driver dispatch, not complete Binder correctness.')
    checks['binder_context_manager_ext'] = scan.check([
        (header, r'#define\s+BINDER_SET_CONTEXT_MGR_EXT\b'),
        (binder, r'case\s+BINDER_SET_CONTEXT_MGR_EXT\s*:')], 'Extended context manager ioctl definition and dispatch.')
    checks['binder_transaction_security_context'] = scan.check([
        (header, r'BR_TRANSACTION_SEC_CTX\s*='),
        (binder, r'\bsecurity_secid_to_secctx\s*\('),
        (binder, r'\bBR_TRANSACTION_SEC_CTX\b')], 'Security context UAPI and driver construction path.')

    # Test actual implementations and syscall table chains, not config labels.
    impls = {'getrandom': ['drivers/char/random.c'],
             'memfd_create': ['mm/memfd.c', 'mm/shmem.c'], 'seccomp': ['kernel/seccomp.c']}
    native = 'include/uapi/asm-generic/unistd.h'
    compat = 'arch/arm64/include/asm/unistd32.h'
    for name, candidates in impls.items():
        implementation = next((p for p in candidates if scan.find(p, r'SYSCALL_DEFINE\d\s*\(\s*' + name + r'\s*,')['matched']), next((p for p in candidates if scan.code(p) is not None), candidates[0]))
        base = [(implementation, r'SYSCALL_DEFINE\d\s*\(\s*' + name + r'\s*,')]
        for abi, table, chain in [
            ('arm64', native, [('arch/arm64/kernel/sys.c', r'sys_call_table[\s\S]*?#include\s*<asm/unistd.h>'),
                              ('arch/arm64/include/asm/unistd.h', r'#include\s*<uapi/asm/unistd.h>'),
                              ('arch/arm64/include/uapi/asm/unistd.h', r'#include\s*<asm-generic/unistd.h>')]),
            ('compat', compat, [('arch/arm64/kernel/sys32.S', r'ENTRY\(compat_sys_call_table\)[\s\S]*?#include\s*<asm/unistd32.h>')])]:
            checks[name + '_' + abi] = scan.check(base + chain + [
                (table, r'#define\s+__NR_' + name + r'\s+\d+'),
                (table, r'__SYSCALL\s*\(\s*__NR_' + name + r'\s*,\s*sys_' + name + r'\s*\)')],
                'Implementation and architecture table include chain; source evidence does not evaluate preprocessor guards or prove a working build.')
    checks['seccomp_tsync'] = scan.check([
        ('include/uapi/linux/seccomp.h', r'#define\s+SECCOMP_FILTER_FLAG_TSYNC\s+1'),
        ('kernel/seccomp.c', r'(?:void|pid_t)\s+seccomp_sync_threads\s*\(void\)\s*\{'),
        ('kernel/seccomp.c', r'if\s*\(flags\s*&\s*SECCOMP_FILTER_FLAG_TSYNC\)\s*seccomp_sync_threads\s*\('),
        ('arch/arm64/kernel/ptrace.c', r'if\s*\(secure_computing\(regs->syscallno\)'),
        ('arch/arm64/include/asm/thread_info.h', r'#define\s+_TIF_SYSCALL_WORK[^\n]*(?:\\\n[^\n]*)*?_TIF_SECCOMP')],
        'TSYNC implementation/call and ARM64 syscall filtering hooks; runtime testing is still necessary.')

    policy_header = 'security/selinux/include/security.h'
    code = scan.code(policy_header)
    policy = {'status': 'unknown', 'maximum': None, 'capabilities': [], 'evidence': []}
    if code is not None:
        definitions = dict(re.findall(r'^#define\s+(POLICYDB_VERSION_\w+)\s+(\w+)', code, re.M))
        value = definitions.get('POLICYDB_VERSION_MAX')
        # A configurable override is not the implementation's supported ceiling.
        defaults = re.findall(r'^#define\s+POLICYDB_VERSION_MAX\s+(POLICYDB_VERSION_\w+)', code, re.M)
        if defaults:
            value = defaults[-1]
        seen = set()
        while value in definitions and value not in seen:
            seen.add(value)
            value = definitions[value]
        policy['maximum'] = int(value) if value and value.isdigit() else None
        caps = re.search(r'enum\s*\{([^}]*POLICYDB_CAPABILITY_[^}]*)\}', code, re.S)
        policy['capabilities'] = re.findall(r'\bPOLICYDB_CAPABILITY_(?!MAX\b)(\w+)\b', caps[1]) if caps else []
        policy['evidence'] = [scan.find(policy_header, r'#define\s+POLICYDB_VERSION_MAX\s+POLICYDB_VERSION_\w+'),
                              scan.find(policy_header, r'#define\s+POLICYDB_VERSION_\w+\s+' + str(policy['maximum']) + r'\b'),
                              scan.find(policy_header, r'POLICYDB_CAPABILITY_\w+')]
        policy['status'] = 'verifiedpresent' if policy['maximum'] is not None and caps else 'tentative'
    policy['note'] = 'Source policy format ceiling and declared capabilities, not Android policy compatibility. A policy-version override does not implement newer formats.'

    dts_root = scan.root / 'arch/arm64/boot/dts'
    actual, mentions = [], []
    if dts_root.is_dir():
        for path in sorted(dts_root.rglob('*')):
            if not path.is_file() or path.is_symlink():
                continue
            relative = path.relative_to(scan.root).as_posix()
            if path.suffix.lower() in ('.dts', '.dtsi'):
                # Filename substring or declared board name; .mk target mentions
                # and unrelated comments are never counted as DTS files.
                if re.search(r'(?:^|[_-])carrera(?:$|[_-])', path.stem, re.I) or scan.find(relative, r'(?:boardname|model|compatible)\s*=\s*"[^"\n]*[Cc][Aa][Rr][Rr][Ee][Rr][Aa]')['matched']:
                    actual.append({'path': relative, 'line': 1})
            elif path.suffix == '.mk' or path.name == 'Makefile':
                evidence = scan.find(relative, r'[^\n]*[Cc][Aa][Rr][Rr][Ee][Rr][Aa][^\n]*\.dtb[^\n]*')
                if evidence['matched']:
                    mentions.append(evidence)
    carrera = {'status': 'verifiedpresent' if actual else ('absent' if dts_root.is_dir() else 'unknown'),
               'actual_source_files': actual, 'makefile_mentions': mentions,
               'note': 'Actual Carrera DTS files are separate from target mentions. Presence does not identify the CRR-L09 board revision or prove the selected DTB is correct.'}
    merge_path = scan.root / 'arch/arm64/configs/merge_hi3635_defconfig'
    delta = {'status': 'unknown', 'evidence': [{'path': str(Path(config).resolve())}, {'path': str(merge_path)}], 'differences': []}
    if merge_path.is_file():
        merge = read_config(merge_path)
        for symbol in sorted(set(cfg) | set(merge)):
            a, b = cfg.get(symbol), merge.get(symbol)
            if (a or {}).get('value') != (b or {}).get('value'):
                delta['differences'].append({'symbol': symbol, 'input': a, 'merge': b})
        delta['status'] = 'verifiedpresent'
    return {'schema_version': 1, 'source': str(scan.root), 'config': str(Path(config).resolve()),
            'scope': 'Offline source evidence only. No build, preprocessor resolution, device execution, or Android boot compatibility conclusion.',
            'checks': checks, 'selinux_policy': policy, 'carrera_dts': carrera,
            'stock_to_merge_config': delta,
            'config_observations': {k: cfg.get(k) for k in ('CONFIG_ARM64', 'CONFIG_COMPAT', 'CONFIG_ANDROID_BINDER_IPC_32BIT', 'CONFIG_ANDROID_BINDER_DEVICES', 'CONFIG_SECCOMP', 'CONFIG_SECCOMP_FILTER', 'CONFIG_MEMCG', 'CONFIG_TMPFS_XATTR', 'CONFIG_DEVPTS_MULTIPLE_INSTANCES')}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path, help='New output directory (must not exist or be inside source)')
    args = parser.parse_args(argv)
    if not args.source.is_dir() or not args.config.is_file():
        parser.error('--source must be a directory and --config a readable file')
    source, out = args.source.resolve(), args.out.resolve()
    if out == source or source in out.parents or out.exists():
        parser.error('--out must be a new directory outside --source')
    try:
        report = audit(source, args.config)
        out.mkdir(parents=True, exist_ok=False)
        target = out / 'kernel-audit.json'
        target.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(str(target))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
