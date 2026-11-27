#!/usr/bin/env python3
"""Explicit Sensync Skill verification, stable updates and recoverable rollback."""
from __future__ import annotations
import argparse, base64, hashlib, io, json, os, re, shutil, sys, tempfile, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath

NAME='sensync-lead-intelligence'
REPO='liuxuan90/sensync-agent-skills'
REF='stable'
SOURCE='skills/'+NAME
MANIFEST='release-manifest.json'
ROOT=Path(__file__).resolve().parents[1]
LIMIT=25*1024*1024

def version(v):
    if not isinstance(v,str) or not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)',v):
        raise ValueError('Invalid semantic version')
    return tuple(map(int,v.split('.')))

def safe_name(name):
    if not isinstance(name,str) or not name or '\\' in name or ':' in name or '\x00' in name:
        raise ValueError('Unsafe package path')
    p=PurePosixPath(name)
    if p.is_absolute() or PureWindowsPath(name).is_absolute() or any(x in ('','.','..') for x in name.split('/')):
        raise ValueError('Unsafe package path')
    if any(x.endswith((' ','.')) or x.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*(f'COM{i}' for i in range(1,10)),*(f'LPT{i}' for i in range(1,10))} for x in p.parts):
        raise ValueError('Unsafe cross-platform package path')
    return p

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8'))

def files(root):
    out={}
    for p in root.rglob('*'):
        rel=p.relative_to(root)
        if p.is_symlink():raise ValueError('Symlinks are not package files')
        if '__pycache__' in rel.parts:continue
        if p.is_file() and rel.as_posix()!=MANIFEST:out[rel.as_posix()]=p
    return out

def verify(root):
    m=read(root/MANIFEST)
    for key,val in {'skill':NAME,'source_repo':REPO,'source_ref':REF,'source_path':SOURCE}.items():
        if m.get(key)!=val:raise ValueError('Manifest trusted source mismatch: '+key)
    version(m.get('version'))
    if not isinstance(m.get('review_before_update'),bool) or not isinstance(m.get('change_types'),list):
        raise ValueError('Invalid review metadata')
    expected=m.get('files')
    if not isinstance(expected,dict) or not expected:raise ValueError('Missing manifest files')
    folded=set()
    for name,sha in expected.items():
        safe_name(name)
        if name==MANIFEST or name.casefold() in folded:raise ValueError('Duplicate/unsafe file entry')
        folded.add(name.casefold())
        if not isinstance(sha,str) or not re.fullmatch('[0-9a-f]{64}',sha):raise ValueError('Invalid checksum')
    actual=files(root)
    if set(actual)!=set(expected):raise ValueError('Package has missing or unexpected files')
    for name,p in actual.items():
        if digest(p)!=expected[name]:raise ValueError('Checksum mismatch: '+name)
    match=re.search(r'(?m)^\s*version:\s*([0-9]+\.[0-9]+\.[0-9]+)\s*$',(root/'SKILL.md').read_text(encoding='utf-8'))
    if not match or match.group(1)!=m['version']:raise ValueError('SKILL/manifest version mismatch')
    return m

def fetch(url,accept='application/octet-stream'):
    req=urllib.request.Request(url,headers={'User-Agent':'Sensync-Skill-Updater/1.0','Accept':accept})
    with urllib.request.urlopen(req,timeout=30) as r:data=r.read(LIMIT+1)
    if len(data)>LIMIT:raise ValueError('Download limit exceeded')
    return data

def remote():
    commit=json.loads(fetch(f'https://api.github.com/repos/{REPO}/commits/{REF}','application/vnd.github+json'))['sha']
    if not re.fullmatch('[0-9a-f]{40}',commit):raise ValueError('Invalid stable commit')
    payload=json.loads(fetch(f'https://api.github.com/repos/{REPO}/contents/{SOURCE}/{MANIFEST}?ref={commit}','application/vnd.github+json'))
    if payload.get('encoding')!='base64':raise ValueError('Unexpected manifest encoding')
    m=json.loads(base64.b64decode(payload['content'],validate=False))
    for k,v in {'skill':NAME,'source_repo':REPO,'source_ref':REF,'source_path':SOURCE}.items():
        if m.get(k)!=v:raise ValueError('Remote source mismatch')
    version(m.get('version'))
    if not isinstance(m.get('files'),dict) or not isinstance(m.get('review_before_update'),bool):raise ValueError('Invalid remote manifest')
    for n in m['files']:safe_name(n)
    return commit,m

def changes(local,remote_m):
    old=local.get('files',{}) if local else {}
    new=remote_m['files']
    return sorted(n for n in set(old)|set(new) if old.get(n)!=new.get(n))

def needs_review(local,m):
    sensitive={'SKILL.md','references/qualification-and-scoring.md','references/product-playbooks.md','references/evidence-policy.md','references/contact-email-policy.md','references/first-email-policy.md','references/workbook-schema.md','references/maintenance.md'}
    return bool(m.get('review_before_update')) or any(n in sensitive or n.startswith(('scripts/','agents/')) or n.endswith('.schema.json') for n in changes(local,m))

def unpack(data,dest):
    used=set(); total=0
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for item in z.infolist():
            parts=PurePosixPath(item.filename).parts
            prefix=PurePosixPath(SOURCE).parts
            if len(parts)<=len(prefix)+1 or tuple(parts[1:1+len(prefix)])!=prefix:continue
            name='/'.join(parts[1+len(prefix):])
            if item.is_dir():
                safe_name(name.rstrip('/'));continue
            rel=safe_name(name)
            if name.casefold() in used:raise ValueError('Duplicate archive entry')
            used.add(name.casefold())
            if (item.external_attr>>16)&0o170000==0o120000:raise ValueError('Archive symlink rejected')
            total+=item.file_size
            if total>LIMIT:raise ValueError('Expanded package limit exceeded')
            p=dest.joinpath(*rel.parts);p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(z.read(item))

def activate(staged,target,backup,simulate_failure=False):
    moved=False; installed=False
    try:
        if target.exists():os.replace(target,backup);moved=True
        if simulate_failure:raise RuntimeError('Simulated activation failure')
        os.replace(staged,target);installed=True
        verify(target)
    except Exception:
        if installed and target.exists():shutil.rmtree(target)
        if moved:os.replace(backup,target)
        raise

def target_ok(target):
    if target.name!=NAME or target.is_symlink():raise ValueError('Target must be the real Sensync Skill folder')
    return target.resolve()

def stamp():return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')

def perform(action,target,accept=False,backup_name=None):
    target=target_ok(target)
    if action=='verify':
        print('VERIFIED_VERSION:',verify(target)['version']);return
    backup_root=target.parent/'.sensync-skill-backups'
    if action=='backups':
        for p in sorted(backup_root.glob(NAME+'-*')):print(p.name)
        return
    if action=='rollback':
        if not backup_name or Path(backup_name).name!=backup_name or not backup_name.startswith(NAME+'-'):raise ValueError('Choose a listed backup name')
        chosen=backup_root/backup_name
        if chosen.is_symlink() or chosen.resolve().parent!=backup_root.resolve():raise ValueError('Invalid backup path')
        verify(chosen);current=verify(target)
        with tempfile.TemporaryDirectory(prefix='sensync-rollback-',dir=target.parent) as temp:
            staged=Path(temp)/'staged';shutil.copytree(chosen,staged)
            os.chdir(target.parent)
            activate(staged,target,backup_root/f'{NAME}-{current["version"]}-{stamp()}')
        print('ROLLED_BACK_VERSION:',verify(target)['version']);return
    local=verify(target) if target.exists() else None
    commit,m=remote();diff=changes(local,m)
    review=needs_review(local,m)
    print('INSTALLED_VERSION:',local['version'] if local else 'not-installed')
    print('STABLE_VERSION:',m['version']);print('STABLE_COMMIT:',commit)
    print('CHANGED_FILES:',', '.join(diff) or 'none')
    print('REVIEW_BEFORE_UPDATE:','YES' if review else 'NO')
    if action=='check':
        print('UPDATE_AVAILABLE:','YES' if not local or version(m['version'])>version(local['version']) else 'NO');return
    if local and version(m['version'])<version(local['version']):raise ValueError('Downgrade refused; use a verified backup rollback')
    if local and version(m['version'])==version(local['version']):
        if diff:raise ValueError('Same-version package differs; publish a new version')
        print('ALREADY_CURRENT:',m['version']);return
    if review and not accept:raise ValueError('Review changed files, then use --accept-reviewed-changes within authorization')
    target.parent.mkdir(parents=True,exist_ok=True);backup_root.mkdir(exist_ok=True)
    os.chdir(target.parent)
    with tempfile.TemporaryDirectory(prefix='sensync-update-',dir=target.parent) as temp:
        staged=Path(temp)/'staged';staged.mkdir()
        unpack(fetch(f'https://codeload.github.com/{REPO}/zip/{commit}'),staged)
        downloaded=verify(staged)
        if downloaded!=m:raise ValueError('Manifest/package mismatch')
        backup=backup_root/f'{NAME}-{local["version"] if local else "fresh"}-{stamp()}'
        activate(staged,target,backup)
    print('UPDATED_VERSION:',m['version']);print('RELOAD_REQUIRED: refresh Skill index or start a new conversation')

def self_test():
    for invalid in ('../outside','C:/outside','a\\b','/absolute','a/../b','a//b','CON.txt','a:stream'):
        try:safe_name(invalid)
        except ValueError:pass
        else:raise AssertionError('Unsafe path accepted')
    verify(ROOT)
    with tempfile.TemporaryDirectory(prefix='sensync-self-test-') as tmp:
        r=Path(tmp);target=r/NAME;staged=r/'staged';backup=r/'backup'
        shutil.copytree(ROOT,target,ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copytree(ROOT,staged,ignore=shutil.ignore_patterns('__pycache__'))
        before=digest(target/'SKILL.md')
        try:activate(staged,target,backup,simulate_failure=True)
        except RuntimeError:pass
        else:raise AssertionError('Failure simulation did not fail')
        assert digest(target/'SKILL.md')==before;verify(target)
        activate(staged,target,backup);verify(target);verify(backup)
        corrupt=r/'corrupt';shutil.copytree(ROOT,corrupt,ignore=shutil.ignore_patterns('__pycache__'))
        with (corrupt/'SKILL.md').open('a',encoding='utf-8') as f:f.write('\ncorruption\n')
        try:activate(corrupt,target,r/'backup2')
        except ValueError:pass
        else:raise AssertionError('Corrupt activation accepted')
        verify(target)
        old={'files':{'scripts/change.py':'old'}};new={'files':{'scripts/change.py':'new'},'review_before_update':False}
        assert needs_review(old,new)
    print('SELF_TEST_OK: package, paths, review detection, activation and recovery')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['verify','check','update','backups','rollback','self-test'])
    p.add_argument('--target',type=Path,default=ROOT)
    p.add_argument('--accept-reviewed-changes',action='store_true')
    p.add_argument('--backup')
    a=p.parse_args()
    try:
        if a.action=='self-test':self_test()
        else:perform(a.action,a.target,a.accept_reviewed_changes,a.backup)
    except Exception as e:
        print('FAILED:',type(e).__name__,str(e),file=sys.stderr);return 1
    return 0

if __name__=='__main__':raise SystemExit(main())
