# 向本机 ComfyUI（127.0.0.1:8188）提交 API 格式工作流，等待完成并把输出音频取回到本地目录。
# 只新增队列任务，不改动 ComfyUI 里打开的工作流标签页。
# 用法（作为模块）：from comfy_run import run; run(graph_dict, out_dir, name)
import json, time, urllib.request, urllib.parse, uuid, os

HOST = "http://127.0.0.1:8188"

def _req(path, data=None):
    req = urllib.request.Request(HOST + path, data=json.dumps(data).encode() if data is not None else None,
                                 headers={"Content-Type": "application/json"} if data is not None else {})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

def run(graph, out_dir, name, timeout=3600):
    pid = json.loads(_req("/prompt", {"prompt": graph, "client_id": str(uuid.uuid4())}))["prompt_id"]
    t0 = time.time()
    while True:
        h = json.loads(_req(f"/history/{pid}"))
        if pid in h:
            st = h[pid].get("status", {})
            if st.get("status_str") == "error":
                raise RuntimeError(json.dumps(st.get("messages", [])[-2:], ensure_ascii=False)[:2000])
            if st.get("completed"):
                break
        if time.time() - t0 > timeout: raise TimeoutError(pid)
        time.sleep(3)
    os.makedirs(out_dir, exist_ok=True); saved = []
    for node_out in h[pid]["outputs"].values():
        for a in node_out.get("audio", []):
            q = urllib.parse.urlencode({"filename": a["filename"], "subfolder": a.get("subfolder", ""), "type": a.get("type", "output")})
            ext = os.path.splitext(a["filename"])[1]
            p = os.path.join(out_dir, f"{name}_{len(saved)}{ext}" if saved else f"{name}{ext}")
            with open(p, "wb") as f: f.write(_req(f"/view?{q}"))
            saved.append(p)
    print(f"[comfy] {name}: {time.time() - t0:.0f}s -> {saved}", flush=True)
    return saved

def stable_audio(prompt, seconds, seed, negative="music, melody, singing, speech, low quality, distorted, clipping", steps=100, cfg=7.0):
    return {
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "stable-audio-open-1.0.safetensors"}},
        "10": {"class_type": "CLIPLoader", "inputs": {"clip_name": "t5-base.safetensors", "type": "stable_audio", "device": "default"}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["10", 0]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["10", 0]}},
        "11": {"class_type": "EmptyLatentAudio", "inputs": {"seconds": seconds, "batch_size": 1}},
        "3": {"class_type": "KSampler", "inputs": {"seed": seed, "steps": steps, "cfg": cfg, "sampler_name": "dpmpp_3m_sde_gpu", "scheduler": "exponential",
                                                   "denoise": 1.0, "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["11", 0]}},
        "12": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "20": {"class_type": "SaveAudioAdvanced", "inputs": {"audio": ["12", 0], "filename_prefix": "audio/movie_game_sfx", "format": "flac"}},
    }

def minimax_music3(caption, lyrics, seconds, seed, steps=30, cfg=1.7):
    return {
        "6": {"class_type": "UNETLoader", "inputs": {"unet_name": "minimax_music3_dit_fp16.safetensors", "weight_dtype": "default"}},
        "3": {"class_type": "CLIPLoader", "inputs": {"clip_name": "minimax_music3_text_encoder_pruned_int8_convrot.safetensors", "type": "minimax", "device": "default"}},
        "7": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_music3_dav.safetensors"}},
        "13": {"class_type": "MiniMaxMusic3TextEncode", "inputs": {"clip": ["3", 0], "caption": caption, "lyrics": lyrics, "seed": seed,
                                                                   "max_duration": seconds, "cfg_scale": cfg, "top_k": 50}},
        "10": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["13", 0]}},
        "15": {"class_type": "EmptyMiniMaxMusic3LatentAudio", "inputs": {"seconds": ["13", 1], "batch_size": 1}},
        "9": {"class_type": "KSampler", "inputs": {"seed": seed, "steps": steps, "cfg": cfg, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0,
                                                   "model": ["6", 0], "positive": ["13", 0], "negative": ["10", 0], "latent_image": ["15", 0]}},
        "12": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["9", 0], "vae": ["7", 0]}},
        "35": {"class_type": "SaveAudioAdvanced", "inputs": {"audio": ["12", 0], "filename_prefix": "audio/movie_game_bgm", "format": "flac"}},
    }
