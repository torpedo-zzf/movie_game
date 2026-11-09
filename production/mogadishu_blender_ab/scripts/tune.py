# 调参渲染：Blender -b convoy_shot.blend --python gpu_on.py --python tune.py -- haze sky sun look pct samples
import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]
haze, skyS, sunE, look, pct, spp = float(a[0]), float(a[1]), float(a[2]), a[3], int(a[4]), int(a[5])
s = bpy.context.scene
s.render.resolution_percentage = pct; s.cycles.samples = spp
hv = bpy.data.materials["haze"].node_tree.nodes["Principled Volume"]
hv.inputs["Density"].default_value = haze; hv.inputs["Color"].default_value = (0.95, 0.72, 0.45, 1)
bpy.data.worlds["world"].node_tree.nodes["Background"].inputs["Strength"].default_value = skyS
bpy.data.lights["sun"].energy = sunE
try: s.view_settings.look = "AgX - " + look
except Exception as e: print("LOOKERR", e, [i.identifier for i in s.view_settings.bl_rna.properties["look"].enum_items])
