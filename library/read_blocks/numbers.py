import struct
from functools import cached_property
from typing import Dict, Literal, List, Tuple, Optional

from library.context import ReadContext, WriteContext
from library.exceptions import EndOfBufferException, DataIntegrityException, IntegerOutOfRangeException
from library.read_blocks.basic import DataBlock
from library.read_blocks.struct_record import INTEGER_STRUCT_CODES, struct_byte_order


class IntegerBlock(DataBlock):
    def __init__(self, length: int, is_signed: bool = False, byte_order: Literal['little', 'big'] = 'little', **kwargs):
        super().__init__(**kwargs)
        self.length = length
        self.is_signed = is_signed
        self.byte_order = byte_order

    @property
    def schema(self) -> Dict:
        descr = f'{self.length}-byte{"s" if self.length > 1 else ""} {"un" if not self.is_signed else ""}signed integer'
        if self.length > 1:
            descr += f' ({self.byte_order} endian)'
        if self.value_validator is not None:
            descr += f'. {self.value_validator}'
        return {
            **super().schema,
            'block_description': descr,
            'min_value': -(1 << (self.length * 8 - 1)) if self.is_signed else 0,
            'max_value': ((1 << (self.length * 8 - 1)) if self.is_signed else (1 << (self.length * 8))) - 1,
            'value_interval': 1,
        }

    # For auto-generated documentation only
    @property
    def size_doc_str(self):
        return str(self.length)

    def new_data(self, patch=None):
        if self.value_validator:
            return self.value_validator.new_data()
        return 0

    # Value of the stored integer: subclasses storing another value as an integer (fixed point numbers, enums, angles)
    # override `from_raw` / `to_raw` instead of `read` / `write`, so records of them are read and written with `struct`
    def from_raw(self, raw: int):
        return raw

    # The integer stored for a value
    def to_raw(self, value) -> int:
        return value

    def read(self, ctx: ReadContext, name: str = '', read_bytes_amount=None):
        raw = ctx.buffer.read(self.length)
        if len(raw) < self.length:
            raise EndOfBufferException(ctx=ctx)
        return self.from_raw(int.from_bytes(raw, byteorder=self.byte_order, signed=self.is_signed))

    def estimate_packed_size(self, data, ctx: WriteContext = None):
        return self.length

    def write(self, data, ctx: WriteContext = None, name: str = '') -> bytes:
        raw = self.to_raw(data)
        try:
            return raw.to_bytes(self.length, byteorder=self.byte_order, signed=self.is_signed).ljust(self.length, b'\0')
        except OverflowError:
            schema = self.schema
            raise IntegerOutOfRangeException(
                ctx=ctx,
                message=f'{name + " = " if name else ""}{raw} does not fit {schema["block_description"]} '
                f'({schema["min_value"]}..{schema["max_value"]})',
            )

    @cached_property
    def fixed_size(self) -> Optional[int]:
        return self.length if type(self).estimate_packed_size is IntegerBlock.estimate_packed_size else None

    @cached_property
    def struct_format(self) -> Optional[Tuple[str, str]]:
        code = INTEGER_STRUCT_CODES.get((self.length, self.is_signed))
        cls = type(self)
        if (
            code is None
            or cls.read is not IntegerBlock.read
            or cls.write is not IntegerBlock.write
            or self.value_validator is not None
            or self.programmatic_value is not None
        ):
            return None
        return struct_byte_order(self.byte_order) if self.length > 1 else '', code

    @cached_property
    def struct_raw(self) -> bool:
        return type(self).from_raw is IntegerBlock.from_raw and type(self).to_raw is IntegerBlock.to_raw

    def from_struct(self, values: tuple, index: int):
        return self.from_raw(values[index]), index + 1

    def to_struct(self, data, values: list):
        values.append(self.to_raw(data))


class FixedPointBlock(IntegerBlock):
    @property
    def schema(self) -> Dict:
        super_schema = super().schema
        descr = (
            f'{self.length * 8}-bit real number ({self.byte_order}-endian, '
            f'{"" if self.is_signed else "not "}signed), where last {self.fraction_bits} '
            f'bits is a fractional part'
        )
        if self.value_validator is not None:
            descr += f'. {self.value_validator}'
        return {
            **super_schema,
            'min_value': float(super_schema['min_value'] / (1 << self.fraction_bits)),
            'max_value': float(super_schema['max_value'] / (1 << self.fraction_bits)),
            'value_interval': float(super_schema['value_interval'] / (1 << self.fraction_bits)),
            'block_description': descr,
        }

    def __init__(self, fraction_bits: int, **kwargs):
        super().__init__(**kwargs)
        self.fraction_bits = fraction_bits

    def from_raw(self, raw: int):
        return float(raw / (1 << self.fraction_bits))

    def to_raw(self, value) -> int:
        return max(
            min(
                round(value * (1 << self.fraction_bits)),
                ((1 << (self.length * 8 - 1)) if self.is_signed else (1 << (self.length * 8))) - 1,
            ),
            -(1 << (self.length * 8 - 1)) if self.is_signed else 0,
        )


class DecimalBlock(DataBlock):
    def __init__(self, length: int, byte_order: Literal['little', 'big'] = 'little', **kwargs):
        super().__init__(**kwargs)
        if length not in [4, 8]:
            raise Exception('DecimalsBlock supports only 4 or 8 bytes length')
        self.length = length
        self.byte_order = byte_order

    @property
    def schema(self) -> Dict:
        descr = f'{"Float" if self.length == 4 else "Double"} number ({self.byte_order}-endian)'
        if self.value_validator is not None:
            descr += f'. {self.value_validator}'
        return {
            **super().schema,
            'block_description': descr,
        }

    @property
    def size_doc_str(self):
        return str(self.length)

    def new_data(self, patch=None):
        return 0.0

    def read(self, ctx: ReadContext, name: str = '', read_bytes_amount=None):
        raw = ctx.buffer.read(self.length)
        if len(raw) < self.length:
            raise EndOfBufferException(ctx=ctx)
        f = 'f' if self.length == 4 else 'd'
        return struct.unpack(f'<{f}' if self.byte_order == 'little' else f'>{f}', raw)[0]

    def estimate_packed_size(self, data, ctx: WriteContext = None):
        return self.length

    def write(self, data, ctx: WriteContext = None, name: str = '') -> bytes:
        f = 'f' if self.length == 4 else 'd'
        return struct.pack(f'<{f}' if self.byte_order == 'little' else f'>{f}', data)

    @cached_property
    def fixed_size(self) -> Optional[int]:
        return self.length if type(self).estimate_packed_size is DecimalBlock.estimate_packed_size else None

    @cached_property
    def struct_format(self) -> Optional[Tuple[str, str]]:
        cls = type(self)
        if (
            cls.read is not DecimalBlock.read
            or cls.write is not DecimalBlock.write
            or self.value_validator is not None
            or self.programmatic_value is not None
        ):
            return None
        return struct_byte_order(self.byte_order), 'f' if self.length == 4 else 'd'

    @cached_property
    def struct_raw(self) -> bool:
        return True

    def from_struct(self, values: tuple, index: int):
        return values[index], index + 1

    def to_struct(self, data, values: list):
        values.append(data)


class EnumByteBlock(IntegerBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'enum_names': self.enum_names,
            'block_description': 'Enum of 256 possible values<br/><details><summary>Value names:</summary>'
            + '<br/>'.join([f'{i} ({hex(i)}): {x}' for i, x in enumerate(self.enum_name_map) if x != str(i)])
            + '</details>',
        }

    def __init__(self, enum_names: List[Tuple[int, str]], raise_error_on_unknown=False, **kwargs):
        super().__init__(length=1, **kwargs)
        self.enum_names = enum_names
        self.raise_error_on_unknown = raise_error_on_unknown
        self.enum_name_map = [str(i) if not self.raise_error_on_unknown else None for i in range(256)]
        for value, name in self.enum_names:
            self.enum_name_map[value] = name

    def new_data(self, patch=None):
        if self.value_validator:
            return self.value_validator.new_data()
        return self.enum_names[0][1]

    def from_raw(self, raw: int):
        if self.raise_error_on_unknown and self.enum_name_map[raw] is None:
            raise DataIntegrityException(message=f'Unknown enum value {raw}')
        return self.enum_name_map[raw]

    def to_raw(self, value) -> int:
        return self.enum_name_map.index(value)
