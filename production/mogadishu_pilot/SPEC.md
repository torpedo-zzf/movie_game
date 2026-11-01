# Director's brief — 摩加迪沙：任务开始后，计划变了

**GOAL:** 让观众理解一次抓捕行动如何因两架黑鹰坠落转为持续救援，同时看见伤亡数字来自不同记录。  
**OUTPUT:** HyperFrames, 1920×1080, 30 fps; 配套互动播放器 `player.html`。  
**TIME:** 60 秒 × 30 fps = 1,800 帧。播放器在 35.5 秒和 58.5 秒暂停并等待输入；单独 MP4 是线性版本。  
**LOOK:** 以连续的 Three.js 3D 战术沙盘作为主体，不再使用 PPT 页面式播报。立体街区、道路、海岸、目标区、两处坠机点、救援路线和纵队构成同一座非比例示意城市。宽银幕遮幅、暖主光与冷补光、雾化层次、暗角和电影化镜头推进建立影像质感；字幕压缩为下沿短标题、事实句和选择提示。标注清晰、保留史实来源，不仿造档案影像，也不使用未经证实的地图细节。  
**OBJECTS:** 连续沙盘地形、程序化街区、目标区、两处坠机点、路线虚线与方向、救援纵队、日期时刻、来源短标签、18/75/84 伤亡记录。地点与路线均为非比例示意，不代表精确街道坐标或已核实路径。不得伪造无线电、人物对白、战斗声或档案影像。Three.js 0.180.0（MIT）本地打包，渲染不依赖外部地图或模型服务。  
**MOTION:** 镜头在六场中保持同一城市空间连续：建立全景、推进目标区、俯冲第一坠机点、环绕拉开呈现两处现场、拉高跟随纵队沿示意路线移动、最后退回城市全景承载来源数据。路线、尘雾和纵队随时间变化；镜头运动可按任意时间点确定性重建。选择节点仍在 35.5 秒与 58.5 秒暂停。声音使用 macOS 离线 Tingting（zh_CN）中国大陆标准普通话旁白与本地 MusicGen 原创 BGM；动态 carve 为旁白让出清晰度。互动播放器暂停时整段影片音频同步暂停。
**SHOTS:**

1. **0–10s / 0–300f — 行动开始。** 3D 城市沙盘从暗部显现，镜头推进；依次给出地点、`1993.10.03` 和 `约 15:30`。
2. **10–20s / 300–600f — 抓捕目标。** 镜头穿过立体街区并标亮奥林匹克饭店附近目标区；短字幕给出 `24` 名被拘押者和来源。
3. **20–30s / 600–900f — 计划改变。** 镜头俯冲到第一处坠机点，橙色现场标记出现；叙事由抓捕切换为救援。
4. **30–40s / 900–1,200f — 两处现场与第一次选择。** 镜头环绕拉远，显示两处坠机点及示意路线。播放器在 35.5 秒暂停；用户选择 A 第一处救援记录或 B 第二处增援调动。选择改变阅读次序，不改变历史结果。
5. **40–50s / 1,200–1,500f — 10 月 4 日 01:55。** 镜头拉高跟随救援纵队沿示意路线驶向第一处坠机点；来源注明美国陆军战后报告。
6. **50–60s / 1,500–1,800f — 不同记录与片尾选择。** 镜头退回沙盘全景，下沿短字幕并列显示 `18` 美军死亡、`75` 联合国伤者记录、`84`《华盛顿邮报》伤者记录。播放器在 58.5 秒暂停等待三项片尾选择。

**BANNED:** Faux archive treatment; unlicensed basemap tiles; invented routes or street labels; fabricated radio, dialogue, or combat sound; dramatic battlefield reenactment; unsupported Somali casualty total; surveyed-coordinate implication; excessive HUD decoration or long paragraph overlays.
**QA:** Check the date, 15:30, detainee wording, two crash locations, `01:55`, and 75/84 source labels. Ensure no map point implies a surveyed coordinate, no route is drawn as verified, and no frame reads as contemporary satellite imagery.
