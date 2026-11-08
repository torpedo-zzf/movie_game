#!/bin/zsh
# 组装 A/B 对比：上 = 现行 Three.js（样片 13.5–16.5 s），下 = Blender Cycles；另出顺序播放版（A 后接 B）。
set -e
cd "${0:A:h}/.."
PILOT=../mogadishu_pilot/renders/mogadishu_sample_60s_master.mp4
FONT="/System/Library/Fonts/Hiragino Sans GB.ttc"
mkdir -p renders
# A：从样片母版截取同一镜头，裁去上下遮幅
ffmpeg -y -v error -ss 13.5 -t 3 -i "$PILOT" -vf "crop=1920:816:0:132" -an -c:v libx264 -crf 16 -pix_fmt yuv420p renders/a_threejs.mp4
# B：Blender 帧 → 同款调色
../mogadishu_pilot/.venv-music/bin/python -I scripts/grade.py renders/convoy renders/b_blender.mp4 405 1.16,1.0,0.78
# 上下对比（1920×1080）
label() { echo "drawtext=fontfile='$FONT':text='$1':x=40:y=24:fontsize=30:fontcolor=0xF0E6D2:box=1:boxcolor=0x000000AA:boxborderw=12"; }
ffmpeg -y -v error -i renders/a_threejs.mp4 -i renders/b_blender.mp4 -filter_complex \
  "[0]scale=1270:540,$(label 'A  现行 · Three.js 实时渲染')[a];[1]scale=1270:540,$(label 'B  试验 · Blender Cycles 离线渲染')[b];[a][b]vstack,pad=1920:1080:325:0:color=0x050606[v]" \
  -map "[v]" -c:v libx264 -crf 18 -pix_fmt yuv420p renders/ab_stacked.mp4
# 顺序版：带遮幅，A 3 s → B 3 s，各循环两遍
mat() { echo "pad=1920:1080:0:132:color=0x050606,$(label "$1")"; }
ffmpeg -y -v error -i renders/a_threejs.mp4 -i renders/b_blender.mp4 -filter_complex \
  "[0]$(mat 'A  现行 · Three.js'),split[a1][a2];[1]$(mat 'B  试验 · Blender Cycles'),split[b1][b2];[a1][b1][a2][b2]concat=n=4:v=1:a=0[v]" \
  -map "[v]" -c:v libx264 -crf 18 -pix_fmt yuv420p renders/ab_sequence.mp4
ls -la renders/*.mp4
