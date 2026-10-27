import importlib.util,tarfile,io
from pathlib import Path
import pytest
from conftest import ROOT
spec=importlib.util.spec_from_file_location('backup',ROOT/'app/scripts/backup.py')
backup=importlib.util.module_from_spec(spec);spec.loader.exec_module(backup)

def test_backup_roundtrip_no_secrets(tmp_path,monkeypatch):
 root=tmp_path/'root';(root/'assets').mkdir(parents=True);(root/'作品').mkdir();(root/'app').mkdir()
 (root/'assets/catalog.json').write_text('[]');(root/'作品/笔记.md').write_text('# 笔记\n原文')
 (root/'app/.env').write_text('SECRET=private')
 monkeypatch.setattr(backup,'ROOT',root)
 archive=tmp_path/'copy.tar.gz';backup.create(archive);out=tmp_path/'restored';backup.restore(archive,out)
 assert (out/'作品/笔记.md').read_text()=='# 笔记\n原文' and not (out/'app/.env').exists()
 with pytest.raises(ValueError):backup.restore(archive,out)

def test_restore_rejects_traversal(tmp_path):
 archive=tmp_path/'bad.tar.gz'
 with tarfile.open(archive,'w:gz') as t:
  info=tarfile.TarInfo('../escape');info.size=1;t.addfile(info,io.BytesIO(b'x'))
 with pytest.raises(ValueError):backup.restore(archive,tmp_path/'dest')
 assert not (tmp_path/'escape').exists()
