const {chromium}=require('C:/Users/seele/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const crypto=require('node:crypto');
(async()=>{
  const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
  const report={errors:[],checks:[],audio:[]};
  try{
    const page=await browser.newPage({viewport:{width:1480,height:1000}});
    page.on('pageerror',error=>report.errors.push(error.message));
    await page.addInitScript(()=>{
      window.audioSchedules=[];
      const original=AudioBufferSourceNode.prototype.start;
      AudioBufferSourceNode.prototype.start=function(...args){
        window.audioSchedules.push({duration:this.buffer?.duration,rate:this.playbackRate.value});
        return original.apply(this,args);
      };
    });
    await page.goto('http://127.0.0.1:5173');
    await page.click('[data-view="studio"]');
    await page.waitForSelector('.preset-voice-card');
    assert.equal(await page.locator('.preset-voice-card').count(),3);
    assert.equal(await page.inputValue('#voice'),'steady');
    assert.deepEqual(await page.locator('#voice optgroup').evaluateAll(nodes=>nodes.map(node=>node.label)),['内置主播','我的克隆','系统声音']);
    assert.equal(await page.locator('#delivery, #autoProsody, #savePresets').count(),0);
    report.checks.push('three built-in cards, separate clone group, fixed voice selection without style controls');
    await page.fill('#voicePreviewText','大家好，欢迎来到直播间。电量从30%充到80%[1]。');
    for(const id of ['steady','energetic','friendly']){
      const before=await page.evaluate(()=>window.audioSchedules.length);
      const responsePromise=page.waitForResponse(r=>r.url().endsWith('/tts/synthesize'),{timeout:120000});
      await page.locator(`[data-voice-card="${id}"] .voice-preview`).click();
      const response=await responsePromise;
      assert.equal(response.status(),200);
      const sent=response.request().postDataJSON();
      assert.equal(sent.voice_id,id);
      assert.ok(sent.text.includes('百分之三十')&&!sent.text.includes('[1]'));
      assert.equal(sent.delivery,'natural');
      const audio=await response.body();
      assert.ok(audio.length>32000);
      fs.writeFileSync(path.join(__dirname,`${id}-preview.wav`),audio);
      await page.waitForFunction(count=>window.audioSchedules.length>count,before,{timeout:10000});
      assert.ok((await page.evaluate(()=>window.audioSchedules.at(-1).duration))>1);
      assert.equal(await page.locator(`[data-voice-card="${id}"]`).getAttribute('class'),'preset-voice-card selected');
      report.audio.push({voice_id:id,bytes:audio.length,sha256:crypto.createHash('sha256').update(audio).digest('hex')});
      await page.click('#stopPreview');
    }
    assert.equal(new Set(report.audio.map(x=>x.sha256)).size,3);
    report.checks.push('each preset returns distinct real audio, decodes and schedules playback; citations/percentages normalized');
    await page.screenshot({path:path.join(__dirname,'studio.png'),fullPage:true});
    await page.reload();await page.click('[data-view="studio"]');await page.waitForSelector('.preset-voice-card');
    assert.equal(await page.inputValue('#voice'),'friendly');
    report.checks.push('selected speaker survives reload');
    await page.fill('#script','大家好，电量从30%充到80%[2]。');
    const streamPromise=page.waitForResponse(r=>r.url().endsWith('/tts/stream'),{timeout:120000});
    await page.click('#play');
    const stream=await streamPromise;assert.equal(stream.status(),200);
    assert.equal(stream.request().postDataJSON().voice_id,'friendly');
    await page.waitForFunction(()=>window.audioSchedules.length>0,null,{timeout:20000});
    await page.click('#stop');report.checks.push('fixed built-in voice is used by live streaming playback');
    await page.click('[data-view="evaluation"]');await page.waitForSelector('#evaluationForm');
    assert.equal(await page.locator('#savePresets').count(),0);
    assert.equal(await page.locator('#evaluationForm optgroup[label="内置主播"] option').count(),3);
    report.checks.push('listening evaluation includes built-ins without mutable clone bindings');
    await page.click('[data-view="avatar"]');await page.waitForSelector('#avatarCanvas');
    assert.equal(await page.inputValue('#voice'),'friendly');
    assert.equal(await page.locator('#delivery').count(),0);
    assert.equal(await page.locator('.avatar-tuning').count(),1);
    report.checks.push('local avatar shares speaker selection and retains mouth controls');
    await page.click('[data-view="studio"]');await page.waitForSelector('.preset-voice-card');
    await page.setViewportSize({width:820,height:1100});
    assert.equal(await page.locator('.preset-voice-grid').evaluate(node=>getComputedStyle(node).gridTemplateColumns.split(' ').length),1);
    await page.screenshot({path:path.join(__dirname,'studio-narrow.png'),fullPage:true});
    assert.deepEqual(report.errors,[]);report.passed=true;
  }catch(error){report.failure=error.stack;throw error;}
  finally{fs.writeFileSync(path.join(__dirname,'ui-report.json'),JSON.stringify(report,null,2));await browser.close();console.log(JSON.stringify(report));}
})().catch(error=>{console.error(error);process.exitCode=1;});
