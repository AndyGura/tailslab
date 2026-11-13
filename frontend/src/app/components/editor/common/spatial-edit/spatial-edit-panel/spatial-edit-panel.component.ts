import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  EventEmitter,
  inject,
  Input,
  OnChanges,
  OnDestroy,
  Output,
  SimpleChanges,
} from '@angular/core';
import { Subject, takeUntil, merge } from 'rxjs';
import { Euler, MathUtils, Quaternion, Vector3 } from 'three';
import { GizmoMode, SpatialEditController, SpatialSnap } from '../spatial-edit.controller';
import { SpatialEditKind, SpatialHandle } from '../spatial-edit.types';
import { MatTooltip } from '@angular/material/tooltip';
import { MatIcon } from '@angular/material/icon';
import { MatProgressSpinner } from '@angular/material/progress-spinner';
import { FormsModule } from '@angular/forms';
import { UpperCasePipe } from '@angular/common';

// Material icons of the known kinds, others get a generic one
const KIND_ICONS: { [kind: string]: string } = {
  prop: 'park',
  terrain_vertex: 'terrain',
  road_point: 'timeline',
};

// The editor panel of a 3D viewport: edit mode (view only, or one of the spatial edit kinds the block declares), gizmo
// mode, the selection's transform (typed values are moves too: the centre of several handles moves them all) and how
// far the file's precision snapped it
@Component({
  selector: 'app-spatial-edit-panel',
  templateUrl: './spatial-edit-panel.component.html',
  styleUrls: ['./spatial-edit-panel.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatTooltip, MatIcon, MatProgressSpinner, FormsModule, UpperCasePipe],
})
export class SpatialEditPanelComponent implements OnChanges, OnDestroy {
  @Input() kinds: SpatialEditKind[] = [];
  @Input() activeKind: SpatialEditKind | null = null;
  @Input() controller: SpatialEditController | null = null;
  // chunks being written again / reloaded after an edit
  @Input() rebuilding: number = 0;
  @Output() activeKindChange = new EventEmitter<SpatialEditKind | null>();
  @Output() focusSelected = new EventEmitter<void>();

  selection: SpatialHandle[] = [];
  snap: SpatialSnap | null = null;
  committing = false;
  gizmoMode: GizmoMode = 'translate';
  // the selected transform shown in the inputs: position (the centre of several handles), rotation in degrees (one
  // handle only; yaw only for a kind turning around z)
  position: [number, number, number] = [0, 0, 0];
  rotationDegrees: [number, number, number] = [0, 0, 0];

  private readonly cdr = inject(ChangeDetectorRef);
  private readonly controllerChanged$ = new Subject<void>();

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['controller']) {
      this.controllerChanged$.next();
      const c = this.controller;
      if (c) {
        merge(c.selection$, c.snap$, c.committing$, c.gizmoMode$)
          .pipe(takeUntil(this.controllerChanged$))
          .subscribe(() => {
            this.selection = c.selection$.value;
            this.snap = c.snap$.value;
            this.committing = c.committing$.value;
            this.gizmoMode = c.gizmoMode$.value;
            this.updateInputs();
            this.cdr.markForCheck();
          });
      }
    }
  }

  ngOnDestroy(): void {
    this.controllerChanged$.next();
    this.controllerChanged$.complete();
  }

  kindIcon(kind: SpatialEditKind): string {
    return KIND_ICONS[kind.kind] || 'control_camera';
  }

  get yawOnly(): boolean {
    return this.activeKind?.rotate_axes === 'z';
  }

  get canTranslate(): boolean {
    return !!this.activeKind?.translate_axes;
  }

  get canRotate(): boolean {
    return !!this.activeKind?.rotate_axes;
  }

  // the rotation of several handles is turned with the gizmo only
  get showRotation(): boolean {
    return this.canRotate && this.selection.length === 1;
  }

  get selectionLabel(): string {
    if (this.selection.length === 1) {
      return this.selection[0].label;
    }
    return `${this.selection.length} ${this.activeKind?.title.toLowerCase() || ''} handles selected (centre)`;
  }

  axisEditable(axis: string, rotation: boolean): boolean {
    return (
      !this.committing && !!(rotation ? this.activeKind?.rotate_axes : this.activeKind?.translate_axes)?.includes(axis)
    );
  }

  setKind(kind: SpatialEditKind | null) {
    if (kind !== this.activeKind) {
      this.activeKindChange.emit(kind);
    }
  }

  setGizmoMode(mode: GizmoMode) {
    this.controller?.setGizmoMode(mode);
  }

  deselect() {
    this.controller?.select([]);
  }

  async moveToCentre() {
    await this.controller?.moveSelectionToCentre();
  }

  focus() {
    if (this.selection.length) {
      this.focusSelected.emit();
    }
  }

  // a value typed in: the new transform goes to the data like a gizmo move
  async applyInputs() {
    if (!this.controller || !this.selection.length) {
      return;
    }
    const position = new Vector3(...this.position.map(v => +v || 0));
    let rotation: Quaternion | null = null;
    if (this.showRotation) {
      const [x, y, z] = this.rotationDegrees.map(v => MathUtils.degToRad(+v || 0));
      rotation = new Quaternion().setFromEuler(new Euler(x, y, z, 'XYZ'));
    }
    await this.controller.moveSelection(position, rotation);
  }

  snapText(snap: SpatialSnap): string {
    const parts = [];
    if (snap.distance > 1e-4) {
      parts.push(snap.distance < 1 ? `${(snap.distance * 1000).toFixed(1)} mm` : `${snap.distance.toFixed(3)} m`);
    }
    if (snap.angle > 1e-4) {
      parts.push(`${MathUtils.radToDeg(snap.angle).toFixed(2)}°`);
    }
    return parts.join(', ');
  }

  private updateInputs() {
    const handle = this.selection[0];
    if (!handle || !this.controller) {
      return;
    }
    this.position = this.controller.pivotPosition.toArray().map(v => +v.toFixed(4)) as [number, number, number];
    const euler = new Euler().setFromQuaternion(new Quaternion().fromArray(handle.rotation || [0, 0, 0, 1]), 'XYZ');
    this.rotationDegrees = [euler.x, euler.y, euler.z].map(v => +MathUtils.radToDeg(v).toFixed(2)) as [
      number,
      number,
      number,
    ];
  }
}
