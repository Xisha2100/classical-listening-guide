---
id: seed-v2-beethoven-00
work_id: beethoven-op67-1
title: 总览｜四大部分怎样组织一场持续的冲突
kind: 曲式
dimensions:
- 曲式
- 调性／调式
scope: overview
section_id: ''
listen_for: 依次比较四个入口的声部密度和节奏组织；章节长度按谱面顺序统计，不包含呈示反复。
claims:
- id: seed-v2-beethoven-00-c1
  statement: ESM 将四个主要部分理解为篇幅相近的结构，尾声承担进一步展开的作用。
  evidence_type: source
  source_ids:
  - beethoven-v2-esm
  segment_ids: []
  listening_cue: ''
- id: seed-v2-beethoven-00-c2
  statement: MTSU 采用125展开、248再现、376尾声入口；Surette／Mason 在374把结束与尾声重叠，并对再现预备区另有划分。
  evidence_type: source
  source_ids:
  - beethoven-v2-mtsu
  - beethoven-v2-mason
  segment_ids: []
  listening_cue: ''
- id: seed-v2-beethoven-00-c3
  statement: 本谱374的实音集合为C、E、G；376为F、降A、C，所以结构边界不能简化为“374起所有和弦都是C小调”。
  evidence_type: score
  source_ids:
  - beethoven-v2-score
  segment_ids:
  - seed-v2-beethoven-00-s4
  listening_cue: ''
origin: seed
status: not_applicable
review_status: unreviewed
listening_status: pending
sources:
- id: beethoven-v2-score
  kind: score
  title: 贝多芬 Op.67 第一乐章 · OpenScore Orchestra 总谱
  author: Ludwig van Beethoven；OpenScore Orchestra 转录
  edition: 固定 MusicXML／canonical MEI 谱本 0dc9a06dc592e643
  pages: ''
  url: https://github.com/MarkGotham/Hauptstimme/tree/main/data/Beethoven%2C_Ludwig_van/Symphony_No.5%2C_Op.67/1
  accessed_at: '2026-10-28'
  excerpt: ''
  extracted: true
  summary: 以下音高、节奏、声部及记号直接取自本地保留的总谱，不将 Hauptstimme 材料标签当作完整曲式分析。总谱 CC0 1.0 Universal。
- id: beethoven-v2-esm
  kind: web
  title: Beethoven Symphony Basics · Symphony No. 5
  author: Eastman School of Music；页面署名 FJ、JM、MER
  edition: ''
  pages: ''
  url: https://www.esm.rochester.edu/beethoven/symphony-no-5/
  accessed_at: '2026-10-28'
  excerpt: ''
  extracted: true
  summary: 资料概括：第一乐章的四大部分篇幅接近；尾声继续展开材料；再现部把先前圆号的呼唤交给巴松。本文只把这些作为导听观点，具体小节、音高与声部另行对谱。
- id: beethoven-v2-mtsu
  kind: web
  title: 'Beethoven’s 5th Symphony: Listening Guide'
  author: James E. Walker Library, Middle Tennessee State University
  edition: ''
  pages: ''
  url: https://library.mtsu.edu/Beethoven5/guide
  accessed_at: '2026-10-28'
  excerpt: ''
  extracted: true
  summary: 资料概括：呈示部结束于124，展开始于125，再现始于248；268是双簧管华彩式插段。该页将尾声入口标为376，与采用374重叠边界的分析可并列阅读。
- id: beethoven-v2-mason
  kind: book
  title: The Appreciation of Music, Volume I
  author: Thomas Whitney Surette；Daniel Gregory Mason
  edition: 第九版；Project Gutenberg 电子版 58458
  pages: 183–187（原书页码）
  url: https://www.gutenberg.org/cache/epub/58458/pg58458-images.html
  accessed_at: '2026-10-28'
  excerpt: ''
  extracted: true
  summary: 资料概括：结构表把374同时列作结束组终点和尾声起点；195之后的段落逐步削减旋律轮廓。它将240–252归入再现的过渡处理，本应用按原主题实际返回采用248作导航边界，保留这一分析差异。
segments:
- id: seed-v2-beethoven-00-s1
  label: 呈示：开头
  score_version: 0dc9a06dc592e643
  start: 0.0
  end: 10.0
  staffs:
  - '14'
  - '17'
  voices: []
  routes: []
  note_ids:
  - k190f35j
  - oeg183e
  - p9vmd3q
  - cch0xk7
  - d1w5y06z
  - e9cerij
  - be441t3
  - q1sk7pjw
  - r4e9plb
  - vnlpifc
  - w1ripc5f
  - gtmrgxe
  - h17bizkb
  - i1inf9ka
  - i155fs3p
  - uvniyfg
  - v5qvyaa
  - h1uo79i7
  start_measure: 0
  end_measure: 4
- id: seed-v2-beethoven-00-s2
  label: 展开：换位部署
  score_version: 0dc9a06dc592e643
  start: 248.0
  end: 264.0
  staffs:
  - '5'
  - '9'
  - '14'
  - '17'
  voices: []
  routes: []
  note_ids:
  - lwzk2lb
  - mhi0bro
  - nw5u76b
  - z1owctuq
  - dzxgc50
  - e1nqx7zv
  - ztcs2ac
  - q19b82ni
  - pnya5r8
  - uw168h8
  - w7b70ls
  - n1tam2hf
  - p1vv9csn
  - r13xz7l3
  - m16lioi0
  - d9bhlx8
  - j17drd7k
  - e4e89ji
  - z1yqqsr4
  - qjmerzo
  - w1hbwhq
  - r148w03p
  - clqmujt
  - hmefagc
  - j1o195sg
  - t1rhuto6
  - w1t8ofu0
  - l1jhydiz
  - q31zkx7
  - sh41ziq
  - g1qlb3o9
  - jwzoe2a
  - f1lu4bey
  - t8es6k
  - v1aeeiov
  - x1alcjws
  - zwvhfye
  start_measure: 124
  end_measure: 131
- id: seed-v2-beethoven-00-s3
  label: 再现：原型回返
  score_version: 0dc9a06dc592e643
  start: 494.0
  end: 504.0
  staffs:
  - '1'
  - '14'
  - '17'
  voices: []
  routes: []
  note_ids:
  - i1qub480
  - k1ja24ua
  - l16n7ev1
  - mf3vop1
  - r14g945h
  - t1c7ipmt
  - x1jiaf49
  - y1j30xrh
  - e1fujchw
  - gv794jn
  - hho0pys
  - ialklek
  - yitxpaf
  - khzlic3
  - uqg71e8
  - o1utjzfc
  - p1g9qdjc
  - q1pb8pc5
  - a12y203p
  - edvqqgx
  - fxqt7l
  - k7asxne
  - l9o7wnz
  - m1cqaf04
  - csdsid3
  - r1muf3h8
  - ychm7u1
  - p6n636h
  - ealligw
  - lyfw8o5
  start_measure: 247
  end_measure: 251
- id: seed-v2-beethoven-00-s4
  label: 尾声：重叠入口
  score_version: 0dc9a06dc592e643
  start: 754.0
  end: 770.0
  staffs:
  - '14'
  - '15'
  - '16'
  - '17'
  voices: []
  routes: []
  note_ids:
  - bzodpnq
  - k3pv0ht
  - a1hlif6l
  - ic2547l
  - p1vbs1js
  - z18oewpb
  - ozzenxm
  - w1rnob2b
  - deol8q4
  - nlwgyak
  - qhnlwuq
  - c1f44wjw
  - k1ew6cny
  - r1s00s0r
  - e15rfr7x
  - ggtkef2
  - qag6nkw
  - z10rfrgt
  - f1160krm
  - u1hy3eu
  - x1kwnavi
  - e1dml4pd
  - ob5utsq
  - t1p9vvi3
  - lnb6isu
  - n171efm9
  - s5d60d2
  - dm27pqx
  - h1n2i6fl
  - b1banv3e
  - exo8lv5
  - gz1p848
  - r1qzvha3
  - v6q9174
  - t1b3ivtx
  - v10xpqw
  - vsqydtt
  - f15l9hr0
  start_measure: 373
  end_measure: 380
created_at: '2026-10-28T03:15:33.111933+00:00'
updated_at: '2026-10-28T03:15:33.112008+00:00'
verification: 数字谱的实际音高、声部、拍位与所列记号已逐项核对，定位通过同一事件索引校验。正文含编辑解释，尚待用户乐理复核及人工试听。钢琴复奏不重现管弦音色或自由延长记号。
---

# 总览｜四大部分怎样组织一场持续的冲突

先把第一乐章听成四段各有任务的过程：呈示部建立 C 小调主部与降 E 大调副部的对比；展开部拆分材料、改变组合；再现部让熟悉的轮廓回到主调范围；尾声继续处理尚未结束的张力。这里的“主调范围”不等于每一小节都只能使用 C 小三和弦，副部再现就会使用 C 大调。

本谱导航采用呈示 1–124、展开 125–247、再现 248–373、尾声 374–502。边界是分析选择：374 的 C 大三和弦同时可作前段终止与新段启动；MTSU 导听从 376 标尾声，Surette／Mason 的表格在374重叠，且把240–252视为再现的预备处理。可依次试听四个入口，再进入各章细读。ESM 强调四部分的篇幅相近；这说明尾声有独立分量，而不只是结束时附加的几记和弦。
