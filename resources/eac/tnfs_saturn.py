"""Sega Saturn TNFS port Over Drivin' GT-R (Japan; the 8 cars replaced by 8 Nissans): car bundles `CARS/<car>.ALL`
and `CAR2/<car>.ALL`, the executable `0` (car AI records), car showcase pictures `UIDATA/*.DAT`. Big-endian (SH-2)
copies of the PC / PSX layouts where there are ones. "Checked" in the descriptions: against every file of the game
folder (`games/tnfs_saturn_gtr`); the Saturn executable is not disassembled, the field meanings of the PC / PSX layouts
are the PC / PSX game's"""

from copy import deepcopy
from typing import Dict, List, Optional, Tuple

from library.context import ReadContext, WriteContext
from library.read_blocks import (
    ArrayBlock,
    BytesBlock,
    DeclarativeCompoundBlock,
    FixedPointBlock,
    IntegerBlock,
    TrailingOptionalBlock,
    UTF8Block,
)
from library.utils import transform_bitness
from resources.eac.car_specs import CarAiAndCrashBody, PlayerCarPhysics
from resources.eac.fields.byte_order import big_endian_copy

# car slots of the game (the PC cars' file names), in the order of the car model ids 0..7, the cars they hold and
# their short names in the executable (0x47df0)
TNFS_SATURN_GTR_CARS = [
    ('SUPRA', 'Skyline GT-R PGC10', 'PGC10'),
    ('DIABLO', 'Skyline GT-R BCNR33', 'BCNR33'),
    ('PORSCHE', 'Fairlady Z 240ZG', '240ZG'),
    ('VETTE', 'Skyline GT-R KPGC110', 'KPGC110'),
    ('TESTA', 'Fairlady Z 300ZX', '300ZX'),
    ('VIPER', 'Skyline GT-R BNR32', 'BNR32'),
    ('NSX', '180SX Type X', '180SX'),
    ('RX7', "Silvia K's", 'SILVIA'),
]

# executable `0`: loaded at 0x06010000, a pointer is the load address + the file offset
TNFS_SATURN_GTR_LOAD_ADDRESS = 0x06010000
TNFS_SATURN_GTR_EXECUTABLE_LENGTH = 598912
TNFS_SATURN_GTR_MODEL_POINTERS_OFFSET = 0x84F14
TNFS_SATURN_GTR_CAR_AI_OFFSET = 0x84F90
TNFS_SATURN_GTR_CAR_AI_POINTERS_OFFSET = 0x85FBC
TNFS_SATURN_GTR_CAR_AI_RECORDS = 9
TNFS_SATURN_GTR_CAR_AI_POINTERS = 23
# entries of the car AI pointer table: car model id 0 at entry 13, the Warrior at entries 21 and 22
TNFS_SATURN_GTR_FIRST_CAR_AI_POINTER = 13
TNFS_SATURN_GTR_WARRIOR_CAR_AI_POINTER = 21
# PC PDN top speed = mph x 29124 (16.16 fixed point m/s, the game's mph to m/s factor 0.4444); the Saturn's are whole
# mph in 16.16
PC_PDN_MPH_TO_RAW = 29124


def saturn_color_to_rgba(color: int) -> int:
    """A Saturn 16-bit RGB colour (bits 0-4 red, 5-9 green, 10-14 blue, 15 the RGB flag, set in every texture colour)
    as RGBA 0xRRGGBBAA, opaque. Which texels are transparent is up to the texture's draw mode, not the colour"""
    red = transform_bitness(color, 5)
    green = transform_bitness(color >> 5, 5)
    blue = transform_bitness(color >> 10, 5)
    return red << 24 | green << 16 | blue << 8 | 0xFF


def _tnfs_saturn_car_physics_fields():
    # the PC layout, big-endian
    return type(
        'Fields',
        (DeclarativeCompoundBlock.Fields,),
        {name: (big_endian_copy(block), extras) for name, (block, extras) in PlayerCarPhysics.Fields.fields},
    )


class TnfsSaturnCarPhysics(PlayerCarPhysics):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': "Player car physics of the Sega Saturn TNFS port (Over Drivin' GT-R): the PC "
            '`PlayerCarPhysics` (PBS) layout, 1912 bytes, every 4-byte field big-endian (the grip tables are bytes); '
            "the checksum is the PC's (byte sum of the first 1880 bytes), right in every file (checked). The first "
            'part of a car bundle `CARS/<car>.ALL` / `CAR2/<car>.ALL` (the two hold the same bytes). Field meanings '
            "as in the PC game. The Warrior's physics (not in the car folders) are the PC TRAFFC.PBS byte for byte",
        }

    Fields = _tnfs_saturn_car_physics_fields()


def _tnfs_saturn_car_ai_fields():
    replaced = {
        'top_speeds': (
            ArrayBlock(
                length=6,
                child=FixedPointBlock(length=4, fraction_bits=16, is_signed=True, byte_order='big'),
            ),
            {
                'description': 'Top speed (mph, whole numbers in 16.16 fixed point) per AI gear, 0 = gear skipped; the PC '
                "PDN holds m/s with its mph factor: PC raw value = mph x 29124 (0.4444 m/s per mph). The Warrior's "
                'are the PC TRAFFC.PDN ones (54, 82, 109, 142, 192 mph; checked)'
            },
        ),
        'gear_count': (
            FixedPointBlock(length=4, fraction_bits=16, is_signed=True, byte_order='big'),
            {
                'description': 'The PC field (`gear_count`, the traffic horn pitch index) in 16.16 fixed point: 5.0 in every '
                'record (PC: the integer 5)'
            },
        ),
    }
    fields = {}
    for name, (block, extras) in CarAiAndCrashBody.Fields.fields:
        fields[name] = replaced.get(name, (big_endian_copy(block), extras))
    return type('Fields', (DeclarativeCompoundBlock.Fields,), fields)


class TnfsSaturnCarAiAndCrashBody(CarAiAndCrashBody):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': "Car AI and crash body of the Sega Saturn TNFS port (Over Drivin' GT-R): the PC "
            '`CarAiAndCrashBody` (PDN) layout, 460 bytes, big-endian, with the top speeds in mph and `gear_count` in '
            '16.16 fixed point. Not a file: 9 records in the executable `0` (`TnfsSaturnGtrExecutable`). The record '
            'of the Warrior is the PC TRAFFC.PDN but for those two fields (checked)',
        }

    Fields = _tnfs_saturn_car_ai_fields()

    @staticmethod
    def pc_data(data: dict) -> dict:
        """The record as PC `CarAiAndCrashBody` data: top speeds in the PC's m/s (raw mph x 29124), `gear_count` an
        integer"""
        result = deepcopy(data)
        result['top_speeds'] = [round(mph * PC_PDN_MPH_TO_RAW) / 0x10000 for mph in data['top_speeds']]
        result['gear_count'] = round(data['gear_count'])
        return result


class TnfsSaturnTextureEntry(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A texture of a Saturn texture bank: name, size, VDP1 draw mode and where its pixels '
            'are. The fields are parts of a VDP1 sprite command (CMDPMOD, CMDSRCA, CMDSIZE)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        name_start = (UTF8Block(length=2), {'description': 'Characters 1 and 2 of the name (`J0` of `J000`)'})
        width_8 = (
            IntegerBlock(length=2, byte_order='big'),
            {'description': 'Width in pixels / 8 (VDP1 CMDSIZE bits 13-8): widths are multiples of 8'},
        )
        height = (
            IntegerBlock(length=2, byte_order='big'),
            {'description': 'Height in pixels (VDP1 CMDSIZE bits 7-0)'},
        )
        draw_mode = (
            IntegerBlock(length=2, byte_order='big'),
            {
                'description': 'VDP1 draw mode word (CMDPMOD): 0x10C8 or 0x1088 in every texture (checked). Bits 3-5 = 1: '
                "colour mode 1, 16 colours from a lookup table (the texture's 16 colours of `colors`); bit 7 (ECD): "
                'end codes off; bit 12 (HSS): high speed shrink; bit 6 (SPD): with it (0x10C8) colour index 0 is drawn '
                'like any other, without it (0x1088) index 0 is transparent: the wheels, the inner tyre faces, the '
                'shadows and the other cut-out textures, whose colour 0 is a key colour (blue, magenta, cyan or '
                'black). The export makes index 0 of a 0x1088 texture transparent'
            },
        )
        pixel_offset = (
            IntegerBlock(length=2, byte_order='big'),
            {
                'description': "Offset of the texture's pixels in `pixels`, in 8-byte units (VDP1 CMDSRCA): the textures "
                'are back to back'
            },
        )
        name_end = (
            UTF8Block(length=2),
            {
                'description': 'Characters 3 and 4 of the name (`00` of `J000`), stored in reverse order: the 4-character '
                'name is `name_start` + this (shown in order here)'
            },
        )

    def read(self, ctx: ReadContext, name: str = '', read_bytes_amount=None):
        data = super().read(ctx, name, read_bytes_amount)
        data['name_end'] = data['name_end'][::-1]
        return data

    def write(self, data, ctx: WriteContext = None, name: str = '') -> bytes:
        data = deepcopy(data)
        data['name_end'] = data['name_end'][::-1]
        return super().write(data, ctx, name)


def tnfs_saturn_texture_name(entry: dict) -> str:
    return (entry['name_start'] + entry['name_end']).rstrip('\0')


# draw mode bit 6 (SPD, transparent pixel disable): without it texels of colour index 0 are not drawn
SATURN_DRAW_MODE_INDEX_0_DRAWN = 0x40


class TnfsSaturnTextureBank(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Texture bank of a Saturn car model: 4-bit textures with 16 colours each (VDP1 colour '
            'mode 1). Pixels: two per byte, the high nibble first (the left pixel), rows of `width` pixels, top to '
            'bottom. Colours: Saturn 16-bit RGB (bits 0-4 red, 5-9 green, 10-14 blue, bit 15 set in every colour), 16 '
            'per texture, in texture order. In the high-poly textures of five cars (BNR32, BCNR33, PGC10, KPGC110, '
            '180SX) colour 0 of the rear light texture (the texture of the `bkll` / `bklr` polygons) is pure green, '
            'the PSX convention for the brake light colour the game writes at run time; the PSX game takes CLUT entries '
            "of pure green (5-bit red < 2, green > 29, blue < 2), the BCNR33's green is 29. Where the Saturn game "
            'writes the brake light colours is not known',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        num_textures = (
            IntegerBlock(length=4, byte_order='big', programmatic_value=lambda ctx: len(ctx.data('textures'))),
            {'description': 'Number of textures'},
        )
        textures = (
            ArrayBlock(child=TnfsSaturnTextureEntry(), length=lambda ctx: ctx.data('num_textures')),
            {
                'description': 'The textures: high-poly banks have `J000`.. (the polygon textures of the model), the tyres '
                '`Tir1`..`Tir4` (`Tyr1`..`Tyr4` in the PGC10) and a few more (`null`); low-poly banks `J000`..`J007`'
            },
        )
        pixels_size = (
            IntegerBlock(length=4, byte_order='big', programmatic_value=lambda ctx: len(ctx.data('pixels'))),
            {'description': 'Length of `pixels` in bytes'},
        )
        pixels = (
            BytesBlock(length=(lambda ctx: ctx.data('pixels_size'), 'pixels_size')),
            {'description': 'Pixels of every texture, 4 bits each'},
        )
        num_colors = (
            IntegerBlock(length=4, byte_order='big', programmatic_value=lambda ctx: len(ctx.data('colors'))),
            {'description': 'Number of colours: 16 per texture'},
        )
        colors = (
            ArrayBlock(child=IntegerBlock(length=2, byte_order='big'), length=lambda ctx: ctx.data('num_colors')),
            {'description': 'Colour lookup tables, 16 colours per texture, in texture order'},
        )


def tnfs_saturn_texture_pixels(bank: dict, index: int) -> Tuple[int, int, List[int], List[int]]:
    """(width, height, colour index per pixel, the 16 colours) of texture `index` of a texture bank"""
    entry = bank['textures'][index]
    width, height = entry['width_8'] * 8, entry['height']
    start = entry['pixel_offset'] * 8
    packed = bank['pixels'][start : start + width * height // 2]
    indices = []
    for byte in packed:
        indices.append(byte >> 4)
        indices.append(byte & 0xF)
    return width, height, indices, list(bank['colors'][16 * index : 16 * index + 16])


def tnfs_saturn_texture_image(bank: dict, index: int):
    """PIL image (indexed, its 16 colours as palette) of texture `index` of a texture bank, colour index 0 transparent
    when the draw mode says so (`SATURN_DRAW_MODE_INDEX_0_DRAWN` not set)"""
    from PIL import Image

    width, height, indices, colors = tnfs_saturn_texture_pixels(bank, index)
    image = Image.new('P', (width, height))
    image.putdata(indices)
    palette = []
    for color in colors:
        rgba = saturn_color_to_rgba(color)
        palette.extend([(rgba >> 24) & 0xFF, (rgba >> 16) & 0xFF, (rgba >> 8) & 0xFF])
    image.putpalette(palette)
    if not bank['textures'][index]['draw_mode'] & SATURN_DRAW_MODE_INDEX_0_DRAWN:
        image.info['transparency'] = bytes([0] + [255] * 15)
    return image


class TnfsSaturnRleImage(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'An 8-bit picture: size, a 256-colour palette (Saturn 16-bit RGB) and run-length encoded '
            'pixels as in PCX files: a byte from 0xC0 up repeats the next byte (b & 0x3F) times, any other byte is one '
            'pixel; rows of `width` pixels top to bottom, the runs go on over row ends. The last pixel is followed by '
            'zeros up to a multiple of 4 bytes (checked)',
        }

    def __init__(self, data_length, **kwargs):
        super().__init__(**kwargs)
        # length of `data`: a function of the context of this block (the picture's size field is before it)
        self.data_length = data_length

    class Fields(DeclarativeCompoundBlock.Fields):
        width = (IntegerBlock(length=2, byte_order='big'), {'description': 'Width in pixels'})
        height = (IntegerBlock(length=2, byte_order='big'), {'description': 'Height in pixels'})
        palette = (
            ArrayBlock(child=IntegerBlock(length=2, byte_order='big'), length=256),
            {'description': 'Colours (Saturn 16-bit RGB, bit 15 set). Colour 0 is the see-through one'},
        )
        data = (
            BytesBlock(length=(lambda ctx: ctx.block.data_length(ctx), 'the size before the picture - 520')),
            {'description': 'Run-length encoded pixels, then zeros up to a multiple of 4 bytes'},
        )


def tnfs_saturn_rle_pixels(data: dict) -> List[int]:
    """Colour index of every pixel of a `TnfsSaturnRleImage`"""
    stream = data['data']
    count = data['width'] * data['height']
    pixels = []
    i = 0
    while len(pixels) < count and i < len(stream):
        value = stream[i]
        i += 1
        if value >= 0xC0:
            pixels.extend([stream[i]] * (value & 0x3F))
            i += 1
        else:
            pixels.append(value)
    if len(pixels) < count:
        pixels.extend([0] * (count - len(pixels)))
    return pixels[:count]


def tnfs_saturn_rle_image(data: dict):
    """RGBA PIL image of a `TnfsSaturnRleImage`, colour index 0 transparent"""
    from PIL import Image

    image = Image.new('P', (data['width'], data['height']))
    image.putdata(tnfs_saturn_rle_pixels(data))
    palette = []
    for color in data['palette']:
        rgba = saturn_color_to_rgba(color)
        palette.extend([(rgba >> 24) & 0xFF, (rgba >> 16) & 0xFF, (rgba >> 8) & 0xFF])
    image.putpalette(palette)
    image.info['transparency'] = bytes([0] + [255] * 255)
    return image.convert('RGBA')


class TnfsSaturnCockpit(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Cockpit view pictures of a car: the dashboard (352x240, colour 0 = the see-through '
            'windscreen) and the steering wheel (176x176, colour 0 transparent), each after its size',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        dashboard_size = (
            IntegerBlock(
                length=4,
                byte_order='big',
                programmatic_value=lambda ctx: (
                    4 + ctx.block.field_blocks_map['dashboard'].estimate_packed_size(ctx.data('dashboard'))
                ),
            ),
            {'description': 'Length of this field and `dashboard` in bytes'},
        )
        dashboard = (
            TnfsSaturnRleImage(data_length=lambda ctx: ctx.data('../dashboard_size') - 520),
            {'description': 'The dashboard, 352x240'},
        )
        steering_wheel_size = (
            IntegerBlock(
                length=4,
                byte_order='big',
                programmatic_value=lambda ctx: (
                    4 + ctx.block.field_blocks_map['steering_wheel'].estimate_packed_size(ctx.data('steering_wheel'))
                ),
            ),
            {'description': 'Length of this field and `steering_wheel` in bytes: the rest of the file'},
        )
        steering_wheel = (
            TnfsSaturnRleImage(data_length=lambda ctx: ctx.data('../steering_wheel_size') - 520),
            {'description': 'The steering wheel, 176x176'},
        )


class TnfsSaturnCarBundle(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': "Car bundle of the Sega Saturn TNFS port Over Drivin' GT-R: `CARS/<car>.ALL` (the "
            'first paint, with the cockpit pictures) and `CAR2/<car>.ALL` (the second paint: the same physics and the '
            'same texture names, other colours and pixels, no cockpit). The executable loads `CARS\\%s.ALL` / '
            "`CAR2\\%s.ALL` (strings at 0x22330). The file names are the PC cars' (SUPRA = Skyline GT-R PGC10, DIABLO "
            '= Skyline GT-R BCNR33, PORSCHE = Fairlady Z 240ZG, VETTE = Skyline GT-R KPGC110, TESTA = Fairlady Z 300ZX, '
            "VIPER = Skyline GT-R BNR32, NSX = 180SX Type X, RX7 = Silvia K's). The car models are in the executable "
            '(`TnfsSaturnOrixGeometry`)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        physics = (TnfsSaturnCarPhysics(), {'description': 'Player car physics'})
        textures = (
            TnfsSaturnTextureBank(),
            {'description': 'Textures of the high-poly model (`MODELS/<car>/high.orix`)'},
        )
        low_poly_textures = (
            TnfsSaturnTextureBank(),
            {'description': 'Textures of the low-poly model (`MODELS/<car>/low.orix`)'},
        )
        cockpit = (
            TrailingOptionalBlock(child=TnfsSaturnCockpit()),
            {'description': 'Cockpit view pictures, in `CARS/<car>.ALL` only'},
        )

    def serializer_class(self):
        from serializers import TnfsSaturnCarBundleSerializer

        return TnfsSaturnCarBundleSerializer


def is_tnfs_saturn_car_bundle(head: bytes) -> bool:
    """Starts with a big-endian PBS whose checksum is right"""
    return len(head) >= 1912 and sum(head[:1880]) == int.from_bytes(head[1908:1912], 'big')


class TnfsSaturnGtrExecutable(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': "The executable `0` of Over Drivin' GT-R (SH-2, big-endian, 598912 bytes, loaded at "
            '0x06010000: a pointer is 0x06010000 + the file offset). Only the car tables are parsed: the car model '
            'pointers, the car AI records and their pointers. Also in it: the car models themselves (ORIX, '
            '`TnfsSaturnOrixGeometry`), the short car names at 0x47df0 (`SILVIA`, `180SX`, `BNR32`, `300ZX`, '
            '`KPGC110`, `240ZG`, `BCNR33`, `PGC10`) and the names the model loader looks up (0x222c4..0x2242c)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        code = (
            BytesBlock(length=TNFS_SATURN_GTR_MODEL_POINTERS_OFFSET),
            {'description': 'Code and data before the car model pointers'},
        )
        model_pointers = (
            ArrayBlock(child=IntegerBlock(length=4, byte_order='big'), length=31),
            {
                'description': 'Car model pointers: [0..8] the high-poly models of car model ids 0..7 (SUPRA, DIABLO, '
                'PORSCHE, VETTE, TESTA, VIPER, NSX, RX7) and of the Warrior, [9..21] 0, [22..30] the low-poly models '
                'in the same order'
            },
        )
        car_ai_records = (
            ArrayBlock(child=TnfsSaturnCarAiAndCrashBody(), length=TNFS_SATURN_GTR_CAR_AI_RECORDS),
            {
                'description': 'Car AI records (PC PDN), 9 of them: [0] the Warrior, [1] NSX, [2] PORSCHE, [3] TESTA, '
                '[4] DIABLO, [5] VIPER, [6] VETTE, [7] SUPRA, [8] RX7 (by `car_ai_pointers`)'
            },
        )
        car_ai_pointers = (
            ArrayBlock(child=IntegerBlock(length=4, byte_order='big'), length=TNFS_SATURN_GTR_CAR_AI_POINTERS),
            {
                'description': 'Pointers to `car_ai_records`: [13 + car model id] the record of each car (model ids 0..7 '
                "-> records 7, 4, 2, 6, 3, 5, 1, 8), [21] and [22] the Warrior's (record 0), [0..12] record 7 (SUPRA)"
            },
        )
        rest = (
            BytesBlock(length=(lambda ctx: ctx.read_bytes_remaining, 'up to the end of the file')),
            {'description': 'Code and data after the car AI pointers'},
        )

    def serializer_class(self):
        from serializers import TnfsSaturnGtrExecutableSerializer

        return TnfsSaturnGtrExecutableSerializer


def tnfs_saturn_gtr_car_ai_records(data: dict) -> Dict[str, int]:
    """Car slot name (`TNFS_SATURN_GTR_CARS`, `WARRIOR`) -> index in `car_ai_records`, by the car AI pointers"""
    record_pointers = {
        TNFS_SATURN_GTR_LOAD_ADDRESS + TNFS_SATURN_GTR_CAR_AI_OFFSET + 460 * i: i
        for i in range(len(data['car_ai_records']))
    }
    pointers = data['car_ai_pointers']
    result = {}
    for model_id, (slot, _, _) in enumerate(TNFS_SATURN_GTR_CARS):
        record = record_pointers.get(pointers[TNFS_SATURN_GTR_FIRST_CAR_AI_POINTER + model_id])
        if record is not None:
            result[slot] = record
    warrior = record_pointers.get(pointers[TNFS_SATURN_GTR_WARRIOR_CAR_AI_POINTER])
    if warrior is not None:
        result['WARRIOR'] = warrior
    return result


def is_tnfs_saturn_gtr_executable(head: bytes) -> bool:
    """The executable `0`: its car AI pointer table (`head` from the file start, at least up to it)"""
    offset = TNFS_SATURN_GTR_CAR_AI_POINTERS_OFFSET
    if len(head) < offset + 4 * TNFS_SATURN_GTR_CAR_AI_POINTERS:
        return False
    first = TNFS_SATURN_GTR_LOAD_ADDRESS + TNFS_SATURN_GTR_CAR_AI_OFFSET
    last = first + 460 * (TNFS_SATURN_GTR_CAR_AI_RECORDS - 1)
    pointers = [
        int.from_bytes(head[offset + 4 * i : offset + 4 * i + 4], 'big') for i in range(TNFS_SATURN_GTR_CAR_AI_POINTERS)
    ]
    return all(first <= p <= last and (p - first) % 460 == 0 for p in pointers)


class TnfsSaturnPcxListEntry(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A picture of a list: its size and a PCX file',
            'inline_description': True,
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        size = (
            IntegerBlock(length=4, byte_order='big', programmatic_value=lambda ctx: len(ctx.data('pcx'))),
            {'description': 'Length of `pcx` in bytes'},
        )
        pcx = (
            BytesBlock(length=(lambda ctx: ctx.data('size'), 'size')),
            {'description': 'A PCX file (version 5, 8 bits, 256-colour palette at the end)'},
        )


def _pcx_list_amount(ctx) -> Optional[int]:
    start = ctx.buffer.tell()
    remaining = ctx.read_bytes_remaining
    pos, amount = 0, 0
    try:
        while pos + 4 <= remaining:
            ctx.buffer.seek(start + pos)
            pos += 4 + int.from_bytes(ctx.buffer.read(4), 'big')
            amount += 1
    finally:
        ctx.buffer.seek(start)
    return amount


class TnfsSaturnPcxList(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': "Pictures of a car showcase page of Over Drivin' GT-R: `UIDATA/<car>GEN.DAT` (general), "
            '`<car>MEC.DAT` (mechanical), `<car>PER.DAT` (performance), named after the PC cars (`512` TESTA, `911` '
            'PORSCHE, `DIA` DIABLO, `NSX`, `RX7`, `SUP` SUPRA, `VIP` VIPER, `ZR1` VETTE). The first picture (320x224) is '
            'the page background with empty text boxes, the others are photos and panels (192x96, 304x84, 304x52...). '
            'The car cards are plain PCX files, `UIDATA/<maker>/MAIN.PCX`',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        pictures = (
            ArrayBlock(
                child=TnfsSaturnPcxListEntry(),
                length=(lambda ctx: _pcx_list_amount(ctx), 'up to the end of the file'),
            ),
            {'description': 'The pictures, back to back'},
        )

    def serializer_class(self):
        from serializers import TnfsSaturnPcxListSerializer

        return TnfsSaturnPcxListSerializer


def is_tnfs_saturn_pcx_list(buffer, length: int) -> bool:
    """A list of (big-endian size, PCX file) up to the end of the file"""

    start = buffer.tell()
    pos = 0
    try:
        while pos + 8 <= length:
            buffer.seek(start + pos)
            head = buffer.read(8)
            if head[4:7] != b'\x0a\x05\x01':
                return False
            pos += 4 + int.from_bytes(head[:4], 'big')
        return pos == length
    finally:
        buffer.seek(start)
