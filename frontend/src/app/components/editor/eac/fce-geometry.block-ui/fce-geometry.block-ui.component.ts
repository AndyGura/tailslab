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
import {
  ObjViewerControl,
  ObjViewerCustomControl,
  ViewFilterOpts,
  ObjViewerComponent,
} from '../../common/obj-viewer/obj-viewer.component';
import { steeringControl, wheelSpeedControl } from '../../common/obj-viewer/car-preview-controls';
import { Box3, BufferAttribute, Mesh, Object3D, Vector3 } from 'three';
import {
  FceCarMeshController,
  FceColor,
  fce3HsbToRgb,
  FceDummy,
  FceVersion,
  FceWheelPosition,
  rgbToFceColor,
} from '../../../../../nfs-three-lib/fce-car-mesh-controller';
import { Fce4CarParts } from '../../../../../nfs-three-lib/fce4-car-parts';
import { CompoundBlockUiComponent } from '../../library/compound.block-ui/compound.block-ui.component';
import { AsyncPipe } from '@angular/common';

const rgbOf = ([r, g, b]: [number, number, number]): number => (r << 16) | (g << 8) | b;

const DEGREES = Math.PI / 180;

const WHEELS: [string, FceWheelPosition | null][] = [
  ['None', null],
  ['Front left', 'frontLeft'],
  ['Front right', 'frontRight'],
  ['Rear left', 'rearLeft'],
  ['Rear right', 'rearRight'],
];

/** A slider of an angle in degrees, `change` gets radians */
const angleControl = (
  label: string,
  min: number,
  max: number,
  change: (radians: number) => void,
): ObjViewerControl => ({
  label,
  type: 'slider',
  minValue: min,
  maxValue: max,
  valueStep: 1,
  value: 0,
  format: v => `${v}°`,
  change: v => change(v * DEGREES),
});

@Component({
  selector: 'app-fce-geometry-block-ui',
  templateUrl: './fce-geometry.block-ui.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ObjViewerComponent, CompoundBlockUiComponent, AsyncPipe],
})
export class FceGeometryBlockUiComponent extends GuiComponent implements AfterViewInit, OnChanges, OnDestroy {
  customControls: ObjViewerCustomControl[] = [];

  previewPaths$: BehaviorSubject<[string, string] | null> = new BehaviorSubject<[string, string] | null>(null);

  readonly cdr = inject(ChangeDetectorRef);

  previewViewFilters: ViewFilterOpts[] = [];

  private extraPath: string | null = null;
  private meshController: FceCarMeshController | null = null;

  private readonly destroyed$: Subject<void> = new Subject<void>();

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.hasOwnProperty('resourceSchema')) {
      // FCE4's damaged copies: the controller's damage controls
      this.previewViewFilters = [this.previewViewFilter];
    }
    if (changes.hasOwnProperty('resourceId') || changes.hasOwnProperty('resourceData')) {
      this.loadPreview().then();
    }
  }

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

  async onObjectLoaded(obj: Object3D) {
    try {
      this.meshController?.dispose();
      let extra: any = {};
      if (this.extraPath) {
        try {
          extra = await (await fetch(this.extraPath)).json();
        } catch (err) {
          console.warn('Cannot load FCE dummies', err);
        }
      }
      const dummies: FceDummy[] = extra.dummies || [];
      if (this.version === 4) {
        this.setTurningVertices(obj, extra.fceTurns || {});
      }
      // default paint is the first color of the car
      const paints = this.paints;
      const meshController = new FceCarMeshController(
        obj,
        this.version,
        dummies,
        paints.map(x => x.color),
        undefined,
        {
          partPositions: extra.fcePartPositions,
          halfSize: this.resourceData?.half_size ?? null,
          // the broken glass texture is in another file (Data/FeArt/3dobj.fsh shat): cracked windows look as before
          brokenGlassTexture: null,
        },
      );
      this.meshController = meshController;
      const controls: ObjViewerCustomControl['controls'] = [];
      if (meshController.isPaintable) {
        paints.forEach(({ label, color }, i) =>
          controls.push({
            label,
            type: 'color',
            value: rgbOf(fce3HsbToRgb(color)),
            // the picked color keeps the transparency of the car's color: it shades the paint (nfs3.exe)
            change: c => this.debounced(() => meshController.setColor(i, rgbToFceColor(c, color.transparency))),
          }),
        );
      }
      if (meshController.hasChrome) {
        // reflects the viewer's sky (no chromeTexture)
        controls.push({
          label: 'Chrome',
          type: 'checkbox',
          value: meshController.chromeEnabled,
          change: v => (meshController.chromeEnabled = v),
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
          {
            label: 'Handbrake',
            type: 'checkbox',
            value: meshController.handbrake,
            change: v => (meshController.handbrake = v),
          },
        );
      }
      this.customControls = controls.length > 0 ? [{ title: `NFS${this.version} car features`, controls }] : [];
      if (meshController.parts) {
        this.customControls.push(...this.fce4Controls(meshController, meshController.parts, obj));
      }
      this.cdr.markForCheck();
    } catch (err) {
      console.error(err);
    }
  }

  /** NFS4 controls: the parts nfs4.exe draws by the car's state, the wheels and the damage of hits */
  private fce4Controls(controller: FceCarMeshController, parts: Fce4CarParts, obj: Object3D): ObjViewerCustomControl[] {
    const partControls: ObjViewerControl[] = [];
    const checkbox = (label: string, value: boolean, change: (v: boolean) => void): ObjViewerControl => ({
      label,
      type: 'checkbox',
      value,
      change,
    });
    if (parts.has('OL') || parts.has('ODL')) {
      partControls.push(checkbox('Headlights (pop-ups, lit dashboard)', parts.headlights, v => (parts.headlights = v)));
    }
    if (parts.has('OT')) {
      partControls.push(checkbox('Roof closed', parts.roofClosed, v => (parts.roofClosed = v)));
    }
    if (parts.has('OD') || parts.has('OND')) {
      partControls.push(checkbox('Driver in the car', parts.driverInCar, v => (parts.driverInCar = v)));
    }
    if (parts.has('OH')) {
      // the game's limit: 0.2 turn
      partControls.push(angleControl('Driver head turn', -72, 72, v => (parts.driverHeadYaw = v)));
    }
    if (parts.has('OS')) {
      // the air brake's angle braking: 0.25 turn
      partControls.push(angleControl('Spoiler angle', 0, 90, v => (parts.spoilerAngle = v)));
    }
    partControls.push(
      angleControl('Body pitch (nose down)', -10, 10, v => (parts.bodyPitch = v)),
      angleControl('Body roll (right side up)', -10, 10, v => (parts.bodyRoll = v)),
    );
    const wheelControls: ObjViewerControl[] = [];
    if (controller.hasWheels) {
      const damage = (label: string, positions: FceWheelPosition[]): ObjViewerControl => ({
        label,
        type: 'slider',
        minValue: 0,
        maxValue: 1,
        valueStep: 0.05,
        value: 0,
        change: v => positions.forEach(p => controller.setWheelDamage(p, v)),
      });
      let hidden: FceWheelPosition | null = null;
      wheelControls.push(
        damage('Front wheels damage', ['frontLeft', 'frontRight']),
        damage('Rear wheels damage', ['rearLeft', 'rearRight']),
        checkbox('Front wheels slide', false, v => (controller.frontSliding = v)),
        checkbox('Rear wheels slide', false, v => (controller.rearSliding = v)),
        {
          label: 'Hidden wheel (spike strips)',
          type: 'radio',
          options: WHEELS.map(([label]) => label),
          value: WHEELS[0][0],
          change: v => {
            if (hidden) {
              controller.setWheelHidden(hidden, false);
            }
            hidden = WHEELS.find(([label]) => label === v)?.[1] ?? null;
            if (hidden) {
              controller.setWheelHidden(hidden, true);
            }
          },
        },
      );
    }
    const result: ObjViewerCustomControl[] = [
      { title: 'NFS4 parts', controls: partControls },
      ...(wheelControls.length ? [{ title: 'NFS4 wheels', controls: wheelControls }] : []),
    ];
    if (parts.hasDamage) {
      // hits on the middle of the high poly body's sides
      const box = new Box3();
      obj.traverse(o => {
        if (o instanceof Mesh && /^hp_\d+_HB(?=__|$)/.test(o.name)) {
          o.geometry.computeBoundingBox();
          box.union(o.geometry.boundingBox!);
        }
      });
      const c = box.getCenter(new Vector3());
      const hit = { amount: 1, radius: 1 };
      const hitButton = (label: string, point: Vector3): ObjViewerControl => ({
        label,
        type: 'button',
        click: () => parts.hit(point, hit.amount, hit.radius),
      });
      result.push({
        title: 'NFS4 damage',
        controls: [
          {
            label: 'Hit amount',
            type: 'slider',
            minValue: 0,
            maxValue: 1,
            valueStep: 0.05,
            value: hit.amount,
            change: v => (hit.amount = v),
          },
          {
            label: 'Hit radius',
            type: 'slider',
            minValue: 0.1,
            maxValue: 3,
            valueStep: 0.1,
            value: hit.radius,
            format: v => `${v.toFixed(1)} m`,
            change: v => (hit.radius = v),
          },
          hitButton('Hit front', new Vector3(c.x, box.max.y, c.z)),
          hitButton('Hit rear', new Vector3(c.x, box.min.y, c.z)),
          hitButton('Hit left', new Vector3(box.min.x, c.y, c.z)),
          hitButton('Hit right', new Vector3(box.max.x, c.y, c.z)),
          hitButton('Hit top', new Vector3(c.x, c.y, box.max.z)),
          { label: 'Repair', type: 'button', click: () => parts.repair() },
        ],
      });
    }
    return result;
  }

  /**
   * The vertices of :OD and :OH that turn, from the OBJ's extra JSON (`fceTurns`: 1 or 0 per face corner, the OBJ
   * loader's vertex order), as the geometry attribute FceCarMeshController reads (the GLB's `_FCE_TURNS`)
   */
  private setTurningVertices(obj: Object3D, turns: { [mesh: string]: number[] }) {
    obj.traverse(o => {
      const values = turns[o.name];
      if (o instanceof Mesh && values && values.length === o.geometry.getAttribute('position').count) {
        o.geometry.setAttribute('_fce_turns', new BufferAttribute(Float32Array.from(values), 1));
      }
    });
  }

  get version(): FceVersion {
    return this.resourceSchema?.block_class_mro?.startsWith('Fce4Geometry') ? 4 : 3;
  }

  /** Colors of car paint: the first color set of the model */
  private get paints(): { label: string; color: FceColor }[] {
    const data = this.resourceData;
    const paint = (label: string, colorsKey: string, numColors: number, fallback: number) => ({
      label,
      // fallback: transparency 127, texel blue 128 shows the brightness
      color: numColors > 0 ? { ...data[colorsKey][0] } : rgbToFceColor(fallback, 127),
    });
    if (this.version === 4) {
      return [
        paint('Primary color', 'primary_colors', data?.num_colors, 0xff0000),
        paint('Interior color', 'interior_colors', data?.num_colors, 0x404040),
        paint('Secondary color', 'secondary_colors', data?.num_colors, 0x808080),
        paint('Driver hair color', 'driver_hair_colors', data?.num_colors, 0x302010),
      ];
    }
    return [
      paint('Primary color', 'primary_colors', data?.num_primary_colors, 0xff0000),
      paint('Secondary color', 'secondary_colors', data?.num_secondary_colors, 0x808080),
    ];
  }

  private debounceTimer: any = null;

  private debounced(func: () => void) {
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }
    this.debounceTimer = setTimeout(func, 50);
  }

  private serializerSettings = {
    geometry__save_obj: true,
    geometry__save_blend: false,
    geometry__export_to_gg_web_engine: false,
  };

  private async loadPreview() {
    this.previewPaths$.next(null);
    if (this.resourceId) {
      const paths = await this.mainService.api.serializeResource(this.resourceId, null, this.serializerSettings);
      this.extraPath = paths.find(x => x.endsWith('_extra.json')) || null;
      this.previewPaths$.next([paths.find(x => x.endsWith('.obj'))!, paths.find(x => x.endsWith('.mtl'))!]);
    }
  }

  // mesh name: <lod>_<part index>[_<part name>][__<texture>][_damaged]
  previewObjectGroupFunc(object: Object3D): string {
    const match = /^(?:hp|mp|lp|tp|part)_\d+(?:_.*?)?(?=__|_damaged$|$)/.exec(object.name);
    return match ? match[0] : object.name;
  }

  private readonly previewViewFilter: ViewFilterOpts = {
    name: 'LOD',
    filterGroups: ['High-poly', 'Medium-poly', 'Low-poly', 'Tiny', 'Other'],
    checkedIndex: 0,
    pickFunction: object => {
      const index = ['hp_', 'mp_', 'lp_', 'tp_'].findIndex(x => object.name.startsWith(x));
      return index >= 0 ? index : 4;
    },
  };

  ngOnDestroy(): void {
    this.meshController?.dispose();
    this.destroyed$.next();
    this.destroyed$.complete();
  }
}
