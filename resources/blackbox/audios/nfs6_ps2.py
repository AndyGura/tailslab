from typing import List, Optional

from library.context import WriteContext
from library.read_blocks import (
    ArrayBlock,
    BytesBlock,
    DeclarativeCompoundBlock,
    DelegateBlock,
    IntegerBlock,
    UTF8Block,
    REMAINING,
)
from library.read_blocks.archives import ArchiveBlock, EntryLayout, ItemDescription, pre_items_payload_length
from library.read_blocks.misc.value_validators import Eq
from library.read_blocks.strings import NullTerminatedUTF8Block

# the jukebox header and every track entry
NFS6_PS2_JUKEBOX_RECORD_LENGTH = 0x60
NFS6_PS2_JUKEBOX_TRACK_HEADER_LENGTH = 0x30
NFS6_PS2_JUKEBOX_NAME_LENGTH = 84
NFS6_PS2_JUKEBOX_GROUP_NAME_LENGTH = 60
NFS6_PS2_JUKEBOX_SECTOR = 2048


def _fit_name_padding(padding: bytes, name: str, field_length: int) -> bytes:
    """Rest of a fixed-length name field after the name and its terminating zero: `padding` cut or zero-padded to
    fit"""
    length = field_length - len(name.encode('utf-8')) - 1
    return (bytes(padding or b'') + bytes(max(0, length)))[: max(0, length)]


class Nfs6Ps2JukeboxTrack(DeclarativeCompoundBlock):
    block_description = 'A song of the jukebox: a stereo PS-ADPCM stream with a "VAGp" header (big endian numbers)'
    serializer = 'Nfs6Ps2JukeboxTrackSerializer'

    class Fields(DeclarativeCompoundBlock.Fields):
        resource_id = (UTF8Block(length=4, value_validator=Eq('VAGp')), {'description': 'Resource ID'})
        version = (IntegerBlock(length=4, byte_order='big'), {'description': 'VAG version: 2'})
        unk0 = (IntegerBlock(length=4, byte_order='big'), {'is_unknown': True, 'description': 'Always 0'})
        data_size = (
            IntegerBlock(length=4, byte_order='big'),
            {
                'description': 'Length of the wave data of both channels in bytes, without the zeros padding the '
                'last block of each channel'
            },
        )
        sampling_rate = (IntegerBlock(length=4, byte_order='big'), {'description': 'Sampling rate: 32000'})
        unk1 = (BytesBlock(length=16), {'is_unknown': True, 'description': 'Zeros'})
        stereo_id = (UTF8Block(length=4, value_validator=Eq('VAGx')), {'description': '"VAGx"'})
        unk2 = (IntegerBlock(length=4, byte_order='big'), {'is_unknown': True, 'description': 'Always 0'})
        channels = (IntegerBlock(length=4, byte_order='big'), {'description': 'Channels: 2'})
        wave_data = (
            BytesBlock(length=(REMAINING, 'up to the next track')),
            {
                'description': 'PS-ADPCM frames (16 bytes, 28 samples) of the channels in blocks of `interleave` '
                'sectors of the jukebox (0x8000 bytes): a block of the left channel, a block of the right one, and so '
                'on. The last round holds the rest of `data_size`, half per channel, each half at the start of its '
                'block, padded with zeros. Each channel ends with a silent frame flagged as the end (flags 1) and the '
                'terminator frame `00 07 77 77..`; zeros follow up to the next track',
            },
        )


class Nfs6Ps2JukeboxGroup(DeclarativeCompoundBlock):
    block_description = 'The group of tracks of the jukebox, 0x40 bytes'

    class Fields(DeclarativeCompoundBlock.Fields):
        num_tracks = (IntegerBlock(length=4), {'usage': 'io,doc', 'description': 'Amount of tracks: 23'})
        name = (
            NullTerminatedUTF8Block(length=NFS6_PS2_JUKEBOX_GROUP_NAME_LENGTH),
            {'description': 'Name of the group: "InGame"'},
        )
        name_padding = (
            BytesBlock(
                length=(
                    lambda ctx: NFS6_PS2_JUKEBOX_GROUP_NAME_LENGTH - len(ctx.data('name').encode('utf-8')) - 1,
                    f'{NFS6_PS2_JUKEBOX_GROUP_NAME_LENGTH - 1} - len(name)',
                )
            ),
            {'description': f'Rest of the {NFS6_PS2_JUKEBOX_GROUP_NAME_LENGTH}-byte name field: 0xCC bytes'},
        )

    def write(self, data, ctx: WriteContext = None, name: str = '') -> bytes:
        # the name field stays 60 bytes long whatever the name
        padding = _fit_name_padding(data['name_padding'], data['name'], NFS6_PS2_JUKEBOX_GROUP_NAME_LENGTH)
        return super().write({**data, 'name_padding': padding}, ctx, name)


class Nfs6Ps2JukeboxEntry(DeclarativeCompoundBlock):
    block_description = 'A track of the jukebox, 0x60 bytes'

    class Fields(DeclarativeCompoundBlock.Fields):
        offset = (IntegerBlock(length=4), {'description': 'Offset of the track (its header) in the file'})
        header_length = (
            IntegerBlock(length=2, value_validator=Eq(NFS6_PS2_JUKEBOX_TRACK_HEADER_LENGTH)),
            {'description': 'Length of the track header: 0x30'},
        )
        num_blocks = (
            IntegerBlock(length=2),
            {
                'description': 'Length of the track (header, wave data and the zeros up to the next track) in 64 KiB, '
                'rounded down'
            },
        )
        unk0 = (IntegerBlock(length=4, value_validator=Eq(0)), {'is_unknown': True, 'description': 'Always 0'})
        name = (
            NullTerminatedUTF8Block(length=NFS6_PS2_JUKEBOX_NAME_LENGTH),
            {
                'description': 'Name of the track: "<artist>-<title>-<album>-<style>", e.g. "Rush-One Little Victory '
                '(Inst)-Vapor Trails-Rock-2"'
            },
        )
        name_padding = (
            BytesBlock(
                length=(
                    lambda ctx: NFS6_PS2_JUKEBOX_NAME_LENGTH - len(ctx.data('name').encode('utf-8')) - 1,
                    f'{NFS6_PS2_JUKEBOX_NAME_LENGTH - 1} - len(name)',
                )
            ),
            {
                'description': f'Rest of the {NFS6_PS2_JUKEBOX_NAME_LENGTH}-byte name field: leftovers of longer names '
                '(e.g. "wav"), 0xCC bytes, a last zero'
            },
        )


class Nfs6Ps2Jukebox(ArchiveBlock):
    block_description = (
        'The in-game music of NFS Hot Pursuit 2 (PS2): 23 songs, the licensed ones with and '
        'without vocals (style "Rock-4" / "Rock-2") and EA\'s own ones ("Rock-0", "Techno-0"), the songs of the '
        "PC game's `audio/music`. Header, a group of tracks, a 0x60-byte entry per track, then the tracks, each "
        'one 0x800-aligned after its 0x30-byte header. Converted to a folder of WAV files named after the tracks'
    )
    serializer = 'Nfs6Ps2JukeboxSerializer'

    def __init__(self, **kwargs):
        super().__init__(
            item_block=DelegateBlock(
                possible_blocks=[
                    Nfs6Ps2JukeboxTrack(),
                    BytesBlock(length=(REMAINING, 'up to the next track')),
                ],
                choice_index=(_track_block_index, '0 for a "VAGp" track, else 1'),
            ),
            alias_field=NullTerminatedUTF8Block(length=NFS6_PS2_JUKEBOX_NAME_LENGTH),
            **kwargs,
        )

    class Fields(ArchiveBlock.Fields):
        interleave = (
            IntegerBlock(length=4),
            {
                'description': 'Length of a block of one channel in the wave data of the tracks, in 2048-byte '
                "sectors: 16 (0x8000 bytes, the interleave which decodes the PC game's songs)"
            },
        )
        channels = (IntegerBlock(length=4), {'description': 'Channels of the tracks: 2'})
        sampling_rate = (IntegerBlock(length=4), {'description': 'Sampling rate of the tracks: 32000'})
        num_groups = (
            IntegerBlock(length=4, value_validator=Eq(1)),
            {'description': 'Amount of track groups: 1 (one more group would make another layout)'},
        )
        unk0 = (
            IntegerBlock(length=4),
            {
                'is_unknown': True,
                'description': "0x1000: the distance between the end of a track's wave data (with the padding of its "
                "last block) and the next track's wave data",
            },
        )
        unk1 = (BytesBlock(length=12), {'is_unknown': True, 'description': 'Zeros'})
        group = (Nfs6Ps2JukeboxGroup(), {'description': 'The group of the tracks'})
        items_descr = (
            ArrayBlock(child=Nfs6Ps2JukeboxEntry(), length='group/num_tracks'),
            {'usage': 'io,doc', 'description': 'The tracks: offset, length and name of each one'},
        )
        pre_items_payload = (
            BytesBlock(
                length=(
                    lambda ctx: pre_items_payload_length(ctx, [x['offset'] for x in ctx.data('items_descr')]),
                    'up to the first track',
                )
            ),
            {
                'description': 'Bytes between the last entry and the first track: leftovers of the tool which wrote '
                'the file (0x900..0x17D0)',
            },
        )
        data_bytes = (
            BytesBlock(length=REMAINING),
            {
                'usage': 'io,doc',
                'description': 'The tracks, at the offsets of `items_descr`. Each one is a '
                '[Nfs6Ps2JukeboxTrack](#nfs6ps2jukeboxtrack)',
            },
        )
        children = (ArrayBlock(child=None, length=None), {'usage': 'ui'})
        name_paddings = (
            ArrayBlock(child=BytesBlock(length=None), length=None),
            {
                'usage': 'ui',
                'description': '`name_padding` of the entries of `items_descr`, by track: written back after the '
                'name, cut or zero-padded to fit',
            },
        )

    def entry_kind_hint(self, head: bytes):
        return 'Nfs6Ps2JukeboxTrack' if head[:4] == b'VAGp' else 'BytesBlock'

    def item_descriptions(self, header: dict) -> List[ItemDescription]:
        return [ItemDescription(i, x['offset'], x['name']) for i, x in enumerate(header['items_descr'])]

    def after_read(self, res: dict, descriptions: List[ItemDescription]):
        res['name_paddings'] = [x['name_padding'] for x in res['items_descr']]

    def heap_offset(self, data, layouts: List[Optional[EntryLayout]]) -> int:
        # the header and each entry take a record
        return NFS6_PS2_JUKEBOX_RECORD_LENGTH * (1 + len(layouts)) + len(data.get('pre_items_payload', b''))

    def make_items_descr(self, data: dict, layouts: List[Optional[EntryLayout]], heap_offset: int) -> list:
        name_paddings = data.get('name_paddings') or []
        return [
            {
                'offset': heap_offset + layout.offset,
                'header_length': NFS6_PS2_JUKEBOX_TRACK_HEADER_LENGTH,
                'num_blocks': layout.length >> 16,
                'unk0': 0,
                'name': child['alias'],
                'name_padding': _fit_name_padding(
                    name_paddings[i] if i < len(name_paddings) else b'', child['alias'], NFS6_PS2_JUKEBOX_NAME_LENGTH
                ),
            }
            for i, (child, layout) in enumerate(zip(data['children'], layouts))
        ]

    def write(self, data, ctx: WriteContext = None, name: str = '') -> bytes:
        group = {**data['group'], 'num_tracks': len(data['children'])}
        return super().write({**data, 'group': group}, ctx=ctx, name=name)


def _track_block_index(ctx, **_) -> int:
    position = ctx.buffer.tell()
    head = ctx.buffer.read(4)
    ctx.buffer.seek(position)
    return 0 if head == b'VAGp' else 1
