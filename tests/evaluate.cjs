(async () => {
// Evaluate through the real JS module loader. Optional checkout overrides are
// applied only to the in-memory test bundle, never to library source files.
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const workspace = path.resolve(process.env.FLATPPL_WORKSPACE || path.join(root, '..'));
const engine = require(path.join(process.env.FLATPPL_JS_DIR || path.join(workspace, 'flatppl-js'), 'packages/engine/index.ts'));
const request = JSON.parse(fs.readFileSync(0, 'utf8'));
const overrides = {};
for (const name of ['stats-templates', 'stats-counts']) {
  const variable = 'FLATPPL_' + name.toUpperCase().replaceAll('-', '_') + '_DIR';
  if (process.env[variable]) overrides[name] = path.resolve(process.env[variable]);
}
function applyOverrides(source) {
  for (const [name, checkout] of Object.entries(overrides)) {
    source = source.replaceAll(new RegExp('https://raw\\.githubusercontent\\.com/BJMCox/flatppl-' + name + '/[^/]+/main\\.flatppl', 'g'), path.join(checkout, 'main.flatppl'));
  }
  return source;
}
const expressions = Array.isArray(request) ? request : null;
const source = expressions ? 'flatppl_compat = "0.1"\na = load_module("../main.flatppl")\n'
  + expressions.map((expression, i) => `probe${i} = ${expression}`).join('\n') : request.source;
const primaryPath = path.join(__dirname, 'query.flatppl');
const bundle = await engine.resolveBundle(primaryPath, source, async filename => {
  if (filename.startsWith('https://')) {
    const response = await fetch(filename);
    if (!response.ok) throw new Error(`HTTP ${response.status} for ${filename}`);
    return applyOverrides(await response.text());
  }
  return applyOverrides(fs.readFileSync(filename, 'utf8'));
});
const model = engine.processSource(source, { path: primaryPath, bundle });
const errors = model.diagnostics.filter(d => d.severity === 'error');
if (errors.length) throw new Error(JSON.stringify(errors));
const result = engine.orchestrator.buildDerivations(model.linkedBindings, { moduleRegistry: model.linkedModuleRegistry });
const names = expressions ? expressions.map((_, i) => `probe${i}`) : request.bindings;
const { createWorkerHandler } = require(path.join(process.env.FLATPPL_JS_DIR || path.join(workspace, 'flatppl-js'), 'packages/engine/worker.ts'));
const worker = createWorkerHandler();
worker.handle({ type: 'init', seed: 47710 });
const ctx = { ...result, sampleCount: 1, rootKey: 47710, rootSeed: 47710, marginalizationCount: 64,
  sendWorker: async message => { const reply = await worker.handle(message); if (reply?.type === 'error') throw new Error(JSON.stringify(reply)); return reply; },
  getMeasure: name => engine.materialiser.materialiseMeasure(name, ctx) };
const values = await Promise.all(names.map(async name => {
  if (result.fixedValues.has(name)) return result.fixedValues.get(name);
  const measure = await ctx.getMeasure(name);
  return measure.samples[0];
}));
process.stdout.write(JSON.stringify(values));
})().catch(error => { console.error(error); process.exitCode = 1; });
