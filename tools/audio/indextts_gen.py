# IndexTTS2 旁白生成（需在 tools/audio/index-tts 目录下用 uv run 运行）。
# 用法：uv run python ../indextts_gen.py <输出目录> audition      → 多音色 × 多情绪，试听同一句
#       uv run python ../indextts_gen.py <输出目录> full <音色wav> <情绪名>  → 全部正式旁白（主干 6 段 + 分支 2 段 + 结尾 3 段）
import sys, os, time
from indextts.infer_v2 import IndexTTS2

LINES = {
    "scene-01": "一九九三年十月三日，摩加迪沙当地时间下午三点半，行动开始。",
    "scene-02": "行动目标是抓捕两名重要助手。美国陆军记录，有二十四人被拘押。",
    "scene-03": "下午四点二十分，一架黑鹰被火箭弹击中，失控坠落在目标区外约三个街区。抓捕行动，随即转为救援。",
    "scene-04": "约二十分钟后，第二架黑鹰也被击落。",
    # 选择 1 的两条分支（BRANCHING.md）
    "scene-04a": "搜救小组从直升机索降到第一处残骸旁，地面部队随后赶到，在这里坚守了一整夜。",
    "scene-04b": "第二处坠机点在南面不到一英里，地面部队一时无法抵达。一名飞行员被俘，十月十四日获释。",
    "scene-05": "十月四日凌晨一点五十五分，救援车队抵达第一处坠机点。",
    "scene-06": "美军死亡十八人。联合国记录七十五人受伤；《华盛顿邮报》记录八十四人。",
    # 选择 2 的三个结尾
    "scene-e1": "天亮后，车队载着伤员和阵亡者，撤回巴基斯坦体育场。",
    "scene-e2": "索马里一方的伤亡，至今没有统一确认的数字；不同来源的估计相差很大。",
    "scene-e3": "战斗后数日，美国宣布在一九九四年三月前撤军。次年三月，美军离开索马里。",
}
# 情绪：文字描述交给 IndexTTS2 内置的情绪模型解析；alpha 是强度
EMOS = {
    "restrained": ("低沉克制的纪录片叙述，平静中带着沉重", 0.6),
    "grave": ("沉痛、压抑，语速放慢，像在讲述一场悲剧", 0.8),
    "tense": ("紧张、急促，压低声音，局势正在失控", 0.7),
}

out, mode = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
tts = IndexTTS2(cfg_path="checkpoints/config.yaml", model_dir="checkpoints",
                use_fp16=True, use_cuda_kernel=False, use_deepspeed=False)

def say(spk, key, emo, path):
    desc, alpha = EMOS[emo]
    t = time.time()
    tts.infer(spk_audio_prompt=spk, text=LINES[key], output_path=path,
              use_emo_text=True, emo_text=desc, emo_alpha=alpha, verbose=False)
    print(f"[tts] {path} {time.time() - t:.1f}s", flush=True)

if mode == "audition":
    for spk in sys.argv[3:]:
        name = os.path.splitext(os.path.basename(spk))[0]
        for emo in EMOS:
            say(spk, "scene-03", emo, f"{out}/{name}_{emo}.wav")
else:
    spk, emo = sys.argv[3], sys.argv[4]
    for key in LINES:
        say(spk, key, emo, f"{out}/{key}.wav")
