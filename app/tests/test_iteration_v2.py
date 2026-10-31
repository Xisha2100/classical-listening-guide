import pytest
from backend.models import Analysis, Source, Guide, GuideSection, Segment
from backend.project import save_analysis
from backend.scores import features, validate_segment, build_score
from conftest import SCORE

def test_guide_sources_and_boundaries_roundtrip(store):
    guide=Guide(work_id='test-work',overview='完整导听',sources=[Source(id='ref',title='谱本')],sections=[GuideSection(id='intro',title='开始',start_measure=0,end_measure=1,source_ids=['ref'])])
    store.save_guide(guide)
    assert store.guide('test-work')['sections'][0]['end_measure']==1
    guide.sections[0].end_measure=99
    with pytest.raises(ValueError):store.save_guide(guide)
    assert store.guide('test-work')['sections'][0]['end_measure']==1

def test_harmonic_features_include_sustained_tie_and_context(store):
    index=store.events('test-work');measure=index['measures'][2]
    seg=validate_segment(Segment(score_version=index['version'],start=measure['start'],end=measure['end']),index)
    result=features(index,seg)
    # Concert F5 continues from preceding bar. A tie continuation is not a new attack.
    assert result['events'][0]['pitch']==77
    assert result['events'][0]['onset']==0 and result['events'][0]['duration']==1
    assert result['verticalities'][0]['bass']==77
    assert result['measures'][0]['staff_context']['1']['meter']['unit']=='4'
    assert result['key_estimate_is_harmonic_proof'] is False

def test_meter_changes_propagate_without_changing_ids(tmp_path):
    changed=SCORE.replace(b'<measure number="2">',b'<measure number="2"><attributes><time><beats>3</beats><beat-type>4</beat-type></time></attributes>')
    _,index=build_score(changed,tmp_path/'meter')
    measure=index['measures'][2]
    segment=Segment(score_version=index['version'],start=measure['start'],end=measure['end'])
    result=features(index,segment)
    assert result['measures'][0]['staff_context']['1']['meter']['count']=='3'


def test_tchaikovsky_score_audit_and_seed_anchors():
    import importlib.util
    from pathlib import Path
    from backend.store import Store, read_json
    from backend.scores import validate_segment
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location('tcha_seeds', root / 'app/scripts/prepare_tchaikovsky_v2.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    store = Store(root)
    indexes = {n: store.events(f'tchaikovsky-op23-{n}') for n in (1, 2, 3)}
    maps = {n: read_json(root / f'assets/scores/tchaikovsky-op23/movement-{n}-measure-map.json') for n in indexes}
    assert module.score_audit(indexes, maps, root)['score_facts_checked']
    data = read_json(root / 'assets/scores/tchaikovsky-op23/deep-analysis.json')
    sources = {s['id']: s for s in data['sources']}
    assert len(data['cards']) == 13
    for item in data['cards']:
        n = int(item['work_id'][-1])
        card = module.make_card(item, indexes[n], maps[n], sources)
        for segment in card.segments:
            validate_segment(segment, indexes[n])
        assert card.listening_status == 'pending'


def test_guide_hierarchy_rejects_cycles_and_out_of_parent_ranges(store):
    parent=GuideSection(id='form',title='呈示部',start_measure=0,end_measure=2)
    child=GuideSection(id='theme',parent_id='form',title='主题',start_measure=1,end_measure=2)
    guide=Guide(work_id='test-work',sections=[parent,child])
    store.save_guide(guide)
    assert store.guide('test-work')['sections'][1]['parent_id']=='form'
    child.parent_id='missing'
    with pytest.raises(ValueError,match='上级章节不存在'):store.save_guide(guide)
    child.parent_id='form';parent.parent_id='theme'
    with pytest.raises(ValueError):store.save_guide(guide)
    parent.parent_id='';parent.end_measure=1
    with pytest.raises(ValueError,match='子章节'):store.save_guide(guide)
    assert store.guide('test-work')['sections'][0]['end_measure']==2


def test_model_provenance_and_segment_roles_persist(store):
    index=store.events('test-work')
    seg=validate_segment(Segment(score_version=index['version'],start=0,end=2,role='phrase',boundary_note='弱起至收束',source_ids=['ref']),index)
    card=Analysis(work_id='test-work',title='完整句',origin='model',analysis_model='gpt-6-sol',analysis_run_id='test',segments=[seg],sources=[Source(id='ref',kind='score')])
    stored=save_analysis(store,card)
    changed=stored.model_copy(deep=True);changed.analysis_model='forged'
    with pytest.raises(ValueError,match='来源与模型'):save_analysis(store,changed)
    assert store.get_note(stored.id).segments[0].role=='phrase'
    changed=stored.model_copy(deep=True);changed.sources=[]
    with pytest.raises(ValueError,match='不存在'):save_analysis(store,changed)
    with pytest.raises(ValueError,match='只有模型'):save_analysis(store,Analysis(work_id='test-work',title='人工笔记',analysis_model='fake'))
