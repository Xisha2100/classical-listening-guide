"""Install the score-checked Beethoven V guide without overwriting personal edits."""
import hashlib
import json
import os
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'app'))
from backend.models import Analysis, Claim, Guide, Segment, Source
from backend.scores import validate_segment
from backend.store import Store, read_json, write_json

WORK_ID = 'beethoven-op67-1'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def score_audit(index, root):
    """Check the musical facts used below against the pinned score, not a model answer."""
    assert len(index['measures']) == 502
    assert [str(m['label']) for m in index['measures']] == [str(n) for n in range(1, 503)]
    staffs = {s['id']: s['label'] for s in index['staffs']}
    for staff, name in [('3', 'Oboe'), ('7', 'Bassoon'), ('9', 'Horn'), ('14', 'Violin')]:
        assert name in staffs[staff]
    def events(measure, staff=None):
        return [e for e in index['events'] if e['measure'] == measure - 1 and e.get('playable', True)
                and (staff is None or e['staff'] == str(staff))]
    def pcs(measure, strings=False):
        return {e['pitch'] % 12 for e in events(measure) if not strings or e['staff'] in {'14','15','16','17','18'}}
    def pitches(measure, staff):
        return [e['pitch'] for e in events(measure, staff)]
    assert pitches(1, 14) == [67, 67, 67]
    assert abs(events(1, 14)[0]['onset'] - index['measures'][0]['start'] - .5) < 1e-6
    assert pcs(20, True) == {8, 0, 6} and pcs(21, True) == {7, 11, 2}
    assert pitches(59, 9) == [70, 70, 70] and pitches(60, 9) == [63]
    assert pitches(303, 7) == [67, 67, 67] and pitches(304, 7) == [60]
    assert pitches(63, 14) == [70, 75] and pitches(307, 14) == [67, 72]
    assert pitches(65, 17) == [46, 46, 46] and pitches(66, 17) == [51]
    assert pcs(117) == {10, 2, 5} and pcs(118) == {3, 7, 10}
    assert pitches(125, 5) == [70, 70, 70]
    assert pitches(196, 1) == [77] and pitches(197, 1) == [79]
    assert not events(196, 14) and events(198, 14)
    assert events(210, 14) and not events(211, 14) and events(211, 1)
    assert pcs(236) == {11, 2, 5, 8}
    assert pitches(248, 14) == [77, 79, 79, 79]
    assert len(events(268, 3)) == 11
    assert index['measures'][267]['end'] - index['measures'][267]['start'] == 10
    assert pcs(374) == {0, 4, 7} and pcs(376) == {5, 8, 0}
    assert pcs(500) == {0, 3, 7} and pcs(501) == {7, 11, 2} and pcs(502) == {0, 3, 7}
    source = root / 'assets/scores/beethoven-op67-1/Beethoven_Op.67_1.mxl'
    with zipfile.ZipFile(source) as archive:
        score = ET.fromstring(archive.read(next(n for n in archive.namelist()
                                               if n.endswith('.xml') and 'META-INF' not in n)))
    parts = {p.attrib['id']: {int(m.attrib['number']): m for m in p.findall('measure')} for p in score.findall('part')}
    assert parts['P14'][124].find('.//repeat') is not None
    assert parts['P14'][2].find('.//fermata') is not None
    assert parts['P14'][5].find('.//fermata') is not None
    assert parts['P14'][20].find('.//pitch/alter').text == '-1'
    assert parts['P14'][210].findtext('.//direction-type/words') == 'dim.'
    assert parts['P9'][59].find('.//dynamics/ff') is not None
    assert parts['P9'][63].find('.//dynamics/p') is not None
    assert parts['P17'][268].findtext('.//direction-type/words') == 'arco'
    assert any(d.text and 'Adagio' in d.text for d in parts['P1'][268].findall('.//direction-type/words'))
    return {'score_facts_checked': True, 'checks': 33, 'human_listening': 'pending',
            'method': '直接核对保留的 MusicXML 声部、音高与记号，以及规范实音事件索引；未声称完成人工试听。',
            'boundary_note': '呈示结束124含反复；125展开；248再现主题进入。374为C大三和弦终止与尾声启动的重叠，376转F小三和弦；两种尾声入口解释并列保留。'}


def make_card(spec, index, sources):
    segments = []
    for n, desc in enumerate(spec['segments']):
        first, last = desc['measures']
        start = index['measures'][first - 1]['start'] + desc.get('start_offset', 0)
        end = index['measures'][last - 1]['end']
        if 'end_offset' in desc:
            end = index['measures'][last - 1]['start'] + desc['end_offset']
        s = Segment(id=f"{spec['id']}-s{n+1}", label=desc['label'], score_version=index['version'],
                    start=start, end=end, staffs=[str(v) for v in desc['staffs']])
        s = validate_segment(s, index)
        if not s.note_ids:
            raise ValueError(f"示例片段没有音符：{spec['id']} / {desc['label']}")
        segments.append(s)
    claims = []
    used_sources = list(spec.get('source_ids', []))
    for n, claim in enumerate(spec['claims']):
        source_ids = claim.get('source_ids', [])
        for sid in source_ids:
            if sid not in used_sources:
                used_sources.append(sid)
        segment_ids = [segments[i].id for i in claim.get('segments', [])]
        if claim['evidence_type'] == 'score' and not segment_ids:
            raise ValueError('谱面论点缺少可播证据')
        if claim['evidence_type'] == 'source' and not source_ids:
            raise ValueError('资料论点缺少来源')
        claims.append(Claim(id=f"{spec['id']}-c{n+1}", statement=claim['statement'],
                            evidence_type=claim['evidence_type'], source_ids=source_ids,
                            segment_ids=segment_ids, listening_cue=claim.get('listening_cue', spec['listen_for'])))
    return Analysis(id=spec['id'], work_id=WORK_ID, title=spec['title'], body=spec['body'],
                    kind=spec['dimensions'][0], dimensions=spec['dimensions'],
                    scope=spec.get('scope', 'section'), section_id=spec.get('section_id', ''),
                    listen_for=spec['listen_for'], claims=claims, sources=[Source.model_validate(sources[s]) for s in used_sources],
                    segments=segments, origin='seed', status='not_applicable' if spec.get('scope') == 'overview' else 'confirmed',
                    review_status='unreviewed', listening_status='pending',
                    verification='数字谱的实际音高、声部、拍位与所列记号已逐项核对，定位通过同一事件索引校验。正文含编辑解释，尚待用户乐理复核及人工试听。钢琴复奏不重现管弦音色或自由延长记号。')


def main(root=ROOT):
    root = Path(root)
    store = Store(root)
    specification = root / 'assets/scores/beethoven-op67-1/deep-analysis.json'
    if not specification.exists() or not any(w['id'] == WORK_ID for w in store.works()):
        return {'skipped': '贝五谱本尚未准备'}
    data = read_json(specification)
    index = store.events(WORK_ID)
    if index['version'] != data['score_version']:
        print('保留贝五个人谱本：版本已变化，深度示例未自动迁移。', flush=True)
        return {'skipped': 'score_version_changed'}
    audit = score_audit(index, root)
    sources = {s['id']: s for s in data['sources']}
    installation = data.setdefault('installation', {'notes': {}, 'archived_v1': []})
    guide_path = root / 'assets/guides/beethoven-op67-1.json'
    guide = Guide.model_validate(data['guide'])
    # Only overwrite a previously installed guide if it has not been edited.
    if not guide_path.exists() and 'guide_sha256' not in installation:
        store.save_guide(guide)
        installation['guide_sha256'] = digest(guide_path)
    elif guide_path.exists() and digest(guide_path) == installation.get('guide_sha256'):
        if read_json(guide_path) != guide.model_dump():
            store.save_guide(guide)
            installation['guide_sha256'] = digest(guide_path)
    current = {a.id: a for a in store.all_notes(WORK_ID)}
    installed = preserved = 0
    for spec in data['cards']:
        card = make_card(spec, index, sources)
        path = store.notes / WORK_ID / f'{card.id}.md'
        previous_hash = installation['notes'].get(card.id)
        if card.id in current:
            if not previous_hash or digest(path) != previous_hash:
                preserved += 1
                continue
            existing = current[card.id]
            if existing.model_dump(exclude={'created_at','updated_at'}) == card.model_dump(exclude={'created_at','updated_at'}):
                continue
            card.created_at = existing.created_at
        elif previous_hash:
            # A deliberately deleted seed stays deleted on subsequent startups.
            preserved += 1
            continue
        store.save(card)
        installation['notes'][card.id] = digest(path)
        installed += 1
    # Archive only byte-for-byte v1 originals. User-edited cards stay exactly where they are.
    for aid, original_hash in data.get('v1_original_sha256', {}).items():
        path = store.notes / WORK_ID / f'{aid}.md'
        if aid in installation['archived_v1'] or not path.exists() or digest(path) != original_hash:
            continue
        archived = store.notes / WORK_ID / 'archive' / 'v1' / path.name
        if archived.exists():
            continue
        archived.parent.mkdir(parents=True, exist_ok=True)
        os.replace(path, archived)
        installation['archived_v1'].append(aid)
    data['verification'] = audit
    write_json(specification, data)
    store.reindex()
    result = {'installed_or_updated': installed, 'personal_or_deleted_preserved': preserved,
              'v2_cards': len(data['cards']), 'segments': sum(len(c['segments']) for c in data['cards']),
              'archived_v1': len(installation['archived_v1']), 'score_audit': audit}
    print('贝五深度示例：' + json.dumps(result, ensure_ascii=False), flush=True)
    return result


if __name__ == '__main__':
    main()
