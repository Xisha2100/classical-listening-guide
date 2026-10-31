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
FEATURE_SCHEMA=4
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
        tk=verovio.toolkit(False);tk.setResourcePath(str(Path(verovio.__file__).parent/'data'));tk.setOptions(OPTIONS)
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
                        events.append({'id':nid,'pitch':midi['pitch'],'onset':onset,'duration':duration,'staff':sid,'voice':voice,'measure':i,'page':page,'playable':bool(note.get('pname')),'velocity':min(1,float(note.get('vel','80'))/127),'name':note.get('pname','').upper()+note.get('oct','')})
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
        enrich_index(index,tree)
        write_json(out/'events.json',index)
        # Persist every page during ingestion: no layout drift between imported IDs and UI.
        for p in range(1,tk.getPageCount()+1): atomic_text(out/f'page-{p}.svg',tk.renderToSVG(p))
    return version,index

def enrich_index(index,tree):
    """Add facts from the canonical MEI without changing score versions or note IDs."""
    contexts={};default={};last_context=None;by_measure={m['id']:m for m in index['measures']}
    notes={e['id']:e for e in index['events']};marks=[]
    def attrs(container,previous):
        result=dict(previous)
        meter=container.find('m:meterSig',NS);key=container.find('m:keySig',NS)
        if meter is not None:result['meter']={'count':meter.get('count',''),'unit':meter.get('unit',''),'symbol':meter.get('sym','')}
        if key is not None:result['key_signature']=key.get('sig','')
        return result
    def walk(node):
        nonlocal default,last_context
        tag=node.tag.split('}')[-1]
        if tag=='scoreDef':
            new_default=attrs(node,default)
            changed={k:v for k,v in new_default.items() if default.get(k)!=v}
            contexts.update({sid:{**c,**changed} for sid,c in contexts.items()})
            default=new_default
            for s in node.findall('.//m:staffDef',NS):contexts[s.get('n')]=attrs(s,{**default,**contexts.get(s.get('n'),{})})
            return
        if tag=='measure':
            m=by_measure.get(node.get(XMLID))
            if m is None:return
            for staff in node.findall('m:staff',NS):
                sid=staff.get('n');current={**default,**contexts.get(sid,{})}
                for layer in staff.findall('m:layer',NS):current=attrs(layer,current)
                contexts[sid]=current
            current_context={sid:dict(c) for sid,c in contexts.items()}
            if current_context!=last_context:m['staff_context']=current_context
            else:m.pop('staff_context',None)
            last_context=current_context
            for tag in ('dynam','dir','tempo','hairpin','fermata'):
                for mark in node.findall('m:'+tag,NS):
                    marks.append({'id':mark.get(XMLID,''),'type':tag,'text':''.join(mark.itertext()).strip(),'staff':mark.get('staff',''),'measure':m['index'],'beat':mark.get('tstamp',''),'beat_unit':'meter_denominator','form':mark.get('form',''),'startid':mark.get('startid','').lstrip('#')})
            for note in node.findall('.//m:note',NS):
                event=notes.get(note.get(XMLID))
                if event is not None:
                    event['articulations']=[a.get('artic','') for a in note.findall('m:artic',NS)]
                    if not note.get('pname'):event['playable']=False
            return
        for child in node:walk(child)
    walk(tree)
    index.update(feature_schema=FEATURE_SCHEMA,marks=marks)
    return index

def upgrade_index(directory, persist=True):
    path=directory/'events.json'
    index=json.loads(path.read_text())
    if index.get('feature_schema',0)<FEATURE_SCHEMA:
        enrich_index(index,ET.parse(directory/'score.mei').getroot())
        if persist:write_json(path,index)
    return index

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
    selected=[]
    for e in index['events']:
        if not e['playable']:continue
        windows=[(r.start,r.end) for r in seg.routes if r.staff==e['staff'] and (not r.voice or r.voice==e['voice'])] if seg.routes else ([(seg.start,seg.end)] if matches(e,seg) else [])
        for start,end in windows:
            on=max(e['onset'],start);off=min(e['onset']+e.get('sounding_duration',e['duration']),end)
            if on<off:selected.append({**e,'original_onset':e['onset'],'onset':on,'duration':off-on})
    if len(selected)>2000:raise ValueError('所选音符过多，请选择相关声部或缩小片段。')
    st=stream.Stream()
    for e in selected:
        n=note.Note(e['pitch']);n.quarterLength=max(.001,e['duration']);st.insert(e['onset']-seg.start,n)
    try:k=st.analyze('key');key={'name':str(k),'correlation':round(k.correlationCoefficient,3)}
    except Exception:key=None
    verticals=[]
    for q in sorted({seg.start,*[e['onset'] for e in selected],*[e['onset']+e['duration'] for e in selected]}):
        if q>=seg.end:continue
        sounding=[e for e in selected if e['onset']<=q<e['onset']+e['duration']-1e-8]
        if sounding:verticals.append({'onset':round(q-seg.start,5),'pitches':sorted({e['pitch'] for e in sounding}),'bass':min(e['pitch'] for e in sounding),'note_ids':[e['id'] for e in sounding]})
    lines=[]
    for sid,voice in sorted({(e['staff'],e['voice']) for e in selected}):
        es=sorted([e for e in selected if e['staff']==sid and e['voice']==voice],key=lambda e:(e['onset'],e['pitch']))
        mono=all(b['onset']>=a['onset']+a['duration']-1e-6 for a,b in zip(es,es[1:]))
        lines.append({'staff':sid,'voice':voice,'note_count':len(es),'first_onset':round(es[0]['onset']-seg.start,5),'monophonic':mono,'intervals':[b['pitch']-a['pitch'] for a,b in zip(es,es[1:])] if mono else [],'durations':[e['duration'] for e in es]})
    measures=[];context={}
    for m in index['measures']:
        context=m.get('staff_context',context)
        if m['end']>seg.start and m['start']<seg.end:measures.append({'index':m['index'],'label':m['label'],'start':m['start']-seg.start,'end':m['end']-seg.start,'staff_context':context})
    return {'time_unit':'quarter_note','notation':'concert','key_estimate':key,'key_estimate_is_harmonic_proof':False,'note_count':len(selected),'pitch_range':[min(e['pitch'] for e in selected),max(e['pitch'] for e in selected)] if selected else None,'events':[{'id':e['id'],'pitch':e['pitch'],'onset':round(e['onset']-seg.start,5),'duration':e['duration'],'staff':e['staff'],'voice':e['voice'],'articulations':e.get('articulations',[]),'measure_index':e['measure'],'measure_offset':round(e['original_onset']-index['measures'][e['measure']]['start'],5)} for e in selected],'measures':measures,'staffs':[s for s in index['staffs'] if s['id'] in {e['staff'] for e in selected}],'verticalities':verticals[:1000],'voice_lines':lines,'marks':[m for m in index.get('marks',[]) if seg.start_measure<=m['measure']<=seg.end_measure and (not m['staff'] or any(s in m['staff'].split() for s in {e['staff'] for e in selected}))]}

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
