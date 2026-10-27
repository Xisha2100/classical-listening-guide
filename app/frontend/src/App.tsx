import { useEffect, useRef, useState } from "react";
import {
  ArrowLeft,
  ArrowUpRight,
  BookOpen,
  Check,
  ChevronLeft,
  ChevronRight,
  Disc3,
  FileMusic,
  Headphones,
  Library,
  LoaderCircle,
  Music2,
  Pause,
  Play,
  Plus,
  RefreshCw,
  Repeat2,
  Search,
  Settings2,
  Sparkles,
  Trash2,
  Upload,
  X,
} from "lucide-react";
import { api, blankAnalysis, blankSource } from "./types";
import type {
  Analysis,
  Job,
  NoteEvent,
  ScoreIndex,
  Segment,
  Source,
  Work,
} from "./types";
import * as player from "./player";
const kinds = ["全部", "动机", "主题", "变奏", "曲式", "和声"];
const statusText = {
  confirmed: "已定位",
  suggested: "待确认",
  unlocated: "待定位",
};
const originText = { seed: "谱例导听", manual: "个人笔记", model: "AI 推测" };
export default function App() {
  const [works, setWorks] = useState<Work[]>([]),
    [query, setQuery] = useState(""),
    [work, setWork] = useState<Work | null>(null),
    [index, setIndex] = useState<ScoreIndex | null>(null),
    [notes, setNotes] = useState<Analysis[]>([]),
    [filter, setFilter] = useState("全部"),
    [noteQuery, setNoteQuery] = useState("");
  const [draft, setDraft] = useState<Analysis | null>(null),
    [selection, setSelection] = useState<Segment | null>(null),
    [page, setPage] = useState(1),
    [svg, setSvg] = useState(""),
    [tab, setTab] = useState("笔记"),
    [editing, setEditing] = useState(false);
  const [startM, setStartM] = useState(1),
    [endM, setEndM] = useState(2),
    [staff, setStaff] = useState(""),
    [voice, setVoice] = useState(""),
    [clickStart, setClickStart] = useState<NoteEvent | null>(null);
  const [book, setBook] = useState<Source>(blankSource),
    [question, setQuestion] = useState("这段音乐的主题与动机有什么特点？"),
    [searchResults, setSearchResults] = useState<Source[]>([]),
    [chosenUrls, setChosenUrls] = useState<string[]>([]),
    [similar, setSimilar] = useState<Segment[]>([]);
  const [settings, setSettings] = useState({
      model: "",
      model_ready: false,
      model_local: false,
      search_ready: false,
    }),
    [showSettings, setShowSettings] = useState(false),
    [showImport, setShowImport] = useState(false),
    [importFile, setImportFile] = useState<File | null>(null),
    [importTitle, setImportTitle] = useState(""),
    [replace, setReplace] = useState(false);
  const [busy, setBusy] = useState(""),
    [job, setJob] = useState<Job | null>(null),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [playing, setPlaying] = useState(false),
    [speed, setSpeed] = useState(1),
    [loop, setLoop] = useState(false),
    [all, setAll] = useState(false),
    [activeIds, setActiveIds] = useState<string[]>([]);
  const [queryNotes, setQueryNotes] = useState<Analysis[] | null>(null);
  useEffect(() => {
    if (!work || !noteQuery.trim()) {
      setQueryNotes(null);
      return;
    }
    let live = true;
    const timer = setTimeout(() => {
      api<Analysis[]>(
        `/works/${work.id}/analyses?q=${encodeURIComponent(noteQuery)}`,
      )
        .then((ns) => {
          if (live) setQueryNotes(ns);
        })
        .catch((e) => {
          if (live) setError(e.message);
        });
    }, 180);
    return () => {
      live = false;
      clearTimeout(timer);
    };
  }, [work?.id, noteQuery, notes]);
  const scoreRef = useRef<HTMLDivElement>(null),
    fetchGeneration = useRef(0);
  const refreshWorks = () => api<Work[]>("/works").then(setWorks);
  useEffect(() => {
    refreshWorks().catch((e) => setError(e.message));
    api<typeof settings>("/settings")
      .then(setSettings)
      .catch((e) => setError(e.message));
    return () => player.stop();
  }, []);
  useEffect(() => {
    if (!work) return;
    const controller = new AbortController();
    setSvg("");
    fetch(`/api/works/${work.id}/pages/${page}`, { signal: controller.signal })
      .then((r) => {
        if (!r.ok) throw new Error("无法加载谱页");
        return r.text();
      })
      .then(setSvg)
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      });
    return () => controller.abort();
  }, [work?.id, page]);
  useEffect(() => {
    const el = scoreRef.current;
    if (!el) return;
    el.querySelectorAll(".selected-note,.sounding-note").forEach((n) =>
      n.classList.remove("selected-note", "sounding-note"),
    );
    selection?.note_ids.forEach((id) =>
      el
        .querySelector(`[id="${CSS.escape(id)}"]`)
        ?.classList.add("selected-note"),
    );
    activeIds.forEach((id) =>
      el
        .querySelector(`[id="${CSS.escape(id)}"]`)
        ?.classList.add("sounding-note"),
    );
  }, [svg, selection, activeIds]);
  useEffect(() => {
    if (!playing || !index || !activeIds.length) return;
    const e = index.events.find((n) => n.id === activeIds[0]);
    if (e && e.page !== page) setPage(e.page);
  }, [activeIds]);
  const halt = () => {
    player.stop();
    setPlaying(false);
    setActiveIds([]);
  };
  const run = async (label: string, fn: () => Promise<void>) => {
    setError("");
    setNotice("");
    setBusy(label);
    try {
      await fn();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  };
  function chooseSegment(s: Segment, idx = index) {
    if (!idx) return;
    halt();
    if (s.score_version !== idx.version) {
      setSelection(null);
      setError("此分析属于旧谱本，请在新谱上重新定位。");
      return;
    }
    setSelection(s);
    setStartM(s.start_measure + 1);
    setEndM(s.end_measure + 1);
    setStaff(s.staffs[0] || "");
    setVoice(s.voices[0] || "");
    setPage(idx.measures[s.start_measure]?.page || 1);
    setClickStart(null);
  }
  function chooseNote(a: Analysis, idx = index) {
    setDraft(structuredClone(a));
    setEditing(false);
    setTab("笔记");
    setSimilar([]);
    setNotice("");
    if (a.segments.length) chooseSegment(a.segments[0], idx);
    else {
      halt();
      setSelection(null);
    }
  }
  async function openWork(w: Work) {
    await run("加载乐谱", async () => {
      halt();
      const token = ++fetchGeneration.current;
      const [data, ns] = await Promise.all([
        api<{ work: Work; index: ScoreIndex }>(`/works/${w.id}/score`),
        api<Analysis[]>(`/works/${w.id}/analyses`),
      ]);
      if (token !== fetchGeneration.current) return;
      setWork(data.work);
      setIndex(data.index);
      setNotes(ns);
      setPage(1);
      setSearchResults([]);
      setChosenUrls([]);
      setFilter("全部");
      setNoteQuery("");
      setBook(blankSource());
      setJob(null);
      setClickStart(null);
      if (ns.length) chooseNote(ns[0], data.index);
      else {
        setDraft(blankAnalysis(w.id));
        setSelection(null);
        setEditing(true);
        setTab("笔记");
      }
    });
  }
  async function refreshNotes() {
    if (work) {
      const ns = await api<Analysis[]>(`/works/${work.id}/analyses`);
      setNotes(ns);
      return ns;
    }
    return [];
  }
  function newNote() {
    if (!work) return;
    halt();
    setDraft(blankAnalysis(work.id));
    setSelection(null);
    setEditing(true);
    setTab("笔记");
    setBook(blankSource());
    setNotice("");
    setSimilar([]);
  }
  async function save(confirm = false) {
    if (!draft || !work) return;
    await run("保存笔记", async () => {
      const segments = draft.segments.length
        ? draft.segments
        : selection
          ? [selection]
          : [];
      const saved = await api<Analysis>("/analyses", {
        ...draft,
        segments,
        status: confirm
          ? "confirmed"
          : segments.length
            ? draft.status === "confirmed"
              ? "confirmed"
              : "suggested"
            : "unlocated",
      });
      await refreshNotes();
      setDraft(saved);
      setEditing(false);
      setNotice("已保存到本机 Markdown 笔记。");
    });
  }
  async function makeRange() {
    if (!index || !work) return;
    await run("定位片段", async () => {
      if (startM < 1 || endM < startM || endM > index.measures.length)
        throw new Error("请检查小节范围。");
      const s = await api<Segment>(`/works/${work.id}/segments`, {
        id: "",
        label: `第 ${index.measures[startM - 1].label}—${index.measures[endM - 1].label} 小节`,
        score_version: index.version,
        start: index.measures[startM - 1].start,
        end: index.measures[endM - 1].end,
        staffs: staff ? [staff] : [],
        voices: voice ? [voice] : [],
        routes: [],
        note_ids: [],
      });
      chooseSegment(s);
    });
  }
  async function clickScore(target: EventTarget | null) {
    if (!index || playing || busy) return;
    const note = (target as Element).closest(".note");
    if (!note) return;
    const e = index.events.find((e) => e.id === note.id);
    if (!e) return;
    if (!clickStart) {
      setClickStart(e);
      setNotice("起点已选。再点一个音符，选定片段终点。");
      return;
    }
    await run("定位片段", async () => {
      const first = clickStart.onset <= e.onset ? clickStart : e,
        last = clickStart.onset <= e.onset ? e : clickStart;
      const s = await api<Segment>(`/works/${work!.id}/segments`, {
        id: "",
        label: "谱面选段",
        score_version: index.version,
        start: first.onset,
        end: last.onset + last.duration,
        staffs: [first.staff],
        voices:
          first.voice === last.voice && first.staff === last.staff
            ? [first.voice]
            : [],
        routes: [],
        note_ids: [],
      });
      chooseSegment(s);
      setNotice("已选择片段，可试听或绑定到笔记。");
    });
  }
  async function joinRoutes() {
    if (!draft || !index || !work) return;
    await run("合并声部接续", async () => {
      const segs = draft.segments;
      if (
        segs.some(
          (s) =>
            s.score_version !== index.version ||
            s.staffs.length !== 1 ||
            s.routes.length,
        )
      )
        throw new Error("请先为每段选择一个谱表，再接续。");
      const sorted = [...segs].sort((a, b) => a.start - b.start);
      const routes = sorted.map((s, i) => ({
        start: s.start,
        end: Math.min(s.end, sorted[i + 1]?.start ?? s.end),
        staff: s.staffs[0],
        voice: s.voices[0] || null,
      }));
      const merged = await api<Segment>(`/works/${work.id}/segments`, {
        label: "主题跨声部接续",
        score_version: index.version,
        start: sorted[0].start,
        end: Math.max(...sorted.map((s) => s.end)),
        staffs: [],
        voices: [],
        routes,
        note_ids: [],
      });
      setDraft({ ...draft, segments: [merged], status: "suggested" });
      chooseSegment(merged);
      setEditing(true);
      setNotice("按各片段起点切换声部；请试听确认并保存。");
    });
  }
  function attach() {
    if (!draft || !selection) return;
    setDraft({
      ...draft,
      segments: [
        ...draft.segments.filter((s) => s.id !== selection.id),
        structuredClone(selection),
      ],
      status: "suggested",
    });
    setEditing(true);
    setNotice("片段已加入草稿，保存后保留。");
  }
  async function playSegments(segs: Segment[]) {
    if (!index || !segs.length) return;
    if (segs.some((s) => s.score_version !== index.version)) {
      setError("谱例属于旧谱本，请重新定位后播放。");
      return;
    }
    setError("");
    setPlaying(true);
    try {
      await player.play(
        index,
        segs,
        speed,
        all,
        loop,
        setActiveIds,
        () => setPlaying(false),
        (s) => {
          setSelection(s);
          setPage(index.measures[s.start_measure]?.page || 1);
        },
      );
    } catch (e) {
      setPlaying(false);
      setError((e as Error).message);
    }
  }
  async function waitJob(j: Job) {
    setJob(j);
    while (j.status === "queued" || j.status === "running") {
      await new Promise((r) => setTimeout(r, 900));
      j = await api<Job>(`/jobs/${j.id}`);
      setJob(j);
    }
    if (j.status === "failed") throw new Error(j.error || "任务失败");
    return j.result;
  }
  async function research() {
    if (!work) return;
    await run("正在检索公开分析", async () => {
      const r = await waitJob(
        await api<Job>("/research", { work_id: work.id, question }),
      );
      setSearchResults(r.sources);
      setChosenUrls([]);
      setNotice(`找到 ${r.sources.length} 条资料，选择后提取正文。`);
    });
  }
  async function extract() {
    if (!work || !draft) return;
    await run("正在提取资料", async () => {
      const r = await waitJob(
        await api<Job>("/extract", { work_id: work.id, urls: chosenUrls }),
      );
      const sources: Source[] = r.sources;
      setDraft({
        ...draft,
        sources: [
          ...draft.sources.filter((s) => !sources.some((n) => n.url === s.url)),
          ...sources,
        ],
      });
      setNotice("资料已加入草稿。提取失败的条目仍标为搜索摘要。");
    });
  }
  async function analyze(mode: "sources" | "segment") {
    if (!work || !draft) return;
    await run("AI 正在结合证据分析", async () => {
      const segs =
        mode === "segment"
          ? draft.segments.length > 1
            ? draft.segments.slice(0, 2)
            : selection
              ? [selection]
              : []
          : [];
      const r = await waitJob(
        await api<Job>("/analysis-runs", {
          work_id: work.id,
          mode,
          question,
          sources: draft.sources,
          segments: segs,
        }),
      );
      await refreshNotes();
      if (r.analyses?.length) chooseNote(r.analyses[0]);
      setNotice("AI 草稿已保存。请试听候选片段，再确认定位。");
    });
  }
  async function retry() {
    if (!job) return;
    await run("重试任务", async () => {
      const r = await waitJob(await api<Job>(`/jobs/${job.id}/retry`, {}));
      if (job.kind === "search") setSearchResults(r.sources || []);
      if (job.kind === "extract" && draft)
        setDraft({ ...draft, sources: [...draft.sources, ...r.sources] });
      if (job.kind === "model") {
        await refreshNotes();
        if (r.analyses?.length) chooseNote(r.analyses[0]);
      }
    });
  }
  async function doImport() {
    if (!importFile) return;
    await run("导入并生成谱页，大型总谱需要一些时间", async () => {
      const f = new FormData();
      f.append("file", importFile);
      f.append("title", importTitle);
      if (replace && work) f.append("work_id", work.id);
      const w = await api<Work>("/import", f);
      setShowImport(false);
      await refreshWorks();
      await openWork(w);
    });
  }
  const filteredWorks = works.filter((w) =>
    [w.title, w.composer, w.catalogue, ...w.aliases]
      .join(" ")
      .toLowerCase()
      .replace(/[\s.]/g, "")
      .includes(query.toLowerCase().replace(/[\s.]/g, "")),
  );
  const visibleNotes = (queryNotes || notes).filter(
    (n) => filter === "全部" || n.kind === filter,
  );
  return (
    <div className={work ? "app workspace" : "app"}>
      <header className="topbar">
        <button
          className="brand"
          onClick={() => {
            if (!busy) {
              halt();
              setWork(null);
              setIndex(null);
              setDraft(null);
            }
          }}
        >
          <span className="brand-mark">
            <Music2 size={21} />
          </span>
          <span>
            听见结构<small>THE LISTENING ROOM</small>
          </span>
        </button>
        <div className="header-right">
          <span className="local-dot">本地资料库</span>
          <button
            className="icon-btn"
            aria-label="设置"
            onClick={() => setShowSettings(true)}
          >
            <Settings2 size={19} />
          </button>
        </div>
      </header>
      {(error || notice || busy) && (
        <div
          className={`message ${error ? "error" : ""}`}
          role={error ? "alert" : "status"}
        >
          {busy ? (
            <LoaderCircle size={16} className="spin" />
          ) : error ? (
            <span>!</span>
          ) : (
            <Check size={16} />
          )}
          <span>{error || busy || notice}</span>
          {!busy && job?.status === "failed" && (
            <button onClick={retry}>重试</button>
          )}
          {!busy && (
            <button
              aria-label="关闭提示"
              onClick={() => {
                setError("");
                setNotice("");
              }}
            >
              <X size={16} />
            </button>
          )}
        </div>
      )}
      {!work ? (
        <main className="library-page">
          <div className="hero">
            <div>
              <div className="eyebrow">A CLOSER LISTEN · 古典音乐导听</div>
              <h1>
                听见旋律，
                <br />
                <span>也听见它的来处。</span>
              </h1>
              <p>
                把书中的见解，放回音乐里。
                <br />
                寻找主题，比较变奏，让每一段分析都能被听见。
              </p>
            </div>
            <div className="hero-stave" aria-hidden="true">
              <div className="big-clef">𝄞</div>
              <div className="stave-lines">
                <span>♪</span>
                <span>♫</span>
                <span>♩</span>
              </div>
              <div className="stave-caption">READ. LISTEN. UNDERSTAND.</div>
            </div>
          </div>
          <div className="library-toolbar">
            <div>
              <h2>
                <Library size={20} /> 我的曲库{" "}
                <span>{works.length.toString().padStart(2, "0")}</span>
              </h2>
              <p>从一个熟悉的作品，开始新的聆听。</p>
            </div>
            <button
              className="button secondary"
              onClick={() => {
                setReplace(false);
                setShowImport(true);
              }}
            >
              <Upload size={16} />
              导入乐谱
            </button>
          </div>
          <label className="main-search">
            <Search size={21} />
            <input
              aria-label="搜索曲名"
              placeholder="搜索曲名、作曲家或作品编号，例如：命运、BWV 847"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            {query && (
              <button aria-label="清空搜索" onClick={() => setQuery("")}>
                <X size={18} />
              </button>
            )}
            <span>曲库检索</span>
          </label>
          <div className="work-grid">
            {filteredWorks.map((w, i) => (
              <button
                className="work-card"
                key={w.id}
                onClick={() => openWork(w)}
                disabled={!!busy}
                style={{ "--work-color": w.color } as React.CSSProperties}
              >
                <div className="work-art">
                  <span className="work-number">0{works.indexOf(w) + 1}</span>
                  <span className="work-era">{w.era}</span>
                  <img
                    src={`/api/works/${w.id}/pages/1`}
                    alt="乐谱预览"
                    loading="lazy"
                  />
                  <div className="work-letter">
                    {w.composer.includes("莫扎特")
                      ? "M"
                      : w.composer.includes("巴赫") ||
                          w.composer.includes("贝多芬")
                        ? "B"
                        : "♪"}
                  </div>
                </div>
                <div className="work-info">
                  <div className="work-catalogue">{w.catalogue}</div>
                  <h3>
                    {w.title}
                    <ArrowUpRight size={21} />
                  </h3>
                  <p className="composer">{w.composer}</p>
                  <p className="work-description">{w.description}</p>
                  <div className="work-bottom">
                    <span>
                      <FileMusic size={14} />
                      {w.movement}
                    </span>
                    <span>进入导听 →</span>
                  </div>
                </div>
              </button>
            ))}
          </div>
          {!filteredWorks.length && (
            <div className="empty">
              <FileMusic size={32} />
              <h3>这首作品还没有入库</h3>
              <p>可导入 MusicXML／MXL，或到公开曲库查找谱本。</p>
              <a
                className="button secondary"
                href={`https://imslp.org/index.php?search=${encodeURIComponent(query)}`}
                target="_blank"
                rel="noreferrer"
              >
                在 IMSLP 查找 <ArrowUpRight size={15} />
              </a>
            </div>
          )}
          <div className="library-note">
            <BookOpen size={20} />
            <div>
              <strong>你的导听书，也是资料库的一部分。</strong>
              <p>
                录入书名、页码与摘录，再将它们连接到真实谱例。所有笔记保存在这台电脑。
              </p>
            </div>
          </div>
          <footer>
            以开源乐谱为基础 · Verovio 排版 · Tone.js 钢琴复奏{" "}
            <span>为更专注的聆听而作</span>
          </footer>
        </main>
      ) : (
        <>
          <div className="work-heading">
            <button
              className="icon-btn"
              aria-label="返回曲库"
              disabled={!!busy}
              onClick={() => {
                halt();
                setWork(null);
              }}
            >
              <ArrowLeft size={19} />
            </button>
            <div>
              <div className="breadcrumb">
                我的曲库 <span>/</span> {work.composer}
              </div>
              <h1>
                {work.title} <small>{work.catalogue}</small>
              </h1>
            </div>
            <div className="heading-meta">
              <span>{work.movement}</span>
              <small>{work.edition} · 实音谱</small>
            </div>
            <button
              className="button secondary compact"
              onClick={newNote}
              disabled={!!busy}
            >
              <Plus size={15} />
              写分析
            </button>
          </div>
          <div className="desk">
            <aside className="analysis-panel">
              <div className="panel-title">
                导听笔记 <span>{notes.length.toString().padStart(2, "0")}</span>
              </div>
              <label className="small-search">
                <Search size={15} />
                <input
                  placeholder="查找分析或书籍摘录"
                  aria-label="搜索分析"
                  value={noteQuery}
                  onChange={(e) => setNoteQuery(e.target.value)}
                />
              </label>
              <div className="filters">
                {kinds.map((k) => (
                  <button
                    className={filter === k ? "active" : ""}
                    onClick={() => setFilter(k)}
                    key={k}
                  >
                    {k}
                  </button>
                ))}
              </div>
              <div className="analysis-list">
                {visibleNotes.map((a, i) => (
                  <button
                    key={a.id}
                    className={`analysis-item ${draft?.id === a.id ? "active" : ""}`}
                    onClick={() => chooseNote(a)}
                  >
                    <div className="analysis-kicker">
                      <span>{a.kind}</span>
                      <span>{statusText[a.status]}</span>
                    </div>
                    <h3>{a.title}</h3>
                    <p>
                      {a.body.slice(0, 66)}
                      {a.body.length > 66 ? "…" : ""}
                    </p>
                    <div className="analysis-origin">
                      <span>{originText[a.origin]}</span>
                      {a.segments.length > 0 && <Headphones size={14} />}
                    </div>
                  </button>
                ))}
                {!visibleNotes.length && (
                  <p className="muted empty-small">
                    还没有匹配的笔记。
                    <br />
                    从“写分析”开始。
                  </p>
                )}
              </div>
              <div className="sidebar-foot">
                <span className="local-dot">Markdown 保存在本机</span>
                <button
                  aria-label="刷新笔记索引"
                  className="icon-btn"
                  onClick={() =>
                    run("刷新索引", async () => {
                      const r = await api<{ errors: string[] }>("/reindex", {});
                      await refreshNotes();
                      setNotice(
                        r.errors.length ? r.errors.join("；") : "索引已刷新。",
                      );
                    })
                  }
                >
                  <RefreshCw size={14} />
                </button>
              </div>
            </aside>
            <main className="score-panel">
              <div className="score-toolbar">
                <span>
                  <FileMusic size={16} /> 乐谱 <small>实音</small>
                </span>
                <div>
                  <button
                    aria-label="上一谱页"
                    disabled={page <= 1}
                    onClick={() => setPage(page - 1)}
                  >
                    <ChevronLeft size={18} />
                  </button>
                  <span>
                    {page} / {index?.pages}
                  </span>
                  <button
                    aria-label="下一谱页"
                    disabled={page >= (index?.pages || 1)}
                    onClick={() => setPage(page + 1)}
                  >
                    <ChevronRight size={18} />
                  </button>
                </div>
              </div>
              <div className="range-tools">
                <label>
                  小节
                  <input
                    aria-label="起始小节序号"
                    type="number"
                    min={1}
                    max={index?.measures.length}
                    value={startM}
                    onChange={(e) => setStartM(+e.target.value)}
                  />
                </label>
                <span>—</span>
                <input
                  aria-label="结束小节序号"
                  type="number"
                  min={1}
                  max={index?.measures.length}
                  value={endM}
                  onChange={(e) => setEndM(+e.target.value)}
                />
                <select
                  aria-label="选择谱表"
                  value={staff}
                  onChange={(e) => {
                    setStaff(e.target.value);
                    setVoice("");
                  }}
                >
                  <option value="">全部谱表</option>
                  {index?.staffs.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.id}. {s.label}
                    </option>
                  ))}
                </select>
                <select
                  aria-label="选择声部"
                  value={voice}
                  onChange={(e) => setVoice(e.target.value)}
                >
                  <option value="">全部声部</option>
                  {(
                    index?.staffs.find((s) => s.id === staff)?.voices || []
                  ).map((v) => (
                    <option key={v} value={v}>
                      声部 {v}
                    </option>
                  ))}
                </select>
                <button
                  className="button secondary compact"
                  onClick={makeRange}
                  disabled={!!busy}
                >
                  选段
                </button>
              </div>
              <div className="score-tip">
                {clickStart
                  ? "已选起点，请点击终点音符"
                  : "点击两个音符可精确选择片段；上方小节按谱面顺序计数。"}
                <button
                  onClick={() => {
                    setReplace(true);
                    setShowImport(true);
                  }}
                  title="导入此作品的新谱本"
                >
                  更换谱本
                </button>
              </div>
              <div className="score-scroll">
                {svg ? (
                  <div
                    className="score-paper"
                    ref={scoreRef}
                    onClick={(e) => clickScore(e.target)}
                    dangerouslySetInnerHTML={{ __html: svg }}
                  />
                ) : (
                  <div className="loading-score">
                    <LoaderCircle className="spin" />
                    正在展开乐谱…
                  </div>
                )}
              </div>
              <div className="score-caption">
                <span>
                  {selection
                    ? `${selection.label} · ${selection.note_ids.length} 个谱面音符`
                    : "选择片段，开始试听"}
                </span>
                <span>谱面顺序播放 · 不展开反复</span>
              </div>
            </main>
            <aside className="detail-panel">
              <div className="detail-tabs">
                {["笔记", "资料", "AI 分析"].map((t) => (
                  <button
                    className={tab === t ? "active" : ""}
                    onClick={() => setTab(t)}
                    key={t}
                  >
                    {t === "AI 分析" && <Sparkles size={14} />} {t}
                  </button>
                ))}
              </div>
              <div className="detail-content">
                {draft && tab === "笔记" && (
                  <>
                    <div className="detail-kicker">
                      <span>{originText[draft.origin]}</span>
                      <span className={`status ${draft.status}`}>
                        {statusText[draft.status]}
                      </span>
                    </div>
                    {editing ? (
                      <>
                        <label className="field">
                          分析标题
                          <input
                            aria-label="分析标题"
                            value={draft.title}
                            onChange={(e) =>
                              setDraft({ ...draft, title: e.target.value })
                            }
                            placeholder="给这段音乐一个观察角度"
                          />
                        </label>
                        <label className="field">
                          类别
                          <select
                            value={draft.kind}
                            onChange={(e) =>
                              setDraft({ ...draft, kind: e.target.value })
                            }
                          >
                            {kinds.slice(1).map((k) => (
                              <option key={k}>{k}</option>
                            ))}
                          </select>
                        </label>
                        <label className="field">
                          我的分析
                          <textarea
                            aria-label="分析正文"
                            rows={9}
                            value={draft.body}
                            onChange={(e) =>
                              setDraft({ ...draft, body: e.target.value })
                            }
                            placeholder="写下你的理解，或到资料页粘贴书籍摘录。"
                          />
                        </label>
                      </>
                    ) : (
                      <>
                        <h2 className="detail-title">
                          {draft.title || "新的聆听笔记"}
                        </h2>
                        <div className="prose">
                          {draft.body.split("\n").map((p, i) => (
                            <p key={i}>{p}</p>
                          ))}
                        </div>
                        <button
                          className="text-button"
                          onClick={() => setEditing(true)}
                        >
                          编辑笔记 →
                        </button>
                      </>
                    )}
                    <div className="section-label">
                      对应谱例 <span>{draft.segments.length}</span>
                    </div>
                    <div className="segment-list">
                      {draft.segments.map((s, i) => (
                        <div
                          className={`segment-chip ${selection?.id === s.id ? "active" : ""}`}
                          key={s.id}
                        >
                          <button onClick={() => chooseSegment(s)}>
                            <Play size={13} />
                            <span>{s.label}</span>
                          </button>
                          {editing && (
                            <button
                              aria-label={`移除片段${i + 1}`}
                              onClick={() =>
                                setDraft({
                                  ...draft,
                                  segments: draft.segments.filter(
                                    (_, j) => j !== i,
                                  ),
                                  status: "suggested",
                                })
                              }
                            >
                              <X size={13} />
                            </button>
                          )}
                        </div>
                      ))}
                    </div>
                    <button
                      className="button secondary full"
                      disabled={!selection}
                      onClick={attach}
                    >
                      <Plus size={15} />
                      绑定当前选段
                    </button>
                    {draft.segments.length > 1 && (
                      <button
                        className="button secondary full"
                        onClick={() => playSegments(draft.segments)}
                      >
                        依次试听全部谱例
                      </button>
                    )}
                    {draft.segments.length > 1 && (
                      <button className="text-button" onClick={joinRoutes}>
                        按谱面时间接续各声部 →
                      </button>
                    )}
                    {selection && (
                      <button
                        className="text-button"
                        onClick={() =>
                          run("寻找相似片段", async () => {
                            const found = await api<Segment[]>(
                              `/works/${work.id}/similar`,
                              selection,
                            );
                            setSimilar(found);
                            setNotice(
                              found.length
                                ? `找到 ${found.length} 处相似旋律。`
                                : "没有找到精确或移调重复；这不代表不存在变奏关系。",
                            );
                          })
                        }
                      >
                        寻找相同或移调的动机 →
                      </button>
                    )}
                    {similar.map((s) => (
                      <button
                        className="similar-result"
                        key={s.id}
                        onClick={() => chooseSegment(s)}
                      >
                        {s.label}
                      </button>
                    ))}
                    {!!draft.sources.length && (
                      <>
                        <div className="section-label">引用资料</div>
                        {draft.sources.map((s) => (
                          <div className="citation" key={s.id}>
                            <BookOpen size={14} />
                            <div>
                              <strong>{s.title}</strong>
                              <p>
                                {[
                                  s.author,
                                  s.edition,
                                  s.pages && `第 ${s.pages} 页`,
                                ]
                                  .filter(Boolean)
                                  .join(" · ")}
                              </p>
                              {s.url && (
                                <a
                                  href={s.url}
                                  target="_blank"
                                  rel="noreferrer"
                                >
                                  查看来源 ↗
                                </a>
                              )}
                            </div>
                          </div>
                        ))}
                      </>
                    )}
                    {draft.verification && (
                      <p className="verification">
                        核验记录：{draft.verification}
                      </p>
                    )}
                    <div className="save-actions">
                      <button
                        className="button primary full"
                        disabled={!!busy || !draft.title.trim()}
                        onClick={() => save(false)}
                      >
                        保存笔记
                      </button>
                      <button
                        className="button secondary full"
                        disabled={
                          !!busy ||
                          (!draft.segments.length && !selection) ||
                          !draft.title.trim()
                        }
                        onClick={() => save(true)}
                      >
                        <Check size={15} />
                        确认定位并保存
                      </button>
                    </div>
                    <p className="muted micro">
                      确认表示谱例位置正确；AI 推测仍保留来源标记。
                    </p>
                    {draft.id && (
                      <button
                        className="delete-button"
                        onClick={() => {
                          if (window.confirm("删除这条分析笔记？"))
                            run("删除笔记", async () => {
                              await api(
                                `/analyses/${draft.id}`,
                                undefined,
                                "DELETE",
                              );
                              const ns = await refreshNotes();
                              if (ns.length) chooseNote(ns[0]);
                              else newNote();
                            });
                        }}
                      >
                        <Trash2 size={13} />
                        删除笔记
                      </button>
                    )}
                  </>
                )}
                {draft && tab === "资料" && (
                  <>
                    <div className="eyebrow">YOUR READING, CONNECTED</div>
                    <h2 className="detail-title">把书中的见解带进来</h2>
                    <p className="muted">摘录保留原文，个人解释写在笔记中。</p>
                    <label className="field">
                      书名 / 资料标题
                      <input
                        aria-label="书名"
                        value={book.title}
                        onChange={(e) =>
                          setBook({ ...book, title: e.target.value })
                        }
                      />
                    </label>
                    <div className="field-row">
                      <label className="field">
                        作者
                        <input
                          value={book.author}
                          onChange={(e) =>
                            setBook({ ...book, author: e.target.value })
                          }
                        />
                      </label>
                      <label className="field">
                        页码
                        <input
                          aria-label="页码"
                          value={book.pages}
                          onChange={(e) =>
                            setBook({ ...book, pages: e.target.value })
                          }
                        />
                      </label>
                    </div>
                    <label className="field">
                      版本
                      <input
                        value={book.edition}
                        onChange={(e) =>
                          setBook({ ...book, edition: e.target.value })
                        }
                        placeholder="出版社 / 年份"
                      />
                    </label>
                    <label className="field">
                      原文摘录
                      <textarea
                        aria-label="书籍摘录"
                        rows={6}
                        value={book.excerpt}
                        onChange={(e) =>
                          setBook({ ...book, excerpt: e.target.value })
                        }
                      />
                    </label>
                    <button
                      className="button primary full"
                      disabled={!book.title || !book.excerpt}
                      onClick={() => {
                        setDraft({
                          ...draft,
                          sources: [
                            ...draft.sources,
                            { ...book, extracted: true },
                          ],
                          title: draft.title || book.title,
                        });
                        setBook(blankSource());
                        setNotice("摘录已加入当前草稿，请保存笔记。");
                      }}
                    >
                      <Plus size={15} />
                      加入当前笔记
                    </button>
                    <div className="section-label">
                      已选资料 <span>{draft.sources.length}</span>
                    </div>
                    {draft.sources.map((s, i) => (
                      <details className="source-detail" key={s.id}>
                        <summary>
                          {s.title}
                          <span>
                            {s.kind === "web"
                              ? s.extracted
                                ? "已提取正文"
                                : "仅搜索摘要"
                              : "原文摘录"}
                          </span>
                        </summary>
                        <p className="prose">{s.excerpt}</p>
                        <button
                          className="text-button"
                          onClick={() =>
                            setDraft({
                              ...draft,
                              sources: draft.sources.filter((_, j) => j !== i),
                            })
                          }
                        >
                          从草稿移除
                        </button>
                      </details>
                    ))}
                    <div className="section-label">搜索公开分析</div>
                    <textarea
                      aria-label="搜索问题"
                      rows={3}
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                    />
                    <button
                      className="button secondary full"
                      disabled={!!busy || !question.trim()}
                      onClick={research}
                    >
                      <Search size={15} />
                      联网搜索
                    </button>
                    {!settings.search_ready && (
                      <p className="muted micro">
                        尚未配置 Tavily。可先录入书籍内容。
                      </p>
                    )}
                    {searchResults.map((s) => (
                      <label className="search-result" key={s.id}>
                        <input
                          type="checkbox"
                          checked={chosenUrls.includes(s.url)}
                          onChange={(e) =>
                            setChosenUrls(
                              e.target.checked
                                ? [...chosenUrls, s.url]
                                : chosenUrls.filter((u) => u !== s.url),
                            )
                          }
                        />
                        <span>
                          <strong>{s.title}</strong>
                          <small>{new URL(s.url).hostname} · 搜索摘要</small>
                          <p>{s.excerpt.slice(0, 180)}</p>
                          <a href={s.url} target="_blank" rel="noreferrer">
                            打开原文 ↗
                          </a>
                        </span>
                      </label>
                    ))}
                    {!!searchResults.length && (
                      <button
                        className="button primary full"
                        disabled={!!busy || !chosenUrls.length}
                        onClick={extract}
                      >
                        提取所选资料并加入笔记
                      </button>
                    )}
                  </>
                )}
                {draft && tab === "AI 分析" && (
                  <>
                    <div className="ai-symbol">
                      <Sparkles size={26} />
                    </div>
                    <h2 className="detail-title">带着证据，深入一段音乐。</h2>
                    <p className="muted">
                      模型读取你选中的资料和乐谱信息，返回独立草稿，保留原来的笔记。
                    </p>
                    <div className="context-box">
                      <span>
                        <BookOpen size={15} />
                        {draft.sources.length} 条引用资料
                      </span>
                      <span>
                        <FileMusic size={15} />
                        {draft.segments.length > 1
                          ? "比较前两个已绑定片段"
                          : selection
                            ? "当前选段已就绪"
                            : "尚未选择乐段"}
                      </span>
                      <small>
                        每个乐段最多 16 小节；资料分析只发送当前笔记的摘录。
                      </small>
                    </div>
                    <label className="field">
                      你想了解什么？
                      <textarea
                        aria-label="AI 分析问题"
                        rows={5}
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                      />
                    </label>
                    <button
                      className="button primary full"
                      disabled={!!busy || !selection || !question.trim()}
                      onClick={() => analyze("segment")}
                    >
                      <Sparkles size={16} />
                      {draft.segments.length > 1
                        ? "比较两个片段"
                        : "分析当前乐段"}
                    </button>
                    <button
                      className="button secondary full"
                      disabled={
                        !!busy || !draft.sources.length || !question.trim()
                      }
                      onClick={() => analyze("sources")}
                    >
                      整理资料并推荐谱例
                    </button>
                    <p className="muted micro">
                      候选位置需要试听确认。模型可以返回“待定位”，不会为无法识别的文字编造音符。
                    </p>
                    {!settings.model_ready && (
                      <div className="config-hint">
                        尚未配置模型服务。
                        <button onClick={() => setShowSettings(true)}>
                          查看配置方法 →
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>
            </aside>
          </div>
          <div className="player-bar">
            <div className="player-track">
              <span className="record-icon">
                <Disc3 className={playing ? "slow-spin" : ""} />
              </span>
              <div>
                <strong>{selection?.label || "选择一个谱例"}</strong>
                <small>{work.title} · 钢琴复奏</small>
              </div>
            </div>
            <div className="transport">
              <button
                className={`icon-btn ${loop ? "on" : ""}`}
                aria-label="循环播放"
                aria-pressed={loop}
                onClick={() => {
                  halt();
                  setLoop(!loop);
                }}
              >
                <Repeat2 size={19} />
              </button>
              <button
                className="play-button"
                aria-label={playing ? "停止播放" : "播放片段"}
                disabled={!selection}
                onClick={() =>
                  playing ? halt() : selection && playSegments([selection])
                }
              >
                {playing ? <Pause size={21} /> : <Play size={21} />}
              </button>
              <select
                aria-label="播放速度"
                value={speed}
                onChange={(e) => {
                  halt();
                  setSpeed(+e.target.value);
                }}
              >
                {[0.5, 0.75, 1, 1.25].map((n) => (
                  <option key={n} value={n}>
                    {n}×
                  </option>
                ))}
              </select>
            </div>
            <div className="player-options">
              <Headphones size={16} />
              <select
                aria-label="播放声部"
                value={all ? "all" : "theme"}
                onChange={(e) => {
                  halt();
                  setAll(e.target.value === "all");
                }}
              >
                <option value="theme">所选主题声部</option>
                <option value="all">范围内全部声部</option>
              </select>
              <span className="local-dot">本地音源</span>
            </div>
          </div>
        </>
      )}
      {showSettings && (
        <div className="modal-backdrop" onClick={() => setShowSettings(false)}>
          <section className="modal" onClick={(e) => e.stopPropagation()}>
            <button
              className="modal-close icon-btn"
              aria-label="关闭设置"
              onClick={() => setShowSettings(false)}
            >
              <X />
            </button>
            <div className="eyebrow">LOCAL FIRST</div>
            <h2>服务与本地资料</h2>
            <p>
              乐谱、笔记和钢琴复奏始终在本机。
              {settings.model_local
                ? "AI 分析使用本机 Ollama，无需 API 密钥。"
                : "AI 分析使用你配置的云端模型。"}
              联网搜索可单独配置 Tavily。
            </p>
            <div className="setting-row">
              大模型{" "}
              <strong>
                {settings.model_ready ? settings.model : "未配置"}
              </strong>
            </div>
            <div className="setting-row">
              Tavily 搜索{" "}
              <strong>{settings.search_ready ? "已配置" : "未配置"}</strong>
            </div>
            <p>
              复制 <code>app/.env.example</code> 为 <code>app/.env</code>
              ，填写模型名称和地址后重启应用。Ollama 须在本机运行，可用 ollama
              list 查看已安装模型。
            </p>
            <pre>
              LLM_MODEL={settings.model || "ollama_chat/qwen3.8:latest"}
              <br />
              LLM_API_KEY=（本地 Ollama 留空）
              <br />
              LLM_API_BASE=http://127.0.0.1:11434
              <br />
              TAVILY_API_KEY=（联网搜索可选）
            </pre>
            <p className="muted">
              正文与引用保存在「作品」，谱本和定位保存在「assets」。备份这两个目录即可保留个人资料。
            </p>
            <div className="license-line">
              排版：Verovio（LGPLv3） · 播放：Tone.js（MIT）
              <br />
              钢琴采样：Alexander Holm · Salamander（CC BY 3.0）
            </div>
          </section>
        </div>
      )}
      {showImport && (
        <div className="modal-backdrop">
          <section className="modal">
            <button
              aria-label="关闭导入"
              className="modal-close icon-btn"
              disabled={!!busy}
              onClick={() => setShowImport(false)}
            >
              <X />
            </button>
            <div className="eyebrow">ADD TO YOUR LIBRARY</div>
            <h2>{replace ? "为当前作品导入新谱本" : "导入数字乐谱"}</h2>
            <p>
              支持 MusicXML、XML 与 MXL，最大 20
              MB。谱本替换后，旧分析需重新定位。
            </p>
            <label className="field">
              作品名称
              <input
                aria-label="导入作品名称"
                value={importTitle}
                onChange={(e) => setImportTitle(e.target.value)}
              />
            </label>
            <label className="upload-field">
              <Upload />
              <input
                aria-label="选择乐谱文件"
                type="file"
                accept=".xml,.musicxml,.mxl"
                onChange={(e) => {
                  setImportFile(e.target.files?.[0] || null);
                  if (!importTitle)
                    setImportTitle(
                      e.target.files?.[0]?.name.replace(/\.[^.]+$/, "") || "",
                    );
                }}
              />
            </label>
            <button
              className="button primary full"
              disabled={!!busy || !importFile || !importTitle.trim()}
              onClick={doImport}
            >
              {busy ? "正在处理…" : "导入并生成乐谱"}
            </button>
            {error && (
              <p role="alert" className="error-text">
                {error}
              </p>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
