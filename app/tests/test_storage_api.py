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

def test_api_crud_validation_and_local_only(store):
 with TestClient(create_app(store.root)) as c:
  assert c.get('/api/works?q=贝五').json()[0]['id']=='test-work'
  assert c.get('/api/works?q=Op.67').json()[0]['id']=='test-work'
  assert c.get('/api/works?q=不在曲库').json()==[]
  assert c.post('/api/reindex',headers={'Origin':'https://evil.example'}).status_code==403
  idx=store.events('test-work')
  p={'work_id':'test-work','title':'新增笔记','body':'个人解释','sources':[{'id':'s1','title':'书名','excerpt':'未修改原文','pages':'23'}],'segments':[{'score_version':idx['version'],'start':0,'end':2}],'status':'confirmed'}
  r=c.post('/api/analyses',json=p);assert r.status_code==200,r.text
  a=r.json();assert a['origin']=='manual' and a['segments'][0]['note_ids']
  a['body']='改后的解释';a['origin']='model'
  assert c.post('/api/analyses',json=a).json()['origin']=='manual'
  a['segments'][0]['note_ids']=['invalid']
  assert c.post('/api/analyses',json=a).status_code==400
  assert c.post('/api/reindex').json()['ok']
  assert len(c.get('/api/works/test-work/analyses?q=未修改原文').json())==1
  assert c.delete('/api/analyses/'+a['id']).status_code==200
  assert c.get('/api/works/test-work/analyses').json()==[]

def test_import_new_version_does_not_reuse_locations(store):
 from conftest import SCORE
 with TestClient(create_app(store.root)) as c:
  old=store.events('test-work')['version']
  changed=SCORE.replace(b'<step>A</step>',b'<step>B</step>')
  r=c.post('/api/import',data={'title':'新版本','work_id':'test-work'},files={'file':('score.musicxml',changed,'application/xml')})
  assert r.status_code==200,r.text
  assert r.json()['score_version']!=old
  assert c.post('/api/works/test-work/segments',json={'score_version':old,'start':0,'end':2}).status_code==400
  assert (store.assets/'generated'/'test-work'/old/'score.mei').exists()
