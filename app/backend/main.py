"""Loopback-only reader. All authoring and research belongs to the Codex workspace."""
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .models import Segment
from .scores import validate_segment
from .store import Store

ROOT = Path(__file__).resolve().parents[2]


def create_app(root=ROOT):
    store = Store(root, read_only=True)
    app = FastAPI(title='听见结构 · Codex 项目阅读器', docs_url=None, redoc_url=None)
    app.state.store = store

    @app.middleware('http')
    async def local_only(request: Request, call_next):
        allowed = ('localhost', '127.0.0.1', '::1', 'testserver')
        if request.url.hostname not in allowed:
            return JSONResponse({'detail': '仅允许本机访问'}, status_code=403)
        origin = request.headers.get('origin')
        if origin and urlparse(origin).hostname not in allowed:
            return JSONResponse({'detail': '不允许跨站访问本地资料'}, status_code=403)
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        # Fetch, audio samples, fonts and scripts are all local. Source links may
        # still be opened deliberately by the reader in another page.
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; media-src 'self' blob:; connect-src 'self'; "
            "font-src 'self' data:; worker-src 'self' blob:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
        )
        return response

    @app.exception_handler(ValueError)
    async def invalid(request, exc):
        return JSONResponse({'detail': str(exc)}, status_code=400)

    @app.get('/api/health')
    def health():
        return {'status': 'ok', 'mode': 'local-reader', 'works': len(store.works()), 'note_errors': store.errors}

    @app.post('/api/reindex')
    def reindex():
        # Only the disposable search cache is written, never notes or scores.
        store.reindex()
        return {'ok': True, 'errors': store.errors}

    @app.get('/api/works')
    def works(q: str = ''):
        import re
        norm = lambda x: re.sub(r'[\W_]', '', x.lower())
        query = norm(q)
        return [w for w in store.works() if not query or query in norm(' '.join(
            [w['title'], w['composer'], w['catalogue'], w['movement']] + w.get('aliases', [])
        ))]

    @app.get('/api/collections')
    def collections():
        return store.collections()

    @app.get('/api/works/{wid}/score')
    def score(wid: str):
        return {'work': store.work(wid), 'index': store.events(wid)}

    @app.get('/api/works/{wid}/guide')
    def guide(wid: str):
        return store.guide(wid)

    @app.get('/api/works/{wid}/pages/{page}')
    def page(wid: str, page: int):
        path = store.score_dir(wid) / f'page-{page}.svg'
        if page < 1 or not path.exists():
            raise HTTPException(404, '谱页不存在')
        return FileResponse(path, media_type='image/svg+xml')

    @app.get('/api/works/{wid}/mei')
    def mei(wid: str):
        return FileResponse(store.score_dir(wid) / 'score.mei', media_type='application/xml')

    @app.get('/api/works/{wid}/analyses')
    def analyses(wid: str, q: str = '', kind: str = ''):
        store.work(wid)
        return store.search_notes(wid, q, kind)

    @app.post('/api/works/{wid}/segments')
    def segment(wid: str, segment: Segment):
        # Stateless selection for audition/clipboard; this does not save an anchor.
        return validate_segment(segment, store.events(wid))

    # Unknown/retired API routes must not accidentally serve the frontend HTML.
    @app.api_route('/api/{path:path}', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'], include_in_schema=False)
    def unknown_api(path: str):
        raise HTTPException(404, '网页仅提供本地阅读与试听；请在 Codex 项目中分析和记录。')

    app.mount('/assets/piano', StaticFiles(directory=store.assets / 'piano', check_dir=False), name='piano')
    dist = Path(root) / 'app' / 'frontend' / 'dist'
    if dist.exists():
        app.mount('/', StaticFiles(directory=dist, html=True), name='frontend')
    return app


app = create_app()
