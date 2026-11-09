#!/bin/zsh
# GPU 串行队列 4：等队列 1–3 → 全部 14 个城市镜头 + 悍马贴地镜头各渲染一张测试帧（50% 分辨率，16 spp），供自审
cd /Users/yul/work/movie_game/production/mogadishu_blender_ab
BL=/Applications/Blender.app/Contents/MacOS/Blender
while pgrep -f "gpu_queue[123].sh" >/dev/null; do sleep 30; done
echo "[queue4] 开始 $(date +%T)"
typeset -A MID; MID=(1 151 2a 353 2c 548 3 760 4 991 L1 1126 4A 1231 4B 1231 5 1351 6 1613 L2 1786 E1 1846 E2 1846 E3 1846)
for S in 1 2a 2c 3 4 L1 4A 4B 5 6 L2 E1 E2 E3; do
  t0=$(date +%s)
  $BL -b --factory-startup --python scripts/city_shots.py -- renders/city_test/$S --shot $S --still $MID[$S] --samples 16 --pct 50 2>&1 | grep -E "Error|Traceback|HELI|CITY instances" | head -4
  echo "[queue4] $S still $MID[$S] $(( $(date +%s) - t0 ))s"
done
# 3 坠落关键帧：被击中、打转、坠地
for F in 676 718 783; do $BL -b --factory-startup --python scripts/city_shots.py -- renders/city_test/3 --shot 3 --still $F --samples 16 --pct 50 2>&1 | grep -E "Error|Traceback" | head -2; done
$BL -b --factory-startup --python scripts/convoy_hero.py -- renders/city_test/hero --still 45 --samples 16 --pct 50 \
  --gen-humvee assets/gen3d/humvee/trellis_s5_300_1.glb --gen-people assets/gen3d/people 2>&1 | grep -E "Error|Traceback" | head -2
echo "[queue4] 测试帧完成 $(date +%T)"
