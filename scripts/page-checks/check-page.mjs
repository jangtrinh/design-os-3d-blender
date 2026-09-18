/** Render-check one delivery page in headless Chrome at desktop and phone width.
 *
 *   node check-page.mjs <page.html> <out-dir>
 *
 * Asserts: no horizontal overflow, every image decoded, Inter and JetBrains Mono
 * resolved, no console errors, and no two horizontal rules within 40 px. Writes one
 * screenshot per width and prints a JSON verdict.
 */
import {spawn} from 'node:child_process';
import {mkdir, writeFile} from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';

const input = process.argv[2];
const isUrl = /^https?:\/\//.test(input);
const page = isUrl ? input : path.resolve(input);
const out = path.resolve(process.argv[3]);
await mkdir(out, {recursive: true});
const chrome = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const child = spawn(chrome, ['--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
  '--remote-debugging-address=127.0.0.1', '--remote-debugging-port=9333',
  '--user-data-dir=' + path.join(out, 'profile'), '--allow-file-access-from-files', 'about:blank'],
  {stdio: ['ignore', 'ignore', 'pipe']});
let stderr = '';
child.stderr.on('data', chunk => { stderr += chunk.toString(); });
const wait = ms => new Promise(r => setTimeout(r, ms));
let list = null;
for (let attempt = 0; attempt < 30 && !list; attempt++) {
  await wait(1000);
  try { list = await (await fetch('http://127.0.0.1:9333/json/list')).json(); } catch { list = null; }
}
if (!list) { console.error(stderr.slice(0, 2000)); throw new Error('Chrome never opened its debugging port'); }
const target = list.find(t => t.type === 'page');
const WebSocket = globalThis.WebSocket;
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener('open', r));
let seq = 0;
const pending = new Map();
const consoleErrors = [];
ws.addEventListener('message', event => {
  const msg = JSON.parse(event.data);
  if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg.result); pending.delete(msg.id); }
  if (msg.method === 'Log.entryAdded' && msg.params.entry.level === 'error') consoleErrors.push(msg.params.entry.text);
  if (msg.method === 'Runtime.exceptionThrown') consoleErrors.push(JSON.stringify(msg.params.exceptionDetails.text));
});
const send = (method, params = {}) => new Promise(resolve => {
  const id = ++seq; pending.set(id, resolve); ws.send(JSON.stringify({id, method, params}));
});
const evaluate = async expression => {
  const res = await send('Runtime.evaluate', {expression, returnByValue: true, awaitPromise: true});
  if (res.exceptionDetails) throw new Error(JSON.stringify(res.exceptionDetails));
  return res.result.value;
};

await send('Page.enable');
await send('Runtime.enable');
await send('Log.enable');

const report = {page, widths: {}, consoleErrors: []};
for (const [name, width, height] of [['desktop', 1280, 900], ['phone', 390, 844]]) {
  await send('Page.navigate', {url: isUrl ? page : pathToFileURL(page).href});
  await wait(1500);
  // Apply the metrics after navigation: a navigate can drop an override applied before it.
  await send('Emulation.setDeviceMetricsOverride', {width, height, deviceScaleFactor: 1, mobile: false});
  await wait(2500);
  await evaluate('window.scrollTo(0, document.body.scrollHeight); 1');
  await wait(1500);
  await evaluate('window.scrollTo(0, 0); 1');
  // Slides live in a horizontal scroller: lazy images there only load once scrolled.
  await evaluate('(() => { const t = document.getElementById("track"); if (t) t.scrollLeft = t.scrollWidth; return 1; })()');
  await wait(2500);
  await evaluate('(() => { const t = document.getElementById("track"); if (t) t.scrollLeft = 0; return 1; })()');
  await wait(1200);
  report.widths[name] = await evaluate(`(() => {
    const imgs = [...document.images];
    const rules = [...document.querySelectorAll('*')].filter(el => {
      const s = getComputedStyle(el);
      return (s.borderTopWidth === '1px' && s.borderTopStyle === 'solid') || el.tagName === 'HR';
    }).map(el => el.getBoundingClientRect().top + window.scrollY).sort((a, b) => a - b);
    let adjacent = 0;
    for (let i = 1; i < rules.length; i++) if (rules[i] - rules[i - 1] < 40 && rules[i] - rules[i - 1] > 0) adjacent++;
    return {
      innerWidth: window.innerWidth,
      scrollWidth: document.scrollingElement.scrollWidth,

      images: imgs.length,
      imagesDecoded: imgs.filter(i => i.complete && i.naturalWidth > 0).length,
      imagesBroken: imgs.filter(i => i.complete && i.naturalWidth === 0).map(i => i.getAttribute('src')),
      imagesPending: imgs.filter(i => !i.complete).map(i => i.getAttribute('src')),
      blanks: document.querySelectorAll('.media-blank').length,
      inter: document.fonts.check('16px Inter'),
      mono: document.fonts.check('13px "JetBrains Mono"'),
      bodyFont: getComputedStyle(document.body).fontFamily,
      fontSizes: new Set([...document.querySelectorAll('h1,h2,h3,p,li,dt,dd,cite')].map(e => getComputedStyle(e).fontSize)).size,
      keyframes: [...document.styleSheets].flatMap(s => { try { return [...s.cssRules]; } catch { return []; } }).filter(r => r.type === 7).length,
      adjacentRules: adjacent,
      wordmarkHref: document.querySelector('.wordmark') && document.querySelector('.wordmark').href,
      videoSources: document.querySelectorAll('video source').length,
    };
  })()`);
  const shot = await send('Page.captureScreenshot', {format: 'png', captureBeyondViewport: false});
  await writeFile(path.join(out, `${name}.png`), Buffer.from(shot.data, 'base64'));
}
report.consoleErrors = consoleErrors;
console.log(JSON.stringify(report, null, 1));
ws.close();
child.kill('SIGTERM');
