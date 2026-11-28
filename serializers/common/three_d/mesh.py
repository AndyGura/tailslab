import itertools
import math
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Tuple, List


class BaseMesh(ABC):
    def __init__(self):
        self.name = None
        self.vertices = []
        self.polygons = []
        self.vertex_uvs = []
        self.pivot_offset = (0, 0, 0)
        # morph target name -> relative delta vector [dx, dy, dz] per vertex (parallel to `vertices`), exported as glTF
        # morph targets by the gg-web-engine export (`add_glb_morph_targets`). Only `change_axes` keeps them in sync
        # with the vertices
        self.morph_targets = {}
        # unit normal [x, y, z] per vertex (parallel to `vertices`) or empty: written to the OBJ as `vn` (corners with
        # the normal of their vertex) and, by the gg-web-engine export, to the GLB as the vertex attribute
        # `_GAME_NORMAL` (`add_glb_vertex_attributes`; three.js geometry attribute `_game_normal`): the game's own
        # normals, which Blender's may differ from. Only `change_axes` keeps them in sync with the vertices
        self.vertex_normals = []
        # False: the `vertex_normals` go to the OBJ only, the GLB gets no `_GAME_NORMAL` of them
        self.glb_game_normals = True
        # morph target name -> the game's normal [x, y, z] per vertex at the target's position (parallel to
        # `vertices`, absolute, not a delta): written by the gg-web-engine export to the GLB as the vertex attribute
        # `_GAME_NORMAL_<TARGET>` (`add_glb_morph_targets`, the vertices matched as for the target; three.js
        # `_game_normal_<target>`), not to the OBJ. Only `change_axes` keeps them in sync with the vertices
        self.morph_target_normals = {}
        # [r, g, b, a] or [r, g, b] (0..1) per vertex (parallel to `vertices`) or empty: written to the OBJ as
        # `v x y z r g b` (4 decimals, the alpha left out; three.js OBJLoader reads them as the geometry attribute
        # `color`, Blender's OBJ import as the colour attribute "Color" of the `.blend`, both decoded from sRGB) and by
        # the gg-web-engine export to the GLB as the vertex attribute COLOR_0, float VEC4 or VEC3 as given, the values
        # as they are (`add_glb_vertex_attributes`; Blender then writes no COLOR_0 of its own)
        self.vertex_colors = []
        # application-specific GLB vertex attribute name (`_PSX_GOURAUD`) -> unsigned bytes per vertex (parallel to
        # `vertices`, the same count for every vertex): written by the gg-web-engine export as unsigned byte normalized
        # accessors (three.js geometry attribute of the name in lower case, value / 255; `add_glb_vertex_attributes`),
        # not to the OBJ
        self.vertex_byte_attributes = {}

    def rotate_z(self, angle):
        c, s = math.cos(angle), math.sin(angle)
        self.vertices = [[p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2]] for p in self.vertices]

    def apply_transform_matrix(self, m: List[List[float]]):
        for v in [m, *m]:
            if len(v) != 4:
                raise ValueError('Transform matrix must contain exactly 4 rows and columns')

        transformed_vertices = []
        for vertex in self.vertices:
            x, y, z = vertex[0], vertex[1], vertex[2]
            w = 1.0

            new_x = m[0][0] * x + m[0][1] * y + m[0][2] * z + m[0][3] * w
            new_y = m[1][0] * x + m[1][1] * y + m[1][2] * z + m[1][3] * w
            new_z = m[2][0] * x + m[2][1] * y + m[2][2] * z + m[2][3] * w
            new_w = m[3][0] * x + m[3][1] * y + m[3][2] * z + m[3][3] * w

            if new_w != 0:
                new_x /= new_w
                new_y /= new_w
                new_z /= new_w

            transformed_vertices.append([new_x, new_y, new_z])

        self.vertices = transformed_vertices

    @abstractmethod
    def to_obj(self, face_index_increment, mtllib=None, pivot_offset=None) -> Tuple[str, int]:
        raise NotImplementedError

    # `pivot`: the pivot offset too
    def change_axes(self, new_x='x', new_y='y', new_z='z', pivot=False):
        map = {
            'x': 0,
            'y': 1,
            'z': 2,
        }

        def get_value_from_vertex_list(vertex: list[int], coordinate: str) -> int:
            value = vertex[map[coordinate[-1]]]
            if coordinate[0] == '-':
                value = -value
            return value

        def convert(vectors):
            return [
                [
                    get_value_from_vertex_list(v, new_x),
                    get_value_from_vertex_list(v, new_y),
                    get_value_from_vertex_list(v, new_z),
                ]
                for v in vectors
            ]

        self.vertices = convert(self.vertices)
        self.morph_targets = {name: convert(deltas) for name, deltas in self.morph_targets.items()}
        self.vertex_normals = convert(self.vertex_normals)
        self.morph_target_normals = {name: convert(normals) for name, normals in self.morph_target_normals.items()}
        if pivot:
            self.pivot_offset = tuple(convert([self.pivot_offset])[0])

    def _keep_vertices(self, indices: List[int]):
        """Keeps the vertices of `indices` (old indices, in their new order) with their texture coordinates and every
        per-vertex list (normals, colours, byte attributes, morph targets and their normals) of one value per vertex.
        The polygons are not changed"""
        count = len(self.vertices)

        def kept(values):
            return [values[i] for i in indices] if len(values) == count else values

        self.vertices = [self.vertices[i] for i in indices]
        self.vertex_uvs = [self.vertex_uvs[i] for i in indices] if len(self.vertex_uvs) else self.vertex_uvs
        self.vertex_normals = kept(self.vertex_normals)
        self.vertex_colors = kept(self.vertex_colors)
        self.morph_targets = {name: kept(values) for name, values in self.morph_targets.items()}
        self.morph_target_normals = {name: kept(values) for name, values in self.morph_target_normals.items()}
        self.vertex_byte_attributes = {name: kept(values) for name, values in self.vertex_byte_attributes.items()}

    # after deleting polygons should call this function
    def remove_orphaned_vertices(self):
        used = sorted({vi for p in self.polygons for vi in p})
        if len(used) == len(self.vertices):
            return
        new_index = {old: new for new, old in enumerate(used)}
        self._keep_vertices(used)
        self.polygons = [[new_index[vi] for vi in p] for p in self.polygons]

    def extend(self, mesh: 'BaseMesh'):
        """Appends the vertices and polygons of `mesh` (its positions moved to this mesh's pivot), with their texture
        coordinates; colours when either mesh has them (white for the vertices of the other one), normals, morph
        targets and byte attributes when both have them"""
        v_offset = (
            self.pivot_offset[0] - mesh.pivot_offset[0],
            self.pivot_offset[1] - mesh.pivot_offset[1],
            self.pivot_offset[2] - mesh.pivot_offset[2],
        )
        count, other_count = len(self.vertices), len(mesh.vertices)

        def per_vertex(values, n):
            return n > 0 and len(values) == n

        own_colors, other_colors = per_vertex(self.vertex_colors, count), per_vertex(mesh.vertex_colors, other_count)
        if own_colors or other_colors:
            channels = len((self.vertex_colors if own_colors else mesh.vertex_colors)[0])
            self.vertex_colors = (
                [list(c) for c in self.vertex_colors] if own_colors else [[1.0] * channels for _ in range(count)]
            )
            self.vertex_colors.extend(
                [list(c) for c in mesh.vertex_colors]
                if other_colors
                else [[1.0] * channels for _ in range(other_count)]
            )
        if (per_vertex(self.vertex_normals, count) or not count) and per_vertex(mesh.vertex_normals, other_count):
            self.vertex_normals = [*self.vertex_normals, *mesh.vertex_normals]
        elif other_count:
            self.vertex_normals = []
        if other_count:
            # morph targets and byte attributes of both meshes, the others left out
            for name in ('morph_targets', 'morph_target_normals', 'vertex_byte_attributes'):
                own, other = getattr(self, name), getattr(mesh, name)
                setattr(
                    self,
                    name,
                    {
                        key: [*own.get(key, []), *values]
                        for key, values in other.items()
                        if per_vertex(values, other_count) and (per_vertex(own.get(key, []), count) or not count)
                    },
                )
        v_index_surplus = count
        self.vertices.extend([[v[0] + v_offset[0], v[1] + v_offset[1], v[2] + v_offset[2]] for v in mesh.vertices])
        self.polygons.extend([[v + v_index_surplus for v in p] for p in mesh.polygons])
        self.vertex_uvs.extend(mesh.vertex_uvs)

    def collapse_vertices(self):
        """Merges the vertices closer than 1 cm on every axis into the first of them, which keeps its texture
        coordinates, normal, colour and other per-vertex values"""
        self.remove_orphaned_vertices()
        # spatial hash: grid cell -> indices of the kept vertices in it
        grid_size = 0.01
        grid = defaultdict(list)
        kept = []
        new_index = []
        for v in self.vertices:
            key = tuple(int(v[k] // grid_size) for k in range(3))
            match = next(
                (
                    j
                    for dx, dy, dz in itertools.product((-1, 0, 1), repeat=3)
                    for j in grid[(key[0] + dx, key[1] + dy, key[2] + dz)]
                    if all(abs(v[k] - self.vertices[kept[j]][k]) < 0.01 for k in range(3))
                ),
                None,
            )
            if match is None:
                match = len(kept)
                kept.append(len(new_index))
                grid[key].append(match)
            new_index.append(match)
        self._keep_vertices(kept)
        self.polygons = [[new_index[vi] for vi in p] for p in self.polygons]


# Mesh with one single texture
class SubMesh(BaseMesh):
    def __init__(self):
        super().__init__()
        self.texture_id = None

    def to_obj(
        self, face_index_increment, mtllib=None, pivot_offset=None, normal_index_increment=None
    ) -> Tuple[str, int]:
        if pivot_offset is None:
            pivot_offset = self.pivot_offset
        res = f'\n\no {self.name}'
        if mtllib is not None:
            res += f'\nmtllib {mtllib}'
        has_colors = len(self.vertex_colors) == len(self.vertices) and len(self.vertices) > 0
        res += '\n' + '\n'.join(
            [
                'v '
                + ' '.join([str(coordinates[i] - pivot_offset[i]) for i in range(3)])
                + (' ' + ' '.join(str(round(c, 4)) for c in self.vertex_colors[n][:3]) if has_colors else '')
                for n, coordinates in enumerate(self.vertices)
            ]
        )
        res += '\n' + '\n'.join([f'vt {uv[0]} {1 - uv[1]}' for uv in self.vertex_uvs])
        has_normals = len(self.vertex_normals) == len(self.vertices) and len(self.vertices) > 0
        if has_normals:
            res += '\n' + '\n'.join([f'vn {n[0]} {n[1]} {n[2]}' for n in self.vertex_normals])
        if self.texture_id:
            res += '\nusemtl ' + self.texture_id
        # normals are counted apart from the vertices in an OBJ: the scene passes how many came before
        vn_increment = face_index_increment if normal_index_increment is None else normal_index_increment

        def corner(x):
            index = x + face_index_increment
            return f'{index}/{index}/{x + vn_increment}' if has_normals else f'{index}/{index}'

        res += '\n' + '\n'.join(['f ' + ' '.join([corner(x) for x in polygon]) for polygon in self.polygons])
        return res, len(self.vertices)


# Mesh with multiple textures
class Mesh(BaseMesh):
    def __init__(self):
        super().__init__()
        self.texture_ids = []

    # splits mesh to few single-texture meshes (with the normals and colours of their vertices). Returns list of
    # tuples: ( mesh, vertex index map, polygon index map )
    def split_by_texture_ids(self) -> List[Tuple[SubMesh, List[int], List[int]]]:
        texture_ids = list({x for x in self.texture_ids})
        texture_ids.sort()
        if len(texture_ids) == 1:
            sm = SubMesh()
            sm.pivot_offset = self.pivot_offset
            sm.texture_id = texture_ids[0]
            sm.name = self.name + '__' + (sm.texture_id or 'None')
            sm.vertices = self.vertices
            sm.vertex_uvs = self.vertex_uvs
            sm.vertex_normals = self.vertex_normals
            sm.vertex_colors = self.vertex_colors
            sm.polygons = self.polygons
            return [(sm, list(range(len(self.vertices))), list(range(len(self.polygons))))]
        res = []
        for texture_id in texture_ids:
            sm = SubMesh()
            sm.name = (self.name or 'None') + '__' + (texture_id or 'None')
            sm.pivot_offset = self.pivot_offset
            sm.texture_id = texture_id
            vertex_indices = []
            new_vertex_indices = {}
            polygon_indices = []
            for i, p in enumerate(self.polygons):
                if self.texture_ids[i] != texture_id:
                    continue
                polygon_indices.append(i)
                new_polygon = []
                for idx in p:
                    if idx not in new_vertex_indices:
                        new_vertex_indices[idx] = len(vertex_indices)
                        vertex_indices.append(idx)
                    new_polygon.append(new_vertex_indices[idx])
                sm.polygons.append(new_polygon)
            for v_idx in vertex_indices:
                sm.vertices.append(self.vertices[v_idx])
                sm.vertex_uvs.append(self.vertex_uvs[v_idx])
                if self.vertex_normals:
                    sm.vertex_normals.append(self.vertex_normals[v_idx])
                if self.vertex_colors:
                    sm.vertex_colors.append(self.vertex_colors[v_idx])
            res.append((sm, vertex_indices, polygon_indices))
        return res

    def sub_meshes(self) -> List[SubMesh]:
        """The single-texture meshes of `split_by_texture_ids`"""
        return [sub_mesh for sub_mesh, _, _ in self.split_by_texture_ids()]

    def to_obj(self, face_index_increment, mtllib=None, pivot_offset=None) -> Tuple[str, int]:
        sub_meshes = self.split_by_texture_ids()
        if len(sub_meshes) == 1:
            return sub_meshes[0][0].to_obj(face_index_increment, mtllib, pivot_offset)
        obj_texts = []
        for sub_model, _, _ in sub_meshes:
            obj, fii = sub_model.to_obj(face_index_increment, mtllib, pivot_offset)
            obj_texts.append(obj)
            face_index_increment += fii
        return '\n\n'.join(obj_texts), face_index_increment

    def extend(self, mesh: 'Mesh'):
        super().extend(mesh)
        self.texture_ids.extend(mesh.texture_ids)


class CubeMesh(SubMesh):
    def _build_mesh(self):
        self.vertices = [
            (-self.dimensions[0] / 2, -self.dimensions[1] / 2, -self.dimensions[2] / 2),
            (-self.dimensions[0] / 2, -self.dimensions[1] / 2, self.dimensions[2] / 2),
            (-self.dimensions[0] / 2, self.dimensions[1] / 2, -self.dimensions[2] / 2),
            (-self.dimensions[0] / 2, self.dimensions[1] / 2, self.dimensions[2] / 2),
            (self.dimensions[0] / 2, -self.dimensions[1] / 2, -self.dimensions[2] / 2),
            (self.dimensions[0] / 2, -self.dimensions[1] / 2, self.dimensions[2] / 2),
            (self.dimensions[0] / 2, self.dimensions[1] / 2, -self.dimensions[2] / 2),
            (self.dimensions[0] / 2, self.dimensions[1] / 2, self.dimensions[2] / 2),
        ]

    def __init__(self, dimensions=(1, 1, 1), position=(0, 0, 0), **kwargs):
        super().__init__(**kwargs)
        self._dimensions = dimensions
        self._position = position
        self._build_mesh()
        self.polygons = [
            (0, 1, 2),
            (2, 1, 3),
            (4, 6, 5),
            (5, 6, 7),
            (1, 0, 5),
            (5, 0, 4),
            (2, 6, 0),
            (0, 6, 4),
            (1, 5, 3),
            (3, 5, 7),
            (2, 3, 6),
            (6, 3, 7),
        ]
        self.vertex_uvs = [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0), (1, 0), (1, 1), (0, 1)]
        self.pivot_offset = (-self.position[0], -self.position[1], -self.position[2])

    @property
    def dimensions(self):
        return self._dimensions

    @dimensions.setter
    def dimensions(self, value):
        self._dimensions = value
        self._build_mesh()

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._position = value
        self.pivot_offset = (-self.position[0], -self.position[1], -self.position[2])
