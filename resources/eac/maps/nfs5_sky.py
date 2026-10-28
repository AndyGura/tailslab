from typing import Dict

from library.read_blocks import ArrayBlock, BytesBlock, DecimalBlock, DeclarativeCompoundBlock, IntegerBlock

# NFS5 (Porsche Unleashed) track sky: GameData/Track/Sky/<track>.fsh (textures), <track>.txt (sky layers) and
# <track>.bin (this block), picked by the track name (alps.crp -> Alps.*). Porsche.exe is encrypted (SafeDisc), so
# none of this was checked against the game's code: field names come from value patterns across the 17 files and
# from how `library/utils/nfs5_sky_to_spherical.py` uses them, and stay unverified.


class Nfs5SkyBin(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Sky settings of an NFS5 track, `GameData/Track/Sky/<track>.bin`: a memory dump of '
            'a settings struct (29148 bytes, 3544 in `Monaco.bin` and `default.bin`; the tail of the bigger ones is '
            'filled with 0xCB, uninitialised memory). Not verified against the game (encrypted executable): the '
            'horizon fields are read from value patterns. The horizon texture `horz` of the FSH of the same name is '
            'cut into `strips_per_bitmap` horizontal strips, the last texel row of each one is transparent padding '
            '(`hor0`, `hor1`... are copies of it with other details). `autobahn_lightning.bin` / `industrial_lightning.bin` (5216 bytes) '
            'are another format, not read',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        version = (IntegerBlock(length=4), {'description': '9, 7 in `Monaco.bin` and `default.bin` (the old ones)'})
        unk0 = (
            DecimalBlock(length=4),
            {'is_unknown': True, 'description': '0..1 (0.86 in Alps, 0 in Foothills: not a dome height)'},
        )
        unk1 = (IntegerBlock(length=4), {'is_unknown': True, 'description': '0 or 5'})
        horizon_segments = (
            IntegerBlock(length=4),
            {
                'description': 'Amount of equal segments of the horizon cylinder around the camera (4, 2 in '
                '`default.bin`), each one showing a strip of `horizon_strips_a`'
            },
        )
        strips_per_bitmap = (
            IntegerBlock(length=4),
            {'description': 'Horizontal strips each horizon bitmap is cut into: 2 (256x128 strips), 1 in Monaco'},
        )
        horizon_bottom = (
            DecimalBlock(length=4),
            {'description': 'Height of the bottom of the horizon band, relative to the eye, world units (-182..-28)'},
        )
        horizon_top = (
            DecimalBlock(length=4),
            {'description': 'Height of the top of the horizon band, relative to the eye, world units (115..367)'},
        )
        horizon_strips_a = (
            ArrayBlock(child=IntegerBlock(length=2), length=8),
            {
                'description': 'Strip shown by each horizon segment, weather region A (default): low byte = strip '
                'index (modulo the strip count), bit 0x100 = mirrored. 0..7 in most files'
            },
        )
        horizon_strips_b = (
            ArrayBlock(child=IntegerBlock(length=2), length=8),
            {
                'description': 'Like `horizon_strips_a`, probably for weather region B (Coastal: 0x107..0x100, the '
                'strips in reverse order, mirrored)'
            },
        )
        unk2 = (DecimalBlock(length=4), {'is_unknown': True, 'description': '0..1'})
        horizon_radius = (
            DecimalBlock(length=4),
            {'description': 'Radius of the horizon cylinder around the camera, world units (500..1500)'},
        )
        unk3 = (DecimalBlock(length=4), {'is_unknown': True, 'description': '0.0002, 0.0004 in `default.bin`'})
        unk4 = (DecimalBlock(length=4), {'is_unknown': True, 'description': '44..125'})
        unk5 = (ArrayBlock(child=IntegerBlock(length=4), length=2), {'is_unknown': True, 'description': 'Zeros'})
        rest = (
            BytesBlock(length=(lambda ctx: ctx.read_bytes_remaining, 'up to end of file')),
            {
                'is_unknown': True,
                'description': 'Not decoded: 6 values at 0x54, 46 (index, value) pairs (mostly -1, 0) from 0x6C, '
                'then from 0x1E0 records of 48 bytes (two floats 0..0.3, 0, two equal RGBA colours, a float 0..1, '
                'an index growing from record to record, up to ~2100: track slices?), then 0xCB filler',
            },
        )

    def serializer_class(self):
        from serializers import JsonSerializer

        return JsonSerializer
