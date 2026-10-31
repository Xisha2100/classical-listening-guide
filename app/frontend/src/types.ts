export interface Work {
  id: string;
  title: string;
  composer: string;
  catalogue: string;
  movement: string;
  era: string;
  color: string;
  description: string;
  score_version: string;
  edition: string;
  source_url: string;
  aliases: string[];
  collection_id?: string;
  arranger?: string;
  movement_order?: number;
  availability?: "ready" | "pending";
  coverage?: string;
  score_type?: string;
}
export interface NoteEvent {
  id: string;
  pitch: number;
  onset: number;
  duration: number;
  sounding_duration: number;
  staff: string;
  voice: string;
  measure: number;
  page: number;
  playable: boolean;
  velocity: number;
}
export interface ScoreIndex {
  version: string;
  events: NoteEvent[];
  measures: {
    index: number;
    label: string;
    id: string;
    start: number;
    end: number;
    page: number;
  }[];
  staffs: { id: string; label: string; voices: string[] }[];
  timeline: { q: number; t: number; tempo: number }[];
  duration: number;
  pages: number;
}
export interface Segment {
  id: string;
  label: string;
  score_version: string;
  start: number;
  end: number;
  staffs: string[];
  voices: string[];
  routes: {
    start: number;
    end: number;
    staff: string;
    voice?: string | null;
  }[];
  note_ids: string[];
  start_measure: number;
  end_measure: number;
  role?: "excerpt" | "theme" | "phrase" | "evidence";
  boundary_note?: string;
  boundary_status?: "candidate" | "supported";
  source_ids?: string[];
}
export interface Source {
  id: string;
  kind: "book" | "web" | "score" | "personal";
  title: string;
  author: string;
  edition: string;
  pages: string;
  url: string;
  accessed_at: string;
  excerpt: string;
  extracted: boolean;
  summary: string;
}
export interface Analysis {
  id: string;
  work_id: string;
  title: string;
  body: string;
  kind: string;
  origin: "manual" | "model" | "seed";
  status: "unlocated" | "suggested" | "confirmed" | "not_applicable";
  dimensions: string[];
  scope: "overview" | "movement" | "section" | "segment";
  section_id: string;
  listen_for: string;
  claims: Claim[];
  review_status: "unreviewed" | "checked";
  listening_status: "pending" | "checked";
  sources: Source[];
  segments: Segment[];
  verification: string;
  analysis_model?: string;
  analysis_run_id?: string;
  created_at?: string;
  updated_at?: string;
}
export async function api<T>(
  path: string,
  body?: unknown,
  method?: string,
): Promise<T> {
  const r = await fetch("/api" + path, {
    method: method || (body === undefined ? "GET" : "POST"),
    headers:
      body instanceof FormData ? {} : { "Content-Type": "application/json" },
    body:
      body === undefined
        ? undefined
        : body instanceof FormData
          ? body
          : JSON.stringify(body),
  });
  if (!r.ok) {
    let d;
    try {
      d = await r.json();
    } catch {
      throw new Error("本地服务不可用，请检查是否已启动。");
    }
    throw new Error(
      typeof d.detail === "string" ? d.detail : "输入格式无效，请检查必填项。",
    );
  }
  return r.json();
}
export const blankAnalysis = (wid: string): Analysis => ({
  id: "",
  work_id: wid,
  title: "",
  body: "",
  kind: "主题",
  origin: "manual",
  status: "unlocated",
  sources: [],
  segments: [],
  verification: "",
  dimensions: ["主题"],
  scope: "segment",
  section_id: "",
  listen_for: "",
  claims: [],
  review_status: "unreviewed",
  listening_status: "pending",
});
export const dimensions = [
  "动机",
  "主题",
  "变奏",
  "曲式",
  "和声",
  "调性／调式",
  "节奏／节拍",
  "织体／复调",
  "配器",
  "力度／奏法",
];
export interface Claim {
  id: string;
  statement: string;
  evidence_type: "source" | "score" | "hypothesis";
  source_ids: string[];
  segment_ids: string[];
  listening_cue: string;
}
export interface GuideSection {
  id: string;
  parent_id?: string;
  title: string;
  start_measure: number;
  end_measure: number;
  description: string;
  source_ids: string[];
}
export interface Guide {
  work_id: string;
  overview: string;
  sections: GuideSection[];
  source_ids: string[];
  sources: Source[];
}
export interface Collection {
  id: string;
  title: string;
  composer: string;
  catalogue: string;
  arranger: string;
  description: string;
  work_ids: string[];
  availability: string;
  missing: string[];
  overview: string;
}
export interface ComparisonEntry {
  id: string;
  work_id: string;
  work_title: string;
  segment: Segment;
}
export function normalizeAnalysis(a: Analysis): Analysis {
  return {
    ...blankAnalysis(a.work_id),
    ...a,
    dimensions: a.dimensions?.length ? a.dimensions : [a.kind],
    sources: a.sources.map((s) => ({ ...s, summary: s.summary || "" })),
    claims: a.claims || [],
  };
}
