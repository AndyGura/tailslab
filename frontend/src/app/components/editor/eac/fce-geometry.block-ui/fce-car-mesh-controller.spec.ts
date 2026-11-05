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
  fcePaintChannel,
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
    expect(fcePaintIndexOfAlpha(3, 159)).toBe(0);
    expect(fcePaintIndexOfAlpha(3, 160)).toBe(1);
    // FCE4: the nearest of 224, 164, 96, 32, the first one on a tie (the shader's thresholds 194, 130, 64)
    expect(fcePaintIndexOfAlpha(4, 194)).toBe(0);
    expect(fcePaintIndexOfAlpha(4, 193)).toBe(1);
    expect(fcePaintIndexOfAlpha(4, 130)).toBe(1);
    expect(fcePaintIndexOfAlpha(4, 129)).toBe(2);
    expect(fcePaintIndexOfAlpha(4, 64)).toBe(2);
    expect(fcePaintIndexOfAlpha(4, 63)).toBe(3);
    expect(fcePaintIndexOfAlpha(4, 1)).toBe(3);
  });

  it('shades the paint by the texture: mid-grey is exactly the paint', () => {
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
    const controller = new FceCarMeshController(car, 3, [], [0xff0000, 0x00ff00], t => (t === map ? 'data:,' : null));
    expect(controller.isPaintable).toBeTrue();
    expect(controller.hasWheels).toBeTrue();
    expect(painted.map).toBe(map);
    expect(painted.customProgramCacheKey()).toContain('fce-paint');
    expect(plain.customProgramCacheKey()).not.toContain('fce-paint');
    controller.dispose();
  });

  for (const filtered of [false, true]) {
    it(`paints in the shader as fcePaintChannel (${filtered ? 'linear' : 'nearest'} filter)`, async () => {
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
      const colors = [0xc86432, 0x2050f0];
      const controller = new FceCarMeshController(plane, 3, [], colors, () => maskUrl(MASK_ALPHAS));
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
        const index = fcePaintIndexOfAlpha(3, MASK_ALPHAS[i]);
        const paint = index < 0 ? null : [colors[index] >> 16, (colors[index] >> 8) & 0xff, colors[index] & 0xff];
        const expected = texel.map((t, c) => (paint ? fcePaintChannel(t, paint[c]) : t));
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
