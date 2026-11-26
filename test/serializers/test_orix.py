import json
import os
import re
import tempfile
import unittest

from PIL import Image

from library import require_resource
from serializers import OrixGeometrySerializer, ShppArchiveSerializer
from serializers.geometries import (
    orix_gouraud_polygons,
    orix_polygon_textures,
    orix_wheel_labels_on_tyres,
    tnfs_tyre_texture_file_name,
)
from serializers.misc.tnfs_psx_car_colors import tnfs_psx_car_colors

SAMPLES = os.path.join(os.path.dirname(__file__), '..', 'samples')
ITEM_ID = '{}__children/{}/item/data'
OBJ_SETTINGS = {
    'geometry__save_obj': True,
    'geometry__save_blend': False,
    'geometry__export_to_gg_web_engine': False,
}


def export(file_name: str, index: int, path: str):
    id = ITEM_ID.format(os.path.join(SAMPLES, file_name), index)
    (id, block, data), _ = require_resource(id)
    serializer = OrixGeometrySerializer()
    serializer.patch_settings(OBJ_SETTINGS)
    return data, serializer.serialize(data, path, id, block)


class TestOrixGeometrySerializer(unittest.TestCase):
    def test_polygon_textures(self):
        (_, _, data), _ = require_resource(ITEM_ID.format(os.path.join(SAMPLES, 'ZTSUPRA.VSM'), 2))
        textures = orix_polygon_textures(data)
        self.assertEqual(len(textures), 65)
        self.assertEqual(textures[0], 'J000')
        # mirrored polygons share an image
        self.assertEqual(textures[0x17], 'J000')
        # the wheel quads: no image in the file, the game sets tyr4
        wheels = {x['name']: textures[x['index']] for x in data['labels'] if x['name'].endswith(('frnt', 'rear'))}
        self.assertEqual(wheels, {'rt_rear': 'tyr4', 'lt_rear': 'tyr4', 'rt_frnt': 'tyr4', 'lt_frnt': 'tyr4'})
        self.assertNotIn(None, textures)
        # an image the PSH lacks
        self.assertIsNone(orix_polygon_textures(data, ['J001'])[0])

    def test_car_model_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'model') + '/'
            data, files = export('ZTSUPRA.VSM', 2, path)
            with open(path + 'geometry.obj') as f:
                obj = f.read()
            with open(path + 'material.mtl') as f:
                mtl = f.read()
            meshes = set(re.findall(r'^o (.+)$', obj, re.M))
            for name in (
                'lbl__lt_frnt__tyr4',
                'lbl__rt_frnt__tyr4',
                'lbl__lt_rear__tyr4',
                'lbl__rt_rear__tyr4',
                'lbl__bkll__J020',
                'lbl__bklr__J020',
                'J000',
                'circ',
                'shad',
            ):
                self.assertIn(name, meshes)
            # every material has its texture, an indexed PNG of the PSH next to the model
            self.assertLessEqual(
                set(re.findall(r'^usemtl (.+)$', obj, re.M)), set(re.findall(r'^newmtl (.+)$', mtl, re.M))
            )
            for texture in re.findall(r'^map_Kd (.+)$', mtl, re.M):
                self.assertTrue(os.path.isfile(path + texture), texture)
            self.assertIn('map_Kd assets/J000.png\nalpha_mode cutout', mtl)
            # 65 quads, the two-sided ones written twice
            two_sided = sum(1 for x in data['polygons'] if x['mapping']['two_sided'])
            self.assertEqual(len(re.findall(r'^f ', obj, re.M)), 65 + two_sided)
            # J001 is stored rotated (7 rows of 16 texels): shown 7 wide, 16 high
            with Image.open(path + 'assets/J001.png') as image:
                self.assertEqual(image.size, (7, 16))
            with open(path + 'geometry_extra.json') as f:
                extra = json.load(f)
            self.assertIn('fx_smok', [x['name'] for x in extra['dummies']])
            self.assertEqual(extra['objects']['lbl__lt_frnt__tyr4'], {'partition': 'outside'})
            with open(path + 'assets/car_colors.json') as f:
                colors = json.load(f)
            self.assertEqual(
                colors,
                {'tail_lights': {'texture_color': '#00ff00', 'textures': ['J020'], 'off': '#420000', 'on': '#ff0000'}},
            )

    def test_low_poly_model_uvs(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'model') + '/'
            data, files = export('ZTSUPRA.VSM', 4, path)
            with open(path + 'geometry.obj') as f:
                obj = f.read()
            self.assertEqual(set(re.findall(r'^o (.+)$', obj, re.M)), {'frnt', 'rear', 'side'})
            # texel coordinates divided by the size of the image as shown
            uvs = [tuple(float(v) for v in x.split()) for x in re.findall(r'^vt (.+)$', obj, re.M)]
            self.assertTrue(all(0 <= u <= 1 and 0 <= v <= 1 for u, v in uvs))

    def test_track_prop_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'model') + '/'
            data, files = export('ZAL1_POR.FAM', 0, path)
            with open(path + 'material.mtl') as f:
                mtl = f.read()
            textures = re.findall(r'^map_Kd (.+)$', mtl, re.M)
            self.assertTrue(textures)
            # the images of the item of the same index of the _PSH.FAM
            for texture in textures:
                self.assertTrue(os.path.isfile(path + texture), texture)
            self.assertFalse(os.path.exists(path + 'assets/car_colors.json'))

    def test_japanese_car_model_export(self):
        # ZKHGC.VSM of the Japanese disc (SLPS-01024): a C0FB archive in another order (KHGCL.POR, KHGC.PBS, KHGC.PDN,
        # KHGC.POR, KHGC.PSH, KHGCL.PSH, KHGC.GRO), tyre images Tir1..Tir4, untextured windows coloured by KHGC.GRO
        (_, _, data), _ = require_resource(ITEM_ID.format(os.path.join(SAMPLES, 'ZKHGC.VSM'), 3))
        wheels = {
            x['name']: orix_polygon_textures(data)[x['index']]
            for x in data['labels']
            if x['name'][3:] in ('frnt', 'rear')
        }
        # the texture of material tire4
        self.assertEqual(set(wheels.values()), {'Tir4'})
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'model') + '/'
            data, files = export('ZKHGC.VSM', 3, path)
            with open(path + 'geometry.obj') as f:
                obj = f.read()
            with open(path + 'material.mtl') as f:
                mtl = f.read()
            meshes = set(re.findall(r'^o (.+)$', obj, re.M))
            for name in ('lbl__lt_frnt__tyr4', 'lbl__rt_frnt__tyr4', 'lbl__lt_rear__tyr4', 'lbl__rt_rear__tyr4'):
                self.assertIn(name, meshes)
            # the tyre images under the names nfs-web loads
            for i in range(1, 5):
                self.assertTrue(os.path.isfile(f'{path}assets/tyr{i}.png'))
                self.assertFalse(os.path.isfile(f'{path}assets/Tir{i}.png'))
            for texture in re.findall(r'^map_Kd (.+)$', mtl, re.M):
                self.assertTrue(os.path.isfile(path + texture), texture)
            # the windows: the mean of their corner colours in KHGC.GRO (#314974 #788cbe #788cbe #242b34)
            self.assertIn('newmtl flat_516389', mtl)
            self.assertIn('newmtl flat_2a3a54', mtl)
            self.assertNotIn('flat_000000', mtl)
            with open(path + 'assets/car_colors.json') as f:
                self.assertEqual(json.load(f)['tail_lights']['textures'], ['J027'])

    def test_gouraud_polygons_as_the_japanese_game_draws_them(self):
        (_, _, data), _ = require_resource(ITEM_ID.format(os.path.join(SAMPLES, 'ZKHGC.VSM'), 3))
        (_, _, gro), _ = require_resource(ITEM_ID.format(os.path.join(SAMPLES, 'ZKHGC.VSM'), 6))
        records = {}
        for record in gro['records']:
            records.setdefault(record['polygon_index'], record['colors'])
        shading = orix_gouraud_polygons(data, records)
        # flag 0x40 or draw type 10: 75 polygons, the windows (draw type 10) untextured
        self.assertEqual(sum(1 for x in shading if x), 75)
        # a window: its record's colours in the order of the polygon's vertices
        self.assertEqual(
            shading[6],
            {
                'colors': [(0x31, 0x49, 0x74), (0x78, 0x8C, 0xBE), (0x78, 0x8C, 0xBE), (0x24, 0x2B, 0x34)],
                'textured': False,
            },
        )
        self.assertTrue(shading[1]['textured'])
        # a record of a polygon drawn without Gouraud colours is not used
        self.assertIsNone(shading[0])
        self.assertIn(0, records)
        # without a record: the material's colour (`Number` 0, `fbumper` 0x19194c)
        self.assertEqual(shading[12]['colors'], [(0, 0, 0)] * 4)
        self.assertEqual(shading[17]['colors'], [(0x19, 0x19, 0x4C)] * 4)
        # no GRO: the US disc's loader draws none
        self.assertEqual(set(map(bool, orix_gouraud_polygons(data, None))), {False})

    def test_japanese_export_has_the_gouraud_colours_by_corner(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'model') + '/'
            export('ZKHGC.VSM', 3, path)
            with open(path + 'geometry.obj') as f:
                obj = f.read()
            with open(path + 'geometry_extra.json') as f:
                colors = json.load(f)['psx_gouraud']
        # per corner of the triangles three.js OBJLoader makes of each mesh's faces, 4 bytes each
        corners, mesh = {}, None
        for line in obj.splitlines():
            if line.startswith('o '):
                mesh = line[2:]
                corners[mesh] = 0
            elif line.startswith('f '):
                corners[mesh] += 3 * (len(line.split()) - 3)
        self.assertTrue(colors)
        for name, values in colors.items():
            self.assertEqual(len(values), 8 * corners[name], name)
        # the window quads: their colours, alpha 255
        window = next(v for k, v in colors.items() if k.startswith('flat_'))
        self.assertIn('314974ff', window)
        # the wheels and other meshes without Gouraud polygons have none
        self.assertNotIn('lbl__lt_frnt__tyr4', colors)

    def test_us_export_has_no_gouraud_colours(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'model') + '/'
            export('ZTSUPRA.VSM', 2, path)
            with open(path + 'geometry_extra.json') as f:
                self.assertNotIn('psx_gouraud', json.load(f))

    def test_japanese_low_poly_model_finds_its_psh_by_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'model') + '/'
            # KHGCL.POR is followed by KHGC.PBS: its textures are KHGCL.PSH, the 6th item
            export('ZKHGC.VSM', 0, path)
            with open(path + 'geometry.obj') as f:
                obj = f.read()
            self.assertEqual(set(re.findall(r'^o (.+)$', obj, re.M)), {'Frnt', 'Rear', 'Side', 'Topp'})

    def test_tyre_texture_file_names(self):
        self.assertEqual(
            [tnfs_tyre_texture_file_name(x) for x in ['Tir1', 'Tyr2', 'tyr3', 'TIR4', 'Tir5', 'Circ', 'tire1']],
            ['tyr1', 'tyr2', 'tyr3', 'tyr4', 'Tir5', 'Circ', 'tire1'],
        )

    def test_wheel_label_moves_to_the_tyre_polygon(self):
        # the KDR30 labels the inner circ quad of its left rear wheel lt_rear, its tyre quad is the next polygon
        square = [
            {'x': 0, 'y': 0, 'z': 0},
            {'x': 0, 'y': 1, 'z': 0},
            {'x': 0, 'y': 1, 'z': 1},
            {'x': 0, 'y': 0, 'z': 1},
        ]
        vertices = [{**v, 'x': x} for x in (-0.5, -0.8, 0.8) for v in square]
        data = {
            'materials': [{'name': b'circ\0\0\0\0'}, {'name': b'rertires'}],
            'polygons': [
                {'material_index': 0, 'polygon_type': 0x84, 'offset_3d': 0},
                {'material_index': 1, 'polygon_type': 0x84, 'offset_3d': 4},
                {'material_index': 1, 'polygon_type': 0x84, 'offset_3d': 8},
            ],
            'vertices': {'data': vertices},
            'vmap': list(range(12)),
            'labels': [{'name': 'lt_rear', 'index': 0}, {'name': 'rt_rear', 'index': 2}, {'name': 'bkll', 'index': 0}],
        }
        moved, changes = orix_wheel_labels_on_tyres(data)
        self.assertEqual(changes, [('lt_rear', 0, 1)])
        self.assertEqual([x['index'] for x in moved['labels']], [1, 2, 0])
        self.assertEqual([x['index'] for x in data['labels']], [0, 2, 0])
        # nothing to move: the same dict
        self.assertIs(orix_wheel_labels_on_tyres(moved)[0], moved)

    def test_import_is_not_supported(self):
        serializer = OrixGeometrySerializer()
        self.assertFalse(serializer.ui_serialization()['reversible'])
        with self.assertRaises(NotImplementedError):
            serializer.deserialize(['x'])


class TestTnfsPsxCarColors(unittest.TestCase):
    @staticmethod
    def item(name, colors):
        return name, {'clut': {'colors': colors}}, None

    def test_tail_lights(self):
        items = [
            self.item('J000', [0x1234, 0x03E0]),
            self.item('J001', [0x03E0] + [0x8000] * 15),
            # only the first 16 CLUT entries are looked at
            self.item('J002', [0x1111] * 16 + [0x03E0]),
            ('text', b'raw', None),
        ]
        self.assertEqual(
            tnfs_psx_car_colors(items),
            {
                'tail_lights': {
                    'texture_color': '#00ff00',
                    'textures': ['J000', 'J001'],
                    'off': '#420000',
                    'on': '#ff0000',
                }
            },
        )

    def test_light_bar(self):
        colors = tnfs_psx_car_colors([self.item('J000', [0x001F, 5]), self.item('J007', [0x7C00])])
        self.assertEqual(colors['light_bar']['texture_colors'], ['#ff0000', '#0000ff'])
        self.assertEqual(colors['light_bar']['textures'], ['J000', 'J007'])
        self.assertEqual(colors['light_bar']['siren_colors_swapped'], ['#0000ff', '#ff0000'])
        self.assertNotIn('tail_lights', colors)

    def test_no_special_colors(self):
        self.assertEqual(tnfs_psx_car_colors([self.item('J000', [0x7FFF, 0x0421])]), {})

    def test_psh_export_writes_car_colors(self):
        id = ITEM_ID.format(os.path.join(SAMPLES, 'ZTSUPRA.VSM'), 3)
        (id, block, data), _ = require_resource(id)
        with tempfile.TemporaryDirectory() as tmp:
            files = ShppArchiveSerializer().serialize(data, os.path.join(tmp, 'psh') + '/', id, block)
            self.assertIn('car_colors.json', [os.path.basename(x) for x in files])


class TestSubdivideBilinearQuads(unittest.TestCase):
    """The Saturn's VDP1 maps a polygon's whole texture bilinearly onto its 4 corners (`subdivide_bilinear_quads`)"""

    @staticmethod
    def quad(corners, deltas=None):
        from serializers.common.three_d import SubMesh

        mesh = SubMesh()
        mesh.vertices = [list(c) for c in corners]
        mesh.vertex_uvs = [[0, 0], [1, 0], [1, 1], [0, 1]]
        if deltas:
            mesh.morph_targets['left_turn'] = [list(d) for d in deltas]
        mesh.polygons = [[0, 1, 2, 3]]
        return mesh

    def test_parallelogram_stays_one_quad(self):
        from serializers.geometries import subdivide_bilinear_quads

        mesh = self.quad([(0, 0, 0), (2, 0, 0), (3, 1, 0), (1, 1, 0)])
        subdivide_bilinear_quads(mesh, (32, 32))
        self.assertEqual(mesh.polygons, [[0, 1, 2, 3]])
        self.assertEqual(len(mesh.vertices), 4)

    def test_trapezoid_becomes_a_grid_on_its_bilinear_patch(self):
        from serializers.geometries import subdivide_bilinear_quads

        corners = [(0, 0, 0), (4, 0, 0), (3, 2, 0), (1, 2, 0)]
        deltas = [(0, 0, 0), (1, 0, 0), (1, 0, 0), (0, 0, 0)]
        mesh = self.quad(corners, deltas)
        subdivide_bilinear_quads(mesh, (32, 32))
        steps = int(len(mesh.polygons) ** 0.5)
        self.assertGreater(steps, 1)
        self.assertEqual(len(mesh.polygons), steps * steps)
        self.assertEqual(len(mesh.vertices), (steps + 1) ** 2)
        self.assertEqual(len(mesh.vertex_uvs), len(mesh.vertices))
        self.assertEqual(len(mesh.morph_targets['left_turn']), len(mesh.vertices))
        # every vertex: the bilinear point of its UV (s along corner 0 -> 1, t along corner 0 -> 3), the morph alike
        for vertex, (s, t), delta in zip(mesh.vertices, mesh.vertex_uvs, mesh.morph_targets['left_turn']):
            a, b, c, d = corners
            expected = [
                (1 - s) * (1 - t) * a[k] + s * (1 - t) * b[k] + s * t * c[k] + (1 - s) * t * d[k] for k in range(3)
            ]
            for k in range(3):
                self.assertAlmostEqual(vertex[k], expected[k])
            self.assertAlmostEqual(delta[0], s)
        # the corners keep their vertices, the grid's quads keep the polygon's winding (corner order)
        self.assertEqual(mesh.polygons[0][0], 0)
        self.assertEqual(mesh.polygons[steps - 1][1], 1)
        self.assertEqual(mesh.polygons[-1][2], 2)
        self.assertEqual(mesh.polygons[-steps][3], 3)

    def test_triangle_stays(self):
        from serializers.common.three_d import SubMesh
        from serializers.geometries import subdivide_bilinear_quads

        mesh = SubMesh()
        mesh.vertices = [[0, 0, 0], [1, 0, 0], [0, 1, 0]]
        mesh.vertex_uvs = [[0, 0], [1, 0], [0, 1]]
        mesh.polygons = [[0, 1, 2]]
        subdivide_bilinear_quads(mesh, (32, 32))
        self.assertEqual(mesh.polygons, [[0, 1, 2]])
