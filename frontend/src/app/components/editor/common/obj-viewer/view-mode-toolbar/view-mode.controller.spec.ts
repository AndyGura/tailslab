import {
  AmbientLight,
  BoxGeometry,
  DoubleSide,
  Float32BufferAttribute,
  LineSegments,
  Mesh,
  MeshBasicMaterial,
  MeshPhongMaterial,
  Object3D,
  Scene,
  Texture,
} from 'three';
import { NO_VERTEX_COLORS_COLOR, VIEW_MODE_IGNORE, ViewModeController } from './view-mode.controller';

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

  // a mesh as OBJLoader makes it of an OBJ with `v` colours, textured
  function coloredMesh(): Mesh {
    const geometry = new BoxGeometry();
    const count = geometry.getAttribute('position').count;
    geometry.setAttribute('color', new Float32BufferAttribute(new Array(count * 3).fill(0.5), 3));
    return new Mesh(geometry, new MeshPhongMaterial({ map: new Texture(), side: DoubleSide }));
  }

  it('should offer vertex colours only while a mesh has them', () => {
    const scene = new Scene();
    const controller = new ViewModeController(scene, new AmbientLight());
    scene.add(new Mesh(new BoxGeometry(), new MeshBasicMaterial()));
    expect(controller.listViewModes).not.toContain('vertex_colors');
    const model = new Object3D();
    model.add(coloredMesh());
    scene.add(model);
    expect(controller.listViewModes).toContain('vertex_colors');
    scene.remove(model);
    expect(controller.listViewModes).not.toContain('vertex_colors');
    controller.dispose();
  });

  it('should draw the vertex colours alone and the meshes without them grey', () => {
    const scene = new Scene();
    const controller = new ViewModeController(scene, new AmbientLight());
    const colored = coloredMesh();
    const textured = colored.material as MeshPhongMaterial;
    const plainMaterial = new MeshBasicMaterial({ map: new Texture() });
    const plain = new Mesh(new BoxGeometry(), plainMaterial);
    scene.add(colored, plain);
    controller.setViewMode('vertex_colors');
    const coloredMaterial = colored.material as MeshBasicMaterial;
    expect(coloredMaterial.vertexColors).toBeTrue();
    expect(coloredMaterial.map).toBeNull();
    expect(coloredMaterial.side).toBe(DoubleSide);
    expect((plain.material as MeshBasicMaterial).color.getHex()).toBe(NO_VERTEX_COLORS_COLOR);
    expect((plain.material as MeshBasicMaterial).vertexColors).toBeFalse();
    // a chunk streamed in while the mode is on gets it too
    const chunk = coloredMesh();
    scene.add(chunk);
    expect((chunk.material as MeshBasicMaterial).vertexColors).toBeTrue();
    controller.setViewMode('material');
    expect(colored.material).toBe(textured);
    expect(plain.material).toBe(plainMaterial);
    controller.dispose();
  });

  it('should go back to the material view when the model with vertex colours is replaced', () => {
    const scene = new Scene();
    const controller = new ViewModeController(scene, new AmbientLight());
    const model = coloredMesh();
    scene.add(model);
    controller.setViewMode('vertex_colors');
    scene.remove(model);
    const material = new MeshBasicMaterial();
    const other = new Mesh(new BoxGeometry(), material);
    scene.add(other);
    expect(controller.viewMode).toBe('material');
    expect(other.material).toBe(material);
    controller.dispose();
  });
});
