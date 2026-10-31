async (page) => {
  const base = new URL(page.url()).origin;
  const errors = [], external = [], checks = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.route('**/*', (route) => {
    const url = new URL(route.request().url());
    if (!['127.0.0.1','localhost'].includes(url.hostname)) { external.push(url.href); return route.abort(); }
    return route.continue();
  });
  try {
    await page.goto(base);
    await page.setViewportSize({width:1440,height:1000});
    const wid = 'tchaikovsky-op23-1';
    const notes = await (await page.request.get(`${base}/api/works/${wid}/analyses`)).json();
    const card = notes.find((n) => n.id === 'sol-1-opening-song');
    if (!card || card.analysis_model !== 'gpt-6-sol') throw Error('GPT-6 Sol analysis missing');
    const theme = card.segments.find((s) => s.role === 'theme');
    if (!(theme.end_measure > theme.start_measure + 3 && theme.boundary_note)) throw Error('theme still only an incipit');
    const guide = await (await page.request.get(`${base}/api/works/${wid}/guide`)).json();
    if (!guide.sections.some((s) => s.parent_id)) throw Error('no form hierarchy');
    await page.getByRole('textbox',{name:'搜索曲名'}).fill('柴一');
    await page.locator(`[data-work-id="${wid}"]`).click();
    await page.locator(`[data-analysis-id="${card.id}"]`).click();
    await page.locator('.selected-note').first().waitFor();
    await page.getByText(/分析模型：gpt-6-sol/).waitFor();
    const themeEntry=page.locator('.segment-entry[data-segment-role="theme"]').first();
    await themeEntry.getByText(/完整主题陈述/).first().waitFor();
    const scopeBefore = await page.getByRole('spinbutton',{name:'起始小节序号'}).inputValue();
    const endBefore = await page.getByRole('spinbutton',{name:'结束小节序号'}).inputValue();
    const beforeJson = JSON.stringify(card.segments);
    await themeEntry.getByRole('button',{name:'试听完整主题陈述',exact:true}).click();
    await page.locator('.sounding-note').first().waitFor({timeout:12000});
    await page.getByRole('button',{name:'停止播放',exact:true}).click();
    await page.getByRole('combobox',{name:'前后文小节数'}).selectOption('2');
    await themeEntry.getByRole('button',{name:'播放前后文',exact:true}).click();
    await page.locator('.player-track').getByText(/谱面小节 5—18/).waitFor();
    await page.locator('.sounding-note').first().waitFor({timeout:12000});
    if (await page.getByRole('spinbutton',{name:'起始小节序号'}).inputValue() !== scopeBefore || await page.getByRole('spinbutton',{name:'结束小节序号'}).inputValue() !== endBefore) throw Error('context overwrote anchor inputs');
    await page.getByRole('button',{name:'停止播放',exact:true}).click();
    const after = await (await page.request.get(`${base}/api/works/${wid}/analyses`)).json();
    if (JSON.stringify(after.find((n)=>n.id===card.id).segments)!==beforeJson) throw Error('context persisted over analysis anchor');
    checks.push('full-theme-and-evidence-separated','context-all-voices-without-anchor-mutation','gpt6sol-provenance');
    const parent = guide.sections.find((s)=>s.id==='m1-intro');
    await page.getByRole('combobox',{name:'筛选导听章节'}).selectOption(parent.id);
    await page.locator(`[data-analysis-id="${card.id}"]`).waitFor();
    checks.push('parent-filter-includes-descendants');
    await page.locator(`[data-analysis-id="${card.id}"]`).click();
    await page.screenshot({path:'output/playwright/tcha-phrases-desktop.png'});
    await page.setViewportSize({width:390,height:844});
    if (await page.evaluate(()=>document.documentElement.scrollWidth > innerWidth+1)) throw Error('mobile overflow');
    if (!await page.getByRole('combobox',{name:'前后文小节数'}).isVisible()) throw Error('context controls hidden on mobile');
    await page.getByRole('combobox',{name:'前后文小节数'}).selectOption('4');
    await page.screenshot({path:'output/playwright/tcha-phrases-mobile.png',fullPage:true});
    await page.screenshot({path:'output/playwright/tcha-phrases-mobile-player.png'});
    checks.push('mobile');
    await page.setViewportSize({width:1440,height:1000});
    for (const [movement,id] of [[2,'sol-2-flute'],[3,'sol-3-a1']]) {
      await page.getByRole('button',{name:'返回曲库',exact:true}).click();
      await page.getByRole('textbox',{name:'搜索曲名'}).fill('柴一');
      await page.locator(`[data-work-id="tchaikovsky-op23-${movement}"]`).click();
      await page.locator(`[data-analysis-id="${id}"]`).click();
      await page.locator('.segment-entry[data-segment-role="theme"]').first().getByRole('button',{name:'试听完整主题陈述',exact:true}).click();
      await page.locator('.sounding-note').first().waitFor({timeout:12000});
      await page.getByRole('button',{name:'停止播放',exact:true}).click();
    }
    checks.push('three-movements-playable');
    if (errors.length || external.length) throw Error(JSON.stringify({errors,external}));
    return {result:'passed',checks,errors,externalRequests:external.length};
  } finally { await page.unroute('**/*'); }
}
