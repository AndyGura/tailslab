import { BufferAttribute, BufferGeometry, Group, Mesh, MeshBasicMaterial, Object3D, Texture, Vector3 } from 'three';
import {
  FCE4_STEERING_WHEEL_RATIO,
  FCE4_TRANSLUCENT_ALPHA,
  fce4PartOf,
  fce4WindowOf,
} from '../../../../../nfs-three-lib/fce4-car-parts';
import { FceCarMeshController } from '../../../../../nfs-three-lib/fce-car-mesh-controller';

/** A mesh of triangles (non-indexed, as three.js's OBJ loader makes them) */
function mesh(name: string, positions: number[], material = new MeshBasicMaterial()): Mesh {
  const geometry = new BufferGeometry();
  geometry.setAttribute('position', new BufferAttribute(Float32Array.from(positions), 3));
  const result = new Mesh(geometry, material);
  result.name = name;
  return result;
}

const TRIANGLE = [0, 0, 0, 1, 0, 0, 0, 1, 0];

/** The position of a mesh's vertex in the car's space */
function vertex(car: Object3D, m: Mesh, i: number): Vector3 {
  car.updateMatrixWorld(true);
  const p = new Vector3().fromBufferAttribute(m.geometry.getAttribute('position') as BufferAttribute, i);
  return p.applyMatrix4(m.matrixWorld).applyMatrix4(car.matrixWorld.clone().invert());
}

/** Whether a mesh is drawn: it and every parent up to the car visible */
function drawn(car: Object3D, m: Object3D): boolean {
  for (let o: Object3D | null = m; o && o !== car; o = o.parent) {
    if (!o.visible) {
      return false;
    }
  }
  return true;
}

function controller(car: Object3D, options = {}, dummies: { name: string; position: [number, number, number] }[] = []) {
  return new FceCarMeshController(car, 4, dummies, [], () => null, options);
}

describe('Fce4CarParts', () => {
  it('reads the part and the window class of a mesh name', () => {
    expect(fce4PartOf('hp_9_OS__car00_damaged')).toEqual({ key: 'hp_9_OS', name: 'OS' });
    expect(fce4PartOf('mp_5_MB__car00_translucent_window_front')).toEqual({ key: 'mp_5_MB', name: 'MB' });
    expect(fce4PartOf('part_1')).toBeNull();
    expect(fce4WindowOf('hp_4_HB__car00_translucent_window_front_breakaway')).toEqual({ sides: 1, breaksAway: true });
    expect(fce4WindowOf('hp_4_HB__car00_window_left_right')).toEqual({ sides: 2 | 8, breaksAway: false });
    expect(fce4WindowOf('hp_4_HB__car00_window_damaged')).toEqual({ sides: 0, breaksAway: false });
    expect(fce4WindowOf('hp_4_HB__car00_translucent')).toBeNull();
  });

  it('shows the parts by the car state through groups, leaving the meshes visible', () => {
    const car = new Group();
    const meshes = [
      'hp_0_HB__car00',
      'hp_1_OL__car00',
      'hp_2_ODL__car00',
      'hp_3_OT__car00',
      'hp_4_OD__car00',
      'hp_5_OH__car00',
      'hp_6_OND__car00',
      'hp_7_OLM__car00',
    ].map(name => mesh(name, TRIANGLE));
    car.add(...meshes);
    const c = controller(car);
    const parts = c.parts!;
    const shown = () => meshes.map(m => drawn(car, m));
    // headlights off, roof closed, driver in the car
    expect(shown()).toEqual([true, false, false, true, true, true, false, true]);
    parts.headlights = true;
    parts.roofClosed = false;
    parts.driverInCar = false;
    expect(shown()).toEqual([true, true, true, false, false, false, true, true]);
    expect(meshes.every(m => m.visible)).toBeTrue();
    expect(parts.has('OL')).toBeTrue();
    expect(parts.has('OS')).toBeFalse();
    c.dispose();
  });

  it('turns the spoiler about its part position, the rear edge up', () => {
    const car = new Group();
    // a vertex 1 m behind the pivot
    const spoiler = mesh('hp_9_OS__car00', [0, -1, 1, 0, 0, 1, 1, 0, 1]);
    car.add(spoiler);
    const c = controller(car, { partPositions: { hp_9_OS: [0, 0, 1] } });
    c.parts!.spoilerAngle = Math.PI / 2;
    const rear = vertex(car, spoiler, 0);
    expect(rear.y).toBeCloseTo(0, 6);
    expect(rear.z).toBeCloseTo(2, 6);
    expect(vertex(car, spoiler, 1).z).toBeCloseTo(1, 6);
    c.dispose();
  });

  it("turns the steering wheel's vertices with the front wheels, the head's about the up axis", () => {
    const car = new Group();
    const driver = mesh('hp_4_OD__car00', [1, 2, 0, 0, 2, 1, 0, 0, 0]);
    // the first two vertices turn
    driver.geometry.setAttribute('_fce_turns', new BufferAttribute(Float32Array.from([1, 1, 0]), 1));
    const head = mesh('hp_5_OH__car00', [1, 0, 1, 0, 0, 1, 0, 1, 1]);
    car.add(driver, head);
    const c = controller(car, { partPositions: { hp_4_OD: [0, 2, 0], hp_5_OH: [0, 0, 1] } });
    const shared = driver.geometry;
    c.steeringAngle = 0.1;
    const angle = 0.1 * FCE4_STEERING_WHEEL_RATIO;
    // turning left: the wheel's top (+z) goes left (-x)
    const top = vertex(car, driver, 1);
    expect(top.x).toBeCloseTo(-Math.sin(angle), 6);
    expect(top.z).toBeCloseTo(Math.cos(angle), 6);
    expect(vertex(car, driver, 2).length()).toBeCloseTo(0, 9);
    // the geometry is the car's own: the app may share the loaded one
    expect(driver.geometry).not.toBe(shared);
    expect(shared.getAttribute('position').getX(0)).toBe(1);
    // positive head yaw: to the left (counter-clockwise from above)
    c.parts!.driverHeadYaw = Math.PI / 2;
    const ahead = vertex(car, head, 2);
    expect(ahead.x).toBeCloseTo(-1, 6);
    expect(ahead.y).toBeCloseTo(0, 6);
    c.steeringAngle = 0;
    expect(
      vertex(car, driver, 1)
        .toArray()
        .map(x => +x.toFixed(6)),
    ).toEqual([0, 2, 1]);
    c.dispose();
  });

  it('leans the body but not the wheels, lifted by the half size', () => {
    const car = new Group();
    const body = mesh('hp_0_HB__car00', [0, 2, 0, 1, 2, 0, 0, 2, 1]);
    const wheel = mesh('hp_10_HLFW__car00', TRIANGLE);
    car.add(body, wheel);
    const c = controller(car, { halfSize: { x: 1, y: 0.6, z: 2.2 } });
    c.parts!.bodyPitch = 0.1;
    // nose down
    expect(vertex(car, body, 0).z).toBeLessThan(c.parts!.body.position.z);
    expect(c.parts!.body.position.z).toBeCloseTo(Math.sin(0.1) * 2.2, 6);
    c.parts!.bodyRoll = 0.3;
    expect(c.parts!.body.position.z).toBeCloseTo(Math.max(Math.sin(0.3), Math.sin(0.1) * 2.2), 6);
    expect(wheel.parent!.parent).toBe(car);
    c.parts!.bodyLift = false;
    expect(c.parts!.body.position.z).toBe(0);
    c.dispose();
  });

  it('damages the vertices within the radius by the amount (OBJ: the damaged copy)', () => {
    const car = new Group();
    const body = mesh('hp_0_HB__car00', [0, 2, 0, 1, 2, 0, 0, -2, 0]);
    const damaged = mesh('hp_0_HB__car00_damaged', [0, 1, 0, 1, 1, 0, 0, -1, 0]);
    car.add(body, damaged);
    const c = controller(car);
    expect(damaged.parent).toBeNull();
    const result = c.parts!.hit({ x: 0, y: 2.5, z: 0 }, 0.5, 1.5);
    expect(result.damaged).toBeTrue();
    expect(vertex(car, body, 0).y).toBeCloseTo(1.5, 6);
    expect(vertex(car, body, 1).y).toBeCloseTo(1.5, 6);
    expect(vertex(car, body, 2).y).toBeCloseTo(-2, 6);
    // a weaker hit does nothing, a stronger one more
    c.parts!.hit({ x: 0, y: 2.5, z: 0 }, 0.25, 1.5);
    expect(vertex(car, body, 0).y).toBeCloseTo(1.5, 6);
    c.parts!.hit({ x: 0, y: 2.5, z: 0 }, 1, 1.5);
    expect(vertex(car, body, 0).y).toBeCloseTo(1, 6);
    const state = c.parts!.getDamage();
    c.parts!.repair();
    expect(vertex(car, body, 0).y).toBeCloseTo(2, 6);
    c.parts!.setDamage(state);
    expect(vertex(car, body, 0).y).toBeCloseTo(1, 6);
    c.dispose();
  });

  it('damages by the GLB morph target "damaged"', () => {
    const car = new Group();
    const body = mesh('hp_0_HB__car00', [0, 2, 0, 1, 2, 0, 0, -2, 0]);
    body.geometry.morphAttributes['position'] = [
      new BufferAttribute(Float32Array.from([0, -1, 0, 0, -1, 0, 0, 1, 0]), 3),
    ];
    body.geometry.morphTargetsRelative = true;
    body.updateMorphTargets();
    body.morphTargetDictionary = { damaged: 0 };
    car.add(body);
    const c = controller(car);
    c.parts!.hit({ x: 0, y: -2.5, z: 0 }, 1, 1);
    expect(vertex(car, body, 2).y).toBeCloseTo(-1, 6);
    expect(vertex(car, body, 0).y).toBeCloseTo(2, 6);
    c.dispose();
  });

  it('cracks the windows of the hit side and breaks the glass away above half damage', () => {
    const car = new Group();
    const glass = new Texture();
    // two triangles: the first one is hit
    const front = mesh(
      'hp_0_HB__car00_translucent_window_front',
      [0, 2, 1, 0.1, 2, 1, 0, 2, 1.1, 5, 0, 1, 5.1, 0, 1, 5, 0, 1.1],
    );
    const breakaway = mesh('hp_0_HB__car00_translucent_window_front_breakaway', [5, 5, 1, 5.1, 5, 1, 5, 5, 1.1]);
    const side = mesh('hp_0_HB__car00_translucent_window_left', [-5, 0, 1, -5, 0.1, 1, -5, 0, 1.1]);
    car.add(front, breakaway, side);
    const c = controller(car, { brokenGlassTexture: glass });
    expect((front.material as MeshBasicMaterial).opacity).toBeCloseTo(FCE4_TRANSLUCENT_ALPHA, 6);
    const weak = c.parts!.hit({ x: 0, y: 2, z: 1 }, 0.4, 0.5);
    // the front side cracks: both front triangles, the break away one too; the left side does not
    expect(weak.windowsCracked).toBe(3);
    expect(weak.windowsBrokenAway).toBe(0);
    expect(front.geometry.getIndex()!.count).toBe(0);
    const frontGlass = front.children[0] as Mesh;
    expect((frontGlass.material as MeshBasicMaterial).map).toBe(glass);
    expect(frontGlass.geometry.getAttribute('position').count).toBe(6);
    expect(Array.from(frontGlass.geometry.getAttribute('uv').array).slice(0, 6)).toEqual([0, 0, 0, 1, 1, 1]);
    expect(side.geometry.getIndex()).toBeNull();
    const strong = c.parts!.hit({ x: 0, y: 2, z: 1 }, 0.8, 0.5);
    expect(strong.windowsBrokenAway).toBe(1);
    expect(breakaway.geometry.getIndex()!.count).toBe(0);
    expect((breakaway.children[0] as Mesh).visible).toBeFalse();
    c.parts!.repair();
    expect(front.geometry.getIndex()!.count).toBe(6);
    expect(frontGlass.visible).toBeFalse();
    c.dispose();
  });

  it('breaks the mirrors within the radius, the lights and the license plate above a quarter', () => {
    const car = new Group();
    const body = mesh('hp_0_HB__car00', TRIANGLE);
    const mirror = mesh('hp_8_OLM__car00', TRIANGLE);
    car.add(body, mirror);
    const dummies: { name: string; position: [number, number, number] }[] = [
      { name: 'HWYN550', position: [0.6, 2, 0] },
      { name: ':LICENSE', position: [0, 2.2, 0] },
      { name: 'SBNO5', position: [0, 2, 1] },
      { name: 'TRYN550', position: [0.6, -2, 0] },
    ];
    const c = controller(car, { partPositions: { hp_8_OLM: [-1, 0.5, 0.8] } }, dummies);
    const weak = c.parts!.hit({ x: 0, y: 2, z: 0.5 }, 0.2, 1.5);
    expect(weak.dummiesBroken).toEqual([]);
    const strong = c.parts!.hit({ x: 0, y: 2, z: 0.5 }, 0.5, 1.5);
    // the license plate first, never the siren, nothing out of the radius
    expect(strong.dummiesBroken).toEqual([1, 0]);
    expect([...c.parts!.brokenDummies]).toEqual([1, 0]);
    const lights = body.children.find(o => o instanceof Group)!;
    expect(lights.children.find(o => o.name === 'HWYN550')!.visible).toBeFalse();
    expect(lights.children.find(o => o.name === 'TRYN550')!.visible).toBeTrue();
    expect(strong.mirrorsBroken).toEqual([]);
    const mirrorHit = c.parts!.hit({ x: -1, y: 0.4, z: 0.8 }, 0.1, 0.3);
    expect(mirrorHit.mirrorsBroken).toEqual(['OLM']);
    expect(drawn(car, mirror)).toBeFalse();
    c.parts!.repair();
    expect(drawn(car, mirror)).toBeTrue();
    expect(lights.children.find(o => o.name === 'HWYN550')!.visible).toBeTrue();
    c.dispose();
  });

  it('tilts damaged wheels, hides wheels with their brake, stops sliding ones', () => {
    const car = new Group();
    const names = [
      'hp_10_HLFW__car00',
      'hp_11_HRFW__car00',
      'hp_12_HLRW__car00',
      'hp_13_HRRW__car00',
      'hp_18_OLB__car00',
    ];
    const meshes = names.map(name => mesh(name, TRIANGLE));
    car.add(...meshes);
    const now = spyOn(performance, 'now').and.returnValue(1000);
    const c = controller(car);
    c.setWheelDamage('frontLeft', 1);
    expect(meshes[0].rotation.y).toBeCloseTo(-0.025 * 2 * Math.PI, 6);
    expect(meshes[1].rotation.y).toBeCloseTo(0, 9);
    c.setWheelHidden('frontLeft', true);
    expect(meshes.map(m => drawn(car, m))).toEqual([false, true, true, true, false]);
    expect(meshes.every(m => m.visible)).toBeTrue();
    c.setWheelHidden('frontLeft', false);
    expect(drawn(car, meshes[0])).toBeTrue();
    c.speed = 6;
    c.frontSliding = true;
    now.and.returnValue(1000 + 10 * (1000 / 64));
    (c as any).spinWheels();
    expect(meshes[1].rotation.x).toBeCloseTo(0, 9);
    expect(meshes[3].rotation.x).toBeCloseTo(-Math.PI, 6);
    c.dispose();
  });
});
