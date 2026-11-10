from typing import Dict

from library.read_blocks import ArrayBlock, BytesBlock, DeclarativeCompoundBlock, IntegerBlock
from library.read_blocks.misc.value_validators import Eq
from library.read_blocks.strings import UTF8Block
from resources.blackbox.chunks import container_chunk_length, nfsu_sub_chunks_field
from resources.blackbox.geometries.nfsu import _CHUNK_ID_DESCR, _CHUNK_LENGTH_DESCR, _ELEVENS_DESCR, elevens_length

# NFS Hot Pursuit 2 (PS2) texture packs: TRACKS/TEX<track>TRACK.BIN, TEX<track>LOCATION.BIN, GLOBAL/*.BIN, loader
# SLUS_203.62 0x10082c. Pixels are palette indexes, 8 or 4 bits, stored as uploaded to GS memory (see
# library/utils/ps2.py), palettes are 32-bit RGBA with alpha 0x80 = opaque, 256-colour ones in CSM1 order


class Nfs6Ps2TexturePackHeader(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Texture pack header: name and original file path'}

    class Fields(DeclarativeCompoundBlock.Fields):
        chunk_id = (IntegerBlock(length=4, value_validator=Eq(0x30300002)), {'description': _CHUNK_ID_DESCR})
        chunk_length = (IntegerBlock(length=4, value_validator=Eq(84)), {'usage': 'io,doc'})
        name = (UTF8Block(length=16), {'description': 'Texture pack name, e.g. "TRACK"'})
        file_path = (
            UTF8Block(length=64),
            {'description': 'Path of the texture pack in the development tools, e.g. "TRACK11\\TrackTextures.tpk"'},
        )
        unk = (IntegerBlock(length=4), {'is_unknown': True})


class Nfs6Ps2MipLevel(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'GS upload settings of an image level'}

    class Fields(DeclarativeCompoundBlock.Fields):
        buffer_width = (IntegerBlock(length=1), {'description': 'GS buffer width of the level in 64-pixel units'})
        swizzled = (
            IntegerBlock(length=1),
            {
                'description': '1: the pixels are stored as uploaded to GS memory as 32-bit pixels (whole GS pages: '
                'at least 128x64 8-bit or 128x128 4-bit pixels), 0: row by row'
            },
        )
        next_level_offset = (
            IntegerBlock(length=2),
            {'description': 'Offset of the next level from the image data, in 256-byte blocks'},
        )


class Nfs6Ps2TextureInfo(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Texture info: name, size, format and location of its data'}

    class Fields(DeclarativeCompoundBlock.Fields):
        runtime_pointers = (BytesBlock(length=8), {'description': 'Written by the game', 'is_unknown': True})
        name = (UTF8Block(length=24), {'description': 'Texture name'})
        name_hash = (
            IntegerBlock(length=4),
            {'description': 'Black Box hash of the name (`bin_hash`): texture id used by meshes'},
        )
        width = (IntegerBlock(length=2), {'description': 'Image width'})
        height = (IntegerBlock(length=2), {'description': 'Image height'})
        bits_per_pixel = (IntegerBlock(length=1), {'description': '8 or 4: palette index bits'})
        unk0 = (IntegerBlock(length=1), {'is_unknown': True})
        num_palette_entries = (IntegerBlock(length=2), {'description': 'Amount of palette colors'})
        unk1 = (IntegerBlock(length=2), {'is_unknown': True})
        num_blocks = (IntegerBlock(length=2), {'description': 'Size of the full-size image in 256-byte units'})
        image_placement = (IntegerBlock(length=4), {'description': 'Offset of the image in the data chunk'})
        palette_placement = (IntegerBlock(length=4), {'description': 'Offset of the palette in the data chunk'})
        image_size = (IntegerBlock(length=4), {'description': 'Size of the image data, mipmaps included'})
        palette_size = (IntegerBlock(length=4), {'description': 'Size of the palette'})
        unk2 = (IntegerBlock(length=4), {'is_unknown': True})
        unk3 = (IntegerBlock(length=4), {'is_unknown': True})
        shift_width = (IntegerBlock(length=1), {'description': 'Log2 of width'})
        shift_height = (IntegerBlock(length=1), {'description': 'Log2 of height'})
        pixel_storage_mode = (
            IntegerBlock(length=1),
            {'description': 'GS pixel storage mode of the texture: 0x13 PSMT8, 0x14 PSMT4'},
        )
        unk4 = (BytesBlock(length=9), {'is_unknown': True})
        levels = (
            ArrayBlock(child=Nfs6Ps2MipLevel(), length=6),
            {'description': 'GS upload settings of the full-size image and its mipmaps'},
        )
        unk5 = (IntegerBlock(length=2), {'is_unknown': True})
        num_mipmaps = (IntegerBlock(length=1), {'description': 'Amount of mipmaps'})
        unk6 = (BytesBlock(length=53), {'is_unknown': True})


class Nfs6Ps2TextureInfos(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Texture infos, one per texture'}

    class Fields(DeclarativeCompoundBlock.Fields):
        chunk_id = (IntegerBlock(length=4, value_validator=Eq(0x30300003)), {'description': _CHUNK_ID_DESCR})
        chunk_length = (
            IntegerBlock(length=4, programmatic_value=lambda ctx: len(ctx.data('textures')) * 164),
            {'usage': 'io,doc', 'description': _CHUNK_LENGTH_DESCR},
        )
        textures = (
            ArrayBlock(child=Nfs6Ps2TextureInfo(), length=lambda ctx: ctx.data('chunk_length') // 164),
            {'description': 'Texture infos'},
        )


class Nfs6Ps2TextureData(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Palettes and pixels of all textures of the pack. Texture infos point to it',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        chunk_id = (IntegerBlock(length=4, value_validator=Eq(0x30300004)), {'description': _CHUNK_ID_DESCR})
        chunk_length = (
            IntegerBlock(length=4, programmatic_value=lambda ctx: len(ctx.data('elevens')) + len(ctx.data('data'))),
            {'usage': 'io,doc', 'description': _CHUNK_LENGTH_DESCR},
        )
        elevens = (
            BytesBlock(length=(lambda ctx: elevens_length(ctx, 0x80), 'up to 128-bytes alignment')),
            {'usage': 'io,doc', 'description': _ELEVENS_DESCR},
        )
        data = (
            BytesBlock(length=lambda ctx: ctx.data('chunk_length') - len(ctx.data('elevens'))),
            {'description': 'Palettes and pixels'},
        )


class Nfs6Ps2TexturePack(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Texture pack (TPK): header, texture infos and their pixel data',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        chunk_id = (IntegerBlock(length=4, value_validator=Eq(0xB0300001)), {'description': _CHUNK_ID_DESCR})
        chunk_length = container_chunk_length()
        sub_chunks = nfsu_sub_chunks_field(
            [Nfs6Ps2TexturePackHeader(), Nfs6Ps2TextureInfos(), Nfs6Ps2TextureData()], 'Child chunks'
        )

    def serializer_class(self):
        from serializers.bitmaps import Nfs6Ps2TexturePackSerializer

        return Nfs6Ps2TexturePackSerializer
