from abc import ABC
from functools import cached_property
from typing import Dict, List, Tuple, Any, TypedDict, Union, Optional

from library.utils.class_property import class_property

from library.context import ReadContext, WriteContext
from library.exceptions import BlockDefinitionException, DataIntegrityException
from library.read_blocks.basic import DataBlock, DataBlockWithChildren
from library.read_blocks.numbers import IntegerBlock
from library.read_blocks.struct_record import join_struct_formats
from library.utils.docs import add_doc_numbers


class FieldExtras(TypedDict, total=False):
    """
    Extra metadata for declarative compound fields.
    Allowed optional keys:
      - description: str — Human-readable description of the field for docs/UI.
      - is_unknown: bool — Marks a field whose purpose/meaning is not fully known.
      - custom_offset: Union[int, str] — For documentation: shows how the field's offset is calculated
        if it is not placed sequentially. Accepts an absolute integer offset or an expression string.
      - usage: str — Where the field should be used. Possible values:
        -- coma-separated strings, e.g. 'ui,io'.
           Possible values are: 'ui', 'io', 'doc' for GUI editor, reading/writing data, and documentation, respectively.
        -- None or 'everywhere' (default) — used in IO, UI, and docs; same as 'ui,io,doc'
    """

    description: str
    is_unknown: bool
    custom_offset: Union[int, str]
    usage: str


def is_io_usage(usage: Union[str, None]) -> bool:
    """A field of this usage (FieldExtras) is read and written"""
    return usage is None or usage == 'everywhere' or 'io' in usage


class CompoundBlock(DataBlockWithChildren, DataBlock, ABC):
    # a description rendering the block inline in the docs, like a leaf block; a subclass can set it as a class attribute
    inline_description: str = None

    # accepts list of fields. Field should be declared as tuple (name, block, extras)
    def __init__(self, fields: List[Tuple[str, DataBlock, FieldExtras]], inline_description: str = None, **kwargs):
        super().__init__(**kwargs)
        self.fields = fields
        if inline_description is not None:
            self.inline_description = inline_description
        self.field_blocks = [(name, instance) for (name, instance, _) in self.fields]
        self.field_blocks_map = {name: res for (name, res, _) in self.fields}
        self.field_extras_map = {name: extra for (name, _, extra) in self.fields}
        # the fields read and written (usage everywhere or with 'io')
        self.io_field_blocks = [
            (name, instance) for (name, instance, extra) in self.fields if is_io_usage(extra.get('usage', 'everywhere'))
        ]

    @property
    def schema(self) -> Dict:
        schema = {
            **super().schema,
            'block_description': '',
            'inline_description': False,
            'fields': [
                {
                    'name': name,
                    'schema': field.schema,
                    'is_unknown': self.field_extras_map.get(name, {}).get('is_unknown', False),
                    'description': self.field_extras_map.get(name, {}).get('description', ''),
                    'usage': self.field_extras_map.get(name, {}).get('usage', 'everywhere'),
                }
                for name, field in self.field_blocks
            ]
            if self.fields
            else [],
        }
        if self.inline_description is not None:
            schema['inline_description'] = True
            schema['block_description'] = self.inline_description
        return schema

    def get_child_block(self, name: str) -> 'DataBlock':
        field = self.field_blocks_map.get(name)
        if field is None:
            raise BlockDefinitionException(f'Cannot find field {name}')
        return field

    def get_child_block_with_data(self, unpacked_data: dict, name: str) -> Tuple['DataBlock', Any]:
        path = name.split('/')
        field = self.field_blocks_map.get(path[0])
        if field is None:
            raise BlockDefinitionException(f'Cannot find field {path[0]}')
        udata = unpacked_data.get(path[0])
        if len(path) > 1:
            return field.get_child_block_with_data(udata, '/'.join(path[1:]))
        else:
            return field, udata

    # For auto-generated documentation only
    @property
    def size_doc_str(self):
        acc = 0
        if callable(self.fields):
            return '?'
        for name, field in self.io_field_blocks:
            field_size_doc = field.size_doc_str
            acc = add_doc_numbers(acc, field_size_doc, show_expressions=False, produce_ranges=True)
        return acc

    def new_data(self, patch=None):
        res = dict()
        if patch is None:
            patch = {}
        for name, field in self.field_blocks:
            res[name] = field.new_data(patch.get(name, {}))
        return res

    # True when the class reads, writes and sizes the data field by field, as CompoundBlock does: its fixed size and
    # struct format then come from the fields. A subclass overriding read / write / estimate_packed_size without
    # changing that (Point3D without normalization) overrides this too
    @property
    def field_by_field_io(self) -> bool:
        cls = type(self)
        return (
            cls.read is CompoundBlock.read
            and cls.write is CompoundBlock.write
            and cls.estimate_packed_size is CompoundBlock.estimate_packed_size
        )

    @cached_property
    def fixed_size(self) -> Optional[int]:
        if not self.field_by_field_io:
            return None
        res = 0
        for _, field in self.io_field_blocks:
            if field.fixed_size is None:
                return None
            res += field.fixed_size
        return res

    @cached_property
    def struct_format(self) -> Optional[Tuple[str, str]]:
        if not self.field_by_field_io or self.value_validator is not None or self.programmatic_value is not None:
            return None
        return join_struct_formats(field for _, field in self.io_field_blocks)

    # (name, block, the value is the unpacked value as it is) of the io fields, for from_struct / to_struct
    @cached_property
    def struct_fields(self) -> List[Tuple[str, DataBlock, bool]]:
        return [(name, field, field.struct_raw) for name, field in self.io_field_blocks]

    def from_struct(self, values: tuple, index: int):
        res = {}
        for name, field, is_raw in self.struct_fields:
            if is_raw:
                res[name] = values[index]
                index += 1
            else:
                res[name], index = field.from_struct(values, index)
        return res, index

    def to_struct(self, data, values: list):
        for name, field, is_raw in self.struct_fields:
            if is_raw:
                values.append(data[name])
            else:
                field.to_struct(data[name], values)

    def read(self, ctx: ReadContext, name: str = '', read_bytes_amount=None):
        record = self.struct_record
        if record is not None:
            start = ctx.buffer.tell()
            try:
                return record.read(ctx.buffer)
            except Exception:
                # end of buffer, a value the field cannot hold: the field by field read raises it with its context
                ctx.buffer.seek(start)
        res = dict()
        self_ctx = ctx.get_or_create_child(name, self, read_bytes_amount, res)
        for name, field in self.io_field_blocks:
            res[name] = field.unpack(ctx=self_ctx, name=name, read_bytes_amount=self_ctx.read_bytes_remaining)
        return res

    def estimate_packed_size(self, data, ctx: WriteContext = None):
        if self.fixed_size is not None:
            return self.fixed_size
        self_ctx = WriteContext(data=data, block=self, parent=ctx)
        res = 0
        for name, field in self.io_field_blocks:
            res += field.estimate_packed_size(data=data.get(name), ctx=self_ctx)
        return res

    def offset_to_child_when_packed(self, data, child_name: str, ctx: WriteContext = None):
        self_ctx = WriteContext(data=data, block=self, parent=ctx)
        res = 0
        for name, field in self.io_field_blocks:
            if name == child_name:
                return res
            res += field.estimate_packed_size(data=data.get(name), ctx=self_ctx)
        raise DataIntegrityException(
            ctx=ctx, message=f'Cannot calculate offset to child "{child_name}". Child with such name not found'
        )

    def write(self, data, ctx: WriteContext = None, name: str = '') -> bytes:
        record = self.struct_record
        if record is not None:
            try:
                return record.write(data)
            except Exception:
                # a missing value or one the field cannot hold: the field by field write raises it with its context
                pass
        self_ctx = WriteContext(data=data, name=name, block=self, parent=ctx)
        self_ctx.result = bytes()
        for name, field in self.io_field_blocks:
            self_ctx.result += field.pack(data=data.get(name), ctx=self_ctx, name=name)
        return self_ctx.result


class SubByteCompoundBlock(IntegerBlock):
    ### schema type: (size, alias, type, details, description)
    ### example 1: (4, 'damage', 'number', [], 'Damage switch (0x8 means damaged)')
    ### example 2: (1, 'is_damaged', 'boolean', [], 'Flag is damaged')
    ### example 3: (2, 'test_enum', 'enum', ['A', 'B', 'C', 'D'], '...')
    def __init__(self, schema: List[Tuple[int, str, str, List[str], str]], **kwargs):
        super().__init__(**kwargs)
        self._schema_def = schema
        # (bit position, mask, alias, type, value by number, number by value) of each value
        self._bit_fields = []
        current_bit = self.length * 8
        for size, alias, type_name, details, _ in schema:
            current_bit -= size
            self._bit_fields.append(
                (
                    current_bit,
                    (1 << size) - 1,
                    alias,
                    type_name,
                    {i: v for i, v in enumerate(details)},
                    {v: i for i, v in enumerate(details)},
                )
            )
        total_bits = sum(size for size, _, _, _, _ in schema)
        if total_bits != self.length * 8:
            raise BlockDefinitionException(
                f'SubByteCompoundBlock schema total bits ({total_bits}) does not match length * 8 ({self.length * 8})'
            )

    @property
    def schema(self) -> Dict:
        block_description = f'Sub-byte compound block'
        if self.length > 1:
            block_description += f' ({self.byte_order} endian)'
        block_description += ':'
        for size, alias, type_name, details, description in self._schema_def:
            if type_name == 'boolean':
                block_description += f'<br/>1-bit flag "{alias}"'
            elif type_name == 'number':
                block_description += f'<br/>{size}-bits int "{alias}"'
            elif type_name == 'enum':
                block_description += f'<br/>{size}-bits enum:'
                for i, v in enumerate(details):
                    block_description += f'<br/>&nbsp;&nbsp;- {i}: {v}'

        return {
            **super().schema,
            'block_description': block_description,
            'inline_description': True,
            'sub_byte_schema': [
                {'size': size, 'alias': alias, 'type': type_name, 'details': details, 'description': description}
                for size, alias, type_name, details, description in self._schema_def
            ],
        }

    def new_data(self, patch=None):
        res = {}
        for size, alias, type_name, details, description in self._schema_def:
            if type_name == 'boolean':
                res[alias] = False
            elif type_name == 'enum':
                res[alias] = details[0] if details else '0'
            else:
                res[alias] = 0
        return res

    def from_raw(self, raw: int):
        res = {}
        for bit, mask, alias, type_name, value_by_number, _ in self._bit_fields:
            value = (raw >> bit) & mask
            if type_name == 'boolean':
                res[alias] = bool(value)
            elif type_name == 'enum':
                res[alias] = value_by_number.get(value, str(value))
            else:
                res[alias] = value
        return res

    def to_raw(self, value) -> int:
        res = 0
        for bit, mask, alias, type_name, _, number_by_value in self._bit_fields:
            field_value = value.get(alias)
            if type_name == 'boolean':
                int_val = 1 if field_value else 0
            elif type_name == 'enum':
                try:
                    int_val = number_by_value[field_value]
                except KeyError:
                    int_val = int(field_value)
            else:
                int_val = int(field_value)
            res |= (int_val & mask) << bit
        return res


class BitFlagsBlock(SubByteCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'flag_names': self.flag_name_map,
            'block_description': f'{self.length * 8} flags container<br/><details><summary>flag names (from least to most significant)</summary>'
            + '<br/>'.join([f'{i}: {x}' for i, x in enumerate(self.flag_name_map) if x != str(i)])
            + '</details>',
        }

    def __init__(self, flag_names: List[Tuple[int, str]], **kwargs):
        self.flag_names = flag_names
        length = kwargs.pop('length', None)
        if length is None:
            raise Exception('BitFlagsBlock requires length')
        schema = []
        self.flag_name_map = [str(i) for i in range(length * 8)]
        for value, name in self.flag_names:
            self.flag_name_map[value] = name
        for i in range(length * 8 - 1, -1, -1):
            schema.append((1, self.flag_name_map[i], 'boolean', '', ''))
        super().__init__(length=length, schema=schema, **kwargs)


class CompoundBlockFields(ABC):
    @class_property
    def fields(cls) -> List[Tuple[str, DataBlock]]:
        try:
            return cls.__fields_cache
        except AttributeError:
            cls.__fields_cache = [
                (key, value)
                for (key, value) in cls.__dict__.items()
                if isinstance(value, DataBlock)
                or (type(value) is tuple and len(value) > 0 and isinstance(value[0], DataBlock))
            ]
            return cls.__fields_cache


class DeclarativeCompoundBlock(CompoundBlock):
    class Fields(CompoundBlockFields):
        pass

    def __init__(self, **kwargs):
        super().__init__(
            fields=[
                (name, *declaration) if type(declaration) is tuple else (name, declaration, {})
                for name, declaration in self.__class__.Fields.fields
            ],
            **kwargs,
        )
