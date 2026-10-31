from fastapi.testclient import TestClient
from backend.main import create_app
from backend.models import Analysis,Source,Segment
from backend.store import Store
from backend.scores import validate_segment

def test_markdown_roundtrip_and_rebuild(store):
 idx=store.events('test-work')
 seg=validate_segment(Segment(score_version=idx['version'],start=0,end=2),idx)
 a=Analysis(work_id='test-work',title='我的主题',body='第一段。\n\n---\n保留分隔线。',sources=[Source(id='book',title='导听书',pages='12—13',excerpt='原文 --- 原样保存')],segments=[seg])
 saved=store.save(a)
 store.db.unlink()
 reopened=Store(store.root).get_note(saved.id)
 assert reopened.body==a.body and reopened.sources==a.sources and reopened.segments==a.segments
 assert store.search_notes('test-work','导听书')[0].id==saved.id
 # Sidecar is an export; atomic Markdown keeps an intact source of truth.
 (store.assets/'segments'/f'{saved.id}.json').unlink()
 assert Store(store.root).get_note(saved.id).segments==saved.segments
 # A damaged derived export must not hide the intact authoritative Markdown.
 (store.assets/'segments'/f'{saved.id}.json').write_text('{broken')
 assert Store(store.root).get_note(saved.id).segments==saved.segments

def test_reader_routes_and_local_only(store):
 idx=store.events('test-work')
 a=store.save(Analysis(work_id='test-work',title='本地记录',body='原文',origin='model',analysis_model='gpt-6-sol',analysis_run_id='existing'))
 with TestClient(create_app(store.root)) as c:
  assert c.get('/api/works?q=贝五').json()[0]['id']=='test-work'
  assert c.get('/api/works?q=Op.67').json()[0]['id']=='test-work'
  assert c.get('/api/works?q=不在曲库').json()==[]
  assert c.get('/api/health').json()['mode']=='local-reader'
  assert c.post('/api/reindex',headers={'Origin':'https://evil.example'}).status_code==403
  paths=c.get('/openapi.json').json()['paths']
  for path in ('/api/research','/api/extract','/api/analysis-runs','/api/jobs/test','/api/model-profiles','/api/settings','/api/score-search','/api/import','/api/analyses'):
   assert path not in paths
   assert c.post(path,json={}).status_code==404
   assert c.get(path).status_code==404
  assert c.put('/api/works/test-work/guide',json={}).status_code in (404,405)
  assert c.delete('/api/analyses/'+a.id).status_code==404
  body=c.get('/api/works/test-work/analyses').json()[0]
  assert body['analysis_model']=='gpt-6-sol' and body['body']=='原文'
  selection=c.post('/api/works/test-work/segments',json={'score_version':idx['version'],'start':0,'end':2}).json()
  assert selection['note_ids']
  assert store.get_note(a.id).segments==[]
  # Simulate Codex editing files while the reader is open, then refresh.
  a.body='Codex 新记录';store.save(a)
  assert c.post('/api/reindex').json()['ok']
  assert c.get('/api/works/test-work/analyses?q=新记录').json()[0]['body']=='Codex 新记录'
  assert "connect-src 'self'" in c.get('/api/health').headers['content-security-policy']


def test_import_new_version_does_not_reuse_locations(store,tmp_path):
 from conftest import SCORE
 from backend.project import import_score
 import pytest
 old=store.events('test-work')['version']
 path=tmp_path/'score.musicxml';path.write_bytes(SCORE.replace(b'<step>A</step>',b'<step>B</step>'))
 meta={'title':'新版本','composer':'测试','catalogue':'Op.67','movement':'I','edition':'测试谱','license':'自制测试资料','source_url':'score.musicxml','previous_work_id':'test-work'}
 work=import_score(store,path,meta)
 assert work['score_version']!=old and work['id']!='test-work'
 with pytest.raises(ValueError):validate_segment(Segment(score_version=old,start=0,end=2),store.events(work['id']))
 assert (store.assets/'generated'/'test-work'/old/'score.mei').exists()
 assert (store.root/work['source_file']).read_bytes()==path.read_bytes()
 count=len(store.works());path.write_bytes(b'broken xml')
 with pytest.raises(ValueError):import_score(store,path,meta)
 assert len(store.works())==count
