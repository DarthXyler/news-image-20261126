// Entry for make.fun's news-image-20261126: Thursday 26 November 2026's world news on one poster.
// The poster is built ahead of time by tools/make_poster.py and committed as entry.png; this program
// checks it against the contest's limits and puts those exact bytes in the output folder
// (no network, Node 22 standard library only, same bytes on every run).
//
// Locally: mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts

import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { crc32 } from 'node:zlib';

const MAX_BYTES = 1024 * 1024; // 1 MiB
const MAX_SIDE = 1024;
const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

function fail(msg: string): never {
  console.error(`entry.png rejected: ${msg}`);
  process.exit(1);
}

/** Walks every chunk: signature, IHDR first, each CRC valid, ends with IEND. Returns width/height. */
function checkPng(buf: Buffer): { width: number; height: number; chunks: number } {
  if (buf.length > MAX_BYTES) fail(`${buf.length} bytes, over ${MAX_BYTES}`);
  if (!buf.subarray(0, 8).equals(PNG_SIGNATURE)) fail('not a PNG signature');
  let off = 8;
  let width = 0;
  let height = 0;
  let chunks = 0;
  let sawEnd = false;
  while (off < buf.length) {
    if (off + 12 > buf.length) fail(`truncated chunk header at byte ${off}`);
    const len = buf.readUInt32BE(off);
    const type = buf.toString('latin1', off + 4, off + 8);
    const end = off + 12 + len;
    if (end > buf.length) fail(`chunk ${type} runs past the end of the file`);
    const want = buf.readUInt32BE(off + 8 + len);
    if (crc32(buf.subarray(off + 4, off + 8 + len)) !== want) fail(`bad CRC in chunk ${type}`);
    if (chunks === 0) {
      if (type !== 'IHDR') fail('first chunk is not IHDR');
      width = buf.readUInt32BE(off + 8);
      height = buf.readUInt32BE(off + 12);
    }
    chunks++;
    off = end;
    if (type === 'IEND') {
      sawEnd = true;
      break;
    }
  }
  if (!sawEnd) fail('no IEND chunk');
  if (off !== buf.length) fail(`${buf.length - off} stray bytes after IEND`);
  if (width < 1 || height < 1 || width > MAX_SIDE || height > MAX_SIDE) fail(`${width}x${height} is outside 1..${MAX_SIDE}`);
  return { width, height, chunks };
}

const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
const poster = readFileSync(new URL('./entry.png', import.meta.url));
const { width, height, chunks } = checkPng(poster);
mkdirSync(outDir, { recursive: true });
const target = join(outDir, 'entry.png');
writeFileSync(target, poster);
if (!readFileSync(target).equals(poster)) fail('written copy differs from entry.png');
console.log(`entry.png: ${width}x${height}, ${poster.length} bytes, ${chunks} chunks ok -> ${target}`);
