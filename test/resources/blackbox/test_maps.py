import os
import unittest
from io import BytesIO
from types import SimpleNamespace

from library import require_file
from resources.blackbox.archives import NfsuJdlzCompressedBlock
from resources.blackbox.maps.nfsu import NfsuChunkBundle, NfsuTrackBundle
from resources.eac.compressions.jdlz import JdlzCompression
from serializers.bitmaps import nfsu_texture_pack_textures, nfsu_texture_to_image
from serializers.geometries import nfsu_geometry_meshes
from serializers.maps import (
    BlackBoxRoad,
    NfsuTrackBundleSerializer,
    NfsuWorld,
    find_nfsu_stream_file,
    nfsu2_track_paths,
    nfsu_ground_heights,
    nfsu_heights_from_roads,
    nfsu_section_ranges,
    nfsu_streaming_sections,
)

SECTION = 'test/samples/NFSU_B36.BUN'


def _chunk(data, key, value):
    return next(c['data'] for c in data['chunks'] if c['data'].get(key) == value)


class TestNfsuChunkBundle(unittest.TestCase):
    def test_section_should_be_read_and_remain_the_same(self):
        (name, block, data) = require_file(SECTION, lazy=False)
        self.assertIsInstance(block, NfsuChunkBundle)
        with open(SECTION, 'rb') as f:
            self.assertEqual(f.read(), block.pack(data, name=name))

    def test_scenery_instances_should_reference_meshes_of_the_section(self):
        (_, _, data) = require_file(SECTION)
        world = NfsuWorld()
        world.collect(data)
        self.assertEqual(len(world.sceneries), 1)
        section_number, infos, instances = world.sceneries[0]
        self.assertEqual(section_number, 236)
        self.assertTrue(instances)
        for instance in instances:
            # rotation with scale
            self.assertTrue(all(-4 < x < 4 for x in instance['rotation']))
            self.assertLess(instance['info_index'], len(infos))
        # other objects use meshes of other sections (shared ones)
        self.assertTrue(any(infos[x['info_index']]['mesh_ids'][0] in world.meshes for x in instances))
        parts = world.scenery_parts(infos, instances)
        self.assertTrue(parts)
        self.assertTrue(any(texture_id in world.textures for texture_id in parts))
        for texture_id, (vertices, uvs, triangles) in parts.items():
            self.assertEqual(len(vertices), len(uvs))
            self.assertLess(triangles.max(), len(vertices))

    def test_mesh_materials_should_cover_all_triangles(self):
        (_, _, data) = require_file(SECTION)
        geometry = _chunk(data, 'header', 0x80134000)
        meshes = nfsu_geometry_meshes(geometry)
        self.assertTrue(meshes)
        for mesh in meshes:
            for _, triangles in mesh.parts:
                self.assertTrue(all(0 <= i < len(mesh.vertices) for t in triangles for i in t))

    def test_texture_should_be_decoded(self):
        (_, _, data) = require_file(SECTION)
        textures = nfsu_texture_pack_textures(_chunk(data, 'chunk_id', 0xB3300000))
        self.assertEqual([t[0]['name'] for t in textures], ['ARC_BUILD_135'])
        info, d3d_format, image_data = textures[0]
        self.assertEqual(d3d_format, int.from_bytes(b'DXT1', 'little'))
        image = nfsu_texture_to_image(info, d3d_format, image_data)
        self.assertEqual(image.size, (128, 128))
        # a building facade: not a flat color
        self.assertGreater(len(set(image.getdata())), 100)


# the track paths and roads chunks of TRACKB1301.lzc (a drift race)
PATHS = 'test/samples/NFSU_TRACKB1301_PATHS.BUN'


class TestNfsuRacePaths(unittest.TestCase):
    def test_paths_and_roads_should_be_read_and_remain_the_same(self):
        (name, block, data) = require_file(PATHS, lazy=False)
        with open(PATHS, 'rb') as f:
            self.assertEqual(f.read(), block.pack(data, name=name))
        roads = _chunk(data, 'chunk_id', 0x00034121)['roads']
        self.assertEqual([(x['road_id'], len(x['nodes'])) for x in roads], [(1, 36), (2, 27)])
        for road in roads:
            for node in road['nodes']:
                self.assertEqual(node['road_id'], road['road_id'])
                self.assertAlmostEqual(abs(complex(node['forward']['x'], node['forward']['y'])), 1, places=3)

    def test_route_should_get_heights_of_roads(self):
        (_, _, data) = require_file(PATHS)
        route, roads = NfsuTrackBundleSerializer().track_paths(data)
        self.assertEqual((len(route.points), route.closed), (11, True))
        self.assertEqual([len(x.points) for x in roads], [36, 27])
        # a flat parking lot
        self.assertTrue(all(z is not None and abs(z - 0.07) < 0.01 for _, _, z in route.points))

    def test_heights_should_follow_the_road_nearest_in_height(self):
        lower = BlackBoxRoad([(0, 0, 0), (100, 0, 0)], False)
        bridge = BlackBoxRoad([(50, -50, 10), (50, 50, 10)], False)
        self.assertEqual(nfsu_heights_from_roads([(10, 1), (50, 0), (90, 0)], [lower, bridge]), [0, 0, 0])
        self.assertEqual(nfsu_heights_from_roads([(50, -40), (50, 0)], [lower, bridge]), [10, 10])
        self.assertEqual(nfsu_heights_from_roads([(0, 0)], []), [None])


# TRACKS/ROUTESL4RB/Routes4201F.bin of NFSU2: roads of a race, one with leftover bytes after its name
NFSU2_ROUTES = 'test/samples/NFSU2_ROUTES4201F.BIN'


def _quad_mesh(name: str, x0: float, y0: float, x1: float, y1: float, z: float, facing_down: bool = False):
    import numpy as np

    triangles = [(0, 2, 1), (0, 3, 2)] if facing_down else [(0, 1, 2), (0, 2, 3)]
    return SimpleNamespace(
        name=name,
        vertices=np.array([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], dtype=np.float64),
        uvs=np.zeros((4, 2)),
        parts=[(None, np.array(triangles))],
    )


def _world(meshes) -> NfsuWorld:
    world = NfsuWorld()
    world.meshes = dict(enumerate(meshes))
    infos = [{'mesh_ids': [i]} for i in range(len(meshes))]
    identity = [1, 0, 0, 0, 1, 0, 0, 0, 1]
    instances = [
        {'info_index': i, 'rotation': identity, 'position': {'x': 0, 'y': 0, 'z': 0}} for i in range(len(meshes))
    ]
    world.sceneries = [(0, infos, instances)]
    return world


class TestNfsu2Roads(unittest.TestCase):
    def test_roads_should_be_read_and_remain_the_same(self):
        (name, block, data) = require_file(NFSU2_ROUTES, lazy=False)
        with open(NFSU2_ROUTES, 'rb') as f:
            self.assertEqual(f.read(), block.pack(data, name=name))
        roads = _chunk(data, 'chunk_id', 0x00034121)['roads']
        self.assertEqual([x['road_id'] for x in roads], [1, 2, 3, 4, 100, 101, 102, 103])
        self.assertEqual({x['name'] for x in roads}, {f'TrackRoutesA1{i}' for i in range(5)})
        self.assertEqual(roads[4]['name_padding'][:2], b'\x03\x00')
        for road in roads:
            points = [(n['position']['x'], n['position']['y']) for n in road['nodes']]
            length = sum(abs(complex(*b) - complex(*a)) for a, b in zip(points, points[1:]))
            self.assertAlmostEqual(road['length'], length, delta=0.1)
            for node in road['nodes']:
                self.assertAlmostEqual(abs(complex(node['direction']['x'], node['direction']['y'])), 32767, delta=4)

    def test_location_roads_should_be_found_next_to_bundle(self):
        import shutil
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            os.makedirs(os.path.join(directory, 'ROUTESL4RB'))
            shutil.copy(NFSU2_ROUTES, os.path.join(directory, 'ROUTESL4RB', 'RoutesAll.bin'))
            route, roads = NfsuTrackBundleSerializer().track_paths({'chunks': []}, os.path.join(directory, 'L4RB.BUN'))
            self.assertIsNone(route)
            self.assertEqual([len(x.points) for x in roads], [28, 22, 22, 8, 30, 25, 25, 10])
            self.assertTrue(all(z is None for road in roads for _, _, z in road.points))
            self.assertIsNone(nfsu2_track_paths(os.path.join(directory, 'L4RC.BUN')))

    def test_ground_heights_should_follow_the_roads(self):
        world = _world(
            [
                _quad_mesh('TRN_CN_ROADA_CHOP_A1', 0, -5, 200, 5, 0),
                _quad_mesh('TRN_CN_ROADA_CHOP_A2', 95, -100, 105, 100, 10),
                _quad_mesh('TRN_CN_TERRAINA_CHOP_A1', -50, -150, 250, 150, -5),
                _quad_mesh('XT_TREE_1A', 40, -10, 60, 10, 20),
                _quad_mesh('TRN_CN_CEILINGSA_CHOP_A1', 150, -10, 170, 10, 8, facing_down=True),
            ]
        )
        # the lower road under the bridge, the tree and the tunnel ceiling
        self.assertEqual(nfsu_ground_heights(world, [(x, 0) for x in range(0, 201, 25)]), [0] * 9)
        # the bridge over the lower road
        self.assertEqual(nfsu_ground_heights(world, [(100, y) for y in range(-100, 101, 25)]), [10] * 9)
        # the terrain off the roads
        self.assertEqual(nfsu_ground_heights(world, [(30, 100), (30, 2)]), [-5, 0])


class TestJdlz(unittest.TestCase):
    def test_compressed_data_should_be_uncompressed_back(self):
        compression = JdlzCompression()
        for raw in [b'', b'a', b'abc' * 1000, bytes(range(256)) * 20, open(SECTION, 'rb').read()]:
            compressed = compression.compress(BytesIO(raw), len(raw))
            self.assertEqual(compressed[:4], b'JDLZ')
            self.assertEqual(int.from_bytes(compressed[12:16], 'little'), len(compressed))
            self.assertEqual(compression.uncompress(BytesIO(compressed), len(compressed)), raw)

    def test_compressed_bundle_should_be_read(self):
        with open(SECTION, 'rb') as f:
            raw = f.read()
        compressed = JdlzCompression().compress(BytesIO(raw), len(raw))
        block = NfsuJdlzCompressedBlock()
        data = block.unpack_from_bytes(compressed, name='test.lzc')
        self.assertIsInstance(block.possible_blocks[data['choice_index']], NfsuChunkBundle)
        packed = block.pack(data)
        self.assertEqual(JdlzCompression().uncompress(BytesIO(packed), len(packed)), raw)


NFSU2_DIR = 'test/samples/claude_tmp/nfsu2'


@unittest.skipUnless(os.path.exists(f'{NFSU2_DIR}/L4RA.BUN'), f'needs NFSU2 samples in {NFSU2_DIR}')
class TestNfsu2LocationBundle(unittest.TestCase):
    def test_location_bundle_should_be_read_and_remain_the_same(self):
        path = f'{NFSU2_DIR}/L4RA.BUN'
        (name, block, data) = require_file(path, lazy=False)
        self.assertIsInstance(block, NfsuTrackBundle)
        with open(path, 'rb') as f:
            self.assertEqual(f.read(), block.pack(data, name=name))

    def test_streaming_sections_should_be_listed(self):
        (_, _, data) = require_file(f'{NFSU2_DIR}/L4RA.BUN')
        sections = nfsu_streaming_sections(data)
        ranges = nfsu_section_ranges(sections)
        self.assertEqual(len(ranges), 392)
        self.assertNotIn('--', [s['name'] for s in ranges])
        stream_end = max(s['offset'] + s['size'] for s in ranges)
        stream_path = f'{NFSU2_DIR}/STREAML4RA.BUN'
        if os.path.exists(stream_path):
            self.assertEqual(find_nfsu_stream_file(f'{NFSU2_DIR}/L4RA.BUN', sections), stream_path)
            self.assertGreaterEqual(os.path.getsize(stream_path), stream_end)

    @unittest.skipUnless(os.path.exists(f'{NFSU2_DIR}/STREAML4RA.BUN'), 'needs NFSU2 STREAML4RA.BUN')
    def test_streamed_section_should_be_read_and_remain_the_same(self):
        (_, _, data) = require_file(f'{NFSU2_DIR}/L4RA.BUN')
        section = next(s for s in nfsu_section_ranges(nfsu_streaming_sections(data)) if s['name'] == 'C22')
        with open(f'{NFSU2_DIR}/STREAML4RA.BUN', 'rb') as f:
            f.seek(section['offset'])
            raw = f.read(section['size'])
        block = NfsuChunkBundle()
        section_data = block.unpack_from_bytes(raw, name='section.BUN')
        self.assertEqual(raw, block.pack(section_data))
        world = NfsuWorld()
        world.collect(section_data)
        # NFSU2 scenery layout: named infos, instances with float bounding box
        self.assertEqual(len(world.sceneries), 2)
        for _, infos, instances in world.sceneries:
            self.assertTrue(all(i['name'] for i in infos))
            self.assertTrue(all(0 <= x['info_index'] < len(infos) for x in instances))


NFSMW_DIR = 'test/samples/claude_tmp/nfsmw'


@unittest.skipUnless(os.path.exists(f'{NFSMW_DIR}/Tracks/L2RA.BUN'), f'needs NFSMW samples in {NFSMW_DIR}')
class TestNfsmwLocationBundle(unittest.TestCase):
    def test_location_bundle_should_be_read_and_remain_the_same(self):
        path = f'{NFSMW_DIR}/Tracks/L2RA.BUN'
        (name, block, data) = require_file(path, lazy=False)
        self.assertIsInstance(block, NfsuTrackBundle)
        with open(path, 'rb') as f:
            self.assertEqual(f.read(), block.pack(data, name=name))

    def test_streaming_sections_should_be_listed(self):
        (_, _, data) = require_file(f'{NFSMW_DIR}/Tracks/L2RA.BUN')
        sections = nfsu_streaming_sections(data)
        self.assertEqual(len(sections), 720)
        self.assertEqual(sections[0]['name'], 'X0')
        stream_path = f'{NFSMW_DIR}/Tracks/STREAML2RA.BUN'
        if os.path.exists(stream_path):
            self.assertEqual(find_nfsu_stream_file(f'{NFSMW_DIR}/Tracks/L2RA.BUN', sections), stream_path)


class TestNfsmwSection(unittest.TestCase):
    def test_scenery_should_be_read(self):
        # NFSMW scenery: instances before definitions, named definitions with 4 mesh ids
        (_, _, data) = require_file('test/samples/NFSMW_C52.BUN')
        world = NfsuWorld()
        world.collect(data)
        self.assertEqual(len(world.sceneries), 1)
        section_number, infos, instances = world.sceneries[0]
        self.assertEqual(section_number, 352)
        self.assertTrue(all(i['name'] for i in infos))
        self.assertTrue(all(0 <= x['info_index'] < len(infos) for x in instances))
        self.assertTrue(world.scenery_parts(infos, instances))
