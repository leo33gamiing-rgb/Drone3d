const {chromium}=require('playwright');
const path=require('path');
(async()=>{
  const [,,dir,...files]=process.argv;
  const b=await chromium.launch();
  const p=await b.newPage();
  for(const f of files){
    await p.goto('file://'+path.join(dir,f+'.html'),{waitUntil:'networkidle'});
    await p.evaluate(()=>document.fonts.ready);
    // overflow check
    const ov=await p.evaluate(()=>[...document.querySelectorAll('.page')].map((pg,i)=>{
      const r=pg.getBoundingClientRect(); let worst=0, who='';
      pg.querySelectorAll('*').forEach(e=>{const b=e.getBoundingClientRect(); const o=b.bottom-(r.bottom- (parseFloat(getComputedStyle(pg).paddingBottom)||0)); if(o>worst+0.5){worst=o;who=e.className||e.tagName}});
      const side=pg.querySelector('.side'); const cols=pg.querySelector('.cols');
      return {page:i+1,overflowPx:Math.round(worst),who, colsH: cols?Math.round(cols.getBoundingClientRect().height):null, sideH: side?Math.round(side.scrollHeight):null, specsH: pg.querySelector('.specs')?Math.round(pg.querySelector('.specs').scrollHeight):null};
    }));
    console.log(f, JSON.stringify(ov));
    await p.pdf({path:path.join(dir,f+'.pdf'),preferCSSPageSize:true,printBackground:true});
  }
  await b.close();
})();
