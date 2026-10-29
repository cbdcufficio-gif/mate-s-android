#!/usr/bin/env python3
"""Execute all public fixtures; missing prerequisites must not masquerade as green CI."""
import json
import os
from pathlib import Path
import shutil
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ('cc', 'mke2fs', 'debugfs', 'img2simg', 'simg2img', 'patchelf',
         'arm-linux-gnueabihf-gcc', 'aarch64-linux-gnu-gcc')

def main():
    os.environ['PATH'] = os.environ.get('PATH', '') + ':/usr/sbin:/sbin'
    missing = [tool for tool in TOOLS if not shutil.which(tool)]
    if missing:
        print('Missing fixture prerequisites: ' + ', '.join(missing), file=sys.stderr)
        return 2
    os.environ['MATES_TEST_CC_ARM'] = shutil.which('arm-linux-gnueabihf-gcc')
    os.environ['MATES_TEST_CC_ARM64'] = shutil.which('aarch64-linux-gnu-gcc')
    os.environ['MATES_PATCHELF'] = shutil.which('patchelf')
    suite = unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {'run': result.testsRun, 'passed': result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped)-len(result.expectedFailures)-len(result.unexpectedSuccesses),
              'skipped': [{'test': str(t), 'reason': reason} for t, reason in result.skipped],
              'failures': len(result.failures), 'errors': len(result.errors),
              'expected_failures':len(result.expectedFailures),'unexpected_successes':len(result.unexpectedSuccesses),
              'tools': {tool: shutil.which(tool) for tool in TOOLS},
              'hardware_verified': False}
    print(json.dumps(report, indent=2))
    return 0 if result.wasSuccessful() and not result.skipped and not result.expectedFailures else 1

if __name__ == '__main__':
    sys.exit(main())
