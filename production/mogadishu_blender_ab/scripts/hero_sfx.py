# 基准镜头（车队贴地跟拍，样片 13.5–16.5 s）的分层声音设计。全部本地程序化合成、固定种子，无外部素材。
# 用法：python hero_sfx.py <输出.wav>
# 层次：头车柴油 V8（点火脉冲 + 涡轮哨音）/ 轮胎碾砂石 / 与画面颠簸同步的悬挂撞击和装载物响动 / 后车与卡车 /
#       街道风声、远处人声、远处黑鹰旋翼 / 一次无线电静噪 / 两侧墙面早期反射 + 短混响。立体声 48 kHz。
import numpy as np, soundfile as sf, sys

SR, DUR, T0 = 48000, 3.0, 13.5
N = int(SR * DUR); t = np.arange(N) / SR
rng = np.random.default_rng(19931003)
BUMPS = [(14.05, 1.0), (14.9, 0.6), (15.62, 1.2), (16.2, 0.7)]  # 与 convoy_hero.py 的画面颠簸一致（绝对时间）

def spec_filter(x, lo=None, hi=None, order=2):
    """频域平滑带通（巴特沃斯幅度响应），整段信号一次 FFT。"""
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); H = np.ones_like(f)
    if hi: H /= np.sqrt(1 + (f / hi) ** (2 * order))
    if lo: H /= np.sqrt(1 + (lo / np.maximum(f, 1e-3)) ** (2 * order))
    return np.fft.irfft(X * H, len(x))
def norm(x, peak=1.0): return x / (np.max(np.abs(x)) + 1e-12) * peak
def pan(x, p):  # p: -1 左 … +1 右，等功率；p 可为数组
    a = (np.asarray(p) + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], 1)
def db(v): return 10 ** (v / 20)

def diesel(rpm, cyl=8, seed=0, rough=0.12):
    """柴油机：按点火频率生成燃烧脉冲（每缸略有不均）→ 低通成机体轰鸣，叠加谐波与涡轮哨音。"""
    r = np.random.default_rng(seed)
    fire = rpm / 60 * cyl / 2
    ph = np.cumsum(fire / SR); k = np.floor(ph).astype(int)
    amp = 1 + rough * r.standard_normal(k.max() + 2)
    frac = ph - np.floor(ph)
    pulse = np.exp(-frac * 9) * amp[k] * (1 + 0.3 * np.sin(2 * np.pi * ph / cyl))  # 每圈的不均匀（V8 隆隆）
    body = spec_filter(pulse - pulse.mean(), 25, 420, 3)
    clatter = spec_filter(r.standard_normal(N) * np.exp(-frac * 30), 900, 3500) * 0.25  # 柴油"喀喀"敲击
    harm = sum(np.sin(2 * np.pi * np.cumsum(fire * h / SR)) / h for h in (0.5, 1, 2, 3))
    turbo = np.sin(2 * np.pi * np.cumsum((3900 + 60 * np.sin(2 * np.pi * 0.4 * t)) / SR)) * 0.02
    return norm(body) + 0.18 * norm(harm) + clatter + turbo

lead_rpm = 2050 + 60 * np.sin(2 * np.pi * 0.35 * t)
engine = diesel(lead_rpm, 8, 1)

# 轮胎碾过砂土：宽带滚动噪声 + 随机碎石爆裂
roll = spec_filter(rng.standard_normal(N), 60, 1800) * (1 + 0.3 * spec_filter(rng.standard_normal(N), None, 6))
pops = np.zeros(N); idx = rng.choice(N, 420, replace=False); pops[idx] = rng.uniform(0.3, 1, 420) * rng.choice([-1, 1], 420)
grit = spec_filter(np.convolve(pops, np.exp(-np.arange(200) / 25), "same"), 1200, 7000)
tyres = norm(roll) * 0.7 + norm(grit) * 0.45

# 悬挂撞击 + 车上装载物（油桶、弹药箱、天线）响动，时刻与画面颠簸一致
clunk = np.zeros(N); rattle = np.zeros(N)
for tb, a in BUMPS:
    i0 = int((tb - T0) * SR)
    if i0 >= N: continue
    n = N - i0; tt = np.arange(n) / SR
    clunk[i0:] += a * np.sin(2 * np.pi * 55 * tt) * np.exp(-tt * 22) + a * 0.5 * spec_filter(rng.standard_normal(n), 150, 900) * np.exp(-tt * 40)
    for _ in range(6):  # 金属件碰撞：短促高频衰减振铃
        j = i0 + int(rng.uniform(0.01, 0.25) * SR)
        if j >= N: continue
        m = N - j; tm = np.arange(m) / SR; fr = rng.uniform(900, 3200)
        rattle[j:] += a * rng.uniform(0.2, 0.6) * np.sin(2 * np.pi * fr * tm) * np.exp(-tm * rng.uniform(40, 90))
    m = min(N - i0, int(0.6 * SR))  # 天线甩动的嗡声
    rattle[i0:i0 + m] += a * 0.12 * np.sin(2 * np.pi * 7.5 * np.arange(m) / SR) * spec_filter(rng.standard_normal(m), 300, 1200) * np.exp(-np.arange(m) / SR * 5)

# 后车：第二辆悍马（13 m 后）与 5 吨卡车（27 m 后），更远、更闷
follow = spec_filter(diesel(1900 + 50 * np.sin(2 * np.pi * 0.27 * t + 1), 8, 2), None, 900) * 0.5
truck = spec_filter(diesel(1750 + 40 * np.sin(2 * np.pi * 0.2 * t + 2), 6, 3), None, 500) * 0.35

# 街道环境：阵风、远处人群嘈杂（带共振峰调制的噪声）、远处黑鹰旋翼（17.2 Hz 桨叶拍击，强低通）
gust = 0.6 + 0.4 * spec_filter(rng.standard_normal(N), None, 0.8); gust = gust / np.max(np.abs(gust))
wind = spec_filter(rng.standard_normal(N), 150, 2500) * gust
crowd = sum(spec_filter(rng.standard_normal(N), f0 * 0.8, f0 * 1.25) * (0.5 + 0.5 * np.sin(2 * np.pi * rng.uniform(2, 5) * t + rng.uniform(0, 6)))
            for f0 in (380, 650, 1100, 2400))
ph = (t * 17.2) % 1.0
rotor = spec_filter(spec_filter(rng.standard_normal(N), None, 500) * (0.3 + 1.4 * np.exp(-ph * 9)), None, 260)

# 无线电静噪（车内电台，一声"嘶—喀"，无语音）
radio = np.zeros(N); r0, r1 = int(0.95 * SR), int(1.32 * SR)
radio[r0:r1] = spec_filter(rng.standard_normal(r1 - r0), 400, 2800) * 0.5
radio[r1:r1 + 900] += np.sin(2 * np.pi * 1800 * np.arange(900) / SR) * np.exp(-np.arange(900) / 120)

# 混音（声像：车在画面右侧；后车在左后；人群偏左；旋翼居中偏高）
mix = (pan(norm(engine), 0.45) * db(-6) + pan(norm(tyres), 0.5) * db(-9) + pan(norm(clunk), 0.4) * db(-7) +
       pan(norm(rattle), 0.35) * db(-15) + pan(norm(follow), -0.35) * db(-17) + pan(norm(truck), -0.5) * db(-22) +
       np.stack([norm(wind) * db(-24), norm(np.roll(wind, 2400)) * db(-24)], 1) +
       pan(norm(crowd), -0.55) * db(-30) + pan(norm(rotor), 0.0) * db(-27) + pan(norm(radio), 0.2) * db(-23))

# 两侧墙面早期反射（街宽 17 m）+ 短混响尾（噪声卷积，0.7 s 衰减）
def delay(x, ms, g, lp): d = int(SR * ms / 1000); y = np.zeros_like(x); y[d:] = x[:-d]; return spec_filter(y, None, lp) * g
L, R = mix[:, 0], mix[:, 1]
L2 = L + delay(R, 31, 0.32, 4500) + delay(L, 54, 0.2, 3500)
R2 = R + delay(L, 26, 0.35, 4500) + delay(R, 49, 0.2, 3500)
ir_t = np.arange(int(0.7 * SR)) / SR
irL = rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 9); irR = rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 9)
def conv(x, h): n = len(x) + len(h); return np.fft.irfft(np.fft.rfft(x, n) * np.fft.rfft(h, n), n)[:len(x)]
wetL, wetR = spec_filter(conv(L2, irL), 200, 5000), spec_filter(conv(R2, irR), 200, 5000)
out = np.stack([L2 + norm(wetL) * np.max(np.abs(L2)) * 0.12, R2 + norm(wetR) * np.max(np.abs(R2)) * 0.12], 1)
fade = np.minimum(1, np.minimum(t / 0.03, (DUR - t) / 0.05))[:, None]
out = norm(out * fade, db(-1.5))
sf.write(sys.argv[1], out.astype(np.float32), SR, subtype="PCM_24")
print("wrote", sys.argv[1], out.shape)
