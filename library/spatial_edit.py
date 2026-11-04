"""Editing a block's data by moving things in a 3D viewport (the GUI's track viewer).

A block whose data has positions the GUI shows in 3D (props, terrain vertices, road points...) declares in its
`schema` under `spatial_edit` the kinds of things which can be moved, and implements `SpatialEditable`. The GUI
offers the tools of the declared kinds only: a kind without `rotate_axes` gets no rotation gizmo.

Positions and rotations are in the coordinates of the files the block's serializer writes for the viewer (the
"export space": the OBJ chunks and their dummies), so the GUI needs no knowledge of the game's axes or units. A move
is an event "the GUI moved handle `id` of `kind` to `position` with `rotation`": the block knows which native values
it changes (often several: offsets of the next vertices, the props of a moved road point, recomputed angles), and
returns them without changing the data. `apply_spatial_moves` applies the moves of the selected handles as one
undoable change and reads the handles back from the data, so the GUI gets the transform the file can hold (fixed point precision, clamped ranges, a prop
re-anchored to another road point) instead of the one it asked for.
"""

import time
from typing import Any, Dict, List, Optional, Tuple

from library.utils.id import join_id

# A spatial edit kind, as declared in a block's schema `spatial_edit` list:
# {
#     'kind': 'prop',                 # passed back to the block's methods
#     'title': 'Props',               # tool name in the GUI
#     'description': '...',           # tooltip
#     'translate_axes': 'xyz',        # gizmo axes for moving (export space), '' = cannot be moved
#     'rotate_axes': 'z',             # gizmo axes for rotating, '' = no rotation
#     'deforms_mesh': True,           # (optional) moving it drags the mesh vertices at its position, as a preview
#     'pick_entities': True,          # (optional) handles with `match` are picked by clicking the matched objects
# }
SpatialEditKind = Dict[str, Any]

# A handle, one movable thing:
# {
#     'id': '12',                     # unique within its kind
#     'chunk': 3,                     # the chunk of the viewer it belongs to (its files show it)
#     'position': [x, y, z],          # export space
#     'rotation': [x, y, z, w],       # quaternion, export space; None for a kind without rotation
#     'label': 'Prop #12',            # shown in the GUI
#     'data_path': 'props/12',        # (optional) the data shown in the GUI's detail panel, relative to the block
#     'match': {'object_index': 12},  # (optional) properties of the exported dummy drawing it
# }
SpatialHandle = Dict[str, Any]


class SpatialEditable:
    """Mixin of a block supporting spatial edits, see the module docstring"""

    def spatial_handles(self, read_data, kind: str, chunks: Optional[List[int]] = None) -> List[SpatialHandle]:
        """Handles of `kind` in the given chunks of the viewer (all of them when None)"""
        raise NotImplementedError

    def spatial_handle(self, read_data, kind: str, handle_id: str) -> SpatialHandle:
        """One handle, read from the data as it is now"""
        raise NotImplementedError

    def spatial_move(
        self, read_data, kind: str, handle_id: str, position: List[float], rotation: Optional[List[float]]
    ) -> Dict[str, Any]:
        """New values of the data for the handle moved to `position` / `rotation` (export space), keyed by their path
        relative to the block ('props/12/position'). Must not change `read_data`: the caller applies them as one
        undoable change"""
        raise NotImplementedError


def stored_value(block, value):
    """The value as the file holds it: written by `block` and read back (rounded, clamped, wrapped)"""
    return block.unpack_from_bytes(block.pack(value))


def _get_path(data, path: str):
    for key in path.split('/'):
        data = data[int(key)] if isinstance(data, list) else data[key]
    return data


def apply_spatial_moves(
    resource_id: str, block: SpatialEditable, read_data, kind: str, moves: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[SpatialHandle]]:
    """Applies moves of several handles (`{'id', 'position', 'rotation'}`) to `read_data` as one change: each move is
    made on the data the earlier ones left (a terrain vertex chain keeps the vertices moved before), a value changed by
    several moves gets one change, from its first old value to its last new one. Returns the 'set' changes (ids like
    the GUI builds them, old values included, for undo) and the handles read back from the changed data, in the order
    of `moves`"""
    import copy

    timestamp = int(time.time() * 1000)
    changes: Dict[str, Dict[str, Any]] = {}
    for move in moves:
        new_values = block.spatial_move(read_data, kind, move['id'], move['position'], move.get('rotation'))
        for path, new_value in new_values.items():
            parent_path, _, key = path.rpartition('/')
            parent = _get_path(read_data, parent_path) if parent_path else read_data
            index = int(key) if isinstance(parent, list) else key
            old_value = parent[index]
            if old_value == new_value:
                continue
            change_id = join_id(resource_id, *path.split('/'))
            if change_id not in changes:
                changes[change_id] = {
                    'id': change_id,
                    'timestamp': timestamp,
                    'op': 'set',
                    'oldValue': copy.deepcopy(old_value),
                }
            changes[change_id]['newValue'] = copy.deepcopy(new_value)
            parent[index] = new_value
    handles = [block.spatial_handle(read_data, kind, move['id']) for move in moves]
    return [c for c in changes.values() if c['oldValue'] != c['newValue']], handles


def apply_spatial_move(
    resource_id: str,
    block: SpatialEditable,
    read_data,
    kind: str,
    handle_id: str,
    position: List[float],
    rotation: Optional[List[float]],
) -> Tuple[List[Dict[str, Any]], SpatialHandle]:
    """`apply_spatial_moves` of one handle"""
    changes, handles = apply_spatial_moves(
        resource_id, block, read_data, kind, [{'id': handle_id, 'position': position, 'rotation': rotation}]
    )
    return changes, handles[0]
