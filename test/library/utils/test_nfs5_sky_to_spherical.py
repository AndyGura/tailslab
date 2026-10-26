import math
import os
import struct
import tempfile
import unittest

import numpy as np

from library.utils.nfs5_sky_to_spherical import (
    Nfs5SkyLayer,
    Nfs5SkySettings,
    horizon_strips,
    is_nfs5_sky_archive,
    nfs5_sky_to_spherical,
    parse_nfs5_sky_text,
    read_nfs5_sky_settings,
)
from resources.eac.maps.nfs5_sky import Nfs5SkyBin

MULTINORMAL = """BEGIN
#Computer capability
\tHIGH
#sky level type
\tMULTINORMAL
#Does this layer block the sun
NO
# sky map RGB (or ARGB) cannot choose "noise
\tst1a
\tsc1a
\tnone
#X Scale Factors
\t1
\t2
\t0
#Y Scale Factors
\t1
\t3
\t0
#move ratio
\t400
#wind speed
\t0\n\t2\n\t0
#wind direction
\t90\n\t40\n\t0
#warp speed
\t0
#warp amount
\t0
\tst1b\n\tsc1b\n\tnone\n\t1\n\t2\n\t0\n\t1\n\t2\n\t0\n\t400\n\t0\n\t2\n\t0\n\t90\n\t40\n\t0\n\t0\n\t0
# CLOUD TEXTURES
\tflat
\tcc1a
\tnone
END
BEGIN
\tMEDIUM\n\tMULTINORMAL\nNO
END
"""

BASIC = """BEGIN
#Computer capability
\tHIGH
#sky level type
\tbasic
NO
\tst1a
# sky map alpha must be none, or noise, speed
\tnone
#cloud texture
\tflat
#X and Y Scale Factors
\t.5
\t.5
\t0\n\t0\n\t90\n\t0\n\t0
\tst1a\n\tnone\n\tflat\n\t.5\n\t.5\n\t0\n\t0\n\t90\n\t0\n\t0
END
"""


def sky_bin(segments=4, strips=2, bottom=-100.0, top=300.0, radius=1000.0, table=(0, 1, 2, 3, 4, 5, 6, 7)):
    header = struct.pack('<IfIIIff', 9, 0.5, 0, segments, strips, bottom, top)
    header += struct.pack('<8H', *table) + struct.pack('<8H', *table)
    header += struct.pack('<ffffII', 0.8, radius, 0.0002, 125.0, 0, 0)
    return header + b'\xcb' * 32


class TestNfs5SkyFiles(unittest.TestCase):
    def test_multinormal_text_region_a_of_the_first_level(self):
        # the textures (flat, cc1a, none) make the layers
        self.assertEqual(
            parse_nfs5_sky_text(MULTINORMAL),
            [Nfs5SkyLayer('st1a', None, 1.0, 1.0), Nfs5SkyLayer('sc1a', 'cc1a', 2.0, 3.0)],
        )

    def test_basic_text(self):
        self.assertEqual(parse_nfs5_sky_text(BASIC), [Nfs5SkyLayer('st1a', None, 0.5, 0.5)])

    def test_bin_settings_and_round_trip(self):
        data = sky_bin()
        self.assertEqual(
            read_nfs5_sky_settings(data), Nfs5SkySettings(4, 2, -100.0, 300.0, 1000.0, (0, 1, 2, 3, 4, 5, 6, 7))
        )
        block = Nfs5SkyBin()
        self.assertEqual(block.pack(block.unpack_from_bytes(data)), data)

    def test_other_bin_format_is_refused(self):
        self.assertIsNone(read_nfs5_sky_settings(struct.pack('<I', 944) + bytes(200)))

    def test_horizon_strips_of_horz(self):
        textures = {'hor0': np.full((256, 4, 4), 2.0), 'horz': np.full((256, 4, 4), 1.0), 'st1a': np.zeros((4, 4, 4))}
        strips = horizon_strips(textures, 2)
        self.assertEqual([s.shape[0] for s in strips], [128] * 2)
        self.assertEqual([s[0, 0, 0] for s in strips], [1.0, 1.0])
        self.assertEqual(len(horizon_strips(textures, 1)), 1)

    def test_sky_archive_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            sky = os.path.join(tmp, 'GameData', 'Track', 'Sky')
            os.makedirs(sky)
            open(os.path.join(sky, 'forest.txt'), 'w').close()
            self.assertTrue(is_nfs5_sky_archive(os.path.join(sky, 'Forest.fsh')))
            self.assertFalse(is_nfs5_sky_archive(os.path.join(sky, 'Alps.fsh')))
            self.assertFalse(is_nfs5_sky_archive(os.path.join(sky, 'Forest.fsh') + '__children/0/item/data'))


class TestNfs5SkyToSpherical(unittest.TestCase):
    W, H = 256, 256

    def render(self, horz, table=(0, 1, 2, 3, 4, 5, 6, 7), sky=(0, 0, 255)):
        st1a = np.zeros((16, 16, 4))
        st1a[..., :3] = sky
        st1a[..., 3] = 255
        settings = Nfs5SkySettings(4, 2, -100.0, 300.0, 1000.0, table)
        return nfs5_sky_to_spherical(
            [Nfs5SkyLayer('st1a', None, 1, 1)], {'st1a': st1a, 'horz': horz}, settings, width=self.W, height=self.H
        )

    def row_of_elevation(self, degrees):
        return int((0.5 - math.radians(degrees) / math.pi) * self.H)

    def test_band_between_bottom_and_top_heights(self):
        horz = np.zeros((256, 64, 4))
        horz[..., 0] = 255
        horz[..., 3] = 255
        horz[127, :, 3] = 0
        horz[255, :, 3] = 0
        out = self.render(horz)
        top = math.degrees(math.atan(300 / 1000))
        self.assertEqual(out[self.row_of_elevation(top + 3), 0].tolist()[:3], [0, 0, 255])
        self.assertEqual(out[self.row_of_elevation(top - 3), 0].tolist()[:3], [255, 0, 0])
        # below the band: one flat colour, the mean of the last drawn row (the padding row is not drawn)
        self.assertEqual(out[self.H - 1, 0].tolist()[:3], [255, 0, 0])

    def test_flat_colour_below_the_band(self):
        horz = np.zeros((256, 64, 4))
        horz[..., 3] = 255
        horz[:, :32, 0] = 200
        horz[:, 32:, 2] = 100
        horz[127, :, 3] = 0
        horz[255, :, 3] = 0
        out = self.render(horz)
        self.assertEqual(out[self.H - 1].tolist()[0][:3], [100, 0, 50])
        self.assertTrue((out[self.H - 1, :, :3] == [100, 0, 50]).all())

    def test_sky_map_spans_the_dome_once_and_texture_repeats(self):
        # sky map: left half (u < 0.5, towards -X) red, right half blue; texture: white with a black column
        sky = np.zeros((16, 16, 4))
        sky[..., 3] = 255
        sky[:, :8, 0] = 255
        sky[:, 8:, 2] = 255
        texture = np.full((4, 4, 4), 255.0)
        out = nfs5_sky_to_spherical(
            [Nfs5SkyLayer('sky', 'tex', 2, 2)], {'sky': sky, 'tex': texture}, None, width=self.W, height=self.H
        )
        row = self.row_of_elevation(30)
        self.assertEqual(out[row, self.W // 2].tolist()[:3], [0, 0, 255])  # +X
        self.assertEqual(out[row, 0].tolist()[:3], [255, 0, 0])  # -X

    def test_segments_strips_and_mirror(self):
        # strip 0 red on its left half (green right), strip 1 white
        horz = np.zeros((256, 64, 4))
        horz[..., 3] = 255
        horz[:128, :32, 0] = 255
        horz[:128, 32:, 1] = 255
        horz[128:, :, :3] = 255
        out = self.render(horz, table=(0, 0x100, 1, 1, 0, 0, 0, 0))
        row = self.H // 2
        c = self.W // 2
        # segment 0 starts at the centre column and runs right: red then green
        self.assertEqual(out[row, c + 4].tolist()[:3], [255, 0, 0])
        self.assertEqual(out[row, c + self.W // 8 + 4].tolist()[:3], [0, 255, 0])
        # segment 1 is the same strip mirrored: green then red
        self.assertEqual(out[row, c + self.W // 4 + 4].tolist()[:3], [0, 255, 0])
        self.assertEqual(out[row, c + self.W // 4 + self.W // 8 + 4].tolist()[:3], [255, 0, 0])
        # segment 2 shows strip 1
        self.assertEqual(out[row, 4].tolist()[:3], [255, 255, 255])
