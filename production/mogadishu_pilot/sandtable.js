import * as THREE from "./vendor/three/three.bundle.js";

const W = 1920, H = 816;
const canvas = document.querySelector("#world");
const renderer = new THREE.WebGLRenderer({ canvas, antialias:true, alpha:false, powerPreference:"high-performance" });
renderer.setPixelRatio(1);
renderer.setSize(W, H, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.18;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x111614);
scene.fog = new THREE.Fog(0x111614, 22, 48);
const camera = new THREE.PerspectiveCamera(38, W / H, 0.1, 90);
scene.add(new THREE.HemisphereLight(0xd6cfbd, 0x29302b, 1.55));
scene.add(new THREE.AmbientLight(0xffffff, 0.22));
const key = new THREE.DirectionalLight(0xf0c38c, 3.25);
key.position.set(-9, 19, 7);
key.castShadow = true;
key.shadow.mapSize.set(2048,2048);
key.shadow.camera.left = -18; key.shadow.camera.right = 18;
key.shadow.camera.top = 16; key.shadow.camera.bottom = -16;
key.shadow.camera.near = 0.5; key.shadow.camera.far = 45;
key.shadow.bias = -0.00025;
scene.add(key, key.target);
key.target.position.set(0,0,0);
const rim = new THREE.DirectionalLight(0x8197a0, 1.2);
rim.position.set(10,11,-10); scene.add(rim);

const world = new THREE.Group(); scene.add(world);
const material = (color, roughness=0.86, metalness=0) => new THREE.MeshStandardMaterial({color,roughness,metalness});
function box(parent,size,pos,mat,cast=true,receive=true) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(...size),mat);
  m.position.set(...pos); m.castShadow=cast; m.receiveShadow=receive; parent.add(m); return m;
}
function seeded(a,b=0) { const n=Math.sin(a*127.1+b*311.7)*43758.5453123; return n-Math.floor(n); }

// Raised tabletop with deterministic sandy texture.
box(world,[24,0.82,16],[0,-0.46,0],material(0x242a27,0.7));
const texCanvas=document.createElement("canvas"); texCanvas.width=texCanvas.height=512;
const ctx=texCanvas.getContext("2d"); ctx.fillStyle="#6d6858"; ctx.fillRect(0,0,512,512);
for(let i=0;i<6200;i++){
  const a=0.025+(i*37%9)*0.004;
  ctx.fillStyle=i%2?"rgba(235,218,183,"+a+")":"rgba(24,27,24,"+a+")";
  ctx.fillRect(i*157.31%512,i*293.17%512,1+i%3,1+(i>>2)%2);
}
const terrainTexture=new THREE.CanvasTexture(texCanvas);
terrainTexture.colorSpace=THREE.SRGBColorSpace;
terrainTexture.wrapS=terrainTexture.wrapT=THREE.RepeatWrapping;
terrainTexture.repeat.set(3,2);
const terrain=new THREE.Mesh(new THREE.PlaneGeometry(23.5,15.5),new THREE.MeshStandardMaterial({map:terrainTexture,color:0xd5c6a3,roughness:1}));
terrain.rotation.x=-Math.PI/2; terrain.position.y=-0.045; terrain.receiveShadow=true; world.add(terrain);

// Schematic east coast and soft water lines.
const sea=new THREE.Mesh(new THREE.PlaneGeometry(5.2,15.4),material(0x31434a,0.42,0.05));
sea.rotation.x=-Math.PI/2; sea.position.set(9.05,-0.025,0); sea.receiveShadow=true; world.add(sea);
const beach=new THREE.Mesh(new THREE.PlaneGeometry(0.72,15.4),material(0xb49d71,1));
beach.rotation.x=-Math.PI/2; beach.position.set(6.2,-0.015,0); world.add(beach);
for(let i=0;i<7;i++){
  const pts=[];
  for(let j=0;j<=32;j++) pts.push(new THREE.Vector3(7.05+Math.sin(j*0.46+i*0.8)*0.09,0.005+i*0.001,-6.9+j*0.43));
  world.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),new THREE.LineBasicMaterial({color:0x94a1a0,transparent:true,opacity:0.12+(i%3)*0.025})));
}

// Street grid and procedural low-rise blocks. Open clearings mark the reported sites.
const road=material(0x363b37,0.98);
for(let x=-7.2;x<=7.21;x+=2.4) box(world,[0.34,0.035,13.7],[x,0.012,0],road,false,true);
for(let z=-6;z<=6.01;z+=2.4) box(world,[17.6,0.035,0.34],[-0.4,0.012,z],road,false,true);
const walls=[0x756e5e,0x827762,0x655f53,0x92866d,0x6c7068,0x817967];
const roofs=[0xaaa087,0x91866d,0x777363,0x847d6d,0xb3a487,0x696c64,0x98896e];
for(let ix=0;ix<8;ix++) for(let iz=0;iz<7;iz++){
  const x=-6.55+ix*1.72+(seeded(ix,iz)-0.5)*0.23;
  const z=-5.2+iz*1.72+(seeded(iz+4,ix+1)-0.5)*0.23;
    if(Math.hypot(x,z)<1.35 || Math.hypot(x+2.4,z-1.2)<1.25 || Math.hypot(x+2.4,z-3.6)<1.25 || seeded(ix+7,iz+3)<0.08) continue;
  const r=seeded(ix+11,iz+5), w=0.72+r*0.36, d=0.68+seeded(ix+3,iz+9)*0.38, h=0.38+seeded(ix+8,iz+14)*1.14;
  const wall=walls[Math.floor(r*walls.length)%walls.length];
  const roof=roofs[Math.floor(seeded(ix+2,iz+12)*roofs.length)%roofs.length];
  const body=box(world,[w,h,d],[x,h/2+0.02,z],material(wall,0.9)); body.rotation.y=(seeded(ix+17,iz+2)-0.5)*0.12;
  box(world,[w*0.94,0.055,d*0.94],[x,h+0.045,z],material(roof,0.92));
  if(r>0.68){const u=0.16+seeded(ix+21,iz+7)*0.11;box(world,[u,0.15,u],[x-w*0.18,h+0.14,z+d*0.16],material(0x59594f,0.96));}
}
for(const [x,z,w,d,h,c] of [
  [-0.15,-1.65,1,0.9,2.1,0x777361],[1.55,0.1,0.92,1.12,1.55,0x93866d],
  [3.25,-2.15,0.82,0.9,1.8,0x6f6c61],[0.9,3.3,1.1,0.82,1.35,0x8c806a]
]) {
  box(world,[w,h,d],[x,h/2+0.04,z],material(c,0.9));
  box(world,[w*0.94,0.06,d*0.94],[x,h+0.07,z],material(0xb2a487,0.95));
}

function ring(radius,color,tube=0.028,opacity=0.86){
  const r=new THREE.Mesh(new THREE.TorusGeometry(radius,tube,8,72),new THREE.MeshBasicMaterial({color,transparent:true,opacity,depthWrite:false}));
  r.rotation.x=-Math.PI/2; return r;
}
const objective=new THREE.Group(); objective.position.set(0,0.06,0);
objective.add(ring(0.82,0xe2c18a,0.026,0.68),ring(1.02,0xe2c18a,0.012,0.34));
const objStem=new THREE.Mesh(new THREE.CylinderGeometry(0.018,0.018,0.85,8),new THREE.MeshBasicMaterial({color:0xe2c18a,transparent:true,opacity:0.52}));
objStem.position.y=0.48; objective.add(objStem); world.add(objective);
function crashSite(x,z){
  const group=new THREE.Group(); group.position.set(x,0.06,z);
  const pulse=ring(0.62,0xe5794d,0.052,0.92), inner=ring(0.28,0xf0c286,0.025,0.82);
  const beacon=new THREE.Mesh(new THREE.OctahedronGeometry(0.19,0),new THREE.MeshBasicMaterial({color:0xf18a56})); beacon.position.y=0.52;
  const stem=new THREE.Mesh(new THREE.CylinderGeometry(0.018,0.018,0.52,6),new THREE.MeshBasicMaterial({color:0xe5794d,transparent:true,opacity:0.82})); stem.position.y=0.23;
  group.add(pulse,inner,beacon,stem); world.add(group); return {group,pulse,beacon,x,z};
}
const site1=crashSite(-2.4,1.2), site2=crashSite(-2.4,3.6);

// Dust haze rises above the markers; no graphic explosion or invented battlefield detail.
const smokeCanvas=document.createElement("canvas"); smokeCanvas.width=smokeCanvas.height=128;
const sctx=smokeCanvas.getContext("2d"), grad=sctx.createRadialGradient(64,64,4,64,64,62);
grad.addColorStop(0,"rgba(222,210,185,0.42)"); grad.addColorStop(0.32,"rgba(187,177,156,0.25)");
grad.addColorStop(0.72,"rgba(123,125,117,0.10)"); grad.addColorStop(1,"rgba(80,83,79,0)");
sctx.fillStyle=grad; sctx.fillRect(0,0,128,128);
const smokeTex=new THREE.CanvasTexture(smokeCanvas);
function dust(site){return Array.from({length:5},(_,i)=>{
  const s=new THREE.Sprite(new THREE.SpriteMaterial({map:smokeTex,color:0xc5bda9,transparent:true,opacity:0.3,depthWrite:false}));
  s.position.set(site.x+(seeded(i,site.x)-0.5)*0.45,0.55+i*0.38,site.z+(seeded(i+2,site.z)-0.5)*0.4);
    s.scale.set(1.3+i*0.28,1.7+i*0.34,1); scene.add(s); return s;
});}
const dust1=dust(site1),dust2=dust(site2);

function route(points,color,dash=0.42,gap=0.24,opacity=0.88){
  const curve=new THREE.CatmullRomCurve3(points.map(p=>new THREE.Vector3(...p)));
  const geometry=new THREE.BufferGeometry().setFromPoints(curve.getPoints(120));
  const line=new THREE.Line(geometry,new THREE.LineDashedMaterial({color,dashSize:dash,gapSize:gap,transparent:true,opacity,depthTest:false}));
  line.computeLineDistances(); line.frustumCulled=false; line.renderOrder=8; line.geometry.setDrawRange(0,0); scene.add(line);
  const dashes=[];
  for(let i=0;i<52;i++){
    const a=curve.getPointAt(i/52),b=curve.getPointAt(Math.min(1,(i+0.55)/52)),direction=new THREE.Vector3().subVectors(b,a);
    const dashMesh=new THREE.Mesh(new THREE.CylinderGeometry(0.048,0.048,direction.length(),7),new THREE.MeshBasicMaterial({color,transparent:true,opacity:Math.min(1,opacity+0.06),depthTest:false}));
    dashMesh.position.copy(a).add(b).multiplyScalar(0.5);
    dashMesh.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),direction.normalize());
    dashMesh.renderOrder=9;dashMesh.visible=false;scene.add(dashMesh);dashes.push(dashMesh);
  }
  return {line,curve,count:geometry.attributes.position.count,dashes};
}
const airPath=route([[0,2.4,0],[-0.7,2.4,0.2],[-1.3,2.4,0.5],[-1.9,2.4,0.85],[-2.4,2.4,1.2]],0xd9b879,0.27,0.18,0.82);
const reliefPath=route([[4.8,2.45,6],[4.8,2.45,3.6],[2.4,2.45,3.6],[2.4,2.45,1.2],[0,2.45,1.2],[-2.4,2.45,1.2]],0xf1aa62,0.42,0.2,0.96);
const arrow=new THREE.Mesh(new THREE.ConeGeometry(0.2,0.48,3),new THREE.MeshBasicMaterial({color:0xf4ad67,transparent:true,opacity:0.95,depthTest:false}));
arrow.rotation.x=Math.PI/2; arrow.position.set(-2.4,2.42,1.2); arrow.renderOrder=10; scene.add(arrow);

function vehicle(){
  const g=new THREE.Group(), body=material(0x71684f,0.72,0.12), glass=new THREE.MeshStandardMaterial({color:0x293437,metalness:0.28,roughness:0.4}), rubber=material(0x242927,0.95);
  box(g,[0.48,0.22,0.78],[0,0.27,0],body); box(g,[0.37,0.2,0.34],[0,0.47,-0.05],glass); box(g,[0.52,0.035,0.82],[0,0.39,0],material(0x9b8a67,0.8),false,false);
  for(const x of [-0.26,0.26]) for(const z of [-0.25,0.25]){const w=new THREE.Mesh(new THREE.CylinderGeometry(0.092,0.092,0.07,10),rubber);w.rotation.z=Math.PI/2;w.position.set(x,0.13,z);w.castShadow=true;g.add(w);}
  return g;
}
const groundPath=new THREE.CatmullRomCurve3([
  new THREE.Vector3(4.8,0.12,6),new THREE.Vector3(4.8,0.12,3.6),new THREE.Vector3(2.4,0.12,3.6),
  new THREE.Vector3(2.4,0.12,1.2),new THREE.Vector3(0,0.12,1.2),new THREE.Vector3(-2.4,0.12,1.2)
]);
const convoy=Array.from({length:4},()=>{const v=vehicle();v.scale.setScalar(1.45);scene.add(v);return v;});

function helicopter(){
  const h=new THREE.Group(), body=new THREE.Mesh(new THREE.SphereGeometry(0.42,16,10),material(0x55584f,0.66,0.18));
  body.scale.set(1.18,0.58,0.7);body.castShadow=true;h.add(body);
  const cockpit=new THREE.Mesh(new THREE.SphereGeometry(0.24,12,8),new THREE.MeshStandardMaterial({color:0x35444a,metalness:0.3,roughness:0.32}));
  cockpit.scale.set(0.92,0.52,0.75);cockpit.position.set(0,0.015,0.25);h.add(cockpit);
  const tail=new THREE.Mesh(new THREE.CylinderGeometry(0.045,0.07,1.05,8),material(0x4d524a,0.74,0.1));
  tail.rotation.x=Math.PI/2;tail.position.set(0,0,-0.76);h.add(tail);
  box(h,[0.42,0.055,0.14],[0,0.03,-1.22],material(0x55584f,0.7),false,false);
  const rotor=new THREE.Group();rotor.position.y=0.27;
  box(rotor,[1.88,0.028,0.09],[0,0,0],material(0x252a27,0.75),false,false);
  const blade=box(rotor,[1.88,0.028,0.09],[0,0,0],material(0x252a27,0.75),false,false);blade.rotation.y=Math.PI/2;
  h.add(rotor);h.userData.rotor=rotor;
  for(const x of [-0.38,0.38]){const skid=box(h,[0.06,0.055,1.15],[x,-0.24,0],material(0x2f3430,0.78),false,false);skid.castShadow=false;}
  scene.add(h);return h;
}
const heli=helicopter();
const flightPath=new THREE.CatmullRomCurve3([
  new THREE.Vector3(0,1.9,-0.35),new THREE.Vector3(-0.8,1.75,0.15),new THREE.Vector3(-1.6,1.48,0.7),new THREE.Vector3(-2.4,1.18,1.2)
]);

const cams=[
  {t:0,p:[16,18,21],a:[0,.3,0],f:39},{t:8,p:[13,14,17],a:[-.3,.35,0],f:37},
  {t:16,p:[9.6,11.5,13],a:[0,.35,0],f:35},{t:24,p:[7.5,8.9,9.4],a:[-2,.35,.8],f:34},
  {t:30,p:[8.2,8.6,8.2],a:[-2.3,.4,2.1],f:34},{t:35.5,p:[8.8,7.8,6.4],a:[-2.7,.4,3],f:33},
  {t:40,p:[14.2,15.5,17],a:[-.2,.35,.6],f:39},{t:45,p:[11.2,11.8,13.5],a:[-.8,.35,1.1],f:36},
  {t:50,p:[10,11.3,12.6],a:[-1,.4,1.2],f:35},{t:58,p:[16.4,18,20.5],a:[-.2,.3,.2],f:39},
  {t:60,p:[17.2,18.3,21],a:[0,.3,0],f:39}
];
const smooth=t=>t*t*(3-2*t);
function cameraAt(t){
  let i=0;while(i<cams.length-2&&t>cams[i+1].t)i++;
  const l=cams[i],r=cams[i+1],q=smooth(THREE.MathUtils.clamp((t-l.t)/(r.t-l.t),0,1));
  const mix=(x,y)=>x+(y-x)*q;
  camera.position.set(mix(l.p[0],r.p[0]),mix(l.p[1],r.p[1]),mix(l.p[2],r.p[2]));
  camera.fov=mix(l.f,r.f);camera.updateProjectionMatrix();
  camera.lookAt(mix(l.a[0],r.a[0]),mix(l.a[1],r.a[1]),mix(l.a[2],r.a[2]));
  camera.updateMatrixWorld(true);
  const impact=Math.max(0,1-Math.abs(t-22.3)/0.42);
  if(impact>0)camera.position.x+=Math.sin(t*48)*0.065*impact;
}
const labels=[
  ["label-objective",new THREE.Vector3(0,1.2,0),t=>t>=8&&t<32],
  ["label-site-one",new THREE.Vector3(-2.4,1.4,1.2),t=>t>=20&&t<60],
  ["label-site-two",new THREE.Vector3(-2.4,1.35,3.6),t=>t>=30&&t<42],
  ["label-relief",new THREE.Vector3(2.4,1.3,3.6),t=>t>=41&&t<51]
].map(([id,point,visible])=>({el:document.getElementById(id),point,visible}));
const projected=new THREE.Vector3();
function updateLabels(t){
  for(const l of labels){
    const show=l.visible(t);l.el.style.opacity=show?"1":"0";if(!show)continue;
    projected.copy(l.point).project(camera);
    const x=(projected.x*.5+.5)*W,y=(-projected.y*.5+.5)*H;
    l.el.style.transform="translate("+x+"px, "+y+"px) translate(-50%, -125%)";
  }
}
function showDust(sprites,t,start){
  const fade=THREE.MathUtils.clamp((t-start)/1.2,0,1)*(t>start+15?THREE.MathUtils.clamp((start+19-t)/4,0,1):1);
  sprites.forEach((s,i)=>{
    const phase=(t*.28+i*.19)%1.25;
    s.position.y=.5+i*.1+phase*.55;s.material.opacity=.2*fade*(1-i*.08);
    const size=.72+i*.17+phase*.22;s.scale.set(size,size*1.25,1);
  });
}
function showRoute(p,amount,t){
  const v=THREE.MathUtils.clamp(amount,0,1),visible=Math.floor(p.dashes.length*v);p.line.visible=v>0;p.line.geometry.setDrawRange(0,Math.floor(p.count*v));p.line.material.dashOffset=-t*.16;
  p.dashes.forEach((dash,i)=>{dash.visible=i<visible;});
}
function renderAt(value){
  const t=THREE.MathUtils.clamp(Number(value)||0,0,60);cameraAt(t);
  objective.visible=t>=8&&t<32;site1.group.visible=t>=20;site2.group.visible=t>=30;
  site1.pulse.scale.setScalar(.88+Math.sin(t*2.4)*.11);site2.pulse.scale.setScalar(.88+Math.sin(t*2.1+.8)*.11);
  site1.beacon.rotation.y=t*.42;site2.beacon.rotation.y=t*.4;
  site1.beacon.material.color.setHex(Math.sin(t*3.2)>.5?0xf5a268:0xe5794d);
  site2.beacon.material.color.setHex(Math.sin(t*3+.1)>.5?0xf5a268:0xe5794d);
  showRoute(airPath,(t-19.5)/3.6,t);showRoute(reliefPath,(t-40.6)/3.8,t);
  arrow.visible=t>=44.2;arrow.material.opacity=.78+Math.sin(t*3.4)*.13;
  const convoyProgress=THREE.MathUtils.clamp((t-41.5)/5.2,0,1);
  convoy.forEach((v,i)=>{
    const q=THREE.MathUtils.clamp(convoyProgress-i*.11,0,1);v.visible=t>=41.5&&(q>0||i===0);
    v.position.copy(groundPath.getPointAt(q));const tan=groundPath.getTangentAt(q);v.rotation.y=Math.atan2(tan.x,tan.z);
  });
  heli.visible=t>=16.8&&t<21.8;
  if(heli.visible){
    const q=THREE.MathUtils.clamp((t-16.8)/5,0,1);heli.position.copy(flightPath.getPoint(q));
    const tan=flightPath.getTangent(q);heli.rotation.y=Math.atan2(-tan.x,-tan.z);heli.userData.rotor.rotation.y=t*23;heli.rotation.z=Math.sin(t*4.1)*.035;
  }
  showDust(dust1,t,21.4);showDust(dust2,t,30.6);updateLabels(t);
  document.getElementById("timecode").textContent=t<40?"1993.10.03 · 15:30":"1993.10.04 · 01:55";
  renderer.render(scene,camera);
}
window.addEventListener("hf-seek",event=>renderAt(event.detail?.time??0));
renderer.compile(scene,camera);
renderAt(window.__hfThreeTime||0);
