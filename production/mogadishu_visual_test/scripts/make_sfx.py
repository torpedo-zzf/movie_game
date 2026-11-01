# Deterministic procedural SFX for the 12 s style test (rotor, convoy engine, wind bed).
import numpy as np, soundfile as sf, sys
SR = 48000
out = sys.argv[1]
profile = sys.argv[2] if len(sys.argv) > 2 else 'test'
rng = np.random.default_rng(1993)

def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)):
        acc = (1 - a) * x[i] + a * acc; y[i] = acc
    return y

def env(t, pts):
    return np.interp(t, [p[0] for p in pts], [p[1] for p in pts])

def norm(x, peak):
    return x / (np.max(np.abs(x)) + 1e-9) * peak

dur = 60.0 if profile == 'pilot' else 12.0
t = np.arange(int(SR * dur)) / SR

# Rotor: 4 blades at ~4.3 rev/s -> ~17.2 Hz blade slap over filtered noise, plus turbine whine.
noise = rng.standard_normal(len(t))
body = lowpass(noise, 380)
phase = (t * 17.2) % 1.0
slap = np.exp(-phase * 9.0)
rotor = body * (0.35 + 1.6 * slap) + 0.04 * np.sin(2 * np.pi * 1180 * t + 0.4 * np.sin(2 * np.pi * 0.7 * t))
ROTOR = {'test': [(0, 0.15), (0.6, 0.75), (2.4, 1.0), (3.3, 0.5), (3.4, 0.08), (9.2, 0.08), (9.5, 0.45), (12, 0.6)],
         'pilot': [(0, 0.15), (2, 0.5), (5, 0.6), (5.05, 1.0), (10, 1.0), (10.05, 0.1), (16.5, 0.1), (16.55, 0.7), (25, 0.6), (25.05, 0.45), (30, 0.4), (30.05, 0.3), (40, 0.25), (40.05, 0.3), (60, 0.25)]}[profile]
rotor = norm(rotor, 1.0) * env(t, ROTOR)

# Convoy: diesel idle/rev (fundamental ~38 Hz with firing harmonics) + tyre/gravel noise.
f0 = 38 + 6 * np.sin(2 * np.pi * 0.31 * t)
ph = 2 * np.pi * np.cumsum(f0) / SR
engine = sum(np.sin(k * ph) / k for k in range(1, 9)) * (1 + 0.25 * np.sin(ph * 0.5))
gravel = lowpass(rng.standard_normal(len(t)), 1400) * 0.8
CONVOY = {'test': [(0, 0), (3.3, 0.0), (3.5, 0.18), (6.3, 0.42), (6.45, 1.0), (9.1, 1.0), (9.3, 0.35), (12, 0.2)],
          'pilot': [(0, 0), (10, 0), (10.1, 0.2), (13.4, 0.45), (13.55, 1.0), (16.4, 1.0), (16.55, 0.2), (20, 0.15), (20.05, 0), (43.4, 0), (43.55, 1.0), (46.9, 1.0), (47.05, 0.3), (50, 0.2), (50.05, 0), (60, 0)]}[profile]
convoy = norm(engine * 0.6 + gravel, 1.0) * env(t, CONVOY)

# Wind / distant city bed.
wind = lowpass(lowpass(rng.standard_normal(len(t)), 600), 600)
wind = norm(wind * (0.7 + 0.3 * np.sin(2 * np.pi * 0.13 * t)), 1.0) * 0.35

mix = 0.55 * rotor + 0.6 * convoy + wind
fade = env(t, [(0, 0), (0.25, 1), (dur - 0.4, 1), (dur, 0)])
mix = norm(mix * fade, 0.7)
sf.write(out, np.stack([mix, np.roll(mix, 24)], axis=1).astype(np.float32), SR, subtype="PCM_16")
