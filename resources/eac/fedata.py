# NFS3 / NFS4 car showroom data: `fedata.<lang>` (eng, fre, ger, ita, spa, swe, bri) in a car's `car.viv`. A binary
# header the front end keeps in its car list, then the spec sheet texts. Read by nfs3.exe 0x439d90 and nfs4.exe
# 0x473d20 (nfs-web `decomp/nfs3/nfs3.exe.gzf`, `decomp/nfs4/nfs4.exe.gzf`, names `FeCars_*`); the readers of each field
# were found in a linear disassembly of the whole executable (nfs-web `decomp/<game>/port-work/car-specs/`).
from typing import Dict

from library.context import ReadContext, WriteContext
from library.exceptions import EndOfBufferException
from library.read_blocks import (
    ArrayBlock,
    BitFlagsBlock,
    BytesBlock,
    DeclarativeCompoundBlock,
    IntegerBlock,
    UTF8Block,
)
from resources.eac.car_specs import Latin1Block

# The spec sheet texts by index, as the front end draws them (nfs3.exe 0x453940 spec sheet, 0x453f60 history, 0x4397c0
# colours, 0x454780 / 0x455660 / 0x4556c0 names; nfs4.exe 0x4a1c94..0x4a1eac spec sheet, 0x4731e5 colours, getter
# 0x473580): (name, label in the front end's TEXT.ENG, section). NFS4 adds `special` after the tyres.
_SPEC_NAMES = [
    ('make', 'Make (nfs3.exe 0x455660)', 'Names'),
    ('model', 'Model (nfs3.exe 0x4556c0)', 'Names'),
    ('full_name', 'Full name: the car list name (record +0x10, 0x439250), the showroom (nfs3.exe 0x454780)', 'Names'),
    ('price', 'Price', 'General'),
    ('status', 'Status', 'General'),
    ('weight', 'Weight', 'General'),
    ('weight_distribution', 'Weight dist, f/r', 'General'),
    ('length', 'Length', 'General'),
    ('width', 'Width', 'General'),
    ('height', 'Height', 'General'),
    ('engine_type', 'Engine type', 'Mechanical'),
    ('displacement', 'Displacement', 'Mechanical'),
    ('horsepower', 'Horsepower', 'Mechanical'),
    ('torque', 'Torque', 'Mechanical'),
    ('max_engine_speed', 'Max. engine speed', 'Mechanical'),
    ('brakes', 'Brakes, f/r', 'Mechanical'),
    ('tires', 'Tires, f/r', 'Mechanical'),
]
_SPEC_TAIL = [
    ('top_speed', 'Top speed', 'Performance'),
    ('accel_0_60', '0-60 mph', 'Performance'),
    ('accel_0_100', '0-100 mph', 'Performance'),
    ('transmission_type', 'Transmission: Type', 'Transmission'),
    ('gearbox', 'Transmission: Gearbox', 'Transmission'),
    ('history_title', 'History title (the make, over the history page)', 'History'),
    *[(f'history_{i + 1}', f'History line {i + 1}', 'History') for i in range(7)],
    *[(f'color_{i + 1}', f'Name of paint colour {i + 1} (colour picker)', 'Colours') for i in range(10)],
]
NFS3_FEDATA_TEXTS = _SPEC_NAMES + _SPEC_TAIL
NFS4_FEDATA_TEXTS = (
    _SPEC_NAMES + [('special', 'Special (e.g. "DSC (Dynamic Stability Control)")', 'Mechanical')] + _SPEC_TAIL
)


class FeDataText(UTF8Block):
    """One text of a fedata text table, Latin-1 (`El Niño`, `Weiß`); its bytes are written by `FeDataTextTable`"""

    def __init__(self, **kwargs):
        super().__init__(length=0, **kwargs)

    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'Latin-1 text, null-terminated in the file'}

    @property
    def size_doc_str(self):
        return 'len + 1'


def fedata_text_offsets(texts, start: int):
    """Offsets of the texts as every shipped file lays them out from `start` (the end of the offset table): each text in
    order with its terminating zero; an empty text points at the zero ending the text before it (start - 1 for the
    first: the last offset's high byte)"""
    offsets = []
    cursor = start
    for text in texts:
        if text:
            offsets.append(cursor)
            cursor += len(text.encode('latin-1')) + 1
        else:
            offsets.append(cursor - 1)
    return offsets


class FeDataTextTable(ArrayBlock):
    """The text table ending a fedata file: u16 count, count u32 offsets from the start of the file, then the
    null-terminated texts up to the end of the file"""

    def __init__(self, table_offset: int, text_names, **kwargs):
        super().__init__(child=FeDataText(), length=(0, 'count'), **kwargs)
        self.table_offset = table_offset
        self.text_names = text_names

    @property
    def schema(self) -> Dict:
        names = '<br/>'.join(
            f'{i}: `{name}` ({section}: {label})' for i, (name, label, section) in enumerate(self.text_names)
        )
        return {
            **super().schema,
            'block_description': f'Text table at 0x{self.table_offset:x}: u16 count, count u32 offsets (from the start '
            'of the file) and the null-terminated Latin-1 texts up to the end of the file. The game reads text i '
            'through the offset table (an index at or past the count gives an empty text). Every shipped file lays '
            'the texts out in order, and an empty text points at the zero ending the one before it (the first at the '
            "offset table's last byte): writing lays them out the same way. The texts:<br/>" + names,
            'text_names': [{'name': n, 'label': lbl, 'section': s} for n, lbl, s in self.text_names],
        }

    @property
    def size_doc_str(self):
        return '2 + 4 * count + texts'

    def new_data(self, patch=None):
        return [''] * len(self.text_names)

    def read(self, ctx: ReadContext, name: str = '', read_bytes_amount=None, resolved_length=None):
        res = []
        ctx.get_or_create_child(name, self, read_bytes_amount, res)
        head = ctx.buffer.read(2)
        if len(head) < 2:
            raise EndOfBufferException(ctx=ctx)
        count = int.from_bytes(head, 'little')
        table = ctx.buffer.read(4 * count)
        if len(table) < 4 * count:
            raise EndOfBufferException(ctx=ctx)
        rest = (
            ctx.buffer.read()
            if read_bytes_amount is None
            else ctx.buffer.read(max(read_bytes_amount - 2 - 4 * count, 0))
        )
        start = self.table_offset + 2 + 4 * count
        for i in range(count):
            offset = int.from_bytes(table[4 * i : 4 * i + 4], 'little')
            if offset >= start:
                raw = rest[offset - start :]
                end = raw.find(b'\0')
                res.append((raw if end < 0 else raw[:end]).decode('latin-1'))
            else:
                # before the texts: only the offset table's last byte (0) points at an empty text in the game's files
                res.append('')
        return res

    def write(self, data, ctx: WriteContext = None, name: str = '') -> bytes:
        texts = list(data or [])
        start = self.table_offset + 2 + 4 * len(texts)
        out = bytearray(len(texts).to_bytes(2, 'little'))
        for offset in fedata_text_offsets(texts, start):
            out += offset.to_bytes(4, 'little')
        for text in texts:
            if text:
                out += text.encode('latin-1') + b'\0'
        return bytes(out)

    def estimate_packed_size(self, data, ctx: WriteContext = None):
        texts = list(data or [])
        return 2 + 4 * len(texts) + sum(len(t.encode('latin-1')) + 1 for t in texts if t)

    def offset_to_child_when_packed(self, data, child_name: str, ctx: WriteContext = None):
        texts = list(data or [])
        index = int(child_name)
        start = self.table_offset + 2 + 4 * len(texts)
        return fedata_text_offsets(texts, start)[index] - self.table_offset


def _u8(**kwargs):
    return IntegerBlock(length=1, **kwargs)


def _s16(**kwargs):
    return IntegerBlock(length=2, is_signed=True, **kwargs)


def _u16(**kwargs):
    return IntegerBlock(length=2, **kwargs)


def _s32(**kwargs):
    return IntegerBlock(length=4, is_signed=True, **kwargs)


_CLASS_TEXT = (
    'Car class: 0 A, 1 B, 2 C, 255 none (Knockout). Kept at car list +0x388 (0x439730); the car lists of the menus '
    'filter by it (0x43a6e0, mask bits 0x10 / 0x20 / 0x40 drop classes 0 / 1 / 2; 0x438dc0 lists the class 255 cars), '
    'the race setup and the opponent picks read it (0x43a580, 0x43ace0, 0x454730, 0x461aa0). The physics reads '
    "carp.txt's `car_class` instead (by none)"
)


class Nfs3CarFeData(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'NFS3 car showroom data: `fedata.<lang>` (eng, fre, ger, ita, spa, swe, bri) in '
            "`GameData/CarModel/<car>/car.viv` and `FeData/Plac/CAR.VIV`; the language is the game's (0x4782b0). "
            "nfs3.exe 0x439d90 (FeCars_Load) reads it for every car folder into the front end's car list (0x3a4-byte "
            'records): a 0x2d-byte header converted field by field, then the text table, kept as it is (getter '
            '0x439ab0). A file whose `format_version` is not 9 drops the car from the list. All texts are Latin-1. '
            "The executable is VEG's Modern Patch build, whose car list loader has patched code (nops at 0x43a210..), "
            'the fields are read as retail',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        car_id = (
            Latin1Block(length=4),
            {
                'description': 'Car id, 4 characters (`Diab`, `AMD7`; the case varies), copied to car list +0x315 '
                '(0x439290). The car is found by its folder name, not by this'
            },
        )
        format_version = (
            _s16(),
            {
                'description': 'Format version, 9 in every file: 0x439d90 drops a car whose file holds another value. Its '
                'low byte is kept at car list +0x38e (not read)'
            },
        )
        bonus = (
            _s16(),
            {
                'description': 'Bonus car (1: Elni, Jxjr, Lcop, Merc, Peln): car list flag 1 (+0x380, 0x439680). Such a '
                'car is locked until its unlock bit is set (0x439c10: the unlock mask 0x6fd2a8 bits by serial number, 0x11 '
                'bit 4, 0x12 bit 2, 0x24 bit 8, 0x27 bit 1, 0x31 bit 0x10; locked cars are greyed out in the lists) and '
                'needs no carp.txt transfer in network races (0x439530)'
            },
        )
        filter_flag = (
            _s16(),
            {
                'description': 'Car list flag 2 (+0x380, 0x4395e0): 1 in every car with a spec sheet, 0 in Elni, Knoc, '
                'Peln, Plac. Read only by car list filters: 0x43a6e0 under mask bit 0x20000 (no caller passes it) and '
                '0x4390f0 (bits 33 / 34 of its 64-bit filter; its only caller 0x4391d0 has no caller): no effect'
            },
        )
        car_class = (_s16(), {'description': _CLASS_TEXT})
        game = (
            _s16(),
            {
                'description': "3 in every NFS3 file (NFS4's files hold 4 in their first field): its low 4 bits are kept "
                'at car list +0x384; their getter 0x439740 has no caller: not read'
            },
        )
        own_art = (
            _s16(),
            {
                'description': 'Car list flag 4 (+0x380, 0x4395c0), 0 in every file: the showcase art (`SH<car>.qfs`, '
                '`IN_<car>.fsh` interior, `SL<car>01.qfs` slides, `H<car>.qfs`; 0x4530c0..0x4535e0, 0x454000, 0x464eb0) is '
                "loaded from the car's own folder instead of `FeData/art/...` (an add-on car carries its art); such cars "
                'are left out of the lists asking for built-in cars (0x43a6e0 mask 0x40000)'
            },
        )
        police = (
            _s16(),
            {
                'description': 'Police car (1: Lcop, Peln, Vcop): car list flag 0x10 (+0x380, 0x4396b0): the pursuit car '
                'lists (0x438d60; 0x43a6e0 masks 0x4000 / 0x8000), cops in Hot Pursuit, speech names (0x426e20)'
            },
        )
        driver_seat = (
            _u8(),
            {
                'description': 'Driver seat (1: Amd7, Jxjr, Jxk8, the British cars): kept at car list +0x3a0 (0x439710) and '
                'by Car_LoadSpecs at car+0x9a8; the in-car camera (0x4240c0) puts the eye 0.4 m left of the centre for '
                '0, right for 1, in the middle for any other value'
            },
        )
        unused_0x13 = (_u8(), {'description': '0 in every file. Not read: the loader copies byte 0x12 alone'})
        shared_car = (
            _s16(),
            {
                'description': 'Car list flag 0x40 (+0x380, 0x439570), 1 in Amd7, Corv, Cout, Diab, Fm50, Jxk8, Scig, '
                'Sl60, Vcop, f355: a network race sends the carp.txt of a car without it and without `bonus` to the other '
                'players (0x49bab0 via 0x439530, 0x49b800); the car allowed check 0x43a4f0 reads it too'
            },
        )
        interior_view_heading = (
            _u16(),
            {
                'description': "Where the showroom's interior view (`IN_<car>.fsh`, a 1280 texel wide panorama) starts, "
                'in texels (360 degrees = 1280): kept at car list +0x38c (0x43bcc0, 128 for a missing car) and set as the '
                "view's horizontal scroll (0x465370 -> 0x55a43c, drawn by 0x464840). 128 for the cars without an "
                'interior'
            },
        )
        serial_number = (
            IntegerBlock(length=4),
            {
                'description': "The car's id in the game, the first part of a 16-byte car id (GUID) copied to car list "
                "+0x31c: the built-in cars have a serial number below 50 and zeros in the rest (0x439620; carp.txt's "
                '`serial_number`), an add-on car a GUID. The game finds cars by it (0x439990), indexes their unlock bits, '
                "the demo's cars (15, 16) and the network's car lists with it"
            },
        )
        guid_data2 = (_u16(), {'description': 'Bytes 4..5 of the car id GUID, 0 for the built-in cars (0x439620)'})
        guid_data3 = (_u16(), {'description': 'Bytes 6..7 of the car id GUID, 0 for the built-in cars (0x439620)'})
        guid_data4 = (
            ArrayBlock(child=_u8(), length=8),
            {'description': 'Bytes 8..15 of the car id GUID, 0 for the built-in cars (0x439620)'},
        )
        acceleration = (
            _u8(),
            {
                'description': "Acceleration rating, the showroom's and car select's bar (0..20; getter 0x438f60 index "
                '0, car list +0x38f)'
            },
        )
        top_speed = (_u8(), {'description': 'Top speed rating (0..20; 0x438f60 index 1, +0x390)'})
        handling = (_u8(), {'description': 'Handling rating (0..20; 0x438f60 index 2, +0x391)'})
        braking = (_u8(), {'description': 'Braking rating (0..20; 0x438f60 index 3, +0x392)'})
        overall_rating = (
            _u8(),
            {
                'description': '5 in every file, kept at car list +0x393; not read (the rating getter 0x438f60 takes '
                'indexes 0..3 only; NFS4 uses its fifth rating to pick opponents)'
            },
        )
        texts = (
            FeDataTextTable(table_offset=0x2D, text_names=NFS3_FEDATA_TEXTS),
            {'description': 'The spec sheet texts (40 in every file; text 2 also becomes the car list name)'},
        )

    def serializer_class(self):
        from serializers import CarFeDataSerializer

        return CarFeDataSerializer


_NFS4_FLAGS = [
    (0, 'bonus'),
    (1, 'filter_flag'),
    (2, 'saved_car'),
    (3, 'network_car'),
    (4, 'police'),
    (5, 'no_game_type_3'),
    (6, 'shared_car'),
    (7, 'no_engine_smoke'),
    (8, 'convertible'),
    (9, 'open_top'),
    (10, 'has_h_art'),
    (11, 'has_showcase_art'),
    (12, 'has_interior'),
    (13, 'has_slides'),
    (14, 'no_upgrades'),
    (15, 'fixed_color'),
]

_NFS4_FLAGS_TEXT = (
    "Car list flags (record +0x378; the network race sends them for the player's car, 0x4eb5d0, and puts the other "
    "player's over the `Data/plac.viv` car, 0x475b50). Bits: 0 `bonus` (B911, Bcam, Elni, PCam, PDia, Peln): locked "
    'until unlocked, greyed out in the lists (0x4737a0, 0x4747e0), and the special grip of Carp_TuneCar (0x4fcad0 '
    'via 0x472e30: car+0x4dc = 1, the wheel grip slider t -> (t + 1) x 0.5, 0x4ff6b0); 1 `filter_flag` (every car with '
    "a spec sheet; NFS3's fedata +0x08): the car list builder 0x4747e0 (0x472d70); 2 `saved_car` (in no file; NFS3's "
    "fedata +0x0e): the car's files and showcase art come from `SaveData\\Cars\\<folder>` instead of "
    '`Data\\Cars\\<folder>` (0x472690 via 0x472d40, 0x4a17f0); 3 `network_car` (Plac; set by 0x475b80 for the '
    "other player's car): its files also from `SaveData\\Cars` (0x472690), left out of the lists (0x472360); "
    '4 `police` (PBmw, PCam, PCor, PDia, PP91, Peln): pursuit lists (0x472250, '
    '0x472ea0), no colour choice (0x442290); 5 `no_game_type_3` (Knoc, MClk, MSlk, Plac): refused in game type 3 '
    "(0x474540, 0x4729a0); 6 `shared_car` (in no file; NFS3's fedata +0x14): read by the car allowed check 0x474540 "
    'and the network code (0x472cc0, 0x4eb903); 7 `no_engine_smoke` (Ff50, Fm50, Plac): no smoke / fire at the engine '
    "after a crash (0x44d7e0 via 0x472b90); 8 `convertible` (BZ3r, Bcam, CCor, Ccam, Jxkr, MSlk, Pfir): the showroom's "
    'CONVERTIBLE_OPT roof option (0x442290, 0x4b4e30) and car+0xad0 = 1 in a race (0x508d70); 9 `open_top` (Ff50): no '
    "roof option, the roof always off (0x7c4b4c = 1, car+0xad0 = 2); 10..13 set by the loader when the car's art "
    'exists (0x473cd0 `H<car>.qfs`, 0x473c20 `SH<car>.qfs`, 0x473b80 `IN_<car>.fsh` interior, 0x473c80 '
    '`SL<car>NN.qfs` slides; 0 in the files, never cleared); 14 `no_upgrades` (Elni, Knoc, MClk, Mcf1, the police cars, '
    'Plac): the car has no upgrade levels (0x472af0: the career shop and the opponent picks, 0x476ef0) and its '
    'ratings are not made rising level by level; 15 `fixed_color` (B911, Bcam): no colour choice (0x442290 via '
    '0x472e50, also 0x464a50, 0x4c2d70). Bits 16..31: 0 in every file, not read'
)


class Nfs4CarFeData(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'NFS4 car showroom data: `fedata.<lang>` (eng, fre, ger, ita, spa, swe, bri) in '
            "`Data/Cars/<car>/car.viv` and `Data/Plac.viv`; the language is the game's (0x4c7080). nfs4.exe 0x473d20 "
            "(FeCars_Load) reads it for every car folder: bytes 2..0x3bd are the front end's car list record as it "
            'is in memory (record = file + 2: the file offsets of the fields below minus 2), copied as they are '
            '(0xef dwords), then a few fields are set; the text table follows (getter 0x473580). A file whose '
            '`format_version` is not 10 drops the car from the list. Run time slots of the record (list link, names, '
            'colour choices...) are zeros in the files. All texts are Latin-1',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        game = (
            _s16(),
            {
                'description': "4 in every NFS4 file (NFS3's files hold 3): its low 4 bits replace those of record "
                "+0x37c (the file's `runtime_0x37c`); their getter 0x473060 has no caller: not read"
            },
        )
        runtime_list = (
            BytesBlock(length=16),
            {
                'description': 'Record +0x00..+0x0f, zeros in the files: the list link (+0x00, set to 0) and the text '
                'table header the loader sets (0x473710: +0x04 count, +0x08 file, +0x0c offsets)'
            },
        )
        name = (
            Latin1Block(length=256),
            {
                'description': "Record +0x10, the car's name in the lists; empty in the files: the loader writes text 2 "
                '(`full_name`) over it'
            },
        )
        car_id = (
            Latin1Block(length=256),
            {
                'description': "Car id (`Mcf1`, record +0x110): the loader copies it to +0x315, then puts the car's "
                'folder name in its place'
            },
        )
        folder = (
            Latin1Block(length=256),
            {'description': "Record +0x210, empty in the files: the loader writes the car's folder name there"},
        )
        runtime_0x310 = (
            BytesBlock(length=12),
            {'description': 'Record +0x310..+0x31b, zeros in the files; +0x315 receives the `car_id` (0x4725f0)'},
        )
        serial_number = (
            _s32(),
            {
                'description': "The car's number in the game (record +0x31c; carp.txt's `serial_number`, 0..49): the "
                'car list index of each number (0x68a15c, 0x473410 / 0x473450) through which the race, the physics and '
                "the network find the car's record"
            },
        )
        runtime_0x320 = (
            BytesBlock(length=88),
            {
                'description': 'Record +0x320..+0x377, zeros in the files: +0x320 set by the loader (0x4739e0), the colour '
                'count (+0x32c, 0x473090) and other run time values'
            },
        )
        flags = (BitFlagsBlock(flag_names=_NFS4_FLAGS, length=4), {'description': _NFS4_FLAGS_TEXT})
        runtime_0x37c = (
            IntegerBlock(length=4),
            {'description': 'Record +0x37c, 0 in the files; its low 4 bits get `game`'},
        )
        car_class = (
            _s32(),
            {
                'description': 'Car class: 0 the race cars (Elni, MClk, Mcf1, Peln, Plac), 1 A, 2 B, 3 C, 255 none '
                '(Knoc). Record +0x380 (0x473030): the lists and race setup filter by it (0x4747e0, 0x4722d0), the network '
                'sends it (0x4eb5d0); Carp_TuneCar 0x4fcad0 gives a class 0 car the special grip (car+0x4dc = 1: the wheel '
                'grip slider t -> (t + 1) x 0.5, 0x4ff6b0)'
            },
        )
        interior_view_heading = (
            _u16(),
            {
                'description': "Where the showroom's interior view (`IN_<car>.fsh`, 1280 texels per turn) starts, in "
                'texels: record +0x384 (0x475bd0, 128 for a missing car), as NFS3. 128 for the cars without an interior'
            },
        )
        format_version = (
            _u8(),
            {
                'description': 'Format version, 10 in every file (record +0x386): 0x473d20 drops a car whose file holds '
                'another value'
            },
        )
        acceleration = (
            ArrayBlock(child=_u8(), length=4),
            {
                'description': 'Acceleration rating (0..20) at upgrade levels 0..3 (record +0x387; 0x4724c0 returns '
                "rating x 0.05): the showroom's and car select's bars. Unless `no_upgrades`, the loader raises each "
                'level to at least the one before'
            },
        )
        top_speed = (ArrayBlock(child=_u8(), length=4), {'description': 'Top speed rating at levels 0..3 (+0x38b)'})
        handling = (ArrayBlock(child=_u8(), length=4), {'description': 'Handling rating at levels 0..3 (+0x38f)'})
        braking = (ArrayBlock(child=_u8(), length=4), {'description': 'Braking rating at levels 0..3 (+0x393)'})
        overall_rating = (
            ArrayBlock(child=_u8(), length=4),
            {
                'description': 'Overall rating at levels 0..3 (+0x397; 0x472530): the AI opponents are picked among cars '
                'of a rating like the player\'s (0x476ef0, 0x4c4f40 "Human Car\'s Rating"); not made rising by the loader'
            },
        )
        unused_0x39d = (_u8(), {'description': 'Record +0x39b, 0 in every file; no reader found'})
        price = (
            _s32(),
            {'description': "Price in dollars (record +0x39c; 0x475df0 index 0): the career mode's car dealer"},
        )
        upgrade_prices = (
            ArrayBlock(child=_s32(), length=3),
            {'description': 'Prices of upgrade levels 1..3 (record +0x3a0; 0x475df0 indexes 1..3), career mode'},
        )
        runtime_0x3ac = (
            BytesBlock(length=12),
            {'description': 'Record +0x3ac..+0x3b7, zeros in the files; no reader found'},
        )
        driver_seat = (
            _u8(),
            {
                'description': "Driver seat as NFS3's fedata +0x12 (1 right: Jxkr only), record +0x3b8; its getter "
                '0x473000 has no caller: not read'
            },
        )
        engine_position = (
            _u8(),
            {
                'description': 'Engine position: 0 front, 1 middle (Ff50, Ldia, MClk, Mcf1, PDia), 2 rear (B911, P911, '
                'PP91). Record +0x3b9 (0x472fd0; the network sends it, 0x4eb5d0): the engine point is 0.85, -0.25 or '
                "-0.85 of the car's half length along it (0x5084d0: car+0xac4, where the crash smoke of 0x44d7e0 comes "
                'out; also 0x4b4780); a crash damages '
                'the engine from the front for 0, from the rear otherwise (Damage_FromCrash 0x449b30)'
            },
        )
        unused_0x3bc = (
            BytesBlock(length=2),
            {'description': 'Record +0x3ba..+0x3bb, zeros in every file; no reader found'},
        )
        texts = (
            FeDataTextTable(table_offset=0x3BE, text_names=NFS4_FEDATA_TEXTS),
            {'description': 'The spec sheet texts (41 in every file; text 2 also becomes the car list name)'},
        )

    def serializer_class(self):
        from serializers import CarFeDataSerializer

        return CarFeDataSerializer


def is_nfs3_fedata(head: bytes) -> bool:
    """An NFS3 fedata header: 4 id characters, then the format version 9"""
    return len(head) >= 0x2F and head[4:6] == b'\x09\x00'


def is_nfs4_fedata(head: bytes) -> bool:
    """An NFS4 fedata file: the record copy with the format version 10 at 0x388"""
    return len(head) >= 0x3C0 and head[0x388] == 10
