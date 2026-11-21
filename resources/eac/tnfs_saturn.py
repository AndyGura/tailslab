"""Sega Saturn TNFS port Over Drivin' GT-R (Japan; the 8 cars replaced by 8 Nissans): car bundles `CARS/<car>.ALL`
and `CAR2/<car>.ALL`, the executable `0` (in-car view records, car AI records), car showcase pictures `UIDATA/*.DAT`,
the menu art `UIDATA/FRONTEND.DAT` / `SHOWCASE.DAT`, the run-length encoded pictures of `UIDATA/ELOAD` and
`UIDATA/ECREDITS`, and the 8-bit pictures `HORIZON/*.IM`, `DASH/*.IM` and `DASH/EMEM3.DAT`.
Big-endian (SH-2) copies of the PC / PSX layouts where there are ones. "Checked" in the descriptions: against every file
of the game folder (`games/tnfs_saturn_gtr`). The car formats are not traced in the Saturn executable: their field
meanings are the PC / PSX game's. The menu art and pictures are (nfs-web's Ghidra project `decomp/tnfs_saturn_gtr`,
addresses in the descriptions)"""

from copy import deepcopy
from io import BytesIO
from typing import Dict, List, Optional, Tuple

import numpy as np

from library.context import ReadContext, WriteContext
from library.read_blocks import (
    REMAINING,
    SizeOf,
    ArrayBlock,
    BytesBlock,
    DeclarativeCompoundBlock,
    FixedPointBlock,
    IntegerBlock,
    TrailingOptionalBlock,
    UTF8Block,
    CountOf,
)
from library.read_blocks.misc.value_validators import Eq
from library.utils.colors import decode_colors, rgb_palette, rgba_image
from resources.eac.car_specs import CarAiAndCrashBody, PlayerCarPhysics
from resources.eac.fields.byte_order import derive_fields

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
# the in-car view's records by car model id (`g_cockpit_table` 0x060815b0, 0x20 bytes each) and the speedometer's
# top by car model id 0..7 (`g_speedo_clamp` 0x06081864, s32)
TNFS_SATURN_GTR_COCKPIT_RECORDS_OFFSET = 0x715B0
TNFS_SATURN_GTR_COCKPIT_RECORDS = 9
TNFS_SATURN_GTR_SPEEDOMETER_TOPS_OFFSET = 0x71864
TNFS_SATURN_GTR_SPEEDOMETER_TOPS = 8
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


def saturn_colors_to_rgba(colors) -> np.ndarray:
    """Saturn 16-bit RGB colours (bits 0-4 red, 5-9 green, 10-14 blue, 15 the RGB flag, set in every texture colour)
    as RGBA (uint32 0xRRGGBBAA), opaque. Which texels are transparent is up to the texture's draw mode, not the
    colour"""
    return decode_colors('bgr555', colors)


def saturn_color_to_rgba(color: int) -> int:
    """`saturn_colors_to_rgba` of one colour"""
    return int(saturn_colors_to_rgba(color))


class TnfsSaturnCarPhysics(PlayerCarPhysics):
    block_description = (
        "Player car physics of the Sega Saturn TNFS port (Over Drivin' GT-R): the PC "
        '`PlayerCarPhysics` (PBS) layout, 1912 bytes, every 4-byte field big-endian (the grip tables are bytes); '
        "the checksum is the PC's (byte sum of the first 1880 bytes), right in every file (checked). The first "
        'part of a car bundle `CARS/<car>.ALL` / `CAR2/<car>.ALL` (the two hold the same bytes). Field meanings '
        "as in the PC game. The Warrior's physics (not in the car folders) are the PC TRAFFC.PBS byte for byte"
    )

    # the PC layout, big-endian
    Fields = derive_fields(PlayerCarPhysics.Fields)


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
    return derive_fields(CarAiAndCrashBody.Fields, replace=replaced)


class TnfsSaturnCarAiAndCrashBody(CarAiAndCrashBody):
    block_description = (
        "Car AI and crash body of the Sega Saturn TNFS port (Over Drivin' GT-R): the PC "
        '`CarAiAndCrashBody` (PDN) layout, 460 bytes, big-endian, with the top speeds in mph and `gear_count` in '
        '16.16 fixed point. Not a file: 9 records in the executable `0` (`TnfsSaturnGtrExecutable`). The record '
        'of the Warrior is the PC TRAFFC.PDN but for those two fields (checked)'
    )

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
    block_description = (
        'A texture of a Saturn texture bank: name, size, VDP1 draw mode and where its pixels '
        'are. The fields are parts of a VDP1 sprite command (CMDPMOD, CMDSRCA, CMDSIZE)'
    )

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
    block_description = (
        'Texture bank of a Saturn car model: 4-bit textures with 16 colours each (VDP1 colour '
        'mode 1). Pixels: two per byte, the high nibble first (the left pixel), rows of `width` pixels, top to '
        'bottom. Colours: Saturn 16-bit RGB (bits 0-4 red, 5-9 green, 10-14 blue, bit 15 set in every colour), 16 '
        'per texture, in texture order. In the high-poly textures of five cars (BNR32, BCNR33, PGC10, KPGC110, '
        '180SX) colour 0 of the rear light texture (the texture of the `bkll` / `bklr` polygons) is pure green, '
        'the PSX convention for the brake light colour the game writes at run time; the PSX game takes CLUT entries '
        "of pure green (5-bit red < 2, green > 29, blue < 2), the BCNR33's green is 29. Where the Saturn game "
        'writes the brake light colours is not known'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        num_textures = (
            IntegerBlock(length=4, byte_order='big', programmatic_value=CountOf('textures')),
            {'description': 'Number of textures'},
        )
        textures = (
            ArrayBlock(child=TnfsSaturnTextureEntry(), length='num_textures'),
            {
                'description': 'The textures: high-poly banks have `J000`.. (the polygon textures of the model), the tyres '
                '`Tir1`..`Tir4` (`Tyr1`..`Tyr4` in the PGC10) and a few more (`null`); low-poly banks `J000`..`J007`'
            },
        )
        pixels_size = (
            IntegerBlock(length=4, byte_order='big', programmatic_value=CountOf('pixels')),
            {'description': 'Length of `pixels` in bytes'},
        )
        pixels = (
            BytesBlock(length='pixels_size'),
            {'description': 'Pixels of every texture, 4 bits each'},
        )
        num_colors = (
            IntegerBlock(length=4, byte_order='big', programmatic_value=CountOf('colors')),
            {'description': 'Number of colours: 16 per texture'},
        )
        colors = (
            ArrayBlock(child=IntegerBlock(length=2, byte_order='big'), length='num_colors'),
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
    image.putpalette(rgb_palette(saturn_colors_to_rgba(colors)))
    if not bank['textures'][index]['draw_mode'] & SATURN_DRAW_MODE_INDEX_0_DRAWN:
        image.info['transparency'] = bytes([0] + [255] * 15)
    return image


class TnfsSaturnRleImage(DeclarativeCompoundBlock):
    block_description = (
        'An 8-bit picture: size, a 256-colour palette (Saturn 16-bit RGB) and run-length encoded '
        'pixels as in PCX files: a byte from 0xC0 up repeats the next byte (b & 0x3F) times, any other byte is one '
        'pixel. Rows of `width` pixels top to bottom, each encoded on its own: no run crosses a row end (checked). '
        '0..3 zero bytes follow the last run: in the cockpit pictures of the car bundles they make the picture and '
        'its size field a multiple of 4 bytes (checked), in the `.IM` pictures not always (`HORIZON/AL1RISE.IM` '
        'ends with its last run, 45677 bytes). Always after a big-endian u32 size counting itself and the picture. '
        'The game loads them with `Vdp2_LoadRleBitmap` 0x0605e83c (bank, palette, colours, x, y, file; '
        "`DASH/EMEM3.DAT`'s with its decoding from memory, 0x0605e6f0): it reads the size, then the rest of the "
        'picture into memory, decodes it row by row into a 512-byte line buffer (a row ends when it has `width` '
        'pixels) and copies the rows to VDP2 VRAM from 0x25e00000 + bank x 0x20000 + x + 512 y, 512 bytes apart; '
        'then the colours into colour RAM from colour palette x 256: '
        '`colours` of them as they are, or all 256 recomputed per channel when `colours` is negative (0x0605e4b8, '
        'not read further)'
    )

    def __init__(self, data_length, **kwargs):
        super().__init__(**kwargs)
        # length of `data`: a function of the context of this block (the picture's size field is before it)
        self.data_length = data_length

    class Fields(DeclarativeCompoundBlock.Fields):
        width = (IntegerBlock(length=2, byte_order='big'), {'description': 'Width in pixels'})
        height = (IntegerBlock(length=2, byte_order='big'), {'description': 'Height in pixels'})
        palette = (
            ArrayBlock(child=IntegerBlock(length=2, byte_order='big'), length=256),
            {
                'description': 'Colours (Saturn 16-bit RGB: bits 0-4 red, 5-9 green, 10-14 blue; bit 15 clear in every '
                'colour, checked). Colour 0 is see-through in the cockpit pictures (the windscreen of the dashboard, '
                'around the steering wheel)'
            },
        )
        data = (
            BytesBlock(length=(lambda ctx: ctx.block.data_length(ctx), 'the size before the picture - 520')),
            {'description': 'Run-length encoded pixels, then 0..3 zero bytes'},
        )


def _tnfs_saturn_rle_rows(stream: bytes, width: int, height: int):
    """(row of colour indices, offset in `stream` after it) of every row of a `TnfsSaturnRleImage`'s runs, as
    `Vdp2_LoadRleBitmap` decodes them: a row ends when it has `width` pixels (a run past it is cut); a row the runs
    leave short (the end of `stream`) is padded with colour 0"""
    i = 0
    for _ in range(height):
        row = []
        while len(row) < width and i < len(stream):
            value = stream[i]
            i += 1
            if value >= 0xC0:
                if i >= len(stream):
                    break
                row.extend([stream[i]] * (value & 0x3F))
                i += 1
            else:
                row.append(value)
        row = row[:width]
        yield row + [0] * (width - len(row)), i


def tnfs_saturn_rle_pixels(data: dict) -> List[int]:
    """Colour index of every pixel of a `TnfsSaturnRleImage`"""
    pixels = []
    for row, _ in _tnfs_saturn_rle_rows(data['data'], data['width'], data['height']):
        pixels.extend(row)
    return pixels


def tnfs_saturn_rle_end(stream: bytes, width: int, height: int) -> Optional[int]:
    """Offset in `stream` after the runs of a `width` x `height` `TnfsSaturnRleImage`, None when `stream` ends before
    the last row is complete"""
    i = 0
    end = len(stream)
    for _ in range(height):
        count = 0
        while count < width:
            if i >= end:
                return None
            value = stream[i]
            i += 1
            if value >= 0xC0:
                if i >= end:
                    return None
                count += value & 0x3F
                i += 1
            else:
                count += 1
    return i


def tnfs_saturn_rle_image(data: dict):
    """RGBA PIL image of a `TnfsSaturnRleImage`, colour index 0 transparent"""
    from PIL import Image

    image = Image.new('P', (data['width'], data['height']))
    image.putdata(tnfs_saturn_rle_pixels(data))
    image.putpalette(rgb_palette(saturn_colors_to_rgba(data['palette'])))
    image.info['transparency'] = bytes([0] + [255] * 255)
    return image.convert('RGBA')


class TnfsSaturnCockpit(DeclarativeCompoundBlock):
    block_description = (
        'Cockpit view pictures of a car: the dashboard (352x240, colour 0 = the see-through '
        'windscreen) and the steering wheel (176x176, colour 0 transparent), each after its size. `Car_Load` '
        '0x06032458 loads them through `Vdp2_LoadRleBitmap` for the player of a one-view race only '
        '(`g_split_screen` 0x06082294 = 0). The race screen is 320x224 (every TVMD write is 0x8000): the 3D view '
        "shows through the windscreen, the car's cockpit record in the executable (`TnfsSaturnCockpitRecord`) "
        'places the needles and the wheel, and the rear view is drawn through a VDP1 user clipping window of 64x23 '
        "at the dashboard's (16, 26) at rest, the glass of every car's mirror frame (`Cockpit_DrawMirrorView` "
        '0x0602d1d8)'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        dashboard_size = (
            IntegerBlock(length=4, byte_order='big', programmatic_value=SizeOf('dashboard') + 4),
            {'description': 'Length of this field and `dashboard` in bytes'},
        )
        dashboard = (
            TnfsSaturnRleImage(data_length=lambda ctx: ctx.data('../dashboard_size') - 520),
            {
                'description': "The dashboard, 352x240: VDP2's NBG0, an 8-bit bitmap in VRAM bank 0 (palette 0). "
                "`Cockpit_Update` 0x0601e97c scrolls it by (16 - sway x, -sway y), and the sway's y is -8 at rest: at "
                "rest the screen shows the dashboard's (16, 8)..(336, 232), the 16 pixels on each side and 8 rows at "
                'the top and bottom are the room the dash sways in. Colour 0 is the see-through windscreen'
            },
        )
        steering_wheel_size = (
            IntegerBlock(length=4, byte_order='big', programmatic_value=SizeOf('steering_wheel') + 4),
            {'description': 'Length of this field and `steering_wheel` in bytes: the rest of the file'},
        )
        steering_wheel = (
            TnfsSaturnRleImage(data_length=lambda ctx: ctx.data('../steering_wheel_size') - 520),
            {
                'description': "The steering wheel, 176x176: VDP2's RBG0 rotation parameter B (the screen's lines "
                "from 112 down), VRAM bank 3, palette 1. It turns about its pixel (89, 89) by the front wheels' angle "
                "(steer_angle >> 14, 1024ths of a turn), placed by the car's cockpit record "
                '(`TnfsSaturnCockpitRecord`). Colour 0 transparent. Its pixels use colours 224..255 and 0 only '
                "(checked): RBG0's other picture, the horizon (rotation parameter A, `TnfsSaturnSizedRleImage`), is "
                'loaded into the same palette with 224 colours and uses colours 1..223'
            },
        )


class TnfsSaturnCarBundle(DeclarativeCompoundBlock):
    block_description = (
        "Car bundle of the Sega Saturn TNFS port Over Drivin' GT-R: `CARS/<car>.ALL` (the "
        'first paint, with the cockpit pictures) and `CAR2/<car>.ALL` (the second paint: the same physics and the '
        'same texture names, other colours and pixels, no cockpit). The executable loads `CARS\\%s.ALL` / '
        "`CAR2\\%s.ALL` (strings at 0x22330). The file names are the PC cars' (SUPRA = Skyline GT-R PGC10, DIABLO "
        '= Skyline GT-R BCNR33, PORSCHE = Fairlady Z 240ZG, VETTE = Skyline GT-R KPGC110, TESTA = Fairlady Z 300ZX, '
        "VIPER = Skyline GT-R BNR32, NSX = 180SX Type X, RX7 = Silvia K's). The car models are in the executable "
        '(`TnfsSaturnOrixGeometry`)'
    )
    serializer = 'TnfsSaturnCarBundleSerializer'

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
            {
                'description': 'Cockpit view pictures, in `CARS/<car>.ALL` only; loaded for the player of a one-view '
                'race only'
            },
        )


def is_tnfs_saturn_car_bundle(head: bytes) -> bool:
    """Starts with a big-endian PBS whose checksum is right"""
    return len(head) >= 1912 and sum(head[:1880]) == int.from_bytes(head[1908:1912], 'big')


def _needle_fields(gauge: str, angle: str, negative_offset: str) -> dict:
    """The six fields of a needle of `TnfsSaturnCockpitRecord`"""
    return {
        f'{gauge}_x_length': (
            IntegerBlock(length=1),
            {
                'description': f"Length L1 of the {gauge} needle's x part (the high byte of a big-endian short): the "
                'needle goes from the centre to centre + (-(L1 sin a + L1 cos a), L2 cos a - L2 sin a)'
            },
        ),
        f'{gauge}_y_length': (
            IntegerBlock(length=1),
            {'description': f"Length L2 of the {gauge} needle's y part (the low byte)"},
        ),
        f'{gauge}_x': (
            IntegerBlock(length=2, byte_order='big', is_signed=True),
            {'description': f"The {gauge}'s centre x on the screen, + the sway's x: at rest the dashboard's x + 16"},
        ),
        f'{gauge}_y': (
            IntegerBlock(length=2, byte_order='big', is_signed=True),
            {
                'description': f"The {gauge}'s centre y on the screen, + the sway's y (-8 at rest): at rest the "
                "dashboard's y"
            },
        ),
        f'{gauge}_scale': (
            IntegerBlock(length=2, byte_order='big', is_signed=True),
            {'description': f'Needle angle a = {angle}'},
        ),
        f'{gauge}_offset': (
            IntegerBlock(length=2, byte_order='big', is_signed=True),
            {'description': f'Added to the needle angle, 1024ths of a turn; can be negative ({negative_offset})'},
        ),
    }


def _tnfs_saturn_cockpit_record_fields():
    fields = {
        'needle_color': (
            IntegerBlock(length=2, byte_order='big'),
            {
                'description': 'Needle colour (Saturn 16-bit RGB): `Race_InitCockpit` puts it into colour RAM colour '
                '0x7f0, the needles are VDP1 lines of colour code 0x27f0. 0x0016 (red) but model 0 (0x2d6b, grey) and '
                'models 2 and 3 (0x5ad6, light grey)'
            },
        ),
        **_needle_fields(
            'tachometer',
            'rpm x scale / max rpm + offset, in 1024ths of a turn (max rpm: the PBS one, the rpm clamped to it)',
            '-174 in model 1',
        ),
        **_needle_fields(
            'speedometer',
            "min(speed, top) x scale / min(the car's top speed, top) + offset, in 1024ths of a turn (the speeds in "
            "the display unit, km/h or mph; top: the model's entry of the executable's `speedometer_tops`)",
            '-38 in model 5',
        ),
        'steering_wheel_left': (
            IntegerBlock(length=2, byte_order='big', is_signed=True),
            {
                'description': "Where the steering wheel picture goes: rotation parameter B's Xst = -(left + sway x / "
                "2) << 16, its left edge at screen x left + sway x / 2, at rest the dashboard's x left + 16. 72 but "
                'model 3 (74)'
            },
        ),
        'steering_wheel_top': (
            IntegerBlock(length=2, byte_order='big', is_signed=True),
            {
                'description': "Yst = -(top + sway y) << 16: the wheel picture's top edge at screen y top + sway y, at "
                "rest the dashboard's y top. 128 but model 6 (136)"
            },
        ),
        'steering_wheel_pivot_x': (
            IntegerBlock(length=2, byte_order='big', is_signed=True),
            {
                'description': "The wheel's rotation centre x in its picture (rotation parameter B's Px and Cx): 89 in "
                'every record'
            },
        ),
        'steering_wheel_pivot_y': (
            IntegerBlock(length=2, byte_order='big', is_signed=True),
            {'description': 'The rotation centre y (Py and Cy): 89 in every record'},
        ),
        'unknown': (
            IntegerBlock(length=2, byte_order='big'),
            {'description': '0 in every record', 'is_unknown': True},
        ),
    }
    return type('Fields', (DeclarativeCompoundBlock.Fields,), fields)


class TnfsSaturnCockpitRecord(DeclarativeCompoundBlock):
    block_description = (
        "A car model's in-car view record of Over Drivin' GT-R's executable (`g_cockpit_table` "
        '0x060815b0, 0x20 bytes, big-endian, signed 16-bit unless said): the needles drawn over the dashboard and '
        'where the steering wheel goes, in screen pixels of the 320x224 race screen. `Race_InitCockpit` 0x0601c7f0 '
        "takes the record of the player's car model and sets the needle colour and the wheel's rotation "
        "parameters; `Cockpit_Update` 0x0601e97c adds the dash's sway every frame and `Cockpit_DrawNeedles` "
        '0x0601e7a4 draws the needles as VDP1 lines: the angle a (`math_div`), its sine and cosine (1024-entry 16.16 '
        'tables at 0x0607fa60 / 0x0607fe60), each product with a length >> 16; down-left at a = 0, clockwise as a '
        "grows. The sway is (0, -8) at rest, so a centre (x, y) is the dashboard picture's (x + 16, y). The "
        "Warrior's record (model 8) has tachometer lengths 29, 11 and no speedometer (all 0: a digital speedometer)"
    )

    Fields = _tnfs_saturn_cockpit_record_fields()


class TnfsSaturnGtrExecutable(DeclarativeCompoundBlock):
    block_description = (
        "The executable `0` of Over Drivin' GT-R (SH-2, big-endian, 598912 bytes, loaded at "
        '0x06010000: a pointer is 0x06010000 + the file offset). Only the car tables are parsed: the cockpit records '
        'and the speedometer tops of the in-car view, the car model pointers, the car AI records and their '
        'pointers. Also in it: the car models themselves (ORIX, `TnfsSaturnOrixGeometry`), the short car names at '
        '0x47df0 (`SILVIA`, `180SX`, `BNR32`, `300ZX`, `KPGC110`, `240ZG`, `BCNR33`, `PGC10`) and the names the model '
        'loader looks up (0x222c4..0x2242c)'
    )
    serializer = 'TnfsSaturnGtrExecutableSerializer'

    class Fields(DeclarativeCompoundBlock.Fields):
        code = (
            BytesBlock(length=TNFS_SATURN_GTR_COCKPIT_RECORDS_OFFSET),
            {'description': 'Code and data before the cockpit records'},
        )
        cockpit_records = (
            ArrayBlock(child=TnfsSaturnCockpitRecord(), length=TNFS_SATURN_GTR_COCKPIT_RECORDS),
            {
                'description': 'The in-car view records by car model id (`g_cockpit_table` 0x060815b0): 0 SUPRA (PGC10), '
                '1 DIABLO (BCNR33), 2 PORSCHE (240ZG), 3 VETTE (KPGC110), 4 TESTA (300ZX), 5 VIPER (BNR32), 6 NSX '
                '(180SX), 7 RX7 (Silvia), 8 the Warrior. Read by `Race_InitCockpit` 0x0601c7f0 and '
                '`Cockpit_DrawNeedles` 0x0601e7a4'
            },
        )
        code_after_cockpit_records = (
            BytesBlock(
                length=TNFS_SATURN_GTR_SPEEDOMETER_TOPS_OFFSET
                - TNFS_SATURN_GTR_COCKPIT_RECORDS_OFFSET
                - 0x20 * TNFS_SATURN_GTR_COCKPIT_RECORDS
            ),
            {'description': 'Code and data between the cockpit records and the speedometer tops'},
        )
        speedometer_tops = (
            ArrayBlock(
                child=IntegerBlock(length=4, byte_order='big', is_signed=True),
                length=TNFS_SATURN_GTR_SPEEDOMETER_TOPS,
            ),
            {
                'description': "The speedometer's top by car model id 0..7 (`g_speedo_clamp` 0x06081864): 240 for 0 "
                'and 3 (PGC10, KPGC110), 180 for the others. Read by `Cockpit_DrawNeedles` 0x0601e7a4, which clamps the '
                "speed and the car's top speed to it (both in the display unit, km/h or mph) before the needle angle; "
                'it draws no speedometer for model 8 (the Warrior)'
            },
        )
        code_after_speedometer_tops = (
            BytesBlock(
                length=TNFS_SATURN_GTR_MODEL_POINTERS_OFFSET
                - TNFS_SATURN_GTR_SPEEDOMETER_TOPS_OFFSET
                - 4 * TNFS_SATURN_GTR_SPEEDOMETER_TOPS
            ),
            {'description': 'Code and data between the speedometer tops and the car model pointers'},
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
            BytesBlock(length=(REMAINING, 'up to the end of the file')),
            {'description': 'Code and data after the car AI pointers'},
        )


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
    inline_description = 'A picture of a list: its size and a PCX file'

    class Fields(DeclarativeCompoundBlock.Fields):
        size = (
            IntegerBlock(length=4, byte_order='big', programmatic_value=CountOf('pcx')),
            {'description': 'Length of `pcx` in bytes'},
        )
        pcx = (
            BytesBlock(length='size'),
            {'description': 'A PCX file (version 5, 8 bits, 256-colour palette at the end)'},
        )


class TnfsSaturnPcxList(DeclarativeCompoundBlock):
    block_description = (
        "Pictures of a car showcase page of Over Drivin' GT-R: `UIDATA/<car>GEN.DAT` (general), "
        '`<car>MEC.DAT` (mechanical), `<car>PER.DAT` (performance), named after the PC cars (`512` TESTA, `911` '
        'PORSCHE, `DIA` DIABLO, `NSX`, `RX7`, `SUP` SUPRA, `VIP` VIPER, `ZR1` VETTE). The first picture (320x224) is '
        'the page background with empty text boxes, the others are photos and panels (192x96, 304x84, 304x52...). '
        'The car cards are plain PCX files, `UIDATA/<maker>/MAIN.PCX`'
    )
    serializer = 'TnfsSaturnPcxListSerializer'

    class Fields(DeclarativeCompoundBlock.Fields):
        pictures = (
            ArrayBlock(
                child=TnfsSaturnPcxListEntry(),
                byte_length=(REMAINING, 'up to the end of the file'),
            ),
            {'description': 'The pictures, back to back'},
        )


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


# --- menu art: sprite banks, the palette table, the font (`UIDATA/FRONTEND.DAT`, `UIDATA/SHOWCASE.DAT`) ---

# VDP1 draw mode (CMDPMOD) bits 3-5: colour mode; 4 = 256-colour bank (8 bits per pixel), 0 = 16-colour bank (4 bits)
SATURN_DRAW_MODE_COLOR_MODE_MASK = 0x38
SATURN_DRAW_MODE_256_COLORS = 0x20
# a sprite's palette 0xFFFF (none): the loaders (0x060420f4, 0x06042474) make it runtime palette 0, colour RAM slot 0,
# which holds the palette of the screen's background picture
TNFS_SATURN_SPRITE_NO_PALETTE = 0xFFFF
# the palette table palette exported for the sprites without a palette: palette 0 (= palette 54), the blue
# background of the title screen (`uidata\redlayer.pcx`, PCX 16)
TNFS_SATURN_SCREEN_PALETTE = 0
# the palette table palette exported for the font glyphs: palette 6 (runtime palette 7, which the font loader
# 0x06041cd4 puts in every glyph entry), a green key colour and a grey ramp
TNFS_SATURN_FONT_PALETTE = 6
# `UIDATA/FRONTEND.DAT`: 4 sprite banks, then 19 PCX files
TNFS_SATURN_FRONTEND_SPRITE_BANKS = 4
TNFS_SATURN_FRONTEND_PICTURES = 19
# palette table palette of each PCX of `FRONTEND.DAT`. 0..12: the track maps (the three stages of the city, coast and
# forest open tracks by their look, then the 4 circuits), each its own: the descriptors (20 bytes from 0x060978e0: data, 3, x / y, runtime palette = table palette + 1) hold the first
# stage's palette of an open track (61, 64, 67 runtime), stages 2 and 3 use the next ones (checked visually: with the
# first stage's palette they come out garbled); 13 the Saturn pad (0x06098b08: 74), 14 the Arcade Racer wheel
# (0x06098b1c: 203), 15 the 3D pad (0x06098b44: 97); 16 `uidata\redlayer.pcx` (menu background, screen struct
# 0x060fe210 + 0x30: runtime palette 1), 17 `uidata\PRPLBKGD.pcx` (purple background, 0x060fe320 + 0x30: 60);
# 18 a plain slanted panel (descriptor at 0x06098230 without a palette; not found: it takes the screen's colours, the
# blue ones of palette 0 exported)
TNFS_SATURN_FRONTEND_PCX_PALETTES = list(range(60, 74)) + [202, 96, 0, 59, 0]
# other palettes a PCX is shown with, exported as `pcx_<index>_<palette>.png`: the menu background (PCX 16) of the
# screens set up by 0x06054648 (runtime palette 0x3a: green) and 0x06054790 / 0x060561a4 / the race loading screen
# 0x0604a304 (0x38: red); 0x060546f4 sets 0x37 = table palette 54, the same colours as palette 0
TNFS_SATURN_FRONTEND_PCX_TINTS = {16: [55, 57]}


class TnfsSaturnSpriteEntry(DeclarativeCompoundBlock):
    block_description = (
        'A sprite of a Saturn sprite bank: size, VDP1 draw mode, where its pixels are and its '
        'palette. The loaders (0x060420f4, 0x06042474) keep the entries in a table of sprites, add 1 to the '
        'palette (0xFFFF becomes 0) and a VRAM offset to `pixel_offset`; a sprite is drawn with VDP1 colour bank '
        'CMDCOLR = the colour RAM slot of its palette (0x06042868)'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        flags = (
            IntegerBlock(length=2, byte_order='big'),
            {
                'description': 'Bit 15 set in every entry; 0x8000 mostly, 0x8100, 0x8200, 0x8A00, 0x9400, 0x9E00, 0xA800, '
                '0xB200, 0xBC00 in a few (the sprites of an animation have increasing values). Unknown, the game ORs '
                'more bits into it at load',
                'is_unknown': True,
            },
        )
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
                'description': 'VDP1 draw mode word (CMDPMOD): 0x10A0 (colour mode 4: 256-colour bank, one byte per '
                'pixel) or 0x1080 (colour mode 0: 16-colour bank, 4 bits per pixel, the high nibble first) in every '
                'sprite (checked); bit 6 (SPD) clear in all: colour index 0 is transparent (the slanted edges of the '
                'cards and bars)'
            },
        )
        pixel_offset = (
            IntegerBlock(length=2, byte_order='big'),
            {
                'description': "Offset of the sprite's pixels in the bank's `pixels`, in 8-byte units (VDP1 CMDSRCA). "
                'Sprites may share pixels with different palettes (the coloured bars)'
            },
        )
        palette = (
            IntegerBlock(length=2, byte_order='big'),
            {
                'description': 'Palette: palette p of the palette table of `UIDATA/FRONTEND.DAT` (colours p x 256 ..; a '
                '4-bit sprite uses the first 16), at run time p + 1. 0xFFFF = none: the sprite takes the palette of '
                "the screen's background picture (colour RAM slot 0): the white title words, tinted with the screen"
            },
        )


class TnfsSaturnSpriteBank(DeclarativeCompoundBlock):
    block_description = (
        "Sprite bank of Over Drivin' GT-R's menus: the sprite entries, then the pixels of "
        'all of them (8 bits or 4 bits per pixel, rows of `width_8` x 8 pixels top to bottom). Each sprite ends '
        'within `pixels`, the last one at its end (checked)'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        num_sprites = (
            IntegerBlock(length=4, byte_order='big', programmatic_value=CountOf('sprites')),
            {'description': 'Number of sprites'},
        )
        sprites = (
            ArrayBlock(child=TnfsSaturnSpriteEntry(), length='num_sprites'),
            {'description': 'The sprites'},
        )
        pixels_size = (
            IntegerBlock(length=4, byte_order='big', programmatic_value=CountOf('pixels')),
            {'description': 'Length of `pixels` in bytes'},
        )
        pixels = (
            BytesBlock(length='pixels_size'),
            {'description': 'Pixels of every sprite'},
        )


class TnfsSaturnFontGlyph(DeclarativeCompoundBlock):
    block_description = (
        'A glyph of the menu font: a sprite entry whose width is in pixels. The font loader '
        '(0x06041cd4) keeps the width as the advance (one less for most characters), rounds it up to 8 and divides '
        'it by 8, rounds the height up '
        'to an even number and adds 7 to the palette. The text renderers (0x060428cc, 0x06042aa4, 0x06042d68, '
        '0x06042f88) copy the glyph pixels (4 bits, the high nibble first, nibble 0 not drawn) into an 8-bit VDP2 '
        "bitmap as colour base + nibble (0x90, or the caller's base): their colours are those of the bitmap's "
        'palette'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        flags = (
            IntegerBlock(length=2, byte_order='big'),
            {'description': '0x8000, 0x8100, 0x8200 or 0xA800. Unknown', 'is_unknown': True},
        )
        width = (
            IntegerBlock(length=2, byte_order='big'),
            {
                'description': 'Width in pixels; the pixels have rows of this width rounded up to 8 pixels (4 bytes)',
            },
        )
        height = (
            IntegerBlock(length=2, byte_order='big'),
            {'description': 'Height in pixels; the pixels have rows for this height rounded up to an even number'},
        )
        draw_mode = (
            IntegerBlock(length=2, byte_order='big'),
            {'description': 'VDP1 draw mode word: 0x1080 (16 colours, 4 bits per pixel) in every glyph'},
        )
        pixel_offset = (
            IntegerBlock(length=2, byte_order='big'),
            {'description': "Offset of the glyph's pixels in the font's `pixels`, in 8-byte units"},
        )
        palette = (
            IntegerBlock(length=2, byte_order='big'),
            {
                'description': 'Palette: 0 in every glyph (7 at run time: palette 6 of the palette table, a green key '
                'colour and a grey ramp). Not used by the text renderers'
            },
        )


class TnfsSaturnFontBank(DeclarativeCompoundBlock):
    block_description = (
        "The menu font of Over Drivin' GT-R: glyph entries, then their pixels. 448 glyphs: "
        'two fonts (a small one and a big italic one) of 224 characters each, 0x20..0xFF in the Mac OS Roman order '
        '(glyph = character - 0x20 + font x 224, the text renderers); missing characters are empty boxes'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        num_glyphs = (
            IntegerBlock(length=4, byte_order='big', programmatic_value=CountOf('glyphs')),
            {'description': 'Number of glyphs'},
        )
        glyphs = (
            ArrayBlock(child=TnfsSaturnFontGlyph(), length='num_glyphs'),
            {'description': 'The glyphs'},
        )
        pixels_size = (
            IntegerBlock(length=4, byte_order='big', programmatic_value=CountOf('pixels')),
            {'description': 'Length of `pixels` in bytes'},
        )
        pixels = (
            BytesBlock(length='pixels_size'),
            {'description': 'Pixels of every glyph, 4 bits each'},
        )


class TnfsSaturnPaletteTable(DeclarativeCompoundBlock):
    block_description = (
        "The palettes of Over Drivin' GT-R's menus: Saturn 16-bit RGB colours (bits 0-4 red, "
        '5-9 green, 10-14 blue), 256 per palette. The loader (0x06042198) reads them into its colour buffer from '
        'colour 256 on, so palette p is runtime palette p + 1 (the numbers the sprite loaders make), and copies '
        'runtime palettes 1..7 into colour RAM; the others are copied into a free colour RAM slot when drawn '
        '(0x06046e20). Colour 0 of most palettes is a key colour (green or magenta), transparent where drawn'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        num_colors = (
            IntegerBlock(
                length=4,
                byte_order='big',
                programmatic_value=lambda ctx: 256 * len(ctx.data('palettes')) + len(ctx.data('extra_colors')),
            ),
            {'description': 'Number of colours: 70416 (275 palettes and 16 colours)'},
        )
        palettes = (
            ArrayBlock(
                child=ArrayBlock(child=IntegerBlock(length=2, byte_order='big'), length=256),
                length=lambda ctx: ctx.data('num_colors') // 256,
            ),
            {'description': 'The palettes, 256 colours each'},
        )
        extra_colors = (
            ArrayBlock(child=IntegerBlock(length=2, byte_order='big'), length=lambda ctx: ctx.data('num_colors') % 256),
            {
                'description': 'Colours after the last whole palette: the first 16 colours of palette 43 again (16 '
                'colours of runtime palette 276, which no sprite names)'
            },
        )


def tnfs_saturn_palette_colors(table: dict, palette: int) -> List[int]:
    """The colours (Saturn 16-bit RGB) of palette `palette` of a `TnfsSaturnPaletteTable`, those of the colours after
    the last whole palette for the number after it"""
    if palette < len(table['palettes']):
        return list(table['palettes'][palette])
    if palette == len(table['palettes']):
        return list(table['extra_colors'])
    return []


class TnfsSaturnFrontendArt(DeclarativeCompoundBlock):
    block_description = (
        "`UIDATA/FRONTEND.DAT` of Over Drivin' GT-R (`UIDATA/GRONTEND.DAT` in a German "
        'version, 0x060563cc): the menu art, read in this order by 0x060563cc and 0x060568bc. Sprite bank 0 '
        '(76 sprites: titles, the car pictures, the track pictures, bars, flags, the first opponent pictures) goes '
        'to VDP1 VRAM, banks 1..3 to memory ("Swapped sprites", copied to VRAM when used; bank 1: the other '
        'opponent pictures). The PCX files have no palette: theirs are in `palettes` (see '
        '`TNFS_SATURN_FRONTEND_PCX_PALETTES`). The last bank is the title screen (0x060456b8)'
    )
    serializer = 'TnfsSaturnFrontendArtSerializer'

    class Fields(DeclarativeCompoundBlock.Fields):
        sprite_banks = (
            ArrayBlock(child=TnfsSaturnSpriteBank(), length=TNFS_SATURN_FRONTEND_SPRITE_BANKS),
            {
                'description': 'Sprite banks 0..3: 76, 6, 16 and 11 sprites. Bank 0: [0] GAME MODE, [1..9] the car '
                'pictures (PGC10, KPGC110, 240ZG, BCNR33, BNR32, 300ZX, 180SX, Silvia, Warrior), [10..16] the tracks, '
                '[73..75] the opponent pictures of PGC10, KPGC110 and 240ZG; bank 1: [0..4] those of BCNR33, BNR32, '
                "300ZX, 180SX and Silvia, [5] the opponents' pack"
            },
        )
        pictures = (
            ArrayBlock(child=TnfsSaturnPcxListEntry(), length=TNFS_SATURN_FRONTEND_PICTURES),
            {
                'description': 'PCX files without a palette (version 5, 8 bits), each after its size, no padding '
                '(0x0605e3c8: size, then that many bytes). Drawn into an 8-bit VDP2 bitmap, colour 0 transparent. '
                '[0..12] the track maps (144x156: by their look the three stages of the city, the coast and the forest '
                'open tracks, then the 4 circuits), [13] the '
                'Saturn pad, [14] the Arcade Racer wheel, [15] the 3D pad, [16] the menu background (320x224), [17] the '
                'purple background (320x224), [18] a plain panel (144x96)'
            },
        )
        palettes = (TnfsSaturnPaletteTable(), {'description': 'The palettes of the sprites and the PCX files'})
        font = (TnfsSaturnFontBank(), {'description': 'The menu font (0x06041cd4, 0x06041bdc)'})
        title_sprites = (
            TnfsSaturnSpriteBank(),
            {
                'description': "The title screen's sprites (0x060456b8): PRESENTS, the OVER DRIVIN' and GT-R logo, "
                'the copyright lines, PRESS START BUTTON and the NISSAN plate in 8 shades'
            },
        )


class TnfsSaturnSpriteBanks(DeclarativeCompoundBlock):
    block_description = (
        'Sprite banks back to back up to the end of the file: `UIDATA/SHOWCASE.DAT` of Over '
        "Drivin' GT-R (3 banks: the car showcase pages' titles, tabs, photos and panels; read by the showcase code "
        "near 0x0604d5dc). Its palettes are in `UIDATA/FRONTEND.DAT`'s palette table (palettes 16..252)"
    )
    serializer = 'TnfsSaturnSpriteBanksSerializer'

    class Fields(DeclarativeCompoundBlock.Fields):
        sprite_banks = (
            ArrayBlock(
                child=TnfsSaturnSpriteBank(),
                byte_length=(REMAINING, 'up to the end of the file'),
            ),
            {'description': 'The sprite banks'},
        )


def _walk_sprite_banks(buffer, length: int) -> List[int]:
    """End offsets (from the buffer's position) of the sprite banks back to back from the buffer's position, as long as
    they look like ones: an entry count, entries with bit 15 of `flags` and a draw mode 0x10xx, a pixel size within
    `length`"""
    start = buffer.tell()
    ends = []
    pos = 0
    try:
        while pos + 8 <= length:
            buffer.seek(start + pos)
            count = int.from_bytes(buffer.read(4), 'big')
            if count == 0 or count > 4096 or pos + 8 + 12 * count > length:
                break
            entries = buffer.read(12 * count)
            if any(not entries[12 * i] & 0x80 or entries[12 * i + 6] != 0x10 for i in range(count)):
                break
            pixels_size = int.from_bytes(buffer.read(4), 'big')
            end = pos + 8 + 12 * count + pixels_size
            if end > length:
                break
            ends.append(end)
            pos = end
        return ends
    finally:
        buffer.seek(start)


def tnfs_saturn_dat_block_class(buffer, length: int):
    """`TnfsSaturnFrontendArt` or `TnfsSaturnSpriteBanks` for a file of that layout (the buffer at its start), else
    None"""
    start = buffer.tell()
    try:
        ends = _walk_sprite_banks(buffer, length)
        if not ends:
            return None
        if ends[-1] == length:
            return TnfsSaturnSpriteBanks
        if len(ends) < TNFS_SATURN_FRONTEND_SPRITE_BANKS:
            return None
        pos = ends[TNFS_SATURN_FRONTEND_SPRITE_BANKS - 1]
        for _ in range(TNFS_SATURN_FRONTEND_PICTURES):
            buffer.seek(start + pos)
            head = buffer.read(7)
            if len(head) < 7 or head[4:7] != b'\x0a\x05\x01':
                return None
            pos += 4 + int.from_bytes(head[:4], 'big')
        buffer.seek(start + pos)
        pos += 4 + 2 * int.from_bytes(buffer.read(4), 'big')
        buffer.seek(start + pos)
        rest = _walk_sprite_banks(buffer, length - pos)
        return TnfsSaturnFrontendArt if len(rest) == 2 and pos + rest[-1] == length else None
    finally:
        buffer.seek(start)


def tnfs_saturn_sprite_pixels(bank: dict, index: int) -> Tuple[int, int, List[int]]:
    """(width, height, colour index per pixel) of sprite `index` of a `TnfsSaturnSpriteBank` (a glyph of a
    `TnfsSaturnFontBank`: its own width and height, the padding cut)"""
    glyph = 'glyphs' in bank
    entry = bank['glyphs' if glyph else 'sprites'][index]
    if glyph:
        width, height = entry['width'], entry['height']
        stride = (width + 7) // 8 * 8
    else:
        width = stride = entry['width_8'] * 8
        height = entry['height']
    start = entry['pixel_offset'] * 8
    if entry['draw_mode'] & SATURN_DRAW_MODE_COLOR_MODE_MASK == SATURN_DRAW_MODE_256_COLORS:
        indices = list(bank['pixels'][start : start + stride * height])
    else:
        indices = []
        for byte in bank['pixels'][start : start + stride * height // 2]:
            indices.append(byte >> 4)
            indices.append(byte & 0xF)
    indices.extend([0] * (stride * height - len(indices)))
    if stride != width:
        indices = [v for row in range(height) for v in indices[row * stride : row * stride + width]]
    return width, height, indices


def tnfs_saturn_sprite_image(bank: dict, index: int, colors: List[int]):
    """RGBA PIL image of sprite (or glyph) `index` of a bank with the given palette colours (Saturn 16-bit RGB; a 4-bit
    sprite uses the first 16), colour index 0 transparent unless the draw mode has SPD"""
    from PIL import Image

    width, height, indices = tnfs_saturn_sprite_pixels(bank, index)
    entry = bank['glyphs' if 'glyphs' in bank else 'sprites'][index]
    image = Image.new('P', (max(width, 1), max(height, 1)))
    if width and height:
        image.putdata(indices)
    image.putpalette(rgb_palette(saturn_colors_to_rgba(list(colors[:256]) + [0] * (256 - len(colors[:256])))))
    if not width or not height:
        image.info['transparency'] = bytes([0] * 256)
    elif not entry['draw_mode'] & SATURN_DRAW_MODE_INDEX_0_DRAWN:
        image.info['transparency'] = bytes([0] + [255] * 255)
    return image.convert('RGBA')


def tnfs_saturn_sprite_palette(entry: dict) -> int:
    """The palette table palette a sprite entry is exported with: its own, `TNFS_SATURN_SCREEN_PALETTE` for none"""
    return TNFS_SATURN_SCREEN_PALETTE if entry['palette'] == TNFS_SATURN_SPRITE_NO_PALETTE else entry['palette']


def tnfs_saturn_pcx_image(pcx: bytes, colors: List[int]):
    """RGBA PIL image of a palette-less PCX file of `FRONTEND.DAT` with the given palette colours, colour index 0
    transparent"""
    from PIL import Image

    indices = np.array(Image.open(BytesIO(pcx)), dtype=np.uint8)
    rgba = saturn_colors_to_rgba(list(colors) + [0] * (256 - len(colors)))
    pixels = rgba[indices]
    channels = np.stack([(pixels >> shift) & 0xFF for shift in (24, 16, 8, 0)], axis=-1).astype(np.uint8)
    channels[indices == 0, 3] = 0
    return Image.fromarray(channels, 'RGBA')


# --- RLE pictures (`UIDATA/ELOAD/<car>/<n>.BIN`, `UIDATA/ELOAD/LOAD.BIN`, `UIDATA/ECREDITS/0<n>.BIN`) ---

TNFS_SATURN_RLE_PICTURE_MAGIC = 0x0408
TNFS_SATURN_RLE_PICTURE_WIDTH = 320


class TnfsSaturnRlePicture(DeclarativeCompoundBlock):
    block_description = (
        "A 16-bit picture of Over Drivin' GT-R, word run-length encoded: the race loading "
        'pictures `UIDATA/ELOAD/<car>/1..7.BIN` (`WARRIOR/1..3.BIN`; 1 = 3 = 5 = 7 and 2 = 4 = 6 byte for byte), '
        '`UIDATA/ELOAD/LOAD.BIN` (0x0604a304) and the credits pages `UIDATA/ECREDITS/01..010.BIN` (0x06063d9c: '
        '`0%d.BIN`). Runs: a big-endian signed 16-bit n; n < 0: -n literal colours follow, n >= 0: the next '
        'colour n + 2 times. The colours (Saturn 16-bit RGB, bit 15 clear in every one) make rows of 320 pixels '
        'top to bottom; every file decodes to exactly `decoded_size` bytes and ends there (checked: 320x224)'
    )
    serializer = 'TnfsSaturnRlePictureSerializer'

    class Fields(DeclarativeCompoundBlock.Fields):
        magic = (
            IntegerBlock(length=2, byte_order='big', value_validator=Eq(TNFS_SATURN_RLE_PICTURE_MAGIC)),
            {'description': '0x0408 in every file'},
        )
        unknown = (
            IntegerBlock(length=2, byte_order='big'),
            {'description': '0 in every file', 'is_unknown': True},
        )
        decoded_size = (
            IntegerBlock(length=4, byte_order='big'),
            {'description': 'Size of the decoded picture in bytes: 0x23000 = 320 x 224 x 2 in every file'},
        )
        data = (
            BytesBlock(length=(REMAINING, 'up to the end of the file')),
            {'description': 'The runs'},
        )


def tnfs_saturn_rle_picture_colors(data: bytes, decoded_size: int) -> Tuple[List[int], int]:
    """(the decoded colours, bytes of `data` read) of the runs of a `TnfsSaturnRlePicture`, up to `decoded_size` bytes
    (or the end of `data`)"""
    import struct

    count = decoded_size // 2
    colors = []
    i = 0
    while len(colors) < count and i + 2 <= len(data):
        n = int.from_bytes(data[i : i + 2], 'big', signed=True)
        i += 2
        if n < 0:
            literal = min(-n, (len(data) - i) // 2)
            colors.extend(struct.unpack(f'>{literal}H', data[i : i + 2 * literal]))
            i += 2 * literal
        else:
            if i + 2 > len(data):
                break
            colors.extend([int.from_bytes(data[i : i + 2], 'big')] * (n + 2))
            i += 2
    return colors[:count], i


def tnfs_saturn_rle_picture_image(data: dict):
    """RGB PIL image of a `TnfsSaturnRlePicture`, 320 pixels wide (bit 15 of the colours, clear in every file, not
    used)"""

    colors, _ = tnfs_saturn_rle_picture_colors(data['data'], data['decoded_size'])
    width = TNFS_SATURN_RLE_PICTURE_WIDTH
    height = data['decoded_size'] // 2 // width
    colors = (colors + [0] * (width * height))[: width * height]
    return rgba_image(width, height, saturn_colors_to_rgba(colors)).convert('RGB')


def is_tnfs_saturn_rle_picture(data: bytes) -> bool:
    """The whole file: magic 0x0408 0, a decoded size of whole 320-pixel rows, runs ending at the end of the file
    exactly when the picture is complete"""
    if len(data) < 10 or int.from_bytes(data[:2], 'big') != TNFS_SATURN_RLE_PICTURE_MAGIC or data[2:4] != b'\0\0':
        return False
    decoded_size = int.from_bytes(data[4:8], 'big')
    if not decoded_size or decoded_size % (2 * TNFS_SATURN_RLE_PICTURE_WIDTH) or decoded_size > 0x100000:
        return False
    colors, read = tnfs_saturn_rle_picture_colors(data[8:], decoded_size)
    return len(colors) == decoded_size // 2 and read == len(data) - 8


# --- size-prefixed 8-bit RLE pictures (`HORIZON/*.IM`, `DASH/*.IM`, `DASH/EMEM3.DAT`) ---

# the most pixels per row and rows `Vdp2_LoadRleBitmap` takes: its line buffer and the VRAM lines are 512 bytes
TNFS_SATURN_RLE_IMAGE_MAX_SIZE = 512
# width, height and palette between a picture's size field and its runs
TNFS_SATURN_RLE_IMAGE_HEADER_SIZE = 4 + 4 + 512


class TnfsSaturnSizedRleImage(DeclarativeCompoundBlock):
    block_description = (
        "An 8-bit run-length encoded picture of Over Drivin' GT-R after its size (`TnfsSaturnRleImage`, the "
        "layout of the cockpit pictures): the files `HORIZON/*.IM` and `DASH/*.IM` (the size is the file's length, "
        'every file decodes completely: checked), the pictures of `DASH/EMEM3.DAT`. Colour 0 is green 0x03E0 in '
        'every file. Horizons `HORIZON/<prefix>RISE.IM`, `HORZ.IM`, `SET.IM` (the prefixes of `TRACKS/<prefix>.ALL`: '
        'AL1..AL3, CL1..CL3, CY1..CY3, TR1..TR4, and TR5, which has no track file): 512 wide, 78..152 rows, sky and '
        "land; RISE mostly with yellow and orange skies, SET red and purple ones; TR4's three files are the same "
        "(dark mountains under a night sky), so are TR5's (sand dunes, the sun in a blue sky). `Horizon_Load` "
        '0x060253c0 loads `HORIZON\\%sRISE.IM`, `%sHORZ.IM` or `%sSET.IM` (strings 0x06025354, 0x06025368, '
        '0x0602537c) by the time of day byte 0x060fd267: 0 RISE, 1 HORZ, 2 SET, any other value HORZ and the log '
        'line "error bad time of day"; `Vdp2_LoadRleBitmap`(2, 1, 224, 0): VRAM bank 2, 224 colours into palette 1. '
        "Bank 2 is the race screen's RBG0 rotation parameter A, which draws the screen's lines above 112 (parameter "
        'B, bank 3, the steering wheel below, also palette 1: its colours are 224..255). The horizons use colours '
        '1..223 (checked): no pixel has colour 0, which would be see-through (inferred: the two parameters share '
        "RBG0's one transparency switch, and the wheel's colour 0 is see-through). HUD `DASH/HUD0E.IM`..`HUD5E.IM`: "
        "352x240, the chase view HUD's six layouts, colour 0 around labels, a rev bar arc of coloured blocks and a "
        'dark box: 0 GEAR, TIME, DIST, POS.; 1 LAP for DIST; 2 and 3 RECORD and SPLIT for POS.; 4 and 5 two '
        'layouts one over the other (POS., TIME, DIST or LAP, GEAR). `Race_InitCockpit` 0x0601c7f0 loads '
        '`DASH\\HUD<n>E.IM` (string 0x06081730): 0 / 1 when the int at 0x060c3a4c is not 0, 2 / 3 when it is, 4 / '
        '5 in a split-screen race (`g_split_screen` 0x06082294), the odd one for track numbers (short 0x060fd25a) '
        'from 9; it also loads `DASH\\EMISC.DAT` (0x06081740, not parsed). `DASH/ETICKET.IM`: 320x224, a police '
        'officer holding out a speeding ticket, a patrol car behind (string 0x06080ea0, no direct code reference '
        "found). `DASH/EMEM2A.IM`, `2B`, `2C`: 320x224, yellow Japanese text on black: a problem with the console's "
        'own RAM (2A), the cartridge RAM (2B), an external device such as a floppy drive (2C): delete (initialise) every '
        'save on the save data management screen. Loaded by 0x060406a8 (strings 0x06096f90..0x06096fb0): '
        '`Vdp2_LoadRleBitmap`(1, 0, 256, 0, 0, file), the one of the int at 0x060bae94 (0, 1, 2). The E of '
        '`HUD<n>E`, `EMEM` and `EMISC` is replaced by the byte at 0x060fd263 before the file is opened. '
        'HUD0E, HUD3E and the EMEM pictures store every pixel as a run of one'
    )
    serializer = 'TnfsSaturnSizedRleImageSerializer'

    class Fields(DeclarativeCompoundBlock.Fields):
        size = (
            IntegerBlock(length=4, byte_order='big', programmatic_value=SizeOf('image') + 4),
            {'description': "Length of this field and `image` in bytes: the file's length for a `.IM` file"},
        )
        image = (
            TnfsSaturnRleImage(data_length=lambda ctx: ctx.data('../size') - 520),
            {'description': 'The picture'},
        )


def _is_tnfs_saturn_sized_rle_image_head(head: bytes, length: int) -> bool:
    """The first 8 bytes of a `TnfsSaturnSizedRleImage` with `length` bytes from its start: a size from the header's up
    to `length`, a width and height `Vdp2_LoadRleBitmap` takes"""
    if len(head) < 8:
        return False
    size = int.from_bytes(head[:4], 'big')
    width = int.from_bytes(head[4:6], 'big')
    height = int.from_bytes(head[6:8], 'big')
    return (
        TNFS_SATURN_RLE_IMAGE_HEADER_SIZE <= size <= length
        and 0 < width <= TNFS_SATURN_RLE_IMAGE_MAX_SIZE
        and 0 < height <= TNFS_SATURN_RLE_IMAGE_MAX_SIZE
    )


def _tnfs_saturn_sized_rle_image_end(data: bytes, pos: int) -> Optional[int]:
    """End of the `TnfsSaturnSizedRleImage` at `pos` of `data` when there is one: a size within `data`, a width and
    height `Vdp2_LoadRleBitmap` takes, runs that decode completely before the size's end, followed by 0..3 zero bytes"""
    if not _is_tnfs_saturn_sized_rle_image_head(data[pos : pos + 8], len(data) - pos):
        return None
    end = pos + int.from_bytes(data[pos : pos + 4], 'big')
    width = int.from_bytes(data[pos + 4 : pos + 6], 'big')
    height = int.from_bytes(data[pos + 6 : pos + 8], 'big')
    stream = data[pos + TNFS_SATURN_RLE_IMAGE_HEADER_SIZE : end]
    runs_end = tnfs_saturn_rle_end(stream, width, height)
    if runs_end is None or len(stream) - runs_end > 3 or any(stream[runs_end:]):
        return None
    return end


def is_tnfs_saturn_sized_rle_image(data: bytes) -> bool:
    """The whole file is one `TnfsSaturnSizedRleImage`"""
    return _tnfs_saturn_sized_rle_image_end(data, 0) == len(data)


def tnfs_saturn_sized_rle_image_ends(data: bytes) -> Optional[List[int]]:
    """End offsets of the `TnfsSaturnSizedRleImage`s back to back from the start of `data` when it is made of them up
    to its end, else None"""
    ends = []
    pos = 0
    while pos < len(data):
        pos = _tnfs_saturn_sized_rle_image_end(data, pos)
        if pos is None:
            return None
        ends.append(pos)
    return ends or None


def is_tnfs_saturn_sized_rle_image_list(buffer, length: int) -> bool:
    """The file (the buffer at its start, `length` bytes) is made of `TnfsSaturnSizedRleImage`s back to back"""
    start = buffer.tell()
    try:
        if not _is_tnfs_saturn_sized_rle_image_head(buffer.read(8), length):
            return False
        buffer.seek(start)
        return tnfs_saturn_sized_rle_image_ends(buffer.read(length)) is not None
    finally:
        buffer.seek(start)


class TnfsSaturnSizedRleImageList(DeclarativeCompoundBlock):
    block_description = (
        "Size-prefixed 8-bit pictures of Over Drivin' GT-R back to back up to the end of the file "
        '(`TnfsSaturnSizedRleImage`): `DASH/EMEM3.DAT`, two 320x224 pictures, every pixel a run of one: yellow '
        'Japanese text on black, a new save needs 52 free blocks, continue?, with YES and NO, YES highlighted in '
        'the first, NO in the second. 0x060406a8 reads both into memory (0x0605e7e8: the size, then the rest) and '
        'draws one or the other into VRAM bank 1 (0x0605e6f0, the decoding of `Vdp2_LoadRleBitmap` from memory, '
        '256 colours into palette 0) as the pad moves the choice'
    )
    serializer = 'TnfsSaturnSizedRleImageListSerializer'

    class Fields(DeclarativeCompoundBlock.Fields):
        images = (
            ArrayBlock(
                child=TnfsSaturnSizedRleImage(),
                byte_length=(REMAINING, 'up to the end of the file'),
            ),
            {'description': 'The pictures'},
        )
