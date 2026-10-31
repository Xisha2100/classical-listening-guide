import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ScoreIndex, Segment } from "./types";
const mocked = vi.hoisted(() => ({
  scheduled: [] as { fn: (t: number) => void; at: number }[],
  attacks: [] as number[][],
}));
vi.mock("tone", () => ({
  start: async () => {},
  Sampler: class {
    volume = { value: 0 };
    constructor(options: { onload: () => void }) {
      queueMicrotask(options.onload);
    }
    toDestination() {
      return this;
    }
    releaseAll() {}
    triggerAttackRelease(pitch: number, duration: number, time: number) {
      mocked.attacks.push([pitch, duration, time]);
    }
  },
  Frequency: (pitch: number) => ({ toFrequency: () => pitch }),
  getDraw: () => ({ schedule: (fn: () => void) => fn() }),
  getTransport: () => ({
    stop: () => {},
    cancel: () => {
      mocked.scheduled = [];
    },
    start: () => {},
    schedule: (fn: (t: number) => void, at: number) => {
      mocked.scheduled.push({ fn, at });
    },
  }),
}));
import { playItems, stop } from "./player";
const segment: Segment = {
  id: "shared-id",
  label: "谱例",
  score_version: "v1",
  start: 0,
  end: 2,
  staffs: ["1"],
  voices: [],
  routes: [],
  note_ids: ["same-note-id"],
  start_measure: 0,
  end_measure: 0,
};
const index = (pitch: number, tempo: number): ScoreIndex => ({
  version: "v1",
  events: [
    {
      id: "same-note-id",
      pitch,
      onset: 0,
      duration: 2,
      sounding_duration: 2,
      staff: "1",
      voice: "1",
      measure: 0,
      page: 1,
      playable: true,
      velocity: 0.5,
    },
  ],
  measures: [],
  staffs: [],
  timeline: [{ q: 0, t: 0, tempo }],
  duration: 2,
  pages: 1,
});
describe("cross-score audio and highlighting", () => {
  beforeEach(() => {
    vi.stubGlobal("window", { clearTimeout });
    mocked.scheduled = [];
    mocked.attacks = [];
  });
  it("uses each score tempo and pitch, and reports its own work identity despite equal note IDs", async () => {
    const switched: string[] = [],
      notes: string[] = [];
    await playItems(
      [
        { index: index(60, 60), segment, work_id: "bach" },
        { index: index(72, 120), segment, work_id: "mozart" },
      ],
      1,
      false,
      false,
      (_ids, wid) => {
        if (wid) notes.push(wid);
      },
      () => {},
      (_s, _i, wid) => switched.push(wid),
    );
    for (const item of [...mocked.scheduled].sort((a, b) => a.at - b.at))
      item.fn(item.at);
    expect(mocked.attacks.map((a) => a.slice(0, 2))).toEqual([
      [60, 2],
      [72, 1],
    ]);
    expect(mocked.attacks[1][2]).toBeCloseTo(2.45);
    expect(switched).toEqual(["bach", "mozart"]);
    expect(new Set(notes)).toEqual(new Set(["bach", "mozart"]));
    stop();
  });
});
