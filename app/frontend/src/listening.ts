import type { GuideSection, ScoreIndex, Segment } from "./types";

export const segmentRoles = {
  theme: "完整主题陈述",
  phrase: "完整乐句／段落",
  evidence: "局部证据",
  excerpt: "自选片段",
};

export function segmentRoleLabel(segment: Segment): string {
  if (segment.boundary_status === "candidate" && segment.role === "theme") return "候选主题范围";
  if (segment.boundary_status === "candidate" && segment.role === "phrase") return "候选乐句范围";
  return segmentRoles[segment.role || "excerpt"];
}

export function sectionWithin(sections: GuideSection[], child: string, parent: string): boolean {
  if (!parent) return true;
  const seen = new Set<string>();
  let id = child;
  while (id && !seen.has(id)) {
    if (id === parent) return true;
    seen.add(id);
    id = sections.find((s) => s.id === id)?.parent_id || "";
  }
  return false;
}

export function sectionDepth(sections: GuideSection[], id: string): number {
  const seen = new Set<string>();
  let depth = 0, current = sections.find((s) => s.id === id);
  while (current?.parent_id && !seen.has(current.id)) {
    seen.add(current.id);
    current = sections.find((s) => s.id === current?.parent_id);
    if (current) depth++;
  }
  return depth;
}

export function printedRange(index: ScoreIndex, segment: Segment): string {
  const a = index.measures[segment.start_measure], b = index.measures[segment.end_measure];
  if (!a || !b) return "";
  const startBeat = segment.start - a.start, endBeat = segment.end - b.start;
  const partial = startBeat > 0.00001 || segment.end < b.end - 0.00001;
  return `谱面小节 ${a.label}—${b.label}${partial ? `（起止拍位 ${Number(startBeat.toFixed(3))}—${Number(endBeat.toFixed(3))}，四分音符为单位）` : ""}`;
}

// A listening window is ephemeral. Never replace the analysis anchor or voice route.
// Context uses the complete ensemble because the theme's route is unknown outside its anchor.
export function withContext(index: ScoreIndex, segment: Segment, measures: number): Segment {
  if (!Number.isInteger(measures) || measures < 0 || measures > 8) throw Error("前后文范围必须为 0—8 小节");
  if (segment.score_version !== index.version) throw Error("谱例属于旧谱本，请重新定位后播放。");
  if (!measures) return segment;
  // Split bars share one printed label. Count them as one contextual measure.
  let first = segment.start_measure, last = segment.end_measure;
  const leftEdge = (i: number) => {
    while (i > 0 && index.measures[i - 1].label === index.measures[i].label) i--;
    return i;
  };
  const rightEdge = (i: number) => {
    while (i < index.measures.length - 1 && index.measures[i + 1].label === index.measures[i].label) i++;
    return i;
  };
  if (!index.measures[first] || !index.measures[last]) throw Error("谱例范围不存在");
  first = leftEdge(first); last = rightEdge(last);
  for (let i = 0; i < measures; i++) {
    first = leftEdge(Math.max(0, first - 1));
    last = rightEdge(Math.min(index.measures.length - 1, last + 1));
  }
  const start = index.measures[first]?.start, end = index.measures[last]?.end;
  if (start === undefined || end === undefined) throw Error("谱例范围不存在");
  return {
    ...segment,
    label: `${segment.label} · 前后文`,
    start, end, start_measure: first, end_measure: last,
    staffs: [], voices: [], routes: [],
    note_ids: index.events.filter((e) => e.onset < end && e.onset + e.sounding_duration > start).map((e) => e.id),
  };
}
