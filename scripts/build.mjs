import { cp, mkdir, readFile, readdir, rm, stat } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const output = path.join(root, 'dist');
const files = ['index.html', 'work.html'];
const directories = ['assets', 'work'];

for (const file of files) {
  const html = await readFile(path.join(root, file), 'utf8');
  if (!html.includes('Аполлинария Пилипюк')) throw new Error(`Unexpected page: ${file}`);
}
await rm(output, { recursive: true, force: true });
await mkdir(output, { recursive: true });
for (const entry of [...files, ...directories]) {
  await cp(path.join(root, entry), path.join(output, entry), {
    recursive: true,
    filter: source => !['.DS_Store', '__pycache__'].includes(path.basename(source)),
  });
}

// Check deployed HTML references, including assets on nested project pages.
const pages = [...files, ...(await readdir(path.join(output, 'work')))
  .filter(file => file.endsWith('.html')).map(file => `work/${file}`)];
for (const page of pages) {
  const html = await readFile(path.join(output, page), 'utf8');
  for (const match of html.matchAll(/(?:src|href)="(\/[^"]*)"/g)) {
    const asset = match[1].split(/[?#]/)[0];
    if (!(await stat(path.join(output, asset))).isFile()) {
      throw new Error(`Missing asset ${asset} in ${page}`);
    }
  }
}
console.log(`Built ${pages.length} pages and all portfolio assets into dist/.`);
