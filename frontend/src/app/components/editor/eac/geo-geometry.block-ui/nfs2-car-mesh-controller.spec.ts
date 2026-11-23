import { BoxGeometry, Group, Mesh, MeshBasicMaterial, PerspectiveCamera, Scene, Texture, WebGLRenderer } from 'three';
import {
  NFS2_CAR_HSVT,
  Nfs2CarMeshController,
  nfs2DrawStateOf,
  nfs2HsvToRgb,
  nfs2PaintOfHsvt,
  nfs2RecolorPaletteEntry,
} from '../../../../../nfs-three-lib/nfs2-car-mesh-controller';

function carMesh(): Group {
  const car = new Group();
  for (const part of [1, 11, 12, 13, 14, 15, 16, 17, 18, 19]) {
    const material = new MeshBasicMaterial({ map: new Texture() });
    const texture = part === 11 ? 'l000' : part % 2 === 0 && part >= 12 ? 'm000' : 'b000';
    material.name = texture;
    const mesh = new Mesh(new BoxGeometry(), material);
    mesh.name = `part_hp_${part}__${texture}`;
    mesh.userData = { geo_part: part, frames: part === 11 ? 2 : part >= 12 && part % 2 === 0 ? 4 : 1 };
    if (part >= 12) {
      // wheels on the right at +x
      mesh.geometry.translate(part === 12 || part === 13 || part === 16 || part === 17 ? 1 : -1, 0, 0);
    }
    car.add(mesh);
  }
  return car;
}

describe('Nfs2CarMeshController', () => {
  it('converts HSV like Color_HsvToRgb', () => {
    expect(nfs2HsvToRgb(0, 0, 210)).toEqual([210, 210, 210]);
    expect(nfs2HsvToRgb(0, 255, 0)).toEqual([0, 0, 0]);
    // pure red / green / blue at full saturation and value
    expect(nfs2HsvToRgb(0, 256, 256)).toEqual([256, 0, 0]);
    expect(NFS2_CAR_HSVT.length).toBe(88);
  });

  it('recolors only the green paint ramp, exactly the paint at the shade knee', () => {
    const paint = nfs2PaintOfHsvt(2);
    expect(nfs2RecolorPaletteEntry(0, 0x80 + paint.mid, 0, paint)).toEqual([...paint.color]);
    expect(nfs2RecolorPaletteEntry(0x56, 0xff, 0, paint)).toBeNull();
    expect(nfs2RecolorPaletteEntry(0, 0x7f, 0, paint)).toBeNull();
    // darker below the knee, toward 4 x the color above it
    const dark = nfs2RecolorPaletteEntry(0, 0x80, 0, paint)!;
    expect(dark).toEqual([0, 0, 0]);
    const light = nfs2RecolorPaletteEntry(0, 0xff, 0, paint)!;
    light.forEach((c, i) => expect(c).toBeGreaterThanOrEqual(paint.color[i]));
  });

  it('animates tyres by speed and brake lights by the brake', () => {
    const car = carMesh();
    const controller = new Nfs2CarMeshController(car, 'assets', { model: 'CALA' });
    expect(controller.hasWheels).toBeTrue();
    // the viewer lists and hides the model's children: the wheels stay among them
    expect(car.getObjectByName('part_hp_12__m000')!.parent).toBe(car);
    expect(car.children.every(c => c instanceof Mesh)).toBeTrue();
    const tyreMap = () => ((car.getObjectByName('part_hp_12__m000') as Mesh).material as MeshBasicMaterial).map!;
    const lightMap = () => ((car.getObjectByName('part_hp_11__l000') as Mesh).material as MeshBasicMaterial).map!;
    const standing = tyreMap();
    const lightsOff = lightMap();
    controller.update(nfs2DrawStateOf(25, 0, false), 1);
    expect(tyreMap()).not.toBe(standing);
    expect(tyreMap().name).toBe('m300');
    controller.update(nfs2DrawStateOf(0, 0, true), 2);
    expect(tyreMap()).toBe(standing);
    expect(lightMap()).not.toBe(lightsOff);
    expect(lightMap().name).toBe('l100');
    controller.dispose();
  });

  it('takes the frames from the parsed GEO without extras (OBJ) and previews the brake lights', () => {
    const car = carMesh();
    car.traverse(o => (o.userData = {}));
    const controller = new Nfs2CarMeshController(car, 'assets', {
      model: 'CALA',
      frames: (part, texture) => (part === 11 && texture === 'l000' ? 2 : texture === 'm000' ? 4 : 1),
    });
    expect(controller.hasBrakeLights).toBeTrue();
    const lightMap = () => ((car.getObjectByName('part_hp_11__l000') as Mesh).material as MeshBasicMaterial).map!;
    controller.update(nfs2DrawStateOf(0, 0, true), 1);
    expect(lightMap().name).toBe('l100');
    controller.update(nfs2DrawStateOf(0, 0, false), 2);
    expect(lightMap().name).not.toBe('l100');
    controller.dispose();
  });

  // TailsLab's GLB attribute `_GAME_NORMAL` (three.js `_game_normal`) on the given parts' meshes
  const withGameNormals = (car: Group, parts: number[]): Group => {
    car.traverse(o => {
      if (o instanceof Mesh && parts.includes(o.userData['geo_part'])) {
        o.geometry.setAttribute('_game_normal', o.geometry.getAttribute('normal').clone());
      }
    });
    return car;
  };

  it('draws the 3Dfx reflections of the parts with a reflection and the game normals', () => {
    const car = withGameNormals(carMesh(), [1, 11, 12]);
    const body = car.getObjectByName('part_hp_1__b000') as Mesh;
    const plain = body.material;
    const controller = new Nfs2CarMeshController(car, 'assets', {
      model: 'CALA',
      voodooReflections: true,
      voodooEnvMap: 'chr0.png',
    });
    expect(controller.hasVoodooReflections).toBeTrue();
    expect(controller.voodooReflections).toBeTrue();
    expect(body.material).not.toBe(plain);
    const env = body.getObjectByName('part_hp_1__b000__reflection') as Mesh;
    expect(env.visible).toBeTrue();
    expect(env.renderOrder).toBe(body.renderOrder + 0.5);
    // the paint's HSV value sets the alpha (R3DCar_ReflectionAlpha): (0xff >> 2) + 0x40
    controller.color = 0xff0000;
    expect((env.material as MeshBasicMaterial).opacity).toBeCloseTo(0x7f / 255);
    // CALA's wheels have no reflection (layout 0)
    expect(car.getObjectByName('part_hp_12__m000__reflection')).toBeUndefined();
    // the shaded brake lights follow the frames
    const lights = car.getObjectByName('part_hp_11__l000') as Mesh;
    controller.update(nfs2DrawStateOf(0, 0, true), 1);
    expect((lights.material as MeshBasicMaterial).map!.name).toBe('l100');
    controller.voodooReflections = false;
    expect(body.material).toBe(plain);
    expect(env.visible).toBeFalse();
    expect((lights.material as MeshBasicMaterial).map!.name).toBe('l100');
    controller.dispose();
  });

  it('compiles the 3Dfx reflection shaders', () => {
    let renderer: WebGLRenderer;
    try {
      renderer = new WebGLRenderer({ canvas: document.createElement('canvas') });
    } catch {
      pending('no WebGL');
      return;
    }
    const errors: string[] = [];
    renderer.debug.onShaderError = (gl, program) => errors.push(gl.getProgramInfoLog(program) ?? 'shader error');
    const car = withGameNormals(carMesh(), [1, 11]);
    const controller = new Nfs2CarMeshController(car, 'assets', {
      model: 'CHEV',
      voodooReflections: true,
      voodooEnvMap: 'chr0.png',
    });
    controller.color = 0x2040ff;
    const scene = new Scene();
    scene.add(car);
    const camera = new PerspectiveCamera();
    camera.up.set(0, 0, 1);
    camera.position.set(0, -5, 1);
    camera.lookAt(0, 0, 0);
    renderer.render(scene, camera);
    expect(errors).toEqual([]);
    // CHEV's reflection 2: the shaded copies and the chr0 pass
    expect(renderer.info.programs!.length).toBeGreaterThan(2);
    controller.dispose();
    renderer.dispose();
  });

  it('has no 3Dfx reflections without the game normals, on traffic cars or without the texture', () => {
    expect(new Nfs2CarMeshController(carMesh(), 'assets', { model: 'CALA' }).hasVoodooReflections).toBeFalse();
    const traffic = new Nfs2CarMeshController(withGameNormals(carMesh(), [1]), 'assets', { model: 'TRAF' });
    expect(traffic.hasVoodooReflections).toBeFalse();
    const noTexture = new Nfs2CarMeshController(withGameNormals(carMesh(), [1]), 'assets', {
      model: 'CALA',
      voodooReflections: true,
    });
    expect(noTexture.voodooReflections).toBeFalse();
  });
});
