#!/bin/zsh
# GPU 串行队列 3：等队列 2 → IndexTTS2 正式旁白（用户选定：音色 B = voice_06，情绪 restrained 克制）
cd /Users/yul/work/movie_game/tools/audio/index-tts
while pgrep -f "gpu_queue[12].sh" >/dev/null; do sleep 30; done
echo "[queue3] 开始 $(date +%T)"
PYTORCH_ENABLE_MPS_FALLBACK=1 uv run python ../indextts_gen.py /Users/yul/work/movie_game/production/mogadishu_blender_ab/audio/indextts/final full \
  demo/examples/voice_06.wav restrained 2>&1 | grep -E "\[tts\]|Error|error"
echo "[queue3] 正式旁白完成 $(date +%T)"
