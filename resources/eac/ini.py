"""
Typed INI text files: a generic block family for EA's `.ini` data files whose keys a game reads one by one.

A file block (`IniFile` subclass) declares its sections (`IniSection`), groups of numbered sections (`IniSectionGroup`,
e.g. `[skin00]`..`[skin19]`) and the typed keys of each (`IniInt`, `IniFloat`, `IniString`, arrays of numbered keys
`IniArray`). The block reads and writes the text itself: the values become fields, keys the definition lacks go to the
section's `other_keys`, sections it lacks to `other_sections`; `source_text` keeps the file as read, and writing puts
the values over it (a changed number in the style of the one it replaces, a new key after the section's last key, a
new section at the end), so comments, blank lines, line endings and key spelling stay and an unchanged file writes
back byte for byte.

Values: integers are read as `sscanf("%d")` (blanks, a sign, digits; `1.00` reads 1), floats as `sscanf("%f")`
(`.5`, `5.`, exponents; the rest of the value ignored), a value without a number counts as a missing key; texts are
everything after `=` and the blanks after it up to the end of the line. A missing key is None.

Which line holds the value the game reads follows the INI parser of the game (`IniFile.ini_parser`). NFS Hot Pursuit 2
PC (`NFSHP2.exe`) uses EA's CINI classes (parser 0x5b5180, lookups 0x527460 / 0x527560 / 0x527650), see `parse_ini`.
"""

import math
import re
import struct
from copy import deepcopy
from typing import Dict, List, NamedTuple, Optional, Tuple

from library.read_blocks import (
    ArrayBlock,
    CompoundBlock,
    DataBlock,
    DecimalBlock,
    DeclarativeCompoundBlock,
    IntegerBlock,
    UTF8Block,
)

# ---------------------------------------------------------------------------------------------------------------------
# The game's parser
# ---------------------------------------------------------------------------------------------------------------------


def _is_blank(b: int) -> bool:
    """CINI's whitespace test: `c < '!'` on a signed char, so bytes 0x80..0xff count as whitespace too"""
    return b <= 0x20 or b >= 0x80


class IniKeyLine(NamedTuple):
    start: int  # line start (first byte of the line, before its indentation)
    end: int  # end of the line's text (before CR / LF)
    eol_end: int  # end of the line with its line break
    key: str
    value_start: int  # first byte of the value (after `=` and the blanks after it)


class IniKey:
    """A key as the game keeps it: one per spelling in a section (case-sensitive), the value of its last line"""

    def __init__(self, name: str):
        self.name = name
        self.lines: List[IniKeyLine] = []

    @property
    def line(self) -> IniKeyLine:
        return self.lines[-1]


class IniSectionText:
    def __init__(self, name: str, header_start: int, header_end: int, name_start: int, name_end: int):
        self.name = name
        self.header_start = header_start  # line start of the header
        self.header_end = header_end  # end of the header line with its line break
        self.name_start = name_start
        self.name_end = name_end
        self.end = header_end  # end of the section: start of the next header line or of the file
        self.keys: List[IniKey] = []
        self._by_name: Dict[str, IniKey] = {}

    def add(self, line: IniKeyLine):
        key = self._by_name.get(line.key)
        if key is None:
            key = self._by_name[line.key] = IniKey(line.key)
            self.keys.append(key)
        key.lines.append(line)

    def lookup(self, name: str) -> Optional[IniKey]:
        """The key a lookup finds: the first one whose name matches ignoring case (0x583280: tolower per character)"""
        lower = name.lower()
        return next((k for k in self.keys if k.name.lower() == lower), None)

    @property
    def last_line_end(self) -> int:
        """End (with its line break) of the section's last key line, or of its header"""
        ends = [line.eol_end for key in self.keys for line in key.lines]
        return max(ends) if ends else self.header_end


class IniText:
    def __init__(self, raw: bytes, sections: List[IniSectionText]):
        self.raw = raw
        self.sections = sections

    def section(self, name: str) -> Optional[IniSectionText]:
        """The section a lookup finds: the first one whose name matches ignoring case"""
        lower = name.lower()
        return next((s for s in self.sections if s.name.lower() == lower), None)


def _line_end(raw: bytes, pos: int) -> int:
    n = len(raw)
    while pos < n and raw[pos] not in (10, 13):
        pos += 1
    return pos


def _next_line(raw: bytes, pos: int) -> Optional[int]:
    """0x5b5490: past the end of the line, then past every blank byte (empty lines included); None at the end"""
    n = len(raw)
    pos = _line_end(raw, pos)
    while pos < n and _is_blank(raw[pos]):
        pos += 1
    return pos if pos < n else None


def _line_break_end(raw: bytes, end: int) -> int:
    """End of the line break at `end` (CRLF, LF or CR)"""
    if raw[end : end + 2] == b'\r\n':
        return end + 2
    if raw[end : end + 1] in (b'\r', b'\n'):
        return end + 1
    return end


def parse_ini(raw: bytes) -> IniText:
    """The sections and keys of an INI text as NFSHP2.exe's CINI parser (0x5b5180) makes them:
    - A section starts at a line whose first byte after blanks is `[` (the file's first line counts only when its
      very first byte is `[`); its name is the text between the line's first `[` and its first `]`, as it is
      (spaces kept). A header without `]` after the `[`, or with an empty name, is skipped together with the key lines
      that follow it. Every header makes a new section (flag 0), also a repeated one: lookups find the first.
    - The section's lines up to the next header line are keys when they contain `=`: the key is the text before the
      first `=` without the blanks around it, the value the text after it without the blanks before it (trailing
      blanks stay). Lines without `=` are skipped: there is no comment syntax, `' a=b` is a key named `' a`.
      Lines are cut after 1023 characters.
    - A key spelled exactly as an earlier one of the section replaces its value (flag 1, case-sensitive 0x453210);
      lookups compare names ignoring case and find the first key (by its first line)
    - Blanks are bytes up to 0x20 and from 0x80 (signed char compares)"""
    n = len(raw)
    sections = []
    pos = 0 if n else None
    first = True
    while pos is not None and pos < n:
        if raw[pos] != 0x5B:  # '['
            if first:
                first = False
                pos = _next_line(raw, pos)
                continue
            pos = _next_line(raw, pos)
            continue
        first = False
        header_start = pos
        end = _line_end(raw, pos)
        line = raw[pos : min(end, pos + 1023)]
        next_pos = _next_line(raw, pos)
        open_i = line.find(b'[')
        close_i = line.find(b']')
        if open_i < 0 or close_i <= open_i + 1:
            pos = next_pos
            continue
        section = IniSectionText(
            name=line[open_i + 1 : close_i].decode('latin-1'),
            header_start=_line_start(raw, header_start),
            header_end=_line_break_end(raw, end),
            name_start=pos + open_i + 1,
            name_end=pos + close_i,
        )
        sections.append(section)
        # the section's lines: up to a line starting with '[' (after blanks)
        q = next_pos
        while q is not None and q < n and raw[q] != 0x5B:
            line_end = _line_end(raw, q)
            text = raw[q : min(line_end, q + 1023)]
            eq = text.find(b'=')
            if eq >= 0:
                key_end = eq
                while key_end > 0 and _is_blank(text[key_end - 1]):
                    key_end -= 1
                v = eq + 1
                while v < len(text) and text[v] != 0 and _is_blank(text[v]):
                    v += 1
                section.add(
                    IniKeyLine(
                        start=_line_start(raw, q),
                        end=line_end,
                        eol_end=_line_break_end(raw, line_end),
                        key=text[:key_end].decode('latin-1'),
                        value_start=q + v,
                    )
                )
            q = _next_line(raw, q)
        section.end = _line_start(raw, q) if q is not None else n
        pos = q
    return IniText(raw, sections)


def _line_start(raw: bytes, pos: int) -> int:
    """Start of the line holding `pos` (the blanks the parser skipped before it belong to the line)"""
    while pos > 0 and raw[pos - 1] not in (10, 13):
        pos -= 1
    return pos


# ---------------------------------------------------------------------------------------------------------------------
# Values
# ---------------------------------------------------------------------------------------------------------------------

# MSVC `sscanf("%d")` / `sscanf("%f")` (0x527560 / 0x527650): blanks, then a number; the rest of the value is ignored
_INT_RE = re.compile(rb'[ \t\n\v\f\r]*([+-]?\d+)')
_FLOAT_RE = re.compile(rb'[ \t\n\v\f\r]*([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)')


def _f32(value: float) -> float:
    return struct.unpack('<f', struct.pack('<f', value))[0] if math.isfinite(value) else value


def format_ini_float(value: float, old: str = None) -> str:
    """A float in the style of the number it replaces (its decimals; a whole number stays whole), else the shortest
    text the game reads as the same 32-bit float, with at least one decimal"""
    value = float(value)
    if old is not None:
        match = re.fullmatch(r'[+-]?\d*\.(\d*)', old)
        if match:
            decimals = len(match.group(1))
            for d in range(decimals, 13):
                text = f'{value:.{d}f}'
                if _f32(float(text)) == _f32(value):
                    return text
        if re.fullmatch(r'[+-]?\d+', old) and value.is_integer():
            return str(int(value))
    for d in range(1, 13):
        text = f'{value:.{d}f}'
        if _f32(float(text)) == _f32(value):
            return text
    return repr(value)


class _IniValue:
    """A typed value of an INI key. `key` is the name the game looks up (None: the field name), `default` what the
    game uses when the key is missing (None: nothing, or not read), `reader` the game's reader (for the docs)"""

    is_ini_value = True
    kind = 'string'

    def __init__(self, key: str = None, default=None, unit: str = None, **kwargs):
        super().__init__(**kwargs)
        self.key = key
        self.default = default
        self.unit = unit

    @property
    def size_doc_str(self):
        return '?'

    def _type_text(self, kind: str) -> str:
        return kind + (f', {self.unit}' if self.unit else '')

    def new_data(self, patch=None):
        return deepcopy(self.default)

    def read(self, ctx, name: str = '', read_bytes_amount=None):
        raise NotImplementedError('INI values are read by their IniFile')

    def write(self, data, ctx=None, name: str = '') -> bytes:
        raise NotImplementedError('INI values are written by their IniFile')

    def estimate_packed_size(self, data, ctx=None):
        raise NotImplementedError('INI values are written by their IniFile')

    def parse(self, text: str):
        """The value the game gets from the value text, None when its reader fails (the key counts as missing)"""
        raise NotImplementedError

    def number_span(self, text: str) -> Optional[Tuple[int, int]]:
        """Where the number the game reads is in the value text (the rest of the value is kept when it changes)"""
        return None

    def format(self, value, old: str = None) -> str:
        raise NotImplementedError

    def same(self, a, b) -> bool:
        return a == b

    def _schema_extra(self) -> Dict:
        res = {'ini_key': self.key, 'ini_kind': self.kind}
        if self.default is not None:
            res['ini_default'] = self.default
        if self.unit:
            res['ini_unit'] = self.unit
        return res


class IniInt(_IniValue, IntegerBlock):
    """An integer value, read with `sscanf("%d")`"""

    kind = 'int'

    def __init__(self, key: str = None, default=None, unit: str = None, **kwargs):
        super().__init__(key=key, default=default, unit=unit, length=4, is_signed=True, **kwargs)

    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            **self._schema_extra(),
            'block_description': self._type_text('Integer (`%d`)'),
        }

    def parse(self, text: str):
        match = _INT_RE.match(text.encode('latin-1'))
        if not match:
            return None
        value = int(match.group(1)) & 0xFFFFFFFF
        return value - (1 << 32) if value >= 1 << 31 else value

    def number_span(self, text: str):
        match = _INT_RE.match(text.encode('latin-1'))
        return match.span(1) if match else None

    def format(self, value, old: str = None) -> str:
        return str(int(round(value)))

    def same(self, a, b) -> bool:
        if a is None or b is None:
            return a is b
        return float(a) == float(b) and float(b).is_integer()


class IniFloat(_IniValue, DecimalBlock):
    """A decimal value, read with `sscanf("%f")` into a 32-bit float"""

    kind = 'float'

    def __init__(self, key: str = None, default=None, unit: str = None, **kwargs):
        super().__init__(key=key, default=default, unit=unit, length=4, **kwargs)

    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            **self._schema_extra(),
            'block_description': self._type_text('Float (`%f`)'),
        }

    def parse(self, text: str):
        match = _FLOAT_RE.match(text.encode('latin-1'))
        return float(match.group(1)) if match else None

    def number_span(self, text: str):
        match = _FLOAT_RE.match(text.encode('latin-1'))
        return match.span(1) if match else None

    def format(self, value, old: str = None) -> str:
        return format_ini_float(value, old)

    def same(self, a, b) -> bool:
        if a is None or b is None:
            return a is b
        return float(a) == float(b)


class IniString(_IniValue, UTF8Block):
    """A text value: what follows `=` and the blanks after it, up to the end of the line (trailing blanks included).
    `max_length` = the game's buffer: it keeps the first max_length - 1 characters"""

    kind = 'string'

    def __init__(self, key: str = None, default=None, unit: str = None, max_length: int = None, **kwargs):
        super().__init__(key=key, default=default, unit=unit, length=0, **kwargs)
        self.max_length = max_length

    @property
    def schema(self) -> Dict:
        descr = 'Text'
        if self.max_length:
            descr += f' (up to {self.max_length - 1} characters kept)'
        return {**super().schema, **self._schema_extra(), 'block_description': descr}

    def new_data(self, patch=None):
        return deepcopy(self.default)

    def parse(self, text: str):
        return text

    def format(self, value, old: str = None) -> str:
        return str(value)


class IniArray(ArrayBlock):
    """Values of numbered keys (`key_format` % index, e.g. `torqueCurve_%d`), item i = key i; a missing key is None"""

    is_ini_value = True

    def __init__(self, child: _IniValue, length: int, key_format: str, first_index: int = 0, **kwargs):
        super().__init__(child=child, length=length, **kwargs)
        self.key_format = key_format
        self.first_index = first_index

    def item_key(self, i: int) -> str:
        return self.key_format % (i + self.first_index)

    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'ini_key': self.key_format,
            'first_index': self.first_index,
            'block_description': f'{self._length} keys `{self.key_format}` (from {self.first_index}), one value each',
        }

    @property
    def size_doc_str(self):
        return '?'

    def new_data(self, patch=None):
        return [self.child.new_data() for _ in range(self._length)]

    def read(self, ctx, name: str = '', read_bytes_amount=None):
        raise NotImplementedError('INI values are read by their IniFile')

    def write(self, data, ctx=None, name: str = '') -> bytes:
        raise NotImplementedError('INI values are written by their IniFile')

    def estimate_packed_size(self, data, ctx=None):
        raise NotImplementedError('INI values are written by their IniFile')


# ---------------------------------------------------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------------------------------------------------


class _IniStructure:
    @property
    def size_doc_str(self):
        return '?'

    def read(self, ctx, name: str = '', read_bytes_amount=None):
        raise NotImplementedError('INI sections are read by their IniFile')

    def write(self, data, ctx=None, name: str = '') -> bytes:
        raise NotImplementedError('INI sections are written by their IniFile')

    def estimate_packed_size(self, data, ctx=None):
        raise NotImplementedError('INI sections are written by their IniFile')


class IniKeyValue(_IniStructure, DeclarativeCompoundBlock):
    """A key the definition does not name, with its value text"""

    class Fields(DeclarativeCompoundBlock.Fields):
        key = (IniString(), {'description': 'Key name, as spelled in the file'})
        value = (IniString(), {'description': 'Value text, as the game keeps it'})

    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'A key line `key=value`', 'inline_description': True}

    def new_data(self, patch=None):
        return {'key': '', 'value': ''}


def _other_keys_field(description: str = None):
    return (
        ArrayBlock(child=IniKeyValue(), length=None),
        {
            'description': description
            or 'Keys of the section the definition does not name (the game reads none of them), in file order',
        },
    )


class IniSection(_IniStructure, CompoundBlock):
    """A section: typed keys (fields) and `other_keys`. `section` = the name the game looks up"""

    def __init__(self, section: str, fields: list, description: str = '', **kwargs):
        self.section = section
        self.section_description = description
        all_fields = list(fields) + [('other_keys', *_other_keys_field())]
        super().__init__(fields=all_fields, **kwargs)

    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'ini_section': self.section,
            'block_description': self.section_description or f'Section `[{self.section}]`',
        }

    def value_fields(self):
        return [(n, b) for n, b in self.field_blocks if n not in ('other_keys', 'section')]

    def new_data(self, patch=None):
        res = {name: block.new_data() for name, block in self.field_blocks}
        res['other_keys'] = []
        return res


class IniGroupSection(IniSection):
    """A section of an `IniSectionGroup`: its name is the `section` field"""

    def __init__(self, fields: list, name_description: str, description: str = '', **kwargs):
        super().__init__(
            section=None,
            fields=[('section', IniString(), {'description': name_description})] + list(fields),
            description=description,
            **kwargs,
        )


class IniSectionGroup(_IniStructure, ArrayBlock):
    """Sections whose name matches `name_pattern` (a regex, ignoring case), in file order; `new_name(i)` names an item
    added at index i. A repeated name after the first is not part of the group (the game finds the first)"""

    def __init__(self, child: IniGroupSection, name_pattern: str, new_name=None, description: str = '', **kwargs):
        super().__init__(child=child, length=None, **kwargs)
        self.name_pattern = re.compile(name_pattern, re.IGNORECASE)
        self.new_name = new_name
        self.group_description = description

    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'ini_section_pattern': self.name_pattern.pattern,
            'block_description': self.group_description or f'Sections named `{self.name_pattern.pattern}`',
        }

    def matches(self, name: str) -> bool:
        return bool(self.name_pattern.fullmatch(name))

    def new_data(self, patch=None):
        return []


class IniOtherSection(_IniStructure, DeclarativeCompoundBlock):
    class Fields(DeclarativeCompoundBlock.Fields):
        section = (IniString(), {'description': 'Section name (between the brackets)'})
        keys = (ArrayBlock(child=IniKeyValue(), length=None), {'description': 'Its keys, in file order'})

    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A section the definition does not name (or a repeated one: the game reads the '
            'first), with its keys',
        }

    def new_data(self, patch=None):
        return {'section': '', 'keys': []}


# ---------------------------------------------------------------------------------------------------------------------
# Files
# ---------------------------------------------------------------------------------------------------------------------


class _Edits:
    """Byte edits over the source text, applied at once"""

    def __init__(self, raw: bytes):
        self.raw = raw
        self.items = []  # (start, end, bytes, order)
        self.order = 0

    def replace(self, start: int, end: int, data: bytes):
        self.items.append((start, end, data, self.order))
        self.order += 1

    def insert(self, pos: int, data: bytes):
        self.replace(pos, pos, data)

    def apply(self) -> bytes:
        out = bytearray()
        pos = 0
        for start, end, data, _ in sorted(self.items, key=lambda e: (e[0], e[1] > e[0], e[3])):
            if start < pos:
                start = pos  # overlapping deletes (a removed section with removed keys)
            out += self.raw[pos:start]
            out += data
            pos = max(pos, end)
        out += self.raw[pos:]
        return bytes(out)


class IniFile(DeclarativeCompoundBlock):
    """Base of typed INI files: subclasses set `Fields = ini_fields_class([...])` with `IniSection` and
    `IniSectionGroup` fields. Reads and writes the whole remaining buffer as Latin-1 text"""

    class Fields(DeclarativeCompoundBlock.Fields):
        pass

    # key lines starting with these are comments for people: the parser makes them keys (`' 0=LOWEST` is the key
    # `' 0`) that no lookup can find, so they stay in the text and out of `other_keys`
    comment_prefixes = ("'", '//', '#', ';')

    def _is_comment_key(self, key: IniKey) -> bool:
        return key.name.startswith(self.comment_prefixes)

    @property
    def size_doc_str(self):
        return '?'

    def serializer_class(self):
        from serializers import IniFileSerializer

        return IniFileSerializer

    def sections_and_groups(self):
        return [
            (name, block)
            for name, block in self.field_blocks
            if isinstance(block, (IniSection, IniSectionGroup)) and name != 'other_sections'
        ]

    def new_data(self, patch=None):
        res = {}
        for name, block in self.field_blocks:
            res[name] = '' if name == 'source_text' else block.new_data()
        return res

    # reading

    @staticmethod
    def _read_value(block: _IniValue, section: Optional[IniSectionText], key: str, raw: bytes):
        found = section.lookup(key) if section is not None else None
        if found is None:
            return None, None
        line = found.line
        text = raw[line.value_start : line.end].decode('latin-1')
        return block.parse(text), found

    def _read_section(self, block: IniSection, section: Optional[IniSectionText], raw: bytes) -> dict:
        res = {}
        used = set()
        for name, value_block in block.value_fields():
            if isinstance(value_block, IniArray):
                values = []
                for i in range(value_block._length):
                    value, found = self._read_value(value_block.child, section, value_block.item_key(i), raw)
                    values.append(value)
                    if found is not None:
                        used.add(id(found))
                res[name] = values
            else:
                value, found = self._read_value(value_block, section, value_block.key or name, raw)
                res[name] = value
                if found is not None:
                    used.add(id(found))
        others = []
        if section is not None:
            for key in section.keys:
                if id(key) not in used and not self._is_comment_key(key):
                    line = key.line
                    others.append({'key': key.name, 'value': raw[line.value_start : line.end].decode('latin-1')})
        res['other_keys'] = others
        return res

    def _assign_sections(self, text: IniText):
        """{field: section text or [section texts]}, and the other sections, as the read sees them"""
        assigned = {}
        taken = set()
        for name, block in self.sections_and_groups():
            if isinstance(block, IniSection):
                section = text.section(block.section)
                assigned[name] = section
                if section is not None:
                    taken.add(id(section))
        seen_names = set()
        first_by_name = {}
        for section in text.sections:
            first_by_name.setdefault(section.name.lower(), section)
        for name, block in self.sections_and_groups():
            if isinstance(block, IniSectionGroup):
                items = []
                for section in text.sections:
                    lower = section.name.lower()
                    if (
                        id(section) not in taken
                        and block.matches(section.name)
                        and first_by_name[lower] is section
                        and lower not in seen_names
                    ):
                        items.append(section)
                        taken.add(id(section))
                        seen_names.add(lower)
                assigned[name] = items
        others = [s for s in text.sections if id(s) not in taken]
        return assigned, others

    def parse_text(self, raw: bytes) -> dict:
        text = parse_ini(raw)
        assigned, others = self._assign_sections(text)
        res = {}
        for name, block in self.field_blocks:
            if name in assigned:
                if isinstance(block, IniSectionGroup):
                    items = []
                    for section in assigned[name]:
                        item = self._read_section(block.child, section, raw)
                        item['section'] = section.name
                        items.append(item)
                    res[name] = items
                else:
                    res[name] = self._read_section(block, assigned[name], raw)
        res['other_sections'] = [
            {
                'section': s.name,
                'keys': [
                    {'key': k.name, 'value': raw[k.line.value_start : k.line.end].decode('latin-1')}
                    for k in s.keys
                    if not self._is_comment_key(k)
                ],
            }
            for s in others
        ]
        res['source_text'] = raw.decode('latin-1')
        return res

    def read(self, ctx, name: str = '', read_bytes_amount=None):
        res = {}
        self_ctx = ctx.get_or_create_child(name, self, read_bytes_amount, res)
        remaining = self_ctx.read_bytes_remaining
        raw = ctx.buffer.read() if remaining is None else ctx.buffer.read(remaining)
        res.update(self.parse_text(raw))
        return res

    # writing

    @staticmethod
    def _eol(raw: bytes) -> bytes:
        if b'\r\n' in raw or not raw:
            return b'\r\n'
        return b'\n' if b'\n' in raw else b'\r'

    @staticmethod
    def _encode(text: str) -> bytes:
        return str(text).encode('latin-1', errors='replace')

    def _key_lines(self, block: IniSection, data: dict) -> List[Tuple[str, str]]:
        """(key, value text) of the section's values that are set, in definition order"""
        lines = []
        for name, value_block in block.value_fields():
            value = data.get(name)
            if isinstance(value_block, IniArray):
                for i, item in enumerate(value or []):
                    if item is not None and i < value_block._length:
                        lines.append((value_block.item_key(i), value_block.child.format(item)))
            elif value is not None:
                lines.append((value_block.key or name, value_block.format(value)))
        for other in data.get('other_keys') or []:
            if other.get('key') is not None:
                lines.append((other['key'], other.get('value') or ''))
        return lines

    def _new_section_text(self, section_name: str, lines: List[Tuple[str, str]], eol: bytes) -> bytes:
        out = self._encode(f'[{section_name}]') + eol
        for key, value in lines:
            out += self._encode(f'{key}={value}') + eol
        return out

    def _edit_value(self, edits: _Edits, raw: bytes, key: IniKey, block: _IniValue, value):
        line = key.line
        text = raw[line.value_start : line.end].decode('latin-1')
        old = block.parse(text)
        if block.same(old, value):
            return
        if value is None:
            edits.replace(line.start, line.eol_end, b'')
            return
        span = block.number_span(text)
        if span is not None:
            start, end = span
            new_text = text[:start] + block.format(value, text[start:end]) + text[end:]
        else:
            new_text = block.format(value)
        edits.replace(line.value_start, line.end, self._encode(new_text))

    def _edit_section(self, edits: _Edits, raw: bytes, eol: bytes, block: IniSection, section, data: dict):
        """Puts the section's values over its text. A key the text lacks goes after the line of the definition's
        previous key the text has (else after the section's last key line), other keys after the last one"""
        used = set()
        anchor = [None]  # end of the line of the last key found, in definition order

        def add(key_name: str, value_text: str):
            pos = anchor[0] if anchor[0] is not None else section.last_line_end
            prefix = eol if pos == len(raw) and raw and raw[-1:] not in (b'\r', b'\n') else b''
            edits.insert(pos, prefix + self._encode(f'{key_name}={value_text}') + eol)

        def edit(key_name: str, value_block: _IniValue, value):
            found = section.lookup(key_name)
            if found is not None:
                used.add(id(found))
                anchor[0] = found.line.eol_end
                self._edit_value(edits, raw, found, value_block, value)
            elif value is not None:
                add(key_name, value_block.format(value))

        for name, value_block in block.value_fields():
            value = data.get(name)
            if isinstance(value_block, IniArray):
                values = list(value or [])
                for i in range(value_block._length):
                    edit(value_block.item_key(i), value_block.child, values[i] if i < len(values) else None)
            else:
                edit(value_block.key or name, value_block, value)
        existing = [k for k in section.keys if id(k) not in used and not self._is_comment_key(k)]
        others = list(data.get('other_keys') or [])
        for i, key in enumerate(existing):
            if i < len(others):
                other = others[i]
                line = key.line
                if other.get('key') != key.name:
                    for old_line in key.lines:
                        if old_line is not line:
                            edits.replace(old_line.start, old_line.eol_end, b'')
                    line_break = raw[line.end : line.eol_end] or eol
                    edits.replace(
                        line.start,
                        line.eol_end,
                        self._encode(f'{other.get("key")}={other.get("value") or ""}') + line_break,
                    )
                elif raw[line.value_start : line.end].decode('latin-1') != (other.get('value') or ''):
                    edits.replace(line.value_start, line.end, self._encode(other.get('value') or ''))
            else:
                for line in key.lines:
                    edits.replace(line.start, line.eol_end, b'')
        anchor[0] = None
        for other in others[len(existing) :]:
            add(other.get('key') or '', other.get('value') or '')

    def _rename_section(self, edits: _Edits, section: IniSectionText, name: str):
        if name is not None and name != section.name:
            edits.replace(section.name_start, section.name_end, self._encode(name))

    def _render(self, data: dict) -> Tuple[bytes, Dict[str, int]]:
        raw = (data.get('source_text') or '').encode('latin-1')
        text = parse_ini(raw)
        eol = self._eol(raw)
        assigned, others = self._assign_sections(text)
        edits = _Edits(raw)
        appended = []  # (field name, bytes)
        for name, block in self.sections_and_groups():
            if isinstance(block, IniSection):
                section = assigned.get(name)
                section_data = data.get(name) or {}
                if section is not None:
                    self._edit_section(edits, raw, eol, block, section, section_data)
                else:
                    lines = self._key_lines(block, section_data)
                    if lines:
                        appended.append((name, self._new_section_text(block.section, lines, eol)))
            else:
                sections = assigned.get(name) or []
                items = list(data.get(name) or [])
                for i, section in enumerate(sections):
                    if i < len(items):
                        self._rename_section(edits, section, items[i].get('section'))
                        self._edit_section(edits, raw, eol, block.child, section, items[i])
                    else:
                        edits.replace(section.header_start, section.end, b'')
                for i, item in enumerate(items[len(sections) :], start=len(sections)):
                    section_name = item.get('section') or (block.new_name(i) if block.new_name else f'section{i}')
                    appended.append(
                        (name, self._new_section_text(section_name, self._key_lines(block.child, item), eol))
                    )
        other_items = list(data.get('other_sections') or [])
        for i, section in enumerate(others):
            if i < len(other_items):
                item = other_items[i]
                self._rename_section(edits, section, item.get('section'))
                self._edit_section(
                    edits,
                    raw,
                    eol,
                    IniSection(section=section.name, fields=[]),
                    section,
                    {'other_keys': item.get('keys') or []},
                )
            else:
                edits.replace(section.header_start, section.end, b'')
        for item in other_items[len(others) :]:
            lines = [(k.get('key') or '', k.get('value') or '') for k in item.get('keys') or []]
            appended.append(('other_sections', self._new_section_text(item.get('section') or '', lines, eol)))
        out = edits.apply()
        offsets = {
            name: section.header_start for name, section in assigned.items() if isinstance(section, IniSectionText)
        }
        if appended:
            if out and out[-1:] not in (b'\r', b'\n'):
                out += eol
            for name, section_bytes in appended:
                offsets.setdefault(name, len(out) + (len(eol) if out else 0))
                out += (eol if out else b'') + section_bytes
        return out, offsets

    def write(self, data, ctx=None, name: str = '') -> bytes:
        return self._render(data)[0]

    def estimate_packed_size(self, data, ctx=None):
        return len(self._render(data)[0])

    def offset_to_child_when_packed(self, data, child_name: str, ctx=None):
        return self._render(data)[1].get(child_name, 0)


def ini_fields_class(sections: list, other_sections_description: str = None):
    """`Fields` of an IniFile from (name, IniSection | IniSectionGroup, extras) tuples, plus `other_sections` and the
    hidden `source_text`"""
    fields = {name: (block, extras) for name, block, extras in sections}
    fields['other_sections'] = (
        ArrayBlock(child=IniOtherSection(), length=None),
        {
            'description': other_sections_description
            or 'Sections the definition does not name, and repeated sections after the first (lookups find the '
            'first), in file order. The game reads none of them',
        },
    )
    fields['source_text'] = (
        UTF8Block(length=0),
        {
            'description': 'The file as read (bytes as Latin-1 characters). Writing puts the values over it: '
            'comments, blank lines, line endings, key spelling and lines the game skips stay, a changed number is '
            'written in the style of the one it replaces',
            'usage': 'io',
        },
    )
    return type('Fields', (DeclarativeCompoundBlock.Fields,), fields)


def ini_value_from_json(block: DataBlock, value):
    """A JSON value as the block's data (numbers of integer fields as ints)"""
    if value is None:
        return None
    if isinstance(block, IniArray):
        return [ini_value_from_json(block.child, v) for v in value]
    if isinstance(block, IniInt):
        return int(round(value))
    if isinstance(block, IniFloat):
        return float(value)
    return value


def ini_data_from_json(block: IniFile, json_data: dict, current: dict = None) -> dict:
    """The data of an IniFile with the values of its JSON export (`IniFileSerializer`): over `current` (the file being
    replaced: its layout stays) or a new file"""
    res = deepcopy(current) if current is not None else block.new_data()

    def section_data(section_block: IniSection, json_section: dict, base: dict) -> dict:
        out = dict(base or section_block.new_data())
        for name, value_block in section_block.field_blocks:
            if name in json_section:
                if name == 'other_keys':
                    out[name] = [{'key': k.get('key', ''), 'value': k.get('value', '')} for k in json_section[name]]
                else:
                    out[name] = ini_value_from_json(value_block, json_section[name])
        return out

    for name, field_block in block.sections_and_groups():
        if name not in json_data:
            continue
        if isinstance(field_block, IniSectionGroup):
            old = res.get(name) or []
            res[name] = [
                section_data(field_block.child, item, old[i] if i < len(old) else None)
                for i, item in enumerate(json_data[name])
            ]
        else:
            res[name] = section_data(field_block, json_data[name] or {}, res.get(name))
    if 'other_sections' in json_data:
        res['other_sections'] = [
            {
                'section': s.get('section', ''),
                'keys': [{'key': k.get('key', ''), 'value': k.get('value', '')} for k in s.get('keys') or []],
            }
            for s in json_data['other_sections']
        ]
    return res
