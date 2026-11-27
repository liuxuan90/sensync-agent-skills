#!/usr/bin/env python3
"""Build reproducible release checksums after reviewing the actual change types."""
import argparse,hashlib,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SKILL=ROOT/'skills/sensync-lead-intelligence'

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--change-types',required=True)
 p.add_argument('--review-required',action='store_true')
 a=p.parse_args()
 changes=[s.strip() for s in a.change_types.split(',') if s.strip()]
 if not changes:raise ValueError('Specify actual change types')
 important={'scripts','permissions','dependencies','workflow','schema','qualification'}
 if important.intersection(changes) and not a.review_required:raise ValueError('Sensitive change types require --review-required')
 text=(SKILL/'SKILL.md').read_text(encoding='utf-8')
 match=re.search(r'(?m)^\s*version:\s*(\d+\.\d+\.\d+)\s*$',text)
 if not match:raise ValueError('Missing version')
 files={}
 for path in sorted(SKILL.rglob('*')):
  if path.is_symlink():raise ValueError('No package symlinks')
  if path.is_file() and path.name!='release-manifest.json' and '__pycache__' not in path.parts:
   if path.suffix in {'.md','.json','.py','.yaml','.yml','.txt'}:
    data=path.read_bytes()
    normalized=data.replace(b'\r\n',b'\n')
    if data!=normalized:path.write_bytes(normalized)
   files[path.relative_to(SKILL).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
 payload={'skill':'sensync-lead-intelligence','version':match.group(1),'source_repo':'liuxuan90/sensync-agent-skills','source_ref':'stable','source_path':'skills/sensync-lead-intelligence','change_types':changes,'review_before_update':a.review_required,'files':files}
 (SKILL/'release-manifest.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
 print('MANIFEST_FILES:',len(files),'VERSION:',match.group(1))

if __name__=='__main__':main()
