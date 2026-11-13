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
import { Object3D, Texture, TextureLoader } from 'three';
import {
  ObjViewerCustomControl,
  ViewFilterOpts,
  ObjViewerComponent,
} from '../../common/obj-viewer/obj-viewer.component';
import { steeringControl, wheelSpeedControl } from '../../common/obj-viewer/car-preview-controls';
import {
  Nfs6CarDummy,
  Nfs6CarLighting,
  Nfs6CarMeshController,
  Nfs6CarMeshProperties,
  Nfs6CarSkin,
} from '../../../../../nfs-three-lib/nfs6-car-mesh-controller';
import { proceduralSkySun } from '../../../../../nfs-three-lib/scene-sky';
import { VIEWER_SKY } from '../../common/obj-viewer/viewer-sky';
import { CompoundBlockUiComponent } from '../../library/compound.block-ui/compound.block-ui.component';
import { AsyncPipe } from '@angular/common';

// the environment map of the car: the location's staticenvmap.fsh (a race), Cars/common.fsh "refl" (the frontend)
const ENVIRONMENT_TRACK = 'Track';
const ENVIRONMENT_SHOWROOM = 'Showroom';
// lighting / environment map of the viewer's sky
const ENVIRONMENT_SCENE = 'Scene';

// NFS6 EAGL model (".o" file): 3D preview of the serialized OBJ, textured from the FSH file the model uses. Car
// models (car.o in car.viv) are exported with "skins.json" and "lighting.json": they get LOD filter, skin switcher,
// wheel controls and the game's shading (Nfs6CarMeshController), lit by a track location (Parkland by default) or the
// viewer's sky
@Component({
  selector: 'app-eagl-model-block-ui',
  templateUrl: './eagl-model.block-ui.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ObjViewerComponent, CompoundBlockUiComponent, AsyncPipe],
})
export class EaglModelBlockUiComponent extends GuiComponent implements AfterViewInit, OnChanges, OnDestroy {
  previewPaths$: BehaviorSubject<[string, string] | null> = new BehaviorSubject<[string, string] | null>(null);

  readonly cdr = inject(ChangeDetectorRef);

  customControls: ObjViewerCustomControl[] = [];
  previewViewFilters: ViewFilterOpts[] = [];

  private extraPath: string | null = null;
  private skinsPath: string | null = null;
  private lightingPath: string | null = null;
  private meshController: Nfs6CarMeshController | null = null;
  // environment maps by URL, owned by the component
  private readonly environmentMaps = new Map<string, Texture>();

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
      this.extraPath = paths.find(x => x.endsWith('_extra.json')) || null;
      this.skinsPath = paths.find(x => x.endsWith('/skins.json')) || null;
      this.lightingPath = paths.find(x => x.endsWith('/lighting.json')) || null;
      const viewFilters = this.skinsPath ? [this.lodViewFilter] : [];
      if (viewFilters.length !== this.previewViewFilters.length) {
        this.previewViewFilters = viewFilters;
        this.cdr.markForCheck();
      }
      this.previewPaths$.next([paths.find(x => x.endsWith('.obj'))!, paths.find(x => x.endsWith('.mtl'))!]);
    }
  }

  async onObjectLoaded(obj: Object3D) {
    this.meshController?.dispose();
    this.meshController = null;
    this.customControls = [];
    if (!this.skinsPath) {
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
      const extra = await loadJson(this.extraPath);
      const dummies: Nfs6CarDummy[] = extra?.dummies || [];
      const objects: { [name: string]: Nfs6CarMeshProperties } | null = extra?.objects || null;
      const skins: Nfs6CarSkin[] = (await loadJson(this.skinsPath)) || [];
      const lighting: Nfs6CarLighting | null = await loadJson(this.lightingPath);
      const meshController = new Nfs6CarMeshController(obj, dummies, skins, lighting, objects);
      this.meshController = meshController;
      // relative to lighting.json
      const lightingDir = (this.lightingPath || '').replace(/[^/]*$/, '');
      let environment = ENVIRONMENT_TRACK;
      const updateEnvironmentMap = () => {
        const path =
          environment === ENVIRONMENT_SHOWROOM ? lighting?.environment_map : meshController.location.environment_map;
        meshController.sceneReflection = environment === ENVIRONMENT_SCENE;
        meshController.environmentMap = path ? this.environmentMap(lightingDir + path) : null;
      };
      updateEnvironmentMap();
      const controls: ObjViewerCustomControl['controls'] = [];
      const locations = lighting?.locations || [];
      if (meshController.hasGameShading) {
        controls.push({
          label: 'Lighting',
          type: 'radio',
          // a car without lighting.json: NFS6_DEFAULT_LOCATION
          options: [...(locations.length ? locations : [meshController.location]).map(x => x.name), ENVIRONMENT_SCENE],
          value: meshController.location.name,
          change: v => {
            meshController.sceneLighting = v === ENVIRONMENT_SCENE ? proceduralSkySun(VIEWER_SKY) : null;
            meshController.location = locations.find(x => x.name === v) || meshController.location;
            updateEnvironmentMap();
          },
        });
        controls.push({
          label: 'Reflection',
          type: 'radio',
          options: [ENVIRONMENT_TRACK, ...(lighting?.environment_map ? [ENVIRONMENT_SHOWROOM] : []), ENVIRONMENT_SCENE],
          value: environment,
          change: v => {
            environment = v;
            updateEnvironmentMap();
          },
        });
        controls.push({
          label: 'Road light level',
          type: 'slider',
          value: meshController.lightLevel,
          minValue: 0,
          maxValue: 1,
          valueStep: 0.05,
          format: v => v.toFixed(2),
          change: v => (meshController.lightLevel = v),
        });
      }
      if (meshController.skin && skins.length > 1) {
        const label = (skin: Nfs6CarSkin) => `${skin.label} (${skin.name})`;
        controls.push({
          label: 'Skin',
          type: 'radio',
          options: skins.map(label),
          value: label(skins[0]),
          change: v => (meshController.skin = skins.find(x => label(x) === v)?.name || null),
        });
      }
      if (meshController.hasLights) {
        controls.push({
          label: 'Show lights',
          type: 'checkbox',
          value: meshController.showLights,
          change: v => (meshController.showLights = v),
        });
      }
      if (meshController.hasWheels) {
        controls.push(
          wheelSpeedControl(v => (meshController.speed = v)),
          steeringControl(v => (meshController.steeringAngle = v)),
        );
      }
      this.customControls = controls.length > 0 ? [{ title: 'NFS6 car features', controls }] : [];
    } catch (err) {
      console.error(err);
    }
    this.cdr.markForCheck();
  }

  // car mesh name: <lod>_<geometry index>_<geometry name>
  private readonly lodViewFilter: ViewFilterOpts = {
    name: 'LOD',
    filterGroups: ['High-poly', 'Medium-poly', 'Low-poly', 'Other'],
    checkedIndex: 0,
    pickFunction: object => {
      const index = ['hp_', 'mp_', 'lp_'].findIndex(x => object.name.startsWith(x));
      return index >= 0 ? index : 3;
    },
  };

  private environmentMap(url: string): Texture {
    let texture = this.environmentMaps.get(url);
    if (!texture) {
      // texels as stored: the shader reads them as the game does
      texture = new TextureLoader().load(url);
      this.environmentMaps.set(url, texture);
    }
    return texture;
  }

  ngOnDestroy(): void {
    this.meshController?.dispose();
    for (const texture of this.environmentMaps.values()) {
      texture.dispose();
    }
    this.environmentMaps.clear();
    this.destroyed$.next();
    this.destroyed$.complete();
  }
}
