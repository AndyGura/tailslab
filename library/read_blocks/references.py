from copy import copy
from typing import Dict, List, Tuple

from library.context import DocumentationContext, WriteContext


# Block parameters (a length, a padding end) are a number, the path of a field (`ctx.data` path, e.g. 'num_items' or
# '../count'), a function of the context, or one of these with its documentation text: (parameter, 'doc')


def param_value(param, ctx):
    """The value of a block parameter in a read or write context"""
    if isinstance(param, tuple):
        param = param[0]
    if isinstance(param, str):
        return ctx.data(param)
    if callable(param):
        return param(ctx)
    return param


def param_doc(param, fallback: str = 'custom_func') -> str:
    """Documentation text of a block parameter: a field path as `DocumentationContext` shows it, `fallback` for a
    function failing there"""
    if isinstance(param, tuple):
        return param[1]
    if isinstance(param, str):
        return param.replace('../', '^')
    if callable(param):
        try:
            return str(param(DocumentationContext()))
        except:
            return fallback
    return str(param)


def is_static_param(param) -> bool:
    """True for a parameter with the same value in every context (not a field path nor a function)"""
    if isinstance(param, tuple):
        param = param[0]
    return not isinstance(param, str) and not callable(param)


# (start, end) of each field of a written compound block
Spans = Dict[str, Tuple[int, int]]


class FieldReference:
    """Programmatic value of a field computed from other fields of its compound block, called with the block's write
    context like any programmatic value. `reference + n` / `reference - n` adds a constant"""

    def __init__(self, add: int = 0):
        self.add = add

    def __add__(self, other: int) -> 'FieldReference':
        res = copy(self)
        res.add = self.add + other
        return res

    __radd__ = __add__

    def __sub__(self, other: int) -> 'FieldReference':
        return self + -other

    def __call__(self, ctx: WriteContext) -> int:
        raise NotImplementedError


class CountOf(FieldReference):
    """The number of items of the field at `path` (`ctx.data` path)"""

    def __init__(self, path: str, add: int = 0):
        super().__init__(add)
        self.path = path

    def __call__(self, ctx: WriteContext) -> int:
        return len(ctx.data(self.path)) + self.add


class LayoutReference(FieldReference):
    """A reference to where fields of the compound block are written. `CompoundBlock.write` writes such a field after
    the others, from the bytes they were written to (`ctx.result` holds zeros in its place until then); called, it
    estimates them"""

    # names of the fields of the compound block it refers to
    names: Tuple[str, ...] = ()

    def from_spans(self, spans: Spans, length: int, item_spans: Dict[str, List[Tuple[int, int]]]):
        """The value from the (start, end) of each written field, the length of the compound block and (for
        `ItemOffsetsOf`) the (start, end) of each item of the arrays it refers to"""
        raise NotImplementedError

    def placeholder(self, field, data) -> bytes:
        """What the field is written as until the value is known: zeros of its size"""
        return bytes(field.fixed_size)


class OffsetOf(LayoutReference):
    """Offset of the field `name` from the start of the compound block"""

    def __init__(self, name: str, add: int = 0):
        super().__init__(add)
        self.names = (name,)

    def __call__(self, ctx: WriteContext) -> int:
        return ctx.block.offset_to_child_when_packed(ctx.get_full_data(), self.names[0]) + self.add

    def from_spans(self, spans: Spans, length: int, item_spans) -> int:
        return spans[self.names[0]][0] + self.add


class SizeOf(LayoutReference):
    """Packed size of the fields `names` together"""

    def __init__(self, *names: str, add: int = 0):
        super().__init__(add)
        self.names = names

    def __call__(self, ctx: WriteContext) -> int:
        return (
            sum(ctx.block.get_child_block(name).estimate_packed_size(ctx.data(name), ctx) for name in self.names)
            + self.add
        )

    def from_spans(self, spans: Spans, length: int, item_spans) -> int:
        return sum(spans[name][1] - spans[name][0] for name in self.names) + self.add


class OwnSize(LayoutReference):
    """Packed size of the whole compound block"""

    def __call__(self, ctx: WriteContext) -> int:
        return ctx.block.estimate_packed_size(ctx.get_full_data()) + self.add

    def from_spans(self, spans: Spans, length: int, item_spans) -> int:
        return length + self.add


class ItemOffsetsOf(LayoutReference):
    """Offsets of the items of the array field `name` from the start of the compound block, as a list: the value of
    an offset table (an array of integers, one per item)"""

    def __init__(self, name: str, add: int = 0):
        super().__init__(add)
        self.names = (name,)

    def __call__(self, ctx: WriteContext) -> List[int]:
        data = ctx.get_full_data()
        array = ctx.block.get_child_block(self.names[0])
        offset = ctx.block.offset_to_child_when_packed(data, self.names[0]) + self.add
        res = []
        for item in data[self.names[0]]:
            res.append(offset)
            offset += array.child.estimate_packed_size(item, ctx)
        return res

    def from_spans(self, spans: Spans, length: int, item_spans) -> List[int]:
        return [start + self.add for start, _ in item_spans[self.names[0]]]

    def placeholder(self, field, data) -> bytes:
        return field.write([0] * len(data[self.names[0]]))
