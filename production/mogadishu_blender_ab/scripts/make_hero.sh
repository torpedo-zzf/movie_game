#!/bin/zsh
# 组装基准镜头：调色（40% 强度 + 高光溢光）→ 混入分层声音 → 与旧 A（Three.js）/ B（Blender 初版）做顺序对比。
set -e
cd "${0:A:h}/.."
PY=../mogadishu_pilot/.venv-music/bin/python
FONT="/System/Library/Fonts/Hiragino Sans GB.ttc"
GRADE_MIX=0.4 HALATION=0.12 $PY -I scripts/grade.py renders/hero renders/hero_silent.mp4 405 1.06,1.0,0.9
# 声音：ComfyUI 生成的 Stable Audio Open 音效（audio/sao）+ ChatTTS 无线电台词 + MiniMax Music 3 配乐（audio/bgm）
RADIO=${RADIO:-audio/chattts/radio.wav}; BGM=${BGM:-$(ls audio/bgm/*.flac 2>/dev/null | head -1)}
$PY -I scripts/hero_mix.py audio/sao "${RADIO:--}" "${BGM:--}" audio/hero_mix.wav
ffmpeg -y -v error -i renders/hero_silent.mp4 -i audio/hero_mix.wav -af loudnorm=I=-16:TP=-1.5:LRA=11 -ar 48000 \
  -c:v copy -c:a aac -b:a 256k -shortest renders/hero.mp4
label() { echo "drawtext=fontfile='$FONT':text='$1':x=40:y=24:fontsize=30:fontcolor=0xF0E6D2:box=1:boxcolor=0x000000AA:boxborderw=12"; }
mat() { echo "pad=1920:1080:0:132:color=0x050606,$(label "$1")"; }
# 顺序对比：A 现行 → B 初版 → C 基准（有声），带遮幅
ffmpeg -y -v error -i renders/a_threejs.mp4 -i renders/b_blender.mp4 -i renders/hero.mp4 -filter_complex \
  "[0]$(mat 'A  现行 · Three.js')[a];[1]$(mat 'B  Blender 初版')[b];[2:v]$(mat 'C  基准镜头 v2 · 做旧车辆/骑楼战损/店招/人物')[c];\
   anullsrc=r=48000:cl=stereo,atrim=0:6[s];[s][2:a]concat=n=2:v=0:a=1[aud];[a][b][c]concat=n=3:v=1:a=0[v]" \
  -map "[v]" -map "[aud]" -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac -b:a 256k renders/abc_sequence.mp4
ls -la renders/hero.mp4 renders/abc_sequence.mp4
