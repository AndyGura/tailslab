from typing import Dict

from resources.common.bitmaps.targa_image import TargaImage


class PcxImage(TargaImage):
    """A PCX (ZSoft Paintbrush) image file, kept as its bytes; the PNG export decodes it with Pillow"""

    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': "A PCX image file (ZSoft Paintbrush; Over Drivin' GT-R: version 5, 8 bits per pixel, "
            'run-length encoded, 256-colour palette at the end), kept as its bytes',
        }

    def serializer_class(self):
        from serializers import PcxImageSerializer

        return PcxImageSerializer
