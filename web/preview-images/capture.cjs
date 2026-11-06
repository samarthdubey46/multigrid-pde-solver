const fs=require('fs'),path=require('path');
// Compatibility for this host's system Playwright.
try{const b=require('/usr/share/nodejs/playwright-core/lib/utilsBundle.js');if(b.rimraf.length===3)b.rimraf=require('util').promisify(b.rimraf);}catch{}
const {chromium}=require('playwright');
(async()=>{const browser=await chromium.launch({headless:true,executablePath:'/opt/google/chrome/chrome'});try{const page=await browser.newPage({viewport:{width:1120,height:1000},deviceScaleFactor:2});for(const [layout,name] of [['1','preview-1-stacked-levels'],['2','preview-2-separate-levels']]){await page.goto(require('url').pathToFileURL(path.join(__dirname,'layout-source.html')).href+'?layout='+layout);await page.screenshot({path:path.join(__dirname,name+'.png'),fullPage:true});console.log(name+'.png saved');}}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
