# 把 Blender 输出的 PNG 序列套上与 mogadishu_pilot/world.js 相同的胶片调色，编码为 MP4。
# 用法：python grade.py <帧目录> <输出.mp4> [起始帧号，用于确定颗粒] [白平衡增益 r,g,b]
# 调色步骤与 world.js gradeMat 一致（色调映射之后的部分）：漂白旁路、降饱和、分离色调、反差、暗角、颗粒、边缘色散。
import numpy as np, subprocess, sys, glob, os

src, out = sys.argv[1], sys.argv[2]
frame0 = int(sys.argv[3]) if len(sys.argv) > 3 else 0
# 可选源白平衡（线性 RGB 增益），在统一调色前把离线渲染素材校到与实时版相近的暖调
WB = np.array([float(v) for v in sys.argv[4].split(',')], np.float32) if len(sys.argv) > 4 else np.ones(3, np.float32)
files = sorted(glob.glob(os.path.join(src, "f_*.png")))
W, H = 1920, 816

def read(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-f", "rawvideo", "-pix_fmt", "rgb48le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint16).reshape(H, W, 3).astype(np.float32) / 65535.0

to_lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
to_srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.maximum(c, 0), 1 / 2.4) - 0.055)
def smoothstep(a, b, x):
    u = np.clip((x - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
dx, dy = xx / W - 0.5, (H - 1 - yy) / H - 0.5
r2 = dx * dx + dy * dy
vig = 1.0 - smoothstep(0.14, 0.62, r2 * 1.35) * 0.55

def hash2(x, y):
    n = np.sin(x * 12.9898 + y * 78.233) * 43758.5453
    return n - np.floor(n)

GRADE_MIX = float(os.environ.get("GRADE_MIX", "1"))
HALATION = float(os.environ.get("HALATION", "0"))  # 可选：胶片高光溢光（红橙色光晕），hero 版使用
def box_blur(a, r):
    for ax in (0, 1):
        c = np.cumsum(np.pad(a, [(r + 1, r) if i == ax else (0, 0) for i in range(a.ndim)], mode="edge"), axis=ax)
        a = (np.take(c, range(2 * r + 1, c.shape[ax]), axis=ax) - np.take(c, range(0, c.shape[ax] - 2 * r - 1), axis=ax)) / (2 * r + 1)
    return a

def grade(img, frame):
    # 边缘色散：R 往外、B 往内各偏 ~r2*0.012
    sh = (np.sqrt(r2) * r2 * 0.012 * W).astype(np.float32)  # 与 world.js 的 d*r2*0.012 一致
    c = img.copy()
    for ch, sgn in ((0, 1), (2, -1)):
        sx = np.clip(xx + sgn * dx / np.maximum(np.sqrt(r2), 1e-4) * sh, 0, W - 1).astype(int)
        sy = np.clip(yy - sgn * dy / np.maximum(np.sqrt(r2), 1e-4) * sh, 0, H - 1).astype(int)
        c[..., ch] = img[sy, sx, ch]
    c = to_lin(c) * WB
    c0 = c.copy()
    l = (c @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
    ov = np.where(l < 0.5, 2 * c * l, 1 - 2 * (1 - c) * (1 - l))
    c = c + (ov - c) * 0.34
    c = l + (c - l) * 0.68
    c = c + np.array([-0.02, 0.012, 0.018], np.float32) * (1 - smoothstep(0, 0.45, l))
    c = c * (1 + (np.array([1.06, 1.0, 0.86], np.float32) - 1) * smoothstep(0.35, 0.95, l))
    c = np.clip((c - 0.5) * 1.08 + 0.5 + 0.004, 0, 1)
    c = c0 + (c - c0) * GRADE_MIX  # 调色强度：1 = 与 world.js 一致；暗调的离线素材用较低值避免压死暗部
    if HALATION > 0:
        hi = np.clip((c - 0.62) / 0.38, 0, 1)
        glow = box_blur(box_blur(hi, 9), 9)
        c = c + glow * np.array([1.0, 0.42, 0.18], np.float32) * HALATION
    c = c * vig[..., None]
    o = to_srgb(c)
    g = hash2(xx + frame * 17.0, yy + frame * 31.0) - 0.5
    g2 = hash2(np.floor(xx * 0.5) + frame * 7.0, np.floor(yy * 0.5) + frame * 3.0) - 0.5
    o = o + ((g * 0.05 + g2 * 0.035)[..., None]) * (1 - np.abs(l - 0.45))
    return np.clip(o * 255 + 0.5, 0, 255).astype(np.uint8)

enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30", "-i", "-",
                        "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
for i, p in enumerate(files):
    enc.stdin.write(grade(read(p), frame0 + i).tobytes())
enc.stdin.close(); enc.wait()
print("graded", len(files), "frames ->", out)
