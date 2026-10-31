---
id: codex-tcha1-intro-syntax
work_id: tchaikovsky-op23-1
title: 引子句法：八小节主体为何需要弱起和落点
kind: 曲式
dimensions:
- 曲式
- 节奏／节拍
scope: segment
section_id: m1-intro-first-phrase
listen_for: 从弱起开始数三拍，听两小节的呼吸；第15小节不要急停，等降D落点及旋律的短休止。
claims:
- id: codex-tcha1-intro-syntax-c1
  statement: 弦乐弱起在第7小节偏移1.5；第16小节偏移0的降D持续0.5，随后休止0.5，偏移1为新的旋律进入。
  evidence_type: score
  source_ids: []
  segment_ids:
  - ct1-syntax-full
  - ct1-syntax-pickup
  - ct1-syntax-end
  listening_cue: ''
- id: codex-tcha1-intro-syntax-c2
  statement: Crescendo 以四个两小节单位概括引子主题。
  evidence_type: source
  source_ids:
  - crescendo-first-movement-2016
  segment_ids: []
  listening_cue: ''
- id: codex-tcha1-intro-syntax-c3
  statement: 两小节分组不自动等同于标准前后句乐段；本卡只确认弱起、到达和接续之间的工作边界。
  evidence_type: hypothesis
  source_ids:
  - score-tcha1-308ba2c4
  segment_ids:
  - ct1-syntax-full
  listening_cue: ''
origin: model
status: suggested
review_status: unreviewed
listening_status: pending
sources:
- id: score-tcha1-308ba2c4
  kind: score
  title: 柴可夫斯基第一钢琴协奏曲第一乐章：本地固定数字总谱
  author: jeronjoseph；PDMX v9 数字转换
  edition: score_version 308ba2c44a982ae0；历史版次仍待校勘
  pages: movement-1.mxl；同版本 MEI 与 events.json
  url: https://zenodo.org/records/15571083
  accessed_at: '2026-10-31'
  excerpt: ''
  extracted: true
  summary: 本次定位以本地印刷小节号、实音事件及原始 MusicXML 为准；谱源标注 CC0-1.0。文件 SHA-256 与逐项证据见本地研究记录。
- id: crescendo-first-movement-2016
  kind: web
  title: 'Les Concertos du Concours : le 1er Tchaikovski – Guide d’écoute'
  author: Bernadette Beyne et Quentin Mourier
  edition: Crescendo Magazine，2016-05-19
  pages: 第一乐章：Introduction、Thèmes 2–3、Réexposition
  url: https://www.crescendo-magazine.be/conc-tchaiko_quentin_corr/
  accessed_at: '2026-10-31'
  excerpt: ''
  extracted: true
  summary: 已读第一乐章相关正文；沿用分析问题，外部小节号不直接套用本地谱。
segments:
- id: ct1-syntax-full
  label: 完整乐句：弱起—八小节主体—落点
  score_version: 308ba2c44a982ae0
  start: 19.5
  end: 45.5
  staffs:
  - '14'
  - '17'
  voices: []
  routes: []
  note_ids:
  - x8sd3ft
  - a11rxkcf
  - bjuphb3
  - h1e85tzv
  - kmtvjv4
  - lap0ypc
  - o1l7g3e6
  - qg3yrdv
  - t1qe1y72
  - y1p4k7ja
  - a2uowkt
  - d1n6oqas
  - gx696m1
  - kauhz6s
  - mjyy1yq
  - o1871q1z
  - r3jn6dn
  - vr1mms6
  - xkw99tm
  - zhh6kqk
  - b110obg5
  - d1o8juy7
  - g1jq4prq
  - m1jvfw2q
  - oit8yel
  - rm05mqe
  - sfex6xc
  - u19vrwfq
  - ydihdm5
  - zv9qqwc
  - dnxn6mb
  - fmfhhm3
  - jpapuw8
  - kyyrp52
  - m1cwcdxb
  - ob964ur
  - rhfh8gw
  - x1hua19z
  - z1t7kyxb
  - cb10t5g
  - d12koyrg
  - h87d6zq
  - kikuvbt
  - n1wfv62k
  - o5zx2pw
  - s105idh1
  - v3jkdjm
  - y1vut9tn
  - z1ff59m7
  - c1ut736q
  - e1wutemu
  - hlrvd8p
  - krp5zu3
  - n1nddj75
  - perqav6
  - skbimi
  - u1kxwpc5
  - z1jtzep2
  - b2tydjh
  - dxai1a8
  - h1r6xbwp
  - j1c400lt
  - m42vckw
  - f10hwvyc
  - kcyf2ft
  - mcxya34
  - o1dnoigg
  - tolri83
  - vsh1clx
  - y1mg4r6h
  - a1n7u99x
  - mmf1146
  start_measure: 6
  end_measure: 15
  role: phrase
  boundary_note: 第7小节偏移1.5为弦乐弱起；第16小节偏移0的降D八分音符在偏移0.5结束。第16小节偏移1已有下一轮旋律，故不播放到该小节末。伴奏的已发音音符可依网页自然尾音设置释放。
  boundary_status: supported
  source_ids:
  - score-tcha1-308ba2c4
- id: ct1-syntax-pickup
  label: 局部证据：第7小节后半的弱起
  score_version: 308ba2c44a982ae0
  start: 19.5
  end: 24.0
  staffs:
  - '14'
  - '17'
  voices: []
  routes: []
  note_ids:
  - x8sd3ft
  - a11rxkcf
  - bjuphb3
  - h1e85tzv
  - kmtvjv4
  - lap0ypc
  - o1l7g3e6
  - qg3yrdv
  - t1qe1y72
  - y1p4k7ja
  - a2uowkt
  - d1n6oqas
  start_measure: 6
  end_measure: 7
  role: evidence
  boundary_note: 包含弱起降A–F–降E与第8小节的延续；这是起句证据，终点不是句末。
  boundary_status: supported
  source_ids:
  - score-tcha1-308ba2c4
- id: ct1-syntax-end
  label: 局部证据：下降音型、到达与短休止前的句尾
  score_version: 308ba2c44a982ae0
  start: 42.0
  end: 45.5
  staffs:
  - '14'
  - '17'
  voices: []
  routes: []
  note_ids:
  - u1kxwpc5
  - z1jtzep2
  - b2tydjh
  - dxai1a8
  - h1r6xbwp
  - j1c400lt
  - m42vckw
  - f10hwvyc
  - kcyf2ft
  - mcxya34
  - o1dnoigg
  - tolri83
  - vsh1clx
  - y1mg4r6h
  - a1n7u99x
  - mmf1146
  start_measure: 14
  end_measure: 15
  role: evidence
  boundary_note: 第15小节三连音下降进入第16小节降D八分音符；之后半拍休止，偏移1再起下一轮。
  boundary_status: supported
  source_ids:
  - score-tcha1-308ba2c4
created_at: '2026-10-31T08:29:16.504890+00:00'
updated_at: '2026-10-31T08:29:16.504961+00:00'
verification: Codex 核对了固定谱本的印刷号映射、MEI、实音事件和相关 MusicXML 记谱；论点分别标注资料观点、谱面观察与分析推测。程序定位检查不等于人工听审；新分析尚待用户复核。当前会话未提供可核验的具体模型标识，故记为
  unknown。
analysis_model: unknown
analysis_run_id: 作品/tchaikovsky-op23-1/研究记录/和声调性句法与配器.md
---

# 引子句法：八小节主体为何需要弱起和落点

“八小节主题”是组织方式的概括，不是播放器可直接截取的长度。本谱的旋律从第7小节后半弱起，以第8–15小节为主体，到第16小节开头才落定。若只放第8–15小节，前面少了引入，后面又少了终止音。

Crescendo 将这个主题概括为四个两小节单位。这里沿用两小节分组的听觉线索，但不直接把它判成标准的四加四前后句乐段：是否构成前句、后句，还要有中间终止等级的证据。当前最清楚的边界是第16小节降D之后的短休止；同小节偏移1已开始下一轮，不能整小节一并纳入。
