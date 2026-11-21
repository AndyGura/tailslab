from abc import ABC
from functools import cached_property
from math import ceil
from typing import Dict, Tuple, Any, Optional, List

from library.context import ReadContext, WriteContext
from library.exceptions import DataIntegrityException, EndOfBufferException
from library.read_blocks.basic import DataBlock, DataBlockWithChildren, LengthPrefixed, read_length
from library.read_blocks.numbers import IntegerBlock
from library.read_blocks.references import is_static_param, param_doc, param_value
from library.utils.docs import multiply_doc_numbers, needs_parentheses


def _stop_doc(stop) -> str:
    return stop[1] if isinstance(stop, tuple) else '?'


class ArrayBlock(DataBlockWithChildren, DataBlock, ABC):
    # How many items, one of:
    # - `length`: the number of items, a block parameter (library/read_blocks/references.py)
    # - `byte_length`: the items take that many bytes (a block parameter too; `REMAINING`: the bytes the array is read
    #   with, the rest of its compound block). Fixed-size items: as many as fit (bytes left over go to the next field);
    #   other items are read one by one until they took them (any size, without counting them first), an item
    #   running past them raises
    # - `stop_before` / `stop_after` (a function or (function, doc)): items read one by one up to the end of the bytes
    #   the array may read (`ReadContext.read_end`) or until `stop_before(ctx)` is True before an item (the array's
    #   read context, the buffer at the item: `ctx.peek(n)` gives the bytes ahead; a terminator after the array) or
    #   `stop_after(item)` after it (a terminator that is the last item)
    def __init__(self, child: DataBlock, length=None, byte_length=None, stop_before=None, stop_after=None, **kwargs):
        super().__init__(**kwargs)
        self.child = child
        self._length = length
        self.byte_length = byte_length
        self.stop_before = stop_before
        self.stop_after = stop_after

    @property
    def is_terminated(self) -> bool:
        return self.stop_before is not None or self.stop_after is not None

    @property
    def schema(self) -> Dict:
        schema = {
            **super().schema,
            'block_description': f'Array of `{self.length_doc_str}` items',
            'child_schema': self.child.schema,
        }
        if self.byte_length is None and not self.is_terminated and is_static_param(self._length):
            schema['length'] = self._length[0] if isinstance(self._length, tuple) else self._length
        return schema

    # For auto-generated documentation only
    @property
    def length_doc_str(self):
        if self.is_terminated:
            return _stop_doc(self.stop_before if self.stop_before is not None else self.stop_after)
        if self.byte_length is not None:
            byte_doc = param_doc(self.byte_length)
            item_size = str(self.child.size_doc_str)
            if not item_size.isdigit() or int(item_size) <= 1:
                return byte_doc
            return f'({byte_doc}) / {item_size}' if needs_parentheses(byte_doc) else f'{byte_doc} / {item_size}'
        return param_doc(self._length)

    # For auto-generated documentation only
    @property
    def size_doc_str(self):
        if self.byte_length is not None:
            return param_doc(self.byte_length)
        if self.is_terminated:
            return multiply_doc_numbers(self.length_doc_str, self.child.size_doc_str)
        if self._length == 0:
            return '0'
        # when set to 0 and added some label, assume that it has some custom logic
        if isinstance(self._length, tuple) and self._length[0] == 0:
            return '?'
        child_size_doc = self.child.size_doc_str
        length_doc = self.length_doc_str
        return multiply_doc_numbers(length_doc, child_size_doc)

    def resolve_length(self, ctx):
        return param_value(self._length, ctx)

    # the length when it is the same for every array: a positive number (0 marks arrays filled by custom code)
    @property
    def static_length(self) -> Optional[int]:
        self_len = self._length[0] if isinstance(self._length, tuple) else self._length
        return self_len if type(self_len) is int and self_len > 0 else None

    # True when the class reads, writes and sizes the items one by one, as ArrayBlock does
    @property
    def item_by_item_io(self) -> bool:
        cls = type(self)
        return (
            cls.read is ArrayBlock.read
            and cls.write is ArrayBlock.write
            and cls.estimate_packed_size is ArrayBlock.estimate_packed_size
        )

    @cached_property
    def fixed_size(self) -> Optional[int]:
        if not self.item_by_item_io or self.static_length is None or self.child.fixed_size is None:
            return None
        return self.static_length * self.child.fixed_size

    @cached_property
    def struct_format(self) -> Optional[Tuple[str, str]]:
        if (
            not self.item_by_item_io
            or self.static_length is None
            or self.value_validator is not None
            or self.programmatic_value is not None
            or self.child.struct_format is None
        ):
            return None
        byte_order, codes = self.child.struct_format
        return byte_order, codes * self.static_length

    def from_struct(self, values: tuple, index: int):
        if self.child.struct_raw:
            end = index + self.static_length
            return list(values[index:end]), end
        res = []
        for _ in range(self.static_length):
            item, index = self.child.from_struct(values, index)
            res.append(item)
        return res, index

    def to_struct(self, data, values: list):
        if len(data) != self.static_length:
            raise ValueError(f'Array of {len(data)} items instead of {self.static_length}')
        if self.child.struct_raw:
            values.extend(data)
        else:
            for item in data:
                self.child.to_struct(item, values)

    def get_child_block(self, name: str) -> 'DataBlock':
        int(name)
        return self.child

    def get_child_block_with_data(self, unpacked_data: list, name: str) -> Tuple['DataBlock', Any]:
        return self.child, unpacked_data[int(name)]

    def new_data(self, patch=None):
        if self.value_validator:
            return self.value_validator.new_data()
        self_len = self._length
        if isinstance(self_len, tuple):
            # cut off the documentation
            (self_len, _) = self_len
        if not is_static_param(self_len) or self_len is None:
            return []
        return [self.child.new_data()] * self_len

    def read(self, ctx: ReadContext, name: str = '', read_bytes_amount=None, resolved_length=None):
        res = []
        self_ctx = ctx.get_or_create_child(name, self, read_bytes_amount, res)
        if resolved_length is None and self.is_terminated:
            return self._read_until_stop(ctx, self_ctx, res)
        if resolved_length is None and self.byte_length is not None:
            byte_length = read_length(self.byte_length, ctx, read_bytes_amount)
            item_size = self.child.fixed_size
            if item_size:
                resolved_length = byte_length // item_size
            else:
                start = ctx.buffer.tell()
                end = start + byte_length
                while ctx.buffer.tell() < end:
                    res.append(self.child.unpack(ctx=self_ctx, name=str(len(res))))
                if ctx.buffer.tell() > end:
                    raise DataIntegrityException(
                        ctx=self_ctx,
                        message=f'The items take {ctx.buffer.tell() - start} bytes instead of {byte_length}',
                    )
                return res
        self_len = self.resolve_length(ctx) if resolved_length is None else resolved_length
        if self.child.__class__ == IntegerBlock and self.child.length == 1 and not self.child.is_signed:
            res = list(ctx.buffer.read(self_len))
            if len(res) < self_len:
                raise EndOfBufferException(ctx=ctx)
            self_ctx.res = res
            return res
        record = self.child.struct_record
        if record is not None:
            start = ctx.buffer.tell()
            try:
                res.extend(record.read_many(ctx.buffer, self_len))
                return res
            except Exception:
                # end of buffer, a value an item field cannot hold: the item by item read raises it with its context
                ctx.buffer.seek(start)
        for i in range(self_len):
            res.append(self.child.unpack(ctx=self_ctx, name=str(i)))
        return res

    def _read_until_stop(self, ctx: ReadContext, self_ctx: ReadContext, res: list) -> list:
        stop_before = self.stop_before[0] if isinstance(self.stop_before, tuple) else self.stop_before
        stop_after = self.stop_after[0] if isinstance(self.stop_after, tuple) else self.stop_after
        end = self_ctx.read_end
        while ctx.buffer.tell() < end:
            if stop_before is not None and stop_before(self_ctx):
                break
            item = self.child.unpack(ctx=self_ctx, name=str(len(res)))
            res.append(item)
            if stop_after is not None and stop_after(item):
                break
        return res

    def estimate_packed_size(self, data, ctx: WriteContext = None):
        if self.child.fixed_size is not None:
            return len(data) * self.child.fixed_size
        self_ctx = WriteContext(data=data, block=self, parent=ctx)
        res = 0
        for item in data:
            res += self.child.estimate_packed_size(data=item, ctx=self_ctx)
        return res

    def offset_to_child_when_packed(self, data, child_name: str, ctx: WriteContext = None):
        index = int(child_name)
        if index >= len(data):
            raise IndexError()
        return self.estimate_packed_size(data[:index], ctx)

    def write(self, data, ctx: WriteContext = None, name: str = '') -> bytes:
        if self.child.__class__ == IntegerBlock and self.child.length == 1 and not self.child.is_signed:
            return bytes(data)
        record = self.child.struct_record
        if record is not None:
            try:
                return record.write_many(data)
            except Exception:
                # a missing value or one an item field cannot hold: the item by item write raises it with its context
                pass
        return b''.join(self.write_items(data, ctx, name))

    def write_items(self, data, ctx: WriteContext = None, name: str = '') -> List[bytes]:
        """The packed items, one by one (`write` joins them)"""
        self_ctx = WriteContext(data=data, block=self, parent=ctx, name=name)
        return [self.child.pack(data=item, ctx=self_ctx, name=str(i)) for i, item in enumerate(data)]


class LengthPrefixedArrayBlock(LengthPrefixed, ArrayBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Array, prefixed with length field'}

    def prefix_value(self, data, packed_size: int) -> int:
        return len(data)

    def offset_to_child_when_packed(self, data, child_name: str, ctx: WriteContext = None):
        index = int(child_name)
        if index >= len(data):
            raise IndexError()
        res = self.length_block.estimate_packed_size(len(data), ctx=ctx)
        for item in data[:index]:
            res += self.child.estimate_packed_size(data=item, ctx=ctx)
        return res


class SubByteArrayBlock(DataBlock):
    def __init__(
        self,
        length,
        bits_per_value: int,
        value_deserialize_func: callable = None,
        value_serialize_func: callable = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._length = length
        self.bits_per_value = bits_per_value
        self.value_deserialize_func = value_deserialize_func
        self.value_serialize_func = value_serialize_func

    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': f'Array of `{self.length_doc_str}` sub-byte numbers. Each number consists of {self.bits_per_value} bits',
            'child_schema': {
                'block_class_mro': 'IntegerBlock__DataBlock',
                'min_value': self.value_deserialize_func(0) if self.value_deserialize_func else 0,
                'max_value': self.value_deserialize_func((1 << self.bits_per_value) - 1)
                if self.value_deserialize_func
                else (1 << self.bits_per_value) - 1,
                'value_interval': self.value_deserialize_func(1) - self.value_deserialize_func(0)
                if self.value_deserialize_func
                else 1,
            },
        }

    # For auto-generated documentation only
    @property
    def length_doc_str(self):
        return param_doc(self._length)

    # For auto-generated documentation only
    @property
    def size_doc_str(self):
        length_doc = self.length_doc_str
        try:
            return str(ceil(int(length_doc) * self.bits_per_value / 8))
        except ValueError:
            return f'ceil(({length_doc})*{self.bits_per_value}/8)'

    def resolve_length(self, ctx):
        return param_value(self._length, ctx)

    def get_child_block_with_data(self, unpacked_data: list, name: str) -> Tuple['DataBlock', Any]:
        return None, unpacked_data[int(name)]

    def new_data(self, patch=None):
        if self.value_validator:
            return self.value_validator.new_data()
        self_len = self._length
        if isinstance(self_len, tuple):
            # cut off the documentation
            (self_len, _) = self_len
        if not is_static_param(self_len):
            return []
        return [0] * self_len

    def read(self, ctx: ReadContext, name: str = '', read_bytes_amount=None):
        self_len = self.resolve_length(ctx)
        raw = ctx.buffer.read(ceil(self.bits_per_value * self_len / 8))
        bitstring = ''.join([bin(x)[2:].rjust(8, '0') for x in raw])
        values = [int(bitstring[i * self.bits_per_value : (i + 1) * self.bits_per_value], 2) for i in range(self_len)]
        if self.value_deserialize_func:
            values = [self.value_deserialize_func(x) for x in values]
        return values

    def estimate_packed_size(self, data, ctx: WriteContext = None):
        return ceil(self.bits_per_value * len(data) / 8)

    def write(self, data, ctx: WriteContext = None, name: str = '') -> bytes:
        value_serialize_func = self.value_serialize_func if self.value_serialize_func else lambda x: x
        bitstring = ''.join(bin(value_serialize_func(item))[2:].rjust(self.bits_per_value, '0') for item in data)
        padding = len(bitstring) % 8
        if padding != 0:
            bitstring += '0' * (8 - padding)
        byte_array = bytearray()
        for i in range(0, len(bitstring), 8):
            byte = int(bitstring[i : i + 8], 2)
            byte_array.append(byte)
        return bytes(byte_array)
