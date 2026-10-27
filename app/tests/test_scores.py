import json
import pytest
from backend.scores import build_score,validate_segment,similar,t_at,xml_bytes
from backend.models import Segment
from conftest import ROOT,SCORE

def segment(index,**kw):
 return Segment(score_version=index['version'],start=0,end=index['duration'],**kw)

def test_actual_pitch_pickup_chord_tuplet_tie_tempo_repeat(score):
 path,idx=score;es=idx['events']
 assert len(idx['measures'])==3 # repeat not expanded
 assert idx['measures'][0]['label']=='0'
 assert idx['measures'][1]['start']==1
 assert es[0]['onset']==.5 and es[0]['pitch']==67
 assert es[1]['onset']==es[2]['onset']==1
 assert es[3]['duration']==pytest.approx(1/3)
 assert es[-2]['sounding_duration']==3 and not es[-1]['playable']
 assert t_at(idx,5)==pytest.approx(5) and t_at(idx,6)==pytest.approx(5.5)
 assert idx['duration']==9 # trailing rests retained
 for e in es:assert f'id="{e["id"]}"' in (path/f'page-{e["page"]}.svg').read_text()

def test_deterministic_ids(score,tmp_path):
 _,idx=score;_,other=build_score(SCORE,tmp_path/'other')
 assert idx==other

@pytest.mark.parametrize('change',[{'score_version':'wrong'},{'end':1000},{'staffs':['999']},{'voices':['999']},{'note_ids':['fabricated']},{'routes':[{'start':0,'end':1,'staff':'99'}]}])
def test_reject_invalid_anchor(score,change):
 _,idx=score;args={'score_version':idx['version'],'start':0,'end':2,**change}
 with pytest.raises(ValueError):validate_segment(Segment(**args),idx)

def test_polyphonic_similarity_rejected(score):
 _,idx=score
 with pytest.raises(ValueError,match='单旋律'):similar(idx,segment(idx))

def test_sources_are_not_executable():
 with pytest.raises(ValueError):xml_bytes(b'<other/>')
 with pytest.raises(ValueError):xml_bytes(b'<!DOCTYPE a [<!ENTITY x "x">]><score-partwise/>')

def test_corpus_15_notes_and_svg_alignment():
 from backend.store import Store
 s=Store(ROOT);notes=s.all_notes();assert not s.errors
 for wid,measures in [('bach-bwv847',31),('mozart-k265',96),('beethoven-op67-1',502)]:
  idx=s.events(wid);cards=[a for a in notes if a.work_id==wid and a.origin=='seed'];assert len(cards)==5
  assert len(idx['measures'])==measures
  pages={}
  for a in cards:
   assert a.sources and a.verification
   for seg in a.segments:
    validate_segment(seg,idx)
    for e in idx['events']:
     if e['id'] not in seg.note_ids:continue
     pages.setdefault(e['page'],(s.score_dir(wid)/f'page-{e["page"]}.svg').read_text())
     assert f'id="{e["id"]}"' in pages[e['page']]
