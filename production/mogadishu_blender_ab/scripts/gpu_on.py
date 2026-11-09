# 在命令行渲染保存的 .blend 前打开 Metal GPU
import bpy
p = bpy.context.preferences.addons["cycles"].preferences
p.compute_device_type = "METAL"; p.get_devices()
for d in p.devices: d.use = d.type == "METAL"
bpy.context.scene.cycles.device = "GPU"
