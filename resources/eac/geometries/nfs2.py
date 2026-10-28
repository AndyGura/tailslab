from typing import Dict

from library.read_blocks import (
    DeclarativeCompoundBlock,
    UTF8Block,
    IntegerBlock,
    ArrayBlock,
    SubByteCompoundBlock,
    FixedPointBlock,
    Padding,
)
from library.read_blocks.misc.value_validators import Eq
from resources.eac.fields.misc import Point3D

# "Verified" in the descriptions below: read in the NFS2 SE executable (nfs2sen.exe, software renderer, nfs-web
# `decomp/nfs2` Ghidra project): GEO loader `R3DCar_LoadGeo` 0x45b860, part render info `R3DCar_SetMeshRenderInfo`
# 0x45b830, polygon builder `Transfmr_AddMeshPolys` 0x46f570, texture setup `CarIO_SetupTextures` 0x463900. Checked
# against every GEO of NFS2 (`CARMODEL/PC/*.GEO`) and NFS2 SE (`SIM/CARDATA/CARDATA.VIV`)


class GeoPolygon(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A single polygon of the mesh. Texture coordinates seem to be hardcoded in game:'
            'for triangles `[[0, 0], [1, 0], [1, 1]]` if "uv_flip" else '
            '`[[0, 1], [1, 1], [1, 0]]`, for quads `[[0, 1], [1, 1], [1, 0], [0, 0]]` if '
            '"uv_flip" else `[[0, 0], [1, 0], [1, 1], [0, 1]]`',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        mapping = (
            SubByteCompoundBlock(
                length=1,
                schema=[
                    (
                        3,
                        'num_frames',
                        'number',
                        [],
                        'Number of animation frames of the texture, 0 means 1 (verified)',
                    ),
                    (1, 'double_sided', 'boolean', [], 'Drawn from both sides (verified)'),
                    (1, 'color_keyed', 'boolean', [], 'Colour-keyed (transparent) texture (inferred)'),
                    (1, 'flip_normal', 'boolean', [], 'Vertices taken in reverse order (verified)'),
                    (1, 'uv_flip', 'boolean', [], 'Other texture coordinates; not read by the renderer'),
                    (1, 'is_triangle', 'boolean', [], 'Triangle: 3 vertices (verified)'),
                ],
            ),
            {
                'description': 'Polygon properties. Bit 0 "is_triangle": a triangle, the 4th vertex is not used '
                '(verified). Bit 1 "uv_flip": changes the texture coordinates (as the converter maps them, which '
                'looks right); the renderer does not read it, `R3DCar_LoadGeo` checks it only on the first polygon '
                'of the rear wheel parts 16 and 18 before moving that quad 5/256 m outwards ("Fixing Wheels"; set '
                'there in every race car). Bit 2 "flip_normal": the game takes the vertices in reverse order, quad '
                '0, 3, 2, 1, triangle 2, 1, 0 (verified, `Transfmr_AddMeshPolys`). Bit 3 "color_keyed": the '
                'renderer uses another polygon type for it (9 / 0xD instead of 8 / 0xC, verified); set on the '
                'polygons whose textures have transparent pixels (tyre quads, inner wheel parts, ground part, some '
                'grilles and spoilers), so most likely the colour-keyed (transparent) texture mode: inferred, the '
                'rasterizer was not followed. Bit 4 "double_sided": drawn from both sides, the game marks the polygon '
                'two-sided (verified). Bits 5-7 "num_frames": number of animation frames, 0 means 1 (verified, '
                '`CarIO_SetupTextures`): the texture of frame k is `texture_name` with its 2nd character + k '
                '(`m000`, `m100`, `m200`, `m300`; `l000`, `l100`). Used by the tyres (wheel parts 12, 14, 16, 18, 4 '
                'frames picked by the speed) and the brake lights (part 11, 2 frames, frame 1 while braking)'
            },
        )
        unk0 = (
            IntegerBlock(length=3),
            {
                'description': 'Run time fields the game writes at load (verified): byte 1 of the polygon = current '
                'animation frame, u16 at byte 2 = index of the first texture. The values in the files mean nothing '
                '(mostly 0)',
                'is_unknown': True,
            },
        )
        vertex_indices = (ArrayBlock(child=IntegerBlock(length=1), length=4), {'description': 'Indexes of vertices'})
        texture_name = (UTF8Block(length=4), {'description': 'ID of texture from neighbouring QFS file'})


class GeoMesh(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'A single mesh, can use multiple textures'}

    class Fields(DeclarativeCompoundBlock.Fields):
        num_vrtx = (IntegerBlock(length=4), {'description': 'number of vertices in block'})
        num_plgn = (IntegerBlock(length=4), {'description': 'number of polygons in block'})
        pos = (
            Point3D(child=FixedPointBlock(length=4, fraction_bits=16, is_signed=True)),
            {
                'description': 'position of part in 3d space (pivot of the mesh, vertices are relative to it). The '
                'unit is meter'
            },
        )
        unk0 = (
            IntegerBlock(length=4),
            {
                'description': 'Run time slot (+0x14): `R3DCar_LoadGeo` writes the pointer to the vertices here '
                '(verified). The value in the file means nothing',
                'is_unknown': True,
            },
        )
        unk1 = (
            IntegerBlock(length=4),
            {
                'description': 'Run time slot (+0x18): `R3DCar_LoadGeo` writes the pointer to the polygons here '
                '(verified). The value in the file means nothing',
                'is_unknown': True,
            },
        )
        unk2 = (
            IntegerBlock(length=8, value_validator=Eq(0)),
            {
                'description': 'At +0x1c. Bytes 0x1e..0x33 of the part header (the last 6 bytes of this field, '
                '`unk3` and `unk4`) are overwritten at run time with render info of the part from a table of the '
                'executable (`R3DCar_SetMeshRenderInfo` 0x45b830, verified): u16 at +0x1e, draw layer at +0x20, '
                'four view angle limits at +0x24..+0x30. The values in the files are these constants',
                'is_unknown': True,
            },
        )
        unk3 = (
            IntegerBlock(length=8, value_validator=Eq(1)),
            {'description': 'At +0x24, overwritten at run time, see `unk2`', 'is_unknown': True},
        )
        unk4 = (
            IntegerBlock(length=8, value_validator=Eq(1)),
            {'description': 'At +0x2c, overwritten at run time, see `unk2`', 'is_unknown': True},
        )
        vertices = (
            ArrayBlock(
                length=lambda ctx: ctx.data('num_vrtx'),
                child=Point3D(child=FixedPointBlock(length=2, fraction_bits=8, is_signed=True)),
            ),
            {'description': 'Vertex coordinates. The unit is meter'},
        )
        offset = (
            Padding(to=(lambda ctx: 52 + (ctx.data('num_vrtx') + 1) // 2 * 12, '52 + ceil(num_vrtx/2)*12')),
            {'description': 'Data offset, happens when `num_vrtx` is odd'},
        )
        polygons = (
            ArrayBlock(length=lambda ctx: ctx.data('num_plgn'), child=GeoPolygon()),
            {'description': 'Array of mesh polygons'},
        )


class GeoGeometry(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A set of 3D meshes, used for cars and props. Contains multiple meshes with '
            'high details, medium and low LOD-s. Textures are in a separate QFS archive: '
            '<name>.QFS next to the GEO file (NFS2), or CARMODEL/PC/<name>.QFS for GEO '
            'items of CARDATA.VIV (NFS2SE)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        unk0 = (
            IntegerBlock(length=4),
            {'description': 'Not read by the game (verified: the parts start at 0x8c)', 'is_unknown': True},
        )
        unk1 = (
            ArrayBlock(child=IntegerBlock(length=4), length=32),
            {'description': 'Not read by the game (verified)', 'is_unknown': True},
        )
        unk2 = (
            IntegerBlock(length=8),
            {'description': 'Not read by the game (verified)', 'is_unknown': True},
        )
        parts = (
            ArrayBlock(child=GeoMesh(), length=32),
            {
                'description': 'Array of 32 body parts: 20 high poly, 3 medium poly, 3 low poly and 6 reserved '
                'spaces. Description of each of them:<br/>'
                '0: High-Poly Additional Body Part<br/>'
                '1: High-Poly Main Body Part<br/>'
                '2: High-Poly Ground Part<br/>'
                '3: High-Poly Front Part<br/>'
                '4: High-Poly Back Part<br/>'
                '5: High-Poly Left Side Part<br/>'
                '6: High-Poly Right Side Part<br/>'
                '7: High-Poly Additional Left Side Part<br/>'
                '8: High-Poly Additional Right Side Part<br/>'
                '9: High-Poly Spoiler Part (drawn as an object of its own, hidden from some view angles)<br/>'
                '10: High-Poly Additional Part<br/>'
                '11: High-Poly Backlights (its polygons with animation frames are the brake lights)<br/>'
                '12: High-Poly Front Right Wheel (right = +x; the first polygon is the tyre quad, 4 tyre frames)<br/>'
                '13: High-Poly Front Right Inner Wheel Part (drawn before everything else)<br/>'
                '14: High-Poly Front Left Wheel (the first polygon is the tyre quad, 4 tyre frames)<br/>'
                '15: High-Poly Front Left Inner Wheel Part (drawn before everything else)<br/>'
                '16: High-Poly Rear Right Wheel (the first polygon is the tyre quad, 4 tyre frames)<br/>'
                '17: High-Poly Rear Right Inner Wheel Part (drawn before everything else)<br/>'
                '18: High-Poly Rear Left Wheel (the first polygon is the tyre quad, 4 tyre frames)<br/>'
                '19: High-Poly Rear Left Inner Wheel Part (drawn before everything else)<br/>'
                '20: Medium-Poly Additional Body Part<br/>'
                '21: Medium-Poly Main Body Part<br/>'
                '22: Medium-Poly Ground Part<br/>'
                '23: Low-Poly Wheel Part<br/>'
                '24: Low-Poly Main Part<br/>'
                '25: Low-Poly Side Part<br/>'
            },
        )

    def serializer_class(self):
        from serializers import GeoGeometrySerializer

        return GeoGeometrySerializer
