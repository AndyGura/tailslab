import {
  AdditiveBlending,
  BoxGeometry,
  BufferAttribute,
  CubeTexture,
  DataTexture,
  Group,
  Mesh,
  MeshBasicMaterial,
  NearestFilter,
  NormalBlending,
  OrthographicCamera,
  PlaneGeometry,
  Scene,
  SRGBColorSpace,
  Texture,
  Vector3,
  WebGLRenderer,
} from 'three';
import {
  Nfs6CarLighting,
  Nfs6CarMeshController,
  Nfs6Location,
  nfs6BentNormal,
  nfs6Brightness,
  nfs6CarBlend,
  nfs6HemisphereAmbient,
  nfs6HotSpecular,
  nfs6Lit,
  nfs6PaintSpecular,
  nfs6PixelColor,
  nfs6SphereMapUv,
  nfs6TrackToWorld,
} from '../../../../../nfs-three-lib/nfs6-car-mesh-controller';

function mesh(name: string, x: number, y: number, z: number, material = new MeshBasicMaterial()): Mesh {
  const geometry = new BoxGeometry(0.2, 0.6, 0.6);
  geometry.translate(x, y, z);
  const result = new Mesh(geometry, material);
  result.name = name;
  return result;
}

describe('Nfs6CarMeshController', () => {
  let car: Group;
  let paint: MeshBasicMaterial;

  beforeEach(() => {
    car = new Group();
    paint = new MeshBasicMaterial({ map: new Texture() });
    paint.name = 'skin';
    car.add(
      mesh('hp_4_ALPHA_OPAQUE_HOODShape', 0, 1.5, 0.3, paint),
      // front right and rear left wheels
      mesh('hp_6_ALPHA_OPAQUE_RUBBER_Shape', 0.8, 1.1, 0.2),
      mesh('hp_8_ALPHA_OPAQUE_RUBBER_Shape2', -0.8, -1.6, 0.2),
      mesh('hp_18_ALPHA_OPAQUE_BRAKE_2Shape', 0.85, 1.2, 0.1),
    );
  });

  it('finds wheels and brakes', () => {
    const controller = new Nfs6CarMeshController(car, [], []);
    expect(controller.hasWheels).toBeTrue();
    const wheel = car.getObjectByName('hp_6_ALPHA_OPAQUE_RUBBER_Shape')!;
    // pivot is moved to the wheel center
    expect(wheel.position.x).toBeCloseTo(0.8);
    expect(wheel.position.y).toBeCloseTo(1.1);
    expect(wheel.position.z).toBeCloseTo(0.2);
    // brake caliper turns around its wheel axis
    const brake = car.getObjectByName('hp_18_ALPHA_OPAQUE_BRAKE_2Shape')!;
    expect(brake.position.x).toBeCloseTo(0.85);
    expect(brake.position.y).toBeCloseTo(1.1);
    expect(brake.position.z).toBeCloseTo(0.2);
  });

  it('steers front wheels and brakes only', () => {
    const controller = new Nfs6CarMeshController(car, [], []);
    controller.steeringAngle = 0.5;
    expect(car.getObjectByName('hp_6_ALPHA_OPAQUE_RUBBER_Shape')!.rotation.z).toBeCloseTo(0.5);
    expect(car.getObjectByName('hp_18_ALPHA_OPAQUE_BRAKE_2Shape')!.rotation.z).toBeCloseTo(0.5);
    expect(car.getObjectByName('hp_8_ALPHA_OPAQUE_RUBBER_Shape2')!.rotation.z).toBe(0);
    expect(car.getObjectByName('hp_4_ALPHA_OPAQUE_HOODShape')!.rotation.z).toBe(0);
  });

  it('shows light bones', () => {
    const controller = new Nfs6CarMeshController(
      car,
      [
        { name: 'LIGHT_TAIL_LEFT1', position: [-0.5, -2.1, 0.2] },
        { name: 'EXHAUST_1', position: [-0.2, -2.1, -0.2] },
      ],
      [],
    );
    expect(controller.hasLights).toBeTrue();
    expect(controller.showLights).toBeFalse();
    controller.showLights = true;
    const light = car.getObjectByName('LIGHT_TAIL_LEFT1')!;
    expect(light.position.toArray()).toEqual([-0.5, -2.1, 0.2]);
    expect(car.getObjectByName('EXHAUST_1')).toBeUndefined();
  });

  it('has default skin when the model uses skin texture', () => {
    const skins = [
      { name: 'skin00', label: 'red', texture: 'textures/skins/skin00-skin.png' },
      { name: 'skin01', label: 'black', texture: 'textures/skins/skin01-skin.png' },
    ];
    expect(new Nfs6CarMeshController(car, [], skins).skin).toBe('skin00');
    paint.name = 'other';
    expect(new Nfs6CarMeshController(new Group().add(mesh('hp_0_X', 0, 0, 0, paint)), [], skins).skin).toBeNull();
  });

  it('keeps the materials of an export without the game shaders', () => {
    const hood = car.getObjectByName('hp_4_ALPHA_OPAQUE_HOODShape') as Mesh;
    const controller = new Nfs6CarMeshController(car, [], []);
    expect(controller.hasGameShading).toBeFalse();
    expect(hood.material).toBe(paint);
    hood.userData = { eaglShader: 'paint', eaglBlend: 'opaque' };
    expect(new Nfs6CarMeshController(car, [], []).hasGameShading).toBeTrue();
    expect(hood.material).not.toBe(paint);
  });

  it('spins the wheels while the speed is set every frame, backwards in reverse', () => {
    jasmine.clock().install();
    try {
      const controller = new Nfs6CarMeshController(car, [], []);
      const wheel = car.getObjectByName('hp_6_ALPHA_OPAQUE_RUBBER_Shape')!;
      for (let i = 0; i < 10; i++) {
        controller.speed = 10;
        jasmine.clock().tick(1000 / 60);
      }
      // negative angle rolls forward
      expect(wheel.rotation.x).toBeLessThan(0);
      const forward = wheel.rotation.x;
      controller.speed = -10;
      jasmine.clock().tick(1000 / 60);
      expect(wheel.rotation.x).toBeGreaterThan(forward);
      controller.speed = 0;
      const stopped = wheel.rotation.x;
      jasmine.clock().tick(1000);
      expect(wheel.rotation.x).toBe(stopped);
      controller.dispose();
    } finally {
      jasmine.clock().uninstall();
    }
  });

  it('loads skins from the given folder', () => {
    const skins = [
      { name: 'skin00', label: 'red', texture: 'textures/skins/skin00-skin.png' },
      { name: 'skin01', label: 'black', texture: 'textures/skins/skin01-skin.png' },
    ];
    const controller = new Nfs6CarMeshController(car, [], skins, null, null, 'https://cdn/cars/murcie/');
    const load = spyOn((controller as any).textureLoader, 'load');
    controller.skin = 'skin01';
    expect(controller.skin).toBe('skin01');
    expect(load.calls.mostRecent().args[0]).toBe('https://cdn/cars/murcie/textures/skins/skin01-skin.png');
  });

  it('takes the shader constants as the exe', () => {
    // D3D lit: 0 when n.h <= 0, the power clamped
    expect(nfs6Lit(-0.2, 5)).toBe(0);
    expect(nfs6Lit(0, 0)).toBe(0);
    expect(nfs6Lit(0.5, 2)).toBeCloseTo(0.25);
    expect(nfs6Lit(0.99, 1000)).toBeCloseTo(Math.pow(0.99, 127.9961));
    // specular_red..blue / 255 + sun intensity / 255 * sun color / 255, at most 1
    expect(nfs6PaintSpecular({ specular_red: 255, specular_green: 51, specular_blue: 0 }, [255, 255, 255])).toEqual([
      1, 0.2, 0,
    ]);
    const paint = nfs6PaintSpecular(
      { specular_red: 220, specular_green: 100, specular_blue: 0, specular_sun_intensity: 51 },
      [255, 0, 255],
    );
    expect(paint[0]).toBe(1);
    expect(paint[1]).toBeCloseTo(100 / 255);
    expect(paint[2]).toBeCloseTo(0.2);
    expect(nfs6PaintSpecular(null, [255, 255, 255])).toEqual([0, 0, 0]);
    // the light level makes the whole car darker, down to 0.4
    expect(nfs6Brightness(0.1)).toBe(0.4);
    expect(nfs6Brightness(0.7)).toBe(0.7);
    // hot spot: towards white by the light level + 0.2, traffic towards black
    expect(nfs6HotSpecular([0.5, 0, 1], 1, false)).toEqual([1, 1, 1]);
    expect(nfs6HotSpecular([0.5, 0, 1], 1, true)).toEqual([0, 0, 0]);
    expect(nfs6HotSpecular([0.5, 0, 1], 0.2, false)).toEqual([0.5, 0, 1]);
    nfs6HotSpecular([0.5, 0, 1], 0.4, false).forEach((c, i) => expect(c).toBeCloseTo([0.8, 0.6, 1][i]));
    // ground to sky by the normal's height
    expect(nfs6HemisphereAmbient(1, [200, 100, 255], [0, 0, 0])).toEqual([200 / 255, 100 / 255, 1]);
    expect(nfs6HemisphereAmbient(0, [200, 100, 50], [100, 50, 250])).toEqual([150 / 255, 75 / 255, 150 / 255]);
    // the environment map normal bends with the position, the sphere map is read mirrored in x
    expect(nfs6BentNormal([0, 0, 1], [0, 0, 0])).toEqual([0, 0, 1]);
    nfs6BentNormal([0, 0, 1], [0, 2.5, 0]).forEach((c, i) => expect(c).toBeCloseTo([0, Math.SQRT1_2, Math.SQRT1_2][i]));
    expect(nfs6SphereMapUv([0, 0, 1])).toEqual([0.5, 0.5]);
    nfs6SphereMapUv([1, 0, 0]).forEach((c, i) => expect(c).toBeCloseTo([0.075, 0.5][i]));
    nfs6SphereMapUv([0, 1, 0]).forEach((c, i) => expect(c).toBeCloseTo([0.5, 0.075][i]));
    expect(nfs6TrackToWorld([1, 2, 3])).toEqual([1, 3, 2]);
    expect(nfs6CarBlend('glass', 'hp_7_ALPHA_ADD_LENSLShape')).toBe('add');
    expect(nfs6CarBlend('glass', 'hp_9_ALPHA_TRANS_WINShape')).toBe('trans');
    expect(nfs6CarBlend('paint', 'hp_9_ALPHA_TRANS_WINShape')).toBe('opaque');
  });

  it('draws pixels as the ps.1.1 pixel shaders', () => {
    // texture * ambient + reflection mask * (environment + specular), times the brightness, every step clamped
    const pixel = nfs6PixelColor([0.5, 0.25, 1, 0.5], [0.2, 0.4, 1], [0.8, 0.8, 0.8, 1], [0.6, 0, 0, 0.5], false);
    [0.4, 0.2, 0.5, 1].forEach((c, i) => expect(pixel[i]).toBeCloseTo(c));
    // glass: the vertex alpha
    expect(nfs6PixelColor([1, 1, 1, 0], [1, 1, 1], [0, 0, 0, 0.47], [1, 1, 1, 1], true)).toEqual([0, 0, 0, 0.47]);
  });

  it('gives every mesh the material of its microcode and blend', () => {
    const skin = new MeshBasicMaterial({ map: new Texture() });
    skin.name = 'skin';
    const model = new Group();
    const meshes = ['hp_1_ALPHA_OPAQUE_HOODShape', 'hp_2_ALPHA_OPAQUE_FBShape', 'hp_7_ALPHA_ADD_LENSLShape'].map(name =>
      mesh(name, 0, 0, 0, skin),
    );
    const window = mesh('hp_9_ALPHA_TRANS_WINShape', 0, 0, 0, skin);
    window.userData = { eaglShader: 'glass', eaglBlend: 'trans', eaglVertexAlpha: 0.5 };
    model.add(...meshes, window);
    const controller = new Nfs6CarMeshController(model, [], [], null, {
      hp_7_ALPHA_ADD_LENSLShape: { eaglShader: 'glass', eaglBlend: 'add' },
    });
    const [hood, bumper, lens] = meshes.map(m => m.material as MeshBasicMaterial);
    // paint (no properties: the default) shared, a copy of the texture's material
    expect(hood).toBe(bumper);
    expect(hood).not.toBe(skin);
    expect(hood.map).toBe(skin.map);
    expect(hood.transparent).toBeFalse();
    expect(hood.depthWrite).toBeTrue();
    expect(hood.alphaTest).toBe(0);
    expect(hood.customProgramCacheKey()).toContain('eagl-vehicle-paint');
    expect(lens.blending).toBe(AdditiveBlending);
    expect(lens.depthWrite).toBeFalse();
    expect(lens.customProgramCacheKey()).toContain('eagl-vehicle-glass');
    const glass = window.material as MeshBasicMaterial;
    expect(glass.blending).toBe(NormalBlending);
    expect(glass.transparent).toBeTrue();
    expect(window.renderOrder).toBe(1);
    expect(meshes[2].renderOrder).toBe(2);
    expect(meshes[0].renderOrder).toBe(0);
    controller.dispose();
  });

  it('draws the paint in the shader as the exe', () => {
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
    // texture: color and the reflection mask in alpha, stored values (no color space)
    const t0: [number, number, number, number] = [200, 60, 20, 128];
    const texture = new DataTexture(new Uint8Array(t0), 1, 1);
    texture.needsUpdate = true;
    const skin = new MeshBasicMaterial({ map: texture });
    skin.name = 'skin';
    // a tiny plane at the car's origin: the environment map normal is the normal
    const plane = new Mesh(new PlaneGeometry(0.001, 0.001), skin);
    plane.name = 'hp_1_ALPHA_OPAQUE_HOODShape';
    plane.userData = { eaglShader: 'paint', eaglBlend: 'opaque' };
    const normal = new Vector3(0.3, -0.4, 0.8).normalize();
    const normals = new Float32Array(4 * 3).map((_, i) => normal.getComponent(i % 3));
    plane.geometry.setAttribute('normal', new BufferAttribute(normals, 3));
    const car = new Group().add(plane);
    const scene = new Scene().add(car);
    // 2 x 2 environment map, the first row on top (flipY false, as D3D)
    const texels = [
      [250, 30, 70, 255],
      [20, 200, 90, 255],
      [100, 100, 255, 255],
      [180, 140, 10, 255],
    ];
    const env = new DataTexture(new Uint8Array(texels.flat()), 2, 2);
    env.magFilter = NearestFilter;
    env.minFilter = NearestFilter;
    env.needsUpdate = true;
    const location: Nfs6Location = {
      name: 'Test',
      ambient_sky: [200, 180, 160],
      ambient_ground: [40, 50, 60],
      sun: [255, 255, 255],
      sun_position: [300, 900, -400],
    };
    const lighting: Nfs6CarLighting = { vehicle_type: 'primary', specular_hotspot_exponent: 55, locations: [location] };
    const specular = { specular_red: 120, specular_green: 60, specular_blue: 30, specular_paint_exponent: 5 };
    const controller = new Nfs6CarMeshController(
      car,
      [],
      [{ name: 'skin00', label: 'red', texture: 'textures/skins/skin00-skin.png', specular }],
      lighting,
    );
    controller.environmentMap = env;
    controller.lightLevel = 0.7;
    const camera = new Vector3(3, -5, 2);
    // the view: well inside the plane
    const view = new OrthographicCamera(-0.0001, 0.0001, 0.0001, -0.0001, -100, 100);
    view.position.copy(camera);
    view.lookAt(0, 0, 0);
    view.updateMatrixWorld();
    renderer.render(scene, view);
    const pixel = new Uint8Array(4);
    const gl = renderer.getContext();
    gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, pixel);
    // the same per vertex in the world: x, y, z up
    const sun = new Vector3(...nfs6TrackToWorld(location.sun_position));
    const h = camera.clone().normalize().add(sun.clone().normalize()).normalize();
    const nh = normal.dot(h);
    const paint = nfs6PaintSpecular(specular, location.sun);
    const hot = nfs6HotSpecular(paint, 0.7, false);
    const d1 = [0, 1, 2].map(i => Math.min(1, paint[i] * nfs6Lit(nh, 5) + hot[i] * nfs6Lit(nh, 55)));
    const d0 = nfs6HemisphereAmbient(normal.z, location.ambient_sky, location.ambient_ground);
    const viewNormal = normal.clone().transformDirection(view.matrixWorldInverse);
    const [u, v] = nfs6SphereMapUv([viewNormal.x, viewNormal.y, viewNormal.z]);
    const t1 = texels[Math.floor(v * 2) * 2 + Math.floor(u * 2)].slice(0, 3).map(c => c / 255);
    const expected = nfs6PixelColor(
      t0.map(c => c / 255) as [number, number, number, number],
      t1 as [number, number, number],
      [...d0, 1],
      [d1[0], d1[1], d1[2], 0.7],
      false,
    );
    Array.from(pixel.slice(0, 3)).forEach((c, i) => expect(Math.abs(c - expected[i] * 255)).toBeLessThanOrEqual(2));
    controller.dispose();
    renderer.dispose();
  });

  it("lights and reflects the scene's sky", () => {
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
    const t0: [number, number, number, number] = [200, 60, 20, 128];
    const texture = new DataTexture(new Uint8Array(t0), 1, 1);
    texture.needsUpdate = true;
    const skin = new MeshBasicMaterial({ map: texture });
    skin.name = 'skin';
    // facing up: the ambient is the sky's
    const plane = new Mesh(new PlaneGeometry(0.001, 0.001), skin);
    plane.name = 'hp_1_ALPHA_OPAQUE_HOODShape';
    plane.userData = { eaglShader: 'paint', eaglBlend: 'opaque' };
    const scene = new Scene().add(plane);
    const color = [60, 120, 240];
    const sky = new CubeTexture(new Array(6).fill(0).map(() => pixelCanvas(color)));
    sky.colorSpace = SRGBColorSpace;
    sky.generateMipmaps = false;
    sky.needsUpdate = true;
    scene.background = sky;
    // the sun's color is the paint's specular color (specular_sun_intensity 255), traffic: no hot spot
    const specular = { specular_sun_intensity: 255, specular_paint_exponent: 1 };
    const controller = new Nfs6CarMeshController(
      plane,
      [],
      [{ name: 'skin00', label: 'red', texture: 'textures/skins/skin00-skin.png', specular }],
      { vehicle_type: 'traffic' },
    );
    const sun = new Vector3(0.6, 0, 0.8);
    controller.sceneLighting = { direction: [sun.x, sun.y, sun.z], color: [0.5, 0.5, 0.5] };
    controller.sceneReflection = true;
    const view = new OrthographicCamera(-0.0001, 0.0001, 0.0001, -0.0001, -100, 100);
    view.position.set(0, 0, 5);
    view.lookAt(0, 0, 0);
    renderer.render(scene, view);
    const pixel = new Uint8Array(4);
    const gl = renderer.getContext();
    gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, pixel);
    const nh = new Vector3(0, 0, 1).dot(new Vector3(0, 0, 1).add(sun).normalize());
    const s = 0.5 * nfs6Lit(nh, 1);
    const sky01 = color.map(c => c / 255) as [number, number, number];
    const expected = nfs6PixelColor(
      t0.map(c => c / 255) as [number, number, number, number],
      sky01,
      [...sky01, 1],
      [s, s, s, 1],
      false,
    );
    Array.from(pixel.slice(0, 3)).forEach((c, i) => expect(Math.abs(c - expected[i] * 255)).toBeLessThanOrEqual(3));
    controller.dispose();
    renderer.dispose();
  });

  it('draws the glass with its vertex colors', () => {
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
    const t0: [number, number, number, number] = [180, 200, 220, 0];
    const texture = new DataTexture(new Uint8Array(t0), 1, 1);
    texture.needsUpdate = true;
    const plane = new Mesh(new PlaneGeometry(0.001, 0.001), new MeshBasicMaterial({ map: texture }));
    plane.name = 'hp_9_ALPHA_TRANS_WINShape';
    // a GLB's COLOR_0: the stored values, with alpha
    const d0: [number, number, number, number] = [0.5, 0.25, 1, 0.6];
    plane.geometry.setAttribute(
      'color',
      new BufferAttribute(
        new Float32Array(16).map((_, i) => d0[i % 4]),
        4,
      ),
    );
    plane.userData = { eaglShader: 'glass', eaglBlend: 'trans' };
    const scene = new Scene().add(plane);
    // the reflection mask is 0: no environment, no specular
    const controller = new Nfs6CarMeshController(plane, [], []);
    const view = new OrthographicCamera(-0.0001, 0.0001, 0.0001, -0.0001, -100, 100);
    view.position.set(0, 0, 5);
    view.lookAt(0, 0, 0);
    renderer.render(scene, view);
    const pixel = new Uint8Array(4);
    const gl = renderer.getContext();
    gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, pixel);
    const expected = nfs6PixelColor(
      t0.map(c => c / 255) as [number, number, number, number],
      [0, 0, 0],
      d0,
      [0, 0, 0, 1],
      true,
    );
    // blended over black: source alpha, inverse source alpha
    Array.from(pixel.slice(0, 3)).forEach((c, i) =>
      expect(Math.abs(c - expected[i] * expected[3] * 255)).toBeLessThanOrEqual(2),
    );
    controller.dispose();
    renderer.dispose();
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
