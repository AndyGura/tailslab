from library.read_blocks import ArrayBlock, BytesBlock, DecimalBlock, DeclarativeCompoundBlock, IntegerBlock

# NFS5 (Porsche Unleashed) track sky: GameData/Track/Sky/<track>.fsh (textures), <track>.txt (sky layers) and
# <track>.bin (this block), picked by the track name (alps.crp -> Alps.*). Fields checked against the unprotected
# Porsche.exe (nfs-web decomp/nfs5): SkyHorizon FUN_00459b50 / FUN_00459d30, dome mesh FUN_00460ec0 / FUN_00460f40
# (called from BasicSky FUN_0045adf0 and MultinormalSky FUN_0045b5a0); see library/utils/nfs5_sky_to_spherical.py.


class Nfs5SkyBin(DeclarativeCompoundBlock):
    block_description = (
        'Sky settings of an NFS5 track, `GameData/Track/Sky/<track>.bin`: a memory dump of '
        'a settings struct (29148 bytes, 3544 in `Monaco.bin` and `default.bin`; the tail of the bigger ones is '
        'filled with 0xCB, uninitialised memory). Checked against Porsche.exe (the unprotected one): '
        'the horizon is 16 flat quads on a cylinder of radius 400 around the eye, each showing a cell of the '
        'horizon texture `horz` of the FSH of the same name, coloured by `hzcl` (16x2: top and bottom vertex '
        'colours); the sky levels of the `.txt` are drawn on a dome, a 16x16 vertex grid curved down from its '
        'centre (`hor0`, `hor1`... are copies of `horz` with other details, their use not traced). '
        '`autobahn_lightning.bin` / `industrial_lightning.bin` (5216 bytes) '
        'are another format, not read'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        version = (IntegerBlock(length=4), {'description': '9, 7 in `Monaco.bin` and `default.bin` (the old ones)'})
        horizon_rotation = (
            DecimalBlock(length=4),
            {'description': "Heading of the horizon cylinder's point 0, turns clockwise from +Z (0..1)"},
        )
        horizon_colour_start = (
            IntegerBlock(length=4),
            {
                'description': 'Column of `hzcl` that colours point 0 of the horizon (0 or 5); point k takes column '
                '(start + k) % 16'
            },
        )
        horizon_cell_columns = (
            IntegerBlock(length=4),
            {'description': 'Columns of cells the horizon bitmap `horz` is cut into (4, 2 in `default.bin`)'},
        )
        horizon_cell_rows = (
            IntegerBlock(length=4),
            {'description': 'Rows of cells of `horz` (2, 1 in the Monaco files)'},
        )
        horizon_bottom = (
            DecimalBlock(length=4),
            {
                'description': 'Height of the bottom of the horizon band relative to the eye, on the cylinder of radius '
                '400 (-182..-28)'
            },
        )
        horizon_height = (
            DecimalBlock(length=4),
            {'description': 'Height of the horizon band (115..367): its top is at `horizon_bottom` + this'},
        )
        horizon_cells = (
            ArrayBlock(child=IntegerBlock(length=2), length=16),
            {
                'description': 'Cell of `horz` shown by each of the 16 horizon quads (1/16 turn each, from point i '
                'to point i + 1): low byte = cell index (column index % `horizon_cell_columns`, row index / '
                '`horizon_cell_columns`), high byte nonzero (0x100) = mirrored'
            },
        )
        dome_rotation = (
            DecimalBlock(length=4),
            {'description': 'Rotation of the sky dome grid around Y, turns (0..1)'},
        )
        dome_size = (
            DecimalBlock(length=4),
            {'description': 'Side of the square 16x16 vertex grid of the sky dome (500..1500), centred on the eye'},
        )
        dome_curvature = (
            DecimalBlock(length=4),
            {
                'description': 'k of the dome height h - k (a^2 + b^2) at grid position (a, b) (0.0002, 0.0004 in '
                '`default.bin`)'
            },
        )
        dome_height = (
            DecimalBlock(length=4),
            {'description': 'h: height of the dome above the eye at its centre (44..125)'},
        )
        unk0 = (ArrayBlock(child=IntegerBlock(length=4), length=2), {'is_unknown': True, 'description': 'Zeros'})
        unk1 = (
            BytesBlock(length=0xB3C - 0x54),
            {
                'is_unknown': True,
                'description': 'Not decoded: 6 values at 0x54, 46 (index, value) pairs (mostly -1, 0) from 0x6C, '
                'then from 0x1E0 records of 48 bytes (two floats 0..0.3, 0, two equal RGBA colours, a float 0..1, '
                'an index growing from record to record: track slices?)',
            },
        )
        water_dome_rotation = (
            DecimalBlock(length=4),
            {'description': "Like `dome_rotation`, for the `...water` sky level types (none in the game's files)"},
        )
        water_dome_size = (DecimalBlock(length=4), {'description': 'Like `dome_size`, water levels'})
        water_dome_curvature = (
            DecimalBlock(length=4),
            {'description': 'Like `dome_curvature`, water levels (negative: a bowl below the eye)'},
        )
        water_dome_height = (DecimalBlock(length=4), {'description': 'Like `dome_height`, water levels (-75, -25)'})
        unk2 = (BytesBlock(length=0xCE4 - 0xB4C), {'is_unknown': True, 'description': 'Not decoded'})
        dome_scale = (
            DecimalBlock(length=4),
            {
                'description': 'Scale of the whole dome mesh (0.1..1.5; the water dome has 1): changes no direction '
                'from the eye'
            },
        )
        rest = (
            BytesBlock(length=(lambda ctx: ctx.read_bytes_remaining, 'up to end of file')),
            {
                'is_unknown': True,
                'description': 'Not decoded (other sky objects read structs at 0xDDC, 0x1A5C, 0x655C, beyond the '
                'end of the 3544-byte files), then 0xCB filler',
            },
        )

    def serializer_class(self):
        from serializers import JsonSerializer

        return JsonSerializer
