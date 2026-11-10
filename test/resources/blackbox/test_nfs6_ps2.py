import json
import os
import tempfile
import unittest
from io import BytesIO

from PIL import Image

from library import require_file
from resources.blackbox.archives import Nfs6Ps2CompressedBlock
from resources.blackbox.maps.nfs6_ps2 import Nfs6Ps2CarGeometry, Nfs6Ps2ChunkBundle, Nfs6Ps2TrackBundle
from resources.eac.compressions.comp import CompCompression
from serializers.bitmaps import nfs6_ps2_texture_pack_textures, nfs6_ps2_texture_to_image
from serializers.geometries import (
    Nfs6Ps2CarSerializer,
    bin_hash,
    nfs6_ps2_car_parts,
    nfs6_ps2_lighting_vectors,
    nfs6_ps2_mesh,
    nfs6_ps2_solid_pack_meshes,
    nfs6_ps2_strip_skips,
    nfs6_ps2_texture_by_name,
)
from serializers.maps import BlackBoxRoad, Nfs6Ps2TrackBundleSerializer, Nfs6Ps2World, blackbox_route, nfs6_ps2_roads

# one mesh of TRACKB11.LZC, its textures and TRACK11_MAP, a scenery with two instances of the mesh, 6 route points
BUNDLE = 'test/samples/NFS6PS2_TRACKB99.BUN'
# GLOBAL/PRERACEANIM.LZC of the game
COMPRESSED = 'test/samples/NFS6PS2_PRERACEANIM.LZC'
# the game's folders with CARS/COUPE/GEOMETRY.LZC, the COUPE textures of CARS/TEXTURES.BIN and GLOBAL/GLOBALB.BUN with the
# lighting materials, the car type COUPE (index 0 here), the shared textures of the model and the paints of COUPE
CAR = 'test/samples/nfs6_ps2_cars/CARS/COUPE/GEOMETRY.LZC'
GLOBALB = 'test/samples/nfs6_ps2_cars/GLOBAL/GLOBALB.BUN'


def _chunk(data, chunk_id):
    return next(c['data'] for c in data['chunks'] if c['data'].get('chunk_id') == chunk_id)


class TestCompCompression(unittest.TestCase):
    def test_game_file_should_be_compressed_again_to_the_same_bytes(self):
        with open(COMPRESSED, 'rb') as f:
            raw = f.read()
        uncompressed = CompCompression().uncompress(BytesIO(raw), len(raw))
        self.assertEqual(len(uncompressed), int.from_bytes(raw[8:12], 'little'))
        self.assertEqual(raw, CompCompression().compress(BytesIO(uncompressed), len(uncompressed)))

    def test_data_should_round_trip(self):
        for data in [b'', b'abc', bytes(range(256)) * 40, b'abcabcabcabcabcd' * 300 + b'xyz' * 7]:
            compressed = CompCompression().compress(BytesIO(data), len(data))
            self.assertEqual(compressed[:4], b'COMP')
            self.assertEqual(int.from_bytes(compressed[12:16], 'little'), len(compressed))
            self.assertEqual(data, CompCompression().uncompress(BytesIO(compressed), len(compressed)))

    def test_incompressible_data_should_be_stored(self):
        data = b'0123456789'
        compressed = CompCompression().compress(BytesIO(data), len(data))
        self.assertEqual(compressed[6:8], b'\x01\x00')
        self.assertEqual(compressed[16:], data)

    def test_compressed_file_should_be_read_and_remain_the_same(self):
        (name, block, data) = require_file(COMPRESSED, lazy=False)
        self.assertIsInstance(block, Nfs6Ps2CompressedBlock)
        with open(COMPRESSED, 'rb') as f:
            self.assertEqual(f.read(), block.pack(data, name=name))


class TestNfs6Ps2TrackBundle(unittest.TestCase):
    def test_bundle_should_be_read_and_remain_the_same(self):
        (name, block, data) = require_file(BUNDLE, lazy=False)
        self.assertIsInstance(block, Nfs6Ps2TrackBundle)
        self.assertIsInstance(block, Nfs6Ps2ChunkBundle)
        with open(BUNDLE, 'rb') as f:
            self.assertEqual(f.read(), block.pack(data, name=name))

    def test_mesh_should_decode_draw_groups(self):
        (_, _, data) = require_file(BUNDLE)
        mesh_chunk = next(
            c['data'] for c in _chunk(data, 0x80034000)['sub_chunks'] if c['data'].get('chunk_id') == 0x80034002
        )
        mesh = nfs6_ps2_mesh(mesh_chunk)
        self.assertEqual(mesh.name, 'XS_15FT_S1_00')
        self.assertEqual(mesh.mesh_id, bin_hash(mesh.name))
        groups = next(
            c['data']['draw_groups'] for c in mesh_chunk['sub_chunks'] if c['data'].get('chunk_id') == 0x00034004
        )
        self.assertEqual(len(mesh.vertices), sum(g['num_vertices'] for g in groups))
        self.assertEqual(sum(len(t) for _, t in mesh.parts), sum(g['num_triangles'] for g in groups))
        header = next(c['data'] for c in mesh_chunk['sub_chunks'] if c['data'].get('chunk_id') == 0x00034003)
        for k in 'xyz':
            values = [v['xyz'.index(k)] for v in mesh.vertices]
            # the box is a bit bigger
            self.assertAlmostEqual(min(values), header['bounding_box_min'][k], delta=0.05)
            self.assertAlmostEqual(max(values), header['bounding_box_max'][k], delta=0.05)
            self.assertLessEqual(header['bounding_box_min'][k], min(values))
            self.assertGreaterEqual(header['bounding_box_max'][k], max(values))
        self.assertEqual(len(mesh.uvs), len(mesh.vertices))
        self.assertEqual(len(mesh.colors), len(mesh.vertices))

    def test_strip_skips_should_follow_the_microprogram(self):
        # one strip
        self.assertEqual(nfs6_ps2_strip_skips(4, [0x6000, 0, 0, 0]), [True, True, False, False])
        # 7 strips of 4: field x up to vertex 14, field w from vertex 15
        skips = nfs6_ps2_strip_skips(28, [0x00286666, 0, 0, 0x00433330])
        self.assertEqual([k for k in range(28) if skips[k]], [k for k in range(28) if k % 4 < 2])
        # 5 strips (TRACK_HELICOPTER): w from vertex 7
        skips = nfs6_ps2_strip_skips(19, [0x001066D8, 0, 0, 0x00036C60])
        self.assertEqual([k for k in range(19) if skips[k]], [0, 1, 4, 5, 7, 8, 10, 11, 15, 16])

    def test_textures_should_decode(self):
        (_, _, data) = require_file(BUNDLE)
        textures = {
            info['name']: (info, image_data)
            for info, image_data in nfs6_ps2_texture_pack_textures(_chunk(data, 0xB0300001))
        }
        self.assertEqual(len(textures), 4)
        for info, image_data in textures.values():
            self.assertEqual(info['name_hash'], bin_hash(info['name']))
            image = nfs6_ps2_texture_to_image(info, image_data).convert('RGBA')
            self.assertEqual(image.size, (info['width'], info['height']))
        # 4-bit, swizzled: the track map is a white line on black, corners black
        info, image_data = textures['TRACK11_MAP']
        self.assertEqual((info['bits_per_pixel'], info['levels'][0]['swizzled']), (4, 1))
        image = nfs6_ps2_texture_to_image(info, image_data).convert('RGB')
        self.assertEqual(image.getpixel((0, 0)), (0, 0, 0))
        self.assertEqual(image.getpixel((255, 255)), (0, 0, 0))
        pixels = image.tobytes()
        self.assertGreater(sum(1 for i in range(0, len(pixels), 3) if pixels[i : i + 3] == b'\xff\xff\xff'), 1000)

    def test_world_should_place_instances_and_route(self):
        (_, _, data) = require_file(BUNDLE)
        world = Nfs6Ps2World()
        world.collect(data)
        self.assertEqual(len(world.sceneries), 1)
        section_number, infos, instances = world.sceneries[0]
        self.assertEqual((section_number, len(instances)), (7, 2))
        parts = world.scenery_parts(infos, instances)
        self.assertEqual(set(parts), {x[0] for x in world.meshes[infos[0]['mesh_ids'][0]].parts})
        points, closed = blackbox_route(data)
        self.assertEqual((len(points), closed), (6, False))

    def test_serializer_should_export_chunks_with_textures_and_route(self):
        (name, block, data) = require_file(BUNDLE)
        serializer = Nfs6Ps2TrackBundleSerializer()
        serializer.patch_settings(
            {
                'geometry__save_obj': True,
                'geometry__save_blend': False,
                'geometry__export_to_gg_web_engine': False,
                'maps__save_as_chunked': True,
                'maps__save_spherical_skybox_texture': True,
                'maps__add_props_to_obj': False,
            }
        )
        with tempfile.TemporaryDirectory() as path:
            files = [os.path.relpath(x, path) for x in serializer.serialize(data, path, id=name, block=block)]
            self.assertIn('terrain_chunk_0.obj', files)
            self.assertIn('terrain_chunks.json', files)
            self.assertIn('track_route.json', files)
            # no sky dome in the sample
            self.assertNotIn('spherical.png', files)
            with open(os.path.join(path, 'terrain_chunk_0.obj')) as f:
                obj = f.read()
            self.assertNotIn('usemtl untextured', obj)
            self.assertEqual(len(os.listdir(os.path.join(path, 'textures'))), 3)
            with open(os.path.join(path, 'track_route.json')) as f:
                route = json.load(f)
            self.assertEqual(len(route['points']), 6)
            self.assertFalse(route['closed'])
            self.assertEqual(route['roads'], [])

    def test_roads_should_join_branches_to_near_points(self):
        def point(x, y, near=(-1, -1, -1)):
            return {'x': x, 'y': y, 'near_points': list(near)}

        paths = [
            {'path_index': 0, 'is_closed': 1, 'first_point': 0, 'end_point': 4},
            {'path_index': 1, 'is_closed': 0, 'first_point': 5, 'end_point': 7},
        ]
        # route 0..3 (4 = its closing point), the branch 5..6 from near point 1 to near point 3
        points = [point(0, 0), point(10, 0), point(10, 10), point(0, 10), point(0, 0)]
        points += [point(12, 2, (0, 1, 6)), point(12, 8, (2, 3, 5))]
        data = {
            'chunks': [
                {
                    'data': {
                        'chunk_id': 0x80034147,
                        'sub_chunks': [
                            {'data': {'chunk_id': 0x34148, 'paths': paths}},
                            {'data': {'chunk_id': 0x34149, 'points': points}},
                        ],
                    }
                }
            ]
        }
        self.assertEqual(blackbox_route(data), ([(0, 0), (10, 0), (10, 10), (0, 10)], True))
        self.assertEqual(
            nfs6_ps2_roads(data),
            [BlackBoxRoad([(10, 0, None), (12, 2, None), (12, 8, None), (10, 10, None)], False)],
        )


class TestNfs6Ps2Car(unittest.TestCase):
    def _car(self):
        (name, block, data) = require_file(CAR)
        return name, block.possible_blocks[data['choice_index']], data['data']

    def test_car_should_be_read_and_remain_the_same(self):
        (name, block, data) = require_file(CAR, lazy=False)
        self.assertIsInstance(block.possible_blocks[data['choice_index']], Nfs6Ps2CarGeometry)
        with open(CAR, 'rb') as f:
            self.assertEqual(f.read(), block.pack(data, name=name))
        (name, block, data) = require_file(GLOBALB, lazy=False)
        with open(GLOBALB, 'rb') as f:
            self.assertEqual(f.read(), block.pack(data, name=name))

    def test_car_type_should_have_wheels(self):
        (_, _, data) = require_file(GLOBALB)
        car_type = _chunk(data, 0x00034600)['car_types'][0]
        self.assertEqual((car_type['name'], car_type['model_name'], car_type['car_class']), ('COUPE', 'COUPE', 2))
        self.assertEqual(car_type['geometry_path'], 'CARS\\COUPE\\GEOMETRY.BIN')
        wheels = {w['index']: w['position'] for w in car_type['wheels']}
        # front left, front right, rear right, rear left; X forward, Y left
        self.assertGreater(wheels[0]['x'], 0)
        self.assertGreater(wheels[0]['y'], 0)
        self.assertLess(wheels[1]['y'], 0)
        self.assertLess(wheels[2]['x'], 0)

    def test_parts_should_be_named_by_mesh_id(self):
        (_, _, data) = self._car()
        meshes = nfs6_ps2_solid_pack_meshes(_chunk(data, 0x80034000))
        (_, _, globalb) = require_file(GLOBALB)
        wheels = _chunk(globalb, 0x00034600)['car_types'][0]['wheels']
        names = sorted(name for name, _, _ in nfs6_ps2_car_parts('COUPE', meshes, wheels))
        self.assertIn('hp_body', names)
        self.assertIn('mp_body', names)
        self.assertEqual(
            [x for x in names if 'tire' in x and x.startswith('hp_')],
            [f'hp_tire_{w}' for w in ('fl', 'fr', 'rl', 'rr')],
        )

    def test_lighting_materials_should_turn_into_vu_vectors(self):
        (_, _, data) = require_file(GLOBALB)
        materials = {x['name']: x for x in _chunk(data, 0x0003401E)['materials']}
        self.assertEqual(len(materials), 49)
        red = materials['RegPaintRed']['frontend']
        self.assertAlmostEqual(red['env_facing'], 0.26, places=6)
        # float32 math of SLUS_203.62 0x116828; the bias: float(bits(2.07)) - 3.32 * float(bits(1.0))
        self.assertEqual(
            nfs6_ps2_lighting_vectors(red),
            [
                3.319999933242798,
                -2462937088.0,
                0.10000000149011612,
                0.003921568859368563,
                1.0299999713897705,
                1.0299999713897705,
                1.0199999809265137,
                71.04000091552734,
                0.9900000095367432,
                1.0099999904632568,
                1.0199999809265137,
                -37.76000213623047,
                10.0,
                -9573079040.0,
                20.0,
                108.0,
            ],
        )
        # no specular scale: no specular
        self.assertEqual(nfs6_ps2_lighting_vectors(materials['Driver']['frontend'])[:2], [0.0, 0.0])
        skins = _chunk(data, 0x00034601)['skins']
        self.assertEqual([(x['car_type_index'], x['skin_number']) for x in skins[:2]], [(0, 1), (0, 2)])
        self.assertIn(skins[0]['lighting_material_hash'], {x['name_hash'] for x in materials.values()})

    def test_mesh_should_have_normals_and_lighting_materials(self):
        (_, _, data) = self._car()
        meshes = nfs6_ps2_solid_pack_meshes(_chunk(data, 0x80034000))
        body = next(m for m in meshes if m.name == 'COUPE_A')
        self.assertEqual(len(body.normals), len(body.vertices))
        self.assertEqual(len(body.vertex_groups), len(body.vertices))
        lit = [i for i, g in enumerate(body.vertex_groups) if body.draw_groups[g]['vu_flags'] & 0x4000]
        self.assertTrue(lit)
        for i in lit:
            self.assertAlmostEqual(sum(c * c for c in body.normals[i]) ** 0.5, 127, delta=2)
        self.assertIn(bin_hash('CARSKIN'), {g['material_hash'] for g in body.draw_groups})

    def test_texture_by_name_should_find_textures_with_cut_names(self):
        on = ({'name': 'MURCIELAGO_BRAKELIGHT_O'}, b'on')
        off = ({'name': 'MURCIELAGO_BRAKELIGHT'}, b'off')
        textures = {bin_hash('MURCIELAGO_BRAKELIGHT_ON'): on, 1: off}
        self.assertIs(nfs6_ps2_texture_by_name(textures, 'MURCIELAGO_BRAKELIGHT_ON'), on)
        # by the stored name when the hash is not the name's
        self.assertIs(nfs6_ps2_texture_by_name(textures, 'MURCIELAGO_BRAKELIGHT'), off)
        self.assertIsNone(nfs6_ps2_texture_by_name(textures, 'MURCIELAGO_BRAKELIGHT_DAMAGE0'))

    def test_serializer_should_export_parts_skins_and_wheels(self):
        (name, block, data) = self._car()
        serializer = Nfs6Ps2CarSerializer()
        serializer.patch_settings(
            {'geometry__save_obj': True, 'geometry__save_blend': False, 'geometry__export_to_gg_web_engine': False}
        )
        with tempfile.TemporaryDirectory() as path:
            serializer.serialize(data, path, id=name, block=block)
            with open(os.path.join(path, 'geometry.obj')) as f:
                objects = [x[2:] for x in f.read().splitlines() if x.startswith('o ')]
            self.assertIn('hp_body__skin', objects)
            # traffic cars have their own window texture, not the window slots
            self.assertIn('hp_body__WINDOW_TRAFFIC', objects)
            self.assertFalse([x for x in objects if x.endswith('__untextured')])
            self.assertEqual(len([x for x in objects if x.startswith('hp_tire_fl__')]), 2)
            with open(os.path.join(path, 'skins.json')) as f:
                skins = json.load(f)
            self.assertEqual([x['name'] for x in skins], [f'SKIN{n}' for n in range(1, 9)])
            for skin in skins:
                self.assertTrue(os.path.exists(os.path.join(path, skin['texture'])))
            with open(os.path.join(path, 'car.json')) as f:
                car = json.load(f)
            self.assertEqual((car['model'], car['car_type']), ('COUPE', 'COUPE'))
            wheels = {w['name']: w['position'] for w in car['wheels']}
            # X right, Y forward: the front left wheel is left and forward
            self.assertLess(wheels['fl'][0], 0)
            self.assertGreater(wheels['fl'][1], 0)
            self.assertGreater(wheels['fr'][0], 0)
            # lighting of every object, the paint's for "CARSKIN"
            self.assertEqual(set(car['meshes']), set(objects))
            body = [v for k, v in car['meshes'].items() if k.startswith('hp_body__skin')]
            self.assertIn('CARSKIN', [x['lighting_material'] for x in body])
            self.assertTrue(all(x['paint_name'] == 'Metal' for x in skins))
            self.assertIn(skins[0]['lighting_material'], car['lighting_materials'])
            names = {x['lighting_material'] for x in car['meshes'].values()} - {'CARSKIN'}
            self.assertTrue(names <= set(car['lighting_materials']))
            self.assertEqual(len(car['lighting_materials']['Default']['frontend']), 16)
            self.assertEqual(car['textures']['skin']['alpha_blend'], 0x0A)
            self.assertTrue(car['textures']['skin']['vertex_lit_env'])
            self.assertEqual(car['textures']['WINDOW_TRAFFIC']['alpha_blend'], 0x44)
            with open(os.path.join(path, 'geometry.obj')) as f:
                self.assertIn('\nvn ', f.read())
            # textures as stored: the GS draws texture * vertex colour / 0x80
            (_, _, textures) = require_file('test/samples/nfs6_ps2_cars/CARS/TEXTURES.BIN')
            pack = _chunk(textures, 0xB0300001)
            info, raw = next(x for x in nfs6_ps2_texture_pack_textures(pack) if x[0]['name'] == 'COUPE_SKIN1')
            with Image.open(os.path.join(path, skins[0]['texture'])) as image:
                self.assertEqual(
                    image.convert('RGBA').tobytes(),
                    nfs6_ps2_texture_to_image(info, raw).convert('RGBA').tobytes(),
                )


if __name__ == '__main__':
    unittest.main()
