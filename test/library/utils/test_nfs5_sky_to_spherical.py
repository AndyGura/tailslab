import math
import os
import struct
import tempfile
import unittest

import numpy as np

from library.utils.nfs5_sky_to_spherical import (
    Nfs5SkyLayer,
    Nfs5SkySettings,
    dome_hits,
    is_nfs5_sky_archive,
    nfs5_sky_to_spherical,
    parse_nfs5_sky_text,
    read_nfs5_sky_settings,
)
from library.utils.sky_spherical import direction_to_pixel
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


CELLS = tuple(range(8)) * 2


def settings(cells=CELLS, rotation=0.0, colour_start=0, columns=4, rows=2, dome=(0.0, 1000.0, 0.000244140625, 100.0)):
    return Nfs5SkySettings(rotation, colour_start, columns, rows, -100.0, 400.0, cells, *dome)


def sky_bin(s=None, size=3544):
    s = s or settings()
    data = struct.pack(
        '<IfIIIff',
        9,
        s.horizon_rotation,
        s.horizon_colour_start,
        s.horizon_cell_columns,
        s.horizon_cell_rows,
        s.horizon_bottom,
        s.horizon_height,
    )
    data += struct.pack('<16H', *s.horizon_cells)
    data += struct.pack('<4f', s.dome_rotation, s.dome_size, s.dome_curvature, s.dome_height)
    return data + bytes(8) + b'\xcb' * (size - len(data) - 8)


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
        self.assertEqual(read_nfs5_sky_settings(data), settings())
        block = Nfs5SkyBin()
        values = block.unpack_from_bytes(data)
        self.assertEqual(values['dome_size'], 1000.0)
        self.assertEqual(block.pack(values), data)

    def test_other_bin_format_is_refused(self):
        self.assertIsNone(read_nfs5_sky_settings(struct.pack('<I', 944) + bytes(200)))

    def test_sky_archive_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            sky = os.path.join(tmp, 'GameData', 'Track', 'Sky')
            os.makedirs(sky)
            open(os.path.join(sky, 'forest.txt'), 'w').close()
            self.assertTrue(is_nfs5_sky_archive(os.path.join(sky, 'Forest.fsh')))
            self.assertFalse(is_nfs5_sky_archive(os.path.join(sky, 'Alps.fsh')))
            self.assertFalse(is_nfs5_sky_archive(os.path.join(sky, 'Forest.fsh') + '__children/0/item/data'))


class TestNfs5Dome(unittest.TestCase):
    def test_zenith_hits_the_grid_centre(self):
        fi, fj, hit = dome_hits(np.array([[0.0, 1.0, 0.0]]), settings())
        self.assertTrue(hit[0])
        self.assertAlmostEqual(fi[0], 7.5)
        self.assertAlmostEqual(fj[0], 7.5)

    def test_hit_lies_on_the_paraboloid(self):
        # towards +Z, rotation 0: a = z, b = x; the hit (a, y) satisfies y = h - k a^2
        d = np.array([[0.0, math.sin(0.3), math.cos(0.3)]])
        fi, fj, hit = dome_hits(d, settings())
        a = fi[0] * 1000 / 15 - 500
        t = a / d[0, 2]
        self.assertAlmostEqual(t * d[0, 1], 100 - 0.000244140625 * a * a, places=6)
        self.assertAlmostEqual(fj[0], 7.5)
        # +X: b = x, column j = (S/2 - b) / step goes down
        fi, fj, hit = dome_hits(np.array([[math.cos(0.3), math.sin(0.3), 0.0]]), settings())
        self.assertAlmostEqual(fi[0], 7.5)
        self.assertLess(fj[0], 7.5)

    def test_rotation_quarter_turn(self):
        # R = 0.25: x = a, z = -b
        fi, fj, hit = dome_hits(
            np.array([[math.cos(0.3), math.sin(0.3), 0.0]]), settings(dome=(0.25, 1000.0, 0.000244140625, 100.0))
        )
        self.assertGreater(fi[0], 7.5)
        self.assertAlmostEqual(fj[0], 7.5)

    def test_rays_beyond_the_grid_miss(self):
        fi, fj, hit = dome_hits(np.array([[0.0, 0.05, 1.0]]) / math.hypot(0.05, 1.0), settings())
        self.assertFalse(hit[0])


class TestNfs5SkyToSpherical(unittest.TestCase):
    W, H = 256, 256

    def render(self, horz, cells=CELLS, sky=(0, 0, 255), hzcl=None, colour_start=0):
        st1a = np.zeros((16, 16, 4))
        st1a[..., :3] = sky
        st1a[..., 3] = 255
        textures = {'st1a': st1a, 'horz': horz}
        if hzcl is not None:
            textures['hzcl'] = hzcl
        return nfs5_sky_to_spherical(
            [Nfs5SkyLayer('st1a', None, 1, 1)],
            textures,
            settings(cells, colour_start=colour_start),
            width=self.W,
            height=self.H,
        )

    def row_of_elevation(self, degrees):
        return int((0.5 - math.radians(degrees) / math.pi) * self.H)

    def test_sky_map_pixel_is_vertex_colour(self):
        # pixel (column j, row i) is vertex (i, j): red = 16 * row, green = 16 * column, interpolated over the grid
        sky = np.zeros((16, 16, 4))
        sky[..., 3] = 255
        sky[..., 0] = 16 * np.arange(16)[:, None]
        sky[..., 1] = 16 * np.arange(16)[None, :]
        out = nfs5_sky_to_spherical(
            [Nfs5SkyLayer('sky', None, 1, 1)], {'sky': sky}, settings(), width=self.W, height=self.H
        )
        for direction in ((0, 0.4, 1), (1, 0.4, 0), (-0.3, 0.6, -1)):
            col, row = direction_to_pixel(direction, self.W, self.H)
            col, row = int(col) % self.W, int(row)
            # the ray through that pixel's centre
            h = ((col + 0.5) / self.W - 0.5) * 2 * math.pi
            e = (0.5 - (row + 0.5) / self.H) * math.pi
            d = np.array([[math.sin(h) * math.cos(e), math.sin(e), math.cos(h) * math.cos(e)]])
            fi, fj, hit = dome_hits(d, settings())
            self.assertTrue(hit[0])
            self.assertAlmostEqual(out[row, col, 0], 16 * fi[0], places=6)
            self.assertAlmostEqual(out[row, col, 1], 16 * fj[0], places=6)
        # nothing beyond the grid square: the clear colour (black) near the horizon
        self.assertEqual(out[self.row_of_elevation(2), self.W // 2, :3].tolist(), [0, 0, 0])

    def test_band_between_bottom_and_top_heights(self):
        horz = np.zeros((256, 64, 4))
        horz[..., 0] = 255
        horz[..., 3] = 255
        out = self.render(horz)
        # the top at y 300 on a cylinder of radius 400 (a little closer between the quads' points)
        top = math.degrees(math.atan(300 / 400))
        c = self.W // 2
        self.assertEqual(out[self.row_of_elevation(top - 3), c].tolist()[:3], [255, 0, 0])
        self.assertNotEqual(out[self.row_of_elevation(top + 3), c].tolist()[:3], [255, 0, 0])
        # below the band: the band's bottom colour
        self.assertEqual(out[self.H - 1, 0].tolist()[:3], [255, 0, 0])

    def test_cells_and_mirror(self):
        # cell 0 (column 0 of 4, row 0): red on its left half, green on its right; the other cells white
        horz = np.full((256, 64, 4), 255.0)
        horz[:128, :8, :3] = [255, 0, 0]
        horz[:128, 8:16, :3] = [0, 255, 0]
        cells = (0, 0x100) + (1,) * 14
        out = self.render(horz, cells=cells)
        row = self.H // 2
        c = self.W // 2
        quad = self.W // 16
        # quad 0 starts at +Z (rotation 0) and runs right (towards +X): red then green
        self.assertEqual(out[row, c + 2].tolist()[:3], [255, 0, 0])
        self.assertEqual(out[row, c + quad - 3].tolist()[:3], [0, 255, 0])
        # quad 1 is the same cell mirrored: green then red
        self.assertEqual(out[row, c + quad + 2].tolist()[:3], [0, 255, 0])
        self.assertEqual(out[row, c + 2 * quad - 3].tolist()[:3], [255, 0, 0])
        # quad 2 shows cell 1
        self.assertEqual(out[row, c + 2 * quad + 8].tolist()[:3], [255, 255, 255])

    def test_hzcl_tints_top_and_bottom(self):
        horz = np.full((256, 64, 4), 255.0)
        hzcl = np.full((2, 16, 4), 255.0)
        hzcl[0, :, :3] = [255, 0, 0]  # top vertices red
        hzcl[1, :, :3] = [0, 0, 255]  # bottom vertices blue
        hzcl[0, 5, :3] = [0, 255, 0]  # point 0 with colour start 5: green at the top
        out = self.render(horz, hzcl=hzcl, colour_start=5)
        c = self.W // 2
        quad = self.W // 16
        top = math.degrees(math.atan(300 / 400))
        near_point_0 = out[self.row_of_elevation(top - 1), c + 1]
        self.assertGreater(near_point_0[1], near_point_0[0])
        mid_quad_3 = out[self.row_of_elevation(top - 1), c + 3 * quad + quad // 2]
        self.assertGreater(mid_quad_3[0], 200)
        bottom = out[self.row_of_elevation(-13), c + 3 * quad + quad // 2]
        self.assertGreater(bottom[2], 200)
        self.assertLess(bottom[0], 60)
