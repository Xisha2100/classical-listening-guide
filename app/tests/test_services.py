import asyncio,json
import pytest
from backend.models import ModelRequest,ModelOutput,Source,Segment
from backend.services import Services,validate_model_output,public_url
from backend.scores import validate_segment

def test_model_ids_and_uncertainty(store):
 idx=store.events('test-work');seg=validate_segment(Segment(id='known',score_version=idx['version'],start=0,end=2),idx)
 req=ModelRequest(work_id='test-work',mode='sources',question='分析',sources=[Source(id='book')])
 base={'title':'主题','body':'据资料推测','kind':'主题','source_ids':['book'],'segment_ids':['known']}
 out=ModelOutput(cards=[base]);cards=validate_model_output(out,req,{'known':seg})
 assert cards[0].status=='suggested' and cards[0].origin=='model'
 for field in ['source_ids','segment_ids']:
  with pytest.raises(ValueError):validate_model_output(ModelOutput(cards=[{**base,field:['madeup']}]),req,{'known':seg})
 assert validate_model_output(ModelOutput(cards=[{**base,'segment_ids':[]}]),req,{'known':seg})[0].status=='unlocated'

def test_search_extract_failure_retains_summary(store):
 svc=Services(store)
 async def mock(endpoint,payload):
  if endpoint=='search':return {'results':[{'url':'https://example.org/analysis','title':'分析','content':'搜索摘要'},{'url':'http://localhost/private','title':'不应出现'}]}
  return {'results':[],'failed_results':[{'url':'https://example.org/analysis'}]}
 svc.tavily=mock
 async def run():
  search=await svc.search({'work_id':'test-work','question':'主题'})
  assert len(search['sources'])==1
  extract=await svc.extract({'work_id':'test-work','urls':['https://example.org/analysis']})
  assert extract['sources'][0]['excerpt']=='搜索摘要' and not extract['sources'][0]['extracted']
  with pytest.raises(ValueError):await svc.extract({'work_id':'test-work','urls':['https://other.org/']})
 asyncio.run(run())

def test_background_failure_retry_and_no_secret(store,monkeypatch):
 svc=Services(store);monkeypatch.setenv('TAVILY_API_KEY','TEST-SECRET')
 async def fail(payload):raise ValueError('failure TEST-SECRET')
 svc.search=fail
 async def run():
  job=svc.submit('search',{'work_id':'test-work','question':'主题'})
  await asyncio.gather(*list(svc.tasks))
  j=svc.get(job['id']);assert j['status']=='failed' and 'TEST-SECRET' not in j['error'] and 'payload' not in j
  async def success(payload):return {'sources':[]}
  svc.search=success
  retry=svc.retry(j['id']);await asyncio.gather(*list(svc.tasks))
  assert svc.get(retry['id'])['status']=='done'
 asyncio.run(run())

@pytest.mark.parametrize('url',['file:///etc/passwd','javascript:alert(1)','http://127.0.0.1/','http://192.168.0.1/','http://localhost/'])
def test_reject_non_public_sources(url):assert not public_url(url)

def test_full_model_pipeline_with_mock_provider(store,monkeypatch):
 import sys,types
 monkeypatch.setenv('LLM_MODEL','test/model');monkeypatch.setenv('LLM_API_KEY','fixture-key')
 idx=store.events('test-work');seg=Segment(id='selected',score_version=idx['version'],start=0,end=2)
 async def completion(**kwargs):
  payload=json.loads(kwargs['messages'][1]['content'])
  assert payload['score_features'][0]['events'][0]['pitch']==67
  assert payload['evidence'][0]['excerpt']=='引文保持原样'
  data={'cards':[{'title':'模型草稿','body':'根据书籍提出主题假设。','kind':'主题','source_ids':['book'],'segment_ids':['selected']}]}
  return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=json.dumps(data)))],usage=None)
 monkeypatch.setitem(sys.modules,'litellm',types.SimpleNamespace(acompletion=completion))
 req=ModelRequest(work_id='test-work',mode='segment',question='主题？',sources=[Source(id='book',title='书',excerpt='引文保持原样')],segments=[seg])
 result=asyncio.run(Services(store).analyze(req))
 a=store.get_note(result['analyses'][0]['id'])
 assert a.origin=='model' and a.status=='suggested' and a.sources[0].excerpt=='引文保持原样'
 assert a.segments[0].note_ids and result['source_ids']==['book']

def test_ollama_default_without_api_key(store,monkeypatch):
 for key in ('LLM_MODEL','LLM_API_KEY','LLM_API_BASE','LLM_TIMEOUT'):monkeypatch.delenv(key,raising=False)
 settings=Services(store).settings()
 assert settings['model']=='ollama_chat/qwen3.8:latest'
 assert settings['model_ready'] and settings['model_local']
 monkeypatch.setenv('LLM_MODEL','test/cloud')
 assert not Services(store).settings()['model_ready']

def test_ollama_calls_are_local_and_keyless(store,monkeypatch):
 import sys,types
 monkeypatch.setenv('LLM_MODEL','ollama_chat/installed-model')
 monkeypatch.setenv('LLM_API_BASE','http://127.0.0.1:11434')
 monkeypatch.setenv('LLM_API_KEY','cloud-key-must-not-be-forwarded')
 monkeypatch.setenv('LLM_TIMEOUT','300')
 async def completion(**kwargs):
  assert 'api_key' not in kwargs
  assert kwargs['model']=='ollama_chat/installed-model'
  assert kwargs['api_base']=='http://127.0.0.1:11434' and kwargs['timeout']==300
  assert kwargs['think'] is False and kwargs['num_ctx']==32768
  assert 'cards' in kwargs['format']['properties']
  data={'cards':[{'title':'本地草稿','body':'资料不足，暂不定位。','kind':'主题','source_ids':['book'],'segment_ids':[]}]}
  return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=json.dumps(data)))],usage=None)
 monkeypatch.setitem(sys.modules,'litellm',types.SimpleNamespace(acompletion=completion))
 p=ModelRequest(work_id='test-work',mode='sources',question='主题？',sources=[Source(id='book',excerpt='测试摘录')])
 out=asyncio.run(Services(store).analyze(p))
 assert out['analyses'][0]['status']=='unlocated'
 assert out['analyses'][0]['origin']=='model'

def test_ollama_connection_failure_is_actionable(store,monkeypatch):
 import sys,types
 monkeypatch.setenv('LLM_MODEL','ollama_chat/not-installed')
 monkeypatch.setenv('LLM_API_BASE','http://127.0.0.1:11434')
 async def completion(**kwargs):raise ConnectionError('unavailable')
 monkeypatch.setitem(sys.modules,'litellm',types.SimpleNamespace(acompletion=completion))
 p=ModelRequest(work_id='test-work',mode='sources',question='主题？',sources=[Source(id='book',excerpt='测试摘录')])
 with pytest.raises(ValueError,match='ollama list'):asyncio.run(Services(store).analyze(p))
 assert store.all_notes()==[]
