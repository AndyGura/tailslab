"""
The sky of an NFS6 (Hot Pursuit 2) location (`tracks/<location>/persist.viv`: EAGL model `skyg.o` + textures
`sky.fsh`) on an equirectangular sky sphere texture (`sky_spherical.py`), drawn as NFSHP2.exe (PC, 2003) draws it.

What the executable does (Ghidra database `decomp/nfs6/NFSHP2.exe.gzf` of nfs-web, names given there):
- `Nfs6Persist_Load` 0x4382a0 loads `sky.fsh` and `skyg.o` of `tracks/<location>/persist.viv` (the location's
  sky: every `levelNN` of the location draws the same one, `lighting.ini` of the levels only sets the sun glow,
  ambient and shadow colours). `Tr.ini` (`[strip]`, `[clouds]`, `[sun]`...), `sun.ini` and `Fog.ini` are not read
  by the game (none of their key names is in the executable): leftovers of the NFS4/NFS5 tool chain.
- `Eagl_SetTrackBlendStates` 0x4d74e0 sets the "TrackState" and "Pass2State" GIF states of the sky model, like the
  track's: alpha blend mode BLEND (`GifState_SetAlphaBlendMode` 0x553620: 1 = SRCALPHA, INVSRCALPHA).
- `Nfs6Persist_DrawSky` 0x4387d0 / 0x4388d0 draws the model with the transform translate(camera.x,
  camera.y - 12.4, -camera.z) (the camera's z is negated into model space): the model moves with the camera, which
  sits `EYE_HEIGHT` above the model origin. `Nfs6Fog_Apply` 0x436640 (called with 1 before and 0 after it) gives the
  sky its own fog density, FogSkyDensity * FogDensity * 0.04 of the current compartment's `drvpath.ini` effects
  (world: FogDensity * 0.01), in the compartment's fog colour. Not applied here: it changes along the track, it is 0
  in Alpine and Medit and in part of Tropics, and the vertex fog formula of the EAGL shaders was not traced.
- The model draws its render methods in index order (data: the command list the `__Model:::skyfs` header points to
  lists them `skyfs_0` first), each with the `NamedTexture` microcode, alpha blended. Not traced in the executable:
  that the microcode multiplies the texture by the vertex diffuse colour (0xf8f8f8, or white in Medit) as Direct3D's
  MODULATE does, done here.
- Clear colour: every one the executable sets is opaque black (`EaglView_SetClearColor` 0x55edb0, e.g. from the
  128x128 views of 0x542010); the main view's was not traced, black is assumed where no sky mesh is (below the
  horizon in Alpine).
- The sun glow (`sun.fsh`, `lighting.ini` `[SunGlow]`, drawn by 0x43e940 after the sky) is a screen-space flare
  with an occlusion test, left out; the sun painted in the sky texture is there.

Every output pixel casts the ray from the eye against the triangles of every mesh (texture coordinates from the
barycentric coordinates of the hit: exact perspective-correct interpolation, as the GPU does it, texture repeated
outside 0..1 like the Direct3D default WRAP addressing; not traced in the executable) and the meshes are composed in
the game's order. Texture sampling is bilinear.
"""

import math
from typing import Dict, List, Optional, Sequence, Tuple

from library.utils.sky_spherical import OUT_HEIGHT, OUT_WIDTH, blend_over, output_directions, sample_bilinear

# the camera is this far above the origin of the sky model (`Nfs6Persist_DrawSky`, float at 0x65de10)
EYE_HEIGHT = 12.4
# clear colour where no sky mesh is (every clear colour the executable sets is black; the main view's not traced)
CLEAR_COLOR = (0, 0, 0)


def _ray_hits(directions, triangle):
    """Rays from the origin (the eye) along `directions` (N, 3) against one triangle: (hit mask, barycentric b1, b2, distance)"""
    import numpy as np

    a, b, c = (np.asarray(p, dtype=np.float64) for p in triangle)
    e1 = b - a
    e2 = c - a
    p = np.cross(directions, e2)
    det = p @ e1
    ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
    s = -a
    b1 = (p @ s) * inv
    q = np.cross(s, e1)
    b2 = (directions @ q) * inv
    t = (q @ e2) * inv
    hit = ok & (b1 >= -1e-9) & (b2 >= -1e-9) & (b1 + b2 <= 1 + 1e-9) & (t > 0)
    return hit, b1, b2, t


def render_mesh(
    directions,
    vertices: Sequence[Tuple[float, float, float]],
    triangles: Sequence[Tuple[int, int, int]],
    uvs: Sequence[Tuple[float, float]],
    colors: Sequence[int],
    texture,
    wrap: bool = True,
    eye: Tuple[float, float, float] = (0.0, 0.0, 0.0),
):
    """Colours (N, 4) of one textured mesh seen along `directions` (N, 3) from `eye` and the mask of the
    directions that hit it (nearest triangle wins). The texture is modulated by the vertex diffuse colour (Direct3D
    MODULATE of texture and diffuse, colour and alpha)"""
    import numpy as np

    n = directions.shape[0]
    best_t = np.full(n, np.inf)
    out_uv = np.zeros((n, 2))
    out_color = np.full((n, 4), 255.0)
    vertices = np.asarray(vertices, dtype=np.float64) - np.asarray(eye, dtype=np.float64)
    uvs = np.asarray(uvs, dtype=np.float64)
    rgba = (
        np.array([[(c >> 24) & 0xFF, (c >> 16) & 0xFF, (c >> 8) & 0xFF, c & 0xFF] for c in colors], dtype=np.float64)
        if colors
        else np.full((len(vertices), 4), 255.0)
    )
    for i0, i1, i2 in triangles:
        tri = vertices[[i0, i1, i2]]
        # only the directions inside the cone around the triangle
        centre = tri.mean(axis=0)
        centre_dir = centre / np.linalg.norm(centre)
        cos_max = min(np.dot(v / np.linalg.norm(v), centre_dir) for v in tri)
        candidates = np.nonzero(directions @ centre_dir >= cos_max - 1e-6)[0]
        if not len(candidates):
            continue
        hit, b1, b2, t = _ray_hits(directions[candidates], tri)
        hit &= t < best_t[candidates]
        idx = candidates[hit]
        if not len(idx):
            continue
        b1, b2 = b1[hit, None], b2[hit, None]
        b0 = 1 - b1 - b2
        best_t[idx] = t[hit]
        out_uv[idx] = uvs[i0] * b0 + uvs[i1] * b1 + uvs[i2] * b2
        out_color[idx] = rgba[i0] * b0 + rgba[i1] * b1 + rgba[i2] * b2
    mask = np.isfinite(best_t)
    colour = sample_bilinear(texture, out_uv[mask, 0], out_uv[mask, 1], wrap) * out_color[mask] / 255
    return mask, colour


def nfs6_sky_to_spherical(
    meshes: List[Tuple[Sequence, Sequence, Sequence, Sequence, object]],
    clear_color: Tuple[int, int, int] = CLEAR_COLOR,
    out_file_name: Optional[str] = None,
    eye_height: float = EYE_HEIGHT,
    width: int = OUT_WIDTH,
    height: int = OUT_HEIGHT,
):
    """`meshes`: (vertices, triangles, uvs, vertex colours 0xRRGGBBAA, RGBA float texture (H, W, 4)) in the order the
    game draws them, in model space. The eye is `eye_height` above the model origin. Where no mesh is hit the screen
    keeps `clear_color`. Returns the RGBA float image"""
    import numpy as np

    directions = output_directions(width, height).reshape(-1, 3)
    out = np.zeros((directions.shape[0], 4))
    out[:, :3] = clear_color
    out[:, 3] = 255
    for vertices, triangles, uvs, colors, texture in meshes:
        mask, colour = render_mesh(directions, vertices, triangles, uvs, colors, texture, eye=(0, eye_height, 0))
        blend_over(out, colour, mask)
    out = out.reshape(height, width, 4)
    if out_file_name:
        from library.utils.sky_spherical import save_rgba

        save_rgba(out, out_file_name)
    return out


def is_nfs6_sky_archive(id: Optional[str]) -> bool:
    """`sky.fsh` of an NFS6 location's `persist.viv`"""
    import re

    return bool(id) and re.search(r'persist\.viv__children/\d+/item/data$', id, re.IGNORECASE) is not None


def serialize_nfs6_sky(items, path: str, id: str) -> List[str]:
    """`spherical.png` in the folder of the exported `sky.fsh` of a `persist.viv` (`items`: (alias, data, block) of
    its images), from `skyg.o` of the same archive. Nothing when the archive item is another FSH or has no sky model"""
    import re

    import numpy as np

    from library import require_resource
    from library.utils import path_join
    from library.utils.id import join_id
    from resources.eac.bitmaps import EacImage
    from resources.eac.geometries.nfs6 import read_eagl_meshes
    from serializers import ImageSerializer
    from serializers.geometries import _find_bigf_child

    match = re.fullmatch(r'(.*?)__children/(\d+)/item/data', id)
    (_, _, archive_data), _ = require_resource(match.group(1))
    children = (archive_data or {}).get('children', [])
    if (children[int(match.group(2))]['alias'] or '').lower() != 'sky.fsh':
        return []
    model_id = _find_bigf_child(match.group(1), 'skyg.o')
    if model_id is None:
        return []
    (_, _, model_data), _ = require_resource(model_id)
    textures = {}
    for i, (alias, data, block) in enumerate(items):
        if isinstance(block, EacImage) and alias not in textures and not isinstance(data, Exception):
            image = ImageSerializer().to_image(data, block, join_id(id, 'children', str(i), 'item', 'data'))
            textures[alias] = np.asarray(image, dtype=np.float64)
    meshes = []
    # render methods in index order, as the model's command list draws them
    for mesh in sorted(read_eagl_meshes(model_data), key=lambda m: int(m.name.rsplit('_', 1)[-1])):
        texture = textures.get(mesh.main_texture)
        if texture is None or not mesh.main_uvs:
            continue
        meshes.append((mesh.vertices, mesh.triangles, mesh.main_uvs, mesh.colors, texture))
    if not meshes:
        return []
    out_path = path_join(path, 'spherical.png')
    nfs6_sky_to_spherical(meshes, out_file_name=out_path)
    return [out_path]
