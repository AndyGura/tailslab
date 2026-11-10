from io import BytesIO
from typing import Dict

from library.read_blocks import BytesBlock
from resources.eac.archives import EacCompressedBlock


class NfsuJdlzCompressedBlock(EacCompressedBlock):
    """JDLZ-compressed file of NFS Underground (*.lzc). Uncompressed data is usually a chunk bundle"""

    def __init__(self, **kwargs):
        from resources.blackbox.maps.nfsu import NfsuChunkBundle, NfsuTrackBundle

        super(EacCompressedBlock, self).__init__(
            possible_blocks=[
                NfsuTrackBundle(),
                NfsuChunkBundle(),
                BytesBlock(length=(lambda ctx: ctx.read_bytes_amount)),
            ],
            **kwargs,
        )

    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'JDLZ-compressed data (LZ77 variant with "JDLZ" header): NFS Underground *.lzc files',
        }

    def _detect_compression(self, buffer):
        from resources.eac.compressions.jdlz import JdlzCompression

        return JdlzCompression()

    def compress(self, uncompressed_bytes: bytes, data) -> bytes:
        from resources.eac.compressions.jdlz import JdlzCompression

        return JdlzCompression().compress(BytesIO(uncompressed_bytes), len(uncompressed_bytes))


class Nfs6Ps2CompressedBlock(EacCompressedBlock):
    """COMP-compressed file of NFS Hot Pursuit 2 (PS2, *.LZC). Uncompressed data is a chunk bundle"""

    def __init__(self, **kwargs):
        from resources.blackbox.maps.nfs6_ps2 import Nfs6Ps2CarGeometry, Nfs6Ps2ChunkBundle, Nfs6Ps2TrackBundle

        super(EacCompressedBlock, self).__init__(
            possible_blocks=[
                Nfs6Ps2TrackBundle(),
                Nfs6Ps2CarGeometry(),
                Nfs6Ps2ChunkBundle(),
                BytesBlock(length=(lambda ctx: ctx.read_bytes_amount)),
            ],
            **kwargs,
        )

    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'COMP-compressed data (LZ77 with "COMP" header): NFS Hot Pursuit 2 (PS2) *.LZC files',
        }

    def _detect_compression(self, buffer):
        from resources.eac.compressions.comp import CompCompression

        return CompCompression()

    def compress(self, uncompressed_bytes: bytes, data) -> bytes:
        from resources.eac.compressions.comp import CompCompression

        return CompCompression().compress(BytesIO(uncompressed_bytes), len(uncompressed_bytes))
