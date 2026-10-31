"""Install checked Tchaikovsky examples while preserving edited or deleted seeds."""
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'app'))
from backend.models import Analysis, Claim, Guide, Segment, Source
from backend.scores import validate_segment
from backend.store import Store, read_json, write_json


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def measure_range(index, mapping, first, last):
    """Printed labels can repeat after a split bar. Include every matching element."""
    starts = [m['ordinal'] - 1 for m in mapping if m['printed_measure'] == str(first)]
    ends = [m['ordinal'] - 1 for m in mapping if m['printed_measure'] == str(last)]
    if not starts or not ends:
        raise ValueError(f'印刷小节号不存在：{first}–{last}')
    a, b = min(starts), max(ends)
    if a > b or str(index['measures'][a]['label']) != str(first) or str(index['measures'][b]['label']) != str(last):
        raise ValueError('原谱与规范索引的小节映射不一致')
    return a, b


def score_audit(indexes, mappings, root):
    """Assert the actual pitches, durations and directions cited by these examples."""
    for movement, expected in [(1, 669), (2, 170), (3, 301)]:
        idx, mapping = indexes[movement], mappings[movement]
        assert len(idx['measures']) == len(mapping) == expected
        assert all(str(m['label']) == entry['printed_measure'] for m, entry in zip(idx['measures'], mapping))
        assert len(idx['staffs']) == 18
        assert 'Clarinets' in idx['staffs'][3]['label']
        assert 'Violins' in idx['staffs'][13]['label']
        assert 'Cellos' in idx['staffs'][16]['label']

    def events(movement, label, staff=None, voice=None):
        a, b = measure_range(indexes[movement], mappings[movement], label, label)
        return [e for e in indexes[movement]['events'] if a <= e['measure'] <= b and e.get('playable', True)
                and (staff is None or e['staff'] == str(staff)) and (voice is None or e['voice'] == str(voice))]

    def line(movement, label, staff, voice='1'):
        return [(e['pitch'], round(e['duration'], 6)) for e in events(movement, label, staff, voice)]

    assert line(1, 1, 6) == [(65, .5), (61, .5), (60, .5)]
    assert line(1, 7, 14) == [(68, .5), (65, .5), (63, .5)]
    assert [p - q for (p, _), (q, _) in zip(line(1, 7, 14), line(1, 7, 17))] == [12, 12, 12]
    for label in (6, 7, 8, 9):
        assert {e['pitch'] % 12 for e in events(1, label, 12)} == {1, 5, 8}
    assert min(e['pitch'] for e in events(1, 10, 13)) == 25
    assert {e['pitch'] % 12 for e in events(1, 10, 12)} == {3, 6, 10}
    assert any(abs(e['duration'] - 1/3) < 1e-5 for e in events(1, 109, 12))
    assert line(1, 185, 4) == line(1, 193, 12) == [(73, 1), (69, 2), (70, 1)]
    assert line(1, 268, 14) == [(77, 1), (79, 1), (75, 1), (77, 1)]
    assert all(abs(e['duration'] - 1/3) < 1e-5 for e in events(1, 268, 17))
    assert line(1, 480, 14) == [(75, 1), (71, 2), (72, 1)]
    assert not [e for label in (539, 540, 541) for e in events(1, label) if e['staff'] not in {'12', '13'}]
    assert events(1, 539, 13) and events(1, 540, 13)
    end = events(1, 665, 12)
    onsets = sorted({e['onset'] for e in end})
    assert [{e['pitch'] % 12 for e in end if e['onset'] == t} for t in onsets] == [{10, 2, 5}, {10, 3, 7}, {10, 2, 5}]
    assert {e['pitch'] % 12 for e in events(1, 666, 12)} == {10}
    assert line(2, 5, 1) == [(80, 1.5), (75, 1), (77, .5)]
    assert line(2, 146, 12) == [(80, 1.5), (75, 1), (82, .5)]
    assert events(3, 8, 12) and events(3, 252, 14)
    assert {e['pitch'] % 12 for e in events(3, 301, 12)} == {10}

    raw = {}
    for movement in (1, 2, 3):
        path = root / f'assets/scores/tchaikovsky-op23/movement-{movement}.mxl'
        with zipfile.ZipFile(path) as archive:
            score = ET.fromstring(archive.read(next(n for n in archive.namelist()
                if n.endswith(('.xml', '.musicxml')) and 'META-INF' not in n)))
        raw[movement] = {p.attrib['id']: p.findall('measure') for p in score.findall('part')}
        assert len(raw[movement]) == 17
        assert raw[movement]['P12'][0].findtext('./attributes/staves') == '2'

    def bar(movement, part, label):
        return next(m for m in raw[movement][part] if m.attrib['number'] == str(label))

    assert bar(1, 'P1', 1).findtext('.//time/beats') == '3'
    assert bar(1, 'P1', 109).findtext('.//time/beats') == '4'
    assert any('Allegro con spirito' in (w.text or '') for w in bar(1, 'P1', 109).findall('.//words'))
    assert any('Cadenza' in (w.text or '') for w in bar(1, 'P1', 538).findall('.//words'))
    assert any('rubato' in (w.text or '') for w in bar(1, 'P1', 539).findall('.//words'))
    assert bar(1, 'P1', 472).findtext('.//key/fifths') == '-2'
    assert bar(2, 'P1', 1).findtext('.//time/beats') == '6'
    assert bar(2, 'P1', 1).findtext('.//time/beat-type') == '8'
    assert 'pizz.' in [w.text for w in bar(2, 'P13', 1).findall('.//words')]
    assert any('Allegro vivace assai' in (w.text or '') for w in bar(2, 'P1', 59).findall('.//words'))
    assert any('Tempo I' in (w.text or '') for w in bar(2, 'P1', 146).findall('.//words'))
    assert bar(3, 'P1', 252).findtext('.//key/fifths') == '-2'
    return {'score_facts_checked': True, 'human_listening': 'pending',
            'method': '逐项对照保留 MusicXML 的音高、谱号、节拍与文字记号，并核验 canonical MEI 实音事件和全部印刷小节号映射。',
            'edition_note': '修订版本待校核。首乐章669个小节元素对应印刷号1–666；重复编号按同一印刷小节的全部分段定位，不套用网络文章小节总数。',
            'navigation_note': '导航依速度、织体和明确谱面标记划分，未声称每个接缝都是唯一的奏鸣曲式边界。'}


def make_card(spec, index, mapping, sources):
    segments = []
    for n, desc in enumerate(spec['segments']):
        a, b = measure_range(index, mapping, *desc['measures'])
        segment = validate_segment(Segment(id=f"{spec['id']}-s{n+1}", label=desc['label'],
            score_version=index['version'], start=index['measures'][a]['start'], end=index['measures'][b]['end'],
            staffs=[str(v) for v in desc['staffs']], voices=[str(v) for v in desc.get('voices', [])]), index)
        if not any(e.get('playable', True) and e['id'] in set(segment.note_ids) for e in index['events']):
            raise ValueError(f"片段没有可播放音符：{spec['id']}")
        segments.append(segment)
    claims = []
    used = list(spec.get('source_ids', []))
    for n, claim in enumerate(spec['claims']):
        ids = claim.get('source_ids', [])
        for sid in ids:
            if sid not in used:
                used.append(sid)
        segment_ids = [segments[i].id for i in claim.get('segments', [])]
        if claim['evidence_type'] == 'score' and not segment_ids:
            raise ValueError('谱面事实需要可播放证据')
        if claim['evidence_type'] == 'source' and not ids:
            raise ValueError('资料论点需要现有来源')
        claims.append(Claim(id=f"{spec['id']}-c{n+1}", statement=claim['statement'], evidence_type=claim['evidence_type'],
            source_ids=ids, segment_ids=segment_ids, listening_cue=claim.get('listening_cue', spec['listen_for'])))
    return Analysis(id=spec['id'], work_id=spec['work_id'], title=spec['title'], body=spec['body'],
        kind=spec['dimensions'][0], dimensions=spec['dimensions'], scope=spec.get('scope', 'section'),
        section_id=spec.get('section_id', ''), listen_for=spec['listen_for'], claims=claims,
        sources=[Source.model_validate(sources[s]) for s in used], segments=segments, origin='seed',
        status='not_applicable' if spec.get('scope') == 'overview' else 'confirmed', review_status='unreviewed',
        listening_status='pending', verification='所列音高、时值、记号和声部位置已对照固定数字谱核验；正文解释仍待乐理复核，人工试听尚未完成。修订版本待校核。钢琴复奏不模拟真实管弦音色、自由华彩或弹性速度。')


def main(root=ROOT):
    root = Path(root)
    specification = root / 'assets/scores/tchaikovsky-op23/deep-analysis.json'
    if not specification.exists():
        return {'skipped': '柴一示例数据尚未准备'}
    data = read_json(specification)
    store = Store(root)
    works = {w['id']: w for w in store.works()}
    if any(f'tchaikovsky-op23-{n}' not in works for n in (1, 2, 3)):
        return {'skipped': '柴一三个乐章尚未全部入库'}
    indexes, mappings = {}, {}
    for movement in (1, 2, 3):
        wid = f'tchaikovsky-op23-{movement}'
        if works[wid]['score_version'] != data['score_versions'][wid]:
            return {'skipped': f'保留个人谱本：{wid}版本已变化，未迁移定位'}
        if digest(root / f'assets/scores/tchaikovsky-op23/movement-{movement}.mxl') != data['source_sha256'][wid]:
            return {'skipped': f'保留个人谱本：{wid}源谱已变化'}
        indexes[movement] = store.events(wid)
        mappings[movement] = read_json(root / f'assets/scores/tchaikovsky-op23/movement-{movement}-measure-map.json')
    audit = score_audit(indexes, mappings, root)
    sources = {s['id']: s for s in data['sources']}
    installation = data.setdefault('installation', {'notes': {}, 'guides': {}})
    for spec in data['guides']:
        movement = int(spec['work_id'][-1])
        index, mapping = indexes[movement], mappings[movement]
        sections = []
        for section in spec['sections']:
            a, b = measure_range(index, mapping, *section['measures'])
            sections.append({k: v for k, v in section.items() if k != 'measures'} | {'start_measure': a, 'end_measure': b})
        guide = Guide.model_validate({**spec, 'sections': sections, 'sources': data['sources']})
        path = root / f"assets/guides/{guide.work_id}.json"
        previous = installation['guides'].get(guide.work_id)
        if (not path.exists() and not previous) or (path.exists() and digest(path) == previous):
            if not path.exists() or read_json(path) != guide.model_dump():
                store.save_guide(guide)
                installation['guides'][guide.work_id] = digest(path)
    current = {a.id: a for a in store.all_notes()}
    installed = preserved = 0
    for spec in data['cards']:
        movement = int(spec['work_id'][-1])
        card = make_card(spec, indexes[movement], mappings[movement], sources)
        path = store.notes / card.work_id / f'{card.id}.md'
        previous = installation['notes'].get(card.id)
        if card.id in current:
            if not previous or digest(path) != previous:
                preserved += 1
                continue
            existing = current[card.id]
            if existing.model_dump(exclude={'created_at', 'updated_at'}) == card.model_dump(exclude={'created_at', 'updated_at'}):
                continue
            card.created_at = existing.created_at
        elif previous:
            preserved += 1
            continue
        store.save(card)
        installation['notes'][card.id] = digest(path)
        installed += 1
    data['verification'] = audit
    write_json(specification, data)
    store.reindex()
    result = {'installed_or_updated': installed, 'personal_or_deleted_preserved': preserved,
        'cards': len(data['cards']), 'segments': sum(len(s['segments']) for s in data['cards']), 'score_audit': audit}
    print('柴一导听示例：' + json.dumps(result, ensure_ascii=False), flush=True)
    return result


if __name__ == '__main__':
    main()
