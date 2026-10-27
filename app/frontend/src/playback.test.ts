import { describe, it, expect } from "vitest";
import { schedule, timeAt } from "./playback";
import type { ScoreIndex, Segment, NoteEvent } from "./types";
const event = (
  id: string,
  pitch: number,
  onset: number,
  duration: number,
  extra: Partial<NoteEvent> = {},
): NoteEvent => ({
  id,
  pitch,
  onset,
  duration,
  sounding_duration: duration,
  staff: "1",
  voice: "1",
  measure: 0,
  page: 1,
  playable: true,
  velocity: 0.6,
  ...extra,
});
const idx: ScoreIndex = {
  version: "v1",
  events: [
    event("a", 60, 0, 3),
    event("b", 64, 1, 1),
    event("c", 67, 2, 2, { staff: "2" }),
    event("tie", 60, 2, 1, { playable: false }),
  ],
  measures: [],
  staffs: [],
  timeline: [
    { q: 0, t: 0, tempo: 60 },
    { q: 2, t: 2, tempo: 120 },
  ],
  duration: 4,
  pages: 1,
};
const seg: Segment = {
  id: "s",
  label: "a",
  score_version: "v1",
  start: 0,
  end: 4,
  staffs: ["1"],
  voices: [],
  routes: [],
  note_ids: [],
  start_measure: 0,
  end_measure: 0,
};
describe("shared score clock", () => {
  it("honors tempo changes and never retriggers a tie continuation", () => {
    const data = schedule(idx, seg, 1);
    expect(data.notes.map((n) => n.id)).toEqual(["a", "b"]);
    expect(data.duration).toBe(3);
    expect(data.notes[0].duration).toBe(2.5);
    expect(timeAt(idx, 3)).toBe(2.5);
  });
  it("clips at both boundaries and reattacks a held note inside a selection", () => {
    const data = schedule(idx, { ...seg, start: 1.5, end: 2.5 }, 1);
    expect(data.notes[0].start).toBe(0);
    expect(data.notes[0].duration).toBe(0.75);
    expect(data.notes[1].duration).toBe(0.5);
  });
  it("slow playback scales both note lengths and gaps", () => {
    expect(schedule(idx, seg, 0.5).duration).toBe(6);
    expect(schedule(idx, seg, 0.5).notes[1].start).toBe(2);
  });
  it("routes change instruments without unrelated accompaniment", () => {
    const routed = {
      ...seg,
      routes: [
        { start: 0, end: 2, staff: "1" },
        { start: 2, end: 4, staff: "2" },
      ],
    };
    expect(schedule(idx, routed, 1).notes.map((n) => n.id)).toEqual([
      "a",
      "b",
      "c",
    ]);
    expect(schedule(idx, routed, 1).notes[0].duration).toBe(2);
    expect(
      schedule(idx, { ...seg, staffs: ["2"] }, 1).notes.map((n) => n.id),
    ).toEqual(["c"]);
    expect(schedule(idx, seg, 1, true).notes).toHaveLength(3);
  });
});
