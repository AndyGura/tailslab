import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from serializers.common.three_d import Scene, SubMesh, export_scenes
from serializers.common.three_d import scenes as scenes_module


class _Settings:
    geometry__save_obj = True
    geometry__save_blend = False
    geometry__export_to_gg_web_engine = False


class TestExportScenes(unittest.TestCase):
    def test_scenes_with_same_file_names_should_go_to_their_directories(self):
        def scene(directory):
            mesh = SubMesh()
            mesh.name = 'mesh__tex'
            mesh.vertices = [[0, 0, 0], [1, 0, 0], [0, 1, 0]]
            mesh.vertex_uvs = [[0, 0], [1, 0], [0, 1]]
            mesh.polygons = [[0, 1, 2]]
            mesh.texture_id = 'tex'
            return Scene(
                name='body',
                sub_meshes=[mesh],
                obj_name='geometry',
                mtl_name='material',
                mtl_texture_names=['tex'],
                mtl_texture_path_func=lambda x: f'../../textures/{x}.png',
                dummies=[{'name': 'd', 'position': [0, 0, 0], 'properties': {}}],
                directory=directory,
            )

        with tempfile.TemporaryDirectory() as tmp:
            files = export_scenes([scene('a/'), scene('b/')], tmp + '/', _Settings())
            for directory in ['a', 'b']:
                for name in ['geometry.obj', 'geometry_extra.json', 'material.mtl']:
                    self.assertIn(os.path.join(tmp, directory, name), files)
                with open(os.path.join(tmp, directory, 'geometry.obj')) as f:
                    self.assertTrue(f.read().startswith('mtllib material.mtl'))


class _GgSettings(_Settings):
    geometry__export_to_gg_web_engine = True


_OLD_EXPORTER = 'def export_glb_meta(filepath, export_materials=True, copyright=""):\n    pass\n'
_NEW_EXPORTER = (
    'def export_glb_meta(filepath, export_materials=True, copyright="", export_normals=True, '
    'export_tangents=True):\n    pass\n'
)


class TestExportScenesGlbOptions(unittest.TestCase):
    def _export(self, scenes, exporter_source):
        """The generated Blender script, with an `exporter.py` of `exporter_source`"""
        with tempfile.TemporaryDirectory() as tmp:
            exporter_dir = os.path.join(tmp, 'exporter')
            os.makedirs(exporter_dir)
            with open(os.path.join(exporter_dir, 'exporter.py'), 'w') as f:
                f.write(exporter_source)
            with (
                patch.object(scenes_module, 'ensure_gg_web_engine_exporter_installed', return_value=exporter_dir),
                patch.object(scenes_module, 'run_blender') as run_blender,
                patch.object(scenes_module, '_warned_missing_export_options', False),
            ):
                export_scenes(scenes, tmp + '/', _GgSettings())
            return run_blender.call_args.kwargs['script']

    def test_scene_without_normals_passes_the_exporter_options(self):
        script = self._export([Scene(name='a', directory='a/', export_normals=False)], _NEW_EXPORTER)
        self.assertIn('def _gg_export_options(', script)
        self.assertIn(
            'copyright="Gurakl Games", **_gg_export_options(export_normals=False, export_tangents=False))', script
        )

    def test_default_scene_script_is_unchanged(self):
        script = self._export([Scene(name='a', directory='a/')], _OLD_EXPORTER)
        self.assertNotIn('_gg_export_options', script)
        self.assertIn('export_materials=True, copyright="Gurakl Games")\n', script)

    def test_warns_when_the_exporter_has_no_normals_options(self):
        with self.assertLogs(level='WARNING') as logs:
            self._export([Scene(name='a', directory='a/', export_normals=False)], _OLD_EXPORTER)
        self.assertIn('export_normals', '\n'.join(logs.output))

    def test_no_warning_when_the_exporter_has_the_options(self):
        with self.assertNoLogs(level='WARNING'):
            self._export([Scene(name='a', directory='a/', export_normals=False)], _NEW_EXPORTER)


class TestMetaOnlyCurveProperties(unittest.TestCase):
    """Curve properties that Blender ID properties can't carry go into the `.meta` after the export"""

    def test_lists_of_objects_skip_blender_and_land_in_the_meta(self):
        normals = [{'x': 1.0, 'y': 0.0, 'z': 0.0}, {'x': 0.0, 'y': -1.0, 'z': 0.5}]
        curve = {
            'name': 'road_path',
            'closed': False,
            'points': [[0, 0, 0], [0, 1, 0]],
            'properties': {'slope': [0.0, 0.25], 'side_normal': normals},
        }
        exported_meta = {
            'formatVersion': 2,
            'curves': [{'name': 'road_path', 'cyclic': False, 'points': [], 'slope': [0.0, 0.25]}],
            'dummies': [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            blender_extras = {}

            def run_blender(path, script):
                # what Blender gets, and the `.meta` the gg-web-engine exporter writes (`json.dump` defaults)
                with open(os.path.join(tmp, 'map_extra.json')) as f:
                    blender_extras.update(json.load(f))
                with open(os.path.join(tmp, 'map.meta'), 'w') as f:
                    json.dump(exported_meta, f)

            with (
                patch.object(scenes_module, 'ensure_gg_web_engine_exporter_installed', return_value=tmp),
                patch.object(scenes_module, 'run_blender', side_effect=run_blender),
            ):
                export_scenes([Scene(name='map', obj_name='map', curves=[curve])], tmp + '/', _GgSettings())
            with open(os.path.join(tmp, 'map.meta')) as f:
                meta_text = f.read()

        self.assertEqual(blender_extras['curves'][0]['properties'], {'slope': [0.0, 0.25]})
        self.assertEqual(curve['properties']['side_normal'], normals)
        expected = {**exported_meta, 'curves': [{**exported_meta['curves'][0], 'side_normal': normals}]}
        self.assertEqual(meta_text, json.dumps(expected))

    def test_meta_is_untouched_without_such_properties(self):
        with tempfile.TemporaryDirectory() as tmp:
            meta_path = os.path.join(tmp, 'map.meta')
            with open(meta_path, 'w') as f:
                f.write('{"curves": [{"name": "c"}]}')
            scenes_module._add_meta_curve_properties(meta_path, [{'name': 'c', 'properties': {'a': [1, 2]}}])
            with open(meta_path) as f:
                self.assertEqual(f.read(), '{"curves": [{"name": "c"}]}')


class TestGgExportOptionsScript(unittest.TestCase):
    """The Blender script helper, run against exporters with other signatures"""

    def _options(self, export_glb_meta, **options):
        exporter = type('Exporter', (), {'export_glb_meta': staticmethod(export_glb_meta)})
        namespace = {'gg_web_engine_exporter': exporter}
        exec(scenes_module._GG_EXPORT_OPTIONS_SCRIPT, namespace)
        # the Blender log gets a warning for the dropped ones
        with redirect_stdout(io.StringIO()):
            return namespace['_gg_export_options'](**options)

    def test_old_exporter_gets_no_options(self):
        def export_glb_meta(filepath, export_materials=True, copyright=''):
            pass

        self.assertEqual(self._options(export_glb_meta, export_normals=False, export_tangents=False), {})

    def test_new_exporter_gets_the_options(self):
        def export_glb_meta(filepath, export_materials=True, copyright='', export_normals=True, export_tangents=True):
            pass

        options = {'export_normals': False, 'export_tangents': False}
        self.assertEqual(self._options(export_glb_meta, **options), options)

    def test_only_accepted_options_and_any_with_kwargs(self):
        def partial(filepath, export_normals=True):
            pass

        def any_kwargs(filepath, **kwargs):
            pass

        self.assertEqual(self._options(partial, export_normals=False, export_tangents=False), {'export_normals': False})
        self.assertEqual(self._options(any_kwargs, export_tangents=False), {'export_tangents': False})
