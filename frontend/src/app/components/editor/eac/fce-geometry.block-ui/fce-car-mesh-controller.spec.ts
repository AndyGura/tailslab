import {
  BoxGeometry,
  DataTexture,
  LinearFilter,
  Mesh,
  MeshBasicMaterial,
  NearestFilter,
  Object3D,
  OrthographicCamera,
  PlaneGeometry,
  Scene,
  SRGBColorSpace,
  Texture,
  WebGLRenderer,
} from 'three';
import {
  FceCarMeshController,
  fceColorToRgb,
  fce3HsbToRgb,
  fce3PaintColor,
  fce3TexelColor,
  FceColor,
  fcePaintChannel,
  FceVersion,
  rgbToFceColor,
  fcePaintIndexOfAlpha,
  fcePaintMaskNextToTexture,
} from '../../../../../nfs-three-lib/fce-car-mesh-controller';

// texels of the test texture and alphas of its paint mask
const TEXELS = [
  [128, 128, 128],
  [64, 200, 10],
  [255, 255, 255],
  [100, 100, 100],
];
const MASK_ALPHAS = [100, 200, 0, 255];

function maskUrl(alphas: number[]): string {
  const canvas = document.createElement('canvas');
  canvas.width = alphas.length;
  canvas.height = 1;
  const ctx = canvas.getContext('2d')!;
  const data = ctx.createImageData(alphas.length, 1);
  alphas.forEach((a, i) => {
    data.data.set([255, 255, 255, a], i * 4);
  });
  ctx.putImageData(data, 0, 0);
  return canvas.toDataURL('image/png');
}

function texture(): DataTexture {
  const data = new Uint8Array(TEXELS.flatMap(t => [...t, 255]));
  const map = new DataTexture(data, TEXELS.length, 1);
  map.colorSpace = SRGBColorSpace;
  map.magFilter = NearestFilter;
  map.minFilter = NearestFilter;
  map.needsUpdate = true;
  return map;
}

describe('FceCarMeshController', () => {
  it('picks the paint by the mask alpha', () => {
    expect(fcePaintIndexOfAlpha(3, 0)).toBe(-1);
    expect(fcePaintIndexOfAlpha(3, 255)).toBe(-1);
    // nfs3.exe 0x49cd00: 1..127 primary, 128..254 secondary
    expect(fcePaintIndexOfAlpha(3, 127)).toBe(0);
    expect(fcePaintIndexOfAlpha(3, 128)).toBe(1);
    // FCE4: the nearest of 224, 164, 96, 32, the first one on a tie (the shader's thresholds 194, 130, 64)
    expect(fcePaintIndexOfAlpha(4, 194)).toBe(0);
    expect(fcePaintIndexOfAlpha(4, 193)).toBe(1);
    expect(fcePaintIndexOfAlpha(4, 130)).toBe(1);
    expect(fcePaintIndexOfAlpha(4, 129)).toBe(2);
    expect(fcePaintIndexOfAlpha(4, 64)).toBe(2);
    expect(fcePaintIndexOfAlpha(4, 63)).toBe(3);
    expect(fcePaintIndexOfAlpha(4, 1)).toBe(3);
  });

  it('converts HSB with the integer math of nfs3.exe', () => {
    expect(fce3HsbToRgb({ hue: 0, saturation: 255, brightness: 255, transparency: 0 })).toEqual([255, 0, 0]);
    expect(fce3HsbToRgb({ hue: 128, saturation: 255, brightness: 255, transparency: 0 })).toEqual([0, 255, 255]);
    expect(fce3HsbToRgb({ hue: 50, saturation: 0, brightness: 90, transparency: 0 })).toEqual([90, 90, 90]);
    expect(fce3HsbToRgb({ hue: 50, saturation: 200, brightness: 0, transparency: 0 })).toEqual([0, 0, 0]);
    // sector 1 (hue 43..85): green full, red falling
    expect(fce3HsbToRgb({ hue: 64, saturation: 255, brightness: 200, transparency: 0 })).toEqual([100, 200, 0]);
    const red = rgbToFceColor(0xff0000, 127);
    expect(fce3HsbToRgb(red)).toEqual([255, 0, 0]);
  });

  it('shades the FCE3 paint brightness by the texel blue and the transparency', () => {
    const color: FceColor = { hue: 0, saturation: 255, brightness: 200, transparency: 127 };
    // blue 128 / (255 - 127) = 1: the brightness
    expect(fce3PaintColor(128, color)).toEqual([200, 0, 0]);
    expect(fce3PaintColor(64, color)).toEqual([100, 0, 0]);
    // the blue channel reduced to 5 bits first
    expect(fce3PaintColor(71, color)).toEqual(fce3PaintColor(64, color));
    expect(fce3PaintColor(255, color)).toEqual([255, 0, 0]);
    // transparency 255: the brightness times the blue, at most 255
    expect(fce3PaintColor(8, { ...color, transparency: 255 })).toEqual([255, 0, 0]);
    // 5 bits per channel: 200 >> 3 = 25, 25 / 31
    expect(fce3TexelColor([0, 0, 128], 50, color, color)).toEqual([206, 0, 0]);
    expect(fce3TexelColor([10, 20, 30], 255, color, color)).toEqual([8, 16, 25]);
  });

  it('shades the FCE4 paint by the texture: mid-grey is exactly the paint', () => {
    expect(fcePaintChannel(128, 200)).toBe(200);
    expect(fcePaintChannel(64, 200)).toBe(100);
    expect(fcePaintChannel(255, 200)).toBe(255);
  });

  it('finds the paint mask next to a texture file', () => {
    const img = document.createElement('img');
    img.src = 'http://localhost/car/car00.png?v=1';
    expect(fcePaintMaskNextToTexture(new Texture(img))).toBe('http://localhost/car/car00_paint_mask.png?v=1');
    expect(fcePaintMaskNextToTexture(new Texture())).toBeNull();
  });

  it('keeps the textures and paints only materials with a paint mask', () => {
    const car = new Object3D();
    const painted = new MeshBasicMaterial({ map: new Texture() });
    const plain = new MeshBasicMaterial({ map: new Texture() });
    for (const [name, material] of [
      ['hp_0_body__car00', painted],
      ['hp_1_wheel__tire', plain],
    ] as const) {
      const mesh = new Mesh(new BoxGeometry(), material);
      mesh.name = name;
      car.add(mesh);
    }
    const map = painted.map;
    const controller = new FceCarMeshController(
      car,
      3,
      [],
      [rgbToFceColor(0xff0000, 127), rgbToFceColor(0x00ff00, 127)],
      t => (t === map ? 'data:,' : null),
    );
    expect(controller.isPaintable).toBeTrue();
    expect(controller.hasWheels).toBeTrue();
    expect(painted.map).toBe(map);
    expect(painted.customProgramCacheKey()).toContain('fce-paint');
    expect(plain.customProgramCacheKey()).not.toContain('fce-paint');
    controller.dispose();
  });

  for (const [version, filtered] of [
    [3, false],
    [3, true],
    [4, false],
  ] as [FceVersion, boolean][]) {
    it(`paints FCE${version} in the shader as the exe (${filtered ? 'linear' : 'nearest'} filter)`, async () => {
      const canvas = document.createElement('canvas');
      let renderer: WebGLRenderer;
      try {
        renderer = new WebGLRenderer({ canvas, preserveDrawingBuffer: true });
      } catch {
        pending('no WebGL');
        return;
      }
      renderer.setPixelRatio(1);
      renderer.setSize(TEXELS.length, 1, false);
      const map = texture();
      if (filtered) {
        map.magFilter = LinearFilter;
        map.minFilter = LinearFilter;
      }
      const material = new MeshBasicMaterial({ map });
      const plane = new Mesh(new PlaneGeometry(2, 2), material);
      plane.name = 'hp_0_body__car00';
      const scene = new Scene();
      scene.add(plane);
      const colors: FceColor[] = [
        { hue: 20, saturation: 180, brightness: 210, transparency: 100 },
        { hue: 170, saturation: 220, brightness: 160, transparency: 255 },
        { hue: 90, saturation: 100, brightness: 120, transparency: 0 },
        { hue: 0, saturation: 0, brightness: 60, transparency: 0 },
      ];
      const alphas = version === 3 ? MASK_ALPHAS : [224, 100, 0, 255];
      const controller = new FceCarMeshController(plane, version, [], colors, () => maskUrl(alphas));
      const enabled = (controller as any).paintTextures.get(map).enabled;
      for (let i = 0; i < 100 && !enabled.value; i++) {
        await new Promise(resolve => setTimeout(resolve, 20));
      }
      expect(enabled.value).toBe(1);
      renderer.render(scene, new OrthographicCamera(-1, 1, 1, -1, -1, 1));
      const gl = renderer.getContext();
      const pixels = new Uint8Array(TEXELS.length * 4);
      gl.readPixels(0, 0, TEXELS.length, 1, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
      TEXELS.forEach((texel, i) => {
        let expected: number[];
        if (version === 3) {
          expected = fce3TexelColor(texel as [number, number, number], alphas[i], colors[0], colors[1]);
        } else {
          const index = fcePaintIndexOfAlpha(4, alphas[i]);
          const rgb = index < 0 ? null : fceColorToRgb(colors[index]);
          const paint = rgb === null ? null : [rgb >> 16, (rgb >> 8) & 0xff, rgb & 0xff];
          expected = texel.map((t, c) => (paint ? fcePaintChannel(t, paint[c]) : t));
        }
        const actual = Array.from(pixels.slice(i * 4, i * 4 + 3));
        actual.forEach((v, c) =>
          expect(Math.abs(v - expected[c]))
            .withContext(`texel ${i}`)
            .toBeLessThanOrEqual(1),
        );
      });
      controller.dispose();
      renderer.dispose();
    });
  }
});
