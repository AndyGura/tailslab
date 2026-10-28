import json
import os
import tempfile
import unittest
from io import BytesIO

from library.loader import _find_block_class
from resources.eac.horizons import (
    Nfs2HorizonInfo,
    Nfs2SeHorizonInfo,
    Nfs3HorizonInfo,
    Nfs4TrackIni,
    hrz_numbers,
    parse_nfs2_horizon_settings,
    parse_nfs2se_horizon_settings,
    parse_nfs3_horizon_settings,
    parse_nfs4_sky_settings,
)

SAMPLES = os.path.join(os.path.dirname(__file__), '..', '..', 'samples')


def sample(name):
    with open(os.path.join(SAMPLES, name), 'rb') as f:
        return f.read()


class TestHrzNumbers(unittest.TestCase):
    def test_numbers_in_comments_are_skipped(self):
        self.assertEqual(hrz_numbers('/* 1, 2 */ 3, -4,\n255,222,91 /* 9 */ 7'), [3, -4, 255, 222, 91, 7])

    def test_numbers_without_commas(self):
        # NFS3 3TR01.HRZ: "86,140,201 187,175,120"
        self.assertEqual(hrz_numbers('86,140,201 187,175,120'), [86, 140, 201, 187, 175, 120])


class TestNfs2SeHorizon(unittest.TestCase):
    def test_parse(self):
        settings = parse_nfs2se_horizon_settings(sample('NFS2SE_3TR02.HRZ').decode())
        self.assertEqual(settings.cloud_dome_offset, -100)
        self.assertEqual(settings.cloud_dome_height, 250)
        self.assertEqual(settings.mirror, 1)
        self.assertEqual(settings.radius, 1500)
        self.assertEqual(settings.angle_degrees, 300)
        self.assertEqual(settings.flat_projection_distance, 1000)
        self.assertEqual(settings.base_y, -750)
        self.assertEqual(settings.gouraud_height, 1250)
        self.assertEqual(settings.gouraud_middle, 735)
        self.assertEqual(settings.pixmap_top, 960)
        self.assertEqual(settings.pixmap_bottom, 600)
        self.assertEqual(settings.sky_top_color, (255, 122, 66))
        # the commented out colours after the values are not read
        self.assertEqual(settings.sun_color, (255, 222, 91))
        self.assertEqual(settings.opposite_sun_color, (0, 0, 130))

    def test_too_few_values(self):
        self.assertIsNone(parse_nfs2se_horizon_settings('1, 2, 3'))

    def test_round_trip(self):
        raw = sample('NFS2SE_3TR02.HRZ')
        block = Nfs2SeHorizonInfo()
        self.assertEqual(block.pack(block.unpack_from_bytes(raw)), raw)


class TestNfs2Horizon(unittest.TestCase):
    def test_parse(self):
        settings = parse_nfs2_horizon_settings(sample('NFS2_TR02.HRZ').decode())
        self.assertEqual(settings.angle_degrees, 300)
        self.assertEqual(settings.pixmap_base_percent, 40)
        self.assertEqual(settings.flat_sky_color, (56, 80, 131))
        self.assertEqual(settings.depth_cueing_distances, (0, 250, 500, 900))
        self.assertEqual(settings.color, (40, 40, 40))


class TestNfs3Horizon(unittest.TestCase):
    def test_parse(self):
        settings = parse_nfs3_horizon_settings(sample('NFS3_3TR00.HRZ').decode())
        self.assertEqual(settings.fog_color, (134, 134, 140))
        self.assertEqual(settings.fog_pixmap_effect_percent, 70)
        self.assertEqual(len(settings.fog_regions), 2)
        self.assertEqual(settings.fog_regions[1].apex_density, 40)
        self.assertEqual(settings.fog_regions[1].after_slice, 300)
        self.assertEqual(settings.cloud_type, 1)
        self.assertEqual(settings.cloud_visual_height, 500)
        self.assertEqual((settings.cloud_dome_offset, settings.cloud_dome_height), (-100, 250))
        self.assertEqual(
            (settings.cloud_bright, settings.cloud_variance, settings.cloud_nimbus_percent), (235, 208, 80)
        )
        self.assertEqual((settings.wind_speed, settings.wind_direction), (10, 100))
        self.assertEqual((settings.black_horizon, settings.mirror, settings.radius), (0, 1, 1500))
        self.assertEqual((settings.angle_degrees, settings.has_pixmap), (0, 1))
        self.assertEqual((settings.base_y, settings.gouraud_height, settings.gouraud_middle), (-1200, 1800, 1200))
        self.assertEqual((settings.pixmap_top, settings.pixmap_bottom), (1350, 1150))
        self.assertEqual(settings.earth_top_color, (117, 106, 15))
        self.assertEqual(settings.earth_bottom_color, (207, 153, 98))
        self.assertEqual(settings.sky_top_color, (120, 182, 239))
        self.assertEqual(settings.sun_color, (223, 210, 151))
        self.assertEqual(settings.opposite_sun_color, (120, 171, 204))
        self.assertEqual(settings.weather, (0,) * 8)
        self.assertEqual(settings.ambient_percent, (100, 100, 100))

    def test_round_trip(self):
        raw = sample('NFS3_3TR00.HRZ')
        block = Nfs3HorizonInfo()
        self.assertEqual(block.pack(block.unpack_from_bytes(raw)), raw)


class TestNfs4TrackIni(unittest.TestCase):
    def test_parse(self):
        settings = parse_nfs4_sky_settings(sample('NFS4_Tr.ini').decode())
        # the same sky as NFS3 3TR00.HRZ, under names
        self.assertEqual(settings.hrzBottomYOff, -1200.0)
        self.assertEqual(settings.hrzGouraudMiddle, 1200.0)
        self.assertEqual(settings.hrzSunColor, (223, 210, 151))
        self.assertEqual(settings.hrzSkyTopColor, (120, 182, 239))
        self.assertEqual(settings.hrzAngle, 0.0)
        self.assertEqual(settings.cloudHeight, 750.0)
        self.assertAlmostEqual(settings.cloudNimbus, 0.8)
        self.assertEqual(settings.cloudUscale, 1.0)
        self.assertEqual(settings.fogColor, (134, 134, 140))
        self.assertEqual((settings.hasSun, settings.angleTheta, settings.angleRho), (1, 0.56, 0.13))
        self.assertEqual((settings.radius, settings.rotates, settings.additive, settings.inFront), (250.0, 1, 1, 0))

    def test_missing_keys_and_clamps(self):
        settings = parse_nfs4_sky_settings(
            '[STRIP]\nHRZANGLE=0.25 \n[clouds]\ncloudType=5\ncloudBright=300\ncloudVariance=400\n'
        )
        self.assertEqual(settings.hrzAngle, 0.25)
        self.assertEqual(settings.cloudType, 2)
        self.assertEqual(settings.cloudBright, 255)
        self.assertEqual(settings.cloudVariance, 255)
        self.assertEqual(settings.cloudUscale, 1.0)
        self.assertEqual(settings.hasSun, 0)

    def test_round_trip(self):
        raw = sample('NFS4_Tr.ini')
        block = Nfs4TrackIni()
        self.assertEqual(block.pack(block.unpack_from_bytes(raw)), raw)


class TestDetection(unittest.TestCase):
    def test_hrz_kinds(self):
        for name, block_class in [
            ('NFS2SE_3TR02.HRZ', Nfs2SeHorizonInfo),
            ('NFS3_3TR00.HRZ', Nfs3HorizonInfo),
            ('NFS2_TR02.HRZ', Nfs2HorizonInfo),
        ]:
            self.assertIs(_find_block_class(BytesIO(sample(name)), f'some/dir/{name}'), block_class)

    def test_nfs4_track_ini(self):
        raw = sample('NFS4_Tr.ini')
        self.assertIs(_find_block_class(BytesIO(raw), 'games/nfs4/Data/Tracks/Hometown/Tr.ini'), Nfs4TrackIni)
        self.assertIs(_find_block_class(BytesIO(raw), 'games/nfs4/Data/Tracks/Hometown/TrNW.ini'), Nfs4TrackIni)


class TestSerializer(unittest.TestCase):
    def test_json(self):
        from serializers import EacHorizonSettingsSerializer

        block = Nfs3HorizonInfo()
        data = block.unpack_from_bytes(sample('NFS3_3TR00.HRZ'))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, '3TR00.HRZ')
            files = EacHorizonSettingsSerializer().serialize(data, path, block=block)
            self.assertEqual(files, [f'{path}.json'])
            with open(files[0]) as f:
                values = json.load(f)
        self.assertEqual(values['sky_top_color'], [120, 182, 239])
        self.assertEqual(values['fog_regions'][0]['center_slice'], 175)


if __name__ == '__main__':
    unittest.main()
