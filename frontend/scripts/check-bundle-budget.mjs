import { readdir, stat, readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const manifestPath = new URL('../dist/.vite/manifest.json', import.meta.url);
const entryPath = new URL('../dist/index.html', import.meta.url);
const initialJsBudget = 650 * 1024;
const initialCssBudget = 220 * 1024;

const html = await readFile(entryPath, 'utf8');
const referencedAssets = [...html.matchAll(/(?:src|href)="(\/assets\/[^"?#]+)"/g)].map(
  ([, asset]) => asset,
);

const files = await readdir(new URL('../dist/assets/', import.meta.url), { recursive: true });
const assetSizes = new Map();
for (const relative of files) {
  const fullPath = join(fileURLToPath(new URL('../dist/assets/', import.meta.url)), relative);
  const fileStat = await stat(fullPath);
  if (fileStat.isFile()) {
    assetSizes.set(`/assets/${relative.replaceAll('\\', '/')}`, fileStat.size);
  }
}

const initialAssets = referencedAssets
  .map((asset) => ({ asset, size: assetSizes.get(asset) ?? 0 }))
  .filter(({ size }) => size > 0);
const initialJs = initialAssets
  .filter(({ asset }) => asset.endsWith('.js'))
  .reduce((total, { size }) => total + size, 0);
const initialCss = initialAssets
  .filter(({ asset }) => asset.endsWith('.css'))
  .reduce((total, { size }) => total + size, 0);

console.log(`Initial assets: ${initialAssets.length}`);
console.log(`Initial JavaScript: ${(initialJs / 1024).toFixed(1)} KiB (budget ${(initialJsBudget / 1024).toFixed(0)} KiB)`);
console.log(`Initial CSS: ${(initialCss / 1024).toFixed(1)} KiB (budget ${(initialCssBudget / 1024).toFixed(0)} KiB)`);

if (initialJs > initialJsBudget || initialCss > initialCssBudget) {
  throw new Error('Initial bundle budget exceeded');
}

try {
  await stat(manifestPath);
  console.log('Build manifest: present');
} catch {
  throw new Error('Build manifest missing');
}

console.log(`Assets scanned: ${assetSizes.size}`);
