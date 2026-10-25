// Verify a public Strata provider through DSH Desktop's bundled streaming client.
// Run with ELECTRON_RUN_AS_NODE=1 and the desktop Electron executable.
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');

(async () => {
  const root = path.resolve(__dirname, '..');
  if (JSON.parse(fs.readFileSync(path.join(root,'config/strata.json'),'utf8')).enabled === false) throw new Error('Strata is disabled on this Windows build');
  const catalog = process.argv[2] || 'strata-harness-provider.json';
  if (catalog !== 'strata-harness-provider.json') throw new Error('Unknown catalog');
  const modules = path.join(process.env.LOCALAPPDATA, 'Programs/DeepSeek Harness/resources/app.asar/dsh/node_modules');
  const {openAICompletionsApi} = await import(pathToFileURL(path.join(modules, '@earendil-works/pi-ai/dist/api/openai-completions.lazy.js')).href);
  const {provider, providerId} = JSON.parse(fs.readFileSync(path.join(root, 'config', catalog), 'utf8'));
  const health = await (await fetch(provider.baseURL.replace(/\/v1$/, '/health'), {signal: AbortSignal.timeout(5000)})).json();
  const props = await (await fetch(provider.baseURL.replace(/\/v1$/, '/props'), {signal: AbortSignal.timeout(5000)})).json();
  if (health.status !== 'ok' || health.model !== provider.models[0].id) throw new Error('Expected quant is not loaded');
  const model = {...provider.models[0], provider: providerId, api: provider.api, baseUrl: provider.baseURL,
    reasoning: false, cost: {input: 0, output: 0, cacheRead: 0, cacheWrite: 0}, compat: provider.compat};
  const context = {messages: [{role: 'user', content: 'Reply with exactly STRATA_CONNECTED.', timestamp: Date.now()}]};
  const stream = openAICompletionsApi().stream(model, context, {headers: provider.headers, maxTokens: 32, temperature: 0,
    signal: AbortSignal.timeout(90000)});
  const result = await stream.result();
  const answer = (result.content || []).filter(x => x.type === 'text').map(x => x.text).join('');
  if (result.stopReason === 'error' || !answer.includes('STRATA_CONNECTED')) throw new Error('Client did not complete expected response');
  const report = {passed: true, checkedAt: new Date().toISOString(), engine: props.build_info,
    client: 'DSH Desktop bundled pi-ai openai-completions', provider: providerId,
    model: model.id, baseURL: provider.baseURL, response: answer, stopReason: result.stopReason, usage: result.usage};
  fs.writeFileSync(path.join(root, 'reports/verification', `${providerId}-dsh-client-current.json`), JSON.stringify(report, null, 2));
  process.stdout.write(JSON.stringify(report) + '\n');
})().catch(() => {process.stderr.write('DSH Strata client verification failed; no private settings logged.\n'); process.exitCode = 1;});
