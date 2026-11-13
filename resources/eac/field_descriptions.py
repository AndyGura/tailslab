"""EA's field description files (`.DES`): the developers' description of a data file (`.DAT`) of NFS2 / NFS2 SE
(car physics `P*.DES`, `SIMTUNE.DES`, the car AI `MCF1.DES`, `TRAFCFG.DES`, `PRSONAL.DES`, the smackables `SM*.DES`)
and NFS5 (`TRAFCFG.DES`). Written by EA's data editor, read by no game executable.

Layout: a body = 94 bytes (memory garbage), int size of the described data, int size of the records, a copy of the
data, then the records. A record = type (10 bytes) and name (80 bytes), text up to the first zero followed by memory
garbage, int size of the field's data, int n, then n bytes: a `Chain` (a group of fields) holds a body of its own (the
group's data and its records), an `Array` / `CArray` 3 ints (the shape), the other types memory garbage. The file is
a body."""

from io import SEEK_CUR
from typing import Dict, List, Optional

from library.context import ReadContext, WriteContext
from library.exceptions import DataIntegrityException, EndOfBufferException
from library.read_blocks import ArrayBlock, BytesBlock, CompoundBlock, DelegateBlock, IntegerBlock, UTF8Block

DES_BODY_HEADER_LENGTH = 94
DES_RECORD_TYPE_LENGTH = 10
DES_RECORD_NAME_LENGTH = 80
# type + name + data size + n
DES_RECORD_HEADER_LENGTH = DES_RECORD_TYPE_LENGTH + DES_RECORD_NAME_LENGTH + 8
# bodies nested in chains: the shipped files have up to 3 (TRAFCFG.DES: "Glue Factors" > "Single Race Glue Factors" >
# "Laps"); chains deeper than this keep their body as raw bytes
DES_MAX_DEPTH = 6
DES_TYPES = ('Fixed', 'Integer', 'Char', 'Array', 'CArray', 'Import', 'Chain')
# keys `EaFieldDescriptions.read` adds for the GUI (not in the file): the TailsLab block of the described data and its
# fields (`block_layout`), to show beside the descriptions
DES_UI_KEYS = ('dat_block', 'dat_fields')


class DesTextBlock(UTF8Block):
    """Text of a fixed-size `.DES` text field: the bytes before the first zero, as Latin-1. The zero and the bytes after
    it are the next field (`DesTextRestBlock`), so a field without a zero (a name of 80 characters) is all text"""

    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': f'Text, up to {self._get_static_length()} Latin-1 characters before the first zero',
        }

    @property
    def size_doc_str(self):
        return f'0..{self._get_static_length()}'

    def read(self, ctx: ReadContext, name: str = '', read_bytes_amount=None, resolved_length=None):
        length = self._get_static_length()
        raw = ctx.buffer.read(length)
        if len(raw) < length:
            raise EndOfBufferException(ctx=ctx)
        text = raw.split(b'\0', 1)[0]
        ctx.buffer.seek(len(text) - len(raw), SEEK_CUR)
        return text.decode('latin-1')

    def estimate_packed_size(self, data, ctx: WriteContext = None):
        return len(data.encode('latin-1'))

    def write(self, data, ctx: WriteContext = None, name: str = '') -> bytes:
        raw = data.encode('latin-1')
        if len(raw) > self._get_static_length() or b'\0' in raw:
            raise DataIntegrityException(
                ctx=ctx, message=f'"{data}": at most {self._get_static_length()} characters, no zero character'
            )
        return raw


def _fit_text_rest(rest: bytes, length: int) -> bytes:
    """The bytes after a text of a fixed-size field, fitted to `length` (the field size - the text length): starting
    with the terminating zero, the stored bytes kept as far as they fit, zeros added"""
    if length <= 0:
        return b''
    rest = rest if rest[:1] == b'\0' else b'\0' + rest
    return rest[:length] + b'\0' * max(0, length - len(rest))


class DesTextRestBlock(BytesBlock):
    """The rest of a fixed-size `.DES` text field after its text (`text_field`): the terminating zero and the bytes
    after it, garbage of the developers' tool kept for writing the file back byte-exact. Refitted on write when the
    text changes length"""

    def __init__(self, text_field: str, field_length: int, **kwargs):
        self.text_field = text_field
        self.field_length = field_length
        super().__init__(
            length=(
                lambda ctx: field_length - len(ctx.data(text_field).encode('latin-1')),
                f'{field_length} - len({text_field})',
            ),
            **kwargs,
        )

    def _length_for(self, ctx) -> Optional[int]:
        try:
            return self.field_length - len(ctx.data(self.text_field).encode('latin-1'))
        except Exception:
            return None

    def estimate_packed_size(self, data, ctx: WriteContext = None):
        length = self._length_for(ctx) if ctx is not None else None
        return len(data) if length is None else length

    def write(self, data, ctx: WriteContext = None, name: str = '') -> bytes:
        length = self._length_for(ctx) if ctx is not None else None
        return data if length is None else _fit_text_rest(data, length)


def _peek_record_count(ctx) -> int:
    """Records of a body: walked over their n (at +94 of each record) until the body's records size is used up"""
    end = ctx.buffer.tell() + ctx.data('records_size')
    start = ctx.buffer.tell()
    count = 0
    try:
        pos = start
        while pos < end:
            ctx.buffer.seek(pos + DES_RECORD_HEADER_LENGTH - 4)
            n = int.from_bytes(ctx.buffer.read(4), 'little', signed=True)
            if n < 0:
                raise DataIntegrityException(ctx=ctx, message=f'Negative record length {n} at {pos}')
            pos += DES_RECORD_HEADER_LENGTH + n
            count += 1
        if pos != end:
            raise DataIntegrityException(ctx=ctx, message='Records do not end with the records size of the body')
    finally:
        ctx.buffer.seek(start)
    return count


def _record_extra_choice(ctx, **_) -> int:
    if ctx.data('type') == 'Chain':
        return 0
    if ctx.data('type') in ('Array', 'CArray') and ctx.data('extra_length') == 12:
        return 1
    return 2


class EaFieldDescriptionShape(CompoundBlock):
    def __init__(self, **kwargs):
        super().__init__(
            fields=[
                (
                    'dimensions',
                    IntegerBlock(length=4, is_signed=True),
                    {'description': '1 for the arrays of one row; 2 for the unnamed pairs of `TRAFCFG.DES`'},
                ),
                (
                    'size_1',
                    IntegerBlock(length=4, is_signed=True),
                    {'description': 'The element count of one-row arrays; 1 for the `TRAFCFG.DES` pairs'},
                ),
                (
                    'size_2',
                    IntegerBlock(length=4, is_signed=True),
                    {'description': 'The element count again; 2 for the `TRAFCFG.DES` pairs'},
                ),
            ],
            inline_description='Shape of an `Array` / `CArray` record: 3 ints',
            **kwargs,
        )


class EaFieldDescriptionRecord(CompoundBlock):
    """A field (or a group of fields, `Chain`) of the described data. `depth`: how many chain bodies hold it"""

    def __init__(self, depth: int = 0, **kwargs):
        self.depth = depth
        if depth + 1 < DES_MAX_DEPTH:
            chain_body = EaFieldDescriptionBody(depth=depth + 1)
        else:
            chain_body = BytesBlock(length=(lambda ctx: ctx.data('extra_length'), 'extra_length'))
        extra = DelegateBlock(
            possible_blocks=[
                chain_body,
                EaFieldDescriptionShape(),
                BytesBlock(length=(lambda ctx: ctx.data('extra_length'), 'extra_length')),
            ],
            choice_index=(_record_extra_choice, '`Chain`: a body; `Array` / `CArray`: the shape; else bytes'),
        )
        super().__init__(
            fields=[
                (
                    'type',
                    DesTextBlock(length=DES_RECORD_TYPE_LENGTH),
                    {
                        'description': 'Type of the field: `Fixed` (16.16 fixed point), `Integer` (int), `Char` (1 '
                        'byte), `Array` (4-byte elements, no element type), `CArray` (bytes), `Import` (a table '
                        'imported from another file, e.g. the AI acceleration tables), `Chain` (a group of fields)'
                    },
                ),
                (
                    'type_rest',
                    DesTextRestBlock('type', DES_RECORD_TYPE_LENGTH),
                    {
                        'usage': 'io,doc',
                        'custom_offset': 'len(type)',
                        'description': 'Rest of the 10-byte type field: a zero, then memory garbage',
                    },
                ),
                (
                    'name',
                    DesTextBlock(length=DES_RECORD_NAME_LENGTH),
                    {
                        'custom_offset': 10,
                        'description': 'Name of the field as the developers wrote it, often with a comment or a '
                        'heading ("SIM MODE ---- telepole launch Value"); a name of 80 characters has no zero',
                    },
                ),
                (
                    'name_rest',
                    DesTextRestBlock('name', DES_RECORD_NAME_LENGTH),
                    {
                        'usage': 'io,doc',
                        'custom_offset': '10 + len(name)',
                        'description': 'Rest of the 80-byte name field: a zero, then memory garbage',
                    },
                ),
                (
                    'data_size',
                    IntegerBlock(length=4, is_signed=True),
                    {
                        'custom_offset': 90,
                        'description': 'Size of the field in the described data, bytes; the fields follow each other '
                        'without gaps, so the sizes of the records before it give its offset',
                    },
                ),
                (
                    'extra_length',
                    IntegerBlock(
                        length=4,
                        is_signed=True,
                        programmatic_value=lambda ctx: extra.estimate_packed_size(ctx.data('extra'), ctx),
                    ),
                    {
                        'usage': 'io,doc',
                        'custom_offset': 94,
                        'description': 'Length of `extra`: 0x38 for `Fixed` / `Integer` / `Char` (one `Fixed` of '
                        '`TRAFCFG.DES` has 0x10), 12 for `Array` / `CArray`, 1 for `Import`, the body for `Chain`',
                    },
                ),
                (
                    'extra',
                    extra,
                    {
                        'custom_offset': 98,
                        'description': '`Chain`: the body of the group (`EaFieldDescriptionBody`); `Array` / `CArray`: '
                        'the shape (`EaFieldDescriptionShape`); else memory garbage (`Import`: one byte, "A")',
                    },
                ),
            ],
            **kwargs,
        )

    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A field description: type and name, then the size of the field, then the '
            'type-specific part (a `Chain` holds the body of its group)',
        }


class EaFieldDescriptionBody(CompoundBlock):
    """Data copy and field records of a file or of a `Chain` group. `depth`: how many chain bodies hold it"""

    def __init__(self, depth: int = 0, **kwargs):
        self.depth = depth
        records = ArrayBlock(
            child=EaFieldDescriptionRecord(depth=depth),
            length=(_peek_record_count, 'until `records_size` bytes are read'),
        )
        super().__init__(
            fields=[
                (
                    'header',
                    BytesBlock(length=DES_BODY_HEADER_LENGTH),
                    {
                        'usage': 'io,doc',
                        'description': "Memory garbage of the developers' tool (in the file's body, leftovers of "
                        'code and texts), kept for writing the file back byte-exact',
                    },
                ),
                (
                    'data_size',
                    IntegerBlock(length=4, is_signed=True, programmatic_value=lambda ctx: len(ctx.data('data'))),
                    {'usage': 'io,doc', 'description': 'Size of `data`: the size of the described data or group'},
                ),
                (
                    'records_size',
                    IntegerBlock(
                        length=4,
                        is_signed=True,
                        programmatic_value=lambda ctx: records.estimate_packed_size(ctx.data('records'), ctx),
                    ),
                    {'usage': 'io,doc', 'description': 'Size of `records` in bytes'},
                ),
                (
                    'data',
                    BytesBlock(length=(lambda ctx: ctx.data('data_size'), 'data_size')),
                    {
                        'description': 'Copy of the described data (of the group, in a `Chain`) as the tool saved it: '
                        'the `.DAT` of the time, which can differ from the shipped one'
                    },
                ),
                (
                    'records',
                    records,
                    {
                        'description': 'The field descriptions, in the order of the fields in `data`; their '
                        '`data_size` add up to the size of `data`'
                    },
                ),
            ],
            **kwargs,
        )

    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A copy of the described data and the descriptions of its fields (the whole file, or '
            'the body of a `Chain` record)',
        }


class EaFieldDescriptions(EaFieldDescriptionBody):
    """A `.DES` file: a body (`EaFieldDescriptionBody`)"""

    def __init__(self, **kwargs):
        super().__init__(depth=0, **kwargs)

    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': "EA's field description file (`.DES`): the developers' description of a data file "
            '(`.DAT`) written by their data editor, read by no game. NFS2 / NFS2 SE: `P<car>.DES` next to '
            '`P<car>.DAT` (`Nfs2CarPhysics`), `GAMEDATA/CARMODEL/PC/SIMTUNE.DES` (`Nfs2SimTune`), '
            '`GAMEDATA/SIM/CARDATA/MCF1.DES` (`Nfs2CarAi`), `GAMEDATA/SIM/AI/TRAFCFG.DES` (`Nfs2TrafficConfig`) and '
            '`PRSONAL.DES` (`Nfs2Personalities`), `GAMEDATA/TRACKS/DATA/PC/SM<track>.DES` (the smackables `SM*.DAT`, '
            'not parsed); NFS5: `GameData/Simulation/AI/TRAFCFG.DES`. A body: memory garbage, a copy of the data, '
            'then one record per field (type, name, size), groups of fields as `Chain` records holding a body of '
            'their own. Field names and types of the data files come from them',
        }

    def read(self, ctx: ReadContext, name: str = '', read_bytes_amount=None):
        res = super().read(ctx, name, read_bytes_amount)
        file_name = getattr(ctx, 'ctx_path', None) or name or ''
        target = described_block(len(res['data']), file_name)
        res['dat_block'] = target.__class__.__name__ if target is not None else None
        res['dat_fields'] = block_layout(target) if target is not None else []
        return res

    def serializer_class(self):
        from serializers.misc.ea_field_descriptions import EaFieldDescriptionsSerializer

        return EaFieldDescriptionsSerializer


def is_ea_field_descriptions(header: bytes, length: Optional[int]) -> bool:
    """A `.DES` file: the body's data and records sizes add up to the file length"""
    if length is None or length < DES_BODY_HEADER_LENGTH + 8 or len(header) < DES_BODY_HEADER_LENGTH + 8:
        return False
    data_size = int.from_bytes(header[DES_BODY_HEADER_LENGTH : DES_BODY_HEADER_LENGTH + 4], 'little', signed=True)
    records_size = int.from_bytes(
        header[DES_BODY_HEADER_LENGTH + 4 : DES_BODY_HEADER_LENGTH + 8], 'little', signed=True
    )
    return data_size >= 0 and records_size >= 0 and DES_BODY_HEADER_LENGTH + 8 + data_size + records_size == length


def des_fields(body: dict, offset: int = 0, path: str = '') -> List[dict]:
    """The fields a `.DES` body describes, groups flattened, in data order: path (group names and the field name, `/`
    separated), type, name, offset in the described data, size, shape (arrays) and the value(s) in the body's data copy
    (`Fixed` as float, `Integer` / `Array` elements as int, `Char` / `CArray` as bytes values, `Import` as raw bytes)"""
    res = []
    data = body['data']
    pos = 0
    for record in body['records']:
        name = record['name']
        full = f'{path}/{name}' if path else name
        size = record['data_size']
        extra = record['extra']['data']
        if record['type'] == 'Chain' and isinstance(extra, dict) and 'records' in extra:
            res.append({'path': full, 'type': 'Chain', 'name': name, 'offset': offset + pos, 'size': size})
            res += des_fields(extra, offset + pos, full)
        else:
            raw = data[pos : pos + size]
            entry = {'path': full, 'type': record['type'], 'name': name, 'offset': offset + pos, 'size': size}
            if isinstance(extra, dict) and 'size_2' in extra:
                entry['shape'] = [extra['dimensions'], extra['size_1'], extra['size_2']]
            entry['value'] = des_value(record['type'], raw)
            res.append(entry)
        pos += size
    return res


def des_value(des_type: str, raw: bytes):
    """Value of a field as its `.DES` type reads it"""
    if des_type == 'Fixed' and len(raw) == 4:
        return int.from_bytes(raw, 'little', signed=True) / 0x10000
    if des_type == 'Integer' and len(raw) == 4:
        return int.from_bytes(raw, 'little', signed=True)
    if des_type == 'Array' and len(raw) % 4 == 0:
        return [int.from_bytes(raw[i : i + 4], 'little', signed=True) for i in range(0, len(raw), 4)]
    if des_type in ('Char', 'CArray'):
        return list(raw) if len(raw) != 1 else raw[0]
    return list(raw)


# the data files of NFS2 / NFS2 SE that `.DES` files describe: (described data size, file name test, block)
def _described_blocks():
    from resources.eac.car_specs import (
        Nfs2CarAi,
        Nfs2CarPhysics,
        Nfs2Personalities,
        Nfs2SimTune,
        Nfs2TrafficConfig,
    )

    return [
        (356, lambda name: name.startswith('P'), Nfs2CarPhysics),
        (232, lambda name: name.startswith('SIMTUNE'), Nfs2SimTune),
        (524, lambda name: True, Nfs2CarAi),
        (452, lambda name: name.startswith('TRAFCFG'), Nfs2TrafficConfig),
        (3012, lambda name: name.startswith('PRSONAL'), Nfs2Personalities),
    ]


def described_block(data_size: int, file_name: str):
    """The TailsLab block of the data file a `.DES` describes (by the described data size and the file name), None for
    a data file not parsed"""
    name = file_name.replace('\\', '/').rsplit('/', 1)[-1].upper()
    for size, name_test, block_class in _described_blocks():
        if size == data_size and name_test(name):
            return block_class()
    return None


def block_layout(block, data=None, offset: int = 0, path: str = '') -> List[dict]:
    """Leaves of a fixed-size block in file order: path (`a.b[1].c`), offset, size, kind (`fixed` = 16.16, `int`,
    `text`, `bytes`, or the element kind for `array`), element size, description. Arrays of compound blocks are expanded
    element by element"""
    from library.read_blocks import DataBlock, FixedPointBlock

    if data is None:
        data = block.new_data()
    res = []
    if isinstance(block, CompoundBlock):
        for name, field in block.field_blocks:
            usage = block.field_extras_map.get(name, {}).get('usage', 'everywhere')
            if usage != 'everywhere' and 'io' not in usage:
                continue
            sub = block_layout(field, data.get(name), offset, f'{path}.{name}' if path else name)
            if len(sub) == 1 and not isinstance(field, CompoundBlock):
                sub[0]['description'] = block.field_extras_map.get(name, {}).get('description', '')
            res += sub
            offset += field.estimate_packed_size(data.get(name))
        return res
    if isinstance(block, ArrayBlock):
        if isinstance(block.child, CompoundBlock):
            for i, item in enumerate(data):
                res += block_layout(block.child, item, offset, f'{path}[{i}]')
                offset += block.child.estimate_packed_size(item)
            return res
        element = block_layout(block.child, data[0] if data else None, offset, path)[0]
        size = block.estimate_packed_size(data)
        return [
            {
                'path': path,
                'offset': offset,
                'size': size,
                'kind': 'array',
                'element_kind': element['kind'],
                'element_size': element['size'],
            }
        ]
    size = block.estimate_packed_size(data) if isinstance(block, DataBlock) else 0
    if isinstance(block, FixedPointBlock):
        kind = 'fixed' if block.fraction_bits == 16 else f'fixed{block.fraction_bits}'
    elif isinstance(block, IntegerBlock):
        kind = 'int'
    elif isinstance(block, UTF8Block):
        size = block._get_static_length() or size
        kind = 'text'
    else:
        kind = 'bytes'
    return [{'path': path, 'offset': offset, 'size': size, 'kind': kind, 'element_size': 1 if kind == 'text' else size}]


def _des_type_fits(des_type: str, leaf: dict, size: int) -> bool:
    kind = leaf.get('element_kind', leaf['kind'])
    element_size = leaf.get('element_size', leaf['size'])
    if des_type == 'Fixed':
        return kind == 'fixed' and element_size == 4
    if des_type == 'Integer':
        return kind == 'int' and element_size == 4
    if des_type == 'Char':
        return element_size == 1 and size == 1
    if des_type == 'Array':
        return element_size == 4 and kind in ('fixed', 'int')
    if des_type == 'CArray':
        return element_size == 1
    return True


def des_check(fields: List[dict], layout: List[dict]) -> List[str]:
    """Differences between the fields of a `.DES` (`des_fields`) and the layout of the TailsLab block of the described
    data (`block_layout`): a field whose bytes are not one leaf, part of one leaf, or exactly a run of leaves, or
    whose type does not fit them. Empty when they agree"""
    problems = []
    for field in fields:
        if field['type'] == 'Chain':
            continue
        start, end = field['offset'], field['offset'] + field['size']
        leaves = [x for x in layout if x['offset'] < end and start < x['offset'] + x['size']]
        if not leaves:
            problems.append(f'{field["path"]}: no field at {start:#x}')
            continue
        inside = len(leaves) == 1 and leaves[0]['offset'] <= start and end <= leaves[0]['offset'] + leaves[0]['size']
        tiles = leaves[0]['offset'] == start and leaves[-1]['offset'] + leaves[-1]['size'] == end
        if not inside and not tiles:
            problems.append(f'{field["path"]}: {start:#x}..{end:#x} cuts {", ".join(x["path"] for x in leaves)}')
            continue
        for leaf in leaves:
            part = min(end, leaf['offset'] + leaf['size']) - max(start, leaf['offset'])
            if not _des_type_fits(field['type'], leaf, part if len(leaves) > 1 else field['size']):
                problems.append(f'{field["path"]}: {field["type"]} does not fit {leaf["path"]} ({leaf["kind"]})')
    return problems
