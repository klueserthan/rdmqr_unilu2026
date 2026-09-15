// Print a reveal.js HTML deck to PDF via Chrome DevTools Protocol, honouring
// reveal's CSS @page size (the plain --print-to-pdf CLI flag falls back to Letter).
// Usage: node reveal_to_pdf.mjs <deck.html> <out.pdf>
import { spawn } from "node:child_process";
import { writeFileSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const [html, out] = process.argv.slice(2);
if (!html || !out) { console.error("usage: node reveal_to_pdf.mjs deck.html out.pdf"); process.exit(2); }
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const PORT = 9333;
const profile = mkdtempSync(join(tmpdir(), "reveal-pdf-"));
const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu", `--remote-debugging-port=${PORT}`,
  `--user-data-dir=${profile}`, "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const bail = (msg) => { console.error(msg); chrome.kill(); process.exit(1); };
setTimeout(() => bail("timeout after 120s"), 120_000).unref();

let target;
for (let i = 0; i < 50 && !target; i++) {
  try { target = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find((t) => t.type === "page"); }
  catch { await sleep(200); }
}
if (!target) bail("Chrome did not start");

const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
let id = 0; const pending = new Map(); const events = [];
ws.onmessage = (m) => {
  const msg = JSON.parse(m.data);
  if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
  else if (msg.method) events.push(msg.method);
};
const send = (method, params = {}) => new Promise((r) => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });

await send("Page.enable");
await send("Page.navigate", { url: "file://" + resolve(html) + "?print-pdf" });
for (let i = 0; i < 300 && !events.includes("Page.loadEventFired"); i++) await sleep(100);
// wait until reveal has laid out its print pages
let pages = 0;
for (let i = 0; i < 60; i++) {
  const r = await send("Runtime.evaluate", { expression: "document.querySelectorAll('.pdf-page').length", returnByValue: true });
  pages = r.result?.result?.value ?? 0;
  if (pages > 0) break;
  await sleep(500);
}
if (!pages) bail("reveal print layout never appeared");
await sleep(3000); // fonts, images, plots

const res = await send("Page.printToPDF", { printBackground: true, preferCSSPageSize: true,
  marginTop: 0, marginBottom: 0, marginLeft: 0, marginRight: 0 });
if (!res.result?.data) bail("printToPDF failed: " + JSON.stringify(res.error));
writeFileSync(out, Buffer.from(res.result.data, "base64"));
console.log(`wrote ${out} (${pages} reveal pages)`);
ws.close(); chrome.kill(); process.exit(0);
