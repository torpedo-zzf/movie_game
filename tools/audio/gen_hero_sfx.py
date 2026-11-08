# 用 ComfyUI 的 Stable Audio Open 1.0 为基准镜头生成音效分层（每层 8 秒，取用其中 3 秒）。
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comfy_run import run, stable_audio
OUT = sys.argv[1]
LAYERS = {
    "engine": "Close-up recording of a military Humvee turbo diesel V8 engine driving slowly, deep rumbling exhaust, mechanical clatter, steady low speed, field recording, no music",
    "tyres": "Heavy off-road truck tires rolling slowly over gravel and sandy dirt road, crunching stones and grit, close microphone, field recording",
    "bumps": "Military vehicle driving over potholes, heavy suspension thuds and metal clunks, rattling jerry cans and equipment boxes, chains clinking, close recording",
    "street": "Hot windy African city street ambience, dry wind gusts, distant crowd murmur and shouting voices, distant dogs, dusty, outdoor field recording",
    "heli": "Distant military helicopter rotor blades thumping overhead, Black Hawk flyover far away, low thudding wash, outdoor",
    "radio": "Military handheld radio static burst, squelch click, short walkie talkie noise, no voice",
}
for i, (k, p) in enumerate(LAYERS.items()):
    run(stable_audio(p, 8.0, 1993 + i), OUT, k)
