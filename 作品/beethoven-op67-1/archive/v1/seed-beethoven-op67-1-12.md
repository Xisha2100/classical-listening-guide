---
id: seed-beethoven-op67-1-12
work_id: beethoven-op67-1
title: 动机在弦乐声部间传递
kind: 动机
origin: seed
status: confirmed
sources:
- id: source-beethoven-op67-1
  kind: score
  title: OpenScore Orchestra / Hauptstimme
  author: ''
  edition: ''
  pages: ''
  url: https://github.com/MarkGotham/Hauptstimme/blob/main/data/Beethoven%2C_Ludwig_van/Symphony_No.5%2C_Op.67/1/Beethoven_Op.67_1_annotations.csv
  accessed_at: ''
  excerpt: ''
  extracted: true
segments:
- id: seed-12-0
  label: 第二小提琴
  score_version: 0dc9a06dc592e643
  start: 10.5
  end: 12.5
  staffs:
  - '15'
  voices:
  - '1'
  routes: []
  note_ids:
  - n2ib81t
  - ru42izx
  - s1qy67ab
  - eyrce34
  start_measure: 5
  end_measure: 6
- id: seed-12-1
  label: 中提琴
  score_version: 0dc9a06dc592e643
  start: 12.5
  end: 14.5
  staffs:
  - '16'
  voices:
  - '1'
  routes: []
  note_ids:
  - r16rnxu
  - w1d58ot6
  - y1ftka4v
  - l1cd6xt3
  start_measure: 6
  end_measure: 7
- id: seed-12-2
  label: 第一小提琴
  score_version: 0dc9a06dc592e643
  start: 14.5
  end: 18.5
  staffs:
  - '14'
  voices:
  - '1'
  routes: []
  note_ids:
  - kd32f0f
  - p1fr6jbb
  - r1hyhysh
  - e1sysc7v
  - r1hxrs5i
  start_measure: 7
  end_measure: 9
- id: seed-hauptstimme-route
  label: 连续接力：二提琴→中提琴→一提琴
  score_version: 0dc9a06dc592e643
  start: 10.5
  end: 18.5
  staffs: []
  voices: []
  routes:
  - start: 10.5
    end: 12.5
    staff: '15'
    voice: '1'
  - start: 12.5
    end: 14.5
    staff: '16'
    voice: '1'
  - start: 14.5
    end: 18.5
    staff: '14'
    voice: '1'
  note_ids:
  - n2ib81t
  - ru42izx
  - s1qy67ab
  - eyrce34
  - r16rnxu
  - w1d58ot6
  - y1ftka4v
  - kd32f0f
  - p1fr6jbb
  - r1hyhysh
  - l1cd6xt3
  - e1sysc7v
  - r1hxrs5i
  start_measure: 5
  end_measure: 9
created_at: '2026-10-27T01:31:07.697715+00:00'
updated_at: '2026-10-27T01:48:53.315179+00:00'
verification: '核对上游主导旋律标注的 measure/beat/part_num 与 MusicXML part-list、实际音符。part_num
  为0基，Verovio staff为1基。片段在第 6、7、8、10 小节开始后的 0.5 个四分音符处切换，连续路线保留乐谱的原时间。 标注记录：[{"qstamp":
  "10.5", "measure": "6", "beat": "1.5", "measure_fraction": "0.25", "label": "a",
  "part": "Vln 2", "part_num": "14", "instrument": "Vln"}, {"qstamp": "12.5", "measure":
  "7", "beat": "1.5", "measure_fraction": "0.25", "label": "a", "part": "Vla", "part_num":
  "15", "instrument": "Vla"}, {"qstamp": "14.5", "measure": "8", "beat": "1.5", "measure_fraction":
  "0.25", "label": "a", "part": "Vln 1", "part_num": "13", "instrument": "Vln"}] 音符和出处已核对；人工听感复核尚待完成。'
---

# 动机在弦乐声部间传递

上游标注从第 6 小节起依次选择第二小提琴、中提琴、第一小提琴为主导声部。分别试听三个入口，听同一节奏材料在不同音区接续。每段保留至下一次入口前的延续音；材料标签 a 是上游的分析标记。
