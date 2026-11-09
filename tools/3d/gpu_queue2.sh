#!/bin/zsh
# GPU 串行队列 2：等队列 1 → FLUX 救援车队车辆参考图 → TRELLIS 转黑鹰/建筑/车辆（硬表面）→ 评估图
cd /Users/yul/work/movie_game/tools/3d
PROD=../../production/mogadishu_blender_ab
BL=/Applications/Blender.app/Contents/MacOS/Blender
while pgrep -f gpu_queue1.sh >/dev/null; do sleep 30; done
echo "[queue2] 开始 $(date +%T)"
V=$PROD/assets/gen3d/vehicles; H=$PROD/assets/gen3d/heli; C=$PROD/assets/gen3d/city; mkdir -p $V $H
mv $C/bh1_10_0.png $C/bh2_10_0.png $H/ 2>/dev/null
VEH="photograph, 45-degree front-left three-quarter view from slightly above, entire vehicle in frame with margin, plain light grey seamless studio background, soft even diffuse lighting, sharp focus, photorealistic, no people, no text"
g() { python3 -I comfy3d.py flux $V $1 $2 "$3" 1344 768 28 2>&1 | grep comfy; }
g apc1 221 "A Malaysian Army Condor wheeled armoured personnel carrier, 1993 United Nations UNOSOM mission, painted white with black UN letters, four large wheels, small turret, dusty, $VEH"
g tank1 222 "A Pakistani Army M48 Patton main battle tank, 1993 United Nations UNOSOM mission, painted white with black UN letters, dusty tracks, $VEH"
g truck1 223 "A US Army M923 five-ton cargo truck, 1993, desert tan paint, canvas covered cargo bed, dusty, $VEH"
# 黑鹰补图：bh1/bh2 都是正面视角，看不到尾梁，TRELLIS 会瞎猜尾部；补两张侧面/斜侧视角
HS="entire helicopter in frame with margin including the long tail boom and tail rotor, plain light grey seamless studio background, soft even diffuse lighting, sharp focus, photorealistic, no people, no text"
hg() { python3 -I comfy3d.py flux $H $1 $2 "$3" 1344 768 28 2>&1 | grep comfy; }
hg bh3 203 "A US Army MH-60L Black Hawk helicopter, 1993, matte dark olive drab paint, seen from the left side in full profile, nose pointing left, four main rotor blades, landing gear down, $HS"
hg bh4 204 "A US Army MH-60L Black Hawk helicopter, 1993, matte dark olive drab paint, three-quarter view from the front left and slightly above, fuselage angled diagonally so the side doors, tail boom and tail rotor are clearly visible, four main rotor blades, $HS"
echo "[queue2] FLUX 车辆完成 $(date +%T)"
t() { python3 -I comfy3d.py trellis $1 trellis_$2 $1/$2_10_0.png 42 1024 hard 2>&1 | grep -E "comfy|Error" | tail -2; }

for n in bh3 bh4; do t $H $n; done
for n in b5 b1 b2 b3 b4 b6; do t $C $n; done
for n in apc1 tank1 truck1; do t $V $n; done
echo "[queue2] TRELLIS 完成 $(date +%T)"
for f in $H/trellis_bh3 $H/trellis_bh4 $V/trellis_apc1 $V/trellis_tank1 $V/trellis_truck1 $C/trellis_b1 $C/trellis_b2 $C/trellis_b3 $C/trellis_b4 $C/trellis_b5 $C/trellis_b6; do
  n=$(basename $f); len=14; case $n in *bh*) len=19.8;; *apc1) len=6;; *tank1) len=9.3;; *truck1) len=7.9;; *b5) len=40;; esac
  $BL -b --factory-startup --python $PROD/scripts/eval_glb.py -- ${f}_300_1.glb $PROD/renders/gen3d/$n $len 48 2>&1 | grep "EVAL raw"
  ffmpeg -y -loglevel error $(for i in 0 1 2 3; do echo -i $PROD/renders/gen3d/${n}_$i.png; done) -filter_complex "[0][1]hstack[a];[2][3]hstack[b];[a][b]vstack,scale=1920:-1" $PROD/renders/gen3d/${n}_grid.jpg
done
echo "[queue2] 评估图完成 $(date +%T)"
