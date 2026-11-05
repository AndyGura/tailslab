import { AmbientLight, BoxGeometry, LineSegments, Mesh, MeshBasicMaterial, Object3D, Scene } from 'three';
import { VIEW_MODE_IGNORE, ViewModeController } from './view-mode.controller';

describe('ViewModeController', () => {
  function setup() {
    const scene = new Scene();
    const model = new Mesh(new BoxGeometry(), new MeshBasicMaterial());
    // an overlay like an editing gizmo: an invisible picking mesh under a flagged root
    const overlay = new Object3D();
    overlay.userData[VIEW_MODE_IGNORE] = true;
    const pickerMaterial = new MeshBasicMaterial({ visible: false });
    const picker = new Mesh(new BoxGeometry(), pickerMaterial);
    picker.name = 'X';
    overlay.add(picker);
    const controller = new ViewModeController(scene, new AmbientLight());
    scene.add(model, overlay);
    return { controller, model, picker, pickerMaterial };
  }

  it('should leave objects marked to be ignored as they are', () => {
    const { controller, model, picker, pickerMaterial } = setup();
    controller.setViewMode('edges');
    expect(model.children.some(c => c instanceof LineSegments)).toBeTrue();
    expect(picker.children.length).toBe(0);
    controller.setViewMode('wireframe');
    expect((model.material as MeshBasicMaterial).wireframe).toBeTrue();
    expect(picker.material).toBe(pickerMaterial);
    controller.setViewMode('material');
    controller.dispose();
  });
});
