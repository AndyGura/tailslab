import { BoxGeometry, Group, Mesh, MeshBasicMaterial, Texture } from 'three';
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
});
