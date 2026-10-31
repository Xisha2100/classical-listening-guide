import { useEffect, useRef, useState } from "react";
import {
  ArrowLeft,
  ArrowUpRight,
  BookOpen,
  Check,
  ChevronLeft,
  ChevronRight,
  Copy,
  Disc3,
  FileMusic,
  Headphones,
  Library,
  LoaderCircle,
  Music2,
  Pause,
  Play,
  RefreshCw,
  Repeat2,
  Search,
  X,
} from "lucide-react";
import { api, dimensions, normalizeAnalysis } from "./types";
import { AnalysisDetails, GuidePanel, SourceView } from "./AnalysisDetails";
import ComparisonViewer from "./ComparisonViewer";
import type { PlayingComparison } from "./ComparisonViewer";
import {
  COMPARE_KEY,
  readComparison,
  addComparison,
  legacyDrafts,
} from "./comparison";
import type {
  Analysis,
  NoteEvent,
  ScoreIndex,
  Segment,
  Work,
  Collection,
  Guide,
  ComparisonEntry,
} from "./types";
import * as player from "./player";
import {
  withContext,
  printedRange,
  segmentRoleLabel,
  sectionDepth,
  sectionWithin,
} from "./listening";
const kinds = ["全部", ...dimensions];
const statusText = {
  confirmed: "已定位",
  suggested: "待确认",
  unlocated: "待定位",
  not_applicable: "概览",
};
const originText = {
  seed: "谱例导听",
  manual: "个人笔记",
  model: "模型分析记录",
};
export default function App() {
  const [works, setWorks] = useState<Work[]>([]),
    [collections, setCollections] = useState<Collection[]>([]);
  const [query, setQuery] = useState(""),
    [collectionFilter, setCollectionFilter] = useState("");
  const [work, setWork] = useState<Work | null>(null),
    [index, setIndex] = useState<ScoreIndex | null>(null);
  const [notes, setNotes] = useState<Analysis[]>([]),
    [draft, setDraft] = useState<Analysis | null>(null);
  const [guide, setGuide] = useState<Guide | null>(null),
    [sectionFilter, setSectionFilter] = useState("");
  const [filter, setFilter] = useState("全部"),
    [noteQuery, setNoteQuery] = useState("");
  const [selection, setSelection] = useState<Segment | null>(null),
    [page, setPage] = useState(1),
    [svg, setSvg] = useState("");
  const [tab, setTab] = useState("笔记"),
    [startM, setStartM] = useState(1),
    [endM, setEndM] = useState(2);
  const [staff, setStaff] = useState(""),
    [voice, setVoice] = useState(""),
    [clickStart, setClickStart] = useState<NoteEvent | null>(null);
  const [busy, setBusy] = useState(""),
    [error, setError] = useState(""),
    [notice, setNotice] = useState("");
  const [playing, setPlaying] = useState(false),
    [speed, setSpeed] = useState(1),
    [loop, setLoop] = useState(false),
    [all, setAll] = useState(false);
  const [activeIds, setActiveIds] = useState<string[]>([]),
    [contextMeasures, setContextMeasures] = useState(2);
  const [playbackWindow, setPlaybackWindow] = useState<Segment | null>(null),
    [abIds, setAbIds] = useState<string[]>([]);
  const [comparison, setComparison] =
      useState<ComparisonEntry[]>(readComparison),
    [comparisonTitle, setComparisonTitle] = useState("");
  const [showComparison, setShowComparison] = useState(false),
    [comparisonView, setComparisonView] = useState<PlayingComparison | null>(
      null,
    );
  const [comparisonActiveIds, setComparisonActiveIds] = useState<string[]>([]),
    [selectionExport, setSelectionExport] = useState("");
  const [oldDrafts] = useState(legacyDrafts);
  const playingWork = useRef("");
  useEffect(() => {
    try {
      localStorage.setItem(COMPARE_KEY, JSON.stringify(comparison));
    } catch {
      setError("无法保存比较队列。");
    }
  }, [comparison]);
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
    fetchGeneration = useRef(0),
    playbackRequest = useRef(0);
  useEffect(() => {
    Promise.all([
      api<Work[]>("/works"),
      api<Collection[]>("/collections"),
      api<{ note_errors: string[] }>("/health"),
    ])
      .then(([ws, cs, health]) => {
        setWorks(ws);
        setCollections(cs);
        if (health.note_errors.length) setError(health.note_errors.join("；"));
      })
      .catch((e) => setError(e.message));
    return () => player.stop();
  }, []);
  useEffect(() => {
    if (!work || !index || work.availability === "pending") {
      setSvg("");
      return;
    }
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
  }, [work?.id, index?.version, page]);
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
    // Orchestral pages are taller than the viewport. Bring the chosen voice into
    // the score pane instead of leaving the user looking at resting woodwinds.
    const paper = scoreRef.current,
      scroller = paper?.parentElement;
    const target = paper?.querySelector(".selected-note, .sounding-note");
    if (!scroller || !target) return;
    const rect = target.getBoundingClientRect(),
      area = scroller.getBoundingClientRect();
    scroller.scrollTop += rect.top - area.top - area.height * 0.35;
  }, [svg, selection?.id]);
  useEffect(() => {
    if (
      !playing ||
      !index ||
      !activeIds.length ||
      (playingWork.current && playingWork.current !== work?.id)
    )
      return;
    const e = index.events.find((n) => n.id === activeIds[0]);
    if (e && e.page !== page) setPage(e.page);
  }, [activeIds]);
  const halt = () => {
    playbackRequest.current++;
    player.stop();
    setPlaying(false);
    setActiveIds([]);
    setComparisonTitle("");
    setComparisonActiveIds([]);
    setPlaybackWindow(null);
    playingWork.current = "";
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
    if (!idx) {
      halt();
      setSelection(null);
      return;
    }
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
    setDraft(normalizeAnalysis(a));
    setTab("笔记");
    setAbIds([]);
    setNotice("");
    if (a.segments.length) chooseSegment(a.segments[0], idx);
    else {
      halt();
      setSelection(null);
      setClickStart(null);
    }
  }
  async function loadWork(w: Work, refresh = false) {
    halt();
    const token = ++fetchGeneration.current;
    const [data, rawNotes, g] = await Promise.all([
      w.availability === "pending"
        ? Promise.resolve({ work: w, index: null })
        : api<{ work: Work; index: ScoreIndex }>(`/works/${w.id}/score`),
      api<Analysis[]>(`/works/${w.id}/analyses`),
      api<Guide>(`/works/${w.id}/guide`),
    ]);
    if (token !== fetchGeneration.current) return;
    const ns = rawNotes.map(normalizeAnalysis);
    setWork(data.work);
    setIndex(data.index);
    setNotes(ns);
    setGuide({ ...g, sources: g.sources || [] });
    setPage(1);
    setClickStart(null);
    setQueryNotes(null);
    if (!refresh) {
      setSectionFilter("");
      setFilter("全部");
      setNoteQuery("");
    } else if (sectionFilter && !g.sections.some((s) => s.id === sectionFilter))
      setSectionFilter("");
    const chosen = (refresh && ns.find((n) => n.id === draft?.id)) || ns[0];
    if (chosen) chooseNote(chosen, data.index);
    else {
      setDraft(null);
      setSelection(null);
    }
    setTab(refresh ? tab : g.overview ? "导听" : "笔记");
  }
  const openWork = (w: Work) => run("加载本地乐谱与分析", () => loadWork(w));
  async function refreshProject() {
    await run("读取项目最新内容", async () => {
      const result = await api<{ errors: string[] }>("/reindex", {});
      const [ws, cs] = await Promise.all([
        api<Work[]>("/works"),
        api<Collection[]>("/collections"),
      ]);
      setWorks(ws);
      setCollections(cs);
      if (work) {
        const updated = ws.find((w) => w.id === work.id);
        if (updated) await loadWork(updated, true);
        else backToLibrary();
      }
      if (result.errors.length) setError(result.errors.join("；"));
      else setNotice("已读取本地最新分析、目录和谱本。");
    });
  }
  function backToLibrary() {
    halt();
    fetchGeneration.current++;
    setWork(null);
    setIndex(null);
    setDraft(null);
    setSelection(null);
    setError("");
    setNotice("");
  }
  async function copySelection() {
    if (!work || !selection || !index) return;
    const text = JSON.stringify(
      {
        work_id: work.id,
        work_title: work.title,
        analysis_id: draft?.id || "",
        printed_range: printedRange(index, selection),
        segment: selection,
      },
      null,
      2,
    );
    setSelectionExport(text);
    try {
      await navigator.clipboard.writeText(text);
      setNotice("选段已复制；回到 Codex 粘贴，并说明想分析什么。");
    } catch {
      setNotice("选段已展开，可手动复制到 Codex。");
    }
  }
  function exportLegacyDrafts() {
    if (!oldDrafts) return;
    const url = URL.createObjectURL(
      new Blob([oldDrafts], { type: "application/json" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = "旧版浏览器草稿.json";
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    setNotice(
      "旧草稿已导出，请交给 Codex 整理入库；浏览器中的原始草稿仍保留。",
    );
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
        staffs: [...new Set([first.staff, last.staff])],
        voices:
          first.voice === last.voice && first.staff === last.staff
            ? [first.voice]
            : [],
        routes: [],
        note_ids: [],
      });
      chooseSegment(s);
      setNotice("已选择片段，可试听或复制给 Codex。");
    });
  }
  async function playSegments(segs: Segment[], context = 0) {
    if (!index || !segs.length) return;
    if (segs.some((s) => s.score_version !== index.version)) {
      setError("谱例属于旧谱本，请重新定位后播放。");
      return;
    }
    setError("");
    setPlaying(true);
    setComparisonTitle("");
    playingWork.current = work?.id || "";
    try {
      const windows = segs.map((s) => withContext(index, s, context));
      await player.play(
        index,
        windows,
        speed,
        context > 0 || all,
        loop,
        setActiveIds,
        () => {
          setPlaying(false);
          setPlaybackWindow(null);
        },
        (s) => {
          // Playback context must not overwrite the saved analysis anchor.
          const anchor = segs.find((original) => original.id === s.id) || s;
          setSelection(anchor);
          setStartM(anchor.start_measure + 1);
          setEndM(anchor.end_measure + 1);
          setStaff(anchor.staffs[0] || "");
          setVoice(anchor.voices[0] || "");
          setPlaybackWindow(s);
          setPage(index.measures[s.start_measure]?.page || 1);
        },
      );
    } catch (e) {
      setPlaying(false);
      setPlaybackWindow(null);
      setError((e as Error).message);
    }
  }
  const filteredWorks = works
    .filter(
      (w) =>
        !collectionFilter ||
        w.collection_id === collectionFilter ||
        collections
          .find((c) => c.id === collectionFilter)
          ?.work_ids.includes(w.id),
    )
    .filter((w) =>
      [w.title, w.composer, w.catalogue, w.movement, ...(w.aliases || [])]
        .join(" ")
        .toLowerCase()
        .replace(/[\s.]/g, "")
        .includes(query.toLowerCase().replace(/[\s.]/g, "")),
    );
  const visibleNotes = (queryNotes || notes).filter(
    (n) =>
      (filter === "全部" ||
        n.kind === filter ||
        n.dimensions?.includes(filter)) &&
      sectionWithin(guide?.sections || [], n.section_id, sectionFilter),
  );
  function focusSection(id: string) {
    setSectionFilter(id);
    setTab("导听");
    const section = guide?.sections.find((s) => s.id === id);
    if (index && section?.start_measure != null) {
      halt();
      setPage(index.measures[section.start_measure]?.page || 1);
      setSelection(null);
    }
  }
  function queueSegment(s: Segment) {
    if (!work) return;
    try {
      setComparison(
        addComparison(comparison, {
          id: crypto.randomUUID(),
          work_id: work.id,
          work_title: `${work.title} · ${work.movement}`,
          segment: structuredClone(s),
        }),
      );
      setNotice("已加入跨作品 A/B 比较，队列保存在此浏览器。");
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function playComparison() {
    await run("准备 A/B 比较", async () => {
      halt();
      const request = playbackRequest.current;
      setComparisonView(null);
      setShowComparison(true);
      const entries = await Promise.all(
        comparison.map(async (item) => {
          const data = await api<{ index: ScoreIndex }>(
            `/works/${item.work_id}/score`,
          );
          if (data.index.version !== item.segment.score_version)
            throw new Error(
              `${item.work_title} 的谱本已变更，请重新加入谱例。`,
            );
          return {
            index: data.index,
            segment: item.segment,
            work_id: item.work_id,
          };
        }),
      );
      if (!entries.length || request !== playbackRequest.current) return;
      setPlaying(true);
      await player
        .playItems(
          entries,
          speed,
          all,
          loop,
          (ids) => {
            setActiveIds([]);
            setComparisonActiveIds(ids);
          },
          () => {
            setPlaying(false);
            setComparisonTitle("");
            playingWork.current = "";
          },
          (seg, idx, wid) => {
            playingWork.current = wid;
            const item = comparison.find(
              (x) => x.work_id === wid && x.segment.id === seg.id,
            );
            setComparisonTitle(`${item?.work_title || "比较"} · ${seg.label}`);
            if (item) setComparisonView({ entry: item, index: idx });
            setActiveIds([]);
          },
        )
        .catch((e) => {
          setPlaying(false);
          throw e;
        });
    });
  }
  const currentCollection = collections.find(
    (c) => c.id === work?.collection_id,
  );
  return (
    <div className={work ? "app workspace" : "app"}>
      <header className="topbar">
        <button className="brand" disabled={!!busy} onClick={backToLibrary}>
          <span className="brand-mark">
            <Music2 size={21} />
          </span>
          <span>
            听见结构<small>THE LISTENING ROOM</small>
          </span>
        </button>
        <div className="header-right">
          <span className="local-dot">Codex 项目 · 本地阅读</span>
          {oldDrafts && (
            <button className="text-button" onClick={exportLegacyDrafts}>
              导出旧版草稿
            </button>
          )}
          <button
            className="button secondary compact"
            disabled={!!busy}
            onClick={refreshProject}
          >
            <RefreshCw size={15} />
            刷新项目
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
                在 Codex 中分析与记录，在这里对谱聆听。
                <br />
                从曲式、和声到织体，让每一段分析都能被听见。
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
          {collections.length > 0 && (
            <div className="collection-strip">
              <button
                className={!collectionFilter ? "active" : ""}
                onClick={() => setCollectionFilter("")}
              >
                全部作品
              </button>
              {collections.map((c) => (
                <button
                  className={collectionFilter === c.id ? "active" : ""}
                  key={c.id}
                  onClick={() => setCollectionFilter(c.id)}
                >
                  {c.title}
                  <small>
                    {c.arranger ? `${c.arranger} · ` : ""}
                    {c.work_ids.length} 个乐章 / 分曲
                  </small>
                </button>
              ))}
            </div>
          )}
          {collectionFilter && (
            <div className="collection-overview">
              <p>
                {collections.find((c) => c.id === collectionFilter)?.overview ||
                  collections.find((c) => c.id === collectionFilter)
                    ?.description}
              </p>
              {(
                collections.find((c) => c.id === collectionFilter)?.missing ||
                []
              ).map((m, i) => (
                <p className="muted" key={i}>
                  待补充：{typeof m === "string" ? m : JSON.stringify(m)}
                </p>
              ))}
            </div>
          )}
          <div className="library-toolbar">
            <div>
              <h2>
                <Library size={20} />
                我的曲库 <span>{String(works.length).padStart(2, "0")}</span>
              </h2>
              <p>本地乐谱与分析，随时重读和比较。</p>
            </div>
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
            <span>本地曲库</span>
          </label>
          <div className="work-grid">
            {filteredWorks.map((w) => (
              <button
                className="work-card"
                key={w.id}
                data-work-id={w.id}
                onClick={() => openWork(w)}
                disabled={!!busy}
                style={{ "--work-color": w.color } as React.CSSProperties}
              >
                <div className="work-art">
                  <span className="work-number">
                    {String(works.indexOf(w) + 1).padStart(2, "0")}
                  </span>
                  <span className="work-era">{w.era}</span>
                  {w.availability !== "pending" && (
                    <img
                      src={`/api/works/${w.id}/pages/1`}
                      alt="乐谱预览"
                      loading="lazy"
                    />
                  )}
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
                  <span
                    className={`availability ${w.availability === "pending" ? "pending" : ""}`}
                  >
                    {w.availability === "pending"
                      ? "完整数字谱待补充 · 可阅读资料"
                      : `${w.score_type || "数字谱"} · ${w.coverage || "谱例可试听"}`}
                  </span>
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
              <p>请在 Codex 项目中补充乐谱与分析，然后点击“刷新项目”。</p>
            </div>
          )}
          <div className="library-note">
            <BookOpen size={20} />
            <div>
              <strong>分析和笔记，留在你的项目里。</strong>
              <p>
                在 Codex
                中提供导听书摘录、提出分析问题或修订意见。记录保存为本地
                Markdown 与 JSON，这里读取最新内容并展示对应乐谱。
              </p>
            </div>
          </div>
        </main>
      ) : (
        <>
          <div className="work-heading">
            <button
              className="back-button"
              aria-label="返回曲库"
              disabled={!!busy}
              onClick={backToLibrary}
            >
              <ArrowLeft size={18} />
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
              <small>
                {work.edition} ·{" "}
                {work.availability === "pending" ? "完整谱待补充" : "实音谱"}
              </small>
            </div>
          </div>
          {currentCollection && (
            <nav className="movement-nav" aria-label="同作品乐章">
              <span>
                {currentCollection.title}
                {currentCollection.arranger
                  ? ` · ${currentCollection.arranger}`
                  : ""}
              </span>
              {works
                .filter((w) => currentCollection.work_ids.includes(w.id))
                .sort(
                  (a, b) => (a.movement_order || 0) - (b.movement_order || 0),
                )
                .map((w) => (
                  <button
                    key={w.id}
                    className={work.id === w.id ? "active" : ""}
                    disabled={!!busy}
                    onClick={() => openWork(w)}
                  >
                    {w.movement}
                    {w.availability === "pending" ? " · 缺谱" : ""}
                  </button>
                ))}
            </nav>
          )}
          <div className="desk">
            <aside className="analysis-panel">
              <div className="panel-title">
                导听笔记 <span>{notes.length.toString().padStart(2, "0")}</span>
              </div>
              {guide && (
                <label className="sidebar-select">
                  <span>曲式范围</span>
                  <select
                    aria-label="筛选导听章节"
                    value={sectionFilter}
                    title={
                      guide.sections.find((s) => s.id === sectionFilter)
                        ?.title || "全貌与全部笔记"
                    }
                    onChange={(e) => focusSection(e.target.value)}
                  >
                    <option value="">全貌与全部笔记</option>
                    {guide.sections.map((s, i) => (
                      <option key={s.id} value={s.id}>
                        {"　".repeat(sectionDepth(guide.sections, s.id))}
                        {String(i + 1).padStart(2, "0")} · {s.title}
                      </option>
                    ))}
                  </select>
                </label>
              )}
              <label className="small-search">
                <Search size={15} />
                <input
                  placeholder="查找分析或书籍摘录"
                  aria-label="搜索分析"
                  value={noteQuery}
                  onChange={(e) => setNoteQuery(e.target.value)}
                />
              </label>
              <label className="sidebar-select dimension-select">
                <span>分析维度</span>
                <select
                  aria-label="筛选分析维度"
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                >
                  {kinds.map((k) => (
                    <option key={k} value={k}>
                      {k === "全部" ? "全部分析" : k}
                    </option>
                  ))}
                </select>
              </label>
              <div className="analysis-list">
                {visibleNotes.map((a, i) => (
                  <button
                    key={a.id}
                    data-analysis-id={a.id}
                    disabled={!!busy}
                    className={`analysis-item ${draft?.id === a.id ? "active" : ""}`}
                    onClick={() => chooseNote(a)}
                  >
                    <div className="analysis-kicker">
                      <span>{a.dimensions?.join(" · ") || a.kind}</span>
                      <span>{statusText[a.status]}</span>
                    </div>
                    <h3>{a.title}</h3>
                    <p>
                      {a.body.slice(0, 66)}
                      {a.body.length > 66 ? "…" : ""}
                    </p>
                    <div className="analysis-origin">
                      <span>
                        {originText[a.origin]} ·{" "}
                        {a.review_status === "checked"
                          ? "内容已核对"
                          : "内容待核对"}
                      </span>
                      {a.segments.length > 0 && <Headphones size={14} />}
                    </div>
                  </button>
                ))}
                {!visibleNotes.length && (
                  <p className="muted empty-small">
                    还没有匹配的笔记。
                    <br />
                    可在 Codex 中补充。
                  </p>
                )}
              </div>
              <div className="sidebar-foot">
                <span className="local-dot">Markdown 保存在本机</span>
                <button
                  aria-label="刷新笔记索引"
                  className="icon-btn"
                  disabled={!!busy}
                  onClick={refreshProject}
                >
                  <RefreshCw size={14} />
                </button>
              </div>
            </aside>{" "}
            <main className="score-panel">
              {guide && sectionFilter && (
                <div className="section-context">
                  <strong>
                    {guide.sections.find((s) => s.id === sectionFilter)?.title}
                  </strong>
                  <p>
                    {
                      guide.sections.find((s) => s.id === sectionFilter)
                        ?.description
                    }
                  </p>
                </div>
              )}
              {work.availability === "pending" ? (
                <div className="empty pending-score">
                  <FileMusic size={36} />
                  <h3>完整数字谱尚未入库</h3>
                  <p>现有资料可以阅读。请在 Codex 中补充谱本后刷新项目。</p>
                </div>
              ) : (
                <>
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
                    <button disabled={!selection} onClick={copySelection}>
                      复制选段给 Codex
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
                </>
              )}
            </main>
            <aside className="detail-panel">
              <div className="detail-tabs">
                {["导听", "笔记", "资料"].map((t) => (
                  <button
                    className={tab === t ? "active" : ""}
                    onClick={() => setTab(t)}
                    key={t}
                  >
                    {t}
                  </button>
                ))}
              </div>
              <fieldset className="detail-content" disabled={!!busy}>
                {tab === "导听" && guide && (
                  <GuidePanel
                    guide={guide}
                    index={index}
                    onSection={focusSection}
                    noteSources={notes.flatMap((note) => note.sources)}
                  />
                )}
                {draft && tab === "笔记" && (
                  <>
                    <div className="detail-kicker">
                      <span>{originText[draft.origin]}</span>
                      <span className={`status ${draft.status}`}>
                        {statusText[draft.status]}
                      </span>
                    </div>
                    {draft.analysis_model && (
                      <p className="model-provenance">
                        分析模型：{draft.analysis_model} · 项目中的既有记录
                      </p>
                    )}
                    <h2 className="detail-title">{draft.title}</h2>
                    <div className="prose">
                      {draft.body.split("\n").map((p, i) => (
                        <p key={i}>{p}</p>
                      ))}
                    </div>
                    <AnalysisDetails
                      analysis={draft}
                      onSegment={chooseSegment}
                    />
                    <div className="section-label">
                      对应谱例 <span>{draft.segments.length}</span>
                    </div>
                    <div className="segment-list">
                      {draft.segments.map((s, i) => (
                        <div
                          className="segment-entry"
                          key={s.id}
                          data-segment-role={s.role || "excerpt"}
                        >
                          <div className="segment-role">
                            {segmentRoleLabel(s)} ·{" "}
                            {index && printedRange(index, s)}
                          </div>
                          <div
                            className={`segment-chip ${selection?.id === s.id ? "active" : ""}`}
                          >
                            <button onClick={() => chooseSegment(s)}>
                              <Play size={13} />
                              <span>{s.label}</span>
                            </button>
                            <button
                              aria-label={`将片段${i + 1}加入比较`}
                              title="加入跨作品 A/B 比较"
                              onClick={() => queueSegment(s)}
                            >
                              A/B
                            </button>
                          </div>
                          {s.boundary_note && (
                            <p className="boundary-note">
                              边界依据：{s.boundary_note}
                            </p>
                          )}
                          <div className="segment-audition">
                            <button
                              className="text-button"
                              onClick={() => playSegments([s])}
                            >
                              试听{segmentRoleLabel(s)}
                            </button>
                            <button
                              className="text-button"
                              onClick={() => playSegments([s], contextMeasures)}
                            >
                              播放前后文
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                    {draft.segments.length > 1 && (
                      <div className="ab-select">
                        <p>选择两个谱例，进行 A/B 试听</p>
                        {draft.segments.map((s) => (
                          <label className="check-line" key={s.id}>
                            <input
                              type="checkbox"
                              checked={abIds.includes(s.id)}
                              disabled={
                                !abIds.includes(s.id) && abIds.length >= 2
                              }
                              onChange={(e) =>
                                setAbIds(
                                  e.target.checked
                                    ? [...abIds, s.id]
                                    : abIds.filter((id) => id !== s.id),
                                )
                              }
                            />
                            {abIds.includes(s.id)
                              ? `${abIds.indexOf(s.id) === 0 ? "A" : "B"} · `
                              : ""}
                            {s.label}
                          </label>
                        ))}
                        <button
                          className="button secondary full"
                          disabled={abIds.length !== 2}
                          onClick={() =>
                            playSegments(
                              abIds.map((id) =>
                                draft.segments.find((s) => s.id === id)!,
                              ),
                            )
                          }
                        >
                          依次试听 A → B
                        </button>
                      </div>
                    )}
                    {draft.segments.length > 1 && (
                      <button
                        className="button secondary full"
                        onClick={() => playSegments(draft.segments)}
                      >
                        依次试听全部谱例
                      </button>
                    )}
                  </>
                )}
                {!draft && tab === "笔记" && (
                  <p className="muted">尚无分析记录。请在 Codex 中补充。</p>
                )}
                {tab === "资料" && (
                  <>
                    <h2 className="detail-title">分析的来源</h2>
                    <p className="muted micro">
                      已保存的摘录、概括与出处。资料更新由 Codex 记录到项目。
                    </p>
                    {draft?.sources.map((s) => (
                      <SourceView key={s.id} source={s} />
                    ))}
                    {!draft?.sources.length && (
                      <p className="muted">
                        当前笔记尚无引用资料，可在“导听”中查看乐章来源。
                      </p>
                    )}
                  </>
                )}
                <p className="reader-hint">
                  需要补充或修订？在 Codex
                  对话中说明作品与分析标题；选中谱例后可复制位置。
                </p>
              </fieldset>
            </aside>
          </div>
          {comparison.length > 0 && (
            <div className="comparison-tray">
              <div>
                <strong>跨作品 A/B 比较</strong>
                <small>队列保留在此浏览器</small>
              </div>
              {comparison.map((item, i) => (
                <div className="comparison-item" key={item.id}>
                  <b>{i === 0 ? "A" : "B"}</b>
                  <span>
                    {item.work_title}
                    <small>{item.segment.label}</small>
                  </span>
                  <button
                    className="icon-btn"
                    aria-label={`移除比较${i === 0 ? "A" : "B"}`}
                    onClick={() => {
                      halt();
                      setComparison(comparison.filter((q) => q.id !== item.id));
                    }}
                  >
                    <X size={14} />
                  </button>
                </div>
              ))}
              <button
                className="button secondary compact"
                disabled={comparison.length !== 2 || !!busy}
                onClick={() => {
                  halt();
                  setComparison([...comparison].reverse());
                }}
              >
                交换 A/B
              </button>
              <button
                className="button primary compact"
                disabled={!!busy || comparison.length !== 2}
                onClick={playComparison}
              >
                试听 A → B
              </button>
            </div>
          )}
          <div className="player-bar">
            <div className="player-track">
              <span className="record-icon">
                <Disc3 className={playing ? "slow-spin" : ""} />
              </span>
              <div>
                <strong>
                  {comparisonTitle || selection?.label || "选择一个谱例"}
                </strong>
                <small>
                  {playbackWindow && index
                    ? `${printedRange(index, playbackWindow)}${playbackWindow !== selection && !playbackWindow.staffs.length ? " · 全部声部" : ""}`
                    : `${work.title} · 钢琴复奏`}
                </small>
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
                disabled={!selection && !playing}
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
              <label className="context-choice">
                前后各
                <select
                  aria-label="前后文小节数"
                  value={contextMeasures}
                  onChange={(e) => {
                    halt();
                    setContextMeasures(+e.target.value);
                  }}
                >
                  {[2, 4, 8].map((n) => (
                    <option key={n} value={n}>
                      {n} 小节
                    </option>
                  ))}
                </select>
              </label>
              <button
                className="text-button"
                disabled={!selection || !!busy}
                onClick={() =>
                  selection && playSegments([selection], contextMeasures)
                }
              >
                播放前后文
              </button>
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
              <span
                className="local-dot"
                title="停止启动新音符后，保留已发声音符的自然延音；前后文使用全部声部，不改变分析定位。"
              >
                自然收尾
              </span>
            </div>
          </div>
        </>
      )}
      {showComparison && (
        <ComparisonViewer
          current={comparisonView}
          externalError={error}
          activeIds={comparisonActiveIds}
          playing={playing}
          busy={!!busy}
          onStop={halt}
          onClose={() => {
            halt();
            setShowComparison(false);
          }}
          onReplay={playComparison}
        />
      )}
      {selectionExport && (
        <div className="modal-backdrop">
          <section
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-label="选段位置"
          >
            <button
              className="modal-close icon-btn"
              aria-label="关闭选段位置"
              onClick={() => setSelectionExport("")}
            >
              <X />
            </button>
            <h2>交给 Codex 继续分析</h2>
            <p>把下面的选段位置粘贴到项目对话，并说明你想了解或修正什么。</p>
            <textarea
              className="selection-export"
              aria-label="选段 JSON"
              readOnly
              rows={14}
              value={selectionExport}
              onFocus={(e) => e.target.select()}
            />
            <button className="button secondary" onClick={copySelection}>
              <Copy size={16} />
              复制选段
            </button>
          </section>
        </div>
      )}
    </div>
  );
}
