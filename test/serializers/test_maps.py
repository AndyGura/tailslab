import unittest
from unittest.mock import patch

from serializers.maps import _require_nfs4_texture_archive


class TestRequireNfs4TextureArchive(unittest.TestCase):
    def setUp(self):
        # No file lookup on disk: the gitignored games/nfs4 folder, where present, has these files in another case
        patcher = patch('library.utils.file_utils.find_files_case_insensitive', return_value=[])
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_uses_own_archive_when_present(self):
        with patch('library.require_resource') as mock_require:
            mock_require.return_value = 'result'
            result = _require_nfs4_texture_archive('games/nfs4/Data/Tracks/Coastal/Trn.frd')
            self.assertEqual(result, 'result')
            mock_require.assert_called_once_with('games/nfs4/Data/Tracks/Coastal/Trn0.QFS__data')

    def test_falls_back_to_forward_track_archive_when_own_is_missing(self):
        # GT1/GT2/Park's reverse tracks ("Trn.FRD") have no dedicated "Trn0.QFS" - they reuse the
        # forward track's "Tr0.QFS" instead.
        def side_effect(id):
            if id == 'games/nfs4/Data/Tracks/GT1/Trn0.QFS__data':
                raise FileNotFoundError(2, 'No such file or directory')
            return 'result'

        with patch('library.require_resource', side_effect=side_effect) as mock_require:
            result = _require_nfs4_texture_archive('games/nfs4/Data/Tracks/GT1/Trn.frd')
            self.assertEqual(result, 'result')
            mock_require.assert_any_call('games/nfs4/Data/Tracks/GT1/Trn0.QFS__data')
            mock_require.assert_called_with('games/nfs4/Data/Tracks/GT1/Tr0.QFS__data')

    def test_forward_track_has_no_fallback(self):
        with patch(
            'library.require_resource', side_effect=FileNotFoundError(2, 'No such file or directory')
        ) as mock_require:
            with self.assertRaises(FileNotFoundError):
                _require_nfs4_texture_archive('games/nfs4/Data/Tracks/GT1/Tr.frd')
            mock_require.assert_called_once_with('games/nfs4/Data/Tracks/GT1/Tr0.QFS__data')

    def test_raises_when_no_candidate_exists(self):
        with patch('library.require_resource', side_effect=FileNotFoundError(2, 'No such file or directory')):
            with self.assertRaises(FileNotFoundError):
                _require_nfs4_texture_archive('games/nfs4/Data/Tracks/GT1/Trn.frd')


class TestTrackPropRotation(unittest.TestCase):
    def test_exported_quaternion_should_rotate_like_game_one(self):
        import math
        import random

        from serializers.maps import _quaternion_to_export_axes, _rotate_by_quaternion, _to_export_axes

        rnd = random.Random(1)
        for _ in range(100):
            q = [rnd.uniform(-1, 1) for _ in range(4)]
            length = math.sqrt(sum(c * c for c in q))
            q = tuple(c / length for c in q)
            v = [rnd.uniform(-5, 5) for _ in range(3)]
            w, x, y, z = _quaternion_to_export_axes(q)
            expected = _to_export_axes(_rotate_by_quaternion(q, v))
            actual = _rotate_by_quaternion((x, y, z, w), _to_export_axes(v))
            for a, b in zip(expected, actual):
                self.assertAlmostEqual(a, b)


class TestEacTrackSerializers(unittest.TestCase):
    def _serialize(self, path, out_dir, **settings):
        import shutil

        from library import require_file

        (name, block, data) = require_file(path)
        serializer = block.serializer_class()()
        serializer.patch_settings(
            {
                'geometry__save_obj': True,
                'geometry__save_blend': False,
                'geometry__export_to_gg_web_engine': False,
                # serializer settings are shared by every instance
                'maps__save_all_lods': False,
                **settings,
            }
        )
        shutil.rmtree(out_dir, ignore_errors=True)
        return serializer.serialize(data, out_dir + '/', name, block)

    def test_frd_props_should_be_exported_as_dummies(self):
        import json
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, 'tr00')
            files = self._serialize(
                'test/golden_corpus/TR00.FRD', out, maps__save_as_chunked=True, maps__add_props_to_obj=False
            )
            # every model in its own folder, like other single models of the converter
            self.assertIn(os.path.join(out, 'props', 'xobj_0_0', 'geometry.obj'), files)
            with open(os.path.join(out, 'props', 'xobj_0_0', 'material.mtl')) as f:
                self.assertIn('map_Kd ../../textures/', f.read())
            with open(os.path.join(out, 'terrain_chunk_75_extra.json')) as f:
                dummies = json.load(f)['dummies']
            windmill = next(d for d in dummies if d['properties']['model_ref_id'] == 'xobj_302_0')
            self.assertEqual(windmill['properties']['type'], 'model')
            animation = json.loads(windmill['properties']['animation'])
            self.assertEqual(animation['delay'], 6)
            self.assertEqual(animation['frame_duration'], 6 / 64)
            self.assertEqual(len(animation['frames']), 17)
            self.assertEqual(animation['frames'][0]['position'], windmill['position'])
            # COL objects of NFS3 don't have known textures
            col_dummies = []
            for name in os.listdir(out):
                if name.endswith('_extra.json'):
                    with open(os.path.join(out, name)) as f:
                        col_dummies += [
                            d for d in json.load(f)['dummies'] if d['properties']['model_ref_id'].startswith('col_')
                        ]
            self.assertEqual(len(col_dummies), 2)
            self.assertTrue(all(d['properties']['is_unknown'] for d in col_dummies))

    def test_frd_route_should_be_the_col_slices(self):
        import json
        import math
        import os
        import tempfile

        from library import require_file

        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, 'tr00')
            files = self._serialize(
                'test/golden_corpus/TR00.FRD', out, maps__save_as_chunked=True, maps__add_props_to_obj=False
            )
            self.assertIn(os.path.join(out, 'track_route.json'), files)
            with open(os.path.join(out, 'track_route.json')) as f:
                route = json.load(f)
        (_, _, frd) = require_file('test/golden_corpus/TR00.FRD')
        # chunk files are placed at the block positions
        self.assertEqual(route['chunks'], [b['position'] for b in frd['blocks']])
        # the golden corpus TR00.COL is NFS2's, its slices don't fit the track: the block positions
        self.assertEqual([p['position'] for p in route['points']], route['chunks'])

        from serializers.maps import nfs3_track_route

        (_, _, col) = require_file('test/samples/NFS3_TR00.COL')
        route = nfs3_track_route(frd, col)
        slices = [r for x in col['extrablocks'] if x['type'] == 'collision_data' for r in x['data_records']['data']]
        self.assertTrue(route['closed'])
        self.assertEqual(len(route['points']), sum(len(b['positions']) for b in frd['blocks']))
        self.assertEqual([p['position'] for p in route['points']], [s['position'] for s in slices])
        # the heading points to the next slice
        a, b = slices[100]['position'], slices[101]['position']
        heading = math.atan2(b['x'] - a['x'], b['z'] - a['z'])
        self.assertAlmostEqual(route['points'][100]['orientation'], heading, delta=0.1)
        # Hometown has no shortcuts
        self.assertEqual(route['roads'], [])

    def test_nfs3_shortcuts_should_join_the_middle_slices_of_a_run(self):
        from serializers.maps import nfs3_track_route

        def position(alt_1=-1, alt_2=-1):
            return {'alt_slice_1': alt_1, 'alt_slice_2': alt_2}

        # 16 slices; slices 2..4 and 12..10 name each other (one shortcut), slice 7 and 14 another one
        alts = {2: (12, -1), 3: (11, -1), 4: (10, -1), 10: (4, -1), 11: (3, -1), 12: (2, -1), 7: (-1, 14), 14: (-1, 7)}
        positions = [position(*alts.get(i, (-1, -1))) for i in range(16)]
        frd = {
            'blocks': [
                {'position': {'x': 0, 'y': 0, 'z': 0}, 'positions': positions[:8]},
                {'position': {'x': 0, 'y': 0, 'z': 48}, 'positions': positions[8:]},
            ]
        }
        col = {
            'extrablocks': [
                {
                    'type': 'collision_data',
                    'data_records': {
                        'data': [
                            {'position': {'x': i, 'y': 1, 'z': 6 * i}, 'forward': {'x': 0, 'y': 0, 'z': 1}}
                            for i in range(16)
                        ]
                    },
                }
            ]
        }
        route = nfs3_track_route(frd, col)
        self.assertEqual(len(route['points']), 16)
        self.assertEqual(route['points'][0]['orientation'], 0)
        self.assertEqual(
            [[p['x'] for p in road['points']] for road in route['roads']],
            [[3, 11], [7, 14]],
        )
        self.assertFalse(any(road['closed'] for road in route['roads']))
        # without COL slices: the block positions
        route = nfs3_track_route(frd, None)
        self.assertEqual([p['position'] for p in route['points']], route['chunks'])
        self.assertEqual(route['roads'], [])

    def test_trk_props_should_be_baked_into_map(self):
        import json
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, 'tr02')
            self._serialize(
                'test/golden_corpus/TR02.TRK', out, maps__save_as_chunked=False, maps__add_props_to_obj=True
            )
            with open(os.path.join(out, 'map.obj')) as f:
                object_names = [line[2:].strip() for line in f if line.startswith('o ')]
            # props of the TRK blocks and of the COL file
            self.assertEqual(len({n.split('__')[0] for n in object_names if n.startswith('prop_')}), 333 + 176 + 82)
            with open(os.path.join(out, 'map_extra.json')) as f:
                objects = json.load(f)['objects']
            # the animated boat of the COL file
            self.assertTrue(objects)
            self.assertTrue(all(json.loads(o['animation'])['delay'] == 44 for o in objects.values()))
            # the road physics data next to the map
            with open(os.path.join(out, 'collision.json')) as f:
                self.assertEqual(json.load(f)['format_version'], 1)

    def test_trk_collision_json_should_hold_what_the_road_physics_reads(self):
        from library import require_file
        from serializers.maps import nfs2_collision_json

        _, _, data = require_file('test/golden_corpus/TR02.TRK')
        _, _, col = require_file('test/golden_corpus/TR02.COL')
        slices = next(eb['data_records']['data'] for eb in col['extrablocks'] if eb['type'] == 'collision_data')
        raw_blocks = [b for sb in data['superblocks'] for b in sb['blocks']]
        blocks = nfs2_collision_json(data)['blocks']
        self.assertEqual(len(blocks), len(raw_blocks))
        for i, (b, raw) in enumerate(zip(blocks, raw_blocks)):
            num_polygons = raw['num_high_polygons']
            self.assertEqual(len(b['polygons']), 4 * num_polygons, i)
            # one polygon_map record per high polygon, its road vectors in the block
            self.assertEqual(len(b['surfaces']), num_polygons, i)
            self.assertEqual(len(b['vectors']), num_polygons, i)
            self.assertTrue(all(v < len(b['road_vectors']) // 6 for v in b['vectors']), i)
            # one median record per slice of the block, each a run of high polygons
            self.assertEqual(len(b['medians']) // 4, min(8, len(slices) - b['first_slice']), i)
            for first, count in zip(b['medians'][0::4], b['medians'][1::4]):
                self.assertLessEqual(first + count, num_polygons, i)
            self.assertEqual(len(b['objects']) % 6, 0, i)
        self.assertEqual(sum(len(b['medians']) // 4 for b in blocks), len(slices))
        # the stored corner order A, B, C, D and the whole surface byte
        b, raw = blocks[18], raw_blocks[18]
        self.assertEqual(b['polygons'][:4], raw['high_polygons'][0]['vertices'])
        polygon_map = next(eb for eb in raw['extrablocks'] if eb['type'] == 'polygon_map')['data_records']['data']
        surface = polygon_map[0]['surface']
        self.assertEqual(b['surfaces'][0], surface['barriers'] << 7 | surface['objects'] << 6 | surface['type'])
        # vertices below nv8 from the next block's position, the others from this block's
        positions = data['block_positions']
        for vertex_i, pivot in [(0, positions[19]), (raw['nv8'], positions[18])]:
            v = raw['vertices'][vertex_i]
            for axis_i, a in enumerate('xyz'):
                self.assertAlmostEqual(b['vertices'][vertex_i * 3 + axis_i], pivot[a] + v[a], places=4)
        # solid and knockable objects, numbered in block order
        objects = [o for b in blocks for o in zip(*[b['objects'][k::6] for k in range(6)])]
        self.assertTrue(objects)
        self.assertEqual([o[4] for o in objects], list(range(len(objects))))
        self.assertTrue({o[5] for o in objects} <= {1, 2})

    def _obj_faces_by_mesh(self, path):
        faces, name = {}, None
        with open(path) as f:
            for line in f:
                if line.startswith('o '):
                    name = line[2:].strip()
                    faces.setdefault(name, 0)
                elif line.startswith('f '):
                    faces[name] += 1
        return faces

    def test_trk_should_export_the_nearest_level_of_detail_with_its_extra_set_and_road_lines(self):
        import os
        import tempfile

        from library import require_file
        from serializers.maps import nfs2_road_lines

        _, _, data = require_file('test/golden_corpus/TR02.TRK')
        _, _, col = require_file('test/golden_corpus/TR02.COL')
        slices = next(eb['data_records']['data'] for eb in col['extrablocks'] if eb['type'] == 'collision_data')
        blocks = [b for sb in data['superblocks'] for b in sb['blocks']]

        def road_lines(b):
            records = [r for eb in b['extrablocks'] if eb['type'] == 'road_lines' for r in eb['data_records']['data']]
            vertices = [[v['x'], v['y'], v['z']] for v in b['vertices']]
            return nfs2_road_lines(records, vertices, b['vertices'], slices, b['first_slice'])

        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, 'tr02')
            self._serialize(
                'test/golden_corpus/TR02.TRK', out, maps__save_as_chunked=True, maps__add_props_to_obj=False
            )
            for i in [0, 18, 100]:
                faces = self._obj_faces_by_mesh(os.path.join(out, f'terrain_chunk_{i}.obj'))
                terrain = sum(n for name, n in faces.items() if '__lin' not in name)
                lines = {name.split('__')[1]: n for name, n in faces.items() if '__lin' in name}
                # nfs2sen.exe draws the nearest blocks with polygon sets 4 and 5 (0x4361a0), then the road lines
                self.assertEqual(terrain, blocks[i]['num_high_polygons'] + blocks[i]['num_high_extra_polygons'], i)
                expected = {}
                for texture, _ in road_lines(blocks[i]):
                    expected[texture] = expected.get(texture, 0) + 1
                self.assertEqual(lines, expected, i)
                self.assertTrue(lines, i)
            self.assertTrue(any(b['num_high_extra_polygons'] for b in blocks))
            out = os.path.join(tmp, 'tr02_lods')
            self._serialize(
                'test/golden_corpus/TR02.TRK',
                out,
                maps__save_as_chunked=True,
                maps__add_props_to_obj=False,
                maps__save_all_lods=True,
            )
            faces = self._obj_faces_by_mesh(os.path.join(out, 'terrain_chunk_18.obj'))
        faces_by_lod = [0, 0, 0]
        for name, n in faces.items():
            if '_lod' in name and '__lin' not in name:
                faces_by_lod[int(name.split('_lod')[1][0])] += n
        b = blocks[18]
        self.assertEqual(
            faces_by_lod,
            [
                b['num_high_polygons'] + b['num_high_extra_polygons'],
                b['num_medium_polygons'] + b['num_medium_extra_polygons'],
                b['num_low_polygons'] + b['num_low_extra_polygons'],
            ],
        )
        # the road lines belong to the highest level
        self.assertTrue(all(name.startswith('block_18_lod0__') for name in faces if '__lin' in name))

    def test_nfs2_road_line_shapes_should_follow_nfs2sen(self):
        from serializers.maps import nfs2_road_line_quads

        # a strip quad 16 units wide (p1 on the side of the right vector) and 32 long: record A at z 0, B at z 32
        p0, p1, p2, p3 = [16, 0, 0], [0, 0, 0], [16, 0, 32], [0, 0, 32]
        full_right = [[0, 0, 0], [5, 0, 0], [5, 0, 32], [0, 0, 32]]
        full_left = [[11, 0, 0], [16, 0, 0], [16, 0, 32], [11, 0, 32]]
        # handlers 0x44bb00, 0x44b6e0, 0x44b250, 0x44a760, 0x44ace0, corners in slot order
        expected = {
            0: [('lin2', [[5, 0, 0], [11, 0, 0], [11, 0, 32], [5, 0, 32]])],
            1: [('lin2', [[5, 0, 16], [11, 0, 16], [11, 0, 32], [5, 0, 32]])],
            2: [('lin2', full_right), ('lin6', full_left)],
            3: [('lin2', full_right), ('lin6', [[11, 0, 16], [16, 0, 16], [16, 0, 32], [11, 0, 32]])],
            4: [('lin2', [[0, 0, 16], [5, 0, 16], [5, 0, 32], [0, 0, 32]]), ('lin6', full_left)],
        }
        for line_type, quads in expected.items():
            self.assertEqual(nfs2_road_line_quads(line_type, 0, p0, p1, p2, p3), quads, line_type)
            # 5..9: the same shapes, white
            white = [(t[:3] + str(int(t[3]) + 1), corners) for t, corners in quads]
            self.assertEqual(nfs2_road_line_quads(line_type + 5, 0, p0, p1, p2, p3), white, line_type)
        # the texture by sort key & 6 (table 0x4c6318), the second line's by [first + 2]
        for key, first, second in [
            (2, 'lin4', 'lin4'),
            (4, 'lin6', 'lin2'),
            (6, 'lin4', 'lin4'),
            (-6, 'lin4', 'lin4'),
            (-7, 'lin2', 'lin6'),
        ]:
            self.assertEqual([t for t, _ in nfs2_road_line_quads(2, key, p0, p1, p2, p3)], [first, second], key)
        self.assertEqual([t for t, _ in nfs2_road_line_quads(7, 4, p0, p1, p2, p3)], ['lin7', 'lin3'])
        self.assertEqual(nfs2_road_line_quads(10, 0, p0, p1, p2, p3), [])

    def test_nfs2_road_lines_should_place_strips_by_slices(self):
        from serializers.maps import nfs2_road_lines

        def vector(x, y, z):
            return {'x': x / 128, 'y': y / 128, 'z': z / 128}

        slices = [
            {'normal': vector(0, 127, 0), 'forward': vector(-3, 0, 100), 'right': vector(-100, 0, 0)},
            {'normal': vector(0, 127, 0), 'forward': vector(0, 0, 127), 'right': vector(-120, 0, 4)},
        ]
        vertices = [[1, 0, 2], [1, 0, 6], [9, 9, 9]]
        raw_vertices = [{'x': 0.5, 'y': 0, 'z': 0.25}, {'x': 1, 'y': 0, 'z': 6}, {'x': 9, 'y': 9, 'z': 9}]
        records = [
            {'vertex_idx': 0, 'slice': 0, 'line_type': 5, 'polygon_idx': 0},
            {'vertex_idx': 1, 'slice': 1, 'line_type': 0xFF, 'polygon_idx': 0},
            {'vertex_idx': 2, 'slice': 1, 'line_type': 5, 'polygon_idx': 0},
        ]
        lines = nfs2_road_lines(records, vertices, raw_vertices, slices, 0)
        # record 1 ends the strip, record 2 is the last one: one quad from records 0 and 1
        self.assertEqual(len(lines), 1)
        texture, corners = lines[0]
        # sort key 0.5 * 256 + 0.25 * 256 = 192: & 6 = 0, white: lin3
        self.assertEqual(texture, 'lin3')
        # P0 = vA - fA, P1 = vA + rA - fA, P2 = vB + fA, P3 = vB + rB + fA, fA = A's forward bytes >> 1 (-3 >> 1 = -2),
        # vertex units 1/256
        f = [-2 / 256, 0, 50 / 256]
        p0 = [1 - f[0], 0, 2 - f[2]]
        p1 = [1 - 100 / 256 - f[0], 0, 2 - f[2]]
        p2 = [1 + f[0], 0, 6 + f[2]]
        p3 = [1 - 120 / 256 + f[0], 0, 6 + 4 / 256 + f[2]]
        edge = lambda a, b: [a[k] + (b[k] - a[k]) * 5 / 16 for k in range(3)]
        expected = [edge(p1, p0), edge(p0, p1), edge(p2, p3), edge(p3, p2)]
        for corner, expected_corner in zip(corners, expected):
            for a, b in zip(corner, expected_corner):
                self.assertAlmostEqual(a, b)
        # a lift moves the points along the slices' normals
        lifted = nfs2_road_lines(records, vertices, raw_vertices, slices, 0, lift=0.02)[0][1]
        self.assertAlmostEqual(lifted[0][1], 0.02 * 127 / 128)

    def test_nfs4_frd_extra_objects_should_be_exported_as_dummies(self):
        import json
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, 'gt1')
            self._serialize(
                'test/golden_corpus/NFS4_GT1.FRD', out, maps__save_as_chunked=True, maps__add_props_to_obj=False
            )
            dummies = []
            for name in os.listdir(out):
                if name.endswith('_extra.json'):
                    with open(os.path.join(out, name)) as f:
                        dummies += json.load(f)['dummies']
            # 350 tree billboards of the blocks and 95 physics props of the global chunk
            self.assertEqual(len(dummies), 445)
            models = {d['properties']['model_ref_id'] for d in dummies}
            # the same models are exported once
            self.assertLess(len(models), 445)
            self.assertEqual(sorted(os.listdir(os.path.join(out, 'props'))), sorted(models))
            # physics props are rotated by their transform matrix
            self.assertTrue(any(d['quaternion'] != [1, 0, 0, 0] for d in dummies))

    def test_nfs4_frd_vroad_should_be_exported(self):
        import json
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, 'gt1')
            files = self._serialize(
                'test/golden_corpus/NFS4_GT1.FRD', out, maps__save_as_chunked=True, maps__add_props_to_obj=False
            )
            vroad_file = os.path.join(out, 'vroad.json')
            self.assertIn(vroad_file, files)
            with open(vroad_file) as f:
                vroad = json.load(f)
            self.assertEqual(len(vroad), 832)
            # positions and distances in meters, as the map: the file's times 1.3
            expected = {
                'ref_point': {'x': -1718.070556640625, 'y': -14.33489990234375, 'z': 374.81488037109375},
                'left_wall': 7.883923530578613,
                'right_wall': 15.767847061157227,
                'left_lane_width': 4.5,
                'right_lane_width': 4.5,
            }
            for k in 'xyz':
                self.assertAlmostEqual(vroad[0]['ref_point'][k], expected['ref_point'][k] * 1.3, places=4)
            for key in ['left_wall', 'right_wall', 'left_lane_width', 'right_lane_width']:
                self.assertAlmostEqual(vroad[0][key], expected[key] * 1.3, places=4)
            self.assertEqual(vroad[0]['normal'], {'x': 0.0, 'y': 0.984375, 'z': -0.0078125})
            self.assertEqual(vroad[0]['forward'], {'x': 0.421875, 'y': -0.0078125, 'z': -0.890625})
            self.assertEqual(vroad[0]['lane_open_bits'], 992)
            self.assertEqual(vroad[0]['left_side_type'], 4)

    def _obj_mesh_names(self, path):
        with open(path) as f:
            return [line[2:].strip() for line in f if line.startswith('o ')]

    def test_nfs4_frd_should_export_highest_lod_and_block_objects(self):
        import os
        import tempfile

        from library import require_file

        _, _, data = require_file('test/golden_corpus/NFS4_GT1.FRD')
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, 'gt1')
            self._serialize(
                'test/golden_corpus/NFS4_GT1.FRD', out, maps__save_as_chunked=True, maps__add_props_to_obj=False
            )
            names = self._obj_mesh_names(os.path.join(out, 'terrain_chunk_10.obj'))
            self.assertFalse(any('_lod' in n for n in names))
            with open(os.path.join(out, 'terrain_chunk_10.obj')) as f:
                faces = sum(1 for line in f if line.startswith('f '))
            block = data['blocks'][10]
            objects = sum(len(block[f'polygons_objects_{i}']) for i in range(4))
            self.assertGreater(objects, 0)
            # only chunks 4 and 5 of the terrain, and the objects: no lower levels of detail on top of each other
            self.assertEqual(
                faces, len(block['polygons_high_res_track']) + len(block['polygons_high_res_misc']) + objects
            )
            self.assertTrue(any(n.startswith('block_10_objects__') for n in names))

    def test_nfs4_frd_should_export_every_lod_with_setting(self):
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, 'gt1')
            self._serialize(
                'test/golden_corpus/NFS4_GT1.FRD',
                out,
                maps__save_as_chunked=True,
                maps__add_props_to_obj=False,
                maps__save_all_lods=True,
            )
            names = self._obj_mesh_names(os.path.join(out, 'terrain_chunk_10.obj'))
            for lod in range(3):
                self.assertTrue(any(n.startswith(f'block_10_lod{lod}__') for n in names), lod)
            # objects are drawn at every level of detail
            self.assertTrue(any(n.startswith('block_10_objects__') for n in names))

    def test_nfs4_frd_should_be_exported_in_meters(self):
        import json
        import math
        import os
        import tempfile

        from library import require_file

        _, _, data = require_file('test/golden_corpus/NFS4_GT1.FRD')
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, 'gt1')
            self._serialize(
                'test/golden_corpus/NFS4_GT1.FRD', out, maps__save_as_chunked=True, maps__add_props_to_obj=False
            )
            with open(os.path.join(out, 'map_extra.json')) as f:
                extra = json.load(f)
            # the road path goes through the block positions, times 1.3
            road_path = next(c for c in extra['curves'] if c['name'] == 'road_path')
            p = data['blocks_headers'][5]['position']
            self.assertTrue(math.dist(road_path['points'][5], [p['x'] * 1.3, p['z'] * 1.3, p['y'] * 1.3]) < 1e-3)
            # billboards (trees) are marked
            dummies = []
            for name in os.listdir(out):
                if name.endswith('_extra.json') and name.startswith('terrain_chunk_'):
                    with open(os.path.join(out, name)) as f:
                        dummies += json.load(f)['dummies']
            self.assertEqual(sum(1 for d in dummies if d['properties'].get('billboard')), 350)

    def test_nfs2_texture_uvs_should_follow_nfs2sen(self):
        import struct

        from resources.eac.maps import TexturesMapExtraDataRecord
        from serializers.maps import nfs2_texture_uvs

        # UVs (image space, v down) of the polygon vertices [v0, v1, v2, v3] as nfs2sen.exe gives them
        # (BWorld_SetupTextureOrders 0x4356e0, Tex_OrientCorners 0x475164, BWorld_AddTrackPolys 0x436ba0) for the
        # alignment values of the NFS2 and NFS2 SE tracks
        expected = {
            1: [[1, 0], [0, 0], [0, 1], [1, 1]],
            3: [[0, 0], [0, 1], [1, 1], [1, 0]],
            5: [[0, 1], [1, 1], [1, 0], [0, 0]],
            9: [[1, 1], [1, 0], [0, 0], [0, 1]],
            16: [[0, 0], [1, 0], [1, 1], [0, 1]],
            18: [[1, 0], [1, 1], [0, 1], [0, 0]],
            20: [[1, 1], [0, 1], [0, 0], [1, 0]],
            24: [[0, 1], [0, 0], [1, 0], [1, 1]],
        }
        block = TexturesMapExtraDataRecord()
        for value, uvs in expected.items():
            self.assertEqual(nfs2_texture_uvs(value), uvs, value)
            # the parsed bit field gives the same UVs and is written back as read
            raw = struct.pack('<HBB3B3B', 7, 0x30, value, 178, 178, 178, 4, 7, 0)
            record = block.unpack_from_bytes(raw)
            self.assertEqual(nfs2_texture_uvs(record['alignment']), uvs, value)
            self.assertEqual(block.pack(record), raw)
        # bits 0x01, 0x20, 0x80 change nothing; 0x40 mirrors top to bottom unless 0x10 is set
        self.assertEqual(nfs2_texture_uvs(0xA0), nfs2_texture_uvs(0))
        self.assertEqual(nfs2_texture_uvs(0x40), [[1, 1], [0, 1], [0, 0], [1, 0]])
        self.assertEqual(nfs2_texture_uvs(0x50), nfs2_texture_uvs(0x10))
        record = block.unpack_from_bytes(struct.pack('<HBB3B3B', 7, 0x34, 1, 0, 0, 0, 4, 7, 0))
        self.assertTrue(
            record['flags']['animated'] and record['flags']['color_keyed'] and record['flags']['double_sided']
        )
        self.assertEqual((record['animation_frames'], record['animation_delay'], record['unk']), (4, 7, 0))

    def test_shpi_texture_names_should_be_the_exported_file_names(self):
        from resources.eac.archives import ShpiBlock
        from serializers.maps import shpi_texture_names

        block = ShpiBlock()
        image = block.item_block.get_choice_index_by_class_name('EacImage')
        palette = next(
            i for i, b in enumerate(block.item_block.possible_blocks) if b.__class__.__name__ == 'EacPalette'
        )

        def child(alias, choice_index, data=None):
            return {'alias': alias, 'item': {'choice_index': choice_index, 'data': data or {}}}

        data = {
            'children': [
                child('CLIF', image),
                child('ROAD', image),
                child('CLIF', image),
                child('clif', image),
                child('!pal', palette),
                child('BAD!', image, Exception('not read')),
                child('CLIF', image),
            ]
        }
        # by SHPI index, as the polygons pick them: names repeat, case is ignored, palettes and items that could not
        # be read are not exported
        self.assertEqual(
            shpi_texture_names(block, data, False), ['CLIF', 'ROAD', 'CLIF0', 'clif1', None, None, 'CLIF2']
        )
        self.assertEqual(shpi_texture_names(block, data, True)[4], '!pal')

    def test_trk_textures_should_be_picked_by_qfs_index(self):
        import os
        import tempfile
        from copy import deepcopy

        from library import require_file
        from serializers import maps

        _, _, col = require_file('test/golden_corpus/TR02.COL')
        numbers = sorted({r['texture_number'] for r in col['extrablocks'][0]['data_records']['data']})[:3]
        require_sibling = maps._require_track_sibling

        def sibling_with_repeated_names(id, *file_names, sub_id=''):
            # the track QFS with three images used by the track named alike, as in NFS2 SE TR060.QFS
            (qfs_id, qfs_block, qfs_data), rest = require_sibling(id, *file_names, sub_id=sub_id)
            if not file_names[0].upper().endswith('.QFS'):
                return (qfs_id, qfs_block, qfs_data), rest
            qfs_data = deepcopy(qfs_data)
            for i, number in enumerate(numbers):
                qfs_data['children'][number]['alias'] = ['DUPE', 'DUPE', 'dupe'][i]
            return (qfs_id, qfs_block, qfs_data), rest

        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(maps, '_require_track_sibling', sibling_with_repeated_names),
        ):
            out = os.path.join(tmp, 'tr02')
            self._serialize(
                'test/golden_corpus/TR02.TRK', out, maps__save_as_chunked=False, maps__add_props_to_obj=True
            )
            textures = {os.path.splitext(x)[0] for x in os.listdir(os.path.join(out, 'textures'))}
            mesh_textures = {n.split('__', 1)[1] for n in self._obj_mesh_names(os.path.join(out, 'map.obj'))}
        self.assertTrue({'DUPE', 'DUPE0', 'dupe1'} <= textures)
        self.assertTrue({'DUPE', 'DUPE0', 'dupe1'} <= mesh_textures)
        # every textured mesh has its image (the road lines' lin<n> come from the game's RENDER/PC/DTEXTURE.FSH, which
        # the golden corpus does not have)
        self.assertEqual({t for t in mesh_textures - textures if not t.startswith('lin')}, set())

    def test_nfs4_polygon_uvs_should_follow_tex_flags(self):
        from serializers.maps import nfs4_polygon_uvs

        def flags(**patch):
            return {'rotation': 0, 'mirror_u': False, 'flip_v': False, 'uv_tiling': 'none', **patch}

        # nfs4.exe UV table 0x5aef6c entries 0, 1, 4, 8 and 32 (image space, v down), given to the polygon corners
        # 1, 0, 3, 2
        self.assertEqual(nfs4_polygon_uvs(flags()), [[1, 0], [0, 0], [0, 1], [1, 1]])
        self.assertEqual(nfs4_polygon_uvs(flags(rotation=1)), [[1, 1], [1, 0], [0, 0], [0, 1]])
        self.assertEqual(nfs4_polygon_uvs(flags(mirror_u=True)), [[0, 0], [1, 0], [1, 1], [0, 1]])
        self.assertEqual(nfs4_polygon_uvs(flags(flip_v=True)), [[1, 1], [0, 1], [0, 0], [1, 0]])
        self.assertEqual(nfs4_polygon_uvs(flags(uv_tiling='v2')), [[1, 0], [0, 0], [0, 2], [1, 2]])

    def _obj_colored_vertices(self, path):
        """(x, y, z, r, g, b) of the `v` lines of an OBJ"""
        with open(path) as f:
            return [tuple(float(x) for x in line.split()[1:]) for line in f if line.startswith('v ')]

    def _assert_corners_have_vertex_colors(self, obj_path, pivot, vertices, colors, scale=1):
        """Every vertex of the chunk OBJ (export axes, relative to the chunk `pivot`, game axes) has the colour of a
        track vertex (game axes, file units times `scale`) at its place"""
        import math

        by_position = {}
        for v, c in zip(vertices, colors):
            key = tuple(round(v[k] * scale, 2) for k in 'xyz')
            by_position.setdefault(key, set()).add(tuple(round(x, 6) for x in c))
        corners = self._obj_colored_vertices(obj_path)
        self.assertGreater(len(corners), 0)
        for x, y, z, *color in corners:
            self.assertEqual(len(color), 3)
            game = (x + pivot[0] * scale, z + pivot[1] * scale, y + pivot[2] * scale)
            key = tuple(round(c, 2) for c in game)
            near = by_position.get(key) or next(
                (cs for k, cs in by_position.items() if math.dist(k, game) < 0.02), set()
            )
            self.assertIn(tuple(round(c, 6) for c in color), near)

    def test_frd_meshes_should_have_the_vertex_shading_as_colors(self):
        import os
        import tempfile

        from library import require_file

        _, _, data = require_file('test/golden_corpus/TR00.FRD')
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, 'tr00')
            self._serialize(
                'test/golden_corpus/TR00.FRD', out, maps__save_as_chunked=True, maps__add_props_to_obj=False
            )
            # terrain and POLYOBJ objects of block 10: the block's shading (0xAARRGGBB) by vertex index; no HRZ next
            # to the golden corpus file: ambient 100 %
            block = data['blocks'][10]
            colors = [[(s >> k & 0xFF) / 255 for k in (16, 8, 0)] for s in block['vertex_shading']]
            p = block['position']
            self._assert_corners_have_vertex_colors(
                os.path.join(out, 'terrain_chunk_10.obj'), (p['x'], p['y'], p['z']), block['vertices'], colors
            )
            # an extra object: its own shading
            xobj = data['extraobject_blocks'][96][0]
            prop_colors = {
                tuple(round(c, 6) for c in v[3:])
                for v in self._obj_colored_vertices(os.path.join(out, 'props', 'xobj_96_0', 'geometry.obj'))
            }
            expected = {tuple(round((s >> k & 0xFF) / 255, 6) for k in (16, 8, 0)) for s in xobj['vertex_shading']}
            self.assertTrue(prop_colors and prop_colors <= expected)
            # COL props have no shading
            for v in self._obj_colored_vertices(os.path.join(out, 'props', 'col_0', 'geometry.obj')):
                self.assertEqual(len(v), 3)

    def test_frd_baked_col_props_should_get_white_vertex_colors(self):
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, 'tr00')
            self._serialize('test/golden_corpus/TR00.FRD', out, maps__save_as_chunked=True, maps__add_props_to_obj=True)
            white = 0
            for name in os.listdir(out):
                if name.startswith('terrain_chunk_') and name.endswith('.obj'):
                    corners = self._obj_colored_vertices(os.path.join(out, name))
                    # every mesh of a chunk has colours
                    self.assertTrue(all(len(v) == 6 for v in corners), name)
                    white += sum(1 for v in corners if v[3:] == (1.0, 1.0, 1.0))
            self.assertGreater(white, 0)

    def test_nfs4_frd_meshes_should_have_the_tinted_vertex_shading_as_colors(self):
        import os
        import tempfile
        from unittest.mock import patch

        from library import require_file
        from serializers.maps import nfs4_shading_tint

        _, _, data = require_file('test/golden_corpus/NFS4_GT1.FRD')
        block = data['blocks'][10]
        p = data['blocks_headers'][10]['position']
        for ambient in [(100, 100, 100), (110, 120, 130)]:
            with (
                tempfile.TemporaryDirectory() as tmp,
                patch('serializers.maps.nfs4_ambient_percent', return_value=ambient),
            ):
                out = os.path.join(tmp, 'gt1')
                self._serialize(
                    'test/golden_corpus/NFS4_GT1.FRD', out, maps__save_as_chunked=True, maps__add_props_to_obj=False
                )
                colors = [
                    [nfs4_shading_tint(s >> k & 0xFF, a) / 255 for k, a in zip((16, 8, 0), ambient)]
                    for s in block['vertex_shading']
                ]
                # terrain and block objects
                self._assert_corners_have_vertex_colors(
                    os.path.join(out, 'terrain_chunk_10.obj'),
                    (p['x'], p['y'], p['z']),
                    block['vertices'],
                    colors,
                    scale=1.3,
                )
                xobj = data['global_objects_1']['objects'][94]
                prop_colors = {
                    tuple(round(c, 6) for c in v[3:])
                    for v in self._obj_colored_vertices(os.path.join(out, 'props', 'xobj_global_1_94', 'geometry.obj'))
                }
                expected = {
                    tuple(round(nfs4_shading_tint(s >> k & 0xFF, a) / 255, 6) for k, a in zip((16, 8, 0), ambient))
                    for s in xobj['vertex_shading']
                }
                self.assertTrue(prop_colors and prop_colors <= expected)

    def test_shading_tints_should_follow_the_games(self):
        from serializers.maps import nfs3_shading_tint, nfs4_shading_tint, track_shading_colors

        # nfs3.exe 0x419660: c * p / 100
        self.assertEqual([nfs3_shading_tint(c, 100) for c in (0, 77, 255)], [0, 77, 255])
        self.assertEqual(nfs3_shading_tint(77, 50), 38)
        # nfs4.exe 0x432230: darker below 100, towards white above
        self.assertEqual([nfs4_shading_tint(c, 100) for c in (0, 77, 255)], [0, 77, 255])
        self.assertEqual(nfs4_shading_tint(77, 30), 23)
        self.assertEqual(nfs4_shading_tint(77, 110), 77 + 10 * 178 // 100)
        self.assertEqual(nfs4_shading_tint(255, 130), 255)
        self.assertEqual(nfs4_shading_tint(0, 130), 76)
        # 0xAARRGGBB, signed (NFS3 XOBJ) or not; the alpha is left out
        colors = track_shading_colors(
            [0xFF336699, 0x80336699 - (1 << 32), 0xFFFFFFFF], (100, 100, 100), nfs4_shading_tint
        )
        self.assertEqual(colors, [[0x33 / 255, 0x66 / 255, 0x99 / 255]] * 2 + [[1.0, 1.0, 1.0]])
        self.assertEqual(
            track_shading_colors([0xFF336699], (110, 120, 130), nfs4_shading_tint),
            [
                [
                    nfs4_shading_tint(0x33, 110) / 255,
                    nfs4_shading_tint(0x66, 120) / 255,
                    nfs4_shading_tint(0x99, 130) / 255,
                ]
            ],
        )

    def test_ambient_light_should_come_from_the_track_settings(self):
        import os
        import shutil
        import tempfile

        from library.loader import path_to_name
        from serializers.maps import nfs3_ambient_percent, nfs4_ambient_percent, nfs4_track_ini_name

        with tempfile.TemporaryDirectory() as tmp:
            tmp = tmp.replace('\\', '/')
            # NFS3: the day HRZ
            shutil.copy('test/samples/NFS3_3TR00.HRZ', os.path.join(tmp, '3tr00.hrz'))
            self.assertEqual(nfs3_ambient_percent(path_to_name(f'{tmp}/TR00.FRD')), (100, 100, 100))
            self.assertEqual(nfs3_ambient_percent(path_to_name(f'{tmp}/TR01.FRD')), (100, 100, 100))
            with open('test/samples/NFS3_3TR00.HRZ', 'rb') as f:
                hrz = f.read()
            # the last three numbers are the ambient light
            with open(os.path.join(tmp, '3TR02.HRZ'), 'wb') as f:
                f.write(hrz.rstrip().rstrip(b'0123456789,') + b'50,60,70\r\n')
            self.assertEqual(nfs3_ambient_percent(path_to_name(f'{tmp}/TR02.FRD')), (50, 60, 70))
            # NFS4: Tr.ini for the day track, TrN.ini for the night one
            self.assertEqual(nfs4_track_ini_name(path_to_name(f'{tmp}/Tr.frd')), 'Tr.ini')
            self.assertEqual(nfs4_track_ini_name(path_to_name(f'{tmp}/Trn.frd')), 'TrN.ini')
            self.assertEqual(nfs4_ambient_percent(path_to_name(f'{tmp}/Tr.frd')), (100, 100, 100))
            with open(os.path.join(tmp, 'tr.ini'), 'w') as f:
                f.write('[light]\r\nAmbientRed=110\r\nAmbientGreen=120\r\nAmbientBlue=130\r\nlightTheta=0.60\r\n')
            with open(os.path.join(tmp, 'TrN.ini'), 'w') as f:
                f.write('[light]\r\nAmbientRed=80\r\n')
            self.assertEqual(nfs4_ambient_percent(path_to_name(f'{tmp}/Tr.frd')), (110, 120, 130))
            self.assertEqual(nfs4_ambient_percent(path_to_name(f'{tmp}/Trn.frd')), (80, 100, 100))

    def test_prop_models_with_other_colors_should_stay_apart(self):
        from serializers.common.three_d import Mesh
        from serializers.maps import _deduplicate_models

        def model(color):
            m = Mesh()
            m.vertices = [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]]
            m.vertex_uvs = [[0, 0], [1, 0], [1, 1], [0, 1]]
            m.vertex_colors = [color] * 4
            m.polygons = [[0, 1, 2, 3]]
            m.texture_ids = ['tex']
            return m

        models = {'a': model([1, 1, 1]), 'b': model([1, 1, 1]), 'c': model([0.5, 0.5, 0.5])}
        self.assertEqual(_deduplicate_models(models), {'a': 'a', 'b': 'a', 'c': 'c'})


class TestTriMapSerializer(unittest.TestCase):
    def _serialize(self, out_dir, chunks_per_file):
        import json
        import os

        from library import require_file

        (name, block, data) = require_file('test/golden_corpus/AL1.TRI')
        serializer = block.serializer_class()()
        serializer.patch_settings(
            {
                'geometry__save_obj': True,
                'geometry__save_blend': False,
                'geometry__export_to_gg_web_engine': False,
                'maps__save_as_chunked': True,
                'maps__add_props_to_obj': False,
                'maps__tnfs_chunks_per_file': chunks_per_file,
            }
        )
        serializer.serialize(data, out_dir + '/', name, block)
        with open(os.path.join(out_dir, 'map_extra.json')) as f:
            chunks = {d['properties']['chunk']: d for d in json.load(f)['dummies'] if d['properties'].get('is_chunk')}
        # world positions of the props by object index, mesh names of every file
        props, mesh_names = {}, {}
        for chunk_name, chunk in chunks.items():
            extra_path = os.path.join(out_dir, f'{chunk_name}_extra.json')
            if os.path.exists(extra_path):
                with open(extra_path) as f:
                    for d in json.load(f)['dummies']:
                        props[d['properties']['object_index']] = [
                            round(d['position'][k] + chunk['position'][k], 3) for k in range(3)
                        ]
            with open(os.path.join(out_dir, f'{chunk_name}.obj')) as f:
                mesh_names[chunk_name] = [line[2:].strip() for line in f if line.startswith('o ')]
        return chunks, props, mesh_names

    def test_chunks_per_file_should_merge_chunks(self):
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            chunks_1, props_1, _ = self._serialize(os.path.join(tmp, 'one'), 1)
            chunks_7, props_7, mesh_names = self._serialize(os.path.join(tmp, 'seven'), 7)
        # 520 TRI chunks: 74 files of 7 chunks, the last one of 2
        self.assertEqual(len(chunks_1), 520)
        self.assertEqual(len(chunks_7), 75)
        self.assertEqual(chunks_7['terrain_block7_1']['position'], chunks_1['terrain_chunk_7']['position'])
        self.assertEqual(chunks_7['terrain_block7_73']['properties']['children'], ['chunk_74'])
        # opened track
        self.assertNotIn('children', chunks_7['terrain_block7_74']['properties'])
        self.assertEqual(props_7, props_1)
        # one mesh per texture, the texture after the last "_"
        for chunk_name, names in mesh_names.items():
            self.assertEqual(len(names), len(set(names)))
            for name in names:
                self.assertTrue(name.startswith(f'{chunk_name}_background/'))

    def test_tri_partial_chunk_export_should_match_full_export(self):
        import filecmp
        import os
        import tempfile

        from library import require_file
        from serializers import get_serializer

        (name, block, data) = require_file('test/samples/AL1.TRI')
        serializer = get_serializer(block, data)
        with tempfile.TemporaryDirectory() as full, tempfile.TemporaryDirectory() as partial:
            serializer.patch_settings(
                {
                    'maps__save_as_chunked': True,
                    'maps__tnfs_chunks_per_file': 1,
                    'maps__add_props_to_obj': False,
                    'geometry__save_obj': True,
                    'geometry__save_blend': False,
                    'geometry__export_to_gg_web_engine': False,
                }
            )
            serializer.serialize(data, full, name, block)
            lane_merges = [
                i for i in range(len(data['terrain'])) if data['road_spline'][i * 4]['item_mode'] == 'lane_merge'
            ]
            chunks = [0, 10, len(data['terrain']) - 1] + [i + 1 for i in lane_merges]
            result = serializer.serialize_chunks(data, partial, name, block, chunks)
            self.assertEqual(sorted(result['chunks']), sorted(set(chunks)))
            for i in chunks:
                for suffix in ('.obj', '_extra.json'):
                    file = f'terrain_chunk_{i}{suffix}'
                    self.assertEqual(os.path.exists(f'{full}/{file}'), os.path.exists(f'{partial}/{file}'), file)
                    if os.path.exists(f'{full}/{file}'):
                        self.assertTrue(filecmp.cmp(f'{full}/{file}', f'{partial}/{file}', shallow=False), file)

    def test_tri_partial_chunk_export_should_drop_only_changed_chunks(self):
        import os
        import tempfile
        from copy import deepcopy

        from library import require_file
        from library.spatial_edit import apply_spatial_move
        from serializers import get_serializer

        (name, block, data) = require_file('test/samples/AL1.TRI')
        data = deepcopy(data)
        serializer = get_serializer(block, data)
        with tempfile.TemporaryDirectory() as path:
            first = serializer.serialize_chunks(data, path, name, block, list(range(5, 15)))
            mtime = os.path.getmtime(f'{path}/terrain_chunk_12.obj')
            handle = block.spatial_handle(data, 'terrain_vertex', '10/0/3')
            position = [handle['position'][0] + 1, handle['position'][1], handle['position'][2]]
            apply_spatial_move(name, block, data, 'terrain_vertex', '10/0/3', position, None)
            # the vertex is in the chunks 9 (its next chunk's first row) and 10, chunk 11 has chunk 10 as previous
            fingerprints = serializer.chunk_fingerprints(data, name)
            changed = [i for i in range(5, 15) if fingerprints[i] != first['chunks'][i]['fingerprint']]
            self.assertEqual(changed, [9, 10, 11])
            second = serializer.serialize_chunks(data, path, name, block, [10, 12])
            self.assertNotEqual(second['chunks'][10]['fingerprint'], first['chunks'][10]['fingerprint'])
            # changed chunks not asked for are deleted, the others stay as they were
            self.assertFalse(os.path.exists(f'{path}/terrain_chunk_9.obj'))
            self.assertFalse(os.path.exists(f'{path}/terrain_chunk_11.obj'))
            self.assertTrue(os.path.exists(f'{path}/terrain_chunk_13.obj'))
            self.assertEqual(os.path.getmtime(f'{path}/terrain_chunk_12.obj'), mtime)
