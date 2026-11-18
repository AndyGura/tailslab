"""
Sample names of the PSX TNFS car sound banks (`Z<car>.VB` / `.VH`, `ZS<car>`), and the engine rpm layers of the
Japanese disc. Verified in the executables:

- US (SLUS_002.04): the race start (0x8003ad34) starts the player's car bank samples 1 and 2 on channels 0 and 2; the
  engine routine `tnfs_sfx_engine_player` (0x8003c4d0, DOS 0x668ab) sets both to the pitch value rpm x 127 / (redline
  + 2000) (max 127) and crossfades them by the smoothed throttle t (table 0x800be4b4, 129 entries: sample 1 `[t / 2]`,
  sample 2 `[128 - t / 2]`): 1 engine on, 2 engine off. 3 is the horn (FUN_8003b020: channel 0xc, player 2 0xd, pitch
  value 64), 0x20 the gear shift (`sfx_oneshot_sample` 0x8003b3e4 for (13, 0), pitch value 64). In split screen
  (FUN_8003bcf0) both players load their `ZS<car>` bank, the same samples in one channel, without the gear shift.
- Japanese (SLPS_010.24): the race start (0x8003a40c) starts samples 1, 2 and 3 (3 not in split screen) on channels 0,
  2 and 12; the engine routine 0x8003bc24 sets the three to the same pitch value and gives each the volume of a
  table of its car by that pitch value (the car's pointers 0x800bd2f4 / 0x800bd324 / 0x800bd354, set by the bank
  loader 0x8003b354): a low, a mid and a high rpm layer, crossfaded by rpm only, the throttle plays no part. The horn
  routines are empty (0x8003a73c, 0x8003a74c): no player horn. 0x20 the gear shift.

A layer's volume (0..127) is `table[pitch value] x min(127, (distance volume + 1) x (pitch value + 20) / 128) / 128`
(the engine on / off loops of the US disc: the crossfade table's entry instead of `table[pitch value]`), then the
patch's volume applies (`TnfsPsxPatch`).
"""

import os
from typing import Dict, NamedTuple, Optional, Tuple

TNFS_PSX_CAR_BANK_NAMES = {1: 'engine_on', 2: 'engine_off', 3: 'honk', 0x20: 'gear'}
TNFS_SKYLINE_MEMORIAL_CAR_BANK_NAMES = {1: 'engine_low', 2: 'engine_mid', 3: 'engine_high', 0x20: 'gear'}
# the cars of the Japanese disc, by the names of their banks: Z<car> (ZS<car> in split screen); the R390 in the
# Warrior's slot keeps the US names ZWARRIOR / ZSWAR
TNFS_SKYLINE_MEMORIAL_CARS = ('KPGC', 'BCNR', 'KHGC', 'EHR', 'KBNR', 'KDR', 'PGC', 'S54B')
TNFS_SKYLINE_MEMORIAL_EXECUTABLE = 'SLPS_010.24'
TNFS_PSX_EXECUTABLE = 'SLUS_002.04'

# volume tables of the Japanese engine layers, 128 values by pitch value (SLPS_010.24, each car's own copy at the
# addresses of TNFS_SKYLINE_MEMORIAL_ENGINE_LAYER_ADDRESSES; traffic and cop slots use the KHGC tables)
_A0 = bytes.fromhex(
    '7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7c7874706c6864605c5854504c4844403c3834302c2824201c1814100c0804000000'
    '00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
    '000000000000000000000000000000000000000000000000'
)
_B0 = bytes.fromhex(
    '7f7f7f7f7f7f7f7f7f7f7f7f7f7f73695f554b413732323232323232323234383c4044484c5054585c6064686c7074787c7f7f7f'
    '7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f'
    '7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f'
)
_C0 = bytes.fromhex(
    '0000000000000000000000000000000000000000000000000000000000000000000000000000000102030405060708090a0b0c0d'
    '0e0f101112131415161718191a1b1c1d1e20222426282a2c2e30323436383a3c3e40424446484a4c4e5050505050505050505050'
    '505050505050505050505050505050505050505050505050'
)
_A1 = bytes.fromhex(
    '7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7c797673706d6a6764615e5b4e4b4845423f3c393633302d2a272421'
    '1e1b1815120f0c090603000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
    '000000000000000000000000000000000000000000000000'
)
_C1 = bytes.fromhex(
    '000000000000000000000000000000000000000000000000000000000000000000000000000000020406080a0c0e10121416181a'
    '1c1e20222426282a2c2e30323436383a3c3e40424446484a4c4e50525456585a5c5e606264646464646464646464646464646464'
    '646464646464646464646464646464646464646464646464'
)
_A2 = bytes.fromhex(
    '7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7e7c7a78767472706e6c6a68666462605e5c5a58565452504e4c4a48'
    '464442403e3c3a38363432302e2c2a28262422201e1c1a18161412100e0c0a080604020000000000000000000000000000000000'
    '000000000000000000000000000000000000000000000000'
)
_C2 = bytes.fromhex(
    '00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
    '0000020406080a0c0e10121416181a1c1e20222426282a2c2e30323436383a3c3e40424446484a4c4e5050505050505050505050'
    '505050505050505050505050505050505050505050505050'
)
_B1 = bytes.fromhex(
    '00000000000000000000000000000000000004080c1014181c2024282c3034383c4044484c5054585c6064686c7074787c7f7f7f'
    '7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f'
    '7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f'
)
_A3 = bytes.fromhex(
    '7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f786e645a50463c32281e140a0500000000000000000000000000000000000000'
    '00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
    '000000000000000000000000000000000000000000000000'
)
_B2 = bytes.fromhex(
    '7f7f7f7f7f7f7f7f7f7f7f7f7f7f73695f554b413742484e545a60666c72787e7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f'
    '7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f'
    '7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f'
)
_A4 = bytes.fromhex(
    '7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f'
    '7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f'
    '7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f'
)
_B3 = bytes.fromhex(
    '000000000000463c506473695f554b413732323232323232323234383c4044484c5054585c6064686c7074787c7f7f7f7f7f7f7f'
    '7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f'
    '7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f'
)
_C3 = bytes.fromhex(
    '00000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e20222426282a2c2e30323436383a3c3e40424446'
    '484a4c4e50525456585a5c5e60626466686a6c6e70727476787a7c7e808080808080808080808080808080808080808080808080'
    '808080808080808080808080808080808080808080808000'
)
TNFS_SKYLINE_MEMORIAL_ENGINE_LAYER_VOLUMES = {
    'KPGC': (_A0, _B0, _C0),
    'BCNR': (_A1, _B0, _C0),
    'KHGC': (_A1, _B0, _C1),
    'EHR': (_A2, _B0, _C2),
    'KBNR': (_A0, _B1, _C2),
    'KDR': (_A3, _B2, _C1),
    'PGC': (_A0, _B0, _C0),
    'S54B': (_A0, _B0, _C0),
    'WARRIOR': (_A4, _B3, _C3),
}
TNFS_SKYLINE_MEMORIAL_ENGINE_LAYER_ADDRESSES = {
    'KPGC': (0x800BC8AC, 0x800BC828, 0x800BC930),
    'BCNR': (0x800BCEDC, 0x800BCE58, 0x800BCF60),
    'KHGC': (0x800BC720, 0x800BC69C, 0x800BC7A4),
    'EHR': (0x800BCBC4, 0x800BCB40, 0x800BCC48),
    'KBNR': (0x800BCD50, 0x800BCCCC, 0x800BCDD4),
    'KDR': (0x800BC594, 0x800BC510, 0x800BC618),
    'PGC': (0x800BCA38, 0x800BC9B4, 0x800BCABC),
    'S54B': (0x800BD068, 0x800BCFE4, 0x800BD0EC),
    'WARRIOR': (0x800BD1F4, 0x800BD170, 0x800BD274),
}


class TnfsPsxCarBank(NamedTuple):
    """Names of the samples of a car bank by sample id, and the volume tables of the engine layers of the Japanese
    disc by sample id (empty for the US disc)"""

    names: Dict[int, str]
    layer_volumes: Dict[int, bytes]


def _is_skyline_memorial(directory: str, car: str) -> bool:
    """A bank of the Japanese disc: its executable is next to the bank (the US one: the US disc), else a bank of one
    of the Japanese cars"""
    try:
        names = {x.upper() for x in os.listdir(directory or '.')}
    except OSError:
        names = set()
    if TNFS_SKYLINE_MEMORIAL_EXECUTABLE in names:
        return True
    if TNFS_PSX_EXECUTABLE in names:
        return False
    return car in TNFS_SKYLINE_MEMORIAL_CARS


def tnfs_psx_car_bank(bank_path: str, sample_ids) -> Optional[TnfsPsxCarBank]:
    """The names of a car bank `Z<car>` (sample ids 1, 2, 3, 0x20) or split screen car bank `ZS<car>` (1, 2, 3), None
    for another bank"""
    directory, file_name = os.path.split(bank_path.replace('\\', '/'))
    stem = os.path.splitext(file_name)[0].upper()
    ids = set(sample_ids)
    if ids == {1, 2, 3, 0x20} and stem.startswith('Z'):
        car = stem[1:]
    elif ids == {1, 2, 3} and stem.startswith('ZS'):
        car = stem[2:]
    else:
        return None
    if not _is_skyline_memorial(directory, car):
        return TnfsPsxCarBank({i: TNFS_PSX_CAR_BANK_NAMES[i] for i in sorted(ids)}, {})
    tables = TNFS_SKYLINE_MEMORIAL_ENGINE_LAYER_VOLUMES.get('WARRIOR' if car in ('WARRIOR', 'WAR') else car)
    return TnfsPsxCarBank(
        {i: TNFS_SKYLINE_MEMORIAL_CAR_BANK_NAMES[i] for i in sorted(ids)},
        dict(zip((1, 2, 3), tables)) if tables else {},
    )
