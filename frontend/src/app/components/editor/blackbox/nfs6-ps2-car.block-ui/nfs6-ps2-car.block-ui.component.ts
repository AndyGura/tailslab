import {
  AfterViewInit,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  inject,
  OnChanges,
  OnDestroy,
  SimpleChanges,
} from '@angular/core';
import { GuiComponent } from '../../gui.component';
import { BehaviorSubject, debounceTime, filter, Subject, takeUntil } from 'rxjs';
import { Object3D } from 'three';
import { ObjViewerCustomControl, ViewFilterOpts } from '../../common/obj-viewer/obj-viewer.component';
import { steeringControl, wheelSpeedControl } from '../../common/obj-viewer/car-preview-controls';
import {
  Nfs6Ps2CarInfo,
  Nfs6Ps2CarMeshController,
  Nfs6Ps2CarSkin,
} from '../../../../../nfs-three-lib/nfs6-ps2-car-mesh-controller';

// NFS Hot Pursuit 2 PS2 car model (CARS/<car>/GEOMETRY.LZC): 3D preview of the serialized OBJ with LOD filter, paint
// switcher, lights and wheel controls (`Nfs6Ps2CarMeshController`)
@Component({
  selector: 'app-nfs6-ps2-car-block-ui',
  templateUrl: './nfs6-ps2-car.block-ui.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: false,
})
export class Nfs6Ps2CarBlockUiComponent extends GuiComponent implements AfterViewInit, OnChanges, OnDestroy {
  previewPaths$: BehaviorSubject<[string, string] | null> = new BehaviorSubject<[string, string] | null>(null);

  readonly cdr = inject(ChangeDetectorRef);

  customControls: ObjViewerCustomControl[] = [];

  private carPath: string | null = null;
  private skinsPath: string | null = null;
  private meshController: Nfs6Ps2CarMeshController | null = null;

  private readonly destroyed$: Subject<void> = new Subject<void>();

  async ngAfterViewInit() {
    this.changes.change$
      .pipe(
        takeUntil(this.destroyed$),
        filter(x => !!(this.resourceId && x.startsWith(this.resourceId))),
        debounceTime(150),
      )
      .subscribe(async () => {
        await this.loadPreview();
      });
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.hasOwnProperty('resourceId') || changes.hasOwnProperty('resourceData')) {
      this.loadPreview().then();
    }
  }

  private async loadPreview() {
    this.previewPaths$.next(null);
    if (this.resourceId) {
      const paths = await this.mainService.api.serializeResource(this.resourceId, null, {
        geometry__save_obj: true,
        geometry__save_blend: false,
        geometry__export_to_gg_web_engine: false,
      });
      this.carPath = paths.find(x => x.endsWith('/car.json')) || null;
      this.skinsPath = paths.find(x => x.endsWith('/skins.json')) || null;
      this.previewPaths$.next([paths.find(x => x.endsWith('.obj'))!, paths.find(x => x.endsWith('.mtl'))!]);
    }
  }

  async onObjectLoaded(obj: Object3D) {
    this.meshController?.dispose();
    this.meshController = null;
    this.customControls = [];
    if (!this.carPath) {
      this.cdr.markForCheck();
      return;
    }
    try {
      const loadJson = async (path: string | null) => {
        try {
          return path ? await (await fetch(path)).json() : null;
        } catch (err) {
          console.warn(`Cannot load ${path}`, err);
          return null;
        }
      };
      const info: Nfs6Ps2CarInfo = await loadJson(this.carPath);
      const skins: Nfs6Ps2CarSkin[] = (await loadJson(this.skinsPath)) || [];
      const baseUrl = this.carPath.substring(0, this.carPath.lastIndexOf('/') + 1);
      // OBJLoader reads the vertex colours as sRGB
      const meshController = new Nfs6Ps2CarMeshController(obj, info, skins, baseUrl, { srgbVertexColors: true });
      this.meshController = meshController;
      const controls: ObjViewerCustomControl['controls'] = [];
      if (meshController.skin && skins.length > 1) {
        const label = (skin: Nfs6Ps2CarSkin) => `${skin.label} (${skin.name})`;
        controls.push({
          label: 'Paint',
          type: 'radio',
          options: skins.map(label),
          value: label(skins[0]),
          change: v => (meshController.skin = skins.find(x => label(x) === v)?.name || null),
        });
      }
      if (meshController.hasGameShading) {
        controls.push(
          {
            label: 'Reflections',
            type: 'checkbox',
            value: meshController.envEnabled,
            change: v => (meshController.envEnabled = v),
          },
          {
            label: 'Race materials',
            type: 'checkbox',
            value: meshController.raceMaterials,
            change: v => (meshController.raceMaterials = v),
          },
        );
      }
      if (meshController.hasLights) {
        controls.push(
          {
            label: 'Headlights',
            type: 'checkbox',
            value: meshController.headlightsOn,
            change: v => (meshController.headlightsOn = v),
          },
          {
            label: 'Brake lights',
            type: 'checkbox',
            value: meshController.brakeLightsOn,
            change: v => (meshController.brakeLightsOn = v),
          },
        );
      }
      if (meshController.hasWheels) {
        controls.push(
          wheelSpeedControl(v => (meshController.speed = v)),
          steeringControl(v => (meshController.steeringAngle = v)),
        );
      }
      this.customControls = controls.length > 0 ? [{ title: 'Car features', controls }] : [];
    } catch (err) {
      console.error(err);
    }
    this.cdr.markForCheck();
  }

  // object name: <lod>_<part>__<material>. The wheel blur discs (drawn at speed instead of the tyres) and the scuffs
  // (drawn on a damaged car) are groups of their own
  readonly previewViewFilters: ViewFilterOpts[] = [
    {
      name: 'LOD',
      filterGroups: ['High-poly', 'Medium-poly', 'Low-poly', 'Lowest-poly', 'Wheel blur', 'Scuffs'],
      checkedIndex: 0,
      pickFunction: object => {
        if (object.name.includes('_wheel_blur_')) {
          return 4;
        }
        if (object.name.includes('_scuffs__')) {
          return 5;
        }
        const index = ['hp_', 'mp_', 'lp_', 'vlp_'].findIndex(x => object.name.startsWith(x));
        return index >= 0 ? index : 0;
      },
    },
  ];

  ngOnDestroy(): void {
    this.meshController?.dispose();
    this.destroyed$.next();
    this.destroyed$.complete();
  }
}
