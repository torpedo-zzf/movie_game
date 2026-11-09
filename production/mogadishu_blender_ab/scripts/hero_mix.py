# 基准镜头最终混音：Stable Audio Open（ComfyUI）音效分层 + ChatTTS 无线电台词 + MiniMax Music 3（ComfyUI）配乐对应段落
# + 与画面颠簸逐帧同步的悬挂撞击（程序化，时刻来自 convoy_hero.py 的 BUMPS）。
# 用法：python hero_mix.py <sao目录> <radio.wav|-> <bgm.flac|-> <输出.wav>
import numpy as np, soundfile as sf, sys, os

SR, DUR, T0 = 48000, 3.0, 13.5
N = int(SR * DUR); t = np.arange(N) / SR
rng = np.random.default_rng(1003)
BUMPS = [(14.05, 1.0), (14.9, 0.6), (15.62, 1.2), (16.2, 0.7)]
sao_dir, radio_p, bgm_p, out_p = sys.argv[1:5]

def resample(x, sr):
    if sr == SR: return x
    n = int(round(len(x) * SR / sr)); X = np.fft.rfft(x, axis=0)
    Y = np.zeros((n // 2 + 1,) + X.shape[1:], complex); k = min(len(X), len(Y)); Y[:k] = X[:k]
    return np.fft.irfft(Y, n, axis=0) * (n / len(x))
def load(p, start, dur=DUR):
    x, sr = sf.read(p, always_2d=True); x = resample(x, sr)
    if x.shape[1] == 1: x = np.repeat(x, 2, 1)
    seg = x[int(start * SR):int(start * SR) + int(dur * SR)]
    return np.pad(seg, ((0, int(dur * SR) - len(seg)), (0, 0)))
def filt(x, lo=None, hi=None, order=2):
    f = np.fft.rfftfreq(len(x), 1 / SR); H = np.ones_like(f)
    if hi: H /= np.sqrt(1 + (f / hi) ** (2 * order))
    if lo: H /= np.sqrt(1 + (lo / np.maximum(f, 1e-3)) ** (2 * order))
    return np.fft.irfft(np.fft.rfft(x, axis=0) * (H[:, None] if x.ndim > 1 else H), len(x), axis=0)
def rms_db(x): return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)
def level(x, target_db): return x * 10 ** ((target_db - rms_db(x)) / 20)
def width(x, w):  # w<1 收窄立体声，>1 展宽
    m, s = (x[:, 0] + x[:, 1]) / 2, (x[:, 0] - x[:, 1]) / 2 * w
    return np.stack([m + s, m - s], 1)
def pan(x, p):
    a = (p + 1) * np.pi / 4; m = x.mean(1) if x.ndim > 1 else x
    return np.stack([m * np.cos(a), m * np.sin(a)], 1)

S = lambda k, start: load(os.path.join(sao_dir, f"{k}.flac"), start)
layers = {
    # 名称: (信号, 目标 RMS dBFS)
    "engine": (pan(filt(S("engine", 1.5), 30), 0.35) * 0.6 + width(filt(S("engine", 1.5), 30), 0.5) * 0.4, -20),
    "tyres": (pan(filt(S("tyres", 2.5), 40), 0.45) * 0.7 + filt(S("tyres", 2.5), 40) * 0.3, -24),
    "street": (width(filt(S("street", 0.5), 80, 9000), 1.4), -34),
    "heli": (filt(S("heli", 1.0), 40, 700), -36),
    "bumpbed": (filt(S("bumps", 1.0), 60), -38),
}

# 与画面同步的悬挂撞击 + 装载物金属碰撞
clunk = np.zeros(N); rattle = np.zeros(N)
for tb, a in BUMPS:
    i0 = int((tb - T0) * SR)
    if i0 >= N: continue
    n = N - i0; tt = np.arange(n) / SR
    clunk[i0:] += a * np.sin(2 * np.pi * 52 * tt) * np.exp(-tt * 20) + a * 0.6 * filt(rng.standard_normal(n), 150, 900) * np.exp(-tt * 35)
    for _ in range(5):
        j = i0 + int(rng.uniform(0.01, 0.22) * SR)
        if j >= N: continue
        m = N - j; tm = np.arange(m) / SR
        rattle[j:] += a * rng.uniform(0.2, 0.6) * np.sin(2 * np.pi * rng.uniform(900, 3000) * tm) * np.exp(-tm * rng.uniform(40, 90))
layers["clunk"] = (pan(clunk, 0.35), -27)
layers["rattle"] = (pan(rattle, 0.3), -36)

# 无线电：静噪起头 → 台词（电台带宽 + 轻度削波）→ "喀"一声收尾
if radio_p != "-":
    v, vsr = sf.read(radio_p, always_2d=True); v = resample(v.mean(1), vsr)
    v = filt(v, 350, 2800, 3); v = np.tanh(v / (np.max(np.abs(v)) + 1e-9) * 2.2)
    rad = np.zeros(N); s0 = int(0.38 * SR)  # 2.5 s 台词在 3 s 镜头内说完
    st = filt(S("radio", 0.0)[:, 0], 400, 3200)
    burst = int(0.18 * SR); rad[s0 - burst:s0] += st[:burst] * np.linspace(0, 1, burst) ** 0.5 * 0.6
    L = min(len(v), N - s0); rad[s0:s0 + L] += v[:L] + st[burst:burst + L] * 0.12
    e = s0 + L
    if e + 1500 < N: rad[e:e + 1500] += np.sin(2 * np.pi * 1700 * np.arange(1500) / SR) * np.exp(-np.arange(1500) / 200) * 0.5
    layers["radio"] = (pan(rad, -0.15), -27)

# 配乐：取 60 秒配乐中与镜头对应的 13.5–16.5 s，压低在声效之下
if bgm_p != "-":
    layers["bgm"] = (filt(load(bgm_p, T0), 35), -30)

mix = sum(level(x, d) for x, d in layers.values())
# 两侧墙面早期反射（街宽约 17 m）
def delay(x, ms, g): d = int(SR * ms / 1000); y = np.zeros_like(x); y[d:] = x[:-d]; return y * g
mix = mix + filt(np.stack([delay(mix[:, 1], 31, 0.25), delay(mix[:, 0], 26, 0.27)], 1), None, 4500)
fade = np.minimum(1, np.minimum(t / 0.03, (DUR - t) / 0.05))[:, None]
mix = mix * fade; mix = mix / np.max(np.abs(mix)) * 10 ** (-1.5 / 20)
sf.write(out_p, mix.astype(np.float32), SR, subtype="PCM_24")
print("layers:", {k: round(rms_db(level(x, d)), 1) for k, (x, d) in layers.items()}, "->", out_p)
