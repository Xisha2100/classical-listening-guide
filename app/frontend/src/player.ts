import * as Tone from "tone";
import type { ScoreIndex, Segment } from "./types";
import { schedule } from "./playback";
let sampler: Tone.Sampler | undefined,
  loading: Promise<void> | undefined,
  generation = 0,
  timeout: number | undefined;
let activeTimers: number[] = [];
export function stop() {
  generation++;
  Tone.getTransport().stop();
  Tone.getTransport().cancel();
  sampler?.releaseAll();
  window.clearTimeout(timeout);
  activeTimers.forEach(clearTimeout);
  activeTimers = [];
}
async function ready() {
  await Tone.start();
  if (!sampler) {
    const urls: Record<string, string> = { A0: "A0.mp3", C8: "C8.mp3" };
    for (let o = 1; o <= 7; o++) {
      urls["C" + o] = "C" + o + ".mp3";
      urls["D#" + o] = "Ds" + o + ".mp3";
      urls["F#" + o] = "Fs" + o + ".mp3";
      urls["A" + o] = "A" + o + ".mp3";
    }
    loading = new Promise<void>((resolve, reject) => {
      sampler = new Tone.Sampler({
        urls,
        baseUrl: "/assets/piano/",
        release: 0.12,
        onload: resolve,
        onerror: () =>
          reject(new Error("钢琴采样加载失败，请检查本地 assets/piano。")),
      }).toDestination();
      sampler.volume.value = -10;
    });
  }
  await loading;
}
export async function play(
  index: ScoreIndex,
  segments: Segment[],
  speed: number,
  all: boolean,
  loop: boolean,
  onNotes: (ids: string[]) => void,
  onEnd: () => void,
  onSegment: (s: Segment) => void,
) {
  stop();
  const token = generation;
  await ready();
  if (token !== generation) return;
  const transport = Tone.getTransport();
  let offset = 0.1;
  for (const s of segments) {
    const data = schedule(index, s, speed, all),
      base = offset;
    transport.schedule(
      (t) =>
        Tone.getDraw().schedule(() => {
          if (token === generation) onSegment(s);
        }, t),
      base,
    );
    for (const n of data.notes) {
      transport.schedule((t) => {
        sampler!.triggerAttackRelease(
          Tone.Frequency(n.pitch, "midi").toFrequency(),
          n.duration,
          t,
          Math.max(0.15, n.velocity),
        );
      }, base + n.start);
    }
    // Sample SVG highlights from the exact scheduled events, never a separate score clock.
    const marks = [
      ...new Set(data.notes.flatMap((n) => [n.start, n.start + n.duration])),
    ].sort((a, b) => a - b);
    for (const at of marks) {
      const ids = data.notes
        .filter(
          (n) => n.start <= at + 0.00001 && n.start + n.duration > at + 0.00001,
        )
        .map((n) => n.id);
      transport.schedule(
        (t) =>
          Tone.getDraw().schedule(() => {
            if (token === generation) onNotes(ids);
          }, t),
        base + at,
      );
    }
    offset += data.duration + 0.35;
  }
  transport.loop = loop;
  transport.loopStart = 0;
  transport.loopEnd = offset;
  if (!loop)
    transport.schedule(
      (t) =>
        Tone.getDraw().schedule(() => {
          if (token === generation) {
            stop();
            onNotes([]);
            onEnd();
          }
        }, t),
      offset,
    );
  transport.start("+0.05");
}
