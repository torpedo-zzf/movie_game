#!/bin/zsh
# 占位片段：每个节点一段带标签的色块视频，用来在正式渲染出来之前测试分支播放器。正式片段由 build_clips.sh 覆盖。
cd ${0:a:h}/clips
F=/System/Library/Fonts/STHeiti\ Medium.ttc
mk() { ffmpeg -y -loglevel error -f lavfi -i "color=c=${3}:s=1920x1080:r=30:d=${2}" -f lavfi -i "sine=f=${4}:d=${2}" \
  -vf "drawtext=fontfile='$F':text='$5':fontcolor=white:fontsize=64:x=(w-tw)/2:y=(h-th)/2-40,drawtext=fontfile='$F':text='%{pts\:hms}':fontcolor=white@0.6:fontsize=36:x=(w-tw)/2:y=h/2+60" \
  -c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 96k -shortest $1.mp4; }
mk trunk 35.5 0x3a3226 220 "主干 0–35.5s（镜头 1–4）"
mk loop1 4 0x2a3a3a 0 "等待循环 1（两根烟柱）"
mk site_a 10 0x5a3a20 260 "分支 A：第一处现场"
mk site_b 10 0x20405a 300 "分支 B：第二处现场"
mk converge 10 0x101828 180 "汇合 · 凌晨 1 点 55 分 夜间车队"
mk dawn 7.5 0x6a4a30 240 "黎明全景 + 伤亡数字"
mk loop2 4 0x5a4030 0 "等待循环 2（黎明）"
mk end_a 8 0x4a4a2a 330 "结尾：任务与救援"
mk end_b 8 0x4a2a3a 350 "结尾：城市与平民"
mk end_c 8 0x2a3a4a 370 "结尾：政策后果"
