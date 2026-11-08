# Blender A/B 试验｜车队贴地跟拍（样片 13.5–16.5 s）

- `renders/ab_stacked.mp4`：上 A（现行 Three.js）/ 下 B（Blender Cycles），同步 3 秒。
- `renders/ab_sequence.mp4`：带遮幅，A→B→A→B 顺序播放，12 秒。
- `renders/b_blender.mp4`：B 单独成片（1920×816，已调色）。

## 做法
- `scripts/convoy_shot.py`：Blender 5.2 无界面运行，全部程序化建模（无下载模型、无 AI 生成）。机位、车速、车距与 world.js 的 convoy-close 镜头逐帧对位。
- Cycles GPU（Metal）64 采样 + 降噪，180° 快门运动模糊，景深 f/2.8；体积尘霾、车轮扬尘与贴地风沙；AgX Punchy。约 40 s/帧，90 帧约 1 小时。
- `scripts/grade.py`：套用与 world.js 相同的胶片调色；B 额外做源白平衡 1.16/1.0/0.78 以接近 A 的暖调。
- `scripts/make_ab.sh`：截取样片母版同一镜头并组装对比。

## 结论（看图工具评估 + 亮度测量）
- B 更好：柔和间接光与软阴影、暗部有细节、车辆结构（轮毂、门缝、后视镜、窗）与材质层次更清楚、边缘更干净。
- B 更差：暖黄沙尘的压抑感偏弱、画面偏亮偏平；建筑仍偏干净；前景车辆过于完整明亮，少了 A 的剪影压迫感。
- 下一步若采用：调低曝光、加重暖色尘霾与逆光；墙面加脏污/破损贴图；引入真实车辆与建筑模型（需另行同意下载）。
