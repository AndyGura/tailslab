"""
PS-ADPCM ("VAG") decoder: the sound format of the PlayStation and PlayStation 2 sound processors (NFS HP2 PS2
SOUND/JUKEBOXM.JBC), as described by https://psx-spx.consoledev.net/soundprocessingunitspu/ (SPU ADPCM).

A frame is 16 bytes, 28 samples: byte 0 filter (high nibble) and shift (low nibble), byte 1 flags (bit 0: the sound ends
here), then 14 bytes of 4-bit samples, low nibble first. A sample is `(nibble << 12 >> shift) + ((s1 * f0 + s2 * f1 +
32) >> 6)`, clamped to 16 bits, s1 / s2 the two previous samples, f0 / f1 the filter's coefficients. The hardware takes
shifts 13..15 as 9; filters above 4 are taken as 4.
"""

from typing import List

import numpy as np

PS_ADPCM_FILTERS = [(0, 0), (60, 0), (115, -52), (98, -55), (122, -60)]


def decode(data: bytes) -> np.ndarray:
    """Samples (int16) of a mono PS-ADPCM stream, up to the first frame with the end flag (that frame excluded: the
    streams end with a silent frame flagged 1 and the terminator frame `00 07 77 77..`)"""
    frames = np.frombuffer(data, dtype=np.uint8, count=len(data) // 16 * 16).reshape(-1, 16)
    ends = np.flatnonzero(frames[:, 1] & 1)
    if len(ends):
        frames = frames[: ends[0]]
    nibbles = np.empty((len(frames), 28), dtype=np.int32)
    nibbles[:, 0::2] = frames[:, 2:] & 0x0F
    nibbles[:, 1::2] = frames[:, 2:] >> 4
    nibbles = (nibbles ^ 8) - 8
    shifts = frames[:, 0] & 0x0F
    shifts[shifts > 12] = 9
    scaled = ((nibbles << 12) >> shifts[:, None].astype(np.int32)).tolist()
    filters = np.minimum(frames[:, 0] >> 4, 4).tolist()
    out = np.empty(len(frames) * 28, dtype=np.int16)
    s1 = s2 = 0
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
