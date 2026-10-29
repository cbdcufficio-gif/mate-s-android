"""Static class/permission comparison; userspace-only classes are kept separate."""
import re
USERSPACE={'property_service','service_manager','hwservice_manager','keystore_key','drmservice'}

def parse_setools(text,kind):
    result={};parts=re.split(r'^\s*'+kind+r'\s+(\w+)\s*$',text,flags=re.M)
    for i in range(1,len(parts),2):
        name,body=parts[i:i+2];inherit=re.search(r'^inherits\s+(\w+)',body,re.M);block=re.search(r'\{(.*?)\}',body,re.S)
        result[name]={'inherits':inherit[1] if inherit else None,'permissions':set(re.findall(r'\b[a-z][a-z0-9_]*\b',block[1])) if block else set()}
    if not result:raise ValueError('No parsed '+kind+' inventory')
    return result

def compare(class_text,common_text,expanded_kernel):
    classes=parse_setools(class_text,'class');commons=parse_setools(common_text,'common')
    kernel={name:set(re.findall(r'"([a-z0-9_]+)"',body)) for name,body in re.findall(r'\{\s*"([a-z0-9_]+)"\s*,\s*\{(.*?)\}\s*\}',expanded_kernel,re.S)}
    if not kernel:raise ValueError('No expanded kernel classmap')
    missing={};userspace=[];unmapped=[]
    for name,row in classes.items():
        perms=set(row['permissions'])
        if row['inherits']:
            if row['inherits'] not in commons:raise ValueError('Missing inherited common '+row['inherits'])
            perms|=commons[row['inherits']]['permissions']
        if name in USERSPACE:userspace.append(name)
        elif name not in kernel:unmapped.append(name)
        elif perms-kernel[name]:missing[name]=sorted(perms-kernel[name])
    return {'status':'STATIC_POLICY_CLASS_PERMISSION_INVENTORY','policy_class_count':len(classes),'kernel_class_count':len(kernel),'userspace_classes_separated':sorted(userspace),'policy_classes_without_kernel_mapping':sorted(unmapped),'permissions_absent_from_mapped_kernel_classes':missing,'limitations':['Unmapped classes may relate to disabled features; absence alone does not imply policy-load failure','Names do not prove hook semantics, allow/deny outcomes or enforcing compatibility']}
