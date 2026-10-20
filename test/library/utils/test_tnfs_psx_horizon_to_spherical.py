import math
import os
import tempfile
import unittest

import numpy as np
from PIL import Image

from library.utils.nfs1_panorama_to_spherical import OUT_HEIGHT, OUT_WIDTH
from library.utils.tnfs_psx_horizon_to_spherical import (
    PSX_FOCAL_PX,
    horizon_info_path,
    tnfs_psx_horizon_to_spherical,
)
from resources.eac.psx import PsxHorizonSettings

# ZAL1A.INF: ring from -81 to +31 px of the 320x240 screen around the horizon line, no mirror
SETTINGS = PsxHorizonSettings(0, 0, 0, 0, 0, 48, 0, 96, (50, 58, 58), (57, 65, 65), 1, 30, -50, 112, 0)


def row_of_screen_y(screen_y):
    """Output row of a screen px offset below the horizon line"""
    elevation = math.atan(-screen_y / PSX_FOCAL_PX)
    return int((0.5 - elevation / math.pi) * OUT_HEIGHT)


def column_of_heading(degrees):
    return int(((degrees + 180) % 360) / 360 * OUT_WIDTH)


class TestPsxHorizonToSpherical(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = os.path.join(self.tmp.name, 'spherical.png')

    def tearDown(self):
        self.tmp.cleanup()

    def _render(self, sectors, settings=SETTINGS):
        tnfs_psx_horizon_to_spherical(sectors, settings, self.out)
        return np.asarray(Image.open(self.out)).astype(int)

    @staticmethod
    def _sectors():
        # sector i: red = 20 * i, left half green 0, right half green 255, blue 200
        sectors = []
        for i in range(8):
            pixels = np.zeros((10, 8, 4), dtype=np.uint8)
            pixels[..., 0] = 20 * i
            pixels[:, 4:, 1] = 255
            pixels[..., 2] = 200
            pixels[..., 3] = 255
            sectors.append(Image.fromarray(pixels, 'RGBA'))
        return sectors

    def test_sectors_of_22_5_degrees_from_heading_0(self):
        out = self._render(self._sectors())
        self.assertEqual(out.shape, (OUT_HEIGHT, OUT_WIDTH, 4))
        eye = OUT_HEIGHT // 2
        for sector in range(16):
            # left part of the sector: its image's left half
            pixel = out[eye, column_of_heading(sector * 22.5 + 3)]
            self.assertEqual(pixel[0], 20 * (sector % 8), sector)
            self.assertEqual(pixel[1], 0)
            self.assertEqual(out[eye, column_of_heading(sector * 22.5 + 19)][1], 255)

    def test_mirror_flag_mirrors_the_second_half(self):
        out = self._render(self._sectors(), SETTINGS._replace(mirror=1))
        eye = OUT_HEIGHT // 2
        for sector in range(8, 16):
            left = out[eye, column_of_heading(sector * 22.5 + 3)]
            self.assertEqual(left[0], 20 * (7 - sector % 8), sector)
            # the image flipped: its right half first
            self.assertEqual(left[1], 255)

    def test_vertical_placement(self):
        out = self._render(self._sectors())
        column = column_of_heading(3)
        # above the gradient: colour top; ring from -81 px to 31 px; fade to black over 81 px below it
        self.assertEqual(out[row_of_screen_y(-106) - 2, column].tolist(), [50, 58, 58, 255])
        gradient = out[row_of_screen_y(-93), column]
        self.assertTrue(50 < gradient[0] < 57)
        self.assertEqual(out[row_of_screen_y(-79), column][3], 255)
        self.assertEqual(out[row_of_screen_y(-79), column][0], 0)
        self.assertEqual(out[row_of_screen_y(29), column][0], 0)
        # below the ring: the texel of hrz0 (red 0, green 0, blue 200) fading to the average of the ring's bottom line
        # (red 70 = mean of 20 * i, green 255 * 3 / 7: columns 0..6 of each sector, 3 of them in the right half)
        ground = [70, round(255 * 3 / 7), 200, 255]
        self.assertTrue(out[row_of_screen_y(33), column][0] < 5)
        self.assertEqual(out[row_of_screen_y(33), column][2], 200)
        middle = out[row_of_screen_y(70), column]
        self.assertTrue(25 < middle[0] < 45 and 40 < middle[1] < 70, middle)
        self.assertEqual(out[row_of_screen_y(115), column].tolist(), ground)
        self.assertEqual(out[OUT_HEIGHT - 1, column].tolist(), ground)
        self.assertEqual(out[OUT_HEIGHT - 1, 0].tolist(), ground)

    def test_needs_8_sectors(self):
        with self.assertRaises(ValueError):
            self._render(self._sectors()[:7])


class TestHorizonInfoPath(unittest.TestCase):
    def test_same_name_any_case_and_german_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ['ZAL1A.INF', 'zcy1b.inf']:
                open(os.path.join(tmp, name), 'w').close()
            self.assertEqual(horizon_info_path(os.path.join(tmp, 'ZAL1A.PSH')), os.path.join(tmp, 'ZAL1A.INF'))
            self.assertEqual(horizon_info_path(os.path.join(tmp, 'ZCY1B.PSH')), os.path.join(tmp, 'zcy1b.inf'))
            self.assertEqual(horizon_info_path(os.path.join(tmp, 'ZGAL1A.PSH')), os.path.join(tmp, 'ZAL1A.INF'))
            self.assertIsNone(horizon_info_path(os.path.join(tmp, 'ZAL1R.PSH')))


if __name__ == '__main__':
    unittest.main()
