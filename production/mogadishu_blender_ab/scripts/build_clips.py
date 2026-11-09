#!/usr/bin/env python3
# 把 Blender 渲染帧 + 正式旁白 + 音效 + 字幕合成为分支播放器的各节点片段（mogadishu_pilot/branch/clips/），
# 再按默认路线（A + 任务与救援）拼一条带 BGM 的线性 MP4。
# 用法：python3 build_clips.py [节点名 ...]   （不给节点名则全部合成，并导出线性版）
#       python3 build_clips.py --linear      （只重拼线性版）
import os, subprocess, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
PILOT = os.path.abspath(os.path.join(ROOT, "..", "mogadishu_pilot"))
CLIPS = os.path.join(PILOT, "branch", "clips")
REN = os.path.join(ROOT, "renders")
NARR = os.path.join(ROOT, "audio", "indextts", "final")
SAO = os.path.join(ROOT, "audio", "sao")
AMB = os.path.join(PILOT, "assets", "sfx", "ambience.wav")
# 配乐：优先用分支版专用的无鼓点铺底（gen_bgm_branch.py 生成），没有则退回旧的 60 秒样片配乐
BGM = next((p for p in [os.path.join(ROOT, "audio", "bgm", "bgm_branch.flac"), os.path.join(ROOT, "audio", "bgm", "bgm_60s_seed1003.flac")] if os.path.exists(p)))
# 配乐电平：BGM 文件统一到 -14 LUFS 后乘 BGM_GAIN（≈ -30 LUFS，比旁白低约 10 dB），旁白期间再乘 DUCK（再降约 7 dB）
BGM_GAIN, DUCK, DUCK_IN, DUCK_OUT = 0.16, 0.45, 0.4, 0.8
WORK = os.path.join(ROOT, "renders", "clips_work")
FPS = 30
FONT = "PingFang SC"

# 镜头 → 帧目录与帧号范围（与 city_shots.py 的 RANGES 一致：帧号 = round(t*30)+1 … round(t1*30)）
def shot(s):
    from math import floor
    R = {"1": (0, 10), "2a": (10, 13.5), "2c": (16.5, 20), "3": (20, 30), "4": (30, 35.5), "L1": (35.5, 39.5), "4A": (35.5, 45.5), "4B": (35.5, 45.5),
         "5": (40, 50), "6": (50, 57.5), "L2": (57.5, 61.5), "E1": (57.5, 65.5), "E2": (57.5, 65.5), "E3": (57.5, 65.5)}
    a, b = R[s]
    return os.path.join(REN, "city", s), int(round(a * FPS)) + 1, int(round(b * FPS))

HERO = (os.path.join(REN, "hero_final"), 1, 90)  # 13.5–16.5 s 悍马贴地镜头（AI 悍马 + AI 人物）

# 字幕时间均为节点内时间（秒）。meta：上遮幅左侧的时间地点；title：画内左下的场景标题；narr：旁白（文件, 起点）；
# sfx：(文件, 起点, 音量, 循环, 淡出起点)；src：下遮幅右侧来源。
NODES = {
    "trunk": dict(
        shots=[shot("1"), shot("2a"), HERO, shot("2c"), shot("3"), shot("4")],
        meta=[(0, 20, "1993.10.03 · 15:30"), (20, 30, "1993.10.03 · 16:20"), (30, 35.5, "1993.10.03 · 16:40")],
        title=[(0.8, 7.5, "1993 年 10 月 3 日 · 15:30", "摩加迪沙 · 行动开始"),
               (10.6, 17.0, "抓捕目标", "两名重要助手 · 陆军记录 24 人被拘押"),
               (26.2, 30.0, "第一架黑鹰坠落", "目标区外约三个街区 · 行动转为救援"),
               (31.0, 35.3, "第二架黑鹰被击落", "约二十分钟后")],
        narr=[("scene-01", 0.6), ("scene-02", 10.4), ("scene-03", 20.4), ("scene-04", 30.8)],
        sfx=[(AMB, 0, 0.55, False, None), ("heli", 0, 0.30, True, 25.4), ("engine", 13.5, 0.45, True, 16.4),
             ("tyres", 13.5, 0.25, True, 16.4), ("thud", 25.9, 0.9, False, None), ("thud", 31.6, 0.35, False, None)],
        src="来源：美国陆军战后报告 · NCO Journal 2022"),
    "loop1": dict(shots=[shot("L1")], meta=[(0, 4, "1993.10.03 · 16:40")], sfx=[(AMB, 30, 0.5, False, None)]),
    "site_a": dict(
        shots=[shot("4A")],
        meta=[(0, 10, "1993.10.03 · 16:40 · 第一处坠机点")],
        title=[(0.6, 6.0, "第一处坠机点", "距目标区约三个街区 · 搜救组索降")],
        narr=[("scene-04a", 0.5)],
        sfx=[(AMB, 36, 0.45, False, None), ("heli", 0, 0.55, True, None)],
        src="来源：美国陆军战后报告"),
    "site_b": dict(
        shots=[shot("4B")],
        meta=[(0, 10, "1993.10.03 · 16:40 · 第二处坠机点")],
        title=[(0.6, 6.0, "第二处坠机点", "在第一处以南 · 不到一英里")],
        narr=[("scene-04b", 0.5)],
        sfx=[(AMB, 36, 0.5, False, None), ("heli", 0, 0.18, True, None)],
        src="来源：美国陆军战后报告 · 美国国务院史料办公室"),
    "converge": dict(
        shots=[shot("5")],
        meta=[(0, 10, "1993.10.04 · 01:55")],
        title=[(0.6, 6.5, "10 月 4 日 · 01:55", "救援纵队抵达第一处坠机点")],
        narr=[("scene-05", 0.6)],
        sfx=[("engine", 0, 0.5, True, None), ("tyres", 0, 0.3, True, None), ("radio", 2.0, 0.18, True, None)],
        src="来源：美国陆军战后报告"),
    "dawn": dict(
        shots=[shot("6")],
        meta=[(0, 7.5, "1993.10.04 · 清晨")],
        stats=(0.5, 7.5, "18　·　75　·　84", "美军死亡 18 · 联合国记录伤者 75 ·《华盛顿邮报》记录伤者 84 · 总伤亡数未确认"),
        narr=[("scene-06", 0.3)],
        sfx=[(AMB, 50, 0.4, False, None)],
        src="来源：美国陆军 · 联合国 S/26738 ·《华盛顿邮报》"),
    "loop2": dict(shots=[shot("L2")], meta=[(0, 4, "1993.10.04 · 清晨")], sfx=[(AMB, 54, 0.4, False, None)]),
    "end_a": dict(
        shots=[shot("E1")],
        meta=[(0, 8, "1993.10.04 · 清晨")],
        title=[(0.6, 6.5, "任务与救援", "车队撤回巴基斯坦体育场")],
        narr=[("scene-e1", 0.5)],
        sfx=[("engine", 0, 0.45, True, None), ("tyres", 0, 0.3, True, None), (AMB, 20, 0.3, False, None)],
        src="来源：美国陆军战后报告"),
    "end_b": dict(
        shots=[shot("E2")],
        meta=[(0, 8, "1993.10.04 · 清晨")],
        title=[(0.6, 6.5, "城市与平民", "索马里一方伤亡没有统一确认的数字")],
        narr=[("scene-e2", 0.5)],
        sfx=[("street", 0, 0.55, True, None), (AMB, 10, 0.4, False, None)],
        src="来源：联合国 S/26738 ·《华盛顿邮报》"),
    "end_c": dict(
        shots=[shot("E3")],
        meta=[(0, 8, "1993.10 → 1994.03")],
        title=[(0.6, 6.5, "政策后果", "宣布撤军 · 1994 年 3 月美军离开索马里")],
        narr=[("scene-e3", 0.5)],
        sfx=[(AMB, 40, 0.35, False, None)],
        src="来源：美国国务院史料办公室"),
}
LINEAR = ["trunk", "site_a", "converge", "dawn", "end_a"]

TEXT = {}  # 旁白文字（字幕用），从 indextts_gen.py 读取
def load_text():
    src = open(os.path.join(ROOT, "..", "..", "tools", "audio", "indextts_gen.py"), encoding="utf-8").read()
    ns = {}
    exec(src[src.index("LINES = {"):src.index("}", src.index("LINES = {")) + 1], ns)
    TEXT.update(ns["LINES"])

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"命令失败：{' '.join(cmd[:6])} …\n{r.stderr[-2000:]}")
    return r.stdout

def dur(path):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).strip())

def ts(t):
    t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def split_line(text, n=24):
    # 按标点切成不超过 n 字的字幕条；返回 [(文字, 字数)]
    parts, cur = [], ""
    for ch in text:
        cur += ch
        if ch in "，。；" and len(cur) >= 6:
            parts.append(cur); cur = ""
    if cur: parts.append(cur)
    out, buf = [], ""
    for p in parts:
        if buf and len(buf) + len(p) > n:
            out.append(buf); buf = ""
        buf += p
    if buf: out.append(buf)
    return [(s.rstrip("，。；"), len(s)) for s in out]

def ass_header():
    sand, ivory, muted, signal = "&H00B5D2DF", "&H00D4E9F3", "&H00A8AEA9", "&H005086DC"
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Meta,{FONT},22,{muted},{muted},&H00000000,&H00000000,0,0,0,0,100,100,3,0,1,0,0,7,0,0,0,1
Style: Narr,{FONT},36,{ivory},{ivory},&H00000000,&H64000000,0,0,0,0,100,100,1,0,1,0,0,2,0,0,0,1
Style: Title,{FONT},50,{ivory},{ivory},&H00000000,&H96000000,1,0,0,0,100,100,2,0,1,0,3,1,0,0,0,1
Style: Sub,{FONT},26,{sand},{sand},&H80000000,&H96000000,0,0,0,0,100,100,2,0,1,1,2,1,0,0,0,1
Style: Stats,{FONT},104,{ivory},{ivory},&H00000000,&H96000000,1,0,0,0,100,100,6,0,1,0,4,5,0,0,0,1
Style: Src,{FONT},16,{muted},{muted},&H00000000,&H00000000,0,0,0,0,100,100,2,0,1,0,0,3,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

def write_ass(name, spec, length, narr_times):
    signal = "&H5086DC&"; ivory = "&HD4E9F3&"
    ev = []
    for a, b, txt in spec.get("meta", []):
        ev.append(f"Dialogue: 0,{ts(a)},{ts(b)},Meta,,0,0,0,,{{\\pos(112,54)}}{{\\c{ivory}\\b1}}摩加迪沙{{\\c{signal}\\b0}}  /  {{\\c&HA9AEA8&}}索马里 · {txt}")
        ev.append(f"Dialogue: 0,{ts(a)},{ts(b)},Meta,,0,0,0,,{{\\an9\\pos(1808,54)}}CG 重现 · 街区与路线为示意")
    for a, b, t1, t2 in spec.get("title", []):
        ev.append(f"Dialogue: 1,{ts(a)},{ts(b)},Title,,0,0,0,,{{\\pos(112,862)\\fad(450,600)}}{t1}")
        ev.append(f"Dialogue: 1,{ts(a + 0.25)},{ts(b)},Sub,,0,0,0,,{{\\pos(114,912)\\fad(450,600)}}{t2}")
    if "stats" in spec:
        a, b, big, small = spec["stats"]
        ev.append(f"Dialogue: 1,{ts(a)},{ts(b)},Stats,,0,0,0,,{{\\pos(960,500)\\fad(700,0)}}{big}")
        ev.append(f"Dialogue: 1,{ts(a + 0.6)},{ts(b)},Sub,,0,0,0,,{{\\an5\\pos(960,600)\\fad(700,0)}}{small}")
    for key, t0, d in narr_times:  # 旁白字幕：按字数比例分配时长
        chunks = split_line(TEXT[key]); total = sum(c for _, c in chunks); t = t0
        for txt, c in chunks:
            seg = d * c / total
            ev.append(f"Dialogue: 2,{ts(t)},{ts(min(length, t + seg + 0.15))},Narr,,0,0,0,,{{\\an2\\pos(960,1012)}}{txt}")
            t += seg
    if spec.get("src"):
        ev.append(f"Dialogue: 0,{ts(0)},{ts(length)},Src,,0,0,0,,{{\\an3\\pos(1808,1068)}}{spec['src']}")
    p = os.path.join(WORK, f"{name}.ass")
    open(p, "w", encoding="utf-8").write(ass_header() + "\n".join(ev) + "\n")
    return p

def make_thud():
    # 远处闷响：棕噪声 + 低通，快起慢收（不用枪声）
    p = os.path.join(WORK, "thud.wav")
    if not os.path.exists(p):
        run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anoisesrc=color=brown:d=3.5:a=1:r=48000",
             "-af", "lowpass=f=110,lowpass=f=110,afade=t=in:d=0.02,afade=t=out:st=0.15:d=3.3:curve=exp,volume=6,alimiter=limit=0.9",
             "-ac", "2", p])
    return p

def trimmed(src):
    # 去掉 TTS 首尾静音，给紧凑的片段多留一点空间
    p = os.path.join(WORK, "narr_" + os.path.basename(src))
    if not os.path.exists(p) or os.path.getmtime(p) < os.path.getmtime(src):
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af",
             "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,adelay=60:all=1", p])
    return p

def sfx_path(k):
    if k == "thud": return make_thud()
    if os.path.isabs(k): return k
    return os.path.join(SAO, f"{k}.flac")

def clip_length(name):
    return sum(b - a + 1 for _, a, b in NODES[name]["shots"]) / FPS

def narr_plan(name, length, quiet=False):
    # 旁白：超长的轻微提速（最多 1.12×）塞进片段。返回 (key, 起点, 实际时长, 文件, 速率)
    out = []
    for k, t0 in NODES[name].get("narr", []):
        p = trimmed(os.path.join(NARR, f"{k}.wav")); d = dur(p)
        room = length - t0 - 0.3; tempo = 1.0
        if d > room:
            tempo = min(1.12, d / room)
            if not quiet: print(f"  [{name}] {k} {d:.2f}s 超出 {room:.2f}s，提速 {tempo:.3f}" + ("（仍超出）" if d / tempo > room else ""))
        out.append((k, t0, d / tempo, p, tempo))
    return out

def write_narr_json():
    # 播放器按此在旁白期间压低 BGM：{节点片段名: [[起, 止], ...]}
    os.makedirs(WORK, exist_ok=True)
    data = {nm: [[round(t0, 2), round(t0 + d, 2)] for _, t0, d, _, _ in narr_plan(nm, clip_length(nm), quiet=True)] for nm in NODES}
    data["_mix"] = {"gain": BGM_GAIN, "duck": DUCK, "in": DUCK_IN, "out": DUCK_OUT}
    with open(os.path.join(CLIPS, "narr.js"), "w") as f:
        f.write("// build_clips.py 生成：各片段的旁白时段（秒），播放器据此压低 BGM\nwindow.NARR = " + json.dumps(data, ensure_ascii=False) + ";\n")

def bgm_m4a():
    # 播放器用的 BGM：统一响度到 -14 LUFS，音量由播放器按 BGM_GAIN 控制
    out = os.path.join(CLIPS, "bgm.m4a")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", BGM, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000", "-c:a", "aac", "-b:a", "192k", out])
    print(f"[bgm] {BGM} -> {out}")

def build(name):
    spec = NODES[name]
    os.makedirs(WORK, exist_ok=True)
    # ---- 画面 ----
    vin, vf, nframes = [], [], 0
    for i, (d, a, b) in enumerate(spec["shots"]):
        missing = [f for f in range(a, b + 1) if not os.path.exists(os.path.join(d, f"f_{f:04d}.png"))]
        if missing:
            sys.exit(f"{name}: {d} 缺 {len(missing)} 帧（如 f_{missing[0]:04d}.png）")
        vin += ["-framerate", str(FPS), "-start_number", str(a), "-i", os.path.join(d, "f_%04d.png")]
        vf.append(f"[{i}:v]scale=1920:816,setsar=1,format=yuv420p10le,trim=end_frame={b - a + 1}[s{i}]")
        nframes += b - a + 1
    length = nframes / FPS
    n = len(spec["shots"])
    narr_times, ain = [], []
    for k, t0, d, p, tempo in narr_plan(name, length):
        narr_times.append((k, t0, d)); ain.append((p, t0, 1.0, False, None, tempo))
    for f, t0, vol, loop, fade in spec.get("sfx", []):
        ain.append((sfx_path(f), t0, vol, loop, fade, 1.0))
    ass = write_ass(name, spec, length, narr_times)
    # ---- 音频输入：环境音从 t0 秒处截取（AMB 的 t0 表示文件内起点），其它音效在节点内 t0 处开始 ----
    ainputs, af, labels = [], [], []
    for j, (p, t0, vol, loop, fade, tempo) in enumerate(ain):
        idx = n + j
        is_amb = p == AMB
        if loop: ainputs += ["-stream_loop", "-1"]
        if is_amb: ainputs += ["-ss", str(t0)]
        ainputs += ["-i", p]
        chain = f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo"
        if tempo != 1.0: chain += f",atempo={tempo:.4f}"
        chain += f",volume={vol}"
        if not is_amb and t0 > 0: chain += f",adelay={int(t0 * 1000)}:all=1"
        if fade is not None: chain += f",afade=t=out:st={fade}:d=1.2"
        chain += f",atrim=end={length},apad=whole_dur={length}[a{j}]"
        af.append(chain); labels.append(f"[a{j}]")
    vcat = "".join(f"[s{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[cat]"
    vpost = ("[cat]pad=1920:1080:0:132:color=0x070909,"
             "drawbox=x=0:y=131:w=1920:h=1:color=0xDC8650@0.22:t=fill,drawbox=x=0:y=948:w=1920:h=1:color=0xDC8650@0.22:t=fill,"
             f"ass='{ass}',format=yuv420p[v]")
    amix = "".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=longest,alimiter=limit=0.95,atrim=end={length}[a]"
    out = os.path.join(CLIPS, f"{name}.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error", *vin, *ainputs, "-filter_complex", ";".join(vf + [vcat, vpost] + af + [amix]),
         "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{length:.3f}", out])
    print(f"[clip] {name}: {length:.2f}s -> {out}")

def linear():
    parts = [os.path.join(CLIPS, f"{n}.mp4") for n in LINEAR]
    total = sum(dur(p) for p in parts)
    # 旁白时段换算到整条时间线，生成 BGM 的压低包络
    wins, off = [], 0.0
    for nm, p in zip(LINEAR, parts):
        wins += [(off + t0, off + t0 + d) for _, t0, d, _, _ in narr_plan(nm, clip_length(nm), quiet=True)]
        off += dur(p)
    env = "*".join(f"(1-{1 - DUCK}*clip((t-{a - DUCK_IN:.2f})/{DUCK_IN},0,1)*clip(({b + DUCK_OUT:.2f}-t)/{DUCK_OUT},0,1))" for a, b in wins) or "1"
    inp = []
    for p in parts: inp += ["-i", p]
    k = len(parts)
    fc = "".join(f"[{i}:v][{i}:a]" for i in range(k)) + f"concat=n={k}:v=1:a=1[v][na];" \
         f"[{k}:a]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=stereo,volume={BGM_GAIN},volume='{env}':eval=frame," \
         f"afade=t=in:d=1.5,afade=t=out:st={total - 3}:d=3,atrim=end={total}[bg];" \
         "[na][bg]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95[a]"
    out = os.path.join(PILOT, "renders", "mogadishu_branch_default_path.mp4")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    run(["ffmpeg", "-y", "-loglevel", "error", *inp, "-stream_loop", "-1", "-i", BGM, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out])
    print(f"[linear] {total:.2f}s -> {out}")

if __name__ == "__main__":
    load_text()
    args = sys.argv[1:]
    if args == ["--linear"]:
        linear()
    elif args == ["--mix"]:  # 只更新播放器的 BGM 与旁白时段
        write_narr_json(); bgm_m4a()
    else:
        for nme in (args or list(NODES)):
            build(nme)
        write_narr_json()
        if not args:
            linear()
