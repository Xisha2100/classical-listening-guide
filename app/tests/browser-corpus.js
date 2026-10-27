async (page) => {
 await page.goto('http://127.0.0.1:8765');
 const works=await (await page.request.get('http://127.0.0.1:8765/api/works')).json();
 const tested=[];const external=[];
 await page.route('**/*',route=>{const url=new URL(route.request().url());if(url.hostname!=='127.0.0.1'){external.push(url.href);return route.abort()}return route.continue()});
 for(const work of works){
  if(await page.getByRole('button',{name:'返回曲库',exact:true}).count())await page.getByRole('button',{name:'返回曲库',exact:true}).click();
  await page.getByRole('textbox',{name:'搜索曲名'}).fill(work.catalogue);
  await page.locator('.work-card').click();
  const notes=await (await page.request.get(`http://127.0.0.1:8765/api/works/${work.id}/analyses`)).json();
  for(const note of notes.filter(n=>n.origin==='seed')){
   await page.locator('.analysis-item').filter({hasText:note.title}).click();
   // Play the last comparison example; the first often repeats the original theme.
   const seg=note.segments[note.segments.length-1];
   await page.locator('.segment-chip').getByRole('button',{name:seg.label,exact:true}).click();
   await page.locator('.selected-note').first().waitFor();
   const ids=await page.locator('.selected-note').evaluateAll(nodes=>nodes.map(n=>n.id));
   if(!ids.every(id=>seg.note_ids.includes(id)))throw Error('wrong highlighted IDs '+note.title);
   await page.getByRole('button',{name:'播放片段',exact:true}).click();
   await page.locator('.sounding-note').first().waitFor({timeout:8000});
   await page.getByRole('button',{name:'停止播放',exact:true}).click();
   await page.locator('.sounding-note').first().waitFor({state:'hidden'});
   tested.push({title:note.title,segment:seg.label,highlightCount:ids.length});
  }
 }
 // Loop, change speed and stop through the actual transport UI.
 await page.getByRole('button',{name:'循环播放',exact:true}).click();
 await page.getByRole('button',{name:'播放片段',exact:true}).click();
 await page.locator('.sounding-note').first().waitFor();
 await page.getByRole('combobox',{name:'播放速度'}).selectOption('0.5');
 await page.getByRole('button',{name:'播放片段',exact:true}).waitFor();
 await page.getByRole('button',{name:'循环播放',exact:true}).click();
 await page.unroute('**/*');
 if(tested.length!==15||external.length)throw Error(JSON.stringify({count:tested.length,external}));
 return {result:'passed',tested,externalRequests:external.length};
}
