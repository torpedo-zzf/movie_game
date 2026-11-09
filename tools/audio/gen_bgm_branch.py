# 分支版配乐：MiniMax Music 3（本地 ComfyUI）。旧的 60 秒样片配乐按旧剪辑卡点（鼓点渐强、高潮、急停），
# 放进分支播放器后会循环、被选择打断，节奏和旁白对不上。这里改成无鼓点、无高潮的克制铺底，任何位置切断/循环都不突兀。
# 用法：python3 gen_bgm_branch.py <输出目录> [seed] [quiet|epic]
# epic：用户反馈克制版“没有代入感”，改成《黑鹰坠落》式战争片配乐——人声吟唱、低沉鼓组、电子脉冲与弦乐持续推进
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comfy_run import run, minimax_music3
OUT, SEED = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 2101
STYLE = sys.argv[3] if len(sys.argv) > 3 else "quiet"
CAPTION = """Global Metadata: Restrained documentary underscore for a sober historical film about a 1993 urban battle, played quietly under a calm spoken narration. Very slow, around 60 BPM but with no audible beat. D minor, modal and unresolved. Mournful, contemplative and still; no tension build, no climax, no triumph, no action-movie energy. The mood stays constant from start to end so it can loop seamlessly.

Vocal Details: No vocals at all. Fully instrumental, no choir, no humming, no spoken words.

Arrangement: Long sustained low string drone (cello and contrabass, soft, sul tasto) with a slowly breathing synth pad underneath. Every few bars a sparse, distant plucked oud-like note or a soft low piano note, with lots of space and reverb. Occasional faint high violin harmonic. No drums, no percussion, no taiko, no pulse, no risers, no hits, no brass, no sudden stops. Dynamics stay low and even throughout, leaving the midrange free for narration."""
LYRICS = """[Intro]

[Instrumental]

[Instrumental]

[Instrumental]

[Outro]
"""
EPIC = """Global Metadata: Epic modern war film score in the style of the Black Hawk Down soundtrack, for an interactive film about the 1993 battle of Mogadishu, Somalia. Around 90 BPM, D minor, dark, urgent and immersive. Relentless forward momentum and rising dread, with a mournful human soul underneath. The intensity stays high and steady from the first bars to the end, with no long silence, no sudden stop and no final cadence, so it can loop seamlessly under a spoken narration.

Vocal Details: Wordless soulful East African / Arabic style vocal chant, a single male voice with long melismatic lines, distant and reverberant, sitting low in the mix. No lyrics, no English words.

Arrangement: Driving low ethnic percussion (large frame drums, deep taiko-like hits, djembe) in a steady propulsive pattern, a pulsing dark electronic bassline and synth arpeggio, aggressive low string ostinato (cellos and basses, spiccato), sustained distorted guitar drone and brass swells, occasional oud phrases. Big and cinematic but the midrange stays clear for narration; no bright lead melody instrument, no cymbal crashes on every bar."""
EPIC_LYRICS = """[Intro]

[Instrumental]

[Build]

[Instrumental]

[Instrumental]

[Outro]
"""
if STYLE == "epic": CAPTION, LYRICS = EPIC, EPIC_LYRICS
run(minimax_music3(CAPTION, LYRICS, 120.0, SEED), OUT, f"bgm_branch_{STYLE}_seed{SEED}" if STYLE != "quiet" else f"bgm_branch_seed{SEED}", timeout=4 * 3600)
