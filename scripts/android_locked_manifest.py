"""Install reviewed public lock and compare actual synced project revisions."""
import hashlib
from pathlib import Path
import re
import xml.etree.ElementTree as ET
LOCK=Path(__file__).resolve().parents[1]/'configs/android-resolved-manifest.xml'
DIGEST='b30f6d479b321cab00305b1c9a31450d0a8940138996e7e25cf27f7a0146f845'

def project_revisions(data):
    if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():raise ValueError('Forbidden manifest entity')
    root=ET.fromstring(data)
    if root.tag!='manifest' or root.findall('include'):raise ValueError('Expected flattened manifest')
    projects={}
    for node in root.findall('project'):
        path=node.get('path',node.attrib['name']);revision=node.get('revision','')
        if path in projects or not re.fullmatch('[0-9a-f]{40}',revision):raise ValueError('Duplicate or unpinned project')
        projects[path]=revision
    if not projects:raise ValueError('Empty manifest')
    return projects

def install_lock(tree):
    data=LOCK.read_bytes()
    if hashlib.sha256(data).hexdigest()!=DIGEST:raise ValueError('Reviewed manifest digest mismatch')
    projects=project_revisions(data)
    # repo init links/includes default.xml in its manifest checkout.
    destination=tree/'.repo/manifests/default.xml'
    if destination.is_symlink() or not destination.is_file():raise ValueError('Unexpected manifest location')
    destination.write_bytes(data)
    return {'sha256':DIGEST,'locked_projects':len(projects)}

def verify_synced(data):
    expected=project_revisions(LOCK.read_bytes());actual=project_revisions(data)
    # repo exports only groups selected by init (default,-darwin).
    root=ET.fromstring(LOCK.read_bytes())
    selected={node.get('path',node.attrib['name']) for node in root.findall('project')
              if not set(node.get('groups','').split(',')) & {'notdefault','darwin'}}
    if set(actual)!=selected:raise ValueError('Synced project selection differs from default,-darwin')
    for path,sha in actual.items():
        if expected.get(path)!=sha:raise ValueError('Synced revision differs: '+path)
    return {'status':'SYNCED_REVISIONS_MATCH_LOCK','selected_projects':len(actual),'locked_projects':len(expected)}
