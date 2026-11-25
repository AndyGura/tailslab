import json
import math
import os
import re
import shutil
import struct
import tempfile
import unittest
from configparser import ConfigParser

from PIL import Image

from serializers.geometries import (
    compose_texture_page,
    crp_car_texture_page_sources,
    crp_image_atlas_position,
    crp_primitive_triangles,
    crp_stream_indices,
    geo_polygon_normal,
    geo_sub_mesh_properties,
    geo_vertex_normals,
    orip_fx_dummies,
    orip_morph_deltas,
    orip_polygon_partitions,
    orip_sub_mesh_names,
    orip_material_names,
    orip_material_texture,
    texture_alpha_mode,
)
from serializers.common.three_d import SubMesh
from serializers.misc.nfs5_car_model import (
    crp_car_is_image_used,
    nfs5_car_packages,
    nfs5_car_tpg_info,
    nfs5_damage_zones,
    nfs5_paint_band,
    nfs5_race_slots,
    nfs5_style_slots,
)
from serializers.common.three_d.glb_morph_targets import (
    add_glb_morph_targets,
    add_glb_vertex_attributes,
    read_accessor,
    read_glb,
    write_glb,
)


class TestCrpImageAtlasPosition(unittest.TestCase):
    def test_reads_12_lower_bits(self):
        self.assertEqual(crp_image_atlas_position({'position': {'x': 192, 'y': 64}}), (192, 64))

    def test_ignores_flags_in_higher_bits(self):
        self.assertEqual(crp_image_atlas_position({'position': {'x': 0, 'y': 0x7000}}), (0, 0))

    def test_values_are_signed(self):
        self.assertEqual(crp_image_atlas_position({'position': {'x': 191, 'y': 0xFFFF}}), (191, -1))


class TestGeoPolygonMapping(unittest.TestCase):
    def test_reads_flags_and_frame_count(self):
        from resources.eac.geometries import GeoPolygon

        block = GeoPolygon()
        # tyre quad: 4 frames (bits 5-7), double-sided off, colour-keyed (bit 3), uv_flip (bit 1)
        raw = bytes([0x8A, 0, 0, 0, 0, 1, 3, 2]) + b'm000'
        data = block.unpack_from_bytes(raw)
        self.assertEqual(
            data['mapping'],
            {
                'num_frames': 4,
                'double_sided': False,
                'color_keyed': True,
                'flip_normal': False,
                'uv_flip': True,
                'is_triangle': False,
            },
        )
        self.assertEqual(block.pack(data), raw)


class TestGeoSubMeshProperties(unittest.TestCase):
    @staticmethod
    def _polygon(num_frames, color_keyed):
        return {'mapping': {'num_frames': num_frames, 'color_keyed': color_keyed}}

    def test_frames_at_least_one(self):
        self.assertEqual(
            geo_sub_mesh_properties(3, [self._polygon(0, False)]), {'geo_part': 3, 'frames': 1, 'color_keyed': False}
        )
        self.assertEqual(
            geo_sub_mesh_properties(12, [self._polygon(4, True), self._polygon(4, True)]),
            {'geo_part': 12, 'frames': 4, 'color_keyed': True},
        )

    def test_mixed_values_left_out(self):
        with self.assertLogs(level='WARNING'):
            res = geo_sub_mesh_properties(11, [self._polygon(2, False), self._polygon(0, False)])
        self.assertEqual(res, {'geo_part': 11, 'color_keyed': False})


def _geo_polygon(indices, four=True, flip=False, is_triangle=None):
    """A GEO polygon: `four` = flag bit 1 (`uv_flip`), the corners the normals code takes; `is_triangle` (bit 0)
    the opposite unless given"""
    return {
        'mapping': {
            'is_triangle': (not four) if is_triangle is None else is_triangle,
            'uv_flip': four,
            'flip_normal': flip,
        },
        'vertex_indices': list(indices) + [indices[-1]] * (4 - len(indices)),
    }


def _geo_part(vertices=(), polygons=(), num_vrtx=None, num_plgn=None):
    """A GEO part of raw 8.8 vertices"""
    return {
        'num_vrtx': len(vertices) if num_vrtx is None else num_vrtx,
        'num_plgn': len(polygons) if num_plgn is None else num_plgn,
        'pos': {'x': 0.0, 'y': 0.0, 'z': 0.0},
        'vertices': [{'x': x / 256, 'y': y / 256, 'z': z / 256} for x, y, z in vertices],
        'polygons': list(polygons),
    }


def _geo_parts(**parts):
    """32 GEO parts, `part_<n>` given, the others empty"""
    return [parts.get(f'part_{i}', _geo_part()) for i in range(32)]


class TestGeoVertexNormals(unittest.TestCase):
    def assertVector(self, actual, expected):
        self.assertEqual(len(actual), 3)
        for a, e in zip(actual, expected):
            self.assertAlmostEqual(a, e, places=6)

    def test_triangle_normal_and_flip(self):
        vertices = [(256, 0, 0), (256, 0, 256), (512, 0, 0)]
        # (B - A) x (C - A) = (0, 0, 256) x (256, 0, 0) = up
        self.assertVector(geo_polygon_normal(vertices, _geo_polygon([0, 1, 2], four=False)), [0, 1, 0])
        self.assertVector(geo_polygon_normal(vertices, _geo_polygon([0, 1, 2], four=False, flip=True)), [0, -1, 0])
        normals = geo_vertex_normals(_geo_parts(part_1=_geo_part(vertices, [_geo_polygon([0, 1, 2], four=False)])))
        for normal in normals[1]:
            self.assertVector(normal, [0, 1, 0])

    def test_flag_bit_1_decides_the_corners(self):
        vertices = [(256, 0, 0), (256, 0, 256), (512, 0, 256), (512, 256, 0)]
        # a triangle (bit 0) with bit 1 set: 4 corners, the normals of ABC and ACD added
        polygon = _geo_polygon([0, 1, 2, 3], four=True, is_triangle=True)
        third = 1 / math.sqrt(3)
        expected = [-third, 1 + third, third]
        length = math.sqrt(sum(x * x for x in expected))
        expected = [x / length for x in expected]
        self.assertVector(geo_polygon_normal(vertices, polygon), expected)
        normals = geo_vertex_normals(_geo_parts(part_1=_geo_part(vertices, [polygon])))
        self.assertVector(normals[1][3], expected)
        # a quad (bit 0 clear) without bit 1: 3 corners, D in no polygon's list
        polygon = _geo_polygon([0, 1, 2, 3], four=False, is_triangle=False)
        self.assertVector(geo_polygon_normal(vertices, polygon), [0, 1, 0])
        normals = geo_vertex_normals(_geo_parts(part_1=_geo_part(vertices, [polygon])))
        self.assertVector(normals[1][0], [0, 1, 0])
        self.assertEqual(normals[1][3], [0.0, 0.0, 0.0])

    def test_zero_normals_stay_zero(self):
        # collinear corners; vertex 3 in no polygon
        vertices = [(256, 0, 0), (512, 0, 0), (768, 0, 0), (256, 256, 256)]
        polygon = _geo_polygon([0, 1, 2], four=False, flip=True)
        self.assertEqual(geo_polygon_normal(vertices, polygon), [0.0, 0.0, 0.0])
        normals = geo_vertex_normals(_geo_parts(part_1=_geo_part(vertices, [polygon])))
        self.assertEqual(normals[1], [[0.0, 0.0, 0.0]] * 4)

    def test_first_8_polygons_of_a_vertex(self):
        vertices = [(256, 0, 0), (256, 0, 256), (512, 0, 0), (512, 0, 0), (256, 256, 0)]
        up = _geo_polygon([0, 1, 2], four=False)
        # its 9th polygon, facing +z, is not counted for vertex 0, but for its other two vertices
        forward = _geo_polygon([0, 3, 4], four=False)
        normals = geo_vertex_normals(_geo_parts(part_1=_geo_part(vertices, [up] * 8 + [forward])))
        self.assertVector(normals[1][0], [0, 1, 0])
        self.assertVector(normals[1][3], [0, 0, 1])
        self.assertVector(normals[1][4], [0, 0, 1])
        normals = geo_vertex_normals(_geo_parts(part_1=_geo_part(vertices, [up] * 7 + [forward])))
        self.assertVector(normals[1][0], [0, 7 / math.sqrt(50), 1 / math.sqrt(50)])

    def test_x_zeroed_at_x_0_without_normalizing(self):
        vertices = [(0, 0, 0), (0, 0, 256), (256, 256, 0)]
        # normal (-1, 1, 0) / sqrt(2)
        normals = geo_vertex_normals(_geo_parts(part_1=_geo_part(vertices, [_geo_polygon([0, 1, 2], four=False)])))
        self.assertVector(normals[1][0], [0, 1 / math.sqrt(2), 0])
        self.assertVector(normals[1][2], [-1 / math.sqrt(2), 1 / math.sqrt(2), 0])

    def test_neighbour_parts(self):
        # part 1: an upward triangle with vertex 0 at (1024, 0, 0)
        own = [(1024, 0, 0), (1024, 0, 256), (1280, 0, 0)]
        up = _geo_polygon([0, 1, 2], four=False)

        def facing_forward(corner):
            x, y, z = corner
            return _geo_part([corner, (x + 256, y, z), (x, y + 256, z)], [_geo_polygon([0, 1, 2], four=False)])

        def facing_right(corner):
            x, y, z = corner
            return _geo_part([corner, (x, y + 256, z), (x, y, z + 256)], [_geo_polygon([0, 1, 2], four=False)])

        forward = [0, 1 / math.sqrt(2), 1 / math.sqrt(2)]
        # 12 raw units away on every axis touches, in the parts' own coordinates (the part pos is not applied)
        touching = facing_forward((1036, 12, -12))
        touching['pos'] = {'x': 5.0, 'y': 5.0, 'z': 5.0}
        normals = geo_vertex_normals(_geo_parts(part_1=_geo_part(own, [up]), part_3=touching))
        self.assertVector(normals[1][0], forward)
        self.assertVector(normals[1][1], [0, 1, 0])
        # and part 3 takes part 1's
        self.assertVector(normals[3][0], forward)
        # 13 units away does not
        normals = geo_vertex_normals(_geo_parts(part_1=_geo_part(own, [up]), part_3=facing_forward((1037, 0, 0))))
        self.assertVector(normals[1][0], [0, 1, 0])
        # parts 0, 2, 9, 10, 11 are no neighbours, nor are parts >= 20
        for q in (0, 2, 9, 10, 11, 20):
            normals = geo_vertex_normals(
                _geo_parts(part_1=_geo_part(own, [up]), **{f'part_{q}': facing_right((1024, 0, 0))})
            )
            self.assertVector(normals[1][0], [0, 1, 0])
        # the neighbour's limits don't matter
        many = facing_forward((1024, 0, 0))
        many['num_plgn'] = 66
        normals = geo_vertex_normals(_geo_parts(part_1=_geo_part(own, [up]), part_5=many))
        self.assertEqual(normals[5], [])
        self.assertVector(normals[1][0], forward)
        # parts 2, 9, 10 and parts >= 20 take no neighbour normals
        for p in (2, 9, 10, 20):
            normals = geo_vertex_normals(
                _geo_parts(**{f'part_{p}': _geo_part(own, [up])}, part_3=facing_forward((1024, 0, 0)))
            )
            self.assertVector(normals[p][0], [0, 1, 0])

    def test_part_limits(self):
        vertices = [(256, 0, 0), (256, 0, 256), (512, 0, 0)]
        polygon = _geo_polygon([0, 1, 2], four=False)

        def normals_of(num_vrtx, num_plgn):
            return geo_vertex_normals(_geo_parts(part_1=_geo_part(vertices, [polygon], num_vrtx, num_plgn)))[1]

        self.assertEqual(len(normals_of(125, 65)), 3)
        self.assertEqual(normals_of(126, 1), [])
        self.assertEqual(normals_of(3, 66), [])
        self.assertEqual(geo_vertex_normals(_geo_parts())[1], [])

    @staticmethod
    def _cardata_geo(alias):
        from library import require_file

        (_, _, viv) = require_file('test/samples/CARDATA.VIV', lazy=False)
        return next(c['item']['data'] for c in viv['children'] if c['alias'].lower() == alias)

    def test_race_cars_point_outwards(self):
        for alias in ('cala.geo', 'f355.geo'):
            parts = self._cardata_geo(alias)['parts']
            normals = geo_vertex_normals(parts)
            self.assertEqual(normals[10], [])
            body = [(v['x'], v['y'], v['z']) for v in parts[1]['vertices']]
            listed = [i for i, n in enumerate(normals[1]) if n != [0.0, 0.0, 0.0]]
            centre = [sum(v[k] for v in body) / len(body) for k in range(3)]
            for i in listed:
                self.assertGreater(sum((body[i][k] - centre[k]) * normals[1][i][k] for k in range(3)), 0, alias)
            # the roof up (game y), the sides outwards
            roof = max(listed, key=lambda i: body[i][1])
            self.assertGreater(normals[1][roof][1], 0.95, alias)
            side = max(listed, key=lambda i: abs(body[i][0]))
            self.assertGreater(normals[1][side][0] * math.copysign(1, body[side][0]), 0.95, alias)
        # CALA's roof vertex (0, 167, -159) / 256
        normals = geo_vertex_normals(self._cardata_geo('cala.geo')['parts'])
        self.assertVector([round(x, 3) for x in normals[1][7]], [0.0, 0.993, -0.093])

    def test_parts_over_the_limits(self):
        self.assertEqual(geo_vertex_normals(self._cardata_geo('futr.geo')['parts'])[21], [])
        normals = geo_vertex_normals(self._cardata_geo('tank.geo')['parts'])
        self.assertEqual((normals[21], normals[24]), ([], []))
        self.assertEqual(len(normals[20]), self._cardata_geo('tank.geo')['parts'][20]['num_vrtx'])


class TestGeoGeometrySerializer(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_exports_game_normals(self):
        """An NFS2 GEO next to its QFS (TANK of NFS2 SE's CARDATA.VIV, any QFS): the parts with normals get `vn`,
        the others (TANK's parts 21 and 24: too many polygons) none"""
        from library import require_file, require_resource
        from library.loader import clear_file_cache, path_to_name
        from serializers import get_serializer

        (_, viv_block, viv) = require_file('test/samples/CARDATA.VIV', lazy=False)
        child = next(c for c in viv['children'] if c['alias'] == 'TANK.geo')
        geo_block = viv_block.item_block.possible_blocks[child['item']['choice_index']]
        geo_path = os.path.join(self.tmp_dir, 'TANK.GEO')
        with open(geo_path, 'wb') as f:
            f.write(geo_block.pack(child['item']['data']))
        shutil.copy('test/samples/VERTBST.QFS', os.path.join(self.tmp_dir, 'TANK.QFS'))
        clear_file_cache(geo_path)
        (geo_id, block, data), _ = require_resource(path_to_name(geo_path))
        serializer = get_serializer(block, data)
        serializer.patch_settings(
            {'geometry__save_obj': True, 'geometry__save_blend': False, 'geometry__export_to_gg_web_engine': False}
        )
        out_path = os.path.join(self.tmp_dir, 'out/')
        serializer.serialize(data, out_path, id=geo_id, block=block)
        with open(os.path.join(out_path, 'geometry.obj')) as f:
            objects = f.read().split('\n\no ')[1:]
        normals = geo_vertex_normals(data['parts'])
        parts = {'part_mp_0': 20, 'part_mp_1': 21, 'part_lp_0': 23, 'part_lp_1': 24}
        vn_count = 0
        for text in objects:
            name = text.split('\n', 1)[0]
            part = parts[name.split('__')[0]]
            vertices = re.findall(r'^v (.*)$', text, re.MULTILINE)
            vns = re.findall(r'^vn (.*)$', text, re.MULTILINE)
            corners = [c for face in re.findall(r'^f (.*)$', text, re.MULTILINE) for c in face.split(' ')]
            if part in (21, 24):
                self.assertEqual(vns, [], name)
                self.assertTrue(all(c.count('/') == 1 for c in corners), name)
                continue
            self.assertEqual(len(vns), len(vertices), name)
            # normal indices count the normals of the objects before only
            self.assertTrue(all(vn_count < int(c.split('/')[2]) <= vn_count + len(vns) for c in corners), name)
            vn_count += len(vns)
            # axes (x, z, y) as the vertices
            game = {tuple(round(x, 6) for x in (n[0], n[2], n[1])) for n in normals[part]}
            self.assertTrue({tuple(round(float(x), 6) for x in vn.split(' ')) for vn in vns} <= game, name)
        self.assertGreater(vn_count, 0)


class TestOripFxDummies(unittest.TestCase):
    data = {
        'vertices': {'data': [{'x': 0.5, 'y': 0.0, 'z': 1.5}, {'x': 0.0, 'y': 0.25, 'z': -2.0}]},
        'fx_polys': [
            {'name': 'FR0', 'index': 0},
            {'name': 'smok', 'index': 1},
            {'name': '\x02', 'index': 1},
            {'name': 'smok', 'index': 0},
        ],
    }

    def test_dummy_per_named_vertex_in_mesh_space(self):
        dummies = orip_fx_dummies(self.data)
        self.assertEqual(
            dummies[0],
            {
                'name': 'fx_FR0',
                'position': [0.5, 1.5, 0.0],
                'rotation': [0, 0, 0],
                'properties': {'fx': 'FR0', 'vertex': 0},
            },
        )
        self.assertEqual(dummies[1]['position'], [0.0, -2.0, 0.25])

    def test_skips_garbage_names_and_makes_names_unique(self):
        self.assertEqual([d['name'] for d in orip_fx_dummies(self.data)], ['fx_FR0', 'fx_smok', 'fx_smok_1'])


def _orip_data(polygons, labels=(), partitions=(), vmap=(), morphs=(), vertices=(), polygon_types=None):
    """ORIP data with the fields the mesh building reads: polygons as (material index), materials named by index
    (0: the front tyres, 3: a flat colour), textured quads with the colour key unless `polygon_types` says otherwise"""
    return {
        'polygons': [
            {'material_index': m, 'polygon_type': polygon_types[i] if polygon_types else 0x8C}
            for i, m in enumerate(polygons)
        ],
        'materials': [
            {'name': name, 'file_name': file_name, 'color': color}
            for name, file_name, color in [
                (b'frntires', '', 0),
                (b'\0' * 8, 'rsid', 0),
                (b'\0' * 8, 'circ', 0),
                (b'red\0\0\0\0\0', '', 0xC81414),
            ]
        ],
        'labels': [{'name': name, 'index': index} for name, index in labels],
        'partitions': [
            {'name': name, 'polygons_start': start, 'num_polygons': count} for name, start, count in partitions
        ],
        'vmap': list(vmap),
        'morphs': [
            {'name': name, 'num_vertices': n, 'vmap_offset': start, 'first_delta': delta}
            for name, n, start, delta in morphs
        ],
        'vertices': {'data': [{'x': x, 'y': y, 'z': z} for x, y, z in vertices]},
    }


class TestOripPartitionsAndMeshNames(unittest.TestCase):
    # polygons: 0 rsid, 1 rsid, 2 rsid, 3 circ, 4 untextured wheel, 5 rsid
    data = _orip_data(
        polygons=[1, 1, 1, 2, 0, 1],
        labels=[('lt_frnt', 4)],
        # vmap: NON-SORT lists 0 and 5, inside 2 and 3, surface 0 and 1, outside 4; polygon 5 is in no drawn one
        partitions=[('NON-SORT', 0, 2), ('inside', 2, 2), ('surface', 4, 2), ('outside', 6, 1)],
        vmap=[0, 5, 2, 3, 0, 1, 4],
    )

    def test_partition_of_each_polygon(self):
        self.assertEqual(
            orip_polygon_partitions(self.data), ['surface', 'surface', 'inside', 'inside', 'outside', None]
        )

    def test_meshes_split_by_partition(self):
        names, partitions = orip_sub_mesh_names(self.data)
        self.assertEqual(names, ['rsid', 'rsid', 'rsid__inside', 'circ', 'lbl__lt_frnt', 'rsid__none'])
        self.assertEqual(partitions[2], 'inside')

    def test_tie_keeps_the_name_for_the_first_polygon_partition(self):
        data = _orip_data(polygons=[1, 1], partitions=[('inside', 1, 1), ('surface', 0, 1)], vmap=[0, 1])
        self.assertEqual(orip_sub_mesh_names(data)[0], ['rsid', 'rsid__inside'])


class TestOripMaterialNames(unittest.TestCase):
    def test_flat_colour_polygons(self):
        # no textured bit, or textured without a bitmap name (the game finds no texture); the tyres keep theirs
        data = _orip_data(polygons=[3, 1, 3, 0], polygon_types=[0x04, 0x84, 0x8C, 0x8C])
        self.assertEqual(orip_material_names(data), ['flat_c81414', 'rsid', 'flat_c81414', ''])
        self.assertEqual([orip_material_texture(x) for x in orip_material_names(data)], [None, 'rsid', None, ''])

    def test_bitmap_missing_in_the_fsh_is_a_flat_colour(self):
        data = _orip_data(polygons=[1, 2, 0], polygon_types=[0x84, 0x84, 0x8C])
        self.assertEqual(orip_material_names(data, fsh_names=['circ']), ['flat_000000', 'circ', ''])

    def test_colour_key_suffixes_only_for_a_texture_used_both_ways(self):
        data = _orip_data(polygons=[1, 1, 2, 2], polygon_types=[0x84, 0x8C, 0x8C, 0x8C])
        names = orip_material_names(data)
        self.assertEqual(names, ['rsid__opaque', 'rsid__cutout', 'circ', 'circ'])
        self.assertEqual([orip_material_texture(x) for x in names], ['rsid', 'rsid', 'circ', 'circ'])


class TestOripMorphDeltas(unittest.TestCase):
    def test_full_names_and_deltas_by_vertex(self):
        data = _orip_data(
            polygons=[],
            vmap=[7, 3, 5],
            morphs=[('left_tur', 2, 1, 2), ('right_tu', 1, 0, 1)],
            vertices=[(0, 0, 0), (0.5, 0, 0), (1, 2, 3), (4, 5, 6)],
        )
        self.assertEqual(
            orip_morph_deltas(data),
            {'left_turn': {3: [1, 2, 3], 5: [4, 5, 6]}, 'right_turn': {7: [0.5, 0, 0]}},
        )

    def test_change_axes_converts_morph_targets_like_vertices(self):
        mesh = SubMesh()
        mesh.vertices = [[1, 2, 3]]
        mesh.morph_targets = {'left_turn': [[0.1, 0.2, 0.3]]}
        mesh.morph_target_normals = {'left_turn': [[0, 0.6, 0.8]]}
        mesh.change_axes(new_z='y', new_y='z')
        self.assertEqual(mesh.vertices, [[1, 3, 2]])
        self.assertEqual(mesh.morph_targets, {'left_turn': [[0.1, 0.3, 0.2]]})
        self.assertEqual(mesh.morph_target_normals, {'left_turn': [[0, 0.8, 0.6]]})


class TestAddGlbMorphTargets(unittest.TestCase):
    def _write_quad_glb(self, path):
        # one node "wheel" with a quad, its vertices in another order than the sub-mesh ones
        positions = [(1.0, 0.0, 0.0), (0.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0)]
        uvs = [(1.0, 0.0), (0.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        binary = b''.join(struct.pack('<3f', *p) for p in positions) + b''.join(struct.pack('<2f', *t) for t in uvs)
        gltf = {
            'asset': {'version': '2.0'},
            'scene': 0,
            'scenes': [{'nodes': [0, 1]}],
            'nodes': [{'name': 'wheel', 'mesh': 0}, {'name': 'fx_smok'}],
            'meshes': [{'name': 'wheel', 'primitives': [{'attributes': {'POSITION': 0, 'TEXCOORD_0': 1}}]}],
            'buffers': [{'byteLength': len(binary)}],
            'bufferViews': [
                {'buffer': 0, 'byteOffset': 0, 'byteLength': 48},
                {'buffer': 0, 'byteOffset': 48, 'byteLength': 32},
            ],
            'accessors': [
                {
                    'bufferView': 0,
                    'componentType': 5126,
                    'count': 4,
                    'type': 'VEC3',
                    'min': [0, 0, 0],
                    'max': [1, 1, 0],
                },
                {'bufferView': 1, 'componentType': 5126, 'count': 4, 'type': 'VEC2'},
            ],
        }
        write_glb(path, gltf, binary)

    def test_adds_targets_matched_by_position(self):
        mesh = SubMesh()
        mesh.name = 'wheel'
        mesh.vertices = [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]]
        mesh.vertex_uvs = [[0, 0], [1, 0], [1, 1], [0, 1]]
        mesh.morph_targets = {
            'left_turn': [[0.5, 0, 0], [0.25, 0, 0], [0, 0, 0], [0, 0, 0]],
            'right_turn': [[0, 0, 0], [0, 0, 0], [0, 0, -1], [0, 0, 0]],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'body.glb')
            self._write_quad_glb(path)
            add_glb_morph_targets(path, [mesh])
            gltf, binary = read_glb(path)
        gltf_mesh = gltf['meshes'][0]
        self.assertEqual(gltf_mesh['extras'], {'targetNames': ['left_turn', 'right_turn']})
        self.assertEqual(gltf_mesh['weights'], [0.0, 0.0])
        targets = gltf_mesh['primitives'][0]['targets']
        self.assertEqual(
            read_accessor(gltf, binary, targets[0]['POSITION']), [(0.25, 0, 0), (0.5, 0, 0), (0, 0, 0), (0, 0, 0)]
        )
        self.assertEqual(
            read_accessor(gltf, binary, targets[1]['POSITION']), [(0, 0, 0), (0, 0, 0), (0, 0, -1), (0, 0, 0)]
        )
        accessor = gltf['accessors'][targets[1]['POSITION']]
        self.assertEqual((accessor['min'], accessor['max']), ([0, 0, -1], [0, 0, 0]))
        # the original data is kept
        self.assertEqual(read_accessor(gltf, binary, 0)[0], (1.0, 0.0, 0.0))
        self.assertEqual(gltf['buffers'][0]['byteLength'], len(binary))

    def test_adds_game_normals_matched_by_position(self):
        mesh = SubMesh()
        mesh.name = 'wheel'
        mesh.vertices = [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]]
        mesh.vertex_uvs = [[0, 0], [1, 0], [1, 1], [0, 1]]
        mesh.vertex_normals = [[0, 0, 1], [1, 0, 0], [0, 1, 0], [0, 0, -1]]
        other = SubMesh()
        other.name = 'fx_smok'
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'body.glb')
            self._write_quad_glb(path)
            add_glb_vertex_attributes(path, [mesh, other])
            gltf, binary = read_glb(path)
        attributes = gltf['meshes'][0]['primitives'][0]['attributes']
        self.assertEqual(
            read_accessor(gltf, binary, attributes['_GAME_NORMAL']), [(1, 0, 0), (0, 0, 1), (0, 1, 0), (0, 0, -1)]
        )
        self.assertEqual(gltf['buffers'][0]['byteLength'], len(binary))

    def test_adds_target_normals_matched_as_the_targets(self):
        mesh = SubMesh()
        mesh.name = 'wheel'
        mesh.vertices = [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]]
        mesh.vertex_uvs = [[0, 0], [1, 0], [1, 1], [0, 1]]
        mesh.morph_targets = {'damaged': [[0, 0, 0], [0, 0, -1], [0, 0, 0], [0, 0, 0]]}
        mesh.morph_target_normals = {'damaged': [[0, 0, 1], [1, 0, 0], [0, 1, 0], [0, 0, -1]]}
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'body.glb')
            self._write_quad_glb(path)
            add_glb_morph_targets(path, [mesh])
            gltf, binary = read_glb(path)
        attributes = gltf['meshes'][0]['primitives'][0]['attributes']
        self.assertEqual(
            read_accessor(gltf, binary, attributes['_GAME_NORMAL_DAMAGED']),
            [(1, 0, 0), (0, 0, 1), (0, 1, 0), (0, 0, -1)],
        )
        self.assertEqual(gltf['buffers'][0]['byteLength'], len(binary))

    def test_game_normals_left_out_of_the_glb(self):
        mesh = SubMesh()
        mesh.name = 'wheel'
        mesh.vertices = [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]]
        mesh.vertex_uvs = [[0, 0], [1, 0], [1, 1], [0, 1]]
        mesh.vertex_normals = [[0, 0, 1]] * 4
        mesh.glb_game_normals = False
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'body.glb')
            self._write_quad_glb(path)
            add_glb_vertex_attributes(path, [mesh])
            gltf, _ = read_glb(path)
        self.assertNotIn('_GAME_NORMAL', gltf['meshes'][0]['primitives'][0]['attributes'])

    def test_adds_vertex_colors_as_they_are(self):
        mesh = SubMesh()
        mesh.name = 'wheel'
        mesh.vertices = [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]]
        mesh.vertex_uvs = [[0, 0], [1, 0], [1, 1], [0, 1]]
        # without alpha: VEC3
        mesh.vertex_colors = [[0.25, 0.5, 1.0], [1.0, 0.0, 0.5], [0.0, 0.0, 0.0], [1.0, 1.0, 1.0]]
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'body.glb')
            self._write_quad_glb(path)
            add_glb_vertex_attributes(path, [mesh])
            gltf, binary = read_glb(path)
        index = gltf['meshes'][0]['primitives'][0]['attributes']['COLOR_0']
        accessor = gltf['accessors'][index]
        self.assertEqual((accessor['componentType'], accessor['type']), (5126, 'VEC3'))
        self.assertNotIn('normalized', accessor)
        self.assertEqual(
            read_accessor(gltf, binary, index), [(1.0, 0.0, 0.5), (0.25, 0.5, 1.0), (0.0, 0.0, 0.0), (1.0, 1.0, 1.0)]
        )
        # with alpha: VEC4
        mesh.vertex_colors = [c + [0.5] for c in mesh.vertex_colors]
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'body.glb')
            self._write_quad_glb(path)
            add_glb_vertex_attributes(path, [mesh])
            gltf, binary = read_glb(path)
        accessor = gltf['accessors'][gltf['meshes'][0]['primitives'][0]['attributes']['COLOR_0']]
        self.assertEqual(accessor['type'], 'VEC4')

    def test_matches_float32_positions_far_from_the_origin(self):
        # an NFS4 extra object with absolute positions: the GLB's float32 positions are off by up to 1.2e-4 there
        mesh = SubMesh()
        mesh.name = 'xobj_global_0_0__DTC1'
        mesh.vertices = [[2674.000115, 2582.18978, 115.1465], [2674.6018, 2580.0, 115.1], [2670.0, 2582.18978, 115.0]]
        mesh.vertex_uvs = [[0, 0], [1, 0], [0, 1]]
        mesh.vertex_colors = [[0.25, 0.5, 1.0], [1.0, 0.0, 0.5], [0.0, 0.0, 0.0]]
        mesh.polygons = [[0, 1, 2]]
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'body.glb')
            write_glb_of_sub_meshes(path, [mesh])
            add_glb_vertex_attributes(path, [mesh])
            gltf, binary = read_glb(path)
        colors = read_accessor(gltf, binary, gltf['meshes'][0]['primitives'][0]['attributes']['COLOR_0'])
        # the GLB has the vertices in reversed order
        self.assertEqual(colors, [(0.0, 0.0, 0.0), (1.0, 0.0, 0.5), (0.25, 0.5, 1.0)])

    def test_adds_byte_attributes_matched_by_position(self):
        mesh = SubMesh()
        mesh.name = 'wheel'
        mesh.vertices = [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]]
        mesh.vertex_uvs = [[0, 0], [1, 0], [1, 1], [0, 1]]
        mesh.vertex_byte_attributes = {
            '_PSX_GOURAUD': [[0x24, 0x2B, 0x34, 255], [0x78, 0x8C, 0xBE, 255], [1, 2, 3, 255], [0x80, 0x80, 0x80, 0]]
        }
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'body.glb')
            self._write_quad_glb(path)
            add_glb_vertex_attributes(path, [mesh])
            gltf, binary = read_glb(path)
        index = gltf['meshes'][0]['primitives'][0]['attributes']['_PSX_GOURAUD']
        accessor = gltf['accessors'][index]
        self.assertEqual((accessor['componentType'], accessor['normalized'], accessor['type']), (5121, True, 'VEC4'))
        self.assertEqual(gltf['bufferViews'][accessor['bufferView']]['byteOffset'] % 4, 0)
        self.assertEqual(
            read_accessor(gltf, binary, index),
            [(0x78, 0x8C, 0xBE, 255), (0x24, 0x2B, 0x34, 255), (1, 2, 3, 255), (0x80, 0x80, 0x80, 0)],
        )
        self.assertNotIn('_GAME_NORMAL', gltf['meshes'][0]['primitives'][0]['attributes'])

    def test_missing_node_is_an_error(self):
        mesh = SubMesh()
        mesh.name = 'other'
        mesh.vertices = [[0, 0, 0]]
        mesh.morph_targets = {'left_turn': [[1, 0, 0]]}
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'body.glb')
            self._write_quad_glb(path)
            with self.assertRaises(ValueError):
                add_glb_morph_targets(path, [mesh])

    @staticmethod
    def _write_triangles_glb(path, positions, uvs, indices):
        """One node "body" with an indexed triangle list"""
        binary = (
            b''.join(struct.pack('<3f', *p) for p in positions)
            + b''.join(struct.pack('<2f', *t) for t in uvs)
            + b''.join(struct.pack('<I', i) for i in indices)
        )
        count = len(positions)
        gltf = {
            'asset': {'version': '2.0'},
            'nodes': [{'name': 'body', 'mesh': 0}],
            'meshes': [{'primitives': [{'attributes': {'POSITION': 0, 'TEXCOORD_0': 1}, 'indices': 2}]}],
            'buffers': [{'byteLength': len(binary)}],
            'bufferViews': [
                {'buffer': 0, 'byteOffset': 0, 'byteLength': 12 * count},
                {'buffer': 0, 'byteOffset': 12 * count, 'byteLength': 8 * count},
                {'buffer': 0, 'byteOffset': 20 * count, 'byteLength': 4 * len(indices)},
            ],
            'accessors': [
                {'bufferView': 0, 'componentType': 5126, 'count': count, 'type': 'VEC3'},
                {'bufferView': 1, 'componentType': 5126, 'count': count, 'type': 'VEC2'},
                {'bufferView': 2, 'componentType': 5125, 'count': len(indices), 'type': 'SCALAR'},
            ],
        }
        write_glb(path, gltf, binary)

    def _targets_of(self, mesh, positions, uvs, indices):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'body.glb')
            self._write_triangles_glb(path, positions, uvs, indices)
            add_glb_morph_targets(path, [mesh])
            gltf, binary = read_glb(path)
        return read_accessor(gltf, binary, gltf['meshes'][0]['primitives'][0]['targets'][0]['POSITION'])

    def test_vertices_at_the_same_place_moving_differently_matched_by_their_triangles(self):
        # vertices 0 and 3 have the same position and texture coordinates, but other deltas: the corner of the
        # triangle (0, 1, 2) moves by 1, the corner of the triangle (3, 4, 5) by 2
        mesh = SubMesh()
        mesh.name = 'body'
        mesh.vertices = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 0], [-1, 0, 0], [0, -1, 0]]
        mesh.vertex_uvs = [[0, 0]] * 6
        mesh.polygons = [[0, 1, 2], [3, 4, 5]]
        mesh.morph_targets = {'damaged': [[0, 0, 1], [0, 0, 0], [0, 0, 0], [0, 0, 2], [0, 0, 0], [0, 0, 0]]}
        # glTF vertices in another order: 0 = sub-mesh 3, 3 = sub-mesh 0
        positions = [(0, 0, 0), (-1, 0, 0), (0, -1, 0), (0, 0, 0), (1, 0, 0), (0, 1, 0)]
        deltas = self._targets_of(mesh, positions, [(0, 0)] * 6, [3, 4, 5, 0, 1, 2])
        self.assertEqual(deltas, [(0, 0, 2), (0, 0, 0), (0, 0, 0), (0, 0, 1), (0, 0, 0), (0, 0, 0)])

    def test_two_triangles_at_the_same_place_move_as_one_polygon_each(self):
        # FCE4 cars have a few triangles twice, with vertices of their own, one of them damaged
        mesh = SubMesh()
        mesh.name = 'body'
        mesh.vertices = [[0, 0, 0], [1, 0, 0], [0, 1, 0]] * 2
        mesh.vertex_uvs = [[0, 0], [1, 0], [0, 1]] * 2
        mesh.polygons = [[0, 1, 2], [3, 4, 5]]
        mesh.morph_targets = {'damaged': [[0, 0, 0]] * 3 + [[0, 0, 1], [0, 0, 2], [0, 0, 3]]}
        positions = [(0, 0, 0), (1, 0, 0), (0, 1, 0)] * 2
        deltas = self._targets_of(mesh, positions, [(0, 0), (1, 0), (0, 1)] * 2, [0, 1, 2, 3, 4, 5])
        self.assertEqual(sorted([deltas[:3], deltas[3:]]), [[(0, 0, 0)] * 3, [(0, 0, 1), (0, 0, 2), (0, 0, 3)]])

    def test_vertices_moving_alike_with_other_target_normals_matched_by_their_triangles(self):
        mesh = SubMesh()
        mesh.name = 'body'
        mesh.vertices = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 0], [-1, 0, 0], [0, -1, 0]]
        mesh.vertex_uvs = [[0, 0]] * 6
        mesh.polygons = [[0, 1, 2], [3, 4, 5]]
        mesh.morph_targets = {'damaged': [[0, 0, 0]] * 6}
        mesh.morph_target_normals = {'damaged': [[1, 0, 0]] + [[0, 0, 1]] * 2 + [[0, 1, 0]] + [[0, 0, 1]] * 2}
        positions = [(0, 0, 0), (-1, 0, 0), (0, -1, 0), (0, 0, 0), (1, 0, 0), (0, 1, 0)]
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'body.glb')
            self._write_triangles_glb(path, positions, [(0, 0)] * 6, [3, 4, 5, 0, 1, 2])
            add_glb_morph_targets(path, [mesh])
            gltf, binary = read_glb(path)
        normals = read_accessor(gltf, binary, gltf['meshes'][0]['primitives'][0]['attributes']['_GAME_NORMAL_DAMAGED'])
        self.assertEqual(normals[0], (0, 1, 0))
        self.assertEqual(normals[3], (1, 0, 0))

    def test_ambiguous_vertex_without_triangles_is_an_error(self):
        mesh = SubMesh()
        mesh.name = 'body'
        mesh.vertices = [[0, 0, 0], [0, 0, 0], [1, 0, 0], [0, 1, 0]]
        mesh.vertex_uvs = [[0, 0]] * 4
        mesh.polygons = [[0, 2, 3]]
        mesh.morph_targets = {'damaged': [[0, 0, 1], [0, 0, 2], [0, 0, 0], [0, 0, 0]]}
        with self.assertRaises(ValueError):
            # the glTF triangle has its corners in the other cyclic order: no polygon matches it
            self._targets_of(mesh, [(0, 0, 0), (1, 0, 0), (0, 1, 0)], [(0, 0)] * 3, [0, 2, 1])


class TestComposeTexturePage(unittest.TestCase):
    def test_size_is_rounded_up_to_power_of_two(self):
        page = compose_texture_page([(Image.new('RGBA', (64, 16)), 100, 20)])
        self.assertEqual(page.size, (256, 64))

    def test_explicit_size(self):
        page = compose_texture_page([(Image.new('RGBA', (16, 16)), 0, 0)], 128, 32)
        self.assertEqual(page.size, (128, 32))

    def test_places_images_and_first_one_wins_on_overlap(self):
        red = Image.new('RGBA', (16, 16), (255, 0, 0, 255))
        green = Image.new('RGBA', (16, 16), (0, 255, 0, 255))
        blue = Image.new('RGBA', (16, 16), (0, 0, 255, 255))
        page = compose_texture_page([(red, 0, 0), (green, 0, 0), (blue, 16, 0)])
        self.assertEqual(page.size, (32, 16))
        self.assertEqual(page.getpixel((5, 5)), (255, 0, 0, 255))
        self.assertEqual(page.getpixel((20, 5)), (0, 0, 255, 255))


class TestTextureAlphaMode(unittest.TestCase):
    def test_opaque_and_masked_textures_are_cutout(self):
        image = Image.new('RGBA', (16, 16), (255, 0, 0, 255))
        image.paste((0, 0, 0, 0), (0, 0, 8, 16))
        self.assertEqual(texture_alpha_mode(image), 'cutout')

    def test_anti_aliased_edges_are_cutout(self):
        image = Image.new('RGBA', (16, 16), (255, 0, 0, 255))
        image.paste((255, 0, 0, 128), (0, 0, 1, 16))
        self.assertEqual(texture_alpha_mode(image), 'cutout')

    def test_partial_alpha_is_blend(self):
        image = Image.new('RGBA', (16, 16), (255, 0, 0, 255))
        image.paste((255, 0, 0, 128), (0, 0, 4, 16))
        self.assertEqual(texture_alpha_mode(image), 'blend')


class TestCrpCarTexturePageSources(unittest.TestCase):
    def test_default_layout(self):
        self.assertEqual(
            crp_car_texture_page_sources([0, 1, 2, 3, 7]),
            {0: 0, 1: 0, 2: 1, 3: 2, 4: 3, 8: 7},
        )

    def test_layout_from_tpg(self):
        tpg = ConfigParser(strict=False)
        tpg.read_string(
            """
[tpage1.details]
mirrortpage=2
[tpage2.details]
sourcetpage=1
[file1.details]
tpage=1
[file2.details]
tpage=4
[file3.details]
tpage=3
"""
        )
        self.assertEqual(crp_car_texture_page_sources([0, 1, 2], tpg), {0: 0, 1: 0, 3: 1, 2: 2})


class TestCrpCarStyle(unittest.TestCase):
    def setUp(self):
        self.tpg = ConfigParser(strict=False, interpolation=None)
        self.tpg.read_string(
            """
[header]
numfiles=1
numtpages=2
movespoilerextent=-0.08
dooraxis=0,1,0.5
[tpage1.details]
width=256
height=256
[tpage2.details]
sourcetpage=1
bpp=4444
[file1.details]
tpage=1
[style2]
name=S
count=1
geometry1=8
type1=1
stripe=1
[style1]
name=Base
count=2
geometry1=8
type1=3
texture2=4
type2=1
[file1.top]
count=1
geometry1=8
type1=0
[file1.top1]
count=2
geometry1=8
type1=3
geometry2=8
type2=4
[file1.dec]
count=1
texture1=4
type1=1
racedecal=1
[file1.fro]
frontend=0
[file1.frf]
frontend=1
[file1.gnl]
night=1
[file1.fag]
testdrive=1
"""
        )

    def test_style_slots(self):
        # texture slots follow the 60 geometry slots; slot 10 shows the race number decals
        self.assertEqual(nfs5_style_slots(self.tpg, 0), {8: 3, 64: 1, 10: 0})
        self.assertEqual(nfs5_style_slots(self.tpg, 1, race_number=True), {8: 1, 10: 1})
        self.assertEqual(nfs5_style_slots(ConfigParser(), 0), {})

    def test_race_slots(self):
        tpg = ConfigParser(strict=False, interpolation=None)
        tpg.read_string('[style1]\ncount=2\ngeometry1=37\ntype1=1\ngeometry2=42\ntype2=1\n')
        slots = nfs5_race_slots(tpg, driver=5)
        # the convertible top up (41 = 1), its animated top hidden, the driver's body, arms and hands
        self.assertEqual(
            {k: slots[k] for k in (9, 37, 41, 42, 43, 56, 58)}, {9: 8, 37: 0, 41: 1, 42: 0, 43: 4, 56: 2, 58: 0}
        )
        self.assertEqual(nfs5_race_slots(tpg, cabrio_down=True)[41], 2)
        self.assertEqual(nfs5_race_slots(tpg, driver=None)[9], 0)

    def test_image_selection_in_a_race(self):
        slots = nfs5_style_slots(self.tpg, 0)
        self.assertFalse(crp_car_is_image_used(self.tpg, 1, 'top', slots))
        self.assertTrue(crp_car_is_image_used(self.tpg, 1, 'top1', slots))
        # the race number decal is drawn (its articles show by slot 10)
        self.assertTrue(crp_car_is_image_used(self.tpg, 1, 'dec', slots))
        # the race's images, not the showroom's
        self.assertTrue(crp_car_is_image_used(self.tpg, 1, 'fro', slots))
        self.assertFalse(crp_car_is_image_used(self.tpg, 1, 'frf', slots))
        self.assertTrue(crp_car_is_image_used(self.tpg, 1, 'sid', slots))
        self.assertTrue(crp_car_is_image_used(self.tpg, 1, 'top', {}))
        # night images at night only; test drive images on the skid pad of a factory mission only
        self.assertFalse(crp_car_is_image_used(self.tpg, 1, 'gnl', slots))
        self.assertTrue(crp_car_is_image_used(self.tpg, 1, 'gnl', slots, night=1))
        self.assertFalse(crp_car_is_image_used(self.tpg, 1, 'fag', slots))
        self.assertTrue(crp_car_is_image_used(self.tpg, 1, 'fag', slots, skidpad=True, factory_mission=True))
        self.assertFalse(crp_car_is_image_used(self.tpg, 1, 'fag', slots, skidpad=True))

    def test_tpg_info(self):
        info = nfs5_car_tpg_info(self.tpg)
        self.assertEqual(
            info['styles'],
            [
                {'name': 'Base', 'slots': [[8, 3], [64, 1]], 'stripe': False},
                {'name': 'S', 'slots': [[8, 1]], 'stripe': True},
            ],
        )
        self.assertEqual(info['header']['moveSpoilerExtent'], -0.08)
        self.assertEqual(info['header']['doorAxis'], [0.0, 1.0, 0.5])
        # the exe's defaults
        self.assertEqual(info['header']['hoodExtent'], 0.15)
        self.assertEqual(
            info['pages'],
            [
                {'index': 0, 'width': 256, 'height': 256, 'format': 1555, 'file': 0},
                {'index': 1, 'width': 0, 'height': 0, 'format': 4444, 'file': 0},
            ],
        )

    def test_packages(self):
        packages = ConfigParser(strict=False, interpolation=None)
        packages.read_string('[header]\ncount=2\n[package1]\n[package2]\nband1=1\nband14=2\n')
        result = nfs5_car_packages(packages)
        self.assertEqual(result[0], [0] * 14 + [3, 3, 0, 0])
        self.assertEqual(result[1][1], 1)
        self.assertEqual(result[1][14:16], [2, 3])

    def test_paint_bands(self):
        # k = (A + 1) * 20 >> 8: 0, 10 and 20 untinted
        self.assertIsNone(nfs5_paint_band(0))
        self.assertIsNone(nfs5_paint_band(255))
        self.assertIsNone(nfs5_paint_band(130))
        self.assertEqual(nfs5_paint_band(13), 17)
        self.assertEqual(nfs5_paint_band(140), 8)
        self.assertEqual(nfs5_paint_band(250), 0)

    def test_damage_zones(self):
        data = {
            'zones': [
                {'zone': 3, 'num_vertices': 2, 'first_index': 0},
                {'zone': 9, 'num_vertices': 1, 'first_index': 2},
            ],
            'vertex_indices': [5, 1, 0],
        }
        self.assertEqual(nfs5_damage_zones(data), {5: 3, 1: 3, 0: 9})


class TestCrpPrimitives(unittest.TestCase):
    def test_triangle_list(self):
        self.assertEqual(crp_primitive_triangles(3, 7), [(0, 1, 2), (3, 4, 5)])

    def test_strip_reverses_every_second_triangle(self):
        self.assertEqual(crp_primitive_triangles(1, 5), [(0, 1, 2), (2, 1, 3), (2, 3, 4)])
        self.assertEqual(crp_primitive_triangles(1, 2), [])

    def test_quads_split_along_first_diagonal(self):
        self.assertEqual(crp_primitive_triangles(4, 8), [(0, 1, 2), (0, 2, 3), (4, 5, 6), (4, 6, 7)])

    def test_lines_give_no_triangles(self):
        self.assertEqual(crp_primitive_triangles(2, 4), [])

    def test_stream_indices(self):
        part_data = {
            'index_rows': [{'identifier': 'vI', 'offset': 0}, {'identifier': 'uI', 'offset': 3}],
            'index_table': [5, 1, 2],
            'uv_index_table': [0, 4, 3],
        }
        # index table of the row's stream + row offset / stride
        self.assertEqual(crp_stream_indices(part_data, 3, {'offset': 32, 'index_stream': 0}, 16), [7, 3, 4])
        self.assertEqual(crp_stream_indices(part_data, 3, {'offset': 8, 'index_stream': 1}, 8), [1, 5, 4])
        # consecutive indices
        self.assertEqual(crp_stream_indices(part_data, 3, {'offset': 48, 'index_stream': 0xFFFF}, 16), [3, 4, 5])
        # no such index row
        self.assertIsNone(crp_stream_indices(part_data, 3, {'offset': 0, 'index_stream': 2}, 16))

    def test_stream_indices_of_single_uv_index_row(self):
        # the only index row is the UV one: its table is the first
        part_data = {'index_rows': [{'identifier': 'uI', 'offset': 0}], 'index_table': [2, 0, 1], 'uv_index_table': []}
        self.assertEqual(crp_stream_indices(part_data, 3, {'offset': 0, 'index_stream': 0}, 8), [2, 0, 1])


class TestCrpGeometrySerializer(unittest.TestCase):
    def _serialize(self, file_path, out):
        from library import require_file
        from serializers import get_serializer

        name, block, data = require_file(file_path)
        serializer = get_serializer(block, data)
        serializer.patch_settings(
            {'geometry__save_obj': True, 'geometry__save_blend': False, 'geometry__export_to_gg_web_engine': False}
        )
        serializer.serialize(data, out, id=name, block=block)

    def test_car_meshes_get_texture_pages(self):
        with tempfile.TemporaryDirectory() as out:
            self._serialize('test/samples/356b.crp', out)
            # wheel and window materials keep the alpha channel, other pages are opaque
            for page, size in [('0', 256), ('1', 256), ('2', 256), ('3', 128), ('3_alpha', 128), ('4_alpha', 64)]:
                with Image.open(os.path.join(out, 'textures', f'page_{page}.png')) as img:
                    self.assertEqual(img.size, (size, size))
            with open(os.path.join(out, 'material.mtl')) as f:
                mtl = f.read()
            self.assertEqual(
                re.findall(r'newmtl (\S+)', mtl),
                ['page_0', 'page_1', 'page_2', 'page_3', 'page_3_alpha', 'page_4_alpha'],
            )
            # only glass is translucent; the other pages' alpha is the paint band (data for a shader)
            self.assertEqual(
                re.findall(r'alpha_mode (\S+)', mtl), ['opaque', 'opaque', 'opaque', 'opaque', 'cutout', 'blend']
            )
            with open(os.path.join(out, 'geometry.obj')) as f:
                obj = f.read()
            body_meshes = re.findall(r'\no (Body_a\d+_LOD1_ai0[^\n]*)\n', obj)
            self.assertIn('Body_a30_LOD1_ai0_page_0', body_meshes)
            self.assertIn('Body_a30_LOD1_ai0_page_0_damaged', body_meshes)
            self.assertIn('usemtl page_0', obj)
            # triangle part without vertex index row (UV index row only)
            self.assertIn('\no DecalDoorL_a6_LOD6_ai0_page_0\n', obj)
            # triangle parts without index rows
            self.assertIn('\no Needle1_a57_LOD1_ai0_', obj)
            self.assertIn('\no InteriorDoorInGlass_a43_LOD1_ai0_', obj)

    def test_car_model_data(self):
        from library import require_resource_as
        from library.utils.id import path_to_name
        from resources.eac.geometries.nfs5 import CrpGeometry
        from serializers import CrpGeometrySerializer
        from serializers.common.three_d import Scene

        serializer = CrpGeometrySerializer()
        with tempfile.TemporaryDirectory() as out:
            self._serialize('test/samples/356b.crp', out)
            with open(os.path.join(out, 'geometry_extra.json')) as f:
                extra = json.load(f)
        articles = extra['nfs5Car']['articles']
        body = articles[30]
        self.assertEqual((body['name'], body['slot'], body['value'], body['drawFlags'] & 0x18), ('Body', 1, 0, 0x18))
        wheels = [a for a in articles if a['name'].startswith('WheelFront')]
        self.assertEqual(sorted(a['wheel'] for a in wheels), [0, 1])
        self.assertEqual({a['pivot'] for a in wheels}, {1, 2})
        self.assertIn('1', wheels[0]['transforms'])
        # every vertex of the body's mesh in a zone, per face corner of the OBJ
        zones = extra['nfs5DamageZones']['Body_a30_LOD1_ai0_page_0']
        self.assertTrue(zones and all(0 <= z <= 9 for z in zones))
        glares = [g for a in articles for g in a.get('glares', [])]
        self.assertTrue(glares)
        # morph targets of the GLB: the damaged copy and the animation frames, relative to the first frame
        _, crp_block, crp_data = require_resource_as(path_to_name('test/samples/356b.crp'), CrpGeometry)
        meshes = list(serializer._build_article_meshes(crp_data, crp_block, lambda m: None, True))
        serializer._add_car_model_data(Scene(), crp_data, crp_block, meshes, None, None)
        by_name = {sub_mesh.name: (sub_mesh, sources) for _, _, _, sub_mesh, sources in meshes}
        body, sources = by_name['Body_a30_LOD1_ai0']
        damaged, _ = by_name['Body_a30_LOD1_ai0_damaged']
        self.assertEqual(len(body.morph_targets['damaged']), len(body.vertices))
        self.assertAlmostEqual(body.vertices[5][0] + body.morph_targets['damaged'][5][0], damaged.vertices[5][0], 5)
        self.assertEqual(len(body.vertex_byte_attributes['_NFS5_DAMAGE_ZONE']), len(body.vertices))
        self.assertEqual(len(sources), len(body.vertices))
        animated = [m for name, (m, _) in by_name.items() if name.startswith('DriverBody') and '_ai0' in name]
        self.assertTrue(animated and all('frame1' in m.morph_targets for m in animated))

    def test_malformed_tpg_falls_back_to_default_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            # directory name has characters which are special in resource ids
            car_dir = os.path.join(tmp, 'my__cars')
            os.makedirs(car_dir)
            shutil.copy('test/samples/356b.crp', car_dir)
            with open(os.path.join(car_dir, '356b.tpg'), 'w') as f:
                f.write('[tpage1.details]\nwidth=256.0\nheight=256\n[file1.details]\ntpage=\n')
            out = os.path.join(tmp, 'out')
            self._serialize(os.path.join(car_dir, '356b.crp'), out)
            with open(os.path.join(out, 'material.mtl')) as f:
                self.assertEqual(
                    re.findall(r'newmtl (\S+)', f.read()),
                    ['page_0', 'page_1', 'page_2', 'page_3', 'page_3_alpha', 'page_4_alpha'],
                )

    @unittest.skipUnless(os.path.exists('test/samples/alps.crp'), 'needs NFS5 track sample test/samples/alps.crp')
    def test_track_chunks_for_track_viewer(self):
        from library import require_resource
        from library.utils.id import join_id
        from serializers import get_serializer

        (_, block, data), _ = require_resource(join_id('test/samples/alps.crp', 'data'))
        serializer = get_serializer(block, data)
        serializer.patch_settings(
            {
                'geometry__save_obj': True,
                'geometry__save_blend': False,
                'geometry__export_to_gg_web_engine': False,
                'maps__save_as_chunked': True,
            }
        )
        try:
            with tempfile.TemporaryDirectory() as out:
                files = serializer.serialize(data, out, id=join_id('test/samples/alps.crp', 'data'), block=block)
                with open(os.path.join(out, 'track_layout.json')) as f:
                    layout = json.load(f)
                # one chunk per road piece of the main road: RD0000C..RD1792C, every 8th
                self.assertEqual(len(layout['chunks']), 225)
                self.assertFalse(layout['closed'])
                self.assertEqual(len([x for x in files if x.endswith('.obj')]), 225)
                # the first road piece goes from Z=464 to Z=416
                self.assertAlmostEqual(layout['chunks'][0]['position']['z'], 464, delta=5)
                self.assertAlmostEqual(abs(layout['chunks'][0]['orientation']), math.pi, delta=0.1)
                with open(os.path.join(out, 'terrain_chunk_0.obj')) as f:
                    obj = f.read()
                # LOD 0 only, material is the FSH alias after the last "_"
                self.assertNotIn('LOD1', obj)
                self.assertIn('\no terrain_chunk_0_0_cla2\n', obj)
                self.assertNotIn('mtllib', obj)
                # pivoted at the road piece center
                xs = [float(line.split()[1]) for line in obj.splitlines() if line.startswith('v ')]
                self.assertLess(max(abs(x) for x in xs), 200)
        finally:
            serializer.patch_settings({'maps__save_as_chunked': False})


class TestFce3GeometrySerializer(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def _serialize_car_viv(self, build_data=None, fce_name='car.fce', textures=None):
        from io import BytesIO

        from library import require_resource
        from library.loader import clear_file_cache, path_to_name
        from resources.eac.archives import BigfBlock
        from serializers import get_serializer
        from test.resources.eac.test_geometries import build_fce3_data

        fce_block, fce_data = (build_data or build_fce3_data)()
        tga_items = []
        for alias, color in textures or [('car00.tga', (255, 0, 0, 0))]:
            tga = BytesIO()
            Image.new('RGBA', (4, 4), color).save(tga, format='TGA')
            tga_items.append((alias, tga.getvalue()))
        bigf = BigfBlock()
        bigf_data = bigf.new_data()
        bytes_choice = bigf.item_block.get_choice_index_by_class_name('BytesBlock')
        bigf_data['children'] = [
            {
                'alias': alias,
                'item': {'choice_index': bytes_choice, 'data': item_bytes},
                'post_offset_payload': b'',
            }
            for alias, item_bytes in [(fce_name, fce_block.pack(fce_data))] + tga_items
        ]
        viv_path = os.path.join(self.tmp_dir, 'car.viv')
        with open(viv_path, 'wb') as f:
            f.write(bigf.pack(bigf_data))
        clear_file_cache(viv_path)
        fce_id = path_to_name(viv_path) + '__children/0/item/data'
        (fce_id, block, data), _ = require_resource(fce_id)
        self.assertEqual(block.__class__, fce_block.__class__)
        serializer = get_serializer(block, data)
        serializer.patch_settings(
            {'geometry__save_obj': True, 'geometry__save_blend': False, 'geometry__export_to_gg_web_engine': False}
        )
        out_path = os.path.join(self.tmp_dir, 'out/')
        serializer.serialize(data, out_path, id=fce_id, block=block)
        return out_path

    def test_exports_parts_with_texture(self):
        out_path = self._serialize_car_viv()
        with open(os.path.join(out_path, 'geometry.obj')) as f:
            obj = f.read()
        with open(os.path.join(out_path, 'material.mtl')) as f:
            mtl = f.read()
        objects = re.findall(r'^o (.*)$', obj, re.MULTILINE)
        self.assertEqual(objects, ['hp_0_HB__car00', 'hp_1_HLFW__car00_translucent'])
        self.assertIn('map_Kd assets/car00.png', mtl)
        self.assertIn('newmtl car00_translucent', mtl)
        self.assertIn('alpha_mode blend', mtl)
        # alpha channel of car texture is not transparency
        with Image.open(os.path.join(out_path, 'assets/car00.png')) as png:
            self.assertEqual(png.convert('RGBA').getpixel((0, 0)), (255, 0, 0, 255))
        with Image.open(os.path.join(out_path, 'assets/car00_paint_mask.png')) as png:
            self.assertEqual(png.convert('RGBA').getpixel((0, 0)), (255, 0, 0, 0))
        # vertices are shared by triangle corners with the same UV: quad has 5 of them (vertex 2 has different UV in
        # both triangles). Double-sided triangle has 3 vertices and 2 faces
        self.assertEqual(len(re.findall(r'^v ', obj, re.MULTILINE)), 8)
        self.assertEqual(len(re.findall(r'^f ', obj, re.MULTILINE)), 4)
        # part position is applied, axes: (x, z, y)
        self.assertIn('v 1.0 4.0 2.0', obj)
        # V goes from bottom to top, as in OBJ
        self.assertIn('vt 0.0 0.25', obj)

    def test_exports_game_normals_and_chrome_classes(self):
        import json

        from test.resources.eac.test_geometries import build_fce3_data

        def with_flags():
            block, data = build_fce3_data()
            data['normals'][1] = {'x': 0.0, 'y': 0.0, 'z': 1.0}
            data['triangles'][1]['flags']['matte'] = True
            data['triangles'][2]['flags']['high_chrome'] = True
            return block, data

        out_path = self._serialize_car_viv(with_flags)
        with open(os.path.join(out_path, 'geometry.obj')) as f:
            obj = f.read()
        objects = re.findall(r'^o (.*)$', obj, re.MULTILINE)
        self.assertEqual(
            objects, ['hp_0_HB__car00', 'hp_0_HB__car00_matte', 'hp_1_HLFW__car00_translucent_high_chrome']
        )
        # FCE normals, axes (x, z, y) as the vertices; corners carry the normal index of their vertex
        normals = re.findall(r'^vn (.*)$', obj, re.MULTILINE)
        self.assertEqual(normals[:3], ['0.0 0.0 1.0', '0.0 1.0 0.0', '0.0 0.0 1.0'])
        self.assertEqual(len(normals), len(re.findall(r'^v ', obj, re.MULTILINE)))
        self.assertIn('f 1/1/1 2/2/2 3/3/3', obj)
        with open(os.path.join(out_path, 'geometry_extra.json')) as f:
            extra = json.load(f)
        self.assertEqual(
            extra['objects'],
            {
                'hp_0_HB__car00': {'fceChrome': 'normal'},
                'hp_0_HB__car00_matte': {'fceChrome': 'none'},
                'hp_1_HLFW__car00_translucent_high_chrome': {'fceChrome': 'high'},
            },
        )

    def test_exports_dummies(self):
        out_path = self._serialize_car_viv()
        import json

        with open(os.path.join(out_path, 'geometry_extra.json')) as f:
            extra = json.load(f)
        self.assertEqual(extra['dummies'], [{'name': 'HFLO', 'position': [0.5, 2.0, 0.25]}])

    def _exported_meta_extras(self, build_data):
        from unittest.mock import patch

        import serializers.geometries as geometries_module

        def build_with_half_size():
            block, data = build_data()
            data['half_size'] = {'x': 1.25, 'y': 0.5, 'z': 2.75}
            return block, data

        exported_scenes = []
        real_export_scenes = geometries_module.export_scenes

        def export_scenes(scenes, path, settings):
            exported_scenes.extend(scenes)
            return real_export_scenes(scenes, path, settings)

        with patch.object(geometries_module, 'export_scenes', side_effect=export_scenes):
            self._serialize_car_viv(build_with_half_size)
        return exported_scenes[0].meta_extras

    def test_meta_has_collision_half_size_in_game_axes(self):
        from test.resources.eac.test_geometries import build_fce3_data

        # not swapped to the GLB axes (x, z, y) as vertices and dummies are
        extras = self._exported_meta_extras(build_fce3_data)
        self.assertEqual(extras['collisionHalfSize'], {'x': 1.25, 'y': 0.5, 'z': 2.75})

    def test_meta_has_car_colors(self):
        from test.resources.eac.test_geometries import build_fce3_data

        def with_colors():
            block, data = build_fce3_data()
            color = {'hue': 10, 'saturation': 20, 'brightness': 30, 'transparency': 40}
            data['num_primary_colors'] = 1
            data['primary_colors'] = [color] + [{**color, 'hue': 0}] * 15
            data['num_secondary_colors'] = 0
            return block, data

        colors = self._exported_meta_extras(with_colors)['fceColors']
        self.assertEqual(
            colors, {'primary': [{'hue': 10, 'saturation': 20, 'brightness': 30, 'transparency': 40}], 'secondary': []}
        )

    def test_meta_and_extra_json_have_no_fce4_keys(self):
        from test.resources.eac.test_geometries import build_fce3_data

        self.assertEqual(set(self._exported_meta_extras(build_fce3_data)), {'collisionHalfSize', 'fceColors'})
        with open(os.path.join(self._serialize_car_viv(), 'geometry_extra.json')) as f:
            self.assertEqual(set(json.load(f)), {'curves', 'dummies', 'objects'})


# FCE4 triangle flag bits by name (`Fce4Triangle.flags`)
FCE4_FLAG_BITS = {
    'matte': 0,
    'high_chrome': 1,
    'no_cull': 2,
    'semi_transparent': 3,
    'window': 5,
    'front_window': 6,
    'left_window': 7,
    'back_window': 8,
    'right_window': 9,
    'broken_window': 10,
}


def build_fce4_model(parts):
    """FCE4 model of `parts`: dicts with `name`, `vertices` [(x, y, z)], `triangles` [(vertex indices, flags)] and
    optional `position` (x, y, z), `damaged` (vertices), `normals`, `damaged_normals` (default (0, 1, 0)),
    `animation_flags`, `uvs` (per triangle: u and v lists)"""
    from resources.eac.geometries.nfs4 import Fce4Geometry

    block = Fce4Geometry()
    data = block.new_data()
    data['version'] = 0x00101014
    data['num_parts'] = len(parts)
    data['num_arts'] = 1
    vertices, damaged, animation_flags, triangles, normals, damaged_normals = [], [], [], [], [], []
    for i, part in enumerate(parts):
        data['part_names'][i] = part['name']
        data['part_positions'][i] = dict(zip('xyz', map(float, part.get('position', (0, 0, 0)))))
        data['part_first_vertex'][i] = len(vertices)
        data['part_num_vertices'][i] = len(part['vertices'])
        data['part_first_triangle'][i] = len(triangles)
        data['part_num_triangles'][i] = len(part['triangles'])
        vertices += part['vertices']
        damaged += part.get('damaged', part['vertices'])
        normals += part.get('normals', [(0, 1, 0)] * len(part['vertices']))
        damaged_normals += part.get('damaged_normals', part.get('normals', [(0, 1, 0)] * len(part['vertices'])))
        animation_flags += part.get('animation_flags', [4] * len(part['vertices']))
        uvs = part.get('uvs', [([0.0, 0.5, 1.0], [0.25, 0.5, 0.75])] * len(part['triangles']))
        for (vertex_indices, flags), (u, v) in zip(part['triangles'], uvs):
            triangle = block.field_blocks_map['triangles'].child.new_data()
            triangle['vertex_indices'] = list(vertex_indices)
            for name, bit in FCE4_FLAG_BITS.items():
                triangle['flags'][name] = bool(flags & (1 << bit))
            triangle['u'], triangle['v'] = list(u), list(v)
            triangles.append(triangle)

    def points(values):
        return [dict(zip('xyz', map(float, value))) for value in values]

    count = len(vertices)
    data['vertices'] = points(vertices)
    data['undamaged_vertices'] = points(vertices)
    data['damaged_vertices'] = points(damaged)
    data['normals'] = points(normals)
    data['undamaged_normals'] = points(normals)
    data['damaged_normals'] = points(damaged_normals)
    data['triangles'] = triangles
    data['reserve1'] = bytes(32 * count)
    data['reserve2'] = bytes(12 * count)
    data['reserve3'] = bytes(12 * count)
    data['reserve4'] = bytes(4 * count)
    data['animation_flags'] = animation_flags
    data['reserve5'] = bytes(4 * count)
    data['reserve6'] = bytes(12 * len(triangles))
    return block, data


QUAD = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]


def obj_objects(obj: str) -> dict:
    """OBJ object name -> its face corners as positions [x, y, z] (strings as written), in file order"""
    positions, objects, current = [], {}, None
    for line in obj.splitlines():
        if line.startswith('o '):
            current = objects.setdefault(line[2:], [])
        elif line.startswith('v '):
            positions.append(line.split()[1:4])
        elif line.startswith('f '):
            current.extend(positions[int(corner.split('/')[0]) - 1] for corner in line.split()[1:])
    return objects


def write_glb_of_sub_meshes(path: str, sub_meshes):
    """A GLB as the gg-web-engine export writes it from the scene's OBJ, for `add_glb_morph_targets` and
    `add_glb_vertex_attributes`: a node per sub-mesh, positions without the pivot, the sub-mesh texture coordinates,
    the vertices in reversed order"""
    gltf = {'asset': {'version': '2.0'}, 'nodes': [], 'meshes': [], 'bufferViews': [], 'accessors': []}
    binary = bytearray()

    def add(data: bytes, component_type: int, count: int, type_name: str) -> int:
        gltf['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
        binary.extend(data)
        gltf['accessors'].append(
            {
                'bufferView': len(gltf['bufferViews']) - 1,
                'componentType': component_type,
                'count': count,
                'type': type_name,
            }
        )
        return len(gltf['accessors']) - 1

    for sub_mesh in sub_meshes:
        order = list(reversed(range(len(sub_mesh.vertices))))
        new_index = {old: new for new, old in enumerate(order)}
        positions = [[sub_mesh.vertices[i][k] - sub_mesh.pivot_offset[k] for k in range(3)] for i in order]
        uvs = [sub_mesh.vertex_uvs[i] for i in order]
        indices = [new_index[i] for polygon in sub_mesh.polygons for i in polygon]
        primitive = {
            'attributes': {
                'POSITION': add(b''.join(struct.pack('<3f', *p) for p in positions), 5126, len(positions), 'VEC3'),
                'TEXCOORD_0': add(b''.join(struct.pack('<2f', *t) for t in uvs), 5126, len(uvs), 'VEC2'),
            },
            'indices': add(b''.join(struct.pack('<I', i) for i in indices), 5125, len(indices), 'SCALAR'),
        }
        gltf['meshes'].append({'primitives': [primitive]})
        gltf['nodes'].append({'name': sub_mesh.name, 'mesh': len(gltf['meshes']) - 1})
    gltf['buffers'] = [{'byteLength': len(binary)}]
    write_glb(path, gltf, bytes(binary))


class TestFce4GeometrySerializer(unittest.TestCase):
    setUp = TestFce3GeometrySerializer.setUp
    tearDown = TestFce3GeometrySerializer.tearDown
    _serialize_car_viv = TestFce3GeometrySerializer._serialize_car_viv
    _exported_meta_extras = TestFce3GeometrySerializer._exported_meta_extras

    def _exported_scene(self, build_data):
        from unittest.mock import patch

        import serializers.geometries as geometries_module

        exported_scenes = []
        real_export_scenes = geometries_module.export_scenes

        def export_scenes(scenes, path, settings):
            exported_scenes.extend(scenes)
            return real_export_scenes(scenes, path, settings)

        with patch.object(geometries_module, 'export_scenes', side_effect=export_scenes):
            out_path = self._serialize_car_viv(build_data)
        return exported_scenes[0], out_path

    def test_meta_has_collision_half_size_in_game_axes(self):
        from test.resources.eac.test_geometries import build_fce4_data

        extras = self._exported_meta_extras(build_fce4_data)
        self.assertEqual(extras['collisionHalfSize'], {'x': 1.25, 'y': 0.5, 'z': 2.75})
        self.assertEqual(set(extras['fceColors']), {'primary', 'interior', 'secondary', 'driver_hair'})

    def test_exports_damaged_copy_of_parts(self):
        from test.resources.eac.test_geometries import build_fce4_data

        out_path = self._serialize_car_viv(build_fce4_data)
        with open(os.path.join(out_path, 'geometry.obj')) as f:
            obj = f.read()
        objects = re.findall(r'^o (.*)$', obj, re.MULTILINE)
        # triangle 0 is a window that breaks away
        self.assertEqual(
            objects,
            [
                'hp_0_HB__car00_window_breakaway',
                'hp_0_HB__car00',
                'hp_0_HB__car00_window_breakaway_damaged',
                'hp_0_HB__car00_damaged',
                'hp_1_HLFW__car00',
                'hp_1_HLFW__car00_damaged',
            ],
        )
        # damaged position of vertex 2 (x, z, y)
        self.assertIn('v 0.75 -0.5 0.75', obj)
        # V goes from top to bottom, OBJ has it from bottom to top
        self.assertIn('vt 0.0 0.75', obj)

    def test_window_classes(self):
        flags = [
            (0x60, '_window_front'),
            (0x460, '_window_front_breakaway'),
            (0x1A0, '_window_left_back'),
            # a side without bit 5 is a window too, of the class of the first triangle
            (0x40, '_window_front'),
            # bit 10 without a window bit: no window
            (0x400, ''),
            (0, ''),
            (0x20, '_window'),
            (0x220 | (1 << 3), '_window_right'),
        ]

        def build():
            return build_fce4_model(
                [{'name': ':HB', 'vertices': QUAD, 'triangles': [([0, 1, 2], f) for f, _ in flags]}]
            )

        out_path = self._serialize_car_viv(build)
        with open(os.path.join(out_path, 'geometry.obj')) as f:
            obj = f.read()
        self.assertEqual(
            re.findall(r'^o (.*)$', obj, re.MULTILINE),
            [
                'hp_0_HB__car00_window_front',
                'hp_0_HB__car00_window_front_breakaway',
                'hp_0_HB__car00_window_left_back',
                'hp_0_HB__car00',
                'hp_0_HB__car00_window',
                # the texture goes before the window class
                'hp_0_HB__car00_translucent_window_right',
            ],
        )
        with open(os.path.join(out_path, 'geometry_extra.json')) as f:
            extra = json.load(f)

        def window(sides, breaks_away=False):
            # ":HB" has chrome: every class is the "normal" one
            return {'fceChrome': 'normal', 'fceWindow': {'sides': sides, 'breaksAway': breaks_away}}

        self.assertEqual(
            extra['objects'],
            {
                'hp_0_HB__car00_window_front': window(['front']),
                'hp_0_HB__car00_window_front_breakaway': window(['front'], True),
                'hp_0_HB__car00_window_left_back': window(['left', 'back']),
                'hp_0_HB__car00': {'fceChrome': 'normal'},
                'hp_0_HB__car00_window': window([]),
                'hp_0_HB__car00_translucent_window_right': window(['right']),
            },
        )

    def _chrome_model(self):
        # ":HB": a normal, a high chrome window and a matte triangle, damaged normals a quarter turn off; ":OC" (the
        # cockpit) has chrome, the wheel and the driver none
        normals = [(0, 1, 0), (0, 1, 0), (0, 0.75, 0.5), (0, 1, 0)]
        return build_fce4_model(
            [
                {
                    'name': ':HB',
                    'vertices': QUAD,
                    'damaged': QUAD[:3] + [(0, 2, 0)],
                    'normals': normals,
                    'damaged_normals': [(1, 0, 0)] * 4,
                    'triangles': [([0, 1, 2], 0), ([0, 2, 3], 0x62), ([1, 2, 3], 1)],
                },
                {'name': ':OC', 'vertices': QUAD[:3], 'normals': normals[:3], 'triangles': [([0, 1, 2], 2)]},
                {'name': ':HLFW', 'vertices': QUAD[:3], 'triangles': [([0, 1, 2], 1)]},
                {'name': ':OD', 'vertices': QUAD[:3], 'triangles': [([0, 1, 2], 0)]},
            ]
        )

    def test_chrome_classes_of_the_chrome_parts(self):
        scene, out_path = self._exported_scene(self._chrome_model)
        names = [m.name for m in scene.sub_meshes]
        self.assertEqual(
            names,
            [
                'hp_0_HB__car00',
                # the chrome class before the window class
                'hp_0_HB__car00_high_chrome_window_front',
                'hp_0_HB__car00_matte',
                'hp_0_HB__car00_damaged',
                'hp_0_HB__car00_high_chrome_window_front_damaged',
                'hp_0_HB__car00_matte_damaged',
                'hp_1_OC__car00_high_chrome',
                'hp_1_OC__car00_high_chrome_damaged',
                # no chrome on the wheels and the driver: one mesh, whatever the flags
                'hp_2_HLFW__car00',
                'hp_2_HLFW__car00_damaged',
                'hp_3_OD__car00',
                'hp_3_OD__car00_damaged',
            ],
        )
        with open(os.path.join(out_path, 'geometry_extra.json')) as f:
            objects = json.load(f)['objects']
        self.assertEqual(
            objects,
            {
                'hp_0_HB__car00': {'fceChrome': 'normal'},
                'hp_0_HB__car00_high_chrome_window_front': {
                    'fceChrome': 'high',
                    'fceWindow': {'sides': ['front'], 'breaksAway': False},
                },
                'hp_0_HB__car00_matte': {'fceChrome': 'none'},
                'hp_0_HB__car00_damaged': {'fceChrome': 'normal'},
                'hp_0_HB__car00_high_chrome_window_front_damaged': {
                    'fceChrome': 'high',
                    'fceWindow': {'sides': ['front'], 'breaksAway': False},
                },
                'hp_0_HB__car00_matte_damaged': {'fceChrome': 'none'},
                'hp_1_OC__car00_high_chrome': {'fceChrome': 'high'},
                'hp_1_OC__car00_high_chrome_damaged': {'fceChrome': 'high'},
            },
        )

    def test_game_normals_of_the_chrome_parts(self):
        scene, out_path = self._exported_scene(self._chrome_model)
        meshes = {m.name: m for m in scene.sub_meshes}
        # FCE normals in the export axes (x, z, y)
        body = meshes['hp_0_HB__car00']
        self.assertEqual(body.vertex_normals, [[0.0, 0.0, 1.0], [0.0, 0.0, 1.0], [0.0, 0.5, 0.75]])
        self.assertTrue(body.glb_game_normals)
        # the damaged ones: the GLB attribute `_GAME_NORMAL_DAMAGED` of the undamaged mesh (the parts the game damages),
        # `vn` of the "_damaged" copy, which leaves the GLB without them
        self.assertEqual(body.morph_target_normals, {'damaged': [[1.0, 0.0, 0.0]] * 3})
        copy = meshes['hp_0_HB__car00_damaged']
        self.assertEqual(copy.vertex_normals, [[1.0, 0.0, 0.0]] * 3)
        self.assertFalse(copy.glb_game_normals)
        self.assertEqual(copy.morph_target_normals, {})
        # ":OC" is not damaged by the game
        self.assertEqual(meshes['hp_1_OC__car00_high_chrome'].morph_target_normals, {})
        self.assertEqual(len(meshes['hp_1_OC__car00_high_chrome'].vertex_normals), 3)
        for name in ('hp_2_HLFW__car00', 'hp_3_OD__car00', 'hp_3_OD__car00_damaged'):
            self.assertEqual(meshes[name].vertex_normals, [], name)
        with open(os.path.join(out_path, 'geometry.obj')) as f:
            obj = f.read()
        self.assertEqual(len(re.findall(r'^vn ', obj, re.MULTILINE)), 2 * (3 + 3 + 3) + 2 * 3)

    def test_damaged_normals_in_glb(self):
        scene, _ = self._exported_scene(self._chrome_model)
        path = os.path.join(self.tmp_dir, 'body.glb')
        write_glb_of_sub_meshes(path, scene.sub_meshes)
        add_glb_morph_targets(path, [m for m in scene.sub_meshes if m.morph_targets])
        add_glb_vertex_attributes(path, scene.sub_meshes)
        gltf, binary = read_glb(path)
        nodes = {node['name']: gltf['meshes'][node['mesh']] for node in gltf['nodes']}
        attributes = nodes['hp_0_HB__car00']['primitives'][0]['attributes']
        # GLB vertices in reversed order
        self.assertEqual(
            read_accessor(gltf, binary, attributes['_GAME_NORMAL']),
            [(0.0, 0.5, 0.75), (0.0, 0.0, 1.0), (0.0, 0.0, 1.0)],
        )
        self.assertEqual(read_accessor(gltf, binary, attributes['_GAME_NORMAL_DAMAGED']), [(1.0, 0.0, 0.0)] * 3)
        self.assertNotIn('_GAME_NORMAL', nodes['hp_0_HB__car00_damaged']['primitives'][0]['attributes'])
        self.assertNotIn('_GAME_NORMAL_DAMAGED', nodes['hp_1_OC__car00_high_chrome']['primitives'][0]['attributes'])
        self.assertIn('_GAME_NORMAL', nodes['hp_1_OC__car00_high_chrome']['primitives'][0]['attributes'])
        self.assertEqual(set(nodes['hp_2_HLFW__car00']['primitives'][0]['attributes']), {'POSITION', 'TEXCOORD_0'})

    def test_no_chrome_on_other_models(self):
        out_path = self._serialize_car_viv(self._chrome_model, fce_name='dash.fce')
        with open(os.path.join(out_path, 'geometry.obj')) as f:
            obj = f.read()
        self.assertEqual(re.findall(r'^vn ', obj, re.MULTILINE), [])
        self.assertNotRegex(obj, r'_matte|_high_chrome')

    def test_window_class_of_flags(self):
        from serializers.geometries import fce4_window_class

        self.assertIsNone(fce4_window_class(0))
        self.assertIsNone(fce4_window_class(0x40F))
        self.assertEqual(fce4_window_class(0x3E0), (('front', 'left', 'back', 'right'), False))
        self.assertEqual(fce4_window_class(0x520), (('back',), True))

    def _damage_model(self):
        # body and pop-up headlights take damage, the wheel's damaged positions are not used by the game
        moved = [(0, 0, 0), (1, 0, 0), (0.75, 0.75, -0.5), (0, 1, 0)]
        return build_fce4_model(
            [
                {'name': ':HB', 'vertices': QUAD, 'damaged': moved, 'triangles': [([0, 1, 2], 0), ([0, 2, 3], 0x60)]},
                {'name': ':HLFW', 'vertices': QUAD, 'damaged': moved, 'triangles': [([0, 1, 2], 0)]},
                {
                    'name': ':OL',
                    'position': (1, 2, 3),
                    'vertices': QUAD[:3],
                    'damaged': [(0, 0, 0.5), (1, 0, 0), (1, 1, 0)],
                    'triangles': [([0, 1, 2], 0)],
                },
            ]
        )

    def test_damaged_positions_as_morph_target(self):
        scene, _ = self._exported_scene(self._damage_model)
        meshes = {m.name: m for m in scene.sub_meshes}
        self.assertEqual(
            list(meshes),
            [
                'hp_0_HB__car00',
                'hp_0_HB__car00_window_front',
                'hp_0_HB__car00_damaged',
                'hp_0_HB__car00_window_front_damaged',
                'hp_1_HLFW__car00',
                'hp_1_HLFW__car00_damaged',
                'hp_2_OL__car00',
                'hp_2_OL__car00_damaged',
            ],
        )
        # damaged - undamaged position per mesh vertex, in the export axes (x, z, y)
        self.assertEqual(
            meshes['hp_0_HB__car00'].morph_targets, {'damaged': [[0, 0, 0], [0, 0, 0], [-0.25, -0.5, -0.25]]}
        )
        self.assertEqual(
            meshes['hp_0_HB__car00_window_front'].morph_targets,
            {'damaged': [[0, 0, 0], [-0.25, -0.5, -0.25], [0, 0, 0]]},
        )
        self.assertEqual(meshes['hp_2_OL__car00'].morph_targets, {'damaged': [[0, 0.5, 0], [0, 0, 0], [0, 0, 0]]})
        for name in ('hp_1_HLFW__car00', 'hp_0_HB__car00_damaged', 'hp_2_OL__car00_damaged'):
            self.assertEqual(meshes[name].morph_targets, {})

    def test_damaged_morph_target_in_glb(self):
        # the gg-web-engine export's post-processing on a GLB written from the scene's meshes
        scene, _ = self._exported_scene(self._damage_model)
        path = os.path.join(self.tmp_dir, 'body.glb')
        write_glb_of_sub_meshes(path, scene.sub_meshes)
        add_glb_morph_targets(path, [m for m in scene.sub_meshes if m.morph_targets])
        gltf, binary = read_glb(path)
        nodes = {node['name']: gltf['meshes'][node['mesh']] for node in gltf['nodes']}
        mesh = nodes['hp_2_OL__car00']
        self.assertEqual(mesh['extras'], {'targetNames': ['damaged']})
        self.assertEqual(mesh['weights'], [0.0])
        # GLB vertices in reversed order
        deltas = read_accessor(gltf, binary, mesh['primitives'][0]['targets'][0]['POSITION'])
        self.assertEqual(deltas, [(0, 0, 0), (0, 0, 0), (0, 0.5, 0)])
        self.assertNotIn('targets', nodes['hp_2_OL__car00_damaged']['primitives'][0])

    def test_no_morph_target_without_damaged_positions(self):
        scene, _ = self._exported_scene(
            lambda: build_fce4_model([{'name': ':HB', 'vertices': QUAD, 'triangles': [([0, 1, 2], 0)]}])
        )
        self.assertEqual([(m.name, m.morph_targets) for m in scene.sub_meshes], [('hp_0_HB__car00', {})])

    def _driver_model(self):
        # ":OD": vertex 0 turns, 1 and 2 stay (bit 2; bit 0 is the game's damage mark), 3 turns; its second triangle
        # is double-sided and has other texture coordinates at vertex 0. ":OH": every vertex turns
        return build_fce4_model(
            [
                {'name': ':HB', 'vertices': QUAD, 'damaged': QUAD[:3] + [(0, 2, 0)], 'triangles': [([0, 1, 2], 0)]},
                {
                    'name': ':OD',
                    'position': (0.5, 1, 1.5),
                    'vertices': [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 0, 1)],
                    'animation_flags': [0, 4, 5, 1],
                    'triangles': [([0, 1, 2], 0), ([3, 0, 1], 1 << 2)],
                    'uvs': [([0.0, 0.5, 1.0], [0.25, 0.5, 0.75]), ([0.0, 0.25, 0.5], [0.0, 0.0, 0.5])],
                },
                {'name': ':OH', 'vertices': QUAD[:3], 'animation_flags': [0, 0, 0], 'triangles': [([0, 1, 2], 0)]},
            ]
        )

    def test_turning_vertices(self):
        scene, out_path = self._exported_scene(self._driver_model)
        meshes = {m.name: m for m in scene.sub_meshes}
        self.assertEqual(
            meshes['hp_1_OD__car00'].vertex_byte_attributes, {'_FCE_TURNS': [[255], [0], [0], [255], [255]]}
        )
        self.assertEqual(meshes['hp_2_OH__car00'].vertex_byte_attributes, {'_FCE_TURNS': [[255], [255], [255]]})
        for name in ('hp_0_HB__car00', 'hp_1_OD__car00_damaged', 'hp_2_OH__car00_damaged'):
            self.assertEqual(meshes[name].vertex_byte_attributes, {})

        # OBJ: per face corner, in the order the OBJ has them
        with open(os.path.join(out_path, 'geometry_extra.json')) as f:
            fce_turns = json.load(f)['fceTurns']
        with open(os.path.join(out_path, 'geometry.obj')) as f:
            objects = obj_objects(f.read())
        self.assertEqual(set(fce_turns), {'hp_1_OD__car00', 'hp_2_OH__car00'})
        # ":OD" vertices in the OBJ (x, z, y), with the part position
        turns_at = {
            ('0.5', '1.5', '1.0'): 1,
            ('1.5', '1.5', '1.0'): 0,
            ('1.5', '1.5', '2.0'): 0,
            ('0.5', '2.5', '1.0'): 1,
        }
        corners = objects['hp_1_OD__car00']
        # the double-sided triangle twice
        self.assertEqual(len(corners), 9)
        self.assertEqual(fce_turns['hp_1_OD__car00'], [turns_at[tuple(c)] for c in corners])
        self.assertEqual(fce_turns['hp_1_OD__car00'], [1, 0, 0, 1, 1, 0, 0, 1, 1])
        self.assertEqual(fce_turns['hp_2_OH__car00'], [1, 1, 1])

    def test_turning_vertices_in_glb(self):
        scene, _ = self._exported_scene(self._driver_model)
        path = os.path.join(self.tmp_dir, 'body.glb')
        write_glb_of_sub_meshes(path, scene.sub_meshes)
        add_glb_vertex_attributes(path, scene.sub_meshes)
        gltf, binary = read_glb(path)
        nodes = {node['name']: gltf['meshes'][node['mesh']] for node in gltf['nodes']}
        attributes = nodes['hp_1_OD__car00']['primitives'][0]['attributes']
        accessor = gltf['accessors'][attributes['_FCE_TURNS']]
        self.assertEqual((accessor['componentType'], accessor['normalized'], accessor['type']), (5121, True, 'SCALAR'))
        # GLB vertices in reversed order
        self.assertEqual(read_accessor(gltf, binary, attributes['_FCE_TURNS']), [(255,), (255,), (0,), (0,), (255,)])
        self.assertNotIn('_FCE_TURNS', nodes['hp_1_OD__car00_damaged']['primitives'][0]['attributes'])

    def test_part_positions_in_export_axes(self):
        scene, out_path = self._exported_scene(self._driver_model)
        positions = {'hp_0_HB': [0, 0, 0], 'hp_1_OD': [0.5, 1.5, 1], 'hp_2_OH': [0, 0, 0]}
        self.assertEqual(scene.meta_extras['fcePartPositions'], positions)
        with open(os.path.join(out_path, 'geometry_extra.json')) as f:
            self.assertEqual(json.load(f)['fcePartPositions'], positions)

    def test_part_positions_of_every_part(self):
        from test.resources.eac.test_geometries import build_fce4_data

        extras = self._exported_meta_extras(build_fce4_data)
        self.assertEqual(extras['fcePartPositions'], {'hp_0_HB': [0, 0, 0], 'hp_1_HLFW': [1, 3, 2]})

    def test_part_lod_prefix(self):
        from serializers.geometries import fce4_part_lod_prefix

        self.assertEqual(
            [fce4_part_lod_prefix(x) for x in [':HB', ':MRFW', ':LB', ':TB', ':OD', ':ORM', 'body']],
            ['hp', 'mp', 'lp', 'tp', 'hp', 'hp', 'part'],
        )

    def test_upgrade_model_uses_own_texture(self):
        from test.resources.eac.test_geometries import build_fce4_data

        out_path = self._serialize_car_viv(
            build_fce4_data,
            fce_name='car1.fce',
            textures=[('car00.tga', (255, 0, 0, 223)), ('car100.tga', (0, 255, 0, 0))],
        )
        with open(os.path.join(out_path, 'material.mtl')) as f:
            mtl = f.read()
        self.assertIn('map_Kd assets/car100.png', mtl)
        self.assertNotIn('car00', mtl)
        # alpha 0 is transparency
        with Image.open(os.path.join(out_path, 'assets/car100.png')) as png:
            self.assertEqual(png.convert('RGBA').getpixel((0, 0)), (0, 255, 0, 0))
        with open(os.path.join(out_path, 'geometry.obj')) as f:
            # car1.fce is a car model too: part roles by name
            self.assertIn('o hp_0_HB__car100\n', f.read())


NFS6_CAR_SAMPLE_DIR = 'test/samples/claude_tmp/nfs6_car'


class TestNfs6CarSerializer(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def _serialize(self, model_id):
        from library import require_resource
        from serializers import get_serializer

        (model_id, block, data), _ = require_resource(model_id)
        serializer = get_serializer(block, data)
        serializer.patch_settings(
            {'geometry__save_obj': True, 'geometry__save_blend': False, 'geometry__export_to_gg_web_engine': False}
        )
        out_path = os.path.join(self.tmp_dir, 'out/')
        paths = serializer.serialize(data, out_path, id=model_id, block=block)
        return out_path, paths

    def test_car_model_without_textures(self):
        from library.loader import clear_file_cache, path_to_name
        from test.resources.eac.test_geometries import build_eagl_model

        path = os.path.join(self.tmp_dir, 'car.o')
        with open(path, 'wb') as f:
            f.write(build_eagl_model(car=True))
        clear_file_cache(path)
        out_path, paths = self._serialize(path_to_name(path))
        self.assertTrue(any(x.endswith('skins.json') for x in paths))
        with open(os.path.join(out_path, 'geometry.obj')) as f:
            obj = f.read()
        self.assertEqual(re.findall(r'^o (.*)$', obj, re.MULTILINE), ['hp_0_ALPHA_OPAQUE_HOODShape'])
        # game (x, y, z) -> (x, -z, y): Y up, front at -Z becomes Z up, front at +Y
        self.assertIn('v 1.0 -1.0 5.0\n', obj)
        # the game normals, turned the same way
        self.assertEqual(len(re.findall(r'^vn 0\.0 -0\.8\d* 0\.6\d*$', obj, re.MULTILINE)), 4)
        # rotation keeps handedness, so faces keep facing outwards: winding of every triangle is reversed back
        faces = re.findall(r'^f (\d+)/\d+/\d+ (\d+)/\d+/\d+ (\d+)/\d+/\d+$', obj, re.MULTILINE)
        self.assertEqual(faces, [('3', '1', '2'), ('4', '3', '2')])
        with open(os.path.join(out_path, 'geometry_extra.json')) as f:
            objects = json.load(f)['objects']
        self.assertEqual(objects, {'hp_0_ALPHA_OPAQUE_HOODShape': {'eaglShader': 'paint', 'eaglBlend': 'opaque'}})
        with open(os.path.join(out_path, 'lighting.json')) as f:
            lighting = json.load(f)
        self.assertEqual(lighting['locations'], [])
        self.assertIsNone(lighting['environment_map'])

    def test_car_lighting_from_game_folders(self):
        from library.loader import clear_file_cache, path_to_name
        from test.resources.eac.test_geometries import build_eagl_model

        car_dir = os.path.join(self.tmp_dir, 'Cars', 'test')
        os.makedirs(car_dir)
        path = os.path.join(car_dir, 'car.o')
        with open(path, 'wb') as f:
            f.write(build_eagl_model(car=True))
        with open(os.path.join(car_dir, 'vehicle.ini'), 'w') as f:
            f.write("'comment\n[effects]\nspecular_hotspot_exponent=55.0\n[vehicletype]\ntype=primary\n")
        for level in ['level01', 'level00']:
            os.makedirs(os.path.join(self.tmp_dir, 'tracks', 'Alpine', level))
        with open(os.path.join(self.tmp_dir, 'tracks', 'Alpine', 'level00', 'lighting.ini'), 'w') as f:
            f.write(
                '[ambientsky]\nred=196\ngreen=170\nblue=162\n[ambientground]\nred=48\ngreen=41\nblue=40\n'
                '[sun]\nred=254\ngreen=226\nblue=207\nposition_x=-691.71f\nposition_y=589.632f\nposition_z=2726.86f\n'
            )
        clear_file_cache(path)
        out_path, paths = self._serialize(path_to_name(path))
        with open(os.path.join(out_path, 'lighting.json')) as f:
            lighting = json.load(f)
        self.assertEqual(lighting['vehicle_type'], 'primary')
        self.assertEqual(lighting['specular_hotspot_exponent'], 55.0)
        self.assertEqual(
            lighting['locations'],
            [
                {
                    'name': 'Alpine',
                    'ambient_sky': [196, 170, 162],
                    'ambient_ground': [48, 41, 40],
                    'sun': [254, 226, 207],
                    'sun_position': [-691.71, 589.632, 2726.86],
                    'environment_map': None,
                }
            ],
        )

    def test_skin_specular(self):
        from configparser import ConfigParser
        from serializers.geometries import nfs6_skin_specular

        ini = ConfigParser()
        ini.read_string(
            '[skin00]\nspecular_red=217\nspecular_paint_exponent=5.0\n[skin01]\ncolor_id=red\n'
            '[skin02]\nspecular_red=1\n[SKINHP]\nspecular_red=7\nspecular_sun_intensity=20\n'
        )
        self.assertEqual(nfs6_skin_specular(ini, 'skin00'), {'specular_red': 217, 'specular_paint_exponent': 5.0})
        # the game reads [skinNN] up to the first one without specular_red
        self.assertIsNone(nfs6_skin_specular(ini, 'skin01'))
        self.assertIsNone(nfs6_skin_specular(ini, 'skin02'))
        self.assertEqual(nfs6_skin_specular(ini, 'skinhp'), {'specular_red': 7, 'specular_sun_intensity': 20})
        self.assertIsNone(nfs6_skin_specular(ini, 'skincop'))

    @unittest.skipUnless(os.path.exists(NFS6_CAR_SAMPLE_DIR), f'needs NFS6 car sample {NFS6_CAR_SAMPLE_DIR}')
    def test_car_from_car_viv(self):
        out_path, _ = self._serialize(f'{NFS6_CAR_SAMPLE_DIR}/car.viv__children/2/item/data')
        with open(os.path.join(out_path, 'geometry.obj')) as f:
            objects = re.findall(r'^o (.*)$', f.read(), re.MULTILINE)
        self.assertEqual(len(objects), 31)
        self.assertIn('hp_6_ALPHA_OPAQUE_RUBBER_Shape', objects)
        self.assertIn('mp_24_MIDLOD_Shape', objects)
        self.assertIn('lp_29_ALPHA_OPAQUE_LODShape', objects)
        with open(os.path.join(out_path, 'material.mtl')) as f:
            mtl = f.read()
        self.assertIn('map_Kd textures/skin.png', mtl)
        self.assertIn('map_Kd textures/wl00.png', mtl)
        # the texture alpha is the reflection mask, the materials ignore it
        self.assertIn('map_Kd textures/skin.png\nalpha_mode opaque', mtl)
        with open(os.path.join(out_path, 'geometry_extra.json')) as f:
            objects = json.load(f)['objects']
        # glass: black with vertex alpha 0x85
        glass = [x for x in objects.values() if x['eaglShader'] == 'glass']
        self.assertTrue(glass)
        self.assertIn(0x85 / 255, [x.get('eaglVertexAlpha') for x in glass])
        with open(os.path.join(out_path, 'skins.json')) as f:
            skins = json.load(f)
        self.assertEqual(
            [(x['name'], x['label']) for x in skins],
            [('skin00', 'red'), ('skin01', 'black'), ('skin02', 'silver'), ('skinhp', 'purple')],
        )
        for skin in skins:
            self.assertTrue(os.path.exists(os.path.join(out_path, skin['texture'])))
        with open(os.path.join(out_path, 'geometry_extra.json')) as f:
            dummies = {x['name']: x['position'] for x in json.load(f)['dummies']}
        self.assertNotIn('DAMAGE01', dummies)
        # front left wheel: left is -X, front is +Y
        x, y, z = dummies['WHEEL_FRONT_LEFT']
        self.assertLess(x, 0)
        self.assertGreater(y, 0)
        self.assertLess(dummies['LIGHT_TAIL_LEFT1'][1], 0)
