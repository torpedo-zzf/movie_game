// 摩加迪沙 60 秒样片：程序化细节城市 + 胶片调色 + 运动模糊（风格沿用 mogadishu_visual_test）。
// 所有画面只由时间 t 决定（确定性 seek）；随机数全部来自固定种子。
import * as THREE from "./vendor/three/three.bundle.js";

const W = 1920, H = 816, DURATION = 60, FPS = 30;
const canvas = document.querySelector("#world");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: false, powerPreference: "high-performance", preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.setSize(W, H, false);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

// ---------- seeded helpers ----------
function mulberry32(a) { return () => { a |= 0; a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
const rand = mulberry32(19931003);
const R = (a = 0, b = 1) => a + (b - a) * rand();
const pick = (arr) => arr[Math.floor(rand() * arr.length) % arr.length];
const hash = (a, b = 0) => { const n = Math.sin(a * 127.1 + b * 311.7) * 43758.5453123; return n - Math.floor(n); };
const clamp01 = (x) => Math.min(1, Math.max(0, x));
const smooth = (a, b, x) => { const u = clamp01((x - a) / (b - a)); return u * u * (3 - 2 * u); };
const easeInOut = (u) => u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2;

// ---------- procedural textures (canvas, seeded) ----------
function canvasTex(size, draw, repeat = true) {
  const c = document.createElement("canvas"); c.width = c.height = size;
  const g = c.getContext("2d"); const r = mulberry32(size * 7 + draw.length);
  draw(g, size, r);
  const tex = new THREE.CanvasTexture(c);
  if (repeat) tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.anisotropy = 8; tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}
function blotches(g, s, r, n, minR, maxR, colorFn) {
  for (let i = 0; i < n; i++) {
    const x = r() * s, y = r() * s, rad = minR + r() * (maxR - minR);
    const grd = g.createRadialGradient(x, y, 0, x, y, rad);
    const col = colorFn(r);
    grd.addColorStop(0, col); grd.addColorStop(1, "rgba(0,0,0,0)");
    g.fillStyle = grd;
    for (const dx of [-s, 0, s]) for (const dy of [-s, 0, s]) { g.save(); g.translate(dx, dy); g.fillRect(x - rad, y - rad, rad * 2, rad * 2); g.restore(); }
  }
}
// 灰泥墙：斑驳、雨痕、弹孔、裂缝。用顶点色染出不同墙色。
const plasterTex = canvasTex(1024, (g, s, r) => {
  g.fillStyle = "#e4ddd0"; g.fillRect(0, 0, s, s);
  blotches(g, s, r, 900, 6, 60, (r) => `rgba(${120 + r() * 60},${105 + r() * 50},${80 + r() * 40},${0.03 + r() * 0.07})`);
  blotches(g, s, r, 260, 20, 140, (r) => r() < 0.5 ? `rgba(255,250,240,${0.05 + r() * 0.08})` : `rgba(90,78,60,${0.04 + r() * 0.06})`);
  for (let i = 0; i < 70; i++) { // 竖向雨痕
    const x = r() * s, y = r() * s, len = 60 + r() * 260, w = 2 + r() * 10;
    const grd = g.createLinearGradient(0, y, 0, y + len);
    grd.addColorStop(0, `rgba(70,60,45,${0.10 + r() * 0.12})`); grd.addColorStop(1, "rgba(70,60,45,0)");
    g.fillStyle = grd; g.fillRect(x, y, w, len);
  }
  for (let i = 0; i < 26; i++) { // 剥落露出的砖/水泥
    const x = r() * s, y = r() * s; g.fillStyle = `rgba(${150 + r() * 40},${125 + r() * 30},${95 + r() * 20},0.55)`;
    g.beginPath(); g.moveTo(x, y); for (let k = 0; k < 7; k++) g.lineTo(x + (r() - 0.5) * 70, y + (r() - 0.5) * 50); g.closePath(); g.fill();
  }
  for (let c = 0; c < 9; c++) { // 弹孔簇
    const cx = r() * s, cy = r() * s;
    for (let i = 0; i < 6 + r() * 14; i++) {
      const x = cx + (r() - 0.5) * 120, y = cy + (r() - 0.5) * 90, rad = 1.5 + r() * 4;
      g.fillStyle = "rgba(225,215,195,0.8)"; g.beginPath(); g.arc(x, y, rad * 2.2, 0, 7); g.fill();
      g.fillStyle = "rgba(40,34,26,0.9)"; g.beginPath(); g.arc(x, y, rad, 0, 7); g.fill();
    }
  }
  g.strokeStyle = "rgba(60,50,40,0.35)"; g.lineWidth = 1.2;
  for (let i = 0; i < 18; i++) { let x = r() * s, y = r() * s; g.beginPath(); g.moveTo(x, y); for (let k = 0; k < 9; k++) { x += (r() - 0.5) * 30; y += r() * 26; g.lineTo(x, y); } g.stroke(); }
});
// 波纹铁皮：条纹 + 锈斑
const tinTex = canvasTex(512, (g, s, r) => {
  g.fillStyle = "#a9a59d"; g.fillRect(0, 0, s, s);
  for (let x = 0; x < s; x += 8) { const grd = g.createLinearGradient(x, 0, x + 8, 0); grd.addColorStop(0, "rgba(255,255,255,0.18)"); grd.addColorStop(0.5, "rgba(0,0,0,0.22)"); grd.addColorStop(1, "rgba(255,255,255,0.18)"); g.fillStyle = grd; g.fillRect(x, 0, 8, s); }
  blotches(g, s, r, 220, 8, 70, (r) => `rgba(${120 + r() * 50},${60 + r() * 30},${25 + r() * 15},${0.12 + r() * 0.3})`);
  blotches(g, s, r, 60, 20, 90, (r) => `rgba(40,32,26,${0.1 + r() * 0.2})`);
});
// 沙土地面
const sandTex = canvasTex(1024, (g, s, r) => {
  g.fillStyle = "#b59a72"; g.fillRect(0, 0, s, s);
  blotches(g, s, r, 700, 10, 120, (r) => `rgba(${130 + r() * 70},${105 + r() * 55},${70 + r() * 40},${0.06 + r() * 0.12})`);
  for (let i = 0; i < 9000; i++) { const v = r(); g.fillStyle = v < 0.5 ? `rgba(70,58,42,${0.2 + r() * 0.4})` : `rgba(235,220,190,${0.15 + r() * 0.3})`; g.fillRect(r() * s, r() * s, 1 + r() * 2.5, 1 + r() * 2.5); }
  for (let i = 0; i < 40; i++) { g.fillStyle = `rgba(60,52,40,${0.05 + r() * 0.07})`; g.beginPath(); g.ellipse(r() * s, r() * s, 30 + r() * 80, 4 + r() * 10, r() * 3, 0, 7); g.fill(); }
});
// 路面：碎裂沥青 + 沙覆盖 + 车辙（v 方向沿道路）
const roadTex = canvasTex(1024, (g, s, r) => {
  g.fillStyle = "#77695a"; g.fillRect(0, 0, s, s);
  blotches(g, s, r, 500, 10, 100, (r) => `rgba(${70 + r() * 40},${62 + r() * 35},${52 + r() * 30},${0.12 + r() * 0.15})`);
  blotches(g, s, r, 160, 40, 200, (r) => `rgba(${175 + r() * 30},${150 + r() * 25},${110 + r() * 20},${0.25 + r() * 0.3})`); // 沙覆盖
  for (const lane of [0.3, 0.38, 0.62, 0.7]) { g.fillStyle = "rgba(60,52,44,0.22)"; g.fillRect(lane * s - 6, 0, 12 + r() * 6, s); }
  g.strokeStyle = "rgba(35,30,26,0.5)"; g.lineWidth = 1.5;
  for (let i = 0; i < 60; i++) { let x = r() * s, y = r() * s; g.beginPath(); g.moveTo(x, y); for (let k = 0; k < 6; k++) { x += (r() - 0.5) * 50; y += (r() - 0.5) * 50; g.lineTo(x, y); } g.stroke(); }
  for (let i = 0; i < 30; i++) { g.fillStyle = "rgba(40,34,28,0.55)"; g.beginPath(); g.ellipse(r() * s, r() * s, 8 + r() * 26, 6 + r() * 18, r() * 3, 0, 7); g.fill(); } // 坑洼
  for (let i = 0; i < 5000; i++) { g.fillStyle = `rgba(${r() < 0.5 ? "30,26,22" : "210,195,170"},${0.2 + r() * 0.3})`; g.fillRect(r() * s, r() * s, 1.5, 1.5); }
});
const puffTex = canvasTex(256, (g, s, r) => {
  for (let i = 0; i < 40; i++) {
    const x = s / 2 + (r() - 0.5) * s * 0.45, y = s / 2 + (r() - 0.5) * s * 0.45, rad = s * (0.12 + r() * 0.22);
    const grd = g.createRadialGradient(x, y, 0, x, y, rad); grd.addColorStop(0, "rgba(255,255,255,0.22)"); grd.addColorStop(1, "rgba(255,255,255,0)");
    g.fillStyle = grd; g.fillRect(0, 0, s, s);
  }
}, false);

// ---------- geometry merging ----------
const buckets = new Map();
const _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _e = new THREE.Euler(), _v = new THREE.Vector3(), _s = new THREE.Vector3();
function worldUV(geo, scale) {
  const p = geo.attributes.position, n = geo.attributes.normal, uv = new Float32Array(p.count * 2);
  for (let i = 0; i < p.count; i++) {
    const ax = Math.abs(n.getX(i)), ay = Math.abs(n.getY(i)), az = Math.abs(n.getZ(i));
    let u, v;
    if (ay >= ax && ay >= az) { u = p.getX(i); v = p.getZ(i); } else if (ax >= az) { u = p.getZ(i); v = p.getY(i); } else { u = p.getX(i); v = p.getY(i); }
    uv[i * 2] = u / scale; uv[i * 2 + 1] = v / scale;
  }
  geo.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
}
// 顶点色：底部沾尘偏暗偏黄，顶部略暗（雨痕），整体按墙色染色。
function tint(geo, color, grime = 1) {
  const p = geo.attributes.position, col = new Float32Array(p.count * 3);
  for (let i = 0; i < p.count; i++) {
    const y = p.getY(i);
    const dust = 1 - grime * 0.32 * (1 - smooth(0, 2.4, y));
    col[i * 3] = color.r * dust; col[i * 3 + 1] = color.g * dust * 0.97; col[i * 3 + 2] = color.b * dust * 0.9;
  }
  geo.setAttribute("color", new THREE.BufferAttribute(col, 3));
}
function add(key, geo, x, y, z, rx = 0, ry = 0, rz = 0, color = new THREE.Color(1, 1, 1), uvScale = 4, grime = 1) {
  let g = geo.index ? geo.toNonIndexed() : geo.clone();
  _m.compose(_v.set(x, y, z), _q.setFromEuler(_e.set(rx, ry, rz)), _s.set(1, 1, 1));
  if (geo.type !== "BoxGeometry") _m.elements[13] += BASE_Y;
  g.applyMatrix4(_m);
  worldUV(g, uvScale); tint(g, color, grime);
  if (!buckets.has(key)) buckets.set(key, []);
  buckets.get(key).push(g);
}
let BASE_Y = 0;
const box = (key, w, h, d, x, y, z, ry, color, uv, grime) => add(key, new THREE.BoxGeometry(w, h, d), x, y + BASE_Y + h / 2, z, 0, ry, 0, color, uv, grime);
function merge(list) {
  let n = 0; for (const g of list) n += g.attributes.position.count;
  const pos = new Float32Array(n * 3), nor = new Float32Array(n * 3), uv = new Float32Array(n * 2), col = new Float32Array(n * 3);
  let o = 0;
  for (const g of list) {
    const c = g.attributes.position.count;
    pos.set(g.attributes.position.array, o * 3); nor.set(g.attributes.normal.array, o * 3);
    uv.set(g.attributes.uv.array, o * 2); col.set(g.attributes.color.array, o * 3); o += c; g.dispose();
  }
  const m = new THREE.BufferGeometry();
  m.setAttribute("position", new THREE.BufferAttribute(pos, 3)); m.setAttribute("normal", new THREE.BufferAttribute(nor, 3));
  m.setAttribute("uv", new THREE.BufferAttribute(uv, 2)); m.setAttribute("color", new THREE.BufferAttribute(col, 3));
  m.computeBoundingSphere(); return m;
}

// ---------- materials ----------
const mats = {
  plaster: new THREE.MeshStandardMaterial({ map: plasterTex, bumpMap: plasterTex, bumpScale: 1.6, roughness: 0.93, vertexColors: true }),
  tin: new THREE.MeshStandardMaterial({ map: tinTex, bumpMap: tinTex, bumpScale: 2.2, roughness: 0.62, metalness: 0.35, vertexColors: true }),
  dark: new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.96, vertexColors: true }),
  props: new THREE.MeshStandardMaterial({ map: plasterTex, roughness: 0.86, vertexColors: true }),
  foliage: new THREE.MeshStandardMaterial({ roughness: 0.95, vertexColors: true, flatShading: true }),
  rubble: new THREE.MeshStandardMaterial({ map: plasterTex, bumpMap: plasterTex, bumpScale: 2, roughness: 1, vertexColors: true, flatShading: true }),
};
const C = (hex) => new THREE.Color(hex);
const WALLS = ["#efe8d9", "#ece2cc", "#e3d3b2", "#d9c39a", "#cfd6cf", "#c7d3d2", "#e6cfc0", "#d8d2c6", "#c9b48c", "#f2eee6"];
const SHUTTERS = ["#4f6b63", "#5d7488", "#7a6a4c", "#6e4d3a", "#3f5a4a", "#8a8070", "#4a5560"];

// ---------- scene, light, sky ----------
const scene = new THREE.Scene();
const FOG_COLOR = new THREE.Color("#c4a982");
scene.fog = new THREE.FogExp2(FOG_COLOR, 0.0042);
scene.background = FOG_COLOR.clone();
const SUN_DIR = new THREE.Vector3(-0.42, 0.6, 0.68).normalize();
const sky = new THREE.Mesh(new THREE.SphereGeometry(900, 32, 16), new THREE.ShaderMaterial({
  side: THREE.BackSide, depthWrite: false, fog: false,
  uniforms: { sun: { value: SUN_DIR }, fogc: { value: FOG_COLOR }, zen: { value: new THREE.Vector3(0.30, 0.36, 0.40) }, glow: { value: 1 } },
  vertexShader: "varying vec3 vDir; void main(){ vDir = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }",
  fragmentShader: `varying vec3 vDir; uniform vec3 sun; uniform vec3 fogc; uniform vec3 zen; uniform float glow;
    void main(){ float h = clamp(vDir.y, 0.0, 1.0);
      vec3 c = mix(fogc, zen, smoothstep(0.02, 0.7, h));
      float s = max(dot(normalize(vDir), sun), 0.0);
      c += glow * vec3(1.0,0.78,0.5) * (pow(s, 8.0) * 0.45 + pow(s, 900.0) * 6.0) + (1.0 - glow) * vec3(0.7,0.8,0.9) * pow(s, 2000.0) * 2.0;
      gl_FragColor = vec4(c, 1.0); }`,
}));
sky.renderOrder = -1; scene.add(sky);
scene.add(new THREE.HemisphereLight(0xb8c4c8, 0x9a7650, 1.5));
const sun = new THREE.DirectionalLight(0xffd4a3, 4.6);
sun.castShadow = true; sun.shadow.mapSize.set(4096, 4096); sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.04;
scene.add(sun, sun.target);
const bounce = new THREE.DirectionalLight(0xc89a6a, 0.6); bounce.position.set(0.6, -0.2, -0.5); scene.add(bounce);

// ---------- city layout ----------
// 单位：米。主干道（示意的“国家大街”方向）沿 z 轴，北向为 -z。
const MAIN_HALF = 7;
const CROSS_Z = [-170, -118, -66, -14, 38, 90, 142, 194];
const NS_X = [-120, -62, 0, 62, 120];
const CROSS_HALF = 4.5, NS_HALF = 4;
const TARGET = new THREE.Vector3(14, 0, -58);
const hotelBox = { x0: 9, x1: 33, z0: -64, z1: -46 };
// 坠机点（非比例示意）：第一处在目标区东北约三个街区；第二处在第一处以南“不到一英里”，此处压缩表现。
const SITE1 = new THREE.Vector3(56, 0, -126), SITE2 = new THREE.Vector3(-34, 0, 206);
const blocked = (x, z, pad = 0) => Math.hypot(x - SITE1.x, z - SITE1.z) < 13 + pad || Math.hypot(x - SITE2.x, z - SITE2.z) < 13 + pad;

const ground = new THREE.Mesh(new THREE.PlaneGeometry(5000, 5000), new THREE.MeshStandardMaterial({ map: sandTex, roughness: 1, color: 0xd2c2a2 }));
sandTex.repeat.set(500, 500); ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
function road(x, z, w, l, alongZ) {
  const t = roadTex.clone(); t.needsUpdate = true; t.repeat.set(1, l / 14);
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, l), new THREE.MeshStandardMaterial({ map: t, roughness: 0.97, color: alongZ ? 0xd8cbb4 : 0xe6d8bd, polygonOffset: true, polygonOffsetFactor: -2 }));
  m.rotation.x = -Math.PI / 2; if (!alongZ) m.rotation.z = Math.PI / 2;
  m.position.set(x, 0.02, z); m.receiveShadow = true; scene.add(m);
}
road(0, 0, MAIN_HALF * 2, 520, true);
for (const z of CROSS_Z) road(0, z, CROSS_HALF * 2, 480, false);
for (const x of NS_X) if (x !== 0) road(x, 0, NS_HALF * 2, 520, true);

function inRoad(x, z, pad = 0) {
  if (Math.abs(x) < MAIN_HALF + pad) return true;
  for (const cz of CROSS_Z) if (Math.abs(z - cz) < CROSS_HALF + pad) return true;
  for (const nx of NS_X) if (Math.abs(x - nx) < NS_HALF + pad) return true;
  return false;
}

// 一栋多层楼：墙体、楼板线脚、窗洞（过梁/窗台/百叶）、底层商铺卷帘、阳台、女儿墙、屋顶水箱/楼梯间/钢筋。
function building(cx, cz, w, d, floors, facing, wallHex, opts = {}) {
  if (blocked(cx, cz)) return;
  const fh = 3.2, h = floors * fh, col = C(wallHex);
  const ry = facing; // 0: 正面朝 +z
  const cos = Math.cos(ry), sin = Math.sin(ry);
  const L = (lx, lz) => [cx + lx * cos + lz * sin, cz - lx * sin + lz * cos];
  box("plaster", w, h, d, cx, 0, cz, ry, col, 4);
  // 楼层线脚
  for (let f = 1; f < floors; f++) { const [x, z] = L(0, 0); box("plaster", w + 0.16, 0.18, d + 0.16, x, f * fh - 0.1, z, ry, col.clone().multiplyScalar(0.94), 4, 0); }
  // 女儿墙
  const pc = col.clone().multiplyScalar(0.97), ph = 0.85 + (opts.tallParapet ? 0.5 : 0);
  for (const [lx, lz, pw, pd] of [[0, d / 2 - 0.1, w, 0.2], [0, -d / 2 + 0.1, w, 0.2], [w / 2 - 0.1, 0, 0.2, d], [-w / 2 + 0.1, 0, 0.2, d]]) {
    const [x, z] = L(lx, lz); box("plaster", pw, ph, pd, x, h, z, ry, pc, 4, 0);
  }
  { const [x, z] = L(0, 0); box("props", w - 0.4, 0.06, d - 0.4, x, h, z, ry, C(pick(["#9c9286", "#8a8174", "#a99f8e", "#7d7468", "#b0a593"])), 4, 0); }
  // 立面开口：四个面，正面细节最多
  const faces = [[0, 1, w], [Math.PI, 1, w], [Math.PI / 2, 0.55, d], [-Math.PI / 2, 0.55, d]];
  faces.forEach(([fr, density, span], fi) => {
    const out = (fi < 2 ? d : w) / 2;
    const fry = ry + fr;
    const fc = Math.cos(fry), fs = Math.sin(fry);
    const P = (u, o) => [cx + u * fc + o * fs, cz - u * fs + o * fc];
    const bays = Math.max(1, Math.floor(span / (2.6 + rand() * 0.8)));
    const step = span / bays;
    const shut = C(pick(SHUTTERS));
    for (let f = 0; f < floors; f++) {
      for (let b = 0; b < bays; b++) {
        if (rand() > density) continue;
        const u = -span / 2 + step * (b + 0.5) + (rand() - 0.5) * 0.3;
        if (f === 0 && fi === 0 && opts.shops) { // 底层商铺卷帘门
          const sw = Math.min(step - 0.5, 2.6), sh = 2.5;
          let [x, z] = P(u, out + 0.04);
          box("tin", sw, sh, 0.08, x, 0.05, z, fry, C(pick(["#6c7a80", "#7d5b45", "#55665a", "#8c8a80", "#5b6470"])), 1.4, 0.6);
          [x, z] = P(u, out + 0.25); box("plaster", sw + 0.5, 0.22, 0.45, x, sh + 0.1, z, fry, col.clone().multiplyScalar(0.9), 4, 0);
          if (rand() < 0.6) { [x, z] = P(u, out + 0.12); box("props", sw + 0.2, 0.7, 0.05, x, sh + 0.4, z, fry, C(pick(["#a8442f", "#2f6b8a", "#c9a23c", "#3e7a52", "#e3dccb", "#5b4a7a"])).multiplyScalar(0.75 + rand() * 0.2), 4, 0); }
          continue;
        }
        if (f === 0 && fi === 0 && b === Math.floor(bays / 2)) { // 门
          let [x, z] = P(u, out + 0.03); box("dark", 1.2, 2.3, 0.06, x, 0, z, fry, C(pick(SHUTTERS)).multiplyScalar(0.8), 4, 0);
          [x, z] = P(u, out + 0.18); box("plaster", 1.6, 0.16, 0.36, x, 2.36, z, fry, col.clone().multiplyScalar(0.92), 4, 0);
          continue;
        }
        const ww = 0.95 + rand() * 0.35, wh = 1.25 + rand() * 0.2, y0 = f * fh + 0.95;
        let [x, z] = P(u, out + 0.02);
        box("dark", ww, wh, 0.05, x, y0, z, fry, C(rand() < 0.15 ? "#2a2a28" : "#151412"), 4, 0);
        [x, z] = P(u, out + 0.1); box("plaster", ww + 0.3, 0.1, 0.22, x, y0 - 0.1, z, fry, col.clone().multiplyScalar(0.93), 4, 0); // 窗台
        [x, z] = P(u, out + 0.13); box("plaster", ww + 0.24, 0.16, 0.28, x, y0 + wh, z, fry, col.clone().multiplyScalar(0.9), 4, 0); // 过梁（投影出窗洞深度）
        const s = rand();
        if (s < 0.35) { // 百叶窗：开/半开/关
          const open = s < 0.12 ? 0 : (s < 0.25 ? 1.2 : 2.1);
          for (const side of [-1, 1]) {
            const hingeU = u + side * ww / 2; const a = side * open;
            const sx = Math.cos(a) * ww / 4 * side, so = Math.abs(Math.sin(a)) * ww / 4;
            [x, z] = P(hingeU - sx * (open ? 1 : -1) * (open ? 1 : 1) * 0 + (open ? side * Math.cos(open) * ww / 4 : -side * ww / 4), out + 0.06 + so);
            add("dark", new THREE.BoxGeometry(ww / 2, wh, 0.04), x, y0 + wh / 2, z, 0, fry - a * 0.5, 0, shut.clone().multiplyScalar(0.85 + rand() * 0.2), 4, 0);
          }
        } else if (s < 0.5) { // 防盗铁栅
          for (let k = 1; k < 5; k++) { [x, z] = P(u - ww / 2 + (ww * k) / 5, out + 0.07); box("dark", 0.03, wh, 0.03, x, y0, z, fry, C("#23201c"), 4, 0); }
        }
      }
      // 阳台
      if (f > 0 && fi === 0 && opts.balcony && rand() < 0.55) {
        const bw = 2.6 + rand() * 1.8, u = (rand() - 0.5) * (span - bw);
        let [x, z] = P(u, out + 0.6); box("plaster", bw, 0.16, 1.2, x, f * fh, z, fry, col.clone().multiplyScalar(0.92), 4, 0);
        [x, z] = P(u, out + 1.15); box("plaster", bw, 0.95, 0.1, x, f * fh + 0.16, z, fry, col, 4, 0);
        if (rand() < 0.5) { // 晾晒的布
          [x, z] = P(u + (rand() - 0.5), out + 1.22); box("props", 0.8 + rand(), 0.7, 0.02, x, f * fh + 0.5, z, fry, C(pick(["#b4473a", "#2f5f86", "#d8b23f", "#e9e4d8", "#5a7a3a"])), 4, 0);
        }
      }
    }
  });
  // 屋顶
  const roofItems = Math.floor(rand() * 4) + 2;
  for (let i = 0; i < roofItems; i++) {
    const [x, z] = L((rand() - 0.5) * (w - 2.5), (rand() - 0.5) * (d - 2.5));
    const r0 = rand();
    if (r0 < 0.4) { // 水箱（带支架）
      const th = rand() < 0.5 ? 0.9 : 0.06;
      if (th > 0.1) for (const [a, b] of [[-0.4, -0.4], [0.4, -0.4], [-0.4, 0.4], [0.4, 0.4]]) box("dark", 0.06, th, 0.06, x + a, h, z + b, 0, C("#2b2722"), 4, 0);
      add("props", new THREE.CylinderGeometry(0.55, 0.55, 1.1, 14), x, h + th + 0.55, z, 0, 0, 0, C(pick(["#2d2f2c", "#3c3a33", "#5f645f", "#6c5b48"])), 4, 0);
    } else if (r0 < 0.6) box("plaster", 2.4, 2.5, 2.6, x, h, z, ry, col.clone().multiplyScalar(0.95), 4, 0); // 楼梯间
    else if (r0 < 0.78) { // 屋顶铁皮棚
      const sw = 2.5 + rand() * 2, sd = 2 + rand() * 1.5;
      for (const [a, b] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) box("props", 0.08, 2.1, 0.08, x + a * sw / 2.2, h, z + b * sd / 2.2, 0, C("#4a3d30"), 4, 0);
      add("tin", new THREE.BoxGeometry(sw, 0.04, sd), x, h + 2.15, z, 0.08, ry, 0, C(pick(["#a29684", "#8d6f58", "#9a9a92"])), 1.6, 0);
    } else if (r0 < 0.9) box("props", 1 + rand() * 1.5, 0.4 + rand() * 0.5, 0.8 + rand(), x, h, z, rand() * 3, C(pick(["#6b5a46", "#4d4a44", "#827563"])), 4, 0); // 杂物堆
    else { // 晾衣绳与衣物
      for (let k = 0; k < 4; k++) box("props", 0.5 + rand() * 0.4, 0.6, 0.02, x + k * 0.7 - 1, h + 1.0, z, ry, C(pick(["#b4473a", "#2f5f86", "#d8b23f", "#e9e4d8", "#5a7a3a", "#7a4e7a"])), 4, 0);
    }
  }
  if (opts.stepped && floors >= 2 && !opts.top) { // 退台的上层体量，打破方盒轮廓
    const sw = w * (0.45 + rand() * 0.25), sd = d * (0.5 + rand() * 0.3);
    const [x, z] = L((rand() - 0.5) * (w - sw), (rand() - 0.5) * (d - sd));
    const prev = BASE_Y; BASE_Y += h;
    building(x, z, sw, sd, 1 + Math.floor(rand() * 2), ry, wallHex, { top: true, balcony: false, tallParapet: rand() < 0.5 });
    BASE_Y = prev;
  }
  if (opts.unfinished) { // 未完成的上一层：柱子和外露钢筋
    for (const [lx, lz] of [[-w / 2 + 0.3, -d / 2 + 0.3], [w / 2 - 0.3, -d / 2 + 0.3], [-w / 2 + 0.3, d / 2 - 0.3], [w / 2 - 0.3, d / 2 - 0.3], [0, d / 2 - 0.3]]) {
      const [x, z] = L(lx, lz); const ch = 0.8 + rand() * 2.0;
      box("plaster", 0.35, ch, 0.35, x, h, z, ry, col.clone().multiplyScalar(0.85), 4, 0);
      for (let k = 0; k < 4; k++) add("dark", new THREE.CylinderGeometry(0.015, 0.015, 1.1, 4), x + (k % 2 - 0.5) * 0.18, h + ch + 0.5, z + (k > 1 ? 0.09 : -0.09), (rand() - 0.5) * 0.3, 0, (rand() - 0.5) * 0.3, C("#4a2f20"), 4, 0);
    }
  }
}
// 平房：铁皮坡屋顶 + 院墙 + 铁门
function house(cx, cz, w, d, wallHex) {
  if (blocked(cx, cz)) return;
  const col = C(wallHex), h = 3.0, ry = rand() < 0.5 ? 0 : Math.PI / 2;
  box("plaster", w, h, d, cx, 0, cz, ry, col, 4);
  const pitch = 0.24, half = (ry === 0 ? d : w) / 2, len = (ry === 0 ? w : d) + 0.6;
  const rc = C(pick(["#b3a99a", "#9e8a74", "#a9a39a", "#8f7660"]));
  for (const s of [-1, 1]) {
    const off = s * half / 2;
    if (ry === 0) add("tin", new THREE.BoxGeometry(len, 0.05, half / Math.cos(pitch) + 0.3), cx, h + Math.tan(pitch) * half / 2, cz + off, s * pitch, 0, 0, rc, 1.6, 0);
    else add("tin", new THREE.BoxGeometry(half / Math.cos(pitch) + 0.3, 0.05, len), cx + off, h + Math.tan(pitch) * half / 2, cz, 0, 0, -s * pitch, rc, 1.6, 0);
  }
  for (let i = 0; i < 2; i++) box("dark", 0.9, 1.1, 0.05, cx + (i - 0.5) * w * 0.5, 1.0, cz + d / 2 + 0.02, 0, C("#161411"), 4, 0);
}
function compoundWall(x0, z0, x1, z1, hex) {
  if (blocked((x0 + x1) / 2, (z0 + z1) / 2, 4)) return;
  const col = C(hex).multiplyScalar(0.95), h = 2.2;
  const gate = rand() < 0.8;
  box("plaster", x1 - x0, h, 0.25, (x0 + x1) / 2, 0, z0, 0, col, 4);
  box("plaster", x1 - x0, h, 0.25, (x0 + x1) / 2, 0, z1, 0, col, 4);
  box("plaster", 0.25, h, z1 - z0, x0, 0, (z0 + z1) / 2, 0, col, 4);
  box("plaster", 0.25, h, z1 - z0, x1, 0, (z0 + z1) / 2, 0, col, 4);
  if (gate) box("tin", 2.6, 2.0, 0.08, (x0 + x1) / 2, 0.05, z1 + 0.14, 0, C(pick(["#4c6f86", "#5b7a5c", "#7e4a3a", "#8b8578"])), 1.2, 0);
}
function tree(x, z, s = 1) {
  if (blocked(x, z)) return;
  add("props", new THREE.CylinderGeometry(0.12 * s, 0.2 * s, 3.2 * s, 6), x, 1.6 * s, z, (rand() - 0.5) * 0.15, 0, (rand() - 0.5) * 0.15, C("#5a4a3a"), 4, 0);
  const n = 3 + Math.floor(rand() * 3);
  for (let i = 0; i < n; i++) {
    const g = new THREE.IcosahedronGeometry(1.6 * s * (0.7 + rand() * 0.5), 1); g.scale(1.25, 0.42, 1.1);
    add("foliage", g, x + (rand() - 0.5) * 2.4 * s, 3.4 * s + rand() * 0.8 * s, z + (rand() - 0.5) * 2.4 * s, 0, rand() * 3, 0, C(pick(["#59603a", "#4b5532", "#646a3e", "#6b6b44"])).multiplyScalar(0.8 + rand() * 0.3), 4, 0);
  }
}
function rubble(x, z, n, spread) {
  if (blocked(x, z, -6)) return;
  for (let i = 0; i < n; i++) {
    const g = new THREE.IcosahedronGeometry(0.15 + rand() * 0.55, 0); g.scale(1, 0.55 + rand() * 0.4, 1);
    add("rubble", g, x + (rand() - 0.5) * spread, 0.1, z + (rand() - 0.5) * spread, rand(), rand() * 3, rand(), C(pick(WALLS)).multiplyScalar(0.7 + rand() * 0.25), 2, 0);
  }
}
function wreck(x, z, ry) { // 烧毁的轿车残骸
  const c = C("#3a2c22");
  box("dark", 4.2, 0.75, 1.8, x, 0.25, z, ry, c, 4, 0);
  box("dark", 2.2, 0.6, 1.6, x - Math.cos(ry) * 0.2, 1.0, z + Math.sin(ry) * 0.2, ry, C("#2b2420"), 4, 0);
  for (const [a, b] of [[1.3, 0.85], [-1.3, 0.85], [1.3, -0.85], [-1.3, -0.85]]) add("dark", new THREE.CylinderGeometry(0.28, 0.28, 0.2, 10), x + a * Math.cos(ry) + b * Math.sin(ry), 0.22, z - a * Math.sin(ry) + b * Math.cos(ry), Math.PI / 2, ry, 0, C("#1b1917"), 4, 0);
}
function tires(x, z, n) { for (let i = 0; i < n; i++) add("dark", new THREE.TorusGeometry(0.36, 0.13, 6, 12), x + (rand() - 0.5) * 1.6, 0.13 + (i % 3) * 0.24, z + (rand() - 0.5) * 1.6, Math.PI / 2 + (rand() - 0.5) * 0.4, 0, rand(), C("#1c1b1a"), 4, 0); }
function drums(x, z) { for (let i = 0; i < 2 + Math.floor(rand() * 3); i++) add("props", new THREE.CylinderGeometry(0.29, 0.29, 0.88, 12), x + (rand() - 0.5) * 1.5, 0.44, z + (rand() - 0.5) * 1.5, 0, 0, 0, C(pick(["#5d6b54", "#7a3b2c", "#3e4d5d", "#8a7a5a"])), 2, 0.4); }
function stall(x, z, ry) { // 市场棚摊
  if (blocked(x, z)) return;
  for (const [a, b] of [[-1.3, -1], [1.3, -1], [-1.3, 1], [1.3, 1]]) box("props", 0.08, 2.4, 0.08, x + a, 0, z + b, 0, C("#6a5440"), 4, 0);
  add("props", new THREE.BoxGeometry(3, 0.03, 2.4), x, 2.45, z, 0.12, ry, 0, C(pick(["#b7703f", "#6f7f8a", "#c4b089", "#8d4f3f"])), 4, 0);
  box("props", 2.4, 0.8, 1.2, x, 0, z, ry, C("#7b6248"), 4, 0);
}

// 沿街区四周排楼，内部放平房与院落。
const blocksX = [];
const xs = [-200, ...NS_X, 200];
for (let i = 0; i < xs.length - 1; i++) blocksX.push([xs[i] + (xs[i] === 0 ? MAIN_HALF : NS_HALF) + 1.5, xs[i + 1] - (xs[i + 1] === 0 ? MAIN_HALF : NS_HALF) - 1.5]);
const zs = [-230, ...CROSS_Z, 250];
for (const [bx0, bx1] of blocksX) {
  for (let j = 0; j < zs.length - 1; j++) {
    const bz0 = zs[j] + CROSS_HALF + 1.5, bz1 = zs[j + 1] - CROSS_HALF - 1.5;
    const nearMain = Math.min(Math.abs(bx0), Math.abs(bx1)) < 12;
    const dist = Math.hypot((bx0 + bx1) / 2, (bz0 + bz1) / 2);
    const tall = nearMain ? 1.0 : Math.max(0.25, 1 - dist / 230);
    const front = (x0, x1, z, facing) => { // 沿一条边
      let x = x0;
      while (x < x1 - 5) {
        const w = Math.min(x1 - x, 7 + rand() * 9), d = 9 + rand() * 5;
        const cx = x + w / 2;
        const inHotel = (px, pz) => px > hotelBox.x0 - 4 && px < hotelBox.x1 + 4 && pz > hotelBox.z0 - 4 && pz < hotelBox.z1 + 4;
        const pos = facing === 0 ? [cx, z - d / 2] : facing === Math.PI ? [cx, z + d / 2] : null;
        if (pos && !inHotel(pos[0], pos[1]) && rand() < 0.9) {
          const floors = Math.max(1, Math.round((1 + rand() * 3) * tall + (nearMain ? 0.6 : 0)));
          building(pos[0], pos[1], w - 0.4 - rand() * 0.6, d, floors, facing, pick(WALLS), { shops: nearMain || rand() < 0.4, balcony: rand() < 0.6, unfinished: rand() < 0.12, tallParapet: rand() < 0.3, stepped: rand() < 0.35 });
        } else if (pos && !inHotel(pos[0], pos[1])) rubble(pos[0], pos[1], 26, 7);
        x += w + rand() * 1.4;
      }
    };
    front(bx0, bx1, bz1, 0);       // 南边沿街，正面朝 +z
    front(bx0, bx1, bz0, Math.PI); // 北边沿街
    // 侧街（沿 x 方向的面朝主干道）
    for (const [edgeX, facing] of [[bx0, -Math.PI / 2], [bx1, Math.PI / 2]]) {
      let z = bz0 + 15;
      while (z < bz1 - 18) {
        const w = 7 + rand() * 8, d = 9 + rand() * 4;
        const cx = facing === -Math.PI / 2 ? edgeX + d / 2 : edgeX - d / 2;
        if (!(cx > hotelBox.x0 - 6 && cx < hotelBox.x1 + 6 && z > hotelBox.z0 - 10 && z < hotelBox.z1 + 10)) {
          const isMain = Math.abs(edgeX) < 12;
          const floors = Math.max(1, Math.round((1 + rand() * 3) * tall + (isMain ? 0.8 : 0)));
          building(cx, z + w / 2, w - 0.6, d, floors, facing, pick(WALLS), { shops: isMain || rand() < 0.3, balcony: rand() < 0.5, unfinished: rand() < 0.12, stepped: rand() < 0.3 });
        }
        z += w + 0.5 + rand() * 2;
      }
    }
    // 内部：院落平房
    const ix0 = bx0 + 14, ix1 = bx1 - 14, iz0 = bz0 + 16, iz1 = bz1 - 16;
    for (let x = ix0; x < ix1 - 6; x += 12 + rand() * 3) {
      for (let z = iz0; z < iz1 - 6; z += 12 + rand() * 3) {
        if (x > hotelBox.x0 - 6 && x < hotelBox.x1 + 6 && z > hotelBox.z0 - 8 && z < hotelBox.z1 + 8) continue;
        const r0 = rand();
        if (r0 < 0.62) { const hw = 6 + rand() * 3, hd = 5 + rand() * 2; house(x + 5, z + 5, hw, hd, pick(WALLS)); if (rand() < 0.6) compoundWall(x, z, x + 11, z + 11, pick(WALLS)); }
        else if (r0 < 0.8) tree(x + 5, z + 5, 0.9 + rand() * 0.5);
        else if (r0 < 0.9) building(x + 5, z + 5, 7 + rand() * 3, 7 + rand() * 3, 1 + Math.floor(rand() * 2), 0, pick(WALLS), { balcony: false });
        else rubble(x + 5, z + 5, 18, 6);
      }
    }
  }
}
// 地标：奥林匹克酒店（示意，五层白色楼）
{
  const cx = (hotelBox.x0 + hotelBox.x1) / 2, cz = (hotelBox.z0 + hotelBox.z1) / 2;
  building(cx, cz, hotelBox.x1 - hotelBox.x0, hotelBox.z1 - hotelBox.z0, 5, -Math.PI / 2, "#f3efe6", { balcony: true, tallParapet: true });
  box("plaster", 26, 0.35, 3, cx, 3.0, cz + 10, 0, C("#e8e2d6"), 4, 0); // 入口雨棚
}
// 主干道陈设：电线杆+电线、残骸、轮胎堆、油桶、碎石、摊位、行道树
const poles = [];
for (let z = -200; z <= 220; z += 24) for (const side of [-1, 1]) {
  if (inRoad(side * (MAIN_HALF + 0.8), z, -3) && CROSS_Z.some((c) => Math.abs(z - c) < CROSS_HALF + 1)) continue;
  const x = side * (MAIN_HALF + 0.9), lean = (hash(z, side) - 0.5) * 0.06;
  add("props", new THREE.CylinderGeometry(0.09, 0.14, 8.5, 7), x, 4.25, z, lean, 0, lean, C("#5c4a38"), 4, 0);
  add("props", new THREE.BoxGeometry(1.8, 0.1, 0.1), x, 7.9, z, 0, Math.PI / 2 * 0, 0, C("#4f4032"), 4, 0);
  poles.push([x, z]);
}
const wires = new THREE.Group(); scene.add(wires);
const wireMat = new THREE.LineBasicMaterial({ color: 0x1d1b18, fog: true });
for (const side of [-1, 1]) {
  const ps = poles.filter((p) => Math.sign(p[0]) === side).sort((a, b) => a[1] - b[1]);
  for (let i = 0; i < ps.length - 1; i++) for (const off of [-0.8, 0, 0.8]) {
    const [x0, z0] = ps[i], [x1, z1] = ps[i + 1]; const pts = [];
    for (let k = 0; k <= 16; k++) { const u = k / 16; pts.push(new THREE.Vector3(x0 + (x1 - x0) * u + off, 7.85 - Math.sin(u * Math.PI) * (0.55 + hash(i, off) * 0.4), z0 + (z1 - z0) * u)); }
    wires.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), wireMat));
  }
}
wreck(-5.0, 14, 0.25); wreck(8.6, -32, 1.4); wreck(-9.2, 66, 1.6);
tires(5.5, 4, 7); tires(-6, -40, 5); tires(4.8, 52, 6);
drums(-6.4, 30); drums(6.2, -8); drums(-6.3, 78);
for (const [x, z, n] of [[3.5, 22, 14], [-4, -22, 10], [-11, 44, 30], [12, 8, 22], [-12, -6, 25]]) rubble(x, z, n, 4);
stall(-10.5, 40, 0); stall(-10.5, 47, 0); stall(10.6, 24, 0); stall(10.6, -24, 0);
for (let z = -190; z < 220; z += 31) { if (hash(z) < 0.55) tree(hash(z, 3) < 0.5 ? -9.5 : 9.5, z + 6, 0.8 + hash(z, 9) * 0.4); }

// 清真寺：圆顶 + 宣礼塔（城市天际线的竖向地标）
function mosque(cx, cz, s = 1) {
  const col = C("#efe9dc");
  box("plaster", 14 * s, 6 * s, 14 * s, cx, 0, cz, 0, col, 4);
  const dome = new THREE.SphereGeometry(4.6 * s, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2);
  add("plaster", dome, cx, 6 * s, cz, 0, 0, 0, C(pick(["#d8d2c2", "#7f9a8f", "#c9b38a"])), 4, 0);
  const mx = cx + 8.5 * s, mz = cz - 5 * s;
  add("plaster", new THREE.CylinderGeometry(1.0 * s, 1.25 * s, 22 * s, 12), mx, 11 * s, mz, 0, 0, 0, col, 4);
  add("plaster", new THREE.CylinderGeometry(1.7 * s, 1.5 * s, 0.6 * s, 12), mx, 17 * s, mz, 0, 0, 0, col.clone().multiplyScalar(0.92), 4, 0);
  add("plaster", new THREE.CylinderGeometry(0.8 * s, 0.9 * s, 3 * s, 12), mx, 23.5 * s, mz, 0, 0, 0, col, 4, 0);
  add("plaster", new THREE.ConeGeometry(1.0 * s, 2.6 * s, 12), mx, 26.3 * s, mz, 0, 0, 0, C("#8fa596"), 4, 0);
}
mosque(-40, -140, 1.1); mosque(88, -30, 1); mosque(-92, 106, 0.9); mosque(36, 118, 0.85);
// 街面杂物：垃圾、碎石、墙根积沙
for (let i = 0; i < 1400; i++) {
  const z = -200 + rand() * 420, side = rand() < 0.5 ? -1 : 1;
  const x = side * (rand() < 0.7 ? MAIN_HALF - 0.6 + rand() * 3.5 : rand() * MAIN_HALF);
  if (inRoad(0, z) && CROSS_Z.some((c) => Math.abs(z - c) < CROSS_HALF)) continue;
  const r0 = rand();
  if (r0 < 0.55) box("props", 0.15 + rand() * 0.4, 0.02, 0.1 + rand() * 0.3, x, 0.03, z, rand() * 3, C(pick(["#d9d2c2", "#8a7d68", "#3d4a5a", "#a8442f", "#2e2c28", "#c9c0a8"])), 4, 0);
  else { const g = new THREE.IcosahedronGeometry(0.06 + rand() * 0.2, 0); add("rubble", g, x, 0.05, z, rand(), rand(), rand(), C(pick(WALLS)).multiplyScalar(0.65 + rand() * 0.25), 2, 0); }
}
for (let z = -200; z < 220; z += 3 + rand() * 5) for (const side of [-1, 1]) {
  if (rand() < 0.45) continue;
  const sand = new THREE.CylinderGeometry(0.01, 1, 1, 4, 1, false, 0, Math.PI); sand.scale(1, 0.35, 1.5 + rand() * 3);
  add("props", sand, side * (MAIN_HALF + 1.2), 0.17, z, 0, side < 0 ? Math.PI / 2 : -Math.PI / 2, 0, C("#c2a77c"), 4, 0);
}
const staticMeshes = [];
for (const [key, list] of buckets) {
  const m = new THREE.Mesh(merge(list), mats[key]); m.castShadow = true; m.receiveShadow = true; scene.add(m); staticMeshes.push(m);
}
buckets.clear();

// ---------- vehicles ----------
const tan = new THREE.MeshStandardMaterial({ color: 0xa8916a, roughness: 0.78, metalness: 0.08 });
const tanDark = new THREE.MeshStandardMaterial({ color: 0x7d6b4f, roughness: 0.85 });
const black = new THREE.MeshStandardMaterial({ color: 0x141312, roughness: 0.8 });
const glass = new THREE.MeshStandardMaterial({ color: 0x2c3234, roughness: 0.18, metalness: 0.6 });
const olive = new THREE.MeshStandardMaterial({ color: 0x5c5a45, roughness: 0.9 });
const canvasMat = new THREE.MeshStandardMaterial({ color: 0x8f7d5c, roughness: 1 });
function part(parent, geo, mat, x, y, z, rx = 0, ry = 0, rz = 0) { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.rotation.set(rx, ry, rz); m.castShadow = m.receiveShadow = true; parent.add(m); return m; }
function wheelSet(g, positions, r, wdt) {
  const wheels = [];
  const tire = new THREE.CylinderGeometry(r, r, wdt, 22); tire.rotateZ(Math.PI / 2);
  const hub = new THREE.CylinderGeometry(r * 0.55, r * 0.55, wdt + 0.02, 10); hub.rotateZ(Math.PI / 2);
  const lug = new THREE.BoxGeometry(wdt + 0.04, r * 0.18, r * 0.9);
  for (const [x, z] of positions) { const w = new THREE.Group(); w.position.set(x, r, z); part(w, tire, black, 0, 0, 0); part(w, hub, tanDark, 0, 0, 0); part(w, lug, tanDark, 0, 0, 0); g.add(w); wheels.push(w); }
  return wheels;
}
// M1025 风格悍马：低矮宽车身、斜引擎盖、硬顶、炮塔环与机枪手
function humvee() {
  const g = new THREE.Group(), body = new THREE.Group(); g.add(body);
  part(body, new THREE.BoxGeometry(2.18, 0.55, 4.6), tan, 0, 0.78, 0);
  part(body, new THREE.BoxGeometry(2.1, 0.28, 1.5), tan, 0, 1.13, 1.45, -0.09);  // 引擎盖
  part(body, new THREE.BoxGeometry(1.4, 0.06, 0.5), black, 0, 0.98, 2.33); // 格栅
  part(body, new THREE.BoxGeometry(2.08, 0.74, 2.7), tan, 0, 1.42, -0.7);   // 车厢硬顶
  part(body, new THREE.BoxGeometry(1.9, 0.5, 0.04), glass, 0, 1.5, 0.66, -0.18); // 风挡
  for (const s of [-1, 1]) { part(body, new THREE.BoxGeometry(0.04, 0.42, 0.9), glass, s * 1.05, 1.52, 0.05); part(body, new THREE.BoxGeometry(0.04, 0.42, 0.9), glass, s * 1.05, 1.52, -0.95); }
  for (const s of [-1, 1]) part(body, new THREE.BoxGeometry(0.34, 0.3, 1.1), tanDark, s * 1.0, 1.05, 1.55); // 挡泥板
  part(body, new THREE.CylinderGeometry(0.55, 0.55, 0.18, 18), tanDark, 0, 1.87, -0.6); // 炮塔环
  part(body, new THREE.BoxGeometry(0.7, 0.45, 0.06), tanDark, 0, 2.15, -0.25); // 护盾
  part(body, new THREE.CylinderGeometry(0.035, 0.035, 1.4, 6), black, 0, 2.18, 0.35, Math.PI / 2 - 0.08); // M2 枪管
  part(body, new THREE.BoxGeometry(0.2, 0.2, 0.5), black, 0, 2.15, -0.35);
  part(body, new THREE.CylinderGeometry(0.2, 0.22, 0.5, 10), olive, 0, 2.2, -0.75); // 机枪手
  part(body, new THREE.SphereGeometry(0.17, 12, 8), olive, 0, 2.55, -0.75);
  part(body, new THREE.BoxGeometry(1.6, 0.4, 0.5), canvasMat, 0, 1.92, -1.65); // 车顶沙袋/装备
  for (const s of [-1, 1]) part(body, new THREE.BoxGeometry(0.22, 0.16, 0.08), black, s * 0.75, 0.95, 2.32);
  const wheels = wheelSet(g, [[-1.0, 1.65], [1.0, 1.65], [-1.0, -1.6], [1.0, -1.6]], 0.47, 0.34);
  g.userData = { body, wheels, r: 0.47 };
  return g;
}
// M923 风格五吨卡车：驾驶室 + 带沙袋的货箱
function truck() {
  const g = new THREE.Group(), body = new THREE.Group(); g.add(body);
  part(body, new THREE.BoxGeometry(2.4, 0.4, 7.6), tanDark, 0, 1.0, 0);
  part(body, new THREE.BoxGeometry(2.1, 0.9, 1.6), tan, 0, 1.6, 2.9); // 发动机舱
  part(body, new THREE.BoxGeometry(2.3, 1.2, 1.5), tan, 0, 2.0, 1.55); // 驾驶室
  part(body, new THREE.BoxGeometry(2.0, 0.55, 0.04), glass, 0, 2.25, 2.31);
  part(body, new THREE.BoxGeometry(2.45, 0.9, 4.2), tan, 0, 1.65, -1.6); // 货箱
  for (let i = 0; i < 7; i++) part(body, new THREE.BoxGeometry(0.55, 0.22, 0.35), canvasMat, -0.9 + (i % 4) * 0.6, 2.2, -0.2 - Math.floor(i / 4) * 3.0);
  for (let i = 0; i < 4; i++) part(body, new THREE.CylinderGeometry(0.18, 0.2, 0.5, 8), olive, -0.7 + i * 0.47, 2.35, -1.6);
  const wheels = wheelSet(g, [[-1.05, 2.8], [1.05, 2.8], [-1.05, -1.0], [1.05, -1.0], [-1.05, -2.4], [1.05, -2.4]], 0.55, 0.38);
  g.userData = { body, wheels, r: 0.55 };
  return g;
}
// 马来西亚“秃鹰”轮式装甲车（联合国白色涂装）
const unWhite = new THREE.MeshStandardMaterial({ color: 0xd8d6cc, roughness: 0.7, metalness: 0.05 });
const unBlack = new THREE.MeshStandardMaterial({ color: 0x1e1f20, roughness: 0.6 });
function condor() {
  const g = new THREE.Group(), body = new THREE.Group(); g.add(body);
  part(body, new THREE.BoxGeometry(2.45, 1.25, 5.4), unWhite, 0, 1.45, -0.2);
  part(body, new THREE.BoxGeometry(2.3, 0.8, 1.3), unWhite, 0, 1.55, 2.75, 0.45); // 斜前装甲
  part(body, new THREE.BoxGeometry(2.0, 0.5, 2.2), unWhite, 0, 2.3, -0.4);
  part(body, new THREE.CylinderGeometry(0.62, 0.7, 0.5, 14), unWhite, 0, 2.75, 0.2); // 炮塔
  part(body, new THREE.CylinderGeometry(0.05, 0.05, 1.5, 6), unBlack, 0, 2.8, 1.0, Math.PI / 2);
  for (const s of [-1, 1]) { part(body, new THREE.BoxGeometry(0.03, 0.55, 1.1), unBlack, s * 1.235, 1.6, 0.6); part(body, new THREE.BoxGeometry(0.03, 0.22, 0.5), unBlack, s * 1.235, 2.05, -1.4); } // 侧面“UN”标记块
  part(body, new THREE.BoxGeometry(0.9, 0.3, 0.03), unBlack, 0, 1.7, -2.91);
  const wheels = wheelSet(g, [[-1.15, 1.7], [1.15, 1.7], [-1.15, -1.9], [1.15, -1.9]], 0.62, 0.42);
  g.userData = { body, wheels, r: 0.62 };
  return g;
}
// 巴基斯坦 M48 主战坦克
const tankMat = new THREE.MeshStandardMaterial({ color: 0x6d6a50, roughness: 0.82, metalness: 0.1 });
function m48() {
  const g = new THREE.Group(), body = new THREE.Group(); g.add(body);
  part(body, new THREE.BoxGeometry(3.3, 1.0, 6.6), tankMat, 0, 1.25, 0);
  part(body, new THREE.BoxGeometry(3.2, 0.5, 1.4), tankMat, 0, 1.2, 3.4, -0.5);
  for (const s of [-1, 1]) { part(body, new THREE.BoxGeometry(0.62, 0.95, 6.9), black, s * 1.75, 0.55, 0); part(body, new THREE.BoxGeometry(0.66, 0.06, 6.9), tankMat, s * 1.75, 1.08, 0); }
  const tur = new THREE.SphereGeometry(1.45, 20, 12); tur.scale(1, 0.48, 1.3);
  part(body, tur, tankMat, 0, 2.05, -0.4);
  part(body, new THREE.CylinderGeometry(0.11, 0.13, 4.6, 10), tankMat, 0, 2.15, 3.3, Math.PI / 2);
  part(body, new THREE.CylinderGeometry(0.45, 0.45, 0.4, 12), tankMat, 0.5, 2.75, -0.9);
  const wheels = [];
  for (const s of [-1, 1]) for (let k = 0; k < 5; k++) { const w = new THREE.Group(); w.position.set(s * 1.75, 0.45, -2.6 + k * 1.3); part(w, new THREE.CylinderGeometry(0.4, 0.4, 0.66, 12).rotateZ(Math.PI / 2), tanDark, 0, 0, 0); part(w, new THREE.BoxGeometry(0.7, 0.08, 0.6), black, 0, 0, 0); g.add(w); wheels.push(w); }
  g.userData = { body, wheels, r: 0.4 };
  return g;
}

// ---------- 车队 ----------
const LANE_X = -2.4;
// 白天突击车队：沿主干道北上，停在目标区南侧
const dayConvoy = [humvee(), humvee(), truck(), humvee(), truck(), humvee()];
const DAY_GAP = [0, 13, 27, 41, 55, 70], DAY_STOP = -44;
dayConvoy.forEach((v) => scene.add(v));
const dayZ = (t, i) => Math.max(DAY_STOP + DAY_GAP[i], 122 - 11.2 * (t - 8.5) + DAY_GAP[i]);
// 夜间救援纵队：自南沿主干道北上，转东驶向第一处坠机点
const reliefPath = new THREE.CurvePath();
const RP = [[LANE_X, 260], [LANE_X, -112], [6, -116.4], [SITE1.x - 12, -116.4]].map(([x, z]) => new THREE.Vector3(x, 0, z));
for (let i = 0; i < RP.length - 1; i++) reliefPath.add(new THREE.LineCurve3(RP[i], RP[i + 1]));
const RELIEF_LEN = reliefPath.getLength();
const nightConvoy = [m48(), m48(), condor(), condor(), humvee(), condor(), condor(), humvee(), condor()];
const NIGHT_GAP = [0, 14, 28, 40, 52, 63, 75, 87, 98];
nightConvoy.forEach((v) => scene.add(v));
const nightLead = (t) => Math.min(RELIEF_LEN, RELIEF_LEN - 13.5 * (47.6 - t));
function nightS(t, i) { return nightLead(t) - NIGHT_GAP[i]; }
function driveBody(v, t, i, dist) {
  const { body, wheels, r } = v.userData;
  body.position.y = Math.sin(t * 9.0 + i * 1.7) * 0.025 + Math.sin(t * 23 + i) * 0.008;
  body.rotation.z = Math.sin(t * 5.3 + i) * 0.008; body.rotation.x = Math.sin(t * 6.1 + i * 2) * 0.006;
  wheels.forEach((w) => { w.rotation.x = -dist / r; });
}
function placeConvoys(t) {
  const day = t < 40;
  dayConvoy.forEach((v, i) => {
    v.visible = day;
    const z = dayZ(t, i);
    v.position.set(LANE_X + Math.sin(z * 0.05 + i) * 0.25, 0, z);
    v.rotation.y = Math.PI + Math.cos(z * 0.05 + i) * 0.012;
    driveBody(v, t, i, 122 - z);
  });
  nightConvoy.forEach((v, i) => {
    const sArc = nightS(t, i);
    v.visible = !day && sArc > 0;
    const u = Math.min(1, Math.max(0, sArc / RELIEF_LEN));
    const p = reliefPath.getPointAt(u), tg = reliefPath.getTangentAt(u);
    v.position.copy(p); v.rotation.y = Math.atan2(tg.x, tg.z);
    driveBody(v, t, i + 3, sArc);
  });
}
const dayMoving = (t, i) => 122 - 11.2 * (t - 8.5) + DAY_GAP[i] > DAY_STOP + DAY_GAP[i];

// ---------- helicopters (MH-60 风格黑鹰) ----------
const heliMat = new THREE.MeshStandardMaterial({ color: 0x23262a, roughness: 0.6, metalness: 0.3 });
const rotorMat = new THREE.MeshBasicMaterial({ color: 0x15171a, transparent: true, opacity: 0.16, depthWrite: false, side: THREE.DoubleSide });
const bladeMat = new THREE.MeshStandardMaterial({ color: 0x1a1c1f, transparent: true, opacity: 0.45, depthWrite: false });
function blackhawk(wreck = false) {
  const g = new THREE.Group();
  const fus = new THREE.SphereGeometry(1, 20, 12); fus.scale(1.15, 1.05, 3.1);
  part(g, fus, heliMat, 0, 0, 0.6);
  part(g, new THREE.BoxGeometry(2.1, 1.5, 3.6), heliMat, 0, -0.1, 0.2);
  part(g, new THREE.BoxGeometry(1.6, 0.7, 2.8), heliMat, 0, 0.95, 0.4);
  const boom = new THREE.CylinderGeometry(0.22, 0.6, 7.5, 10); boom.rotateX(Math.PI / 2);
  const tailGroup = new THREE.Group(); g.add(tailGroup);
  part(tailGroup, boom, heliMat, 0, 0.45, -5.3);
  part(tailGroup, new THREE.BoxGeometry(0.18, 2.2, 1.2), heliMat, 0, 1.35, -8.8, -0.35);
  part(tailGroup, new THREE.BoxGeometry(3.6, 0.06, 0.8), heliMat, 0, 0.15, -8.6);
  for (const s of [-1, 1]) part(g, new THREE.BoxGeometry(0.12, 0.7, 0.12), black, s * 0.8, -1.2, 1.4);
  part(g, new THREE.BoxGeometry(2.0, 0.08, 0.15), black, 0, -1.55, 1.4);
  const rotor = new THREE.Group(); rotor.position.set(0, 1.55, 0.4); g.add(rotor);
  const disc = new THREE.Mesh(new THREE.CircleGeometry(8.2, 48), rotorMat); disc.rotation.x = -Math.PI / 2;
  if (!wreck) rotor.add(disc);
  for (let i = 0; i < 4; i++) {
    const len = wreck ? 2.5 + hash(i, 7) * 4.5 : 8.1;
    const b = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.05, len), wreck ? heliMat : bladeMat); b.position.z = len / 2;
    const arm = new THREE.Group(); arm.rotation.y = i * Math.PI / 2 + (wreck ? hash(i) * 0.5 : 0); if (wreck) arm.rotation.x = 0.25 + hash(i, 2) * 0.3; arm.add(b); rotor.add(arm);
  }
  const tail = new THREE.Group(); tail.position.set(0.25, 1.6, -8.9); g.add(tail);
  if (!wreck) { const td = new THREE.Mesh(new THREE.CircleGeometry(1.4, 24), rotorMat); td.rotation.y = Math.PI / 2; tail.add(td); }
  if (wreck) { tailGroup.rotation.set(0.18, 0.5, 0.25); tailGroup.position.set(0.6, -0.4, -0.6); }
  g.traverse((o) => { if (o.isMesh && o.material !== rotorMat) o.castShadow = true; });
  g.userData = { rotor, tail };
  return g;
}
// 0、1：突击机组；2：Super 61（20 s 前在目标区外围盘旋）；3：Super 64（30 s 前盘旋）
const helis = [blackhawk(), blackhawk(), blackhawk(), blackhawk()];
helis.forEach((h) => scene.add(h));
const wreck1 = blackhawk(true), wreck2 = blackhawk(true);
wreck1.position.set(SITE1.x, 1.0, SITE1.z); wreck1.rotation.set(0.12, 2.3, 0.55);
wreck2.position.set(SITE2.x, 1.0, SITE2.z); wreck2.rotation.set(-0.1, -0.7, -0.5);
scene.add(wreck1, wreck2);
const orbit = (c, r, h, w, ph) => (t) => new THREE.Vector3(c.x + Math.cos(t * w + ph) * r, h + Math.sin(t * 0.6 + ph) * 1.5, c.z + Math.sin(t * w + ph) * r);
function heliPos(i, t) {
  const approach = (start, end, a, b, t) => { const u = clamp01((t - a) / (b - a)); return start.clone().lerp(end, easeInOut(u)); };
  if (t >= 40) return orbit(SITE1, 70 + i * 25, 80 + i * 12, 0.12, i * 2.1)(t); // 夜间高空掩护
  if (i === 0 || i === 1) {
    const hold = TARGET.clone().add(new THREE.Vector3(i ? -8 : 10, 30 + i * 4, i ? 10 : -4));
    if (t < 15) return approach(new THREE.Vector3(-30 - i * 25, 48 + i * 4, 260 + i * 40), hold, -1, 15, t).add(new THREE.Vector3(0, 0, 0));
    if (t < 20 || i === 1) return orbit(hold, 4, hold.y, 0.35, i * 3)(t);
    return orbit(SITE1, 26, 34, 0.3, 0)(t); // 坠机后在第一处上空掩护
  }
  if (i === 2) return orbit(TARGET, 75, 52, 0.22, 1.2)(t);
  return orbit(TARGET, 110, 60, -0.18, 2.6)(t);
}
function placeHelis(t) {
  helis.forEach((h, i) => {
    h.visible = !(i === 2 && t >= 20) && !(i === 3 && t >= 30) && !(t >= 40 && i > 1);
    const p = heliPos(i, t), p2 = heliPos(i, t + 0.05);
    h.position.copy(p);
    const dx = p2.x - p.x, dz = p2.z - p.z, sp = Math.hypot(dx, dz) / 0.05;
    h.rotation.set(0, sp > 0.5 ? Math.atan2(dx, dz) : Math.PI, 0);
    h.rotateX(Math.min(0.16, sp * 0.005)); h.rotateZ(Math.sin(t * 0.7 + i) * 0.03);
    h.userData.rotor.rotation.y = t * 27.0 + i;
    h.userData.tail.rotation.x = t * 120 + i;
  });
  wreck1.visible = t >= 20; wreck2.visible = t >= 30;
}
// 坠机点周边碎屑（重新合并一批静态网格）
for (const [site, seed] of [[SITE1, 1], [SITE2, 2]]) {
  for (let i = 0; i < 70; i++) {
    const a = hash(i, seed) * 6.283, r = 2 + hash(i, seed + 5) * 10;
    const g = new THREE.IcosahedronGeometry(0.1 + hash(i, seed + 9) * 0.45, 0); g.scale(1, 0.5, 1);
    add("rubble", g, site.x + Math.cos(a) * r, 0.08, site.z + Math.sin(a) * r, i, i * 2, 0, C(pick(WALLS)).multiplyScalar(0.6 + rand() * 0.3), 2, 0);
  }
  for (let i = 0; i < 12; i++) box("dark", 0.4 + rand() * 1.6, 0.05, 0.3 + rand(), site.x + (rand() - 0.5) * 16, 0.02, site.z + (rand() - 0.5) * 16, rand() * 3, C("#202224"), 4, 0);
}
for (const [key, list] of buckets) { const m = new THREE.Mesh(merge(list), mats[key]); m.castShadow = m.receiveShadow = true; scene.add(m); }
buckets.clear();

// ---------- 夜间光：月光、火光 ----------
const FIRES = [[SITE1.x + 4, SITE1.z + 3], [9, -74], [-6.5, 28], [62, -98], [SITE2.x - 3, SITE2.z + 4], [-60, -40], [4, -150], [-8.5, -84], [7.5, -104], [-8, -10], [24, -121]].map(([x, z]) => new THREE.Vector3(x, 0.6, z));
const fireLights = FIRES.map((p) => { const l = new THREE.PointLight(0xff8a3a, 0, 55, 2); l.position.copy(p).setY(1.6); scene.add(l); return l; });
const flameSprites = FIRES.map(() => Array.from({ length: 8 }, () => { const m = new THREE.SpriteMaterial({ map: puffTex, color: 0xffa050, transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending, fog: false }); const s = new THREE.Sprite(m); scene.add(s); return s; }));

// 救援纵队的车灯/工作灯（夜间）
const convoyLights = [2, 5].map((i) => { const l = new THREE.PointLight(0xffe2b0, 0, 30, 2); scene.add(l); return { l, i }; });
function placeConvoyLights(t, night) {
  for (const { l, i } of convoyLights) { const v = nightConvoy[i]; l.position.copy(v.position).add(new THREE.Vector3(Math.sin(v.rotation.y) * 4, 2.6, Math.cos(v.rotation.y) * 4)); l.intensity = v.visible ? night * 55 : 0; }
}
// ---------- particles：车队扬尘、坠机点与火点浓烟、旋翼下洗 ----------
const sprites = [];
function makeSprite(color, opacity) { const m = new THREE.SpriteMaterial({ map: puffTex, color, transparent: true, opacity, depthWrite: false, fog: true }); const s = new THREE.Sprite(m); scene.add(s); sprites.push(s); return s; }
const DUST_N = 24;
const dayDust = dayConvoy.map(() => Array.from({ length: DUST_N }, () => makeSprite(0xcdb48c, 0)));
const nightDust = nightConvoy.map(() => Array.from({ length: 14 }, () => makeSprite(0x8c9a98, 0)));
// [x, z, 起始时间]
const SMOKES = [[SITE1.x, SITE1.z, 20.2], [SITE2.x, SITE2.z, 24], [78, -190, -20], [-110, -88, -20], [40, -230, -20], [-140, 20, -20], [9, -74, 26]];
const smokeSprites = SMOKES.map(() => Array.from({ length: 34 }, () => makeSprite(0x3a332c, 0)));
const washSprites = Array.from({ length: 30 }, () => makeSprite(0xd8c19a, 0));
const _dust = new THREE.Color(), _smoke = new THREE.Color();
function updateParticles(t, night) {
  _dust.set(0xcdb48c).lerp(new THREE.Color(0x2a3634), night);
  _smoke.set(0x3a332c).lerp(new THREE.Color(0x0c1112), night);
  const life = 2.6;
  dayConvoy.forEach((v, vi) => dayDust[vi].forEach((s, i) => {
    const a = (t + i * (life / DUST_N)) % life, emitT = t - a;
    const moving = dayMoving(emitT, vi) && v.visible;
    const z = dayZ(emitT, vi) + 2.2 + hash(i, vi) * 1.5, spread = 0.6 + a * 1.4;
    s.position.set(LANE_X + (hash(i, vi + 9) - 0.5) * spread * 1.8, 0.4 + a * 0.75 + hash(i, 4) * 0.6, z + a * 1.2);
    const sc = 1.6 + a * 3.0; s.scale.set(sc * 1.4, sc, 1);
    s.material.color.copy(_dust);
    s.material.opacity = moving ? 0.42 * Math.sin(Math.PI * clamp01(a / life)) * smooth(0, 0.25, a) : 0;
    s.material.rotation = hash(i, vi) * 6 + a * 0.3;
  }));
  nightConvoy.forEach((v, vi) => nightDust[vi].forEach((s, i) => {
    const a = (t + i * (life / 14)) % life, sArc = nightS(t - a, vi);
    const ok = v.visible && sArc > 0 && nightLead(t - a) < RELIEF_LEN;
    const p = reliefPath.getPointAt(clamp01(sArc / RELIEF_LEN)), tg = reliefPath.getTangentAt(clamp01(sArc / RELIEF_LEN));
    s.position.set(p.x - tg.x * 3 + (hash(i, vi) - 0.5) * (1 + a * 2), 0.5 + a * 0.7, p.z - tg.z * 3 + (hash(i, vi + 3) - 0.5) * (1 + a * 2));
    const sc = 2 + a * 3; s.scale.set(sc * 1.4, sc, 1);
    s.material.color.copy(_dust);
    s.material.opacity = ok ? 0.3 * Math.sin(Math.PI * clamp01(a / life)) : 0;
  }));
  SMOKES.forEach(([sx, sz, start], si) => smokeSprites[si].forEach((s, i) => {
    const lifeS = 16, a = (t + i * (lifeS / 34) + si * 3) % lifeS, u = a / lifeS;
    const born = t - a >= start;
    s.position.set(sx + u * 26 + Math.sin(u * 5 + i) * 3, 2 + u * 70, sz + u * 10);
    const sc = 6 + u * 30; s.scale.set(sc, sc, 1);
    s.material.color.copy(_smoke);
    s.material.opacity = born ? 0.55 * Math.sin(Math.PI * u) * (0.6 + hash(i, si) * 0.4) : 0;
    s.material.rotation = i + u;
  }));
  const hp = helis[0].position, hoverLow = hp.y < 40 && t < 40;
  washSprites.forEach((s, i) => {
    const a = (t + i * 0.1) % 3, u = a / 3, ang = hash(i) * 6.28 + u, r = 4 + u * 26;
    s.position.set(hp.x + Math.cos(ang) * r, 0.8 + u * 4, hp.z + Math.sin(ang) * r);
    const sc = 5 + u * 12; s.scale.set(sc * 1.6, sc, 1);
    s.material.color.copy(_dust);
    s.material.opacity = hoverLow ? 0.28 * Math.sin(Math.PI * u) : 0;
  });
  FIRES.forEach((p, fi) => {
    const fl = 0.75 + 0.25 * Math.sin(t * 13 + fi * 2) * Math.sin(t * 7.3 + fi);
    fireLights[fi].intensity = night * 260 * fl;
    flameSprites[fi].forEach((s, i) => {
      const a = (t * 1.6 + i / 8) % 1;
      s.position.set(p.x + (hash(i, fi) - 0.5) * 1.2, 0.3 + a * 2.2, p.z + (hash(i, fi + 4) - 0.5) * 1.2);
      const sc = 1.6 * (1 - a * 0.6); s.scale.set(sc, sc * 1.4, 1);
      s.material.opacity = night * 0.85 * Math.sin(Math.PI * a) * fl;
    });
  });
}

// ---------- 示意路线与地点环 ----------
function routeTube(points, radius) {
  const curve = new THREE.CatmullRomCurve3(points, false, "catmullrom", 0.05);
  const mat = new THREE.MeshBasicMaterial({ color: 0xe8905a, transparent: true, opacity: 0, depthWrite: false, fog: false });
  const mesh = new THREE.Mesh(new THREE.TubeGeometry(curve, 300, radius, 8, false), mat); mesh.renderOrder = 5; scene.add(mesh);
  return { mesh, mat, len: mesh.geometry.index.count };
}
const dayRoute = routeTube([new THREE.Vector3(LANE_X, 0.5, 140), new THREE.Vector3(LANE_X, 0.5, -48), new THREE.Vector3(6, 0.5, -54), new THREE.Vector3(TARGET.x - 4, 0.5, TARGET.z + 2)], 0.9);
const linkRoute = routeTube([SITE1.clone().setY(4), new THREE.Vector3((SITE1.x + SITE2.x) / 2, 40, (SITE1.z + SITE2.z) / 2), SITE2.clone().setY(4)], 1.1);
const reliefRoute = routeTube(RP.map((p) => p.clone().setY(0.6)).concat([SITE1.clone().setY(0.6).add(new THREE.Vector3(-6, 0, 4))]), 1.1);
function ringAt(pos, r) { const m = new THREE.MeshBasicMaterial({ color: 0xe8905a, transparent: true, opacity: 0, depthWrite: false, fog: false, side: THREE.DoubleSide }); const mesh = new THREE.Mesh(new THREE.RingGeometry(r, r + 1.6, 96), m); mesh.rotation.x = -Math.PI / 2; mesh.position.copy(pos).setY(0.6); scene.add(mesh); return { mesh, m }; }
const targetRing = ringAt(new THREE.Vector3(TARGET.x + 7, 0, TARGET.z + 3), 26);
const site1Ring = ringAt(SITE1, 15), site2Ring = ringAt(SITE2, 15);
function showRoute(r, t, a, b, until = 99) {
  r.mat.opacity = t >= a && t < until ? 0.85 * smooth(a, a + 0.4, t) : 0;
  r.mesh.geometry.setDrawRange(0, Math.floor(r.len * easeInOut(clamp01((t - a) / (b - a))) / 3) * 3);
}
function showRing(r, t, a, until = 99, pulse = false) {
  const on = t >= a && t < until;
  r.m.opacity = on ? (0.55 + Math.sin(t * 4) * 0.2) * smooth(a, a + 0.5, t) : 0;
  const s = pulse && on ? 1 + 0.6 * (1 - smooth(a, a + 1.4, t)) : 1; r.mesh.scale.set(s, s, 1);
}

// ---------- 昼夜 ----------
const DAY = { fog: new THREE.Color("#c4a982"), zen: new THREE.Vector3(0.30, 0.36, 0.40), sunC: new THREE.Color(0xffd4a3), sunI: 4.6, hemi: 1.5, bounce: 0.6, exp: 1.18 };
const NIGHT = { fog: new THREE.Color("#1c3033"), zen: new THREE.Vector3(0.025, 0.04, 0.05), sunC: new THREE.Color(0x9cb8cc), sunI: 1.7, hemi: 0.75, bounce: 0, exp: 2.1 };
const MOON_DIR = new THREE.Vector3(0.45, 0.7, -0.4).normalize();
const hemi = scene.children.find((o) => o.isHemisphereLight);
const lightDir = new THREE.Vector3();
function setTimeOfDay(n) {
  FOG_COLOR.copy(DAY.fog).lerp(NIGHT.fog, n); scene.fog.color.copy(FOG_COLOR);
  sky.material.uniforms.fogc.value = FOG_COLOR;
  sky.material.uniforms.zen.value.copy(DAY.zen).lerp(NIGHT.zen, n);
  sky.material.uniforms.glow.value = 1 - n;
  sun.color.copy(DAY.sunC).lerp(NIGHT.sunC, n); sun.intensity = DAY.sunI + (NIGHT.sunI - DAY.sunI) * n;
  hemi.intensity = DAY.hemi + (NIGHT.hemi - DAY.hemi) * n; bounce.intensity = DAY.bounce * (1 - n);
  lightDir.copy(SUN_DIR).lerp(MOON_DIR, n).normalize();
  sky.material.uniforms.sun.value = lightDir;
  gradeMat.uniforms.exposure.value = DAY.exp + (NIGHT.exp - DAY.exp) * n;
  gradeMat.uniforms.night.value = n;
}

// ---------- camera choreography ----------
const camera = new THREE.PerspectiveCamera(30, W / H, 0.5, 2600);
const _a = new THREE.Vector3(), _b = new THREE.Vector3(), _look = new THREE.Vector3();
const shake = (t, amt) => [Math.sin(t * 7.1) * 0.6 + Math.sin(t * 13.7 + 1) * 0.3 + Math.sin(t * 2.3) * 0.5, Math.sin(t * 6.3 + 2) * 0.5 + Math.sin(t * 15.1) * 0.25].map((v) => v * amt);
// 镜头远近跟随剧情：全景建立 → 街区/车辆近景 → 回到态势
const SHOTS = [
  { id: "wide-open", start: 0, end: 5 }, { id: "heli-chase", start: 5, end: 10 },
  { id: "street-convoy", start: 10, end: 13.5 }, { id: "convoy-close", start: 13.5, end: 16.5 }, { id: "target-overview", start: 16.5, end: 20 },
  { id: "dive-site1", start: 20, end: 25 }, { id: "site1-street", start: 25, end: 30 },
  { id: "reveal-both", start: 30, end: 40 },
  { id: "night-wide", start: 40, end: 43.5 }, { id: "night-convoy", start: 43.5, end: 47 }, { id: "night-arrival", start: 47, end: 50 },
  { id: "night-record", start: 50, end: 60 },
];
function shotAt(t) { for (const s of SHOTS) if (t < s.end) return s; return SHOTS[SHOTS.length - 1]; }
function cameraAt(t) {
  const s = shotAt(t), u = clamp01((t - s.start) / (s.end - s.start)), k = easeInOut(u);
  let fov = 30, shadowSize = 160, fog = 0.0042; const focus = new THREE.Vector3();
  switch (s.id) {
    case "wide-open": _a.set(-250 + u * 22, 80 - u * 8, 215 - u * 18); _look.set(-12 + u * 8, 18, -10 - u * 8); fov = 21; focus.set(-20, 0, 20); shadowSize = 260; fog = 0.0024; break;
    case "heli-chase": { const h = helis[0].position; const [sx, sy] = shake(t, 0.3); _a.set(h.x - 16 + sx, h.y + 7 + sy, h.z + 30 - u * 6); _look.set(h.x + 2, h.y - 6, h.z - 40); fov = 38; focus.set(h.x, 0, h.z - 60); shadowSize = 200; fog = 0.0034; break; }
    case "street-convoy": { const [sx, sy] = shake(t, 0.05); _a.set(5.2 + sx, 2.4 + sy, 20 + u * 3.5); _look.set(-1.4 + sx * 2, 2.6, 90); fov = 34; focus.set(0, 0, 50); shadowSize = 110; fog = 0.0062; break; }
    case "convoy-close": { const z = dayZ(t, 0); const [sx, sy] = shake(t * 1.6, 0.035); _a.set(LANE_X - 3.1 + sx, 1.0 + sy, z + 2.6 - u * 1.4); _look.set(LANE_X + 0.4, 1.35, z - 3.2 - u * 0.6); fov = 44; focus.set(LANE_X, 0, z); shadowSize = 50; fog = 0.0058; break; }
    case "target-overview": _a.set(-70 + u * 14, 62 + u * 14, 34 - u * 20); _look.set(TARGET.x + 2, 4, TARGET.z + 14); fov = 36; focus.set(TARGET.x - 10, 0, TARGET.z + 20); shadowSize = 130; fog = 0.0038; break;
    case "dive-site1": _a.set(TARGET.x - 40, 120, TARGET.z + 70).lerp(_b.set(SITE1.x - 46, 26, SITE1.z + 46), k); _look.set(TARGET.x, 0, TARGET.z).lerp(_b.set(SITE1.x, 2, SITE1.z), k); fov = 36 - k * 4; focus.set(SITE1.x - 10, 0, SITE1.z + 20); shadowSize = 150; fog = 0.0035 + k * 0.002; break;
    case "site1-street": { const [sx, sy] = shake(t, 0.04); _a.set(SITE1.x - 19 + u * 3 + sx, 2.2 + sy, SITE1.z + 13 - u * 2); _look.set(SITE1.x + 1, 2.2, SITE1.z - 1); fov = 40; focus.set(SITE1.x, 0, SITE1.z); shadowSize = 60; fog = 0.0065; break; }
    case "reveal-both": { const m = SITE1.clone().lerp(SITE2, 0.5); _a.set(SITE1.x - 60, 70, SITE1.z + 60).lerp(_b.set(-330, 330, 260), easeInOut(clamp01(u * 1.6))); _look.set(SITE1.x, 0, SITE1.z).lerp(_b.set(m.x, 0, m.z), easeInOut(clamp01(u * 1.6))); fov = 34; focus.copy(m); shadowSize = 300; fog = 0.0038 - easeInOut(clamp01(u * 1.6)) * 0.0026; break; }
    case "night-wide": _a.set(-260 + u * 20, 150 - u * 10, 210 - u * 16); _look.set(10, 0, -40); fov = 26; focus.set(0, 0, -20); shadowSize = 260; fog = 0.0022; break;
    case "night-convoy": { const v = nightConvoy[2], p = v.position; const [sx, sy] = shake(t * 1.6, 0.035); const fwd = new THREE.Vector3(Math.sin(v.rotation.y), 0, Math.cos(v.rotation.y)), side = new THREE.Vector3(fwd.z, 0, -fwd.x); _a.copy(p).addScaledVector(side, 3.4).addScaledVector(fwd, -2 - u * 1.5).add(new THREE.Vector3(sx, 1.1 + sy, 0)); _look.copy(p).addScaledVector(fwd, 5).setY(1.6); fov = 44; focus.copy(p).setY(0); shadowSize = 60; fog = 0.0055; break; }
    case "night-arrival": _a.set(SITE1.x - 70, 22, SITE1.z + 36).lerp(_b.set(SITE1.x - 120, 130, SITE1.z + 150), k); _look.set(SITE1.x - 20, 0, SITE1.z + 8).lerp(_b.set(SITE1.x - 10, 0, SITE1.z + 10), k); fov = 36; focus.set(SITE1.x - 20, 0, SITE1.z + 10); shadowSize = 130; fog = 0.0045 - k * 0.0015; break;
    default: { const a = -2.3 + u * 0.35, r = 420; _a.set(Math.cos(a) * r, 260 - u * 20, Math.sin(a) * -r + 60); _look.set(10, 0, 20); fov = 30; focus.set(0, 0, 0); shadowSize = 320; fog = 0.0018; }
  }
  camera.position.copy(_a); camera.fov = fov; camera.updateProjectionMatrix(); camera.lookAt(_look);
  if (/street|close|convoy/.test(s.id)) camera.rotateZ(Math.sin(t * 3.1) * 0.004);
  scene.fog.density = fog;
  sun.position.copy(focus).addScaledVector(lightDir, 400); sun.target.position.copy(focus);
  const sc = sun.shadow.camera; sc.left = -shadowSize; sc.right = shadowSize; sc.top = shadowSize; sc.bottom = -shadowSize; sc.near = 50; sc.far = 900; sc.updateProjectionMatrix();
  sky.position.copy(camera.position);
  return s;
}

// ---------- post：运动模糊累积 + 胶片调色 ----------
const sceneRT = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: 4 });
const accumRT = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType });
const quadCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
const quadGeo = new THREE.PlaneGeometry(2, 2);
const accumMat = new THREE.ShaderMaterial({
  uniforms: { src: { value: null }, weight: { value: 1 } }, transparent: true, depthTest: false, depthWrite: false,
  blending: THREE.CustomBlending, blendEquation: THREE.AddEquation, blendSrc: THREE.OneFactor, blendDst: THREE.OneFactor,
  vertexShader: "varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy,0.0,1.0); }",
  fragmentShader: "uniform sampler2D src; uniform float weight; varying vec2 vUv; void main(){ gl_FragColor = vec4(texture2D(src, vUv).rgb * weight, weight); }",
});
const gradeMat = new THREE.ShaderMaterial({
  uniforms: { src: { value: accumRT.texture }, frame: { value: 0 }, exposure: { value: 1.18 }, night: { value: 0 }, res: { value: new THREE.Vector2(W, H) } },
  depthTest: false, depthWrite: false,
  vertexShader: "varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy,0.0,1.0); }",
  fragmentShader: `
    uniform sampler2D src; uniform float frame; uniform float exposure; uniform float night; uniform vec2 res; varying vec2 vUv;
    vec3 aces(vec3 x){ const float a=2.51,b=0.03,c=2.43,d=0.59,e=0.14; return clamp((x*(a*x+b))/(x*(c*x+d)+e),0.0,1.0); }
    float h(vec2 p){ return fract(sin(dot(p, vec2(12.9898,78.233))) * 43758.5453); }
    vec3 toSRGB(vec3 c){ return mix(c*12.92, 1.055*pow(c, vec3(1.0/2.4)) - 0.055, step(0.0031308, c)); }
    void main(){
      vec2 d = vUv - 0.5; float r2 = dot(d, d);
      // 轻微色散（仅画面边缘）
      vec2 ca = d * r2 * 0.012;
      vec3 c = vec3(texture2D(src, vUv + ca).r, texture2D(src, vUv).g, texture2D(src, vUv - ca).b) * exposure;
      // 高光晕染（halation）：取亮部做小范围采样
      vec3 glow = vec3(0.0);
      for (int i = 0; i < 12; i++) { float a = float(i) * 0.5236; vec2 o = vec2(cos(a), sin(a)) * vec2(9.0, 9.0) / res * (1.0 + float(i - (i/2)*2)); vec3 s = texture2D(src, vUv + o).rgb * exposure; glow += max(s - 1.1, 0.0); }
      c += glow / 12.0 * vec3(1.0, 0.55, 0.3) * 0.55;
      c = aces(c);
      // 漂白旁路：叠加亮度、降饱和、提高反差
      float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
      vec3 ov = mix(2.0*c*l, 1.0 - 2.0*(1.0-c)*(1.0-l), step(0.5, l));
      c = mix(c, ov, 0.34);
      c = mix(vec3(l), c, 0.68);
      // 分离色调：暗部偏青绿，亮部偏琥珀
      c += (vec3(-0.02, 0.012, 0.018)) * (1.0 - smoothstep(0.0, 0.45, l));
      c *= mix(vec3(1.0), vec3(1.06, 1.0, 0.86), smoothstep(0.35, 0.95, l));
      // 夜景：偏青绿、再降饱和（参照战争片夜战的冷绿色调）
      c = mix(c, mix(vec3(l), c, 0.55) * vec3(0.82, 1.0, 0.94), night);
      c = clamp((c - 0.5) * 1.08 + 0.5 + 0.004, 0.0, 1.0);
      // 暗角
      c *= 1.0 - smoothstep(0.14, 0.62, r2 * 1.35) * 0.55;
      vec3 outc = toSRGB(c);
      // 胶片颗粒（按帧号确定）
      float g = h(floor(vUv * res) + vec2(frame * 17.0, frame * 31.0)) - 0.5;
      float g2 = h(floor(vUv * res * 0.5) + vec2(frame * 7.0, frame * 3.0)) - 0.5;
      outc += (g * 0.05 + g2 * 0.035) * (1.0 - abs(l - 0.45));
      gl_FragColor = vec4(outc, 1.0);
    }`,
});
const accumQuad = new THREE.Mesh(quadGeo, accumMat), gradeQuad = new THREE.Mesh(quadGeo, gradeMat);
const accumScene = new THREE.Scene(); accumScene.add(accumQuad);
const gradeScene = new THREE.Scene(); gradeScene.add(gradeQuad);

// ---------- labels（DOM，投影到 3D 位置） ----------
const LABELS = [
  { el: document.getElementById("label-objective"), pos: () => new THREE.Vector3(TARGET.x + 7, 16, TARGET.z + 3), on: (t) => t >= 17.2 && t < 20 },
  { el: document.getElementById("label-site-one"), pos: () => SITE1.clone().setY(12), on: (t) => (t >= 21.2 && t < 25) || (t >= 30.4 && t < 40) || (t >= 47.4 && t < 50) || t >= 51 },
  { el: document.getElementById("label-site-two"), pos: () => SITE2.clone().setY(12), on: (t) => t >= 31.4 && t < 40 },
  { el: document.getElementById("label-relief"), pos: () => nightConvoy[3].position.clone().setY(7), on: (t) => t >= 47.4 && t < 50 },
];
const timecode = document.getElementById("timecode");
function updateLabels(t) {
  for (const lb of LABELS) {
    if (!lb.el) continue;
    const p = lb.pos().project(camera);
    const x = (p.x * 0.5 + 0.5) * W, y = (-p.y * 0.5 + 0.5) * H;
    const inView = p.z < 1 && x > 80 && x < W - 80 && y > 60 && y < H - 40;
    lb.el.style.opacity = lb.on(t) && inView ? "1" : "0";
    lb.el.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px)`;
  }
  if (timecode) timecode.textContent = t < 40 ? "1993.10.03 · 15:30" : "1993.10.04 · 01:55";
}

// ---------- frame ----------
const SUBS = 4, SHUTTER = 0.5 / FPS; // 180° 快门
function drawScene(t) {
  const night = t >= 40 ? 1 : 0;
  setTimeOfDay(night);
  placeConvoys(t); placeHelis(t); updateParticles(t, night); placeConvoyLights(t, night);
  showRoute(dayRoute, t, 17.0, 18.6, 25);
  showRoute(linkRoute, t, 31.0, 32.6, 40);
  showRoute(reliefRoute, t, 47.0, 48.4);
  showRing(targetRing, t, 17.4, 25);
  showRing(site1Ring, t, 20.8, 99, true);
  showRing(site2Ring, t, 31.2, 99, true);
  return cameraAt(t);
}
function renderAt(value) {
  const t = Math.min(DURATION - 1e-4, Math.max(0, Number(value) || 0));
  const s = shotAt(t);
  renderer.autoClear = false;
  renderer.setRenderTarget(accumRT); renderer.setClearColor(0x000000, 0); renderer.clear();
  for (let i = 0; i < SUBS; i++) {
    const ts = Math.max(s.start, t - SHUTTER * (i / (SUBS - 1))); // 快门窗口不跨越剪辑点
    drawScene(ts);
    renderer.setRenderTarget(sceneRT); renderer.clear(); renderer.render(scene, camera);
    accumMat.uniforms.src.value = sceneRT.texture; accumMat.uniforms.weight.value = 1 / SUBS;
    renderer.setRenderTarget(accumRT); renderer.render(accumScene, quadCam);
  }
  drawScene(t);
  gradeMat.uniforms.frame.value = Math.round(t * FPS);
  renderer.setRenderTarget(null); renderer.clear(); renderer.render(gradeScene, quadCam);
  updateLabels(t);
}
window.addEventListener("hf-seek", (e) => renderAt(e.detail?.time ?? 0));
setTimeOfDay(0);
renderer.compile(scene, camera);
renderAt(window.__hfThreeTime || 0);
window.__worldReady && window.__worldReady();
