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
