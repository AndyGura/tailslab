from typing import Dict

from library.read_blocks import ArrayBlock, BytesBlock, DecimalBlock, DeclarativeCompoundBlock, IntegerBlock
from resources.eac.fields.misc import Point3D

# NFS5 (Porsche Unleashed) track files next to `GameData/Track/<track>.crp`, read by Porsche.exe (nfs-web
# `decomp/nfs5/Porsche.exe.gzf`, addresses cited in the descriptions).

NFS5_JUNCTION_SIZE = 0x24
NFS5_WALL_EDGE_SIZE = 28


def is_nfs5_junctions_size(length: int) -> bool:
    return length > 0 and length % NFS5_JUNCTION_SIZE == 0


def is_nfs5_wall_edges_size(length: int) -> bool:
    return length >= 4 and (length - 4) % NFS5_WALL_EDGE_SIZE == 0


class Nfs5Junction(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'A junction of the road spline sections, 36 bytes'}

    class Fields(DeclarativeCompoundBlock.Fields):
        index = (
            IntegerBlock(length=4),
            {'description': "The junction's index (equals the record index on Alps). Not read by the game"},
        )
        end_weights = (
            ArrayBlock(child=DecimalBlock(length=4), length=8),
            {
                'description': "Weight of each of the junction's ends, in the order the game lists them (Porsche.exe "
                '0x480b40): the branch probabilities (Alps junction 1: 1.0 / 0.15 / 0.85 for the arriving section '
                'and the two leaving ones); unused slots 0. Without the file the game uses 1 / (ends on that side)'
            },
        )


class Nfs5Junctions(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Junction weights of an NFS5 track, `GameData/Track/<track>.jnc`: an array of '
            '[Nfs5Junction](#nfs5junction) (Porsche.exe 0x481080). The game builds the junctions from the sections '
            "of the road spline (the CRP's [CrpSimTPart](#crpsimtpart), 0x480900 / 0x480b40) and reads the file "
            'only when its size / 36 equals their number (every track file does: alps 6, autobahn 35, canyon 17, '
            'castle 24, coastal 6, farmland 14, foothills 6, forest 6, industrial 26, monaco1..5 4 / 6 / 11 / 10 / '
            '6, skidpad 1)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        junctions = (
            ArrayBlock(
                child=Nfs5Junction(),
                length=(lambda ctx: ctx.read_bytes_remaining // NFS5_JUNCTION_SIZE, 'file size / 36'),
            ),
            {'description': 'The junctions'},
        )

    def serializer_class(self):
        from serializers import JsonSerializer

        return JsonSerializer


class Nfs5WallEdge(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'A wall edge of the track collision, 28 bytes'}

    class Fields(DeclarativeCompoundBlock.Fields):
        flags = (
            IntegerBlock(length=1),
            {
                'description': 'Bits 4..7 of the surface flags of the faces the edge comes from (`surface_flags` of '
                'the CRP materials): 0, 0x10, 0x20, 0x30, 0x50, 0x60'
            },
        )
        unk0 = (
            BytesBlock(length=3),
            {
                'is_unknown': True,
                'description': 'Not read (Porsche.exe 0x487e80): garbage, 2 patterns on most tracks, random on '
                'monaco1, monaco2 and skidpad',
            },
        )
        p0 = (Point3D(child=DecimalBlock(length=4)), {'description': 'First end'})
        p1 = (
            Point3D(child=DecimalBlock(length=4)),
            {
                'description': 'Second end. No edge of the game files is longer than 100 in x or z (the game would '
                'turn such an edge into a 1 m stub)'
            },
        )


class Nfs5WallEdges(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Wall edges of an NFS5 track, `GameData/Track/<track>.edg`, read by Porsche.exe '
            '0x487e80 into the collision tree (`WTreeElem_Edge`). A cache: without the file the game builds the edges '
            'from all faces of the CRP (0x488590, pass 0 of 0x4750b0)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        unk0 = (
            IntegerBlock(length=4),
            {
                'is_unknown': True,
                'description': 'Not read by the game: a checksum or a count of something (29087 on alps, with 7694 '
                'edges)',
            },
        )
        edges = (
            ArrayBlock(
                child=Nfs5WallEdge(),
                length=(lambda ctx: ctx.read_bytes_remaining // NFS5_WALL_EDGE_SIZE, '(file size - 4) / 28'),
            ),
            {'description': 'The edges'},
        )

    def serializer_class(self):
        from serializers import JsonSerializer

        return JsonSerializer
