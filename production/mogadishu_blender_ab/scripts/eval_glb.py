# 评估生成的 GLB：导入、按真实车长缩放落地、在 goegap HDRI 下多角度渲染，打印面数/贴图信息。
# 用法：blender -b --factory-startup --python scripts/eval_glb.py -- <in.glb> <输出前缀> [真实长度m=4.57] [samples=64] [height]（人物按身高）
import bpy, sys, os, math, mathutils

argv = sys.argv[sys.argv.index("--") + 1:]
glb, out = argv[0], argv[1]
length = float(argv[2]) if len(argv) > 2 else 4.57
spp = int(argv[3]) if len(argv) > 3 else 64
BY_H = len(argv) > 4 and argv[4] == "height"  # 人物：按身高缩放，镜头拉近
ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets", "polyhaven")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
faces = sum(len(o.data.polygons) for o in objs)
imgs = [(i.name, tuple(i.size)) for i in bpy.data.images]
print("EVAL meshes", len(objs), "faces", faces, "images", imgs)

# 归一化：最长水平边 = 车长，底部贴地，中心在原点
root = bpy.data.objects.new("root", None); bpy.context.scene.collection.objects.link(root)
for o in objs:
    if o.parent is None: o.parent = root
bpy.context.view_layer.update()
pts = [o.matrix_world @ mathutils.Vector(c) for o in objs for c in o.bound_box]
mn = mathutils.Vector([min(p[i] for p in pts) for i in range(3)]); mx = mathutils.Vector([max(p[i] for p in pts) for i in range(3)])
size = mx - mn; s = length / (size.z if BY_H else max(size.x, size.y))
root.scale = (s, s, s); root.location = (-(mn.x + mx.x) / 2 * s, -(mn.y + mx.y) / 2 * s, -mn.z * s)
print("EVAL raw size", tuple(round(v, 3) for v in size), "-> m", tuple(round(v * s, 2) for v in size))

sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "GPU"; sc.cycles.samples = spp; sc.cycles.use_denoising = True
prefs = bpy.context.preferences.addons["cycles"].preferences; prefs.compute_device_type = "METAL"; prefs.get_devices()
for d in prefs.devices: d.use = True
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
env = w.node_tree.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(os.path.join(ASSETS, "hdri", "goegap_4k.hdr"))
w.node_tree.links.new(env.outputs[0], w.node_tree.nodes["Background"].inputs[0])
bpy.ops.mesh.primitive_plane_add(size=600); g = bpy.context.object
m = bpy.data.materials.new("ground"); m.use_nodes = True
m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.42, 0.34, 0.24, 1); g.data.materials.append(m)
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.data.energy = 4; sun.data.angle = math.radians(1.5); sun.rotation_euler = (math.radians(58), 0, math.radians(-35))

cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 40
for i, (az, el, d) in enumerate([(35, 12, 8.5), (125, 10, 8.5), (215, 14, 8.5), (300, 4, 6.0)]):
    if BY_H: d *= 0.45
    else: d *= max(1.0, length / 4.57)  # 大物体（直升机、楼）按尺寸拉远
    a, e = math.radians(az), math.radians(el)
    zc = 0.9 * (1.0 if BY_H else max(1.0, length / 4.57)); cam.location = (d * math.cos(a) * math.cos(e), d * math.sin(a) * math.cos(e), zc + d * math.sin(e))
    cam.rotation_euler = (mathutils.Vector((0, 0, zc)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = f"{out}_{i}.png"; bpy.ops.render.render(write_still=True)
print("EVAL done", out)
