import { BehaviorSubject } from 'rxjs';
import {
  BufferAttribute,
  BufferGeometry,
  Camera,
  CanvasTexture,
  Color,
  Object3D,
  Points,
  PointsMaterial,
  Quaternion,
  Raycaster,
  Scene,
  Vector2,
  Vector3,
} from 'three';
import { TransformControls } from 'three/examples/jsm/controls/TransformControls.js';
import { SpatialEditKind, SpatialHandle } from './spatial-edit.types';
import { VIEW_MODE_IGNORE } from '../obj-viewer/view-mode-toolbar/view-mode.controller';

export type GizmoMode = 'translate' | 'rotate';

// How far the stored transforms are from the ones asked for (the largest of the selection): the file holds positions
// and angles with less precision (fixed point, 8-bit angles), clamps them to its ranges, a block may re-anchor a thing
// elsewhere
export interface SpatialSnap {
  // meters (export space units)
  distance: number;
  // radians
  angle: number;
}

// A handle's new transform
export interface SpatialMove {
  handle: SpatialHandle;
  position: Vector3;
  // null for a kind without rotation
  rotation: Quaternion | null;
}

// What the viewer hosting the editor provides
export interface SpatialEditHost {
  // objects drawing a handle (kinds with `pick_entities`): clicking them selects the handle
  handleObjects?(handle: SpatialHandle): Object3D[];
  // objects hiding handles behind them (terrain): a handle behind them is not picked
  occluders?(): Object3D[];
  // a drag of the selected handles starts / moves them (a preview: the data does not have it yet) / ends
  previewStart?(handles: SpatialHandle[]): void;
  preview?(moves: SpatialMove[]): void;
  previewEnd?(): void;
  // writes the moves to the data as one change, resolves with the handles as stored (in the order of `moves`), null
  // when it failed
  commit(moves: SpatialMove[]): Promise<SpatialHandle[] | null>;
}

const MARKER_COLOR = 0x4fc3f7;
const HOVER_COLOR = 0xffeb3b;
const SELECTED_COLOR = 0xff9800;
// pick radius around a handle marker, in CSS pixels
const PICK_RADIUS = 10;
// a handle this far behind the first occluder hit still counts as visible (it lies on the occluder's surface)
const OCCLUSION_TOLERANCE = 0.75;
// a press moving less than this (CSS pixels) before it is released is a click
const CLICK_DISTANCE = 4;

function markerTexture(): CanvasTexture {
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = 32;
  const ctx = canvas.getContext('2d')!;
  ctx.beginPath();
  ctx.arc(16, 16, 12, 0, Math.PI * 2);
  ctx.fillStyle = '#ffffff';
  ctx.fill();
  ctx.lineWidth = 4;
  ctx.strokeStyle = '#000000';
  ctx.stroke();
  return new CanvasTexture(canvas);
}

function isShown(object: Object3D): boolean {
  for (let o: Object3D | null = object; o; o = o.parent) {
    if (!o.visible) return false;
  }
  return true;
}

function handlePosition(handle: SpatialHandle): Vector3 {
  return new Vector3().fromArray(handle.position);
}

function handleRotation(handle: SpatialHandle): Quaternion {
  return new Quaternion().fromArray(handle.rotation || [0, 0, 0, 1]);
}

/**
 * Moves the handles of one spatial edit kind (library/spatial_edit.py) in a three.js scene: a marker per handle, a
 * click selects one (the nearest marker on screen that is not behind the occluders, or an object drawing a handle), a
 * drag on empty space selects the visible ones in a box; with Shift both add to the selection (a click on a selected
 * one removes it), with Ctrl / Cmd they remove from it. Alt + drag is left to the camera. A gizmo with the axes the kind
 * declares sits at the centre of the selection: moving it moves every selected handle by as much, rotating it turns
 * them around it, each one with it. A drag is previewed by the host; when it ends the host commits the moves of all
 * of them as one change and the selection jumps to the transforms the data holds. The viewer's camera must not take
 * left clicks while editing, and must hold still while `pointerCaptured$`.
 */
export class SpatialEditController {
  // the selected handles, the last selected one last
  readonly selection$ = new BehaviorSubject<SpatialHandle[]>([]);
  // of the last move of the selection, null when it landed where it was asked to
  readonly snap$ = new BehaviorSubject<SpatialSnap | null>(null);
  readonly committing$ = new BehaviorSubject<boolean>(false);
  // the pointer is on a gizmo axis, drags it or draws a selection box: a camera dragged with the same button must
  // hold still
  readonly pointerCaptured$ = new BehaviorSubject<boolean>(false);
  readonly gizmoMode$ = new BehaviorSubject<GizmoMode>('translate');

  private kind: SpatialEditKind | null = null;
  private handles: SpatialHandle[] = [];
  private readonly handleIndex = new Map<string, number>();
  // objects drawing handles -> handle
  private readonly pickObjects = new Map<Object3D, SpatialHandle>();
  private readonly texture = markerTexture();
  private readonly markers: Points;
  private readonly hoverMarker: Points;
  private readonly selectedMarkers: Points;
  // the gizmo's object: at the centre of the selection, turned like the handle when one is selected
  private readonly pivot = new Object3D();
  private readonly gizmo: TransformControls;
  private readonly raycaster = new Raycaster();
  private readonly box: HTMLDivElement;
  private pointerDownAt: Vector2 | null = null;
  // what a press on empty space does: a click picks, a drag draws a box
  private selectMode: 'replace' | 'add' | 'remove' = 'replace';
  private boxSelecting = false;
  private hoverFrame: number | null = null;
  private dragging = false;
  // the pivot and the selection when a move started
  private moveStart: { position: Vector3; rotation: Quaternion; handles: SpatialHandle[] } | null = null;
  private readonly listeners: [EventTarget, string, (e: any) => void][] = [];

  constructor(
    private readonly scene: Scene,
    private readonly camera: Camera,
    private readonly canvas: HTMLCanvasElement,
    private readonly host: SpatialEditHost,
  ) {
    this.markers = this.createPoints(7, MARKER_COLOR, true);
    this.hoverMarker = this.createPoints(12, HOVER_COLOR, false);
    this.selectedMarkers = this.createPoints(13, SELECTED_COLOR, false);
    this.gizmo = new TransformControls(camera, canvas);
    this.gizmo.setSpace('world');
    this.gizmo.addEventListener('dragging-changed', (e: any) => (e.value ? this.onDragStart() : this.onDragEnd()));
    this.gizmo.addEventListener('objectChange', () => this.onDragMove());
    this.gizmo.addEventListener('axis-changed', () => this.updatePointerCaptured());
    this.gizmo.addEventListener('dragging-changed', () => this.updatePointerCaptured());
    // overlays: the view modes (wireframe, edges...) must not change them, an edge line on a picking mesh of the gizmo
    // would be what a ray hits, and an axis without a name moves nothing
    for (const overlay of [this.pivot, this.gizmo.getHelper(), this.markers, this.hoverMarker, this.selectedMarkers]) {
      overlay.userData[VIEW_MODE_IGNORE] = true;
    }
    scene.add(this.pivot, this.gizmo.getHelper(), this.markers, this.hoverMarker, this.selectedMarkers);
    this.box = document.createElement('div');
    Object.assign(this.box.style, {
      position: 'absolute',
      display: 'none',
      border: '1px dashed #ff9800',
      background: 'rgba(255, 152, 0, 0.12)',
      pointerEvents: 'none',
    });
    canvas.parentElement?.appendChild(this.box);
    this.listen(canvas, 'pointerdown', (e: PointerEvent) => this.onPointerDown(e));
    this.listen(window, 'pointerup', (e: PointerEvent) => this.onPointerUp(e));
    this.listen(window, 'pointermove', (e: PointerEvent) => this.onPointerMove(e));
    this.listen(canvas, 'pointerleave', () => this.setMarkers(this.hoverMarker, []));
    this.updateGizmo();
  }

  get activeKind(): SpatialEditKind | null {
    return this.kind;
  }

  get isDragging(): boolean {
    return this.dragging;
  }

  // the centre of the selection
  get pivotPosition(): Vector3 {
    return this.pivot.position.clone();
  }

  // null: editing off, nothing shown
  setKind(kind: SpatialEditKind | null) {
    if (this.dragging) {
      this.gizmo.detach();
    }
    this.kind = kind;
    this.select([]);
    this.setHandles([]);
    if (kind && !kind.rotate_axes && this.gizmoMode$.value === 'rotate') {
      this.gizmoMode$.next('translate');
    }
    if (kind && !kind.translate_axes && kind.rotate_axes) {
      this.gizmoMode$.next('rotate');
    }
    this.updateGizmo();
  }

  // Handles of the current kind (of the loaded chunks). Selected handles stay selected, with the handle of the same id
  setHandles(handles: SpatialHandle[]) {
    this.handles = handles;
    this.handleIndex.clear();
    handles.forEach((h, i) => this.handleIndex.set(h.id, i));
    this.refreshPickObjects();
    this.markers.geometry.dispose();
    this.markers.geometry = new BufferGeometry();
    this.markers.geometry.setAttribute('position', new BufferAttribute(this.positionsOf(handles), 3));
    this.setMarkers(this.hoverMarker, []);
    if (!this.dragging) {
      const selection = this.selection$.value;
      const fresh = selection.map(h => this.handleById(h.id) || h);
      if (fresh.some((h, i) => h !== selection[i])) {
        // moved by something else (undo, a value typed in a panel): the snap of the last move is gone
        if (fresh.some((h, i) => h.position.some((v, j) => v !== selection[i].position[j]))) {
          this.snap$.next(null);
        }
        this.applySelection(fresh);
      }
    }
  }

  // The objects drawing handles changed (chunks reloaded) while the handles did not
  refreshPickObjects() {
    this.pickObjects.clear();
    if (!this.kind?.pick_entities || !this.host.handleObjects) {
      return;
    }
    for (const handle of this.handles) {
      if (handle.match) {
        for (const object of this.host.handleObjects(handle)) {
          this.pickObjects.set(object, handle);
        }
      }
    }
  }

  // Replaces the selection
  select(handles: SpatialHandle[]) {
    if (this.dragging) {
      return;
    }
    const ids = (hs: SpatialHandle[]) => hs.map(h => h.id).join('|');
    if (ids(handles) !== ids(this.selection$.value)) {
      this.snap$.next(null);
    }
    this.applySelection(handles);
  }

  // Adds the handle to the selection, or removes it if it is selected
  toggle(handle: SpatialHandle) {
    const selection = this.selection$.value;
    this.select(
      selection.some(h => h.id === handle.id) ? selection.filter(h => h.id !== handle.id) : [...selection, handle],
    );
  }

  selectById(...ids: string[]) {
    this.select(ids.map(id => this.handleById(id)).filter((h): h is SpatialHandle => !!h));
  }

  setGizmoMode(mode: GizmoMode) {
    const axes = mode === 'rotate' ? this.kind?.rotate_axes : this.kind?.translate_axes;
    if (!axes || this.dragging) {
      return;
    }
    this.gizmoMode$.next(mode);
    this.updateGizmo();
  }

  // A move typed in (or any move not made with the gizmo): the pivot to `position` (the selection moves with it) and,
  // for one selected handle, to `rotation`
  async moveSelection(position: Vector3, rotation: Quaternion | null) {
    if (!this.selection$.value.length || this.dragging || this.committing$.value) {
      return;
    }
    this.startMove();
    this.pivot.position.copy(position);
    if (rotation && this.selection$.value.length === 1) {
      this.pivot.quaternion.copy(rotation);
    }
    this.host.preview?.(this.selectionMoves());
    await this.commit();
  }

  // Moves every selected handle to the centre of the selection (on the axes the kind moves along), as one change. The
  // handles stay apart in the data: nothing is merged
  async moveSelectionToCentre() {
    const handles = this.selection$.value;
    const axes = this.kind?.translate_axes || '';
    if (handles.length < 2 || !axes || this.dragging || this.committing$.value) {
      return;
    }
    this.startMove();
    const centre = this.pivot.position;
    const moves = handles.map(handle => {
      const position = handlePosition(handle);
      for (const axis of ['x', 'y', 'z'] as const) {
        if (axes.includes(axis)) {
          position[axis] = centre[axis];
        }
      }
      return { handle, position, rotation: this.kind!.rotate_axes ? handleRotation(handle) : null };
    });
    this.host.preview?.(moves);
    await this.commit(moves);
  }

  dispose() {
    for (const [target, type, listener] of this.listeners) {
      target.removeEventListener(type, listener);
    }
    if (this.hoverFrame !== null) {
      cancelAnimationFrame(this.hoverFrame);
    }
    this.box.remove();
    this.gizmo.detach();
    this.gizmo.dispose();
    this.scene.remove(this.pivot, this.gizmo.getHelper(), this.markers, this.hoverMarker, this.selectedMarkers);
    for (const points of [this.markers, this.hoverMarker, this.selectedMarkers]) {
      points.geometry.dispose();
      (points.material as PointsMaterial).dispose();
    }
    this.texture.dispose();
  }

  private handleById(id: string): SpatialHandle | undefined {
    const i = this.handleIndex.get(id);
    return i === undefined ? undefined : this.handles[i];
  }

  private listen(target: EventTarget, type: string, listener: (e: any) => void) {
    target.addEventListener(type, listener);
    this.listeners.push([target, type, listener]);
  }

  private createPoints(size: number, color: number, depthTest: boolean): Points {
    const points = new Points(
      new BufferGeometry(),
      new PointsMaterial({
        size,
        sizeAttenuation: false,
        color: new Color(color),
        map: this.texture,
        alphaTest: 0.5,
        depthTest,
        transparent: !depthTest,
      }),
    );
    points.frustumCulled = false;
    // hover and selection markers are drawn over everything
    points.renderOrder = depthTest ? 0 : 1000;
    return points;
  }

  private positionsOf(handles: { position: [number, number, number] }[]): Float32Array {
    const positions = new Float32Array(handles.length * 3);
    handles.forEach((h, i) => positions.set(h.position, i * 3));
    return positions;
  }

  private setMarkers(points: Points, positions: [number, number, number][]) {
    points.geometry.dispose();
    points.geometry = new BufferGeometry();
    points.geometry.setAttribute(
      'position',
      new BufferAttribute(this.positionsOf(positions.map(position => ({ position }))), 3),
    );
  }

  private updatePointerCaptured() {
    const captured = this.boxSelecting || this.gizmoTakesPointer();
    if (captured !== this.pointerCaptured$.value) {
      this.pointerCaptured$.next(captured);
    }
  }

  // The selection, the pivot at its centre (turned like the handle when there is one)
  private applySelection(handles: SpatialHandle[]) {
    if (handles.length) {
      const centre = new Vector3();
      handles.forEach(h => centre.add(handlePosition(h)));
      this.pivot.position.copy(centre.divideScalar(handles.length));
      this.pivot.quaternion.copy(handles.length === 1 ? handleRotation(handles[0]) : new Quaternion());
      this.pivot.updateMatrixWorld();
    }
    this.setMarkers(
      this.selectedMarkers,
      handles.map(h => h.position),
    );
    this.updateGizmo(handles);
    // last: listeners read the pivot
    this.selection$.next(handles);
  }

  private updateGizmo(selection: SpatialHandle[] = this.selection$.value) {
    const mode = this.gizmoMode$.value;
    const axes = (mode === 'rotate' ? this.kind?.rotate_axes : this.kind?.translate_axes) || '';
    if (!selection.length || !this.kind || !axes) {
      this.gizmo.detach();
      return;
    }
    this.gizmo.setMode(mode);
    this.gizmo.showX = axes.includes('x');
    this.gizmo.showY = axes.includes('y');
    this.gizmo.showZ = axes.includes('z');
    // the plane handles and the free rotation need every axis
    const all = axes.includes('x') && axes.includes('y') && axes.includes('z');
    this.gizmo.showXY = this.gizmo.showYZ = this.gizmo.showXZ = all;
    this.gizmo.showE = this.gizmo.showXYZE = all;
    this.gizmo.attach(this.pivot);
  }

  private startMove() {
    const handles = this.selection$.value;
    this.moveStart = { position: this.pivot.position.clone(), rotation: this.pivot.quaternion.clone(), handles };
    this.host.previewStart?.(handles);
  }

  // Each selected handle where the pivot takes it: moved by as much as the pivot, turned around it as much as it
  private selectionMoves(): SpatialMove[] {
    const start = this.moveStart;
    if (!start) {
      return [];
    }
    const turn = this.pivot.quaternion.clone().multiply(start.rotation.clone().invert());
    const rotates = !!this.kind?.rotate_axes;
    return start.handles.map(handle => ({
      handle,
      position: handlePosition(handle).sub(start.position).applyQuaternion(turn).add(this.pivot.position),
      rotation: rotates ? turn.clone().multiply(handleRotation(handle)) : null,
    }));
  }

  private pointerToNdc(e: { clientX: number; clientY: number }): Vector2 {
    const rect = this.canvas.getBoundingClientRect();
    return new Vector2(((e.clientX - rect.left) / rect.width) * 2 - 1, -((e.clientY - rect.top) / rect.height) * 2 + 1);
  }

  private firstOccluderDistance(): number {
    if (!this.host.occluders) {
      return Infinity;
    }
    const hit = this.raycaster
      .intersectObjects(this.host.occluders(), true)
      .find(h => isShown(h.object) && !(h.object as any).isPoints);
    return hit ? hit.distance : Infinity;
  }

  // The handle under the pointer: the nearest marker on screen within PICK_RADIUS which is not hidden by the
  // occluders, else the first object drawing a handle
  private pick(e: { clientX: number; clientY: number }): SpatialHandle | null {
    if (!this.kind || !this.handles.length) {
      return null;
    }
    const rect = this.canvas.getBoundingClientRect();
    const ndc = this.pointerToNdc(e);
    this.raycaster.setFromCamera(ndc, this.camera);
    const eye = new Vector3();
    this.camera.getWorldPosition(eye);
    const occluderDistance = this.firstOccluderDistance();
    let best: SpatialHandle | null = null;
    let bestScreenDistance = PICK_RADIUS;
    const v = new Vector3();
    for (const handle of this.handles) {
      v.fromArray(handle.position).project(this.camera);
      if (v.z < -1 || v.z > 1) continue;
      const dx = ((v.x - ndc.x) * rect.width) / 2;
      const dy = ((v.y - ndc.y) * rect.height) / 2;
      const screenDistance = Math.hypot(dx, dy);
      if (screenDistance > bestScreenDistance) continue;
      if (eye.distanceTo(v.fromArray(handle.position)) > occluderDistance + OCCLUSION_TOLERANCE) continue;
      best = handle;
      bestScreenDistance = screenDistance;
    }
    if (best || !this.pickObjects.size) {
      return best;
    }
    for (const hit of this.raycaster.intersectObjects([...this.pickObjects.keys()], true)) {
      if (hit.distance > occluderDistance + OCCLUSION_TOLERANCE || !isShown(hit.object)) continue;
      for (let o: Object3D | null = hit.object; o; o = o.parent) {
        const handle = this.pickObjects.get(o);
        if (handle) return handle;
      }
    }
    return null;
  }

  // Handles whose markers are in the box between two pointer positions and not hidden by the occluders
  private pickInBox(a: Vector2, b: Vector2): SpatialHandle[] {
    const ndcA = this.pointerToNdc({ clientX: a.x, clientY: a.y });
    const ndcB = this.pointerToNdc({ clientX: b.x, clientY: b.y });
    const [minX, maxX] = [Math.min(ndcA.x, ndcB.x), Math.max(ndcA.x, ndcB.x)];
    const [minY, maxY] = [Math.min(ndcA.y, ndcB.y), Math.max(ndcA.y, ndcB.y)];
    const eye = new Vector3();
    this.camera.getWorldPosition(eye);
    const v = new Vector3();
    const direction = new Vector3();
    return this.handles.filter(handle => {
      v.fromArray(handle.position).project(this.camera);
      if (v.z < -1 || v.z > 1 || v.x < minX || v.x > maxX || v.y < minY || v.y > maxY) {
        return false;
      }
      const position = handlePosition(handle);
      const distance = eye.distanceTo(position);
      this.raycaster.set(eye, direction.subVectors(position, eye).normalize());
      this.raycaster.far = distance;
      const visible = this.firstOccluderDistance() > distance - OCCLUSION_TOLERANCE;
      this.raycaster.far = Infinity;
      return visible;
    });
  }

  private gizmoTakesPointer(): boolean {
    return this.dragging || (this.gizmo.object !== undefined && this.gizmo.axis !== null);
  }

  private onPointerDown(e: PointerEvent) {
    const free =
      e.button === 0 && !e.altKey && !document.pointerLockElement && !this.gizmoTakesPointer() && !!this.kind;
    this.pointerDownAt = free ? new Vector2(e.clientX, e.clientY) : null;
    this.selectMode = e.shiftKey ? 'add' : e.ctrlKey || e.metaKey ? 'remove' : 'replace';
    // a drag from here draws a selection box, the camera holds still
    this.boxSelecting = free;
    this.updatePointerCaptured();
  }

  private onPointerUp(e: PointerEvent) {
    const downAt = this.pointerDownAt;
    const boxSelecting = this.boxSelecting;
    this.pointerDownAt = null;
    this.boxSelecting = false;
    this.box.style.display = 'none';
    this.updatePointerCaptured();
    if (!downAt || e.button !== 0 || !this.kind) {
      return;
    }
    const upAt = new Vector2(e.clientX, e.clientY);
    const selection = this.selection$.value;
    if (downAt.distanceTo(upAt) <= CLICK_DISTANCE) {
      const handle = this.pick(e);
      if (this.selectMode === 'replace') {
        this.select(handle ? [handle] : []);
      } else if (handle && (this.selectMode === 'add' || selection.some(h => h.id === handle.id))) {
        this.toggle(handle);
      }
    } else if (boxSelecting) {
      const inBox = this.pickInBox(downAt, upAt);
      if (this.selectMode === 'replace') {
        this.select(inBox);
      } else if (this.selectMode === 'add') {
        this.select([...selection, ...inBox.filter(h => !selection.some(s => s.id === h.id))]);
      } else {
        this.select(selection.filter(h => !inBox.some(b => b.id === h.id)));
      }
    }
  }

  private onPointerMove(e: PointerEvent) {
    if (this.boxSelecting && this.pointerDownAt) {
      if (this.pointerDownAt.distanceTo(new Vector2(e.clientX, e.clientY)) <= CLICK_DISTANCE) {
        return;
      }
      const canvasRect = this.canvas.getBoundingClientRect();
      const parentRect = this.canvas.parentElement!.getBoundingClientRect();
      const x = Math.max(Math.min(e.clientX, canvasRect.right), canvasRect.left);
      const y = Math.max(Math.min(e.clientY, canvasRect.bottom), canvasRect.top);
      Object.assign(this.box.style, {
        display: 'block',
        left: `${Math.min(x, this.pointerDownAt.x) - parentRect.left}px`,
        top: `${Math.min(y, this.pointerDownAt.y) - parentRect.top}px`,
        width: `${Math.abs(x - this.pointerDownAt.x)}px`,
        height: `${Math.abs(y - this.pointerDownAt.y)}px`,
      });
      return;
    }
    if (this.hoverFrame !== null || !this.kind || e.target !== this.canvas) {
      return;
    }
    const at = { clientX: e.clientX, clientY: e.clientY };
    this.hoverFrame = requestAnimationFrame(() => {
      this.hoverFrame = null;
      const hovered =
        this.dragging || this.pointerDownAt || document.pointerLockElement || this.gizmoTakesPointer()
          ? null
          : this.pick(at);
      const selected = hovered && this.selection$.value.some(h => h.id === hovered.id);
      this.setMarkers(this.hoverMarker, hovered && !selected ? [hovered.position] : []);
      this.canvas.style.cursor = hovered ? 'pointer' : '';
    });
  }

  private onDragStart() {
    if (!this.selection$.value.length) return;
    this.dragging = true;
    this.setMarkers(this.hoverMarker, []);
    this.startMove();
  }

  private onDragMove() {
    if (!this.dragging) return;
    const moves = this.selectionMoves();
    this.setMarkers(
      this.selectedMarkers,
      moves.map(m => m.position.toArray() as [number, number, number]),
    );
    this.host.preview?.(moves);
  }

  private async onDragEnd() {
    this.dragging = false;
    if (this.moveStart) {
      await this.commit();
    }
  }

  private async commit(moves: SpatialMove[] = this.selectionMoves()) {
    const start = this.moveStart!;
    this.moveStart = null;
    const moved = moves.some(
      m =>
        handlePosition(m.handle).distanceTo(m.position) > 1e-6 ||
        (m.rotation !== null && handleRotation(m.handle).angleTo(m.rotation) > 1e-6),
    );
    let stored: SpatialHandle[] = start.handles;
    if (moved) {
      this.committing$.next(true);
      try {
        stored = (await this.host.commit(moves)) || start.handles;
      } catch (err) {
        console.error('Could not move', start.handles, err);
      } finally {
        this.committing$.next(false);
      }
    }
    // the transforms the data holds
    this.host.preview?.(
      stored.map(handle => ({
        handle,
        position: handlePosition(handle),
        rotation: handle.rotation ? handleRotation(handle) : null,
      })),
    );
    this.host.previewEnd?.();
    if (moved) {
      let distance = 0;
      let angle = 0;
      stored.forEach((handle, i) => {
        distance = Math.max(distance, handlePosition(handle).distanceTo(moves[i].position));
        if (handle.rotation && moves[i].rotation) {
          angle = Math.max(angle, handleRotation(handle).angleTo(moves[i].rotation!));
        }
      });
      this.snap$.next(distance > 1e-4 || angle > 1e-4 ? { distance, angle } : null);
    }
    const positions = this.markers.geometry.getAttribute('position') as BufferAttribute | undefined;
    for (const handle of stored) {
      const i = this.handleIndex.get(handle.id);
      if (i !== undefined) {
        this.handles[i] = handle;
        positions?.setXYZ(i, ...handle.position);
      }
    }
    if (positions) {
      positions.needsUpdate = true;
    }
    this.applySelection(stored);
  }
}
