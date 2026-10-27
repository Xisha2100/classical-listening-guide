"""Portable backups without API secrets; restore only into an empty directory."""
import argparse,tarfile
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[2]
def create(target):
 target=Path(target).resolve()
 if target.exists():raise ValueError('备份文件已存在，请换一个名称')
 if target.suffixes[-2:]!=['.tar','.gz']:raise ValueError('备份文件使用 .tar.gz 扩展名')
 if any(target.is_relative_to(ROOT/name) for name in ('assets','作品')):raise ValueError('备份请放在资料目录之外')
 with tarfile.open(target,'w:gz') as archive:
  for name in ('assets','作品'):
   if (ROOT/name).exists():archive.add(ROOT/name,arcname=name,filter=lambda info:info if info.isfile() or info.isdir() else None)
 print(target)
def restore(source,destination):
 dest=Path(destination).resolve()
 if dest.exists() and any(dest.iterdir()):raise ValueError('恢复目标必须为空目录，避免覆盖现有笔记')
 with tarfile.open(source,'r:gz') as archive:
  members=archive.getmembers()
  for m in members:
   p=PurePosixPath(m.name)
   if p.is_absolute() or '..' in p.parts or not p.parts or p.parts[0] not in ('assets','作品') or not (m.isfile() or m.isdir()):raise ValueError('备份包含不安全或非资料文件')
  dest.mkdir(parents=True,exist_ok=True)
  archive.extractall(dest,members=members,filter='data')
 print(dest)
if __name__=='__main__':
 parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='action',required=True)
 c=sub.add_parser('create');c.add_argument('archive')
 r=sub.add_parser('restore');r.add_argument('archive');r.add_argument('--into',required=True)
 args=parser.parse_args()
 if args.action=='create':create(args.archive)
 else:restore(args.archive,args.into)
