/** Assert the owner's hard rules on a page: badge aspect, stacked cards, nothing over an image. */
import {spawn} from 'node:child_process';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const input = process.argv[2];
const isUrl = /^https?:\/\//.test(input);
const child = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  ['--headless=new','--disable-gpu','--no-first-run','--remote-debugging-port=9336',
   '--user-data-dir=/tmp/claude-501/rules-profile','about:blank'], {stdio:['ignore','ignore','ignore']});
const wait = ms => new Promise(r => setTimeout(r, ms));
let list=null; for (let i=0;i<30&&!list;i++){await wait(1000); try{list=await (await fetch('http://127.0.0.1:9336/json/list')).json();}catch{list=null;}}
const ws=new WebSocket(list.find(t=>t.type==='page').webSocketDebuggerUrl);
await new Promise(r=>ws.addEventListener('open',r));
let seq=0; const pending=new Map();
ws.addEventListener('message', e=>{const m=JSON.parse(e.data); if(m.id&&pending.has(m.id)){pending.get(m.id)(m.result);pending.delete(m.id);}});
const send=(method,params={})=>new Promise(res=>{const id=++seq;pending.set(id,res);ws.send(JSON.stringify({id,method,params}));});
await send('Page.enable'); await send('Runtime.enable');
await send('Page.navigate',{url: isUrl ? input : pathToFileURL(path.resolve(input)).href});
await wait(6000);
const res = await send('Runtime.evaluate',{returnByValue:true,expression:`(() => {
  const badges = [...document.querySelectorAll(".badges img")];
  const distorted = badges.filter(i => i.naturalWidth > 0 &&
    Math.abs(i.width / i.height - i.naturalWidth / i.naturalHeight) > 0.02)
    .map(i => i.alt + " rendered " + i.width + "x" + i.height + " natural " + i.naturalWidth + "x" + i.naturalHeight);
  const overlaid = [...document.querySelectorAll(".capture-stage *")]
    .filter(el => getComputedStyle(el).position === "absolute").map(el => el.className);
  const gridCards = [...document.querySelectorAll(".project-card")]
    .filter(c => getComputedStyle(c).display === "grid").length;
  return {badges: badges.length, distorted, overlaid, gridCards,
    withWidthAttr: badges.filter(i => i.hasAttribute("width")).length};
})()`});
console.log(JSON.stringify(res.result.value, null, 1));
ws.close(); child.kill('SIGTERM');
