# 基准镜头（hero 版）：在 convoy_shot.py 基础上换 Poly Haven CC0 PBR 贴图/HDRI/道具、逆光、人物剪影与手持运镜。
# 原注释：车队贴地跟拍镜头（Blender Cycles 版），与 mogadishu_pilot/world.js 中 13.5–16.5 s 的 "convoy-close" 镜头对位。
# 用法：Blender -b --factory-startup --python convoy_hero.py -- <输出目录> [--still FRAME] [--samples N] [--pct P] [--gen-humvee x.glb]
# 坐标：Three.js (x, y, z) → Blender (x, -z, y)；车队沿 +y（北）行驶。全部程序化、固定种子。
import bpy, bmesh, math, random, sys, os
from mathutils import Vector, Matrix, Euler

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(argv[0] if argv else "renders/convoy")
STILL = int(argv[argv.index("--still") + 1]) if "--still" in argv else None
SAMPLES = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 64
RES_PCT = int(argv[argv.index("--pct") + 1]) if "--pct" in argv else 100
GEN_HUMVEE = os.path.abspath(argv[argv.index("--gen-humvee") + 1]) if "--gen-humvee" in argv else None  # TRELLIS.2 生成的悍马 GLB
GEN_PEOPLE = os.path.abspath(argv[argv.index("--gen-people") + 1]) if "--gen-people" in argv else None  # TRELLIS.2 生成人物 GLB 所在目录（trellis_*_300_1.glb）

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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from matlib import *  # 材质（MAT、pbr_mat 等）与 Builder

# ---------------- street ----------------
road = bpy.data.objects.new("road", bpy.data.meshes.new("road"))
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.0, matrix=Matrix.Diagonal((8.5, 160, 1, 1)) @ Matrix.Translation((0, -0.35, 0)))
bm.to_mesh(road.data); bm.free(); road.data.materials.append(MAT["road"]); bpy.context.collection.objects.link(road)
ground = bpy.data.objects.new("ground", bpy.data.meshes.new("ground"))
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=600, matrix=Matrix.Translation((0, 0, -0.03)))
bm.to_mesh(ground.data); bm.free(); ground.data.materials.append(MAT["sand"]); bpy.context.collection.objects.link(ground)

WALL_Y0, WALL_Y1 = -150, 40
SHOP_PAINT = ["paint_r", "paint_b", "paint_y", "shutter", "tin"]

brng = random.Random(1960)  # 新增的建筑细节单独取随机数，不打乱原有布局
pick_b = lambda seq: seq[int(brng.random() * len(seq)) % len(seq)]
SIGNS = []
SIGN_WORDS = ["DUKAANKA XAMAR", "FARMASHIYE", "MAKHAAYADA", "HOTEL SHAMO", "BAKAAR", "DUKAAN", "RAAXO", "SHIDAAL", "CAWO STORE",
              "TELEFOON", "KAALINTA", "MAQAAYAD", "HILIB", "DAHAB", "XAWAALAD", "BIYO", "JAAMAC & WIILAL"]

def building(side, y0, w, d, floors):
    """side=-1 西侧 / +1 东侧；正面朝向街道。"""
    B = Builder(); fh = 3.2; h = floors * fh; WK = pick(WALLS)
    front = side * 8.6; cx = front + side * d / 2; cy = y0 + w / 2
    arcade = floors >= 2 and brng.random() < 0.35; AD = 2.0   # 意式殖民时期骑楼：底层退进 2 m，柱廊 + 拱
    if arcade:
        B.box(WK, (d, w, h - fh), (cx, cy, fh + (h - fh) / 2))
        B.box(WK, (d - AD, w, fh), (cx + side * AD / 2, cy, fh / 2))
        nb = max(2, int(w / 3.2)); st_ = w / nb
        for k in range(nb + 1):
            B.box(WK, (0.5, 0.5, fh), (front + side * 0.25, y0 + min(max(k * st_, 0.25), w - 0.25), fh / 2))
            B.box(WK, (0.62, 0.62, 0.18), (front + side * 0.25, y0 + min(max(k * st_, 0.25), w - 0.25), 0.09))   # 柱础
        for k in range(nb):
            yc = y0 + (k + 0.5) * st_
            B.box(WK, (0.5, st_ - 0.5, 0.45), (front + side * 0.25, yc, fh - 0.225))                              # 拱上墙
            for sd in (-1, 1):                                                                                     # 拱肩（斜撑近似拱弧）
                B.box(WK, (0.5, 0.55, 0.55), (front + side * 0.25, yc + sd * (st_ / 2 - 0.45), fh - 0.55), (sd * 0.785, 0, 0))
            if brng.random() < 0.5: SIGNS.append((pick_b(SIGN_WORDS), front - side * 0.005, yc, fh - 0.23, side, st_ - 0.8, 0.4, "ink_k"))
    else:
        B.box(WK, (d, w, h), (cx, cy, h / 2))
    for f in range(1, floors): B.box(WK, (d + 0.18, w + 0.18, 0.18), (cx, cy, f * fh))
    ph = 0.85 + (0.5 if rng.random() < 0.3 else 0)
    for (dx, dy, sx, sy) in [(0, w / 2 - 0.1, d, 0.2), (0, -w / 2 + 0.1, d, 0.2), (d / 2 - 0.1, 0, 0.2, w), (-d / 2 + 0.1, 0, 0.2, w)]:
        B.box(WK, (sx, sy, ph), (cx + dx, cy + dy, h + ph / 2))
    fx = front - side * 0.0  # 立面平面（x）
    gx = front + side * AD if arcade else fx  # 底层店面所在平面
    bays = max(1, int(w / R(2.6, 3.4))); step = w / bays
    shutter_key = pick(["shutter", "wood", "paint_b"])
    for f in range(floors):
        for b in range(bays):
            y = y0 + step * (b + 0.5) + R(-0.15, 0.15)
            if f == 0:
                if rng.random() < 0.7:  # 卷帘商铺 + 招牌
                    sw = min(step - 0.5, 2.6)
                    B.box("tin", (0.08, sw, 2.5), (gx + side * 0.04, y, 1.3))
                    B.box(WK, (0.45, sw + 0.5, 0.22), (gx - side * 0.22, y, 2.65))
                    if rng.random() < 0.65 and not arcade:
                        pk = pick(SHOP_PAINT); B.box(pk, (0.05, sw + 0.2, 0.7), (fx - side * 0.47, y, 3.15))
                        if brng.random() < 0.85:
                            SIGNS.append((pick_b(SIGN_WORDS), fx - side * 0.5, y, 3.15, side, sw, 0.62, "ink_k" if pk in ("paint_y", "shutter", "tin") else "ink_w"))
                    if not arcade and brng.random() < 0.35:  # 铁皮遮阳棚，向街面倾斜
                        B.box("tin", (1.4, sw + 0.6, 0.03), (fx - side * 0.72, y, 2.9), (0, side * 0.2, 0))
                        for sd in (-1, 1): B.cyl("steel", 0.02, 0.02, 0.9, (fx - side * 1.3, y + sd * (sw / 2 + 0.2), 2.4), (0, -side * 0.6, 0), seg=6)
                elif rng.random() < 0.6:
                    B.box("dark", (0.06, 1.2, 2.3), (gx - side * 0.02, y, 1.15)); B.box(WK, (0.36, 1.6, 0.16), (gx - side * 0.18, y, 2.38))
                continue
            if rng.random() > 0.92: continue
            ww, wh, z0 = R(0.95, 1.3), R(1.25, 1.45), f * fh + 0.95
            B.box("dark", (0.05, ww, wh), (fx - side * 0.01, y, z0 + wh / 2))
            for sd in (-1, 1):  # 窗侧框：凸出墙面，给窗洞一圈投影，读出墙厚
                B.box(WK, (0.22, 0.12, wh + 0.12), (fx - side * 0.1, y + sd * (ww / 2 + 0.06), z0 + wh / 2))
            B.box(WK, (0.24, ww + 0.3, 0.1), (fx - side * 0.11, y, z0 - 0.05))
            B.box(WK, (0.3, ww + 0.24, 0.16), (fx - side * 0.14, y, z0 + wh + 0.08))
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
            B.box(WK, (1.2, bw, 0.16), (fx - side * 0.6, y, f * fh + 0.08))
            B.box(WK, (0.1, bw, 0.95), (fx - side * 1.15, y, f * fh + 0.62))
            if rng.random() < 0.6: B.box("cloth", (0.02, R(0.7, 1.4), 0.7), (fx - side * 1.22, y + R(-0.6, 0.6), f * fh + 0.75))
    for _ in range(int(R(2, 5))):  # 屋顶水箱/楼梯间/杂物
        rx, ry = cx + R(-d / 2 + 1.5, d / 2 - 1.5), cy + R(-w / 2 + 1.5, w / 2 - 1.5)
        k = rng.random()
        if k < 0.45: B.cyl(pick(["olive", "steel", "rust"]), 0.55, 0.55, 1.1, (rx, ry, h + 0.6 + (0.9 if rng.random() < 0.5 else 0)))
        elif k < 0.7: B.box(WK, (2.4, 2.6, 2.4), (rx, ry, h + 1.2))
        else: B.box("tin", (2.6, 2.2, 0.04), (rx, ry, h + 2.1), (0.08, 0, 0))
    if rng.random() < 0.15:  # 未完工楼层：柱 + 外露钢筋
        for (dx, dy) in [(-d / 2 + 0.3, -w / 2 + 0.3), (d / 2 - 0.3, -w / 2 + 0.3), (-d / 2 + 0.3, w / 2 - 0.3), (d / 2 - 0.3, w / 2 - 0.3)]:
            ch = R(0.8, 2.6); B.box(WK, (0.35, 0.35, ch), (cx + dx, cy + dy, h + ch / 2))
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

# 手绘店招文字（Blender 文字物体；Latin 字母的索马里语）
for (txt, x, y, z, side, wmax, hmax, ink) in SIGNS:
    cu = bpy.data.curves.new("sign", "FONT"); cu.body = txt; cu.align_x = "CENTER"; cu.align_y = "CENTER"; cu.extrude = 0.004
    cu.space_character = 1.05; cu.shear = brng.uniform(-0.12, 0.05)
    ob = bpy.data.objects.new("sign_" + txt, cu); bpy.context.collection.objects.link(ob); cu.materials.append(MAT[ink])
    bpy.context.view_layer.update(); dx, dy = max(ob.dimensions.x, 1e-3), max(ob.dimensions.y, 1e-3)
    sc = min(wmax * 0.9 / dx, hmax * 0.75 / dy); ob.scale = (sc, sc, sc)
    ob.location = (x, y, z); ob.rotation_euler = (math.pi / 2, brng.uniform(-0.02, 0.02), -side * math.pi / 2)
print("signs", len(SIGNS))

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
        r = R(0.04, 0.2); P.cyl(pick(WALLS + ["sand", "sand", "grime"]), r * R(0.8, 1.6), r * R(0.4, 1.0), r * R(0.5, 1.2), (x, y, r * 0.3), (R(-0.6, 0.6), R(-0.6, 0.6), R(0, 3)), seg=int(R(4, 7)))  # 碎砖块/灰浆块
for (x, y, n) in [(5.5, -40, 7), (-7.6, -70, 5), (6.0, -95, 6)]:  # 西侧贴墙，让出机位  # 轮胎堆
    for k in range(n):
        ob_r = 0.36; P.cyl("rubber", ob_r, ob_r, 0.26, (x + R(-0.8, 0.8), y + R(-0.8, 0.8), 0.13 + (k % 3) * 0.26), (R(-0.2, 0.2), R(-0.2, 0.2), 0), seg=18)
for (x, y) in [(-7.6, -52), (6.2, -20), (-7.6, -88)]:  # 油桶
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

# ---------------- Poly Haven CC0 道具（实例化） ----------------
def load_prop(name):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ASSETS, "models", name, f"{name}_1k.gltf"))
    obs = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    for o in set(bpy.data.objects) - before:
        if o.type != "MESH": bpy.data.objects.remove(o)
    for o in obs:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    if len(obs) > 1:
        with bpy.context.temp_override(active_object=obs[0], selected_editable_objects=obs, selected_objects=obs):
            bpy.ops.object.join()
    ob = obs[0]
    with bpy.context.temp_override(active_object=ob, selected_editable_objects=[ob], selected_objects=[ob]):
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    me = ob.data; zmin = min(v.co.z for v in me.vertices)  # 让原点落在底面
    for v in me.vertices: v.co.z -= zmin
    for c in ob.users_collection: c.objects.unlink(ob)
    return me

PROPS = {n: load_prop(n) for n in ["old_tyre", "barrel_03", "metal_jerrycan", "concrete_road_barrier", "wooden_crate_01",
                                    "old_military_crate", "cement_bag", "trashbag", "rusted_wheel_rim_01", "plastic_monobloc_chair_01", "utility_box_01"]}
def place(name, x, y, rz=0.0, z=0.0, tilt=(0, 0), s=1.0):
    ob = bpy.data.objects.new(name, PROPS[name]); bpy.context.collection.objects.link(ob)
    ob.location = (x, y, z); ob.rotation_euler = (tilt[0], tilt[1], rz); ob.scale = (s, s, s)
    return ob
prng = random.Random(4)
PR = lambda a, b: a + (b - a) * prng.random()
# 街口路障（前方，头车绕行）、两侧人行道杂物；西侧紧贴镜头的前景杂物制造视差
for y in (-6.0, -4.4):
    place("concrete_road_barrier", PR(2.2, 3.4), y, PR(-0.3, 0.3))
place("concrete_road_barrier", 5.6, 4.0, 1.4)
for i in range(70):
    side = -1 if i % 3 else 1
    x = side * PR(6.9 if side < 0 else 6.3, 8.2); y = PR(-72, 12)  # 西侧让出机位通道
    n = prng.choice(["old_tyre", "old_tyre", "barrel_03", "metal_jerrycan", "wooden_crate_01", "cement_bag", "cement_bag", "trashbag", "trashbag",
                     "rusted_wheel_rim_01", "plastic_monobloc_chair_01", "old_military_crate"])
    if n in ("old_tyre", "rusted_wheel_rim_01") and prng.random() < 0.6:
        place(n, x, y, PR(0, 6.3), tilt=(math.pi / 2, 0))  # 平放
    elif n == "old_tyre":
        place(n, x, y, PR(0, 6.3), tilt=(0, PR(-0.25, 0.25)), z=0.0)
    elif n == "plastic_monobloc_chair_01" and prng.random() < 0.4:
        place(n, x, y, PR(0, 6.3), tilt=(math.pi / 2, 0), z=0.3)  # 翻倒
    else:
        place(n, x, y, PR(0, 6.3))
for y in range(-70, 12, 14):  # 墙上配电箱
    place("utility_box_01", -8.45, y + PR(0, 6), -math.pi / 2, z=1.4)
    place("utility_box_01", 8.45, y + PR(0, 6), math.pi / 2, z=1.4)

# ---------------- 人物剪影（远中景，焦外 + 尘霾中只读轮廓与姿态） ----------------
SKIN = simple_mat("skin", (0.075, 0.045, 0.03), 0.55, noise=0.25, bump=0.08, scale=40)
HAIR = simple_mat("hair", (0.012, 0.01, 0.009), 0.7, noise=0.2, bump=0.4, scale=80)
def garb(name, c, fold=0.35):
    """布料：底色 + 竖向长褶（拉伸噪声做凹凸与明暗）+ 织纹。"""
    m, nt, out = node_mat(name); L = nt.links
    b = principled(nt, out, Roughness=0.92)
    if "Sheen Weight" in b.inputs: b.inputs["Sheen Weight"].default_value = 0.4
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (6, 6, 1.2)
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 3; n.inputs["Detail"].default_value = 4; L.new(mp.outputs[0], n.inputs["Vector"])
    w = nt.nodes.new("ShaderNodeTexNoise"); w.inputs["Scale"].default_value = 300; L.new(tc.outputs["Object"], w.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = fold
    mx.inputs[6].default_value = c + (1,); L.new(n.outputs["Color"], mx.inputs[7]); L.new(mx.outputs[2], b.inputs["Base Color"])
    hs = nt.nodes.new("ShaderNodeMath"); hs.operation = "MULTIPLY_ADD"; hs.inputs[1].default_value = 0.08
    L.new(w.outputs["Fac"], hs.inputs[0]); L.new(n.outputs["Fac"], hs.inputs[2])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.6; bp.inputs["Distance"].default_value = 0.02
    L.new(hs.outputs[0], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m
MEN_C = [(0.62, 0.58, 0.5), (0.7, 0.68, 0.62), (0.18, 0.22, 0.3), (0.5, 0.42, 0.25), (0.2, 0.2, 0.18), (0.3, 0.32, 0.22), (0.45, 0.4, 0.36), (0.12, 0.16, 0.2)]
WOMEN_C = [(0.55, 0.12, 0.08), (0.62, 0.32, 0.05), (0.1, 0.3, 0.2), (0.35, 0.1, 0.3), (0.12, 0.15, 0.38), (0.6, 0.45, 0.1), (0.05, 0.05, 0.06), (0.5, 0.2, 0.25)]
CLOTH = [garb(f"garb_m{i}", c) for i, c in enumerate(MEN_C)]
WCLOTH = [garb(f"garb_w{i}", c, 0.45) for i, c in enumerate(WOMEN_C)]
def limb(bm, a, b, r0, r1, mi, seg=12):
    a, b = Vector(a), Vector(b); d = b - a
    M = Matrix.Translation((a + b) / 2) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r0, radius2=r1, depth=d.length, matrix=M)
    for f in {f for v in res["verts"] for f in v.link_faces}: f.material_index = mi
def blob(bm, c, r, sc, mi, rot=None):
    M = Matrix.Translation(Vector(c)) @ (Euler(rot).to_matrix().to_4x4() if rot else Matrix()) @ Matrix.Diagonal((*sc, 1))
    res = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=r, matrix=M)
    for f in {f for v in res["verts"] for f in v.link_faces}: f.material_index = mi
def part(name, root, build, mats, loc, smooth_lv=1):
    bm = bmesh.new(); build(bm)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in mats: me.materials.append(m)
    for p_ in me.polygons: p_.use_smooth = True
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); ob.parent = root; ob.location = loc
    if smooth_lv: md = ob.modifiers.new("sub", "SUBSURF"); md.levels = md.render_levels = smooth_lv
    return ob
def person(name, x, y, heading, phase=None, pose="stand", h=1.72):
    """phase=None 站立；否则为步行/奔跑相位起点。
    男：衬衫 + macawis 围裙或长裤，可戴白色 koofiyad 小帽；女：dirac 长裙 + garbasaar 头巾披到肩背。
    躯干/骨盆/肩/颈/头分体建模后细分平滑；上下臂、大小腿分节，有肘/膝弯曲；手、脚单独成形。"""
    rp = random.Random(hash(name) & 0xffff); k = h / 1.72
    woman = rp.random() < 0.4
    root = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(root)
    root.location = (x, y, 0); root.rotation_euler = (0, 0, heading)
    if woman:
        top = WCLOTH[rp.randrange(len(WCLOTH))]; bot = top; scarf = WCLOTH[rp.randrange(len(WCLOTH))]
    else:
        top = CLOTH[rp.randrange(len(CLOTH))]; bot = CLOTH[rp.randrange(len(CLOTH))]; scarf = HAIR
    mats = [SKIN, top, bot, scarf]
    skirt = woman or rp.random() < 0.45
    def torso(bm):
        tv = [bm.verts.new(v) for v in [(-0.15 * k, -0.095, 0.95 * k), (0.15 * k, -0.095, 0.95 * k), (0.15 * k, 0.085, 0.95 * k), (-0.15 * k, 0.085, 0.95 * k),
                                        (-0.2 * k, -0.1, 1.44 * k), (0.2 * k, -0.1, 1.44 * k), (0.2 * k, 0.11, 1.44 * k), (-0.2 * k, 0.11, 1.44 * k)]]
        tf = [bm.faces.new([tv[j] for j in idx]) for idx in [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]]
        for f_ in tf: f_.material_index = 1
        bmesh.ops.recalc_face_normals(bm, faces=tf)
        bmesh.ops.subdivide_edges(bm, edges=list({e for f_ in tf for e in f_.edges}), cuts=2, use_grid_fill=True)
        blob(bm, (0, 0.005, 1.43 * k), 0.09 * k, (2.35, 1.25, 0.75), 1)                 # 肩
        blob(bm, (0, 0, 0.95 * k), 0.12 * k, (1.45, 1.0, 0.9), 2)                       # 骨盆
        limb(bm, (0, 0, 1.44 * k), (0, 0.012, 1.56 * k), 0.052 * k, 0.046 * k, 0)       # 颈
        blob(bm, (0, 0.012, 1.635 * k), 0.098 * k, (0.86, 1.0, 1.14), 0)                # 颅
        blob(bm, (0, 0.06, 1.595 * k), 0.06 * k, (1.0, 0.85, 0.9), 0)                   # 下颌/面部
        blob(bm, (0, 0.085, 1.625 * k), 0.018 * k, (0.8, 1.2, 1.6), 0)                  # 鼻
        if woman:
            blob(bm, (0, 0.0, 1.645 * k), 0.118 * k, (0.95, 1.05, 1.15), 3)             # 头巾包头
            limb(bm, (0, -0.01, 1.58 * k), (0, -0.02, 1.1 * k), 0.13 * k, 0.27 * k, 3, seg=16)   # 头巾垂到背
            limb(bm, (0, 0, 1.0 * k), (0, 0, 0.05 * k), 0.2 * k, 0.33 * k, 1, seg=16)   # dirac 长裙
        else:
            blob(bm, (0, -0.005, 1.665 * k), 0.1 * k, (0.9, 1.02, 0.7), 3)              # 短发
            if rp.random() < 0.35: blob(bm, (0, -0.005, 1.705 * k), 0.1 * k, (0.92, 1.02, 0.45), 1 if rp.random() < 0.5 else 2)  # 小帽
            if skirt: limb(bm, (0, 0, 0.98 * k), (0, 0, 0.3 * k), 0.165 * k, 0.21 * k, 2, seg=14)   # macawis
    body = part(name + "_b", root, torso, mats, (0, 0, 0))
    def arm(bm):  # 上臂 + 前臂（肘部微屈）+ 手
        limb(bm, (0, 0, 0), (0, 0.0, -0.3 * k), 0.048 * k, 0.04 * k, 1)
        blob(bm, (0, 0.0, -0.3 * k), 0.04 * k, (1, 1, 1), 1 if not woman else 1)
        limb(bm, (0, 0, -0.3 * k), (0, 0.06, -0.56 * k), 0.038 * k, 0.03 * k, 0 if not woman else 1)
        blob(bm, (0, 0.07, -0.63 * k), 0.045 * k, (0.55, 0.9, 1.5), 0)
    def leg(bm):  # 大腿 + 小腿 + 脚（凉鞋）
        limb(bm, (0, 0, 0), (0, 0.01, -0.44 * k), 0.075 * k, 0.055 * k, 2)
        limb(bm, (0, 0.01, -0.44 * k), (0, -0.01, -0.86 * k), 0.052 * k, 0.038 * k, 0 if skirt else 2)
        blob(bm, (0, 0.04, -0.89 * k), 0.05 * k, (0.75, 2.0, 0.55), 0)
    parts = []
    for side_, (hip, sh) in enumerate([((0.09, 0, 0.92), (0.205, 0, 1.4)), ((-0.09, 0, 0.92), (-0.205, 0, 1.4))]):
        if not woman:
            parts.append((part(name + "_leg", root, leg, mats, (hip[0] * k, hip[1], hip[2] * k)), side_, False))
        ab = part(name + "_arm", root, arm, mats, (sh[0] * k, sh[1], sh[2] * k)); ab.parent = body  # 手臂挂在躯干上，前倾时跟着走
        parts.append((ab, side_, True))
    for f in range(scene.frame_start - 2, scene.frame_end + 3):
        t = T0 + (f - 1) / FPS
        if phase is None:
            sway = math.sin(t * 1.3 + x) * 0.02
            for ob, s_, arm_ in parts:
                pt = arm_ and pose == "point" and s_ == 0
                ob.rotation_euler = ((1.25 if pt else 0) + sway, 0.08 * (1 if s_ else -1) * arm_ + (0.15 if pt else 0), 0)
                ob.keyframe_insert("rotation_euler", frame=f)
            body.rotation_euler = (0, 0, math.sin(t * 0.7 + y) * 0.25 if pose == "watch" else 0); body.keyframe_insert("rotation_euler", frame=f)
        else:
            spd = 1.4 if pose == "walk" else 4.2; ph = (phase + t * spd * 1.9) * math.pi
            root.location = (x - math.sin(heading) * spd * (t - T0), y + math.cos(heading) * spd * (t - T0), abs(math.sin(ph)) * 0.04 * spd)
            root.keyframe_insert("location", frame=f)
            for ob, s_, arm_ in parts:
                a = math.sin(ph + s_ * math.pi) * (0.45 if pose == "walk" else 0.9)
                ob.rotation_euler = ((a * 0.8 if arm_ else -a), 0, 0); ob.keyframe_insert("rotation_euler", frame=f)
            body.rotation_euler = (-(0.04 if pose == "walk" else 0.14), 0, 0); body.keyframe_insert("rotation_euler", frame=f)
# ---------------- TRELLIS.2 生成人物（--gen-people）：静态站立旁观者 ----------------
PEOPLE = []
def load_gen_people(d):
    """导入目录下每个人物 GLB → 身高归一到 1 m、脚底落地、面朝 +Y；布料去金属、加粗糙与一层沙尘。"""
    import glob, numpy as np
    for path in sorted(glob.glob(os.path.join(d, "trellis_*_300_1.glb"))):
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=path)
        new = [o for o in bpy.data.objects if o not in before]
        ob = [o for o in new if o.type == "MESH"][0]
        me = ob.data; me.transform(ob.matrix_world)
        for o in new: bpy.data.objects.remove(o)
        co = np.array([v.co for v in me.vertices]); mn, mx = co.min(0), co.max(0)
        me.transform(Matrix.Rotation(math.pi, 4, "Z") @ Matrix.Scale(1 / (mx[2] - mn[2]), 4) @ Matrix.Translation(Vector((-(mn[0] + mx[0]) / 2, -(mn[1] + mx[1]) / 2, -mn[2]))))
        for m in me.materials:
            nt = m.node_tree; bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
            for key in ("Metallic", "Roughness"):
                if bsdf.inputs[key].links: nt.links.remove(bsdf.inputs[key].links[0])
            bsdf.inputs["Metallic"].default_value = 0.0; bsdf.inputs["Roughness"].default_value = 0.78
            src = bsdf.inputs["Base Color"].links[0].from_socket
            mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.inputs["Factor"].default_value = 0.12
            nt.links.new(src, mix.inputs[6]); mix.inputs[7].default_value = (0.55, 0.47, 0.35, 1)
            nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
        PEOPLE.append((me, 0.82 if "trellis_m4" in path else 1.0)); print("GEN person", os.path.basename(path), len(me.polygons), "faces")  # m4 是少年，矮一些
def gen_person(name, x, y, heading, h, idx):
    if not PEOPLE: load_gen_people(GEN_PEOPLE)
    me, k = PEOPLE[idx % len(PEOPLE)]; h *= k
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    ob.location = (x, y, 0); ob.rotation_euler = (0, 0, heading); ob.scale = (h, h, h)
crowd = random.Random(7)
for i in range(26):  # 两侧人行道/门口旁观者
    side = crowd.choice([-1, -1, 1]); y = crowd.uniform(-35, 5)
    px, ph_ = side * crowd.uniform(7.0, 8.3), (math.pi / 2 if side < 0 else -math.pi / 2) + crowd.uniform(-0.9, 0.9) + (math.pi if crowd.random() < 0.2 else 0)
    pose, ph = crowd.choice(["stand", "stand", "watch", "point"]), crowd.uniform(1.6, 1.85)
    if GEN_PEOPLE: gen_person(f"p{i}", px, y, ph_, ph, i)
    else: person(f"p{i}", px, y, ph_, pose=pose, h=ph)
for i in range(6):  # 沿街步行
    side = crowd.choice([-1, 1])
    person(f"w{i}", side * crowd.uniform(7.0, 7.8), crowd.uniform(-32, 0), crowd.choice([0, math.pi]), phase=crowd.random(), pose="walk", h=crowd.uniform(1.6, 1.85))
for i, (x0, y0) in enumerate([(7.0, -8.0), (8.0, -5.5), (6.5, -2.0)]):  # 前方街口有人横穿跑开（紧张感）
    person(f"r{i}", x0, y0, math.pi / 2, phase=i * 0.3, pose="run", h=1.75)
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
    B.cyl("tire", r, r, w, (0, 0, 0), (0, math.pi / 2, 0), seg=40)
    for k in range(28):  # 胎纹块
        a = k / 28 * 2 * math.pi
        B.box("tire", (w * 0.9, 0.09, 0.05), (0, math.cos(a) * (r + 0.01), math.sin(a) * (r + 0.01)), (a, 0, 0))
    B.cyl("tan", r * 0.62, r * 0.62, w - 0.07, (0, 0, 0), (0, math.pi / 2, 0), seg=32)            # 轮辋：缩进胎侧之内
    B.cyl("tan", r * 0.66, r * 0.66, w - 0.12, (0, 0, 0), (0, math.pi / 2, 0), seg=32)            # 轮辋外缘（夹在胎唇里）
    B.cyl("grime", r * 0.26, r * 0.22, w - 0.02, (0, 0, 0), (0, math.pi / 2, 0), seg=20)          # 轮毂/轮边减速器端盖（油泥）
    for k in range(8):
        a = k / 8 * 2 * math.pi; B.cyl("steel", 0.022, 0.018, w + 0.01, (0, math.cos(a) * r * 0.4, math.sin(a) * r * 0.4), (0, math.pi / 2, 0), seg=6)
    for k in range(6):  # 中央加强筋
        a = k / 6 * 2 * math.pi; B.box("tan", (w - 0.05, 0.03, r * 0.3), (0, math.cos(a) * r * 0.45, math.sin(a) * r * 0.45), (a, 0, 0))
    ob = B.obj(name, bevel=0.05, parent=parent); ob.location = loc; ob.modifiers["bevel"].segments = 3  # 胎肩圆角
    return ob

def turret_crew(B):
    """炮塔环、M2 与机枪手（车顶高 1.83 m 为基准）。"""
    S = (-1, 1)
    B.cyl("tan", 0.58, 0.58, 0.16, (0, -0.6, 1.91), seg=36)
    B.cyl("gasket", 0.5, 0.5, 0.17, (0, -0.6, 1.915), seg=36)
    B.box("tan", (0.8, 0.05, 0.5), (0, -0.16, 2.2), (-0.08, 0, 0)); B.box("tan", (0.3, 0.05, 0.36), (-0.52, -0.3, 2.14), (0, 0, 0.9)); B.box("tan", (0.3, 0.05, 0.36), (0.52, -0.3, 2.14), (0, 0, -0.9))
    B.cyl("steel", 0.04, 0.04, 1.14, (0, 0.38, 2.2), (math.pi / 2 - 0.06, 0, 0), seg=12)                   # 枪管
    B.cyl("steel", 0.055, 0.055, 0.28, (0, 0.06, 2.2), (math.pi / 2 - 0.06, 0, 0), seg=12)                 # 枪管套
    B.box("steel", (0.18, 0.62, 0.2), (0, -0.4, 2.2)); B.box("steel", (0.12, 0.2, 0.1), (0.2, -0.4, 2.16))   # 机匣 + 弹箱
    B.box("olive", (0.16, 0.3, 0.2), (0.24, -0.38, 2.08))
    B.cyl("steel", 0.04, 0.04, 0.3, (0, -0.5, 2.0), seg=8)                                                 # 枪架
    B.cyl("olive", 0.21, 0.24, 0.55, (0, -0.85, 2.25), seg=16)
    B.cyl("olive", 0.24, 0.24, 0.3, (0, -0.85, 2.38), seg=16)                                              # 防弹背心
    B.cyl("olive", 0.05, 0.05, 0.1, (0, -0.83, 2.6), seg=10)
    for (c, r, sc, key) in [((0, -0.82, 2.73), 0.12, (0.9, 1.0, 1.15), "skin"), ((0, -0.84, 2.79), 0.17, (1.0, 1.1, 0.72), "canvas"),
                            ((0, -0.69, 2.84), 0.12, (1.1, 0.25, 0.25), "gasket")]:
        hb = bmesh.ops.create_uvsphere(B.bm, u_segments=16, v_segments=10, radius=r, matrix=Matrix.Translation(c) @ Matrix.Diagonal((*sc, 1)))
        i = B.mi(key)
        for f in {f for v in hb["verts"] for f in v.link_faces}: f.material_index = i
    for s in S:
        B.cyl("olive", 0.07, 0.065, 0.32, (s * 0.26, -0.78, 2.42), (0.2, s * 0.35, 0), seg=10)            # 上臂
        B.cyl("olive", 0.06, 0.05, 0.36, (s * 0.2, -0.62, 2.3), (1.2, s * 0.2, 0), seg=10)                 # 前臂伸向枪柄

def humvee(name):
    """M1025 武器载车（按公开尺寸：长 4.57、宽 2.16、顶高 1.83、轴距 3.3 m）：
    收腰硬顶车厢 + 斜背、宽平引擎盖/翼子板、外露轮拱与车桥、带胶条的窗、外露门铰链、格栅/灯组/护杠、炮塔与随车装载。"""
    root = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(root)
    body = bpy.data.objects.new(name + "_body", None); bpy.context.collection.objects.link(body); body.parent = root
    B = Builder(); S = (-1, 1)
    # —— 外壳 ——
    B.hull("tan", [(-1.08, 0.85, 0.98), (1.08, 0.85, 0.98), (1.08, 2.30, 0.98), (-1.08, 2.30, 0.98)],
                  [(-1.02, 0.85, 1.24), (1.02, 0.85, 1.24), (1.0, 2.22, 1.10), (-1.0, 2.22, 1.10)])          # 引擎盖+前翼子板
    B.hull("tan", [(-0.52, 0.95, 1.2), (0.52, 0.95, 1.2), (0.5, 2.15, 1.08), (-0.5, 2.15, 1.08)],
                  [(-0.46, 0.95, 1.275), (0.46, 0.95, 1.275), (0.44, 2.12, 1.14), (-0.44, 2.12, 1.14)])       # 引擎盖中央隆起
    B.box("tan", (2.12, 0.07, 0.3), (0, 2.28, 0.86))                                                        # 前脸下板
    B.box("tan", (2.14, 1.9, 0.62), (0, -0.1, 0.93))                                                        # 车门下部/车厢底盆
    B.box("tan", (2.16, 1.25, 0.28), (0, -1.66, 1.12))                                                      # 后翼子板平台
    B.box("tan", (1.4, 1.2, 0.36), (0, -1.66, 0.8))                                                         # 后部下盆
    B.hull("tan", [(-1.04, 0.80, 1.24), (1.04, 0.80, 1.24), (1.04, -1.25, 1.24), (-1.04, -1.25, 1.24)],
                  [(-0.88, 0.52, 1.83), (0.88, 0.52, 1.83), (0.88, -1.25, 1.83), (-0.88, -1.25, 1.83)])       # 收腰硬顶车厢
    B.hull("tan", [(-1.04, -1.25, 1.24), (1.04, -1.25, 1.24), (1.04, -2.26, 1.24), (-1.04, -2.26, 1.24)],
                  [(-0.88, -1.25, 1.83), (0.88, -1.25, 1.83), (0.95, -2.26, 1.42), (-0.95, -2.26, 1.42)])     # 斜背货舱
    # —— 窗：风挡两片 + 中柱；侧窗四片（贴合收腰斜面），黑色胶条框 ——
    wa = math.atan2(0.28, 0.56); nW = Vector((0, math.cos(wa), math.sin(wa)))
    for s in S:
        c = Vector((s * 0.45, 0.66, 1.52)) + nW * 0.012
        B.box("gasket", (0.84, 0.012, 0.56), c - nW * 0.004, (wa, 0, 0)); B.box("glass", (0.78, 0.012, 0.5), c, (wa, 0, 0))
    B.box("tan", (0.07, 0.03, 0.6), Vector((0, 0.66, 1.52)) + nW * 0.02, (wa, 0, 0))
    B.box("steel", (0.012, 0.012, 0.5), Vector((0.1, 0.66, 1.29)) + nW * 0.03, (wa + 1.2, 0, 0.3))           # 雨刮
    B.box("steel", (0.012, 0.012, 0.5), Vector((-0.75, 0.66, 1.29)) + nW * 0.03, (wa + 1.2, 0, 0.3))
    ta = math.atan2(0.16, 0.59)
    for s in S:
        nS = Vector((s * math.cos(ta), 0, math.sin(ta)))
        for (y0, y1) in [(0.05, 0.62), (-0.95, -0.2)]:
            zc = 1.56; xc = s * (1.04 - (zc - 1.24) * 0.16 / 0.59)
            c = Vector((xc, (y0 + y1) / 2, zc)) + nS * 0.012
            B.box("gasket", (0.012, y1 - y0 + 0.06, 0.46), c - nS * 0.004, (0, -s * ta, 0)); B.box("glass", (0.012, y1 - y0, 0.4), c, (0, -s * ta, 0))
        # 门缝（车厢斜面 + 底盆竖直面）与铰链、把手
        for yy in (0.8, -0.12, -1.02):
            B.box("gasket", (0.012, 0.012, 0.58), Vector((s * 0.97, yy, 1.53)) + nS * 0.006, (0, -s * ta, 0))
            B.box("gasket", (0.012, 0.012, 0.6), (s * 1.074, yy, 0.93))
        B.box("gasket", (0.012, 1.84, 0.012), (s * 1.074, -0.11, 0.64))
        for yy in (0.76, -0.16):
            for zz in (0.82, 1.12, 1.45):
                B.cyl("steel", 0.022, 0.022, 0.1, (s * (1.085 if zz < 1.3 else 1.0 - (zz - 1.24) * 0.27 + 0.015), yy, zz), seg=8)
        for yy in (0.15, -0.85):
            B.box("steel", (0.04, 0.16, 0.035), (s * 1.09, yy, 1.12))
            B.box("gasket", (0.02, 0.05, 0.05), (s * 1.09, yy + 0.06, 1.05))   # 门锁
        # 后视镜：支臂 + 镜面
        B.cyl("steel", 0.012, 0.012, 0.36, (s * 1.12, 0.78, 1.45), (0, s * 1.1, 0), seg=6)
        B.box("gasket", (0.05, 0.17, 0.26), (s * 1.28, 0.8, 1.55), (0, 0, s * 0.15))
        # 前大灯（深嵌灯座 + 镜片）、转向灯、尾灯
        B.cyl("gasket", 0.105, 0.105, 0.06, (s * 0.8, 2.315, 0.9), (math.pi / 2, 0, 0), seg=24)
        B.cyl("lens", 0.08, 0.08, 0.02, (s * 0.8, 2.345, 0.9), (math.pi / 2, 0, 0), seg=24)
        B.box("amber", (0.08, 0.03, 0.06), (s * 0.8, 2.33, 0.76))
        B.box("paint_r", (0.1, 0.03, 0.14), (s * 0.92, -2.27, 1.1))
        # 轮拱内衬、车桥半轴
        for yy in (1.65, -1.65):
            B.box("steel", (0.04, 1.05, 0.48), (s * 0.7, yy, 0.74))
            B.cyl("steel", 0.06, 0.06, 0.55, (s * 0.42, yy, 0.52), (0, math.pi / 2, 0), seg=10)
        # 外扩翼子板唇边（轮拱上沿）
        B.box("tan", (0.32, 1.25, 0.05), (s * 0.94, 1.6, 0.975)); B.box("tan", (0.32, 1.2, 0.05), (s * 0.94, -1.66, 1.0))
    # 格栅：竖向散热槽
    B.box("gasket", (1.1, 0.04, 0.3), (0, 2.31, 0.88))
    for k in range(9): B.box("tan", (0.05, 0.05, 0.3), (-0.48 + k * 0.12, 2.32, 0.88))
    # 保险杠、拖钩、护杠、绞盘
    B.box("steel", (2.0, 0.16, 0.16), (0, 2.42, 0.6)); B.box("gasket", (0.5, 0.2, 0.22), (0, 2.42, 0.62))
    for s in S:
        B.cyl("steel", 0.04, 0.04, 0.16, (s * 0.62, 2.53, 0.6), (math.pi / 2, 0, 0), seg=10)
        B.cyl("steel", 0.025, 0.025, 0.55, (s * 0.5, 2.5, 0.92), seg=8)
    B.cyl("steel", 0.025, 0.025, 1.0, (0, 2.5, 1.2), (0, math.pi / 2, 0), seg=8)
    # 车架、差速器
    for s in S: B.box("steel", (0.12, 4.2, 0.2), (s * 0.45, 0, 0.55))
    for yy in (1.65, -1.65): B.cyl("steel", 0.17, 0.17, 0.3, (0, yy, 0.5), (0, math.pi / 2, 0), seg=16)
    B.box("steel", (0.5, 2.6, 0.18), (0, 0, 0.42))                                                         # 传动轴/油箱护板
    turret_crew(B)
    # —— 随车装载：车顶背囊/弹药箱、后部油桶、鞭状天线 ——
    for k, (x, y, w_, d_, h_) in enumerate([(-0.5, -1.55, 0.5, 0.35, 0.28), (0.45, -1.5, 0.45, 0.4, 0.25), (0.0, -1.95, 0.9, 0.3, 0.2)]):
        B.box("canvas", (w_, d_, h_), (x, y, 1.83 - (0.18 if y < -1.6 else 0) + h_ / 2), (0.25 if y < -1.6 else 0, 0, R(-0.15, 0.15)))
    B.box("olive", (0.3, 0.16, 0.2), (0.6, -0.95, 1.93))
    for s in S:
        B.cyl("steel", 0.009, 0.004, 2.6, (s * 0.95, -2.05, 2.65), (0.08, -s * 0.05, 0), seg=6)
        B.cyl("gasket", 0.03, 0.03, 0.12, (s * 0.95, -2.05, 1.36), seg=8)
    # —— 车内：仪表台、方向盘、座椅、驾驶员与副驾（PASGT 头盔、防弹背心），透过车窗可见 ——
    B.box("gasket", (1.9, 0.35, 0.22), (0, 0.62, 1.3)); B.box("grime", (2.0, 2.0, 0.03), (0, -0.2, 1.0))
    B.cyl("gasket", 0.19, 0.19, 0.03, (-0.48, 0.38, 1.42), (1.1, 0, 0), seg=20)
    for sx in (-0.48, 0.48):
        B.box("olive", (0.48, 0.12, 0.6), (sx, -0.35, 1.38), (-0.15, 0, 0)); B.box("olive", (0.48, 0.45, 0.12), (sx, -0.1, 1.12))
        B.cyl("olive", 0.17, 0.2, 0.42, (sx, -0.14, 1.36), seg=14)                                           # 躯干 + 背心
        B.cyl("olive", 0.045, 0.045, 0.1, (sx, -0.12, 1.6), seg=10)
        for (c, rr, sc, key) in [((sx, -0.1, 1.71), 0.1, (0.9, 1.0, 1.15), "skin"), ((sx, -0.12, 1.76), 0.14, (1.0, 1.1, 0.7), "canvas")]:
            hb = bmesh.ops.create_uvsphere(B.bm, u_segments=14, v_segments=8, radius=rr, matrix=Matrix.Translation(c) @ Matrix.Diagonal((*sc, 1)))
            i = B.mi(key)
            for f in {f for v in hb["verts"] for f in v.link_faces}: f.material_index = i
        for s in S:
            B.cyl("olive", 0.05, 0.045, 0.42, (sx + s * 0.16, 0.1, 1.42), (1.1, 0, -s * 0.15), seg=8)          # 手臂前伸
    sh = B.obj(name + "_shell", bevel=0.045, parent=body); sh.modifiers["bevel"].segments = 3
    for s in S:
        jc = bpy.data.objects.new(name + "_can", PROPS["metal_jerrycan"]); bpy.context.collection.objects.link(jc)
        jc.parent = body; jc.location = (s * 0.72, -2.32, 0.78); jc.rotation_euler = (0, 0, math.pi / 2)
    wheels = [wheel(f"{name}_w{i}", 0.47, 0.32, root, loc) for i, loc in enumerate([(-0.92, 1.65, 0.47), (0.92, 1.65, 0.47), (-0.92, -1.65, 0.47), (0.92, -1.65, 0.47)])]
    return root, body, wheels

# ---------------- TRELLIS.2 生成悍马（--gen-humvee）----------------
GEN = {}
def load_gen_humvee(path):
    """导入 GLB → 车长缩放到 4.57 m、车头朝 +Y、落地；把四个车轮切成独立网格（原点在轮心，可旋转）；
    改材质：车窗（低亮度 + 高处 + 竖直面）换成光滑反光玻璃，叠加沙尘膜与下半车身泥浆。"""
    import numpy as np
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    ob = [o for o in new if o.type == "MESH"][0]
    me = ob.data; me.transform(ob.matrix_world)
    for o in new: bpy.data.objects.remove(o)
    co = np.array([v.co for v in me.vertices])
    mn, mx = co.min(0), co.max(0); k = 4.57 / (mx[1] - mn[1])
    me.transform(Matrix.Rotation(math.pi, 4, "Z") @ Matrix.Scale(k, 4) @ Matrix.Translation(Vector((-(mn[0] + mx[0]) / 2, -(mn[1] + mx[1]) / 2, -mn[2]))))
    co = np.array([v.co for v in me.vertices])
    # 车轮：轮心以下（z<0.45）、车身外侧（|x|>0.8）的点，在 y 向的跨度≈轮径
    wheels = []
    for sx in (-1, 1):
        for sy in (1, -1):
            sel = co[(co[:, 0] * sx > 0.8) & (co[:, 1] * sy > 0.6) & (co[:, 2] < 0.42)]
            y0, y1 = sel[:, 1].min(), sel[:, 1].max(); r = (y1 - y0) / 2
            wheels.append((Vector((sx * 0.5 * (np.abs(sel[:, 0]).min() + np.abs(sel[:, 0]).max()), (y0 + y1) / 2, r)), r, np.abs(sel[:, 0]).min()))
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    parts = []
    for c, r, xin in wheels:
        fs = [f for f in bm.faces if (lambda m: m.x * c.x > 0 and abs(m.x) > xin - 0.06 and math.hypot(m.y - c.y, m.z - c.z) < r * 1.02)(f.calc_center_median())]
        wm = bmesh.new(); vmap = {}
        uv_src = bm.loops.layers.uv.active; uv_dst = wm.loops.layers.uv.new("UVMap") if uv_src else None
        for f in fs:
            vs = [vmap.setdefault(v, wm.verts.new(v.co - c)) for v in f.verts]
            try: nf = wm.faces.new(vs)
            except ValueError: continue
            nf.smooth = f.smooth
            if uv_src:
                for l0, l1 in zip(f.loops, nf.loops): l1[uv_dst].uv = l0[uv_src].uv
        wme = bpy.data.meshes.new("gen_wheel"); wm.to_mesh(wme); wm.free()
        for m in me.materials: wme.materials.append(m)
        parts.append((wme, c.copy(), r))
        bmesh.ops.delete(bm, geom=fs, context="FACES_ONLY")
    bm.to_mesh(me); bm.free()
    # 车顶高度（驾驶室中部）
    co = np.array([v.co for v in me.vertices])
    roof = float(co[(np.abs(co[:, 0]) < 0.4) & (co[:, 1] > -1.0) & (co[:, 1] < 0.0)][:, 2].max())
    gen_grime(me.materials[0])
    print("GEN humvee", len(me.polygons), "faces; wheels", [(tuple(round(x, 2) for x in c), round(r, 2)) for _, c, r in parts], "roof", round(roof, 2))
    return me, parts, roof

def gen_grime(m):
    nt = m.node_tree; L = nt.links
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    base_src = bsdf.inputs["Base Color"].links[0].from_socket
    rough_src = bsdf.inputs["Roughness"].links[0].from_socket if bsdf.inputs["Roughness"].links else None
    def node(kind, **kw):
        n = nt.nodes.new(kind)
        for k_, v in kw.items(): setattr(n, k_, v)
        return n
    tc = node("ShaderNodeTexCoord"); sep = node("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    geo = node("ShaderNodeNewGeometry"); nsep = node("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Normal"], nsep.inputs[0])
    def noise(scale, detail=6):
        n = node("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = detail
        L.new(tc.outputs["Object"], n.inputs["Vector"]); return n.outputs["Fac"]
    def rng_(sock, a, b, c=0.0, d=1.0):
        n = node("ShaderNodeMapRange"); L.new(sock, n.inputs[0])
        for i, v in zip((1, 2, 3, 4), (a, b, c, d)): n.inputs[i].default_value = v
        return n.outputs[0]
    def mul(x, y):
        n = node("ShaderNodeMath", operation="MULTIPLY")
        for i, v in enumerate((x, y)):
            if isinstance(v, float): n.inputs[i].default_value = v
            else: L.new(v, n.inputs[i])
        return n.outputs[0]
    def mixc(a, c, fac):
        n = node("ShaderNodeMix", data_type="RGBA"); L.new(fac, n.inputs["Factor"])
        for sock, v in ((n.inputs[6], a), (n.inputs[7], c)):
            if isinstance(v, tuple): sock.default_value = (*v, 1)
            else: L.new(v, sock)
        return n.outputs[2]
    lum = node("ShaderNodeRGBToBW"); L.new(base_src, lum.inputs[0])
    # 车窗遮罩：暗、在腰线以上、近竖直面
    glass = mul(mul(rng_(lum.outputs[0], 0.09, 0.04), rng_(sep.outputs[2], 1.2, 1.3)), rng_(nsep.outputs[2], 0.85, 0.6))
    col = mixc(base_src, (0.55, 0.47, 0.35), mul(rng_(noise(1.5), 0.45, 0.7), 0.35))          # 沙尘膜
    mud = mul(rng_(sep.outputs[2], 1.1, 0.5), rng_(noise(3.0, 8), 0.35, 0.65))                # 下半车身泥浆
    col = mixc(col, (0.36, 0.29, 0.2), mul(mud, 0.8))
    col = mixc(col, (0.012, 0.013, 0.014), glass)
    L.new(col, bsdf.inputs["Base Color"])
    r0 = rough_src if rough_src else None
    rmix = node("ShaderNodeMix", data_type="FLOAT"); L.new(glass, rmix.inputs["Factor"]); rmix.inputs[3].default_value = 0.05
    if r0:
        radd = node("ShaderNodeMath", operation="ADD", use_clamp=True); L.new(r0, radd.inputs[0]); L.new(mul(mud, 0.25), radd.inputs[1])
        L.new(radd.outputs[0], rmix.inputs[2])
    else: rmix.inputs[2].default_value = 0.7
    L.new(rmix.outputs[0], bsdf.inputs["Roughness"])
    met = bsdf.inputs["Metallic"]
    if met.links: nt.links.remove(met.links[0])
    met.default_value = 0.0

def humvee_gen(name):
    if not GEN: GEN["data"] = load_gen_humvee(GEN_HUMVEE)
    me, parts, roof = GEN["data"]
    root = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(root)
    body = bpy.data.objects.new(name + "_body", None); bpy.context.collection.objects.link(body); body.parent = root
    sh = bpy.data.objects.new(name + "_shell", me); bpy.context.collection.objects.link(sh); sh.parent = body
    B = Builder(); turret_crew(B)
    tc = B.obj(name + "_turret", bevel=0.03, parent=body); tc.location = (0, 0, roof - 1.83)
    wheels = []
    for i, (wme, c, r) in enumerate(parts):
        w = bpy.data.objects.new(f"{name}_w{i}", wme); bpy.context.collection.objects.link(w); w.parent = root; w.location = c
        wheels.append(w)
    GEN["r"] = sum(r for _, _, r in parts) / len(parts)
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

make_hv = humvee_gen if GEN_HUMVEE else humvee
convoy = [make_hv("hmmwv_0"), make_hv("hmmwv_1"), truck("truck_2")]
GAPS = [0, 13, 27]
RADII = [GEN.get("r", 0.47), GEN.get("r", 0.47), 0.55]
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
    vol.inputs["Color"].default_value = (0.86, 0.74, 0.56, 1); vol.inputs["Anisotropy"].default_value = 0.3
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
            px = LANE_X + wheel_side * (1 + a * (2.2 if front else 0.6))
            s = (0.5 + a * 3.2) if front else (0.9 + a * 1.5)
            px = max(px, LANE_X - 3.7 + 1.0 + s * 1.3)  # 尘团外缘与机位保持 ≥1 m，不吞镜头
            ob.location = (px, y + (4.2 if front else 0), 0.35 + a * 0.7); ob.scale = (s * 1.3, s * 1.6, s * 0.8)
            dens.inputs[1].default_value = (0.45 if vi == 0 else 2.0) * math.sin(math.pi * min(1, a / LIFE)) * min(1, a / 0.25)
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
dd = nt.nodes.new("ShaderNodeMath"); dd.operation = "MULTIPLY"; dd.inputs[1].default_value = 0.18; L.new(mul.outputs[0], dd.inputs[0])
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
hv = nt.nodes.new("ShaderNodeVolumePrincipled"); hv.inputs["Color"].default_value = (0.95, 0.72, 0.45, 1); hv.inputs["Density"].default_value = 0.0006; hv.inputs["Anisotropy"].default_value = 0.45
ho = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(hv.outputs[0], ho.inputs["Volume"]); haze.data.materials.append(hm)

# ---------------- light & world ----------------
sun_dir = Vector((-0.45, 0.7, 0.62)).normalized()  # 指向太阳：低角度、镜头前方偏左 → 侧逆光，掠过车身朝镜头一侧勾出板件，并在街上投下穿街光束
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); bpy.context.collection.objects.link(sun)
sun.data.energy = 9.0; sun.data.angle = math.radians(0.6); sun.data.color = (1.0, 0.78, 0.55)
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
# 天空压一层沙尘色：不要干净的蓝天
# 沙尘天空：地平线暖白、天顶偏灰蓝，太阳方向一团暖色光晕（而不是一块平涂的灰）
wtc = wn.nodes.new("ShaderNodeTexCoord"); wsep = wn.nodes.new("ShaderNodeSeparateXYZ"); wn.links.new(wtc.outputs["Generated"], wsep.inputs[0])
hz = wn.nodes.new("ShaderNodeMapRange"); hz.inputs["From Min"].default_value = 0.0; hz.inputs["From Max"].default_value = 0.55
wn.links.new(wsep.outputs["Z"], hz.inputs["Value"])
hpow = wn.nodes.new("ShaderNodeMath"); hpow.operation = "POWER"; hpow.inputs[1].default_value = 0.6; wn.links.new(hz.outputs[0], hpow.inputs[0])
grad = wn.nodes.new("ShaderNodeMix"); grad.data_type = "RGBA"; grad.inputs[6].default_value = (1.0, 0.82, 0.6, 1); grad.inputs[7].default_value = (0.5, 0.5, 0.5, 1)
wn.links.new(hpow.outputs[0], grad.inputs["Factor"])
sdot = wn.nodes.new("ShaderNodeVectorMath"); sdot.operation = "DOT_PRODUCT"; sdot.inputs[1].default_value = tuple(sun_dir)
wn.links.new(wtc.outputs["Generated"], sdot.inputs[0])
glow = wn.nodes.new("ShaderNodeMath"); glow.operation = "POWER"; glow.inputs[1].default_value = 6.0; glow.use_clamp = True
gcl = wn.nodes.new("ShaderNodeMath"); gcl.operation = "MAXIMUM"; gcl.inputs[1].default_value = 0.0; wn.links.new(sdot.outputs["Value"], gcl.inputs[0])
wn.links.new(gcl.outputs[0], glow.inputs[0])
gl = wn.nodes.new("ShaderNodeMix"); gl.data_type = "RGBA"; gl.blend_type = "ADD"; gl.inputs[7].default_value = (0.9, 0.6, 0.3, 1)
wn.links.new(glow.outputs[0], gl.inputs["Factor"]); wn.links.new(grad.outputs[2], gl.inputs[6])
dusty = wn.nodes.new("ShaderNodeMix"); dusty.data_type = "RGBA"; dusty.inputs["Factor"].default_value = 0.75
wn.links.new(warm.outputs[2], dusty.inputs[6]); wn.links.new(gl.outputs[2], dusty.inputs[7]); warm = dusty
# 照明用 Poly Haven HDRI（goegap，沙漠正午）提供真实天光层次；镜头直视的背景仍用尘霾天空，避免 HDRI 远山穿帮
env = wn.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(os.path.join(ASSETS, "hdri", "goegap_4k.hdr"))
emap = wn.nodes.new("ShaderNodeMapping"); emap.inputs["Rotation"].default_value = (0, 0, math.atan2(sun_dir.x, sun_dir.y))
etc = wn.nodes.new("ShaderNodeTexCoord"); wn.links.new(etc.outputs["Generated"], emap.inputs["Vector"]); wn.links.new(emap.outputs[0], env.inputs["Vector"])
ebg = wn.nodes.new("ShaderNodeBackground"); ebg.inputs["Strength"].default_value = 0.45
ewarm = wn.nodes.new("ShaderNodeMix"); ewarm.data_type = "RGBA"; ewarm.blend_type = "MULTIPLY"; ewarm.inputs["Factor"].default_value = 1.0; ewarm.inputs[7].default_value = (1.0, 0.8, 0.58, 1)
wn.links.new(env.outputs[0], ewarm.inputs[6]); wn.links.new(ewarm.outputs[2], ebg.inputs[0])
lp = wn.nodes.new("ShaderNodeLightPath"); wsel = wn.nodes.new("ShaderNodeMixShader")
wn.links.new(lp.outputs["Is Camera Ray"], wsel.inputs[0]); wn.links.new(ebg.outputs[0], wsel.inputs[1])
bg.inputs["Strength"].default_value = 0.09
wo = wn.nodes.new("ShaderNodeOutputWorld"); wn.links.new(warm.outputs[2], bg.inputs[0]); wn.links.new(bg.outputs[0], wsel.inputs[2]); wn.links.new(wsel.outputs[0], wo.inputs["Surface"])
print("SKY", sky.sky_type)

# ---------------- camera ----------------
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); bpy.context.collection.objects.link(cam); scene.camera = cam
cam.data.sensor_fit = "VERTICAL"; cam.data.angle_y = math.radians(44); cam.data.clip_start = 0.1; cam.data.clip_end = 2000
cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 2.8; cam.data.dof.aperture_ratio = 1.6; cam.data.dof.aperture_blades = 7
from mathutils import noise as mnoise
def hand(t, seed, amp, freq):
    """手持：低频漂移 + 中频呼吸 + 高频颤动（Perlin），比正弦叠加更像真人肩扛。"""
    v = Vector((seed * 31.7, seed * 11.3, 0.0))
    return sum(mnoise.noise(v + Vector((t * freq * k, 0, 0))) * amp / k for k in (1, 2.7, 6.1))
BUMPS = [(14.05, 1.0), (14.9, 0.6), (15.62, 1.2), (16.2, 0.7)]  # 路面颠簸：衰减振荡
def bump(t):
    return sum(a * math.exp(-(t - t0) * 9) * math.sin((t - t0) * 38) for t0, a in BUMPS if t >= t0) * 0.018
for f in range(scene.frame_start - 2, scene.frame_end + 3):
    t = T0 + (f - 1) / FPS; u = max(0, min(1, (t - T0) / (T1 - T0)))
    z = -lead_y(t)  # three z
    sx, sy = hand(t, 1, 0.07, 0.9), hand(t, 2, 0.05, 1.1) + bump(t)
    pos = Vector((LANE_X - 3.7 + sx, -(z + 3.4 - u * 1.4), 0.8 + sy))  # 比实时版稍远、更低：仰拍，机枪手入画
    look = Vector((LANE_X + 0.4 + hand(t, 3, 0.12, 0.6), -(z - 3.2 - u * 0.6), 1.75 + hand(t, 4, 0.06, 0.7) + bump(t) * 0.6))
    d = look - pos
    q = d.to_track_quat("-Z", "Y"); e = q.to_euler(); e.rotate_axis("Z", hand(t, 5, 0.012, 0.8))
    cam.location = pos; cam.rotation_euler = e
    # 对焦：跟头车，带一点跟焦员的滞后与呼吸
    cam.data.dof.focus_distance = (Vector((LANE_X, -z, 1.2)) - pos).length * (1 + hand(t, 6, 0.05, 0.5))
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
    cam.data.dof.keyframe_insert("focus_distance", frame=f)

# ---------------- render settings ----------------
r = scene.render
r.engine = "CYCLES"; r.resolution_x, r.resolution_y = 1920, 816; r.resolution_percentage = RES_PCT
r.use_motion_blur = True; r.motion_blur_shutter = 0.5
r.image_settings.file_format = "PNG"; r.image_settings.color_depth = "16"
r.use_overwrite = False; r.use_placeholder = True  # 中断后重跑会跳过已渲染的帧
cy = scene.cycles
prefs = bpy.context.preferences.addons["cycles"].preferences; prefs.compute_device_type = "METAL"; prefs.get_devices()
for dv in prefs.devices: dv.use = dv.type == "METAL"
cy.device = "GPU"; cy.samples = SAMPLES; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.02
cy.use_denoising = True
cy.max_bounces = 6; cy.diffuse_bounces = 3; cy.glossy_bounces = 2; cy.volume_bounces = 1; cy.transparent_max_bounces = 4
cy.volume_step_rate = 2.0; cy.volume_preview_step_rate = 4.0
cy.seed = 1993; cy.use_animated_seed = True
try:
    scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Punchy"; scene.view_settings.exposure = -0.1
except Exception:
    pass
r.filepath = os.path.join(OUT, "f_####")
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "..", "convoy_hero.blend"))
if "--no-render" in argv:
    pass  # 只搭场景、存 .blend（检查脚本用，不占 GPU）
elif STILL:
    scene.frame_set(STILL); r.filepath = os.path.join(OUT, f"still_{STILL:04d}"); bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
