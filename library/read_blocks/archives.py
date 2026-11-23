import traceback
from abc import ABC
from typing import Any, Dict, Iterator, List, NamedTuple, Optional, Tuple

from library.context import ReadContext, WriteContext
from library.lazy import LazyDict, Slot, source_for_buffer, unloaded_slot
from library.read_blocks import CompoundBlock, DeclarativeCompoundBlock, BytesBlock
from library.read_blocks.basic import DataBlock


# Base abstract class for archive blocks: a header with a directory of items (`items_descr`), the items in
# `data_bytes` (must be the last io field). The data has `children` instead of `items_descr` and `data_bytes`.
# Subclasses:
# 1) Provide item block to super().__init__ (a delegate block; its `BytesBlock(length=REMAINING)` choice takes items
#    no other block reads)
# 2) Declare own compound block fields as usual, documentation and io friendly, `items_descr` and `data_bytes` with
#    usage "io,doc" (skip showing in UI)
# 3) Add `children = (ArrayBlock(child=None, length=None), {'usage': 'ui'})` to Fields class
# 4) Declare `pre_items_payload = (BytesBlock(length=(<lambda>, 'doc')), {...})` right before `data_bytes`: the bytes
#    between the end of the item descriptions and the first item (`pre_items_payload_length` computes them)
# 5) Implement `item_descriptions` (the entries `items_descr` gives) and `make_items_descr` (`items_descr` of entries
#    written to `data_bytes`); `read`, `write` and `estimate_packed_size` are done here. Hooks for other layouts:
#    `heap_order`, `is_empty_entry`, `slots_end`, `after_read`
#
# Entry bytes: an entry owns its slot, from its item offset up to the offset of the next item (in the file order).
# The item is parsed from the slot start, bytes left after the item end are `post_offset_payload`. Entries never
# have bytes before their item: the offset table points at the item start. Entries sharing an offset (NFS2 SE
# HUDDATA.VIV: three of length 0 at the offset of the next item) share one slot: the longest item owns it, the others
# take only their item length, so the slot's bytes are kept once and written back at the same offset.
# With lazy read context, entries are unloaded `LazyDict`s, seeded with `alias`. Unloaded entry is written back as
# its original slot bytes.


class ItemDescription(NamedTuple):
    """An entry of an archive as its directory gives it"""

    # place in `children`
    index: int
    # offset of the item from the start of the archive, None for an entry without data (empty bytes)
    offset: Optional[int]
    alias: Any = None
    # bytes the item is read with, None: its whole slot
    item_length: Optional[int] = None
    # name of its read context, None: the index
    name: Optional[str] = None


class EntryLayout(NamedTuple):
    """Where an entry is written: offset in `data_bytes`, length of the item and of the whole slot (item and
    post-offset payload)"""

    offset: int
    item_length: int
    length: int


# key of the data `ArchiveBlock.write` writes with the layouts of the entries it packed: header fields sizing the
# archive (`estimate_packed_size`) take them instead of packing the items again
_LAYOUTS_KEY = '__entry_layouts__'


class ArchiveBlock(DeclarativeCompoundBlock, ABC):
    def __init__(self, item_block, alias_field=None, **kwargs):
        super().__init__(**kwargs)
        self.item_block = item_block
        fields = [
            ('item', item_block, {}),
            ('post_offset_payload', BytesBlock(length=None), {}),
        ]
        if alias_field is not None:
            fields.append(('alias', alias_field, {}))
        self.has_alias = alias_field is not None
        self.entry_keys = frozenset(name for (name, _, _) in fields)
        self.field_blocks_map['children'].child = CompoundBlock(fields=fields)

    @property
    def schema(self) -> Dict:
        # an archive holds archives of its own kind (BIGF in BIGF): the nested reference is a stub
        if getattr(self, '_schema_in_progress', False):
            return {
                'block_class_mro': '__'.join(
                    [x.__name__ for x in self.__class__.mro() if x.__name__ not in ['object', 'ABC']]
                ),
                'is_recursive_ref': True,
            }
        self._schema_in_progress = True
        try:
            return super().schema
        finally:
            self._schema_in_progress = False

    @property
    def bytes_choice(self) -> int:
        try:
            return self.item_block.get_choice_index_by_class_name('BytesBlock')
        except ValueError:
            return -1

    def items(self, data, of_class: type = None) -> Iterator[Tuple[int, dict, DataBlock, Any]]:
        """(index, entry, item block, item data) of the entries of `data` (`of_class`: only items of that block
        class); entries of a lazy read are loaded"""
        for i, child in enumerate(data['children']):
            item = child['item']
            if item is None:
                continue
            block = self.item_block.possible_blocks[item['choice_index']]
            if of_class is None or isinstance(block, of_class):
                yield i, child, block, item['data']

    # --- read

    def item_descriptions(self, header: dict) -> List[ItemDescription]:
        """The entries of the archive, by its header (the io fields before `data_bytes`, offsets relative to the
        archive start), one per entry of `children`, in the order to read them"""
        raise NotImplementedError

    def slots_end(self, header: dict, block_start: int, region_end: int, descriptions: List[ItemDescription]) -> int:
        """Where the slot of the last item ends (absolute): the end of the items region"""
        return region_end

    def empty_entry(self) -> dict:
        """An entry without data (an item description without offset)"""
        return {'item': {'choice_index': self.bytes_choice, 'data': b''}, 'post_offset_payload': b''}

    def after_read(self, res: dict, descriptions: List[ItemDescription]):
        """Adds what else the archive keeps of its header to the read data (`items_descr` is still there)"""

    def read(self, ctx: ReadContext, name: str = '', read_bytes_amount=None):
        block_start = ctx.buffer.tell()
        res, self_ctx, region_start, region_length = self.read_header(ctx, name, read_bytes_amount)
        end_pos = region_start + region_length
        descriptions = self.item_descriptions(res)
        stored = [x for x in descriptions if x.offset is not None]
        offsets = [block_start + x.offset for x in stored]
        lengths = (
            slot_lengths(offsets, self.slots_end(res, block_start, end_pos, stored), [x.item_length for x in stored])
            if stored
            else []
        )
        # entries are parsed later in lazy mode: keep header (with io-only fields) for their contexts
        entry_ctx = self_ctx.detached(ctx.buffer, data=dict(res)) if self_ctx.lazy else self_ctx
        children = [None] * len(descriptions)
        for description in descriptions:
            if description.offset is None:
                children[description.index] = self.empty_entry()
        for description, offset, length in zip(stored, offsets, lengths):
            children[description.index] = self.read_entry(
                entry_ctx,
                name=description.name or str(description.index),
                offset=offset,
                length=length,
                item_length=description.item_length,
                alias=description.alias,
            )
        res['children'] = children
        self.after_read(res, descriptions)
        ctx.buffer.seek(end_pos)
        del res['items_descr']
        return res

    def read_header(
        self, ctx: ReadContext, name: str = '', read_bytes_amount=None
    ) -> Tuple[dict, ReadContext, int, int]:
        """Reads io fields before `data_bytes`. Returns data, own context, absolute start and length of items region.
        Buffer is left at the region start"""
        res = dict()
        self_ctx = ctx.get_or_create_child(name, self, read_bytes_amount, res)
        region_start, region_length = None, 0
        for field_name, field in self.io_field_blocks:
            if field_name == 'data_bytes':
                region_start = ctx.buffer.tell()
                region_length = field.resolve_length(self_ctx)
                break
            res[field_name] = field.unpack(
                ctx=self_ctx, name=field_name, read_bytes_amount=self_ctx.read_bytes_remaining
            )
        return res, self_ctx, region_start, region_length

    def read_entry(
        self,
        ctx: ReadContext,
        name: str,
        offset: int,
        length: int,
        item_length: Optional[int] = None,
        alias=None,
    ):
        """One entry (`children` item). `offset` and `length` are the absolute slot, the item is read with
        `read_bytes_amount=item_length` (whole slot by default). `ctx` should hold the header data, including io-only
        fields, for item blocks looking them up. Returns a plain dict, or an unloaded `LazyDict` if ctx is lazy"""
        seed = {'alias': alias} if self.has_alias else {}
        slot = Slot(
            source=None,
            offset=offset,
            length=max(0, length),
            item_length=length if item_length is None else item_length,
            parse_fn=_parse_entry,
            parent_ctx=ctx,
            keys=self.entry_keys,
            seed=seed,
            args=(self, name),
        )
        if ctx.lazy:
            slot.source = source_for_buffer(ctx.buffer)
            if slot.source is not None:
                position = ctx.buffer.tell()
                ctx.buffer.seek(offset)
                slot.hint = self.entry_kind_hint(ctx.buffer.read(min(4, max(0, length))))
                ctx.buffer.seek(position)
                return LazyDict(slot)
        ctx.buffer.seek(offset)
        return _parse_entry(ctx, slot)

    def entry_kind_hint(self, head: bytes) -> Optional[str]:
        """Class name of the block an entry starting with `head` (up to 4 bytes) probably holds, for the GUI to show
        unloaded entries; None if unknown"""
        return None

    # --- write

    def make_items_descr(self, data: dict, layouts: List[Optional[EntryLayout]], heap_offset: int) -> list:
        """`items_descr` of the entries written as `layouts` (None: an empty entry), their offsets in `data_bytes`
        moved by `heap_offset` (the offset of `data_bytes` in the archive)"""
        raise NotImplementedError

    def heap_order(self, data) -> List[int]:
        """Indices of the children in the order their data is stored"""
        return list(range(len(data['children'])))

    def is_empty_entry(self, child) -> bool:
        """Whether the entry is written without data (an item description without offset)"""
        return False

    def entry_sizes(self, child, ctx: WriteContext = None) -> Tuple[int, int]:
        """Lengths of item and post-offset payload of entry when packed"""
        slot = unloaded_slot(child)
        if slot is not None:
            item_length = min(slot.item_length, slot.length)
            return item_length, slot.length - item_length
        return (
            self.item_block.estimate_packed_size(data=child['item'], ctx=ctx),
            len(child['post_offset_payload']),
        )

    def entry_bytes(self, child, ctx: WriteContext = None, name: str = '') -> Tuple[bytes, bytes]:
        """Packed item and post-offset payload of entry"""
        slot = unloaded_slot(child)
        if slot is not None:
            raw = slot.raw()
            item_length = min(slot.item_length, slot.length)
            return raw[:item_length], raw[item_length:]
        return (
            self.item_block.pack(data=child['item'], ctx=ctx, name=name),
            child['post_offset_payload'],
        )

    def entry_layouts(self, data, ctx: WriteContext = None) -> List[Optional[EntryLayout]]:
        """Where the entries are written: the layouts of the entries packed by `write` (`data` it writes), else from
        their packed sizes"""
        if _LAYOUTS_KEY in data:
            return data[_LAYOUTS_KEY]
        children = data['children']
        layouts = [None] * len(children)
        position = 0
        for i in self.heap_order(data):
            if self.is_empty_entry(children[i]):
                continue
            item_length, post_length = self.entry_sizes(children[i], ctx)
            layouts[i] = EntryLayout(position, item_length, item_length + post_length)
            position += item_length + post_length
        return layouts

    def heap_offset(self, data, layouts: List[Optional[EntryLayout]]) -> int:
        """Offset of `data_bytes` in the archive: the size of its header with the directory of these entries"""
        header = {**data, 'items_descr': self.make_items_descr(data, layouts, 0)}
        return self.offset_to_child_when_packed(header, 'data_bytes')

    def estimate_packed_size(self, data, ctx: WriteContext = None):
        layouts = self.entry_layouts(data, ctx)
        return self.heap_offset(data, layouts) + sum(x.length for x in layouts if x is not None)

    def write(self, data, ctx: WriteContext = None, name: str = '') -> bytes:
        children = data['children']
        parts, layouts, position = [], [None] * len(children), 0
        for i in self.heap_order(data):
            if self.is_empty_entry(children[i]):
                continue
            item, post = self.entry_bytes(children[i], ctx, str(i))
            layouts[i] = EntryLayout(position, len(item), len(item) + len(post))
            parts += [item, post]
            position += len(item) + len(post)
        written = {**data, _LAYOUTS_KEY: layouts, 'data_bytes': b''.join(parts)}
        written['items_descr'] = self.make_items_descr(written, layouts, self.heap_offset(written, layouts))
        return super().write(written, ctx, name)


def pre_items_payload_length(ctx: ReadContext, offsets: List[int]) -> int:
    """Length of `pre_items_payload`: from the buffer position up to the smallest item offset (relative to the block
    start), 0 without items or when the first item starts before the position"""
    return max(0, min(offsets, default=ctx.local_buffer_pos) - ctx.local_buffer_pos)


def slot_lengths(offsets: List[int], region_end: int, item_lengths: Optional[List[Optional[int]]] = None) -> List[int]:
    """Slot length of each item by absolute item offsets: up to the next bigger offset, or up to the region end.
    Items at one offset with `item_lengths` (None: the whole slot) share the slot: the longest one (the last of equal
    ones) owns it, the others get their item length"""
    ordered = sorted(set(offsets))
    next_offset = {x: ordered[i + 1] if i + 1 < len(ordered) else region_end for i, x in enumerate(ordered)}
    lengths = [next_offset[x] - x for x in offsets]
    if item_lengths is None or len(ordered) == len(offsets):
        return lengths
    owners = {}
    for i, offset in enumerate(offsets):
        size = lengths[i] if item_lengths[i] is None else min(item_lengths[i], lengths[i])
        if offset not in owners or size >= owners[offset][1]:
            owners[offset] = (i, size)
    return [
        length if owners[offset][0] == i or item_lengths[i] is None else min(item_lengths[i], length)
        for i, (offset, length) in enumerate(zip(offsets, lengths))
    ]


def _parse_entry(ctx: ReadContext, slot: Slot) -> dict:
    archive, name = slot.args
    try:
        item = archive.item_block.unpack(ctx=ctx, name=name, read_bytes_amount=slot.item_length)
    except Exception:
        traceback.print_exc()
        ctx.buffer.seek(slot.offset)
        item = {'choice_index': archive.bytes_choice, 'data': ctx.buffer.read(slot.item_length)}
    slot_end = slot.offset + slot.length
    tail = slot_end - ctx.buffer.tell()
    res = {'item': item}
    if archive.has_alias:
        res['alias'] = slot.seed['alias']
    res['post_offset_payload'] = ctx.buffer.read(tail) if tail > 0 else b''
    return res


# Items at the offsets of an offset table, parsed into a "ui" array while a raw "io" field keeps their bytes (NFS2 /
# NFS3 TRK blocks and COL files: extrablocks)


def read_items_at_offsets(ctx: ReadContext, child: DataBlock, offsets: List[int], base: int) -> list:
    """Items of `child` at `offsets` from the absolute position `base`, read with `ctx` (named by their index). The
    buffer position is kept"""
    position = ctx.buffer.tell()
    items = []
    for i, offset in enumerate(offsets):
        ctx.buffer.seek(base + offset)
        items.append(child.unpack(ctx, name=str(i)))
    ctx.buffer.seek(position)
    return items


def pack_items_at_offsets(
    child: DataBlock, items: list, offsets: List[int], raw: bytes, region_start: int, new_region_start: int
) -> Tuple[bytes, List[int]]:
    """The raw bytes and offsets of `items` read from `raw` at `offsets` (`raw` starts at offset `region_start`),
    written back with their edits: an item still packing to the bytes at its offset keeps its slot (up to the next
    item) as it is, a changed one is written before the rest of its slot, items past the read ones come last.
    Returns the new raw bytes and offsets (`raw` starting at `new_region_start`). An item whose bytes keep its own
    length (a size field) is never taken for an unchanged prefix of its old bytes"""
    relative = [x - region_start for x in offsets[: len(items)]]
    ends = dict(zip(sorted(set(relative)), sorted(set(relative))[1:] + [len(raw)]))
    pieces = [raw[: min(relative, default=len(raw))]] if relative else []
    position = len(pieces[0]) if pieces else 0
    new_offsets = [None] * len(items)
    placed = {}
    for i in sorted(range(len(relative)), key=lambda x: relative[x]):
        start = relative[i]
        slot = raw[start : ends[start]]
        packed = child.pack(items[i])
        if slot[: len(packed)] == packed:
            if start in placed:
                new_offsets[i] = placed[start]
                continue
            new_slot = slot
        else:
            old_length = child.estimate_packed_size(child.unpack_from_bytes(slot))
            new_slot = packed + slot[old_length:]
        placed[start] = new_offsets[i] = new_region_start + position
        pieces.append(new_slot)
        position += len(new_slot)
    for i in range(len(relative), len(items)):
        packed = child.pack(items[i])
        new_offsets[i] = new_region_start + position
        pieces.append(packed)
        position += len(packed)
    return b''.join(pieces), new_offsets
