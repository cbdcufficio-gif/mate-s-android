#!/usr/bin/env python3
"""Hydrate only Q's ARM WebView LFS inputs on disposable public CI."""
import hashlib
import os
from pathlib import Path
import re
import subprocess
import zipfile
from android_graph_probe import ROOT, guarded

ARCHES = ('arm', 'arm64')
POINTER = re.compile(r'version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize ([0-9]+)\n?')


def parse_pointer(data):
    match = POINTER.fullmatch(data.decode('ascii'))
    if not match or int(match[2]) <= 0:
        raise ValueError('Invalid WebView LFS pointer')
    return match[1], int(match[2])


def verify_apk(path, digest, size):
    if path.is_symlink() or not path.is_file() or path.stat().st_size != size:
        raise ValueError('WebView APK size/type differs from Git LFS pointer')
    actual = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            actual.update(block)
    if actual.hexdigest() != digest:
        raise ValueError('WebView APK SHA256 differs from Git LFS pointer')
    with zipfile.ZipFile(path) as apk:
        if 'AndroidManifest.xml' not in apk.namelist() or apk.testzip() is not None:
            raise ValueError('Invalid WebView APK contents/CRC')
    return {'bytes': size, 'sha256': digest, 'zip_crc_verified': True}


def prepare_webview(source):
    if os.environ.get('GITHUB_ACTIONS') != 'true' or os.environ.get('RUNNER_ENVIRONMENT') != 'github-hosted':
        raise ValueError('WebView download is limited to disposable public CI')
    result = []
    for arch in ARCHES:
        repo = source / 'external/chromium-webview/prebuilt' / arch
        # Read the committed pointer, not a mutable URL or guessed APK version.
        blob_size = int(subprocess.check_output(['git', 'cat-file', '-s', 'HEAD:webview.apk'], cwd=repo))
        if blob_size > 1024:
            raise ValueError('WebView input is no longer an LFS pointer; review upstream layout')
        pointer = subprocess.check_output(['git', 'show', 'HEAD:webview.apk'], cwd=repo)
        digest, size = parse_pointer(pointer)
        run = guarded(['git', 'lfs', 'pull', '--include=webview.apk', '--exclude='],
                      repo, ROOT / ('webview-lfs-' + arch + '.log'), seconds=300, reserve=20*1024**3)
        if run['returncode'] or run['stop_reason']:
            raise ValueError('WebView LFS download failed for ' + arch + ': ' + str(run))
        item = verify_apk(repo / 'webview.apk', digest, size)
        item.update(arch=arch, source_commit=subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip(), download=run)
        result.append(item)
    return result
