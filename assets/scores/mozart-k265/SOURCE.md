# K.265 谱本与分析来源

原始资料来自 [TAVERN](https://github.com/jcdevaney/TAVERN)（commit `7cc65dc5365603a92376af50ac71491bea7a16ae`），由 Johanna Devaney、Claire Arthur、Nathaniel Condit-Schultz、Kirsten Nisula 等维护。

- [K265.xml](K265.xml)：完整 MusicXML，共 324 小节、两个钢琴谱表，原始编码为 UTF-16。
- [K265.krn](K265.krn)：完整 Humdrum 原谱。
- [annotations](annotations/)：主题与前三变奏的和声／乐句标注，各乐句保留 a、b 两位标注者的 joined 文件。
- [原始 README](README.upstream.txt) 与 [CC BY-SA 4.0 许可全文](LICENSE)。
- [TAVERN 数据说明](https://u.osu.edu/tavern/dataset-details/)

MVP 使用原始记谱顺序的第 1—96 小节：主题 1—24，变奏一 25—48，变奏二 49—72，变奏三 73—96。应用裁切生成副本，原始文件完整保留。每组乐句起点依次为该组第 1、9、17 小节；已用 joined 文件的 `=` 小节标记与 MusicXML 的实际音符复核。

joined 文件的 `**function`、`**harm` 是分析标注，`**kern` 是音符；标注者之间的分歧应保留。某些分析 spine 的拍号和音符 spine 不同，播放拍号以 MusicXML 为准。

引用：Devaney, Arthur, Condit-Schultz & Nisula (2015), “Theme And Variation Encodings with Roman Numerals (TAVERN): A New Data Set for Symbolic Music Analysis”, ISMIR, 728–734。

下载日期：2026-10-27。下载文件未修改；裁切及后续生成的 MEI 为本项目衍生文件，须保留署名并以同许可分发。
