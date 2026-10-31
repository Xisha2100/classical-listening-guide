"""Publish fully prepared movements; acquisition is never run during app startup."""
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'app'))
from backend.store import Store,read_json,write_json
from backend.scores import build_score

def main(root=ROOT):
    root=Path(root);store=Store(root)
    directory=root/'assets/scores/tchaikovsky-op23'
    prepared=directory/'prepared-works.json'
    if not prepared.exists():return
    works=read_json(prepared)
    if len(works)!=3:raise ValueError('柴一三个乐章尚未全部准备，未发布曲库')
    manifest=read_json(directory/'manifest.json')
    if hashlib.sha256((directory/'source-complete.mxl').read_bytes()).hexdigest()!=manifest['source_sha256']:
        raise ValueError('柴一原始总谱哈希不一致')
    for w,m in zip(works,manifest['movements']):
        source=root/w['source_file']
        if hashlib.sha256(source.read_bytes()).hexdigest()!=m['sha256']:raise ValueError('柴一分乐章源谱哈希不一致')
        output=root/'assets/generated'/w['id']/w['score_version']
        if not (output/'events.json').exists():
            version,_=build_score(source.read_bytes(),output.parent)
            if version!=w['score_version']:raise ValueError('生成版本改变，须重新核对分析定位')
        index=read_json(output/'events.json')
        if len(index['measures'])!=m['measure_count'] or len(index['staffs'])!=18:raise ValueError('柴一乐章长度或声部不完整')
        if not all((output/f'page-{p}.svg').exists() for p in range(1,index['pages']+1)):raise ValueError('柴一谱页尚未完整生成')
    existing={w['id']:w for w in store.works()}
    for w in works:
        if w['id'] not in existing:store.put_work(w)
    path=store.assets/'collections.json'
    collections=read_json(path)
    for c in collections:
        if c['id']=='tchaikovsky-op23':
            c.update(work_ids=[w['id'] for w in works],availability='ready',missing=['完整三乐章已取得并解析；具体修订版、逐音人工校勘与试听仍待核对。'],description='三个乐章完整管弦总谱已入库，首乐章提供多维谱例细读。')
    write_json(path,collections)
    print('柴一完整数字总谱：3 乐章、18 谱表，原始哈希和谱页完整性检查通过。')

if __name__=='__main__':main()
