import unittest
from copy import deepcopy
from io import BytesIO

from library import require_file
from library.context import ReadContext
from resources.eac.maps.nfs4 import Nfs4SpeedFile


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

    def _handle_from_file(self, block, tri, kind, handle_id):
        """The handle as read back from the written file"""
        written = block.unpack_from_bytes(block.pack(tri))
        return block.spatial_handle(written, kind, handle_id)

    def test_spatial_terrain_vertex_move_should_keep_next_vertices(self):
        from library.spatial_edit import apply_spatial_move

        (name, block, tri) = require_file('test/samples/AL1.TRI')
        tri = deepcopy(tri)
        before = block._terrain_row_vertices(tri, 10, 2)
        handle = block.spatial_handle(tri, 'terrain_vertex', '10/2/3')
        target = [handle['position'][0] + 1.2345, handle['position'][1] - 0.5, handle['position'][2] + 2.001]
        changes, stored = apply_spatial_move(name, block, tri, 'terrain_vertex', '10/2/3', target, None)
        self.assertEqual([c['id'] for c in changes], [f'{name}__terrain/10/rows/2/3', f'{name}__terrain/10/rows/2/4'])
        after = block._terrain_row_vertices(tri, 10, 2)
        for column in range(11):
            if column != 3:
                self.assertEqual(before[column], after[column])
        # 9.7 fixed point: within 1/256 m of the target
        for a, b in zip(stored['position'], target):
            self.assertAlmostEqual(a, b, delta=1 / 256)
        self.assertEqual(self._handle_from_file(block, tri, 'terrain_vertex', '10/2/3'), stored)

    def test_spatial_terrain_center_vertex_move_should_keep_both_sides(self):
        from library.spatial_edit import apply_spatial_move

        (name, block, tri) = require_file('test/samples/AL1.TRI')
        tri = deepcopy(tri)
        before = block._terrain_row_vertices(tri, 20, 0)
        handle = block.spatial_handle(tri, 'terrain_vertex', '20/0/0')
        target = [handle['position'][0] + 3, handle['position'][1], handle['position'][2] - 1]
        apply_spatial_move(name, block, tri, 'terrain_vertex', '20/0/0', target, None)
        after = block._terrain_row_vertices(tri, 20, 0)
        self.assertEqual(before[1:], after[1:])

    def test_spatial_prop_move_should_reanchor_prop_and_snap_rotation(self):
        import math

        from library.spatial_edit import apply_spatial_move

        (name, block, tri) = require_file('test/samples/AL1.TRI')
        tri = deepcopy(tri)
        handle = block.spatial_handle(tri, 'prop', '5')
        self.assertEqual(handle['match'], {'object_index': 5})
        target = [handle['position'][0] + 40, handle['position'][1] + 3, handle['position'][2]]
        yaw = 0.7
        rotation = [0, 0, math.sin(yaw / 2), math.cos(yaw / 2)]
        _, stored = apply_spatial_move(name, block, tri, 'prop', '5', target, rotation)
        point = tri['props'][5]['road_point_idx']
        # the nearest road point
        spline = tri['road_spline'][: len(tri['terrain']) * 4]
        self.assertEqual(
            point,
            min(
                range(len(spline)),
                key=lambda n: sum((spline[n]['position'][c] - target_c) ** 2 for c, target_c in zip('xzy', target)),
            ),
        )
        self.assertEqual(stored['chunk'], point // 4)
        # 8-bit angle relative to the road: within half a step of the asked yaw
        stored_yaw = 2 * math.atan2(stored['rotation'][2], stored['rotation'][3])
        self.assertAlmostEqual((stored_yaw - yaw + math.pi) % (2 * math.pi) - math.pi, 0, delta=math.pi / 256)
        self.assertEqual(self._handle_from_file(block, tri, 'prop', '5'), stored)

    def test_spatial_road_point_move_should_update_angles_and_carry_terrain(self):
        import math

        from library.spatial_edit import apply_spatial_move

        (name, block, tri) = require_file('test/samples/AL1.TRI')
        tri = deepcopy(tri)
        row_before = block._terrain_row_vertices(tri, 25, 1)
        handle = block.spatial_handle(tri, 'road_point', '101')
        self.assertEqual(apply_spatial_move(name, block, tri, 'road_point', '101', handle['position'], None)[0], [])
        target = [handle['position'][0] + 2, handle['position'][1], handle['position'][2] + 1]
        apply_spatial_move(name, block, tri, 'road_point', '101', target, None)
        a, b = tri['road_spline'][100]['position'], tri['road_spline'][101]['position']
        heading = math.atan2(b['x'] - a['x'], b['z'] - a['z']) % (2 * math.pi)
        self.assertAlmostEqual(tri['road_spline'][100]['orientation'], heading, delta=2 * math.pi / 0x4000)
        normal = tri['road_spline'][100]['side_normal']
        self.assertAlmostEqual(math.sqrt(sum(v * v for v in normal.values())), 0.5, delta=0.001)
        # the terrain row of the point is relative to it
        row_after = block._terrain_row_vertices(tri, 25, 1)
        for before, after in zip(row_before, row_after):
            self.assertAlmostEqual(after['x'] - before['x'], 2, delta=0.001)
            self.assertAlmostEqual(after['y'] - before['y'], 1, delta=0.001)

    def test_spatial_moves_of_a_vertex_chain_should_be_one_change(self):
        from library.spatial_edit import apply_spatial_moves

        (name, block, original) = require_file('test/samples/AL1.TRI')
        for ids in (['10/2/2', '10/2/3', '10/2/4'], ['10/2/4', '10/2/3', '10/2/2']):
            tri = deepcopy(original)
            before = block._terrain_row_vertices(tri, 10, 2)
            moves = []
            for handle_id in ids:
                position = block.spatial_handle(tri, 'terrain_vertex', handle_id)['position']
                moves.append(
                    {'id': handle_id, 'position': [position[0], position[1], position[2] + 2], 'rotation': None}
                )
            changes, handles = apply_spatial_moves(name, block, tri, 'terrain_vertex', moves)
            self.assertEqual([h['id'] for h in handles], ids)
            # raised together, A3 and A4 keep their offsets: A2 goes up, A5's offset goes down to keep it, each once
            # (the changes in between cancel out)
            self.assertEqual(sorted(c['id'] for c in changes), [f'{name}__terrain/10/rows/2/{c}' for c in (2, 5)])
            after = block._terrain_row_vertices(tri, 10, 2)
            for column in range(11):
                delta = 2 if column in (2, 3, 4) else 0
                # the game's y is the export z
                self.assertAlmostEqual(after[column]['y'] - before[column]['y'], delta, delta=1 / 128, msg=ids)
                self.assertEqual(after[column]['x'], before[column]['x'])
            # undo: the old values give the original data back
            for change in changes:
                column = int(change['id'].rsplit('/', 1)[1])
                tri['terrain'][10]['rows'][2][column] = change['oldValue']
            self.assertEqual(tri['terrain'][10], original['terrain'][10])

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
    def test_nfs4_frd_should_remain_the_same(self):
        (name, block, data) = require_file('test/samples/GT1.FRD')
        with open('test/samples/GT1.FRD', 'rb') as bdata:
            original = bdata.read()
        self.assertEqual(block.pack(data, name=name), original)

    def test_nfs4_frd_slices_and_road_data_should_be_named(self):
        (name, block, data) = require_file('test/samples/GT1.FRD')
        headers = data['blocks_headers']
        self.assertEqual(sum(h['num_slices'] for h in headers), len(data['vroad']))
        self.assertTrue(all(h['num_slices'] == 8 for h in headers[:-1]))
        for header, trk_block in zip(headers, data['blocks']):
            for record in trk_block['polygon_vroad_data']:
                self.assertLess(record['polygon'], header['polygon_chunk_sizes'][4])
                self.assertLessEqual(record['cell_z_min'], record['cell_z_max'])
                self.assertLessEqual(record['cell_x_min'], record['cell_x_max'])
        surfaces = [r['surface'] for b in data['blocks'] for r in b['polygon_vroad_data']]
        self.assertTrue(any(s['walls'] for s in surfaces))
        self.assertTrue(all(0 <= s['surface_type'] < 32 for s in surfaces))
        vroad = data['vroad'][0]
        self.assertTrue(0 <= vroad['left_side_type'] <= 5 and 0 <= vroad['right_side_type'] <= 5)
        self.assertGreater(vroad['right_lanes'], 0)
        self.assertNotEqual(vroad['lane_open_bits'], 0)
        types = {x['collision']['type'] for b in data['blocks'] for x in b['xobj']}
        self.assertTrue(types <= {'none', 'solid', 'knockable', 'crash_only'})
        specials = [o['special_data'] for o in data['global_objects_1']['objects'] if o['special_data']]
        self.assertTrue(specials)
        self.assertTrue(all(0 <= s['slice'] < len(data['vroad']) for s in specials))


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

    def test_speeds_file_should_hold_speeds_and_lanes(self):
        from library.loader import probe_block_class

        # odd n = 3: n // 2 + 1 = 2 speed bytes, 3 lane bytes; even n = 4: 3 speed bytes (the last one 0), 4 lane bytes
        for raw, n in ((bytes([60, 72, 0x70, 0x60, 0x80]), 3), (bytes([60, 72, 0, 0x70, 0x60, 0x80, 0x50]), 4)):
            self.assertEqual(len(raw), n // 2 + 1 + n)
            for name in ('SPEEDSF.BIN', 'SPEEDSR.BIN'):
                block_class = probe_block_class(BytesIO(raw), f'GameData/Tracks/TRK005/{name}', len(raw))
                self.assertEqual(block_class.__name__, 'Nfs3SpeedsFile')
            block = block_class()
            data = block.unpack_from_bytes(raw)
            self.assertEqual(data['speeds'], list(raw[: n // 2 + 1]))
            self.assertEqual([x['lane'] for x in data['lanes']], [b >> 4 for b in raw[n // 2 + 1 :]])
            self.assertEqual(block.pack(data), raw)
        # 6 bytes is no slice count's size (3k bytes)
        with self.assertRaises(NotImplementedError):
            probe_block_class(BytesIO(bytes(6)), 'GameData/Tracks/TRK005/SPEEDSF.BIN', 6)

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


class TestNfs4TrackSmallFiles(unittest.TestCase):
    def test_heights_sim_should_be_one_float_per_slice(self):
        import struct
        from library.loader import probe_block_class

        raw = struct.pack('<3f', 7.6875, 4.25, 10.0)
        block_class = probe_block_class(BytesIO(raw), 'games/nfs4/Data/Tracks/GT1/heights.sim', len(raw))
        self.assertEqual(block_class.__name__, 'Nfs4HeightsSim')
        block = block_class()
        data = block.unpack_from_bytes(raw)
        self.assertEqual(data['heights'], [7.6875, 4.25, 10.0])
        self.assertEqual(block.pack(data), raw)

    def test_speed_file_should_hold_speeds_lanes_and_offsets(self):
        import struct
        from library.loader import probe_block_class

        # 3 slices: ceil(3 / 2) speed bytes, 3 lane bytes, 3 floats
        raw = bytes([60, 72]) + bytes([0x70, 0x60, 0x80]) + struct.pack('<3f', 0.5, -2.0, 3.25)
        self.assertEqual(len(raw), (3 + 1) // 2 + 5 * 3)
        for name in ('spdFA.bin', 'spdra.bin'):
            block_class = probe_block_class(BytesIO(raw), f'Data/Tracks/Uk/{name}', len(raw))
            self.assertEqual(block_class.__name__, 'Nfs4SpeedFile')
        with self.assertRaises(NotImplementedError):
            probe_block_class(BytesIO(raw[:-1]), 'Data/Tracks/Uk/spdFA.bin', len(raw) - 1)
        block = Nfs4SpeedFile()
        data = block.unpack_from_bytes(raw)
        self.assertEqual(data['speeds'], [60, 72])
        self.assertEqual([x['lane'] for x in data['lanes']], [7, 6, 8])
        self.assertEqual(data['line_offsets'], [0.5, -2.0, 3.25])
        self.assertEqual(block.pack(data), raw)


class TestNfs5TrackSmallFiles(unittest.TestCase):
    def test_junctions_should_hold_end_weights(self):
        import struct
        from library.loader import probe_block_class

        raw = struct.pack('<I8f', 0, 1.0, *[0.0] * 7) + struct.pack('<I8f', 1, 1.0, 0.25, 0.75, *[0.0] * 5)
        block_class = probe_block_class(BytesIO(raw), 'GameData/Track/alps.jnc', len(raw))
        self.assertEqual(block_class.__name__, 'Nfs5Junctions')
        with self.assertRaises(NotImplementedError):
            probe_block_class(BytesIO(raw[:-1]), 'GameData/Track/alps.jnc', len(raw) - 1)
        block = block_class()
        data = block.unpack_from_bytes(raw)
        self.assertEqual([x['index'] for x in data['junctions']], [0, 1])
        self.assertEqual(data['junctions'][1]['end_weights'][:3], [1.0, 0.25, 0.75])
        self.assertEqual(block.pack(data), raw)

    def test_wall_edges_should_hold_flags_and_ends(self):
        import struct
        from library.loader import probe_block_class

        raw = struct.pack('<I', 29087) + bytes([0x60, 0xDF, 0x2E, 0x01]) + struct.pack('<6f', 1, 2, 3, 4, 5, 6)
        block_class = probe_block_class(BytesIO(raw), 'GameData/Track/alps.edg', len(raw))
        self.assertEqual(block_class.__name__, 'Nfs5WallEdges')
        block = block_class()
        data = block.unpack_from_bytes(raw)
        edge = data['edges'][0]
        self.assertEqual(edge['flags'], 0x60)
        self.assertEqual(edge['p0'], {'x': 1.0, 'y': 2.0, 'z': 3.0})
        self.assertEqual(edge['p1'], {'x': 4.0, 'y': 5.0, 'z': 6.0})
        self.assertEqual(block.pack(data), raw)
