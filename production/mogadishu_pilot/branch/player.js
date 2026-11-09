// 分支播放器：按 graph.js 的节点图播放片段。两个 <video> 交替做无缝衔接与交叉淡化；
// 选择节点播放等待循环镜头（首尾交叉淡化，画面不冻结），倒计时结束按默认项继续；BGM 独立于片段连续播放。
const G = window.GRAPH;
const vids = [document.querySelector("#v0"), document.querySelector("#v1")];
const veil = document.querySelector("#veil");
const panel = document.querySelector("#panel");
const note = document.querySelector("#note");
const statusLine = document.querySelector("#status");
const bgm = document.querySelector("#bgm");
const FADE = 0.45;
// BGM 电平：clips/narr.js 给出各片段旁白时段，旁白期间把 BGM 再压低（与线性版 build_clips.py 的混音一致）
const NARR = window.NARR || {};
const MIX = NARR._mix || { gain: 0.16, duck: 0.45, in: 0.4, out: 0.8 };

let cur = 0;            // 当前可见的 video 下标
let state = {};         // 选择累积的状态：site、ending
let history = [];       // 走过的节点
let token = 0;          // 每次切换节点 +1，旧回调据此作废
let timer = null;

const front = () => vids[cur];
const back = () => vids[1 - cur];

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}

function swapTo(src, { loop = false } = {}) {
  // 把片段装进后台 video，播起来后淡入、旧的淡出
  const v = back();
  const old = front();
  v.onended = null; v.ontimeupdate = null;
  if (!v.src.endsWith(src)) v.src = src;
  v.currentTime = 0;
  v.loop = false;
  return v.play().then(() => {
    cur = 1 - cur;
    v.classList.add("on");
    old.classList.remove("on");
    setTimeout(() => { if (old !== front()) { old.pause(); old.onended = null; old.ontimeupdate = null; } }, FADE * 1000 + 50);
    return v;
  });
}

function preload(srcs) {
  // 在后台 video 上预读下一批可能的片段（浏览器缓存即可）
  for (const s of srcs) { const l = document.createElement("link"); l.rel = "preload"; l.as = "video"; l.href = s; document.head.append(l); }
}

function go(id) {
  const my = ++token;
  clearInterval(timer); timer = null;
  const n = G.nodes[id];
  history.push(id);
  hideNote();
  if (n.end) return showCard();
  if (n.options) return showChoice(id, n, my);
  veil.classList.remove("on");
  statusLine.textContent = `播放中 · ${pathText() || "共同主线"}`;
  const nexts = [n.next].flatMap((k) => { const m = G.nodes[k]; return m.clip ? [m.clip] : m.loop ? [m.loop] : []; });
  preload(nexts);
  swapTo(n.clip).then((v) => {
    if (my !== token) return;
    if (n.note && state.site) setTimeout(() => { if (my === token) showNote(n.note[state.site]); }, 1200);
    v.ontimeupdate = () => {
      // 片段末尾提前一个淡化时长切到下一节点，避免黑场
      if (my === token && v.duration && v.currentTime >= v.duration - FADE) { v.ontimeupdate = null; go(n.next); }
    };
    v.onended = () => { if (my === token) go(n.next); };
  }).catch(() => playBlocked());
}

function playLoop(src, my) {
  // 等待循环：同一片段两个 video 交替，每圈末尾交叉淡化
  swapTo(src).then((v) => {
    if (my !== token) return;
    v.ontimeupdate = () => {
      if (my === token && v.duration && v.currentTime >= v.duration - FADE - 0.05) { v.ontimeupdate = null; playLoop(src, my); }
    };
  }).catch(() => playBlocked());
}

function showChoice(id, n, my) {
  playLoop(n.loop, my);
  preload(n.options.map((o) => G.nodes[o.next].clip));
  statusLine.textContent = `${n.eyebrow} · 等待选择`;
  panel.replaceChildren();
  const left = el("div");
  left.append(el("p", "eyebrow", n.eyebrow), el("h1", null, n.title), el("p", "copy", n.copy));
  const box = el("div", "choices");
  const buttons = n.options.map((o, i) => {
    const b = el("button");
    const kbd = el("kbd", null, o.key); const t = el("b", null, o.label); const h = el("span", null, o.hint);
    b.append(kbd, t, h);
    if (i === 0) b.classList.add("default");
    b.addEventListener("click", () => choose(o, my));
    return b;
  });
  box.append(...buttons);
  panel.append(left, box);
  veil.classList.add("on");
  buttons[0].focus({ preventScroll: true });
  // 倒计时：默认项按钮底部的进度条缩短；时间到按默认项继续
  if (n.timeout) {
    const t0 = performance.now();
    timer = setInterval(() => {
      if (my !== token) return clearInterval(timer);
      const left_ = Math.max(0, 1 - (performance.now() - t0) / (n.timeout * 1000));
      buttons[0].style.setProperty("--left", `${left_ * 100}%`);
      if (left_ <= 0) { clearInterval(timer); choose(n.options[0], my); }
    }, 100);
  }
  window.onkeydown = (e) => {
    const o = n.options.find((x) => x.key.toLowerCase() === e.key.toLowerCase());
    if (o && my === token) choose(o, my);
  };
}

function choose(o, my) {
  if (my !== token) return;
  window.onkeydown = null;
  Object.assign(state, o.set || {});
  veil.classList.remove("on");
  go(o.next);
}

function pathText() {
  const parts = [];
  if (state.site) parts.push(G.labels.site[state.site]);
  if (state.ending) parts.push(G.labels.ending[state.ending]);
  return parts.join(" → ");
}

function showNote(text) { note.textContent = text; note.classList.add("on"); setTimeout(hideNote, 5200); }
function hideNote() { note.classList.remove("on"); }

function showCard() {
  statusLine.textContent = `已看完 · ${pathText()}`;
  front().pause();
  panel.replaceChildren();
  const left = el("div");
  left.append(el("p", "eyebrow", "你的路线"), el("h1", null, pathText()), el("p", "copy", G.coda));
  const otherSite = state.site === "first" ? "second" : "first";
  const row = el("div", "row");
  const again = el("button", "primary", "从头再看");
  again.addEventListener("click", restart);
  const c1 = el("button", "ghost", `回到选择 1 · 去看${G.labels.site[otherSite]}`);
  c1.addEventListener("click", () => { state = { site: null }; bgm.play().catch(() => {}); go("choice1"); });
  const c2 = el("button", "ghost", "回到选择 2 · 换个结尾");
  c2.addEventListener("click", () => { state.ending = null; bgm.play().catch(() => {}); go("choice2"); });
  row.append(c1, c2, again);
  panel.append(left, row);
  veil.classList.add("on");
}

function showStart() {
  panel.replaceChildren();
  const left = el("div");
  left.append(el("p", "eyebrow", "MOGADISHU · 1993 · 分支互动样片"), el("h1", null, "任务开始后，计划变了"),
    el("p", "copy", "两次选择：先去哪处坠机现场，结尾看哪一面。选择改变你看到的内容，不改变历史结果。"));
  const row = el("div", "row");
  const b = el("button", "primary", "开始观看");
  b.addEventListener("click", start);
  row.append(b);
  panel.append(left, row);
  veil.classList.add("on");
}

function start() {
  state = {}; history = [];
  if (G.bgm) { bgm.src = G.bgm; bgm.volume = MIX.gain; bgm.currentTime = 0; bgm.play().catch(() => {}); }
  go(G.start);
}

function restart() { token++; vids.forEach((v) => { v.pause(); v.classList.remove("on"); }); bgm.pause(); showStart(); }

function playBlocked() {
  statusLine.textContent = "无法播放片段；请确认 clips/ 下的视频已生成，并通过本地服务器打开";
}

function bgmTarget() {
  const v = front();
  const key = decodeURIComponent(v.src.split("/").pop() || "").replace(/\.mp4$/, "");
  const t = v.currentTime;
  const clamp = (x) => Math.min(1, Math.max(0, x));
  let g = 1;
  for (const [a, b] of NARR[key] || []) {
    const f = clamp((t - (a - MIX.in)) / MIX.in) * clamp((b + MIX.out - t) / MIX.out);
    g = Math.min(g, 1 - (1 - MIX.duck) * f);
  }
  return MIX.gain * g;
}

// 平滑追随目标音量，避免跳变（用定时器而非 requestAnimationFrame：标签页在后台时动画帧会暂停，音频却继续播放）
setInterval(() => { bgm.volume += (bgmTarget() - bgm.volume) * 0.25; }, 50);
showStart();
