# 视觉升级交接｜摩加迪沙交互影游

更新时间：2026-11-01

## 当前目标

用户认为现有样片“大体结构差不多，但视觉效果还是不答预期”，要求提高精细度，并明确了方向：

- 建筑要更细，减少方块模型和游戏感。
- 参考电影《黑鹰坠落》（Black Hawk Down）的影像质感，但只借鉴构图、光线、色彩和镜头节奏，不直接复用电影画面。
- 镜头远近按剧情切换：沙盘全景建立空间，街区近景解释路线，车辆近景强化行动感，再回到全景交代态势。
- 地图与史实资料由制作方自行网上查找。
- 可使用本机 ComfyUI 的 Qwen Image 2.1 生成概念图、材质和氛围素材；建筑、黑鹰、军车、地面及烟尘由制作方继续建模/生成。
- 先做风格验证镜头，确认质感后再替换完整 60 秒；现有 60 秒 MP4 仅作上一版，不代表用户验收。

## 已核实史料

1. [U.S. Army, US Forces Somalia After Action](https://api.army.mil/e2/c/downloads/314322.pdf)：报告称 1993-10-03 约 15:30 行动开始，目标地点在 Olympic Hotel 附近；24 名索马里人被抓获；第一架黑鹰坠落在目标约三个街区外；另一架坠落在第一处以南不到一英里；援军纵队于 10 月 4 日 01:55 抵达第一处坠机点。报告 Map 3 标出了街道、目标区、两处坠机点、机场、港口等地理关系。
2. [U.S. Army Center of Military History, *The U.S. Army in Somalia, 1992–1994* (GovInfo PDF)](https://www.govinfo.gov/content/pkg/GOVPUB-D110-PURL-LPS58876/pdf/GOVPUB-D110-PURL-LPS58876.pdf)：Map 10 为 10 月 3–4 日战斗态势图，包含机场、新港、Olympic Hotel、两处坠机点、路线进出方向等信息。在线文本注明该版权方另有部分地图不提供在线查看；使用公开可见图时保留来源标注，不把示意图包装成精确测绘。
3. [Los Angeles Times：与《黑鹰坠落》摄影指导 Slawomir Idziak 的访谈](https://www.latimes.com/archives/la-xpm-2002-mar-24-ca-hart24-story.html)：Idziak 讨论了影片色彩、滤镜和照明决策。可借鉴偏尘土暖色、非平光照明和有方向性的光影；这是从访谈与影片画面做的视觉归纳，不作为史实来源。

## 本机生成与建模能力

- Comfy Desktop 正在运行，浏览器已打开本机 `http://127.0.0.1:8188/`。
- ComfyUI 模型库可见 `qwen_image_2.1_int8_convrot`。
- ComfyUI 模型库可见 `trellis_2_int8_convrot`；模板库搜索到 `Pixal3D & TRELLIS.2：图像到模型`。节点分类中有 3D 和 `保存GLB`。尚未实际跑通该模板，后续 Agent 需验证输入/输出节点和 GLB 质量。
- Blender 已运行；工程现有 HyperFrames 使用本地 Three.js 0.180.0。
- ComfyUI 中原有 `Unsaved Workflow` 是用户自己的工作流，页面当时显示 1 个正在运行任务。不要覆盖、清空或取消它；新工作应新建单独工作流/标签。ComfyUI 当前任务队列未被本项目改动。
- Qwen Image 适合生成概念图、贴图/表面参考和气氛底图；不要把它直接当作带正确透视/连续街区的可动画 3D 场景。路线、地点、车辆路径应保持在 3D 场景中控制。

## 建议执行路径

1. 先基于 Army Map 3 / CMH Map 10 整理一张仅供制作使用的空间关系图，标出目标区、Crash Site #1/#2、机场、新港、National Street、Shalalawi Street；最终影片仍注明“非比例示意”。
2. 做 10–12 秒风格验证：全景建立城市 → 中近景穿过更细的街区 → 车辆与地面尘土近景 → 拉回态势图。相机远近变化跟随叙事，不持续用同一种等距视角。
3. 在 ComfyUI 新建独立 Qwen Image 2.1 文生图工作流，先生成无字的街区材质/概念关键帧；然后尝试 Pixal3D & TRELLIS.2 转成建筑/车辆网格并导出 GLB。若输出网格形体或拓扑不合用，改由 Blender/Three.js 制作可控模型，生成图仅用于材质与氛围。
4. 提升模型细节：真实比例的门窗、阳台、屋顶设备、墙面磨损、路缘/路障和车辆轮胎；材质使用粗糙度/法线细节，控制建筑重复感。避免过度科幻 HUD、鲜艳描边和均匀方块。
5. 将相机、车辆和雾尘制作成可确定性 seek 的动画，再先渲染一个短镜头审阅；用户认可后才重做全片。

## 当前工程文件

- HyperFrames 项目：本目录 `index.html`、`sandtable.js`、`player.html`、`player.js`。
- 上一版 60 秒视频：`renders/mogadishu_sample_60s.mp4`（当前不满足新的视觉标准，后续确认风格后替换）。
- 上一版预览图：`renders/choice-point-1.png`、`renders/choice-point-2.png`。
- 原互动节点仍在播放器 35.5 秒与 58.5 秒；继续保留。
- 旁白使用本地离线中文普通话；继续使用中国大陆标准普通话。

## 交互与安全边界

- 本次仅检查了 ComfyUI 模型/模板列表；没有生成图片、改变工作流、保存用户的 Comfy 工作流或触碰运行中的任务。
- 已创建一个仅交接用的新浏览器标签页。原 ComfyUI 页面保持在本机。
- 所有战术路线均为示意；地图来源和叙述口径以公开官方报告为准。电影镜头只作视觉参考，不作为史料。
