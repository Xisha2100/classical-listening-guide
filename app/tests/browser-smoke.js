async (page) => {
  const base = new URL(page.url()).origin;
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.addInitScript(() => {
    if (window.__audioStats) return;
    window.__audioStats = { samples: 0, energy: 0, analysers: [] };
    const start = AudioBufferSourceNode.prototype.start;
    AudioBufferSourceNode.prototype.start = function (...args) {
      if (this.buffer && this.buffer.duration > 0.1) {
        window.__audioStats.samples++;
        const data = this.buffer.getChannelData(0);
        for (let i = 0; i < data.length; i += 100)
          window.__audioStats.energy += Math.abs(data[i]);
      }
      return start.apply(this, args);
    };
    const connect = AudioNode.prototype.connect;
    AudioNode.prototype.connect = function (...args) {
      if (args[0] instanceof AudioDestinationNode) {
        const analyser = this.context.createAnalyser();
        connect.call(this, analyser);
        window.__audioStats.analysers.push(analyser);
      }
      return connect.apply(this, args);
    };
  });
  await page.goto(base);
  const works = await (await page.request.get(`${base}/api/works`)).json();
  const work = works.find((w) => w.id === "beethoven-op67-1");
  if (!work) throw Error("Beethoven baseline missing");
  const existing = await (
    await page.request.get(`${base}/api/works/${work.id}/analyses`)
  ).json();
  const playable = existing.find(
    (n) =>
      n.segments.length && n.segments[0].score_version === work.score_version,
  );
  if (!playable) throw Error("representative score example missing");
  {
    await page.getByRole("heading", { name: /我的曲库/ }).waitFor();
    await page.getByRole("textbox", { name: "搜索曲名" }).fill("贝五");
    await page.locator(`[data-work-id="${work.id}"]`).waitFor();
    await page.locator(`[data-work-id="${work.id}"]`).click();
    await page.locator(`[data-analysis-id="${playable.id}"]`).click();
    await page.locator(".selected-note").first().waitFor();
    await page.getByRole("button", { name: "播放片段", exact: true }).click();
    await page.waitForFunction(
      () => window.__audioStats.samples > 0 && window.__audioStats.energy > 0,
      null, {timeout:15000},
    );
    const audioPeak = await page.evaluate(async () => {
      let peak = 0;
      for (let i = 0; i < 30; i++) {
        for (const a of window.__audioStats.analysers) {
          const data = new Float32Array(a.fftSize);
          a.getFloatTimeDomainData(data);
          for (const v of data) peak = Math.max(peak, Math.abs(v));
        }
        await new Promise((r) => setTimeout(r, 50));
      }
      return peak;
    });
    if (audioPeak <= 0) throw Error("silent audio output");
    if (
      await page.getByRole("button", { name: "停止播放", exact: true }).count()
    )
      await page.getByRole("button", { name: "停止播放", exact: true }).click();
    for (const name of ['写分析','AI 分析','设置','在线找谱','导入乐谱','保存笔记','确认定位并保存']) {
      if (await page.getByRole('button',{name,exact:true}).count()) throw Error('authoring control remains: '+name);
    }
    await page.getByRole('button',{name:'资料',exact:true}).click();
    if (playable.sources.length) await page.locator('.source-evidence').first().waitFor();
    await page.getByRole('button',{name:'笔记',exact:true}).click();
    await page.getByRole('button',{name:'复制选段给 Codex',exact:true}).click();
    const exported=JSON.parse(await page.getByRole('textbox',{name:'选段 JSON'}).inputValue());
    if(exported.work_id!==work.id || exported.segment.score_version!==work.score_version || !exported.segment.note_ids.length) throw Error('selection identity lost');
    await page.getByRole('button',{name:'关闭选段位置',exact:true}).click();
    await page.getByRole('button',{name:'刷新项目',exact:true}).click();
    await page.getByText('已读取本地最新分析、目录和谱本。',{exact:true}).waitFor();
    await page.getByRole('heading',{name:playable.title,exact:true,level:2}).waitFor();
    await page.screenshot({path:'output/playwright/reader-desktop.png'});
    await page.getByRole("button", { name: "返回曲库", exact: true }).click();
    await page.setViewportSize({ width: 390, height: 844 });
    await page.getByRole("textbox", { name: "搜索曲名" }).fill("BWV847");
    await page.locator(".work-card").first().click();
    await page.locator(".score-paper svg").first().waitFor();
    if (
      await page.evaluate(
        () => document.documentElement.scrollWidth > window.innerWidth + 1,
      )
    )
      throw Error("mobile horizontal overflow");
    await page.screenshot({
      path: "output/playwright/mobile.png",
      fullPage: true,
    });
    await page.setViewportSize({ width: 1440, height: 1000 });
    if (errors.length) throw Error(JSON.stringify(errors));
    return {
      result: "passed",
      audioPeak,
      errors,
      flows: [
        "alias-search",
        "real-audio",
        "local-sources",
        "selection-export",
        "refresh-project",
        "read-only-controls",
        "mobile",
      ],
    };
  }
}
