import {
  BoxGeometry,
  BufferAttribute,
  CubeTexture,
  DataTexture,
  Group,
  Mesh,
  MeshBasicMaterial,
  NearestFilter,
  OrthographicCamera,
  PlaneGeometry,
  Scene,
  SRGBColorSpace,
  Texture,
  Vector3,
  WebGLRenderer,
} from 'three';
import {
  NFS6_PS2_RSQRT,
  Nfs6Ps2CarInfo,
  Nfs6Ps2CarMeshController,
  nfs6Ps2BitsFloat,
  nfs6Ps2EnvAlpha,
  nfs6Ps2Modulate,
  nfs6Ps2Pow,
  nfs6Ps2PowParams,
  nfs6Ps2Reflect,
  nfs6Ps2VertexLight,
} from '../../../../../nfs-three-lib/nfs6-ps2-car-mesh-controller';

function mesh(name: string, x: number, y: number, z: number, material = new MeshBasicMaterial()): Mesh {
  const geometry = new BoxGeometry(0.2, 0.6, 0.6);
  geometry.translate(x, y, z);
  const result = new Mesh(geometry, material);
  result.name = name;
  return result;
}

const INFO: Nfs6Ps2CarInfo = {
  model: 'TEST',
  car_type: 'TEST',
  wheels: [
    { name: 'fl', position: [-0.8, 1.3, 0.3], radius: 0.3 },
    { name: 'fr', position: [0.8, 1.3, 0.3], radius: 0.3 },
    { name: 'rr', position: [0.8, -1.4, 0.3], radius: 0.32 },
    { name: 'rl', position: [-0.8, -1.4, 0.3], radius: 0.32 },
  ],
  lights: { headlight: { off: 'textures/lights/TEST_HEADLIGHT.png', on: 'textures/lights/TEST_HEADLIGHT_ON.png' } },
};

// nfs6_ps2_lighting_vectors of RegPaintRed (GLOBAL/GLOBALB), front end set
const REG_PAINT_RED = [
  3.319999933242798, -2462937088, 0.10000000149011612, 0.003921568859368563, 1.0299999713897705, 1.0299999713897705,
  1.0199999809265137, 71.04000091552734, 0.9900000095367432, 1.0099999904632568, 1.0199999809265137, -37.76000213623047,
  10, -9573079040, 20, 108,
];

describe('Nfs6Ps2CarMeshController', () => {
  let car: Group;

  beforeEach(() => {
    car = new Group();
    const paint = new MeshBasicMaterial({ map: new Texture() });
    paint.name = 'skin';
    const headlight = new MeshBasicMaterial({ map: new Texture() });
    headlight.name = 'headlight';
    car.add(
      mesh('hp_body__skin', 0, 0, 0.5, paint),
      mesh('hp_body__headlight', 0, 2, 0.5, headlight),
      mesh('hp_tire_fl__skin', -0.8, 1.3, 0.3),
      mesh('hp_tire_rr__skin', 0.8, -1.4, 0.3),
      mesh('hp_brake_fr__BRAKESFRONT', 0.75, 1.3, 0.3),
    );
  });

  it('pivots wheel parts at their wheels', () => {
    const controller = new Nfs6Ps2CarMeshController(car, INFO, [], '');
    expect(controller.hasWheels).toBeTrue();
    const tire = car.getObjectByName('hp_tire_fl__skin')!;
    expect(tire.position.x).toBeCloseTo(-0.8);
    expect(tire.position.y).toBeCloseTo(1.3);
    expect(tire.position.z).toBeCloseTo(0.3);
  });

  it('steers front wheels, spins tyres only', () => {
    const controller = new Nfs6Ps2CarMeshController(car, INFO, [], '');
    controller.steeringAngle = 0.4;
    expect(car.getObjectByName('hp_tire_fl__skin')!.rotation.z).toBeCloseTo(0.4);
    expect(car.getObjectByName('hp_brake_fr__BRAKESFRONT')!.rotation.z).toBeCloseTo(0.4);
    expect(car.getObjectByName('hp_tire_rr__skin')!.rotation.z).toBe(0);
    expect(car.getObjectByName('hp_body__skin')!.rotation.z).toBe(0);
  });

  it('knows the paint and the lights', () => {
    const controller = new Nfs6Ps2CarMeshController(
      car,
      INFO,
      [{ name: 'SKIN1', label: 'red', texture: 'textures/skins/TEST_SKIN1.png' }],
      '',
    );
    expect(controller.skin).toBe('SKIN1');
    expect(controller.hasLights).toBeTrue();
    expect(controller.hasGameShading).toBeFalse();
  });

  it('uses the vertex colours of an export without lighting', () => {
    const body = car.getObjectByName('hp_body__skin') as Mesh;
    const count = body.geometry.getAttribute('position').count;
    body.geometry.setAttribute('color', new BufferAttribute(new Float32Array(count * 4), 4));
    new Nfs6Ps2CarMeshController(car, INFO, [], '');
    expect((body.material as MeshBasicMaterial).vertexColors).toBeTrue();
    expect(
      ((car.getObjectByName('hp_body__headlight') as Mesh).material as MeshBasicMaterial).vertexColors,
    ).toBeFalse();
  });

  it('gives shaded objects materials of their own, the paint lighting for CARSKIN', () => {
    const body = car.getObjectByName('hp_body__skin') as Mesh;
    // no texture to change with the paint
    const shared = new MeshBasicMaterial();
    shared.name = 'skin';
    body.material = shared;
    const info: Nfs6Ps2CarInfo = {
      ...INFO,
      textures: { skin: { alpha_blend: 0x0a, vertex_lit_env: true, alpha_test: false, repeat: [false, false] } },
      meshes: { hp_body__skin: { lighting_material: 'CARSKIN', vu_flags: 0x4180 } },
      lighting_materials: {
        RegPaintRed: { frontend: REG_PAINT_RED, race: REG_PAINT_RED.map(x => x * 2) },
        Default: { frontend: new Array(16).fill(1), race: new Array(16).fill(1) },
      },
    };
    const skins = [
      { name: 'SKIN1', label: 'red', texture: 't1.png', lighting_material: 'RegPaintRed' },
      { name: 'SKIN2', label: 'gray', texture: 't2.png', lighting_material: 'Unknown' },
    ];
    const controller = new Nfs6Ps2CarMeshController(car, info, skins, '');
    expect(controller.hasGameShading).toBeTrue();
    expect(body.material).not.toBe(shared);
    expect((body.material as MeshBasicMaterial).name).toBe('skin');
    const vectors = () => (controller as any).shaded[0].uniforms.vectors.value.flatMap((v: any) => v.toArray());
    expect(vectors()).toEqual(REG_PAINT_RED);
    controller.raceMaterials = true;
    expect(vectors()[0]).toBeCloseTo(REG_PAINT_RED[0] * 2, 4);
    controller.raceMaterials = false;
    // a lighting material the export lacks: "Default", as the game
    controller.skin = 'SKIN2';
    expect(vectors()).toEqual(new Array(16).fill(1));
  });
});

describe('nfs6Ps2 lighting helpers', () => {
  it('raises to the power with the float bit pattern', () => {
    // bias = float(bits(scale)) - n * float(bits(1.0)), float32
    expect(nfs6Ps2PowParams(3.32, 2.07)).toEqual([Math.fround(3.32), REG_PAINT_RED[1]]);
    expect(nfs6Ps2Pow(1, ...nfs6Ps2PowParams(3.32, 2.07))).toBeCloseTo(2.07, 3);
    const p = nfs6Ps2Pow(0.5, ...nfs6Ps2PowParams(2, 1));
    expect(p).toBeGreaterThan(0.24);
    expect(p).toBeLessThan(0.27);
    expect(nfs6Ps2Pow(0.1, 0, 0)).toBe(0);
  });

  it('normalizes the reflection as the VU1, 0.94 / length', () => {
    expect(NFS6_PS2_RSQRT).toEqual([-0.5, 1597031552]);
    expect(nfs6Ps2BitsFloat(0x3f70c49c)).toBeCloseTo(0.9405, 4);
    const r = nfs6Ps2Reflect(new Vector3(0, 0, 1), new Vector3(3, 0, -4));
    expect(r.x / r.length()).toBeCloseTo(0.6);
    expect(r.z / r.length()).toBeCloseTo(0.8);
    expect(r.length()).toBeGreaterThan(0.9);
    expect(r.length()).toBeLessThan(1.0);
  });

  it('lights a vertex as the VU1', () => {
    const lights = {
      directions: [new Vector3(0, 0, 1), new Vector3(1, 0, 0), new Vector3(0, 1, 0)],
      colors: [
        [80, 80, 80],
        [64, 64, 64],
        [128, 128, 180],
      ] as [number, number, number][],
      ambient: [32, 32, 32] as [number, number, number],
    };
    // no specular: reflection away from every light (least R.L 0.1 to the power 3.32 * 2.07)
    const reflect = new Vector3(0, -1, 0);
    const normal = new Vector3(0, 0, 1);
    const specular = nfs6Ps2Pow(Math.fround(0.1), REG_PAINT_RED[0], REG_PAINT_RED[1]);
    expect(specular).toBeLessThan(0.002);
    const [r, , b, a] = nfs6Ps2VertexLight(normal, reflect, [255, 255, 255], REG_PAINT_RED, lights, false);
    // light 0 diffuse, every light's specular at the least R.L
    expect(r).toBe(Math.trunc(32 + 80 * REG_PAINT_RED[4] + (80 + 64 + 128) * REG_PAINT_RED[8] * specular));
    expect(b).toBe(Math.trunc(32 + 80 * REG_PAINT_RED[6] + (80 + 64 + 180) * REG_PAINT_RED[10] * specular));
    expect(a).toBe(128);
    // vertex colour 0: no light
    expect(nfs6Ps2VertexLight(normal, reflect, [0, 0, 0], REG_PAINT_RED, lights, false).slice(0, 3)).toEqual([0, 0, 0]);
    // a paint: alpha from the specular of light 0 with the paint exponent
    const toLight0 = new Vector3(0, 0, 1);
    const paint = nfs6Ps2VertexLight(normal, toLight0, [255, 255, 255], REG_PAINT_RED, lights, true);
    const s0 = nfs6Ps2Pow(1, REG_PAINT_RED[12], REG_PAINT_RED[13]);
    expect(paint[3]).toBe(Math.min(255, Math.trunc(20 + 108 * s0)));
    expect(paint[0]).toBe(255);
  });

  it('weighs the environment pass by the reflection angle', () => {
    // back towards the camera: env_facing * 128 (0.26), away from it: env_grazing * 128 (0.85)
    expect(nfs6Ps2EnvAlpha(1, REG_PAINT_RED)).toBe(33);
    expect(nfs6Ps2EnvAlpha(-1, REG_PAINT_RED)).toBe(108);
    expect(nfs6Ps2EnvAlpha(0, REG_PAINT_RED)).toBe(71);
    expect(nfs6Ps2Modulate(127, 128)).toBe(127);
    expect(nfs6Ps2Modulate(200, 200)).toBe(255);
    expect(nfs6Ps2Modulate(90, 176)).toBe(123);
  });
});

describe('Nfs6Ps2CarMeshController shading', () => {
  // a plane facing the camera (+z), 1 x 1 texture, game normal +z, vertex colour 200
  function render(
    texel: number[],
    info: Nfs6Ps2CarInfo,
    setup: (controller: Nfs6Ps2CarMeshController, scene: Scene) => void,
  ): number[] | null {
    const canvas = document.createElement('canvas');
    let renderer: WebGLRenderer;
    try {
      renderer = new WebGLRenderer({ canvas, preserveDrawingBuffer: true });
    } catch {
      return null;
    }
    renderer.setPixelRatio(1);
    renderer.setSize(1, 1, false);
    const map = new DataTexture(new Uint8Array(texel), 1, 1);
    map.colorSpace = SRGBColorSpace;
    map.magFilter = NearestFilter;
    map.minFilter = NearestFilter;
    map.needsUpdate = true;
    const material = new MeshBasicMaterial({ map });
    material.name = 'skin';
    const plane = new Mesh(new PlaneGeometry(2, 2), material);
    plane.name = 'hp_body__skin';
    plane.geometry.setAttribute(
      '_game_normal',
      new BufferAttribute(
        new Float32Array(4 * 3).fill(0).map((_, i) => (i % 3 === 2 ? 1 : 0)),
        3,
      ),
    );
    plane.geometry.setAttribute(
      'color',
      new BufferAttribute(
        new Float32Array(4 * 4).fill(200 / 255).map((v, i) => (i % 4 === 3 ? 1 : v)),
        4,
      ),
    );
    const scene = new Scene();
    scene.add(plane);
    const controller = new Nfs6Ps2CarMeshController(plane, info, [], '');
    setup(controller, scene);
    const view = new OrthographicCamera(-0.1, 0.1, 0.1, -0.1, -100, 100);
    view.position.set(0, 0, 10);
    view.lookAt(0, 0, 0);
    renderer.render(scene, view);
    const pixel = new Uint8Array(4);
    const gl = renderer.getContext();
    gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, pixel);
    controller.dispose();
    renderer.dispose();
    return Array.from(pixel);
  }

  // diffuse only (no specular colour), vertex colours fully, no environment alpha change over the plane
  const VECTORS = [3, REG_PAINT_RED[1], 0.1, 1 / 255, 1, 0.5, 0.25, 64, 0, 0, 0, 0, 10, 0, 20, 0];
  const info = (vuFlags: number): Nfs6Ps2CarInfo => ({
    ...INFO,
    textures: { skin: { alpha_blend: 0x0a, vertex_lit_env: false, alpha_test: true, repeat: [false, false] } },
    meshes: { hp_body__skin: { lighting_material: 'Test', vu_flags: vuFlags } },
    lighting_materials: { Test: { frontend: VECTORS, race: VECTORS } },
  });

  it('draws the VU1 lighting and the GS texture function', () => {
    const pixel = render([100, 60, 200, 255], info(0x4080), controller => {
      // camera space: (0, 0, -1) is towards the camera, the plane's normal
      controller.lighting = {
        space: 'camera',
        directions: [
          [0, 0, -1],
          [0, -1, 0],
          [0, 0, 1],
        ],
        colors: [
          [100, 100, 100],
          [50, 50, 50],
          [70, 70, 70],
        ],
        ambient: [20, 20, 20],
      };
    });
    if (!pixel) {
      pending('no WebGL');
      return;
    }
    // light 0 only (light 1 is perpendicular, light 2 behind), times vertex colour 200 / 255
    const lit = [1, 0.5, 0.25].map(d => Math.trunc((20 + 100 * d) * (1 + (200 - 255) / 255)));
    const expected = [100, 60, 200].map((t, c) => nfs6Ps2Modulate(t, lit[c]));
    pixel.slice(0, 3).forEach((v, c) => expect(Math.abs(v - expected[c])).toBeLessThanOrEqual(1));
  });

  it("lights by the scene's sky and sun", () => {
    const color = [60, 120, 240];
    const sky = new CubeTexture(new Array(6).fill(0).map(() => pixelCanvas(color)));
    sky.colorSpace = SRGBColorSpace;
    sky.generateMipmaps = false;
    sky.needsUpdate = true;
    // texel 128: the lit colour as it is
    const pixel = render([128, 128, 128, 255], info(0x4080), (controller, scene) => {
      scene.background = sky;
      controller.sceneLighting = { direction: [0, 0, 1], color: [0.5, 0.5, 0.5] };
    });
    if (!pixel) {
      pending('no WebGL');
      return;
    }
    // ambient: the sky (the normal is up), 128 = 1; the sun as light 0 (colour 64) straight on; vertex colour 200
    const lit = [1, 0.5, 0.25].map((d, c) => Math.trunc(((color[c] / 255) * 128 + 64 * d) * (1 + (200 - 255) / 255)));
    pixel.slice(0, 3).forEach((v, c) => expect(Math.abs(v - lit[c])).toBeLessThanOrEqual(1));
  });

  it('adds the environment pass by its vertex alpha', () => {
    const sky = new CubeTexture(new Array(6).fill(0).map(() => pixelCanvas([60, 120, 240])));
    sky.colorSpace = SRGBColorSpace;
    sky.magFilter = NearestFilter;
    sky.minFilter = NearestFilter;
    sky.generateMipmaps = false;
    sky.needsUpdate = true;
    const pixel = render([0, 0, 0, 255], info(0x4180), (controller, scene) => {
      scene.background = sky;
      controller.lighting = {
        space: 'world',
        directions: [
          [0, 0, 1],
          [1, 0, 0],
          [0, 1, 0],
        ],
        colors: [
          [0, 0, 0],
          [0, 0, 0],
          [0, 0, 0],
        ],
        ambient: [0, 0, 0],
      };
    });
    if (!pixel) {
      pending('no WebGL');
      return;
    }
    // black texel: only the environment, 128 grey vertex colour, alpha 64
    const expected = [60, 120, 240].map(e => Math.floor((nfs6Ps2Modulate(e, 128) * 64) / 128));
    pixel.slice(0, 3).forEach((v, c) => expect(Math.abs(v - expected[c])).toBeLessThanOrEqual(1));
  });
});

function pixelCanvas([r, g, b]: number[]): HTMLCanvasElement {
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = 1;
  const ctx = canvas.getContext('2d')!;
  ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
  ctx.fillRect(0, 0, 1, 1);
  return canvas;
}
