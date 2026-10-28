import math
import os
import tempfile
import unittest

import numpy as np

from library.utils.eac_horizon_to_spherical import (
    horizon_archive_kind,
    nfs2se_sky,
    nfs3_sky,
    nfs4_sky,
    parse_sun_text,
    render_horizon_sky,
    ring_colors,
)
from resources.eac.horizons import (
    parse_nfs2se_horizon_settings,
    parse_nfs3_horizon_settings,
    parse_nfs4_sky_settings,
)

SAMPLES = os.path.join(os.path.dirname(__file__), '..', '..', 'samples')
WIDTH, HEIGHT = 1024, 512


def read_sample(name):
    with open(os.path.join(SAMPLES, name)) as f:
        return f.read()


def column(heading_turns):
    """Output column of a heading (turns clockwise from +Z): +X (0.25) at the centre"""
    return int(((heading_turns + 0.25) % 1.0) * WIDTH)


def row(elevation):
    return int((0.5 - elevation / math.pi) * HEIGHT)


def strips(heights=(32,) * 8):
    """Strip i: solid red 20 * i + 10, opaque"""
    result = []
    for i, height in enumerate(heights):
        pixels = np.zeros((height, 16, 4))
        pixels[..., 0] = 20 * i + 10
        pixels[..., 3] = 255
        result.append(pixels)
    return result


def solid(value, size=8, alpha=255):
    pixels = np.full((size, size, 4), float(value))
    pixels[..., 3] = alpha
    return pixels


class TestRingColors(unittest.TestCase):
    def test_sun_around_vertex_0_opposite_around_7_8(self):
        colors = ring_colors((255, 0, 0), (0, 0, 255))
        for k in (0, 15, 16):
            self.assertEqual(list(colors[k]), [255, 0, 0])
        np.testing.assert_array_equal(colors[7], colors[8])
        # 7/8 of the way, in 16.16 steps
        self.assertEqual(list(colors[7]), [((255 << 16) - 7 * 255 * 0x2000) >> 16, 0, (7 * 255 * 0x2000) >> 16])
        np.testing.assert_array_equal(colors[1], colors[14])


class TestNfs2SeSky(unittest.TestCase):
    def setUp(self):
        # 3TR02.HRZ: angle 300 degrees, mirror, flat projection 1000, base -750, height 1250, middle 735,
        # pixmap 600..960; no clouds (track 0)
        self.settings = parse_nfs2se_horizon_settings(read_sample('NFS2SE_3TR02.HRZ'))
        self.out = render_horizon_sky(nfs2se_sky(self.settings, strips(), None, 0), WIDTH, HEIGHT).astype(int)

    def test_sector_k_from_heading_angle_plus_k_sixteenths(self):
        rotation = ((300 << 16) // 360) / 65536
        eye = HEIGHT // 2
        for k in range(16):
            strip = k if k < 8 else 15 - k
            self.assertEqual(self.out[eye, column(rotation + (k + 0.5) / 16), 0], 20 * strip + 10, k)

    def test_pixmap_rows_flat_projection(self):
        # 16.16 fractions of the height: 0x10000 // 1250 = 52
        bottom = -750 + 1250 * (600 * 52) / 65536
        top = -750 + 1250 * (32 * ((960 * 52 - 600 * 52) // 32) + 600 * 52) / 65536
        c = column(0.4)
        self.assertEqual(self.out[row(math.atan(bottom / 1000)) - 2, c, 0], self.out[HEIGHT // 2, c, 0])
        above = self.out[row(math.atan(top / 1000)) - 2, c]
        self.assertNotEqual(above[0], self.out[HEIGHT // 2, c, 0])

    def test_sky_and_earth(self):
        c = column(0.4)
        # above the band: the clear colour, the SKY top colour
        self.assertEqual(list(self.out[row(math.radians(60)), c, :3]), [255, 122, 66])
        # just above the base: EARTH base colour
        self.assertEqual(list(self.out[row(math.atan(-740 / 1000)), c, :3]), [132, 117, 115])

    def test_black_horizon(self):
        out = render_horizon_sky(nfs2se_sky(self.settings._replace(black_horizon=1), strips(), None, 0), 64, 32)
        self.assertEqual(out[..., :3].max(), 0)

    def test_clouds_added_overhead(self):
        sky = nfs2se_sky(self.settings, strips(), solid(40), 2)
        out = render_horizon_sky(sky, 64, 32).astype(int)
        self.assertEqual(list(out[0, 10, :3]), [255, 162, 106])

    def test_clouds_alpha_blended_at_half_on_track_7(self):
        sky = nfs2se_sky(self.settings, strips(), solid(40), 7)
        out = render_horizon_sky(sky, 64, 32).astype(int)
        alpha = 0x7F / 255
        expected = [round(c * (1 - alpha) + 40 * alpha) for c in (255, 122, 66)]
        self.assertEqual(list(out[0, 10, :3]), expected)


class TestNfs3Sky(unittest.TestCase):
    def setUp(self):
        self.settings = parse_nfs3_horizon_settings(read_sample('NFS3_3TR00.HRZ'))

    def test_sector_k_from_heading_k_sixteenths_plus_quarter_minus_angle(self):
        for degrees in (0, 160):
            settings = self.settings._replace(angle_degrees=degrees, cloud_type=0)
            out = render_horizon_sky(nfs3_sky(settings, strips(), None, None, None), WIDTH, HEIGHT).astype(int)
            rotation = ((degrees << 16) // 360) / 65536
            # pixmap from -50 to 150 around the eye, radius 1500
            r = row(math.atan(50 / 1500))
            for k in range(16):
                strip = k if k < 8 else 15 - k
                heading = (k + 0.5) / 16 + 0.25 - rotation - 0.00002
                self.assertEqual(out[r, column(heading), 0], 20 * strip + 10, (degrees, k))

    def test_shorter_strips_end_lower(self):
        settings = self.settings._replace(cloud_type=0)
        out = render_horizon_sky(nfs3_sky(settings, strips((16,) + (32,) * 7), None, None, None), WIDTH, HEIGHT).astype(
            int
        )
        # strip 0 covers -50 .. 50, strip 1 -50 .. 150
        r = row(math.atan(100 / 1500))
        self.assertNotEqual(out[r, column(0.25 + 0.5 / 16), 0], 10)
        self.assertEqual(out[r, column(0.25 + 1.5 / 16), 0], 30)

    def test_clouds_overhead(self):
        settings = self.settings._replace(cloud_variance=0)
        out = render_horizon_sky(nfs3_sky(settings, strips(), solid(100), None, None), 64, 32).astype(int)
        # a uniform brightness keeps (sqrt((235 - 128) / 128) + 1) * 127.5 = 244, vertex colour and alpha:
        # sky top + 100 * (244 / 255) ** 2, saturated
        self.assertEqual(list(out[0, 10, :3]), [120 + 92, 255, 255])

    def test_sun(self):
        settings = self.settings._replace(cloud_type=0)
        sun = solid(200, alpha=255)
        out = render_horizon_sky(nfs3_sky(settings, strips(), None, sun, 'A0 B0 R25'), WIDTH, HEIGHT).astype(int)
        # direction (cos 0, cos 0, sin 0) = (1, 1, 0): +X, 45 degrees up, additive
        self.assertEqual(list(out[row(math.radians(45)), column(0.25), :3]), [255, 255, 255])
        self.assertEqual(list(out[row(math.radians(45)), column(0.75), :3]), [120, 182, 239])


class TestNfs4Sky(unittest.TestCase):
    def test_sector_k_from_heading_k_sixteenths_minus_angle(self):
        settings = parse_nfs4_sky_settings(read_sample('NFS4_Tr.ini'))._replace(cloudType=0, hrzAngle=0.22)
        out = render_horizon_sky(nfs4_sky(settings, strips(), None, None), WIDTH, HEIGHT).astype(int)
        r = row(math.atan(50 / 1500))
        for k in range(16):
            strip = k if k < 8 else 15 - k
            self.assertEqual(out[r, column((k + 0.5) / 16 - 0.22), 0], 20 * strip + 10, k)

    def test_sun_from_image_text_without_has_sun(self):
        settings = parse_nfs4_sky_settings(read_sample('NFS4_Tr.ini'))._replace(cloudType=0, hasSun=0)
        sun = solid(200)
        out = render_horizon_sky(nfs4_sky(settings, strips(), None, sun, 'A90 B0 R25'), WIDTH, HEIGHT).astype(int)
        # (cos 90, cos 0, sin 90) = (0, 1, 1): +Z, 45 degrees up
        self.assertEqual(list(out[row(math.radians(45)), column(0.0), :3]), [255, 255, 255])
        none = render_horizon_sky(nfs4_sky(settings, strips(), None, sun, None), 64, 32)
        self.assertEqual(len(np.unique(none[2, :, 0])), 1)


class TestSunText(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse_sun_text('A200  B45  R25  ROTATE \x00'), (200, 45, 25, True, True, False))
        self.assertEqual(parse_sun_text('A0 B45 R30 INFRONT NOADD'), (0, 45, 30, False, False, True))
        self.assertIsNone(parse_sun_text('A0 B45'))


class TestArchiveKind(unittest.TestCase):
    def test_kinds(self):
        with tempfile.TemporaryDirectory() as tmp:
            for directory, files in [
                ('GAMEDATA/TRACKS/SE', ['TR020.QFS', '3TR02.HRZ']),
                ('GAMEDATA/TRACKS/PC', ['TR020.QFS', 'TR02.HRZ']),
                ('GameData/Tracks/TRK001', ['TR010.QFS', 'TR011.QFS', '3TR01.HRZ']),
                ('Data/Tracks/Hometown', ['sky.qfs', 'Tr.ini']),
            ]:
                os.makedirs(os.path.join(tmp, directory))
                for name in files:
                    open(os.path.join(tmp, directory, name), 'w').close()
            self.assertEqual(horizon_archive_kind(f'{tmp}/GAMEDATA/TRACKS/SE/TR020.QFS__data'), 'nfs2se')
            self.assertIsNone(horizon_archive_kind(f'{tmp}/GAMEDATA/TRACKS/PC/TR020.QFS'))
            self.assertEqual(horizon_archive_kind(f'{tmp}/GameData/Tracks/TRK001/TR010.QFS'), 'nfs3')
            self.assertIsNone(horizon_archive_kind(f'{tmp}/GameData/Tracks/TRK001/TR011.QFS'))
            self.assertEqual(horizon_archive_kind(f'{tmp}/Data/Tracks/Hometown/sky.qfs'), 'nfs4')
            self.assertIsNone(horizon_archive_kind(None))


if __name__ == '__main__':
    unittest.main()
