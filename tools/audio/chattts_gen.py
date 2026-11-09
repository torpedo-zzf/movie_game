# ChatTTS 生成旁白/台词。固定说话人种子保证全片同一音色；跳过文本润色，避免模型自行加入"嗯、那个"等口语词。
# 用法：python chattts_gen.py <输出目录> <说话人种子> <name=文本> [name=文本 ...]
import sys, os, torch, numpy as np, soundfile as sf, ChatTTS

out_dir, seed = sys.argv[1], int(sys.argv[2])
items = [a.split("=", 1) for a in sys.argv[3:]]
os.makedirs(out_dir, exist_ok=True)
chat = ChatTTS.Chat()
chat.load(compile=False, device=torch.device("cpu"))
torch.manual_seed(seed)
spk = chat.sample_random_speaker()
open(os.path.join(out_dir, "speaker.txt"), "w").write(spk)  # 存下说话人向量，换环境也能复现同一音色
params = ChatTTS.Chat.InferCodeParams(spk_emb=spk, temperature=0.12, top_P=0.7, top_K=20, manual_seed=seed)
wavs = chat.infer([t for _, t in items], skip_refine_text=True, params_infer_code=params)
for (name, text), w in zip(items, wavs):
    w = np.asarray(w).reshape(-1).astype(np.float32)
    p = os.path.join(out_dir, f"{name}.wav"); sf.write(p, w, 24000)
    print(f"{name}\t{len(w) / 24000:.2f}s\t{text}", flush=True)
