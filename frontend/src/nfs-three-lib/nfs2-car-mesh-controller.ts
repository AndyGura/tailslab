import {
  Box3,
  Camera,
  ClampToEdgeWrapping,
  FrontSide,
  Material,
  Mesh,
  MeshBasicMaterial,
  NearestFilter,
  Object3D,
  Texture,
  TextureLoader,
  Vector3,
  WebGLRenderer,
} from 'three';
import { Point3 } from '@gg-web-engine/core';
import { setupNfs1Texture } from './nfs1-model-utils';

/*
 * How NFS2 SE draws a car (nfs2sen.exe, names and comments in the Ghidra DB `decomp/nfs2/nfs2sen.exe.gzf` of
 * nfs-web): R3DCar_SetupBody 0x45a9b0 builds a body object (parts 0..11, spoiler 9 as a child) and four wheel objects
 * (wheel part + its inner part: 12+13, 14+15, 16+17, 18+19); Render_Car 0x45a510 draws them with Transfmr_DrawObject
 * 0x461e50. There is no depth sorting inside a car: every part goes into one of 32 layers (a per-model layout table,
 * g_car_part_layouts 0x4c7a70), the layers are drawn in increasing order, the polygons of a part in file order, back
 * faces culled. Some parts are skipped from some view angles (the camera's yaw and pitch in the car's frame). The car
 * as a whole is depth sorted against the scene.
 * Here: the car's meshes are drawn after the opaque scene (the GLB root's group render order), in layer order
 * (`renderOrder`), depth tested against what is drawn but without writing depth, so later layers paint over earlier
 * ones as in the game; then every mesh again, depth only, so later objects and other cars hide behind it. Within a
 * part the order is the GLB's (one mesh per texture), not the polygons' file order.
 */

/** nfs2sen g_model_names 0x4c5fe0: index = the game's car type */
// prettier-ignore
export const NFS2_MODEL_NAMES = [
  'MCF1', 'FF50', 'F355', 'GT90', 'IDGO', 'MACH', 'JAGR', 'LGT1', 'ESPR', 'NAZC', 'CALA', 'ISDE', 'CHEV', 'DAYT', 'FUTR',
  'CITR', 'OPP', 'TRAF', 'CITR', 'COMC', 'SBUS', 'SEMI', 'VANA', 'QUAT', 'VOLW', 'YJ', 'MERC', 'VWFB', 'MIAT', 'BUG',
  'LAND', 'ARMY', 'BMW5', 'SNOW', 'MONO', 'LIMO', 'MIAT', 'SBUS', 'SBUS', 'SBUS', 'CRAT', 'CART', 'OUTH', 'TREX',
];
const MODEL_IDGO = 4;
const MODEL_MACH = 5;
// race cars: car types below 0xf (R3DCar_LoadGeo "Fixing Wheels")
const RACE_CAR_MODELS = 0xf;

/** R3DCar_LayoutOfModel 0x45b7f8: the car type's layout in NFS2_CAR_PART_LAYOUTS */
const layoutOfModel = (model: number): number => {
  switch (model) {
    case 1:
    case 9:
    case 0xd:
      return 4;
    case 4:
      return 1;
    case 5:
      return 2;
    case 0xb:
    case 0xe:
      return 5;
    case 0xc:
      return 3;
    default:
      return 0;
  }
};

/**
 * Per part: draw layer, then the view limits r0, r1 (yaw) and r2, r3 (pitch): the part is skipped when r0 < yaw < r1
 * and r2 < pitch < r3 (empty ranges: always drawn); r0 SPOILER_VIEW_RULE: see partVisible
 */
type Nfs2PartRenderInfo = [number, number, number, number, number];
const SPOILER_VIEW_RULE = 0x20000;

// g_car_part_layouts 0x4c7a70 (6 layouts x 26 parts, 0x18 bytes each: +4 layer, +8..+0x14 view limits)
// prettier-ignore
const NFS2_CAR_PART_LAYOUTS: Nfs2PartRenderInfo[][] = [
  [
    [5, 0x1, 0x0, 0x1, 0x0],
    [14, -0x7e00, 0x7e00, 0x4600, 0x3c00],
    [6, -0x7e00, 0x7e00, -0x100, -0x7d00],
    [11, -0x3600, 0x3600, -0x7e00, 0x7e00],
    [12, 0x4000, 0x7e00, -0x7e00, 0x7e00],
    [7, -0x400, 0x6e00, -0x7e00, 0x7e00],
    [8, -0x6e00, 0x400, -0x7e00, 0x7e00],
    [9, 0x1, 0x0, 0x1, 0x0],
    [10, 0x1, 0x0, 0x1, 0x0],
    [16, 0x20000, 0x7e00, 0x100, 0x7e00],
    [15, 0x1, 0x0, 0x1, 0x0],
    [13, 0x1, 0x0, 0x1, 0x0],
    [17, -0x800, 0x7e00, -0x7e00, 0x7e00],
    [1, -0x800, 0x6400, -0x7e00, -0xa00],
    [18, -0x7e00, 0x800, -0x7e00, 0x7e00],
    [2, -0x6400, 0x800, -0x7e00, -0xa00],
    [19, -0x800, 0x7e00, -0x7e00, 0x7e00],
    [3, -0x800, 0x7e00, -0x7e00, -0xa00],
    [20, -0x7e00, 0x800, -0x7e00, 0x7e00],
    [4, -0x7e00, 0x800, -0x7e00, -0xa00],
    [2, 0x1, 0x0, 0x1, 0x0],
    [4, 0x1, 0x0, 0x1, 0x0],
    [3, -0x7e00, 0x7e00, -0x100, -0x7d00],
    [1, 0x1, 0x0, 0x1, 0x0],
    [2, 0x1, 0x0, 0x1, 0x0],
    [1, 0x1, 0x0, 0x1, 0x0],
  ],
  [
    [5, 0x1, 0x0, 0x1, 0x0],
    [14, -0x7e00, 0x7e00, 0x4600, 0x3c00],
    [26, -0x7e00, 0x7e00, -0x100, -0x7d00],
    [11, -0x3600, 0x3600, -0x7e00, 0x7e00],
    [12, 0x4000, 0x7e00, -0x7e00, 0x7e00],
    [7, -0x500, 0x6400, -0x7e00, 0x7e00],
    [8, -0x6400, 0x500, -0x7e00, 0x7e00],
    [9, 0x1, 0x0, 0x1, 0x0],
    [10, 0x1, 0x0, 0x1, 0x0],
    [25, -0x7e00, 0x7e00, 0x100, 0x7d00],
    [6, -0x7e00, 0x7e00, 0xa00, 0x7e00],
    [13, 0x1, 0x0, 0x1, 0x0],
    [21, -0x300, 0x7e00, -0x7e00, 0x7e00],
    [1, 0x1, 0x0, -0x7e00, -0xa00],
    [22, -0x7e00, 0x300, -0x7e00, 0x7e00],
    [2, 0x2, 0x0, -0x7e00, -0xa00],
    [23, -0x800, 0x7e00, -0x7e00, 0x7e00],
    [3, 0x3, 0x0, -0x7e00, -0xa00],
    [24, -0x7e00, 0x800, -0x7e00, 0x7e00],
    [4, 0x4, 0x0, -0x7e00, -0xa00],
    [2, 0x1, 0x0, 0x1, 0x0],
    [3, 0x1, 0x0, 0x1, 0x0],
    [4, -0x7e00, 0x7e00, -0x100, -0x7d00],
    [1, 0x1, 0x0, 0x1, 0x0],
    [2, 0x1, 0x0, 0x1, 0x0],
    [1, 0x1, 0x0, 0x1, 0x0],
  ],
  [
    [5, 0x1, 0x0, 0x1, 0x0],
    [9, -0x7e00, 0x7e00, 0x4600, 0x3c00],
    [26, -0x7e00, 0x7e00, -0x100, -0x7d00],
    [6, 0x1, 0x0, 0x1, 0x0],
    [10, 0x1, 0x0, 0x1, 0x0],
    [11, 0x1, 0x0, 0x1, 0x0],
    [12, 0x1, 0x0, 0x1, 0x0],
    [13, 0x1, 0x0, 0x1, 0x0],
    [14, 0x1, 0x0, 0x1, 0x0],
    [7, -0x7e00, 0x7e00, 0x100, 0x7e00],
    [8, -0x7e00, 0x7e00, 0xa00, 0x7e00],
    [25, 0x1, 0x0, 0x1, 0x0],
    [21, -0x300, 0x7e00, -0x7e00, 0x7e00],
    [1, 0x1, 0x0, -0x7e00, -0xa00],
    [22, -0x7e00, 0x300, -0x7e00, 0x7e00],
    [2, 0x2, 0x0, -0x7e00, -0xa00],
    [23, -0x800, 0x7e00, -0x7e00, 0x7e00],
    [3, 0x3, 0x0, -0x7e00, -0xa00],
    [24, -0x7e00, 0x800, -0x7e00, 0x7e00],
    [4, 0x4, 0x0, -0x7e00, -0xa00],
    [2, 0x1, 0x0, 0x1, 0x0],
    [3, 0x1, 0x0, 0x1, 0x0],
    [4, -0x7e00, 0x7e00, -0x100, -0x7d00],
    [1, 0x1, 0x0, 0x1, 0x0],
    [2, 0x1, 0x0, 0x1, 0x0],
    [1, 0x1, 0x0, 0x1, 0x0],
  ],
  [
    [5, 0x1, 0x0, 0x1, 0x0],
    [14, -0x7e00, 0x7e00, 0x4600, 0x3c00],
    [26, -0x7e00, 0x7e00, -0x100, -0x7d00],
    [11, -0x3600, 0x3600, -0x7e00, 0x7e00],
    [12, 0x4000, 0x7e00, -0x7e00, 0x7e00],
    [7, -0x500, 0x6400, -0x7e00, 0x7e00],
    [8, -0x6400, 0x500, -0x7e00, 0x7e00],
    [9, 0x1, 0x0, 0x1, 0x0],
    [10, 0x1, 0x0, 0x1, 0x0],
    [25, -0x2000, 0x2000, -0x4000, 0x4000],
    [6, -0x7e00, 0x7e00, 0xa00, 0x7e00],
    [13, 0x1, 0x0, 0x1, 0x0],
    [21, -0x300, 0x7e00, -0x7e00, 0x7e00],
    [1, 0x1, 0x0, -0x7e00, -0xa00],
    [22, -0x7e00, 0x300, -0x7e00, 0x7e00],
    [2, 0x2, 0x0, -0x7e00, -0xa00],
    [23, -0x800, 0x7e00, -0x7e00, 0x7e00],
    [3, 0x3, 0x0, -0x7e00, -0xa00],
    [24, -0x7e00, 0x800, -0x7e00, 0x7e00],
    [4, 0x4, 0x0, -0x7e00, -0xa00],
    [2, 0x1, 0x0, 0x1, 0x0],
    [3, 0x1, 0x0, 0x1, 0x0],
    [4, -0x7e00, 0x7e00, -0x100, -0x7d00],
    [1, 0x1, 0x0, 0x1, 0x0],
    [2, 0x1, 0x0, 0x1, 0x0],
    [1, 0x1, 0x0, 0x1, 0x0],
  ],
  [
    [5, 0x1, 0x0, 0x1, 0x0],
    [14, -0x7e00, 0x7e00, 0x4600, 0x3c00],
    [6, -0x7e00, 0x7e00, -0x100, -0x7d00],
    [11, -0x3600, 0x3600, -0x7e00, 0x7e00],
    [12, 0x4000, 0x7e00, -0x7e00, 0x7e00],
    [7, -0x400, 0x6e00, -0x7e00, 0x7e00],
    [8, -0x6e00, 0x400, -0x7e00, 0x7e00],
    [9, 0x1, 0x0, 0x1, 0x0],
    [10, 0x1, 0x0, 0x1, 0x0],
    [16, 0x20000, 0x7e00, 0x100, 0x7e00],
    [15, 0x1, 0x0, 0x1, 0x0],
    [13, 0x1, 0x0, 0x1, 0x0],
    [17, -0x800, 0x7e00, -0x7e00, 0x7e00],
    [1, -0x800, 0x6400, -0x7e00, -0xa00],
    [18, -0x7e00, 0x800, -0x7e00, 0x7e00],
    [2, -0x6400, 0x800, -0x7e00, -0xa00],
    [19, -0x800, 0x7e00, -0x7e00, 0x7e00],
    [3, -0x800, 0x7e00, -0x7e00, -0xa00],
    [20, -0x7e00, 0x800, -0x7e00, 0x7e00],
    [4, -0x7e00, 0x800, -0x7e00, -0xa00],
    [2, 0x1, 0x0, 0x1, 0x0],
    [4, 0x1, 0x0, 0x1, 0x0],
    [3, -0x7e00, 0x7e00, -0x100, -0x7d00],
    [1, 0x1, 0x0, 0x1, 0x0],
    [2, 0x1, 0x0, 0x1, 0x0],
    [1, 0x1, 0x0, 0x1, 0x0],
  ],
  [
    [5, 0x1, 0x0, 0x1, 0x0],
    [14, -0x7e00, 0x7e00, 0x4600, 0x3c00],
    [6, -0x7e00, 0x7e00, -0x100, -0x7d00],
    [11, -0x3600, 0x3600, -0x7e00, 0x7e00],
    [12, 0x4000, 0x7e00, -0x7e00, 0x7e00],
    [7, -0x400, 0x6e00, -0x7e00, 0x7e00],
    [8, -0x6e00, 0x400, -0x7e00, 0x7e00],
    [9, 0x1, 0x0, 0x1, 0x0],
    [10, 0x1, 0x0, 0x1, 0x0],
    [16, 0x20000, 0x7e00, 0x100, 0x7e00],
    [15, 0x1, 0x0, 0x1, 0x0],
    [13, 0x1, 0x0, 0x1, 0x0],
    [17, -0x800, 0x7e00, -0x7e00, 0x7e00],
    [1, -0x800, 0x6400, -0x7e00, -0xa00],
    [18, -0x7e00, 0x800, -0x7e00, 0x7e00],
    [2, -0x6400, 0x800, -0x7e00, -0xa00],
    [19, -0x800, 0x7e00, -0x7e00, 0x7e00],
    [3, -0x800, 0x7e00, -0x7e00, -0xa00],
    [20, -0x7e00, 0x800, -0x7e00, 0x7e00],
    [4, -0x7e00, 0x800, -0x7e00, -0xa00],
    [2, 0x1, 0x0, 0x1, 0x0],
    [4, 0x1, 0x0, 0x1, 0x0],
    [3, -0x7e00, 0x7e00, -0x100, -0x7d00],
    [1, 0x1, 0x0, 0x1, 0x0],
    [2, 0x1, 0x0, 0x1, 0x0],
    [1, 0x1, 0x0, 0x1, 0x0],
  ],
];

/** nfs2sen g_car_hsvt 0x4c5820: per car color h, s, v (0..255) and the shade knee (Color_RecolorEntry) */
// prettier-ignore
export const NFS2_CAR_HSVT: readonly (readonly [number, number, number, number])[] = [
  [0, 0, 210, 80], [0, 0, 60, 110], [254, 215, 249, 96], [253, 219, 133, 100],
  [249, 179, 101, 81], [28, 253, 209, 58], [13, 225, 249, 89], [42, 151, 89, 92],
  [89, 175, 63, 105], [150, 255, 230, 106], [169, 165, 177, 117], [211, 205, 132, 79],
  [127, 207, 100, 100], [25, 196, 200, 73], [0, 0, 120, 86], [248, 197, 210, 95],
  [120, 163, 211, 102], [163, 86, 211, 102], [26, 89, 250, 94], [43, 211, 239, 102],
  [15, 204, 244, 159], [26, 218, 255, 123], [53, 167, 176, 145], [246, 112, 247, 105],
  [228, 255, 125, 143], [88, 223, 101, 231], [8, 24, 48, 152], [136, 24, 240, 136],
  [249, 240, 135, 128], [32, 24, 255, 48], [253, 241, 248, 88], [26, 254, 255, 58],
  [142, 229, 55, 74], [160, 32, 37, 148], [20, 16, 255, 52], [128, 8, 224, 112],
  [254, 248, 176, 96], [163, 240, 129, 97], [40, 248, 238, 73], [206, 248, 46, 72],
  [70, 8, 255, 73], [78, 8, 31, 177], [253, 223, 165, 127], [170, 194, 70, 80],
  [5, 248, 198, 48], [254, 248, 216, 104], [31, 245, 255, 49], [109, 223, 165, 127],
  [45, 16, 86, 56], [162, 224, 55, 97], [70, 8, 255, 73], [8, 24, 48, 152],
  [254, 255, 224, 104], [26, 254, 255, 58], [176, 225, 136, 112], [70, 8, 255, 73],
  [0, 255, 208, 88], [88, 175, 45, 127], [163, 208, 97, 97], [45, 0, 254, 104],
  [8, 24, 48, 152], [26, 254, 255, 58], [142, 229, 55, 74], [128, 9, 224, 64],
  [0, 0, 200, 128], [252, 240, 135, 120], [45, 0, 254, 104], [254, 248, 216, 104],
  [136, 24, 240, 136], [8, 24, 16, 128], [26, 254, 255, 58], [163, 240, 129, 97],
  [157, 74, 250, 110], [78, 8, 31, 177], [163, 208, 97, 97], [254, 248, 176, 96],
  [131, 230, 27, 56], [26, 254, 255, 58], [2, 255, 176, 120], [206, 248, 54, 104],
  [107, 176, 30, 128], [128, 8, 255, 104], [254, 248, 216, 104], [26, 254, 255, 58],
  [45, 0, 14, 80], [163, 208, 97, 97], [45, 0, 254, 86], [254, 248, 216, 104],
];

/** Race car colors: the first 24 of NFS2_CAR_HSVT, the entries of CARMODEL/PC/CARHSVT.TXT */
export const NFS2_RACE_CAR_COLORS = 24;

// the exe's rounding fixed-point multiply, for non-negative operands
const fixmul = (a: number, b: number): number => Math.floor((a * b + 0x8000) / 0x10000);

/**
 * nfs2sen Color_HsvToRgb 0x446608: h 0..255, s and v 0..256 -> r, g, b 0..256 (integer math as in the exe)
 */
export function nfs2HsvToRgb(h: number, s: number, v: number): [number, number, number] {
  let rgb: [number, number, number];
  if (v < 1) {
    rgb = [0, 0, 0];
  } else if (s < 1) {
    rgb = [v, v, v];
  } else {
    const sector = (h * 6) >> 8;
    const f = (h * 6 - sector * 256) << 8;
    const p = ((0x100 - s) * v) >> 8;
    const q = ((0x100 - fixmul(s, f)) * v) >> 8;
    const t = ((0x100 - fixmul(s, 0x10000 - f)) * v) >> 8;
    rgb = [
      [v, t, p],
      [q, v, p],
      [p, v, t],
      [p, q, v],
      [t, p, v],
      [v, p, q],
    ][sector] as [number, number, number];
  }
  return rgb.map(c => Math.max(0, Math.min(0x100, c))) as [number, number, number];
}

/**
 * A car paint as the game applies it: the paint color (0..256 per channel) and the shade where the texture shows it
 * exactly (`mid`, the 4th value of an HSVT entry)
 */
export interface Nfs2CarPaint {
  color: readonly [number, number, number];
  mid: number;
}

/** The game's car color `index` (NFS2_CAR_HSVT; race cars 0..23) */
export const nfs2PaintOfHsvt = (index: number): Nfs2CarPaint => {
  const [h, s, v, mid] = NFS2_CAR_HSVT[index];
  return { color: nfs2HsvToRgb(h, s, v), mid };
};

/** nfs-web: the shade knee for colors not from the game's table, the median of the race car colors' */
export const NFS2_RGB_PAINT_MID = 100;

/** nfs-web: a 0xRRGGBB color painted the game's way (NFS2_RGB_PAINT_MID) */
export const nfs2PaintOfRgb = (rgb: number, mid = NFS2_RGB_PAINT_MID): Nfs2CarPaint => ({
  color: [rgb >> 16, (rgb >> 8) & 0xff, rgb & 0xff],
  mid,
});

/**
 * nfs2sen Color_RecolorPalette 0x446a90 + Color_RecolorEntry 0x446b40: the new value of a palette color (0..255 per
 * channel), null when the game leaves it (only the green paint ramp: r < 0x56, g >= 0x80, b < 0x56). The car's QFS
 * textures are 8-bit with one palette (`0000`), which the game recolors: the PNG's pixels are the palette's colors,
 * so recoloring them by value is the same. The shader of the controller does the same per texel.
 */
export function nfs2RecolorPaletteEntry(
  r: number,
  g: number,
  b: number,
  paint: Nfs2CarPaint,
): [number, number, number] | null {
  if (r >= 0x56 || g < 0x80 || b >= 0x56) {
    return null;
  }
  const { color, mid } = paint;
  const shade = g - 0x80;
  const d = shade - mid;
  const out = color.map(c =>
    d <= 0 ? Math.trunc((c * shade) / mid) : Math.trunc(((Math.min(c * 4, 0xff) - c) * d) / (0x7f - mid)) + c,
  );
  if (r > 0 && b > 0) {
    out[0] = Math.min(out[0] + ((r * 3) >> 1), 0xff);
    out[1] = Math.min(out[1] + (shade >> 1), 0xff);
    out[2] = Math.min(out[2] + ((b * 3) >> 1), 0xff);
  }
  return out as [number, number, number];
}

class PaintUniforms {
  readonly color = { value: new Vector3() };
  readonly mid = { value: 1 };
  readonly enabled = { value: 0 };

  set(paint: Nfs2CarPaint | null) {
    this.enabled.value = paint ? 1 : 0;
    if (paint) {
      this.color.value.set(...paint.color);
      this.mid.value = paint.mid;
    }
  }
}

/**
 * The material paints its texels as nfs2RecolorPaletteEntry (in the fragment shader: reading a canvas back gets noise
 * from anti-fingerprinting). Each texel is painted before filtering, as the game paints its palette: with a nearest
 * filter the sample is the texel, a linearly filtered map (TailsLab's OBJ viewer) is sampled texel by texel (painting
 * the filtered colour left green fringes where paint meets other colours). The sRGB value is read back to 0..255;
 * integer divisions as floor(a / b + 0.5 / b): exact for the integer operands here
 */
function paintInShader(material: Material, uniforms: PaintUniforms) {
  const previous = material.onBeforeCompile;
  const previousKey = material.customProgramCacheKey;
  material.onBeforeCompile = (shader, renderer) => {
    previous.call(material, shader, renderer);
    shader.uniforms['nfs2PaintColor'] = uniforms.color;
    shader.uniforms['nfs2PaintMid'] = uniforms.mid;
    shader.uniforms['nfs2PaintEnabled'] = uniforms.enabled;
    // read when drawn: the map (texture frames) can change
    shader.uniforms['nfs2PaintFiltered'] = {
      get value() {
        const map = (material as MeshBasicMaterial).map;
        return map && map.magFilter !== NearestFilter ? 1 : 0;
      },
    };
    shader.fragmentShader = shader.fragmentShader
      .replace(
        '#include <map_pars_fragment>',
        `#include <map_pars_fragment>
        uniform vec3 nfs2PaintColor;
        uniform float nfs2PaintMid;
        uniform float nfs2PaintEnabled;
        uniform float nfs2PaintFiltered;
        vec3 nfs2Div( vec3 a, float b ) { return floor( a / b + 0.5 / b ); }
        vec4 nfs2Paint( vec4 sampled ) {
          vec3 texel = floor( sRGBTransferOETF( sampled ).rgb * 255.0 + 0.5 );
          if ( texel.r >= 86.0 || texel.g < 128.0 || texel.b >= 86.0 ) {
            return sampled;
          }
          float shade = texel.g - 128.0;
          vec3 painted = shade <= nfs2PaintMid
            ? nfs2Div( nfs2PaintColor * shade, nfs2PaintMid )
            : nfs2Div( ( min( nfs2PaintColor * 4.0, 255.0 ) - nfs2PaintColor ) * ( shade - nfs2PaintMid ),
                127.0 - nfs2PaintMid ) + nfs2PaintColor;
          if ( texel.r > 0.0 && texel.b > 0.0 ) {
            painted = min( painted + floor( vec3( texel.r * 3.0, shade, texel.b * 3.0 ) / 2.0 ), 255.0 );
          }
          return vec4( sRGBTransferEOTF( vec4( painted / 255.0, 1.0 ) ).rgb, sampled.a );
        }`,
      )
      .replace(
        '#include <map_fragment>',
        `#include <map_fragment>
        #ifdef USE_MAP
        if ( nfs2PaintEnabled > 0.5 ) {
          vec4 painted;
          if ( nfs2PaintFiltered > 0.5 ) {
            // the game paints texels (palette colors) before any filtering: the 4 texels of a bilinear sample painted,
            // then blended (base level only: a mipmapped minification aliases instead of fringing green)
            ivec2 size = textureSize( map, 0 );
            vec2 p = vMapUv * vec2( size ) - 0.5;
            ivec2 i0 = ivec2( floor( p ) );
            vec2 f = p - floor( p );
            ivec2 last = size - 1;
            vec4 t00 = nfs2Paint( texelFetch( map, clamp( i0, ivec2( 0 ), last ), 0 ) );
            vec4 t10 = nfs2Paint( texelFetch( map, clamp( i0 + ivec2( 1, 0 ), ivec2( 0 ), last ), 0 ) );
            vec4 t01 = nfs2Paint( texelFetch( map, clamp( i0 + ivec2( 0, 1 ), ivec2( 0 ), last ), 0 ) );
            vec4 t11 = nfs2Paint( texelFetch( map, clamp( i0 + ivec2( 1, 1 ), ivec2( 0 ), last ), 0 ) );
            painted = mix( mix( t00, t10, f.x ), mix( t01, t11, f.x ), f.y );
          } else {
            // nearest: the sample is the texel
            painted = nfs2Paint( sampledDiffuseColor );
          }
          diffuseColor = vec4( diffuse, opacity ) * painted;
        }
        #endif`,
      );
  };
  material.customProgramCacheKey = () => `${previousKey.call(material)}|nfs2-paint`;
  material.needsUpdate = true;
}

/**
 * The exe's car fields the drawing reads (nfs2-physics.c `get_car_render`), raw values. Cars of other physics fill
 * them with nfs2DrawStateOf.
 */
export interface Nfs2CarDrawState {
  /** car+0x2e4 ramped steering, -128..127, positive to the right */
  steer: number;
  /** car+0x2b8 speed along the road's forward axis, 16.16 m/s */
  forwardSpeed: number;
  /** car+0x2f4 wheelspin / slide state: not 0 blurs the rear tyres */
  wheelspin: number;
  /** car+0x2f8 front wheelspin (sim model): not 0 blurs the front tyres */
  frontWheelspin: number;
  /** car+0x2fc locked wheels: bit 1 front, bit 2 rear (standing tyres) */
  lockedWheels: number;
  /** car+0x280: 2 when the race is finished */
  raceState: number;
  /** car+0xbc horizontal speed, 16.16 m/s */
  horizontalSpeed: number;
  /** car+0x2d8 ramped brake 0..255: brake lights on when not 0 */
  brake: number;
  /**
   * car+0x15c height above ground (16.16 m): with it, update moves the wheels (R3DCar_WheelBounce); without, the
   * caller places them (`placeWheel`, `wheelIdlePositions`)
   */
  heightAboveGround?: number;
  /** car+0x67c, car+0x680: wheel vibration of the crash code (not ported: 0) */
  vibration?: number;
  vibrationSpeed?: number;
}

/** A draw state for a car of other physics: speed m/s (negative reversing), steering -1..1 (positive right), braking */
export const nfs2DrawStateOf = (speed: number, steering: number, braking: boolean): Nfs2CarDrawState => ({
  steer: Math.round(Math.max(-1, Math.min(1, steering)) * 127),
  forwardSpeed: Math.round(speed * 0x10000),
  wheelspin: 0,
  frontWheelspin: 0,
  lockedWheels: 0,
  raceState: 0,
  horizontalSpeed: Math.round(Math.abs(speed) * 0x10000),
  brake: braking ? 0xff : 0,
});

// the sim's tick rate: the frame counter and the wheel bounce change at most once per tick
const SIM_TICK_MS = 1000 / 64;
// the GLB root's render group order, + one per car: each car is drawn as a whole after the opaque scene
const CAR_GROUP_ORDER = 1000;
let nextCarGroupOrder = CAR_GROUP_ORDER;
// render order of a mesh: layer * LAYER_ORDER + its place in the GLB; the depth pass after every layer
const LAYER_ORDER = 1000;
const DEPTH_PASS_ORDER = 100 * LAYER_ORDER;
// Fixing Wheels (R3DCar_LoadGeo 0x45b860): the tyre quad 5/256 m outward
const WHEEL_FIX_OFFSET = 5 / 256;
// R3DCar_FrontWheelCallback 0x45baa0: steering angle factor limit
const MAX_STEER_FACTOR = 0x2a;

type AnimationGroup = 'front' | 'rear' | 'brake';

interface PartMesh {
  mesh: Mesh;
  part: number;
  // place in the GLB (render order inside a layer)
  index: number;
  depthMesh: Mesh;
  wheel: WheelObject | null;
}

/**
 * A wheel object of the exe: its meshes (wheel part and inner part) have their geometry relative to the pivot and are
 * moved and turned together (each its own transform: they stay where they are in the model, the TailsLab viewer
 * lists and hides the model's children)
 */
interface WheelObject {
  meshes: Mesh[];
  front: boolean;
  // the view the steering was set for
  viewKey: string;
}

interface AnimatedMaterial {
  material: MeshBasicMaterial;
  depthMaterial: MeshBasicMaterial;
  // texture of every frame, frame 0 the GLB's own
  frames: Texture[];
}

/** The GEO part of a mesh: TailsLab's extras, else its name (part_hp_<i>, part_mp_<i>, part_lp_<i>, part_res_<i>) */
function partOf(mesh: Mesh): number | null {
  const part = mesh.userData?.['geo_part'];
  if (typeof part === 'number') {
    return part;
  }
  const match = /^part_(hp|mp|lp|res)_(\d+)/.exec(mesh.name);
  if (!match) {
    return null;
  }
  return +match[2] + { hp: 0, mp: 20, lp: 23, res: 26 }[match[1] as 'hp' | 'mp' | 'lp' | 'res'];
}

/** Texture name of a material ("<texture>" as TailsLab names textures and materials) */
const textureNameOf = (material: Material): string | null =>
  ((material as MeshBasicMaterial).map?.name || material.name || '').trim() || null;

/** Texture of animation frame `frame` (CarIO_SetupTextures 0x463900): the name's 2nd character + frame */
const frameTextureName = (name: string, frame: number): string =>
  name[0] + String.fromCharCode(name.charCodeAt(1) + frame) + name.substring(2);

/**
 * Draws an NFS2 SE car model (TailsLab GEO -> GLB, meshes `part_<lod>_<part>__<texture>`, node extras `geo_part`,
 * `frames`, `color_keyed`, `geo_part_pos` since 2026-10-28) the way nfs2sen.exe does (see above): paint (palette
 * recolor), draw layers and view-angle part culling, tyre and brake light texture frames, front wheels steered by the
 * view angle, wheel bounce, the game's wheel fix. Models converted before the extras: tyres animated (4 frames, every
 * NFS2 SE car has them), brake lights not, wheels turn about their quad's centre.
 * Not done (see nfs-web's src/nfs2/nfs2-physics/CLAUDE.md, "Car drawing"): body roll / pitch of the crash code, the
 * ground shadow, the track's light (tunnels), level of detail, traffic colors.
 */
export class Nfs2CarMeshController {
  /** car type (NFS2_MODEL_NAMES index), -1 when unknown */
  readonly model: number;
  private readonly layout: number;
  private readonly parts: PartMesh[] = [];
  private readonly paintUniforms = new PaintUniforms();
  private readonly animations = new Map<AnimationGroup, { frame: number; materials: AnimatedMaterial[] }>();
  private readonly ownMaterials: Material[] = [];
  private readonly ownTextures: Texture[] = [];
  // the car's centre (bounding box of its parts), where the exe measures the view angles from
  private readonly centre = new Vector3();
  // the view of the last render: yaw and pitch of (car - camera) in the car's frame, 0x10000 per turn
  private viewKey = '';
  private viewYaw = 0;
  private viewPitch = 0;
  private layerKey = '';
  private readonly cameraPosition = new Vector3();

  private state: Nfs2CarDrawState = nfs2DrawStateOf(0, 0, false);
  // R3DCar_BodyCallback's frame counter (car+0x648) and the last sim tick seen
  private frameCounter = 0;
  private lastTick: number | null = null;

  // wheel pivots, order: front right, front left, rear right, rear left (parts 12, 14, 16, 18 with 13, 15, 17, 19)
  public wheelIdlePositions: Point3[] = [];
  private readonly wheelObjects: WheelObject[] = [];

  get hasWheels(): boolean {
    return this.wheelObjects.length > 0;
  }

  /** Puts wheel `index` (see wheelIdlePositions) with its pivot at `position` (the model's frame) */
  placeWheel(index: number, position: Point3) {
    for (const m of this.wheelObjects[index]?.meshes ?? []) {
      m.position.set(position.x, position.y, position.z);
    }
  }

  private _paint: Nfs2CarPaint | null = null;
  /** The paint (null: the texture as it is, green) */
  get paint(): Nfs2CarPaint | null {
    return this._paint;
  }

  set paint(value: Nfs2CarPaint | null) {
    this._paint = value;
    this.paintUniforms.set(value);
  }

  private _color: number | null = null;
  /** nfs-web: paint by a 0xRRGGBB color (nfs2PaintOfRgb) */
  get color(): number | null {
    return this._color;
  }

  set color(value: number) {
    this._color = value;
    this.paint = nfs2PaintOfRgb(value);
  }

  /** Paint by the game's color index (NFS2_CAR_HSVT) */
  set colorIndex(value: number) {
    this._color = null;
    this.paint = nfs2PaintOfHsvt(value);
  }

  constructor(
    private readonly mesh: Object3D,
    assetsPath: string,
    /**
     * model: the GEO's name (CALA ...), default from the assets path (".../<model>.geo/assets"); frames: animation
     * frames of a part's polygons with this texture, for models without TailsLab's extras (the OBJ export: TailsLab
     * reads them from the parsed GEO)
     */
    options: { model?: string; frames?: (part: number, texture: string) => number } = {},
  ) {
    const modelName = (options.model ?? /([^/]+)\.geo(?:\/|$)/i.exec(assetsPath)?.[1] ?? '').toUpperCase();
    this.model = NFS2_MODEL_NAMES.indexOf(modelName);
    this.layout = layoutOfModel(this.model);
    // each car its own group order: drawn as a whole, after the opaque scene
    mesh.renderOrder = nextCarGroupOrder++;
    if (!(mesh as any).isGroup) {
      console.warn('Nfs2CarMeshController: the model root is not a Group, its draw order is not kept');
    }

    const meshes: { mesh: Mesh; part: number }[] = [];
    mesh.traverse(o => {
      if (o instanceof Mesh) {
        const part = partOf(o);
        if (part !== null && part < 26) {
          meshes.push({ mesh: o, part });
        }
      }
    });
    const box = new Box3();
    for (const { mesh: m } of meshes) {
      m.geometry.computeBoundingBox();
      box.union(m.geometry.boundingBox!);
    }
    box.getCenter(this.centre);

    this.setUpWheels(meshes);
    this.setUpAnimations(meshes, assetsPath, options.frames);

    // materials: painted, back faces culled, depth tested without writing depth; a depth-only twin for the depth pass
    const depthMaterials = new Map<Material, MeshBasicMaterial>();
    for (const [index, { mesh: m, part }] of meshes.entries()) {
      const material = m.material as Material;
      let depthMaterial = depthMaterials.get(material);
      if (!depthMaterial) {
        paintInShader(material, this.paintUniforms);
        material.side = FrontSide;
        // drawn opaque: texels with alpha are cut out (the GLB's materials have alphaTest already)
        if (material.transparent && material.alphaTest === 0) {
          material.alphaTest = 0.5;
        }
        material.transparent = false;
        material.depthTest = true;
        material.depthWrite = false;
        depthMaterial = new MeshBasicMaterial({
          map: (material as MeshBasicMaterial).map,
          alphaTest: material.alphaTest,
          side: FrontSide,
          colorWrite: false,
        });
        depthMaterials.set(material, depthMaterial);
        this.ownMaterials.push(depthMaterial);
      }
      for (const animation of this.animations.values()) {
        for (const animated of animation.materials) {
          if (animated.material === material) {
            animated.depthMaterial = depthMaterial;
          }
        }
      }
      const depthMesh = new Mesh(m.geometry, depthMaterial);
      depthMesh.name = `${m.name}__depth`;
      depthMesh.renderOrder = DEPTH_PASS_ORDER + index;
      m.add(depthMesh);
      const entry: PartMesh = {
        mesh: m,
        part,
        index,
        depthMesh,
        wheel: this.wheelObjects.find(w => w.meshes.includes(m)) ?? null,
      };
      this.parts.push(entry);
      const beforeRender = (renderer: WebGLRenderer, camera: Camera) => this.beforeRender(entry, renderer, camera);
      m.onBeforeRender = (renderer, _scene, camera) => beforeRender(renderer, camera);
      depthMesh.onBeforeRender = (renderer, _scene, camera) => beforeRender(renderer, camera);
    }
    this.updateLayers();
  }

  /**
   * Wheel objects (R3DCar_AddWheel 0x45b700): wheel part and inner part turn and move together about the inner part's
   * position (the last mesh added sets the object's position, Transfmr_AddMesh 0x4622b0), so a tyre quad whose part
   * position differs is drawn shifted by the difference (IDGO, MCF1: 1-2 cm). Fixing Wheels (R3DCar_LoadGeo): the
   * tyre quads of IDGO's front wheels and of every race car's rear wheels (their first polygon has flag 2: all of
   * them) 5/256 m outward.
   */
  private setUpWheels(meshes: { mesh: Mesh; part: number }[]) {
    // a model without the four wheel parts (no wheels): none
    if (![12, 14, 16, 18].every(wheelPart => meshes.some(m => m.part === wheelPart))) {
      return;
    }
    for (const [i, wheelPart] of [12, 14, 16, 18].entries()) {
      const wheelMeshes = meshes.filter(m => m.part === wheelPart).map(m => m.mesh);
      const innerMeshes = meshes.filter(m => m.part === wheelPart + 1).map(m => m.mesh);
      const partPos = (m: Mesh | undefined): Vector3 | null => {
        const pos = m?.userData?.['geo_part_pos'];
        return Array.isArray(pos) ? new Vector3(pos[0], pos[1], pos[2]) : null;
      };
      const wheelPos = partPos(wheelMeshes[0]);
      const innerPos = partPos(innerMeshes[0]) ?? wheelPos;
      const fixed = (i < 2 && this.model === MODEL_IDGO) || (i >= 2 && this.model >= 0 && this.model < RACE_CAR_MODELS);
      for (const m of wheelMeshes) {
        const box = new Box3().setFromBufferAttribute(m.geometry.getAttribute('position') as any);
        const outward = Math.sign(box.min.x + box.max.x) || 1;
        const shift = new Vector3(fixed ? outward * WHEEL_FIX_OFFSET : 0, 0, 0);
        if (wheelPos && innerPos) {
          shift.add(innerPos).sub(wheelPos);
        }
        m.geometry.translate(shift.x, shift.y, shift.z);
      }
      // pivot: the inner part's position, else (models converted before the extras) the tyre quad's centre
      let pivotPos = innerPos;
      if (!pivotPos) {
        const box = new Box3();
        for (const m of wheelMeshes) {
          m.geometry.computeBoundingBox();
          box.union(m.geometry.boundingBox!);
        }
        pivotPos = box.getCenter(new Vector3());
      }
      const wheelObjectMeshes = [...wheelMeshes, ...innerMeshes];
      for (const m of wheelObjectMeshes) {
        // the GLB's meshes have no transform of their own
        m.geometry.translate(-pivotPos.x, -pivotPos.y, -pivotPos.z);
        m.geometry.computeBoundingBox();
        m.geometry.computeBoundingSphere();
        m.position.copy(pivotPos);
        m.rotation.order = 'ZXY';
      }
      this.wheelObjects.push({ meshes: wheelObjectMeshes, front: i < 2, viewKey: '' });
      this.wheelIdlePositions.push({ x: pivotPos.x, y: pivotPos.y, z: pivotPos.z });
    }
  }

  /**
   * Texture frames (CarIO_SetupTextures): meshes whose polygons have frames (extras `frames`; without the extras the
   * tyre quads, 4 frames) get a material of their own per group: front tyres (parts 12, 14), rear tyres (16, 18), brake
   * lights (part 11, R3DCar_FindBrakeLightPolys 0x45b5b0). Frames 1.. are the PNGs next to the textures
   */
  private setUpAnimations(
    meshes: { mesh: Mesh; part: number }[],
    assetsPath: string,
    framesOf?: (part: number, texture: string) => number,
  ) {
    const loader = new TextureLoader();
    const loaded = new Map<string, Texture>();
    const load = (name: string, like: Texture): Texture => {
      let texture = loaded.get(name);
      if (!texture) {
        // a frame that can't load is drawn as frame 0 (an empty texture is cut out by the alpha test: the polygon
        // vanished while braking when the brake light frames were not on the CDN)
        texture = loader.load(`${assetsPath}/${name}.png`, undefined, undefined, () => this.frameMissing(texture!));
        setupNfs1Texture(texture);
        texture.name = name;
        // as the GLB's own textures: not flipped (TextureLoader's default is)
        texture.flipY = like.flipY;
        texture.wrapS = ClampToEdgeWrapping;
        texture.wrapT = ClampToEdgeWrapping;
        loaded.set(name, texture);
        this.ownTextures.push(texture);
      }
      return texture;
    };
    const clones = new Map<string, AnimatedMaterial>();
    for (const { mesh: m, part } of meshes) {
      const group: AnimationGroup | null =
        part === 12 || part === 14 ? 'front' : part === 16 || part === 18 ? 'rear' : part === 11 ? 'brake' : null;
      const material = m.material as MeshBasicMaterial;
      const name = textureNameOf(material);
      const extras = m.userData?.['frames'];
      const frames =
        typeof extras === 'number'
          ? extras
          : name && framesOf
            ? framesOf(part, name)
            : group === 'front' || group === 'rear'
              ? 4
              : 1;
      if (!group || frames < 2 || !name || !material.map) {
        continue;
      }
      const key = `${group}|${material.uuid}`;
      let animated = clones.get(key);
      if (!animated) {
        const clone = material.clone();
        this.ownMaterials.push(clone);
        animated = {
          material: clone,
          depthMaterial: null!,
          frames: [
            material.map,
            ...Array.from({ length: frames - 1 }, (_, i) => load(frameTextureName(name, i + 1), material.map!)),
          ],
        };
        clones.set(key, animated);
        if (!this.animations.has(group)) {
          this.animations.set(group, { frame: 0, materials: [] });
        }
        this.animations.get(group)!.materials.push(animated);
      }
      m.material = animated.material;
    }
  }

  /** A frame texture failed to load: frame 0 instead */
  private frameMissing(texture: Texture) {
    for (const animation of this.animations.values()) {
      for (const animated of animation.materials) {
        const i = animated.frames.indexOf(texture);
        if (i > 0) {
          animated.frames[i] = animated.frames[0];
          if (animated.material.map === texture) {
            animated.material.map = animated.frames[0];
            animated.depthMaterial.map = animated.frames[0];
          }
        }
      }
    }
  }

  /** The texture frame of an animation group, see update */
  private setFrame(group: AnimationGroup, frame: number) {
    const animation = this.animations.get(group);
    if (!animation || animation.frame === frame) {
      return;
    }
    animation.frame = frame;
    for (const { material, depthMaterial, frames } of animation.materials) {
      // the same program: a map for another (no needsUpdate)
      material.map = frames[Math.min(frame, frames.length - 1)];
      depthMaterial.map = material.map;
    }
  }

  /**
   * Once per drawn frame, with the car's state and the sim tick (cars of other physics: the time in 1/64 s ticks).
   * Tyres (R3DCar_BodyCallback 0x45bd50): a counter goes up once per drawn frame in which the sim ticked; forward
   * speed over 20 m/s frame 3, over 7 m/s 1 / 2 every frame, over 2.5 m/s every 2nd, over 0.2 m/s every 4th, else 0;
   * wheelspin blurs the rear (3), front wheelspin the front; locked wheels stand (0), both once the race is finished
   * and the car below 2 m/s. Brake lights: frame 1 while the ramped brake is not 0.
   */
  update(state: Nfs2CarDrawState, simTick: number) {
    this.state = state;
    const ticked = simTick !== this.lastTick;
    this.lastTick = simTick;
    if (ticked) {
      this.frameCounter++;
    }
    const n = this.frameCounter;
    const speed = Math.abs(state.forwardSpeed);
    let front: number;
    if (speed > 0x140000) {
      front = 3;
    } else if (speed > 0x70000) {
      front = (n & 1) + 1;
    } else if (speed > 0x28000) {
      front = ((n & 2) >> 1) + 1;
    } else if (speed > 0x3333) {
      front = ((n & 4) >> 2) + 1;
    } else {
      front = 0;
    }
    let rear = front;
    if (state.wheelspin !== 0) {
      rear = 3;
    }
    if (state.frontWheelspin !== 0) {
      front = 3;
    }
    // the exe also writes car+0x2fc = 3 here (recomputed by the physics every step)
    const locked = state.raceState === 2 && state.horizontalSpeed < 0x20000 ? 3 : state.lockedWheels;
    if (locked & 1) {
      front = 0;
    }
    if (locked & 2) {
      rear = 0;
    }
    this.setFrame('front', front);
    this.setFrame('rear', rear);
    this.setFrame('brake', state.brake !== 0 ? 1 : 0);
    if (ticked && state.heightAboveGround !== undefined) {
      this.updateWheelBounce(state);
    }
  }

  /**
   * R3DCar_WheelBounce 0x45bbc0, once per sim tick: the wheels drop by the height above ground (0.01..0.04 m) when
   * they vibrate (crash vibration, wheelspin) and shake by a random part of the vibration
   */
  private updateWheelBounce(state: Nfs2CarDrawState) {
    for (const [i, { meshes, front }] of this.wheelObjects.entries()) {
      let v = state.vibration ?? 0;
      if ((state.vibrationSpeed ?? 0) > 0x2c0000 && v <= 0x2666) {
        v = 0x2666;
      }
      if ((front ? state.frontWheelspin : state.wheelspin) !== 0 && v <= 0xb333) {
        v = 0xb333;
      }
      const drop = v > 0x28f ? Math.min(Math.abs(state.heightAboveGround!) + 0x28f, 0xa3d) : 0;
      const shake = () => Math.trunc(fixmul(Math.floor(Math.random() * 0x1000000), v) / 0x1000);
      const offset = shake() > 0 ? -shake() - drop : shake() - drop;
      for (const m of meshes) {
        m.position.z = this.wheelIdlePositions[i].z + offset / 0x10000;
      }
    }
  }

  /** The view of this render: yaw and pitch (atan2 of x and of the height against forward, 0x10000 per turn) */
  private updateView(renderer: WebGLRenderer, camera: Camera) {
    const key = `${renderer.info.render.frame}|${camera.id}`;
    if (key === this.viewKey) {
      return;
    }
    this.viewKey = key;
    // car - camera in the car's frame (nfs-web axes: x right, y forward, z up)
    const camera_ = this.mesh.worldToLocal(camera.getWorldPosition(this.cameraPosition));
    const x = this.centre.x - camera_.x;
    const forward = this.centre.y - camera_.y;
    const up = this.centre.z - camera_.z;
    // math_atan2_16 0x48ee20 (the exe interpolates a table)
    this.viewYaw = Math.round((Math.atan2(x, forward) * 0x8000) / Math.PI);
    this.viewPitch = Math.round((Math.atan2(up, forward) * 0x8000) / Math.PI);
    this.updateLayers();
  }

  /**
   * Layer of a part for the view (Render_Car 0x45a510, Transfmr_DrawObject): IDGO draws its wheels' inner parts
   * (layers 1..4) over the body from the side they face, MACH reorders layers 6..9 by the yaw
   */
  private layerOf(part: number): number {
    const layer = NFS2_CAR_PART_LAYOUTS[this.layout][part][0];
    const yaw = this.viewYaw;
    if (this.model === MODEL_IDGO && layer < 5) {
      if (layer === 1 && yaw >= -0x7f00 && yaw < -0x1f00) return 0x12;
      if (layer === 2 && yaw > 0x1f00 && yaw <= 0x7f00) return 0x11;
      if (layer === 3 && yaw > -0x3200 && yaw <= 0) return 0x13;
      if (layer === 4 && yaw > 0 && yaw < 0x3200) return 0x14;
      return layer;
    }
    if (this.model === MODEL_MACH && layer >= 6 && layer <= 9) {
      if (yaw <= -0x6000 || yaw >= 0x6000) return [9, 8, 7, 6][layer - 6];
      if (Math.abs(yaw) > 0x2e00) return [8, 9, 6, 7][layer - 6];
    }
    return layer;
  }

  /** Render orders by layer; three sorts before the meshes' onBeforeRender: a layer change shows from the next frame */
  private updateLayers() {
    const layers = this.parts.map(p => this.layerOf(p.part));
    const key = layers.join(',');
    if (key === this.layerKey) {
      return;
    }
    this.layerKey = key;
    this.parts.forEach((p, i) => (p.mesh.renderOrder = layers[i] * LAYER_ORDER + p.index));
  }

  /** Transfmr_DrawObject: skipped from some view angles */
  private partVisible(part: number): boolean {
    const [, r0, r1, r2, r3] = NFS2_CAR_PART_LAYOUTS[this.layout][part];
    const yaw = this.viewYaw;
    const pitch = this.viewPitch;
    if (r0 === SPOILER_VIEW_RULE) {
      return pitch <= 0x2000 && (pitch >= -0x7500 || Math.abs(yaw) <= 0x6e00);
    }
    return !(r0 < yaw && yaw < r1 && r2 < pitch && pitch < r3);
  }

  /**
   * R3DCar_FrontWheelCallback 0x45baa0: the front wheels turn by k x steering (0x10000 per turn), k up to 0x2a growing
   * with the view's angle off the car's long axis, 0 seen from the side; IDGO always 0x2a.
   * SKIPPED: halved (LGT1 quartered) when turning right in the exe's camera view type 7 (Camera_ViewType 0x439c90).
   */
  private steerFactor(): number {
    const steer = this.state.steer;
    if (steer === 0 || this.model === MODEL_IDGO) {
      return MAX_STEER_FACTOR;
    }
    const yaw = this.viewYaw;
    let d = 0;
    if (yaw > -0x3200 && yaw < 0x3200) {
      d = Math.abs(yaw);
    } else if (yaw > 0x4600) {
      d = 0x7f00 - yaw;
    } else if (yaw < -0x4600) {
      d = yaw + 0x7f00;
    }
    return Math.min(Math.trunc(d / 256), MAX_STEER_FACTOR);
  }

  private beforeRender(entry: PartMesh, renderer: WebGLRenderer, camera: Camera) {
    this.updateView(renderer, camera);
    // skipped parts draw nothing (a draw range: three checks it after onBeforeRender)
    entry.mesh.geometry.drawRange.count = this.partVisible(entry.part) ? Infinity : 0;
    const wheel = entry.wheel;
    if (wheel?.front && wheel.viewKey !== this.viewKey) {
      wheel.viewKey = this.viewKey;
      // positive steering turns right: a negative turn about z (nfs-web: z up)
      const angle = (-this.steerFactor() * this.state.steer * 2 * Math.PI) / 0x10000;
      for (const m of wheel.meshes) {
        m.rotation.z = angle;
        // three computes the model view matrix after onBeforeRender, from the world matrix (the depth twin too)
        m.updateMatrixWorld(true);
      }
    }
  }

  private previewTimer: any = null;
  private previewSpeed = 0;
  private previewSteering = 0;
  private previewBrake = false;
  private previewTick = 0;

  /** Preview without a game loop (TailsLab): brake lights on (the brake pedal) */
  set brakeLightsOn(value: boolean) {
    this.previewBrake = value;
    this.startPreview();
  }

  get brakeLightsOn(): boolean {
    return this.previewBrake;
  }

  /** The model has brake lights (part 11 polygons with frames) */
  get hasBrakeLights(): boolean {
    return this.animations.has('brake');
  }

  /** Preview without a game loop (TailsLab): speed in m/s, the tyres animate on their own */
  set speed(value: number) {
    this.previewSpeed = value;
    this.startPreview();
  }

  get speed(): number {
    return this.previewSpeed;
  }

  /** Preview without a game loop (TailsLab): steering angle in radians, positive to the left, 0.5 is full */
  set steeringAngle(value: number) {
    this.previewSteering = value;
    this.startPreview();
  }

  get steeringAngle(): number {
    return this.previewSteering;
  }

  private startPreview() {
    if (!this.previewTimer) {
      this.previewTimer = setInterval(
        () =>
          this.update(
            nfs2DrawStateOf(this.previewSpeed, -this.previewSteering / 0.5, this.previewBrake),
            this.previewTick++,
          ),
        SIM_TICK_MS,
      );
    }
  }

  dispose() {
    if (this.previewTimer) {
      clearInterval(this.previewTimer);
      this.previewTimer = null;
    }
    for (const { mesh: m, depthMesh } of this.parts) {
      m.onBeforeRender = () => {};
      m.geometry.drawRange.count = Infinity;
      depthMesh.removeFromParent();
    }
    this.ownMaterials.forEach(m => m.dispose());
    this.ownTextures.forEach(t => t.dispose());
    this.animations.clear();
  }
}
