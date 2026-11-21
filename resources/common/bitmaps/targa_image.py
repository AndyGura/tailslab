from library.read_blocks import BytesBlock, REMAINING


class TargaImage(BytesBlock):
    serializer = 'TargaImageSerializer'

    def __init__(self):
        super().__init__(length=REMAINING)
