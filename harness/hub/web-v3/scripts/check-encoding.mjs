// Fails the build when source text is mojibake — UTF-8 bytes that were read
// back as cp1252 and re-saved, turning "GIÁM SÁT" into "GIÃƒÆ’Ã‚ÂM SÃƒÆ’Ã‚ÂT".
// tsc and vite never catch this: mangled text is still a valid string.
//
// Detection uses the one property that separates the two cases: correctly
// encoded Vietnamese cannot be encoded to cp1252 at all, while mojibake round
// trips back to clean UTF-8. So a run that survives the trip was mojibake.
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = fileURLToPath(new URL("../src/", import.meta.url));
const EXTS = new Set([".tsx", ".ts", ".css", ".html"]);

// cp1252 differs from latin-1 only in 0x80-0x9F. Undefined slots are left null:
// 0x81/0x8D/0x8F/0x90/0x9D have no character, yet those bytes really do occur
// inside the mojibake of Đ and Á, so they are handled by the <= 0xFF fallback.
const CP1252_HIGH = "€‚ƒ„…†‡ˆ‰Š‹ŒŽ‘’“”•–—˜™š›œžŸ";
const TO_BYTE = new Map();
for (let i = 0; i < CP1252_HIGH.length; i++) TO_BYTE.set(CP1252_HIGH[i], 0x80 + i);

const utf8 = new TextDecoder("utf-8", { fatal: true });

/** Reverse one mojibake layer, or null when the run is not mojibake. */
function unwrap(run) {
  const bytes = [];
  for (const ch of run) {
    const mapped = TO_BYTE.get(ch);
    if (mapped !== undefined) bytes.push(mapped);
    else if (ch.codePointAt(0) <= 0xff) bytes.push(ch.codePointAt(0));
    else return null;
  }
  try {
    return utf8.decode(new Uint8Array(bytes));
  } catch {
    return null;
  }
}

function walk(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) walk(path, out);
    else if (EXTS.has(path.slice(path.lastIndexOf(".")))) out.push(path);
  }
  return out;
}

let bad = 0;
for (const path of walk(ROOT)) {
  const text = readFileSync(path, "utf8");
  const lines = text.split(/\r?\n/);
  lines.forEach((line, i) => {
    for (const [run] of line.matchAll(/[^\x00-\x7F]+/g)) {
      const fixed = unwrap(run);
      if (fixed === null || fixed === run) continue;
      bad++;
      if (bad <= 20) {
        console.error(`${relative(ROOT, path)}:${i + 1}  ${JSON.stringify(run)} should be ${JSON.stringify(fixed)}`);
      }
    }
  });
}

if (bad) {
  console.error(`\n${bad} mangled text run(s). Repair the source encoding before building.`);
  process.exit(1);
}
console.log("encoding ok");
