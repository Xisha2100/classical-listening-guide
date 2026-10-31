import type { ComparisonEntry } from "./types";
export const COMPARE_KEY = "listening-room.comparison.v2";
export function readComparison(
  storage: Pick<Storage, "getItem"> = localStorage,
): ComparisonEntry[] {
  try {
    const value = JSON.parse(storage.getItem(COMPARE_KEY) || "[]");
    return Array.isArray(value)
      ? value.filter((x) => x.work_id && x.segment?.score_version).slice(0, 2)
      : [];
  } catch {
    return [];
  }
}
export function addComparison(
  queue: ComparisonEntry[],
  item: ComparisonEntry,
): ComparisonEntry[] {
  if (
    queue.some(
      (q) => q.work_id === item.work_id && q.segment.id === item.segment.id,
    )
  )
    return queue;
  if (queue.length >= 2) throw new Error("A、B 均已有谱例，请先移除其中一项。");
  return [...queue, item];
}

export function legacyDrafts(
  storage: Pick<Storage, "getItem"> = localStorage,
): string | null {
  try {
    const raw = storage.getItem("listening-room.drafts.v2");
    if (!raw) return null;
    try {
      const data = JSON.parse(raw);
      return Object.keys(data.records || {}).length ? raw : null;
    } catch {
      return raw;
    }
  } catch {
    return null;
  }
}
