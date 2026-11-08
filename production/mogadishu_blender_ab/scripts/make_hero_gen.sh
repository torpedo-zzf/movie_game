#!/bin/zsh
# AI 悍马版基准镜头：与 v2 同一调色和同一混音，输出单独成片 + v2/AI 上下对比。
set -e
cd "${0:A:h}/.."
PY=../mogadishu_pilot/.venv-music/bin/python
FONT="/System/Library/Fonts/Hiragino Sans GB.ttc"
GRADE_MIX=0.4 HALATION=0.12 $PY -I scripts/grade.py renders/hero_gen renders/hero_gen_silent.mp4 405 1.06,1.0,0.9
ffmpeg -y -v error -i renders/hero_gen_silent.mp4 -i audio/hero_mix.wav -af loudnorm=I=-16:TP=-1.5:LRA=11 -ar 48000 \
  -c:v copy -c:a aac -b:a 256k -shortest renders/hero_gen.mp4
label() { echo "drawtext=fontfile='$FONT':text='$1':x=24:y=18:fontsize=26:fontcolor=0xF0E6D2:box=1:boxcolor=0x000000AA:boxborderw=10"; }
ffmpeg -y -v error -i renders/hero.mp4 -i renders/hero_gen.mp4 -filter_complex \
  "[0:v]scale=1280:-2,$(label 'v2 · 程序化悍马')[a];[1:v]scale=1280:-2,$(label 'AI 悍马 · FLUX→TRELLIS.2 本地生成')[b];[a][b]vstack[v]" \
  -map "[v]" -map 1:a -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a copy renders/hero_v2_vs_gen.mp4
ls -la renders/hero_gen.mp4 renders/hero_v2_vs_gen.mp4
