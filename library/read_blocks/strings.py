from typing import Dict

from library.context import ReadContext, WriteContext
from library.exceptions import DataIntegrityException, EndOfBufferException
from library.read_blocks.basic import DataBlock, LengthPrefixed, read_length
from library.read_blocks.references import is_static_param, param_doc, param_value


_ENCODING_NAMES = {'utf-8': 'UTF-8', 'latin-1': 'Latin-1'}


class UTF8Block(DataBlock):
    # `length`: a block parameter (library/read_blocks/references.py). `encoding`: of the text, 'latin-1' for 8-bit
    # characters (Windows-1252 / Latin-1: `Coupé`; bytes after the first zero are kept as characters, so a field with
    # leftovers there writes back byte-exact)
    def __init__(self, length, encoding: str = 'utf-8', **kwargs):
        super().__init__(**kwargs)
        self._length = length
        self.encoding = encoding

    @property
    def schema(self) -> Dict:
        descr = f'{_ENCODING_NAMES.get(self.encoding, self.encoding)} string'
        if self.value_validator:
            descr += f'. {self.value_validator}'
        return {**super().schema, 'block_description': descr, 'length': self.size_doc_str}

    # For auto-generated documentation only
    @property
    def size_doc_str(self):
        return param_doc(self._length)

    def resolve_length(self, ctx):
        return param_value(self._length, ctx)

    def _get_static_length(self):
        if not is_static_param(self._length):
            return None
        return self._length[0] if isinstance(self._length, tuple) else self._length

    def new_data(self, patch=None):
        if self.value_validator:
            return self.value_validator.new_data()
        return ''

    # lengths are in bytes: a character outside ASCII takes 2..4 of them
    def read(self, ctx: ReadContext, name: str = '', read_bytes_amount=None, resolved_length=None):
        self_len = read_length(self._length, ctx, read_bytes_amount) if resolved_length is None else resolved_length
        raw = ctx.buffer.read(self_len)
        if len(raw) < self_len:
            raise EndOfBufferException(ctx=ctx)
        res = raw.decode(self.encoding)
        if self._length == self_len:
            res = res.rstrip('\x00')
        return res

    def estimate_packed_size(self, data, ctx: WriteContext = None):
        static_length = self._get_static_length()
        length = len(data.encode(self.encoding))
        if static_length is not None:
            return max(length, static_length)
        return length

    def write(self, data, ctx: WriteContext = None, name: str = '') -> bytes:
        raw = data.encode(self.encoding)
        static_length = self._get_static_length()
        if static_length is not None:
            if len(raw) > static_length:
                raise DataIntegrityException(
                    f'"{data}" is {len(raw)} bytes, {name or "the field"} holds {static_length}', ctx=ctx
                )
            raw += b'\x00' * (static_length - len(raw))
        return raw


class LengthPrefixedUtf8Block(LengthPrefixed, UTF8Block):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Utf-8 block, prefixed with length field'}

    def prefix_value(self, data, packed_size: int) -> int:
        return packed_size


class NullTerminatedUTF8Block(DataBlock):
    """`errors`: how bytes which are not UTF-8 are read. 'ignore' drops them; 'surrogateescape' keeps each as a
    character U+DC80..U+DCFF, written back as the same byte (for fields where they occur and the file must stay
    byte-exact; such a string cannot be written to a UTF-8 text file as is)"""

    def __init__(self, length, errors: str = 'ignore', **kwargs):
        super().__init__(**kwargs)
        self._length = length
        self.errors = errors

    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Null-terminated UTF-8 string. Ends with first occurrence of zero byte',
            'length': self.size_doc_str,
        }

    # For auto-generated documentation only
    @property
    def size_doc_str(self):
        return '1..?'

    def read(self, ctx: ReadContext, name: str = '', read_bytes_amount=None):
        # up to the first zero, past `length` too; read in slots of `length` bytes
        start = ctx.buffer.tell()
        slot = self._length if type(self._length) is int and self._length > 0 else 64
        res = b''
        while True:
            chunk = ctx.buffer.read(slot)
            if not chunk:
                raise EndOfBufferException(ctx=ctx)
            end = chunk.find(b'\0')
            if end >= 0:
                res += chunk[:end]
                ctx.buffer.seek(start + len(res) + 1)
                return res.decode('utf-8', errors=self.errors)
            res += chunk

    def encode(self, data: str) -> bytes:
        return data.encode('utf-8', errors='surrogateescape' if self.errors == 'surrogateescape' else 'strict')

    def estimate_packed_size(self, data, ctx: WriteContext = None):
        return len(self.encode(data)) + 1

    def write(self, data, ctx: WriteContext = None, name: str = '') -> bytes:
        return self.encode(data) + b'\00'
