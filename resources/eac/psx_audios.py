"""
PlayStation TNFS (SLUS-00204, and the Japanese SLPS-01024) sound banks: EA's own PlayStation sound library format, a
pair of files per bank, `Z<bank>.VH` (`TnfsPsxPatchBank`, magic "BXSP": the patches, sound settings by sample id) and
`Z<bank>.VB` (`TnfsPsxVagBank`, magic "Bgav": the samples, each a Sony "VAGp" header with SPU ADPCM data). Not Sony's
VAB format ("pBAV"), though the file extensions are the same. Addresses: the US executable SLUS_002.04, the Japanese
SLPS_010.24 has the same sound library at other addresses (`sfx_voice_start` 0x800b4350 there).
"""

from typing import Dict, Optional

from library.context import ReadContext, WriteContext
from library.read_blocks import (
    ArrayBlock,
    BytesBlock,
    DeclarativeCompoundBlock,
    IntegerBlock,
    TrailingOptionalBlock,
    UTF8Block,
)
from library.read_blocks.misc.value_validators import Eq, Or
from resources.eac.psx import CRCF_FOOTER_LENGTH, PsxCrcFooter, crc_footer_at, with_crc_footer

# SPU pitch of a voice playing a sample at 44100 Hz (`VxPitch`); the SPU plays no faster than 0x4000 (psx-spx: higher
# values are taken as 0x4000)
PSX_SPU_PITCH_44100 = 0x1000
PSX_SPU_MAX_PITCH = 0x4000
PSX_SPU_SAMPLE_RATE = 44100
TNFS_PSX_SAMPLE_IDS = 128
TNFS_PSX_PATCH_BANK_HEADER_LENGTH = 0x10 + TNFS_PSX_SAMPLE_IDS
TNFS_PSX_PATCH_LENGTH = 24
TNFS_PSX_VAG_HEADER_LENGTH = 0x30


def psx_spu_sample_rate(pitch: int) -> float:
    """Sample rate (Hz) a voice plays a sample at with SPU pitch `pitch` (0x1000 = 44100 Hz)"""
    return pitch * PSX_SPU_SAMPLE_RATE / PSX_SPU_PITCH_44100


def _footer_criteria(ctx, **kwargs):
    return crc_footer_at(ctx, 0)


class TnfsPsxPatch(DeclarativeCompoundBlock):
    block_description = (
        'A patch of a sound bank: the sample (one or two channels) and how the game plays it. '
        'A voice plays at SPU pitch `pitch` x 2^(cents / 1200), cents = (pitch value - 64) x `bend_range` x 100 '
        '/ 64 (towards 0) + a random value within +-`random_pitch_range` drawn when it starts (`sfx_voice_start` '
        '0x800b6274, `math_func_003` 0x800b5fb8; pitch updates FUN_800bb954): the pitch value 0..127 is the '
        "game's, 64 = `pitch`, e.g. rpm x 127 / (redline + 2000) for the engine loops (`tnfs_sfx_engine_player` "
        '0x8003c4d0). The SPU plays no faster than pitch 0x4000 (176400 Hz)'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        sample_offset = (
            IntegerBlock(length=4, is_signed=True),
            {
                'description': 'Offset of the "VAGp" header of the sample in the `.VB` (of its left channel for two '
                'channels), -1 = none (an empty patch). The bank loader FUN_800b90e0 makes it a pointer, the uploader '
                'FUN_800b926c an SPU address'
            },
        )
        right_sample_offset = (
            IntegerBlock(length=4, is_signed=True),
            {'description': 'Offset of the "VAGp" header of the right channel in the `.VB`, -1 = none (one channel)'},
        )
        pitch = (
            IntegerBlock(length=2),
            {
                'description': 'SPU pitch the sample plays at for pitch value 64: 0x1000 = 44100 Hz, the rate is pitch '
                'x 44100 / 4096. The "VAGp" header\'s sampling rate is not read for a bank sample. Both channels play '
                'at this pitch (FUN_800b60b8 reads this one)'
            },
        )
        right_pitch = (
            IntegerBlock(length=2),
            {'description': 'SPU pitch of the right channel: `pitch` (two channels) or 0, not read by the game'},
        )
        unknown = (
            IntegerBlock(length=2),
            {
                'description': 'Copied to the voice (its +0x54, which the voice queue sets to 1000) when it starts, '
                'not read by the sound library; 0 in every file',
                'is_unknown': True,
            },
        )
        random_pitch_range = (
            IntegerBlock(length=2),
            {
                'description': 'Random pitch variation in cents: a voice starts within +-this of its pitch (more than '
                '1200 is taken as 1200; FUN_800b60b8, `sfx_random_range` 0x800b97d4). 100..300 on some one-shots '
                '(hits, gear shifts, front end), 0 elsewhere'
            },
        )
        channels = (
            IntegerBlock(length=1, value_validator=Or([1, 2])),
            {
                'description': 'Channels: 1, or 2 (`sample_offset` played on the left side, `right_sample_offset` on '
                'the right one, both at half volume each side in mono sound mode)'
            },
        )
        volume = (
            IntegerBlock(length=1),
            {
                'description': 'Volume 0..127 (+- a random value within `random_volume_range`, FUN_800b5f5c); the '
                "voice volume is the group's volume x (the game's volume + 1) x (this + 1) / 2^14 (FUN_800b9a94)"
            },
        )
        pan = (
            IntegerBlock(length=1),
            {
                'description': 'Pan 0..255 (+- a random value within `random_pan_range`, FUN_800b5ee4): 0x40 centre, 0 '
                'left, 0x7f right, 0x80..0xff the same mirrored (behind; FUN_800b5d88). Used for sounds played without '
                'a pan of their own (FUN_800b668c, FUN_800b66e0, FUN_800b6730: the front end); the race sounds pass '
                'the pan of their direction'
            },
        )
        bend_range = (
            IntegerBlock(length=1),
            {
                'description': "Pitch bend range in semitones: the game's pitch value 0 / 127 plays the sample this "
                'many semitones lower / higher (x 63 / 64) than 64'
            },
        )
        random_volume_range = (
            IntegerBlock(length=1),
            {
                'description': 'Random volume variation: a voice starts within +-this of `volume`, clamped to 0..127 '
                '(FUN_800b5f5c). 0x7f on the gear shift of Z512TR, 0 elsewhere'
            },
        )
        random_pan_range = (
            IntegerBlock(length=1),
            {
                'description': 'Random pan variation: a voice starts within +-this of `pan` (FUN_800b5ee4). 0 in '
                'every file'
            },
        )
        uploaded_channels = (
            IntegerBlock(length=1),
            {
                'description': 'Set at run time: bit 0 / 1 when the left / right sample is in SPU memory (the uploader '
                'FUN_800b926c); the lookup FUN_800b5e30 ignores a patch without them. 0 in every file'
            },
        )
        reverb = (
            IntegerBlock(length=1),
            {
                'description': 'Non-zero: the voice gets the SPU reverb while the reverb voices are on (the player in '
                'a tunnel, `tnfs_sfx_tunnel_reverb_on` 0x800b9b7c, `spu_set_reverb_voices` 0x800b72b0)'
            },
        )


class TnfsPsxPatchBank(DeclarativeCompoundBlock):
    block_description = (
        'Sound bank header `Z<bank>.VH` ("PatchBank" resource of the game, magic "BXSP"): '
        'the patch of each sample id, the samples are in the `.VB` of the same name (`TnfsPsxVagBank`). A race '
        'loads the player car bank (or two split screen banks), an opponent bank and `ZCOLLISN`; the game finds '
        'a sound by bank and sample id (FUN_800b5e30), the ids of the PC banks: car banks 1 / 2 the engine loops '
        '(engine on / engine off; the Japanese disc: three rpm layers 1 / 2 / 3), 3 the horn (the US disc), 0x20 '
        'the gear shift; opponent banks 0x41 the horn, 0x43 / 0x45 the engine; `ZCOLLISN` the collision bank '
        'ids. The bank loader FUN_800b90e0 checks both magics and turns the offsets into pointers'
    )
    serializer = 'CompleteJsonSerializer'

    class Fields(DeclarativeCompoundBlock.Fields):
        resource_id = (UTF8Block(length=4, value_validator=Eq('BXSP')), {'description': 'Resource ID'})
        patch_count = (
            IntegerBlock(length=4, programmatic_value=lambda ctx: len(ctx.data('patches'))),
            {'usage': 'io,doc', 'description': 'Number of patches'},
        )
        sample_count = (
            IntegerBlock(length=4),
            {'description': 'Number of samples ("VAGp") in the `.VB`: patches can share one'},
        )
        spu_memory_size = (
            IntegerBlock(length=4),
            {
                'description': 'Bytes of SPU memory the game allocates for the samples (FUN_800b9554), the `data_size` '
                'of the `.VB`: the length of its samples without their "VAGp" headers (the US banks; the uploader '
                "copies `data_size` bytes of each), or with them (the Japanese disc's own banks)"
            },
        )
        patch_indices = (
            ArrayBlock(child=IntegerBlock(length=1, is_signed=True), length=TNFS_PSX_SAMPLE_IDS),
            {'description': 'Index of the patch of each sample id 0..127, -1 = none'},
        )
        patches = (
            ArrayBlock(child=TnfsPsxPatch(), length=lambda ctx: ctx.data('patch_count')),
            {'description': 'The patches'},
        )
        crc_footer = (
            TrailingOptionalBlock(child=PsxCrcFooter(), criteria=(_footer_criteria, 'the file ends with "CRCF"')),
            {'description': 'CRC footer'},
        )

    def write(self, data, ctx: WriteContext = None, name: str = '') -> bytes:
        packed = super().write({**data, 'crc_footer': None}, ctx, name)
        return with_crc_footer(packed, data.get('crc_footer'))


def tnfs_psx_bank_patches(data: dict) -> Dict[int, dict]:
    """The patch of each sample id of a `TnfsPsxPatchBank`, in id order"""
    return {
        sample_id: data['patches'][index]
        for sample_id, index in enumerate(data['patch_indices'])
        if 0 <= index < len(data['patches'])
    }


def _bytes_to_end(ctx: ReadContext) -> Optional[int]:
    while ctx is not None and (not isinstance(ctx, ReadContext) or ctx.read_bytes_remaining is None):
        ctx = ctx.parent
    return ctx.read_bytes_remaining if ctx is not None else None


def _bytes_to_next_sample(ctx) -> int:
    """Bytes from here up to the next "VAGp" header (at a multiple of 16 bytes) or to the end of the samples (the CRC
    footer or the end of the file)"""
    remaining = _bytes_to_end(ctx)
    if remaining is None or remaining <= 0:
        return 0
    position = ctx.buffer.tell()
    try:
        rest = ctx.buffer.read(remaining)
    finally:
        ctx.buffer.seek(position)
    end = len(rest)
    if end >= CRCF_FOOTER_LENGTH and rest[end - CRCF_FOOTER_LENGTH : end - CRCF_FOOTER_LENGTH + 4] == b'CRCF':
        end -= CRCF_FOOTER_LENGTH
    found = rest.find(b'VAGp', 0, end)
    while found >= 0 and found % 16:
        found = rest.find(b'VAGp', found + 1, end)
    return end if found < 0 else found


class TnfsPsxVagSample(DeclarativeCompoundBlock):
    block_description = (
        'A sample: Sony\'s "VAGp" header (big-endian numbers) and SPU ADPCM data (16-byte '
        'frames of 28 samples, `library/utils/audio_ps_adpcm_codec.py`), the flags of the frames give the loop: '
        'looped samples flag every frame 2 (repeat), the loop start frame 6 and the last one 3 (the SPU goes back '
        'to the loop start after it); one-shots flag frame 1 with 4, end with a frame flagged 1 (the voice stops '
        'after it) and the frame `00 07 77..`. An item of `TnfsPsxVagBank`, or a file of its own '
        '(`ZSFXLEVL.VAG` of the Japanese disc, with a CRC footer)'
    )
    serializer = 'TnfsPsxVagSampleSerializer'

    class Fields(DeclarativeCompoundBlock.Fields):
        resource_id = (UTF8Block(length=4, value_validator=Eq('VAGp')), {'description': 'Resource ID'})
        version = (IntegerBlock(length=4, byte_order='big'), {'description': 'VAG version: 3, a few 2'})
        reserved = (IntegerBlock(length=4, byte_order='big'), {'description': '0 in every file'})
        data_size = (
            IntegerBlock(length=4, byte_order='big'),
            {
                'description': 'Length of the ADPCM data in bytes: what the uploader FUN_800b926c copies to SPU memory '
                '(FUN_800b8c74 reads it). Can run past the next sample: `CarHorn` of ZCOLLISN / ZCOLLIS0 says 9088 '
                'bytes and has 8960 before the next sample (its loop ends before them), so `wave_data` ends there',
            },
        )
        sampling_rate = (
            IntegerBlock(length=4, byte_order='big'),
            {
                'description': 'Sampling rate the sample was made at (44100, 44070, 22050, 16000...). A bank sample '
                'plays at the pitch of its patch instead; a sample loaded on its own gets the pitch rate x 4096 / '
                '44100 (FUN_800b8cc4)'
            },
        )
        unknown = (
            BytesBlock(length=12),
            {
                'description': "Reserved in Sony's VAG format: zeros or leftovers of the tools that made the files "
                '(`3f 3c`, `7f ff`...), not read by the game',
                'is_unknown': True,
            },
        )
        name = (UTF8Block(length=16), {'description': 'Name of the sample, e.g. "R33_low2", "Diablo LoadL"'})
        wave_data = (
            BytesBlock(
                length=(
                    lambda ctx: min(ctx.data('data_size'), _bytes_to_next_sample(ctx)),
                    'data_size, at most up to the next "VAGp" header',
                )
            ),
            {'description': 'SPU ADPCM frames, the first one silent (zeros)'},
        )
        leftovers = (
            BytesBlock(length=(_bytes_to_next_sample, 'up to the next "VAGp" header or the end of the samples')),
            {
                'description': 'Bytes after `wave_data` up to the next sample: none in most banks, in a few the rest '
                'of a longer sample (`BumpScreech` of ZCOLLISN, the opponent engines `911IntLoad`, `TR348Load`...), '
                'never uploaded to SPU memory',
                'is_unknown': True,
            },
        )
        crc_footer = (
            TrailingOptionalBlock(
                child=PsxCrcFooter(), criteria=(_footer_criteria, 'a file of its own ending with "CRCF"')
            ),
            {'description': 'CRC footer of a sample in a file of its own'},
        )

    def write(self, data, ctx: WriteContext = None, name: str = '') -> bytes:
        packed = super().write({**data, 'crc_footer': None}, ctx, name)
        return with_crc_footer(packed, data.get('crc_footer'))


class TnfsPsxVagBank(DeclarativeCompoundBlock):
    block_description = (
        'Sound bank samples `Z<bank>.VB` (magic "Bgav"): the samples of the patches of the '
        '`.VH` of the same name (`TnfsPsxPatchBank`), back to back. Converted to a folder with a WAV per sample '
        'id of the `.VH` (see `TnfsPsxVagBankSerializer`)'
    )
    serializer = 'TnfsPsxVagBankSerializer'

    class Fields(DeclarativeCompoundBlock.Fields):
        resource_id = (UTF8Block(length=4, value_validator=Eq('Bgav')), {'description': 'Resource ID'})
        length = (
            IntegerBlock(
                length=4, programmatic_value=lambda ctx: 16 + tnfs_psx_vag_samples_length(ctx.data('samples'))
            ),
            {'usage': 'io,doc', 'description': 'Length of the file without the CRC footer'},
        )
        sample_count = (
            IntegerBlock(length=4, programmatic_value=lambda ctx: len(ctx.data('samples'))),
            {'usage': 'io,doc', 'description': 'Number of samples'},
        )
        data_size = (
            IntegerBlock(length=4),
            {
                'description': 'The `spu_memory_size` of the `.VH`: the length of the samples without their "VAGp" '
                "headers (the US banks), or with them (the Japanese disc's own banks)"
            },
        )
        samples = (
            ArrayBlock(child=TnfsPsxVagSample(), length=lambda ctx: ctx.data('sample_count')),
            {
                'description': 'The samples, each at an offset (from the start of the file) a patch of the `.VH` '
                'gives, a multiple of 16'
            },
        )
        crc_footer = (
            TrailingOptionalBlock(child=PsxCrcFooter(), criteria=(_footer_criteria, 'the file ends with "CRCF"')),
            {'description': 'CRC footer'},
        )

    def write(self, data, ctx: WriteContext = None, name: str = '') -> bytes:
        packed = super().write({**data, 'crc_footer': None}, ctx, name)
        return with_crc_footer(packed, data.get('crc_footer'))


def tnfs_psx_vag_samples_length(samples: list) -> int:
    """Length in bytes of the samples of a `TnfsPsxVagBank`"""
    return sum(TNFS_PSX_VAG_HEADER_LENGTH + len(x['wave_data']) + len(x['leftovers']) for x in samples)


def tnfs_psx_vag_bank_samples_by_offset(data: dict) -> Dict[int, dict]:
    """The samples of a `TnfsPsxVagBank` by their offset in the file (the offsets of the `.VH` patches)"""
    res = {}
    offset = 16
    for sample in data['samples']:
        res[offset] = sample
        offset += TNFS_PSX_VAG_HEADER_LENGTH + len(sample['wave_data']) + len(sample['leftovers'])
    return res
