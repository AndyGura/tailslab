"""
PS-ADPCM ("VAG") decoder: the sound format of the PlayStation and PlayStation 2 sound processors (NFS HP2 PS2
SOUND/JUKEBOXM.JBC, PSX TNFS sound banks `.VB`), as described by https://psx-spx.consoledev.net/soundprocessingunitspu/
(SPU ADPCM).

A frame is 16 bytes, 28 samples: byte 0 filter (high nibble) and shift (low nibble), byte 1 flags (bit 0 loop end: the
sound ends after this frame, bit 1 repeat: it then goes back to the loop start instead of stopping, bit 2 loop start),
then 14 bytes of 4-bit samples, low nibble first. A sample is `(nibble << 12 >> shift) + ((s1 * f0 + s2 * f1 +
32) >> 6)`, clamped to 16 bits, s1 / s2 the two previous samples, f0 / f1 the filter's coefficients. The hardware takes
shifts 13..15 as 9; filters above 4 are taken as 4.
"""

from typing import List, NamedTuple, Optional

import numpy as np

PS_ADPCM_FILTERS = [(0, 0), (60, 0), (115, -52), (98, -55), (122, -60)]
PS_ADPCM_FRAME_SAMPLES = 28
# flags (byte 1 of a frame) the PlayStation SPU reads
FLAG_LOOP_END = 0x01
FLAG_LOOP_REPEAT = 0x02
FLAG_LOOP_START = 0x04


def _frames(data: bytes) -> np.ndarray:
    return np.frombuffer(data, dtype=np.uint8, count=len(data) // 16 * 16).reshape(-1, 16)


def decode(data: bytes) -> np.ndarray:
    """Samples (int16) of a mono PS-ADPCM stream, up to the first frame with the end flag (that frame excluded: the
    streams end with a silent frame flagged 1 and the terminator frame `00 07 77 77..`)"""
    frames = _frames(data)
    ends = np.flatnonzero(frames[:, 1] & FLAG_LOOP_END)
    if len(ends):
        frames = frames[: ends[0]]
    return _decode_frames(frames)


class SpuSample(NamedTuple):
    """What a PlayStation SPU voice plays of a sample: `samples` (int16) up to the end of the frame with the first
    loop end flag, and the index of the sample it then goes back to (`loop_start`, None: the voice stops)"""

    samples: np.ndarray
    loop_start: Optional[int]


# passes through a loop decoded at most until its samples stay the same (the filter history converges in a few frames)
_LOOP_PASSES = 8


def decode_spu_sample(data: bytes) -> SpuSample:
    """A sample as the SPU plays it from its first frame (psx-spx "SPU ADPCM Samples"): every frame up to and
    including the first one with the loop end flag (bit 0); with the repeat flag (bit 1) in that frame the voice goes
    back to the repeat address, the start of the last frame before it with the loop start flag (bit 2), else it is
    released and falls silent. Without a loop end flag: every frame, no loop. The SPU keeps the two previous samples
    of the filters across the jump, so the loop sounds seamless only decoded after its own end: the loop's samples are
    those of the passes after the first (decoded again from the end of the pass before until they stay the same; the
    first pass, after the frames before the loop, differs in its first samples)"""
    frames = _frames(data)
    ends = np.flatnonzero(frames[:, 1] & FLAG_LOOP_END)
    loop_start_frame = None
    if len(ends):
        end = ends[0]
        frames = frames[: end + 1]
        if frames[end, 1] & FLAG_LOOP_REPEAT:
            starts = np.flatnonzero(frames[:, 1] & FLAG_LOOP_START)
            loop_start_frame = int(starts[-1]) if len(starts) else 0
    samples = _decode_frames(frames)
    if loop_start_frame is None:
        return SpuSample(samples, None)
    loop_start = loop_start_frame * PS_ADPCM_FRAME_SAMPLES
    loop = samples[loop_start:]
    for _ in range(_LOOP_PASSES):
        again = _decode_frames(frames[loop_start_frame:], int(loop[-1]), int(loop[-2]) if len(loop) > 1 else 0)
        if np.array_equal(again, loop):
            break
        loop = again
    return SpuSample(np.concatenate([samples[:loop_start], loop]), loop_start)


def _decode_frames(frames: np.ndarray, s1: int = 0, s2: int = 0) -> np.ndarray:
    """Samples of PS-ADPCM frames, `s1` / `s2` the two samples before them"""
    nibbles = np.empty((len(frames), 28), dtype=np.int32)
    nibbles[:, 0::2] = frames[:, 2:] & 0x0F
    nibbles[:, 1::2] = frames[:, 2:] >> 4
    nibbles = (nibbles ^ 8) - 8
    shifts = frames[:, 0] & 0x0F
    shifts[shifts > 12] = 9
    scaled = ((nibbles << 12) >> shifts[:, None].astype(np.int32)).tolist()
    filters = np.minimum(frames[:, 0] >> 4, 4).tolist()
    out = np.empty(len(frames) * 28, dtype=np.int16)
    i = 0
    for frame_samples, filter_index in zip(scaled, filters):
        f0, f1 = PS_ADPCM_FILTERS[filter_index]
        for sample in frame_samples:
            sample += (s1 * f0 + s2 * f1 + 32) >> 6
            sample = -32768 if sample < -32768 else 32767 if sample > 32767 else sample
            out[i] = sample
            i += 1
            s2, s1 = s1, sample
    return out


def deinterleave(data: bytes, channels: int, interleave: int, num_bytes: int) -> List[bytes]:
    """The streams of `channels` channels stored in blocks of `interleave` bytes per channel, one channel after
    another. `num_bytes` is the wave data of all channels without padding: the remainder after the whole blocks is split
    evenly between the channels, each part at the start of its channel's block of the last (zero padded) round"""
    round_length = channels * interleave
    whole = num_bytes // round_length * round_length
    tail = (num_bytes - whole) // channels
    rounds = np.frombuffer(data, dtype=np.uint8, count=whole).reshape(-1, channels, interleave)
    return [
        rounds[:, channel].tobytes() + data[whole + channel * interleave : whole + channel * interleave + tail]
        for channel in range(channels)
    ]


def decode_interleaved(data: bytes, channels: int, interleave: int, num_bytes: int) -> bytes:
    """16-bit little endian PCM, channels interleaved, of interleaved PS-ADPCM streams (see `deinterleave`), as long
    as the shortest channel"""
    decoded = [decode(x) for x in deinterleave(data, channels, interleave, num_bytes)]
    length = min(len(x) for x in decoded)
    return np.stack([x[:length] for x in decoded], axis=1).astype('<i2').tobytes()
