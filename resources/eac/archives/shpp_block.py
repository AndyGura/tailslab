from io import SEEK_CUR
from typing import Dict

from library.read_blocks import (
    ArrayBlock,
    AutoDetectBlock,
    BytesBlock,
    IntegerBlock,
    TrailingOptionalBlock,
    UTF8Block,
    REMAINING,
)
from library.read_blocks.archives import ArchiveBlock
from library.read_blocks.misc.value_validators import Eq
from resources.eac.archives.shpi_block import ShpiBlock
from resources.eac.psx import PsxCrcFooter, PsxItemCrcFooterMixin
from resources.eac.psx_bitmaps import PSX_IMAGE_IDS, PsxImage


class PsxShapeItemBlock(AutoDetectBlock):
    """An SHPP item: a PSX image when it starts with an image id, raw bytes otherwise"""

    def detect(self, ctx, name=None, read_bytes_amount=None):
        head = ctx.buffer.read(1)
        ctx.buffer.seek(-len(head), SEEK_CUR)
        if len(head) == 1 and head[0] in [x for x, _ in PSX_IMAGE_IDS]:
            return self.get_choice_index_by_class_name('PsxImage')
        return self.get_choice_index_by_class_name('BytesBlock')


class ShppBlock(PsxItemCrcFooterMixin, ShpiBlock):
    """The PlayStation counterpart of SHPI (`.PSH` files of the PSX TNFS): the same header and directory, with PSX
    images (`PsxImage`, each with its CLUT) as items"""

    serializer = 'ShppArchiveSerializer'

    @property
    def schema(self) -> Dict:
        return {
            **super(ShpiBlock, self).schema,
            'block_description': 'A container of PSX images (`.PSH` files of the PSX TNFS, also inside its `_PSH.FAM` '
            'wwww archives): the PSX counterpart of SHPI, same header and directory. The game finds an image by its '
            '4-character name (`tnfs_front_image` 0x80010334, case-sensitive). Track textures `Z<track><time>.PSH` '
            'hold the horizon: `hrz0`..`hrz7` (8 sectors of 22.5 degrees each) and `rhrz` (rear-view mirror)',
        }

    def __init__(self, **kwargs):
        super(ShpiBlock, self).__init__(
            item_block=PsxShapeItemBlock(
                possible_blocks=[
                    PsxImage(),
                    BytesBlock(length=(REMAINING, 'item_length')),
                ]
            ),
            alias_field=UTF8Block(length=4),
            **kwargs,
        )

    # every field declared here: `Fields` takes the fields of its own class only
    class Fields(ArchiveBlock.Fields):
        resource_id = (UTF8Block(length=4, value_validator=Eq('SHPP')), {'description': 'Resource ID'})
        length = (
            IntegerBlock(length=4, programmatic_value=lambda ctx: ctx.block.size_without_footer(ctx.get_full_data())),
            {'description': 'The length of this SHPP block in bytes, without the CRC footer'},
        )
        num_items = ShpiBlock.Fields.num_items
        shpi_dir = (UTF8Block(length=4), {'description': 'Directory id: "GIMX" in every file'})
        items_descr = ShpiBlock.Fields.items_descr
        pre_items_payload = ShpiBlock.Fields.pre_items_payload
        data_bytes = (
            ShpiBlock.Fields.data_bytes[0],
            {
                'usage': 'io,doc',
                'description': 'A part of block, where items data is located. Offsets to the entries are defined in '
                '`items_descr`. Every item is padded to 4 bytes. Possible item types:<br/>- [PsxImage](#psximage)',
            },
        )
        # not shared with SHPI: `ArchiveBlock.__init__` sets the item block of the children array
        children = (ArrayBlock(child=None, length=None), {'usage': 'ui'})
        crc_footer = (
            TrailingOptionalBlock(child=PsxCrcFooter()),
            {
                'usage': 'ui,doc',
                'description': 'CRC footer after the SHPP (`length` does not count it), in a file of its own and in '
                'a BIGF or C0FB item (PSX car archives `.VSM` / `.WSM`): inside a FAM archive it follows the last '
                'item of the FAM',
            },
        )

    def new_data(self, patch=None):
        return {**super().new_data(), 'shpi_dir': 'GIMX', 'crc_footer': None}

    def entry_kind_hint(self, head: bytes):
        if not head:
            return None
        return 'PsxImage' if head[0] in [x for x, _ in PSX_IMAGE_IDS] else 'BytesBlock'
