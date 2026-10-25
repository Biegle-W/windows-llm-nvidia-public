// Run with DSH Desktop's Electron executable and ELECTRON_RUN_AS_NODE=1.
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {isDeepStrictEqual} = require('node:util');

(async () => {
  const root = path.resolve(__dirname, '..');
  if (JSON.parse(fs.readFileSync(path.join(root, 'config/strata.json'), 'utf8')).enabled === false) {
    throw new Error('Strata is disabled on this Windows build; check config/strata.json');
  }
  const modules = path.join(process.env.LOCALAPPDATA, 'Programs/DeepSeek Harness/resources/app.asar/dsh/node_modules');
  const load = name => import(pathToFileURL(path.join(modules, name)).href);
  const {parseDocument} = await load('yaml/dist/index.js');
  const {withFileLock, writeFileAtomic} = await load('@deepseek-ai/dsh-atomic-write/lib/index.js');
  const filename = path.join(process.env.USERPROFILE, '.dsh/profiles/desktop/cordis.patch.yml');
  const catalog = process.argv[2] || 'strata-harness-provider.json';
  if (catalog !== 'strata-harness-provider.json') throw new Error('Unknown provider catalog');
  const desired = JSON.parse(fs.readFileSync(path.join(root, 'config', catalog), 'utf8'));
  const setDefault = desired.selectAsDefault !== false;
  const health = await (await fetch(desired.provider.baseURL.replace(/\/v1$/, '/health'), {signal: AbortSignal.timeout(5000)})).json();
  if (health.status !== 'ok' || health.model !== desired.defaultModel) throw new Error('Strata is not ready');
  await withFileLock(filename, async () => {
    const original = fs.readFileSync(filename, 'utf8');
    const doc = parseDocument(original);
    if (doc.errors.length) throw new Error('Invalid desktop YAML');
    const before = doc.toJS();
    const expected = structuredClone(before);
    const providers = expected.map((entry, i) => entry.name === '@deepseek-ai/dsh-llm-pi-ai' ? i : -1).filter(i => i >= 0);
    const defaults = expected.map((entry, i) => entry.name === '@deepseek-ai/dsh-agent-default-model' ? i : -1).filter(i => i >= 0);
    if (providers.length !== 1 || defaults.length !== 1) throw new Error('Unexpected desktop profile layout');
    const p = providers[0], d = defaults[0];
    for (const [id, model] of Object.entries(desired.retiredProviders || {})) {
      const existing = expected[p].config.providers[id];
      if (existing && (!existing.models?.length || existing.models.some(entry => entry.id !== model))) {
        throw new Error('Retired provider contains unrelated models');
      }
      delete expected[p].config.providers[id];
      doc.deleteIn([p, 'config', 'providers', id]);
    }
    expected[p].config.providers[desired.providerId] = desired.provider;
    if (setDefault) {
      expected[d].config.provider = desired.providerId;
      expected[d].config.model = desired.defaultModel;
    }
    doc.setIn([p, 'config', 'providers', desired.providerId], desired.provider);
    if (setDefault) {
      doc.setIn([d, 'config', 'provider'], desired.providerId);
      doc.setIn([d, 'config', 'model'], desired.defaultModel);
    }
    const next = doc.toString();
    const parsed = parseDocument(next);
    if (parsed.errors.length || !isDeepStrictEqual(parsed.toJS(), expected)) throw new Error('Unexpected settings change');
    if (next !== original) {
      fs.copyFileSync(filename, filename + '.before-strata-' + Date.now());
      await writeFileAtomic(filename, next, {mode: 0o600, dirMode: 0o700});
    }
    console.log(JSON.stringify({provider: desired.providerId, model: desired.defaultModel,
      baseURL: desired.provider.baseURL, selectedAsDefault: setDefault,
      retiredProviders: Object.keys(desired.retiredProviders || {}), unrelatedSettingsPreserved: true}));
  }, {waitMs: 30000});
})().catch(() => { console.error('DSH Strata configuration failed; no private settings logged.'); process.exitCode = 1; });
