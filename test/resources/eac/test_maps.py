import unittest
from copy import deepcopy
from io import BytesIO

from library import require_file
from library.context import ReadContext


class TestTriMap(unittest.TestCase):
    def test_tri_should_remain_the_same(self):
        (name, block, tri) = require_file('test/samples/AL1.TRI')
        output = block.pack(tri, name=name)
        with open('test/samples/AL1.TRI', 'rb') as bdata:
            original = bdata.read()
            self.assertEqual(len(original), len(output))
            for i, x in enumerate(original):
                self.assertEqual(x, output[i], f'Wrong value at index {i}')

    def test_reverse_track_should_swap_waterfall_sides(self):
        (name, block, tri) = require_file('test/samples/AL1.TRI')
        tri = deepcopy(tri)
        length = len(tri['terrain']) * 4
        tri['road_spline'][100]['item_mode'] = 'waterfall_audio_left_channel'
        tri['road_spline'][200]['item_mode'] = 'waterfall_audio_right_channel'
        block.action_reverse_track(tri)
        self.assertEqual(tri['road_spline'][length - 1 - 100]['item_mode'], 'waterfall_audio_right_channel')
        self.assertEqual(tri['road_spline'][length - 1 - 200]['item_mode'], 'waterfall_audio_left_channel')

    def test_police_spots(self):
        (name, block, tri) = require_file('test/samples/AL1.TRI')
        spots = [i for i, p in enumerate(tri['road_spline']) if p['police_spot']['is_spot']]
        self.assertEqual(spots, [145, 440, 690, 1073, 1154, 1340, 1423])
        self.assertEqual(
            tri['road_spline'][145]['police_spot'],
            {'unused': 0, 'chance': '97/128', 'drives_off': True, 'is_left': False, 'is_spot': True},
        )
        self.assertEqual(tri['road_spline'][440]['police_spot']['chance'], '65/128')
        self.assertTrue(tri['road_spline'][440]['police_spot']['is_left'])

    def test_reverse_track_should_swap_police_spot_sides(self):
        (name, block, tri) = require_file('test/samples/AL1.TRI')
        tri = deepcopy(tri)
        length = len(tri['terrain']) * 4
        block.action_reverse_track(tri)
        self.assertTrue(tri['road_spline'][length - 1 - 145]['police_spot']['is_left'])
        self.assertFalse(tri['road_spline'][length - 1 - 440]['police_spot']['is_left'])
        self.assertFalse(tri['road_spline'][0]['police_spot']['is_left'])


class TestNfs4FrdMap(unittest.TestCase):
    def test_nfs4_frd_should_be_same_size_and_stable(self):
        (name, block, data) = require_file('test/samples/GT1.FRD')
        with open('test/samples/GT1.FRD', 'rb') as bdata:
            original = bdata.read()
        output = block.pack(data, name=name)
        # `polygon_vroad_data.normal`/`.forward` are re-normalized to unit length on write, which
        # is lossy (the source data isn't always exactly unit length in the first place), so a
        # byte-identical round trip isn't expected here - only that the size is preserved and the
        # result stabilizes (a handful of vectors sit close enough to a quantization boundary that
        # convergence takes one extra cycle, hence comparing the 2nd and 3rd cycle rather than the
        # 1st and 2nd).
        self.assertEqual(len(original), len(output))
        data_twice = block.unpack_from_bytes(output, name=name + '__twice')
        output_twice = block.pack(data_twice, name=name + '__twice')
        data_thrice = block.unpack_from_bytes(output_twice, name=name + '__thrice')
        output_thrice = block.pack(data_thrice, name=name + '__thrice')
        self.assertEqual(output_twice, output_thrice)


class TestNfs6AiPaths(unittest.TestCase):
    def test_ai_paths_should_be_read_and_remain_the_same(self):
        import struct
        from resources.eac.maps.nfs6 import Nfs6AiPaths

        def graph(paths):
            nodes = [p for _, pts in paths for p in (pts[0], pts[-1])]
            b = struct.pack('<I', len(nodes)) + b''.join(struct.pack('<3f', *p) for p in nodes)
            b += struct.pack('<I', len(paths))
            for i, (name, pts) in enumerate(paths):
                b += name.encode().ljust(16, b'\0') + struct.pack('<IIfII', 2 * i, 2 * i + 1, 44.703, 1, len(pts))
                b += b''.join(struct.pack('<7f', *p, 10, -10, 1.5, 48) for p in pts)
            return b

        raw = struct.pack('<I', 1)
        raw += graph([('AI_center00', [(0, 1, 0), (0, 1, 5), (0, 1, 10)]), ('AI_center01', [(0, 1, 10), (5, 1, 10)])])
        raw += graph([('Helipath_center', [(0, 50, 0), (0, 50, 10)])])
        block = Nfs6AiPaths()
        data = block.unpack_from_bytes(raw)
        road = data['road_paths']
        self.assertEqual(len(road['nodes']), 4)
        self.assertEqual(road['paths'][1]['name'], 'AI_center01')
        self.assertEqual(road['paths'][1]['start_node'], 2)
        self.assertEqual(road['paths'][0]['points'][1]['position'], {'x': 0, 'y': 1, 'z': 5})
        self.assertEqual(road['paths'][0]['points'][1]['left_width'], 10)
        self.assertEqual(data['helicopter_paths']['paths'][0]['name'], 'Helipath_center')
        self.assertEqual(block.pack(data), raw)


class TestFrdMap(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.name, cls.block, cls.data = require_file('test/golden_corpus/TR00.FRD')

    def test_frd_should_remain_the_same(self):
        with open('test/golden_corpus/TR00.FRD', 'rb') as f:
            original = f.read()
        self.assertEqual(self.block.pack(self.data, name=self.name), original)

    def test_xobj_reference_point_should_match_block_reference(self):
        # pt_ref of an extra object is a float point, its reference in the block is 16.16 fixed point
        ref = self.data['blocks'][0]['xobj'][0]
        xobj = self.data['extraobject_blocks'][4 * 0][0]
        for k in 'xyz':
            self.assertAlmostEqual(ref['position'][k], xobj['data']['data']['pt_ref'][k], places=3)
        self.assertEqual(ref['position'], self.data['blocks'][0]['polyobj'][ref['cross_index']]['position'])

    def test_polyobj_references_should_follow_first_polyobj_chunk(self):
        refs = self.data['blocks'][0]['polyobj']
        objects = self.data['polygon_blocks'][0]['polyobj'][0]['data']['data']
        self.assertEqual([r['type'] for r in refs], [o['type'] for o in objects])
        self.assertEqual([r['size'] for r in refs], [20 if r['type'] == 4 else 16 for r in refs])
        self.assertEqual([r['xobj_idx'] for r in refs if r['type'] == 4], [0, 1, 2])
        self.assertEqual(len(self.data['blocks'][0]['polyobj_unused']), 4 * sum(1 for r in refs if r['type'] != 4))

    def test_animated_xobj_keyframes_should_have_unit_quaternions(self):
        animated = [x for chunk in self.data['extraobject_blocks'] for x in chunk if x['cross_type'] == 3]
        self.assertEqual(len(animated), 2)
        for xobj in animated:
            for frame in xobj['data']['data']['animdata']:
                q = frame['orientation']
                self.assertAlmostEqual(q['x'] ** 2 + q['y'] ** 2 + q['z'] ** 2 + q['w'] ** 2, 1, places=3)

    def test_animated_xobj_size_should_cover_animation(self):
        animated = [x for chunk in self.data['extraobject_blocks'] for x in chunk if x['cross_type'] == 3]
        for xobj in animated:
            animation = xobj['data']['data']
            self.assertEqual(animation['animation_size'], 8 + 20 * animation['num_animdata'])
            self.assertEqual(animation['animation_size_2'], animation['animation_size'])
        static = [x for chunk in self.data['extraobject_blocks'] for x in chunk if x['cross_type'] == 4]
        self.assertTrue(static)
        self.assertTrue(all(x['data']['data']['animation_size'] == 0 for x in static))

    def test_xobj_refs_and_slices_should_be_named(self):
        xobjs = [x for b in self.data['blocks'] for x in b['xobj']]
        self.assertEqual({x['type'] for x in xobjs} - {'solid', 'knockable', 'no_collision'}, set())
        self.assertTrue(all(x['radius'] > 0 for x in xobjs))
        positions = [p for b in self.data['blocks'] for p in b['positions']]
        # one slice per COL collision_data record
        self.assertEqual(len(positions), 959)
        self.assertTrue(all(p['alt_slice_1'] == -1 and p['alt_slice_2'] == -1 for p in positions))
        flags = self.data['blocks'][0]['polygons'][0]['flags']
        self.assertEqual(set(flags), {'barriers', 'objects', 'surface'})


class TestFrdPolyObjRef(unittest.TestCase):
    def test_record_size_should_depend_on_type(self):
        import struct
        from resources.eac.maps import FrdPolyObjRef

        block = FrdPolyObjRef()
        polygons = struct.pack('<HBB3i', 16, 1, 8, 65536, -65536, 32768)
        xobj = struct.pack('<HBB3iI', 20, 4, 5, 0, 0, 0, 2)
        data = block.unpack_from_bytes(polygons)
        self.assertEqual(data['position'], {'x': 1.0, 'y': -1.0, 'z': 0.5})
        self.assertEqual(block.pack(data), polygons)
        data = block.unpack_from_bytes(xobj)
        self.assertEqual(data['xobj_idx'], 2)
        self.assertEqual(block.pack(data), xobj)
        data['type'] = 1
        self.assertEqual(len(block.pack(data)), 16)


class TestMapColFile(unittest.TestCase):
    def test_col_files_should_remain_the_same(self):
        for path in ['test/golden_corpus/TR02.COL', 'test/golden_corpus/TR00.COL']:
            (name, block, data) = require_file(path)
            with open(path, 'rb') as f:
                self.assertEqual(block.pack(data, name=name), f.read(), path)

    def test_animated_prop_should_have_orientation(self):
        (_, _, data) = require_file('test/golden_corpus/TR02.COL')
        props = next(x for x in data['extrablocks'] if x['type'] == 'props_7')['data_records']['data']
        animated = [p for p in props if p['type'] == 'animated_prop']
        self.assertEqual(len(animated), 1)
        position = animated[0]['position']['data']
        self.assertEqual(position['anim_delay'], 44)
        q = position['frames'][0]['orientation']
        self.assertEqual((q['x'], q['z']), (0, 0))
        self.assertAlmostEqual(q['y'] ** 2 + q['w'] ** 2, 1, places=3)


class TestTrkMap(unittest.TestCase):
    def test_trk_should_remain_the_same_and_read_special_props(self):
        (name, block, data) = require_file('test/golden_corpus/TR02.TRK')
        with open('test/golden_corpus/TR02.TRK', 'rb') as f:
            self.assertEqual(block.pack(data, name=name), f.read())
        special = [
            p
            for sb in data['superblocks']
            for b in sb['blocks']
            for eb in b['extrablocks']
            if eb['type'] in ['props_7', 'props_18']
            for p in eb['data_records']['data']
            if p['type'] == 'special_prop'
        ]
        self.assertEqual(len(special), 34)
        self.assertEqual(special[0]['position']['data']['special_idx'], 0)

    def test_trk_road_polygons_should_match_polygon_map_and_medians(self):
        (_, _, data) = require_file('test/golden_corpus/TR02.TRK')
        blocks = [b for sb in data['superblocks'] for b in sb['blocks']]
        for b in blocks:
            self.assertEqual(b['first_slice'], b['block_idx'] * 8)
            self.assertIn(len(b['padding']), (0, 2))
            records = {eb['type']: eb['data_records']['data'] for eb in b['extrablocks']}
            self.assertEqual(len(records['polygon_map']), b['num_road_polygons'])
            for median in records['median_polygons']:
                self.assertLessEqual(median['first_polygon'] + median['num_polygons'], b['num_road_polygons'])
        b = blocks[18]
        self.assertEqual(
            (b['num_extra_polygons'], b['num_road_polygons'], b['num_unk_polygons']),
            (4, 72, 8),
        )
        self.assertEqual((len(b['extra_polygons']), len(b['road_polygons']), len(b['unk_polygons'])), (4, 72, 8))
        self.assertEqual(b['road_polygons'][0]['vertices'], [65, 66, 45, 43])

    def test_trk_track_objects_should_match_special_props(self):
        (_, _, data) = require_file('test/golden_corpus/TR02.TRK')
        object_indexes = []
        for b in [b for sb in data['superblocks'] for b in sb['blocks']]:
            objects = next((eb['data_records']['data'] for eb in b['extrablocks'] if eb['type'] == 'track_objects'), [])
            object_indexes += [o['object_idx'] for o in objects]
            special = [
                p['position']['data']
                for eb in b['extrablocks']
                if eb['type'] == 'props_7'
                for p in eb['data_records']['data']
                if p['type'] == 'special_prop'
            ]
            self.assertEqual(sorted(p['special_idx'] for p in special), list(range(len(objects))))
            for p in special:
                self.assertEqual(objects[p['special_idx']]['position'], p['position'])
        self.assertEqual(object_indexes, list(range(34)))


class TestTrkExtraDataRecords(unittest.TestCase):
    def test_nfs2_se_median_record(self):
        from resources.eac.maps import MedianExtraDataRecord

        # a slice of NFS2 SE TR03.TRK block 34, at a fork
        raw = bytes.fromhex('18000f027901ffff')
        block = MedianExtraDataRecord()
        data = block.unpack(ReadContext(BytesIO(raw)), read_bytes_amount=len(raw))
        self.assertEqual(
            data, {'first_polygon': 24, 'num_polygons': 15, 'unk': 2, 'alt_slice_1': 377, 'alt_slice_2': -1}
        )
        self.assertEqual(block.pack(data), raw)

    def test_nfs2_se_polygon_map_record(self):
        from resources.eac.maps import PolygonMapExtraDataRecord

        # a road polygon of NFS2 SE TR03.TRK block 34
        raw = bytes.fromhex('11ca')
        block = PolygonMapExtraDataRecord()
        data = block.unpack(ReadContext(BytesIO(raw)), read_bytes_amount=len(raw))
        self.assertEqual(data, {'vectors_idx': 17, 'surface': {'barriers': True, 'objects': True, 'type': 10}})
        self.assertEqual(block.pack(data), raw)

    def test_nfs2_se_track_object_record(self):
        from resources.eac.maps import TrackObjectExtraDataRecord

        # a knockable object of NFS2 SE TR02.TRK block 95
        raw = bytes.fromhex('fb24dd0089190000d806e2049c000e0007000002')
        block = TrackObjectExtraDataRecord()
        data = block.unpack(ReadContext(BytesIO(raw)), read_bytes_amount=len(raw))
        self.assertAlmostEqual(data['position']['x'], 221.14445, places=4)
        self.assertEqual(
            {k: v for k, v in data.items() if k != 'position'},
            {'radius': 0.609375, 'object_idx': 14, 'height': 3.5, 'unk0': 0, 'unk1': 0, 'type': 'knockable'},
        )
        self.assertEqual(block.pack(data), raw)


class TestCollisionExtraDataRecord(unittest.TestCase):
    def test_nfs2_se_lane_fields(self):
        from resources.eac.maps import CollisionExtraDataRecord

        # a slice of NFS2 SE TR04.COL
        raw = bytes.fromhex('0eb35ffe00000000c465e601007f001a007d7d00e6001200e0071d0ec50e5531090a0000')
        block = CollisionExtraDataRecord()
        data = block.unpack(ReadContext(BytesIO(raw)), read_bytes_amount=len(raw))
        self.assertEqual(data['flags'], 0x55)
        self.assertEqual(data['lanes'], {'unk': 3, 'count': 1})
        self.assertEqual(data['left_lane_width'], 4.5)
        self.assertEqual(data['right_lane_width'], 5.0)
        self.assertEqual(data['unk3'], 0)
        self.assertEqual(block.pack(data), raw)


# the first textures_map record and the first slice of NFS3 TR00.COL
NFS3_TEXTURES_MAP_RECORD = bytes.fromhex('4a00000030010000')
NFS3_SLICE = bytes.fromhex('c4613d03f0560d007e8a8800f80f5500007eff2255ffa310a200ab10df56170063cd1b00')


def _nfs3_col_file() -> bytes:
    import struct

    textures_map = struct.pack('<IBBH', 16, 2, 0, 1) + NFS3_TEXTURES_MAP_RECORD
    collision_data = struct.pack('<IBBH', 44, 15, 0, 1) + NFS3_SLICE
    body = struct.pack('<2I', 8, 8 + len(textures_map)) + textures_map + collision_data
    return struct.pack('<4sIII', b'COLL', 11, 16 + len(body), 2) + body


class TestNfs3MapColFile(unittest.TestCase):
    def test_loader_should_tell_nfs3_col_from_nfs2(self):
        from library.loader import probe_block_class

        with open('test/golden_corpus/TR02.COL', 'rb') as f:
            self.assertEqual(probe_block_class(f, 'TR02.COL').__name__, 'MapColFile')
        raw = _nfs3_col_file()
        self.assertEqual(probe_block_class(BytesIO(raw), 'TR00.COL', len(raw)).__name__, 'Nfs3MapColFile')

    def test_nfs3_col_should_read_nfs3_records(self):
        from resources.eac.maps import Nfs3MapColFile

        raw = _nfs3_col_file()
        block = Nfs3MapColFile()
        data = block.unpack_from_bytes(raw)
        self.assertEqual(block.pack(data), raw)
        texture = data['extrablocks'][0]['data_records']['data'][0]
        self.assertEqual((texture['texture_number'], texture['alignment']), (74, 'rotate_180'))
        self.assertEqual((texture['unk1'], texture['unk2'], texture['unk3']), (0x30, 0, 0))
        slice_ = data['extrablocks'][1]['data_records']['data'][0]
        self.assertEqual(slice_['walls'], {'left': 5, 'right': 5})
        self.assertEqual(slice_['lanes'], {'left': 2, 'right': 2})
        self.assertEqual((slice_['left_lane_width'], slice_['right_lane_width']), (8.0, 8.0))
        self.assertEqual(slice_['normal'], {'x': 0.0, 'y': 126 / 128, 'z': -1 / 128})
        self.assertAlmostEqual(slice_['left_border'], 23.339, places=3)
        self.assertAlmostEqual(slice_['right_border'], 27.802, places=3)
        self.assertEqual(slice_['unk0'], 0x0FF8)

    def test_nfs3_slice_should_round_trip_unnormalized_vectors(self):
        from resources.eac.maps import Nfs3CollisionExtraDataRecord

        block = Nfs3CollisionExtraDataRecord()
        data = block.unpack(ReadContext(BytesIO(NFS3_SLICE)), read_bytes_amount=len(NFS3_SLICE))
        self.assertEqual(block.pack(data), NFS3_SLICE)


class TestNfs3TrackSmallFiles(unittest.TestCase):
    def test_simhts_should_be_one_float_per_slice(self):
        import struct
        from library.loader import probe_block_class

        raw = struct.pack('<3f', 5.25, 16.75, 10.0)
        block_class = probe_block_class(BytesIO(raw), 'GameData/Tracks/TRK000/SIMHTS.DAT', len(raw))
        self.assertEqual(block_class.__name__, 'Nfs3SimHeights')
        block = block_class()
        data = block.unpack_from_bytes(raw)
        self.assertEqual(data['heights'], [5.25, 16.75, 10.0])
        self.assertEqual(block.pack(data), raw)

    def test_can_should_read_keyframes(self):
        import struct
        from library.loader import probe_block_class

        # the first two keyframes of NFS3 TR0000.CAN, header of a 2-keyframe file
        frames = [
            (-2614904, 306527, 8258486, -1321, 12866, 9756, 2440),
            (-2641631, 297165, 8079467, -1345, 12868, 9742, 2470),
        ]
        raw = struct.pack('<HHHH', 48, 0x41, 2, 6) + b''.join(struct.pack('<3i4h', *f) for f in frames)
        block_class = probe_block_class(BytesIO(raw), 'TR0000.CAN', len(raw))
        self.assertEqual(block_class.__name__, 'Nfs3CanAnimation')
        block = block_class()
        data = block.unpack_from_bytes(raw)
        self.assertEqual((data['size'], data['num_keyframes'], data['ticks_per_frame']), (48, 2, 6))
        self.assertAlmostEqual(data['keyframes'][0]['position']['x'], -39.9003, places=3)
        q = data['keyframes'][0]['orientation']
        self.assertAlmostEqual(q['x'] ** 2 + q['y'] ** 2 + q['z'] ** 2 + q['w'] ** 2, 1, places=3)
        self.assertEqual(block.pack(data), raw)
        data['keyframes'].pop()
        self.assertEqual(block.pack(data)[:6], struct.pack('<HHH', 28, 0x41, 1))
