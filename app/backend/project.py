"""Local authoring operations for Codex. Never exposed as HTTP write routes."""
import hashlib
import uuid
from pathlib import Path

from .models import Analysis, Guide, Segment
from .scores import build_score, validate_segment
from .store import read_json


def validate_analysis(store, analysis: Analysis, *, strict_anchors=False):
    a = analysis.model_copy(deep=True)
    store.work(a.work_id)
    if len({s.id for s in a.sources}) != len(a.sources) or any(not s.id for s in a.sources):
        raise ValueError('引用 ID 不能为空或重复')
    source_ids = {s.id for s in a.sources}
    index = store.events(a.work_id) if a.segments else None
    segments = []
    for original in a.segments:
        segment = validate_segment(original.model_copy(deep=True), index)
        if strict_anchors and (original.note_ids != segment.note_ids or
                              original.start_measure != segment.start_measure or
                              original.end_measure != segment.end_measure):
            raise ValueError(f'片段 {original.label} 的音符或小节索引与范围不一致')
        if any(ref not in source_ids for ref in segment.source_ids):
            raise ValueError('片段边界引用了不存在的资料')
        segments.append(segment)
    a.segments = segments
    if len({s.id for s in segments}) != len(segments):
        raise ValueError('片段 ID 重复')
    segment_ids = {s.id for s in segments}
    for claim in a.claims:
        if any(ref not in source_ids for ref in claim.source_ids) or any(ref not in segment_ids for ref in claim.segment_ids):
            raise ValueError('分析论点引用了不存在的资料或片段')
        if claim.evidence_type == 'source' and not claim.source_ids:
            raise ValueError('资料论点需要引用来源')
        if claim.evidence_type == 'score' and not claim.segment_ids:
            raise ValueError('谱面论点需要对应片段')
    if a.section_id and a.section_id not in {s['id'] for s in store.guide(a.work_id)['sections']}:
        raise ValueError('分析引用不存在的章节')
    if not a.dimensions:
        a.dimensions = [a.kind]
    if not a.segments:
        if a.status == 'confirmed':
            raise ValueError('确认定位需要有效片段')
        a.status = 'not_applicable' if a.scope in ('overview', 'movement') else 'unlocated'
    elif a.status in ('not_applicable', 'unlocated'):
        a.status = 'suggested'
    return a


def save_analysis(store, analysis: Analysis):
    a = validate_analysis(store, analysis)
    existing = [item for item in store.all_notes() if item.id == a.id] if a.id else []
    if existing:
        old = existing[0]
        if old.work_id != a.work_id:
            raise ValueError('分析不能移动到其他作品')
        # A revision must never silently relabel the original author/model.
        if (a.origin, a.analysis_model, a.analysis_run_id) != (old.origin, old.analysis_model, old.analysis_run_id):
            raise ValueError('请保留原分析来源与模型记录；重新分析应另建卡片并归档旧版')
        a.created_at = old.created_at
        if any(getattr(a, key) != getattr(old, key) for key in ('title', 'body', 'sources', 'segments', 'claims', 'listen_for')):
            a.verification = ''
            a.review_status = 'unreviewed'
            if a.segments != old.segments:
                a.listening_status = 'pending'
    elif a.origin == 'model' and not (a.analysis_model and a.analysis_run_id):
        raise ValueError('GPT 分析须记录实际模型（未知则写 unknown）及本地分析记录路径或标识')
    elif a.origin != 'model' and (a.analysis_model or a.analysis_run_id):
        raise ValueError('只有模型分析可以填写模型来源')
    return store.save(a)


def import_score(store, path: Path, metadata: dict):
    """Always create a new edition, preserving all previous anchors and sources."""
    if path.suffix.lower() not in ('.xml', '.musicxml', '.mxl'):
        raise ValueError('仅支持 MusicXML／MXL')
    if path.stat().st_size > 20_000_000:
        raise ValueError('谱文件最多 20 MB')
    for key in ('title', 'composer', 'catalogue', 'movement', 'edition', 'license', 'source_url'):
        if not isinstance(metadata.get(key), str) or not metadata[key].strip():
            raise ValueError(f'导入元数据缺少 {key}；本地来源可用项目相对路径')
    data = path.read_bytes()
    wid = 'import-' + uuid.uuid4().hex[:12]
    previous = store.work(metadata['previous_work_id']) if metadata.get('previous_work_id') else None
    version, _ = build_score(data, store.assets / 'generated' / wid)
    source = store.assets / 'scores' / wid / version
    source.mkdir(parents=True, exist_ok=True)
    original = source / ('original.mxl' if data[:2] == b'PK' else 'original.musicxml')
    original.write_bytes(data)
    keys = ('title', 'composer', 'catalogue', 'movement', 'edition', 'license', 'source_url',
            'aliases', 'description', 'collection_id', 'movement_order', 'source_revision', 'coverage', 'arranger', 'score_type')
    work = {key: metadata[key] for key in keys if key in metadata}
    work.update(id=wid, score_version=version, source_sha256=hashlib.sha256(data).hexdigest(),
                source_file=str(original.relative_to(store.root)), availability='ready', color='#546d65', era='自选曲库')
    work.setdefault('description', 'Codex 项目收录的数字乐谱')
    work.setdefault('aliases', [])
    if previous:
        work.update(previous_work_id=previous['id'], collection_id=previous.get('collection_id', previous['id']))
    store.put_work(work)
    return work


def check_project(store):
    """Validate authoritative content without repairing or rewriting it."""
    notes = store.all_notes()
    errors = list(store.errors)
    seen = set()
    for a in notes:
        try:
            if a.id in seen:
                raise ValueError('分析 ID 重复')
            seen.add(a.id)
            validate_analysis(store, a, strict_anchors=True)
            sidecar = store.assets / 'segments' / f'{a.id}.json'
            if sidecar.exists() and [Segment.model_validate(s) for s in read_json(sidecar)] != a.segments:
                raise ValueError('片段 JSON 导出与 Markdown 元数据不一致，请用 save-analysis 同步')
        except (ValueError, OSError, KeyError) as exc:
            errors.append(f'{a.work_id}/{a.id}: {exc}')
    for work in store.works():
        try:
            if work.get('availability') == 'pending':
                continue
            index = store.events(work['id'])
            if work['score_version'] != index['version']:
                raise ValueError('曲库与事件索引的谱本版本不同')
            for page in range(1, index['pages'] + 1):
                if not (store.score_dir(work['id']) / f'page-{page}.svg').is_file():
                    raise ValueError(f'缺少谱页 {page}')
            store.validate_guide(Guide.model_validate(store.guide(work['id'])))
        except (ValueError, OSError, KeyError) as exc:
            errors.append(f"{work['id']}: {exc}")
    return {'ok': not errors, 'works': len(store.works()), 'analyses': len(notes), 'errors': errors}
