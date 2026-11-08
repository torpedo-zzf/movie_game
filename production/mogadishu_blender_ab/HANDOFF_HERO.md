# 基准镜头交接（车队贴地跟拍，样片 13.5–16.5 s）

更新：2026-11-02。目标：在一个 3 秒镜头上验证"影视/CG 级"画面 + 沉浸式声音，用户认可后再铺到 60 秒全片。

## 已完成
- **场景**：`scripts/convoy_hero.py`（由 `convoy_shot.py` 复制改造；原脚本保留作 A/B）
  - Poly Haven CC0 素材（用户已同意下载，169 MB）在 `assets/polyhaven/`：11 套 2K 贴图、goegap 4K HDRI、12 个 1K glTF 道具
  - 墙面/卷帘/铁皮/路面/地面换成 PBR 三向投影贴图；HDRI 只做照明，背景用加沙尘的天空
  - 侧逆光低角度太阳；手持运镜（Perlin + 路面颠簸 `BUMPS`）；f/2.8，变形镜头散景
  - M1025 悍马重建（收腰车厢、斜背、带胶条玻璃、铰链、格栅、灯、护杠、炮塔机枪手、随车油桶）
  - 街边人物剪影 26 个站立 + 6 个步行 + 3 个前方横穿奔跑；道具散布；西侧人行道给机位让出通道
- **渲染**：`renders/hero/f_0001–0090.png`（Cycles 64 spp，约 25 s/帧）
- **调色**：`scripts/grade.py` 新增 `GRADE_MIX`（调色强度）与 `HALATION`（高光溢光）；hero 用 0.4 / 0.12，白平衡 1.06,1.0,0.9
- **声音**（用户指定工具链）：
  - 音效：ComfyUI Stable Audio Open 1.0 → `audio/sao/*.flac`（engine/tyres/bumps/street/heli/radio，各 8 s）
  - 语音：ChatTTS（`tools/audio/.venv-chattts`，权重在 `tools/audio/models/asset`，需在该目录下运行）
    - 旁白：用户选定种子 7，6 段正式旁白在 `audio/chattts/narr_7/scene-01..06.wav`（用户试听认可）；说话人向量存于 `narr_7/speaker.txt`
      （注意：同种子在当前环境的输出与早先候选 `cand_7` 不一致，以 narr_7 为准）
    - 无线电台词：`audio/chattts/radio.wav`（种子 41，"Convoy, keep it tight. Eyes on the rooftops."）
  - 混音：`scripts/hero_mix.py`（音效分层 + 同步颠簸撞击 + 电台 + BGM 对应段落）
- **成片**：`scripts/make_hero.sh` → `renders/hero.mp4`（3 s，-15.8 LUFS，暂无 BGM）、`renders/abc_sequence.mp4`（A Three.js → B Blender 初版 → C 基准）
- 工具脚本：`tools/audio/comfy_run.py`（向 127.0.0.1:8188 提交 API 工作流并取回音频）、`gen_hero_sfx.py`、`gen_bgm.py`、`chattts_gen.py`

## 未完成 / 下一步
1. **BGM（MiniMax Music 3，ComfyUI 本地）**：第一次生成卡死——Mac 上 ComfyUI 默认把"文本编码器"（实为自回归生成器，8.7 GB int8）放 CPU，约 120 s/步，已中断。已改 `--gpu-only` 重启：MPS 上约 1 步/秒，10 秒片段 288 s，60 秒 BGM 约 30 分钟。
   用户选择"**ComfyUI 改 GPU 重启**"：需要给 Comfy Desktop 的服务器启动参数加 `--gpu-only` 再重启。服务器当前参数见进程 `ComfyUI/main.py`（base dir `/Users/yul/work/comfy`）。
   改设置/重启前先跟用户确认具体做法（上次查找配置时被用户中断）。之后先跑一段短时长（如 10 s）测速，再跑 `python3 -I tools/audio/gen_bgm.py production/mogadishu_blender_ab/audio/bgm 1003`，最后重跑 `scripts/make_hero.sh`。
   int8 convrot 在 MPS 上是否可用尚未验证；不行就退回 Comfy Cloud 节点（需用户登录、消耗点数）。
2. 旁白已完成（narr_7）；铺全片时按 voiceover_script.md 的时间点放置。
3. 画面遗留：悍马漆面仍偏干净偏亮；人物仍像人台；建筑仍偏方盒、重复。
4. 尚无人试听任何音频（只做了响度/频谱检查）。

## 查看帧
`.claude/launch.json` 里的 `blender-ab-review`（端口 8766）+ `renders/review.html?f=相对路径,...`；看图工具（doubao）经常超时，用浏览器截图看。

## 本地 AI 3D 资产测试（2026-11-03）
- 工具：`tools/3d/comfy3d.py`（FLUX dev 出参考图 → TRELLIS.2 出 GLB，按官方模板改写；KEEP_CACHE=1 重试复用缓存）
- 悍马：`assets/gen3d/humvee/ref34_s5_10_0.png`（FLUX，45° 前侧视角；正前视角的 ref_s11/s23 不适合重建）→ `trellis_s5_300_1.glb`（40 万面，2K 底色/金属粗糙 + 4K 法线 + AO）
- 耗时：FLUX 约 190 s/张（峰值锁定 ~35 GB）；TRELLIS.2 实际计算 20 分钟（精细化 1024），峰值锁定 18.5 GB
- **MPS 限制**：精细化 1536 产生 1919 万体素，超过 2^24，BakeTextureFromVoxel 布尔索引越界；必须用 1024
- 评估：`scripts/eval_glb.py` → `renders/gen3d/trellis_s5_grid.jpg`。外形/比例/背面补全很好；问题：车身面板有起伏不平、边缘偏软、玻璃是黑色不透明贴图、贴图偏糊
- 换进镜头：`convoy_hero.py --gen-humvee assets/gen3d/humvee/trellis_s5_300_1.glb`（`humvee_gen`：切出四轮可转、窗玻璃遮罩、沙尘/泥浆、炮塔与机枪手沿用 `turret_crew`）→ `renders/hero_gen/`（90 帧 40 分钟）
- 成片：`scripts/make_hero_gen.sh` → `renders/hero_gen.mp4`、`renders/hero_v2_vs_gen.mp4`（与 v2 同调色同混音）；试听页已加
