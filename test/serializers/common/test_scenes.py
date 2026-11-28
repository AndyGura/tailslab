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
                # no GLB without Blender
                patch.object(scenes_module, 'add_glb_vertex_attributes'),
            ):
                export_scenes(scenes, tmp + '/', _GgSettings())
            return run_blender.call_args.kwargs['script']

    def test_scene_without_normals_passes_the_exporter_options(self):
        script = self._export([Scene(name='a', directory='a/', export_normals=False)], _NEW_EXPORTER)
        self.assertIn('def _gg_export_options(', script)
        self.assertIn(
            'copyright="Gurakl Games", **_gg_export_options(export_normals=False, export_tangents=False))', script
        )

    def test_scene_with_vertex_colors_gets_no_blender_colors(self):
        mesh = SubMesh()
        mesh.name = 'block_0__tex'
        mesh.vertices = [[0, 0, 0], [1, 0, 0], [0, 1, 0]]
        mesh.vertex_uvs = [[0, 0], [1, 0], [0, 1]]
        mesh.vertex_colors = [[1, 1, 1], [0.5, 0.5, 0.5], [0, 0, 0]]
        mesh.polygons = [[0, 1, 2]]
        mesh.texture_id = 'tex'
        script = self._export(
            [Scene(name='a', directory='a/', sub_meshes=[mesh]), Scene(name='b', directory='b/')], _NEW_EXPORTER
        )
        # COLOR_0 comes from `add_glb_vertex_attributes`, with the values as they are
        self.assertIn('copyright="Gurakl Games", **_gg_export_options(export_vertex_color=\'NONE\'))', script)
        self.assertIn('/b", export_materials=True, copyright="Gurakl Games")\n', script)
        script = self._export([Scene(name='a', directory='a/', sub_meshes=[mesh], export_normals=False)], _NEW_EXPORTER)
        self.assertIn(
            "**_gg_export_options(export_normals=False, export_tangents=False, export_vertex_color='NONE'))",
            script,
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


class TestMetaExtras(unittest.TestCase):
    """`Scene.meta_extras` become top level keys of the `.meta`, after the exporter's own ones"""

    def test_keys_are_added_after_the_exported_ones(self):
        exported_meta = {'formatVersion': 2, 'curves': [], 'dummies': [{'name': 'd'}], 'rigidBodies': []}
        half_size = {'x': 1.25, 'y': 0.5, 'z': 2.75}
        with tempfile.TemporaryDirectory() as tmp:
            blender_extras = {}

            def run_blender(path, script):
                with open(os.path.join(tmp, 'geometry_extra.json')) as f:
                    blender_extras.update(json.load(f))
                with open(os.path.join(tmp, 'body.meta'), 'w') as f:
                    json.dump(exported_meta, f)

            scene = Scene(
                name='body',
                dummies=[{'name': 'd', 'position': [0, 0, 0]}],
                meta_extras={'collisionHalfSize': half_size},
            )
            with (
                patch.object(scenes_module, 'ensure_gg_web_engine_exporter_installed', return_value=tmp),
                patch.object(scenes_module, 'run_blender', side_effect=run_blender),
            ):
                export_scenes([scene], tmp + '/', _GgSettings())
            with open(os.path.join(tmp, 'body.meta')) as f:
                meta_text = f.read()

        self.assertNotIn('collisionHalfSize', blender_extras)
        # the exporter's part of the file is unchanged
        self.assertEqual(
            meta_text, json.dumps(exported_meta)[:-1] + ', "collisionHalfSize": ' + json.dumps(half_size) + '}'
        )

    def test_meta_is_untouched_without_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            meta_path = os.path.join(tmp, 'body.meta')
            with open(meta_path, 'w') as f:
                f.write('{"curves": []}')
            scenes_module._add_meta_top_level_keys(meta_path, {})
            with open(meta_path) as f:
                self.assertEqual(f.read(), '{"curves": []}')


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


def _colored_scene(directory: str = '') -> Scene:
    """A scene of a mesh with RGBA vertex colours and a mesh without colours, one texture"""
    colored = SubMesh()
    colored.name = 'block_0__tex'
    colored.vertices = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]]
    colored.vertex_uvs = [[0, 0], [1, 0], [0, 1], [1, 1]]
    colored.vertex_colors = [[0.25, 0.5, 1.0, 1.0], [1.0, 0.0, 0.5, 0.5], [0.0, 0.0, 0.0, 1.0], [1.0, 1.0, 1.0, 1.0]]
    colored.polygons = [[0, 1, 2], [2, 1, 3]]
    colored.texture_id = 'tex'
    plain = SubMesh()
    plain.name = 'block_1__tex'
    plain.vertices = [[3, 0, 0], [4, 0, 0], [3, 1, 0]]
    plain.vertex_uvs = [[0, 0], [1, 0], [0, 1]]
    plain.polygons = [[0, 1, 2]]
    plain.texture_id = 'tex'
    return Scene(
        name='map',
        obj_name='map',
        sub_meshes=[colored, plain],
        mtl_texture_names=['tex'],
        mtl_texture_path_func=lambda x: f'{x}.png',
        directory=directory,
    )


def _obj_vertex_lines(path: str) -> dict:
    """Object name -> its `v` lines of an OBJ file"""
    objects = {}
    name = None
    with open(path) as f:
        for line in f:
            if line.startswith('o '):
                name = line[2:].strip()
                objects[name] = []
            elif line.startswith('v '):
                objects[name].append(line.strip())
    return objects


class TestExportScenesVertexColors(unittest.TestCase):
    def test_obj_has_the_colors_of_the_colored_meshes(self):
        with tempfile.TemporaryDirectory() as tmp:
            export_scenes([_colored_scene()], tmp + '/', _Settings())
            vertices = _obj_vertex_lines(os.path.join(tmp, 'map.obj'))
        # the alpha left out
        self.assertEqual(
            vertices['block_0__tex'],
            ['v 0 0 0 0.25 0.5 1.0', 'v 1 0 0 1.0 0.0 0.5', 'v 0 1 0 0.0 0.0 0.0', 'v 1 1 0 1.0 1.0 1.0'],
        )
        self.assertEqual(vertices['block_1__tex'], ['v 3 0 0', 'v 4 0 0', 'v 3 1 0'])

    def test_glb_gets_the_colors_as_color_0(self):
        from serializers.common.three_d.glb_morph_targets import read_accessor, read_glb
        from test.serializers.test_geometries import write_glb_of_sub_meshes

        scene = _colored_scene()
        with tempfile.TemporaryDirectory() as tmp:
            scripts = []

            def run_blender(path, script):
                # the GLB and `.meta` the gg-web-engine exporter writes of the OBJ: no COLOR_0
                scripts.append(script)
                write_glb_of_sub_meshes(os.path.join(tmp, 'map.glb'), scene.sub_meshes)
                with open(os.path.join(tmp, 'map.meta'), 'w') as f:
                    json.dump({'formatVersion': 2, 'curves': [], 'dummies': []}, f)

            with (
                patch.object(scenes_module, 'ensure_gg_web_engine_exporter_installed', return_value=tmp),
                patch.object(scenes_module, 'run_blender', side_effect=run_blender),
            ):
                files = export_scenes([scene], tmp + '/', _GgSettings())
            gltf, binary = read_glb(os.path.join(tmp, 'map.glb'))
        self.assertIn(os.path.join(tmp, 'map.glb'), [os.path.normpath(x) for x in files])
        # Blender writes no COLOR_0 of its own: the converter's are the values as they are
        self.assertIn("export_vertex_color='NONE'", scripts[0])
        nodes = {node['name']: gltf['meshes'][node['mesh']]['primitives'][0] for node in gltf['nodes']}
        colors = nodes['block_0__tex']['attributes']['COLOR_0']
        self.assertEqual(gltf['accessors'][colors]['type'], 'VEC4')
        # the test GLB has the vertices in reversed order
        self.assertEqual(
            read_accessor(gltf, binary, colors),
            [(1.0, 1.0, 1.0, 1.0), (0.0, 0.0, 0.0, 1.0), (1.0, 0.0, 0.5, 0.5), (0.25, 0.5, 1.0, 1.0)],
        )
        self.assertNotIn('COLOR_0', nodes['block_1__tex']['attributes'])

    def test_glb_colors_of_corners_at_one_place_follow_their_triangles(self):
        # two triangles sharing an edge with corners of their own colours there (NFS5 track `fd` colours)
        from serializers.common.three_d.glb_morph_targets import add_glb_vertex_attributes, read_accessor, read_glb
        from test.serializers.test_geometries import write_glb_of_sub_meshes

        mesh = SubMesh()
        mesh.name = 'RD0000C_a0_LOD0_ai0_cla2'
        mesh.vertices = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]]
        mesh.vertex_uvs = [[0, 0], [1, 0], [0, 1], [1, 0], [1, 1], [0, 1]]
        mesh.vertex_colors = [[1.0, 0.0, 0.0, 1.0]] * 3 + [[0.0, 0.0, 1.0, 1.0]] * 3
        mesh.polygons = [[0, 1, 2], [3, 4, 5]]
        # and two triangles on top of each other, of other colours
        mesh.vertices += [[5, 0, 0], [6, 0, 0], [5, 1, 0]] * 2
        mesh.vertex_uvs += [[0, 0], [1, 0], [0, 1]] * 2
        mesh.vertex_colors += [[0.0, 1.0, 0.0, 1.0]] * 3 + [[1.0, 1.0, 0.0, 1.0]] * 3
        mesh.polygons += [[6, 7, 8], [9, 10, 11]]
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'map.glb')
            write_glb_of_sub_meshes(path, [mesh])
            with self.assertNoLogs(level='WARNING'):
                add_glb_vertex_attributes(path, [mesh])
            gltf, binary = read_glb(path)
        primitive = gltf['meshes'][0]['primitives'][0]
        colors = read_accessor(gltf, binary, primitive['attributes']['COLOR_0'])
        indices = [x[0] for x in read_accessor(gltf, binary, primitive['indices'])]
        triangle_colors = [{colors[i] for i in indices[k : k + 3]} for k in range(0, len(indices), 3)]
        self.assertEqual(triangle_colors[:2], [{(1.0, 0.0, 0.0, 1.0)}, {(0.0, 0.0, 1.0, 1.0)}])
        # one colour per triangle, each of the two
        self.assertEqual(sorted(triangle_colors[2:], key=sorted), [{(0.0, 1.0, 0.0, 1.0)}, {(1.0, 1.0, 0.0, 1.0)}])

    def test_glb_colors_of_meshes_of_one_name_go_to_their_nodes(self):
        # names cut to 27 characters repeat (NFSU car parts): Blender names the later objects "<name>.001"..., in no
        # fixed order, so the nodes are told apart by their positions
        from serializers.common.three_d.glb_morph_targets import add_glb_vertex_attributes, read_accessor, read_glb
        from test.serializers.test_geometries import write_glb_of_sub_meshes

        name = '350Z_KIT00_LEFT_SIDE_MIRRO__untextured'
        meshes = []
        # the third one has the places of the first one and more (a level of detail)
        for color, vertices in [
            ([1.0, 0.0, 0.0, 1.0], [[0, 0, 0], [1, 0, 0], [0, 1, 0]]),
            (None, [[5, 0, 0], [6, 0, 0], [5, 1, 0]]),
            ([0.0, 0.0, 1.0, 1.0], [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]]),
        ]:
            mesh = SubMesh()
            mesh.name = name
            mesh.vertices = vertices
            mesh.vertex_uvs = [[x, y] for x, y, _ in vertices]
            mesh.vertex_colors = [color] * len(vertices) if color else []
            mesh.polygons = [[0, 1, 2]] + ([[2, 1, 3]] if len(vertices) == 4 else [])
            meshes.append(mesh)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'body.glb')
            nodes = []
            for mesh, node_name in zip(meshes, [name + '.002', name, name + '.001']):
                node = SubMesh()
                node.name, node.vertices, node.vertex_uvs, node.polygons = (
                    node_name,
                    mesh.vertices,
                    mesh.vertex_uvs,
                    mesh.polygons,
                )
                nodes.append(node)
            write_glb_of_sub_meshes(path, nodes)
            add_glb_vertex_attributes(path, meshes)
            gltf, binary = read_glb(path)
        attributes = {n['name']: gltf['meshes'][n['mesh']]['primitives'][0]['attributes'] for n in gltf['nodes']}
        self.assertEqual(set(read_accessor(gltf, binary, attributes[name + '.002']['COLOR_0'])), {(1.0, 0.0, 0.0, 1.0)})
        self.assertNotIn('COLOR_0', attributes[name])
        self.assertEqual(set(read_accessor(gltf, binary, attributes[name + '.001']['COLOR_0'])), {(0.0, 0.0, 1.0, 1.0)})


def _blender_executable():
    from serializers.common.three_d import blender_scripts

    executable = blender_scripts.general_config.blender_executable
    return executable if executable and os.path.isfile(executable) else None


@unittest.skipUnless(_blender_executable(), 'needs Blender (general setting blender_executable)')
class TestExportScenesVertexColorsThroughBlender(unittest.TestCase):
    """The OBJ, `.blend` and (with a gg-web-engine exporter downloaded before: no network in tests) GLB of a scene
    with vertex colours, exported by Blender"""

    def test_blend_and_glb_have_the_colors(self):
        from serializers.common.three_d import gg_web_engine_exporter
        from serializers.common.three_d.blender_scripts import run_blender
        from serializers.common.three_d.glb_morph_targets import read_accessor, read_glb

        exporter_dir = os.path.dirname(gg_web_engine_exporter._EXPORTER_FILE)
        with_glb = os.path.isfile(gg_web_engine_exporter._EXPORTER_FILE)

        class Settings(_Settings):
            geometry__save_blend = True
            geometry__export_to_gg_web_engine = with_glb

        with tempfile.TemporaryDirectory() as tmp:
            from PIL import Image

            Image.new('RGBA', (4, 4), (255, 255, 255, 255)).save(os.path.join(tmp, 'tex.png'))
            with patch.object(scenes_module, 'ensure_gg_web_engine_exporter_installed', return_value=exporter_dir):
                export_scenes([_colored_scene()], tmp + '/', Settings())
            # the colour attributes of the `.blend`, as Blender shows them (sRGB)
            colors_path = os.path.join(tmp, 'colors.json')
            run_blender(
                path=tmp,
                script=f"""
import json
bpy.ops.wm.open_mainfile(filepath="{os.path.join(tmp, 'map.blend')}")
colors = {{}}
for o in bpy.data.objects:
    if o.type == 'MESH':
        colors[o.name] = {{a.name: [list(d.color_srgb) for d in a.data] for a in o.data.color_attributes}}
with open("{colors_path}", "w") as f:
    json.dump(colors, f)
""",
            )
            with open(colors_path) as f:
                blend_colors = json.load(f)
            glb = read_glb(os.path.join(tmp, 'map.glb')) if with_glb else None

        self.assertEqual(set(blend_colors['block_0__tex']), {'Color'})
        # the OBJ has no alpha: opaque in the `.blend`
        expected = [[0.25, 0.5, 1.0, 1.0], [1.0, 0.0, 0.5, 1.0], [0.0, 0.0, 0.0, 1.0], [1.0, 1.0, 1.0, 1.0]]
        self.assertEqual(len(blend_colors['block_0__tex']['Color']), len(expected))
        for got, want in zip(sorted(blend_colors['block_0__tex']['Color']), sorted(expected)):
            for a, b in zip(got, want):
                self.assertAlmostEqual(a, b, 4)
        self.assertEqual(blend_colors['block_1__tex'], {})
        if glb is None:
            return
        gltf, binary = glb
        nodes = {
            node['name']: gltf['meshes'][node['mesh']]['primitives'][0] for node in gltf['nodes'] if 'mesh' in node
        }
        attributes = nodes['block_0__tex']['attributes']
        self.assertEqual(
            sorted(read_accessor(gltf, binary, attributes['COLOR_0'])),
            sorted(tuple(c) for c in _colored_scene().sub_meshes[0].vertex_colors),
        )
        self.assertNotIn('COLOR_0', nodes['block_1__tex']['attributes'])
