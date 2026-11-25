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
  ObjViewerComponent,
} from '../../common/obj-viewer/obj-viewer.component';
import { steeringControl, wheelSpeedControl } from '../../common/obj-viewer/car-preview-controls';
import { Object3D, Vector3 } from 'three';
import {
  NFS5_ANIMATIONS,
  NFS5_ZONE_NAMES,
  NFS5_ZONES,
  Nfs5CarData,
  Nfs5CarMeshController,
} from '../../../../../nfs-three-lib/nfs5-car-mesh-controller';
import { TrackMapBlockUiComponent } from '../track-map.block-ui/track-map.block-ui.component';
import { CompoundBlockUiComponent } from '../../library/compound.block-ui/compound.block-ui.component';
import { AsyncPipe } from '@angular/common';

const DEGREES = Math.PI / 180;

const checkbox = (label: string, value: boolean, change: (v: boolean) => void): ObjViewerControl => ({
  label,
  type: 'checkbox',
  value,
  change,
});

const slider = (
  label: string,
  minValue: number,
  maxValue: number,
  valueStep: number,
  value: number,
  change: (v: number) => void,
  format?: (v: number) => string,
): ObjViewerControl => ({ label, type: 'slider', minValue, maxValue, valueStep, value, change, format });

// hits along the car's axes: the push on the car, model axes (x left, y backward, z up)
const HITS: [string, Vector3][] = [
  ['Hit front', new Vector3(0, 1, 0)],
  ['Hit rear', new Vector3(0, -1, 0)],
  ['Hit left', new Vector3(-1, 0, 0)],
  ['Hit right', new Vector3(1, 0, 0)],
  ['Hit front left', new Vector3(-1, 1, 0).normalize()],
  ['Hit front right', new Vector3(1, 1, 0).normalize()],
  ['Hit rear left', new Vector3(-1, -1, 0).normalize()],
  ['Hit rear right', new Vector3(1, -1, 0).normalize()],
  ['Hit roof', new Vector3(0, 0, -1)],
];

const DETAILS = ['Low', 'Medium', 'High'];

// NFS5 CRP geometry: cars open in the 3D model viewer, tracks ("karT") in the shared track viewer
@Component({
  selector: 'app-crp-geometry-block-ui',
  templateUrl: './crp-geometry.block-ui.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TrackMapBlockUiComponent, ObjViewerComponent, CompoundBlockUiComponent, AsyncPipe],
})
export class CrpGeometryBlockUiComponent extends GuiComponent implements AfterViewInit, OnChanges, OnDestroy {
  previewPaths$: BehaviorSubject<[string, string] | null> = new BehaviorSubject<[string, string] | null>(null);

  isTrack$: BehaviorSubject<boolean> = new BehaviorSubject<boolean>(false);

  customControls: ObjViewerCustomControl[] = [];

  readonly cdr = inject(ChangeDetectorRef);

  private meshController: Nfs5CarMeshController | null = null;

  private extraPath: string | null = null;

  private readonly destroyed$: Subject<void> = new Subject<void>();

  async ngAfterViewInit() {
    this.changes.change$
      .pipe(
        takeUntil(this.destroyed$),
        filter(x => !this.isTrack$.value && !!(this.resourceId && x.startsWith(this.resourceId))),
        debounceTime(150),
      )
      .subscribe(async () => {
        await this.loadPreview();
      });
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.hasOwnProperty('resourceId') || changes.hasOwnProperty('resourceData')) {
      this.isTrack$.next(this.resourceData?.resource_id === 'karT');
      this.loadPreview().then();
    }
  }

  // mesh name: <article name>_a<article index>_LOD<lod>_ai<animation frame>[_<texture>][_damaged]
  previewObjectGroupFunc(object: Object3D): string {
    const info = Nfs5CarMeshController.parseMeshName(object.name);
    return info
      ? `${info.article}${info.articleIndex !== null ? ` #${info.articleIndex}` : ''} LOD${info.lod}` +
          (info.isDamaged ? ' damaged' : '')
      : object.name;
  }

  async onObjectLoaded(obj: Object3D) {
    try {
      this.meshController?.dispose();
      let extra: any = {};
      if (this.extraPath) {
        try {
          extra = await (await fetch(this.extraPath)).json();
        } catch (err) {
          console.warn('Cannot load the NFS5 car data', err);
        }
      }
      const car: Nfs5CarData | null = extra.nfs5Car ?? null;
      const controller = new Nfs5CarMeshController(obj, { car, damageZones: extra.nfs5DamageZones ?? null });
      this.meshController = controller;
      this.state = { tach: 0, speedo: 0, lateral: 0, longitudinal: 0, reverse: false, hitSpeed: 100 };
      this.customControls = this.controls(controller);
      this.cdr.markForCheck();
    } catch (err) {
      console.error(err);
    }
  }

  private state = { tach: 0, speedo: 0, lateral: 0, longitudinal: 0, reverse: false, hitSpeed: 100 };

  private refreshControls(c: Nfs5CarMeshController) {
    this.customControls = this.controls(c);
    this.cdr.markForCheck();
  }

  /** The controls of every state Porsche.exe changes on a car (Nfs5CarMeshController) */
  private controls(c: Nfs5CarMeshController): ObjViewerCustomControl[] {
    if (!c.hasModelData) {
      return c.hasWheels
        ? [
            {
              title: 'NFS5 car features',
              controls: [wheelSpeedControl(v => (c.speed = v)), steeringControl(v => (c.steeringAngle = v))],
            },
          ]
        : [];
    }
    const s = this.state;
    const drivers = ['None', ...Array.from({ length: 8 }, (_, i) => `Driver ${i}`)];
    const car: ObjViewerControl[] = [];
    if (c.styleNames.length) {
      car.push({
        label: 'Body style',
        type: 'radio',
        options: c.styleNames,
        value: c.styleNames[c.bodyStyle] ?? c.styleNames[0],
        change: v => {
          c.bodyStyle = Math.max(0, c.styleNames.indexOf(v));
          // the convertible top depends on the style
          this.refreshControls(c);
        },
      });
    }
    car.push(
      {
        label: 'Driver (the front end draws 0..7)',
        type: 'radio',
        options: drivers,
        value: c.driver === null ? 'None' : `Driver ${c.driver}`,
        change: v => (c.driver = v === 'None' ? null : drivers.indexOf(v) - 1),
      },
      {
        label: 'View',
        type: 'radio',
        options: ['Outside', 'In-car'],
        value: c.view === 'cockpit' ? 'In-car' : 'Outside',
        change: v => (c.view = v === 'In-car' ? 'cockpit' : 'outside'),
      },
      slider('Level of detail (by distance)', 0, 6, 1, c.lod, v => (c.lod = v)),
      {
        label: 'Car detail (game option)',
        type: 'radio',
        options: DETAILS,
        value: DETAILS[c.detail],
        change: v => (c.detail = DETAILS.indexOf(v)),
      },
    );
    if (c.hasCabrio) {
      car.push(checkbox('Convertible top down', c.cabrioDown, v => (c.cabrioDown = v)));
    }
    car.push(
      checkbox('Race number (decals)', c.raceNumber, v => (c.raceNumber = v)),
      checkbox('Tiny car cheat (antenna)', c.tinyCar, v => (c.tinyCar = v)),
    );

    const motion = () => c.setDriverMotion(s.lateral, s.longitudinal, s.reverse);
    const driving: ObjViewerControl[] = [
      wheelSpeedControl(v => (c.speed = v)),
      steeringControl(v => (c.steeringAngle = v)),
      slider(
        'Rev counter needle',
        -0.5,
        0.5,
        0.01,
        s.tach,
        v => c.setNeedles((s.tach = v), s.speedo),
        v => `${v} turn`,
      ),
      slider(
        'Speedometer needle',
        -0.5,
        0.5,
        0.01,
        s.speedo,
        v => c.setNeedles(s.tach, (s.speedo = v)),
        v => `${v} turn`,
      ),
      slider(
        'Lateral acceleration (driver)',
        -20,
        20,
        0.5,
        s.lateral,
        v => {
          s.lateral = v;
          motion();
        },
        v => `${v} m/s²`,
      ),
      slider(
        'Longitudinal acceleration (driver)',
        -20,
        20,
        0.5,
        s.longitudinal,
        v => {
          s.longitudinal = v;
          motion();
        },
        v => `${v} m/s²`,
      ),
      checkbox('Reversing (the driver looks back)', s.reverse, v => {
        s.reverse = v;
        motion();
      }),
      checkbox('Horn (right arm)', c.horn, v => (c.horn = v)),
    ];
    if (c.animationFrames(2)) {
      driving.push(slider('Speed wing raised', 0, 1, 0.05, c.wing, v => (c.wing = v)));
    }

    const parts: ObjViewerControl[] = [
      slider('Hood open', 0, 1, 0.05, c.hoodOpen, v => (c.hoodOpen = v)),
      slider('Trunk open', 0, 1, 0.05, c.trunkOpen, v => (c.trunkOpen = v)),
      slider(
        'Left door',
        0,
        90,
        1,
        0,
        v => c.setDoorOpen('left', (v * DEGREES) / (2 * Math.PI)),
        v => `${v}°`,
      ),
      slider(
        'Right door',
        0,
        90,
        1,
        0,
        v => c.setDoorOpen('right', (v * DEGREES) / (2 * Math.PI)),
        v => `${v}°`,
      ),
      slider('Moving spoiler raised', 0, 1, 0.05, c.moveSpoiler, v => (c.moveSpoiler = v)),
    ];
    if (c.animationFrames(1)) {
      parts.push(
        slider('Convertible top animation (front end)', 0, 1, 0.05, c.cabrioAnimation, v => (c.cabrioAnimation = v)),
      );
    }
    // the parts' geometry switches (the record's GEOMCONFIG) over the race's slots
    for (const choice of c.slotChoices) {
      if (choice.values.length < 2) {
        continue;
      }
      const options = ['Race', ...choice.values.map(String)];
      const config = c.getGeometryConfig();
      const articles = choice.articles.slice(0, 4).join(', ') + (choice.articles.length > 4 ? '...' : '');
      parts.push({
        label: `Slot ${choice.slot} (${articles})`,
        type: 'radio',
        options,
        value: config[choice.slot] >= 0 ? String(config[choice.slot]) : 'Race',
        change: v => {
          const next = c.getGeometryConfig();
          next[choice.slot] = v === 'Race' ? -1 : +v;
          c.setGeometryConfig(next);
        },
      });
    }

    const lights: ObjViewerControl[] = [
      checkbox('Headlights', false, v => c.setLights({ headlights: v })),
      checkbox('Braking', false, v => c.setLights({ brake: v })),
      checkbox('Reverse gear', false, v => c.setLights({ reverse: v })),
      checkbox('Left indicator', false, v => c.setLights({ left: v })),
      checkbox('Right indicator', false, v => c.setLights({ right: v })),
      checkbox('Hazard lights (out of the race)', false, v => c.setLights({ hazard: v })),
      checkbox('Blink phase', false, v => c.setLights({ blink: v })),
    ];
    if (c.hasPopUpHeadlights) {
      lights.push(slider('Pop-up headlights raised', 0, 1, 0.05, 0, v => c.setLights({ popUp: v })));
    }
    if (c.hasGlares) {
      lights.push(checkbox('Show glares', c.showGlares, v => (c.showGlares = v)));
    }

    const result: ObjViewerCustomControl[] = [
      { title: 'NFS5 car', controls: car },
      { title: 'NFS5 driving', controls: driving },
      { title: 'NFS5 parts', controls: parts },
      { title: 'NFS5 lights', controls: lights },
    ];
    if (c.isPaintable) {
      // the record's _COLORCONFIG: body, accent 1, accent 2, interior
      const colors = [0xb00000, 0xffffff, 0x202020, 0x505050];
      let stripePackage = 0;
      const paint = () => this.debounced(() => c.setPaint(colors, stripePackage));
      const paintControls: ObjViewerControl[] = [
        checkbox('Paint (tinted as the game draws it)', c.paintEnabled, v => {
          if (v) {
            c.setPaint(colors, stripePackage);
          } else {
            c.paintEnabled = false;
          }
        }),
        ...['Body colour', 'Accent colour 1', 'Accent colour 2', 'Interior colour'].map(
          (label, i): ObjViewerControl => ({
            label,
            type: 'color',
            value: colors[i],
            change: v => {
              colors[i] = v;
              paint();
            },
          }),
        ),
      ];
      if (c.stripePackages > 1) {
        paintControls.push(
          slider('Stripe package', 0, c.stripePackages - 1, 1, 0, v => {
            stripePackage = v;
            paint();
          }),
        );
      }
      result.push({ title: 'NFS5 paint', controls: paintControls });
    }
    if (c.hasDamage) {
      result.push({
        title: 'NFS5 damage',
        controls: [
          slider(
            'Hit speed',
            10,
            200,
            5,
            s.hitSpeed,
            v => (s.hitSpeed = v),
            v => `${v} m/s`,
          ),
          ...HITS.map(([label, normal]): ObjViewerControl => ({
            label,
            type: 'button',
            click: () => {
              c.hit(normal, s.hitSpeed);
              this.refreshControls(c);
            },
          })),
          ...Array.from({ length: NFS5_ZONES }, (_, z) =>
            slider(`Zone ${z} (${NFS5_ZONE_NAMES[z]})`, 0, 100, 1, c.getZoneDamage(z), v => c.setZoneDamage(z, v)),
          ),
          {
            label: 'Repair',
            type: 'button',
            click: () => {
              c.repair();
              this.refreshControls(c);
            },
          },
        ],
      });
    }
    const animations = NFS5_ANIMATIONS.map((name, i) => ({ name, i, frames: c.animationFrames(i) })).filter(
      a => a.i > 0 && a.frames > 1,
    );
    if (animations.length) {
      result.push({
        title: 'NFS5 animation frames',
        controls: animations.map(a =>
          slider(`${a.name} (animation ${a.i})`, 0, a.frames - 1, 0.1, 0, v => c.setAnimation(a.i, v)),
        ),
      });
    }
    return result;
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
    if (this.resourceId && !this.isTrack$.value) {
      const paths = await this.mainService.api.serializeResource(this.resourceId, null, this.serializerSettings);
      this.extraPath = paths.find(x => x.endsWith('_extra.json')) || null;
      this.previewPaths$.next([paths.find(x => x.endsWith('.obj'))!, paths.find(x => x.endsWith('.mtl'))!]);
    }
  }

  ngOnDestroy(): void {
    this.meshController?.dispose();
    this.destroyed$.next();
    this.destroyed$.complete();
  }
}
