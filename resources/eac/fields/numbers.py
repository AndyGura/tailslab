import math
from typing import Dict

from library.read_blocks import DecimalBlock, FixedPointBlock, IntegerBlock


class AngleBlock:
    def wrap_angle(self, value):
        while value >= 2 * math.pi:
            value -= math.pi * 2
        while value < 0:
            value += math.pi * 2
        return value


class Nfs1Angle8(AngleBlock, IntegerBlock):
    @property
    def schema(self) -> Dict:
        super_schema = super().schema
        return {
            **super_schema,
            'min_value': float(math.pi * 2 * super_schema['min_value'] / 256),
            'max_value': float(math.pi * 2 * super_schema['max_value'] / 256),
            'value_interval': float(math.pi * 2 * super_schema['value_interval'] / 256),
            'block_description': 'EA games 8-bit angle. 0 means 0 degrees, 0x100 (max value + 1) means 360 degrees',
        }

    def __init__(self, **kwargs):
        super().__init__(length=1, is_signed=False, **kwargs)

    def from_raw(self, raw: int):
        return float((raw / 256) * (math.pi * 2))

    def to_raw(self, value) -> int:
        return min(round(256 * self.wrap_angle(value) / (math.pi * 2)), 0xFF)


class Nfs1Angle14(AngleBlock, IntegerBlock):
    @property
    def schema(self) -> Dict:
        super_schema = super().schema
        return {
            **super_schema,
            'min_value': float(math.pi * 2 * (super_schema['min_value'] & 0x3FFF) / 0x4000),
            'max_value': float(math.pi * 2 * (super_schema['max_value'] & 0x3FFF) / 0x4000),
            'value_interval': float(math.pi * 2 * (super_schema['value_interval'] & 0x3FFF) / 0x4000),
            'block_description': 'EA games 14-bit angle (little-endian), where first 2 bits unused or have unknown'
            ' data. 0 means 0 degrees, 0x4000 (max value + 1) means 360 degrees',
        }

    def __init__(self, **kwargs):
        super().__init__(length=2, byte_order='little', is_signed=False, **kwargs)

    def from_raw(self, raw: int):
        return float(((raw & 0x3FFF) / 0x4000) * (math.pi * 2))

    def to_raw(self, value) -> int:
        return min(round(0x4000 * self.wrap_angle(value) / (math.pi * 2)), 0x3FFF)


class IntegerAngleBlock(IntegerBlock):
    """Angle kept as the plain integer the game stores, `full_turn` units per 360 degrees. Unlike `Nfs1Angle8` /
    `Nfs1Angle14` the value is not converted to radians: only the GUI shows it as an angle (`angle_full_turn`)"""

    def __init__(self, full_turn: int, **kwargs):
        super().__init__(**kwargs)
        self.full_turn = full_turn

    @property
    def schema(self) -> Dict:
        super_schema = super().schema
        return {
            **super_schema,
            'angle_full_turn': self.full_turn,
            'block_description': f'{super_schema["block_description"]}, angle: {hex(self.full_turn)} means 360 degrees',
        }


class Nfs1TimeField(IntegerBlock):
    @property
    def schema(self) -> Dict:
        super_schema = super().schema
        return {
            **super_schema,
            'min_value': float(super_schema['min_value'] / 60),
            'max_value': float(super_schema['max_value'] / 60),
            'value_interval': float(super_schema['value_interval'] / 60),
            'block_description': f'TNFS time field. {super_schema["block_description"]}, '
            'equals to amount of ticks (amount of seconds * 60)',
        }

    def from_raw(self, raw: int):
        return float(raw) / 60

    def to_raw(self, value) -> int:
        return int(value * 60)


# Number fields of a decompiled struct by their C type (`byte_order='big'` and the other block arguments pass through)
def u8(**kwargs):
    return IntegerBlock(length=1, **kwargs)


def u16(**kwargs):
    return IntegerBlock(length=2, **kwargs)


def s16(**kwargs):
    return IntegerBlock(length=2, is_signed=True, **kwargs)


def u32(**kwargs):
    return IntegerBlock(length=4, **kwargs)


def s32(**kwargs):
    return IntegerBlock(length=4, is_signed=True, **kwargs)


def f32(**kwargs):
    return DecimalBlock(length=4, **kwargs)


# 4-byte fixed point numbers: 16.16 signed / unsigned, 24.8 signed
def fixed16(**kwargs):
    return FixedPointBlock(length=4, fraction_bits=16, is_signed=True, **kwargs)


def ufixed16(**kwargs):
    return FixedPointBlock(length=4, fraction_bits=16, is_signed=False, **kwargs)


def fixed8(**kwargs):
    return FixedPointBlock(length=4, fraction_bits=8, is_signed=True, **kwargs)
