# 用 ComfyUI 的 MiniMax Music 3（本地模型）生成 60 秒样片配乐：纯器乐，结构对齐样片的剧情段落。
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comfy_run import run, minimax_music3
OUT, SEED = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1003
CAPTION = """Global Metadata: Cinematic war-drama underscore for a documentary-style film about a 1993 urban battle. 92 BPM, D minor with Phrygian colour. Grim, tense and restrained rather than heroic; dread builds steadily, peaks, then collapses into a somber, exhausted night. No triumphalism, no cheerful elements.

Vocal Details: No vocals at all. Fully instrumental, no choir, no humming, no spoken words.

Arrangement: Intro: low sustained cello and contrabass drone with dry wind texture and a distant, sparse plucked oud-like string motif. Build: a pulsing low frame-drum and taiko ostinato enters with East African hand percussion, sub-bass hits on the downbeats, tremolo violins rising, metallic scrapes. Peak: full low brass clusters, driving percussion, dissonant string stabs, a sudden hard stop into near silence. Night section: very quiet, solo cello lament over a soft heartbeat pulse and distant low strings, sparse and cold. Outro: the drone thins out and ends unresolved on a single held low note."""
LYRICS = """[Intro]

[Instrumental]

[Build]

[Instrumental]

[Break]

[Instrumental]

[Outro]
"""
run(minimax_music3(CAPTION, LYRICS, 60.0, SEED), OUT, f"bgm_60s_seed{SEED}", timeout=5400)
