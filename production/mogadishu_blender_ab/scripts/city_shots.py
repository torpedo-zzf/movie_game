# 全片写实 CG 航拍镜头（PLAN_FULL60.md）：程序化摩加迪沙城市 + TRELLIS.2 生成资产 + 黑鹰坠落/烟柱/夜间车队。
# 用法：Blender -b --factory-startup --python city_shots.py -- <输出目录> --shot S [--still F] [--samples N] [--pct P] [--no-render]
#   S ∈ 1, 2a, 2c, 3, 4, L1, 4A, 4B, 5, 6, L2, E1, E2, E3（2b 为 convoy_hero.py 的 13.5–16.5 s 贴地跟拍）
#   分支节点图（BRANCHING.md）：主干 1→2a→2b→2c→3→4，选择 1（L1 循环等待）→ 4A 第一处 / 4B 第二处 → 汇合 5（01:55）→ 6，
#   选择 2（L2 循环等待）→ E1 任务与救援 / E2 城市与平民 / E3 政策后果。
#   帧号 = 镜头内部时钟 t 的帧号（30 fps，t = (f-1)/30）；分支镜头沿用主干时钟，所以 4A/4B、E1–E3 帧号范围相同、输出到各自目录。
# 坐标：+Y 北、+X 东，米。目标区 T 在原点；第一坠机点 C1 在东北约三个街区；第二坠机点 C2 在南面不到一英里；海岸在南。
# 所有地点、路线均为非比例示意（与史料的相对关系一致，不代表测绘坐标）。
import bpy, bmesh, math, random, sys, os, glob
from mathutils import Vector, Matrix, Euler, noise as mnoise
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(argv[0] if argv else "renders/city")
arg = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
SHOT = arg("--shot", "1"); STILL = int(arg("--still")) if arg("--still") else None
SAMPLES = int(arg("--samples", 32)); RES_PCT = int(arg("--pct", 100))
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
GEN3D = os.path.join(ROOT, "assets", "gen3d")
FPS = 30
RANGES = {"1": (0, 10), "2a": (10, 13.5), "2c": (16.5, 20), "3": (20, 30), "4": (30, 35.5), "L1": (35.5, 39.5), "4A": (35.5, 45.5), "4B": (35.5, 45.5),
          "5": (40, 50), "6": (50, 57.5), "L2": (57.5, 61.5), "E1": (57.5, 65.5), "E2": (57.5, 65.5), "E3": (57.5, 65.5)}
AFTERNOON_POST = ("4", "L1", "4A", "4B"); LATE = ("5", "6", "L2", "E1", "E2", "E3")
TA, TB = RANGES[SHOT]
F0, F1 = int(round(TA * FPS)) + 1, int(round(TB * FPS))
NIGHT, DAWN = SHOT == "5", SHOT in ("6", "L2", "E1", "E2", "E3")
tf = lambda f: (f - 1) / FPS
FRAMES = range(F0 - 2, F1 + 3)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene; scene.render.fps = FPS; scene.frame_start, scene.frame_end = F0, F1
sys.path.insert(0, HERE)
from matlib import *  # MAT、pbr_mat、simple_mat、Builder、WALLS
rng = random.Random(19931003); R = lambda a=0.0, b=1.0: a + (b - a) * rng.random()

T = Vector((0, 0, 0)); C1 = Vector((150, 165, 0)); C2 = Vector((-330, -1240, 0))
coast = lambda x: -2050 + 140 * math.sin(x / 700 + 0.6) + 55 * math.sin(x / 230 + 2.0)
def ground_z(x, y):
    d = y - coast(x)  # >0 陆地
    return 0.0 if d > 80 else (-2.2 + 2.2 * max(0.0, d) / 80 if d > -400 else -2.2)

# ---------------- 额外材质 ----------------
MAT["leaf"] = simple_mat("leaf", (0.05, 0.07, 0.025), 0.8, noise=0.6, bump=0.5, scale=3)
MAT["tank"] = simple_mat("tank", (0.04, 0.05, 0.07), 0.5, noise=0.3)
MAT["roofslab"] = pbr_mat("roofslab", "worn_plaster_wall", tile=3.0, tint=(0.95, 0.9, 0.82), bump=0.4)
def emit_mat(name, col, strength):
    m, nt, out = node_mat(name); e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*col, 1); e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], out.inputs["Surface"]); return m, e
MAT["window_lit"] = emit_mat("window_lit", (1.0, 0.62, 0.3), 2.5)[0]

def ground_mat():
    """大尺度：沙土底 + 公里级明暗/色块（避免贴图在航拍高度重复）。"""
    m = pbr_mat("ground", "dry_ground_01", tile=4.0, tint=(1.05, 0.9, 0.72), bump=0.5, dirt=False)
    nt = m.node_tree; L = nt.links; b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    src = b.inputs["Base Color"].links[0].from_socket
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 0.004; n.inputs["Detail"].default_value = 8
    L.new(geo.outputs["Position"], n.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 0.6
    L.new(src, mx.inputs[6]); L.new(n.outputs["Color"], mx.inputs[7])
    n2 = nt.nodes.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 0.03; n2.inputs["Detail"].default_value = 4
    L.new(geo.outputs["Position"], n2.inputs["Vector"])
    r2 = nt.nodes.new("ShaderNodeMapRange"); r2.inputs["From Min"].default_value = 0.45; r2.inputs["From Max"].default_value = 0.7; r2.inputs["To Max"].default_value = 0.35
    L.new(n2.outputs["Fac"], r2.inputs["Value"])
    lt = nt.nodes.new("ShaderNodeMix"); lt.data_type = "RGBA"; lt.inputs[7].default_value = (0.78, 0.68, 0.52, 1)
    L.new(r2.outputs[0], lt.inputs["Factor"]); L.new(mx.outputs[2], lt.inputs[6]); L.new(lt.outputs[2], b.inputs["Base Color"])
    return m
MAT["ground"] = ground_mat()

def street_mat(name, asphalt):
    m = pbr_mat(name, "asphalt_03" if asphalt else "sandy_gravel", tile=3.0, tint=(0.95, 0.88, 0.76) if asphalt else (0.92, 0.8, 0.62), bump=0.5, dirt=False, rough_add=0.2)
    return m
MAT["street"] = street_mat("street", False); MAT["avenue"] = street_mat("avenue", True)

def water_mat():
    m, nt, out = node_mat("sea"); L = nt.links
    b = principled(nt, out, Roughness=0.2 if DAWN else 0.06, IOR=1.33)  # 黎明逆光：粗一点，免得太阳反光成一根白条
    b.inputs["Base Color"].default_value = (0.02, 0.09, 0.1, 1)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    mp = nt.nodes.new("ShaderNodeMapping"); mp.name = "seamap"; L.new(geo.outputs["Position"], mp.inputs["Vector"])
    w1 = nt.nodes.new("ShaderNodeTexWave"); w1.inputs["Scale"].default_value = 0.035; w1.inputs["Distortion"].default_value = 6; w1.inputs["Detail"].default_value = 4
    n1 = nt.nodes.new("ShaderNodeTexNoise"); n1.inputs["Scale"].default_value = 0.6; n1.inputs["Detail"].default_value = 6
    L.new(mp.outputs[0], w1.inputs["Vector"]); L.new(mp.outputs[0], n1.inputs["Vector"])
    ad = nt.nodes.new("ShaderNodeMath"); ad.operation = "ADD"; L.new(w1.outputs["Fac"], ad.inputs[0]); L.new(n1.outputs["Fac"], ad.inputs[1])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25; bp.inputs["Distance"].default_value = 0.4
    L.new(ad.outputs[0], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    # 近岸浅水泛青、浪花
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Position"], sep.inputs[0])
    return m, mp
SEA, SEAMAP = water_mat()

# ---------------- 地面、街道、海 ----------------
def grid_obj(name, x0, x1, y0, y1, nx, ny, zf, mat):
    bm = bmesh.new(); vs = []
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx; y = y0 + (y1 - y0) * j / ny
            vs.append(bm.verts.new((x, y, zf(x, y))))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i; bm.faces.new((vs[a], vs[a + 1], vs[a + nx + 2], vs[a + nx + 1]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(mat)
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob); return ob
grid_obj("ground", -6000, 6000, -3200, 5000, 240, 164, ground_z, MAT["ground"])
sea = grid_obj("sea", -20000, 20000, -30000, -1700, 1, 1, lambda x, y: -0.6, SEA)

# 街道网：主干道每 ~420 m（26 m 宽、沥青），次街每 ~75 m（9–12 m，土路）；整体略带扰动
XS, YS = [], []
x = -3000.0
while x < 3000: XS.append(x); x += R(62, 92)
y = coast(0) + 120
while y < 2800: YS.append(y); y += R(62, 92)
AVE_X = {i for i in range(len(XS)) if i % 6 == 2}; AVE_Y = {j for j in range(len(YS)) if j % 6 == 3}
def strip(bm, a, b, w, mi):
    d = (b - a); n = Vector((-d.y, d.x, 0)).normalized() * w / 2
    vs = [bm.verts.new(p) for p in (a - n, a + n, b + n, b - n)]
    bm.faces.new(vs).material_index = mi
sbm = bmesh.new()
for i, x in enumerate(XS):
    w = 26 if i in AVE_X else R(8, 12)
    strip(sbm, Vector((x, coast(x) + 40, 0.04)), Vector((x, 2900, 0.04)), w, 1 if i in AVE_X else 0)
for j, y in enumerate(YS):
    w = 26 if j in AVE_Y else R(8, 12)
    strip(sbm, Vector((-3100, y, 0.05)), Vector((3100, y, 0.05)), w, 1 if j in AVE_Y else 0)
sme = bpy.data.meshes.new("streets"); sbm.to_mesh(sme); sbm.free()
sme.materials.append(MAT["street"]); sme.materials.append(MAT["avenue"])
scene.collection.objects.link(bpy.data.objects.new("streets", sme))
def street_half(i, axis):
    return 13 if (i in (AVE_X if axis == "x" else AVE_Y)) else 6

# ---------------- 原型（隐藏集合；城市用几何节点实例化） ----------------
PROTO = bpy.data.collections.new("protos"); scene.collection.children.link(PROTO)
bpy.context.view_layer.layer_collection.children["protos"].exclude = True
protos = []  # (obj, w, d, kind)
def add_proto(ob, w, d, kind):
    for c in ob.users_collection: c.objects.unlink(ob)
    PROTO.objects.link(ob); ob.name = f"P{len(protos):03d}_{kind}"; protos.append((ob, w, d, kind)); return len(protos) - 1

def house(w, d, floors, rs, tin=False):
    B = Builder(); h = floors * 3.1 + 0.25; wall = rs.choice(WALLS)
    B.box(wall, (w, d, h), (0, 0, h / 2))
    if tin:
        B.hull("tin", [(-w / 2 - 0.3, -d / 2 - 0.3, h), (w / 2 + 0.3, -d / 2 - 0.3, h), (w / 2 + 0.3, d / 2 + 0.3, h), (-w / 2 - 0.3, d / 2 + 0.3, h)],
               [(-w / 2 - 0.3, -d / 2 - 0.3, h + 0.15), (w / 2 + 0.3, -d / 2 - 0.3, h + 0.15), (w / 2 + 0.3, d / 2 + 0.3, h + 0.75), (-w / 2 - 0.3, d / 2 + 0.3, h + 0.75)])
    else:
        B.box("roofslab", (w - 0.4, d - 0.4, 0.06), (0, 0, h + 0.03))
        for sx, sy, lx, ly in ((0, 1, w, 0.22), (0, -1, w, 0.22), (1, 0, 0.22, d), (-1, 0, 0.22, d)):
            B.box(wall, (lx, ly, 0.75), (sx * (w / 2 - 0.11), sy * (d / 2 - 0.11), h + 0.37))
        if floors >= 2 and rs.random() < 0.7: B.box(wall, (2.6, 3.2, 2.4), (rs.uniform(-w / 4, w / 4), rs.uniform(-d / 4, d / 4), h + 1.2))
        if rs.random() < 0.6: B.cyl("tank", 0.6, 0.6, 1.1, (rs.uniform(-w / 3, w / 3), rs.uniform(-d / 3, d / 3), h + 0.6), seg=12)
        if rs.random() < 0.3: B.box("tin", (rs.uniform(2, 4), rs.uniform(2, 3), 0.08), (rs.uniform(-w / 4, w / 4), rs.uniform(-d / 4, d / 4), h + 2.0), rot=(0.08, 0, 0))
    shut = rs.choice(["wood", "paint_b", "dark", "shutter"])
    for fl in range(floors):
        z = fl * 3.1 + 1.7
        for side, L_, ax in ((1, w, "x"), (-1, w, "x"), (1, d, "y"), (-1, d, "y")):
            n = max(1, int(L_ / 3.2))
            for k in range(n):
                if rs.random() < 0.25: continue
                u = (k + 0.5) / n * L_ - L_ / 2
                lit = NIGHT and rs.random() < 0.06
                key = "window_lit" if lit else ("dark" if rs.random() < 0.6 else shut)
                if ax == "x": B.box(key, (1.0, 0.12, 1.25), (u, side * (d / 2 + 0.02), z))
                else: B.box(key, (0.12, 1.0, 1.25), (side * (w / 2 + 0.02), u, z))
    B.box(rs.choice(["paint_b", "shutter", "wood", "rust"]), (1.3, 0.14, 2.2), (rs.uniform(-w / 3, w / 3), -d / 2 - 0.03, 1.1))
    return B.obj("house", bevel=0.03)

def compound(w, d, rs):
    B = Builder(); h = rs.uniform(2.2, 2.8); wall = rs.choice(WALLS); g = 3.0
    B.box(wall, (w, 0.25, h), (0, d / 2, h / 2)); B.box(wall, (0.25, d, h), (w / 2, 0, h / 2)); B.box(wall, (0.25, d, h), (-w / 2, 0, h / 2))
    B.box(wall, ((w - g) / 2, 0.25, h), (-(w + g) / 4, -d / 2, h / 2)); B.box(wall, ((w - g) / 2, 0.25, h), ((w + g) / 4, -d / 2, h / 2))
    B.box(rs.choice(["tin", "rust", "paint_b"]), (g, 0.08, h - 0.2), (0, -d / 2, (h - 0.2) / 2))
    return B.obj("compound", bevel=0.02)

def tree(rs, s):
    B = Builder(); th = rs.uniform(2.5, 4.0) * s
    B.cyl("wood", 0.18 * s, 0.12 * s, th, (0, 0, th / 2), seg=8)
    mi = B.mi("leaf")
    for k in range(rs.randint(4, 7)):
        M = Matrix.Translation((rs.uniform(-1.6, 1.6) * s, rs.uniform(-1.6, 1.6) * s, th + rs.uniform(0.3, 1.4) * s)) @ Matrix.Diagonal((rs.uniform(1.4, 2.4) * s, rs.uniform(1.4, 2.4) * s, rs.uniform(0.6, 1.0) * s, 1))
        r = bmesh.ops.create_icosphere(B.bm, subdivisions=2, radius=1.0, matrix=M)
        for f in {f for v in r["verts"] for f in v.link_faces}: f.material_index = mi
    return B.obj("tree", bevel=0)

prs = random.Random(7)
HOUSES = []
for w, d in ((7, 8), (9, 9), (10, 12), (12, 10), (13, 14), (16, 12), (18, 15)):
    for floors in (1, 2, 3):
        if floors == 3 and w < 10: continue
        for v in range(2):
            tin = floors == 1 and v == 1
            HOUSES.append(add_proto(house(w, d, floors, prs, tin), w, d, f"h{floors}"))
WALLP = [add_proto(compound(w, d, prs), w, d, "wall") for w, d in ((14, 18), (18, 22), (24, 26), (30, 28))]
TREES = [add_proto(tree(prs, s), 4, 4, "tree") for s in (0.8, 1.0, 1.3)]

def load_glb(path):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]; ob = [o for o in new if o.type == "MESH"][0]
    me = ob.data; me.transform(ob.matrix_world)
    for o in new: bpy.data.objects.remove(o)
    return me
def norm_mesh(me, size=None, height=None, rot=0.0):
    """居中落地；size=最长水平边，height=高度。"""
    import numpy as np
    co = np.array([v.co for v in me.vertices]); mn, mx = co.min(0), co.max(0)
    k = size / max(mx[0] - mn[0], mx[1] - mn[1]) if size else height / (mx[2] - mn[2])
    me.transform(Matrix.Rotation(rot, 4, "Z") @ Matrix.Scale(k, 4) @ Matrix.Translation(Vector((-(mn[0] + mx[0]) / 2, -(mn[1] + mx[1]) / 2, -mn[2]))))
    return me
def matte(me, dust=0.15, rough=0.75):
    for m in me.materials:
        nt = m.node_tree; b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        if b.inputs["Metallic"].links: nt.links.remove(b.inputs["Metallic"].links[0])
        b.inputs["Metallic"].default_value = 0.0
        if b.inputs["Roughness"].links: nt.links.remove(b.inputs["Roughness"].links[0])
        b.inputs["Roughness"].default_value = rough
        if b.inputs["Base Color"].links and dust > 0:
            src = b.inputs["Base Color"].links[0].from_socket
            mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.inputs["Factor"].default_value = dust; mx.inputs[7].default_value = (0.6, 0.5, 0.37, 1)
            nt.links.new(src, mx.inputs[6]); nt.links.new(mx.outputs[2], b.inputs["Base Color"])

GENB = []
for p in sorted(glob.glob(os.path.join(GEN3D, "city", "trellis_b*_300_1.glb"))):
    if "b5" in p: continue  # 五层楼作为目标区地标单独放置
    if os.path.basename(p) == "trellis_b1_300_1.glb": continue  # b1 只生成出一面薄墙，不合格
    me = norm_mesh(load_glb(p), size=14.0); matte(me, 0.1, 0.85)
    ob = bpy.data.objects.new("genb", me); scene.collection.objects.link(ob)
    GENB.append(add_proto(ob, 14, 14, "gen"))
print("CITY protos", len(protos), "gen buildings", len(GENB))

# ---------------- 地块布置 → 点云属性 → 几何节点实例化 ----------------
pts = []  # (x, y, z, rotz, sx, sy, sz, proto)
def clear_zone(x, y):
    return (Vector((x, y, 0)) - C1).length < 16 or (Vector((x, y, 0)) - C2).length < 16 or abs(x - T.x) < 26 and abs(y - T.y) < 18
lrs = random.Random(11)
for i in range(len(XS) - 1):
    for j in range(len(YS) - 1):
        bx0, bx1 = XS[i] + street_half(i, "x"), XS[i + 1] - street_half(i + 1, "x")
        by0, by1 = YS[j] + street_half(j, "y"), YS[j + 1] - street_half(j + 1, "y")
        cx = (bx0 + bx1) / 2
        if by0 < coast(cx) + 70: continue
        dist = math.hypot(cx, (by0 + by1) / 2)
        fringe = max(0.0, (dist - 2300) / 900)  # 城外稀疏
        rows = [(by0, (by0 + by1) / 2, 0.0), ((by0 + by1) / 2, by1, math.pi)] if by1 - by0 > 34 else [(by0, by1, 0.0)]
        for ry0, ry1, face in rows:
            x = bx0
            while x < bx1 - 6:
                lw = min(lrs.uniform(12, 26), bx1 - x); ld = ry1 - ry0
                lx, ly = x + lw / 2, (ry0 + ry1) / 2; x += lw
                if lrs.random() < fringe or clear_zone(lx, ly): continue
                near = math.hypot(lx, ly) < 700
                if lrs.random() < 0.55 and ld > 12:  # 院墙 + 院内房屋 + 树
                    wp = min(WALLP, key=lambda k: abs(protos[k][1] - lw) + abs(protos[k][2] - ld))
                    pts.append((lx, ly, 0, face, lw / protos[wp][1], ld / protos[wp][2], 1, wp))
                    cand = [k for k in HOUSES if protos[k][1] < lw - 3 and protos[k][2] < ld * 0.6]
                    if cand:
                        hp = lrs.choice(cand); hd = protos[hp][2]
                        pts.append((lx + lrs.uniform(-1, 1), ly + (ld / 2 - hd / 2 - 1.5) * (1 if face == 0 else -1), 0, face, 1, 1, 1, hp))
                    if lrs.random() < 0.45:
                        pts.append((lx + lrs.uniform(-lw / 3, lw / 3), ly - (ld / 4) * (1 if face == 0 else -1), 0, lrs.uniform(0, 6.28), 1, 1, 1, lrs.choice(TREES)))
                else:
                    if GENB and near and lrs.random() < 0.3:
                        gp = lrs.choice(GENB); s = min(lw, ld) / 14 * 0.95
                        pts.append((lx, ly, 0, face + lrs.choice([0, math.pi / 2, math.pi, -math.pi / 2]), s, s, s, gp)); continue
                    cand = [k for k in HOUSES if protos[k][1] <= lw + 1 and protos[k][2] <= ld + 1]
                    if near: cand = [k for k in cand if not protos[k][3] == "h1"] or cand
                    if cand:
                        hp = lrs.choice(cand)
                        pts.append((lx, ly, 0, face, min(1.15, lw / protos[hp][1]), min(1.15, ld / protos[hp][2]), 1, hp))
print("CITY instances", len(pts))

pme = bpy.data.meshes.new("city_pts"); pme.vertices.add(len(pts))
pme.vertices.foreach_set("co", [c for p in pts for c in p[:3]])
a = pme.attributes.new("proto", "INT", "POINT"); a.data.foreach_set("value", [p[7] for p in pts])
a = pme.attributes.new("rot", "FLOAT_VECTOR", "POINT"); a.data.foreach_set("vector", [c for p in pts for c in (0, 0, p[3])])
a = pme.attributes.new("scl", "FLOAT_VECTOR", "POINT"); a.data.foreach_set("vector", [c for p in pts for c in p[4:7]])
city = bpy.data.objects.new("city", pme); scene.collection.objects.link(city)
ng = bpy.data.node_groups.new("scatter", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
N = ng.nodes; LK = ng.links
gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
iop = N.new("GeometryNodeInstanceOnPoints"); ci = N.new("GeometryNodeCollectionInfo")
ci.inputs["Collection"].default_value = PROTO; ci.inputs["Separate Children"].default_value = True; ci.inputs["Reset Children"].default_value = True
def named(name, dt):
    n = N.new("GeometryNodeInputNamedAttribute"); n.data_type = dt; n.inputs["Name"].default_value = name; return n.outputs["Attribute"]
LK.new(gi.outputs[0], iop.inputs["Points"]); LK.new(ci.outputs[0], iop.inputs["Instance"])
iop.inputs["Pick Instance"].default_value = True
LK.new(named("proto", "INT"), iop.inputs["Instance Index"])
LK.new(named("rot", "FLOAT_VECTOR"), iop.inputs["Rotation"]); LK.new(named("scl", "FLOAT_VECTOR"), iop.inputs["Scale"])
LK.new(iop.outputs[0], go.inputs[0])
city.modifiers.new("scatter", "NODES").node_group = ng

# ---------------- 目标区地标（Olympic Hotel 样式五层楼） ----------------
hotel_glb = os.path.join(GEN3D, "city", "trellis_b5_300_1.glb")
if os.path.exists(hotel_glb):
    me = norm_mesh(load_glb(hotel_glb), size=40.0); matte(me, 0.08, 0.85)
    hotel = bpy.data.objects.new("hotel", me)
else:
    hotel = house(40, 22, 5, random.Random(3)); hotel.name = "hotel"
    for c in hotel.users_collection: c.objects.unlink(hotel)
scene.collection.objects.link(hotel); hotel.location = (T.x, T.y, 0)

# ---------------- 黑鹰 ----------------
def load_heli():
    """TRELLIS 黑鹰：机长 19.8 m（含旋翼）、机头朝 +Y；删去主旋翼桨叶（改用程序化旋转桨叶 + 运动模糊）。"""
    import numpy as np
    cands = sorted(glob.glob(os.path.join(GEN3D, "heli", "trellis_bh*_300_1.glb")))
    if not cands: return None
    me = load_glb(cands[0]); co = np.array([v.co for v in me.vertices]); mn, mx = co.min(0), co.max(0)
    ax = 0 if (mx[0] - mn[0]) > (mx[1] - mn[1]) else 1
    rot = math.pi / 2 if ax == 0 else 0.0
    me = norm_mesh(me, size=19.8, rot=rot)
    co = np.array([v.co for v in me.vertices]); zmid = (co[:, 2].min() + co[:, 2].max()) / 2
    lowy = co[co[:, 2] < zmid][:, 1]
    if (lowy > 0).sum() < (lowy < 0).sum(): me.transform(Matrix.Rotation(math.pi, 4, "Z")); co[:, :2] *= -1
    top = co[:, 2].max()
    hub = co[(np.abs(co[:, 0]) < 0.8) & (np.abs(co[:, 1] - 1.0) < 3)][:, 2].max() if True else top
    bm = bmesh.new(); bm.from_mesh(me)
    kill = [f for f in bm.faces if (lambda c: c.z > hub - 0.35 and math.hypot(c.x, c.y - 0.6) > 1.4)(f.calc_center_median())]
    bmesh.ops.delete(bm, geom=kill, context="FACES"); bm.to_mesh(me); bm.free()
    matte(me, 0.05, 0.6)
    print("HELI", os.path.basename(cands[0]), len(me.polygons), "faces hub", round(float(hub), 2))
    return me, float(hub)
HELI = load_heli()
BLADE = None
def rotor_mesh():
    B = Builder()
    for k in range(4):
        a = k * math.pi / 2
        B.box("rubber", (0.53, 8.0, 0.08), (math.sin(a) * 4.2, math.cos(a) * 4.2, 0), rot=(0.03, 0, -a))
    B.cyl("steel", 0.45, 0.35, 0.5, (0, 0, -0.1), seg=12)
    ob = B.obj("rotor", bevel=0); me = ob.data; bpy.data.objects.remove(ob); return me
def heli(name):
    root = bpy.data.objects.new(name, None); scene.collection.objects.link(root)
    if HELI:
        me, hub = HELI
        body = bpy.data.objects.new(name + "_body", me)
    else:
        B = Builder(); B.hull("olive", [(-1, 4, 0.8), (1, 4, 0.8), (1, -3, 0.8), (-1, -3, 0.8)], [(-0.9, 3.5, 2.6), (0.9, 3.5, 2.6), (0.9, -3, 2.6), (-0.9, -3, 2.6)])
        B.box("olive", (0.5, 7.5, 0.7), (0, -6.6, 2.1)); B.box("olive", (0.15, 1.2, 2.0), (0, -10.2, 2.8))
        body = B.obj(name + "_body", bevel=0.05); hub = 3.6
    scene.collection.objects.link(body) if body.name not in scene.collection.objects else None
    body.parent = root
    global BLADE
    if BLADE is None: BLADE = rotor_mesh()
    rot = bpy.data.objects.new(name + "_rotor", BLADE); scene.collection.objects.link(rot); rot.parent = root; rot.location = (0, 0.6, hub + 0.1)
    return root, body, rot
def spin_rotor(rot, rps=4.3):
    for f in (F0 - 2, F1 + 3):
        rot.rotation_euler = (0, 0, -2 * math.pi * rps * tf(f)); rot.keyframe_insert("rotation_euler", frame=f)
    for fc in rot.animation_data.action.fcurves if hasattr(rot.animation_data.action, "fcurves") else []:
        for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
def set_lin(ob):
    ad = ob.animation_data
    if ad and ad.action and hasattr(ad.action, "fcurves"):
        for fc in ad.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
def fly(root, posf, headf, bankf=lambda t: 0.0, pitchf=lambda t: -0.05):
    for f in FRAMES:
        t = tf(f); root.location = posf(t); root.rotation_euler = (pitchf(t), bankf(t), headf(t))
        root.keyframe_insert("location", frame=f); root.keyframe_insert("rotation_euler", frame=f)

# ---------------- 体积：烟柱 / 尘团 ----------------
def smoke_column(name, base, t_start, dark=0.06, height=420, wind=(0.22, 0.08)):
    """缓慢上升的烟柱：盒子体积，噪声随时间上移；半径随高度增大，顶部被风吹斜。"""
    ob = bpy.data.objects.new(name, bpy.data.meshes.new(name))
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((wind[0] * height * 0.5, wind[1] * height * 0.5, height / 2)) @ Matrix.Diagonal((height * 0.55, height * 0.55, height, 1)))
    bm.to_mesh(ob.data); bm.free(); scene.collection.objects.link(ob); ob.location = base
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); L = nt.links
    vol = nt.nodes.new("ShaderNodeVolumePrincipled"); vol.inputs["Color"].default_value = (dark, dark * 0.95, dark * 0.9, 1); vol.inputs["Anisotropy"].default_value = 0.25
    out = nt.nodes.new("ShaderNodeOutputMaterial"); L.new(vol.outputs[0], out.inputs["Volume"])
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    def math_(op, a, b):
        n = nt.nodes.new("ShaderNodeMath"); n.operation = op
        for i, v in enumerate((a, b)):
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: L.new(v, n.inputs[i])
        return n.outputs[0]
    z = sep.outputs["Z"]
    cx = math_("SUBTRACT", sep.outputs["X"], math_("MULTIPLY", z, wind[0])); cy = math_("SUBTRACT", sep.outputs["Y"], math_("MULTIPLY", z, wind[1]))
    r = math_("SQRT", math_("ADD", math_("MULTIPLY", cx, cx), math_("MULTIPLY", cy, cy)), 0)
    rad = math_("ADD", 6.0, math_("MULTIPLY", z, 0.16))
    fall = nt.nodes.new("ShaderNodeMapRange"); L.new(math_("DIVIDE", r, rad), fall.inputs["Value"]); fall.inputs["From Min"].default_value = 0.35; fall.inputs["From Max"].default_value = 1.0
    fall.inputs["To Min"].default_value = 1; fall.inputs["To Max"].default_value = 0
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (0.045, 0.045, 0.025); L.new(tc.outputs["Object"], mp.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.noise_dimensions = "4D"; nz.inputs["Scale"].default_value = 1.0; nz.inputs["Detail"].default_value = 7; nz.inputs["Roughness"].default_value = 0.6
    L.new(mp.outputs[0], nz.inputs["Vector"])
    th = nt.nodes.new("ShaderNodeMapRange"); L.new(nz.outputs["Fac"], th.inputs["Value"]); th.inputs["From Min"].default_value = 0.42; th.inputs["From Max"].default_value = 0.7
    grow = nt.nodes.new("ShaderNodeMapRange"); grow.name = "grow"; L.new(z, grow.inputs["Value"])  # 上升前沿：只在 z < 前沿 处有烟
    grow.inputs["From Min"].default_value = 0; grow.inputs["To Min"].default_value = 1; grow.inputs["To Max"].default_value = 0
    topf = nt.nodes.new("ShaderNodeMapRange"); L.new(z, topf.inputs["Value"]); topf.inputs["From Min"].default_value = height * 0.55; topf.inputs["From Max"].default_value = height
    topf.inputs["To Min"].default_value = 1; topf.inputs["To Max"].default_value = 0
    dens = math_("MULTIPLY", math_("MULTIPLY", math_("MULTIPLY", fall.outputs[0], th.outputs[0]), grow.outputs[0]), topf.outputs[0])
    dens = math_("MULTIPLY", dens, math_("DIVIDE", 1.2, math_("ADD", 1.0, math_("MULTIPLY", z, 0.02))))
    L.new(dens, vol.inputs["Density"]); ob.data.materials.append(m)
    for f in FRAMES:
        t = tf(f); age = max(0.0, t - t_start)
        grow.inputs["From Max"].default_value = 0.01 + age * 9.0 if age < 60 else height
        grow.inputs["From Max"].keyframe_insert("default_value", frame=f)
        mp.inputs["Location"].default_value = (0, 0, -t * 0.12); mp.inputs["Location"].keyframe_insert("default_value", frame=f)
        nz.inputs["W"].default_value = t * 0.05; nz.inputs["W"].keyframe_insert("default_value", frame=f)
        ob.hide_render = age <= 0; ob.keyframe_insert("hide_render", frame=f)
    return ob

def puff_mat(name, col, aniso=0.3):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); L = nt.links
    out = nt.nodes.new("ShaderNodeOutputMaterial"); vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (*col, 1); vol.inputs["Anisotropy"].default_value = aniso
    tc = nt.nodes.new("ShaderNodeTexCoord"); n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 2.0; n.inputs["Detail"].default_value = 6
    L.new(tc.outputs["Object"], n.inputs["Vector"])
    gr = nt.nodes.new("ShaderNodeTexGradient"); gr.gradient_type = "SPHERICAL"; L.new(tc.outputs["Object"], gr.inputs["Vector"])
    mu = nt.nodes.new("ShaderNodeMath"); mu.operation = "MULTIPLY"; L.new(n.outputs["Fac"], mu.inputs[0]); L.new(gr.outputs["Fac"], mu.inputs[1])
    rm = nt.nodes.new("ShaderNodeMapRange"); rm.inputs["From Min"].default_value = 0.04; rm.inputs["From Max"].default_value = 0.3; L.new(mu.outputs[0], rm.inputs["Value"])
    d = nt.nodes.new("ShaderNodeMath"); d.operation = "MULTIPLY"; d.inputs[1].default_value = 0.0
    L.new(rm.outputs[0], d.inputs[0]); L.new(d.outputs[0], vol.inputs["Density"]); L.new(vol.outputs[0], out.inputs["Volume"])
    return m, d.inputs[1]
def puff(name, col, track):
    """track(t) → (位置, 半径, 密度) 或 None（不可见）。"""
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob)
    m, dens = puff_mat(name, col); me.materials.append(m); ob.rotation_euler = (R(0, 3), R(0, 3), R(0, 3))
    for f in FRAMES:
        st = track(tf(f))
        if st is None: p, r_, d_ = Vector((0, 0, -500)), 0.01, 0.0
        else: p, r_, d_ = st
        ob.location = p; ob.scale = (r_, r_, r_ * 0.8); dens.default_value = d_
        ob.keyframe_insert("location", frame=f); ob.keyframe_insert("scale", frame=f); dens.keyframe_insert("default_value", frame=f)
    return ob

def rotor_wash(center, t0=0.0):
    """悬停黑鹰下方的旋翼下洗扬尘：一圈向外翻滚的扁平尘团。"""
    for k in range(10):
        ang = k * 0.63; off = k * 0.23
        def tr(t, ang=ang, off=off):
            a = ((t - t0) + off) % 2.3
            r = 6 + a * 9
            return (center + Vector((math.cos(ang + a * 0.2) * r, math.sin(ang + a * 0.2) * r, 1.0 + a * 1.2)), 3 + a * 3.5, 0.5 * math.sin(math.pi * a / 2.3))
        puff(f"wash_{center.x:.0f}_{k}", (0.8, 0.68, 0.5), tr)

# ---------------- 镜头事件 ----------------
T_HIT, T_IMPACT = 22.3, 25.9
HIT_P = C1 + Vector((-95, -70, 46))
def s61_pos(t):
    """Super 61：沿东北向航线低空飞行；被击中后打转、减速、下坠，坠入 C1 街巷。"""
    d = (C1 - HIT_P.xy.to_3d()); d.z = 0; d.normalize()
    if t <= T_HIT: return HIT_P + d * 28 * (t - T_HIT) + Vector((0, 0, 1.5 * math.sin(t)))
    s = min(1.0, (t - T_HIT) / (T_IMPACT - T_HIT))
    end = C1 + Vector((0, 0, 1.2))
    xy = HIT_P.lerp(end, 1 - (1 - s) ** 1.6)
    return Vector((xy.x, xy.y, HIT_P.z * (1 - s ** 1.7) + 1.2 * s ** 1.7))
def s61_head(t):
    d = C1 - HIT_P; base = math.atan2(-d.x, d.y)
    if t <= T_HIT: return base
    dt = t - T_HIT; return base + 2 * math.pi * (0.25 * dt * dt + 0.2 * dt) if t < T_IMPACT else s61_head(T_IMPACT - 1e-3)
def s61_bank(t):
    if t <= T_HIT: return 0.0
    return min(1.2, 0.35 * (t - T_HIT)) if t < T_IMPACT else 1.25
def tail_world(t):
    head = s61_head(t)
    return s61_pos(t) + Vector((-math.sin(head) * -8.5, math.cos(head) * -8.5, 2.2))

def build_events():
    if SHOT == "3" or SHOT in AFTERNOON_POST + LATE:
        h, body, rot = heli("super61")
        fly(h, s61_pos, s61_head, s61_bank, lambda t: -0.08 if t < T_HIT else -0.2)
        for f in FRAMES:
            t = tf(f); rot.rotation_euler = (0, 0, -2 * math.pi * 4.3 * min(t, T_IMPACT)); rot.keyframe_insert("rotation_euler", frame=f)
        set_lin(rot)
        if SHOT == "3":
            fl, e = emit_mat("flash", (1.0, 0.7, 0.35), 0.0)
            bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0); me = bpy.data.meshes.new("flash"); bm.to_mesh(me); bm.free(); me.materials.append(fl)
            fo = bpy.data.objects.new("flash", me); scene.collection.objects.link(fo)
            for f in FRAMES:
                t = tf(f); a = t - T_HIT
                fo.location = tail_world(t); fo.scale = (1.1,) * 3
                e.inputs["Strength"].default_value = 300 * math.exp(-a * 40) if 0 <= a < 0.15 else 0.0
                fo.keyframe_insert("location", frame=f); fo.keyframe_insert("scale", frame=f); e.inputs["Strength"].keyframe_insert("default_value", frame=f)
            # 尾部拖出的烟：每 0.05 s 从尾部放一团（彼此重叠成连续烟带），原地扩散、变淡
            for k in range(72):
                te = T_HIT + 0.05 + k * 0.05
                def tr(t, te=te):
                    a = t - te
                    if a < 0 or te > T_IMPACT: return None
                    return (tail_world(te) + Vector((0.6 * a, 0.3 * a, 0.8 * a)), 2.4 + a * 2.2, 0.8 * math.exp(-a * 0.45))
                puff(f"trail_{k}", (0.07, 0.065, 0.06), tr)
            # 坠地冲击：扬起的尘土 + 黑烟
            for k in range(14):
                ang = k * 2.4; spd = 4 + (k % 4) * 2.5
                def tr(t, ang=ang, spd=spd, k=k):
                    a = t - T_IMPACT
                    if a < 0: return None
                    r = spd * (1 - math.exp(-a * 0.8)) * 3
                    return (C1 + Vector((math.cos(ang) * r, math.sin(ang) * r, 2 + a * (2.5 + k % 3))), 4 + a * 3.5, (2.0 if k % 2 else 1.2) * math.exp(-a * 0.25))
                puff(f"impact_{k}", (0.62, 0.52, 0.38) if k % 2 else (0.08, 0.075, 0.07), tr)
        if SHOT == "3" or SHOT in AFTERNOON_POST: smoke_column("col1", C1, T_IMPACT + 0.8)
        else: smoke_column("col1", C1, -60.0, height=380)
        if SHOT in AFTERNOON_POST: smoke_column("col2", C2, 31.6)
        if SHOT in LATE: smoke_column("col2", C2, -60.0, height=380)
        if SHOT in AFTERNOON_POST + LATE:
            # Super 64 残骸：侧翻在 C2 街巷里，旋翼停转（不渲染冲击过程，只交代结果）
            h2, b2, r2 = heli("super64"); h2.location = C2 + Vector((0, 0, 0.9)); h2.rotation_euler = (0.12, 1.05, 2.3)
            r2.rotation_euler = (0.25, 0, 0.4)
        if SHOT == "4A":
            # 搜救直升机在第一坠机点上空悬停、索降搜救小组（远景，只见下洗扬尘）
            h3, b3, r3 = heli("csar"); spin_rotor(r3)
            fly(h3, lambda t: C1 + Vector((-14, -10, 26 + 0.6 * math.sin(t * 0.8))), lambda t: 0.9 + 0.02 * math.sin(t * 0.5), lambda t: 0.02 * math.sin(t))
            rotor_wash(C1 + Vector((-14, -10, 0)))
            for k, (ang, rad, alt) in enumerate(((0.8, 260, 140), (3.6, 340, 170))):
                h4, b4, r4 = heli(f"cover_{k}"); spin_rotor(r4)
                fly(h4, lambda t, ang=ang, rad=rad, alt=alt: C1 + Vector((math.cos(ang + 0.1 * t) * rad, math.sin(ang + 0.1 * t) * rad, alt)),
                    lambda t, ang=ang: ang + 0.1 * t + math.pi, lambda t: -0.25)
    if SHOT in ("1", "2a", "2c", "3"):
        # 目标区上空悬停/盘旋的其他直升机（远景）
        for k, (ang, rad, alt) in enumerate(((0.3, 30, 26), (2.4, 34, 30), (4.2, 220, 90), (1.4, 300, 110))):
            h, body, rot = heli(f"heli_{k}"); spin_rotor(rot)
            hover = rad < 60
            def pos(t, ang=ang, rad=rad, alt=alt, hover=hover):
                a = ang + (0.02 if hover else 0.09) * t
                return T + Vector((math.cos(a) * rad, math.sin(a) * rad, alt + 0.8 * math.sin(t * 0.7 + ang)))
            def hd(t, ang=ang, hover=hover):
                a = ang + (0.02 if hover else 0.09) * t
                return a + (math.pi if not hover else 0.6)
            fly(h, pos, hd, (lambda t: 0.0) if hover else (lambda t: -0.25))
            if hover and SHOT in ("2a", "2c"): rotor_wash(T + Vector((math.cos(ang) * rad, math.sin(ang) * rad, 0)))
build_events()

# ---------------- 车队（2c 白天抵达目标；5 夜间救援） ----------------
def vehicle_mesh(kind):
    p = {"humvee": os.path.join(GEN3D, "humvee", "trellis_s5_300_1.glb")}.get(kind) or (sorted(glob.glob(os.path.join(GEN3D, "vehicles", f"trellis_{kind}*_300_1.glb"))) or [None])[0]
    if p and os.path.exists(p):
        # 各模型车头朝向不同：悍马/坦克/卡车转 180° 后车头朝 +Y；APC 生成时车头朝 -X，需再转 -90°
        me = load_glb(p); me = norm_mesh(me, size={"humvee": 4.57, "apc": 6.0, "tank": 9.3}.get(kind, 5), rot=math.pi / 2 if kind == "apc" else math.pi)
        matte(me, 0.18, 0.7); return me
    B = Builder(); B.box("tan", (2.3, 5.5, 1.5), (0, 0, 1.1)); ob = B.obj(kind, bevel=0.08); me = ob.data; bpy.data.objects.remove(ob); return me
def convoy(path, n, gap, speed, t_start, kinds, lights=False):
    meshes = {k: vehicle_mesh(k) for k in set(kinds)}
    L_ = [0.0]
    for i in range(1, len(path)): L_.append(L_[-1] + (path[i] - path[i - 1]).length)
    def at(s):
        s = max(0.0, min(L_[-1] - 0.01, s))
        for i in range(1, len(L_)):
            if s <= L_[i]:
                u = (s - L_[i - 1]) / (L_[i] - L_[i - 1]); return path[i - 1].lerp(path[i], u), (path[i] - path[i - 1]).normalized()
    for v in range(n):
        kind = kinds[v % len(kinds)]
        ob = bpy.data.objects.new(f"cv_{v}", meshes[kind]); scene.collection.objects.link(ob)
        heads = []
        if lights:
            for sx in (-0.7, 0.7):
                sp = bpy.data.objects.new(f"hl_{v}_{sx}", bpy.data.lights.new(f"hl_{v}_{sx}", "SPOT")); scene.collection.objects.link(sp)
                sp.data.energy = 900; sp.data.spot_size = math.radians(55); sp.data.spot_blend = 0.6; sp.data.color = (1.0, 0.88, 0.7); sp.data.shadow_soft_size = 0.08
                sp.parent = ob; sp.location = (sx, 2.4, 1.0); sp.rotation_euler = (math.radians(80), 0, 0); heads.append(sp)
        for f in FRAMES:
            s = speed * (tf(f) - t_start) - v * gap
            p, d = at(s)
            ob.location = (p.x, p.y, 0.02 + 0.03 * math.sin(tf(f) * 7 + v)); ob.rotation_euler = (0, 0, math.atan2(-d.x, d.y))
            ob.keyframe_insert("location", frame=f); ob.keyframe_insert("rotation_euler", frame=f)
    return at
STREET_X_C1 = min(XS, key=lambda x: abs(x - C1.x)); STREET_Y_T = min(YS, key=lambda y: abs(y - (T.y - 30)))
if SHOT == "2c":
    path = [Vector((-900, STREET_Y_T, 0)), Vector((STREET_X_C1 - 160, STREET_Y_T, 0))]
    CONVOY_AT = convoy(path, 9, 16, 7.5, 20.0 - 750 / 7.5, ["humvee", "humvee", "truck"])  # 头车 20 s 时到目标西侧街口
if SHOT == "5":
    sy0 = min(YS, key=lambda y: abs(y - (C1.y - 420)))
    path = [Vector((STREET_X_C1 - 600, sy0, 0)), Vector((STREET_X_C1, sy0, 0)), Vector((STREET_X_C1, C1.y - 12, 0))]
    L0 = 600 + (C1.y - 12 - sy0)
    CV_T0 = 50.0 - L0 / 9.0  # 头车 50 s 抵达 C1
    CONVOY_AT = convoy(path, 10, 18, 9.0, CV_T0, ["apc", "humvee", "tank", "apc", "humvee"], lights=True)
    # 街上零星燃烧的轮胎路障与院内灯火
    frs = random.Random(5)
    for k in range(90):
        big = k < 12  # 大火：沿车队路线附近的燃烧轮胎路障（带烟）；其余为院内零星灯火
        if big: x, y = STREET_X_C1 + frs.uniform(-500, 60), sy0 + frs.uniform(-15, 420); x = x if frs.random() < 0.5 else STREET_X_C1 + frs.uniform(-4, 4)
        else: x, y = frs.uniform(-1500, 1500), frs.uniform(-1200, 1500)
        lt = bpy.data.objects.new(f"fire_{k}", bpy.data.lights.new(f"fire_{k}", "POINT")); scene.collection.objects.link(lt)
        e0 = (6000 if big else 500) * frs.uniform(0.6, 1.2)
        lt.data.energy = e0; lt.data.color = (1.0, 0.45, 0.12) if big else (1.0, 0.62, 0.3); lt.data.shadow_soft_size = 1.0
        lt.location = (x, y, 1.2 if big else 3.0)
        if big:
            for f in range(F0 - 2, F1 + 3, 2):
                lt.data.energy = e0 * (0.8 + 0.4 * mnoise.noise(Vector((k * 3.1, tf(f) * 4, 0)))); lt.data.keyframe_insert("energy", frame=f)
            smoke_column(f"firesmoke_{k}", Vector((x, y, 0)), -60.0, dark=0.03, height=90, wind=(0.3, 0.1))
if SHOT == "E1":
    # 天亮后车队载着伤员和阵亡者离开第一坠机点（与第 5 镜同一条路线反向）
    sy0 = min(YS, key=lambda y: abs(y - (C1.y - 420)))
    path = [Vector((STREET_X_C1, C1.y - 20, 0)), Vector((STREET_X_C1, sy0, 0)), Vector((STREET_X_C1 - 900, sy0, 0))]
    CV_T0 = 57.5 - 210 / 4.5  # 末车刚离开坠机点
    CONVOY_AT = convoy(path, 12, 17, 4.5, CV_T0, ["apc", "humvee", "tank", "apc", "humvee", "truck"], lights=True)
if SHOT == "E2":
    # 清晨街巷：居民站在门口和路边，望向仍在冒烟的坠机点（不出现伤者、不特写）
    PEOPLE = []
    for p in sorted(glob.glob(os.path.join(GEN3D, "people", "trellis_*_300_1.glb"))):
        me = norm_mesh(load_glb(p), height=1.72 * (0.82 if "m4" in p else 1.0), rot=math.pi); matte(me, 0.12, 0.78); PEOPLE.append(me)
    if not PEOPLE:
        B = Builder(); B.box("tan", (0.45, 0.3, 1.7), (0, 0, 0.85)); ob = B.obj("pfb", bevel=0.05); PEOPLE = [ob.data]; bpy.data.objects.remove(ob)
    prs2 = random.Random(77)
    for k in range(80):
        y = C1.y - 340 + prs2.uniform(0, 300); side = prs2.choice((-1, 1))
        x = STREET_X_C1 + side * prs2.uniform(3.2, 5.2)
        ob = bpy.data.objects.new(f"pp{k}", prs2.choice(PEOPLE)); scene.collection.objects.link(ob)
        d = (C1 - Vector((x, y, 0))).normalized() if prs2.random() < 0.6 else Vector((-side, prs2.uniform(-0.5, 0.5), 0)).normalized()
        ob.location = (x, y, 0.04); ob.rotation_euler = (0, 0, math.atan2(d.x, -d.y) + prs2.uniform(-0.4, 0.4))

# ---------------- 光照与天空 ----------------
if NIGHT:
    sun_dir = Vector((0.4, -0.3, 0.75)).normalized(); sun_col, sun_E = (0.55, 0.65, 1.0), 0.12
elif DAWN:
    sun_dir = Vector((0.93, -0.25, 0.07)).normalized(); sun_col, sun_E = (1.0, 0.62, 0.38), 3.5
else:
    sun_dir = Vector((-0.837, -0.224, 0.5)).normalized(); sun_col, sun_E = (1.0, 0.86, 0.68), 6.0  # 约 16:00，西南偏西
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); scene.collection.objects.link(sun)
sun.data.energy = sun_E; sun.data.angle = math.radians(3.0 if DAWN else 0.6); sun.data.color = sun_col
sun.rotation_euler = sun_dir.to_track_quat("Z", "Y").to_euler()
world = bpy.data.worlds.new("world"); scene.world = world; world.use_nodes = True
wn = world.node_tree; wn.nodes.clear()
sky = wn.nodes.new("ShaderNodeTexSky")
types = [i.identifier for i in sky.bl_rna.properties["sky_type"].enum_items]
for want in ("MULTIPLE_SCATTERING", "SINGLE_SCATTERING", "NISHITA", "HOSEK_WILKIE"):
    if want in types: sky.sky_type = want; break
for at_, val in (("sun_elevation", max(math.asin(sun_dir.z), -0.05 if NIGHT else 0.02)), ("sun_rotation", math.atan2(sun_dir.x, sun_dir.y) + math.pi),
                 ("air_density", 1.6), ("dust_density", 5.0), ("altitude", 30.0)):
    if hasattr(sky, at_):
        try: setattr(sky, at_, val)
        except Exception: pass
if hasattr(sky, "sun_disc"): sky.sun_disc = False  # 低角度太阳盘在尘霾里会拉成一根白条
bg = wn.nodes.new("ShaderNodeBackground")
warm = wn.nodes.new("ShaderNodeMix"); warm.data_type = "RGBA"; warm.blend_type = "MULTIPLY"; warm.inputs["Factor"].default_value = 1.0
warm.inputs[7].default_value = (0.25, 0.32, 0.55, 1) if NIGHT else ((1.0, 0.8, 0.65, 1) if DAWN else (1.0, 0.86, 0.68, 1))
wn.links.new(sky.outputs[0], warm.inputs[6]); wn.links.new(warm.outputs[2], bg.inputs[0])
bg.inputs["Strength"].default_value = 0.004 if NIGHT else (0.25 if DAWN else 0.32)
if NIGHT:
    nb = wn.nodes.new("ShaderNodeBackground"); nb.inputs["Color"].default_value = (0.012, 0.018, 0.035, 1); nb.inputs["Strength"].default_value = 1.0
    add = wn.nodes.new("ShaderNodeAddShader"); wn.links.new(bg.outputs[0], add.inputs[0]); wn.links.new(nb.outputs[0], add.inputs[1]); bgo = add.outputs[0]
else: bgo = bg.outputs[0]
wo = wn.nodes.new("ShaderNodeOutputWorld"); wn.links.new(bgo, wo.inputs["Surface"])

# 大气透视：整座城市罩一层均匀尘霾
haze = bpy.data.objects.new("haze", bpy.data.meshes.new("haze"))
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, -2000, 700)) @ Matrix.Diagonal((24000, 30000, 1400, 1))); bm.to_mesh(haze.data); bm.free()
scene.collection.objects.link(haze)
hm = bpy.data.materials.new("haze"); hm.use_nodes = True; nt = hm.node_tree; nt.nodes.clear()
hv = nt.nodes.new("ShaderNodeVolumePrincipled")
hv.inputs["Color"].default_value = (0.35, 0.42, 0.6, 1) if NIGHT else ((0.95, 0.72, 0.55, 1) if DAWN else (0.92, 0.78, 0.6, 1))
hv.inputs["Density"].default_value = 0.00035 if NIGHT else (0.00015 if DAWN else 0.00012); hv.inputs["Anisotropy"].default_value = 0.5
ho = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(hv.outputs[0], ho.inputs["Volume"]); haze.data.materials.append(hm)

# 海面波纹缓慢移动
for f in (F0 - 2, F1 + 3):
    SEAMAP.inputs["Location"].default_value = (tf(f) * 0.6, tf(f) * 0.9, 0); SEAMAP.inputs["Location"].keyframe_insert("default_value", frame=f)

# ---------------- 摄影机 ----------------
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); scene.collection.objects.link(cam); scene.camera = cam
cam.data.sensor_fit = "VERTICAL"; cam.data.sensor_height = 24; cam.data.clip_start = 0.5; cam.data.clip_end = 40000
def cr(keys, t):
    """Catmull-Rom 插值 keys=[(t, Vector)]，端点外夹紧；输入时间做 smoothstep 让起止更柔。"""
    ts = [k[0] for k in keys]
    if t <= ts[0]: return keys[0][1].copy()
    if t >= ts[-1]: return keys[-1][1].copy()
    i = max(j for j in range(len(ts) - 1) if ts[j] <= t)
    p0 = keys[max(i - 1, 0)][1]; p1 = keys[i][1]; p2 = keys[i + 1][1]; p3 = keys[min(i + 2, len(keys) - 1)][1]
    u = (t - ts[i]) / (ts[i + 1] - ts[i])
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)
def shake(t, amp, seed=1):
    return Vector(tuple(sum(mnoise.noise(Vector((seed * 13.1 + a * 7.3, t * fr, 0))) * amp / k for k, fr in ((1, 0.35), (2.5, 1.1))) for a in range(3)))
c1z = lambda z: C1 + Vector((0, 0, z))
if SHOT == "1":
    FOV = lambda t: 34
    POS = [(0, Vector((-500, -3900, 620))), (5, Vector((-350, -3050, 520))), (10, Vector((-240, -2300, 420)))]
    LOOK = [(0, Vector((150, -300, 0))), (10, Vector((80, -150, 0)))]
elif SHOT == "2a":
    FOV = lambda t: 42
    POS = [(10, Vector((-430, -360, 70))), (11.8, Vector((-250, -220, 52))), (13.5, Vector((-110, -120, 46)))]
    LOOK = [(10, Vector((0, 0, 18))), (13.5, Vector((0, 0, 14)))]
elif SHOT == "2c":
    FOV = lambda t: 36
    POS = [(16.5, Vector((-260, -230, 120))), (18.3, Vector((-300, -90, 125))), (20, Vector((-290, 60, 130)))]
    LOOK = [(16.5, Vector((-120, STREET_Y_T, 0))), (20, Vector((-40, -10, 5)))]
elif SHOT == "3":
    FOV = lambda t: 9.5 if t < T_IMPACT + 0.6 else 9.5 + (t - T_IMPACT - 0.6) * 1.6   # 长焦跟拍，坠地后慢慢松开
    POS = [(20, Vector((210, -260, 115))), (30, Vector((240, -210, 125)))]
    LOOK = None
def orbit(t):
    u = (t - 30) / 10; a = math.radians(-60 + 95 * u); r = 380 + 600 * u * u; z = 180 + 420 * u
    return C1 + Vector((math.cos(a) * r, math.sin(a) * r, z))
LOOK4 = [(30, c1z(60)), (35, (C1 * 0.6 + C2 * 0.4) + Vector((0, 0, 40))), (40, (C1 * 0.45 + C2 * 0.55) + Vector((0, 0, 20)))]
POS6 = [(50, c1z(160) + Vector((-260, -200, 0))), (53.75, c1z(380) + Vector((-700, -520, 0))), (57.5, c1z(640) + Vector((-1150, -900, 0)))]
LOOK6 = [(50, c1z(20)), (53.75, Vector((700, -900, 0))), (57.5, Vector((2200, -2400, 0)))]
loop_drift = lambda t, amp: Vector((math.sin(2 * math.pi * t / 4) * amp, math.cos(2 * math.pi * t / 4) * amp * 0.6, math.sin(4 * math.pi * t / 4) * amp * 0.3))  # 4 s 周期，循环片段首尾相接
if SHOT == "4":
    FOV = lambda t: 30
    POS = [(t, orbit(t)) for t in (30, 32.5, 35, 37.5, 40)]; LOOK = LOOK4
elif SHOT == "L1":
    FOV = lambda t: 30
    POS = None; LOOK = None
elif SHOT == "4A":
    # 从环绕位俯冲到第一坠机点：残骸、悬停的搜救直升机和下洗扬尘
    FOV = lambda t: 30 + 6 * min(1, (t - 35.5) / 10)
    P4, L4 = orbit(35.5), cr(LOOK4, 35.5)
    POS = [(35.5, P4), (39, C1 + Vector((-260, -330, 200))), (42.5, C1 + Vector((-160, -190, 90))), (45.5, C1 + Vector((-100, -120, 58)))]
    LOOK = [(35.5, L4), (39, c1z(20)), (45.5, c1z(8))]
elif SHOT == "4B":
    # 向南飞越城区，接近第二根烟柱和孤立的第二坠机点
    FOV = lambda t: 30 + 4 * min(1, (t - 35.5) / 10)
    P4, L4 = orbit(35.5), cr(LOOK4, 35.5)
    POS = [(35.5, P4), (40, C2 + Vector((330, 760, 430))), (45.5, C2 + Vector((190, 320, 160)))]
    LOOK = [(35.5, L4), (40, C2 + Vector((0, 0, 70))), (45.5, C2 + Vector((0, 0, 10)))]
elif SHOT == "5":
    FOV = lambda t: 40
    POS = None; LOOK = None
elif SHOT == "6":
    FOV = lambda t: 38
    POS = POS6; LOOK = LOOK6
elif SHOT == "L2":
    FOV = lambda t: 38
    POS = None; LOOK = None
elif SHOT == "E1":
    FOV = lambda t: 34
    POS = None; LOOK = None
elif SHOT == "E2":
    # 贴着街巷缓慢前推，人群背影望向前方的烟柱
    FOV = lambda t: 40
    POS = [(57.5, Vector((STREET_X_C1 + 1.5, C1.y - 360, 22))), (65.5, Vector((STREET_X_C1 + 0.5, C1.y - 150, 17)))]
    LOOK = [(57.5, Vector((STREET_X_C1, C1.y - 230, 2))), (65.5, Vector((STREET_X_C1, C1.y + 20, 30)))]
elif SHOT == "E3":
    # 从城市上空退到海面上，回望晨光中的摩加迪沙与两根烟柱
    FOV = lambda t: 36
    POS = [(57.5, Vector((-1000, -735, 640))), (61.5, Vector((-760, -2200, 520))), (65.5, Vector((-520, -3400, 380)))]
    LOOK = [(57.5, Vector((500, -500, 0))), (65.5, Vector((120, 0, 90)))]
for f in FRAMES:
    t = tf(f)
    if SHOT == "3":
        tgt = s61_pos(min(t, T_IMPACT)) if t < T_IMPACT + 0.4 else C1 + Vector((0, 0, min(30.0, (t - T_IMPACT) * 7)))
        lag = s61_pos(max(20, min(t, T_IMPACT) - 0.25))
        look = tgt.lerp(lag, 0.35) + shake(t, 1.2, 4)
        pos = cr(POS, t) + shake(t, 1.5, 2)
    elif SHOT == "L1":
        pos = orbit(35.5) + loop_drift(t, 4.0); look = cr(LOOK4, 35.5) + loop_drift(t + 1, 2.0)
    elif SHOT == "L2":
        pos = cr(POS6, 57.5) + loop_drift(t, 6.0); look = cr(LOOK6, 57.5) + loop_drift(t + 1, 4.0)
    elif SHOT == "E1":
        p, d = CONVOY_AT(4.5 * (t - CV_T0) - 4 * 17)  # 跟第 5 辆车，高位斜跟
        u = (t - 57.5) / 8
        pos = p - d * (110 - 20 * u) + Vector((60, 0, 80 + 40 * u)) + shake(t, 1.0, 6)
        look = p + d * 40 + Vector((0, 0, 2))
    elif SHOT == "5":
        p, d = CONVOY_AT(9.0 * (t - CV_T0) - 3 * 18)  # 跟第 4 辆车
        u = (t - 40) / 10
        pos = p - d * (70 - 25 * u) + Vector((-30, 0, 55 + 35 * u)) + shake(t, 1.2, 5)
        look = p + d * 25 + Vector((0, 0, 2))
    else:
        pos = cr(POS, t) + shake(t, 0.8 if SHOT in ("1", "6", "E3") else 1.0, 3); look = cr(LOOK, t)
    cam.location = pos; cam.rotation_euler = (look - pos).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = 12.0 / math.tan(math.radians(FOV(t)) / 2)  # 竖向视角 → 焦距（sensor_height 24）
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f); cam.data.keyframe_insert("lens", frame=f)

# ---------------- 渲染设置 ----------------
r = scene.render
r.engine = "CYCLES"; r.resolution_x, r.resolution_y = 1920, 816; r.resolution_percentage = RES_PCT
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.use_persistent_data = True
r.image_settings.file_format = "PNG"; r.image_settings.color_depth = "16"
r.use_overwrite = False; r.use_placeholder = True  # 中断后重跑会跳过已渲染的帧
cy = scene.cycles
prefs = bpy.context.preferences.addons["cycles"].preferences; prefs.compute_device_type = "METAL"; prefs.get_devices()
for dv in prefs.devices: dv.use = dv.type == "METAL"
cy.device = "GPU"; cy.samples = SAMPLES; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.03
cy.use_denoising = True; cy.max_bounces = 5; cy.diffuse_bounces = 2; cy.glossy_bounces = 2; cy.volume_bounces = 1; cy.transparent_max_bounces = 4
cy.volume_step_rate = 4.0; cy.seed = 1993; cy.use_animated_seed = True
try:
    scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Punchy"
    scene.view_settings.exposure = 2.0 if NIGHT else 0.0
except Exception: pass
os.makedirs(OUT, exist_ok=True); r.filepath = os.path.join(OUT, "f_####")
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f"city_shot{SHOT}.blend"))
if "--no-render" in argv: pass
elif STILL:
    scene.frame_set(STILL); r.filepath = os.path.join(OUT, f"still_{STILL:04d}"); bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
