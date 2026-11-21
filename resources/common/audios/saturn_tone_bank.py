"""Sega Saturn tone bank (tone data of Sega's sound driver for the SCSP sound chip): instruments ("voices") of
layers, each layer a note range playing one sample, with the SCSP slot register values it is played with, and the
samples. Big-endian. Read from the files of Over Drivin' GT-R (`SOUNDS/*.BIN`, checked against all 16); the layer
fields after the slot registers are named by what the data shows"""

from typing import List

from library.read_blocks import (
    REMAINING,
    ArrayBlock,
    BytesBlock,
    DeclarativeCompoundBlock,
    IntegerBlock,
    SubByteCompoundBlock,
)

# the SCSP plays a sample at 44100 Hz when the note played is the layer's base note (OCT 0, FNS 0)
SCSP_SAMPLE_RATE = 44100
SATURN_TONE_BANK_HEADER_TABLES = 4
MIXER_SIZE = 18
VELOCITY_TABLE_SIZE = 10
PEG_SIZE = 10
PLFO_SIZE = 4
VOICE_HEADER_SIZE = 4
LAYER_SIZE = 32


class SaturnToneLayer(DeclarativeCompoundBlock):
    block_description = (
        'A layer of a voice: a note range and the sample it plays. Bytes 2..0x18 are the SCSP '
        'slot registers 0x00..0x16 (high byte) the driver writes for it'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        start_note = (IntegerBlock(length=1), {'description': 'Lowest note (MIDI number) the layer plays'})
        end_note = (IntegerBlock(length=1), {'description': 'Highest note the layer plays'})
        sample_control = (
            SubByteCompoundBlock(
                length=2,
                byte_order='big',
                schema=[
                    (3, 'unused', 'number', [], 'Not used, 0'),
                    (1, 'key_on_execute', 'boolean', [], 'KYONEX, set by the driver at run time'),
                    (1, 'key_on', 'boolean', [], 'KYONB, set by the driver at run time'),
                    (2, 'source_bit_control', 'number', [], 'SBCTL: 0'),
                    (2, 'sound_source', 'number', [], 'SSCTL: 0 = the sample in sound memory'),
                    (
                        2,
                        'loop_control',
                        'enum',
                        ['no_loop', 'normal_loop', 'reverse_loop', 'alternating_loop'],
                        'LPCTL: no_loop (play once up to `loop_end`), normal_loop (`loop_start`..`loop_end` again and '
                        'again)',
                    ),
                    (1, 'pcm_8bit', 'boolean', [], 'PCM8B: 8-bit samples (signed), else 16-bit (signed, big-endian)'),
                    (4, 'start_address_high', 'number', [], 'SA bits 16-19'),
                ],
            ),
            {'description': 'SCSP slot register 0x00: sample format and loop mode'},
        )
        start_address = (
            IntegerBlock(length=2, byte_order='big'),
            {
                'description': 'SA bits 0-15: offset of the sample in the bank (the driver adds the address the bank '
                'is loaded at): the first sample starts right after the voices (checked)'
            },
        )
        loop_start = (
            IntegerBlock(length=2, byte_order='big'),
            {'description': 'LSA: loop start, in samples from the start of the sample'},
        )
        loop_end = (
            IntegerBlock(length=2, byte_order='big'),
            {
                'description': 'LEA: loop end, in samples from the start of the sample: the SCSP goes back to `loop_start` '
                'when it reaches it (without a loop: stops there). The sample data holds `loop_end` + 1 samples '
                '(checked: the samples are back to back)'
            },
        )
        envelope = (
            SubByteCompoundBlock(
                length=2,
                byte_order='big',
                schema=[
                    (5, 'decay_2_rate', 'number', [], 'D2R'),
                    (5, 'decay_1_rate', 'number', [], 'D1R'),
                    (1, 'hold', 'boolean', [], 'EGHOLD'),
                    (5, 'attack_rate', 'number', [], 'AR: 31 in every layer'),
                ],
            ),
            {'description': 'SCSP slot register 0x08: amplitude envelope rates'},
        )
        envelope_2 = (
            SubByteCompoundBlock(
                length=2,
                byte_order='big',
                schema=[
                    (1, 'unused', 'number', [], 'Not used'),
                    (1, 'loop_start_link', 'boolean', [], 'LPSLNK'),
                    (4, 'key_rate_scaling', 'number', [], 'KRS'),
                    (5, 'decay_level', 'number', [], 'DL'),
                    (5, 'release_rate', 'number', [], 'RR'),
                ],
            ),
            {'description': 'SCSP slot register 0x0A: envelope levels and release'},
        )
        total_level = (
            SubByteCompoundBlock(
                length=2,
                byte_order='big',
                schema=[
                    (6, 'unused', 'number', [], 'Not used'),
                    (1, 'stack_write_inhibit', 'boolean', [], 'STWINH'),
                    (1, 'sound_direct', 'boolean', [], 'SDIR'),
                    (8, 'level', 'number', [], 'TL: attenuation, 0.375 dB steps (0 in every layer)'),
                ],
            ),
            {'description': 'SCSP slot register 0x0C'},
        )
        modulation = (
            IntegerBlock(length=2, byte_order='big'),
            {'description': 'SCSP slot register 0x0E (MDL, MDXSL, MDYSL): 0 in every layer'},
        )
        pitch = (
            IntegerBlock(length=2, byte_order='big'),
            {
                'description': 'SCSP slot register 0x10 (OCT, FNS): 0 in every layer, the driver sets the pitch from '
                'the note played'
            },
        )
        lfo = (
            IntegerBlock(length=2, byte_order='big'),
            {'description': 'SCSP slot register 0x12 (LFO): 0 in every layer'},
        )
        input_mix = (
            IntegerBlock(length=2, byte_order='big'),
            {
                'description': 'SCSP slot register 0x14 (ISEL, IMXL): the effect DSP input and its level (0x0B, 0x07 or '
                '0 in the files)'
            },
        )
        direct_level_pan = (
            SubByteCompoundBlock(
                length=1,
                schema=[
                    (
                        3,
                        'direct_level',
                        'number',
                        [],
                        'DISDL: direct output level, 7 = 0 dB, each step down 6 dB less, 0 = off',
                    ),
                    (
                        5,
                        'direct_pan',
                        'number',
                        [],
                        'DIPAN: bits 0-3 attenuate one side (0 = centre, 0xF = that side off, 3 dB steps), bit 4 picks '
                        'the side: with it the right one (the sound to the left), without it the left one. 0x1F / 0x0F '
                        'in the two layers of the stereo engine samples, 0 elsewhere',
                    ),
                ],
            ),
            {'description': 'SCSP slot register 0x16 high byte: direct output level and pan'},
        )
        base_note = (
            IntegerBlock(length=1),
            {
                'description': 'Note at which the sample plays at 44100 Hz (OCT 0, FNS 0); a note n plays it at 44100 x '
                '2^((n - base note) / 12) Hz. 60 in every layer'
            },
        )
        fine_tune = (
            IntegerBlock(length=1, is_signed=True),
            {'description': 'Fine tuning of the base note, 0 in every layer (its unit is not known)'},
        )
        unknown = (
            BytesBlock(length=5),
            {'description': 'Zeros in every layer', 'is_unknown': True},
        )


class SaturnToneVoice(DeclarativeCompoundBlock):
    block_description = 'A voice (an instrument): a 4-byte header and its layers'

    class Fields(DeclarativeCompoundBlock.Fields):
        mode = (
            SubByteCompoundBlock(
                length=1,
                schema=[
                    (4, 'play_mode', 'number', [], 'Play mode, 0 in every file'),
                    (4, 'bend_range', 'number', [], 'Pitch bend range in semitones: 12 in every file'),
                ],
            ),
            {'description': 'Play mode and pitch bend range'},
        )
        portamento = (IntegerBlock(length=1), {'description': 'Portamento time, 0 in every file'})
        layers_count = (
            IntegerBlock(length=1, programmatic_value=lambda ctx: len(ctx.data('layers')) - 1),
            {'description': 'Number of layers - 1'},
        )
        volume_bias = (IntegerBlock(length=1, is_signed=True), {'description': 'Volume bias, 0 in every file'})
        layers = (
            ArrayBlock(child=SaturnToneLayer(), length=lambda ctx: ctx.data('layers_count') + 1),
            {'description': 'The layers'},
        )


def _voices_count(ctx) -> int:
    return (ctx.data('mixer_offset') - 2 * SATURN_TONE_BANK_HEADER_TABLES) // 2


class SaturnToneBank(DeclarativeCompoundBlock):
    block_description = (
        "Sega Saturn tone bank (tone data of Sega's sound driver): offsets of the tables, the "
        "mixer, velocity, pitch envelope and pitch LFO tables, the voices and the samples. Over Drivin' GT-R "
        '`SOUNDS/*.BIN`: the engine sounds of the cars, one voice each. Player banks (`9110` = 911 PORSCHE slot, '
        '`DIABLO`, `NSX`, `RX7`, `SUPRA`, `TR512` = TESTA, `VIPER`, `ZR1` = VETTE) have 6 layers: note 50 two '
        'looped 8-bit samples, left and right channels of the engine sound (`engine_on`), note 51 the same for '
        'the engine without throttle (`engine_off`), note 52 a looped 16-bit sample (the horn, a steady tone), '
        'note 53 a 16-bit one-shot (the gear shift: two clunks). Opponent banks `OPP*` have 2: note 40 the '
        "player bank's horn at half the sample rate, note 41 the left channel of its `engine_on` at 2^(-9/12) of "
        "the sample rate (played 12 and 9 notes lower, so at the pitch of the player's; checked by correlation). "
        'Cars sharing a real engine share the engine samples (BNR32 / BCNR33, PGC10 / KPGC110, Silvia / 180SX). '
        'The roles are guesses from the data: the game code is not disassembled'
    )
    serializer = 'SaturnToneBankSerializer'

    class Fields(DeclarativeCompoundBlock.Fields):
        mixer_offset = (IntegerBlock(length=2, byte_order='big'), {'description': 'Offset of `mixers`'})
        velocity_offset = (IntegerBlock(length=2, byte_order='big'), {'description': 'Offset of `velocity_tables`'})
        peg_offset = (IntegerBlock(length=2, byte_order='big'), {'description': 'Offset of `pitch_envelopes`'})
        plfo_offset = (IntegerBlock(length=2, byte_order='big'), {'description': 'Offset of `pitch_lfos`'})
        voice_offsets = (
            ArrayBlock(
                child=IntegerBlock(length=2, byte_order='big'), length=(_voices_count, '(mixer_offset - 8) / 2')
            ),
            {'description': 'Offsets of the voices (one in every file)'},
        )
        mixers = (
            BytesBlock(length=(lambda ctx: ctx.data('velocity_offset') - ctx.data('mixer_offset'), '18 * n')),
            {'description': 'Mixer tables, 18 bytes each (effect send levels): one, zeros'},
        )
        velocity_tables = (
            BytesBlock(length=(lambda ctx: ctx.data('peg_offset') - ctx.data('velocity_offset'), '10 * n')),
            {'description': 'Velocity tables, 10 bytes each: one'},
        )
        pitch_envelopes = (
            BytesBlock(length=(lambda ctx: ctx.data('plfo_offset') - ctx.data('peg_offset'), '10 * n')),
            {'description': 'Pitch envelope (PEG) tables, 10 bytes each: one, zeros'},
        )
        pitch_lfos = (
            BytesBlock(length=(lambda ctx: ctx.data('voice_offsets/0') - ctx.data('plfo_offset'), '4 * n')),
            {'description': 'Pitch LFO tables, 4 bytes each: one'},
        )
        voices = (
            ArrayBlock(child=SaturnToneVoice(), length=lambda ctx: len(ctx.data('voice_offsets'))),
            {'description': 'The voices, back to back'},
        )
        wave_data = (
            BytesBlock(length=(REMAINING, 'up to the end of the file')),
            {
                'description': "The samples (and a few padding bytes); a layer's `start_address` counts from the "
                'start of the bank'
            },
        )


def saturn_tone_bank_header_size(data: dict) -> int:
    """Offset of `wave_data` in the bank"""
    return data['voice_offsets'][0] + sum(VOICE_HEADER_SIZE + LAYER_SIZE * len(v['layers']) for v in data['voices'])


def saturn_tone_layer_samples(data: dict, layer: dict) -> List[int]:
    """Samples of a layer as signed 16-bit values (8-bit ones x 256): `loop_end` + 1 of them"""
    start = (
        layer['sample_control']['start_address_high'] << 16 | layer['start_address']
    ) - saturn_tone_bank_header_size(data)
    count = layer['loop_end'] + 1
    wave = data['wave_data']
    if layer['sample_control']['pcm_8bit']:
        raw = wave[start : start + count]
        return [(b - 256 if b >= 128 else b) * 256 for b in raw]
    raw = wave[start : start + 2 * count]
    return [int.from_bytes(raw[i : i + 2], 'big', signed=True) for i in range(0, len(raw) - 1, 2)]


def saturn_tone_layer_sample_rate(layer: dict) -> float:
    """Sample rate a layer plays its sample at for its own (first) note"""
    return SCSP_SAMPLE_RATE * 2 ** ((layer['start_note'] - layer['base_note']) / 12)


def is_saturn_tone_bank(head: bytes, length: int) -> bool:
    """Table offsets in order with room for whole tables, then a voice whose layers fit in the file, with notes up to
    127 and samples after the voices. `head`: the first bytes of the file (at least up to the first voice's layers)"""
    if len(head) < 16:
        return False
    mixer, velocity, peg, plfo, voice = (int.from_bytes(head[i : i + 2], 'big') for i in range(0, 10, 2))
    if not (
        10 <= mixer < velocity < peg <= plfo <= voice
        and mixer % 2 == 0
        and (velocity - mixer) % MIXER_SIZE == 0
        and (peg - velocity) % VELOCITY_TABLE_SIZE == 0
        and (plfo - peg) % PEG_SIZE == 0
        and (voice - plfo) % PLFO_SIZE == 0
        and voice + VOICE_HEADER_SIZE <= len(head)
    ):
        return False
    layers = head[voice + 2] + 1
    end = voice + VOICE_HEADER_SIZE + LAYER_SIZE * layers
    if end > len(head) or end > length:
        return False
    for i in range(layers):
        layer = head[voice + VOICE_HEADER_SIZE + LAYER_SIZE * i : voice + VOICE_HEADER_SIZE + LAYER_SIZE * (i + 1)]
        start_address = (layer[2] & 0xF) << 16 | int.from_bytes(layer[4:6], 'big')
        if not (layer[0] <= layer[1] <= 127 and layer[25] <= 127 and end <= start_address < length):
            return False
    return True
