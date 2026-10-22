import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('kernel_audit', Path(__file__).resolve().parents[1] / 'scripts/kernel_audit.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class KernelAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / 'source'
        self.source.mkdir()
        self.config = self.base / 'stock.config'
        self.config.write_text('CONFIG_ARM64=y\nCONFIG_COMPAT=y\nCONFIG_FINGERPRINT=y\n')

    def put(self, relative, text):
        path = self.source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def report(self):
        return module.audit(self.source, self.config)

    def wire_getrandom(self, table=True):
        self.put('drivers/char/random.c', 'SYSCALL_DEFINE3(getrandom, char *, buf, int, n, int, flags) { return 0; }')
        self.put('arch/arm64/kernel/sys.c', 'void *sys_call_table[] = {\n#include <asm/unistd.h>\n};')
        self.put('arch/arm64/include/asm/unistd.h', '#include <uapi/asm/unistd.h>')
        self.put('arch/arm64/include/uapi/asm/unistd.h', '#include <asm-generic/unistd.h>')
        self.put('include/uapi/asm-generic/unistd.h', '#define __NR_getrandom 278\n' + ('__SYSCALL(__NR_getrandom, sys_getrandom)' if table else '// __SYSCALL(__NR_getrandom, sys_getrandom)'))
        self.put('arch/arm64/kernel/sys32.S', 'ENTRY(compat_sys_call_table)\n#include <asm/unistd32.h>')
        self.put('arch/arm64/include/asm/unistd32.h', '#define __NR_getrandom 384\n__SYSCALL(__NR_getrandom, sys_getrandom)')

    def test_implementation_without_active_table_is_not_verified(self):
        self.wire_getrandom(table=False)
        checks = self.report()['checks']
        self.assertEqual(checks['getrandom_arm64']['status'], 'tentative')
        self.assertEqual(checks['getrandom_compat']['status'], 'verifiedpresent')
        self.assertFalse(checks['getrandom_arm64']['evidence'][-1]['matched'])

    def test_wired_syscall_requires_implementation_and_include_chain(self):
        self.wire_getrandom()
        self.assertEqual(self.report()['checks']['getrandom_arm64']['status'], 'verifiedpresent')
        self.put('drivers/char/random.c', '/* SYSCALL_DEFINE3(getrandom, ...) {} */')
        self.assertEqual(self.report()['checks']['getrandom_arm64']['status'], 'tentative')
        (self.source / 'arch/arm64/kernel/sys.c').unlink()
        self.assertEqual(self.report()['checks']['getrandom_arm64']['status'], 'unknown')

    def test_dts_mentions_are_not_source_files_and_prefix_is_not_required(self):
        self.put('arch/arm64/boot/dts/auto-generate/hi3635_dtb.mk', 'dtb-y += hi3635/CARRERA_UL_VN2_config.dtb\n')
        self.put('arch/arm64/boot/dts/auto-generate/GRACE.dts', '/* CARRERA */\n/model/ {};')
        result = self.report()['carrera_dts']
        self.assertEqual(result['status'], 'absent')
        self.assertEqual(len(result['makefile_mentions']), 1)
        self.put('arch/arm64/boot/dts/auto-generate/vendor-hi3635-CARRERA_UL.dts', '/dts-v1/;')
        self.put('arch/arm64/boot/dts/board.dtsi', 'hisi,boardname = "CARRERA_UL";')
        self.assertEqual(len(self.report()['carrera_dts']['actual_source_files']), 2)

    def test_policy_ceiling_and_config_delta(self):
        self.put('security/selinux/include/security.h', '#define POLICYDB_VERSION_XPERMS_IOCTL 30\n#ifdef CONFIG_CUSTOM\n#define POLICYDB_VERSION_MAX CONFIG_CUSTOM\n#else\n#define POLICYDB_VERSION_MAX POLICYDB_VERSION_XPERMS_IOCTL\n#endif\nenum { POLICYDB_CAPABILITY_NETPEER, POLICYDB_CAPABILITY_OPENPERM, __POLICYDB_CAPABILITY_MAX };')
        self.put('arch/arm64/configs/merge_hi3635_defconfig', 'CONFIG_ARM64=y\nCONFIG_COMPAT=y\n# CONFIG_FINGERPRINT is not set\n')
        report = self.report()
        self.assertEqual(report['selinux_policy']['maximum'], 30)
        self.assertEqual(report['selinux_policy']['capabilities'], ['NETPEER', 'OPENPERM'])
        self.assertEqual(report['stock_to_merge_config']['differences'][0]['symbol'], 'CONFIG_FINGERPRINT')

    def test_output_directory_is_new_and_inputs_unchanged(self):
        original = self.config.read_bytes()
        out = self.base / 'result'
        module.main(['--source', str(self.source), '--config', str(self.config), '--out', str(out)])
        self.assertEqual(json.loads((out / 'kernel-audit.json').read_text())['schema_version'], 1)
        self.assertEqual(self.config.read_bytes(), original)
        with self.assertRaises(SystemExit):
            module.main(['--source', str(self.source), '--config', str(self.config), '--out', str(out)])
        with self.assertRaises(SystemExit):
            module.main(['--source', str(self.source), '--config', str(self.config), '--out', str(self.source / 'output')])

    def test_binder_header_and_kconfig_do_not_prove_driver_support(self):
        self.put('include/uapi/linux/android/binder.h', '#define BINDER_SET_CONTEXT_MGR_EXT 123\nBC_TRANSACTION_SG = 17, BC_REPLY_SG = 18')
        self.put('drivers/android/binder.c', '/* case BINDER_SET_CONTEXT_MGR_EXT: */\n')
        checks = self.report()['checks']
        self.assertEqual(checks['binder_context_manager_ext']['status'], 'tentative')
        self.assertEqual(checks['binder_scatter_gather']['status'], 'tentative')

    def test_tsync_flag_does_not_prove_implementation(self):
        self.put('include/uapi/linux/seccomp.h', '#define SECCOMP_FILTER_FLAG_TSYNC 1')
        self.put('kernel/seccomp.c', 'int something_else(void) { return 0; }')
        self.put('arch/arm64/kernel/ptrace.c', 'if (secure_computing(regs->syscallno) == -1) return -1;')
        self.put('arch/arm64/include/asm/thread_info.h', '#define _TIF_SYSCALL_WORK (_TIF_SECCOMP)')
        self.assertEqual(self.report()['checks']['seccomp_tsync']['status'], 'tentative')

    def test_comments_preserve_evidence_lines(self):
        self.put('sample.c', '/* ignored\nSYSCALL_DEFINE3(getrandom, ignored)\n*/\nactual();\n')
        evidence = module.Inspector(self.source).find('sample.c', r'actual\(')
        self.assertEqual(evidence['line'], 4)
        self.assertFalse(module.Inspector(self.source).find('sample.c', r'SYSCALL_DEFINE')['matched'])


if __name__ == '__main__':
    unittest.main()
