"""
Adds morph targets to a GLB written by the gg-web-engine Blender exporter, which exports without them
(`export_morph=False` in its `exporter.py`).

`export_scenes` calls `add_glb_morph_targets` after Blender has written the GLB, with the sub-meshes that have
`morph_targets`. Every glTF vertex of the mesh (node name = sub-mesh name) is matched with the sub-mesh vertex at the
same position (and the same texture coordinates when positions alone are ambiguous): Blender reorders and splits
vertices, but the GLB positions are the OBJ ones, since the OBJ is imported with forward Y / up Z and exported without
Y-up conversion. Each target becomes a glTF morph target with a POSITION accessor of relative deltas, named in
`mesh.extras.targetNames` (three.js GLTFLoader reads them into `morphTargetDictionary`), with default weights 0.
"""

import json
import math
import struct
from typing import List, Tuple

from .mesh import SubMesh

_GLB_MAGIC = b'glTF'
_CHUNK_JSON = 0x4E4F534A
_CHUNK_BIN = 0x004E4942
_FLOAT = 5126
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


def _append_vec3_accessor(gltf: dict, binary: bytearray, vectors: List[List[float]]) -> int:
    binary.extend(b'\x00' * (-len(binary) % 4))
    data = b''.join(struct.pack('<3f', *v) for v in vectors)
    gltf.setdefault('bufferViews', []).append(
        {'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data), 'target': _ARRAY_BUFFER}
    )
    binary.extend(data)
    # float32 values, like the data, so that min / max bound it exactly
    as_float32 = [struct.unpack('<3f', struct.pack('<3f', *v)) for v in vectors]
    gltf.setdefault('accessors', []).append(
        {
            'bufferView': len(gltf['bufferViews']) - 1,
            'componentType': _FLOAT,
            'count': len(vectors),
            'type': 'VEC3',
            'min': [min(v[i] for v in as_float32) for i in range(3)],
            'max': [max(v[i] for v in as_float32) for i in range(3)],
        }
    )
    return len(gltf['accessors']) - 1


def _close(a, b, tolerance: float) -> bool:
    return all(math.isclose(x, y, abs_tol=tolerance) for x, y in zip(a, b))


def _match_vertex(sub_mesh: SubMesh, position, uv, tolerance: float) -> int:
    """Index of the sub-mesh vertex exported as the glTF vertex at `position` with texture coordinates `uv`: one with
    the same position, or with the same texture coordinates among them too when the vertices at that position have
    different morph deltas"""
    pivot = sub_mesh.pivot_offset
    candidates = [
        i for i, v in enumerate(sub_mesh.vertices) if _close([v[k] - pivot[k] for k in range(3)], position, tolerance)
    ]

    def same_deltas(indices):
        return all(len({tuple(deltas[i]) for i in indices}) == 1 for deltas in sub_mesh.morph_targets.values())

    if candidates and not same_deltas(candidates) and uv is not None:
        candidates = [i for i in candidates if _close(sub_mesh.vertex_uvs[i], uv, tolerance)]
    if not candidates:
        raise ValueError(f'Mesh "{sub_mesh.name}": no vertex at {position} for the morph targets')
    if not same_deltas(candidates):
        raise ValueError(f'Mesh "{sub_mesh.name}": vertices at {position} have different morph deltas')
    return candidates[0]


def add_glb_morph_targets(glb_path: str, sub_meshes: List[SubMesh], tolerance: float = 1e-4):
    """Adds the `morph_targets` of `sub_meshes` to the meshes of the nodes with their names in the GLB file"""
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
        for primitive in mesh['primitives']:
            positions = read_accessor(gltf, binary, primitive['attributes']['POSITION'])
            uv_accessor = primitive['attributes'].get('TEXCOORD_0')
            # the same as the sub-mesh ones: the OBJ has 1 - v, the glTF exporter flips V back
            uvs = read_accessor(gltf, binary, uv_accessor) if uv_accessor is not None else [None] * len(positions)
            matches = [_match_vertex(sub_mesh, p, uv, tolerance) for p, uv in zip(positions, uvs)]
            primitive['targets'] = [
                {'POSITION': _append_vec3_accessor(gltf, binary, [sub_mesh.morph_targets[name][i] for i in matches])}
                for name in target_names
            ]
        mesh['weights'] = [0.0] * len(target_names)
        mesh.setdefault('extras', {})['targetNames'] = target_names
    gltf['buffers'][0]['byteLength'] = len(binary) + (-len(binary) % 4)
    write_glb(glb_path, gltf, bytes(binary))


def _match_normal(sub_mesh: SubMesh, position, uv, gltf_normal, tolerance: float) -> List[float]:
    """Game normal of the sub-mesh vertex exported as the glTF vertex at `position`: of the vertices at that position,
    those with the texture coordinates `uv` when their normals differ, then the one nearest to the glTF normal"""
    pivot = sub_mesh.pivot_offset
    candidates = [
        i for i, v in enumerate(sub_mesh.vertices) if _close([v[k] - pivot[k] for k in range(3)], position, tolerance)
    ]
    if not candidates:
        raise ValueError(f'Mesh "{sub_mesh.name}": no vertex at {position} for the game normals')

    def normals_of(indices):
        return {tuple(sub_mesh.vertex_normals[i]) for i in indices}

    if len(normals_of(candidates)) > 1 and uv is not None:
        candidates = [i for i in candidates if _close(sub_mesh.vertex_uvs[i], uv, tolerance)] or candidates
    if len(normals_of(candidates)) > 1 and gltf_normal is not None:
        candidates.sort(key=lambda i: -sum(a * b for a, b in zip(sub_mesh.vertex_normals[i], gltf_normal)))
    return sub_mesh.vertex_normals[candidates[0]]


def _append_float_accessor(gltf: dict, binary: bytearray, vectors: List[List[float]], type_name: str) -> int:
    size = len(vectors[0]) if vectors else 0
    binary.extend(b'\x00' * (-len(binary) % 4))
    data = b''.join(struct.pack(f'<{size}f', *v) for v in vectors)
    gltf.setdefault('bufferViews', []).append(
        {'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data), 'target': _ARRAY_BUFFER}
    )
    binary.extend(data)
    gltf.setdefault('accessors', []).append(
        {'bufferView': len(gltf['bufferViews']) - 1, 'componentType': _FLOAT, 'count': len(vectors), 'type': type_name}
    )
    return len(gltf['accessors']) - 1


def _position_index(sub_mesh: SubMesh) -> dict:
    """Sub-mesh vertex indices by position rounded to 1 mm"""
    pivot = sub_mesh.pivot_offset
    index = {}
    for i, v in enumerate(sub_mesh.vertices):
        index.setdefault(tuple(round(v[k] - pivot[k], 3) for k in range(3)), []).append(i)
    return index


def _match_color(sub_mesh: SubMesh, index: dict, position, uv, tolerance: float) -> List[float]:
    """Vertex color of the sub-mesh vertex exported as the glTF vertex at `position`: of the vertices at that position,
    one with the texture coordinates `uv`"""
    candidates = index.get(tuple(round(x, 3) for x in position))
    if not candidates:
        pivot = sub_mesh.pivot_offset
        candidates = [
            i
            for i, v in enumerate(sub_mesh.vertices)
            if _close([v[k] - pivot[k] for k in range(3)], position, tolerance)
        ]
    if not candidates:
        raise ValueError(f'Mesh "{sub_mesh.name}": no vertex at {position} for the vertex colors')
    if uv is not None:
        candidates = [i for i in candidates if _close(sub_mesh.vertex_uvs[i], uv, tolerance)] or candidates
    return list(sub_mesh.vertex_colors[candidates[0]])


def add_glb_vertex_attributes(glb_path: str, sub_meshes: List[SubMesh], tolerance: float = 1e-4):
    """Adds the `vertex_normals` of `sub_meshes` to the meshes of the nodes with their names in the GLB file, as the
    vertex attribute `_GAME_NORMAL` (an application-specific glTF attribute; three.js GLTFLoader reads it as the
    geometry attribute `_game_normal`), and their `vertex_colors` as COLOR_0. The GLB keeps Blender's NORMAL: the game
    normals are for code that follows the game's own shading (FCE chrome, `FceCarMeshController`). Vertices are matched
    as for the morph targets"""
    with_normals = {sm.name for sm in sub_meshes if len(sm.vertices) and len(sm.vertex_normals) == len(sm.vertices)}
    with_colors = {sm.name for sm in sub_meshes if len(sm.vertices) and len(sm.vertex_colors) == len(sm.vertices)}
    sub_meshes = [sm for sm in sub_meshes if sm.name in with_normals or sm.name in with_colors]
    if not sub_meshes:
        return
    gltf, binary = read_glb(glb_path)
    binary = bytearray(binary)
    nodes = {node.get('name'): node for node in gltf.get('nodes', []) if 'mesh' in node}
    for sub_mesh in sub_meshes:
        node = nodes.get(sub_mesh.name)
        if node is None:
            raise ValueError(f'Cannot add vertex attributes: no mesh node "{sub_mesh.name}" in {glb_path}')
        for primitive in gltf['meshes'][node['mesh']]['primitives']:
            attributes = primitive['attributes']
            positions = read_accessor(gltf, binary, attributes['POSITION'])
            uvs = (
                read_accessor(gltf, binary, attributes['TEXCOORD_0'])
                if 'TEXCOORD_0' in attributes
                else [None] * len(positions)
            )
            if sub_mesh.name in with_normals:
                normals = (
                    read_accessor(gltf, binary, attributes['NORMAL'])
                    if 'NORMAL' in attributes
                    else [None] * len(positions)
                )
                attributes['_GAME_NORMAL'] = _append_vec3_accessor(
                    gltf,
                    binary,
                    [_match_normal(sub_mesh, p, uv, n, tolerance) for p, uv, n in zip(positions, uvs, normals)],
                )
            if sub_mesh.name in with_colors:
                index = _position_index(sub_mesh)
                attributes['COLOR_0'] = _append_float_accessor(
                    gltf,
                    binary,
                    [_match_color(sub_mesh, index, p, uv, tolerance) for p, uv in zip(positions, uvs)],
                    'VEC4',
                )
    gltf['buffers'][0]['byteLength'] = len(binary) + (-len(binary) % 4)
    write_glb(glb_path, gltf, bytes(binary))
