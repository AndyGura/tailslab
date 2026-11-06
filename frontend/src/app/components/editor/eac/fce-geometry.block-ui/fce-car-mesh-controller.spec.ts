import {
  BufferAttribute,
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
  Vector3,
  WebGLRenderer,
} from 'three';
import {
  FceCarMeshController,
  fce3ChromeAdd,
  fce3ChromeEnvMatrix,
  fce3ChromeUv,
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
    // the body has a copy of its own (chrome), painted
    const body = (car.children[0] as Mesh).material as MeshBasicMaterial;
    expect(body.map).toBe(map);
    expect(body.customProgramCacheKey()).toContain('fce-paint');
    expect(plain.customProgramCacheKey()).not.toContain('fce-paint');
    controller.dispose();
  });

  it('builds the chrome environment matrix as nfs3.exe', () => {
    // camera straight behind a car heading +z: the identity
    const behind = fce3ChromeEnvMatrix([0, 0, -10]);
    [1, 0, 0, 0, 1, 0, 0, 0, 1].forEach((v, i) => expect(behind[i]).toBeCloseTo(v, 6));
    // camera to the left: RotY(0.25 turn)
    const left = fce3ChromeEnvMatrix([-10, 0, 0]);
    [0, 0, -1, 0, 1, 0, 1, 0, 0].forEach((v, i) => expect(left[i]).toBeCloseTo(v, 6));
    // camera above: RotX(-0.25 turn) after RotY(-0.5 turn)
    const above = fce3ChromeEnvMatrix([0, 10, -1e-9]);
    [1, 0, 0, 0, 0, -1, 0, 1, 0].forEach((v, i) => expect(above[i]).toBeCloseTo(v, 6));
  });

  it('maps a normal to the chrome sphere map as nfs3.exe', () => {
    expect(fce3ChromeUv([0, 0, -1])).toEqual([0.5, 0.5]);
    expect(fce3ChromeUv([0, 0, 1])).toEqual([0.5, 0.5]);
    const [u, v] = fce3ChromeUv([1, 0, 0]);
    expect(u).toBeCloseTo(1, 5);
    expect(v).toBe(0.5);
    expect(fce3ChromeUv([0, -1, 0])[1]).toBeCloseTo(0, 5);
  });

  it('adds the chrome texel at 4 bits, times the vertex color and the texel alpha', () => {
    expect(fce3ChromeAdd([255, 128, 15, 255], 1)).toEqual([255, 136, 0]);
    expect(fce3ChromeAdd([255, 255, 255, 136], 1)).toEqual([136, 136, 136]);
    fce3ChromeAdd([240, 0, 0, 255], 0x7f / 255).forEach((c, i) => expect(c).toBeCloseTo([0x7f, 0, 0][i], 5));
  });

  it('gives chrome to the FCE3 body but matte meshes, with materials of their own', () => {
    const car = new Object3D();
    const shared = new MeshBasicMaterial({ map: new Texture() });
    const meshes: { [name: string]: Mesh } = {};
    for (const name of [
      'hp_0_body__car00',
      'hp_0_body__car00_matte',
      'hp_0_body__car00_high_chrome',
      'hp_1_wheel__car00',
    ]) {
      meshes[name] = new Mesh(new BoxGeometry(), shared);
      meshes[name].name = name;
      car.add(meshes[name]);
    }
    const controller = new FceCarMeshController(car, 3, [], [], () => null);
    expect(controller.hasChrome).toBeTrue();
    const key = (name: string) => (meshes[name].material as MeshBasicMaterial).customProgramCacheKey();
    expect(key('hp_0_body__car00')).toContain(`fce-chrome-normal-${0x7f / 255}`);
    expect(key('hp_0_body__car00_high_chrome')).toContain('fce-chrome-normal-1');
    expect(meshes['hp_0_body__car00_matte'].material).toBe(shared);
    expect(meshes['hp_1_wheel__car00'].material).toBe(shared);
    expect(meshes['hp_0_body__car00'].material).not.toBe(shared);
    expect(new FceCarMeshController(car.clone(), 4, [], [], () => null).hasChrome).toBeFalse();
    controller.dispose();
  });

  it('draws the chrome pass in the shader as the exe', () => {
    const canvas = document.createElement('canvas');
    let renderer: WebGLRenderer;
    try {
      renderer = new WebGLRenderer({ canvas, preserveDrawingBuffer: true });
    } catch {
      pending('no WebGL');
      return;
    }
    renderer.setPixelRatio(1);
    renderer.setSize(1, 1, false);
    const black = new DataTexture(new Uint8Array([0, 0, 0, 255]), 1, 1);
    black.needsUpdate = true;
    const plane = new Mesh(new PlaneGeometry(2, 2), new MeshBasicMaterial({ map: black }));
    plane.name = 'hp_0_body__car00';
    // the game's normal, mesh axes (x, y forward, z up)
    const normal = new Vector3(0.3, -0.8, 0.5).normalize();
    const normals = new Float32Array(4 * 3).map((_, i) => normal.getComponent(i % 3));
    plane.geometry.setAttribute('_game_normal', new BufferAttribute(normals, 3));
    const scene = new Scene();
    scene.add(plane);
    // 2 x 2 chrome texture, the first row on top (flipY false: v = 0 is the first row, as in D3D)
    const texels = [
      [250, 30, 70, 255],
      [20, 200, 90, 160],
      [100, 100, 255, 255],
      [180, 140, 10, 90],
    ];
    const chrome = new DataTexture(new Uint8Array(texels.flat()), 2, 2);
    chrome.colorSpace = SRGBColorSpace;
    chrome.magFilter = NearestFilter;
    chrome.minFilter = NearestFilter;
    chrome.needsUpdate = true;
    const controller = new FceCarMeshController(plane, 3, [], [], () => null);
    controller.chromeTexture = chrome;
    // the chrome turns to the camera drawing the car
    const camera = new Vector3(3, -5, 2);
    const view = new OrthographicCamera(-0.1, 0.1, 0.1, -0.1, -100, 100);
    view.position.copy(camera);
    view.lookAt(0, 0, 0);
    renderer.render(scene, view);
    const pixel = new Uint8Array(4);
    const gl = renderer.getContext();
    gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, pixel);
    // the same in the game's axes: (x, z, y)
    const e = fce3ChromeEnvMatrix([camera.x, camera.z, camera.y]);
    const g = [normal.x, normal.z, normal.y];
    const n = [0, 1, 2].map(c => g[0] * e[c] + g[1] * e[3 + c] + g[2] * e[6 + c]) as [number, number, number];
    const [u, v] = fce3ChromeUv(n);
    const texel = texels[Math.floor(v * 2) * 2 + Math.floor(u * 2)] as [number, number, number, number];
    const expected = fce3ChromeAdd(texel, 0x7f / 255);
    Array.from(pixel.slice(0, 3)).forEach((c, i) => expect(Math.abs(c - expected[i])).toBeLessThanOrEqual(1));
    controller.dispose();
    renderer.dispose();
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
