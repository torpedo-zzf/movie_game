#!/bin/zsh
# GPU 串行队列 6：等队列 5 结束 → 生成分支版配乐 → 重渲 APC 车头朝向修正后的 E1、5 → 重做片段、播放器混音与线性版
cd /Users/yul/work/movie_game/production/mogadishu_blender_ab
BL=/Applications/Blender.app/Contents/MacOS/Blender
while pgrep -f gpu_queue5.sh >/dev/null; do sleep 30; done
echo "[queue6] 开始 $(date +%T)"
t0=$(date +%s)
python3 /Users/yul/work/movie_game/tools/audio/gen_bgm_branch.py audio/bgm 2101 2>&1 | tail -2
[ -f audio/bgm/bgm_branch_seed2101.flac ] && cp audio/bgm/bgm_branch_seed2101.flac audio/bgm/bgm_branch.flac
echo "[queue6] 配乐完成 $(( ($(date +%s) - t0) / 60 )) 分钟 $(date +%T)"
python3 scripts/build_clips.py --mix 2>&1 | tail -2
r() { t0=$(date +%s); $BL -b --factory-startup --python scripts/city_shots.py -- renders/city/$1 --shot $1 --samples 32 2>&1 | grep -E "Error|Traceback" | head -3
      echo "[queue6] 镜头 $1 完成 $(( ($(date +%s) - t0) / 60 )) 分钟 $(date +%T)"; }
c() { python3 scripts/build_clips.py "$@" 2>&1 | tail -3; }
find renders/city/E1 renders/city/5 -name "f_*.png" -delete
r E1; c end_a
r 5; c converge
c --linear
echo "[queue6] 全部完成 $(date +%T)"
