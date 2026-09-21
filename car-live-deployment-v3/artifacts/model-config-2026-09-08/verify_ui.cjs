const {chromium}=require('C:/Users/seele/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
 const report={errors:[],checks:[]};let page,original;
 try{
  page=await browser.newPage({viewport:{width:1480,height:980}});page.on('pageerror',e=>report.errors.push(e.message));
  const get=async()=>{const r=await page.request.get('http://127.0.0.1:8000/api/llm/config');assert.equal(r.status(),200);return r.json();};
  original=await get();
  await page.goto('http://127.0.0.1:5173');await page.click('[data-view="model"]');await page.waitForSelector('#modelConfigForm');
  assert.equal(await page.inputValue('#llmBaseUrl'),original.base_url);
  assert.equal(await page.inputValue('#llmModel'),original.model);
  assert.equal(await page.inputValue('#llmApiKey'),'');assert.equal(await page.getAttribute('#llmApiKey','type'),'password');
  report.checks.push('current configuration loads, existing key is not returned or populated');
  const nextTimeout=original.timeout_seconds===120?119:original.timeout_seconds+1;
  await page.fill('#llmTimeout',String(nextTimeout));await page.click('#saveModel');
  await page.waitForFunction(()=>document.querySelector('#modelResult').textContent==='配置已保存并生效。');
  const updated=await get();assert.equal(updated.timeout_seconds,nextTimeout);assert.equal(updated.api_key_configured,original.api_key_configured);
  report.checks.push('UI save applies immediately and preserves existing key');
  await page.reload();await page.click('[data-view="model"]');await page.waitForSelector('#modelConfigForm');
  assert.equal(await page.inputValue('#llmTimeout'),String(nextTimeout));assert.equal(await page.inputValue('#llmApiKey'),'');
  report.checks.push('page reload retains saved fields');
  await page.route('**/api/llm/config',route=>route.request().method()==='PUT'?route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'验收模拟：文件暂不可写'})}):route.continue());
  await page.fill('#llmTimeout',String(original.timeout_seconds));await page.click('#saveModel');
  await page.waitForFunction(()=>document.querySelector('#modelResult').textContent.includes('文件暂不可写'));
  assert.equal((await get()).timeout_seconds,nextTimeout);assert.equal(await page.locator('#saveModel').isEnabled(),true);
  await page.unroute('**/api/llm/config');report.checks.push('failed save keeps current configuration and enables retry');
  await page.click('#probeModel');await page.waitForFunction(()=>document.querySelector('#modelConnectionState').textContent==='连接成功',null,{timeout:30000});
  assert.equal((await get()).timeout_seconds,original.timeout_seconds);
  await page.screenshot({path:path.join(__dirname,'model-config.png'),fullPage:true});
  report.checks.push('save-and-test succeeds against configured model, original timeout restored');
  const response=await page.request.post('http://127.0.0.1:8000/api/query',{data:{question:'这款车的CLTC纯电续航是多少公里？',brand:'欧拉',series:'欧拉5 EV',year:'2026'},timeout:30000});
  const answer=await response.json();assert.equal(response.status(),200);assert.equal(answer.provider,'llm-grounded-rag');assert.match(answer.answer,/580/);
  report.query={provider:answer.provider,latency_ms:answer.latency_ms};
  const leaks=await page.evaluate(()=>Object.keys(localStorage).some(k=>/llm|api.?key|secret/i.test(k))||Object.keys(sessionStorage).some(k=>/llm|api.?key|secret/i.test(k)));
  assert.equal(leaks,false);assert.deepEqual(report.errors,[]);report.passed=true;
 }catch(e){report.failure=e.stack;throw e;}finally{
  if(page&&original){await page.unroute('**/api/llm/config');const restored=await page.request.put('http://127.0.0.1:8000/api/llm/config',{data:{base_url:original.base_url,model:original.model,timeout_seconds:original.timeout_seconds}});report.restored=restored.status()===200;}
  fs.writeFileSync(path.join(__dirname,'report.json'),JSON.stringify(report,null,2));await browser.close();console.log(JSON.stringify(report));
 }
})().catch(e=>{console.error(e);process.exitCode=1;});
