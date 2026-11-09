#!/bin/zsh
# GPU 串行队列 5：正式渲染（1920×816，32 spp）。按节点顺序渲染，每个节点的镜头齐了就合成该节点片段，替换播放器占位。
# 可重跑：已渲染帧会跳过（先清掉中断留下的 0 字节占位帧）。
cd /Users/yul/work/movie_game/production/mogadishu_blender_ab
BL=/Applications/Blender.app/Contents/MacOS/Blender
find renders/city renders/hero_final -name "f_*.png" -size 0 -delete 2>/dev/null
r() { t0=$(date +%s); $BL -b --factory-startup --python scripts/city_shots.py -- renders/city/$1 --shot $1 --samples 32 2>&1 | grep -E "Error|Traceback" | head -3
      echo "[queue5] 镜头 $1 完成 $(( ($(date +%s) - t0) / 60 )) 分钟 $(date +%T)"; }
c() { python3 scripts/build_clips.py "$@" 2>&1 | tail -3; }
echo "[queue5] 开始 $(date +%T)"
for S in 1 2a; do r $S; done
t0=$(date +%s); $BL -b --factory-startup --python scripts/convoy_hero.py -- renders/hero_final --samples 32 \
  --gen-humvee assets/gen3d/humvee/trellis_s5_300_1.glb --gen-people assets/gen3d/people 2>&1 | grep -E "Error|Traceback" | head -3
echo "[queue5] 悍马贴地镜头完成 $(( ($(date +%s) - t0) / 60 )) 分钟 $(date +%T)"
for S in 2c 3 4; do r $S; done; c trunk
r L1; c loop1
r 4A; c site_a
r 5; c converge
r 6; c dawn
r L2; c loop2
r E1; c end_a
c --linear
r 4B; c site_b
r E2; c end_b
r E3; c end_c
echo "[queue5] 全部完成 $(date +%T)"
