import type { ScoreIndex, Segment, NoteEvent } from "./types";
export function timeAt(index: ScoreIndex, q: number): number {
  const a = index.timeline;
  let l = 0,
    r = a.length - 1;
  while (l < r) {
    const m = Math.ceil((l + r) / 2);
    if (a[m].q <= q) l = m;
    else r = m - 1;
  }
  return a[l].t + ((q - a[l].q) * 60) / a[l].tempo;
}
export function belongs(e: NoteEvent, s: Segment, all = false) {
  if (all) return true;
  if (s.routes.length)
    return s.routes.some(
      (r) =>
        e.onset >= r.start &&
        e.onset < r.end &&
        e.staff === r.staff &&
        (!r.voice || e.voice === r.voice),
    );
  return (
    (!s.staffs.length || s.staffs.includes(e.staff)) &&
    (!s.voices.length || s.voices.includes(e.voice))
  );
}
export function schedule(
  index: ScoreIndex,
  s: Segment,
  speed: number,
  all = false,
  releaseTail = false,
) {
  const begin = timeAt(index, s.start),
    end = timeAt(index, s.end);
  const notes = index.events
    .filter(
      (e) =>
        e.playable &&
        e.onset < s.end &&
        e.onset + e.sounding_duration > s.start &&
        belongs(e, s, all),
    )
    .map((e) => {
      const route = !all ? s.routes.find((r) =>
        e.onset >= r.start && e.onset < r.end && e.staff === r.staff &&
        (!r.voice || e.voice === r.voice)) : undefined;
      // Interior voice changes still clip. At the final boundary, let an already
      // sounding note finish without starting any notes from the following bar.
      const limit = route && route.end < s.end ? route.end :
        releaseTail ? index.duration : s.end;
      const start = Math.max(e.onset, s.start);
      const stop = Math.min(e.onset + e.sounding_duration, limit);
      return {
        id: e.id, pitch: e.pitch, velocity: e.velocity,
        start: (timeAt(index, start) - begin) / speed,
        duration: Math.max(0.015, (timeAt(index, stop) - timeAt(index, start)) / speed),
      };
    });
  return { duration: Math.max((end - begin) / speed, ...notes.map((n) => n.start + n.duration)), notes };
}
