#!/usr/bin/env python3
"""Resolve public manifest refs without cloning Android; no build or device access."""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from remote_preflight import BASE, COMMIT, LIMIT, inspect_manifest


def project_url(fetch, name):
    # repo resolves fetch relative to the manifest repository URL, not a directory.
    base=urllib.parse.urljoin('https://github.com/LineageOS/android',fetch.rstrip('/')+'/')
    return base.rstrip('/')+'/'+name


def resolve_ref(url, revision):
    if re.fullmatch(r'[0-9a-fA-F]{40}', revision):
        return revision.lower()
    if revision.startswith('refs/'):
        refs = [revision, revision+'^{}']
    else:
        refs = ['refs/heads/'+revision, 'refs/tags/'+revision, 'refs/tags/'+revision+'^{}']
    result = subprocess.run(['git','ls-remote','--exit-code',url,*refs],check=True,
                            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=45,
                            env={**os.environ,'GIT_TERMINAL_PROMPT':'0'})
    return select_revision(result.stdout, revision)


def select_revision(output, revision):
    rows = dict((ref,sha) for sha,ref in (line.split() for line in output.splitlines()))
    candidates = [revision] if revision.startswith('refs/') else ['refs/heads/'+revision,'refs/tags/'+revision]
    matches = [rows.get(ref+'^{}',rows[ref]) for ref in candidates if ref in rows]
    if len(matches)!=1 or not re.fullmatch('[0-9a-fA-F]{40}',matches[0]):
        raise ValueError('Missing, ambiguous or invalid revision: '+revision)
    return matches[0].lower()


def main():
    if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('RUNNER_ENVIRONMENT')!='github-hosted':
        raise SystemExit('Public disposable runner only')
    output=Path('out/manifest-lock');output.mkdir(parents=True,exist_ok=False)
    documents={}
    def fetch(name):
        with urllib.request.urlopen(BASE+name,timeout=30) as stream:
            data=stream.read(LIMIT+1)
        documents[name]=data
        return data
    inventory=inspect_manifest(fetch)
    root=ET.Element('manifest')
    def flatten(name):
        for child in ET.fromstring(documents[name]):
            if child.tag=='include': flatten(child.attrib['name'])
            else: root.append(child)
    flatten('default.xml')
    projects=inventory['projects']
    nodes={node.get('path',node.attrib['name']):node for node in root.findall('project')}
    def lock(project):
        remote=inventory['remotes'][project['remote']]
        url=project_url(remote['fetch'],project['name'])
        if not url.startswith('https://') or urllib.parse.urlsplit(url).hostname not in ('github.com','android.googlesource.com','gitlab.com'):
            raise ValueError('Unreviewed public remote: '+url)
        sha=resolve_ref(url,project['revision'])
        return project,sha
    report={'manifest_commit':COMMIT,'status':'RESOLVING','source_downloaded':False,
            'android_built':False,'project_count':len(projects),'documents':inventory['documents']}
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            for project,sha in pool.map(lock,projects):
                nodes[project['path']].set('revision',sha)
        ET.indent(root)
        manifest=ET.tostring(root,encoding='utf-8',xml_declaration=True)+b'\n'
        (output/'resolved-manifest.xml').write_bytes(manifest)
        report.update(status='PUBLIC_MANIFEST_REFS_LOCKED',sha256=hashlib.sha256(manifest).hexdigest(),
                      limitation='Refs resolved during a time interval, not an atomic upstream snapshot; source availability and builds not verified')
    except Exception as error:
        report.update(status='MANIFEST_LOCK_FAILED',error=str(error))
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    (output/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in sorted(output.iterdir())))
    print(json.dumps(report,indent=2))
    return 0 if report['status']=='PUBLIC_MANIFEST_REFS_LOCKED' else 1


if __name__=='__main__':raise SystemExit(main())
