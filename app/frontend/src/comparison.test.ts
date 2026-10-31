import { describe, expect, it } from "vitest";
import { addComparison, legacyDrafts } from "./comparison";
import type { ComparisonEntry } from "./types";
describe("cross-work comparison identity", () => {
  const item = (wid: string, version: string): ComparisonEntry => ({
    id: wid,
    work_id: wid,
    work_title: wid,
    segment: {
      id: "same-segment-id",
      label: "例",
      score_version: version,
      start: 0,
      end: 4,
      staffs: ["1"],
      voices: [],
      routes: [],
      note_ids: ["same-note-id"],
      start_measure: 0,
      end_measure: 0,
    },
  });
  it("keeps identically named anchors from separate scores separate", () => {
    const queue = addComparison(
      addComparison([], item("bach", "bach-v1")),
      item("mozart", "mozart-v1"),
    );
    expect(queue.map((q) => [q.work_id, q.segment.score_version])).toEqual([
      ["bach", "bach-v1"],
      ["mozart", "mozart-v1"],
    ]);
    expect(addComparison(queue, item("bach", "bach-v1"))).toHaveLength(2);
    expect(() =>
      addComparison(queue, item("beethoven", "beethoven-v1")),
    ).toThrow("A、B");
  });
});

it("offers unchanged legacy drafts for export, even malformed JSON", () => {
  const raw = '{"records":{"one":{"draft":{"body":"原文"}}}}';
  expect(legacyDrafts({ getItem: () => raw })).toBe(raw);
  expect(legacyDrafts({ getItem: () => "{broken" })).toBe("{broken");
  expect(legacyDrafts({ getItem: () => '{"records":{}}' })).toBeNull();
});
