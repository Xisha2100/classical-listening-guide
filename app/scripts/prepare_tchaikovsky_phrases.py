"""Install the GPT-6 Sol phrase analysis; preserve personal edits and archive old excerpts."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'app'))
from backend.models import Analysis, Claim, Guide, Segment, Source
from backend.scores import validate_segment
from backend.store import Store, read_json, write_json
from prepare_tchaikovsky_v2 import measure_range


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bounds(spec, index, mapping):
    first, last = spec['measures']
    a, b = measure_range(index, mapping, first, last)
    if spec.get('ordinal_measures'):
        a, b = (n - 1 for n in spec['ordinal_measures'])
        if not 0 <= a <= b < len(mapping):
            raise ValueError('Invalid ordinal range')
        if mapping[a]['printed_measure'] != str(first) or mapping[b]['printed_measure'] != str(last):
            raise ValueError('Printed labels do not match ordinal range')
    return a, b


def make_segment(spec, index, mapping, sid):
    a, b = bounds(spec, index, mapping)
    start = index['measures'][a]['start'] + spec.get('start_offset', 0)
    end = index['measures'][b]['start'] + spec['end_offset'] if 'end_offset' in spec else index['measures'][b]['end']
    if not index['measures'][a]['start'] <= start < index['measures'][a]['end']:
        raise ValueError('Start offset outside first measure')
    if not index['measures'][b]['start'] < end <= index['measures'][b]['end']:
        raise ValueError('End offset outside last measure')
    if spec['role'] in ('theme', 'phrase') and not spec.get('boundary_note'):
        raise ValueError('Complete listening spans need boundary evidence')
    return validate_segment(Segment(
        id=sid, score_version=index['version'], label=spec['label'], start=start, end=end,
        staffs=[str(s) for s in spec.get('staffs', [])], voices=[str(v) for v in spec.get('voices', [])],
        routes=spec.get('routes', []), role=spec['role'], boundary_note=spec.get('boundary_note', ''),
        boundary_status=spec.get('certainty', 'candidate'),
        source_ids=spec.get('source_ids', [])), index)


def build_card(spec, index, mapping, sources, run_id):
    segments = [make_segment(s, index, mapping, f"{spec['id']}-s{i+1}") for i, s in enumerate(spec['segments'])]
    source_ids = list(spec.get('source_ids', []))
    claims = []
    for n, claim in enumerate(spec['claims']):
        ids = [segments[i].id for i in claim.get('segments', [])]
        refs = claim.get('source_ids', [])
        if claim['evidence_type'] == 'score' and not ids:
            raise ValueError('Score claim needs evidence')
        if claim['evidence_type'] == 'source' and not refs:
            raise ValueError('Source claim needs reference')
        source_ids.extend(refs)
        claims.append(Claim(id=f"{spec['id']}-c{n+1}", statement=claim['statement'], evidence_type=claim['evidence_type'],
                            source_ids=refs, segment_ids=ids, listening_cue=claim.get('listening_cue', spec['listen_for'])))
    for segment in segments:
        source_ids.extend(segment.source_ids)
    source_ids = list(dict.fromkeys(source_ids))
    if any(s not in sources for s in source_ids):
        raise ValueError('Unknown source')
    return Analysis(id=spec['id'], work_id=spec['work_id'], title=spec['title'], body=spec['body'],
                    kind=spec['dimensions'][0], dimensions=spec['dimensions'], scope=spec.get('scope', 'segment'),
                    section_id=spec.get('section_id', ''), listen_for=spec['listen_for'], claims=claims,
                    sources=[sources[s] for s in source_ids], segments=segments, origin='model',
                    analysis_model='gpt-6-sol', analysis_run_id=run_id,
                    status='suggested' if segments else 'not_applicable', review_status='unreviewed', listening_status='pending',
                    verification='GPT-6 Sol 根据所列资料与固定数字谱提出曲式和乐句边界；程序已检查谱本、印刷编号、声部和音符范围。边界理由见各谱例，资料编号差异已注明。尚未完成人工乐理复核及听感验收。')


def main(root=ROOT, dry_run=False):
    root = Path(root)
    folder = root / 'assets/scores/tchaikovsky-op23'
    spec_path = folder / 'phrase-analysis.json'
    if not spec_path.exists():
        return {'skipped': 'GPT-6 Sol 分析资料尚未准备'}
    data = read_json(spec_path)
    store = Store(root)
    ledger_path = folder / 'phrase-installation.json'
    ledger = read_json(ledger_path) if ledger_path.exists() else {'notes': {}, 'guides': {}, 'archived': []}
    old_data = read_json(folder / 'deep-analysis.json')
    old_ledger = old_data.get('installation', {})
    sources = {s['id']: Source.model_validate(s) for s in data['sources']}
    if len(sources) != len(data['sources']):
        raise ValueError('Duplicate source IDs')
    indexes, mappings = {}, {}
    for n in (1, 2, 3):
        wid = f'tchaikovsky-op23-{n}'
        work = store.work(wid)
        if digest(root / work['source_file']) != work['source_sha256']:
            raise ValueError(f'{wid}: source score changed; reanalysis required')
        indexes[wid] = store.events(wid)
        mappings[wid] = read_json(folder / f'movement-{n}-measure-map.json')
        if indexes[wid]['version'] != data['score_versions'][wid]:
            raise ValueError(f'{wid}: score version mismatch')
    guides = {}
    for spec in data['guides']:
        wid = spec['work_id']; sections = []
        for section in spec['sections']:
            a, b = bounds(section, indexes[wid], mappings[wid])
            sections.append({**section, 'start_measure': a, 'end_measure': b})
        guides[wid] = Guide.model_validate({**spec, 'sections': sections, 'sources': list(sources.values())})
    if set(guides) != set(indexes):
        raise ValueError('All three movements need a guide')
    run_id = data.get('analysis_run_id', 'tchaikovsky-phrases-2026-10-31')
    cards = [build_card(c, indexes[c['work_id']], mappings[c['work_id']], sources, run_id) for c in data['cards']]
    if len({c.id for c in cards}) != len(cards):
        raise ValueError('Duplicate card IDs')
    for card in cards:
        if card.section_id and card.section_id not in {s.id for s in guides[card.work_id].sections}:
            raise ValueError('Unknown guide section')
    blocked = []
    for wid in guides:
        path = store.assets / f'guides/{wid}.json'
        expected = {ledger['guides'].get(wid), old_ledger.get('guides', {}).get(wid)}
        if path.exists() and digest(path) not in expected:
            blocked.append(wid)
    if blocked:
        raise ValueError('保留已编辑的导听目录；请先合并目录再安装：' + ', '.join(blocked))
    # Validate every hierarchy before any writes (using the same API invariants).
    for guide in guides.values():
        sections = {s.id: s for s in guide.sections}
        if len(sections) != len(guide.sections):
            raise ValueError('Duplicate guide IDs')
        for section in guide.sections:
            if any(ref not in sources for ref in section.source_ids): raise ValueError('Unknown section reference')
            seen = {section.id}; current = section
            while current.parent_id:
                parent = sections.get(current.parent_id)
                if not parent or parent.id in seen: raise ValueError('Invalid hierarchy')
                if not parent.start_measure <= current.start_measure <= current.end_measure <= parent.end_measure:
                    raise ValueError('Child outside parent')
                seen.add(parent.id); current = parent
    if dry_run:
        return {'valid': True, 'cards': len(cards), 'segments': sum(len(c.segments) for c in cards), 'sections': sum(len(g.sections) for g in guides.values())}
    for wid, guide in guides.items():
        store.save_guide(guide)
        ledger['guides'][wid] = digest(store.assets / f'guides/{wid}.json')
    current = {c.id: c for c in store.all_notes()}
    changed = preserved = 0
    for card in cards:
        path = store.notes / card.work_id / f'{card.id}.md'
        previous = ledger['notes'].get(card.id)
        if card.id in current:
            if not previous or digest(path) != previous:
                preserved += 1; continue
            existing = current[card.id]
            if existing.model_dump(exclude={'created_at','updated_at'}) == card.model_dump(exclude={'created_at','updated_at'}):
                continue
            card.created_at = existing.created_at
        elif previous:
            preserved += 1; continue
        store.save(card)
        ledger['notes'][card.id] = digest(path)
        changed += 1
    for old in old_data['cards']:
        path = store.notes / old['work_id'] / f"{old['id']}.md"
        previous = old_ledger.get('notes', {}).get(old['id'])
        if path.exists() and previous and digest(path) == previous:
            archive = path.parent / 'archive' / 'v2' / path.name
            archive.parent.mkdir(parents=True, exist_ok=True)
            if archive.exists() and digest(archive) != previous:
                raise ValueError('Archive already contains a different version')
            path.replace(archive)
            ledger['archived'].append(old['id'])
    ledger['archived'] = sorted(set(ledger['archived']))
    ledger['analysis_sha256'] = digest(spec_path)
    write_json(ledger_path, ledger)
    store.reindex()
    return {'installed_or_updated': changed, 'personal_or_deleted_preserved': preserved, 'cards': len(cards), 'archived_v2': len(ledger['archived']), 'analysis_model': 'gpt-6-sol'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    print(json.dumps(main(dry_run=args.check), ensure_ascii=False))
