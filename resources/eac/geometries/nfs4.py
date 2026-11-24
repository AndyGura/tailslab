from library.read_blocks import (
    DeclarativeCompoundBlock,
    UTF8Block,
    IntegerBlock,
    ArrayBlock,
    BitFlagsBlock,
    BytesBlock,
    DecimalBlock,
    CountOf,
)
from resources.eac.fields.misc import Point3D
from resources.eac.geometries.nfs3 import Fce3Geometry, FceColor

# size of FCE4 header. Offsets of all data tables are relative to it
FCE4_HEADER_SIZE = 0x2038

# first 4 bytes of FCE4 file: NFS4: High Stakes, Motor City Online
FCE4_VERSION = 0x00101014
FCE4M_VERSION = 0x00101015

FCE4_PART_NAMES = [
    (':HB', 'high body'),
    (':MB', 'medium body'),
    (':LB', 'low body'),
    (':TB', 'tiny body'),
    (':OT', 'roof of a convertible, shown only with the top closed'),
    (':OL', 'pop-up headlights, shown with the headlights on'),
    (':OS', 'optional spoiler, turned about X by the spoiler angle'),
    (':OLB', 'left front brake'),
    (':ORB', 'right front brake'),
    (':OLM', 'left mirror, hidden once broken'),
    (':ORM', 'right mirror, hidden once broken'),
    (':OC', 'interior'),
    (':ODL', 'dashboard, drawn unlit when the headlights are on'),
    (':OH', 'driver head, turned about Y by the head angle (`animation_flags`)'),
    (':OD', 'driver holding the steering wheel, whose vertices turn about Z with the steering (`animation_flags`)'),
    (
        ':OND',
        'chair and steering wheel without driver, drawn instead of ":OD" and ":OH" when the driver is out of the car',
    ),
    (
        ':HLFW',
        'high left front wheel ("M" instead of "H" for medium wheels, "R" instead of "L" for right, '
        '"M"/"R" instead of "F" for middle/rear)',
    ),
]


class Fce4Color(FceColor):
    """The same as FCE3 color, but every component is 1 byte"""

    class Fields(DeclarativeCompoundBlock.Fields):
        hue = (IntegerBlock(length=1), {'description': 'Hue'})
        saturation = (IntegerBlock(length=1), {'description': 'Saturation'})
        brightness = (IntegerBlock(length=1), {'description': 'Brightness'})
        transparency = (IntegerBlock(length=1), {'description': 'Transparency'})


class Fce4Triangle(DeclarativeCompoundBlock):
    block_description = 'A single triangle of FCE4 mesh'

    class Fields(DeclarativeCompoundBlock.Fields):
        tex_page = (
            IntegerBlock(length=4),
            {
                'description': 'Texture page index. 0 for car models (texture car00.tga), other values are used '
                'by multi-texture models like police officers and pursuit road objects'
            },
        )
        vertex_indices = (
            ArrayBlock(child=IntegerBlock(length=4), length=3),
            {
                'description': 'Vertex indices, local to the part: add `part_first_vertex` of the part to get index '
                'in `vertices`'
            },
        )
        unk0 = (ArrayBlock(child=IntegerBlock(length=4), length=3), {'is_unknown': True})
        flags = (
            BitFlagsBlock(
                length=4,
                flag_names=[
                    (0, 'matte'),
                    (1, 'high_chrome'),
                    (2, 'no_cull'),
                    (3, 'semi_transparent'),
                    (5, 'window'),
                    (6, 'front_window'),
                    (7, 'left_window'),
                    (8, 'back_window'),
                    (9, 'right_window'),
                    (10, 'broken_window'),
                ],
            ),
            {
                'description': 'Triangle flags, nfs4.exe reads the lower 16 bits. "matte": no environment reflection '
                '(underbody), "high_chrome": strong reflection (windows), "no_cull": triangle is visible from both '
                'sides, "semi_transparent": translucent triangle (windows). Triangle is visible behind a '
                'semi-transparent triangle only if it has smaller index. Chrome: nfs4.exe draws a second, environment '
                'mapped pass over the parts ":HB", ":MB", ":LB", ":OC", ":ODL", ":OLM", ":ORM", ":OS", ":OT", ":OL" '
                '(Render_CarParts 0x50dd60; not the wheels, brakes, driver nor ":TB") with the track\'s chrome texture '
                '(sky.qfs CHRD) at sphere map coordinates of the vertex `normals`, as nfs3.exe: none for "matte" '
                '(polygon flag 4, 0x4eee40), the high colour for "high_chrome" (flag 8), the normal colour for the '
                'others (CarDraw_QueuePolys 0x4f0a70), both from the track light under the car, the sky top colour '
                'and the paint (Render_CarChrome 0x50d6f0), texel x colour (alphas too) added to the framebuffer '
                '(source alpha, one). The export splits the triangles of those parts by these classes, mesh name '
                'suffix "_matte" / "_high_chrome" (before the window suffix), node extras {"fceChrome": "normal" | '
                '"high" | "none"}. Windows (Fce_BreakWindows 0x4ed0e0, run on a '
                'part after a hit damaged its vertices): a triangle with any of the bits 5..9 (0x3e0) is a window '
                'triangle, the bits 6..9 are its sides: "front_window", "left_window", "back_window", "right_window" '
                '(one or none in the NFS4 cars, but for a triangle of traffic/sedan2 and one of traffic/snowplow with '
                'two; "window" is set on most of them). The window triangles with a damaged vertex crack, and so do '
                'all window triangles of the part sharing a side with one of them: they are '
                'drawn with the broken glass texture "shat" of Data/FeArt/3dobj.fsh, texture coordinates (0, 0), '
                '(0, 1), (1, 1) at their vertices 0, 1, 2. "broken_window" (bit 10): the glass breaks away: the '
                'triangle is no longer drawn once its side was hit hard (vertex 0 of a damaged window triangle of '
                'that side with a damage weight over 0.5, `reserve4`); the software renderer draws it on. The export '
                'puts the window triangles of every class into meshes of their own, named '
                '"..._window[_front][_left][_back][_right][_breakaway]", node extras '
                '{"fceWindow": {"sides": [...], "breaksAway": ...}}'
            },
        )
        u = (
            ArrayBlock(child=DecimalBlock(length=4), length=3),
            {'description': 'Texture U coordinates of 3 vertices, 0..1'},
        )
        v = (
            ArrayBlock(child=DecimalBlock(length=4), length=3),
            {'description': 'Texture V coordinates of 3 vertices, 0..1, from top to bottom'},
        )


# tables of FCE4 file in their usual order: (name, size per vertex, size per triangle)
FCE4_TABLES = [
    ('vertices', 12, 0),
    ('normals', 12, 0),
    ('triangles', 0, 56),
    ('reserve1', 32, 0),
    ('reserve2', 12, 0),
    ('reserve3', 12, 0),
    ('undamaged_vertices', 12, 0),
    ('undamaged_normals', 12, 0),
    ('damaged_vertices', 12, 0),
    ('damaged_normals', 12, 0),
    ('reserve4', 4, 0),
    ('animation_flags', 4, 0),
    ('reserve5', 4, 0),
    ('reserve6', 0, 12),
]


def _standard_offset(ctx, table: str) -> int:
    num_vertices = len(ctx.data('vertices'))
    num_triangles = len(ctx.data('triangles'))
    offset = 0
    for name, vertex_size, triangle_size in FCE4_TABLES:
        if name == table:
            return offset
        offset += vertex_size * num_vertices + triangle_size * num_triangles
    raise ValueError(table)


def _vector_table(description: str):
    return (
        ArrayBlock(child=Point3D(child=DecimalBlock(length=4)), length='num_vertices'),
        {'description': description},
    )


def _offset_field(table: str, description: str):
    return (
        IntegerBlock(length=4, programmatic_value=lambda ctx: _standard_offset(ctx, table)),
        {'usage': 'io,doc', 'description': description},
    )


class Fce4Geometry(DeclarativeCompoundBlock):
    block_description = (
        'FCE 3D model, version 4 (NFS4: High Stakes, Motor City Online). Used for cars '
        '(car.fce in car.viv), dashboards (dash.fce), police officers, helicopter, menu models. Consists of up '
        'to 64 parts, each of them is a separate mesh with own position, and up to 16 "dummies": named points, '
        'which are used for lights, license plates, smoke and water effects. In addition to FCE3, every vertex '
        'has a "damaged" position, used when car is crashed. Coordinate system: X points right, Y up, Z '
        'forward. The unit is meter. Texture is a TGA image car00.tga, which is located next to car.fce in '
        'car.viv. Alpha channel of the texture defines which car color is applied to the pixel (nfs4.exe '
        '0x4ee620): 0xff none, 0xc4..0xfe primary, 0x80..0xc3 interior, 0x40..0x7f secondary, 0x01..0x3f driver '
        'hair, 0 a transparent pixel. The interior, secondary and hair colors are those of the color set whose '
        'primary color is the nearest to the chosen one (0x4ef310). A painted pixel is shaded as in NFS3 '
        "(0x4ee550 = nfs3.exe 0x49cc50): the color's brightness times the pixel's blue (5 bits) / (255 - "
        'transparency), times the blue when transparency is 255, at most 255'
    )
    serializer = 'Fce4GeometrySerializer'

    class Fields(DeclarativeCompoundBlock.Fields):
        version = (
            IntegerBlock(length=4),
            {'description': 'Format version. 0x00101014 in NFS4, 0x00101015 in Motor City Online (FCE4M)'},
        )
        unk0 = Fce3Geometry.Fields.unk0
        num_triangles = Fce3Geometry.Fields.num_triangles
        num_vertices = Fce3Geometry.Fields.num_vertices
        num_arts = Fce3Geometry.Fields.num_arts
        vertices_offset = _offset_field(
            'vertices',
            'Offset of vertices table, relative to header end (0x2038). Tables go one after another in order: '
            'vertices, normals, triangles, reserved areas 1-3, undamaged vertices, undamaged normals, damaged '
            'vertices, damaged normals, reserved area 4, animation flags, reserved areas 5-6',
        )
        normals_offset = _offset_field('normals', 'Offset of normals table, relative to header end')
        triangles_offset = _offset_field('triangles', 'Offset of triangles table, relative to header end')
        reserve1_offset = _offset_field('reserve1', 'Offset of reserved area 1, relative to header end')
        reserve2_offset = _offset_field('reserve2', 'Offset of reserved area 2, relative to header end')
        reserve3_offset = _offset_field('reserve3', 'Offset of reserved area 3, relative to header end')
        undamaged_vertices_offset = _offset_field(
            'undamaged_vertices', 'Offset of undamaged vertices table, relative to header end'
        )
        undamaged_normals_offset = _offset_field(
            'undamaged_normals', 'Offset of undamaged normals table, relative to header end'
        )
        damaged_vertices_offset = _offset_field(
            'damaged_vertices', 'Offset of damaged vertices table, relative to header end'
        )
        damaged_normals_offset = _offset_field(
            'damaged_normals', 'Offset of damaged normals table, relative to header end'
        )
        reserve4_offset = _offset_field('reserve4', 'Offset of reserved area 4, relative to header end')
        animation_flags_offset = _offset_field(
            'animation_flags', 'Offset of vertex animation flags table, relative to header end'
        )
        reserve5_offset = _offset_field('reserve5', 'Offset of reserved area 5, relative to header end')
        reserve6_offset = _offset_field('reserve6', 'Offset of reserved area 6, relative to header end')
        half_size = (
            Point3D(child=DecimalBlock(length=4)),
            {
                'description': 'Half-size of the whole model (bounding box) along x (right), y (up), z (forward), at '
                "header +0x4c: nfs4.exe uses it as the half extents of the car's rigid body box (Car_Reset 0x4448d0 "
                'copies it into the game setup car and passes it to the body setup 0x4f4a20; human players take the '
                "front end's copy, the FCE's with game setup flag 2). Half the extent of the parts' vertices in 34 of "
                'the 41 NFS4 car models (the others within a few cm). The gg-web-engine export writes it as it is, in '
                'these axes, to `collisionHalfSize` of the `.meta` (the GLB has y and z swapped: x right, y forward, '
                'z up)'
            },
        )
        num_dummies = Fce3Geometry.Fields.num_dummies
        dummy_positions = Fce3Geometry.Fields.dummy_positions
        num_parts = Fce3Geometry.Fields.num_parts
        part_positions = (
            Fce3Geometry.Fields.part_positions[0],
            {
                'description': 'Positions of parts. Vertices of the part are relative to it. Only first `num_parts` '
                'are used. nfs4.exe turns ":OS" (about X), ":OD" (about Z) and ":OH" (about Y) about them, and tests '
                'the mirrors ":OLM", ":ORM" for breaking at theirs. Exported as `fcePartPositions` of the `.meta` and '
                'of the OBJ\'s extra JSON (mesh name prefix "<lod>_<part index>_<name>" -> [x, y, z], the GLB axes: x '
                'right, y forward, z up)'
            },
        )
        part_first_vertex = Fce3Geometry.Fields.part_first_vertex
        part_num_vertices = Fce3Geometry.Fields.part_num_vertices
        part_first_triangle = Fce3Geometry.Fields.part_first_triangle
        part_num_triangles = Fce3Geometry.Fields.part_num_triangles
        num_colors = (
            IntegerBlock(length=4),
            {
                'description': 'Number of car colors, 0..16. Every color is a set of 4 colors with the same index in '
                'tables below'
            },
        )
        primary_colors = (
            ArrayBlock(child=Fce4Color(), length=16),
            {'description': 'Primary car colors (car body). Only first `num_colors` are used'},
        )
        interior_colors = (
            ArrayBlock(child=Fce4Color(), length=16),
            {'description': 'Interior colors. Only first `num_colors` are used'},
        )
        secondary_colors = (
            ArrayBlock(child=Fce4Color(), length=16),
            {'description': 'Secondary car colors. Only first `num_colors` are used'},
        )
        driver_hair_colors = (
            ArrayBlock(child=Fce4Color(), length=16),
            {'description': 'Driver hair colors. Only first `num_colors` are used'},
        )
        unk1 = (BytesBlock(length=260), {'is_unknown': True})
        dummy_names = (
            ArrayBlock(child=UTF8Block(length=64), length=16),
            {
                'description': 'Names of dummies. The name defines what the dummy is. Special names: ":LICENSE", '
                '":LICMED", ":LICLOW" (license plate in high/medium/low LOD), ":LICENSE_EURO" (long license plate), '
                '":SMOKE" (smoke when shifting gears), ":WATER" (water generator). Other dummies are lights, where '
                'every letter is a property: 1st is kind ("H": headlight, "T": taillight, "B": brake light, "R": '
                'reverse light, "P": direction indicator, "S": siren), 2nd is color ("W": white, "R": red, "B": blue, '
                '"O": orange, "Y": yellow), 3rd is "Y"/"N" for breakable or not, 4th is flashing mode ("O"/"E" for '
                'odd/even flashing, "N" for no flashing), 5th is intensity 0..9, 6th and 7th are flashing time and '
                'delay 0..9'
            },
        )
        part_names = (
            ArrayBlock(child=UTF8Block(length=64), length=64),
            {
                'description': 'Names of parts. For car models, the role of the part is defined by its name: '
                + ', '.join(f'"{name}": {description}' for name, description in FCE4_PART_NAMES)
            },
        )
        unk2 = (BytesBlock(length=528), {'is_unknown': True})
        vertices = _vector_table('Vertex positions, relative to position of their part')
        normals = _vector_table(
            'Vertex normals, the ones the chrome pass reads (CarDraw_Part 0x4f0e00 -> CarDraw_EnvMapUVs 0x4f09d0, '
            'sphere map coordinates as nfs3.exe). Exported for the parts with chrome (see the triangle `flags`): OBJ '
            '`vn`, GLB vertex attribute `_GAME_NORMAL` (game axes swapped as the vertices)'
        )
        triangles = (
            ArrayBlock(child=Fce4Triangle(), length='num_triangles'),
            {'description': 'Triangles'},
        )
        reserve1 = (
            BytesBlock(length=(lambda ctx: 32 * ctx.data('num_vertices'), '32 * num_vertices')),
            {'is_unknown': True},
        )
        reserve2 = (
            BytesBlock(length=(lambda ctx: 12 * ctx.data('num_vertices'), '12 * num_vertices')),
            {
                'description': 'Run time slot of 3 floats per vertex: Fce_DamageVertices (nfs4.exe 0x4ed390) keeps '
                'the undamaged vertex + its part position - the hit point there'
            },
        )
        reserve3 = (
            BytesBlock(length=(lambda ctx: 12 * ctx.data('num_vertices'), '12 * num_vertices')),
            {'is_unknown': True},
        )
        undamaged_vertices = _vector_table(
            'Undamaged vertex positions, a copy of `vertices` (in every NFS4 car): the run time copy nfs4.exe blends '
            'the damaged parts from (Fce_DamageVertices 0x4ed390)'
        )
        undamaged_normals = _vector_table(
            "Undamaged vertex normals, a copy of `normals`: the run time copy the damaged parts' normals are blended "
            'from'
        )
        damaged_vertices = _vector_table(
            'Vertex positions of crashed car, relative to position of their part. nfs4.exe blends the vertices of '
            '":HB", ":MB", ":LB", ":OL" and ":OT" (only those, Car_DamageVisual 0x44a510) from `undamaged_vertices` to '
            "these by their damage weight (`reserve4`, Fce_DamageVertices 0x4ed390); the other parts' damaged "
            'positions are not used. Exported as a copy of every mesh, "<mesh>_damaged", and on the GLB meshes of '
            'those parts as the morph target "damaged" (the delta to `vertices`; models with damaged positions only)'
        )
        damaged_normals = _vector_table(
            'Vertex normals of crashed car: Fce_DamageVertices (nfs4.exe 0x4ed390) blends `normals` of the damaged '
            'parts from `undamaged_normals` to these by the damage weight of the vertex, as the positions, not '
            'normalized. Exported for the parts with chrome: GLB vertex attribute `_GAME_NORMAL_DAMAGED` of the '
            'meshes with the morph target "damaged" (the same vertices), OBJ `vn` of the "<mesh>_damaged" copies'
        )
        reserve4 = (
            BytesBlock(length=(lambda ctx: 4 * ctx.data('num_vertices'), '4 * num_vertices')),
            {
                'description': 'Run time slot of a float per vertex: its damage weight, 0..1, by which '
                'Fce_DamageVertices (nfs4.exe 0x4ed390) blends it from `undamaged_vertices` to `damaged_vertices`'
            },
        )
        animation_flags = (
            ArrayBlock(child=IntegerBlock(length=4), length='num_vertices'),
            {
                'description': 'Vertex animation flags. Bit 2 (4): the vertex stays put; the vertices without it turn '
                'with their part: on ":OD" (driver holding the steering wheel) the steering wheel\'s vertices (12 in '
                'most cars) turn with the steering, about Z (forward) through the part position, on ":OH" (driver '
                'head) all vertices turn with the head, about Y (up) through the part position. Bit 0: set by nfs4.exe '
                'at run time on a vertex it damaged (Fce_DamageVertices 0x4ed390). Exported for ":OD" and ":OH" as '
                "the GLB vertex attribute `_FCE_TURNS` (255: turns, 0: stays) and `fceTurns` of the OBJ's extra JSON "
                '(OBJ object name -> 1 or 0 per face corner, in file order)'
            },
        )
        reserve5 = (
            BytesBlock(length=(lambda ctx: 4 * ctx.data('num_vertices'), '4 * num_vertices')),
            {'is_unknown': True},
        )
        reserve6 = (
            BytesBlock(
                length=(
                    lambda ctx: (
                        12 * ctx.data('num_triangles')
                        + (ctx.data('num_vertices') if ctx.data('version') == FCE4M_VERSION else 0)
                    ),
                    '12 * num_triangles (+ num_vertices in FCE4M)',
                )
            ),
            {'is_unknown': True},
        )
