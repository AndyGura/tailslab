from copy import deepcopy
from typing import Callable, Dict, Iterable, Tuple

from library.read_blocks import (
    ArrayBlock,
    CompoundBlock,
    DataBlock,
    DecimalBlock,
    DeclarativeCompoundBlock,
    DelegateBlock,
    IntegerBlock,
    OptionalBlock,
)


def big_endian_copy(block: DataBlock) -> DataBlock:
    """A deep copy of a block with every integer block in it (fixed point numbers, bit fields, angles...) read and
    written big-endian: the layout of a little-endian PC structure as a big-endian console (3DO, Sega Saturn) stores
    it. Byte arrays and strings are unchanged"""
    block = deepcopy(block)
    stack = [block]
    while stack:
        current = stack.pop()
        if isinstance(current, (IntegerBlock, DecimalBlock)):
            current.byte_order = 'big'
        elif isinstance(current, ArrayBlock):
            stack.append(current.child)
        elif isinstance(current, CompoundBlock):
            stack.extend(child for _, child in current.field_blocks)
        elif isinstance(current, DelegateBlock):
            stack.extend(current.possible_blocks)
        elif isinstance(current, OptionalBlock):
            stack.append(current.child)
    return block


def derive_fields(
    base,
    transform: Callable[[DataBlock], DataBlock] = big_endian_copy,
    replace: Dict[str, Tuple[DataBlock, dict]] = None,
    drop: Iterable[str] = (),
):
    """A `Fields` class of another platform's copy of a structure: the fields of `base` (a `Fields` class) in order,
    each block `transform`-ed (big-endian by default), the fields of `replace` (name: (block, extras)) in place of
    theirs, the fields `drop` left out"""
    replace = replace or {}
    fields = {
        name: replace.get(name, (transform(block), extras)) for name, (block, extras) in base.fields if name not in drop
    }
    return type('Fields', (DeclarativeCompoundBlock.Fields,), fields)
