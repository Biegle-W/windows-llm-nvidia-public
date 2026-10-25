// Test DSH Desktop's installed streaming SDK without printing the private key.
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const {pathToFileURL} = require('node:url');
(async () => {
  const root = path.resolve(__dirname, '..');
  const {provider, defaultModel} = JSON.parse(fs.readFileSync(path.join(root,'config/harness-provider.json'),'utf8'));
  const target=process.argv[2] || defaultModel;
  if (!provider.models.some(m => m.id === target)) throw new Error('Unknown model');
  const apiKey = fs.readFileSync(path.join(root,'data/credentials/.local-api-key'),'utf8').trim();
  const install = [process.env.LOCALAPPDATA, path.join(os.homedir(), 'AppData/Local')]
    .filter(Boolean).map(base => path.join(base,'Programs/DeepSeek Harness'))
    .find(base => fs.existsSync(path.join(base,'resources/app.asar')));
  if (!install) throw new Error('DSH Desktop installation unavailable');
  const modules = path.join(install,'resources/app.asar/dsh/node_modules');
  const {openAICompletionsApi} = await import(pathToFileURL(path.join(modules,'@earendil-works/pi-ai/dist/api/openai-completions.lazy.js')).href);
  const model = {...provider.models.find(m => m.id === target), provider:'llamacpp', api:provider.api,
    baseUrl:provider.baseURL, reasoning:false, compat:provider.compat,
    cost:{input:0,output:0,cacheRead:0,cacheWrite:0}};
  const stream = openAICompletionsApi().stream(model,{messages:[{
    role:'user',content:'Reply with exactly WINDOWS_NVIDIA_CONNECTED.',timestamp:Date.now()}]},
    {apiKey,maxTokens:2048,temperature:0.1,signal:AbortSignal.timeout(300000)});
  const result = await stream.result();
  const answer = (result.content || []).filter(x => x.type === 'text').map(x => x.text).join('');
  const passed=result.stopReason !== 'error' && answer.includes('WINDOWS_NVIDIA_CONNECTED');
  const report={passed,checkedAt:new Date().toISOString(),client:'DSH Desktop bundled pi-ai',provider:'llamacpp',
    model:target,response:answer,usage:result.usage,stopReason:result.stopReason,
    error:result.errorMessage ? result.errorMessage.split(apiKey).join('[redacted]') : undefined};
  fs.writeFileSync(path.join(root,`reports/verification/router-dsh-${target}-20261023.json`),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report));
  if (!passed) throw new Error('Streaming check failed');
})().catch(() => {console.error('DSH streaming verification failed; no private settings logged.'); process.exitCode=1;});
