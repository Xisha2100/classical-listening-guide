import json
import subprocess
import sys
from pathlib import Path

import pytest
from backend.models import Analysis, Source, Claim, Segment
from backend.project import check_project, save_analysis
from backend.store import Store
from backend.scores import validate_segment

ROOT = Path(__file__).resolve().parents[2]


def test_authoring_checks_claims_and_invalidates_review(store):
    a = save_analysis(store, Analysis(work_id='test-work', title='总览', scope='overview', kind='曲式',
        body='结构概览', sources=[Source(id='book', title='导听书', excerpt='原文', summary='个人理解')]))
    assert a.status == 'not_applicable' and a.dimensions == ['曲式']
    a.claims = [Claim(statement='资料观点', evidence_type='source', source_ids=['missing'])]
    with pytest.raises(ValueError, match='不存在'): save_analysis(store, a)
    a.claims[0].source_ids = ['book']; a = save_analysis(store, a)
    a.review_status = 'checked'; a = save_analysis(store, a)
    assert a.review_status == 'checked'
    a.sources[0].excerpt = '修订原文'; a = save_analysis(store, a)
    assert a.review_status == 'unreviewed'
    assert check_project(Store(store.root, read_only=True))['ok']


def test_check_rejects_stale_note_ids_without_repairing_content(store):
    index = store.events('test-work')
    segment = validate_segment(Segment(score_version=index['version'], start=0, end=2), index)
    a = save_analysis(store, Analysis(work_id='test-work', title='片段', segments=[segment]))
    a.segments[0].note_ids = [index['events'][-1]['id']]
    store.save(a)  # Simulate an erroneous manual file edit that bypasses validation.
    path = store.notes / a.work_id / f'{a.id}.md'
    before = path.read_bytes()
    result = check_project(Store(store.root, read_only=True))
    assert not result['ok'] and '索引与范围不一致' in result['errors'][0]
    assert path.read_bytes() == before


def test_read_only_store_does_not_upgrade_files_or_write_notes(store):
    path = store.score_dir('test-work') / 'events.json'
    data = json.loads(path.read_text()); data['feature_schema'] = 0
    path.write_text(json.dumps(data)); before = path.read_bytes()
    reader = Store(store.root, read_only=True)
    assert reader.events('test-work')['feature_schema'] > 0
    assert path.read_bytes() == before
    with pytest.raises(ValueError, match='阅读器不能写入'):
        reader.save(Analysis(work_id='test-work', title='不应保存'))


def test_cli_save_export_selection_features_and_check(store, tmp_path):
    def cli(*args):
        return subprocess.run([sys.executable, str(ROOT/'app/scripts/project.py'), '--root', str(store.root), *args], capture_output=True, text=True)
    payload = tmp_path/'analysis.json'
    payload.write_text(json.dumps({'work_id':'test-work','title':'Codex 记录','body':'保留资料与自己的解释','origin':'model','analysis_model':'test-model','analysis_run_id':'test-session'}))
    result = cli('save-analysis', '--file', str(payload))
    assert result.returncode == 0, result.stderr
    saved = json.loads(result.stdout)
    exported = tmp_path/'export.json'
    result = cli('export-analysis','--id',saved['id'],'--output',str(exported))
    assert result.returncode == 0 and json.loads(exported.read_text())['body']=='保留资料与自己的解释'
    segment = tmp_path/'selection.json'
    result = cli('segment','--work','test-work','--from-measure','1','--to-measure','2','--staff','1','--output',str(segment))
    assert result.returncode == 0, result.stderr
    result = cli('features','--work','test-work','--segment',str(segment))
    assert result.returncode == 0 and json.loads(result.stdout)['note_count'] > 0, result.stderr
    result = cli('check')
    assert result.returncode == 0 and json.loads(result.stdout)['analyses'] == 1, result.stderr
    result = cli('segment','--work','test-work','--from-measure','9','--to-measure','10')
    assert result.returncode != 0 and '超出谱本' in result.stderr
