/* Run: node web/verify.cjs. Requires Playwright; CHROME_PATH may select a browser.
   The page itself remains dependency-free. Screenshots go to web/validation/. */
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const { pathToFileURL } = require('node:url');
const htmlPath = path.join(__dirname, 'index.html');
const html = fs.readFileSync(htmlPath, 'utf8');
const scripts = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const data = JSON.parse(scripts[0]);
const core = vm.createContext({});
vm.runInContext(scripts[1], core);
const expected = {zero:[3.1704180357133085e-13,180,111],linear:[1.0770476404261172e-13,126,77],random:[1.5004271652813487e-14,198,123]};
const results = {};
for (const initial of Object.keys(expected)) {
  const solver = new core.PhotonicSolver.Solver(data,initial);
  const result = solver.complete();
  const [residual,optical,digital] = expected[initial];
  assert.equal(result.status,'converged');
  assert.equal(result.relativeResidual,residual);
  assert.equal(result.counts.optical,optical); assert.equal(result.counts.digital,digital);
  results[initial] = JSON.parse(JSON.stringify(result));
}
console.log('PASS: numerical baselines, all three starting guesses');
if (process.argv.includes('--core-only')) process.exit(0);
try { const u = require('/usr/share/nodejs/playwright-core/lib/utilsBundle.js'); if (u.rimraf.length === 3) u.rimraf = require('node:util').promisify(u.rimraf); } catch {}
const { chromium } = require('playwright');
const screenshots = path.join(__dirname,'validation');
fs.mkdirSync(screenshots,{recursive:true});
const report = {baseline:Object.fromEntries(Object.entries(results).map(([key,r])=>[key,{relativeResidual:r.relativeResidual,counts:r.counts}])),checks:[]};
function pass(name) { report.checks.push(name); console.log('PASS:',name); }
(async () => {
  const browser = await chromium.launch({headless:true, ...(process.env.CHROME_PATH ? {executablePath:process.env.CHROME_PATH} : {})});
  const errors = [];
  const context = await browser.newContext({viewport:{width:1440,height:1050}});
  const page = await context.newPage();
  page.on('pageerror',e=>errors.push(e.message));
  const open = () => page.goto(pathToFileURL(htmlPath).href);
  const state = () => page.evaluate(()=>PhotonicLab.state());
  const shot = name => page.screenshot({path:path.join(screenshots,name+'.png'),fullPage:true});
  try {
    await open();
    assert.equal((await state()).playing,false);
    assert.equal(await page.locator('#explore').getAttribute('open'),null);
    assert.equal(await page.locator('[data-component="encoder"]').count(),1);
    assert.equal(await page.locator('[data-component="detector"]').count(),1);
    assert.equal(await page.locator('[data-component^="matrix"]').count(),3);
    await shot('desktop-ready');
    await page.keyboard.press('Tab');
    assert.equal(await page.evaluate(()=>document.activeElement.getAttribute('href')),'index.html');
    await page.keyboard.press('Tab');
    assert.equal(await page.evaluate(()=>document.activeElement.getAttribute('href')),'loop.html');
    await page.keyboard.press('Tab');
    assert.equal(await page.evaluate(()=>document.activeElement.id),'run');
    await page.locator('[data-component="laser"]').focus();
    assert.equal(await page.evaluate(()=>getComputedStyle(document.activeElement.querySelector('.face')).stroke),'rgb(255, 255, 255)');
    const before = await state();
    await page.keyboard.press('Enter');
    assert.equal(await page.locator('#component-info').isVisible(),true);
    assert.equal((await state()).event,before.event);
    await page.locator('#close-component').click();
    await page.locator('[data-stage="correct"]').click();
    assert.match(await page.locator('#overview-note').textContent(),/fine → coarse → fine/);
    assert.equal((await state()).event,before.event);
    pass('keyboard focus and component / overview explanations do not advance solver');
    await page.locator('#fullscreen').click();
    assert.equal(await page.evaluate(()=>document.fullscreenElement?.id),'workspace');
    await page.locator('#fullscreen').click();
    assert.equal(await page.evaluate(()=>document.fullscreenElement),null);
    assert.match(await page.locator('#x-samples').textContent(),/x = \[0, 0, 0/);
    pass('full-screen workspace enters/exits; initial x values visible');
    await page.evaluate(()=>{PhotonicLab.reset();while(!PhotonicLab.state().operation.includes('encodes'))PhotonicLab.step();});
    await page.locator('#next').click(); // Matrix multiplication with real animation time.
    await page.waitForTimeout(180);
    await page.locator('#run').click(); // Pause during beam travel.
    const paused = await state();
    const packet = await page.locator('#signal-packet').getAttribute('cx');
    assert(paused.presentation.progress>0 && paused.presentation.progress<1);
    await page.waitForTimeout(180);
    assert.equal((await state()).event,paused.event);
    assert.equal((await state()).presentation.progress,paused.presentation.progress);
    assert.equal(await page.locator('#signal-packet').getAttribute('cx'),packet);
    await shot('desktop-optical-multiply');
    await page.locator('#run').click();
    await page.waitForTimeout(80);
    assert((await state()).presentation.progress>paused.presentation.progress);
    await page.locator('#reset').click();
    await page.waitForTimeout(100);
    assert.equal((await state()).event,0);
    assert.equal((await state()).presentation.animating,false);
    await page.evaluate(()=>{PhotonicLab.next();PhotonicLab.next();PhotonicLab.next();});
    assert.equal((await state()).event,1);
    assert.equal(await page.locator('#next').isDisabled(),true);
    await page.locator('#reset').click();
    pass('pause freezes beam and generator; resume, repeated Next and mid-operation restart');
    await page.evaluate(()=>{while(!PhotonicLab.state().operation.includes('completes pre-sweep'))PhotonicLab.step();});
    assert.equal(await page.locator('#signal-packet').getAttribute('visibility'),'hidden');
    assert.equal(await page.locator('[data-component="cpu"]').getAttribute('class'),'component cpu-active');
    assert.match(await page.locator('#signal-values').textContent(),/old e[\s\S]*new e/);
    assert.match(await page.locator('#zero-explanation').textContent(),/e = 0/);
    assert.match(await page.locator('#x-status').textContent(),/unchanged/);
    await shot('desktop-cpu-update');
    await page.evaluate(()=>{while(PhotonicLab.state().activeLevel!==1 || !PhotonicLab.state().operation.includes('Fixed matrix'))PhotonicLab.step();});
    assert.match(await page.locator('[data-component="matrix"]').textContent(),/A₁.*22 × 22/);
    await page.evaluate(()=>{while(PhotonicLab.state().activeLevel!==2 || !PhotonicLab.state().operation.includes('Fixed matrix'))PhotonicLab.step();});
    assert.match(await page.locator('[data-component="matrix"]').textContent(),/A₂.*8 × 8/);
    await page.evaluate(()=>{while(!PhotonicLab.state().operation.includes('3×3 system'))PhotonicLab.step();});
    assert.match(await page.locator('[data-component="cpu"]').textContent(),/3 × 3 solve/);
    assert.equal(await page.locator('#signal-packet').getAttribute('visibility'),'hidden');
    pass('three optical levels and CPU-only 3×3 coarse solve');
    await page.locator('#explore > summary').click();
    await page.locator('summary').filter({hasText:'Inside the solver'}).click();
    await page.selectOption('#routine','multigrid');
    await shot('desktop-details');
    await page.locator('#finish').click();
    assert.equal((await state()).status,'converged');
    await page.locator('#explore > summary').click();
    await shot('desktop-completed');
    assert.equal(await page.locator('#run').isDisabled(),true);
    assert.equal(await page.locator('#next').isDisabled(),true);
    assert.match(await page.locator('#scene-title').textContent(),/Solution found/);
    pass('completion stops playback with success caption');
    // Verify actual downloaded bytes restart locally, independent of current DOM state.
    await page.locator('#explore > summary').click();
    const downloadPromise = page.waitForEvent('download');
    await page.locator('#download').click();
    const download = await downloadPromise;
    const downloaded = path.join('/tmp','photonic-verified-download.html');
    await download.saveAs(downloaded);
    const downloadedPage = await context.newPage();
    await downloadedPage.goto(pathToFileURL(downloaded).href);
    assert.equal(await downloadedPage.evaluate(()=>PhotonicLab.state().status),'ready');
    assert.deepEqual(await downloadedPage.evaluate(()=>PhotonicLab.finish().counts),results.zero.counts);
    await downloadedPage.close();
    pass('downloaded HTML boots and solves offline');
    // Deterministic clock drives the real presentation scheduler without a 30-minute wait.
    const controlled = await browser.newContext();
    await controlled.addInitScript(()=>{
      Object.defineProperty(document,'modelContext',{configurable:true,value:{registerTool(tool){window.testTools ??= [];window.testTools.push(tool);}}});
      let clock=0, nextId=0;const pending=new Map();
      window.requestAnimationFrame=fn=>{pending.set(++nextId,fn);return nextId;};
      window.cancelAnimationFrame=id=>pending.delete(id);
      window.flushPresentation=(delta=2000)=>{clock=Math.max(clock,performance.now())+delta;const frames=[...pending.values()];pending.clear();frames.forEach(fn=>fn(clock));};
    });
    const controlledPage = await controlled.newPage();
    controlledPage.on('pageerror',e=>errors.push(e.message));
    await controlledPage.goto(pathToFileURL(htmlPath).href);
    const toolChecks = await controlledPage.evaluate(async()=>{
      const tools=Object.fromEntries(testTools.map(tool=>[tool.name,tool]));
      const before=PhotonicLab.state();await tools.get_solver_state.execute({});
      const unchanged=PhotonicLab.state().event===before.event;
      await tools.reset_solver.execute({initial:'linear'});
      const result=await tools.solve_pde.execute({});
      let rejected=false;try{await tools.reset_solver.execute({initial:'invalid'});}catch{rejected=true;}
      return {names:Object.keys(tools),unchanged,result,rejected};
    });
    assert.deepEqual(toolChecks.names,['get_solver_state','solve_pde','reset_solver']);
    assert(toolChecks.unchanged && toolChecks.rejected);
    assert.deepEqual(toolChecks.result.counts,results.linear.counts);
    pass('registered tools retain names, execution, read-only state and input validation');
    await controlledPage.evaluate(()=>{PhotonicLab.reset();while(!PhotonicLab.state().operation.includes('Fixed matrix'))PhotonicLab.step();PhotonicLab.next();flushPresentation(350);});
    assert.equal(await controlledPage.locator('#signal-packet').getAttribute('fill'),'#ffd18a');
    await controlledPage.evaluate(()=>flushPresentation(700));
    assert.equal(await controlledPage.locator('#signal-packet').getAttribute('fill'),'#9ce6d7');
    assert.equal((await controlledPage.evaluate(()=>PhotonicLab.state())).counts.adc,1);
    await controlledPage.evaluate(()=>{PhotonicLab.finish();flushPresentation();});
    assert.deepEqual((await controlledPage.evaluate(()=>PhotonicLab.state())).counts,results.zero.counts);
    pass('detection animates optical arrival before electrical return; finish cancels pending animation');
    for (const initial of Object.keys(expected)) {
      const browserBaseline = await controlledPage.evaluate(initial => { PhotonicLab.reset(initial); return PhotonicLab.finish(); }, initial);
      // Math.sin and last-bit arithmetic can differ between Node and Chromium V8.
      browserBaseline.solution.forEach((value, i) => assert(Math.abs(value-results[initial].x[i]) < 1e-12));
      assert(Math.abs(browserBaseline.relativeResidual/results[initial].relativeResidual-1) < 1e-4);
      for (const mode of ['manual','autoplay','finish']) {
        const actual = await controlledPage.evaluate(({initial,mode})=>{
          PhotonicLab.reset(initial);
          if(mode==='finish')return PhotonicLab.finish();
          if(mode==='autoplay')PhotonicLab.playPause();
          let guard=0;
          while(!['converged','error','limit'].includes(PhotonicLab.state().status)&&guard++<20000){
            if(mode==='manual')PhotonicLab.next();
            window.flushPresentation();
          }
          return PhotonicLab.state();
        },{initial,mode});
        assert.equal(actual.status,'converged');
        assert.deepEqual(actual.solution,browserBaseline.solution);
        assert.deepEqual(actual.counts,results[initial].counts);
        assert.equal(actual.relativeResidual,browserBaseline.relativeResidual);
        assert.equal(actual.playing,false);
      }
    }
    pass('manual Next, autoplay and finish identical for zero / linear / random');
    // Inject terminal conditions at the generator boundary to exercise presentation branches.
    await page.evaluate(()=>{
      PhotonicLab.reset();const original=PhotonicSolver.Solver.prototype.next;
      PhotonicSolver.Solver.prototype.next=function(){PhotonicSolver.Solver.prototype.next=original;this.generator=(function*(){throw new Error('Injected numerical breakdown');})();return original.call(this);};
      PhotonicLab.next();
    });
    assert.equal((await state()).status,'error');
    assert.match(await page.locator('#scene-title').textContent(),/Numerical error/);
    assert.equal((await state()).playing,false);
    await page.evaluate(()=>{
      PhotonicLab.reset();const original=PhotonicSolver.Solver.prototype.next;
      PhotonicSolver.Solver.prototype.next=function(){PhotonicSolver.Solver.prototype.next=original;this.status='limit';this.finished=true;return {done:true,value:this.result()};};
      PhotonicLab.next();
    });
    assert.match(await page.locator('#scene-title').textContent(),/Iteration limit/);
    assert.equal((await state()).playing,false);
    pass('distinct numerical-error and iteration-limit captions stop playback (fault injection)');
    await page.emulateMedia({reducedMotion:'reduce'});
    await page.evaluate(()=>{PhotonicLab.reset();while(!PhotonicLab.state().operation.includes('encodes'))PhotonicLab.step();PhotonicLab.next();});
    assert.equal(await page.locator('#signal-packet').getAttribute('visibility'),'hidden');
    assert.equal((await state()).presentation.animating,false);
    assert.match(await page.locator('[data-component="matrix"]').getAttribute('class'),/active/);
    pass('reduced motion uses static highlights');
    await page.emulateMedia({reducedMotion:'no-preference'});
    await page.setViewportSize({width:390,height:844});
    await page.evaluate(()=>PhotonicLab.reset());
    await page.locator('#explore').evaluate(el=>el.open=false);
    await shot('mobile-ready');
    await page.evaluate(()=>{while(!PhotonicLab.state().operation.includes('Fixed matrix'))PhotonicLab.step();});
    await shot('mobile-optical-multiply');
    await page.evaluate(()=>{while(!PhotonicLab.state().operation.includes('completes pre-sweep'))PhotonicLab.step();});
    await shot('mobile-cpu-update');
    await page.locator('#explore').evaluate(el=>el.open=true);
    await shot('mobile-details');
    await page.evaluate(()=>PhotonicLab.finish());
    await page.locator('#explore').evaluate(el=>el.open=false);
    await shot('mobile-completed');
    for(const width of [320,375,390,700,768,1440]){
      await page.setViewportSize({width,height:900});
      await page.locator('details').evaluateAll(nodes=>nodes.forEach(node=>node.open=true));
      const dimensions=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));
      assert(dimensions.scroll<=dimensions.width,`horizontal overflow at ${width}: ${dimensions.scroll}`);
    }
    pass('mobile screenshots and no horizontal overflow at 320–1440px, all details expanded');
    assert.deepEqual(errors,[]);
    pass('no browser JavaScript errors');
    fs.writeFileSync(path.join(screenshots,'report.json'),JSON.stringify(report,null,2)+'\n');
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});
