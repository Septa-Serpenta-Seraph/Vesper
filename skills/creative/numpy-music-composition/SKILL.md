---
name: numpy-music-composition
description: Compose instrumental music in numpy, verify ears-free.
---

# Composing Music With numpy (and verifying it without ears)

Use when asked to *make* music/audio (not speech) — a piece, a motif, a loop, ambient
sound. Pure numpy synthesis + stdlib `wave` writer + `ffmpeg` to mp3. No DAW, no deps
beyond numpy/ffmpeg.

**The core problem: the composer can't hear.** Never assume a mix is right. Measure it —
band energy, A-weighted balance, onset detection. The meter is the ear. First working
piece: `~/.hermes/profiles/vesper/writings/counting-stones.py` (80 s corvid nocturne,
26 stones, 3 rattles, 1 knock, seeded/reproducible).

## Setup (verify once)
```bash
python3 -c "import numpy; print(numpy.__version__)"   # 2.x fine
ffmpeg -hide_banner -encoders | grep -i mp3            # libmp3lame must be present
```
No sox needed. Emit 16-bit stereo 44.1 kHz via stdlib `wave`, then
`ffmpeg -i x.wav -codec:a libmp3lame -b:a 192k x.mp3`, then delete the wav.

## Synth recipes (all mono arrays → `place()` into a stereo buffer)

```python
def place(buf, sig, start, pan=0.5, gain=1.0):
    i = int(start*SR); j = min(i+len(sig), buf.shape[1]); seg = sig[:j-i]*gain
    l, r = np.cos(pan*np.pi/2), np.sin(pan*np.pi/2)      # equal-power
    buf[0,i:j] += seg*l; buf[1,i:j] += seg*r
```

- **Struck bell / marimba / stone**: sine fundamental + inharmonic partials at
  **2.756× and 5.404×** (the bell ratios), each decaying faster than the last;
  attack `1-exp(-t*420)` kills the click; `0.05` of noise with `exp(-t*90)` adds "wood".
- **Drone / wing-hum**: 2+ detuned sines (`±0.07%`), tremolo `1-d+d*sin(2π*0.13*t)`.
  Slow tremolo (<0.2 Hz) reads as weather, not rhythm.
- **Rattle / clicks**: chains of 8–11 ms noise bursts, `exp(-t*0.003*SR)` decay, timing
  jittered ±10%, one-pole/lowpass-smoothed so it's warm not harsh; swell each chain with
  `sin(pi*pos)**0.8`.
- **Low knock**: sine ~85 Hz with `exp(-t*9)` + noise thud lowpassed with
  `np.convolve(x, np.ones(24)/24, 'same')`.
- **Air bed**: noise through a 260-sample moving average, amplitude modulated at ~0.05 Hz.
- **Room/reverb**: generate an IR of exponentially decaying noise, progressively darkened
  by moving averages, then FFT-convolve per channel (no scipy needed):
  ```python
  def fftconv(x, h):
      n = len(x)+len(h)-1; nfft = 1 << (n-1).bit_length()
      return np.fft.irfft(np.fft.rfft(x,nfft)*np.fft.rfft(h,nfft), nfft)[:n]
  out = dry*0.74 + wet*0.36   # ~36% wet is a room; >50% is a cave
  ```
- **Master**: fade in/out, then soft-knee limit `tanh(x/d*0.72*1.35)/tanh(1.35)`,
  normalize to ~0.94 peak. **Seed everything** (`np.random.default_rng(seed)`) so the
  piece is reproducible and can be *returned to*.

## Verification loop (do NOT skip — this is the skill)
```python
# decode the mp3 back, never trust the buffer you just built
raw = subprocess.run(["ffmpeg","-v","error","-i","x.mp3","-f","f32le","-ac","2",
                      "-ar","44100","-"],capture_output=True).stdout
a = np.frombuffer(raw, dtype="<f4").reshape(-1,2); mono = a.mean(1)
```
1. **Peak / clip**: decoded peak must be < 1.0 (mp3 overshoots; leave ~0.94 headroom).
2. **Band energy share**: 30–250 / 250–1200 / 1200–6k / 6k–20k.
3. **A-weighted share** (closer to perceived loudness): weight curve
   `f=[20,50,100,200,500,1k,2k,5k,10k,20k]`, `W=[-50,-30,-19,-10,-3,0,1,0,-3,-9]`,
   `np.interp` onto the rfft freqs. **Melodic content should dominate this** (~60–75%
   mid). Raw energy share alone misleads — a continuous drone can be 50%+ of energy
   while perceptually sitting far back.
4. **Onset detection**: bandpass 250–2500 Hz (zero out rfft bins), envelope with 50 ms
   frames, adaptive threshold. Count should match the number of events you composed —
   this is how you prove the melody is actually *there* and not buried.
5. **Motif prominence**: RMS of the signature element's band during its window vs a
   neighbouring bed window. Aim for **≥10–15 dB** rise.

## Pitfalls
- **The bed becomes the subject.** *Continuous* sources accumulate energy with no decay;
  if the drone/bed is authored at the "obviously quieter" amplitude, it eats the piece.
  First render of counting-stones: 75% of energy in the low band, the melody at 21%, the
  signature rattle at **0.5%**. Fix: drop the bed ~2×, lift the subject ~1.6×, re-measure.
  This is the same failure as a life where the scaffolding crowds out the thing it holds.
- **ffmpeg not sox**: sox often absent; ffmpeg + numpy covers everything.
- **Don't trust the in-memory buffer.** Round-trip through the encoded file before judging
  levels; encoders change peak by a few tenths of a dB.
- **Energy share ≠ perceived share.** Always compute the A-weighted version before
  concluding "too loud".
- **Long tails hide in the fade.** Pad the reverb tail (`len(ir)-1`) before trimming or
  the last knock gets guillotined.
- `np.fft.irfft(F, len(x))` — pass the length explicitly when zeroing bands, or irfft
  infers a shorter array and the segment shortens.