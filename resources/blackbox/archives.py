from library.read_blocks import BytesBlock
from resources.eac.archives import EacCompressedBlock


class NfsuJdlzCompressedBlock(EacCompressedBlock):
    """JDLZ-compressed file of NFS Underground (*.lzc). Uncompressed data is usually a chunk bundle"""

    block_description = 'JDLZ-compressed data (LZ77 variant with "JDLZ" header): NFS Underground *.lzc files'

    def __init__(self, **kwargs):
        from resources.blackbox.maps.nfsu import NfsuChunkBundle, NfsuTrackBundle
        from resources.eac.compressions.jdlz import JdlzCompression

        super().__init__(
            possible_blocks=[
                NfsuTrackBundle(),
                NfsuChunkBundle(),
                BytesBlock(length=(lambda ctx: ctx.read_bytes_amount)),
            ],
            compression=JdlzCompression(),
            **kwargs,
        )


class Nfs6Ps2CompressedBlock(EacCompressedBlock):
    """COMP-compressed file of NFS Hot Pursuit 2 (PS2, *.LZC). Uncompressed data is a chunk bundle"""

    block_description = 'COMP-compressed data (LZ77 with "COMP" header): NFS Hot Pursuit 2 (PS2) *.LZC files'

    def __init__(self, **kwargs):
        from resources.blackbox.maps.nfs6_ps2 import Nfs6Ps2CarGeometry, Nfs6Ps2ChunkBundle, Nfs6Ps2TrackBundle
        from resources.eac.compressions.comp import CompCompression

        # the bundle blocks subclass Nfs6Ps2ChunkBundle: the loader's class itself, not the first subclass of it (a
        # plain bundle such as GLOBAL/GLOBALB.LZC is no track)
        super().__init__(
            possible_blocks=[
                Nfs6Ps2TrackBundle(),
                Nfs6Ps2CarGeometry(),
                Nfs6Ps2ChunkBundle(),
                BytesBlock(length=(lambda ctx: ctx.read_bytes_amount)),
            ],
            compression=CompCompression(),
            exact_class=True,
            **kwargs,
        )
