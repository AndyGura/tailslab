import { BoxGeometry, BufferAttribute, Material, Mesh, MeshBasicMaterial, Object3D, Texture } from 'three';
import { TnfsCarColors, TnfsCarMeshController } from '../../../../../nfs-three-lib/tnfs-car-mesh-controller';
import {
  createTnfsCarMeshController,
  PSX_GOURAUD_ATTRIBUTE,
  TnfsSkylineMemorialCarMeshController,
} from '../../../../../nfs-three-lib/tnfs-skyline-memorial-car-mesh-controller';
import { addPsxGouraudColors } from './orip-geometry.block-ui.component';

const CAR_COLORS: TnfsCarColors = {
  tail_lights: { texture_color: '#00ff00', textures: ['J038'], off: '#420000', on: '#ff0000' },
};

function withGouraud(mesh: Mesh): Mesh {
  const count = mesh.geometry.getAttribute('position').count;
  const values = new Uint8Array(count * 4);
  for (let i = 0; i < values.length; i += 4) {
    values.set([0xc8, 0x96, 0x28, 0xff], i);
  }
  mesh.geometry.setAttribute(PSX_GOURAUD_ATTRIBUTE, new BufferAttribute(values, 4, true));
  return mesh;
}

function texturedMesh(name: string, material?: Material): Mesh {
  const mesh = new Mesh(new BoxGeometry(), material ?? new MeshBasicMaterial({ map: new Texture() }));
  mesh.name = name;
  (mesh.material as Material).name ||= name;
  return mesh;
}

// a Japanese car: textured and untextured (window) meshes with Gouraud colours, a mesh without, the four wheels
function skylineMesh(): Object3D {
  const car = new Object3D();
  for (const name of ['lbl__rt_frnt__tyr4', 'lbl__lt_frnt__tyr4', 'lbl__rt_rear__tyr4', 'lbl__lt_rear__tyr4']) {
    car.add(texturedMesh(name));
  }
  car.add(withGouraud(texturedMesh('J000')));
  car.add(withGouraud(texturedMesh('J038')));
  const window = new Mesh(new BoxGeometry(), new MeshBasicMaterial({ color: 0x516389 }));
  window.name = 'flat_516389';
  car.add(withGouraud(window));
  car.add(texturedMesh('Shad'));
  return car;
}

const compiled = (material: Material) => {
  const shader = {
    uniforms: {},
    vertexShader: '#include <common>\nvoid main() {\n#include <begin_vertex>\n}',
    fragmentShader: '#include <common>\nvoid main() {\n#include <map_fragment>\n#include <color_fragment>\n}',
  } as any;
  material.onBeforeCompile(shader, undefined as any);
  return shader;
};

describe('TnfsSkylineMemorialCarMeshController', () => {
  it('is created for a model with Gouraud colours, the base controller otherwise', () => {
    const skyline = createTnfsCarMeshController(skylineMesh(), CAR_COLORS, 'assets', false);
    expect(skyline).toBeInstanceOf(TnfsSkylineMemorialCarMeshController);
    expect(skyline.hasWheels).toBeTrue();
    skyline.dispose();
    const plain = new Object3D();
    plain.add(texturedMesh('J000'));
    const base = createTnfsCarMeshController(plain, CAR_COLORS, 'assets', false);
    expect(base).toBeInstanceOf(TnfsCarMeshController);
    expect(base).not.toBeInstanceOf(TnfsSkylineMemorialCarMeshController);
    base.dispose();
  });

  it('draws the colours after the recolored texels, on the texel as the GPU does', () => {
    const car = skylineMesh();
    const controller = createTnfsCarMeshController(car, CAR_COLORS, 'assets', false);
    const tailLights = car.getObjectByName('J038') as Mesh;
    const shader = compiled(tailLights.material as Material);
    expect(shader.vertexShader).toContain(`attribute vec4 ${PSX_GOURAUD_ATTRIBUTE};`);
    expect(shader.vertexShader).toContain(`vPsxGouraud = ${PSX_GOURAUD_ATTRIBUTE};`);
    const recolor = shader.fragmentShader.indexOf('tnfsRecolorCount )');
    const gouraud = shader.fragmentShader.indexOf('vPsxGouraud.rgb * ( 255.0 / 128.0 )');
    expect(recolor).toBeGreaterThan(-1);
    expect(gouraud).toBeGreaterThan(recolor);
    expect(shader.fragmentShader).toContain('sRGBTransferOETF( vec4( diffuseColor.rgb, 1.0 ) )');
    expect((tailLights.material as Material).customProgramCacheKey()).toContain('psx-gouraud');
    controller.dispose();
  });

  it('draws an untextured polygon in its colour, a mesh without colours as before', () => {
    const car = skylineMesh();
    const controller = createTnfsCarMeshController(car, CAR_COLORS, 'assets', false);
    const window = car.getObjectByName('flat_516389') as Mesh;
    expect(compiled(window.material as Material).fragmentShader).toContain('vec3 psxShaded = vPsxGouraud.rgb;');
    const shadow = car.getObjectByName('Shad') as Mesh;
    expect(compiled(shadow.material as Material).vertexShader).not.toContain(PSX_GOURAUD_ATTRIBUTE);
    controller.dispose();
  });

  it('gives the meshes with colours their own copy of a material shared with meshes without', () => {
    const car = new Object3D();
    const shared = new MeshBasicMaterial({ map: new Texture() });
    shared.name = 'J000';
    const colored = withGouraud(texturedMesh('J000', shared));
    const plain = texturedMesh('J000', shared);
    car.add(colored, plain);
    const controller = createTnfsCarMeshController(car, null, 'assets', false);
    expect(plain.material).toBe(shared);
    expect(colored.material).not.toBe(shared);
    expect((colored.material as MeshBasicMaterial).map).toBe(shared.map);
    expect(compiled(plain.material as Material).vertexShader).not.toContain(PSX_GOURAUD_ATTRIBUTE);
    expect(compiled(colored.material as Material).vertexShader).toContain(PSX_GOURAUD_ATTRIBUTE);
    controller.dispose();
  });

  it('gives a wheel neutral colours when the other wheel of its axle has colours', () => {
    const car = skylineMesh();
    const frontRight = withGouraud(car.getObjectByName('lbl__rt_frnt__tyr4') as Mesh);
    const frontLeft = car.getObjectByName('lbl__lt_frnt__tyr4') as Mesh;
    const controller = createTnfsCarMeshController(car, null, 'assets', false);
    expect(frontLeft.material).toBe(frontRight.material);
    const neutral = frontLeft.geometry.getAttribute(PSX_GOURAUD_ATTRIBUTE);
    expect([neutral.getX(0), neutral.getW(0)]).toEqual([0x80 / 255, 0]);
    expect(compiled(frontLeft.material as Material).vertexShader).toContain(PSX_GOURAUD_ATTRIBUTE);
    expect(
      (car.getObjectByName('lbl__rt_rear__tyr4') as Mesh).geometry.getAttribute(PSX_GOURAUD_ATTRIBUTE),
    ).toBeFalsy();
    controller.dispose();
  });

  it("reads the colours of the converter's OBJ export by mesh", async () => {
    const car = new Object3D();
    const mesh = texturedMesh('J000');
    car.add(mesh);
    const corners = mesh.geometry.getAttribute('position').count;
    const extra = { psx_gouraud: { J000: 'c8964cff'.repeat(corners), Shad: '80808000' } };
    spyOn(window, 'fetch').and.resolveTo(new Response(JSON.stringify(extra)));
    await addPsxGouraudColors(car, 'model/geometry_extra.json');
    const colors = mesh.geometry.getAttribute(PSX_GOURAUD_ATTRIBUTE);
    expect(colors.count).toBe(corners);
    expect(colors.normalized).toBeTrue();
    expect([colors.getX(1), colors.getY(1), colors.getZ(1), colors.getW(1)]).toEqual([
      0xc8 / 255,
      0x96 / 255,
      0x4c / 255,
      1,
    ]);
  });
});
