import { hexToPsxColor, psxColorToHex, psxColorToRgba } from './psx-color';

describe('psx-color', () => {
  it('converts PSX colors to RGBA, 0x0000 transparent', () => {
    expect(psxColorToRgba(0)).toBe(0);
    expect(psxColorToRgba(0x001f)).toBe(0xff0000ff);
    expect(psxColorToRgba(0x03e0)).toBe(0x00ff00ff);
    expect(psxColorToRgba(0x7c00)).toBe(0x0000ffff);
    // STP black is opaque black
    expect(psxColorToRgba(0x8000)).toBe(0x000000ff);
    expect(psxColorToHex(0x801f)).toBe('#ff0000');
  });

  it('converts picked colors back keeping the STP bit, black stays opaque', () => {
    expect(hexToPsxColor('#ff0000', 0)).toBe(0x001f);
    expect(hexToPsxColor('#ff0000', 0x8000)).toBe(0x801f);
    expect(hexToPsxColor('#000000', 0x1234)).toBe(0x8000);
    expect(hexToPsxColor('nope', 0)).toBeNull();
    for (const color of [0x0001, 0x1234, 0x7fff, 0x8421]) {
      expect(hexToPsxColor(psxColorToHex(color), color)).toBe(color);
    }
  });
});
