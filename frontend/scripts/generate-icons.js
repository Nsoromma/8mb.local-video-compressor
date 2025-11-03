/* eslint-disable no-console */
import fs from 'node:fs';
import path from 'node:path';

let sharp;
let pngToIco;
try {
  sharp = (await import('sharp')).default;
  pngToIco = (await import('png-to-ico')).default;
} catch (e) {
  console.log('[icons] Dependencies not available locally; skipping icon generation.');
  process.exit(0);
}

const root = path.resolve(process.cwd());
const staticDir = path.join(root, 'static');
const srcSvg = path.join(staticDir, 'favicon.svg');

async function ensureStatic() {
  if (!fs.existsSync(staticDir)) fs.mkdirSync(staticDir, { recursive: true });
}

async function makePng(size, dest) {
  const svg = fs.readFileSync(srcSvg);
  const buf = await sharp(svg)
    .resize(size, size, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
    .png()
    .toBuffer();
  fs.writeFileSync(dest, buf);
  return dest;
}

async function main() {
  await ensureStatic();
  if (!fs.existsSync(srcSvg)) {
    console.error('Missing static/favicon.svg; cannot generate raster icons.');
    process.exit(0);
  }

  const out16 = path.join(staticDir, 'favicon-16x16.png');
  const out32 = path.join(staticDir, 'favicon-32x32.png');
  const out180 = path.join(staticDir, 'apple-touch-icon.png'); // 180x180
  const out192 = path.join(staticDir, 'android-chrome-192x192.png');
  const out512 = path.join(staticDir, 'android-chrome-512x512.png');

  console.log('Generating PNG favicons from SVG...');
  await makePng(16, out16);
  await makePng(32, out32);
  await makePng(180, out180);
  await makePng(192, out192);
  await makePng(512, out512);

  console.log('Generating favicon.ico...');
  const icoBuf = await pngToIco([out16, out32]);
  fs.writeFileSync(path.join(staticDir, 'favicon.ico'), icoBuf);

  console.log('Icon generation complete.');
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
