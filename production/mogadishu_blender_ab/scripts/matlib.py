# 共享材质库与 Builder（从 convoy_hero.py 抽出，供 city_shots.py 复用）。导入时即创建 MAT 中的全部材质。
import bpy, bmesh, math, os
from mathutils import Vector, Matrix, Euler

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
    """CARC 沙漠黄（686A）野战车漆：偏暗哑的底漆 + 全车一层浮尘 + 车身下部溅泥 + 缝隙积垢（AO）
    + 水平面积尘 + 从棱边往下的雨/油痕 + 凸边磨损。目标是“跑过几百公里土路”的车，不是新车。"""
    m, nt, out = node_mat("tan_paint"); L = nt.links
    b = principled(nt, out, Roughness=0.7, Metallic=0.0)
    geo = nt.nodes.new("ShaderNodeNewGeometry"); tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    def node(kind, **kw):
        n = nt.nodes.new(kind)
        for k, v in kw.items():
            if k in n.inputs: n.inputs[k].default_value = v
            else: setattr(n, k, v)
        return n
    def mix(a, c, fac, blend="MIX"):
        x = node("ShaderNodeMix", data_type="RGBA", blend_type=blend)
        for i, v in ((6, a), (7, c)):
            if isinstance(v, tuple): x.inputs[i].default_value = v
            else: L.new(v, x.inputs[i])
        if isinstance(fac, float): x.inputs["Factor"].default_value = fac
        else: L.new(fac, x.inputs["Factor"])
        return x.outputs[2]
    def rng_(v, a, b_, c=0.0, d=1.0):
        r = node("ShaderNodeMapRange"); r.inputs["From Min"].default_value = a; r.inputs["From Max"].default_value = b_
        r.inputs["To Min"].default_value = c; r.inputs["To Max"].default_value = d; L.new(v, r.inputs["Value"]); return r.outputs[0]
    def mul(a, c):
        x = node("ShaderNodeMath", operation="MULTIPLY"); L.new(a, x.inputs[0])
        if isinstance(c, float): x.inputs[1].default_value = c
        else: L.new(c, x.inputs[1])
        return x.outputs[0]
    def noise(scale, detail, vec=None, sc=None):
        n = node("ShaderNodeTexNoise", Scale=scale, Detail=detail)
        if sc:
            mp = node("ShaderNodeMapping"); mp.inputs["Scale"].default_value = sc; L.new(tc.outputs["Object"], mp.inputs["Vector"]); L.new(mp.outputs[0], n.inputs["Vector"])
        else: L.new(tc.outputs["Object"], n.inputs["Vector"])
        return n
    # 底漆：比原来暗、灰一些，大块色差（补漆/日晒）
    big = noise(0.9, 3.0)
    col = mix((0.40, 0.32, 0.20, 1), big.outputs["Color"], 0.18, "OVERLAY")
    patch = rng_(noise(0.6, 2.0).outputs["Fac"], 0.56, 0.6)
    col = mix(col, (0.36, 0.30, 0.20, 1), mul(patch, 0.6))                      # 补漆块
    # 全车浮尘：低频起伏的薄尘
    film = rng_(noise(2.5, 8.0).outputs["Fac"], 0.35, 0.7, 0.25, 0.6)
    col = mix(col, (0.58, 0.50, 0.38, 1), film)
    # 缝隙/凹角积垢：AO（外侧）
    ao = node("ShaderNodeAmbientOcclusion", samples=8); ao.inputs["Distance"].default_value = 0.18
    cav = rng_(ao.outputs["AO"], 0.95, 0.45)
    col = mix(col, (0.17, 0.13, 0.09, 1), mul(cav, 0.75))
    # 雨/油痕：从棱边往下的竖向条纹
    st = noise(4.0, 4.0, sc=(5, 5, 0.35))
    streak = rng_(st.outputs["Fac"], 0.56, 0.72, 0.0, 0.4)
    col = mix(col, (0.24, 0.19, 0.13, 1), streak)
    # 车身下部溅泥：高度渐变 × 斑点噪声，离地越近越重越暗
    splat = noise(7.0, 10.0, sc=(3, 3, 1.4))
    low = rng_(sep.outputs["Z"], 0.45, 1.25, 1.0, 0.0)
    mud = rng_(mul(low, splat.outputs["Fac"]), 0.12, 0.42)
    col = mix(col, (0.47, 0.38, 0.27, 1), mud)
    caked = rng_(mul(low, splat.outputs["Fac"]), 0.38, 0.52)
    col = mix(col, (0.30, 0.24, 0.17, 1), caked)                                # 结块的深色泥
    # 水平面积尘
    sn = node("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Normal"], sn.inputs[0])
    up = rng_(sn.outputs["Z"], 0.55, 0.95, 0.0, 0.8)
    fn = noise(9.0, 8.0)
    col = mix(col, (0.64, 0.55, 0.42, 1), mul(up, fn.outputs["Fac"]))
    # 凸边磨损：露出更浅的底层
    aoi = node("ShaderNodeAmbientOcclusion", inside=True, samples=8); aoi.inputs["Distance"].default_value = 0.04
    ew = rng_(aoi.outputs["AO"], 0.85, 0.6)
    en = noise(25.0, 6.0)
    wear = rng_(mul(ew, en.outputs["Fac"]), 0.25, 0.4)
    col = mix(col, (0.55, 0.49, 0.40, 1), wear)
    L.new(col, b.inputs["Base Color"])
    rough = node("ShaderNodeMath", operation="ADD", use_clamp=True); rough.inputs[1].default_value = 0.62
    L.new(mul(film, 0.5), rough.inputs[0])
    rough2 = node("ShaderNodeMath", operation="ADD", use_clamp=True); L.new(rough.outputs[0], rough2.inputs[0]); L.new(mul(mud, 0.3), rough2.inputs[1])
    L.new(rough2.outputs[0], b.inputs["Roughness"])
    hb = node("ShaderNodeMath", operation="ADD"); L.new(mul(fn.outputs["Fac"], 0.3), hb.inputs[0]); L.new(mul(caked, 1.0), hb.inputs[1])
    bp = node("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25; bp.inputs["Distance"].default_value = 0.006
    L.new(hb.outputs[0], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m

def tire_mat():
    """轮胎：黑橡胶上糊一层干土，胎面与胎侧下半更多，沟槽里积尘。"""
    m, nt, out = node_mat("tire"); L = nt.links
    b = principled(nt, out, Roughness=0.9)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 6; n.inputs["Detail"].default_value = 10
    L.new(tc.outputs["Object"], n.inputs["Vector"])
    r = nt.nodes.new("ShaderNodeMapRange"); r.inputs["From Min"].default_value = 0.38; r.inputs["From Max"].default_value = 0.62
    r.inputs["To Min"].default_value = 0.25; r.inputs["To Max"].default_value = 0.85
    L.new(n.outputs["Fac"], r.inputs["Value"])
    ao = nt.nodes.new("ShaderNodeAmbientOcclusion"); ao.inputs["Distance"].default_value = 0.05
    cv = nt.nodes.new("ShaderNodeMapRange"); cv.inputs["From Min"].default_value = 1.0; cv.inputs["From Max"].default_value = 0.6
    L.new(ao.outputs["AO"], cv.inputs["Value"])
    f = nt.nodes.new("ShaderNodeMath"); f.operation = "MAXIMUM"; f.use_clamp = True
    L.new(r.outputs[0], f.inputs[0]); L.new(cv.outputs[0], f.inputs[1])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"
    mx.inputs[6].default_value = (0.03, 0.028, 0.026, 1); mx.inputs[7].default_value = (0.40, 0.33, 0.24, 1)
    L.new(f.outputs[0], mx.inputs["Factor"]); L.new(mx.outputs[2], b.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.6; bp.inputs["Distance"].default_value = 0.01
    L.new(n.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m

def glass_mat():
    """车窗：深色光面反射天空，带一层不均匀浮尘（粗糙度噪声）。"""
    m, nt, out = node_mat("glass"); L = nt.links
    b = principled(nt, out, Roughness=0.06, Metallic=0.0)
    b.inputs["Base Color"].default_value = (0.72, 0.7, 0.62, 1)                       # 透明玻璃（略带黄绿），能看到车内乘员
    if "Transmission Weight" in b.inputs: b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["IOR"].default_value = 1.5
    tc = nt.nodes.new("ShaderNodeTexCoord"); n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 4; n.inputs["Detail"].default_value = 6
    L.new(tc.outputs["Object"], n.inputs["Vector"])
    r = nt.nodes.new("ShaderNodeMapRange"); r.inputs["From Min"].default_value = 0.4; r.inputs["From Max"].default_value = 0.7
    r.inputs["To Min"].default_value = 0.04; r.inputs["To Max"].default_value = 0.18
    L.new(n.outputs["Fac"], r.inputs["Value"]); L.new(r.outputs[0], b.inputs["Roughness"])
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

# ---------------- Poly Haven CC0 PBR 贴图（无 UV，按世界坐标三向投影） ----------------
ASSETS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "polyhaven"))
def tex_nodes(nt, name, vec, maps=("diff", "rough", "disp"), box=True):
    out = {}
    for k in maps:
        p = os.path.join(ASSETS, "tex", name, f"{name}_{'nor_gl' if k == 'nor' else k}_2k.jpg")
        if not os.path.exists(p): continue
        n = nt.nodes.new("ShaderNodeTexImage"); n.image = bpy.data.images.load(p, check_existing=True)
        if k != "diff": n.image.colorspace_settings.name = "Non-Color"
        if box: n.projection = "BOX"; n.projection_blend = 0.25
        nt.links.new(vec, n.inputs["Vector"]); out[k] = n
    return out

def pbr_mat(name, tex, tile=2.0, tint=(1, 1, 1), bump=0.6, dirt=True, metal=0.0, rough_add=0.0, damage=False):
    """贴图底色 × 每栋随机明暗/色偏，叠加墙根沾尘与雨痕（沿用程序化 grime 思路）。"""
    m, nt, out = node_mat(name); L = nt.links
    b = principled(nt, out, Metallic=metal)
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1 / tile,) * 3
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    T = tex_nodes(nt, tex, mp.outputs[0])
    info = nt.nodes.new("ShaderNodeObjectInfo")
    hue = nt.nodes.new("ShaderNodeHueSaturation"); L.new(T["diff"].outputs["Color"], hue.inputs["Color"])
    rv = nt.nodes.new("ShaderNodeMapRange"); rv.inputs["To Min"].default_value = 0.78; rv.inputs["To Max"].default_value = 1.08
    L.new(info.outputs["Random"], rv.inputs["Value"]); L.new(rv.outputs[0], hue.inputs["Value"])
    tn = nt.nodes.new("ShaderNodeMix"); tn.data_type = "RGBA"; tn.blend_type = "MULTIPLY"; tn.inputs["Factor"].default_value = 1
    L.new(hue.outputs[0], tn.inputs[6]); tn.inputs[7].default_value = tuple(tint) + (1,)
    col = tn.outputs[2]
    if dirt:
        geo = nt.nodes.new("ShaderNodeNewGeometry"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Position"], sep.inputs[0])
        base = nt.nodes.new("ShaderNodeMapRange"); base.inputs["From Max"].default_value = 1.8; base.inputs["To Min"].default_value = 0.6; base.inputs["To Max"].default_value = 0
        L.new(sep.outputs["Z"], base.inputs["Value"])
        m3 = nt.nodes.new("ShaderNodeMix"); m3.data_type = "RGBA"; m3.inputs[7].default_value = (0.5, 0.39, 0.26, 1)
        L.new(base.outputs[0], m3.inputs["Factor"]); L.new(col, m3.inputs[6]); col = m3.outputs[2]
        mapn = nt.nodes.new("ShaderNodeMapping"); mapn.inputs["Scale"].default_value = (3.0, 3.0, 0.2); L.new(geo.outputs["Position"], mapn.inputs["Vector"])
        n2 = nt.nodes.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 2.0; n2.inputs["Detail"].default_value = 3; L.new(mapn.outputs[0], n2.inputs["Vector"])
        st = nt.nodes.new("ShaderNodeMapRange"); st.inputs["From Min"].default_value = 0.55; st.inputs["From Max"].default_value = 0.78; st.inputs["To Max"].default_value = 0.45
        L.new(n2.outputs["Fac"], st.inputs["Value"])
        m2 = nt.nodes.new("ShaderNodeMix"); m2.data_type = "RGBA"; m2.blend_type = "MULTIPLY"; m2.inputs[7].default_value = (0.55, 0.47, 0.38, 1)
        L.new(st.outputs[0], m2.inputs["Factor"]); L.new(col, m2.inputs[6]); col = m2.outputs[2]
    height = T["disp"].outputs["Color"]
    if damage:
        # 战损：成片剥落露出底层灰浆（damaged_plaster 贴图）+ 成簇弹孔（Voronoi 小坑，只在噪声选中的区域出现）
        D = tex_nodes(nt, "damaged_plaster", mp.outputs[0])
        geo2 = nt.nodes.new("ShaderNodeNewGeometry")
        pn = nt.nodes.new("ShaderNodeTexNoise"); pn.inputs["Scale"].default_value = 0.35; pn.inputs["Detail"].default_value = 6; pn.inputs["Roughness"].default_value = 0.65
        L.new(geo2.outputs["Position"], pn.inputs["Vector"])
        pm = nt.nodes.new("ShaderNodeMapRange"); pm.inputs["From Min"].default_value = 0.6; pm.inputs["From Max"].default_value = 0.63
        L.new(pn.outputs["Fac"], pm.inputs["Value"])
        md = nt.nodes.new("ShaderNodeMix"); md.data_type = "RGBA"; L.new(pm.outputs[0], md.inputs["Factor"])
        L.new(col, md.inputs[6]); L.new(D["diff"].outputs["Color"], md.inputs[7]); col = md.outputs[2]
        cl = nt.nodes.new("ShaderNodeTexNoise"); cl.inputs["Scale"].default_value = 0.8; L.new(geo2.outputs["Position"], cl.inputs["Vector"])
        clm = nt.nodes.new("ShaderNodeMapRange"); clm.inputs["From Min"].default_value = 0.6; clm.inputs["From Max"].default_value = 0.66
        L.new(cl.outputs["Fac"], clm.inputs["Value"])
        vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 6.0; vo.inputs["Randomness"].default_value = 1.0
        L.new(geo2.outputs["Position"], vo.inputs["Vector"])
        hole = nt.nodes.new("ShaderNodeMapRange"); hole.inputs["From Min"].default_value = 0.05; hole.inputs["From Max"].default_value = 0.02
        L.new(vo.outputs["Distance"], hole.inputs["Value"])
        ring = nt.nodes.new("ShaderNodeMapRange"); ring.inputs["From Min"].default_value = 0.11; ring.inputs["From Max"].default_value = 0.05
        L.new(vo.outputs["Distance"], ring.inputs["Value"])
        hm = nt.nodes.new("ShaderNodeMath"); hm.operation = "MULTIPLY"; L.new(hole.outputs[0], hm.inputs[0]); L.new(clm.outputs[0], hm.inputs[1])
        rm = nt.nodes.new("ShaderNodeMath"); rm.operation = "MULTIPLY"; L.new(ring.outputs[0], rm.inputs[0]); L.new(clm.outputs[0], rm.inputs[1])
        mr = nt.nodes.new("ShaderNodeMix"); mr.data_type = "RGBA"; mr.inputs[7].default_value = (0.62, 0.58, 0.52, 1)   # 弹孔周围崩掉的浅色灰浆
        L.new(rm.outputs[0], mr.inputs["Factor"]); L.new(col, mr.inputs[6]); col = mr.outputs[2]
        mh = nt.nodes.new("ShaderNodeMix"); mh.data_type = "RGBA"; mh.inputs[7].default_value = (0.06, 0.05, 0.045, 1)
        L.new(hm.outputs[0], mh.inputs["Factor"]); L.new(col, mh.inputs[6]); col = mh.outputs[2]
        hd = nt.nodes.new("ShaderNodeMix"); hd.data_type = "FLOAT"; L.new(pm.outputs[0], hd.inputs["Factor"])
        L.new(height, hd.inputs[2]); dsub = nt.nodes.new("ShaderNodeMath"); dsub.operation = "SUBTRACT"
        L.new(D["disp"].outputs["Color"], dsub.inputs[0]); dsub.inputs[1].default_value = 0.6; L.new(dsub.outputs[0], hd.inputs[3])
        hh = nt.nodes.new("ShaderNodeMath"); hh.operation = "MULTIPLY_ADD"; L.new(hm.outputs[0], hh.inputs[0]); hh.inputs[1].default_value = -1.5
        L.new(hd.outputs[0], hh.inputs[2]); height = hh.outputs[0]
    L.new(col, b.inputs["Base Color"])
    ra = nt.nodes.new("ShaderNodeMath"); ra.operation = "ADD"; ra.inputs[1].default_value = rough_add; ra.use_clamp = True
    L.new(T["rough"].outputs["Color"], ra.inputs[0]); L.new(ra.outputs[0], b.inputs["Roughness"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.03
    L.new(height, bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m

def road_pbr():
    """土路为主、残破沥青斑块；路缘积沙、两道车辙压实发暗。"""
    m, nt, out = node_mat("road"); L = nt.links
    b = principled(nt, out)
    tc = nt.nodes.new("ShaderNodeTexCoord"); geo = nt.nodes.new("ShaderNodeNewGeometry")
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1 / 2.5,) * 3; L.new(tc.outputs["Object"], mp.inputs["Vector"])
    A = tex_nodes(nt, "asphalt_03", mp.outputs[0], box=False); G = tex_nodes(nt, "sandy_gravel", mp.outputs[0], box=False)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Position"], sep.inputs[0])
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 0.12; n.inputs["Detail"].default_value = 8; L.new(geo.outputs["Position"], n.inputs["Vector"])
    patch = nt.nodes.new("ShaderNodeMapRange"); patch.inputs["From Min"].default_value = 0.5; patch.inputs["From Max"].default_value = 0.56
    L.new(n.outputs["Fac"], patch.inputs["Value"])
    ax = nt.nodes.new("ShaderNodeMath"); ax.operation = "ABSOLUTE"; L.new(sep.outputs["X"], ax.inputs[0])
    edge = nt.nodes.new("ShaderNodeMapRange"); edge.inputs["From Min"].default_value = 6.5; edge.inputs["From Max"].default_value = 4.0; L.new(ax.outputs[0], edge.inputs["Value"])
    f = nt.nodes.new("ShaderNodeMath"); f.operation = "MULTIPLY"; L.new(patch.outputs[0], f.inputs[0]); L.new(edge.outputs[0], f.inputs[1])
    def mixc(a, c, fac, dtype="RGBA"):
        x = nt.nodes.new("ShaderNodeMix"); x.data_type = dtype
        L.new(fac, x.inputs["Factor"]); L.new(a, x.inputs[6 if dtype == "RGBA" else 2]); L.new(c, x.inputs[7 if dtype == "RGBA" else 3])
        return x.outputs[2 if dtype == "RGBA" else 0]
    col = mixc(G["diff"].outputs["Color"], A["diff"].outputs["Color"], f.outputs[0])
    wt = nt.nodes.new("ShaderNodeMix"); wt.data_type = "RGBA"; wt.blend_type = "MULTIPLY"; wt.inputs["Factor"].default_value = 1; wt.inputs[7].default_value = (1.08, 0.95, 0.78, 1)
    L.new(col, wt.inputs[6]); col = wt.outputs[2]
    rut = nt.nodes.new("ShaderNodeMath"); rut.operation = "PINGPONG"; rut.inputs[1].default_value = 1.1
    off = nt.nodes.new("ShaderNodeMath"); off.operation = "ADD"; off.inputs[1].default_value = 2.75
    L.new(sep.outputs["X"], off.inputs[0]); L.new(off.outputs[0], rut.inputs[0])
    rutm = nt.nodes.new("ShaderNodeMapRange"); rutm.inputs["From Max"].default_value = 0.4; rutm.inputs["To Min"].default_value = 0.3; rutm.inputs["To Max"].default_value = 0.0
    L.new(rut.outputs[0], rutm.inputs["Value"])
    dk = nt.nodes.new("ShaderNodeMix"); dk.data_type = "RGBA"; dk.blend_type = "MULTIPLY"; dk.inputs[7].default_value = (0.62, 0.58, 0.54, 1)
    L.new(rutm.outputs[0], dk.inputs["Factor"]); L.new(col, dk.inputs[6]); L.new(dk.outputs[2], b.inputs["Base Color"])
    rr = nt.nodes.new("ShaderNodeMapRange"); rr.inputs["To Min"].default_value = 0.75; rr.inputs["To Max"].default_value = 1.0  # 干燥尘土路，不出现湿反光
    L.new(mixc(G["rough"].outputs["Color"], A["rough"].outputs["Color"], f.outputs[0]), rr.inputs["Value"]); L.new(rr.outputs[0], b.inputs["Roughness"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.8; bp.inputs["Distance"].default_value = 0.04
    L.new(mixc(G["disp"].outputs["Color"], A["disp"].outputs["Color"], f.outputs[0]), bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m

WALL_TEX = [("painted_plaster_wall", (1.0, 0.97, 0.9)), ("worn_plaster_wall", (1.0, 0.95, 0.86)), ("yellow_plaster", (1.0, 0.95, 0.85)),
            ("worn_plaster_wall", (0.92, 0.97, 0.95)), ("blue_plaster_weathered", (0.95, 0.95, 0.88)), ("painted_plaster_wall", (1.0, 0.92, 0.8)), ("red_plaster_weathered", (0.95, 0.9, 0.85))]
WALLS = [f"wall_{i}" for i in range(len(WALL_TEX))]

MAT = {
    "plaster": plaster_mat(),
    **{k: pbr_mat(k, t, tile=2.2, tint=c, damage=True) for k, (t, c) in zip(WALLS, WALL_TEX)},
    "dark": simple_mat("opening", (0.025, 0.022, 0.02), 0.9, noise=0.1),
    "shutter": pbr_mat("shutter", "rusty_metal_shutter", tile=1.6, bump=0.8, dirt=False, metal=0.4),
    "tin": pbr_mat("tin", "rusty_corrugated_iron", tile=1.8, bump=1.0, dirt=False, metal=0.5),
    "wood": simple_mat("wood", (0.25, 0.18, 0.12), 0.85, noise=0.4, bump=0.3, scale=20),
    "rubber": simple_mat("rubber", (0.025, 0.024, 0.023), 0.88, noise=0.15, bump=0.6, scale=30),
    "steel": simple_mat("steel", (0.06, 0.06, 0.06), 0.45, 0.8, noise=0.3),
    "glass": glass_mat(),
    "lens": simple_mat("lens", (0.5, 0.5, 0.45), 0.05, noise=0.05, bump=0.0),
    "amber": simple_mat("amber", (0.5, 0.2, 0.02), 0.1, noise=0.05, bump=0.0),
    "gasket": simple_mat("gasket", (0.02, 0.02, 0.02), 0.7, noise=0.1, bump=0.0),
    "olive": simple_mat("olive", (0.17, 0.17, 0.12), 0.9, noise=0.4, bump=0.3, scale=10),
    "canvas": simple_mat("canvas", (0.36, 0.3, 0.2), 0.95, noise=0.5, bump=0.5, scale=25),
    "grime": simple_mat("grime", (0.07, 0.06, 0.045), 0.75, noise=0.5, bump=0.3, scale=20),
    "rust": simple_mat("rust", (0.16, 0.08, 0.04), 0.9, noise=0.7, bump=0.5, scale=8),
    "paint_r": simple_mat("sign_red", (0.42, 0.13, 0.08), 0.8, noise=0.5),
    "paint_b": simple_mat("sign_blue", (0.1, 0.22, 0.32), 0.8, noise=0.5),
    "paint_y": simple_mat("sign_yellow", (0.55, 0.42, 0.12), 0.8, noise=0.5),
    "ink_w": simple_mat("ink_w", (0.62, 0.6, 0.55), 0.85, noise=0.5, bump=0.0, scale=40),
    "ink_k": simple_mat("ink_k", (0.03, 0.03, 0.035), 0.85, noise=0.4, bump=0.0, scale=40),
    "cloth": simple_mat("cloth", (0.45, 0.3, 0.22), 0.95, noise=0.5, bump=0.2, scale=30),
    "tan": tan_paint(),
    "tire": tire_mat(),
    "skin": simple_mat("skin_g", (0.13, 0.085, 0.06), 0.6, noise=0.2, bump=0.1, scale=30),
    "road": road_pbr(),
    "sand": pbr_mat("sand", "dry_ground_01", tile=3.0, tint=(1.05, 0.92, 0.74), bump=0.6, dirt=False),
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
    def hull(self, key, bottom, top):
        """任意 8 点棱台（底 4 点 + 顶 4 点，同序），用于收腰车厢、斜背等非方盒形体。"""
        vs = [self.bm.verts.new(p) for p in list(bottom) + list(top)]
        i = self.mi(key)
        fs = [self.bm.faces.new([vs[j] for j in idx]) for idx in [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]]
        for f in fs: f.material_index = i
        bmesh.ops.recalc_face_normals(self.bm, faces=fs)
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

