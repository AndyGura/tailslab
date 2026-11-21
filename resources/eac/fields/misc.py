import math
from typing import Dict

from library.context import WriteContext
from library.read_blocks import IntegerBlock, CompoundBlock


class VectorBlock(CompoundBlock):
    """Components `axes` (one letter each) of type `child`; `normalized`: written as a unit vector (a zero vector as
    the last axis). The description is `description_prefix` + the description of `child`"""

    description_prefix = 'Vector, where each component is: '

    def __init__(self, child, axes: str = 'xyz', normalized=False, **kwargs):
        self.normalized = normalized
        super().__init__(fields=[(axis, child, {}) for axis in axes], **kwargs)

    @property
    def schema(self) -> Dict:
        schema = super().schema
        return {
            **schema,
            'block_description': self.description_prefix
            + schema['fields'][0]['schema']['block_description']
            + (', normalized' if self.normalized else ''),
            'inline_description': True,
        }

    # the write override only normalizes
    @property
    def field_by_field_io(self) -> bool:
        return not self.normalized

    def write(self, data, ctx: WriteContext = None, name: str = '') -> bytes:
        if self.normalized:
            axes = [axis for axis, _ in self.field_blocks]
            length = math.sqrt(sum(data[axis] ** 2 for axis in axes))
            if length == 0:
                data[axes[-1]] = 1.0
            elif length != 1:
                for axis in axes:
                    data[axis] /= length
        return super().write(data, ctx, name)


class Point2D(VectorBlock):
    description_prefix = 'Point in 2D space (x,y), where each coordinate is: '

    def __init__(self, child, normalized=False, **kwargs):
        super().__init__(child, axes='xy', normalized=normalized, **kwargs)


class Point3D(VectorBlock):
    description_prefix = 'Point in 3D space (x,y,z), where each coordinate is: '

    def __init__(self, child, normalized=False, **kwargs):
        super().__init__(child, axes='xyz', normalized=normalized, **kwargs)


class Quaternion(VectorBlock):
    description_prefix = (
        'Rotation quaternion (x,y,z,w), in the same axes as the positions next to it, where each component is: '
    )

    def __init__(self, child, **kwargs):
        super().__init__(child, axes='xyzw', **kwargs)


class RGBBlock(CompoundBlock):
    inline_description = 'Color RGB values'

    def __init__(self, **kwargs):
        child = IntegerBlock(length=1, is_signed=False)
        super().__init__(fields=[('r', child, {}), ('g', child, {}), ('b', child, {})], **kwargs)
