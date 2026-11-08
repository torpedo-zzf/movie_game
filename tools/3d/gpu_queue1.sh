#!/bin/zsh
# GPU 串行队列 1：等人物 TRELLIS 跑完 → 人物评估图 → IndexTTS2 试听 → FLUX 黑鹰/建筑参考图
cd /Users/yul/work/movie_game/tools/3d
PROD=../../production/mogadishu_blender_ab
BL=/Applications/Blender.app/Contents/MacOS/Blender
while pgrep -f "comfy3d.py trellis" >/dev/null; do sleep 30; done
echo "[queue] 人物 TRELLIS 完成 $(date +%T)"

for n in m2 m3 w1 w2 m4; do
  $BL -b --factory-startup --python $PROD/scripts/eval_glb.py -- $PROD/assets/gen3d/people/trellis_${n}_300_1.glb $PROD/renders/gen3d/trellis_$n 1.75 64 height 2>&1 | grep "EVAL raw"
  ffmpeg -y -loglevel error $(for i in 0 1 2 3; do echo -i $PROD/renders/gen3d/trellis_${n}_$i.png; done) -filter_complex "[0][1]hstack[a];[2][3]hstack[b];[a][b]vstack" $PROD/renders/gen3d/trellis_${n}_grid.jpg
done
echo "[queue] 人物评估图完成 $(date +%T)"

cd ../audio/index-tts
PYTORCH_ENABLE_MPS_FALLBACK=1 uv run python ../indextts_gen.py /Users/yul/work/movie_game/production/mogadishu_blender_ab/audio/indextts/audition audition \
  demo/examples/voice_05.wav demo/examples/voice_06.wav demo/examples/voice_09.wav demo/examples/voice_11.wav \
  /Users/yul/work/movie_game/production/mogadishu_blender_ab/audio/chattts/narr_7/scene-01.wav 2>&1 | grep -E "\[tts\]|Error|error"
echo "[queue] TTS 试听完成 $(date +%T)"
cd ../../3d

O=$PROD/assets/gen3d/city; mkdir -p $O
HELI="photograph, 45-degree front-left three-quarter view from slightly above, entire aircraft in frame with margin, plain light grey seamless studio background, soft even diffuse lighting, sharp focus, photorealistic, no people, no text"
BLD="isolated single building on plain light grey seamless studio background, 45-degree three-quarter view from slightly above showing the roof and two facades, entire building in frame with margin, soft even diffuse overcast lighting, sharp focus, photorealistic, no people, no vehicles, no text"
g() { python3 -I comfy3d.py flux $O $1 $2 "$3" $4 $5 28 2>&1 | grep comfy; }
g bh1 201 "A US Army MH-60L Black Hawk helicopter, 1993, matte dark olive drab paint, four main rotor blades and tail rotor intact, landing gear down, $HELI" 1344 768
g bh2 202 "A US Army UH-60 Black Hawk helicopter, 1993, matte dark green military paint, four main rotor blades and tail rotor intact, fixed wheels, $HELI" 1344 768
g b1 211 "Single-storey whitewashed concrete house in Mogadishu Somalia 1993, flat roof with low parapet, small barred windows, blue painted steel door, peeling plaster, dust stains at the base, $BLD" 1024 1024
g b2 212 "Two-storey ochre plastered house in Mogadishu Somalia 1993, flat roof with water tank, small balcony with iron railing, weathered stained walls, $BLD" 1024 1024
g b3 213 "Walled residential compound in Mogadishu Somalia 1993, high white plastered perimeter wall with rusty metal gate, single-storey house inside with rusty corrugated iron roof, $BLD" 1024 1024
g b4 214 "Three-storey Italian colonial era concrete apartment block in Mogadishu Somalia 1993, arched windows and shutters, faded cream plaster with damage and bullet scars, flat roof, $BLD" 1024 1024
g b5 215 "Five-storey 1980s concrete hotel building in Mogadishu Somalia 1993, white painted facade with regular rows of windows, flat roof with rooftop structures, weathered, $BLD" 1024 1024
g b6 216 "Row of three small single-storey shops in Mogadishu Somalia 1993, rusty corrugated metal shutters, faded hand-painted wall colors, flat roofs, $BLD" 1024 1024
echo "[queue] FLUX 参考图完成 $(date +%T)"
