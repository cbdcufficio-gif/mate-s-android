"""Inspect the fixed public G0 SELinux header, without loading policy."""
import hashlib,struct
MAGIC=0xf97cff8c
POLICY_STRING=b'SE Linux'
MLS=1
REJECT_UNKNOWN=2
ALLOW_UNKNOWN=4
G0_SHA256='e450f2631168a9653694ce84f9882d86dbc6b9d16ff57b6049d5870102cdbe9f'

def parse_header(data):
    if len(data)<8:raise ValueError('Truncated policy header')
    magic,length=struct.unpack_from('<II',data)
    if magic!=MAGIC or length!=len(POLICY_STRING):raise ValueError('Invalid policy magic or identifier length')
    offset=8+length
    if len(data)<offset+16 or data[8:offset]!=POLICY_STRING:raise ValueError('Invalid or truncated policy identifier')
    version,config,sym_num,ocon_num=struct.unpack_from('<IIII',data,offset)
    return {'version':version,'config':config,'mls':bool(config&MLS),'reject_unknown':bool(config&REJECT_UNKNOWN),'allow_unknown':bool(config&ALLOW_UNKNOWN),'other_config_bits':config&~(MLS|REJECT_UNKNOWN|ALLOW_UNKNOWN),'symbol_tables':sym_num,'object_context_tables':ocon_num}

def inspect_g0(data):
    digest=hashlib.sha256(data).hexdigest()
    if digest!=G0_SHA256:raise ValueError('G0 policy digest mismatch')
    result=parse_header(data)
    if result['version']!=30:raise ValueError('Unexpected G0 policy version')
    return {'policy_sha256':digest,'header':result,'runtime_policy_loaded':False}
