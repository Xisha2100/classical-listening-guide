import json, re, sqlite3, uuid, os, threading
from datetime import datetime, timezone
from pathlib import Path
import yaml
import jieba
from .models import Analysis

SAFE_ID = re.compile(r'^[a-zA-Z0-9_-]{1,100}$')
def now(): return datetime.now(timezone.utc).isoformat()
def safe_id(value):
    if not SAFE_ID.fullmatch(value): raise ValueError('无效标识符')
    return value

def atomic_text(path: Path, value: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    tmp.write_text(value, encoding='utf-8')
    os.replace(tmp, path)

def write_json(path, value): atomic_text(path, json.dumps(value, ensure_ascii=False, indent=2))
def read_json(path): return json.loads(path.read_text(encoding='utf-8'))
def words(text): return ' '.join(jieba.cut(text.lower()))

class Store:
    def __init__(self, root):
        self.root = Path(root)
        self.assets = self.root / 'assets'
        self.notes = self.root / '作品'
        self.cache = self.root / 'app' / '.cache'
        self.cache.mkdir(parents=True, exist_ok=True)
        jieba.dt.tmp_dir = str(self.cache)
        self.lock = threading.RLock()
        self.db = self.cache / 'index.sqlite3'
        self.errors = []
        self.reindex()
    def works(self):
        p = self.assets / 'catalog.json'
        return read_json(p) if p.exists() else []
    def work(self, wid):
        safe_id(wid)
        for w in self.works():
            if w['id'] == wid: return w
        raise ValueError('未找到作品')
    def put_work(self, work):
        with self.lock:
            works = self.works()
            works = [work if w['id']==work['id'] else w for w in works] if any(w['id']==work['id'] for w in works) else works+[work]
            write_json(self.assets/'catalog.json', works)
    def score_dir(self, wid):
        w = self.work(wid)
        return self.assets/'generated'/safe_id(wid)/safe_id(w['score_version'])
    def events(self, wid): return read_json(self.score_dir(wid)/'events.json')
    def read_note(self, path):
        text = path.read_text(encoding='utf-8')
        match = re.match(r'\A---\n(.*?)\n---(?:\n|$)(.*)\Z', text, re.S)
        if not match: raise ValueError('笔记缺少 YAML 元数据')
        front, body = match.groups()
        data = yaml.safe_load(front)
        body = body.lstrip('\n')
        if body.startswith('# '): body = body.split('\n', 1)[1].lstrip('\n')
        data['body'] = body.rstrip()
        seg = self.assets/'segments'/f"{safe_id(data['id'])}.json"
        data['segments'] = data.get('segments', read_json(seg) if seg.exists() else [])
        return Analysis.model_validate(data)
    def all_notes(self, work_id=None):
        result=[]
        self.errors=[]
        for path in sorted(self.notes.glob('*/*.md')):
            try:
                a=self.read_note(path)
                if work_id is None or a.work_id==work_id: result.append(a)
            except (ValueError, KeyError, TypeError, yaml.YAMLError) as e:
                self.errors.append(f'{path.name}: {type(e).__name__}')
        return result
    def get_note(self, aid):
        safe_id(aid)
        for a in self.all_notes():
            if a.id==aid: return a
        raise ValueError('未找到分析')
    def save(self, a):
        with self.lock:
            a.id = safe_id(a.id or uuid.uuid4().hex)
            self.work(a.work_id)
            a.created_at = a.created_at or now()
            a.updated_at = now()
            # JSON sidecar holds structured anchors, Markdown holds prose and evidence.
            write_json(self.assets/'segments'/f'{a.id}.json', [s.model_dump() for s in a.segments])
            data = a.model_dump(exclude={'body'})
            title = a.title.replace('\n', ' ')
            text = '---\n'+yaml.safe_dump(data, allow_unicode=True,sort_keys=False)+'---\n\n# '+title+'\n\n'+a.body+'\n'
            atomic_text(self.notes/safe_id(a.work_id)/f'{a.id}.md',text)
            self.reindex()
            return a
    def delete(self, aid):
        with self.lock:
            a=self.get_note(aid)
            (self.notes/a.work_id/f'{a.id}.md').unlink()
            (self.assets/'segments'/f'{a.id}.json').unlink(missing_ok=True)
            self.reindex()
    def reindex(self):
        with self.lock, sqlite3.connect(self.db) as db:
            db.execute('CREATE VIRTUAL TABLE IF NOT EXISTS notes USING fts5(id UNINDEXED, work_id UNINDEXED, text)')
            db.execute('DELETE FROM notes')
            for a in self.all_notes():
                text=' '.join([a.title,a.body,a.kind]+[s.title+' '+s.excerpt for s in a.sources])
                db.execute('INSERT INTO notes VALUES(?,?,?)',(a.id,a.work_id,words(text)))
    def search_notes(self, wid, query='',kind=''):
        notes=self.all_notes(wid)
        if kind: notes=[a for a in notes if a.kind==kind]
        if query.strip():
            tokens = [t for t in jieba.cut(query.lower()) if t.strip()]
            match=' OR '.join('"'+t.replace('"','""')+'"' for t in tokens)
            with sqlite3.connect(self.db) as db:
                ids={r[0] for r in db.execute('SELECT id FROM notes WHERE notes MATCH ? AND work_id=?',(match,wid))} if match else set()
            notes=[a for a in notes if a.id in ids or query.lower() in (a.title+a.body).lower()]
        return sorted(notes,key=lambda a:(a.origin!='seed',a.created_at))
