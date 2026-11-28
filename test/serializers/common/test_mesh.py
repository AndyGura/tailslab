import unittest

from serializers.common.three_d import Mesh, SubMesh


class TestMesh(unittest.TestCase):
    def test_remove_orphaned_vertices(self):
        mesh = SubMesh()
        mesh.vertices = [[0, 0, 0], [0, 5, 0], [0, 0, 5], [5, 0, 0], [5, 5, 0], [5, 0, 5], [0, 5, 5], [5, 5, 5]]
        mesh.vertex_uvs = [
            [0, 0],
            [0, 5],
            [0, 3],
            [5, 0],
            [5, 5],
            [3, 0],
            [3, 5],
            [3, 3],
        ]
        mesh.polygons = [[0, 2, 1], [5, 6, 4]]
        mesh.remove_orphaned_vertices()
        self.assertEqual(mesh.vertices, [[0, 0, 0], [0, 5, 0], [0, 0, 5], [5, 5, 0], [5, 0, 5], [0, 5, 5]])
        self.assertEqual(
            mesh.vertex_uvs,
            [
                [0, 0],
                [0, 5],
                [0, 3],
                [5, 5],
                [3, 0],
                [3, 5],
            ],
        )
        self.assertEqual(mesh.polygons, [[0, 2, 1], [4, 5, 3]])

    def test_collapse_vertices(self):
        mesh = SubMesh()
        mesh.vertices = [
            [0, 0, 0],
            [5, 5, 0],
            [5, 0, 0],
            [5, 5, 0],
            [5, 0, 0],
            [10, 0, 0],
            [5, 5, 20],
            [5, 0, 20],
            [10, 0, 20],
        ]
        mesh.vertex_uvs = [0, 0] * len(mesh.vertices)
        mesh.polygons = [[0, 2, 1], [3, 4, 5], [8, 6, 7]]
        mesh.collapse_vertices()
        self.assertEqual(
            mesh.vertices,
            [
                [0, 0, 0],
                [5, 5, 0],
                [5, 0, 0],
                [10, 0, 0],
                [5, 5, 20],
                [5, 0, 20],
                [10, 0, 20],
            ],
        )
        self.assertEqual(mesh.polygons, [[0, 2, 1], [1, 2, 3], [6, 4, 5]])

    def test_to_obj_writes_vertex_colors_without_alpha(self):
        mesh = SubMesh()
        mesh.name = 'part'
        mesh.vertices = [[0, 0, 0], [1, 0, 0], [0, 1, 0]]
        mesh.vertex_uvs = [[0, 0], [1, 0], [0, 1]]
        mesh.vertex_colors = [[0.5, 0.25, 1, 0.5], [0, 0, 0, 1], [1, 1, 1, 1]]
        mesh.polygons = [[0, 1, 2]]
        obj, _ = mesh.to_obj(1)
        vertex_lines = [x for x in obj.split('\n') if x.startswith('v ')]
        self.assertEqual(vertex_lines, ['v 0 0 0 0.5 0.25 1', 'v 1 0 0 0 0 0', 'v 0 1 0 1 1 1'])

    def test_split_by_texture_ids_keeps_vertex_colors(self):
        mesh = Mesh()
        mesh.name = 'block_0'
        mesh.vertices = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]]
        mesh.vertex_uvs = [[0, 0], [1, 0], [0, 1], [1, 1]]
        mesh.vertex_colors = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9], [1, 1, 1]]
        mesh.polygons = [[0, 1, 2], [3, 2, 1]]
        mesh.texture_ids = ['a', 'b']
        a, b = mesh.sub_meshes()
        self.assertEqual(a.vertex_colors, [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]])
        self.assertEqual(b.vertex_colors, [[1, 1, 1], [0.7, 0.8, 0.9], [0.4, 0.5, 0.6]])
        mesh.texture_ids = ['a', 'a']
        (single,) = mesh.sub_meshes()
        self.assertEqual(single.vertex_colors, mesh.vertex_colors)

    def test_to_obj_writes_vertex_colors_with_4_decimals(self):
        import numpy as np

        mesh = SubMesh()
        mesh.name = 'part'
        mesh.vertices = [[0, 0, 0], [1, 0, 0], [0, 1, 0]]
        mesh.vertex_uvs = [[0, 0], [1, 0], [0, 1]]
        # the game's bytes / 255: 4 decimals give the same bytes back
        mesh.vertex_colors = np.array([[72, 72, 110, 255], [255, 0, 1, 255], [128, 128, 128, 128]]) / 255
        mesh.polygons = [[0, 1, 2]]
        obj, _ = mesh.to_obj(1)
        vertex_lines = [x for x in obj.split('\n') if x.startswith('v ')]
        self.assertEqual(
            vertex_lines, ['v 0 0 0 0.2824 0.2824 0.4314', 'v 1 0 0 1.0 0.0 0.0039', 'v 0 1 0 0.502 0.502 0.502']
        )
        self.assertEqual([round(float(x) * 255) for x in vertex_lines[0].split()[4:]], [72, 72, 110])

    def test_to_obj_writes_no_colors_unless_every_vertex_has_one(self):
        mesh = SubMesh()
        mesh.name = 'part'
        mesh.vertices = [[0, 0, 0], [1, 0, 0], [0, 1, 0]]
        mesh.vertex_uvs = [[0, 0], [1, 0], [0, 1]]
        mesh.vertex_colors = [[1, 1, 1], [0, 0, 0]]
        mesh.polygons = [[0, 1, 2]]
        obj, _ = mesh.to_obj(1)
        self.assertEqual([x for x in obj.split('\n') if x.startswith('v ')], ['v 0 0 0', 'v 1 0 0', 'v 0 1 0'])

    def test_to_obj_writes_colors_and_normals_of_each_texture(self):
        mesh = Mesh()
        mesh.name = 'block_0'
        mesh.vertices = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]]
        mesh.vertex_uvs = [[0, 0], [1, 0], [0, 1], [1, 1]]
        mesh.vertex_normals = [[0, 0, 1]] * 4
        mesh.vertex_colors = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9], [1, 1, 1]]
        mesh.polygons = [[0, 1, 2], [3, 2, 1]]
        mesh.texture_ids = ['a', 'b']
        obj, next_index = mesh.to_obj(1)
        self.assertEqual(next_index, 7)
        self.assertEqual(
            [x for x in obj.split('\n') if x.startswith(('o ', 'v ', 'usemtl ', 'f '))],
            [
                'o block_0__a',
                'v 0 0 0 0.1 0.2 0.3',
                'v 1 0 0 0.4 0.5 0.6',
                'v 0 1 0 0.7 0.8 0.9',
                'usemtl a',
                'f 1/1/1 2/2/2 3/3/3',
                'o block_0__b',
                'v 1 1 0 1 1 1',
                'v 0 1 0 0.7 0.8 0.9',
                'v 1 0 0 0.4 0.5 0.6',
                'usemtl b',
                'f 4/4/4 5/5/5 6/6/6',
            ],
        )

    def test_change_axes_keeps_vertex_colors(self):
        mesh = SubMesh()
        mesh.vertices = [[1, 2, 3]]
        mesh.vertex_normals = [[0, 1, 0]]
        mesh.vertex_colors = [[0.25, 0.5, 0.75, 1.0]]
        mesh.change_axes(new_y='z', new_z='y')
        self.assertEqual(mesh.vertices, [[1, 3, 2]])
        self.assertEqual(mesh.vertex_normals, [[0, 0, 1]])
        self.assertEqual(mesh.vertex_colors, [[0.25, 0.5, 0.75, 1.0]])

    def _mesh_with_vertex_values(self) -> SubMesh:
        """5 vertices, the third one used by no polygon, each with its own normal, colour, byte value, morph delta"""
        mesh = SubMesh()
        mesh.vertices = [[0, 0, 0], [1, 0, 0], [9, 9, 9], [0, 1, 0], [1, 1, 0]]
        mesh.vertex_uvs = [[0, 0], [1, 0], [0.5, 0.5], [0, 1], [1, 1]]
        mesh.vertex_normals = [[0, 0, 1], [0, 1, 0], [1, 0, 0], [0, 0, -1], [0, -1, 0]]
        mesh.vertex_colors = [[0, 0, 0, 1], [0.25, 0, 0, 1], [0.5, 0, 0, 1], [0.75, 0, 0, 1], [1, 0, 0, 1]]
        mesh.vertex_byte_attributes = {'_NFS5_MATERIAL': [[0], [1], [2], [3], [4]]}
        mesh.morph_targets = {'damaged': [[0, 0, 0], [0, 0, 1], [0, 0, 2], [0, 0, 3], [0, 0, 4]]}
        mesh.polygons = [[0, 1, 3], [3, 1, 4]]
        return mesh

    def test_remove_orphaned_vertices_keeps_the_values_of_the_other_vertices(self):
        mesh = self._mesh_with_vertex_values()
        mesh.remove_orphaned_vertices()
        self.assertEqual(mesh.vertices, [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]])
        self.assertEqual(mesh.polygons, [[0, 1, 2], [2, 1, 3]])
        self.assertEqual(mesh.vertex_uvs, [[0, 0], [1, 0], [0, 1], [1, 1]])
        self.assertEqual(mesh.vertex_normals, [[0, 0, 1], [0, 1, 0], [0, 0, -1], [0, -1, 0]])
        self.assertEqual([c[0] for c in mesh.vertex_colors], [0, 0.25, 0.75, 1])
        self.assertEqual(mesh.vertex_byte_attributes, {'_NFS5_MATERIAL': [[0], [1], [3], [4]]})
        self.assertEqual(mesh.morph_targets, {'damaged': [[0, 0, 0], [0, 0, 1], [0, 0, 3], [0, 0, 4]]})

    def test_collapse_vertices_keeps_the_values_of_the_first_vertex_of_a_place(self):
        mesh = self._mesh_with_vertex_values()
        # a corner of its own at the place of vertex 1, with another colour
        mesh.vertices.append([1.001, 0, 0])
        mesh.vertex_uvs.append([1, 0])
        mesh.vertex_normals.append([1, 0, 0])
        mesh.vertex_colors.append([0, 1, 0, 1])
        mesh.vertex_byte_attributes['_NFS5_MATERIAL'].append([5])
        mesh.morph_targets['damaged'].append([0, 0, 5])
        mesh.polygons[1] = [3, 5, 4]
        mesh.collapse_vertices()
        self.assertEqual(mesh.vertices, [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]])
        self.assertEqual(mesh.polygons, [[0, 1, 2], [2, 1, 3]])
        self.assertEqual([c[:2] for c in mesh.vertex_colors], [[0, 0], [0.25, 0], [0.75, 0], [1, 0]])
        self.assertEqual(len(mesh.vertex_normals), 4)
        self.assertEqual(mesh.vertex_byte_attributes, {'_NFS5_MATERIAL': [[0], [1], [3], [4]]})

    def test_extend_joins_the_vertex_colors(self):
        a = SubMesh()
        a.vertices = [[0, 0, 0], [1, 0, 0], [0, 1, 0]]
        a.vertex_uvs = [[0, 0], [1, 0], [0, 1]]
        a.vertex_normals = [[0, 0, 1]] * 3
        a.vertex_colors = [[0.5, 0.5, 0.5, 0.5]] * 3
        a.polygons = [[0, 1, 2]]
        b = SubMesh()
        b.vertices = [[0, 0, 1], [1, 0, 1], [0, 1, 1]]
        b.vertex_uvs = [[0, 0], [1, 0], [0, 1]]
        b.vertex_normals = [[0, 1, 0]] * 3
        b.polygons = [[0, 1, 2]]
        b.pivot_offset = (0, 0, 1)
        a.extend(b)
        self.assertEqual(a.vertices[3:], [[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        self.assertEqual(a.polygons, [[0, 1, 2], [3, 4, 5]])
        # white for the vertices of the mesh without colours
        self.assertEqual(a.vertex_colors, [[0.5, 0.5, 0.5, 0.5]] * 3 + [[1.0, 1.0, 1.0, 1.0]] * 3)
        self.assertEqual(a.vertex_normals, [[0, 0, 1]] * 3 + [[0, 1, 0]] * 3)
        # normals of one mesh only can't be joined
        c = SubMesh()
        c.vertices = [[2, 2, 2]]
        c.vertex_uvs = [[0, 0]]
        c.vertex_colors = [[0, 0, 0, 1]]
        a.extend(c)
        self.assertEqual(a.vertex_normals, [])
        self.assertEqual(a.vertex_colors[-1], [0, 0, 0, 1])
        self.assertEqual(len(a.vertex_colors), len(a.vertices))
