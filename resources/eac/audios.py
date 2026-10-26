from copy import deepcopy
from io import SEEK_CUR
from typing import Dict

from library.context import ReadContext, WriteContext
from library.read_blocks import (
    DeclarativeCompoundBlock,
    UTF8Block,
    IntegerBlock,
    BytesBlock,
    Padding,
    ArrayBlock,
    EnumByteBlock,
    OptionalBlock,
    BitFlagsBlock,
)
from library.read_blocks.misc.value_validators import Eq


class EacsAudioHeader(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A header for EACS audio. It is almost identical to AsfAudio when it is the only '
            'sound in the file (*.EAS), but also can be included in single SoundBank file '
            '(*.BNK), which has multiple EACS headers and wave data located separately',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        resource_id = (UTF8Block(value_validator=Eq('EACS'), length=4), {'description': 'Resource ID'})
        sampling_rate = (IntegerBlock(length=4), {'description': 'Sampling rate of audio'})
        sound_resolution = (IntegerBlock(length=1), {'description': 'How many bytes in one wave data entry'})
        channels = (IntegerBlock(length=1), {'description': 'Channels amount. 1 is mono, 2 is stereo'})
        compression = (
            IntegerBlock(length=1),
            {
                'description': 'If equals to 2, wave data is compressed with [IMA ADPCM]('
                'https://wiki.multimedia.cx/index.php/Electronic_Arts_Formats_(2)'
                '#IMA_ADPCM_Decompression_Algorithm) codec'
            },
        )
        unk0 = (IntegerBlock(length=1), {'is_unknown': True})
        wave_data_length = (
            IntegerBlock(length=4),
            {
                'description': 'Amount of wave data entries. Should be multiplied by '
                'sound_resolution to calculated the size of data in bytes'
            },
        )
        repeat_loop_beginning = (
            IntegerBlock(length=4),
            {
                'description': 'When audio ends, it repeats in loop from here. Should be '
                'multiplied by sound_resolution to calculate offset in bytes'
            },
        )
        repeat_loop_length = (
            IntegerBlock(length=4),
            {
                'description': 'If play audio in loop, at this point we should rewind to repeat_'
                'loop_beginning. Should be multiplied by sound_resolution to '
                'calculate offset in bytes'
            },
        )
        wave_data_offset = (
            IntegerBlock(length=4),
            {'description': 'Offset of wave data start in current file, relative to start of the file itself'},
        )
        unk1 = (IntegerBlock(length=4), {'is_unknown': True})


class SoundBankHeaderEntry(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': "TNFS sound bank (*.BNK) entry: the game's playback settings for a sample, "
            'followed by its EACS header. Field meanings come from the game code, as decoded by the '
            '[tnfs-1995](https://github.com/marcos2250/tnfs-1995) project',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        voice_mask = (
            IntegerBlock(length=4),
            {
                'description': "Bit mask of the game's mixer channels (voices) this sample may play on (bit n = "
                'channel n), used by the DOS voice allocator `sfx_voice_alloc` (0x96760). The collision bank '
                'duplicates looped wavs under several indices, each with a different bit. Examples: collision bank '
                'wind 0x29 has bit 5 (wind channel 5), waterfall 0x3e bit 11 (channel 0xb), the hits bits 4 and 5 '
                '(one-shot channel 4), car bank engine_off bit 1 (channel 1), car bank horn bit 14 (player horn '
                'channel 0xe). The exception is car bank engine_on: bit 6, played on channel 0',
            },
        )
        eacs_header_offset = (
            IntegerBlock(length=4),
            {
                'description': 'Offset of `eacs_header` in the file: offset of this entry + 40. The game turns it '
                'into a pointer when it loads the bank'
            },
        )
        play_time_limit = (
            IntegerBlock(length=4),
            {
                'description': 'Play time limit in sound driver ticks. At voice start the game stores this value - 1 '
                'in the voice (voice+4; DOS `sfx_voice_start_one` 0x96d22, demo 0x79ca2, Win95 SE 0x48eed8), the '
                'driver tick (DOS `sfx_driver_tick` 0xaada7, Win95 SE 0x4a4ac0) decrements it and stops the voice '
                'when it goes below 0. 0 = no limit, the value of every entry in the shipped banks'
            },
        )
        random_range = (
            IntegerBlock(length=4),
            {
                'description': 'Random pitch range in cents. At every voice start (DOS 0x96d22) the pitch offset of '
                'the voice is `pitch_offset` + a random value in [-random_range, +random_range]. 300 for hits, '
                '150-250 for gear clicks, 600 for collision bank entry 0x50, 0 for loops'
            },
        )
        pitch_offset = (
            IntegerBlock(length=4, is_signed=True),
            {
                'description': 'Base pitch offset in cents, added to every pitch the voice plays at (see '
                '`random_range`, `bend_range_semitones`). 0 in all TNFS banks'
            },
        )
        priority = (IntegerBlock(length=1), {'description': 'Playback priority'})
        unk3 = (
            IntegerBlock(length=1),
            {
                'is_unknown': True,
                'description': 'DOS and the demo copy it to the voice (voice+0x14), no code reads it there; Win95 SE '
                'does not copy it. 0x80 in every entry of the shipped banks',
            },
        )
        unk4 = (
            IntegerBlock(length=1, is_signed=True),
            {
                'is_unknown': True,
                'description': 'Read by no binary (DOS, demo, Win95 SE): probably an authoring transpose the games '
                'ignore. 0 in most entries; -5, -6, -12 (e.g. collision bank 0x3d) and 2 in some collision bank '
                'entries',
            },
        )
        bend_range_semitones = (
            IntegerBlock(length=1),
            {
                'description': 'Pitch bend range in semitones. The game plays a sample at pitch value 0..127 '
                '(64 = original pitch). Every pitch set computes cents = (value - 64) * bend_range_semitones * 100 / '
                '64 + the pitch offset of the voice (`pitch_offset` + random, see `random_range`), the playback rate '
                'is the base rate * 2 ^ (cents / 1200) (DOS 0xa6fbd, table 0xa5470)'
            },
        )
        pan = (IntegerBlock(length=1), {'description': 'Pan, 0..127, 64 is center'})
        volume = (
            IntegerBlock(length=1),
            {
                'description': 'Volume, 0..127, with a random +-`random_volume_range`. The final volume is master '
                'volume * entry volume * channel volume / 127^2'
            },
        )
        random_volume_range = (
            IntegerBlock(length=1),
            {
                'description': 'Random volume range: the volume is `volume` +- a random value up to it. 0 in all TNFS banks'
            },
        )
        driver = (
            IntegerBlock(length=1),
            {
                'description': "Sound driver of the sample, a run time field: the demo's bank loader (0x79a62) writes "
                'it when it loads the bank, so a non-zero value here and in the following bytes of a shipped bank is '
                'a leftover of the tool that saved it. 0 or 0x0a in TNFS banks (0xcc in one entry)'
            },
        )
        flags = (
            BitFlagsBlock(length=1, flag_names=[(0, 'stereo_pair')]),
            {
                'description': 'Bit 0: stereo pair, the next sample of the bank is the other channel (`*3D` / `*3` '
                'banks: collision bank 0x30-0x3a even entries and 0x3f, opponent bank 0x43 and 0x45)'
            },
        )
        unk5 = (
            BytesBlock(length=11),
            {
                'is_unknown': True,
                'description': 'Run time voice data (see `driver`): zeros, or leftovers in the entries with a '
                'non-zero `driver`',
            },
        )
        eacs_header = (
            EacsAudioHeader(),
            {
                'description': 'EACS header. Its `wave_data_offset` points into the wave data region of the '
                'sound bank file'
            },
        )


class EacsAudioFile(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A file with single EACS audio entry',
            'custom_actions': [
                {
                    'method': 'silence',
                    'title': 'Silence',
                    'description': 'Makes this audio sample completely silent',
                    'is_pure': False,
                    'args': [],
                }
            ],
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        header = (EacsAudioHeader(), {'description': 'EACS header: sampling rate, resolution, channels, loop settings'})
        offset = (Padding(to=lambda ctx: ctx.data('header/wave_data_offset'), is_global=True), {'is_unknown': True})
        wave_data = (
            BytesBlock(
                length=(
                    lambda ctx: min(
                        ctx.read_bytes_remaining,
                        ctx.data('header/wave_data_length') * ctx.data('header/sound_resolution'),
                    ),
                    'min(`remaining file bytes`, `header.wave_data_length` * `header.sound_resolution`)',
                )
            ),
            {
                'description': 'Wave data is here. If header.sound_resolution == 1, contains signed bytes, '
                'else - unsigned'
            },
        )

    def serializer_class(self):
        from serializers import EacsAudioSerializer

        return EacsAudioSerializer

    def action_silence(self, read_data, **kwargs):
        read_data['wave_data'] = b'\x00' * len(read_data['wave_data'])


class AsfAudio(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'An audio file, which is supported by FFMPEG and can be converted using only it. '
            'Has some explanation [here](https://wiki.multimedia.cx/index.php/Electronic_'
            'Arts_Formats_(2))',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        resource_id = (UTF8Block(value_validator=Eq('1SNh'), length=4), {'description': 'Resource ID'})
        unk0 = (BytesBlock(length=8), {'is_unknown': True})
        sampling_rate = (IntegerBlock(length=4), {'description': 'Sampling rate of audio'})
        sound_resolution = (IntegerBlock(length=1), {'description': 'How many bytes in one wave data entry'})
        channels = (IntegerBlock(length=1), {'description': 'Channels amount. 1 is mono, 2 is stereo'})
        compression = (
            IntegerBlock(length=1),
            {
                'description': 'If equals to 2, wave data is compressed with [IMA ADPCM codec]('
                'https://wiki.multimedia.cx/index.php/Electronic_Arts_Formats_(2)'
                '#IMA_ADPCM_Decompression_Algorithm)'
            },
        )
        unk1 = (IntegerBlock(length=1), {'is_unknown': True})
        wave_data_length = (
            IntegerBlock(length=4),
            {
                'description': 'Amount of wave data entries. Should be multiplied by '
                'sound_resolution to calculated the size of data in bytes'
            },
        )
        repeat_loop_beginning = (
            IntegerBlock(length=4),
            {
                'description': 'When audio ends, it repeats in loop from here. Should be '
                'multiplied by sound_resolution to calculate offset in bytes'
            },
        )
        repeat_loop_length = (
            IntegerBlock(length=4),
            {
                'description': 'If play audio in loop, at this point we should rewind to repeat_'
                'loop_beginning. Should be multiplied by sound_resolution to '
                'calculate offset in bytes'
            },
        )
        wave_data_offset = (
            IntegerBlock(length=4),
            {'description': 'Offset of wave data start in current file, relative to start of the file itself'},
        )
        unk2 = (IntegerBlock(length=4), {'is_unknown': True})
        offset = (
            Padding(to=(lambda ctx: ctx.data('wave_data_offset') + 40, 'wave_data_offset + 40')),
            {'description': 'Padding between the header and wave data'},
        )
        wave_data = (
            BytesBlock(
                length=(
                    lambda ctx: min(
                        ctx.read_bytes_remaining, ctx.data('wave_data_length') * ctx.data('sound_resolution')
                    ),
                    'min(`remaining file bytes`, `wave_data_length` * `sound_resolution`)',
                )
            ),
            {'description': 'Wave data is here'},
        )

    def serializer_class(self):
        from serializers import FfmpegSupportedAudioSerializer

        return FfmpegSupportedAudioSerializer


EA_SOUND_PATCH_TAGS = [
    (0x00, 'unk_0x00'),
    (0x06, 'priority'),
    (0x07, 'unk_0x07'),
    (0x08, 'release_envelope'),
    (0x09, 'playback_envelope'),
    (0x0A, 'bend_range_semitones'),
    (0x0B, 'bank_channels'),
    (0x0C, 'pan'),
    (0x0D, 'random_pan_range'),
    (0x0E, 'volume'),
    (0x0F, 'random_volume_range'),
    (0x10, 'detune'),
    (0x11, 'random_detune_range'),
    (0x12, 'unk_0x12'),
    (0x13, 'effect_bus'),
    (0x14, 'user_data'),
    (0x80, 'version'),
    (0x82, 'channels'),
    (0x83, 'codec'),
    (0x84, 'sampling_rate'),
    (0x85, 'num_samples'),
    (0x86, 'loop_start'),
    (0x87, 'loop_end'),
    (0x88, 'data_offset'),
    (0x89, 'data_offset_channel_2'),
    (0x8A, 'unk_0x8a'),
    (0x8B, 'unk_0x8b'),
    (0x8C, 'flags'),
    (0x91, 'unk_0x91'),
    (0x92, 'unk_0x92'),
    (0x93, 'unk_0x93'),
    (0xA0, 'codec_2'),
    (0xFC, 'padding'),
    (0xFD, 'info_start'),
    (0xFE, 'layer_end'),
    (0xFF, 'end'),
]
# tags without a value
EA_SOUND_PATCH_MARKERS = ['padding', 'info_start', 'layer_end', 'end']


def _ea_sound_patch_tag_count(ctx) -> int:
    """Amount of tags of the patch at the current buffer position, up to and including the end tag 0xFF"""
    start = ctx.buffer.tell()
    count = 0
    try:
        while True:
            tag = ctx.buffer.read(1)
            if not tag:
                return count
            count += 1
            if tag[0] == 0xFF:
                return count
            if tag[0] in (0xFC, 0xFD, 0xFE):
                continue
            length = ctx.buffer.read(1)
            if not length:
                return count
            ctx.buffer.seek(length[0], SEEK_CUR)
    finally:
        ctx.buffer.seek(start)


class EaSoundPatchTag(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A tag of EA sound patch: tag id, then (except for tags 0xFC-0xFF) the length of the '
            'value and the value, big endian unsigned. Tag meanings follow '
            '[vgmstream](https://github.com/vgmstream/vgmstream) (`ea_schl.c`), the ones named `unk_*` are not known',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        tag = (EnumByteBlock(enum_names=EA_SOUND_PATCH_TAGS), {'description': 'Tag id'})
        value_length = (
            OptionalBlock(
                IntegerBlock(length=1),
                criteria=(
                    lambda ctx: ctx.data('tag') not in EA_SOUND_PATCH_MARKERS,
                    'tag is not padding, info_start, layer_end or end',
                ),
            ),
            {'description': 'Length of value in bytes. 0 means value 0'},
        )
        value = (
            OptionalBlock(
                BytesBlock(length=(lambda ctx: ctx.data('value_length'), 'value_length')),
                criteria=(
                    lambda ctx: ctx.data('tag') not in EA_SOUND_PATCH_MARKERS,
                    'tag is not padding, info_start, layer_end or end',
                ),
            ),
            {'description': 'Value, big endian unsigned integer'},
        )

    def read(self, ctx: ReadContext, name: str = '', read_bytes_amount=None):
        res = super().read(ctx, name, read_bytes_amount)
        if res['tag'] in EA_SOUND_PATCH_MARKERS:
            res['value_length'] = res['value'] = None
        else:
            res['value'] = int.from_bytes(res['value'], 'big')
        return res

    def _to_native(self, data):
        if data['tag'] in EA_SOUND_PATCH_MARKERS:
            return data
        data = deepcopy(data)
        data['value'] = int(data['value']).to_bytes(data['value_length'], 'big')
        return data

    def estimate_packed_size(self, data, ctx: WriteContext = None):
        return 1 if data['tag'] in EA_SOUND_PATCH_MARKERS else 2 + data['value_length']

    def write(self, data, ctx: WriteContext = None, name: str = '') -> bytes:
        return super().write(self._to_native(data), ctx, name)


class EaSoundPatch(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'EA sound patch ("PT" header): a sound of a BNKl sound bank as a list of tags. '
            'Tags before `info_start` are playback settings (priority, volume, pan, pitch bend range...), tags '
            'after it describe the wave data: `num_samples`, `channels` (default 1), `sampling_rate` (default '
            '22050), loop sample indices `loop_start` and `loop_end` (inclusive; a sample loops when it has one of '
            'them, from 0 / up to the last sample when the other one is missing), `data_offset` (wave data offset '
            'from the start of the bank file) and the codec. Without the `version` tag, `codec` 7 is EA-XA ADPCM v1, '
            '9 is EA MicroTalk 10:1 (speech), no `codec` tag is 16-bit little endian PCM. With `version` 1, '
            '`codec_2` 8 is 16-bit little endian PCM, 9 is signed 8-bit PCM, no `codec_2` tag is EA-XA ADPCM v2. '
            'Stereo samples are interleaved. A sound can have several layers, played together, separated by the '
            '`layer_end` tag, each one with its own settings and wave data (NFS3 player car engines add a short '
            'mono loop to the stereo engine sample)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        platform_magic = (UTF8Block(length=2, value_validator=Eq('PT')), {'description': 'Patch header magic'})
        platform = (IntegerBlock(length=2), {'description': 'Platform id, 0 is PC'})
        tags = (
            ArrayBlock(child=EaSoundPatchTag(), length=(_ea_sound_patch_tag_count, 'up to and including tag "end"')),
            {'description': 'Tags'},
        )

    def estimate_packed_size(self, data, ctx: WriteContext = None):
        tag_block = self.field_blocks_map['tags'].child
        return 4 + sum(tag_block.estimate_packed_size(x) for x in data['tags'])

    @staticmethod
    def layers(data) -> list:
        """Tags of every layer as a dict {tag name: value}"""
        res = [{}]
        for tag in data['tags']:
            if tag['tag'] == 'layer_end':
                res.append({})
            elif tag['tag'] not in EA_SOUND_PATCH_MARKERS:
                res[-1][tag['tag']] = tag['value']
        return res


# chunk ids of an EA audio stream: header, chunk count, data, loop end, end
EA_AUDIO_STREAM_CHUNK_IDS = (b'SCHl', b'SCCl', b'SCDl', b'SCLl', b'SCEl')


def _read_end(ctx) -> int:
    """Absolute buffer offset where the bytes the block may read end: the end of the closest context with a known
    amount of bytes to read (the file, an archive item), else the end of the buffer"""
    c = ctx
    while c is not None:
        if getattr(c, 'read_bytes_amount', None) is not None and getattr(c, 'read_start_offset', None) is not None:
            return c.read_start_offset + c.read_bytes_amount
        c = c.parent
    pos = ctx.buffer.tell()
    end = ctx.buffer.seek(0, 2)
    ctx.buffer.seek(pos)
    return end


def scan_ea_audio_stream_chunks(buffer, end: int) -> int:
    """Length of the chunks at the buffer position up to and including the end chunk SCEl (or up to an unknown chunk,
    a next stream header, a broken chunk size or `end`). Keeps the buffer position"""
    start = buffer.tell()
    pos = start
    try:
        while pos + 8 <= end:
            buffer.seek(pos)
            head = buffer.read(8)
            chunk_id, size = head[:4], int.from_bytes(head[4:], 'little')
            if chunk_id not in EA_AUDIO_STREAM_CHUNK_IDS or chunk_id == b'SCHl' or size < 8 or pos + size > end:
                break
            pos += size
            if chunk_id == b'SCEl':
                break
        return pos - start
    finally:
        buffer.seek(start)


def scan_ea_audio_stream_padding(buffer, end: int) -> int:
    """Length of the bytes at the buffer position before the next stream header SCHl (MUS files align streams to 4
    bytes), all remaining bytes up to `end` when there is no next stream. Keeps the buffer position"""
    start = buffer.tell()
    try:
        tail = buffer.read(min(end - start, 64))
        index = tail.find(b'SCHl')
        return index if index >= 0 else end - start
    finally:
        buffer.seek(start)


def is_ea_audio_stream(buffer, length: int = None) -> bool:
    """Whether the SCHl file at the buffer position holds audio chunks only (EA videos interleave picture chunks with
    the audio ones: `mTCD` in NFS2 SE DCT movies, `MV0K`, `MADk`...). Checks the first chunks. Keeps the buffer
    position"""
    start = buffer.tell()
    end = start + length if length is not None else buffer.seek(0, 2)
    pos = start
    try:
        for _ in range(16):
            if pos + 8 > end:
                return True
            buffer.seek(pos)
            head = buffer.read(8)
            chunk_id, size = head[:4], int.from_bytes(head[4:], 'little')
            if chunk_id not in EA_AUDIO_STREAM_CHUNK_IDS or size < 8:
                return False
            pos += size
            if chunk_id == b'SCEl':
                return True
        return True
    finally:
        buffer.seek(start)


def _ea_audio_streams_count(ctx) -> int:
    buffer = ctx.buffer
    start = buffer.tell()
    end = _read_end(ctx)
    count = 0
    pos = start
    try:
        while pos + 8 <= end:
            buffer.seek(pos)
            head = buffer.read(8)
            if head[:4] != b'SCHl':
                break
            count += 1
            buffer.seek(pos + int.from_bytes(head[4:], 'little'))
            pos = buffer.tell() + scan_ea_audio_stream_chunks(buffer, end)
            buffer.seek(pos)
            pos += scan_ea_audio_stream_padding(buffer, end)
        return count
    finally:
        buffer.seek(start)


class EaAudioStream(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'EA audio stream (NFS2 - NFS6 music, NFS6 speech): header chunk "SCHl" '
            'with a sound patch (sampling rate, channels, number of samples, loop, codec), then the wave data in '
            'chunks of 8-byte header (id, length including the header) and data: SCCl (amount of SCDl chunks), SCDl '
            '(wave data), SCLl (loop end), SCEl (end). Explained by '
            '[vgmstream](https://github.com/vgmstream/vgmstream) (`ea_schl.c`); the converter decodes it with FFmpeg',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        resource_id = (UTF8Block(value_validator=Eq('SCHl'), length=4), {'description': 'Header chunk id'})
        header_length = (
            IntegerBlock(
                length=4,
                programmatic_value=lambda ctx: (
                    8
                    + ctx.block.field_blocks_map['header'].estimate_packed_size(ctx.data('header'))
                    + len(ctx.data('header_padding'))
                ),
            ),
            {'description': 'Length of the header chunk, including the chunk id and this field'},
        )
        header = (
            EaSoundPatch(),
            {
                'description': 'Sound patch: tags before `info_start` are playback settings, the ones after it '
                'describe the wave data. Without the `version` tag (NFS2 - NFS4) `codec` 7 is EA-XA ADPCM v1, no '
                '`codec` is 16-bit little endian PCM (NFS3 menu music: each SCDl chunk holds the amount of samples, '
                '4 bytes, then the samples, channels interleaved), the sampling rate is 22050 without '
                '`sampling_rate`; with `version` 1 (NFS5, NFS6) the codec is EA-XA ADPCM v2 '
                '("R1" in FFmpeg). `loop_start` / `loop_end` are sample indices of the loop'
            },
        )
        header_padding = (
            BytesBlock(
                length=(
                    lambda ctx: ctx.data('header_length') - ctx.local_buffer_pos,
                    'header_length - (header fields length)',
                )
            ),
            {'description': 'Zeros up to the end of the header chunk'},
        )
        data = (
            BytesBlock(
                length=(
                    lambda ctx: scan_ea_audio_stream_chunks(ctx.buffer, _read_end(ctx)),
                    'chunks up to and including the end chunk SCEl',
                )
            ),
            {'description': 'Chunks SCCl, SCDl, SCLl, SCEl with the wave data, as they are in the file'},
        )
        padding = (
            BytesBlock(
                length=(
                    lambda ctx: scan_ea_audio_stream_padding(ctx.buffer, _read_end(ctx)),
                    'up to the next stream or the end of file',
                )
            ),
            {'description': 'Zeros aligning the next stream of the file to 4 bytes', 'is_unknown': True},
        )


class EaAudioStreams(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A file of EA audio streams (`SCHl`): NFS2 / NFS2 SE `.ASF` (a song), NFS2 / NFS2 '
            'SE / NFS3 `.MUS` (interactive music: a stream per node of the `.MAP` file of the same name), NFS4 '
            '`Data/Audio/MUSIC/*.ASF`, NFS5 songs in `GameData/Music/zzzymus.viv`, NFS6 `audio/music/*.asf`, NFS6 '
            'speech in `radio.viv`. Converted to WAV with FFmpeg: a file with one stream to `<name>.wav` + '
            '`<name>.meta.json` (loop), a file with more streams to a folder with `<index>.wav` + `<index>.meta.json` '
            'per stream and `playthrough.wav` (the streams in the order of the `.LIN`, else `.MAP` file next to it, '
            'see `EaMusicMap`; all streams in file order without one)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        streams = (
            ArrayBlock(child=EaAudioStream(), length=(_ea_audio_streams_count, 'streams up to the end of file')),
            {'description': 'Audio streams'},
        )

    def serializer_class(self):
        from serializers import EaAudioStreamsSerializer

        return EaAudioStreamsSerializer


class EaMusicMapBranch(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A branch of an interactive music node: the node to play next while the music '
            'state value (0..100) set by the game is in the range',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        min_value = (IntegerBlock(length=1), {'description': 'Lowest state value of the branch'})
        max_value = (IntegerBlock(length=1), {'description': 'Highest state value of the branch (100 at most)'})
        next_node = (IntegerBlock(length=1), {'description': 'Index of the node to play next'})


class EaMusicMapNode(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A node of interactive music: one audio stream of the `.MUS` file and the nodes '
            'which can follow it',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        section = (
            IntegerBlock(length=1),
            {'description': 'Section of the song the node belongs to: the row of `events` used while it plays'},
        )
        num_branches = (IntegerBlock(length=1), {'description': 'Amount of used `branches`, 0 in an end node'})
        unk0 = (BytesBlock(length=2), {'is_unknown': True, 'description': 'Always FF FF'})
        branches = (
            ArrayBlock(child=EaMusicMapBranch(), length=8),
            {
                'description': 'Branches, the first `num_branches` are used, the next ones are zeros or leftovers. '
                'The value ranges of the used ones cover 0..100'
            },
        )


class EaMusicMap(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Interactive music map "PFDx" (EA PathFinder) versions 0 and 1, NFS2 / NFS2 SE '
            '`GAMEDATA/AUDIO/PC/*.MAP`, NFS3 `GameData/Audio/pc/*.map` and `*.lin`, for the `.MUS` file of the same '
            'name (EaAudioStreams), big endian. NFS3 `.lin` maps list the same streams as the `.map`, with one branch '
            'per node (0..100): the song played linearly. Music '
            'plays node by node: when a node ends, the branch matching the music state value which the game sets '
            '(0..100) picks the next one; a game event jumps to the node `events` gives for the section of the '
            'current node. Layout from [vgmstream](https://github.com/vgmstream/vgmstream) '
            '(`ea_schl_map_mpf_mus.c`), the node fields from the files',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        resource_id = (UTF8Block(value_validator=Eq('PFDx'), length=4), {'description': 'Resource ID'})
        version = (IntegerBlock(length=1), {'description': 'Version, 0 or 1'})
        start_node = (IntegerBlock(length=1), {'description': 'Index of the node the music starts with'})
        num_nodes = (
            IntegerBlock(length=1, programmatic_value=lambda ctx: len(ctx.data('nodes'))),
            {'description': 'Amount of nodes'},
        )
        num_events = (IntegerBlock(length=1), {'description': 'Amount of events per section, 16 in NFS2 SE'})
        unk0 = (BytesBlock(length=3), {'is_unknown': True, 'description': 'Zeros'})
        num_sections = (
            IntegerBlock(length=1, programmatic_value=lambda ctx: len(ctx.data('events'))),
            {'description': 'Amount of sections (rows of `events`)'},
        )
        nodes = (
            ArrayBlock(child=EaMusicMapNode(), length=(lambda ctx: ctx.data('num_nodes'), 'num_nodes')),
            {'description': 'Nodes'},
        )
        events = (
            ArrayBlock(
                child=ArrayBlock(
                    child=IntegerBlock(length=1), length=(lambda ctx: ctx.data('../num_events'), 'num_events')
                ),
                length=(lambda ctx: ctx.data('num_sections'), 'num_sections'),
            ),
            {
                'description': 'For each section, the node each game event jumps to (0 for an event without a '
                'jump). Meanings of the events are not known'
            },
        )
        stream_offsets = (
            ArrayBlock(
                child=IntegerBlock(length=4, byte_order='big'),
                length=(lambda ctx: ctx.data('num_nodes'), 'num_nodes'),
            ),
            {'description': 'Offset of the audio stream of each node in the `.MUS` file'},
        )

    def serializer_class(self):
        from serializers import JsonSerializer

        return JsonSerializer
