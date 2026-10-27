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
}
export interface Analysis {
  id: string;
  work_id: string;
  title: string;
  body: string;
  kind: string;
  origin: "manual" | "model" | "seed";
  status: "unlocated" | "suggested" | "confirmed";
  sources: Source[];
  segments: Segment[];
  verification: string;
  created_at?: string;
  updated_at?: string;
}
export interface Job {
  id: string;
  kind: string;
  status: string;
  error?: string;
  result?: any;
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
});
export const blankSource = (): Source => ({
  id: crypto.randomUUID(),
  kind: "book",
  title: "",
  author: "",
  edition: "",
  pages: "",
  url: "",
  accessed_at: "",
  excerpt: "",
  extracted: false,
});
