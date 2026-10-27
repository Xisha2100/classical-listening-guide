"""Build offline scores and transparent seed notes from retained source assets."""
import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'app'))
from backend.store import Store,write_json
from backend.scores import build_score,validate_segment
from backend.models import Analysis,Segment,Source,Route

WORKS=[
 {'id':'bach-bwv847','title':'C 小调赋格','composer':'约翰·塞巴斯蒂安·巴赫','catalogue':'BWV 847','movement':'《平均律》第一卷 · 第二首赋格','era':'巴洛克','color':'#52694f','aliases':['巴赫','平均律','C小调赋格','Bach','Well Tempered Clavier','BWV847'],'description':'在三条旋律之间，听见同一主题的接力。','edition':'Urs Metzger / Peters，Noctave 数字转换','source_url':'https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=1941','file':'assets/scores/bach-bwv847/source.mxl'},
 {'id':'mozart-k265','title':'小星星变奏曲','composer':'沃尔夫冈·阿马德乌斯·莫扎特','catalogue':'K.265','movement':'主题与前三个变奏','era':'古典主义','color':'#b08d55','aliases':['小星星','莫扎特','Mozart','K265','K.300e','Ah vous dirai-je maman'],'description':'熟悉的旋律，如何变成四种不同的表情。','edition':'TAVERN 数字谱，截取前 96 小节','source_url':'https://u.osu.edu/tavern/dataset-details/','file':'assets/scores/mozart-k265/K265.xml','crop':96},
 {'id':'beethoven-op67-1','title':'第五交响曲','composer':'路德维希·范·贝多芬','catalogue':'Op.67','movement':'第一乐章 · Allegro con brio','era':'古典主义','color':'#a46248','aliases':['命运','贝五','贝多芬第五','Beethoven','Symphony 5','第五交响曲','Op67'],'description':'从四个音开始，追踪动机在乐队中的流动。','edition':'OpenScore Orchestra / Hauptstimme','source_url':'https://github.com/MarkGotham/Hauptstimme','file':'assets/scores/beethoven-op67-1/Beethoven_Op.67_1.mxl'}]

def main():
 store=Store(ROOT)
 for cfg in WORKS:
  path=ROOT/cfg['file']
  if not path.exists():print('缺少源谱',path,flush=True);continue
  old=next((w for w in store.works() if w['id']==cfg['id']),None)
  if '--rebuild' not in sys.argv and old and (store.score_dir(cfg['id'])/'events.json').exists():print('已准备',cfg['id'],flush=True);continue
  print('处理',cfg['id'],flush=True)
  version,index=build_score(path.read_bytes(),ROOT/'assets'/'generated'/cfg['id'],cfg.get('crop'))
  w={k:v for k,v in cfg.items() if k not in ('file','crop')};w['score_version']=version;w['source_sha256']=hashlib.sha256(path.read_bytes()).hexdigest();w['source_file']=cfg['file']
  store.put_work(w);print('完成',cfg['id'],len(index['events']),'音符',len(index['measures']),'小节',index['pages'],'页',flush=True)
 specs_path=ROOT/'assets'/'scores'/'seed-specs.json'
 if not specs_path.exists():return
 specs=json.loads(specs_path.read_text())
 if isinstance(specs,dict):specs=specs.get('analyses',specs.get('seeds',[]))
 ledger_path=ROOT/'assets'/'seeds-initialized.json'
 initialized=set(json.loads(ledger_path.read_text())) if ledger_path.exists() else set()
 for n,spec in enumerate(specs):
  aid=f"seed-{spec['work_id']}-{n:02d}"
  if aid in initialized:continue
  wid=spec['work_id'];index=store.events(wid);segments=[]
  for desc in spec.get('segments',[spec]):
   sm=int(desc['start_measure'])-1;em=int(desc['end_measure'])-1
   start=index['measures'][sm]['start']+float(desc.get('start_offset',0))
   end=index['measures'][em]['end'] if 'end_offset' not in desc else index['measures'][em]['start']+float(desc['end_offset'])
   seg=Segment(id=f'seed-{n}-{len(segments)}',label=desc.get('label',spec['title']),score_version=index['version'],start=start,end=end,staffs=[str(desc['staff'])] if desc.get('staff') else [],voices=[str(desc['voice'])] if desc.get('voice') else [])
   for r in desc.get('routes',[]):
    rs=index['measures'][int(r['start_measure'])-1]['start']+r.get('start_offset',0)
    re=index['measures'][int(r['end_measure'])-1]['start']+r.get('end_offset',0)
    seg.routes.append(Route(start=rs,end=re,staff=str(r['staff']),voice=r.get('voice')))
   segments.append(validate_segment(seg,index))
  aid=f'seed-{wid}-{n:02d}'
  if any(a.id==aid for a in store.all_notes(wid)):
   initialized.add(aid);continue
  source=Source(id=f'source-{wid}',kind='score',title=spec.get('source_title', 'Music Theory for the 21st-Century Classroom · Fugue Analysis' if 'pugetsound' in spec.get('source_url','') else store.work(wid)['edition']),url=spec.get('source_url',store.work(wid)['source_url']),excerpt=spec.get('evidence',''),extracted=True)
  verification=spec.get('verification','按数字谱音符核对。')
  if isinstance(verification,dict):verification=verification.get('method','')+' 标注记录：'+json.dumps(verification.get('annotation_rows',[]),ensure_ascii=False)
  verification+=' 音符和出处已核对；人工听感复核尚待完成。'
  a=Analysis(id=aid,work_id=wid,title=spec['title'],body=spec['body'],kind=spec['kind'],origin='seed',status='confirmed',sources=[source],segments=segments,verification=verification)
  store.save(a);initialized.add(aid)
 write_json(ledger_path,sorted(initialized))
 print('分析卡片',len(store.all_notes()),flush=True)
if __name__=='__main__':main()
