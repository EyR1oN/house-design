const fs=require('fs'),path=require('path');
const {chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});const page=await browser.newPage({viewport:{width:900,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('file:///'+path.join(__dirname,'kitchen-storage-preview.html').replaceAll('\\','/'));const frame=page.frameLocator('iframe');await frame.locator('#kitchen-study-oct27 svg').first().waitFor();
 for(const width of [900,390]){
  await page.setViewportSize({width,height:1100});
  for(const option of ['buffet','island','wall','peninsula']){
   await frame.locator('[data-option="'+option+'"]').click();
   await frame.locator('[data-option="'+option+'"][aria-pressed="true"]').waitFor();
   const state=await frame.locator('#kitchen-study-oct27').evaluate(el=>({svg:el.querySelectorAll('svg').length,text:el.querySelector('.ks-facts').textContent,overflow:el.scrollWidth>el.clientWidth+2}));
   if(state.svg!==2||state.overflow||!state.text.trim())throw new Error(JSON.stringify({width,option,state}));
  }
 }
 await page.setViewportSize({width:900,height:1100});await frame.locator('[data-option="island"]').click();await page.screenshot({path:path.join(__dirname,'kitchen-storage-check.png'),fullPage:true});
 await browser.close();if(errors.length)throw new Error(errors.join('\n'));console.log('VISUAL_CHECK_OK: 4 options at desktop/mobile; no page errors or horizontal overflow');
})();
