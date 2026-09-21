const {chromium}=require('C:/Users/seele/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{
  const micFile=path.join(__dirname,'simulated-microphone.wav');
  const input=JSON.parse(fs.readFileSync(path.join(__dirname,'microphone-input.json'),'utf8'));
  const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',args:['--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream',`--use-file-for-fake-audio-capture=${micFile}`]});
  const report={errors:[],checks:[]};let createdId,page;
  try{
    page=await browser.newPage({viewport:{width:1480,height:1050}});
    page.on('pageerror',e=>report.errors.push(e.message));
    await page.addInitScript(()=>{
      window.micCalls=0;window.testStreams=[];window.micMode='allow';
      const original=navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
      navigator.mediaDevices.getUserMedia=async options=>{
        window.micCalls++;
        if(window.micMode==='deny')throw new DOMException('Test denied','NotAllowedError');
        const stream=await original(options);window.testStreams.push(stream);
        if(window.micMode==='pending')await new Promise(resolve=>window.resolveMic=resolve);
        return stream;
      };
    });
    await page.goto('http://127.0.0.1:5173');await page.click('[data-view="studio"]');await page.waitForSelector('#cloneCapture');
    assert.equal(await page.evaluate(()=>window.micCalls),0);
    await page.fill('#voicePrompt','手动填写的参考文本。');
    await page.click('#captureRecordTab');
    assert.equal(await page.evaluate(()=>window.micCalls),0);
    assert.equal(await page.locator('#recordScript').textContent(),input.text);
    await page.evaluate(()=>window.micMode='deny');await page.click('#recordStart');
    await page.waitForFunction(()=>document.querySelector('#recordStatus').textContent.includes('未获得麦克风权限'));
    assert.equal(await page.locator('#recordStart').isEnabled(),true);
    report.checks.push('microphone requested only on Record; denied permission shows retry/upload options');
    await page.evaluate(()=>window.micMode='pending');await page.click('#recordStart');
    await page.waitForFunction(()=>Boolean(window.resolveMic));await page.click('#captureUploadTab');
    await page.evaluate(()=>window.resolveMic());
    await page.waitForFunction(()=>window.testStreams.every(s=>s.getTracks().every(t=>t.readyState==='ended')));
    assert.equal(await page.inputValue('#voicePrompt'),'手动填写的参考文本。');
    report.checks.push('switching mode during permission request closes delayed streams and preserves upload text');
    await page.evaluate(()=>window.micMode='allow');await page.click('#captureRecordTab');await page.click('#recordStart');
    await page.waitForFunction(()=>document.querySelector('#recordStatus').textContent.startsWith('正在录音'));
    await page.waitForTimeout(1200);await page.click('#recordStop');
    await page.waitForFunction(()=>document.querySelector('#recordStatus').textContent.includes('不足 3 秒'));
    assert.equal(await page.locator('#recordPreview').isVisible(),false);
    report.checks.push('too-short recording is rejected without a clone upload');
    await page.click('#recordStart');await page.waitForFunction(()=>document.querySelector('#recordStatus').textContent.startsWith('正在录音'));
    assert.equal(await page.locator('#clone').isDisabled(),true);
    await page.waitForTimeout(Math.ceil((input.seconds+.15)*1000));await page.click('#recordStop');
    await page.waitForFunction(()=>document.querySelector('#recordStatus').textContent.startsWith('已录制'),null,{timeout:15000});
    const sample=await page.evaluate(async()=>{
      const sample=voiceRecorder.sample();const data=Array.from(new Uint8Array(await sample.file.arrayBuffer()));
      return {name:sample.file.name,type:sample.file.type,text:sample.prompt,auxiliary:sample.auxiliary.length,duration:sample.duration,data};
    });
    assert.equal(sample.type,'audio/wav');assert.equal(sample.text,input.text);assert.equal(sample.auxiliary,0);
    assert.ok(sample.duration>=3&&sample.duration<=10);
    fs.writeFileSync(path.join(__dirname,'recorded-microphone.wav'),Buffer.from(sample.data));
    assert.equal(await page.locator('#recordPreview').isVisible(),true);
    assert.ok(await page.evaluate(()=>window.testStreams.every(s=>s.getTracks().every(t=>t.readyState==='ended'))));
    await page.fill('#voiceName','麦克风验收临时音色');
    await page.locator('#cloneCapture').screenshot({path:path.join(__dirname,'microphone.png')});
    report.checks.push('recording converts to WAV, includes exact read-along transcript, supports playback and releases microphone');
    const analyzePromise=page.waitForResponse(r=>r.url().endsWith('/voices/analyze'));
    await page.click('#analyzeVoice');const analyzed=await analyzePromise;assert.equal(analyzed.status(),200);
    report.sampleQuality=(await analyzed.json()).quality.status;
    const clonePromise=page.waitForResponse(r=>r.url().endsWith('/voices/clone'),{timeout:60000});
    await page.click('#clone');const cloned=await clonePromise;assert.equal(cloned.status(),200);
    const result=await cloned.json();createdId=result.id;
    assert.equal(result.quality.status,'ready');
    await page.waitForFunction(id=>document.querySelector('#voice')?.value===id&&document.querySelector('#voice').selectedOptions[0]?.disabled===false,createdId,{timeout:90000});
    report.checks.push('recorded WAV and automatic transcript create a real clone, complete warmup/calibration and select it');
    await page.fill('#voicePreviewText','大家好，欢迎来到直播间。');
    const previewPromise=page.waitForResponse(r=>r.url().endsWith('/tts/synthesize'),{timeout:120000});
    await page.click('#previewVoice');const preview=await previewPromise;assert.equal(preview.status(),200);
    assert.equal(preview.request().postDataJSON().voice_id,createdId);
    assert.ok((await preview.body()).length>32000);await page.click('#stopPreview');
    report.checks.push('microphone-created clone generates usable preview audio through the existing GPT-SoVITS path');
    await page.click('#captureRecordTab');await page.click('#recordStart');
    await page.waitForFunction(()=>document.querySelector('#recordStatus').textContent.startsWith('正在录音'));
    await page.click('[data-view="knowledge"]');await page.waitForSelector('#batchTools');
    assert.ok(await page.evaluate(()=>window.testStreams.every(s=>s.getTracks().every(t=>t.readyState==='ended'))));
    report.checks.push('leaving the studio stops the microphone');
    assert.deepEqual(report.errors,[]);report.passed=true;
  }catch(error){report.failure=error.stack;throw error;}
  finally{
    if(createdId&&page){const r=await page.request.delete('http://127.0.0.1:8000/api/voices/'+createdId);report.temporaryCloneRemoved=r.status()===200;}
    fs.writeFileSync(path.join(__dirname,'microphone-report.json'),JSON.stringify(report,null,2));
    await browser.close();console.log(JSON.stringify(report));
  }
})().catch(error=>{console.error(error);process.exitCode=1;});
