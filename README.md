# 听见结构：古典音乐导听助手

在本机浏览器中查找数字乐谱，把导听书摘录和个人分析连接到可播放的钢琴谱例。初始曲库包含巴赫 BWV 847 完整赋格、莫扎特 K.265 主题与前三个变奏、贝多芬第五交响曲第一乐章完整总谱，共 15 张示例分析卡片。

## 启动

已在本机安装所需依赖。在此目录执行：

```sh
./start.sh
```

浏览器打开 [本地导听助手](http://127.0.0.1:8765)。终端保持运行，按 `Ctrl+C` 停止。服务只监听 `127.0.0.1:8765`。

首次迁移到其他机器时，需要 Node.js 22 或更新版本，以及 uv 或 Python 3.12；启动脚本会安装锁定的依赖。首次安装需要联网，完成后查看谱面、编辑笔记和钢琴播放均使用本地文件，不需要外部服务。测试环境为 macOS、Python 3.12、Node.js 24、Chromium。

## 完成一次导听笔记

1. 搜索“命运”“贝五”“Op.67”，打开贝多芬第五交响曲。
2. 选择左侧示例分析，谱面高亮对应音符；点击底部播放按钮。可慢放、循环、切换主题声部或范围内全部声部。
3. 点击“写分析”，在“资料”页填写书名、作者、版本、页码及原文摘录，再加入当前笔记。个人解释在“笔记”页单独编辑。
4. 用起止小节、谱表和声部选择片段，或在谱面依次点击起点和终点音符。点击“绑定当前选段”。小节输入为从 1 开始的**谱面顺序序号**，显示标签保留印刷小节号；内部拍位单位为四分音符。
5. 一张卡片可绑定多个片段，分别试听或依次比较。不同时间段的单谱表片段可“按谱面时间接续各声部”；重叠区间在下一片段起点切换。
6. 试听后“确认定位并保存”。确认只改变定位状态，不把 AI 推测改写为人工分析。笔记与引用保存在本机，重开后仍可编辑。

巴赫示例使用不同谱表／声层；低声部在源谱内改变 voice 编号的地方使用整条下谱表。贝多芬“动机在弦乐声部间传递”预置了按 Hauptstimme 入口拍位接续的片段。莫扎特示例可比较主题、右手十六分音符、左手十六分音符和三连音变奏。

## 本地 Ollama 与可选联网搜索

默认使用本机 Ollama，当前已配置本机已有的 `qwen3.8:latest`，不需要模型 API 密钥。先确保 Ollama 已运行，再启动导听应用：

```sh
ollama list
# 如果 Ollama 尚未运行，可在另一终端运行：
ollama serve
```

`app/.env` 中的配置如下（[示例配置](app/.env.example) 同步提供默认值）：

```dotenv
LLM_MODEL=ollama_chat/qwen3.8:latest
LLM_API_BASE=http://127.0.0.1:11434
LLM_API_KEY=
LLM_TIMEOUT=300
TAVILY_API_KEY=
```

`ollama list` 中的完整模型名放在 `ollama_chat/` 后面。当前机器还已有 `gemma4:26b`，切换时可改为 `ollama_chat/gemma4:26b`，然后重启应用。本地接口地址使用 Ollama 根地址，不加 `/v1`。模型首次加载可能较慢，默认等待 300 秒；可按需调整 `LLM_TIMEOUT`（最多 1800 秒）。设置窗口表示配置已就绪，并不代表已经检测到模型进程。

本地模型通过 LiteLLM 的 [Ollama 接口](https://docs.litellm.ai/docs/providers/ollama) 调用。启用结构化 JSON 输出，返回结果仍经 Pydantic 和谱面／引用 ID 校验。分析资料只发送到本机 Ollama；不会在本地调用失败时转发给云端模型。本地模式不发送 `LLM_API_KEY`，可保留已有云端配置的密钥。

Tavily 仅用于可选的联网搜索，单独填写 `TAVILY_API_KEY`。“资料”页先搜索，再勾选结果、提取正文并加入笔记。提取失败时保留搜索摘要，明确显示“仅搜索摘要”。书籍手工摘录与本地模型分析不依赖 Tavily。

将来如需切换云端服务，可将 `LLM_MODEL` 改为对应的 LiteLLM 提供商／模型标识，填写 `LLM_API_KEY`，并清空或改写 `LLM_API_BASE`；修改后重启。使用云端模型时，选中的摘录与结构化乐谱信息会发送到该服务。

“AI 分析”提供两种操作：整理资料并推荐已有候选谱例，或分析当前乐段／比较前两个已绑定片段。每个片段最多 16 小节，合计最多 2,000 个发音事件。模型返回独立草稿，引用和片段 ID 必须通过校验；不能确定位置时保存为“待定位”。服务失败可以重试，不影响原笔记。未配置搜索密钥时，Ollama 分析和其他本地功能仍可正常使用。

## 导入与谱本版本

支持 MusicXML／MXL（MusicXML `score-partwise`，最大 20 MB；MXL 解压总大小最多 30 MB）。首页“导入乐谱”创建作品，作品页“更换谱本”创建该作品的新版本。版本由规范化内容与渲染配置计算，原文件保留 SHA-256。

谱面、模型定位和播放共享生成的 MEI 音符 ID 与事件索引。更换谱本后，旧分析保留，但旧片段不能播放或确认为新谱本位置，需重新选择。生成谱面采用**实音记谱**，钢琴按实际音高复奏，包含移调乐器的转换。原始移调记谱保留在源文件中。

播放按谱面顺序一次经过各小节，不执行反复跳转；延长记号按记谱时值处理，不模拟演奏者的自由延长。钢琴采样复奏保留所选声部音符，不生成双手缩编。相似检索覆盖单旋律的相同音程与相对节奏模式，不能自动确认复杂变奏或完整曲式。

## 数据与目录

| 路径 | 内容 |
|---|---|
| [app/backend](app/backend/) | FastAPI、乐谱入库、校验、搜索和模型服务 |
| [app/frontend](app/frontend/) | React、TypeScript、Vite、Tone.js 界面 |
| [作品](作品/) | Markdown 笔记；YAML 中保留书目、原文和完整片段定位 |
| [assets/catalog.json](assets/catalog.json) | 作品、别名、谱本版本、来源与文件哈希 |
| [assets/scores](assets/scores/) | 原始数字谱、上游标注和来源说明 |
| [assets/generated](assets/generated/) | 每个版本的 MEI、SVG 页与事件索引 |
| [assets/segments](assets/segments/) | 片段 JSON 副本，方便其他程序读取 |
| [assets/piano](assets/piano/) | 本地 Salamander MP3 采样与署名 |
| `app/.cache` | 可重建的 SQLite FTS5 索引、分词缓存、搜索及模型运行记录 |

Markdown 是笔记的权威记录，使用原子替换写入；JSON 片段文件是结构化副本。应用启动和“刷新笔记索引”都会重建 FTS5。删除 SQLite 不会丢失笔记；删除缓存会丢失临时搜索结果、任务记录与重试能力。初始示例只初始化一次，删除后不会在每次启动时复活。

可用外部编辑器修改 Markdown 正文与引用，保留 YAML 的 ID、作品 ID 和片段字段，再点击刷新。无法解析的笔记会报告文件名，不被静默覆盖。位置采用零基小节内部索引，拍位采用四分音符单位。

## 备份与恢复

停止应用后备份，以避免恰好写入时截取到不同状态：

```sh
app/.venv/bin/python app/scripts/backup.py create /tmp/音乐导听备份.tar.gz
app/.venv/bin/python app/scripts/backup.py restore /tmp/音乐导听备份.tar.gz --into /tmp/音乐导听恢复
```

备份包含 `作品` 和 `assets`，不含 API 密钥、依赖或缓存。恢复目标必须为空目录。核对恢复后的目录，再将其中的 `作品`、`assets` 放到另一份应用代码旁，运行 `./start.sh`。启动时会从笔记重建 SQLite。配置文件 `app/.env` 如需迁移，应单独保管。

## 开发与验证

```sh
PYTHONPATH=app app/.venv/bin/python -m pytest app/tests -q
cd app/frontend
npm test
npm run build
```

开发时可分别启动 FastAPI（端口 8765）与 `npm run dev`，Vite 将 `/api` 和钢琴资源代理给后端。生产运行由 FastAPI 提供 Vite 构建产物。

保持应用运行，在另一终端执行 `app/scripts/browser_tests.sh`。回归测试使用 Chromium／Chrome；首次若提示没有浏览器，先在 `app/frontend` 执行 `npx playwright-cli install-browser`。

浏览器回归脚本为 [browser-smoke.js](app/tests/browser-smoke.js)，以 Playwright CLI 的 `run-code` 运行，覆盖别名搜索、真实音频非静音输出、录入书籍、绑定确认、重开编辑和窄屏布局。脚本只删除自身创建的临时笔记。截图输出到 `output/playwright`。后端测试不需要云端密钥，模型和搜索以模拟响应验证。

详细验收结果和边界见 [验收记录](app/验收记录.md)。原始乐谱、采样与生成文件的许可见 [来源与许可](assets/来源与许可.md)。
