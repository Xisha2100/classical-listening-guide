async (page) => {
  const base = new URL(page.url()).origin;
  await page.goto(base);
  const works = await (await page.request.get(`${base}/api/works`)).json();
  const tested = [];
  const external = [];
  let expected = 0;
  let pending = 0;
  await page.route("**/*", (route) => {
    const url = new URL(route.request().url());
    if (url.hostname !== "127.0.0.1" && url.hostname !== "localhost") {
      external.push(url.href);
      return route.abort();
    }
    return route.continue();
  });
  try {
    for (const work of works) {
      if (
        await page
          .getByRole("button", { name: "返回曲库", exact: true })
          .count()
      )
        await page
          .getByRole("button", { name: "返回曲库", exact: true })
          .click();
      await page
        .getByRole("textbox", { name: "搜索曲名" })
        .fill(work.catalogue);
      await page.locator(`[data-work-id="${work.id}"]`).click();
      if (work.availability === "pending") {
        await page
          .getByRole("heading", { name: "完整数字谱尚未入库", exact: true })
          .waitFor();
        if (await page.locator(".score-paper svg").count())
          throw Error("pending work masquerades as playable score");
        pending++;
        continue;
      }
      const notes = await (
        await page.request.get(`${base}/api/works/${work.id}/analyses`)
      ).json();
      const seed = notes.filter(
        (n) =>
          (n.origin === "seed" || (n.analysis_model === "gpt-6-sol" && n.id.startsWith("sol-"))) &&
          n.segments?.length &&
          n.segments.every((s) => s.score_version === work.score_version),
      );
      expected += seed.length;
      for (const note of seed) {
        await page.locator(`[data-analysis-id="${note.id}"]`).click();
        const seg = note.segments[note.segments.length - 1];
        await page
          .locator(".segment-chip")
          .getByRole("button", { name: seg.label, exact: true })
          .click();
        await page.locator(".selected-note").first().waitFor();
        const ids = await page
          .locator(".selected-note")
          .evaluateAll((nodes) => nodes.map((n) => n.id));
        if (!ids.every((id) => seg.note_ids.includes(id)))
          throw Error("wrong highlighted IDs " + note.title);
        await page
          .getByRole("button", { name: "播放片段", exact: true })
          .click();
        await page
          .locator(".sounding-note")
          .first()
          .waitFor({ timeout: 12000 });
        await page
          .getByRole("button", { name: "停止播放", exact: true })
          .click();
        await page
          .locator(".sounding-note")
          .first()
          .waitFor({ state: "hidden" });
        tested.push({
          work_id: work.id,
          title: note.title,
          segment: seg.label,
          highlightCount: ids.length,
        });
      }
    }
    if (tested.length !== expected || expected < 15 || external.length)
      throw Error(JSON.stringify({ count: tested.length, expected, external }));
    // Reopen a known playable card after visiting pending entries.
    const baseline = tested[0];
    if (
      await page.getByRole("button", { name: "返回曲库", exact: true }).count()
    )
      await page.getByRole("button", { name: "返回曲库", exact: true }).click();
    const w = works.find((w) => w.id === baseline.work_id);
    await page.getByRole("textbox", { name: "搜索曲名" }).fill(w.catalogue);
    await page.locator(`[data-work-id="${w.id}"]`).click();
    await page
      .locator(".analysis-item")
      .filter({ hasText: baseline.title })
      .click();
    await page.getByRole("button", { name: "循环播放", exact: true }).click();
    await page.getByRole("button", { name: "播放片段", exact: true }).click();
    await page.locator(".sounding-note").first().waitFor();
    await page.getByRole("combobox", { name: "播放速度" }).selectOption("0.5");
    await page.getByRole("button", { name: "播放片段", exact: true }).waitFor();
    await page.getByRole("button", { name: "循环播放", exact: true }).click();
    return {
      result: "passed",
      tested,
      pending,
      expected,
      externalRequests: external.length,
    };
  } finally {
    await page.unroute("**/*");
  }
}
