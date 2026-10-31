#!/usr/bin/env python3
"""Reproduce the v0.2 asset audit. Large upstream archives stay outside the repo.

Download public PDMX v9 files into --cache, inventory candidate rows, and extract
only candidate entries into a quarantine directory. This script never bypasses
MuseScore restrictions and never treats a CSV license flag as musical validation.
Copying into assets is deliberately separate from acquisition and requires an
explicit reviewed manifest.
"""
from __future__ import annotations
import argparse, copy, csv, hashlib, io, json, re, shutil, subprocess, tarfile, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
E = ET

RECORD = 'https://zenodo.org/records/15571083'
KNOWN_IDS = {'12906169','12962101','13106833','5871238','5895897','5997637'}

def candidate(row):
    score_id=Path(row.get('metadata','')).stem
    text=' '.join(row.get(k,'') or '' for k in ['song_name','title','subtitle','artist_name','composer_name','tags']).lower()
    compact=re.sub(r'[^a-z0-9]','',text)
    if score_id in KNOWN_IDS:return True
    if ('moussorgsky' in compact or 'mussorgsky' in compact or 'pictures' in compact or 'ravel' in compact) and ('pictures' in compact or 'exposition' in compact or 'moussorgskyravelpicturesmike' in compact):return True
    if 'concerto' in compact and ('beethoven' in compact or 'tchai' in compact):return True
    return False

def read_rows(cache):
    with (cache/'PDMX.csv').open(encoding='utf-8',newline='') as f:
        rows=[r for r in csv.DictReader(f) if candidate(r)]
    return rows

def extract(cache,rows):
    out=cache/'quarantine';out.mkdir(exist_ok=True)
    for fmt in ['metadata','mxl']:
        archive=cache/f'{fmt}.tar.gz'
        wanted={r[fmt].lstrip('./') for r in rows if r.get(fmt) not in (None,'','NA','N/A')}
        if not archive.exists():raise FileNotFoundError(archive)
        found=0
        with tarfile.open(archive,'r|gz') as tf:
            for entry in tf:
                name=entry.name.lstrip('./')
                if name not in wanted:continue
                # Never extract arbitrary paths or links from the tarball.
                if not entry.isfile() or entry.size>40_000_000:raise ValueError('Unsafe candidate entry '+name)
                p=out/name;p.parent.mkdir(parents=True,exist_ok=True)
                p.write_bytes(tf.extractfile(entry).read());found+=1
        print(f'{fmt}: {found}/{len(wanted)} extracted',flush=True)

def inspect_mxl(path):
    with zipfile.ZipFile(path) as z:
        container=ET.fromstring(z.read('META-INF/container.xml'))
        rootfile=next(e.get('full-path') for e in container.iter() if e.tag.endswith('rootfile'))
        raw=z.read(rootfile)
    root=ET.fromstring(raw)
    return {'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,
            'root_tag':root.tag,'musicxml_version':root.get('version'),
            'work_title':root.findtext('work/work-title'),'movement_title':root.findtext('movement-title'),
            'rights':[''.join(e.itertext()) for e in root.findall('./identification/rights')],
            'creators':[{'type':e.get('type'),'value':''.join(e.itertext())} for e in root.findall('./identification/creator')],
            'parts':[{'id':p.get('id'),'name':p.findtext('part-name')} for p in root.findall('./part-list/score-part')],
            'measure_counts':{p.get('id'):len(p.findall('measure')) for p in root.findall('part')},
            'note_count':len(root.findall('.//note/pitch')),
            'unpitched_count':len(root.findall('.//note/unpitched')),
            'directions':[e.text for e in root.findall('.//direction-type/words') if e.text][:35]}

def publish_tchaikovsky(cache):
    out=Path('assets/scores/tchaikovsky-op23');out.mkdir(parents=True,exist_ok=True)
    r=next(x for x in json.load(open(cache/'candidates.json')) if '5871238' in x['metadata']);src=cache/'quarantine'/r['mxl'].lstrip('./');shutil.copy2(src,out/'source-complete.mxl')
    meta=cache/'quarantine'/r['metadata'].lstrip('./');shutil.copy2(meta,out/'source-metadata.json')
    with zipfile.ZipFile(src) as z:
     f=next(x.get('full-path') for x in E.fromstring(z.read('META-INF/container.xml')).iter() if x.tag.endswith('rootfile'));root=E.fromstring(z.read(f))
    container=b'<?xml version="1.0"?><container><rootfiles><rootfile full-path="score.musicxml" media-type="application/vnd.recordare.musicxml+xml"/></rootfiles></container>'
    manifest={'work_id':'tchaikovsky-op23','source_url':'https://musescore.com/user/20208436/scores/5871238','archive_url':'https://zenodo.org/records/15571083','archive_member':r['mxl'],'license':'CC0-1.0','license_url':'https://creativecommons.org/publicdomain/zero/1.0/','internal_rights':['Public Domain'],'license_conflict_resolution':'The PDMX row has license_conflict=True. Actual MusicXML rights is Public Domain and original author body explicitly states Creative Commons copyright waiver. Manual review found no substantive contradiction or reserved-rights statement.','source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'source_title_warning':'The upstream page/CSV title says movement I but the actual archived MXL contains all three movements.','orchestration':'piano and full orchestra; 17 parts, piano uses 2 staves','validation':'XML parsed; all 17 parts have 1140 measure elements; boundaries have explicit tempo, meter, reset measure labels, and previous final barlines. Not a complete manual proofread.','movements':[]}
    order=['divisions','key','time','staves','part-symbol','instruments','clef','staff-details','transpose','measure-style']
    for idx,(start,end,title) in enumerate([(1,669,'I. Allegro non troppo e molto maestoso — Allegro con spirito'),(670,839,'II. Andantino semplice'),(840,1140,'III. Allegro con fuoco')],1):
     rt=copy.deepcopy(root)
     for e in list(rt):
      if e.tag=='credit':rt.remove(e)
     t=rt.find('movement-title')
     if t is None:t=E.SubElement(rt,'movement-title')
     t.text=title
     wt=rt.find('work/work-title')
     if wt is not None:wt.text='Piano Concerto No. 1 in B-flat minor, Op. 23'
     maps=[]
     for part in rt.findall('part'):
      allm=part.findall('measure');state={}
      for m in allm[:start]:
       for attrs in m.findall('attributes'):
        for el in attrs:
         if el.tag in order:state[(el.tag,el.get('number','1'))]=copy.deepcopy(el)
      first=allm[start-1]
      for attrs in first.findall('attributes'):first.remove(attrs)
      attrs=E.Element('attributes')
      for el in sorted(state.values(),key=lambda x:(order.index(x.tag),x.get('number','1'))):attrs.append(el)
      first.insert(0,attrs)
      for m in allm[:start-1]+allm[end:]:part.remove(m)
      if not maps:maps=[{'ordinal':j+1,'source_ordinal':start+j,'printed_measure':m.get('number')} for j,m in enumerate(part.findall('measure'))]
     raw=E.tostring(rt,encoding='utf-8',xml_declaration=True)
     file=out/f'movement-{idx}.mxl'
     with zipfile.ZipFile(file,'w',zipfile.ZIP_DEFLATED) as z:z.writestr('META-INF/container.xml',container);z.writestr('score.musicxml',raw)
     (out/f'movement-{idx}-measure-map.json').write_text(json.dumps(maps,ensure_ascii=False,indent=2)+'\n')
     manifest['movements'].append({'movement':idx,'title':title,'file':file.name,'measure_count':end-start+1,'source_start_ordinal':start,'source_end_ordinal':end,'printed_start':maps[0]['printed_measure'],'printed_end':maps[-1]['printed_measure'],'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'map_file':f'movement-{idx}-measure-map.json'})
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    (out/'SOURCE.md').write_text('# 柴可夫斯基第一钢琴协奏曲 Op.23：完整管弦总谱\n\n来源：[jeronjoseph 原作者谱页](https://musescore.com/user/20208436/scores/5871238)，实际下载自 [PDMX v9](https://zenodo.org/records/15571083)。许可为 [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)，原文件 rights 为 Public Domain，作者正文亦声明公共领域及 Creative Commons copyright waiver。PDMX 清单标记 license_conflict=true；人工检查实际文件与作者声明，未发现实质矛盾或保留权利声明。\n\n原网页标题只写第一乐章，但归档 MXL 实际包含完整三乐章，共 17 个声部、1140 个小节元素。原文件完整保留为 source-complete.mxl；分乐章文件继承乐章入口的谱号、调号、节拍、移调、divisions 和钢琴双谱表状态。第一乐章有拆小节，669 个元素末尾印刷号为 666；第二、三乐章分别 170、301 个元素。不得将内部 ordinal 当作印刷小节号。\n\n验证已覆盖 XML 解析、全声部小节数一致、乐章入口速度与节拍、前乐章终止线及原始序号映射；尚未完成逐音人工校勘与试听。转录版底本与具体修订版本仍待对照原总谱确认。\n\n元数据、SHA-256、乐章范围与映射见 manifest.json。大型原始下载包仅在临时缓存中。\n')
    print(out.resolve());print(json.dumps(manifest['movements'],ensure_ascii=False,indent=2))

def publish_ravel(cache):
    out=Path('assets/scores/pictures-ravel');out.mkdir(exist_ok=True,parents=True)
    rows=json.load(open(cache/'candidates.json'));items=[]
    for r in rows:
     meta=cache/'quarantine'/r['metadata'].lstrip('./')
     if not meta.exists():continue
     s=json.load(open(meta))['data']['score']
     if s['user']['id']!=6105546 or '5273' not in r['metadata']:continue
     seq=int(re.search(r'(\d+) of 15',s['body']).group(1));src=cache/'quarantine'/r['mxl'].lstrip('./')
     if not src.exists():raise FileNotFoundError(src)
     with zipfile.ZipFile(src) as z:
      f=next(e.get('full-path') for e in E.fromstring(z.read('META-INF/container.xml')).iter() if e.tag.endswith('rootfile'));root=E.fromstring(z.read(f))
     assert r['license']=='cc-zero' and r['license_conflict']=='False'
     rights=[e.text for e in root.findall('./identification/rights')];assert not rights,rights
     dst=out/f'section-{seq:02d}.mxl';shutil.copy2(src,dst);shutil.copy2(meta,out/f'section-{seq:02d}-metadata.json')
     item={'section':seq,'title':s['title'],'source_url':s['url'],'file':dst.name,'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'license':'CC0-1.0','internal_rights':rights,'upstream_series_label':s['body'],'archive_member':r['mxl'],'part_count':len(root.findall('part')),'measure_counts':{p.get('id'):len(p.findall('measure')) for p in root.findall('part')},'printed_last_measure':root.findall('part')[0].findall('measure')[-1].get('number'),'pitch_note_count':len(root.findall('.//note/pitch')),'validation':'XML parsed; upstream series identity and orchestration metadata checked. Not manually proofread.'};items.append(item)
     # Save both local ordinal and source measure text; anonymous/split numbers are not rewritten.
     mm=[{'ordinal':i+1,'printed_measure':m.get('number')} for i,m in enumerate(root.findall('part')[0].findall('measure'))];(out/f'section-{seq:02d}-measure-map.json').write_text(json.dumps(mm,ensure_ascii=False,indent=2)+'\n')
    items.sort(key=lambda x:x['section'])
    manifest={'work_id':'pictures-ravel','arranger':'Maurice Ravel','status':'incomplete','required_sections':15,'available_series_sections':len(items),'archive_url':'https://zenodo.org/records/15571083','license':'CC0-1.0','license_url':'https://creativecommons.org/publicdomain/zero/1.0/','sections':items,'missing':[{'section':2,'title':'Gnomus','reason':'Not in PDMX v9; no accessible full orchestral digital source obtained.'},{'section':6,'title':'Tuileries','candidate_url':'https://musescore.com/user/17103446/scores/5848890','reason':'Different author CC0 11-part MXL obtained; Ravel instrumentation/completeness comparison still required.'},{'section':11,'title':'Limoges — Le Marché','candidate_url':'https://musescore.com/user/6105546/scores/5273141','reason':'Series page identified; file not in PDMX v9; original website access blocked by verification.'}]}
    r=next(x for x in rows if '5848890' in x['metadata']);cand=out/'candidates';cand.mkdir(exist_ok=True);shutil.copy2(cache/'quarantine'/r['mxl'].lstrip('./'),cand/'section-06-tuileries.mxl');shutil.copy2(cache/'quarantine'/r['metadata'].lstrip('./'),cand/'section-06-metadata.json')
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    (out/'SOURCE.md').write_text('# 《图画展览会》拉威尔管弦乐版：取得情况\n\n本目录尚不完整，不能标为全套已收录。原作者 mike320 的 15 文件系列现取得其中 12 份：1、3、4、5、7、8、9、10、12、13、14、15。来源为 [PDMX v9](https://zenodo.org/records/15571083)，各文件公开原页、原始清单条目、元数据与 SHA-256 均在 manifest.json 中记录。\n\n12 份清单许可均为 CC0，license_conflict=false，实际 MusicXML rights 为空。原作者页面正文明确各自属于 15 文件系列的哪一份。文件包含管弦乐各声部，不是钢琴原作。\n\n尚缺 Gnomus、Tuileries、Limoges；candidates/ 中另有 jini5517 的 Tuileries（30 小节、11 声部、CC0），需与拉威尔原谱逐声部核对，尚不作为第 6 段校验通过。不得用这 12 份冒称完整组曲，也不得用钢琴谱补齐。\n\n已作 XML 与声部/小节数检查；尚未完成逐音人工校勘和试听。GB 级原始归档仅在 /tmp/music-guide-corpus-cache 中缓存。\n')
    print([(i['section'],i['title'],i['part_count'],set(i['measure_counts'].values())) for i in items])

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cache',type=Path,default=Path('/tmp/music-guide-corpus-cache'))
    ap.add_argument('action',choices=['download','inventory','extract','inspect','publish-tchaikovsky','publish-ravel'])
    args=ap.parse_args();cache=args.cache;cache.mkdir(parents=True,exist_ok=True)
    if args.action=='download':
        for name in ['PDMX.csv','metadata.tar.gz','mxl.tar.gz']:
            subprocess.run(['curl','-fL','--retry','3','-C','-',f'{RECORD}/files/{name}?download=1','-o',str(cache/name)],check=True)
        return
    rows=read_rows(cache)
    (cache/'candidates.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    if args.action=='inventory':
        for r in rows:
            if int(r.get('n_tracks') or 0)>8:
                print(json.dumps({k:r.get(k) for k in ['metadata','mxl','title','song_name','composer_name','n_tracks','license','license_conflict','song_length.bars']},ensure_ascii=False))
    elif args.action=='extract':extract(cache,rows)
    elif args.action=='publish-tchaikovsky':publish_tchaikovsky(cache)
    elif args.action=='publish-ravel':publish_ravel(cache)
    elif args.action=='inspect':
        reports=[]
        for r in rows:
            p=cache/'quarantine'/r['mxl'].lstrip('./')
            if not p.exists():continue
            try:details=inspect_mxl(p)
            except Exception as e:details={'error':str(e)}
            reports.append({'row':r,'inspection':details})
        (cache/'inspection.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n')
        print(f'{len(reports)} inspections in {cache / "inspection.json"}')

if __name__=='__main__':main()
