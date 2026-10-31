import type { Analysis, Guide, Segment, Source, ScoreIndex } from "./types";
import { sectionDepth } from "./listening";

export function SourceView({ source }: { source: Source }) {
  const url = /^https?:\/\//i.test(source.url) ? source.url : "";
  return (
    <div className="source-evidence">
      <strong>{source.title}</strong>
      <p className="muted micro">
        {[
          source.author,
          source.edition,
          source.pages && `第 ${source.pages} 页`,
        ]
          .filter(Boolean)
          .join(" · ")}
      </p>
      {source.kind === "web" && (
        <p className="muted micro">
          {source.extracted ? "已保存正文摘录" : "仅保存摘要／链接"}
          {source.accessed_at && ` · ${source.accessed_at}`}
        </p>
      )}
      {source.excerpt && <blockquote>{source.excerpt}</blockquote>}
      {source.summary && (
        <p className="prose">
          <b>资料概括（非原文）：</b>
          {source.summary}
        </p>
      )}
      {url && (
        <a href={url} target="_blank" rel="noreferrer">
          查看原始来源 ↗
        </a>
      )}
      {source.url && !url && (
        <p className="muted micro">项目资料位置：{source.url}</p>
      )}
    </div>
  );
}
export function AnalysisDetails({
  analysis: a,
  onSegment,
}: {
  analysis: Analysis;
  onSegment: (s: Segment) => void;
}) {
  return (
    <>
      <div className="dimension-tags">
        {a.dimensions.map((d) => (
          <span key={d}>{d}</span>
        ))}
      </div>
      {a.listen_for && (
        <div className="listen-cue">
          <strong>试听时留意</strong>
          <p>{a.listen_for}</p>
        </div>
      )}
      <div className="review-controls">
        <p>
          {a.review_status === "checked" ? "内容已核对" : "内容待核对"} ·{" "}
          {a.listening_status === "checked" ? "已对谱试听" : "待人工对谱试听"}
        </p>
        {a.verification && <p className="muted micro">{a.verification}</p>}
      </div>
      {!!a.claims.length && <div className="section-label">论点与依据</div>}
      {a.claims.map((c, i) => (
        <details className="claim-card" key={c.id || i}>
          <summary>
            {c.statement}
            <span>
              {
                {
                  source: "资料观点",
                  score: "谱面观察",
                  hypothesis: "分析推测",
                }[c.evidence_type]
              }
            </span>
          </summary>
          {c.listening_cue && <p className="listen-cue">{c.listening_cue}</p>}
          {c.source_ids.map((id) => {
            const source = a.sources.find((s) => s.id === id);
            return source ? (
              <SourceView source={source} key={id} />
            ) : (
              <p className="error-text" key={id}>
                引用未找到：{id}
              </p>
            );
          })}
          {c.segment_ids.map((id) => {
            const segment = a.segments.find((s) => s.id === id);
            return segment ? (
              <button
                className="button secondary full"
                key={id}
                onClick={() => onSegment(segment)}
              >
                查看谱例 · {segment.label}
              </button>
            ) : (
              <p className="error-text" key={id}>
                谱例未找到：{id}
              </p>
            );
          })}
          {!c.source_ids.length && !c.segment_ids.length && (
            <p className="muted micro">此论点尚未关联证据。</p>
          )}
        </details>
      ))}
    </>
  );
}
export function GuidePanel({
  guide,
  index,
  onSection,
  noteSources,
}: {
  guide: Guide;
  index: ScoreIndex | null;
  onSection: (id: string) => void;
  noteSources: Source[];
}) {
  const sources = [...guide.sources, ...noteSources];
  return (
    <>
      <div className="eyebrow">THE WHOLE, AND ITS PARTS</div>
      <h2 className="detail-title">从全貌到细节</h2>
      <div className="prose">
        {guide.overview ? (
          guide.overview.split("\n").map((p, i) => <p key={i}>{p}</p>)
        ) : (
          <p>乐章概览待补充，可先阅读已有分析。</p>
        )}
      </div>
      <div className="guide-section-list">
        {guide.sections.map((s, i) => (
          <div
            className="guide-section"
            key={s.id}
            style={{ marginLeft: sectionDepth(guide.sections, s.id) * 12 }}
          >
            <button className="text-button" onClick={() => onSection(s.id)}>
              <span>{String(i + 1).padStart(2, "0")} · </span>
              <strong>{s.title}</strong>
            </button>
            <small>
              {index
                ? `第 ${index.measures[s.start_measure]?.label}—${index.measures[s.end_measure]?.label} 小节`
                : "待定位"}
            </small>
            <p>{s.description}</p>
            {!!s.source_ids.length && (
              <details className="section-evidence">
                <summary>本段依据 · {s.source_ids.length}</summary>
                {s.source_ids.map((id) => {
                  const source = sources.find((item) => item.id === id);
                  return source ? (
                    <SourceView key={id} source={source} />
                  ) : (
                    <p key={id} className="error-text">
                      引用未找到：{id}
                    </p>
                  );
                })}
              </details>
            )}
          </div>
        ))}
      </div>
      {!!guide.sources.length && (
        <>
          <div className="section-label">导听来源</div>
          {guide.sources.map((s) => (
            <SourceView key={s.id} source={s} />
          ))}
        </>
      )}
    </>
  );
}
