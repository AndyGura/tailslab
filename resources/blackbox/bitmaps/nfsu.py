from library.read_blocks import (
    ArrayBlock,
    BytesBlock,
    DeclarativeCompoundBlock,
    EnumByteBlock,
    IntegerBlock,
)
from library.read_blocks.misc.value_validators import Eq
from library.read_blocks.strings import UTF8Block
from resources.blackbox.chunks import (
    ChunkBlock,
    ZeroChunk,
    chunk_rest,
    chunks_field,
    peek_chunk_length,
    peek_chunk_payload,
    records_to_chunk_end,
)

# Image compression types (TEXCOMP_* of the game), as found in texture info entries
NFSU_TEXTURE_COMPRESSION_TYPES = [
    (0x00, 'DEFAULT'),
    (0x04, '4BIT'),
    (0x08, '8BIT'),
    (0x10, '16BIT'),
    (0x18, '24BIT'),
    (0x20, '32BIT'),
    (0x21, 'DXT'),
    (0x22, 'DXTC1'),
    (0x24, 'DXTC3'),
    (0x26, 'DXTC5'),
]


class NfsuTexturePackHeader(ChunkBlock):
    block_description = 'Texture pack header: name and original file path'

    CHUNK_ID = 0x33310001

    class Fields(ChunkBlock.Fields):
        chunk_length = (IntegerBlock(length=4, value_validator=Eq(124)), {'usage': 'io,doc'})
        version = (IntegerBlock(length=4), {'description': 'Texture pack version, 4 in NFSU, 5 in NFSU2'})
        name = (UTF8Block(length=28), {'description': 'Texture pack name, e.g. "TRACK"'})
        file_path = (
            UTF8Block(length=64),
            {'description': 'Path of the texture pack in the original development environment'},
        )
        hash = (IntegerBlock(length=4), {'description': 'Hash of the texture pack name'})
        unk = (BytesBlock(length=24), {'is_unknown': True})


class NfsuTextureHashes(ChunkBlock):
    block_description = 'Hashes of texture names, one per texture'

    CHUNK_ID = 0x33310002

    class Fields(ChunkBlock.Fields):
        hashes = (
            records_to_chunk_end(ArrayBlock(child=IntegerBlock(length=4), length=2), 8),
            {'description': 'Texture name hash and zero, per texture'},
        )


class NfsuTextureInfo(DeclarativeCompoundBlock):
    block_description = 'Texture info: name, size, format and location of its data'

    class Fields(DeclarativeCompoundBlock.Fields):
        unk0 = (BytesBlock(length=12), {'is_unknown': True})
        name = (UTF8Block(length=24), {'description': 'Texture name'})
        name_hash = (IntegerBlock(length=4), {'description': 'Hash of the name: texture id used by meshes'})
        class_name_hash = (IntegerBlock(length=4), {'is_unknown': True})
        image_parent_hash = (IntegerBlock(length=4), {'is_unknown': True})
        image_placement = (IntegerBlock(length=4), {'description': 'Offset of image data in the data chunk'})
        palette_placement = (IntegerBlock(length=4), {'description': 'Offset of palette in the data chunk'})
        image_size = (IntegerBlock(length=4), {'description': 'Size of image data, including mipmaps'})
        palette_size = (IntegerBlock(length=4), {'description': 'Size of palette, 0 if there is no palette'})
        base_image_size = (IntegerBlock(length=4), {'description': 'Size of the full-size image (without mipmaps)'})
        width = (IntegerBlock(length=2), {'description': 'Image width'})
        height = (IntegerBlock(length=2), {'description': 'Image height'})
        shift_width = (IntegerBlock(length=1), {'description': 'Log2 of width'})
        shift_height = (IntegerBlock(length=1), {'description': 'Log2 of height'})
        image_compression_type = (
            EnumByteBlock(enum_names=NFSU_TEXTURE_COMPRESSION_TYPES),
            {'description': 'Image format. The exact format is defined by the formats chunk'},
        )
        palette_compression_type = (IntegerBlock(length=1), {'is_unknown': True})
        num_palette_entries = (IntegerBlock(length=2), {'description': 'Amount of palette colors'})
        num_mipmap_levels = (IntegerBlock(length=1), {'description': 'Amount of mipmaps'})
        tilable_uv = (IntegerBlock(length=1), {'is_unknown': True})
        bias_level = (IntegerBlock(length=1), {'is_unknown': True})
        rendering_order = (IntegerBlock(length=1), {'is_unknown': True})
        scroll_type = (IntegerBlock(length=1), {'is_unknown': True})
        used_flag = (IntegerBlock(length=1), {'is_unknown': True})
        apply_alpha_sorting = (IntegerBlock(length=1), {'is_unknown': True})
        alpha_usage_type = (IntegerBlock(length=1), {'is_unknown': True})
        alpha_blend_type = (IntegerBlock(length=1), {'is_unknown': True})
        flags = (IntegerBlock(length=1), {'is_unknown': True})
        scroll_time_step = (IntegerBlock(length=2, is_signed=True), {'is_unknown': True})
        scroll_speed_s = (IntegerBlock(length=2, is_signed=True), {'is_unknown': True})
        scroll_speed_t = (IntegerBlock(length=2, is_signed=True), {'is_unknown': True})
        offset_s = (IntegerBlock(length=2, is_signed=True), {'is_unknown': True})
        offset_t = (IntegerBlock(length=2, is_signed=True), {'is_unknown': True})
        scale_s = (IntegerBlock(length=2, is_signed=True), {'is_unknown': True})
        scale_t = (IntegerBlock(length=2, is_signed=True), {'is_unknown': True})
        unk1 = (BytesBlock(length=22), {'is_unknown': True})


class NfsuCompressedTexture(DeclarativeCompoundBlock):
    block_description = 'Location of a compressed texture in the texture pack file'

    class Fields(DeclarativeCompoundBlock.Fields):
        name_hash = (IntegerBlock(length=4), {'description': 'Hash of the texture name'})
        offset = (
            IntegerBlock(length=4),
            {
                'description': 'Offset of the compressed texture in the file (absolute: the first one is the start '
                'of texture data chunk payload)'
            },
        )
        compressed_size = (IntegerBlock(length=4), {'description': 'Size of the compressed texture'})
        size = (IntegerBlock(length=4), {'description': 'Size of the uncompressed texture'})
        flags = (IntegerBlock(length=4), {'is_unknown': True})
        unk = (IntegerBlock(length=4), {'is_unknown': True})


class NfsuCompressedTextures(ChunkBlock):
    block_description = (
        'NFSU2 compressed texture pack: locations of textures, one per texture. Every '
        'texture is compressed separately (JDLZ or HUFF) and holds its image data, followed by its texture info '
        '(124 bytes) and pixel format (32 bytes). Such a pack has no texture infos and formats chunks'
    )

    CHUNK_ID = 0x33310003

    class Fields(ChunkBlock.Fields):
        textures = (
            records_to_chunk_end(NfsuCompressedTexture(), 24),
            {'description': 'Compressed textures'},
        )


class NfsuTextureLocation(DeclarativeCompoundBlock):
    block_description = 'Where the data of a texture is in the texture data chunk (NFSU, 20 bytes)'

    class Fields(DeclarativeCompoundBlock.Fields):
        name_hash = (IntegerBlock(length=4), {'description': 'Hash of the texture name'})
        offset = (
            IntegerBlock(length=4),
            {'description': 'Offset of the texture data: the data of the next texture starts at `offset + size`'},
        )
        size = (IntegerBlock(length=4), {'description': 'Size of the texture data in bytes'})
        flags = (IntegerBlock(length=4), {'is_unknown': True, 'description': '0x100 in every file'})
        unk = (IntegerBlock(length=4), {'is_unknown': True, 'description': '0 in every file'})


class NfsuTextureLocations(ChunkBlock):
    block_description = (
        'NFSU texture pack: where the data of each texture is (20-byte records; NFSU2 and NFSMW keep their '
        'compressed textures table under this id, `NfsuCompressedTextures`). Not read by the converter: the texture '
        'infos give the data offsets'
    )

    CHUNK_ID = 0x33310003

    class Fields(ChunkBlock.Fields):
        textures = (records_to_chunk_end(NfsuTextureLocation(), 20), {'description': 'Texture data locations'})

    def matches_chunk(self, ctx) -> bool:
        # NFSU2's 24-byte records have other values there
        payload = peek_chunk_payload(ctx, peek_chunk_length(ctx))
        return (
            len(payload) > 0
            and len(payload) % 20 == 0
            and all(payload[i + 12 : i + 20] == b'\0\1\0\0\0\0\0\0' for i in range(0, len(payload), 20))
        )


class NfsuTextureInfos(ChunkBlock):
    block_description = 'Texture infos, one per texture'

    CHUNK_ID = 0x33310004

    class Fields(ChunkBlock.Fields):
        textures = (
            records_to_chunk_end(NfsuTextureInfo(), 124),
            {'description': 'Texture infos'},
        )


class NfsuTextureFormat(DeclarativeCompoundBlock):
    block_description = 'Exact pixel format of a texture'

    class Fields(DeclarativeCompoundBlock.Fields):
        unk0 = (BytesBlock(length=20), {'is_unknown': True})
        format = (
            IntegerBlock(length=4),
            {
                'description': 'Direct3D format: FourCC "DXT1" (0x31545844), "DXT3", "DXT5", 0x15 (A8R8G8B8) or 0x29 '
                '(8-bit with palette)'
            },
        )
        unk1 = (BytesBlock(length=8), {'is_unknown': True})


class NfsuTextureFormats(ChunkBlock):
    block_description = 'Pixel formats of textures, one per texture'

    CHUNK_ID = 0x33310005

    class Fields(ChunkBlock.Fields):
        formats = (
            records_to_chunk_end(NfsuTextureFormat(), 32),
            {'description': 'Formats'},
        )


class NfsuTexturePackInfo(ChunkBlock):
    block_description = 'Texture pack info container: header, hashes, infos, formats'

    CHUNK_ID = 0xB3310000

    class Fields(ChunkBlock.Fields):
        sub_chunks = chunks_field(
            [
                NfsuTexturePackHeader(),
                NfsuTextureHashes(),
                NfsuCompressedTextures(),
                NfsuTextureInfos(),
                NfsuTextureFormats(),
                ZeroChunk(),
                NfsuTextureLocations(),
            ],
            'Child chunks',
        )


class NfsuTextureData(ChunkBlock):
    block_description = 'Pixel data of all textures of the pack. Texture infos point to it'

    CHUNK_ID = 0x33320002
    ALIGNMENT = 0x80

    class Fields(ChunkBlock.Fields):
        data = (
            chunk_rest(),
            {'description': 'Image data and palettes'},
        )


class NfsuTexturePackDataContainer(ChunkBlock):
    block_description = 'Texture pack data container'

    CHUNK_ID = 0xB3320000

    class Fields(ChunkBlock.Fields):
        sub_chunks = chunks_field([NfsuTextureData(), ZeroChunk()], 'Child chunks')


class NfsuTexturePack(ChunkBlock):
    block_description = (
        'Texture pack (TPK): a container of texture infos and their pixel data. Standalone '
        'in car TEXTURES.BIN and TRACKS/TEXnnnnTRACK.BIN, embedded in track bundles'
    )
    serializer = 'NfsuTexturePackSerializer'

    CHUNK_ID = 0xB3300000

    class Fields(ChunkBlock.Fields):
        sub_chunks = chunks_field([NfsuTexturePackInfo(), NfsuTexturePackDataContainer(), ZeroChunk()], 'Child chunks')
