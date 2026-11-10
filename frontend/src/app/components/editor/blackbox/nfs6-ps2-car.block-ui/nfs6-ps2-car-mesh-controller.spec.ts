import { BoxGeometry, BufferAttribute, Group, Mesh, MeshBasicMaterial, Texture } from 'three';
import { Nfs6Ps2CarInfo, Nfs6Ps2CarMeshController } from '../../../../../nfs-three-lib/nfs6-ps2-car-mesh-controller';

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
  });

  it('uses the vertex colours of a GLB', () => {
    const body = car.getObjectByName('hp_body__skin') as Mesh;
    const count = body.geometry.getAttribute('position').count;
    body.geometry.setAttribute('color', new BufferAttribute(new Float32Array(count * 4), 4));
    new Nfs6Ps2CarMeshController(car, INFO, [], '');
    expect((body.material as MeshBasicMaterial).vertexColors).toBeTrue();
    expect(((car.getObjectByName('hp_body__headlight') as Mesh).material as MeshBasicMaterial).vertexColors).toBeFalse();
  });
});
