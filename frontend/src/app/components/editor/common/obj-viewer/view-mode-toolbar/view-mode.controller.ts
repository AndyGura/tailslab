import {
  AmbientLight,
  BufferGeometry,
  EdgesGeometry,
  LineBasicMaterial,
  LineSegments,
  Material,
  Mesh,
  MeshBasicMaterial,
  MeshLambertMaterial,
  MeshPhongMaterial,
  MeshStandardMaterial,
  Object3D,
} from 'three';

export type ViewMode = 'material' | 'wireframe' | 'unlit' | 'edges' | 'vertex_colors';

// Colour of the meshes without vertex colours in the 'vertex_colors' view mode
export const NO_VERTEX_COLORS_COLOR = 0x808080;

// The mesh has vertex colours: the geometry attribute `color` (the OBJ's `v` colours, decoded from sRGB by OBJLoader)
export function hasVertexColors(mesh: Mesh): boolean {
  return !!mesh.geometry?.getAttribute('color');
}

// `userData` key of objects the view modes leave alone, with everything under them (viewer overlays)
export const VIEW_MODE_IGNORE = 'viewModeIgnore';

export class ViewModeController {
  public onFrameAll?: () => void;
  private _viewMode: ViewMode = 'material';
  private originalMaterials: Map<Mesh, Material | Material[]> = new Map();
  private edgeLines: LineSegments[] = [];
  private meshesWithViewModeMaterials: Set<Mesh> = new Set();
  private controllerManagedMaterials: Map<Mesh, Material | Material[]> = new Map();
  // meshes of the tree with vertex colours: the 'vertex_colors' view mode is offered while there is one
  private meshesWithVertexColors: Set<Mesh> = new Set();
  private onChildAddedBound: (event: any) => void;
  private onChildRemovedBound: (event: any) => void;

  constructor(
    private rootObject: Object3D,
    private ambientLight: AmbientLight,
  ) {
    this.captureOriginalMaterials();
    this.onChildAddedBound = this.onChildAdded.bind(this);
    this.onChildRemovedBound = this.onChildRemoved.bind(this);
    this.rootObject.addEventListener('childadded', this.onChildAddedBound);
    this.rootObject.addEventListener('childremoved', this.onChildRemovedBound);
  }

  get listViewModes(): ViewMode[] {
    const modes: ViewMode[] = ['material', 'wireframe', 'unlit', 'edges'];
    return this.meshesWithVertexColors.size ? [...modes, 'vertex_colors'] : modes;
  }

  get viewMode(): ViewMode {
    return this._viewMode;
  }

  setViewMode(mode: ViewMode): void {
    this._viewMode = mode;
    this.applyViewMode();
  }

  public frameAll(): void {
    this.onFrameAll?.();
  }

  // Meshes of the tree, without the objects marked `userData.viewModeIgnore` and what is under them: viewer overlays
  // (an editing gizmo, whose invisible picking meshes must keep their materials and get no edge lines)
  private forEachMesh(root: Object3D, fn: (mesh: Mesh) => void): void {
    if (root.userData?.[VIEW_MODE_IGNORE]) {
      return;
    }
    if (root instanceof Mesh) {
      fn(root);
    }
    for (const child of root.children) {
      this.forEachMesh(child, fn);
    }
  }

  private captureOriginalMaterials(): void {
    this.originalMaterials.clear();
    this.forEachMesh(this.rootObject, obj => {
      this.originalMaterials.set(obj, Array.isArray(obj.material) ? [...obj.material] : obj.material.clone());
      this.noteVertexColors(obj);
    });
  }

  private noteVertexColors(mesh: Mesh): void {
    if (hasVertexColors(mesh)) {
      this.meshesWithVertexColors.add(mesh);
    }
  }

  private clearEdgeLines(): void {
    if (this.edgeLines.length > 0) {
      for (const edgeLine of this.edgeLines) {
        if (edgeLine.parent) {
          edgeLine.parent.remove(edgeLine);
        }
        edgeLine.geometry.dispose();
        (edgeLine.material as LineBasicMaterial).dispose();
      }
    }
    this.edgeLines = [];
  }

  public applyViewMode(): void {
    this.clearEdgeLines();
    this.applyViewModeToTree(this.rootObject);
  }

  private applyViewModeToTree(root: Object3D): void {
    this.forEachMesh(root, obj => this.applyViewModeToMesh(obj));
  }

  private applyViewModeToMesh(obj: Mesh): void {
    const originalMaterial = this.originalMaterials.get(obj);
    if (!originalMaterial) {
      // If we found a mesh that wasn't there before, capture its material
      this.originalMaterials.set(obj, Array.isArray(obj.material) ? [...obj.material] : obj.material.clone());
    }

    switch (this._viewMode) {
      case 'material':
        this.restoreMaterials(obj);
        this.ambientLight.intensity = 2;
        break;
      case 'wireframe':
        this.replaceMaterials(
          obj,
          mat =>
            new MeshBasicMaterial({
              color: mat instanceof MeshBasicMaterial ? mat.color : 0xffffff,
              wireframe: true,
              transparent: true,
              opacity: 0.8,
            }),
        );
        this.ambientLight.intensity = 2;
        break;
      case 'unlit':
        this.replaceMaterials(obj, mat => {
          let textureMap = null;
          let materialColor = 0xffffff;
          if (
            mat instanceof MeshBasicMaterial ||
            mat instanceof MeshLambertMaterial ||
            mat instanceof MeshStandardMaterial ||
            mat instanceof MeshPhongMaterial
          ) {
            textureMap = mat.map;
            materialColor = mat.color.getHex();
          }
          return new MeshBasicMaterial({
            color: materialColor,
            map: textureMap,
            transparent: mat.transparent,
            opacity: mat.opacity,
            side: mat.side,
          });
        });
        this.ambientLight.intensity = 0;
        break;
      case 'vertex_colors':
        // the colours alone, unlit; meshes without them grey
        this.replaceMaterials(obj, mat =>
          hasVertexColors(obj)
            ? new MeshBasicMaterial({
                vertexColors: true,
                transparent: obj.geometry.getAttribute('color').itemSize === 4,
                side: mat.side,
              })
            : new MeshBasicMaterial({ color: NO_VERTEX_COLORS_COLOR, side: mat.side }),
        );
        this.ambientLight.intensity = 0;
        break;
      case 'edges':
        this.restoreMaterials(obj);
        this.ambientLight.intensity = 2;

        const edges = new EdgesGeometry(obj.geometry as BufferGeometry);
        const edgeMaterial = new LineBasicMaterial({ color: 0x000000, linewidth: 2 });
        const edgeLines = new LineSegments(edges, edgeMaterial);
        obj.add(edgeLines);
        this.edgeLines.push(edgeLines);
        break;
    }
  }

  // Gives the mesh back its own materials
  private restoreMaterials(obj: Mesh): void {
    if (this.meshesWithViewModeMaterials.has(obj)) {
      const storedMaterial = this.controllerManagedMaterials.get(obj);
      if (storedMaterial) {
        obj.material = storedMaterial;
        this.controllerManagedMaterials.delete(obj);
      }
      this.meshesWithViewModeMaterials.delete(obj);
    }
  }

  // Replaces the mesh's materials by the view mode's materials made of its own ones (kept to restore them)
  private replaceMaterials(obj: Mesh, make: (material: Material) => Material): void {
    if (!this.meshesWithViewModeMaterials.has(obj)) {
      this.controllerManagedMaterials.set(obj, obj.material);
    }
    const current = this.controllerManagedMaterials.get(obj) || obj.material;
    const materials = (Array.isArray(current) ? current : [current]).map(make);
    obj.material = materials.length === 1 ? materials[0] : materials;
    this.meshesWithViewModeMaterials.add(obj);
  }

  private onChildAdded(event: any): void {
    this.forEachMesh(event.child, obj => this.noteVertexColors(obj));
    if (this._viewMode === 'vertex_colors' && !this.meshesWithVertexColors.size) {
      // a model without vertex colours replaced the one with them
      this.setViewMode('material');
      return;
    }
    this.applyViewModeToTree(event.child);
  }

  private onChildRemoved(event: any): void {
    this.forEachMesh(event.child, obj => {
      this.originalMaterials.delete(obj);
      this.controllerManagedMaterials.delete(obj);
      this.meshesWithViewModeMaterials.delete(obj);
      this.meshesWithVertexColors.delete(obj);
    });
  }

  public dispose(): void {
    this.rootObject.removeEventListener('childadded', this.onChildAddedBound);
    this.rootObject.removeEventListener('childremoved', this.onChildRemovedBound);
    this.clearEdgeLines();
    this.originalMaterials.clear();
    this.controllerManagedMaterials.clear();
    this.meshesWithViewModeMaterials.clear();
    this.meshesWithVertexColors.clear();
  }
}
