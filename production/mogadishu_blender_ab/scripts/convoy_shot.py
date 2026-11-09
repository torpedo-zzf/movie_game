# 车队贴地跟拍镜头（Blender Cycles 版），与 mogadishu_pilot/world.js 中 13.5–16.5 s 的 "convoy-close" 镜头对位。
# 用法：Blender -b --factory-startup --python convoy_shot.py -- <输出目录> [--still FRAME] [--samples N]
# 坐标：Three.js (x, y, z) → Blender (x, -z, y)；车队沿 +y（北）行驶。全部程序化、固定种子。
import bpy, bmesh, math, random, sys, os
from mathutils import Vector, Matrix, Euler

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(argv[0] if argv else "renders/convoy")
STILL = int(argv[argv.index("--still") + 1]) if "--still" in argv else None
SAMPLES = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 64
RES_PCT = int(argv[argv.index("--pct") + 1]) if "--pct" in argv else 100

FPS, T0, T1 = 30, 13.5, 16.5
LANE_X, SPEED = -2.4, 11.2
lead_y = lambda t: -max(-44.0, 122 - SPEED * (t - 8.5))  # Blender y of lead vehicle
rng = random.Random(19931003)
R = lambda a=0.0, b=1.0: a + (b - a) * rng.random()
pick = lambda seq: seq[int(rng.random() * len(seq)) % len(seq)]

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = FPS
scene.frame_start, scene.frame_end = 1, int(round((T1 - T0) * FPS))

# ---------------- materials ----------------
def node_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    return m, nt, out

def principled(nt, out, **kw):
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    for k, v in kw.items():
        if k in b.inputs: b.inputs[k].default_value = v
    nt.links.new(b.outputs[0], out.inputs["Surface"]); return b

def plaster_mat():
    """灰泥墙：按物体随机墙色、多尺度斑驳、墙根沾尘、雨痕、剥落与弹孔凹凸。"""
    m, nt, out = node_mat("plaster"); L = nt.links
    b = principled(nt, out, Roughness=0.9)
    geo = nt.nodes.new("ShaderNodeNewGeometry"); info = nt.nodes.new("ShaderNodeObjectInfo")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cols = ["#efe8d9", "#e3d3b2", "#d9c39a", "#c7d3d2", "#e6cfc0", "#d8d2c6", "#c9b48c", "#f2eee6"]
    el = ramp.color_ramp.elements
    while len(el) < len(cols): el.new(0)
    for i, c in enumerate(cols):
        el[i].position = i / (len(cols) - 1)
        el[i].color = tuple(int(c[j:j + 2], 16) / 255 for j in (1, 3, 5)) + (1,)
    ramp.color_ramp.interpolation = "CONSTANT"
    L.new(info.outputs["Random"], ramp.inputs[0])
    # 斑驳
    n1 = nt.nodes.new("ShaderNodeTexNoise"); n1.inputs["Scale"].default_value = 0.6; n1.inputs["Detail"].default_value = 8
    L.new(geo.outputs["Position"], n1.inputs["Vector"])
    mott = nt.nodes.new("ShaderNodeMix"); mott.data_type = "RGBA"; mott.blend_type = "MULTIPLY"; mott.inputs["Factor"].default_value = 0.35
    L.new(ramp.outputs[0], mott.inputs[6]); L.new(n1.outputs["Color"], mott.inputs[7])
    # 雨痕：沿竖直方向拉伸的噪声
    mapn = nt.nodes.new("ShaderNodeMapping"); mapn.inputs["Scale"].default_value = (3.0, 3.0, 0.25)
    L.new(geo.outputs["Position"], mapn.inputs["Vector"])
    n2 = nt.nodes.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 2.0; n2.inputs["Detail"].default_value = 3
    L.new(mapn.outputs[0], n2.inputs["Vector"])
    streak = nt.nodes.new("ShaderNodeMapRange"); streak.inputs["From Min"].default_value = 0.55; streak.inputs["From Max"].default_value = 0.75
    streak.inputs["To Min"].default_value = 0; streak.inputs["To Max"].default_value = 0.35
    L.new(n2.outputs["Fac"], streak.inputs["Value"])
    dirt = (0.33, 0.27, 0.19, 1)
    m2 = nt.nodes.new("ShaderNodeMix"); m2.data_type = "RGBA"; m2.inputs[7].default_value = dirt
    L.new(streak.outputs[0], m2.inputs["Factor"]); L.new(mott.outputs[2], m2.inputs[6])
    # 墙根沾尘
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Position"], sep.inputs[0])
    base = nt.nodes.new("ShaderNodeMapRange"); base.inputs["From Min"].default_value = 0.0; base.inputs["From Max"].default_value = 2.2
    base.inputs["To Min"].default_value = 0.55; base.inputs["To Max"].default_value = 0.0
    L.new(sep.outputs["Z"], base.inputs["Value"])
    m3 = nt.nodes.new("ShaderNodeMix"); m3.data_type = "RGBA"; m3.inputs[7].default_value = (0.62, 0.5, 0.35, 1)
    L.new(base.outputs[0], m3.inputs["Factor"]); L.new(m2.outputs[2], m3.inputs[6])
    # 剥落斑块（Voronoi）露出更深的水泥
    vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 1.4
    L.new(geo.outputs["Position"], vor.inputs["Vector"])
    n3 = nt.nodes.new("ShaderNodeTexNoise"); n3.inputs["Scale"].default_value = 1.1; n3.inputs["Detail"].default_value = 6
    L.new(geo.outputs["Position"], n3.inputs["Vector"])
    peel = nt.nodes.new("ShaderNodeMapRange"); peel.inputs["From Min"].default_value = 0.66; peel.inputs["From Max"].default_value = 0.7
    L.new(n3.outputs["Fac"], peel.inputs["Value"])
    m4 = nt.nodes.new("ShaderNodeMix"); m4.data_type = "RGBA"; m4.inputs[7].default_value = (0.47, 0.42, 0.35, 1)
    L.new(peel.outputs[0], m4.inputs["Factor"]); L.new(m3.outputs[2], m4.inputs[6])
    L.new(m4.outputs[2], b.inputs["Base Color"])
    # 凹凸：细颗粒 + 剥落边缘 + 弹孔
    pock = nt.nodes.new("ShaderNodeTexVoronoi"); pock.inputs["Scale"].default_value = 9.0; pock.feature = "F1"
    L.new(geo.outputs["Position"], pock.inputs["Vector"])
    pk = nt.nodes.new("ShaderNodeMapRange"); pk.inputs["From Min"].default_value = 0.0; pk.inputs["From Max"].default_value = 0.06
    pk.inputs["To Min"].default_value = -1; pk.inputs["To Max"].default_value = 0
    L.new(pock.outputs["Distance"], pk.inputs["Value"])
    grain = nt.nodes.new("ShaderNodeTexNoise"); grain.inputs["Scale"].default_value = 40; grain.inputs["Detail"].default_value = 4
    L.new(geo.outputs["Position"], grain.inputs["Vector"])
    hsum = nt.nodes.new("ShaderNodeMath"); hsum.operation = "ADD"
    L.new(grain.outputs["Fac"], hsum.inputs[0]); L.new(peel.outputs[0], hsum.inputs[1])
    hsum2 = nt.nodes.new("ShaderNodeMath"); hsum2.operation = "MULTIPLY_ADD"
    L.new(pk.outputs[0], hsum2.inputs[0]); hsum2.inputs[1].default_value = 0.25; L.new(hsum.outputs[0], hsum2.inputs[2])
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.35; bump.inputs["Distance"].default_value = 0.02
    L.new(hsum2.outputs[0], bump.inputs["Height"]); L.new(bump.outputs[0], b.inputs["Normal"])
    return m

def simple_mat(name, color, rough=0.8, metal=0.0, noise=0.25, bump=0.15, scale=6.0):
    m, nt, out = node_mat(name); L = nt.links
    b = principled(nt, out, Roughness=rough, Metallic=metal)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = 6
    L.new(geo.outputs["Position"], n.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = noise
    mx.inputs[6].default_value = color + (1,); L.new(n.outputs["Color"], mx.inputs[7])
    L.new(mx.outputs[2], b.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.01
    L.new(n.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m

def tan_paint():
    """沙漠黄车漆：边角磨损 + 车身下部积尘（Pointiness 与高度）。"""
    m, nt, out = node_mat("tan_paint"); L = nt.links
    b = principled(nt, out, Roughness=0.62, Metallic=0.05)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    paint = (0.47, 0.38, 0.24, 1); dust = (0.6, 0.5, 0.36, 1)
    obj = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); L.new(obj.outputs["Object"], sep.inputs[0])
    low = nt.nodes.new("ShaderNodeMapRange"); low.inputs["From Min"].default_value = 0.2; low.inputs["From Max"].default_value = 1.4
    low.inputs["To Min"].default_value = 0.8; low.inputs["To Max"].default_value = 0.15
    L.new(sep.outputs["Z"], low.inputs["Value"])
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 3.5; n.inputs["Detail"].default_value = 8
    L.new(obj.outputs["Object"], n.inputs["Vector"])
    f = nt.nodes.new("ShaderNodeMath"); f.operation = "MULTIPLY"; L.new(low.outputs[0], f.inputs[0]); L.new(n.outputs["Fac"], f.inputs[1])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.inputs[6].default_value = paint; mx.inputs[7].default_value = dust
    L.new(f.outputs[0], mx.inputs["Factor"])
    wear = nt.nodes.new("ShaderNodeMapRange"); wear.inputs["From Min"].default_value = 0.53; wear.inputs["From Max"].default_value = 0.6
    L.new(geo.outputs["Pointiness"], wear.inputs["Value"])
    mx2 = nt.nodes.new("ShaderNodeMix"); mx2.data_type = "RGBA"; mx2.inputs[7].default_value = (0.66, 0.6, 0.5, 1)
    L.new(wear.outputs[0], mx2.inputs["Factor"]); L.new(mx.outputs[2], mx2.inputs[6])
    L.new(mx2.outputs[2], b.inputs["Base Color"])
    rr = nt.nodes.new("ShaderNodeMapRange"); rr.inputs["To Min"].default_value = 0.55; rr.inputs["To Max"].default_value = 0.92
    L.new(f.outputs[0], rr.inputs["Value"]); L.new(rr.outputs[0], b.inputs["Roughness"])
    return m

def road_mat():
    m, nt, out = node_mat("road"); L = nt.links
    b = principled(nt, out, Roughness=0.95)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Position"], sep.inputs[0])
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 0.35; n.inputs["Detail"].default_value = 10
    L.new(geo.outputs["Position"], n.inputs["Vector"])
    sand = nt.nodes.new("ShaderNodeMapRange"); sand.inputs["From Min"].default_value = 0.45; sand.inputs["From Max"].default_value = 0.62
    L.new(n.outputs["Fac"], sand.inputs["Value"])
    # 路缘积沙：|x| 越大越偏沙
    ax = nt.nodes.new("ShaderNodeMath"); ax.operation = "ABSOLUTE"; L.new(sep.outputs["X"], ax.inputs[0])
    edge = nt.nodes.new("ShaderNodeMapRange"); edge.inputs["From Min"].default_value = 4.0; edge.inputs["From Max"].default_value = 7.0
    L.new(ax.outputs[0], edge.inputs["Value"])
    mxf = nt.nodes.new("ShaderNodeMath"); mxf.operation = "MAXIMUM"; L.new(sand.outputs[0], mxf.inputs[0]); L.new(edge.outputs[0], mxf.inputs[1])
    # 车辙：沿 y 的两条暗带
    rut = nt.nodes.new("ShaderNodeMath"); rut.operation = "PINGPONG"; rut.inputs[1].default_value = 1.1
    off = nt.nodes.new("ShaderNodeMath"); off.operation = "ADD"; off.inputs[1].default_value = 0.35
    L.new(sep.outputs["X"], off.inputs[0]); L.new(off.outputs[0], rut.inputs[0])
    rutm = nt.nodes.new("ShaderNodeMapRange"); rutm.inputs["From Min"].default_value = 0.0; rutm.inputs["From Max"].default_value = 0.35
    rutm.inputs["To Min"].default_value = 0.22; rutm.inputs["To Max"].default_value = 0.0
    L.new(rut.outputs[0], rutm.inputs["Value"])
    asphalt = nt.nodes.new("ShaderNodeMix"); asphalt.data_type = "RGBA"
    asphalt.inputs[6].default_value = (0.24, 0.21, 0.18, 1); asphalt.inputs[7].default_value = (0.58, 0.47, 0.33, 1)
    L.new(mxf.outputs[0], asphalt.inputs["Factor"])
    dark = nt.nodes.new("ShaderNodeMix"); dark.data_type = "RGBA"; dark.blend_type = "MULTIPLY"; dark.inputs[7].default_value = (0.55, 0.52, 0.48, 1)
    L.new(rutm.outputs[0], dark.inputs["Factor"]); L.new(asphalt.outputs[2], dark.inputs[6])
    fine = nt.nodes.new("ShaderNodeTexNoise"); fine.inputs["Scale"].default_value = 60; fine.inputs["Detail"].default_value = 4
    L.new(geo.outputs["Position"], fine.inputs["Vector"])
    fm = nt.nodes.new("ShaderNodeMix"); fm.data_type = "RGBA"; fm.blend_type = "OVERLAY"; fm.inputs["Factor"].default_value = 0.35
    L.new(dark.outputs[2], fm.inputs[6]); L.new(fine.outputs["Color"], fm.inputs[7])
    L.new(fm.outputs[2], b.inputs["Base Color"])
    cr = nt.nodes.new("ShaderNodeTexVoronoi"); cr.feature = "DISTANCE_TO_EDGE"; cr.inputs["Scale"].default_value = 0.9
    L.new(geo.outputs["Position"], cr.inputs["Vector"])
    crm = nt.nodes.new("ShaderNodeMapRange"); crm.inputs["From Min"].default_value = 0.0; crm.inputs["From Max"].default_value = 0.03
    L.new(cr.outputs["Distance"], crm.inputs["Value"])
    hs = nt.nodes.new("ShaderNodeMath"); hs.operation = "MULTIPLY_ADD"; hs.inputs[1].default_value = 0.4
    L.new(fine.outputs["Fac"], hs.inputs[0]); L.new(crm.outputs[0], hs.inputs[2])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.5; bp.inputs["Distance"].default_value = 0.02
    L.new(hs.outputs[0], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m

MAT = {
    "plaster": plaster_mat(),
    "dark": simple_mat("opening", (0.025, 0.022, 0.02), 0.9, noise=0.1),
    "shutter": simple_mat("shutter", (0.22, 0.3, 0.27), 0.7, noise=0.45, bump=0.3, scale=14),
    "tin": simple_mat("tin", (0.36, 0.33, 0.3), 0.55, 0.5, noise=0.6, bump=0.4, scale=3),
    "wood": simple_mat("wood", (0.25, 0.18, 0.12), 0.85, noise=0.4, bump=0.3, scale=20),
    "rubber": simple_mat("rubber", (0.025, 0.024, 0.023), 0.88, noise=0.15, bump=0.6, scale=30),
    "steel": simple_mat("steel", (0.06, 0.06, 0.06), 0.45, 0.8, noise=0.3),
    "glass": simple_mat("glass", (0.03, 0.035, 0.035), 0.12, 0.3, noise=0.05, bump=0.0),
    "olive": simple_mat("olive", (0.17, 0.17, 0.12), 0.9, noise=0.4, bump=0.3, scale=10),
    "canvas": simple_mat("canvas", (0.36, 0.3, 0.2), 0.95, noise=0.5, bump=0.5, scale=25),
    "rust": simple_mat("rust", (0.16, 0.08, 0.04), 0.9, noise=0.7, bump=0.5, scale=8),
    "paint_r": simple_mat("sign_red", (0.42, 0.13, 0.08), 0.8, noise=0.5),
    "paint_b": simple_mat("sign_blue", (0.1, 0.22, 0.32), 0.8, noise=0.5),
    "paint_y": simple_mat("sign_yellow", (0.55, 0.42, 0.12), 0.8, noise=0.5),
    "cloth": simple_mat("cloth", (0.45, 0.3, 0.22), 0.95, noise=0.5, bump=0.2, scale=30),
    "tan": tan_paint(),
    "road": road_mat(),
    "sand": simple_mat("sand", (0.56, 0.45, 0.31), 1.0, noise=0.35, bump=0.4, scale=2),
}
MKEYS = list(MAT.keys())

# ---------------- mesh building ----------------
class Builder:
    """把很多盒子写进同一个 bmesh，按材质下标分面；最后生成一个带倒角的物体。"""
    def __init__(self): self.bm = bmesh.new(); self.used = []
    def mi(self, key):
        if key not in self.used: self.used.append(key)
        return self.used.index(key)
    def box(self, key, size, loc, rot=(0, 0, 0)):
        M = Matrix.Translation(Vector(loc)) @ Euler(rot).to_matrix().to_4x4() @ Matrix.Diagonal(Vector((size[0], size[1], size[2], 1)))
        r = bmesh.ops.create_cube(self.bm, size=1.0, matrix=M)
        i = self.mi(key)
        for f in {f for v in r["verts"] for f in v.link_faces}: f.material_index = i
    def cyl(self, key, r1, r2, depth, loc, rot=(0, 0, 0), seg=16):
        M = Matrix.Translation(Vector(loc)) @ Euler(rot).to_matrix().to_4x4()
        r = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=seg, radius1=r1, radius2=r2, depth=depth, matrix=M)
        i = self.mi(key)
        for f in {f for v in r["verts"] for f in v.link_faces}: f.material_index = i
    def obj(self, name, bevel=0.025, parent=None, smooth=False):
        me = bpy.data.meshes.new(name); self.bm.to_mesh(me); self.bm.free()
        for k in self.used: me.materials.append(MAT[k])
        if smooth:
            for p in me.polygons: p.use_smooth = True
        ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
        if bevel > 0:
            md = ob.modifiers.new("bevel", "BEVEL"); md.width = bevel; md.segments = 2; md.limit_method = "ANGLE"; md.harden_normals = False
        if parent: ob.parent = parent
        return ob

# ---------------- street ----------------
road = bpy.data.objects.new("road", bpy.data.meshes.new("road"))
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.0, matrix=Matrix.Diagonal((8.5, 160, 1, 1)) @ Matrix.Translation((0, -0.35, 0)))
bm.to_mesh(road.data); bm.free(); road.data.materials.append(MAT["road"]); bpy.context.collection.objects.link(road)
ground = bpy.data.objects.new("ground", bpy.data.meshes.new("ground"))
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=600, matrix=Matrix.Translation((0, 0, -0.03)))
bm.to_mesh(ground.data); bm.free(); ground.data.materials.append(MAT["sand"]); bpy.context.collection.objects.link(ground)

WALL_Y0, WALL_Y1 = -150, 40
SHOP_PAINT = ["paint_r", "paint_b", "paint_y", "shutter", "tin"]

def building(side, y0, w, d, floors):
    """side=-1 西侧 / +1 东侧；正面朝向街道。"""
    B = Builder(); fh = 3.2; h = floors * fh
    front = side * 8.6; cx = front + side * d / 2; cy = y0 + w / 2
    B.box("plaster", (d, w, h), (cx, cy, h / 2))
    for f in range(1, floors): B.box("plaster", (d + 0.18, w + 0.18, 0.18), (cx, cy, f * fh))
    ph = 0.85 + (0.5 if rng.random() < 0.3 else 0)
    for (dx, dy, sx, sy) in [(0, w / 2 - 0.1, d, 0.2), (0, -w / 2 + 0.1, d, 0.2), (d / 2 - 0.1, 0, 0.2, w), (-d / 2 + 0.1, 0, 0.2, w)]:
        B.box("plaster", (sx, sy, ph), (cx + dx, cy + dy, h + ph / 2))
    fx = front - side * 0.0  # 立面平面（x）
    bays = max(1, int(w / R(2.6, 3.4))); step = w / bays
    shutter_key = pick(["shutter", "wood", "paint_b"])
    for f in range(floors):
        for b in range(bays):
            y = y0 + step * (b + 0.5) + R(-0.15, 0.15)
            if f == 0:
                if rng.random() < 0.7:  # 卷帘商铺 + 招牌
                    sw = min(step - 0.5, 2.6)
                    B.box("tin", (0.08, sw, 2.5), (fx - side * 0.0 + side * 0.04, y, 1.3))
                    B.box("plaster", (0.45, sw + 0.5, 0.22), (fx - side * 0.22, y, 2.65))
                    if rng.random() < 0.65: B.box(pick(SHOP_PAINT), (0.05, sw + 0.2, 0.7), (fx - side * 0.47, y, 3.15))
                elif rng.random() < 0.6:
                    B.box("dark", (0.06, 1.2, 2.3), (fx - side * 0.02, y, 1.15)); B.box("plaster", (0.36, 1.6, 0.16), (fx - side * 0.18, y, 2.38))
                continue
            if rng.random() > 0.92: continue
            ww, wh, z0 = R(0.95, 1.3), R(1.25, 1.45), f * fh + 0.95
            B.box("dark", (0.05, ww, wh), (fx - side * 0.01, y, z0 + wh / 2))
            B.box("plaster", (0.24, ww + 0.3, 0.1), (fx - side * 0.11, y, z0 - 0.05))
            B.box("plaster", (0.3, ww + 0.24, 0.16), (fx - side * 0.14, y, z0 + wh + 0.08))
            s = rng.random()
            if s < 0.4:  # 百叶：开/半开/关
                ang = pick([0.0, 1.0, 1.9])
                for sd in (-1, 1):
                    hy = y + sd * ww / 2
                    cy_ = hy - sd * math.cos(ang) * ww / 4 if ang else y + sd * ww / 4
                    cx_ = fx - side * (0.05 + math.sin(ang) * ww / 4)
                    B.box(shutter_key, (0.04, ww / 2, wh), (cx_, cy_, z0 + wh / 2), (0, 0, -side * sd * ang))
            elif s < 0.55:
                for k in range(1, 5): B.box("steel", (0.03, 0.03, wh), (fx - side * 0.07, y - ww / 2 + ww * k / 5, z0 + wh / 2))
        if f > 0 and rng.random() < 0.35:  # 阳台 + 晾晒
            bw = R(2.6, 4.0); y = y0 + R(bw / 2, w - bw / 2)
            B.box("plaster", (1.2, bw, 0.16), (fx - side * 0.6, y, f * fh + 0.08))
            B.box("plaster", (0.1, bw, 0.95), (fx - side * 1.15, y, f * fh + 0.62))
            if rng.random() < 0.6: B.box("cloth", (0.02, R(0.7, 1.4), 0.7), (fx - side * 1.22, y + R(-0.6, 0.6), f * fh + 0.75))
    for _ in range(int(R(2, 5))):  # 屋顶水箱/楼梯间/杂物
        rx, ry = cx + R(-d / 2 + 1.5, d / 2 - 1.5), cy + R(-w / 2 + 1.5, w / 2 - 1.5)
        k = rng.random()
        if k < 0.45: B.cyl(pick(["olive", "steel", "rust"]), 0.55, 0.55, 1.1, (rx, ry, h + 0.6 + (0.9 if rng.random() < 0.5 else 0)))
        elif k < 0.7: B.box("plaster", (2.4, 2.6, 2.4), (rx, ry, h + 1.2))
        else: B.box("tin", (2.6, 2.2, 0.04), (rx, ry, h + 2.1), (0.08, 0, 0))
    if rng.random() < 0.15:  # 未完工楼层：柱 + 外露钢筋
        for (dx, dy) in [(-d / 2 + 0.3, -w / 2 + 0.3), (d / 2 - 0.3, -w / 2 + 0.3), (-d / 2 + 0.3, w / 2 - 0.3), (d / 2 - 0.3, w / 2 - 0.3)]:
            ch = R(0.8, 2.6); B.box("plaster", (0.35, 0.35, ch), (cx + dx, cy + dy, h + ch / 2))
            for k in range(4): B.cyl("rust", 0.012, 0.012, 1.1, (cx + dx + (k % 2 - 0.5) * 0.18, cy + dy + (k // 2 - 0.5) * 0.18, h + ch + 0.5), (R(-0.2, 0.2), R(-0.2, 0.2), 0), seg=4)
    ob = B.obj(f"bldg_{side}_{int(y0)}", bevel=0.03)
    ob.color = (R(), 0, 0, 1)
    return ob

for side in (-1, 1):
    y = WALL_Y0
    while y < WALL_Y1:
        w = R(7, 15)
        if rng.random() < 0.08:  # 空地/废墟
            y += w; continue
        building(side, y, w - R(0.3, 0.8), R(9, 13), max(1, int(R(1.4, 4.6))))
        y += w + R(0, 1.2)

# 街面陈设
P = Builder()
poles = []
for y in range(-150, 41, 24):
    for side in (-1, 1):
        x = side * 7.9; P.cyl("wood", 0.1, 0.14, 8.5, (x, y, 4.25), (R(-0.03, 0.03), R(-0.03, 0.03), 0), seg=8)
        P.box("wood", (1.8, 0.1, 0.1), (x, y, 7.9)); poles.append((x, y))
for i in range(900):
    side = pick((-1, 1)); x = side * (R(5.6, 8.4) if rng.random() < 0.75 else R(0, 5.5)); y = R(-150, 40)
    if rng.random() < 0.5: P.box(pick(["cloth", "canvas", "wood", "sand", "plaster"]), (R(0.15, 0.5), R(0.1, 0.4), 0.015), (x, y, 0.01), (0, 0, R(0, 3)))
    else:
        r = R(0.05, 0.25); P.box(pick(["plaster", "sand", "plaster"]), (r * R(1, 2), r * R(1, 2), r), (x, y, r / 2), (R(0, 1), R(0, 1), R(0, 3)))
for (x, y, n) in [(5.5, -40, 7), (-6.2, -70, 5), (6.0, -95, 6)]:  # 轮胎堆
    for k in range(n):
        ob_r = 0.36; P.cyl("rubber", ob_r, ob_r, 0.26, (x + R(-0.8, 0.8), y + R(-0.8, 0.8), 0.13 + (k % 3) * 0.26), (R(-0.2, 0.2), R(-0.2, 0.2), 0), seg=18)
for (x, y) in [(-6.4, -52), (6.2, -20), (-6.3, -88)]:  # 油桶
    for k in range(3): P.cyl(pick(["olive", "rust", "paint_b"]), 0.29, 0.29, 0.88, (x + R(-0.7, 0.7), y + R(-0.7, 0.7), 0.44), seg=18)
# 烧毁车辆残骸
for (x, y, rz) in [(5.6, -63, 0.2), (-6.0, -14, 1.4)]:
    P.box("rust", (1.8, 4.2, 0.75), (x, y, 0.62), (0, 0, rz)); P.box("rust", (1.6, 2.2, 0.6), (x, y - 0.2, 1.3), (0, 0, rz))
    for (a, b) in [(0.85, 1.3), (-0.85, 1.3), (0.85, -1.3), (-0.85, -1.3)]:
        P.cyl("rust", 0.25, 0.25, 0.2, (x + a, y + b, 0.25), (0, math.pi / 2, rz), seg=12)
# 墙根积沙
for y in range(-150, 41, 3):
    for side in (-1, 1):
        if rng.random() < 0.5: P.box("sand", (R(0.8, 1.6), R(1.5, 4), 0.25), (side * R(7.6, 8.2), y + R(0, 2), 0.04), (0, side * 0.25, 0))
P.obj("street_props", bevel=0.01)
# 电线（下垂）
for side in (-1, 1):
    ps = sorted([p for p in poles if (p[0] > 0) == (side > 0)], key=lambda p: p[1])
    for i in range(len(ps) - 1):
        for off in (-0.8, 0, 0.8):
            cu = bpy.data.curves.new("wire", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.008
            sp = cu.splines.new("POLY"); sp.points.add(15)
            (x0, y0), (x1, y1) = ps[i], ps[i + 1]; sag = R(0.5, 0.9)
            for k in range(16):
                u = k / 15; sp.points[k].co = (x0 + off, y0 + (y1 - y0) * u, 7.85 - math.sin(u * math.pi) * sag, 1)
            ob = bpy.data.objects.new("wire", cu); cu.materials.append(MAT["dark"]); bpy.context.collection.objects.link(ob)

# ---------------- Humvee ----------------
def wheel(name, r, w, parent, loc):
    B = Builder()
    B.cyl("rubber", r, r, w, (0, 0, 0), (0, math.pi / 2, 0), seg=40)
    for k in range(28):  # 胎纹块
        a = k / 28 * 2 * math.pi
        B.box("rubber", (w * 0.9, 0.09, 0.05), (0, math.cos(a) * (r + 0.01), math.sin(a) * (r + 0.01)), (a, 0, 0))
    B.cyl("tan", r * 0.55, r * 0.55, w + 0.04, (0, 0, 0), (0, math.pi / 2, 0), seg=24)
    for k in range(8):
        a = k / 8 * 2 * math.pi; B.cyl("steel", 0.025, 0.025, w + 0.08, (0, math.cos(a) * r * 0.35, math.sin(a) * r * 0.35), (0, math.pi / 2, 0), seg=6)
    ob = B.obj(name, bevel=0.02, parent=parent); ob.location = loc
    return ob

def humvee(name):
    root = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(root)
    body = bpy.data.objects.new(name + "_body", None); bpy.context.collection.objects.link(body); body.parent = root
    B = Builder()
    B.box("tan", (2.18, 4.6, 0.55), (0, 0, 0.82))                      # 车身下部
    B.box("tan", (2.1, 1.55, 0.3), (0, 1.5, 1.2), (-0.09, 0, 0))       # 引擎盖
    B.box("tan", (0.9, 1.3, 0.12), (0, 1.45, 1.36), (-0.09, 0, 0))     # 引擎盖中部隆起
    for s_ in (-1, 1):
        B.box("tan", (0.42, 1.35, 0.1), (s_ * 0.98, 1.55, 1.24), (-0.05, s_ * 0.18, 0))  # 外扩轮眉
        B.box("tan", (0.42, 1.1, 0.1), (s_ * 0.98, -1.6, 1.14), (0, s_ * 0.18, 0))
        B.box("steel", (0.25, 0.9, 0.06), (s_ * 1.12, 0.0, 0.5))                    # 侧踏板
    for xg in (-0.8, -0.3, 0.3, 0.8): B.box("steel", (0.06, 0.06, 0.5), (xg, 2.55, 0.85))  # 防撞栏立柱
    B.box("steel", (1.8, 0.06, 0.06), (0, 2.55, 1.08))
    B.box("dark", (1.5, 0.06, 0.42), (0, 2.31, 0.98))                    # 格栅
    for k in range(7): B.box("tan", (0.05, 0.08, 0.4), (-0.6 + k * 0.2, 2.33, 0.98))
    B.box("steel", (2.1, 0.12, 0.16), (0, 2.42, 0.62))                   # 保险杠
    for s in (-1, 1):
        B.box("steel", (0.12, 0.2, 0.08), (s * 0.7, 2.5, 0.62))          # 拖钩
        B.box("tan", (0.36, 1.2, 0.32), (s * 1.0, 1.55, 1.05))           # 挡泥板
        B.box("dark", (0.22, 0.05, 0.16), (s * 0.8, 2.33, 1.12))         # 前灯
        B.box("steel", (0.04, 0.22, 0.16), (s * 1.18, 0.62, 1.75))       # 后视镜
        for dy in (0.08, -0.95):
            B.box("dark", (0.02, 0.85, 0.02), (s * 1.095, dy, 1.08))     # 车门缝
            B.box("glass", (0.03, 0.75, 0.38), (s * 1.06, dy, 1.55))     # 侧窗
        B.box("steel", (0.06, 0.12, 0.05), (s * 1.1, 0.35, 1.25))        # 门把手
    B.box("tan", (2.06, 2.7, 0.72), (0, -0.7, 1.46))                     # 硬顶车厢
    B.box("glass", (1.9, 0.04, 0.48), (0, 0.68, 1.55), (-0.18, 0, 0))   # 风挡
    B.box("tan", (0.06, 0.06, 0.5), (0, 0.69, 1.55), (-0.18, 0, 0))     # 风挡中柱
    B.cyl("tan", 0.56, 0.56, 0.18, (0, -0.6, 1.92), seg=28)              # 炮塔环
    B.box("tan", (0.75, 0.06, 0.48), (0, -0.22, 2.22))                   # 护盾
    B.cyl("steel", 0.035, 0.035, 1.45, (0, 0.35, 2.2), (math.pi / 2 - 0.08, 0, 0), seg=10)  # M2 枪管
    B.box("steel", (0.2, 0.55, 0.22), (0, -0.35, 2.18))
    B.box("canvas", (1.6, 0.6, 0.38), (0, -1.75, 2.0))                   # 车顶装备
    for k in range(4): B.box("canvas", (0.5, 0.3, 0.2), (-0.6 + k * 0.4, -1.4, 2.25), (0, 0, R(-0.3, 0.3)))
    B.cyl("steel", 0.008, 0.004, 2.8, (-0.85, -1.9, 3.3), (0.12, 0, 0), seg=6)  # 鞭状天线
    B.cyl("olive", 0.2, 0.23, 0.55, (0, -0.85, 2.25), seg=16)            # 机枪手躯干
    B.cyl("olive", 0.18, 0.2, 0.08, (0, -0.85, 2.62), seg=16)
    hb = bmesh.ops.create_uvsphere(B.bm, u_segments=16, v_segments=10, radius=0.165, matrix=Matrix.Translation((0, -0.82, 2.74)))
    i = B.mi("olive")
    for f in {f for v in hb["verts"] for f in v.link_faces}: f.material_index = i
    sh = B.obj(name + "_shell", bevel=0.06, parent=body); sh.modifiers["bevel"].segments = 3
    wheels = [wheel(f"{name}_w{i}", 0.47, 0.34, root, loc) for i, loc in enumerate([(-1.0, 1.62, 0.47), (1.0, 1.62, 0.47), (-1.0, -1.6, 0.47), (1.0, -1.6, 0.47)])]
    return root, body, wheels

def truck(name):
    root = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(root)
    body = bpy.data.objects.new(name + "_body", None); bpy.context.collection.objects.link(body); body.parent = root
    B = Builder()
    B.box("tan", (2.4, 7.6, 0.4), (0, 0, 1.0)); B.box("tan", (2.1, 1.6, 0.9), (0, 2.9, 1.6))
    B.box("tan", (2.3, 1.5, 1.2), (0, 1.55, 2.0)); B.box("glass", (2.0, 0.04, 0.55), (0, 2.31, 2.25))
    B.box("canvas", (2.45, 4.2, 1.5), (0, -1.6, 2.0))
    B.obj(name + "_shell", bevel=0.04, parent=body)
    wheels = [wheel(f"{name}_w{i}", 0.55, 0.38, root, loc) for i, loc in enumerate([(-1.05, 2.8, 0.55), (1.05, 2.8, 0.55), (-1.05, -1.0, 0.55), (1.05, -1.0, 0.55), (-1.05, -2.4, 0.55), (1.05, -2.4, 0.55)])]
    return root, body, wheels

convoy = [humvee("hmmwv_0"), humvee("hmmwv_1"), truck("truck_2")]
GAPS = [0, 13, 27]
RADII = [0.47, 0.47, 0.55]
for f in range(scene.frame_start - 2, scene.frame_end + 3):
    t = T0 + (f - 1) / FPS
    for i, (root, body, wheels) in enumerate(convoy):
        y = lead_y(t) - GAPS[i]
        root.location = (LANE_X + math.sin(y * 0.05 + i) * 0.25, y, 0); root.keyframe_insert("location", frame=f)
        body.location = (0, 0, math.sin(t * 9 + i * 1.7) * 0.025 + math.sin(t * 23 + i) * 0.008)
        body.rotation_euler = (math.sin(t * 6.1 + i * 2) * 0.006, math.sin(t * 5.3 + i) * 0.008, 0)
        body.keyframe_insert("location", frame=f); body.keyframe_insert("rotation_euler", frame=f)
        for w in wheels:
            w.rotation_euler = (-(y + 200) / RADII[i], 0, 0); w.keyframe_insert("rotation_euler", frame=f)

# ---------------- 扬尘（体积） ----------------
def dust_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); L = nt.links
    out = nt.nodes.new("ShaderNodeOutputMaterial"); vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (0.72, 0.6, 0.44, 1); vol.inputs["Anisotropy"].default_value = 0.45
    tc = nt.nodes.new("ShaderNodeTexCoord"); n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 2.2; n.inputs["Detail"].default_value = 6
    L.new(tc.outputs["Object"], n.inputs["Vector"])
    grad = nt.nodes.new("ShaderNodeTexGradient"); grad.gradient_type = "SPHERICAL"; L.new(tc.outputs["Object"], grad.inputs["Vector"])
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; L.new(n.outputs["Fac"], mul.inputs[0]); L.new(grad.outputs["Fac"], mul.inputs[1])
    ramp = nt.nodes.new("ShaderNodeMapRange"); ramp.inputs["From Min"].default_value = 0.04; ramp.inputs["From Max"].default_value = 0.32
    L.new(mul.outputs[0], ramp.inputs["Value"])
    dens = nt.nodes.new("ShaderNodeMath"); dens.operation = "MULTIPLY"; dens.name = "density"; dens.inputs[1].default_value = 0.0
    L.new(ramp.outputs[0], dens.inputs[0]); L.new(dens.outputs[0], vol.inputs["Density"])
    L.new(vol.outputs[0], out.inputs["Volume"])
    return m, dens

LIFE = 2.6
for vi in range(len(convoy)):
    for k in range(16):
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0); me = bpy.data.meshes.new("puff"); bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new(f"dust_{vi}_{k}", me); bpy.context.collection.objects.link(ob)
        m, dens = dust_mat(f"dust_{vi}_{k}"); me.materials.append(m)
        off = k * LIFE / 16; ob.rotation_euler = (R(0, 3), R(0, 3), R(0, 3))
        for f in range(scene.frame_start - 2, scene.frame_end + 3):
            t = T0 + (f - 1) / FPS
            a = (t + off) % LIFE; emit = t - a
            y = lead_y(emit) - GAPS[vi] - 2.6 - a * 1.2
            spread = 0.8 + a * 1.4
            wheel_side = (-1.05 if k % 2 else 1.05) if k % 4 < 2 else (k % 3 - 1) * 0.5 * spread
            front = k % 4 < 2
            ob.location = (LANE_X + wheel_side * (1 + a * (2.2 if front else 0.6)), y + (4.2 if front else 0), 0.35 + a * 0.7)
            s = (0.5 + a * 3.2) if front else (0.9 + a * 1.5); ob.scale = (s * 1.3, s * 1.6, s * 0.8)
            dens.inputs[1].default_value = 3.2 * math.sin(math.pi * min(1, a / LIFE)) * min(1, a / 0.25)
            ob.keyframe_insert("location", frame=f); ob.keyframe_insert("scale", frame=f)
            dens.inputs[1].keyframe_insert("default_value", frame=f)

# 贴地风沙：街道前方横向飘过的低矮沙层（体积 + 随时间平移的噪声）
drift = bpy.data.objects.new("drift", bpy.data.meshes.new("drift"))
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, -45, 0.9)) @ Matrix.Diagonal((20, 70, 1.8, 1))); bm.to_mesh(drift.data); bm.free()
bpy.context.collection.objects.link(drift)
dm = bpy.data.materials.new("drift"); dm.use_nodes = True; nt = dm.node_tree; nt.nodes.clear(); L = nt.links
dv = nt.nodes.new("ShaderNodeVolumePrincipled"); dv.inputs["Color"].default_value = (0.78, 0.62, 0.42, 1); dv.inputs["Anisotropy"].default_value = 0.4
geo = nt.nodes.new("ShaderNodeNewGeometry"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (0.35, 0.18, 1.2)
L.new(geo.outputs["Position"], mp.inputs["Vector"])
dn = nt.nodes.new("ShaderNodeTexNoise"); dn.inputs["Scale"].default_value = 1.6; dn.inputs["Detail"].default_value = 5
L.new(mp.outputs[0], dn.inputs["Vector"])
sep = nt.nodes.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Position"], sep.inputs[0])
fall = nt.nodes.new("ShaderNodeMapRange"); fall.inputs["From Min"].default_value = 0.0; fall.inputs["From Max"].default_value = 1.6; fall.inputs["To Min"].default_value = 1; fall.inputs["To Max"].default_value = 0
L.new(sep.outputs["Z"], fall.inputs["Value"])
th = nt.nodes.new("ShaderNodeMapRange"); th.inputs["From Min"].default_value = 0.5; th.inputs["From Max"].default_value = 0.75
L.new(dn.outputs["Fac"], th.inputs["Value"])
mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; L.new(th.outputs[0], mul.inputs[0]); L.new(fall.outputs[0], mul.inputs[1])
dd = nt.nodes.new("ShaderNodeMath"); dd.operation = "MULTIPLY"; dd.inputs[1].default_value = 0.35; L.new(mul.outputs[0], dd.inputs[0])
L.new(dd.outputs[0], dv.inputs["Density"])
do = nt.nodes.new("ShaderNodeOutputMaterial"); L.new(dv.outputs[0], do.inputs["Volume"]); drift.data.materials.append(dm)
for f in (scene.frame_start - 2, scene.frame_end + 3):
    t = T0 + (f - 1) / FPS; mp.inputs["Location"].default_value = (-1.6 * t, 0.2 * t, 0); mp.inputs["Location"].keyframe_insert("default_value", frame=f)
for fc in (dm.node_tree.animation_data.action.fcurves if hasattr(dm.node_tree.animation_data.action, "fcurves") else []):
    for kp in fc.keyframe_points: kp.interpolation = "LINEAR"

# 浮尘颗粒（近景空气中的亮点，受逆光时显现）
MOTE = bpy.data.materials.new("mote"); MOTE.use_nodes = True
mn = MOTE.node_tree; mb = mn.nodes["Principled BSDF"]; mb.inputs["Base Color"].default_value = (0.8, 0.68, 0.5, 1); mb.inputs["Roughness"].default_value = 1
Mb = bmesh.new()
for i in range(1400):
    y = R(-75, -20); M = Matrix.Translation((R(-9, 6), y, R(0.2, 5)))
    bmesh.ops.create_icosphere(Mb, subdivisions=0, radius=R(0.004, 0.012), matrix=M)
me = bpy.data.meshes.new("motes"); Mb.to_mesh(me); Mb.free(); me.materials.append(MOTE)
motes = bpy.data.objects.new("motes", me); bpy.context.collection.objects.link(motes)
for f in (scene.frame_start - 2, scene.frame_end + 3):
    t = T0 + (f - 1) / FPS; motes.location = (0.4 * t, 0.6 * t, 0.15 * math.sin(t)); motes.keyframe_insert("location", frame=f)
for fc in (motes.animation_data.action.fcurves if hasattr(motes.animation_data.action, "fcurves") else []):
    for kp in fc.keyframe_points: kp.interpolation = "LINEAR"

# 空气中的尘霾（整体体积，产生阳光光束）
haze = bpy.data.objects.new("haze", bpy.data.meshes.new("haze"))
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, -60, 15)) @ Matrix.Diagonal((80, 260, 30, 1))); bm.to_mesh(haze.data); bm.free()
bpy.context.collection.objects.link(haze)
hm = bpy.data.materials.new("haze"); hm.use_nodes = True; nt = hm.node_tree; nt.nodes.clear()
hv = nt.nodes.new("ShaderNodeVolumePrincipled"); hv.inputs["Color"].default_value = (0.95, 0.72, 0.45, 1); hv.inputs["Density"].default_value = 0.0025; hv.inputs["Anisotropy"].default_value = 0.55
ho = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(hv.outputs[0], ho.inputs["Volume"]); haze.data.materials.append(hm)

# ---------------- light & world ----------------
sun_dir = Vector((-0.42, -0.68, 0.6)).normalized()  # 指向太阳
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); bpy.context.collection.objects.link(sun)
sun.data.energy = 8.0; sun.data.angle = math.radians(0.8); sun.data.color = (1.0, 0.86, 0.68)
sun.rotation_euler = sun_dir.to_track_quat("Z", "Y").to_euler()
world = bpy.data.worlds.new("world"); scene.world = world; world.use_nodes = True
wn = world.node_tree; wn.nodes.clear()
sky = wn.nodes.new("ShaderNodeTexSky")
types = [i.identifier for i in sky.bl_rna.properties["sky_type"].enum_items]
for want in ("MULTIPLE_SCATTERING", "SINGLE_SCATTERING", "NISHITA", "HOSEK_WILKIE"):
    if want in types: sky.sky_type = want; break
for attr, val in (("sun_elevation", math.asin(sun_dir.z)), ("sun_rotation", math.atan2(sun_dir.x, sun_dir.y) + math.pi), ("air_density", 1.4), ("dust_density", 6.0), ("altitude", 10.0)):
    if hasattr(sky, attr):
        try: setattr(sky, attr, val)
        except Exception: pass
if hasattr(sky, "sun_disc"): sky.sun_disc = False
bg = wn.nodes.new("ShaderNodeBackground"); bg.inputs["Strength"].default_value = 0.06
warm = wn.nodes.new("ShaderNodeMix"); warm.data_type = "RGBA"; warm.blend_type = "MULTIPLY"; warm.inputs["Factor"].default_value = 1.0; warm.inputs[7].default_value = (1.0, 0.82, 0.6, 1)
wn.links.new(sky.outputs[0], warm.inputs[6])
wo = wn.nodes.new("ShaderNodeOutputWorld"); wn.links.new(warm.outputs[2], bg.inputs[0]); wn.links.new(bg.outputs[0], wo.inputs["Surface"])
print("SKY", sky.sky_type)

# ---------------- camera ----------------
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); bpy.context.collection.objects.link(cam); scene.camera = cam
cam.data.sensor_fit = "VERTICAL"; cam.data.angle_y = math.radians(44); cam.data.clip_start = 0.1; cam.data.clip_end = 2000
cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 2.8
def shake(t, amt):
    return (math.sin(t * 7.1) * 0.6 + math.sin(t * 13.7 + 1) * 0.3 + math.sin(t * 2.3) * 0.5) * amt, (math.sin(t * 6.3 + 2) * 0.5 + math.sin(t * 15.1) * 0.25) * amt
for f in range(scene.frame_start - 2, scene.frame_end + 3):
    t = T0 + (f - 1) / FPS; u = max(0, min(1, (t - T0) / (T1 - T0)))
    z = -lead_y(t)  # three z
    sx, sy = shake(t * 1.6, 0.035)
    pos = Vector((LANE_X - 3.1 + sx, -(z + 2.6 - u * 1.4), 1.0 + sy))
    look = Vector((LANE_X + 0.4, -(z - 3.2 - u * 0.6), 1.35))
    d = look - pos
    q = d.to_track_quat("-Z", "Y"); e = q.to_euler(); e.rotate_axis("Z", math.sin(t * 3.1) * 0.004)
    cam.location = pos; cam.rotation_euler = e
    cam.data.dof.focus_distance = (Vector((LANE_X, -z, 1.2)) - pos).length
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
    cam.data.dof.keyframe_insert("focus_distance", frame=f)

# ---------------- render settings ----------------
r = scene.render
r.engine = "CYCLES"; r.resolution_x, r.resolution_y = 1920, 816; r.resolution_percentage = RES_PCT
r.use_motion_blur = True; r.motion_blur_shutter = 0.5
r.image_settings.file_format = "PNG"; r.image_settings.color_depth = "16"
cy = scene.cycles
prefs = bpy.context.preferences.addons["cycles"].preferences; prefs.compute_device_type = "METAL"; prefs.get_devices()
for dv in prefs.devices: dv.use = dv.type == "METAL"
cy.device = "GPU"; cy.samples = SAMPLES; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.02
cy.use_denoising = True
cy.max_bounces = 6; cy.diffuse_bounces = 3; cy.glossy_bounces = 2; cy.volume_bounces = 1; cy.transparent_max_bounces = 4
cy.volume_step_rate = 2.0; cy.volume_preview_step_rate = 4.0
cy.seed = 1993; cy.use_animated_seed = True
try:
    scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Punchy"
except Exception:
    pass
r.filepath = os.path.join(OUT, "f_####")
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "..", "convoy_shot.blend"))
if STILL:
    scene.frame_set(STILL); r.filepath = os.path.join(OUT, f"still_{STILL:04d}"); bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
