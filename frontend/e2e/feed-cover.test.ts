import assert from 'node:assert/strict';
import {after,before,describe,it} from 'node:test';
import type {Browser} from 'playwright-core';
import {launch,requiredEnv,VIEWPORTS} from './harness.ts';

describe('新作封面显示时机',()=>{
 let browser:Browser;
 before(async()=>{browser=await launch()});
 after(async()=>{await browser?.close()});
 for(const viewport of VIEWPORTS)for(const delay of [0,1800]){
  it(`${viewport.name} ${delay?'慢图':'预加载'}完成取景才显示`,{timeout:60000},async()=>{
   const context=await browser.newContext({viewport:{width:viewport.width,height:viewport.height}});
   try{
    await context.addInitScript(()=>{
     localStorage.setItem('peach.settings.v1',JSON.stringify({detailAutoplay:false}));
     (window as any).__unframed=[];
     const check=(img:HTMLImageElement)=>{
      if(!img.matches('.feednew img.cover')||img.dataset.frame)return;
      if(getComputedStyle(img).visibility==='visible'&&img.naturalWidth)
       (window as any).__unframed.push({src:img.src,complete:img.complete});
     };
     // 捕获监听先于应用执行，记录加载图尚未取景的那一刻。
     document.addEventListener('load',event=>{
      if(event.target instanceof HTMLImageElement)check(event.target);
     },true);
     const sample=()=>{document.querySelectorAll<HTMLImageElement>('.feednew img.cover').forEach(check);requestAnimationFrame(sample)};
     requestAnimationFrame(sample);
    });
    const page=await context.newPage();
    const remote='https://covers.example.test/framing.svg';
    await page.route(remote,async route=>{
     if(delay)await new Promise(resolve=>setTimeout(resolve,delay));
     await route.fulfill({contentType:'image/svg+xml',body:'<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="1000"><rect width="796" height="1000" fill="#f00"/><rect x="796" width="704" height="1000" fill="#0f0"/></svg>'});
    });
    await page.route(/\/api\/feeds\/discoveries\?/,route=>route.fulfill({json:{ok:true,items:[{id:1,code:'EXM-001',title:'示例新作',has_cover:false,cover_url:remote}]}}));
    await page.goto(requiredEnv('PEACH_E2E_ORIGIN')+'/stats');
    for(let round=0;round<2;round++){
     await page.evaluate(()=>{history.pushState({},'','/');window.dispatchEvent(new PopStateEvent('popstate'))});
     const image=page.locator('#feedNew img.cover.panel');
     await image.waitFor({state:'visible'});
     assert.equal(await image.evaluate(img=>img.style.getPropertyValue('--panel-clip')),'0% 0% 0% 53.07%');
     const positions=await image.evaluate(async img=>{
      const samples:string[]=[];
      for(let n=0;n<12;n++){
       await new Promise(requestAnimationFrame);
       const css=getComputedStyle(img);
       samples.push([css.left,css.top,css.width,css.height,css.clipPath].join('|'));
      }
      return samples;
     });
     assert.equal(new Set(positions).size,1,'可见封面的取景保持稳定');
     assert.deepEqual(await page.evaluate(()=>(window as any).__unframed),[],'已加载封面在取景完成前保持隐藏');
     await page.evaluate(()=>{history.pushState({},'','/stats');window.dispatchEvent(new PopStateEvent('popstate'))});
     await page.locator('#feedNew').waitFor({state:'hidden'});
    }
   }finally{await context.close()}
  });
 }
 for(const viewport of VIEWPORTS){
  it(`${viewport.name} 设置里的视频大小同步首页和 JAV`,{timeout:60000},async()=>{
   const context=await browser.newContext({viewport:{width:viewport.width,height:viewport.height},reducedMotion:'reduce'});
   try{
    await context.addInitScript(()=>localStorage.setItem('peach.settings.v1',JSON.stringify({detailAutoplay:false,homeLayout:'big',javLayout:'big'})));
    const page=await context.newPage();
    await page.goto(requiredEnv('PEACH_E2E_ORIGIN')+'/');
    await page.locator('#grid [data-media-card]').first().waitFor({state:'visible'});
    if(viewport.name==='mobile')await page.locator('#filterBtn').click();
    await page.locator('#settingsBtn').click();
    await page.locator('#settingsPanel').getByRole('tab',{name:'浏览',exact:true}).click();
    await page.locator('#javSizeSetting label:has(input[value="small"])').click();
    const saved=await page.evaluate(()=>JSON.parse(localStorage.getItem('peach.settings.v1')||'{}'));
    assert.equal(saved.homeLayout,'small');assert.equal(saved.javLayout,'small');
    await page.locator('#settingsClose').click();
    const ratio=await page.locator('#grid [data-media-pic]').first().evaluate(node=>{
     const rect=node.getBoundingClientRect();return rect.width/rect.height;
    });
    assert.ok(Math.abs(ratio-16/9)<.01);
   }finally{await context.close()}
  });
  it(`${viewport.name} 竖版正封完整放入卡片`,{timeout:60000},async()=>{
   const context=await browser.newContext({viewport:{width:viewport.width,height:viewport.height}});
   try{
    const page=await context.newPage(),remote='https://covers.example.test/front.svg';
    await page.route(remote,route=>route.fulfill({contentType:'image/svg+xml',body:'<svg xmlns="http://www.w3.org/2000/svg" width="632" height="900"><rect width="632" height="900" fill="#0f0"/></svg>'}));
    await page.route(/\/api\/feeds\/discoveries\?/,route=>route.fulfill({json:{ok:true,items:[{id:1,code:'EXM-001',title:'示例新作',has_cover:false,cover_url:remote}]}}));
    await page.goto(requiredEnv('PEACH_E2E_ORIGIN')+'/');
    const image=page.locator('#feedNew img.cover[data-frame="front"]');await image.waitFor({state:'visible'});
    assert.equal(await image.evaluate(img=>getComputedStyle(img).objectFit),'contain');
   }finally{await context.close()}
  });
 }
});
