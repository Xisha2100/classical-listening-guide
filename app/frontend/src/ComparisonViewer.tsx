import { useEffect, useRef, useState } from "react";
import { ChevronLeft, ChevronRight, X } from "lucide-react";
import type { ComparisonEntry, ScoreIndex } from "./types";
export interface PlayingComparison {
  entry: ComparisonEntry;
  index: ScoreIndex;
}
export default function ComparisonViewer({
  current,
  externalError,
  activeIds,
  playing,
  busy,
  onStop,
  onClose,
  onReplay,
}: {
  current: PlayingComparison | null;
  externalError: string;
  activeIds: string[];
  playing: boolean;
  busy: boolean;
  onStop: () => void;
  onClose: () => void;
  onReplay: () => void;
}) {
  const [page, setPage] = useState(1),
    [svg, setSvg] = useState(""),
    [error, setError] = useState("");
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    setPage(
      current?.index.measures[current.entry.segment.start_measure]?.page || 1,
    );
  }, [current]);
  useEffect(() => {
    if (!current) return;
    const note = current.index.events.find((e) => e.id === activeIds[0]);
    if (note) setPage(note.page);
  }, [activeIds, current]);
  useEffect(() => {
    setSvg("");
    setError("");
    if (!current) return;
    const controller = new AbortController();
    fetch(
      `/api/works/${encodeURIComponent(current.entry.work_id)}/pages/${page}`,
      { signal: controller.signal },
    )
      .then((r) => {
        if (!r.ok) throw Error("比较谱页加载失败");
        return r.text();
      })
      .then(setSvg)
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      });
    return () => controller.abort();
  }, [current?.entry.work_id, page]);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.querySelectorAll(".selected-note,.sounding-note").forEach((n) =>
      n.classList.remove("selected-note", "sounding-note"),
    );
    current?.entry.segment.note_ids.forEach((id) =>
      el
        .querySelector(`[id="${CSS.escape(id)}"]`)
        ?.classList.add("selected-note"),
    );
    activeIds.forEach((id) =>
      el
        .querySelector(`[id="${CSS.escape(id)}"]`)
        ?.classList.add("sounding-note"),
    );
  }, [svg, activeIds, current]);
  return (
    <div className="modal-backdrop comparison-backdrop">
      <section
        className="modal comparison-modal"
        role="dialog"
        aria-modal="true"
        aria-label="比较谱面"
      >
        <button
          className="modal-close icon-btn"
          aria-label="关闭比较谱面"
          onClick={onClose}
        >
          <X />
        </button>
        <div className="eyebrow">LISTEN SIDE BY SIDE</div>
        <h2>比较谱面</h2>
        <p className="comparison-heading">
          {current
            ? `${current.entry.work_title} · ${current.entry.segment.label}`
            : "正在准备 A/B 谱例…"}
        </p>
        <p className="muted micro">
          播放自动切换到对应作品的谱面。关闭后回到原来的分析。
        </p>
        <div className="comparison-controls">
          <button
            className="button primary"
            disabled={!playing && !busy}
            onClick={onStop}
          >
            停止比较
          </button>
          <button
            className="button secondary"
            disabled={busy}
            onClick={onReplay}
          >
            重新试听 A → B
          </button>
          <div>
            <button
              className="icon-btn"
              aria-label="比较上一谱页"
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
            >
              <ChevronLeft size={17} />
            </button>
            <span>
              {page} / {current?.index.pages || "—"}
            </span>
            <button
              className="icon-btn"
              aria-label="比较下一谱页"
              disabled={page >= (current?.index.pages || 1)}
              onClick={() => setPage(page + 1)}
            >
              <ChevronRight size={17} />
            </button>
          </div>
        </div>
        {(error || externalError) && (
          <p role="alert" className="error-text">
            {error || externalError}
          </p>
        )}
        <div className="comparison-paper-scroll">
          {svg ? (
            <div
              className="score-paper comparison-paper"
              ref={ref}
              data-comparison-work-id={current?.entry.work_id}
              dangerouslySetInnerHTML={{ __html: svg }}
            />
          ) : (
            <p className="loading-score">正在展开比较谱面…</p>
          )}
        </div>
      </section>
    </div>
  );
}
