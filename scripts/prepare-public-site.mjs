import { copyFileSync, existsSync, lstatSync, mkdirSync, readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const output = join(root, '.public-site');
const files = ['index.html', 'dashboard.html', 'models.html', 'about.html', 'app.js', 'styles.css'];
const configPath = join(root, 'deploy', 'public.staticwebapp.config.json');

// Fail closed: never copy the repository root, backend, symlinks or stale output.
if (existsSync(output)) throw new Error('Output already exists; use a fresh checkout or remove only .public-site before repackaging.');
for (const directory of ['frontend', 'deploy']) {
  const stat = lstatSync(join(root, directory));
  if (stat.isSymbolicLink() || !stat.isDirectory()) throw new Error(`Unsafe source directory: ${directory}`);
}
const sources = [...files.map(file => join(root, 'frontend', file)), configPath];
for (const source of sources) {
  const stat = lstatSync(source);
  if (stat.isSymbolicLink() || !stat.isFile()) throw new Error(`Unsafe source file: ${source}`);
}
const config = JSON.parse(readFileSync(configPath, 'utf8'));
for (const route of ['/admin*', '/api*', '/backend*', '/.auth/login/aad', '/.auth/login/github', '/.auth*']) {
  if (!config.routes?.some(rule => rule.route === route && rule.statusCode === 404)) {
    throw new Error(`Missing deny rule: ${route}`);
  }
}
if (config.auth || config.navigationFallback) throw new Error('No custom auth or fallback exposure permitted.');
mkdirSync(output);
for (const file of files) copyFileSync(join(root, 'frontend', file), join(output, file));
copyFileSync(configPath, join(output, 'staticwebapp.config.json'));
console.log(`Prepared ${files.length} frontend files plus public configuration. Backend and AI repair are excluded.`);