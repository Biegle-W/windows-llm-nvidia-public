// Run through DSH Desktop's Electron with ELECTRON_RUN_AS_NODE=1.
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const {pathToFileURL} = require('node:url');
const {isDeepStrictEqual} = require('node:util');

(async () => {
  const root = path.resolve(__dirname, '..');
  const install = [process.env.LOCALAPPDATA, path.join(os.homedir(), 'AppData/Local')]
    .filter(Boolean).map(base => path.join(base,'Programs/DeepSeek Harness'))
    .find(base => fs.existsSync(path.join(base,'resources/app.asar')));
  if (!install) throw new Error('DSH Desktop installation unavailable');
  const modules = path.join(install, 'resources/app.asar/dsh/node_modules');
  const load = name => import(pathToFileURL(path.join(modules, name)).href);
  const {parseDocument} = await load('yaml/dist/index.js');
  const {withFileLock, writeFileAtomic} = await load('@deepseek-ai/dsh-atomic-write/lib/index.js');
  const filename = path.join(process.env.USERPROFILE, '.dsh/profiles/desktop/cordis.patch.yml');
  const desired = JSON.parse(fs.readFileSync(path.join(root, 'config/harness-provider.json'), 'utf8'));
  if (!desired.provider.models.length || !desired.defaultModel) throw new Error('Register a Windows model first');
  const key = fs.readFileSync(path.join(root, 'data/credentials/.local-api-key'), 'utf8').trim();
  const response = await fetch(desired.provider.baseURL + '/models', {
    headers: {Authorization: 'Bearer ' + key}, signal: AbortSignal.timeout(5000)});
  if (!response.ok) throw new Error('Backend catalog unavailable');
  const models = (await response.json()).data.map(m => m.id).sort();
  if (!isDeepStrictEqual(models, desired.provider.models.map(m => m.id).sort())) throw new Error('Catalog mismatch');
  await withFileLock(filename, async () => {
    const original = fs.readFileSync(filename, 'utf8');
    const doc = parseDocument(original);
    if (doc.errors.length) throw new Error('Invalid desktop YAML');
    const expected = structuredClone(doc.toJS());
    const indexes = name => expected.map((e,i) => e.name === name ? i : -1).filter(i => i >= 0);
    const providers = indexes('@deepseek-ai/dsh-llm-pi-ai');
    const defaults = indexes('@deepseek-ai/dsh-agent-default-model');
    if (providers.length !== 1 || defaults.length !== 1) throw new Error('Unexpected desktop layout');
    const p = providers[0], d = defaults[0];
    const existing = expected[p].config.providers.llamacpp || {...desired.provider};
    // Retain credential routing and all unrelated provider options.
    const updated = {...existing, displayName: desired.provider.displayName,
      baseURL: desired.provider.baseURL, models: desired.provider.models,
      compat: {...existing.compat, ...desired.provider.compat}};
    // Thinking is model-specific; LFM requires its reasoning template.
    delete updated.compat.chatTemplateKwargs;
    expected[p].config.providers.llamacpp = updated;
    doc.setIn([p,'config','providers','llamacpp'], updated);
    const strata = JSON.parse(fs.readFileSync(path.join(root,'config/strata.json'), 'utf8'));
    if (strata.enabled === false) {
      const old = expected[p].config.providers['strata-q3'];
      if (old && old.models.some(m => m.id !== 'qwen3.8-flash-next-iq3_xxs')) throw new Error('Unrelated Strata models');
      delete expected[p].config.providers['strata-q3'];
      doc.deleteIn([p,'config','providers','strata-q3']);
    }
    expected[d].config.provider = 'llamacpp'; expected[d].config.model = desired.defaultModel;
    doc.setIn([d,'config','provider'], 'llamacpp'); doc.setIn([d,'config','model'], desired.defaultModel);
    const next = doc.toString();
    if (!isDeepStrictEqual(parseDocument(next).toJS(), expected)) throw new Error('Unexpected settings change');
    if (next !== original) {
      fs.copyFileSync(filename, filename + '.before-windows-nvidia-' + Date.now());
      await writeFileAtomic(filename, next, {mode:0o600, dirMode:0o700});
    }
    console.log(JSON.stringify({passed:true, provider:'llamacpp', models, defaultModel:desired.defaultModel,
      strataDeferred:strata.enabled === false, unrelatedSettingsPreserved:true}));
  }, {waitMs:30000});
})().catch(() => {console.error('Desktop catalog update failed; no private settings logged.'); process.exitCode=1;});
