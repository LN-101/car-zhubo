# Broadcast speech parameters

## Speed

A speed factor between 0.5x and 2.0x (default 1.0x) maps to IndexTTS 2.5 `duration_factor = 1 / speed` for subsequently synthesized segments. Generation-side duration control preserves voice pitch, and the change applies from the next generated segment; already queued and playing audio is unaffected. The applied factor is recorded per broadcast. Acceptance: A4.

## Volume

A volume gain between 0 % and 200 % (default 100 %) is applied in the playback callback, so it affects the audio being played immediately, including the currently playing item. Samples are clipped to the PCM16 range. The applied gain is recorded. Acceptance: A4.

## Intonation

Intonation uses named tone presets with an intensity from 0 to 1 (default 0): neutral (no emotion vector), warm (亲切), energetic (活力) and steady (沉稳). A preset maps to the 8-dimension emotion vector order `[happy, angry, sad, afraid, disgusted, melancholic, surprised, calm]`, scaled by the intensity and passed as `emo_vector` for subsequently synthesized segments with `use_random=False`. The QwenEmotion text model stays unloaded. Intonation changes take effect from the next generated segment, and the applied vector is recorded. Acceptance: A4.

## Activation and ranges

Activation is hybrid: volume changes apply immediately to playing audio, while speed and intonation changes apply from the next generated segment, becoming audible within the bounded queue window. Controls enforce the stated ranges. Parameter values live for the session and are reused for the next broadcast until changed. Acceptance: A4, A6.
