# 本机 ComfyUI 出图 → 3D：FLUX dev 生成参考图，TRELLIS.2 生成带 PBR 贴图的 GLB。
# 只往队列追加任务，不碰 ComfyUI 里打开的工作流；每步结束调用 /free 释放显存（大模型必须串行跑）。
# 用法：（trellis 第 6 个参数为精细化体素分辨率，默认 1024；第 7 个为 hard/organic）
#   python -I comfy3d.py flux <输出目录> <名字> <种子> "<提示词>" [宽 高 步数]
#   python -I comfy3d.py trellis <输出目录> <名字> <参考图.png> [种子]
import json, time, urllib.request, urllib.parse, uuid, os, sys, subprocess

HOST = "http://127.0.0.1:8188"

def _req(path, data=None, raw=None, headers=None):
    body = raw if raw is not None else (json.dumps(data).encode() if data is not None else None)
    h = headers or ({"Content-Type": "application/json"} if data is not None else {})
    with urllib.request.urlopen(urllib.request.Request(HOST + path, data=body, headers=h), timeout=120) as r:
        return r.read()

def wired_gb():
    out = subprocess.run(["vm_stat"], capture_output=True, text=True).stdout
    pg = 16384; d = {l.split(":")[0]: int(l.split(":")[1].strip(" .")) for l in out.splitlines()[1:] if ":" in l}
    return d.get("Pages wired down", 0) * pg / 1e9, d.get("Pages free", 0) * pg / 1e9

def free():  # 队列里有别的任务（可能是用户的）就不卸载
    q = json.loads(_req("/queue"))
    if q["queue_running"] or q["queue_pending"]: print("队列非空，跳过 /free", flush=True); return
    _req("/free", {"unload_models": True, "free_memory": True})

def upload(path):
    bnd = uuid.uuid4().hex; name = os.path.basename(path)
    body = (f"--{bnd}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{name}\"\r\nContent-Type: image/png\r\n\r\n").encode() \
        + open(path, "rb").read() + f"\r\n--{bnd}\r\nContent-Disposition: form-data; name=\"subfolder\"\r\n\r\nmovie_game\r\n--{bnd}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n--{bnd}--\r\n".encode()
    r = json.loads(_req("/upload/image", raw=body, headers={"Content-Type": f"multipart/form-data; boundary={bnd}"}))
    return f"{r['subfolder']}/{r['name']}" if r.get("subfolder") else r["name"]

def run(graph, out_dir, name, timeout=7200):
    pid = json.loads(_req("/prompt", {"prompt": graph, "client_id": str(uuid.uuid4())}))["prompt_id"]
    t0 = time.time(); peak = 0
    while True:
        h = json.loads(_req(f"/history/{pid}"))
        peak = max(peak, wired_gb()[0])
        if pid in h:
            st = h[pid].get("status", {})
            if st.get("status_str") == "error":
                raise RuntimeError(json.dumps(st.get("messages", [])[-2:], ensure_ascii=False)[:3000])
            if st.get("completed"): break
        if time.time() - t0 > timeout: raise TimeoutError(pid)
        time.sleep(3)
    os.makedirs(out_dir, exist_ok=True); saved = []
    for nid, node_out in h[pid]["outputs"].items():
        for key, items in node_out.items():
            if not isinstance(items, list): continue
            for a in items:
                if not isinstance(a, dict) or "filename" not in a: continue
                if a.get("type") == "temp" and key == "images": continue  # 预览图不取
                q = urllib.parse.urlencode({"filename": a["filename"], "subfolder": a.get("subfolder", ""), "type": a.get("type", "output")})
                ext = os.path.splitext(a["filename"])[1]
                p = os.path.join(out_dir, f"{name}_{nid}_{len(saved)}{ext}")
                open(p, "wb").write(_req(f"/view?{q}")); saved.append(p)
    print(f"[comfy] {name}: {time.time() - t0:.0f}s, 峰值锁定内存 {peak:.1f} GB -> {saved}", flush=True)
    return saved

def flux(prompt, seed, w=1024, h=1024, steps=28, guidance=3.5):
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "flux1-dev.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "DualCLIPLoader", "inputs": {"clip_name1": "t5xxl_fp16.safetensors", "clip_name2": "clip_l.safetensors", "type": "flux"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["2", 0]}},
        "5": {"class_type": "FluxGuidance", "inputs": {"conditioning": ["4", 0], "guidance": guidance}},
        "6": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["4", 0]}},
        "7": {"class_type": "EmptySD3LatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "8": {"class_type": "KSampler", "inputs": {"seed": seed, "steps": steps, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0,
                                                   "model": ["1", 0], "positive": ["5", 0], "negative": ["6", 0], "latent_image": ["7", 0]}},
        "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["3", 0]}},
        "10": {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": "movie_game/flux"}},
    }

def trellis(image_name, seed=42, upsample=1536, remesh=768, faces=400000, tex=4096, hard_surface=True):
    # 按 ComfyUI 官方模板 3d_pixal3d_trellis2_image_to_model（TRELLIS.2 分支）改写为 API 格式
    sk = lambda s, steps, cfg, sch, model, pos, neg, lat: {"class_type": "KSampler", "inputs": {
        "seed": s, "steps": steps, "cfg": cfg, "sampler_name": "euler", "scheduler": sch, "denoise": 1.0,
        "model": model, "positive": pos, "negative": neg, "latent_image": lat}}
    return {
        "40": {"class_type": "UNETLoader", "inputs": {"unet_name": "trellis_2_int8_convrot.safetensors", "weight_dtype": "default"}},
        "117": {"class_type": "VAELoader", "inputs": {"vae_name": "trellis_2_shape_vae_bf16.safetensors"}},
        "118": {"class_type": "VAELoader", "inputs": {"vae_name": "trellis_2_texture_vae_bf16.safetensors"}},
        "15": {"class_type": "CLIPVisionLoader", "inputs": {"clip_name": "dino_v3_L_naf_fp32.safetensors"}},
        "193": {"class_type": "LoadBackgroundRemovalModel", "inputs": {"bg_removal_name": "birefnet.safetensors"}},
        "122": {"class_type": "LoadImage", "inputs": {"image": image_name}},
        "192": {"class_type": "RemoveBackground", "inputs": {"bg_removal_model": ["193", 0], "image": ["122", 0]}},
        "312": {"class_type": "ImageCropToMask", "inputs": {"images": ["122", 0], "masks": ["192", 0], "width": 1024, "height": 1024,
                                                            "pad_factor": 1.1, "grow_mask": 0, "background": "#000000"}},
        "302": {"class_type": "SaveImage", "inputs": {"images": ["312", 0], "filename_prefix": "movie_game/trellis_input"}},
        "199": {"class_type": "CFGOverride", "inputs": {"model": ["40", 0], "cfg": 1, "start_percent": 0.667, "end_percent": 1}},
        "279": {"class_type": "CFGOverride", "inputs": {"model": ["40", 0], "cfg": 1, "start_percent": 0.769, "end_percent": 1}},
        "125": {"class_type": "RescaleCFG", "inputs": {"model": ["199", 0], "multiplier": 0.7}},
        "126": {"class_type": "RescaleCFG", "inputs": {"model": ["279", 0], "multiplier": 0.5}},
        "108": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["125", 0], "shift": 5}},
        "299": {"class_type": "Trellis2Conditioning", "inputs": {"clip_vision_model": ["15", 0], "image": ["312", 0]}},
        "87": {"class_type": "EmptyTrellis2LatentStructure", "inputs": {"batch_size": 1}},
        "3": sk(seed + 14, 12, 7.5, "normal", ["108", 0], ["299", 0], ["299", 1], ["87", 0]),
        "119": {"class_type": "VaeDecodeStructureTrellis2", "inputs": {"samples": ["3", 0], "vae": ["117", 0], "resolution": "32"}},
        "91": {"class_type": "Trellis2ShapeStage", "inputs": {"positive": ["299", 0], "negative": ["299", 1], "voxel": ["119", 0]}},
        "18": sk(seed, 20, 7.5, "normal", ["126", 0], ["91", 0], ["91", 1], ["91", 2]),
        "94": {"class_type": "Trellis2UpsampleStage", "inputs": {"positive": ["91", 0], "negative": ["91", 1], "shape_latent": ["18", 0],
                                                                 "vae": ["117", 0], "target_resolution": upsample}},
        "23": sk(seed, 12, 7.5, "simple", ["126", 0], ["94", 0], ["94", 1], ["94", 2]),
        "92": {"class_type": "VaeDecodeShapeTrellis", "inputs": {"samples": ["23", 0], "vae": ["117", 0]}},
        "98": {"class_type": "Trellis2TextureStage", "inputs": {"positive": ["94", 0], "negative": ["94", 1], "shape_latent": ["23", 0]}},
        "12": sk(seed + 1, 12, 1, "normal", ["40", 0], ["98", 0], ["98", 1], ["98", 2]),
        "93": {"class_type": "VaeDecodeTextureTrellis", "inputs": {"samples": ["12", 0], "vae": ["118", 0], "shape_subdivides": ["92", 1]}},
        "241": {"class_type": "RemeshMesh", "inputs": {"mesh": ["92", 0], "resolution": remesh, "sign_mode": "solid", "sign_mode.fill": 20.0,
                                                       "sign_mode.qef": hard_surface, "band": 1.0, "project_back": 0.0, "fix_poles": False,
                                                       "smooth_iters": 0 if hard_surface else 20, "drop_small_components": 0.01, "precluster_max_verts": 20000000}},
        "186": {"class_type": "DecimateMesh", "inputs": {"mesh": ["241", 0], "target_face_count": faces, "placement_mode": "midpoint"}},
        "238": {"class_type": "MeshSmoothNormals", "inputs": {"mesh": ["186", 0], "crease_angle": 40 if hard_surface else 180}},
        "196": {"class_type": "UnwrapMesh", "inputs": {"mesh": ["238", 0], "segmenter": "pec", "resolution": tex, "padding": 1, "weld_distance": 0.0002}},
        "147": {"class_type": "BakeTextureFromVoxel", "inputs": {"mesh": ["196", 0], "voxel_colors": ["93", 0], "reference_mesh": ["92", 0], "texture_size": min(tex, 2048)}},  # MPS 上 4096 烘焙索引越界
        "224": {"class_type": "BakeNormalMapFromMesh", "inputs": {"low_poly": ["196", 0], "high_poly": ["241", 0], "resolution": tex, "cage_distance": 0.05, "ignore_backfaces": True}},
        "233": {"class_type": "BakeAmbientOcclusion", "inputs": {"low_poly": ["196", 0], "high_poly": ["241", 0], "resolution": 2048, "samples": 64,
                                                                 "max_distance": 0.71, "strength": 1, "bias": 0.01}},
        "210": {"class_type": "ApplyTextureToMesh", "inputs": {"mesh": ["196", 0], "base_color": ["147", 0], "metallic": ["147", 1], "roughness": ["147", 2],
                                                               "occlusion": ["233", 0], "normal_map": ["224", 0]}},
        "260": {"class_type": "MeshSmoothNormals", "inputs": {"mesh": ["210", 0], "crease_angle": 40 if hard_surface else 180}},
        "300": {"class_type": "SaveGLB", "inputs": {"mesh": ["260", 0], "filename_prefix": "3d/movie_game/trellis"}},
    }

if __name__ == "__main__":
    mode, out_dir, name = sys.argv[1:4]
    if not os.environ.get("KEEP_CACHE"): free()  # /free 会清空执行缓存，重试时设 KEEP_CACHE=1 复用已算好的前几步
    print("开始前 锁定/空闲 GB: %.1f / %.1f" % wired_gb(), flush=True)
    try:
        if mode == "flux":
            seed, prompt = int(sys.argv[4]), sys.argv[5]
            w, h, steps = (map(int, sys.argv[6:9]) if len(sys.argv) > 8 else (1024, 1024, 28))
            run(flux(prompt, seed, w, h, steps), out_dir, name)
        else:
            img = upload(sys.argv[4]); seed = int(sys.argv[5]) if len(sys.argv) > 5 else 42
            up = int(sys.argv[6]) if len(sys.argv) > 6 else 1024  # MPS：1536 会产出 >2^24 个体素，烘焙时布尔索引越界
            hard = (sys.argv[7] if len(sys.argv) > 7 else "hard") == "hard"  # organic：人物/软表面，平滑法线、不开 QEF
            run(trellis(img, seed, upsample=up, hard_surface=hard), out_dir, name)
    except Exception:
        print("失败：保留 ComfyUI 执行缓存，修正后用 KEEP_CACHE=1 重试", flush=True); raise
    else:
        free(); print("结束后 锁定/空闲 GB: %.1f / %.1f" % wired_gb(), flush=True)
