"""
The sky of an NFS Hot Pursuit 2 (PS2) track on an equirectangular sky sphere texture (`sky_spherical.py`).

What the executable does (SLUS_203.62, Ghidra database `decomp/nfs6_ps2/SLUS_203.62.gzf` of nfs-web):
- 0x11c5f8 finds the scenery instances of the meshes "SKYDOME" and "SKYDOME_ENVMAP" (by `bin_hash` of the name) in
  the track bundle and keeps their transforms (0x11c450: instance rotation / 0x4000 and position, as for every
  scenery instance). 0x11c6f8 draws SKYDOME in the views 1..3 (the player views) and SKYDOME_ENVMAP in the other
  ones (environment maps). Both are spheres around the track (radius 3000..7700) with the textures SKYBLUE (around,
  repeated) and SKYBLUECAP (top) of TEX<track>TRACK.BIN.
- The GS modulates the texture by the vertex colour (0x80 = 1.0) and blends by the texture alpha; the draw groups
  of the mesh are drawn in their order.

Not traced: the camera position inside the dome (the eye is put at the dome's centre, the origin of the mesh, which
is placed at the middle of the track) and the clear colour (black; the sphere covers every direction).

The track's world axes are X, Y on the ground and Z up: a direction (x, y, z) of the sky sphere layout (Y up) is
(x, z, y) of the track, as the track viewer shows the track (terrain chunks with Z up, chunk positions swapped).
"""

from typing import List, Optional, Sequence, Tuple

from library.utils.nfs6_sky_to_spherical import render_mesh
from library.utils.sky_spherical import OUT_HEIGHT, OUT_WIDTH, blend_over, output_directions

CLEAR_COLOR = (0, 0, 0)


def nfs6_ps2_sky_to_spherical(
    meshes: List[Tuple[Sequence, Sequence, Sequence, Sequence, object]],
    out_file_name: Optional[str] = None,
    width: int = OUT_WIDTH,
    height: int = OUT_HEIGHT,
):
    """`meshes`: (vertices in the track axes around the eye, triangles, uvs, vertex colours 0xRRGGBBAA as the
    GS uses them (0x80 = 1.0), RGBA float texture (H, W, 4)) in drawing order. Returns the RGBA float image"""
    import numpy as np

    directions = output_directions(width, height).reshape(-1, 3)[:, [0, 2, 1]]
    out = np.zeros((directions.shape[0], 4))
    out[:, :3] = CLEAR_COLOR
    out[:, 3] = 255
    for vertices, triangles, uvs, colors, texture in meshes:
        # render_mesh multiplies by colour / 0xFF
        doubled = [sum(min(0xFF, ((c >> shift) & 0xFF) * 2) << shift for shift in (24, 16, 8, 0)) for c in colors]
        mask, colour = render_mesh(directions, vertices, triangles, uvs, doubled, texture)
        blend_over(out, colour, mask)
    out = out.reshape(height, width, 4)
    if out_file_name:
        from library.utils.sky_spherical import save_rgba

        save_rgba(out, out_file_name)
    return out
