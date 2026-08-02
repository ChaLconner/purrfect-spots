import { readdir, readFile, writeFile } from 'node:fs/promises';
import { join, extname } from 'node:path';
import { brotliCompress, constants } from 'node:zlib';
import { promisify } from 'node:util';
import { fileURLToPath } from 'node:url';

const compress = promisify(brotliCompress);
const dist = fileURLToPath(new URL('../dist/', import.meta.url));
const textExtensions = new Set(['.js', '.mjs', '.css', '.json', '.webmanifest', '.html']);
// Emit a sibling for every text asset so nginx can safely set Content-Encoding
// whenever the client advertises Brotli, without a header/file mismatch.

async function collectFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await collectFiles(path)));
    } else if (entry.isFile()) {
      files.push(path);
    }
  }
  return files;
}

const files = await collectFiles(dist);
let compressedCount = 0;
for (const file of files) {
  if (!textExtensions.has(extname(file).toLowerCase())) continue;
  const compressed = await compress(await readFile(file), {
    params: {
      [constants.BROTLI_PARAM_QUALITY]: 5,
    },
  });
  await writeFile(`${file}.br`, compressed);
  compressedCount++;
}

console.log(`Brotli assets: ${compressedCount}`);
