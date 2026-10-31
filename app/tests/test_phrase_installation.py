"""Migration must never replace a user's edited notes with a new model analysis."""
import hashlib
import importlib.util
import sys
import shutil
from pathlib import Path
from backend.models import Analysis, Source
from backend.store import write_json, read_json


def test_phrase_installation_archives_only_unedited_seeds_and_preserves_edits(store):
    scripts=Path(__file__).resolve().parents[1]/'scripts'
    sys.path.insert(0,str(scripts))
    spec=importlib.util.spec_from_file_location('phrase_install',scripts/'prepare_tchaikovsky_phrases.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    root=store.root;folder=store.assets/'scores/tchaikovsky-op23';folder.mkdir(parents=True)
    fixture=store.work('test-work');idx=store.events('test-work')
    source=folder/'fixture.xml';source.write_text('<fixture/>')
    cards=[];guides=[];old_cards=[];old_hashes={};versions={}
    for n in (1,2,3):
        wid=f'tchaikovsky-op23-{n}';versions[wid]=idx['version']
        shutil.copytree(store.score_dir('test-work'),store.assets/'generated'/wid/idx['version'])
        store.put_work({**fixture,'id':wid,'source_file':str(source.relative_to(root)),'source_sha256':module.digest(source)})
        write_json(folder/f'movement-{n}-measure-map.json',[{'ordinal':m['index']+1,'printed_measure':m['label']} for m in idx['measures']])
        guides.append({'work_id':wid,'overview':'新分析','source_ids':['score'],'sections':[{'id':'whole','title':'全曲','measures':[0,2],'source_ids':['score']}]})
        cards.append({'id':f'new-{n}','work_id':wid,'title':'完整乐句','body':'先句后证据','dimensions':['主题'],'scope':'segment','section_id':'whole','listen_for':'终止','source_ids':['score'],'claims':[{'statement':'观察','evidence_type':'score','segments':[0]}],'segments':[{'label':'乐句','role':'phrase','measures':[0,1],'start_offset':.5,'end_offset':2,'staffs':['1'],'boundary_note':'弱起与延音','source_ids':['score'],'certainty':'supported'}]})
        old=store.save(Analysis(id=f'old-{n}',work_id=wid,title='旧短例',body='旧内容',origin='seed'))
        path=store.notes/wid/f'{old.id}.md'
        old_cards.append({'id':old.id,'work_id':wid});old_hashes[old.id]=module.digest(path)
    changed=store.get_note('old-2');changed.body='用户改过';store.save(changed)
    write_json(folder/'deep-analysis.json',{'cards':old_cards,'installation':{'notes':old_hashes,'guides':{}}})
    write_json(folder/'phrase-analysis.json',{'score_versions':versions,'sources':[Source(id='score',kind='score').model_dump()],'cards':cards,'guides':guides})
    assert module.main(root,dry_run=True)['valid']
    assert not (store.notes/'tchaikovsky-op23-1'/'new-1.md').exists()
    result=module.main(root)
    assert result['cards']==3 and result['archived_v2']==2
    assert store.get_note('old-2').body=='用户改过'
    assert (store.notes/'tchaikovsky-op23-1/archive/v2/old-1.md').exists()
    first=store.get_note('new-1');assert first.analysis_model=='gpt-6-sol'
    assert first.segments[0].start==.5 and first.segments[0].end==3
    first.body='用户修正主题';store.save(first)
    store.delete('new-3')
    again=module.main(root)
    assert again['personal_or_deleted_preserved']==2
    assert store.get_note('new-1').body=='用户修正主题'
    assert not (store.notes/'tchaikovsky-op23-3/new-3.md').exists()


def test_tchaikovsky_real_phrase_boundaries_and_sources():
    from backend.store import Store
    scripts=Path(__file__).resolve().parents[1]/'scripts'
    sys.path.insert(0,str(scripts))
    import prepare_tchaikovsky_phrases as installer
    root=scripts.parents[1];data=read_json(root/'assets/scores/tchaikovsky-op23/phrase-analysis.json')
    assert data['analysis_model']=='gpt-6-sol'
    store=Store(root);sources={s['id']:Source.model_validate(s) for s in data['sources']}
    indexes={n:store.events(f'tchaikovsky-op23-{n}') for n in (1,2,3)}
    maps={n:read_json(root/f'assets/scores/tchaikovsky-op23/movement-{n}-measure-map.json') for n in indexes}
    built={}
    for spec in data['cards']:
        n=int(spec['work_id'][-1]);card=installer.build_card(spec,indexes[n],maps[n],sources,'test')
        assert all(s.boundary_note and s.source_ids for s in card.segments)
        assert card.analysis_model=='gpt-6-sol' and card.listening_status=='pending'
        built[card.id]=card
    opening=built['sol-1-opening-song'].segments[0];idx=indexes[1]
    assert opening.start==idx['measures'][6]['start']+1.5
    assert opening.end==idx['measures'][15]['start']+.5
    next_phrase=[e['id'] for e in idx['events'] if e['staff']=='14' and e['measure']==15 and e['onset']>=idx['measures'][15]['start']+1]
    assert next_phrase and not set(next_phrase)&set(opening.note_ids)
    clarinet=built['sol-1-secondary-one'].segments[0]
    assert clarinet.staffs==['4']
    first=[e['pitch'] for e in idx['events'] if e['id'] in clarinet.note_ids and e['playable']][:3]
    assert first==[73,69,70]  # Concert Db–A–Bb, not the piano accompaniment.
    assert any(s.role=='evidence' for c in built.values() for s in c.segments)
    assert any(s.boundary_status=='candidate' for c in built.values() for s in c.segments)
