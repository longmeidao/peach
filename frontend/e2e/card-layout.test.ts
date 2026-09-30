import assert from 'node:assert/strict';
import {after,before,describe,it} from 'node:test';
import type {Browser} from 'playwright-core';
import {launch,requiredEnv,VIEWPORTS} from './harness.ts';

describe('混排作品的画面框',()=>{
 let browser:Browser;
 before(async()=>{browser=await launch()});
 after(async()=>{await browser?.close()});
 for(const viewport of VIEWPORTS)for(const size of ['big','small']){
  it(`${viewport.name} ${size} 作品与 Mix 等高并保留横图`,async()=>{
   const context=await browser.newContext({viewport:{width:viewport.width,height:viewport.height}});
   try{
    await context.addInitScript(size=>localStorage.setItem('peach.settings.v1',JSON.stringify({detailAutoplay:false,homeLayout:size})),size);
    const page=await context.newPage();
    await page.route('**/api/items?*',route=>route.fulfill({json:{items:Array.from({length:20},(_,i)=>({
     id:91000+i,name:`示例作品 ${i}`,creator:'示例创作者',is_jav:i%2===0,has_thumb:true,has_cover:false,
     width:1600,height:900,location:'local',duration:120,
    })),total:20,has_more:false}}));
    await page.route('**/poster?*',route=>route.fulfill({contentType:'image/svg+xml',body:'<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900"><rect width="1600" height="900" fill="white"/></svg>'}));
    await page.goto(requiredEnv('PEACH_E2E_ORIGIN')+'/',{waitUntil:'load'});
    await page.locator('#grid [data-mix-card]').waitFor();
    const frames=await page.locator('#grid [data-media-grid] > [data-media-card] [data-media-pic], #grid [data-mix-cover]').evaluateAll(nodes=>nodes.map(node=>{
     const box=node.getBoundingClientRect(),img=node.querySelector('img')!;
     return {ratio:box.width/box.height,fit:getComputedStyle(img).objectFit,background:getComputedStyle(img).backgroundColor};
    }));
    assert.ok(frames.length>=20);
    for(const frame of frames){
     assert.ok(Math.abs(frame.ratio-(size==='big'?3/4:16/9))<.01,JSON.stringify(frame));
     assert.equal(frame.fit,'contain');
     assert.equal(frame.background,'rgb(0, 0, 0)');
    }
   }finally{await context.close()}
  });
 }
});
