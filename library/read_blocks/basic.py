from abc import ABC, abstractmethod
from functools import cached_property
from io import SEEK_CUR, BytesIO
from typing import Dict, Any, Tuple, Optional

from library.context import ReadContext, WriteContext, DocumentationContext
from library.exceptions import DataIntegrityException, BlockDefinitionException, EndOfBufferException
from library.read_blocks.misc.value_validators import ValueValidator
from library.read_blocks.struct_record import StructRecord
from library.utils import represent_value_as_str


# cached properties computed from a block's settings
CACHED_LAYOUT_PROPERTIES = ('fixed_size', 'struct_format', 'struct_raw', 'struct_record', 'struct_fields')


class DataBlock(ABC):
    root_read_ctx = ReadContext()
    # name of the block's serializer class in the `serializers` package (conversion in the GUI / CLI), None: not
    # convertible on its own; override `serializer_class` for a serializer depending on the block's settings
    serializer: str = None

    # a class attribute `block_description = '...'` is the description of the class's blocks (docs and GUI): their
    # schema gets it over what the class's own schema or its base classes give, as a `schema` override setting it would
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if 'block_description' not in cls.__dict__:
            return
        description = cls.__dict__['block_description']
        own_schema = cls.__dict__.get('schema')

        def schema(self) -> Dict:
            base = own_schema.fget(self) if own_schema is not None else super(cls, self).schema
            return {**base, 'block_description': description}

        cls.schema = property(schema)

    def __init__(self, value_validator: ValueValidator = None, programmatic_value=None, **kwargs):
        self.value_validator = value_validator
        self.programmatic_value = programmatic_value

    # For auto-generated documentation only
    @property
    def size_doc_str(self):
        return '?'

    # For GUI
    @property
    def schema(self) -> Dict:
        s = {
            'block_class_mro': '__'.join(
                [x.__name__ for x in self.__class__.mro() if x.__name__ not in ['object', 'ABC']]
            ),
            'block_description': '',
        }
        if self.value_validator:
            s['value_validator'] = self.value_validator.schema()
        if self.programmatic_value:
            s['is_programmatic'] = True
        if self.serializer_class():
            s['serialization'] = self.serializer_class()().ui_serialization()
        return s

    def get_child_block(self, name: str) -> 'DataBlock':
        return None

    def get_child_block_with_data(self, unpacked_data, name) -> Tuple['DataBlock', Any]:
        return None, unpacked_data.get(name)

    # creates empty data
    def new_data(self, patch=None):
        if self.value_validator:
            return self.value_validator.new_data()
        raise BlockDefinitionException('Cannot generate new data for block.')

    def serializer_class(self):
        if self.serializer is None:
            return None
        import serializers

        return getattr(serializers, self.serializer)

    # Packed size of every value of the block (what `estimate_packed_size` returns for any data), None when it depends
    # on the data. Cached, like the struct properties below
    @cached_property
    def fixed_size(self) -> Optional[int]:
        return None

    # (byte order '<' / '>', or '' when it does not matter, and the `struct` format characters) of a block whose packed
    # value `struct` reads and writes, with `from_struct` / `to_struct` converting it from / to the unpacked values;
    # None for other blocks. A block with a value validator or a programmatic value has none
    @cached_property
    def struct_format(self) -> Optional[Tuple[str, str]]:
        return None

    # True when the value is the one unpacked `struct` value as it is (plain numbers)
    @cached_property
    def struct_raw(self) -> bool:
        return False

    # The precompiled `struct` reader / writer of the block's values, None when the block has no struct format
    @cached_property
    def struct_record(self) -> Optional[StructRecord]:
        struct_format = self.struct_format
        if struct_format is None or not struct_format[1]:
            return None
        return StructRecord(self)

    def from_struct(self, values: tuple, index: int) -> Tuple[Any, int]:
        """The value of the block from `struct`-unpacked `values` at `index`, and the index after its values"""
        raise NotImplementedError

    def to_struct(self, data, values: list):
        """Appends the `struct` values of `data` to `values`"""
        raise NotImplementedError

    # copies (deepcopy, pickle) leave the cached layout out: a copy may get other settings (`big_endian_copy`), and a
    # `struct.Struct` cannot be copied
    def __getstate__(self):
        state = self.__dict__.copy()
        for name in CACHED_LAYOUT_PROPERTIES:
            state.pop(name, None)
        return state

    @abstractmethod
    def read(self, ctx: ReadContext, name: str = '', read_bytes_amount=None):
        pass

    def estimate_packed_size(self, data, ctx: WriteContext = None):
        raise BlockDefinitionException(
            ctx=ctx,
            message='Cannot estimate packed size of data block '
            + '__'.join([x.__name__ for x in self.__class__.mro() if x.__name__ not in ['object', 'ABC']]),
        )

    @abstractmethod
    def write(self, data, ctx: WriteContext = None, name: str = '') -> bytes:
        pass

    def validate_after_read(self, value, ctx: ReadContext = root_read_ctx, name: str = ''):
        if self.value_validator and not self.value_validator.validate(value):
            raise DataIntegrityException(
                ctx=ctx, message=f'Expected {self.value_validator}, found {represent_value_as_str(value)} at {name}'
            )

    ### final method, should never override
    def unpack(self, ctx: ReadContext = root_read_ctx, name: str = '', read_bytes_amount=None):
        v = self.read(ctx=ctx, name=name, read_bytes_amount=read_bytes_amount)
        self.validate_after_read(v, ctx, name)
        return v

    ### final method, should never override. Shortcut for reading data from pure bytes
    def unpack_from_bytes(self, b: bytes, name: str = ''):
        return self.unpack(ReadContext(BytesIO(b)), name=name, read_bytes_amount=len(b))

    ### final method, should never override
    def pack(self, data, ctx: WriteContext = None, name: str = '') -> bytes:
        if self.programmatic_value:
            data = self.programmatic_value(ctx)
        return self.write(data, ctx, name)


class DataBlockWithChildren(ABC):
    ### get child block
    @abstractmethod
    def get_child_block(self, name: str) -> 'DataBlock':
        pass

    ### from given unpacked data, get offset to child block by name in packed byte array
    @abstractmethod
    def offset_to_child_when_packed(self, data, child_name: str, ctx: WriteContext = None):
        index = int(child_name)
        if index >= len(data):
            raise IndexError()
        return self.estimate_packed_size(data[:index], ctx)


class BytesBlock(DataBlock):
    serializer = 'PlainBinarySerializer'

    def __init__(self, length, allow_negative_length=False, **kwargs):
        super().__init__(**kwargs)
        self._length = length
        self.allow_negative_length = allow_negative_length

    # For auto-generated documentation only
    @property
    def size_doc_str(self):
        if isinstance(self._length, tuple):
            (_, doc_str) = self._length
            return doc_str
        if callable(self._length):
            try:
                return str(self._length(DocumentationContext()))
            except:
                return 'custom_func'
        else:
            return str(self._length)

    @property
    def schema(self) -> Dict:
        descr = 'Bytes'
        if self.value_validator is not None:
            descr += f'. {self.value_validator}'
        return {
            **super().schema,
            'block_description': descr,
        }

    def resolve_length(self, ctx):
        self_len = self._length
        if isinstance(self_len, tuple):
            # cut off the documentation
            (self_len, _) = self_len
        if callable(self_len):
            self_len = self_len(ctx)
        return self_len

    def new_data(self, patch=None):
        if self.value_validator:
            return self.value_validator.new_data()
        self_len = self._length
        if isinstance(self_len, tuple):
            # cut off the documentation
            (self_len, _) = self_len
        if callable(self_len) or self_len is None:
            return b''
        return bytes([0] * self_len)

    def read(self, ctx: ReadContext, name: str = '', read_bytes_amount=None):
        self_len = self.resolve_length(ctx)
        if self_len < 0:
            if self.allow_negative_length:
                ctx.buffer.seek(self_len, SEEK_CUR)
                return b''
            raise BlockDefinitionException(ctx=ctx, message='Cannot read bytes block with negative length')
        res = ctx.buffer.read(self_len)
        if len(res) < self_len:
            raise EndOfBufferException(ctx=ctx.get_or_create_child(name, self))
        return res

    def estimate_packed_size(self, data, ctx: WriteContext = None):
        return len(data)

    def write(self, data, ctx: WriteContext = None, name: str = '') -> bytes:
        return data


class Padding(BytesBlock):
    def __init__(self, to, is_global=False, **kwargs):
        # handle case where 'to' is a tuple (lambda, description)
        to_lambda = to[0] if isinstance(to, tuple) else to
        if isinstance(to, tuple):
            to_descr = to[1]
        elif callable(to):
            try:
                to_descr = to(DocumentationContext())
            except:
                to_descr = '?'
        else:
            to_descr = str(to)
        super().__init__(
            length=(
                lambda ctx: (
                    (to_lambda(ctx) if callable(to_lambda) else to_lambda)
                    - (ctx.buffer.tell() if is_global else ctx.local_buffer_pos)
                ),
                f'up to offset {to_descr}',
            ),
            **kwargs,
        )
        self.to = to
        self.to_descr = to_descr
        self.is_global = is_global

    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Padding bytes',
        }
