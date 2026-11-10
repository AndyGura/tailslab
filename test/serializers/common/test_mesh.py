import unittest

from serializers.common.three_d import SubMesh


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
