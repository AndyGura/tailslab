import { BoxGeometry, BufferAttribute, Group, Mesh, MeshBasicMaterial, Scene, Texture, Vector3 } from 'three';
import {
  Nfs5CarArticle,
  Nfs5CarData,
  Nfs5CarMaterial,
  Nfs5CarMeshController,
  nfs5Bands,
  nfs5HitZones,
  nfs5LayerDrawn,
  nfs5Lights,
  nfs5PaintBand,
  nfs5RaceSlots,
  nfs5RenderCaps,
  nfs5SkySpecularAlpha,
  nfs5SpecularBlend,
  nfs5SpecularLevel,
  nfs5SpecularUv,
  nfs5ZoneDamageAfterHit,
  NFS5_DRAW_BODY,
  NFS5_DRAW_DAMAGE,
  NFS5_DRAW_DRIVER,
  NFS5_DRAW_STEERING_WHEEL,
  NFS5_DRAW_WHEELS,
} from '../../../../../nfs-three-lib/nfs5-car-mesh-controller';

function mesh(name: string, x: number, y: number, z: number, size = 0.6): Mesh {
  // OBJ meshes: a vertex per face corner
  const geometry = new BoxGeometry(size, size, size).toNonIndexed();
  geometry.translate(x, y, z);
  const result = new Mesh(geometry, new MeshBasicMaterial());
  result.name = name;
  return result;
}

// a translation in the CRP's axes (x left, y up, z backward) as the export's 16 floats (row vectors)
const at = (x: number, y: number, z: number) => [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, x, y, z, 1];

function article(index: number, name: string, props: Partial<Nfs5CarArticle>): Nfs5CarArticle {
  return { index, name, slot: 0, value: 0, drawFlags: NFS5_DRAW_BODY, lods: [1], transforms: {}, ...props };
}

const CAR: Nfs5CarData = {
  formatVersion: 1,
  articles: [
    article(0, 'Body', { slot: 1, drawFlags: NFS5_DRAW_BODY | NFS5_DRAW_DAMAGE, lods: [1, 2], cockpit: true }),
    article(1, 'Body1', { slot: 1, value: 1 }),
    // the front left wheel at CRP (0.7, 0.3, -1.2): model (0.7, -1.2, 0.3)
    article(2, 'WheelFront', {
      slot: 13,
      drawFlags: NFS5_DRAW_WHEELS,
      wheel: 0,
      pivot: 1,
      transforms: { 1: at(0.7, 0.3, -1.2) },
    }),
    article(3, 'Steer', {
      slot: 46,
      drawFlags: NFS5_DRAW_STEERING_WHEEL,
      pivot: 5,
      cockpit: true,
      transforms: { 1: at(0.4, 0.7, -0.2) },
    }),
    article(4, 'DriverBody2', { slot: 9, value: 2, drawFlags: NFS5_DRAW_DRIVER, animation: 6, frames: 2 }),
    article(5, 'LeftHand1', { slot: 56, value: 1, drawFlags: NFS5_DRAW_DRIVER, insideOnly: true, cockpit: true }),
    article(6, 'CabrioUp', { slot: 41, value: 1 }),
    article(7, 'CabrioDown', { slot: 41, value: 2 }),
  ],
  styles: [
    { name: 'Coupe', slots: [], stripe: false },
    {
      name: 'Cabrio',
      slots: [
        [37, 1],
        [1, 1],
      ],
      stripe: true,
    },
  ],
  header: {
    driverCamPos: [0, 0, 0],
    driverCamRot: [0, 0, 0],
    doorAxis: [0, 1, 0],
    noRoof: false,
    hoodExtent: 0.15,
    trunkExtent: -0.15,
    headlightExtent: 0,
    moveSpoilerExtent: 0,
  },
  damageZones: {},
  pages: [],
  packages: [],
};

function car(): { root: Group; zones: { [name: string]: number[] } } {
  const root = new Group();
  const body = mesh('Body_a0_LOD1_ai0_page_0', 0, 0, 0.5, 1);
  const damaged = mesh('Body_a0_LOD1_ai0_page_0_damaged', 0, 0, 0.5, 1);
  // the damaged copy: every vertex 0.1 lower
  damaged.geometry.translate(0, 0, -0.1);
  root.add(
    body,
    damaged,
    mesh('Body_a0_LOD2_ai0_page_0', 0, 0, 0.5, 1),
    mesh('Body1_a1_LOD1_ai0_page_0', 0, 0, 0.5, 1),
    mesh('WheelFront_a2_LOD1_ai0_page_3_alpha', 0.7, -1.2, 0.3),
    mesh('Steer_a3_LOD1_ai0_page_2', 0.4, -0.2, 0.7, 0.3),
    mesh('DriverBody2_a4_LOD1_ai0_page_9', 0.4, 0, 0.8, 0.4),
    mesh('DriverBody2_a4_LOD1_ai1_page_9', 0.4, 0.2, 0.8, 0.4),
    mesh('LeftHand1_a5_LOD1_ai0_page_9', 0.4, -0.2, 0.7, 0.1),
    mesh('CabrioUp_a6_LOD1_ai0_page_0', 0, 0, 1.2),
    mesh('CabrioDown_a7_LOD1_ai0_page_0', 0, 0.5, 1.0),
  );
  const corners = body.geometry.getAttribute('position').count;
  // the first half of the body's vertices in zone 1 (front), the rest in zone 5 (rear)
  const zones = { [body.name]: Array.from({ length: corners }, (_, i) => (i < corners / 2 ? 1 : 5)) };
  return { root, zones };
}

const shown = (root: Group) =>
  root.children
    .filter(x => x.visible && !x.name.includes('__glare'))
    .map(x => x.name)
    .sort();

describe('Nfs5CarMeshController', () => {
  it('parses mesh names, exported by CrpGeometrySerializer and renamed by three.js', () => {
    expect(Nfs5CarMeshController.parseMeshName('Body1_a7_LOD2_ai0_page_4_alpha_damaged')).toEqual({
      article: 'Body1',
      articleIndex: 7,
      lod: 2,
      animationFrame: 0,
      isDamaged: true,
    });
    expect(Nfs5CarMeshController.parseMeshName('RightArm1_a64_LOD1_ai12')?.animationFrame).toBe(12);
    // older names without the article index
    expect(Nfs5CarMeshController.parseMeshName('DoorIn_LOD2_ai0001')?.articleIndex).toBeNull();
    expect(Nfs5CarMeshController.parseMeshName('DoorIn_LOD2_ai0.001')?.animationFrame).toBe(0);
    // trailing space of article name, replaced by GLTFLoader
    expect(Nfs5CarMeshController.parseMeshName('Light2__a12_LOD1_ai0_page_0')?.article).toBe('Light2');
    expect(Nfs5CarMeshController.parseMeshName('shadow')).toBeNull();
  });

  it('guesses a default exterior without the model data', () => {
    const names = [
      'Body_LOD1_ai0_page_0',
      'Body_LOD2_ai0_page_0',
      'Body_LOD1_ai0_page_0_damaged',
      'Body1_LOD1_ai0_page_0',
      'Light2_LOD1_ai0_page_0',
      'Light2a_LOD1_ai0_page_0',
      'SpoilerDown_LOD1_ai0_page_0',
      'SpoilerUp_LOD1_ai0_page_0',
      'DriverBody1_LOD1_ai0',
      'WheelFront_LOD1_ai0_page_3_alpha',
    ];
    const isDefault = Nfs5CarMeshController.defaultExteriorFilter(names);
    expect(names.filter(isDefault)).toEqual([
      'Body_LOD1_ai0_page_0',
      'Light2_LOD1_ai0_page_0',
      'SpoilerDown_LOD1_ai0_page_0',
      'WheelFront_LOD1_ai0_page_3_alpha',
    ]);
  });

  it('finds wheels and turns the car to Y forward without the model data', () => {
    const root = new Group();
    root.add(mesh('WheelFront_LOD1_ai0_page_3_alpha', -0.7, -1.2, 0.3), mesh('Body_LOD1_ai0_page_0', 0, 0, 0.5));
    const controller = new Nfs5CarMeshController(root, true);
    expect(controller.hasModelData).toBeFalse();
    expect(controller.hasWheels).toBeTrue();
    const wheel = root.getObjectByName('WheelFront_LOD1_ai0_page_3_alpha')!;
    expect(wheel.position.x).toBeCloseTo(0.7);
    expect(wheel.position.y).toBeCloseTo(1.2);
    controller.steeringAngle = 0.3;
    expect(wheel.rotation.z).toBeCloseTo(0.3);
    controller.dispose();
  });

  it('shows the articles of the race geometry configuration', () => {
    const { root } = car();
    const controller = new Nfs5CarMeshController(root, { car: CAR });
    expect(shown(root)).toEqual([
      'Body_a0_LOD1_ai0_page_0',
      'DriverBody2_a4_LOD1_ai0_page_9',
      'Steer_a3_LOD1_ai0_page_2',
      'WheelFront_a2_LOD1_ai0_page_3_alpha',
    ]);
    // the second style: the other body; its convertible top up, or down
    controller.bodyStyle = 1;
    expect(shown(root)).toContain('Body1_a1_LOD1_ai0_page_0');
    expect(shown(root)).toContain('CabrioUp_a6_LOD1_ai0_page_0');
    expect(shown(root)).not.toContain('Body_a0_LOD1_ai0_page_0');
    controller.cabrioDown = true;
    expect(shown(root)).toContain('CabrioDown_a7_LOD1_ai0_page_0');
    expect(shown(root)).not.toContain('CabrioUp_a6_LOD1_ai0_page_0');
    // the parts' configuration over the race's
    controller.setGeometryConfig(Object.assign(new Array(120).fill(-1), { 1: 0 }));
    expect(shown(root)).toContain('Body_a0_LOD1_ai0_page_0');
    // an empty car
    controller.driver = null;
    expect(shown(root)).not.toContain('DriverBody2_a4_LOD1_ai0_page_9');
    controller.dispose();
  });

  it('draws the articles in their draw order, an overlay over the article under it', () => {
    const data: Nfs5CarData = {
      ...CAR,
      articles: [
        article(0, 'Body', { slot: 1, order: 0 }),
        article(1, 'Light1', { slot: 19, order: 2 }),
        article(2, 'Interior', { slot: 24, order: 129 }),
        article(3, 'DecalGauge', { slot: 28, order: 131 }),
      ],
    };
    const root = new Group();
    const body = mesh('Body_a0_LOD1_ai0_page_0', 0, 0, 0.5, 1);
    const light = mesh('Light1_a1_LOD1_ai0_page_0', 0, 0, 0.5, 1);
    light.material = body.material;
    const interior = mesh('Interior_a2_LOD1_ai0_page_2', 0, 0, 0.5, 0.8);
    const gauge = mesh('DecalGauge_a3_LOD1_ai0_page_2', 0, 0, 0.5, 0.8);
    root.add(body, light, interior, gauge);
    const controller = new Nfs5CarMeshController(root, { car: data });
    // a signed byte: the inside (129, 131 = -127, -125) first
    expect([body, light, interior, gauge].map(m => m.renderOrder)).toEqual([0, 2, -127, -125]);
    // the first order keeps its material; the next ones are pulled forward by their rank
    const offset = (m: Mesh) => {
      const material = m.material as MeshBasicMaterial;
      return material.polygonOffset ? material.polygonOffsetFactor : 0;
    };
    expect([body, light, interior, gauge].map(offset)).toEqual([-2, -3, 0, -1]);
    expect(light.material).not.toBe(body.material);
    controller.dispose();
  });

  it('draws the in-car view and the levels of detail as the game does', () => {
    const { root } = car();
    const controller = new Nfs5CarMeshController(root, { car: CAR });
    controller.view = 'cockpit';
    // level 2 of the in-car body articles, the steering wheel of level 1, the hands; no wheels, no driver's body
    expect(shown(root)).toEqual([
      'Body_a0_LOD2_ai0_page_0',
      'LeftHand1_a5_LOD1_ai0_page_9',
      'Steer_a3_LOD1_ai0_page_2',
    ]);
    controller.view = 'outside';
    controller.lod = 1;
    expect(shown(root)).toContain('Body_a0_LOD2_ai0_page_0');
    controller.dispose();
  });

  it('turns the wheels and the steering wheel about their origins', () => {
    const { root } = car();
    const controller = new Nfs5CarMeshController(root, { car: CAR });
    const wheel = root.getObjectByName('WheelFront_a2_LOD1_ai0_page_3_alpha') as Mesh;
    const centre = new Vector3(0.7, -1.2, 0.3);
    controller.steeringAngle = 0.3;
    root.updateMatrixWorld(true);
    // the wheel's centre stays, its front (-Y) turns to the left (+X: the model's x is the left)
    expect(centre.clone().applyMatrix4(wheel.matrixWorld).distanceTo(centre)).toBeLessThan(1e-6);
    const front = new Vector3(0.7, -1.5, 0.3).applyMatrix4(wheel.matrixWorld);
    expect(front.x).toBeGreaterThan(0.7);
    // the steering wheel turns by both front wheels' angles, at most 4.5 / 23 turn
    controller.steeringAngle = 3;
    root.updateMatrixWorld(true);
    const steer = root.getObjectByName('Steer_a3_LOD1_ai0_page_2') as Mesh;
    const rim = new Vector3(0.5, -0.2, 0.7).applyMatrix4(steer.matrixWorld);
    const angle = Math.atan2(rim.z - 0.7, rim.x - 0.4);
    expect(Math.abs(angle)).toBeCloseTo((4.5 / 23) * 2 * Math.PI, 4);
    controller.dispose();
  });

  it('dents the zones of the damage and repairs', () => {
    const { root, zones } = car();
    const controller = new Nfs5CarMeshController(root, { car: CAR, damageZones: zones });
    expect(controller.hasDamage).toBeTrue();
    const body = root.getObjectByName('Body_a0_LOD1_ai0_page_0') as Mesh;
    const before = body.geometry.getAttribute('position');
    const z0 = before.getZ(0);
    const zLast = before.getZ(before.count - 1);
    // a front hit at 60 m/s: damage 30 in zone 1, its vertices 0.6 of the way to the damaged copy
    expect(controller.hit({ x: 0, y: 1, z: 0 }, 60)).toEqual([1]);
    expect(controller.getZoneDamage(1)).toBeCloseTo(30);
    const position = body.geometry.getAttribute('position');
    expect(position.getZ(0)).toBeCloseTo(z0 - 0.06);
    expect(position.getZ(position.count - 1)).toBeCloseTo(zLast);
    controller.setZoneDamage(5, 100);
    expect(position.getZ(position.count - 1)).toBeCloseTo(zLast - 0.1);
    controller.repair();
    expect(position.getZ(0)).toBeCloseTo(z0);
    expect(controller.getDamage().every(d => d === 0)).toBeTrue();
    controller.dispose();
  });

  it('blends the frames of an animation', () => {
    const { root } = car();
    const controller = new Nfs5CarMeshController(root, { car: CAR });
    const driver = root.getObjectByName('DriverBody2_a4_LOD1_ai0_page_9') as Mesh;
    const y0 = driver.geometry.getAttribute('position').getY(0);
    expect(controller.animationFrames(6)).toBe(2);
    controller.setAnimation(6, 0.5);
    expect(driver.geometry.getAttribute('position').getY(0)).toBeCloseTo(y0 + 0.1);
    controller.setAnimation(6, 1);
    expect(driver.geometry.getAttribute('position').getY(0)).toBeCloseTo(y0 + 0.2);
    controller.dispose();
  });

  it('keeps the race rules of slots, lights, hits and paint', () => {
    const slots = nfs5RaceSlots([[37, 1]], { driver: 5 });
    expect([slots[9], slots[37], slots[41], slots[42], slots[43], slots[56]]).toEqual([8, 0, 1, 0, 4, 2]);
    expect(nfs5RaceSlots(null, { cabrioDown: true })[41]).toBe(0);

    const input = {
      headlights: true,
      brake: false,
      reverse: false,
      left: true,
      right: false,
      blink: true,
      popUp: null,
    };
    const lights = nfs5Lights(input, []);
    // tail lights at 0.6, the left indicators blinking, the left rear brake light with them
    expect(lights.on.slice(0, 4)).toEqual([true, true, true, true]);
    expect(lights.intensity[2]).toBeCloseTo(0.6);
    expect([lights.on[4], lights.on[6], lights.on[10], lights.on[11]]).toEqual([true, false, true, true]);
    // a damaged front left breaks its headlight and indicator
    expect(nfs5Lights(input, [31]).on.slice(0, 5)).toEqual([false, true, true, true, false]);

    // pushed backwards: the front; pushed down: the roof too; at 10 or slower: nothing
    expect(nfs5HitZones({ x: 0, y: 0, z: 1 }, 50)).toEqual([1]);
    expect(nfs5HitZones({ x: 0, y: -1, z: 0.3 }, 50)).toEqual([8, 1]);
    expect(nfs5HitZones({ x: 0, y: 0, z: 1 }, 10)).toEqual([]);
    const damage = nfs5ZoneDamageAfterHit([0, 0, 20, 0, 0, 0, 0, 40, 0, 0], 1, 100);
    expect(damage.slice(0, 3)).toEqual([45, 50, 25]);

    expect(nfs5PaintBand(13)).toBe(17);
    expect(nfs5PaintBand(255)).toBeNull();
    const bands = nfs5Bands([0xff0000, 0x00ff00, 0x0000ff, 0x808080], null, true);
    expect([bands[0], bands[6], bands[14]]).toEqual([0xff0000, 0x00ff00, 0x808080]);
  });

  it('keeps the rules of the specular pass', () => {
    // car chrome 0 compiles the groups of caps mask 0 only (the windows), 1 and 2 those of mask 2 too (the body)
    expect([0, 1, 2].map(nfs5RenderCaps)).toEqual([1, 3, 3]);
    const body = { param: 0.5, passes: [2, 4] };
    const window = { param: 1, passes: [0] };
    expect([nfs5LayerDrawn(body, 1), nfs5LayerDrawn(body, 3), nfs5LayerDrawn(window, 1)]).toEqual([false, true, true]);
    expect(nfs5LayerDrawn(null, 3)).toBeFalse();
    // the materials' parameters 0, 0.5, 1 pick SPC1, SPC2, SPC3
    expect([0, 0.04, 0.05, 0.5, 0.94, 0.95, 1].map(nfs5SpecularLevel)).toEqual([0, 0, 1, 1, 1, 2, 2]);
    // facing the camera: the middle; turned up: the bottom half (Direct3D's v); at the silhouette: the edge
    expect(nfs5SpecularUv([0, 0, 1])).toEqual([0.5, 0.5]);
    const up = nfs5SpecularUv([0, Math.SQRT1_2, Math.SQRT1_2]);
    expect(up[0]).toBe(0.5);
    expect(up[1]).toBeGreaterThan(0.75);
    expect(nfs5SpecularUv([1, 0, 0])).toEqual([1, 0.5]);
    // the texel over the car by its alpha, times the light
    const blended = nfs5SpecularBlend([0.2, 0.4, 0.6], [1, 1, 1, 0.5], [0.5, 1, 1]);
    expect(blended.map(x => +x.toFixed(4))).toEqual([0.35, 0.7, 0.8]);
    // the sky: up-facing normals only, level 0 none
    expect(nfs5SkySpecularAlpha(0, 0.9)).toBe(0);
    expect(nfs5SkySpecularAlpha(1, -0.9)).toBe(0);
    expect(nfs5SkySpecularAlpha(1, 0.7)).toBeCloseTo(0.338);
    expect(nfs5SkySpecularAlpha(2, 0.6)).toBeCloseTo((0.153 + 0.357) / 2);
    expect(nfs5SkySpecularAlpha(2, 1)).toBeCloseTo(0.308);
  });

  it('gives the vertices the specular level of their materials and picks the source', () => {
    const { root } = car();
    const body = root.getObjectByName('Body_a0_LOD1_ai0_page_0') as Mesh;
    const count = body.geometry.getAttribute('position').count;
    // the GLB's _NFS5_MATERIAL (normalized bytes): the first half material 1 (a body at 0.5), the rest 2 (none)
    body.geometry.setAttribute(
      '_nfs5_material',
      new BufferAttribute(
        Uint8Array.from({ length: count }, (_, i) => (i < count / 2 ? 1 : 2)),
        1,
        true,
      ),
    );
    const steer = root.getObjectByName('Steer_a3_LOD1_ai0_page_2') as Mesh;
    const material = (index: number, method: string, param: number | null, passes: number[]): Nfs5CarMaterial => ({
      index,
      method,
      page: 0,
      specular: param === null ? null : { param, passes },
      skyMap: null,
    });
    const materials = [
      material(0, 'CarWindow', 1, [0]),
      material(1, 'CarExtEnv', 0.5, [2, 4]),
      material(2, 'CarExt', null, []),
    ];
    const steerCorners = steer.geometry.getAttribute('position').count;
    const c = new Nfs5CarMeshController(root, {
      car: { ...CAR, formatVersion: 2, materials },
      // the OBJ's per corner materials: the window
      faceMaterials: { [steer.name]: new Array(steerCorners).fill(0) },
    });
    expect(c.hasReflections).toBeTrue();
    const levels = (mesh: Mesh) => Array.from(mesh.geometry.getAttribute('nfs5SpecularLevel').array as Float32Array);
    // level + 1, 0 none
    expect(levels(body)[0]).toBe(2);
    expect(levels(body)[count - 1]).toBe(0);
    expect(new Set(levels(steer))).toEqual(new Set([3]));
    // car chrome 0: the windows only
    c.carChrome = 0;
    expect(levels(body)[0]).toBe(0);
    expect(levels(steer)[0]).toBe(3);
    // the game's textures when given, else the scene's sky cube
    const uniforms = (c as any).reflection;
    c.updateReflections(new Scene());
    expect(uniforms.mode.value).toBe(0);
    c.reflectionTextures = [null, new Texture(), null];
    c.updateReflections(null);
    expect(uniforms.mode.value).toBe(1);
    c.reflectionsEnabled = false;
    c.updateReflections(null);
    expect(uniforms.mode.value).toBe(0);
    c.dispose();
  });
});
