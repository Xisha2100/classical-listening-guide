"""One persisted MEI defines both SVG IDs and sounding note events."""
import hashlib, io, json, threading, uuid, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from functools import lru_cache
import verovio
from .models import Segment
from .store import write_json, atomic_text

NS={'m':'http://www.music-encoding.org/ns/mei'}
XMLID='{http://www.w3.org/XML/1998/namespace}id'
LOCK=threading.RLock()
OPTIONS={'expandNever':True,'transposeToSoundingPitch':True,'pageWidth':1800,'pageHeight':2400,'scale':45,'adjustPageHeight':True,'breaks':'auto','footer':'none','header':'none','xmlIdSeed':847}

def xml_bytes(data: bytes) -> bytes:
    if len(data)>20_000_000: raise ValueError('谱文件最多 20 MB')
    if data[:2]==b'PK':
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            if sum(i.file_size for i in z.infolist())>30_000_000: raise ValueError('解压后谱文件过大')
            meta=ET.fromstring(z.read('META-INF/container.xml'))
            rf=next((e for e in meta.iter() if e.tag.split('}')[-1]=='rootfile'),None)
            if rf is None: raise ValueError('MXL 缺少根乐谱')
            data=z.read(rf.attrib['full-path'])
    if b'<!ENTITY' in data.upper(): raise ValueError('乐谱不允许自定义 XML 实体')
    root=ET.fromstring(data)
    if root.tag not in ('score-partwise',): raise ValueError('请导入 MusicXML score-partwise 或 MXL')
    return ET.tostring(root,encoding='utf-8')

def frac(values, default=0):
    if not values: return default
    n,d=values[0];return n/d

def t_at(index, q):
    points=index['timeline']
    # Segment times are derived from the same Verovio tempo map, including silence.
    import bisect
    pos=bisect.bisect_right([p['q'] for p in points],q)-1
    p=points[max(0,pos)]
    return p['t']+(q-p['q'])*60/p['tempo']

def build_score(data, out:Path, crop=None):
    try: raw=xml_bytes(data)
    except (ET.ParseError,zipfile.BadZipFile,KeyError,RuntimeError) as exc: raise ValueError('谱文件损坏或不是有效的 MusicXML／MXL') from exc
    if crop:
        root=ET.fromstring(raw)
        for p in root.findall('part'):
            for m in p.findall('measure')[crop:]: p.remove(m)
        raw=ET.tostring(root,encoding='utf-8')
    version=hashlib.sha256(raw+json.dumps(OPTIONS,sort_keys=True).encode()+b'index-v2').hexdigest()[:16]
    out=out/version;out.mkdir(parents=True,exist_ok=True)
    atomic_text(out/'normalized.musicxml',raw.decode())
    with LOCK:
        tk=verovio.toolkit();tk.setResourcePath(str(Path(verovio.__file__).parent/'data'));tk.setOptions(OPTIONS)
        if not tk.loadData(raw.decode()): raise ValueError('Verovio 无法读取此乐谱')
        mei=tk.getMEI();atomic_text(out/'score.mei',mei)
        tk.renderToMIDI()
        tree=ET.fromstring(mei)
        tm=tk.renderToTimemap({'includeMeasures':True,'includeRests':True})
        tempo=120;timeline=[];measure_starts={}
        for x in tm:
            tempo=x.get('tempo',tempo)
            timeline.append({'q':x['qstamp'],'t':x['tstamp']/1000,'tempo':tempo})
            if x.get('measureOn'): measure_starts[x['measureOn']]=(x['qstamp'],x['tstamp']/1000)
        staffs={}
        for s in tree.findall('.//m:staffDef',NS):
            sid=s.get('n')
            if sid not in staffs:
                label=''.join(s.find('m:label',NS).itertext()).strip() if s.find('m:label',NS) is not None else f'谱表 {sid}'
                staffs[sid]={'id':sid,'label':label,'voices':[]}
        measures=[];events=[]
        for i,m in enumerate(tree.findall('.//m:measure',NS)):
            mid=m.get(XMLID); q,sec=measure_starts.get(mid,(measures[-1]['start'] if measures else 0,0))
            page=tk.getPageWithElement(mid)
            measures.append({'index':i,'label':m.get('n',str(i+1)),'id':mid,'start':q,'page':page})
            for staff in m.findall('m:staff',NS):
                sid=staff.get('n')
                for layer in staff.findall('m:layer',NS):
                    voice=layer.get('n','1')
                    if voice not in staffs[sid]['voices']: staffs[sid]['voices'].append(voice)
                    for note in layer.findall('.//m:note',NS):
                        nid=note.get(XMLID);times=tk.getTimesForElement(nid);midi=tk.getMIDIValuesForElement(nid)
                        if 'pitch' not in midi or not times.get('qfracOn'):continue
                        onset=frac(times['qfracOn']);duration=frac(times.get('qfracDuration'))
                        events.append({'id':nid,'pitch':midi['pitch'],'onset':onset,'duration':duration,'staff':sid,'voice':voice,'measure':i,'page':page,'playable':True,'velocity':min(1,float(note.get('vel','80'))/127),'name':note.get('pname','').upper()+note.get('oct','')})
        byid={e['id']:e for e in events}
        ties={}
        for tie in tree.findall('.//m:tie',NS):
            a=tie.get('startid','').lstrip('#');b=tie.get('endid','').lstrip('#')
            if a in byid and b in byid:ties[a]=b;byid[b]['playable']=False
        for e in events:
            end=e['onset']+e['duration'];cur=e['id'];seen=set()
            while cur in ties and cur not in seen:
                seen.add(cur);cur=ties[cur];end=max(end,byid[cur]['onset']+byid[cur]['duration'])
            e['sounding_duration']=end-e['onset']
        if not events or not timeline: raise ValueError('谱文件没有可播放的音符')
        duration=max([e['onset']+e['duration'] for e in events]+[p['q'] for p in timeline])
        for i,m in enumerate(measures):m['end']=measures[i+1]['start'] if i+1<len(measures) else duration
        index={'version':version,'notation':'concert','events':events,'measures':measures,'staffs':list(staffs.values()),'timeline':timeline,'duration':duration,'pages':tk.getPageCount(),'engine':tk.getVersion()}
        write_json(out/'events.json',index)
        # Persist every page during ingestion: no layout drift between imported IDs and UI.
        for p in range(1,tk.getPageCount()+1): atomic_text(out/f'page-{p}.svg',tk.renderToSVG(p))
    return version,index

def validate_segment(seg:Segment, index):
    if seg.score_version!=index['version']:raise ValueError('谱本版本不一致，请重新定位')
    if not (0<=seg.start<seg.end<=index['duration']+1e-6):raise ValueError('片段范围超出乐谱')
    known={s['id']:s for s in index['staffs']}
    if any(s not in known for s in seg.staffs):raise ValueError('片段包含不存在的谱表')
    for r in seg.routes:
        if not seg.start<=r.start<r.end<=seg.end or r.staff not in known: raise ValueError('无效的声部接续范围')
        if r.voice and r.voice not in known[r.staff]['voices']:raise ValueError('不存在的声部')
    if seg.voices and any(v not in {v for s in index['staffs'] for v in s['voices']} for v in seg.voices):raise ValueError('不存在的声部')
    event_ids={e['id'] for e in index['events']}
    if any(n not in event_ids for n in seg.note_ids):raise ValueError('片段引用不存在的音符')
    notes=[e for e in index['events'] if seg.start<=e['onset']<seg.end and matches(e,seg)]
    if not notes:raise ValueError('该范围及声部内没有音符')
    seg.note_ids=[e['id'] for e in notes]
    seg.id=seg.id or uuid.uuid4().hex
    seg.start_measure=next((m['index'] for m in index['measures'] if m['start']<=seg.start<m['end']),0)
    seg.end_measure=next((m['index'] for m in index['measures'] if m['start']<seg.end<=m['end']),len(index['measures'])-1)
    return seg

def matches(e,seg):
    if seg.routes:return any(r.start<=e['onset']<r.end and r.staff==e['staff'] and (not r.voice or r.voice==e['voice']) for r in seg.routes)
    return (not seg.staffs or e['staff'] in seg.staffs) and (not seg.voices or e['voice'] in seg.voices)

def features(index, seg):
    from music21 import stream,note,chord
    seg=validate_segment(seg,index)
    selected_ids=set(seg.note_ids)
    selected=[e for e in index['events'] if e['id'] in selected_ids and e['playable']]
    st=stream.Stream()
    for e in selected:
        n=note.Note(e['pitch']);n.quarterLength=max(.001,e['duration']);st.insert(e['onset']-seg.start,n)
    try:k=st.analyze('key');key={'name':str(k),'correlation':round(k.correlationCoefficient,3)}
    except Exception:key=None
    return {'time_unit':'quarter_note','key_estimate':key,'note_count':len(selected),'pitch_range':[min(e['pitch'] for e in selected),max(e['pitch'] for e in selected)] if selected else None,'events':[{'id':e['id'],'pitch':e['pitch'],'onset':round(e['onset']-seg.start,5),'duration':e['duration'],'staff':e['staff'],'voice':e['voice']} for e in selected]}

def similar(index,seg):
    seg=validate_segment(seg,index)
    chosen=sorted([e for e in index['events'] if e['id'] in seg.note_ids and e['playable']],key=lambda e:e['onset'])
    if len(chosen)<3 or len(chosen)>64:raise ValueError('请选择单声部的 3—64 个音符')
    if len({e['onset'] for e in chosen})!=len(chosen):raise ValueError('相似检索需要单旋律，请选择一个谱表与声部')
    def signature(es):
        base=es[0]['duration'] or 1
        return ([es[i+1]['pitch']-es[i]['pitch'] for i in range(len(es)-1)], [round(e['duration']/base,4) for e in es], [round((e['onset']-es[0]['onset'])/base,4) for e in es])
    sig=signature(chosen);out=[]
    for s in index['staffs']:
        for v in s['voices']:
            ns=sorted([e for e in index['events'] if e['staff']==s['id'] and e['voice']==v and e['playable']],key=lambda e:e['onset'])
            for i in range(len(ns)-len(chosen)+1):
                chunk=ns[i:i+len(chosen)]
                if len({e['onset'] for e in chunk})!=len(chunk) or signature(chunk)!=sig:continue
                if chunk[0]['id']==chosen[0]['id']:continue
                result=Segment(label=f"移调 {chunk[0]['pitch']-chosen[0]['pitch']:+d} 半音 · 第 {index['measures'][chunk[0]['measure']]['label']} 小节",score_version=index['version'],start=chunk[0]['onset'],end=chunk[-1]['onset']+chunk[-1]['duration'],staffs=[s['id']],voices=[v])
                out.append(validate_segment(result,index).model_dump())
                if len(out)>=20:return out
    return out
