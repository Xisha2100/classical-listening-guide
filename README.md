# 听见结构：Codex 音乐赏析项目

在 Codex 中查阅资料、分析乐谱、整理书籍摘录并记录到本地；网页用于阅读分析、展示乐谱和钢琴试听。

网页没有联网搜索、模型调用、模型设置或笔记编辑功能，也不需要启动 Ollama 或配置 API 密钥。GPT 分析在当前 Codex 项目对话中进行，模型由对话本身决定。网页显示的“分析模型”是该条记录的历史来源。

## 开始使用

在 Codex 中打开本仓库。可以直接提出这样的任务：

> 分析柴一第一乐章开头主题的句法与和声，参考现有研究资料，区分完整主题和局部证据，记录到项目；尚未确定的判断保留为推测。

也可以粘贴书籍摘录并附书名、作者、版本与页码，让 Codex 整理成分析卡片。后续工作遵循 [Agent 分析指南](Agent.md)和[分析工作规范](分析工作规范.md)。

启动网页：

```sh
./start.sh
```

打开 [本地阅读器](http://127.0.0.1:8765/)。首次安装需要 Node.js 22 或更新版本，以及 uv 或 Python 3.12；脚本会安装锁定依赖并构建页面。首次安装后，本地阅读、曲库检索和钢琴播放不需要联网。服务仅监听 `127.0.0.1`，在启动终端按 Ctrl+C 停止。

日常流程：

1. 在 Codex 中完成资料研究、谱面分析和文件保存。
2. 网页点击“刷新项目”，读取最新曲库、导听结构、笔记与引用。
3. 选择分析卡片，查看完整主题、乐句或局部证据的对应位置并试听。
4. 需要进一步分析时，选中谱例或点击两个音符，再点击“复制选段给 Codex”，将位置 JSON 和问题一起粘贴到对话。

“刷新项目”只更新检索缓存，不改写笔记。启动脚本也不会重新安装示例或覆盖已修改的分析。比较队列等阅读偏好保留在当前浏览器；旧版尚未保存的浏览器草稿会提供“导出旧版草稿”，原始内容保留，导出的 JSON 可交给 Codex 整理入库。

## 当前内容

| 作品 | 已入库乐谱 | 活跃分析卡片 |
|---|---|---:|
| 巴赫 BWV 847 | 完整赋格 | 5 |
| 莫扎特 K.265 | 主题与前三个变奏 | 5 |
| 贝多芬第五交响曲 Op.67 | 第一乐章完整总谱 | 15 |
| 柴可夫斯基第一钢琴协奏曲 Op.23 | 三个完整乐章的数字总谱 | 37 |

合计 6 个谱本／乐章、62 张分析。更早的分析版本保留在各作品的 `archive/` 中，默认不列入阅读器。

柴一的首轮主题与边界分析由 GPT-6 Sol 子代理完成，详见[主题边界研究记录](assets/scores/tchaikovsky-op23/research-notes.md)。第一乐章又补充了 9 张和声、调性、句法与配器卡片，关联 14 个完整乐句／段落和 19 个局部证据；本轮具体模型标识不可核验，记录为 `unknown`，详见[补充研究记录](作品/tchaikovsky-op23-1/研究记录/和声调性句法与配器.md)。三个乐章现共 41 个曲式节点、88 个播放段。完整主题、乐句与局部证据分别标识，定位、内容复核和人工听审状态分别保存；自动播放检查不替代人工听审。

贝多芬第三钢琴协奏曲及拉威尔配器版《图画展览会》的资料与候选谱仍保留；完整数字谱尚未校验入库，不能当作完整可播放内容。莫扎特目前只覆盖主题及前三个变奏。

## 阅读与试听

左侧用紧凑下拉框筛选曲式范围和分析维度，再选择具体卡片。支持动机、主题、变奏、曲式、和声、调性／调式、节奏／节拍、织体／复调、配器和力度／奏法。右侧阅读论点、引用、摘录与概括，保留内容核对、定位和人工试听的独立状态。

可以慢放、循环、选择谱表／声部、依次试听同卡片的多个谱例，或将两个谱例加入跨作品 A／B 比较。前后文播放可扩展前后各 2、4、8 个印刷小节，以全部声部帮助听清进入与收束；它不改变保存的分析位置。范围结束后不启动新音符，已经发声的音符保留自然延音。

谱面按实音记谱，播放使用本地钢琴采样；这是各声部的钢琴音色复奏，不是双手缩编或真实管弦录音。按谱面顺序播放，不自动执行反复跳转，不模拟自由速度及完整的演奏诠释。

## 本地记录工具

以下命令供 Codex 在项目目录中使用；不经过网页，也不调用模型或网络服务。

```sh
# 列出谱本 ID、版本及来源。
app/.venv/bin/python app/scripts/project.py catalog

# 校验全部分析、引用、曲式层级、谱页与片段定位；失败返回非零状态。
app/.venv/bin/python app/scripts/project.py check

# 按谱面顺序选择第 1—2 个小节元素；可重复指定 --staff 和 --voice。
app/.venv/bin/python app/scripts/project.py segment \
  --work bach-bwv847 --from-measure 1 --to-measure 2 \
  --output /tmp/选段.json

# 读取结构化实音、节奏、持续音与局部特征，也接受网页复制的选段 JSON。
app/.venv/bin/python app/scripts/project.py features \
  --work bach-bwv847 --segment /tmp/选段.json --output /tmp/谱面特征.json

# 单旋律 3—64 个音符的精确／移调重复候选，结果仍需音乐判断。
app/.venv/bin/python app/scripts/project.py similar \
  --work bach-bwv847 --segment /tmp/选段.json

# 导出既有卡片，便于保留元数据后修订。
app/.venv/bin/python app/scripts/project.py export-analysis \
  --id seed-bach-bwv847-00 --output /tmp/分析.json

# 校验并保存 Markdown 与片段 JSON；更改内容会撤销原有内容核对状态。
app/.venv/bin/python app/scripts/project.py save-analysis --file /tmp/分析.json
app/.venv/bin/python app/scripts/project.py save-guide --file /tmp/导听目录.json
```

`segment` 参数是从 1 开始的小节**顺序号**；数据中的 `start_measure`／`end_measure` 从 0 开始，印刷小节号另存在事件索引的 `label` 中。弱起、同号分段或 X1 等特殊小节必须通过索引映射，不能直接做数字减一。

完整字段见 [数据模型](app/backend/models.py)。新模型分析需要填写 `origin: model`、实际模型名 `analysis_model` 和本地研究记录路径或标识 `analysis_run_id`；不知道实际型号时写 `unknown`。重新分析采用新的卡片 ID，保留旧版出处。

导入本地 MusicXML／MXL：

```sh
app/.venv/bin/python app/scripts/project.py import-score \
  --file /path/to/score.mxl --metadata /tmp/谱本元数据.json
```

元数据须包含 `title`、`composer`、`catalogue`、`movement`、`edition`、`license`、`source_url`；本地来源可用项目相对路径。还可填写 `aliases`、`coverage`、`collection_id`、`source_revision` 等。用 `previous_work_id` 表明旧谱本时，仍创建独立谱本，旧定位不会套用到新谱。工具保留原文件和 SHA-256。未知许可的候选材料应先留在研究阶段。

## 文件与技术结构

| 位置 | 作用 |
|---|---|
| [作品](作品/) | 带 YAML 元数据的 Markdown 卡片；正文、引用和片段是正式记录 |
| [assets/catalog.json](assets/catalog.json) | 作品、谱本版本、来源及曲名别名 |
| [assets/guides](assets/guides/) | 曲式目录、层级及概览 |
| [assets/scores](assets/scores/) | 原始谱本、来源、研究记录与已有分析生成材料 |
| [assets/generated](assets/generated/) | 稳定音符 ID 的 MEI、SVG 谱页和统一事件索引 |
| [assets/segments](assets/segments/) | Markdown 中片段元数据的 JSON 导出 |
| [assets/piano](assets/piano/) | 离线钢琴音源 |
| [app/frontend](app/frontend/) | React、TypeScript、Tone.js 本地阅读与试听界面 |
| [app/backend](app/backend/) | FastAPI 只读接口；Verovio、music21 处理及本地校验工具 |
| `app/.cache/` | 可删除重建的 SQLite FTS5 检索索引与缓存 |

保留 [来源与许可记录](assets/来源与许可.md) 以及各谱源的许可文件。旧 `.env`、`app/.local/` 和历史任务缓存不会被读取或删除，继续排除在 Git 之外。新版本不加载其中的 API 密钥。

## 备份与恢复

```sh
app/.venv/bin/python app/scripts/backup.py create /tmp/音乐导听备份.tar.gz
app/.venv/bin/python app/scripts/backup.py restore /tmp/音乐导听备份.tar.gz --into /tmp/音乐导听恢复
```

备份包含 `作品/` 与 `assets/`，不含依赖、缓存、旧密钥配置或浏览器存储。研究时避免一边写文件一边备份。恢复目标必须为空目录；核对后将恢复的内容与应用代码放在一起，运行 `project.py check` 和 `./start.sh`。项目规范与应用代码由 Git 保存。

## 开发与验证

```sh
app/.venv/bin/python -m pytest app/tests -q
npm --prefix app/frontend test
npm --prefix app/frontend run build
app/.venv/bin/python app/scripts/project.py check
git diff --check
```

保持应用运行后执行 `bash app/scripts/browser_tests.sh`，或用 `MUSIC_TEST_URL=http://127.0.0.1:8767` 指定测试服务。采用已有 Playwright CLI；首次若提示缺浏览器，在 `app/frontend` 执行 `npx playwright-cli install-browser`。验证别名检索、实际音频输出、全部活跃示例的音符高亮、来源阅读、选段交接、项目刷新、跨作品比较、柴一主题与前后文、窄屏布局。截图位于 `output/playwright/`。

开发前端可在 `app/frontend` 中执行 `npm run dev`，Vite 代理本地 API 与钢琴资源。正式运行由 FastAPI 提供构建页面。旧版内容准备脚本保留用于追溯，不在日常启动时执行；重跑前先检查是否会变更现有卡片。历次结果见 [验收记录](app/验收记录.md)。
