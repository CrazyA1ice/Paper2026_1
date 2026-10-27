const {chromium} = require('C:/Users/Quant/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const fs = require('node:fs');
(async()=>{
 const dir='C:\\Users\\Quant\\Desktop\\Paper2026_1\\paper_template\\长江信息通信\\格式核对工作_20261027\\secondary_preview';
 const browser=await chromium.launch({headless:true,executablePath:'C:/Users/Quant/AppData/Local/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-win64/chrome-headless-shell.exe'});
 const page=await browser.newPage();
 await page.goto(pathToFileURL(path.join(dir,'review.html')).href);
 await page.evaluate(()=>document.fonts.ready);
 await page.pdf({path:path.join(dir,'review.pdf'),printBackground:true,preferCSSPageSize:true});
 const checks=await page.evaluate(()=>({images:document.images.length,math:document.querySelectorAll('math').length,overflow:[...document.querySelectorAll('.equation,table,p,h1,h2')].filter(e=>e.scrollWidth>e.clientWidth+2).map(e=>({text:e.textContent.slice(0,100),width:e.clientWidth,scroll:e.scrollWidth})),imageComplete:[...document.images].map(i=>i.complete&&i.naturalWidth>0)}));
 fs.writeFileSync(path.join(dir,'browser_checks.json'),JSON.stringify(checks,null,2));
 console.log(JSON.stringify(checks));
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
