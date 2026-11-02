"""Bounded inventory of public init scripts; never executes guest commands."""
import hashlib
import posixpath
import re

ROOTS = ('/', '/system/etc/init', '/product/etc/init',
         '/product_services/etc/init', '/odm/etc/init', '/vendor/etc/init')

def capture(image):
    pending = list(ROOTS)
    seen = set()
    files = []
    unresolved = []
    total = 0
    while pending:
        directory = pending.pop(0)
        if directory in seen:
            continue
        seen.add(directory)
        if len(seen) > 256:
            raise ValueError('Init directory budget exceeded')
        node = image.stat(directory)
        if node['type'] != 'directory':
            unresolved.append({'path': directory, 'type': node['type']})
            continue
        for line in image.command('ls -p ' + directory).splitlines():
            if not line.startswith('/'):
                continue
            fields = line.split('/')
            if len(fields) < 7:
                raise ValueError('Malformed debugfs listing')
            name = fields[5]
            if name in ('.', '..'):
                continue
            if not re.fullmatch(r'[A-Za-z0-9_.+@-]+', name):
                raise ValueError('Unsafe init inventory entry')
            path = posixpath.join(directory, name)
            if directory == '/' and not name.endswith('.rc'):
                continue
            kind = image.stat(path)['type']
            if kind == 'directory':
                pending.append(path)
            elif kind == 'symlink':
                unresolved.append({'path': path, 'type': kind})
            elif name.endswith('.rc') and kind == 'regular':
                data = image.read(path).read_bytes()
                total += len(data)
                if len(data) > 1024 * 1024 or total > 8 * 1024 * 1024 or len(files) >= 1024:
                    raise ValueError('Init script budget exceeded')
                files.append({'path': path, 'sha256': hashlib.sha256(data).hexdigest(),
                              'text': data.decode('utf-8')})
    return {'status': 'PUBLIC_INIT_SCRIPT_INVENTORY', 'files': files,
            'unresolved': unresolved, 'runtime_imports_resolved': False,
            'limitations': ['Inventory only; property expansion, parser and runtime not executed',
                            'Missing directories and symlinks require explicit review']}
