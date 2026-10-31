import { describe, it, expect } from "vitest";
import { withContext, sectionWithin, sectionDepth, printedRange } from "./listening";
import type { GuideSection, ScoreIndex, Segment } from "./types";
const score: ScoreIndex = {
  version: "v1", pages: 1, duration: 12, events: [], staffs: [],
  timeline: [{ q: 0, t: 0, tempo: 60 }],
  measures: [0, 1, 2, 3].map((i) => ({ index: i, id: `m${i}`, label: ["0", "1", "1", "2"][i], start: i * 3, end: i * 3 + 3, page: 1 })),
};
const segment: Segment = { id: "s", label: "完整乐句", score_version: "v1", start: 3.5, end: 8, start_measure: 1, end_measure: 2, staffs: ["1"], voices: ["2"], routes: [{ start: 3.5, end: 8, staff: "1", voice: "2" }], note_ids: ["theme"], role: "phrase", boundary_note: "弱起至终止", source_ids: ["score"] };
const sections: GuideSection[] = [
  { id: "exposition", title: "呈示", start_measure: 0, end_measure: 3, description: "", source_ids: [] },
  { id: "secondary", parent_id: "exposition", title: "副部", start_measure: 1, end_measure: 3, description: "", source_ids: [] },
  { id: "phrase", parent_id: "secondary", title: "乐句", start_measure: 1, end_measure: 2, description: "", source_ids: [] },
];
describe("context is a separate audition window", () => {
  it("clamps at score ends, includes all voices, and leaves the anchor and route intact", () => {
    const before = structuredClone(segment), window = withContext(score, segment, 2);
    expect(window.start).toBe(0); expect(window.end).toBe(12);
    expect(window.staffs).toEqual([]); expect(window.routes).toEqual([]);
    expect(window.id).toBe(segment.id);
    expect(segment).toEqual(before);
    expect(withContext(score, segment, 0)).toBe(segment);
  });
  it("preserves printed labels and beat offsets despite split measure numbering", () => {
    expect(printedRange(score, segment)).toContain("1—1");
    expect(printedRange(score, segment)).toContain("0.5—2");
    expect(() => withContext({ ...score, version: "v2" }, segment, 2)).toThrow("旧谱本");
    const split = withContext(score, { ...segment, start: 9, end: 12, start_measure: 3, end_measure: 3 }, 1);
    expect(split.start_measure).toBe(1); // Includes both elements of preceding printed bar 1.
  });
  it("includes descendants in a form filter, but not siblings or unrelated notes", () => {
    expect(sectionWithin(sections, "phrase", "exposition")).toBe(true);
    expect(sectionWithin(sections, "exposition", "phrase")).toBe(false);
    expect(sectionWithin(sections, "unknown", "exposition")).toBe(false);
    expect(sectionDepth(sections, "phrase")).toBe(2);
    expect(sectionWithin(sections, "unknown", "")).toBe(true);
  });
});
