// PSX 16-bit colors (TNFS PSX `.PSH` images and CLUTs): bits 0-4 red, 5-9 green, 10-14 blue, 15 STP.
// 0x0000 is transparent (the GPU does not draw such texels), every other value is opaque. The same conversion as
// `psx_color_to_rgba` in `resources/eac/psx_bitmaps.py`.

export const PSX_STP_BIT = 0x8000;

const to8Bit = (value: number): number => Math.round(((value & 0x1f) * 255) / 31);
const to5Bit = (value: number): number => Math.round(((value & 0xff) * 31) / 255);

// 0xRRGGBBAA of a PSX color
export function psxColorToRgba(color: number): number {
  if (color === 0) return 0;
  return ((to8Bit(color) << 24) | (to8Bit(color >> 5) << 16) | (to8Bit(color >> 10) << 8) | 0xff) >>> 0;
}

// '#rrggbb' of a PSX color
export function psxColorToHex(color: number): string {
  return '#' + (psxColorToRgba(color) >>> 8).toString(16).padStart(6, '0');
}

// a PSX color of '#rrggbb' keeping the STP bit of `previous`. Black is 0x8000: 0x0000 would be transparent
export function hexToPsxColor(hex: string, previous: number): number | null {
  const match = /^#?([0-9a-f]{6})/i.exec(hex);
  if (!match) return null;
  const rgb = parseInt(match[1], 16);
  const color = to5Bit(rgb >> 16) | (to5Bit(rgb >> 8) << 5) | (to5Bit(rgb) << 10) | (previous & PSX_STP_BIT);
  return color === 0 ? PSX_STP_BIT : color;
}
