"""
Adds morph targets to a GLB written by the gg-web-engine Blender exporter, which exports without them
(`export_morph=False` in its `exporter.py`).

`export_scenes` calls `add_glb_morph_targets` after Blender has written the GLB, with the sub-meshes that have
`morph_targets`. Every glTF vertex of the mesh (node name = sub-mesh name) is matched with the sub-mesh vertex at the
same position (and the same texture coordinates when positions alone are ambiguous; and the glTF triangles it is a
corner of, matched with the sub-mesh polygons, when vertices with the same position and texture coordinates move
differently): Blender reorders and splits vertices, but the GLB positions are the OBJ ones, since the OBJ is imported
with forward Y / up Z and exported without Y-up conversion. Each target becomes a glTF morph target with a POSITION
accessor of relative deltas, named in `mesh.extras.targetNames` (three.js GLTFLoader reads them into
`morphTargetDictionary`), with default weights 0. The game's normals at a target (`morph_target_normals`) become the
vertex attribute `_GAME_NORMAL_<TARGET>` of the same vertices (three.js `_game_normal_<target>`), and vertices with the
same position and deltas but other normals there are told apart by their triangles too.
"""

import itertools
import json
import logging
import math
import struct
from typing import List, Tuple

from .mesh import SubMesh

_GLB_MAGIC = b'glTF'
_CHUNK_JSON = 0x4E4F534A
_CHUNK_BIN = 0x004E4942
_FLOAT = 5126
_UNSIGNED_BYTE = 5121
_ARRAY_BUFFER = 34962
_COMPONENT_SIZES = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
_COMPONENT_FORMATS = {5120: 'b', 5121: 'B', 5122: 'h', 5123: 'H', 5125: 'I', 5126: 'f'}
_TYPE_SIZES = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}


def read_glb(path: str) -> Tuple[dict, bytes]:
    with open(path, 'rb') as f:
        data = f.read()
    magic, version, length = struct.unpack_from('<4sII', data, 0)
    if magic != _GLB_MAGIC or version != 2:
        raise ValueError(f'Not a glTF 2.0 binary file: {path}')
    offset = 12
    gltf, binary = None, b''
    while offset < length:
        chunk_length, chunk_type = struct.unpack_from('<II', data, offset)
        chunk = data[offset + 8 : offset + 8 + chunk_length]
        if chunk_type == _CHUNK_JSON:
            gltf = json.loads(chunk.decode('utf-8'))
        elif chunk_type == _CHUNK_BIN and not binary:
            binary = chunk
        offset += 8 + chunk_length
    if gltf is None:
        raise ValueError(f'GLB without JSON chunk: {path}')
    return gltf, binary


def write_glb(path: str, gltf: dict, binary: bytes):
    json_chunk = json.dumps(gltf, separators=(',', ':')).encode('utf-8')
    json_chunk += b' ' * (-len(json_chunk) % 4)
    binary += b'\x00' * (-len(binary) % 4)
    length = 12 + 8 + len(json_chunk) + (8 + len(binary) if binary else 0)
    with open(path, 'wb') as f:
        f.write(struct.pack('<4sII', _GLB_MAGIC, 2, length))
        f.write(struct.pack('<II', len(json_chunk), _CHUNK_JSON))
        f.write(json_chunk)
        if binary:
            f.write(struct.pack('<II', len(binary), _CHUNK_BIN))
            f.write(binary)


def read_accessor(gltf: dict, binary: bytes, index: int) -> List[tuple]:
    accessor = gltf['accessors'][index]
    view = gltf['bufferViews'][accessor['bufferView']]
    components = _TYPE_SIZES[accessor['type']]
    fmt = '<' + _COMPONENT_FORMATS[accessor['componentType']] * components
    item_size = struct.calcsize(fmt)
    stride = view.get('byteStride') or item_size
    start = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    return [struct.unpack_from(fmt, binary, start + i * stride) for i in range(accessor['count'])]


def _append_accessor(gltf: dict, binary: bytearray, data: bytes, accessor: dict, byte_stride: int = None) -> int:
    """Index of a new accessor (`bufferView` + `accessor`) of `data`, appended 4-byte aligned to the binary chunk as a
    buffer view of its own"""
    binary.extend(b'\x00' * (-len(binary) % 4))
    view = {'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data), 'target': _ARRAY_BUFFER}
    if byte_stride:
        view['byteStride'] = byte_stride
    gltf.setdefault('bufferViews', []).append(view)
    binary.extend(data)
    gltf.setdefault('accessors', []).append({'bufferView': len(gltf['bufferViews']) - 1, **accessor})
    return len(gltf['accessors']) - 1


def _append_float_accessor(
    gltf: dict, binary: bytearray, vectors: List[List[float]], type_name: str, bounds: bool = False
) -> int:
    """Float accessor of the vectors; `bounds`: with `min` / `max` (POSITION accessors need them)"""
    size = len(vectors[0]) if vectors else 0
    accessor = {'componentType': _FLOAT, 'count': len(vectors), 'type': type_name}
    if bounds:
        # float32 values, like the data, so that min / max bound it exactly
        as_float32 = [struct.unpack(f'<{size}f', struct.pack(f'<{size}f', *v)) for v in vectors]
        accessor['min'] = [min(v[i] for v in as_float32) for i in range(size)]
        accessor['max'] = [max(v[i] for v in as_float32) for i in range(size)]
    return _append_accessor(gltf, binary, b''.join(struct.pack(f'<{size}f', *v) for v in vectors), accessor)


def _append_byte_accessor(gltf: dict, binary: bytearray, vectors: List[List[int]]) -> int:
    """Unsigned byte normalized accessor of the vectors (1..4 bytes each), every element 4-byte aligned as glTF wants
    for vertex attributes"""
    size = len(vectors[0]) if vectors else 0
    stride = (size + 3) // 4 * 4
    accessor = {
        'componentType': _UNSIGNED_BYTE,
        'normalized': True,
        'count': len(vectors),
        'type': 'SCALAR' if size == 1 else f'VEC{size}',
    }
    data = b''.join(bytes(v) + bytes(stride - size) for v in vectors)
    return _append_accessor(gltf, binary, data, accessor, stride if stride != size else None)


def _close(a, b, tolerance: float) -> bool:
    return all(math.isclose(x, y, abs_tol=tolerance) for x, y in zip(a, b))


def _position_index(sub_mesh: SubMesh) -> dict:
    """Sub-mesh vertex indices by position rounded to 1 mm"""
    pivot = sub_mesh.pivot_offset
    index = {}
    for i, v in enumerate(sub_mesh.vertices):
        index.setdefault(tuple(round(v[k] - pivot[k], 3) for k in range(3)), []).append(i)
    return index


def _vertices_near(sub_mesh: SubMesh, index: dict, position, tolerance: float) -> List[int]:
    """Sub-mesh vertices within `tolerance` of `position`, in vertex order: those of the cells of the position index
    the tolerance reaches. Far from the origin the reach is a float32 step of the coordinate (the GLB's positions are
    float32: 2.4e-4 at 2000, the absolute positions of NFS4 extra objects)"""
    reach = [max(tolerance, 2**-23 * abs(x)) for x in position]
    # a reach under half a cell: at most two cells per axis
    if max(reach) >= 5e-4:
        cells = list(index.values())
    else:
        cells = [
            index.get(key, ())
            for key in itertools.product(*({round(x - r, 3), round(x + r, 3)} for x, r in zip(position, reach)))
        ]
    pivot = sub_mesh.pivot_offset
    candidates = sorted(i for cell in cells for i in cell)
    return [
        i
        for i in candidates
        if all(abs(sub_mesh.vertices[i][k] - pivot[k] - position[k]) <= reach[k] for k in range(3))
    ]


def _same_deltas(sub_mesh: SubMesh, indices, normals: bool = True) -> bool:
    """Whether the vertices move alike: the same deltas of every morph target (`normals`: and the same normals at it)"""
    return all(
        len({tuple(values[i]) for i in indices}) == 1
        for values in [*sub_mesh.morph_targets.values(), *(sub_mesh.morph_target_normals.values() if normals else ())]
    )


def _morph_candidates(sub_mesh: SubMesh, index: dict, position, uv, tolerance: float) -> List[int]:
    """The sub-mesh vertices that can be the glTF vertex at `position` with texture coordinates `uv`: those with the
    same position, or with the same texture coordinates among them too when the vertices at that position have
    different morph deltas"""
    candidates = _vertices_near(sub_mesh, index, position, tolerance)
    if candidates and not _same_deltas(sub_mesh, candidates) and uv is not None:
        candidates = [i for i in candidates if _close(sub_mesh.vertex_uvs[i], uv, tolerance)]
    if not candidates:
        raise ValueError(f'Mesh "{sub_mesh.name}": no vertex at {position} for the morph targets')
    return candidates


def _polygons_by_vertex(sub_mesh: SubMesh) -> dict:
    """Sub-mesh vertex index -> indices of the polygons it is a corner of"""
    polygons_of = {}
    for p, polygon in enumerate(sub_mesh.polygons):
        for i in set(polygon):
            polygons_of.setdefault(i, []).append(p)
    return polygons_of


def _matching_polygons(sub_mesh: SubMesh, polygons_of: dict, corner_sets: List[set]) -> List[Tuple[int, List[int]]]:
    """The sub-mesh polygons matching a glTF triangle, whose corners can be the sub-mesh vertices of `corner_sets`: the
    polygons with three corners, in the same cyclic order, in those sets. (polygon index, those three corners)"""
    result = []
    for p in sorted({p for s in corner_sets[0] for p in polygons_of.get(s, ())}):
        polygon = sub_mesh.polygons[p]
        for chosen in itertools.combinations(range(len(polygon)), 3):
            for rotation in range(3):
                corners = [polygon[x] for x in chosen[rotation:] + chosen[:rotation]]
                if all(c in corner_sets[i] for i, c in enumerate(corners)):
                    result.append((p, corners))
    return result


def _triangle_corner_vertices(
    sub_mesh: SubMesh, polygons_of: dict, candidates: List[List[int]], triangles, wanted: set
) -> dict:
    """For the glTF vertices `wanted`: the sub-mesh vertices they can be by the glTF triangles they are corners of
    (`candidates`: per glTF vertex, the sub-mesh vertices at its position), the corners at their place of the
    `_matching_polygons`. Per wanted vertex, the vertices every triangle with a matching polygon gives"""
    found = {}
    for triangle in triangles:
        if not wanted.intersection(triangle):
            continue
        matching = _matching_polygons(sub_mesh, polygons_of, [set(candidates[g]) for g in triangle])
        for k, g in enumerate(triangle):
            vertices = {corners[k] for _, corners in matching}
            if g in wanted and vertices:
                found[g] = found[g] & vertices if g in found else vertices
    return found


def _primitive_triangles(gltf: dict, binary: bytes, primitive: dict, count: int) -> List[tuple]:
    """Vertex index triples of a triangle list primitive, none for other modes"""
    if primitive.get('mode', 4) != 4:
        return []
    if 'indices' in primitive:
        indices = [x[0] for x in read_accessor(gltf, binary, primitive['indices'])]
    else:
        indices = list(range(count))
    return [tuple(indices[i : i + 3]) for i in range(0, len(indices) - 2, 3)]


def _match_vertices(sub_mesh: SubMesh, index: dict, positions, uvs, triangles, tolerance: float) -> List[int]:
    """Index of the sub-mesh vertex exported as each glTF vertex: of the `_morph_candidates`; where they have
    different morph deltas (vertices with the same position and texture coordinates), the one the glTF triangles of
    the vertex give (`_triangle_corner_vertices`). Left: corners of glTF triangles matching several polygons (two
    triangles at the same place, moved differently), each triangle taking a polygon of its own where it can, its
    corners moving as one polygon's"""
    candidates = [_morph_candidates(sub_mesh, index, p, uv, tolerance) for p, uv in zip(positions, uvs)]
    matches = [c[0] if _same_deltas(sub_mesh, c) else None for c in candidates]
    unresolved = {g for g, match in enumerate(matches) if match is None}
    if not unresolved:
        return matches
    polygons_of = _polygons_by_vertex(sub_mesh)
    for g, vertices in _triangle_corner_vertices(sub_mesh, polygons_of, candidates, triangles, unresolved).items():
        if _same_deltas(sub_mesh, vertices):
            matches[g] = min(vertices)
            unresolved.discard(g)

    def deltas_of(i):
        return [
            tuple(values[i]) for values in [*sub_mesh.morph_targets.values(), *sub_mesh.morph_target_normals.values()]
        ]

    taken = set()
    for triangle in triangles:
        if not unresolved.intersection(triangle):
            continue
        # polygons whose corners move as the corners of the triangle already matched
        matching = [
            (p, corners)
            for p, corners in _matching_polygons(sub_mesh, polygons_of, [set(candidates[g]) for g in triangle])
            if all(matches[g] is None or deltas_of(matches[g]) == deltas_of(c) for g, c in zip(triangle, corners))
        ]
        if not matching:
            continue
        p, corners = next((m for m in matching if m[0] not in taken), matching[0])
        taken.add(p)
        for g, c in zip(triangle, corners):
            if matches[g] is None:
                matches[g] = c
                unresolved.discard(g)
    for g in sorted(unresolved):
        # moving alike, only their normals at the targets differ: the first one
        if _same_deltas(sub_mesh, candidates[g], normals=False):
            logging.warning(
                f'Mesh "{sub_mesh.name}": vertices at {positions[g]} with other target normals, the first taken'
            )
            matches[g] = candidates[g][0]
            unresolved.discard(g)
    if unresolved:
        g = min(unresolved)
        raise ValueError(f'Mesh "{sub_mesh.name}": vertices at {positions[g]} have different morph deltas')
    return matches


def add_glb_morph_targets(glb_path: str, sub_meshes: List[SubMesh], tolerance: float = 1e-4):
    """Adds the `morph_targets` of `sub_meshes` to the meshes of the nodes with their names in the GLB file, and their
    `morph_target_normals` as the vertex attributes `_GAME_NORMAL_<TARGET>` (float VEC3, the same vertices)"""
    sub_meshes = [sm for sm in sub_meshes if sm.morph_targets]
    if not sub_meshes:
        return
    gltf, binary = read_glb(glb_path)
    binary = bytearray(binary)
    nodes = {node.get('name'): node for node in gltf.get('nodes', []) if 'mesh' in node}
    for sub_mesh in sub_meshes:
        node = nodes.get(sub_mesh.name)
        if node is None:
            raise ValueError(f'Cannot add morph targets: no mesh node "{sub_mesh.name}" in {glb_path}')
        mesh = gltf['meshes'][node['mesh']]
        target_names = list(sub_mesh.morph_targets.keys())
        index = _position_index(sub_mesh)
        for primitive in mesh['primitives']:
            positions = read_accessor(gltf, binary, primitive['attributes']['POSITION'])
            uv_accessor = primitive['attributes'].get('TEXCOORD_0')
            # the same as the sub-mesh ones: the OBJ has 1 - v, the glTF exporter flips V back
            uvs = read_accessor(gltf, binary, uv_accessor) if uv_accessor is not None else [None] * len(positions)
            triangles = _primitive_triangles(gltf, binary, primitive, len(positions))
            matches = _match_vertices(sub_mesh, index, positions, uvs, triangles, tolerance)
            primitive['targets'] = [
                {
                    'POSITION': _append_float_accessor(
                        gltf, binary, [sub_mesh.morph_targets[name][i] for i in matches], 'VEC3', bounds=True
                    )
                }
                for name in target_names
            ]
            for name, normals in sorted(sub_mesh.morph_target_normals.items()):
                if len(normals) == len(sub_mesh.vertices):
                    primitive['attributes'][f'_GAME_NORMAL_{name.upper()}'] = _append_float_accessor(
                        gltf, binary, [normals[i] for i in matches], 'VEC3'
                    )
        mesh['weights'] = [0.0] * len(target_names)
        mesh.setdefault('extras', {})['targetNames'] = target_names
    gltf['buffers'][0]['byteLength'] = len(binary) + (-len(binary) % 4)
    write_glb(glb_path, gltf, bytes(binary))


def _match_normal(sub_mesh: SubMesh, index: dict, position, uv, gltf_normal, tolerance: float) -> List[float]:
    """Game normal of the sub-mesh vertex exported as the glTF vertex at `position`: of the vertices at that position,
    those with the texture coordinates `uv` when their normals differ, then the one nearest to the glTF normal"""
    candidates = _vertices_near(sub_mesh, index, position, tolerance)
    if not candidates:
        raise ValueError(f'Mesh "{sub_mesh.name}": no vertex at {position} for the game normals')

    def normals_of(indices):
        return {tuple(sub_mesh.vertex_normals[i]) for i in indices}

    if len(normals_of(candidates)) > 1 and uv is not None:
        candidates = [i for i in candidates if _close(sub_mesh.vertex_uvs[i], uv, tolerance)] or candidates
    if len(normals_of(candidates)) > 1 and gltf_normal is not None:
        candidates.sort(key=lambda i: -sum(a * b for a, b in zip(sub_mesh.vertex_normals[i], gltf_normal)))
    return sub_mesh.vertex_normals[candidates[0]]


def _match_values(
    sub_mesh: SubMesh, values: List[list], index: dict, position, uv, tolerance: float, what: str, warn: bool = True
) -> list:
    """Values (parallel to the sub-mesh vertices) of the sub-mesh vertex exported as the glTF vertex at `position`: of
    the vertices at that position (rounded to 1 mm, else within `tolerance`), one with the texture coordinates `uv`.
    `warn`: a warning when those still differ in their values (two corners the GLB cannot tell apart)"""
    candidates = index.get(tuple(round(x, 3) for x in position)) or _vertices_near(sub_mesh, index, position, tolerance)
    if not candidates:
        raise ValueError(f'Mesh "{sub_mesh.name}": no vertex at {position} for the {what}')
    if uv is not None:
        candidates = [i for i in candidates if _close(sub_mesh.vertex_uvs[i], uv, tolerance)] or candidates
    if warn and len({tuple(values[i]) for i in candidates}) > 1:
        logging.warning(f'Mesh "{sub_mesh.name}": vertices at {position} with other attribute values, the first taken')
    return list(values[candidates[0]])


def add_glb_vertex_attributes(glb_path: str, sub_meshes: List[SubMesh], tolerance: float = 1e-4):
    """Adds the `vertex_normals` of `sub_meshes` to the meshes of the nodes with their names in the GLB file, as the
    vertex attribute `_GAME_NORMAL` (an application-specific glTF attribute; three.js GLTFLoader reads it as the
    geometry attribute `_game_normal`), their `vertex_colors` as COLOR_0 (float VEC4, or VEC3 for colours without
    alpha; replacing one Blender wrote) and their `vertex_byte_attributes` as unsigned byte normalized attributes of
    their names (three.js: the name in lower case, value / 255; `_PSX_GOURAUD`). The GLB
    keeps Blender's NORMAL: the game normals are for code that follows the game's own shading (FCE chrome,
    `FceCarMeshController`). Sub-meshes with `glb_game_normals` off get no `_GAME_NORMAL`. Vertices are matched as for
    the morph targets"""
    with_normals = {
        sm.name
        for sm in sub_meshes
        if sm.glb_game_normals and len(sm.vertices) and len(sm.vertex_normals) == len(sm.vertices)
    }
    with_colors = {sm.name for sm in sub_meshes if len(sm.vertices) and len(sm.vertex_colors) == len(sm.vertices)}
    with_bytes = {
        sm.name
        for sm in sub_meshes
        if len(sm.vertices) and any(len(v) == len(sm.vertices) for v in sm.vertex_byte_attributes.values())
    }
    sub_meshes = [sm for sm in sub_meshes if sm.name in with_normals or sm.name in with_colors or sm.name in with_bytes]
    if not sub_meshes:
        return
    gltf, binary = read_glb(glb_path)
    binary = bytearray(binary)
    nodes = {node.get('name'): node for node in gltf.get('nodes', []) if 'mesh' in node}
    for sub_mesh in sub_meshes:
        node = nodes.get(sub_mesh.name)
        if node is None:
            raise ValueError(f'Cannot add vertex attributes: no mesh node "{sub_mesh.name}" in {glb_path}')
        index = _position_index(sub_mesh)
        for primitive in gltf['meshes'][node['mesh']]['primitives']:
            attributes = primitive['attributes']
            positions = read_accessor(gltf, binary, attributes['POSITION'])
            none = [None] * len(positions)
            uvs = read_accessor(gltf, binary, attributes['TEXCOORD_0']) if 'TEXCOORD_0' in attributes else none
            if sub_mesh.name in with_normals:
                normals = read_accessor(gltf, binary, attributes['NORMAL']) if 'NORMAL' in attributes else none
                attributes['_GAME_NORMAL'] = _append_float_accessor(
                    gltf,
                    binary,
                    [_match_normal(sub_mesh, index, p, uv, n, tolerance) for p, uv, n in zip(positions, uvs, normals)],
                    'VEC3',
                    bounds=True,
                )
            if sub_mesh.name in with_colors:
                colors = [
                    _match_values(sub_mesh, sub_mesh.vertex_colors, index, p, uv, tolerance, 'vertex colors', False)
                    for p, uv in zip(positions, uvs)
                ]
                attributes['COLOR_0'] = _append_float_accessor(
                    gltf, binary, colors, f'VEC{len(colors[0]) if colors else 4}'
                )
            if sub_mesh.name in with_bytes:
                for name, values in sorted(sub_mesh.vertex_byte_attributes.items()):
                    if len(values) != len(sub_mesh.vertices):
                        continue
                    attributes[name] = _append_byte_accessor(
                        gltf,
                        binary,
                        [
                            _match_values(sub_mesh, values, index, p, uv, tolerance, 'vertex attributes')
                            for p, uv in zip(positions, uvs)
                        ],
                    )
    gltf['buffers'][0]['byteLength'] = len(binary) + (-len(binary) % 4)
    write_glb(glb_path, gltf, bytes(binary))
