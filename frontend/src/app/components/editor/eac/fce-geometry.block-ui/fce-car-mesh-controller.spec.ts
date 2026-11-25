import {
  BufferAttribute,
  BoxGeometry,
  CubeTexture,
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
  Vector4,
  WebGLRenderer,
} from 'three';
import {
  FceCarMeshController,
  FCE3_TRANSLUCENT_ALPHA,
  FCE4_DEFAULT_TRACK_LIGHT,
  fce3ChromeAdd,
  fce3ChromeEnvMatrix,
  fce3ChromeUv,
  fce3SkyChromeAlpha,
  fce3WheelSpinStep,
  fce3HsbToRgb,
  fce3PaintColor,
  fce3TexelColor,
  fce4CarTrackLight,
  fce4ChromeAdd,
  fce4ChromeColors,
  fce4NearestColorSet,
  fce4RgbToHsb,
  fce4TexelColor,
  fceChromeClassOf,
  FceColor,
  FceVersion,
  rgbToFceColor,
  fcePaintIndexOfAlpha,
  fcePaintMaskNextToTexture,
} from '../../../../../nfs-three-lib/fce-car-mesh-controller';
import { SCENE_SKY_TOP_COLOR, SCENE_TRACK_LIGHT } from '../../../../../nfs-three-lib/scene-sky';

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

/** A 1 x 1 canvas of a color */
function pixelCanvas([r, g, b]: number[]): HTMLCanvasElement {
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = 1;
  const ctx = canvas.getContext('2d')!;
  ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
  ctx.fillRect(0, 0, 1, 1);
  return canvas;
}

/** The vertex color uniform a chrome material's shader gets (its onBeforeCompile on an empty shader) */
function chromeColorOf(mesh: Mesh): Vector4 {
  const shader: any = { uniforms: {}, vertexShader: '', fragmentShader: '' };
  (mesh.material as MeshBasicMaterial).onBeforeCompile(shader, null as any);
  return shader.uniforms['fceChromeColor'].value;
}

/** A WebGL renderer drawing 1 x 1 pixel, null without WebGL */
function pixelRenderer(): WebGLRenderer | null {
  try {
    const renderer = new WebGLRenderer({ canvas: document.createElement('canvas'), preserveDrawingBuffer: true });
    renderer.setPixelRatio(1);
    renderer.setSize(1, 1, false);
    return renderer;
  } catch {
    return null;
  }
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
    // nfs4.exe 0x4ee620: 0xc4..0xfe primary, 0x80..0xc3 interior, 0x40..0x7f secondary, 1..0x3f driver hair
    expect(fcePaintIndexOfAlpha(4, 0)).toBe(-1);
    expect(fcePaintIndexOfAlpha(4, 255)).toBe(-1);
    expect(fcePaintIndexOfAlpha(4, 0xfe)).toBe(0);
    expect(fcePaintIndexOfAlpha(4, 0xc4)).toBe(0);
    expect(fcePaintIndexOfAlpha(4, 0xc3)).toBe(1);
    expect(fcePaintIndexOfAlpha(4, 0x80)).toBe(1);
    expect(fcePaintIndexOfAlpha(4, 0x7f)).toBe(2);
    expect(fcePaintIndexOfAlpha(4, 0x40)).toBe(2);
    expect(fcePaintIndexOfAlpha(4, 0x3f)).toBe(3);
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

  it('paints FCE4 texels as nfs4.exe: the FCE3 paint, four colors by the alpha, 5 bits', () => {
    const colors: FceColor[] = [
      { hue: 0, saturation: 255, brightness: 200, transparency: 127 },
      { hue: 85, saturation: 255, brightness: 200, transparency: 127 },
      { hue: 170, saturation: 255, brightness: 200, transparency: 127 },
      { hue: 0, saturation: 0, brightness: 100, transparency: 127 },
    ];
    // the texel's blue shades the brightness: 128 / (255 - 127) = 1
    expect(fce4TexelColor([0, 0, 128], 0xd0, colors)).toEqual(fce3TexelColor([0, 0, 128], 1, colors[0], colors[0]));
    expect(fce4TexelColor([0, 0, 128], 0x90, colors)).toEqual(fce3TexelColor([0, 0, 128], 1, colors[1], colors[1]));
    expect(fce4TexelColor([0, 0, 128], 0x50, colors)).toEqual(fce3TexelColor([0, 0, 128], 1, colors[2], colors[2]));
    expect(fce4TexelColor([0, 0, 64], 0x10, colors)).toEqual([49, 49, 49]);
    // unpainted texels go through the 16-bit texture too
    expect(fce4TexelColor([10, 20, 30], 255, colors)).toEqual([8, 16, 25]);
  });

  it('picks the FCE4 color set whose primary is the nearest to the chosen color', () => {
    const primaries = [rgbToFceColor(0xff0000, 127), rgbToFceColor(0x00ff00, 127), rgbToFceColor(0x0000ff, 127)];
    expect(fce4NearestColorSet(primaries, rgbToFceColor(0x10e020, 127))).toBe(1);
    expect(fce4NearestColorSet(primaries, rgbToFceColor(0x2000c0, 127))).toBe(2);
    expect(fce4NearestColorSet([], rgbToFceColor(0x2000c0, 127))).toBe(0);
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

  it('adds the chrome texel at 4 bits, times the vertex color, its alpha (the same grey) and the texel alpha', () => {
    expect(fce3ChromeAdd([255, 128, 15, 255], 1)).toEqual([255, 136, 0]);
    expect(fce3ChromeAdd([255, 255, 255, 136], 1)).toEqual([136, 136, 136]);
    // D3DTBLEND_MODULATEALPHA: 0x7f7f7f7f twice, colour and alpha
    fce3ChromeAdd([240, 0, 0, 255], 0x7f / 255).forEach((c, i) =>
      expect(c).toBeCloseTo([(0x7f * 0x7f) / 255, 0, 0][i], 5),
    );
  });

  it('converts RGB to HSB with the integer math of nfs4.exe', () => {
    expect(fce4RgbToHsb(0xff0000)).toEqual([0, 255, 255]);
    expect(fce4RgbToHsb(0x00ff00)).toEqual([85, 255, 255]);
    expect(fce4RgbToHsb(0x0000ff)).toEqual([171, 255, 255]);
    // red the largest: (g - b) / delta = -1 sector, / 6 + 1 turn, x 256 rounded
    expect(fce4RgbToHsb(0xff00ff)).toEqual([213, 255, 255]);
    expect(fce4RgbToHsb(0x808080)).toEqual([0, 0, 128]);
    expect(fce4RgbToHsb(0)).toEqual([0, 0, 0]);
    // saturation 96 * 256 / 127 truncated, hue 32 / 96 sector as 16.16 truncated, / 6 truncated, x 256 rounded
    expect(fce4RgbToHsb(0x7f3f1f)).toEqual([14, 193, 127]);
  });

  it("averages the track light under the car's wheels as nfs4.exe", () => {
    expect(fce4CarTrackLight([0x102030, 0x405060, null])).toBe(0x535b63);
    expect(fce4CarTrackLight([null, null, null, null])).toBe(FCE4_DEFAULT_TRACK_LIGHT);
    // the mean floored: (3 x 255 + 254) >> 2
    expect(fce4CarTrackLight([0xffffff, 0xffffff, 0xffffff, 0xfefefe])).toBe(0xfefefe);
  });

  it('computes the FCE4 chrome colors as nfs4.exe', () => {
    // white sky, the default track light (brightness 127): (255 * 127 >> 9) + 0x80 = 191, the paint's 200 >> 2 off
    expect(fce4ChromeColors(0x7f7f7f, 0xffffff, 200, 0)).toEqual({ normal: 0x8d8d8d8d, high: 0xbfbfbfbf });
    // sky HSB (149, 170, 192): normal (149, 63, 164 - 63 = 101 clamped to 0x7f), high (149, 85, 164)
    expect(fce4ChromeColors(0x606060, 0x4080c0, 255, 0)).toEqual({ normal: 0x7f5f6f7f, high: 0xa46d89a4 });
    // covered, 3 slices: the sky 160 / 256 towards the track light, every byte x 208 >> 8
    expect(fce4ChromeColors(0x204060, 0xc0e0ff, 100, 3)).toEqual({ normal: 0x70636970, high: 0x856f7a85 });
    // 8 slices: the track light alone, halved
    expect(fce4ChromeColors(0x808080, 0x0000ff, 0, 8)).toEqual({ normal: 0x50505050, high: 0x50505050 });
    expect(fce4ChromeColors(0x808080, 0x0000ff, 0, 12)).toEqual(fce4ChromeColors(0x808080, 0x0000ff, 0, 8));
    // brightness clamped to 0x7f..0xff
    expect(fce4ChromeColors(0, 0, 255, 0)).toEqual({ normal: 0x7f7f7f7f, high: 0x80808080 });
    expect(fce4ChromeColors(0xffffff, 0xffffff, 0, 0)).toEqual({ normal: 0xffffffff, high: 0xffffffff });
  });

  it('adds the FCE4 chrome texel times the vertex color and both alphas', () => {
    expect(fce4ChromeAdd([255, 255, 255, 255], 0xffffffff)).toEqual([255, 255, 255]);
    // texel 15 / 15, 8 / 15, 1 / 15 (4 bits) x color 0xff, 0x80, 0 / 255, x texel alpha 1 x color alpha 0x80 / 255
    fce4ChromeAdd([240, 128, 16, 255], 0x80ff8000).forEach((c, i) =>
      expect(c).toBeCloseTo([1, (8 / 15) * (0x80 / 255), 0][i] * (0x80 / 255) * 255, 5),
    );
    expect(fce4ChromeAdd([255, 255, 255, 0], 0xffffffff)).toEqual([0, 0, 0]);
  });

  it('reads the chrome class of a mesh, before the FCE4 window class', () => {
    const mesh = (name: string, extras?: string) => {
      const o = new Object3D();
      o.name = name;
      if (extras) {
        o.userData['fceChrome'] = extras;
      }
      return o;
    };
    expect(fceChromeClassOf(mesh('hp_0_HB__car00'))).toBe('normal');
    expect(fceChromeClassOf(mesh('hp_0_HB__car00_matte_damaged'))).toBe('none');
    expect(fceChromeClassOf(mesh('hp_0_HB__car00_translucent_high_chrome_window_front_breakaway'))).toBe('high');
    expect(fceChromeClassOf(mesh('hp_0_HB__car00_high_chrome_window_damaged'))).toBe('high');
    expect(fceChromeClassOf(mesh('hp_0_HB__car00', 'none'))).toBe('none');
  });

  it('gives chrome to the FCE4 chrome parts but matte meshes, the classes their colors', () => {
    const car = new Object3D();
    const shared = new MeshBasicMaterial({ map: new Texture() });
    const meshes: { [name: string]: Mesh } = {};
    for (const name of [
      'hp_0_HB__car00',
      'hp_0_HB__car00_translucent_high_chrome_window_front',
      'hp_0_HB__car00_matte',
      'mp_5_MB__car00',
      'lp_9_LB__car00',
      'tp_12_TB__car00',
      'hp_13_OC__car00',
      'hp_14_OLM__car00_high_chrome',
      'hp_15_OD__car00',
      'hp_16_OLB__car00',
      'hp_1_HLFW__car00',
    ]) {
      meshes[name] = new Mesh(new BoxGeometry(), shared);
      meshes[name].name = name;
      car.add(meshes[name]);
    }
    const controller = new FceCarMeshController(car, 4, [], [], () => null);
    expect(controller.hasChrome).toBeTrue();
    const chrome = (controller as any).chrome;
    for (const name of ['hp_0_HB__car00', 'mp_5_MB__car00', 'lp_9_LB__car00', 'hp_13_OC__car00']) {
      expect(meshes[name].material).withContext(name).not.toBe(shared);
      expect(chromeColorOf(meshes[name])).withContext(name).toBe(chrome.colors.normal.value);
    }
    for (const name of ['hp_0_HB__car00_translucent_high_chrome_window_front', 'hp_14_OLM__car00_high_chrome']) {
      expect(chromeColorOf(meshes[name])).withContext(name).toBe(chrome.colors.high.value);
    }
    for (const name of [
      'hp_0_HB__car00_matte',
      'tp_12_TB__car00',
      'hp_15_OD__car00',
      'hp_16_OLB__car00',
      'hp_1_HLFW__car00',
    ]) {
      expect(meshes[name].material).withContext(name).toBe(shared);
    }
    controller.dispose();
  });

  it('draws the FCE4 chrome pass with the colors of the track light, the sky top and the paint', () => {
    const renderer = pixelRenderer();
    if (!renderer) {
      pending('no WebGL');
      return;
    }
    const black = new DataTexture(new Uint8Array([0, 0, 0, 255]), 1, 1);
    black.needsUpdate = true;
    const car = new Object3D();
    const normal = new Vector3(0.3, -0.8, 0.5).normalize();
    // two chrome meshes in view, the body and the cockpit behind it
    for (const [name, z] of [
      ['hp_0_HB__car00', 0],
      ['hp_13_OC__car00', -0.01],
    ] as const) {
      const plane = new Mesh(new PlaneGeometry(2, 2), new MeshBasicMaterial({ map: black }));
      plane.name = name;
      plane.position.z = z;
      const normals = new Float32Array(4 * 3).map((_, i) => normal.getComponent(i % 3));
      plane.geometry.setAttribute('_game_normal', new BufferAttribute(normals, 3));
      car.add(plane);
    }
    // the wheels, out of view (in their geometry, as TailsLab's meshes): front left, front right, rear left, rear right
    for (const [name, x, y] of [
      ['hp_1_HLFW__car00', -50, 50],
      ['hp_2_HRFW__car00', 50, 50],
      ['hp_3_HLRW__car00', -50, -50],
      ['hp_4_HRRW__car00', 50, -50],
    ] as const) {
      const wheel = new Mesh(new BoxGeometry(0.5, 0.5, 0.5).translate(x, y, 0));
      wheel.name = name;
      car.add(wheel);
    }
    const scene = new Scene();
    scene.add(car);
    const lights: { [key: string]: number | null } = { '-50,50': 0x405060, '50,50': 0x203040, '-50,-50': null };
    let lookups = 0;
    scene.userData[SCENE_TRACK_LIGHT] = (x: number, y: number) => {
      lookups++;
      const key = `${Math.round(x)},${Math.round(y)}`;
      return key in lights ? lights[key] : 0x102030;
    };
    scene.userData[SCENE_SKY_TOP_COLOR] = 0x4080c0;
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
    const paint = { hue: 10, saturation: 200, brightness: 180, transparency: 127 };
    const controller = new FceCarMeshController(car, 4, [], [paint], () => null);
    controller.chromeTexture = chrome;
    controller.chromeCoveredSlices = 2;
    const camera = new Vector3(3, -5, 2);
    const view = new OrthographicCamera(-0.1, 0.1, 0.1, -0.1, -100, 100);
    view.position.copy(camera);
    view.lookAt(0, 0, 0);
    renderer.render(scene, view);
    // the track light looked up once per frame for the car, not per chrome mesh
    expect(lookups).toBe(4);
    const pixel = new Uint8Array(4);
    const gl = renderer.getContext();
    gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, pixel);
    const e = fce3ChromeEnvMatrix([camera.x, camera.z, camera.y]);
    const g = [normal.x, normal.z, normal.y];
    const n = [0, 1, 2].map(c => g[0] * e[c] + g[1] * e[3 + c] + g[2] * e[6 + c]) as [number, number, number];
    const [u, v] = fce3ChromeUv(n);
    const texel = texels[Math.floor(v * 2) * 2 + Math.floor(u * 2)] as [number, number, number, number];
    const trackLight = fce4CarTrackLight([0x405060, 0x203040, null, 0x102030]);
    const brightness = fce4RgbToHsb(fce3HsbToRgb(paint).reduce((rgb, c) => (rgb << 8) | c, 0))[2];
    const color = fce4ChromeColors(trackLight, 0x4080c0, brightness, 2).normal;
    // the body in front of the cockpit: its pixel
    const expected = fce4ChromeAdd(texel, color);
    Array.from(pixel.slice(0, 3)).forEach((c, i) => expect(Math.abs(c - expected[i])).toBeLessThanOrEqual(1));
    // a new frame looks the track light up again
    renderer.render(scene, view);
    expect(lookups).toBe(8);
    controller.dispose();
    renderer.dispose();
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
    expect(key('hp_0_body__car00')).toContain('fce-chrome-normal');
    // nfs3.exe's vertex colors, 0x7f7f7f7f and 0xffffffff
    expect(chromeColorOf(meshes['hp_0_body__car00']).toArray()).toEqual([
      0x7f / 255,
      0x7f / 255,
      0x7f / 255,
      0x7f / 255,
    ]);
    expect(chromeColorOf(meshes['hp_0_body__car00_high_chrome']).toArray()).toEqual([1, 1, 1, 1]);
    expect(meshes['hp_0_body__car00_matte'].material).toBe(shared);
    expect(meshes['hp_1_wheel__car00'].material).toBe(shared);
    expect(meshes['hp_0_body__car00'].material).not.toBe(shared);
    expect(new FceCarMeshController(car.clone(), 4, [], [], () => null).hasChrome).toBeFalse();
    controller.dispose();
  });

  it('draws FCE3 translucent polygons at the race vertex alpha 0x4f, the chrome copy too', () => {
    const car = new Object3D();
    const meshes: { [name: string]: Mesh } = {};
    for (const name of ['hp_0_body__car00_translucent_high_chrome', 'hp_0_body__car00']) {
      meshes[name] = new Mesh(new BoxGeometry(), new MeshBasicMaterial({ map: new Texture(), transparent: true }));
      meshes[name].name = name;
      car.add(meshes[name]);
    }
    const controller = new FceCarMeshController(car, 3, [], [], () => null);
    expect(FCE3_TRANSLUCENT_ALPHA).toBe(0x4f / 255);
    expect((meshes['hp_0_body__car00_translucent_high_chrome'].material as MeshBasicMaterial).opacity).toBe(
      FCE3_TRANSLUCENT_ALPHA,
    );
    expect((meshes['hp_0_body__car00'].material as MeshBasicMaterial).opacity).toBe(1);
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

  it('reflects the sky of the scene without a chrome texture', () => {
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
    // turned up in the environment matrix space (y 0.83): the sky adds about half of itself (fce3SkyChromeAlpha)
    const normal = new Vector3(0.2, -0.3, 0.93).normalize();
    const normals = new Float32Array(4 * 3).map((_, i) => normal.getComponent(i % 3));
    plane.geometry.setAttribute('_game_normal', new BufferAttribute(normals, 3));
    const scene = new Scene();
    scene.add(plane);
    // a color per cube face: +x, -x, +y, -y, +z, -z
    const faces = [
      [240, 30, 70],
      [20, 200, 90],
      [100, 100, 255],
      [180, 140, 10],
      [60, 220, 220],
      [250, 250, 120],
    ];
    const sky = new CubeTexture(faces.map(pixelCanvas));
    sky.colorSpace = SRGBColorSpace;
    // one color per face: WebGL 2 filters a cube texture across the face edges
    sky.magFilter = NearestFilter;
    sky.minFilter = NearestFilter;
    sky.generateMipmaps = false;
    sky.needsUpdate = true;
    scene.background = sky;
    const controller = new FceCarMeshController(plane, 3, [], [], () => null);
    const camera = new Vector3(3, -5, 2);
    const view = new OrthographicCamera(-0.1, 0.1, 0.1, -0.1, -100, 100);
    view.position.copy(camera);
    view.lookAt(0, 0, 0);
    const pixel = new Uint8Array(4);
    const gl = renderer.getContext();
    renderer.render(scene, view);
    gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, pixel);
    // the camera's direction reflected by the normal, looked up as three.js draws a cube background (x mirrored)
    const eye = camera.clone().normalize();
    const r = normal
      .clone()
      .multiplyScalar(2 * normal.dot(eye))
      .sub(eye);
    const lookup = [-r.x, r.y, r.z];
    const axis = [0, 1, 2].reduce((a, c) => (Math.abs(lookup[c]) > Math.abs(lookup[a]) ? c : a), 0);
    const face = faces[axis * 2 + (lookup[axis] < 0 ? 1 : 0)];
    // the normal's y in the environment matrix space (game axes: x, z up as y, y as z)
    const e = fce3ChromeEnvMatrix([camera.x, camera.z, camera.y]);
    const up = normal.x * e[1] + normal.z * e[4] + normal.y * e[7];
    expect(up).toBeCloseTo(0.832, 2);
    const expected = fce3ChromeAdd([...face, fce3SkyChromeAlpha(up) * 255] as any, 0x7f / 255);
    expect(Math.max(...expected)).toBeGreaterThan(20);
    Array.from(pixel.slice(0, 3)).forEach((c, i) => expect(Math.abs(c - expected[i])).toBeLessThanOrEqual(1));
    // no chrome without the option, or without a sky
    controller.chromeEnabled = false;
    renderer.render(scene, view);
    gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, pixel);
    expect(Array.from(pixel.slice(0, 3))).toEqual([0, 0, 0]);
    controller.chromeEnabled = true;
    scene.background = null;
    renderer.render(scene, view);
    gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, pixel);
    expect(Array.from(pixel.slice(0, 3))).toEqual([0, 0, 0]);
    controller.dispose();
    sky.dispose();
    renderer.dispose();
  });

  it('dims the sky chrome to what the CHRD textures of the tracks add: sky for normals turned up, little elsewhere', () => {
    expect(fce3SkyChromeAlpha(1)).toBeCloseTo(0.55, 6);
    expect(fce3SkyChromeAlpha(0.65)).toBeCloseTo(0.275, 6);
    expect(fce3SkyChromeAlpha(0.3)).toBeCloseTo(0.07, 6);
    expect(fce3SkyChromeAlpha(0)).toBeCloseTo(0.07, 6);
    expect(fce3SkyChromeAlpha(-0.15)).toBeCloseTo(0.035, 6);
    expect(fce3SkyChromeAlpha(-0.3)).toBe(0);
    expect(fce3SkyChromeAlpha(-1)).toBe(0);
  });

  it('spins the FCE3 wheels per sim tick as nfs3.exe, at most 8 turns per second', () => {
    expect(fce3WheelSpinStep(0, true, false)).toBe(0);
    expect(fce3WheelSpinStep(6, true, false)).toBeCloseTo(0.05, 9);
    expect(fce3WheelSpinStep(15, true, false)).toBe(0.125);
    expect(fce3WheelSpinStep(80, false, false)).toBe(0.125);
    expect(fce3WheelSpinStep(-80, true, false)).toBe(-0.125);
    // the handbrake slows the rear wheels only
    expect(fce3WheelSpinStep(80, false, true)).toBeCloseTo(0.0125, 9);
    expect(fce3WheelSpinStep(1.2, false, true)).toBeCloseTo(0.01, 9);
    expect(fce3WheelSpinStep(80, true, true)).toBe(0.125);
  });

  it('spins the FCE3 wheels by the sim ticks passed', () => {
    const car = new Object3D();
    const wheels: Mesh[] = [];
    for (const name of ['hp_1_wheel', 'hp_3_wheel']) {
      const wheel = new Mesh(new BoxGeometry());
      wheel.name = name;
      car.add(wheel);
      wheels.push(wheel);
    }
    const now = spyOn(performance, 'now').and.returnValue(1000);
    const controller = new FceCarMeshController(car, 3, [], [], () => null);
    controller.speed = 6;
    controller.handbrake = true;
    // 10 ticks of 1/64 s
    now.and.returnValue(1000 + 10 * (1000 / 64));
    (controller as any).spinWheels();
    // front 10 * 0.05 turns, rear (handbrake) 10 * 0.0125 turns; negative rolls forward
    expect(wheels[0].rotation.x).toBeCloseTo(-Math.PI, 6);
    expect(wheels[1].rotation.x).toBeCloseTo(-Math.PI / 4, 6);
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
          expected = fce4TexelColor(texel as [number, number, number], alphas[i], colors);
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
