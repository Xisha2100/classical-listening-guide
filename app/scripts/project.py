#!/usr/bin/env python3
"""Codex workspace commands; no network requests or model clients."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'app'))
from backend.models import Analysis, Guide, Segment
from backend.project import check_project, import_score, save_analysis
from backend.scores import features, similar, validate_segment
from backend.store import Store, read_json, write_json


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT, help='项目目录（默认此仓库）')
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('catalog', 'check', 'reindex'):
        sub.add_parser(name)
    for name in ('save-analysis', 'save-guide', 'export-analysis'):
        cmd = sub.add_parser(name)
        cmd.add_argument('--file' if name != 'export-analysis' else '--id', required=True)
        cmd.add_argument('--output', type=Path)
    cmd = sub.add_parser('import-score')
    cmd.add_argument('--file', type=Path, required=True)
    cmd.add_argument('--metadata', type=Path, required=True)
    cmd.add_argument('--output', type=Path)
    cmd = sub.add_parser('segment', help='按谱面顺序选择范围，输入小节序号从 1 开始')
    cmd.add_argument('--work', required=True)
    cmd.add_argument('--from-measure', type=int, required=True)
    cmd.add_argument('--to-measure', type=int, required=True)
    cmd.add_argument('--staff', action='append', default=[])
    cmd.add_argument('--voice', action='append', default=[])
    cmd.add_argument('--output', type=Path)
    for name in ('features', 'similar'):
        cmd = sub.add_parser(name)
        cmd.add_argument('--work', required=True)
        cmd.add_argument('--segment', type=Path, required=True, help='片段 JSON，或网页复制的选段 JSON')
        cmd.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    try:
        writing = args.command in ('save-analysis', 'save-guide', 'import-score')
        store = Store(args.root.resolve(), read_only=not writing)
        if args.command == 'catalog':
            result = store.works()
        elif args.command == 'check':
            result = check_project(store)
        elif args.command == 'reindex':
            store.reindex()
            result = {'ok': not store.errors, 'errors': store.errors}
        elif args.command == 'save-analysis':
            result = save_analysis(store, Analysis.model_validate(read_json(Path(args.file)))).model_dump()
        elif args.command == 'export-analysis':
            result = store.get_note(args.id).model_dump()
        elif args.command == 'save-guide':
            result = store.save_guide(Guide.model_validate(read_json(Path(args.file))))
        elif args.command == 'import-score':
            result = import_score(store, args.file, read_json(args.metadata))
        else:
            index = store.events(args.work)
            if args.command == 'segment':
                start, end = args.from_measure - 1, args.to_measure - 1
                if not 0 <= start <= end < len(index['measures']):
                    raise ValueError('小节序号超出谱本')
                segment = validate_segment(Segment(score_version=index['version'], start=index['measures'][start]['start'],
                    end=index['measures'][end]['end'], staffs=args.staff, voices=args.voice,
                    label=f"第 {index['measures'][start]['label']}—{index['measures'][end]['label']} 小节"), index)
                result = {'work_id': args.work, 'segment': segment.model_dump()}
            else:
                data = read_json(args.segment)
                if data.get('work_id', args.work) != args.work:
                    raise ValueError('选段所属作品不一致')
                segment = Segment.model_validate(data.get('segment', data))
                result = features(index, segment) if args.command == 'features' else similar(index, segment)
        if getattr(args, 'output', None):
            write_json(args.output, result)
            print(str(args.output.resolve()))
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if isinstance(result, dict) and result.get('ok') is False else 0
    except (ValueError, OSError, KeyError) as exc:
        print(f'项目操作失败：{exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
