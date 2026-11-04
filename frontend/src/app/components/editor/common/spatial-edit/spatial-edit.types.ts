// Spatial edits (library/spatial_edit.py): a block declares in its schema `spatial_edit` the kinds of things which can
// be moved in a 3D viewport. Positions and rotations are in the coordinates of the files the block's serializer
// writes for the viewer (export space, Z up), so the viewer needs no knowledge of the game.

export interface SpatialEditKind {
  kind: string;
  title: string;
  description?: string;
  // gizmo axes ("xyz", "z", ""), export space
  translate_axes: string;
  rotate_axes: string;
  // moving a handle drags the mesh vertices at its position (a preview until the files are written again)
  deforms_mesh?: boolean;
  // handles with `match` are picked by clicking the objects drawing them
  pick_entities?: boolean;
}

export interface SpatialHandle {
  id: string;
  chunk: number;
  position: [number, number, number];
  // quaternion [x, y, z, w], null for a kind without rotation
  rotation: [number, number, number, number] | null;
  label: string;
  // the data shown for the selected handle, relative to the block
  data_path?: string;
  // properties of the exported dummy drawing the handle
  match?: { [key: string]: any };
}

// A handle's new transform, sent to the backend
export interface SpatialMoveRequest {
  id: string;
  position: number[];
  rotation: number[] | null;
}

export interface SpatialMoveResult {
  // the handles as the file holds them, in the order of the moves
  handles: SpatialHandle[];
  changed: boolean;
}

// The track viewer's partial export (serializers/common/chunk_export.py)
export interface ChunkExportResult {
  // folder of the chunk files, relative to the static folder
  path: string;
  chunk_count: number;
  chunks: { [index: string]: { fingerprint: string; files: string[]; position: [number, number, number] } };
}

export function spatialEditKinds(schema: any): SpatialEditKind[] {
  return (schema?.spatial_edit as SpatialEditKind[]) || [];
}
