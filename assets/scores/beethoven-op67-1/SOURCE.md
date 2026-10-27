# 贝多芬 Op.67 第一乐章来源

原始资料来自 [Hauptstimme／OpenScore Orchestra](https://github.com/MarkGotham/Hauptstimme/tree/main/data/Beethoven%2C_Ludwig_van/Symphony_No.5%2C_Op.67/1)，由 Mark Gotham、Lewis Wolstanholme 等项目贡献者提供。

- [完整总谱](Beethoven_Op.67_1.mxl)：MusicXML，共 502 个谱面小节、18 个单谱表乐器声部。
- [主导旋律提取谱](Beethoven_Op.67_1_melody.mxl)
- [主导旋律标注](Beethoven_Op.67_1_annotations.csv)
- [小节顺序与反复映射](Beethoven_Op.67_1.mm.json)
- [原始 README](README.upstream.txt)、[标注方法](annotation.upstream.txt)、[代码 MIT 许可](LICENSE)

上游明确分别声明：**总谱 CC0 1.0 Universal；分析标注 CC-By-SA；代码 MIT**。上游 README 未为分析标注指定 CC-By-SA 的版本号，本项目不补造版本。以上原件未修改；应用新增的中文说明为本项目撰写，涉及标注衍生数据保留相同署名及 ShareAlike 要求。

`part_num` 是从 0 开始的声部索引，而 Verovio 此谱的 staff 从 1 开始。已对照 MusicXML part-list：Vln 1 的 part_num=13 对应 P14／staff 14；Vln 2=14 对应 staff 15；Vla=15 对应 staff 16；Hn 1=8 对应 staff 9；Cl 1=4 对应 staff 5。

定位使用 `measure` 和 `beat` 映射到谱面顺序；`beat` 为从 1 开始的拍位，本谱主要是 2/4。第 268 小节为扩展的双簧管独奏，不可用 `(小节号−1)×2` 推算后续时刻。第 124 小节的反复记号在本 MVP 不执行。

标注表每行是一次主导旋律区段的起点，区段通常结束于下一行起点。标签 a、b 等属于该作品的材料标记；不等同于完整的曲式判定。原始数据仍可能有主观分歧，需与乐谱和听觉共同核对。

下载日期：2026-10-27。原始文件来自上游 main；逐文件 SHA-256 见 [manifest.json](../manifest.json)。
