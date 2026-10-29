"""Compare version-name requirements from captured readelf output, without execution."""
import re

def version_names(text):
    mode=None;provider=None;definitions=set();needs={}
    for line in text.splitlines():
        if line.startswith('Version definition section'):mode='definitions'
        elif line.startswith('Version needs section'):mode='needs'
        elif line.startswith('Version symbols section'):mode=None
        if mode=='needs':
            file=re.search(r'File:\s+(\S+)',line)
            if file:provider=file[1];needs.setdefault(provider,set())
        name=re.search(r'\bName:\s+(\S+)',line)
        if name and mode=='definitions':definitions.add(name[1])
        elif name and mode=='needs' and provider:needs[provider].add(name[1])
    return definitions,needs

def compare(matrix):
    physical={row['physical']:row for row in matrix};edges=[];unresolved=[]
    for row in matrix:
        _,needs=version_names(row['version_info'])
        for dep in row['dependencies']:
            required=needs.get(dep['needed'],set());candidates=dep['candidates']
            if not candidates:continue
            candidate=candidates[0];provider=physical.get(candidate['physical'])
            if provider is None:
                unresolved.append({'consumer':row['guest'],'needed':dep['needed'],'reason':'provider version inventory missing'});continue
            defined,_=version_names(provider['version_info']);missing=required-defined
            item={'consumer':row['guest'],'needed':dep['needed'],'provider':candidate['physical'],'required':sorted(required),'missing':sorted(missing)};edges.append(item)
            if missing:unresolved.append(item)
    return {'status':'STATIC_ELF_VERSION_NAMES_MATCH_CANDIDATES' if not unresolved else 'STATIC_ELF_VERSION_BLOCKERS','edges_checked':len(edges),'versioned_edges':sum(bool(x['required']) for x in edges),'unresolved':unresolved,'limitations':['Only recorded candidate providers, not live linker namespace selection','Version names do not prove every imported symbol exists, dlopen behavior or hardware ABI']}
