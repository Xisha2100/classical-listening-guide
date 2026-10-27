import os, json, uuid, asyncio, hashlib
from pathlib import Path
from contextlib import asynccontextmanager
from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from .store import Store, safe_id, now, read_json, write_json
from .models import Analysis, Segment, ResearchRequest, ExtractRequest, ModelRequest
from .scores import validate_segment, build_score, features, similar
from .services import Services

ROOT=Path(__file__).resolve().parents[2]
load_dotenv(ROOT/'app'/'.env')

def create_app(root=ROOT):
    store=Store(root);services=Services(store)
    @asynccontextmanager
    async def lifespan(app):
        yield
        for task in services.tasks:task.cancel()
        if services.tasks:await asyncio.gather(*list(services.tasks),return_exceptions=True)
    app=FastAPI(title='听见结构 · 本地导听助手',lifespan=lifespan)
    app.state.store=store;app.state.services=services
    @app.middleware('http')
    async def local_only(request:Request,call_next):
        host=request.url.hostname
        if host not in ('localhost','127.0.0.1','::1','testserver'):
            return JSONResponse({'detail':'仅允许本机访问'},status_code=403)
        origin=request.headers.get('origin')
        if origin and urlparse(origin).hostname not in ('localhost','127.0.0.1','::1','testserver'):
            return JSONResponse({'detail':'不允许跨站访问本地资料'},status_code=403)
        response=await call_next(request)
        response.headers['X-Content-Type-Options']='nosniff'
        return response
    @app.exception_handler(ValueError)
    async def invalid(request,exc):return JSONResponse({'detail':str(exc)},status_code=400)
    @app.get('/api/health')
    def health():return {'status':'ok','works':len(store.works()),'note_errors':store.errors}
    @app.get('/api/settings')
    def settings():return services.settings()
    @app.post('/api/reindex')
    def reindex():
        store.reindex();return {'ok':True,'errors':store.errors}
    @app.get('/api/works')
    def works(q:str=''):
        import re
        norm=lambda x:re.sub(r'[\W_]','',x.lower())
        query=norm(q)
        return [w for w in store.works() if not query or query in norm(' '.join([w['title'],w['composer'],w['catalogue'],w['movement']]+w.get('aliases',[])))]
    @app.get('/api/works/{wid}/score')
    def score(wid:str):return {'work':store.work(wid),'index':store.events(wid)}
    @app.get('/api/works/{wid}/pages/{page}')
    def page(wid:str,page:int):
        p=store.score_dir(wid)/f'page-{page}.svg'
        if page<1 or not p.exists():raise HTTPException(404,'谱页不存在')
        return FileResponse(p,media_type='image/svg+xml')
    @app.get('/api/works/{wid}/mei')
    def mei(wid:str):return FileResponse(store.score_dir(wid)/'score.mei',media_type='application/xml')
    @app.get('/api/works/{wid}/analyses')
    def analyses(wid:str,q:str='',kind:str=''):
        store.work(wid);return store.search_notes(wid,q,kind)
    def checked(a):
        index=store.events(a.work_id)
        a.segments=[validate_segment(s,index) for s in a.segments]
        if a.status=='confirmed' and not a.segments:raise ValueError('请先定位片段，再确认。')
        if not a.segments:a.status='unlocated'
        return a
    @app.post('/api/analyses')
    def save(a:Analysis):
        if a.id:
            old=store.get_note(a.id)
            if old.work_id!=a.work_id:raise ValueError('分析不能移动到其他作品')
            a.origin=old.origin;a.created_at=old.created_at
            if a.body!=old.body:a.verification=''
        else:
            a.origin='manual';a.verification=''
        return store.save(checked(a))
    @app.delete('/api/analyses/{aid}')
    def delete(aid:str):store.delete(aid);return {'ok':True}
    @app.post('/api/works/{wid}/segments')
    def segment(wid:str,s:Segment):return validate_segment(s,store.events(wid))
    @app.post('/api/works/{wid}/features')
    def get_features(wid:str,s:Segment):return features(store.events(wid),s)
    @app.post('/api/works/{wid}/similar')
    def get_similar(wid:str,s:Segment):return similar(store.events(wid),s)
    @app.post('/api/research')
    async def research(r:ResearchRequest):
        store.work(r.work_id);return services.submit('search',r.model_dump())
    @app.post('/api/extract')
    async def extract(r:ExtractRequest):
        store.work(r.work_id);return services.submit('extract',r.model_dump())
    @app.post('/api/analysis-runs')
    async def analyze(r:ModelRequest):
        store.work(r.work_id);return services.submit('model',r.model_dump())
    @app.get('/api/jobs/{jid}')
    def job(jid:str):return services.get(jid)
    @app.post('/api/jobs/{jid}/retry')
    async def retry(jid:str):return services.retry(jid)
    @app.post('/api/import')
    async def import_score(file:UploadFile=File(...),title:str=Form(...),composer:str=Form('未知'),catalogue:str=Form('自选谱'),work_id:str=Form('')):
        if not file.filename.lower().endswith(('.xml','.musicxml','.mxl')):raise ValueError('仅支持 MusicXML／MXL')
        data=await file.read(20_000_001)
        if len(data)>20_000_000:raise ValueError('谱文件最多 20 MB')
        if not title.strip():raise ValueError('请输入作品名称')
        # Ingest first; no catalog changes occur if parsing fails.
        wid=safe_id(work_id) if work_id else 'import-'+uuid.uuid4().hex[:12]
        old=store.work(wid) if work_id else None
        version,index=await asyncio.to_thread(build_score,data,store.assets/'generated'/wid)
        source=store.assets/'scores'/wid/version;source.mkdir(parents=True,exist_ok=True)
        (source/('original.mxl' if data[:2]==b'PK' else 'original.musicxml')).write_bytes(data)
        w={**(old or {}),'id':wid,'title':title.strip(),'composer':composer,'catalogue':catalogue,'movement':(old or {}).get('movement','用户导入'),'aliases':(old or {}).get('aliases',[]),'score_version':version,'source_sha256':hashlib.sha256(data).hexdigest(),'source_file':str(source.relative_to(root)/('original.mxl' if data[:2]==b'PK' else 'original.musicxml')),'edition':'用户导入谱本','source_url':'','description':'本机导入的数字乐谱','color':'#546d65','era':'自选曲库'}
        if old:w['previous_versions']=old.get('previous_versions',[])+[old['score_version']]
        store.put_work(w);return w
    app.mount('/assets/piano',StaticFiles(directory=store.assets/'piano',check_dir=False),name='piano')
    dist=Path(root)/'app'/'frontend'/'dist'
    if dist.exists():
        app.mount('/',StaticFiles(directory=dist,html=True),name='frontend')
    return app

app=create_app()
