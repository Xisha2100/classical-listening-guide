async (page) => {
  const base=new URL(page.url()).origin, errors=[], writes=[], external=[];
  const onError=e=>errors.push(e.message);
  const onRequest=req=>{if(['POST','PUT','PATCH','DELETE'].includes(req.method()))writes.push(new URL(req.url()).pathname);};
  page.on('pageerror',onError);page.on('request',onRequest);
  await page.route('**/*',route=>{
    const url=new URL(route.request().url());
    if(url.origin!==base){external.push(url.href);return route.abort();}
    return route.continue();
  });
  const previous=await page.evaluate(()=>({drafts:localStorage.getItem('listening-room.drafts.v2'),comparison:localStorage.getItem('listening-room.comparison.v2')}));
  try {
    const legacy='{"records":{"legacy":{"draft":{"title":"旧版未保存笔记","body":"原始摘录"}}},"last":{}}';
    await page.evaluate(raw=>{localStorage.setItem('listening-room.drafts.v2',raw);localStorage.removeItem('listening-room.comparison.v2');},legacy);
    await page.goto(base);
    await page.getByRole('button',{name:'导出旧版草稿',exact:true}).waitFor();
    const downloadWait=page.waitForEvent('download');
    await page.getByRole('button',{name:'导出旧版草稿',exact:true}).click();
    const download=await downloadWait;
    if(download.suggestedFilename()!=='旧版浏览器草稿.json')throw Error('legacy draft export missing');
    if(await page.evaluate(()=>localStorage.getItem('listening-room.drafts.v2'))!==legacy)throw Error('legacy draft modified');
    const works=await (await page.request.get(base+'/api/works')).json();
    const chosen=works.find(w=>w.id==='bach-bwv847'),other=works.find(w=>w.id==='mozart-k265');
    const cards=await (await page.request.get(`${base}/api/works/${chosen.id}/analyses`)).json();
    const card=cards.find(c=>c.segments.length);
    await page.locator(`[data-work-id="${chosen.id}"]`).click();
    await page.locator(`[data-analysis-id="${card.id}"]`).click();
    // Simulate Codex's next local-file revision. Backend tests cover real disk writes.
    const changed=cards.map(c=>c.id===card.id?{...c,body:'Codex 刚刚记录的新解释',sources:[...c.sources,{id:'refresh-ref',kind:'personal',title:'新资料',author:'',edition:'',pages:'',url:'',accessed_at:'',excerpt:'保留的摘录',summary:'独立的概括',extracted:false}]}:c);
    await page.route(`**/api/works/${chosen.id}/analyses`,route=>route.fulfill({json:changed}));
    await page.getByRole('button',{name:'刷新项目',exact:true}).click();
    await page.locator('.detail-panel').getByText('Codex 刚刚记录的新解释',{exact:true}).waitFor();
    await page.getByRole('button',{name:'资料',exact:true}).click();
    await page.getByText('保留的摘录',{exact:true}).waitFor();
    await page.unroute(`**/api/works/${chosen.id}/analyses`);
    await page.getByRole('button',{name:'笔记',exact:true}).click();
    await page.getByRole('button',{name:'将片段1加入比较',exact:true}).click();
    await page.getByRole('button',{name:'返回曲库',exact:true}).click();
    await page.locator(`[data-work-id="${other.id}"]`).click();
    const otherCards=await (await page.request.get(`${base}/api/works/${other.id}/analyses`)).json();
    await page.locator(`[data-analysis-id="${otherCards.find(c=>c.segments.length).id}"]`).click();
    await page.getByRole('button',{name:'将片段1加入比较',exact:true}).click();
    const queue=await page.evaluate(()=>JSON.parse(localStorage.getItem('listening-room.comparison.v2')));
    if(queue.length!==2 || queue[0].work_id===queue[1].work_id)throw Error('comparison identity mixed');
    await page.getByRole('button',{name:'试听 A → B',exact:true}).click();
    await page.locator(`.comparison-paper[data-comparison-work-id="${chosen.id}"]`).waitFor();
    await page.locator(`.comparison-paper[data-comparison-work-id="${other.id}"]`).waitFor({timeout:25000});
    await page.getByRole('button',{name:'停止比较',exact:true}).click();
    await page.getByRole('button',{name:'关闭比较谱面',exact:true}).click();
    // The page must not invoke any old model/search/writing endpoints.
    if(writes.some(p=>p!=='/api/reindex'&&!p.endsWith('/segments')))throw Error('unexpected write API: '+writes.join(','));
    if(errors.length||external.length)throw Error(JSON.stringify({errors,external}));
    return {result:'passed',flows:['legacy-draft-preserved-and-exportable','refresh-selected-analysis-and-sources','cross-work-comparison','local-only-requests'],externalRequests:external.length};
  } finally {
    await page.unroute('**/*');
    page.off('pageerror',onError);page.off('request',onRequest);
    await page.evaluate(previous=>{
      for(const [name,key] of [['drafts','listening-room.drafts.v2'],['comparison','listening-room.comparison.v2']]){
        if(previous[name]===null)localStorage.removeItem(key);else localStorage.setItem(key,previous[name]);
      }
    },previous);
  }
}
