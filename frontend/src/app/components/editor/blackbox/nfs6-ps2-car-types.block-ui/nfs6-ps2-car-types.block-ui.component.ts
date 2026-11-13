import { ChangeDetectionStrategy, Component } from '@angular/core';
import {
  CurveAxis,
  CurveMarker,
  CurveMarkerChange,
  CurvePoint,
  CurveSeries,
  CurveSeriesChange,
} from '../../common/curve-editor/curve-editor.component';
import { StatTile } from '../../common/stat-tiles/stat-tiles.component';
import { SliderSpec } from '../../common/slider-field/slider-field.component';
import {
  CarSpecEditorBase,
  fmt,
  GEAR_COLORS,
  KW_TO_HP,
  MPS_TO_KMH,
} from '../../eac/player-car-physics.block-ui/car-specs';
import { BlockSchema } from '../../types';
import { joinId } from '../../../../utils/join-id';
import {
  angle16ToDeg,
  boxInertia,
  clutchRadPerMps,
  curveRpm,
  dragForce,
  driveForce,
  ENGINE_SAMPLES,
  enginePeaks,
  engineTorque,
  frictionTorque,
  gridScore,
  LOCATIONS,
  maxWheelAngle,
  MPS_TO_MPH,
  needleAngle,
  Nfs6Ps2DriveTrain,
  Nfs6Ps2Engine,
  powerKw,
  RPM_TO_RAD,
  samplePitchOctaves,
  shiftPoints,
  speedAt,
  speedLimitMph,
  springForce,
  STEER_TABLE_MAX_SPEED,
  topGear,
  topSpeedEstimate,
  turningRadius,
} from './nfs6-ps2-car-specs';

export const USAGE_TYPES = ['Racer', 'Police', 'Traffic'];
export const CAR_STATUSES: { [v: number]: string } = {
  0: 'available',
  1: 'locked',
  3: 'not offered',
  4: 'locked, stats hidden',
};

export type Nfs6Ps2GearRow = {
  index: number;
  name: string;
  color: string;
  ratio: number;
  maxSpeed: number;
  shiftUp: number | null;
  shiftDown: number | null;
  peakAccel: number;
};

export const gearName = (g: number) => (g === 0 ? 'R' : g === 1 ? 'N' : `${g - 1}`);

// Editor of the NFS Hot Pursuit 2 (PS2) car types table (GLOBALB chunk 0x34600, `Nfs6Ps2CarTypeInfos`): a list of the
// car types and, for the one picked, key figures and tabs per subsystem with charts, every curve computed as the
// executable does (`nfs6-ps2-car-specs.ts`), and an "All fields" tab
@Component({
  selector: 'app-nfs6-ps2-car-types-block-ui',
  templateUrl: './nfs6-ps2-car-types.block-ui.component.html',
  styleUrls: [
    '../../eac/player-car-physics.block-ui/player-car-physics.block-ui.component.scss',
    './nfs6-ps2-car-types.block-ui.component.scss',
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: false,
})
export class Nfs6Ps2CarTypesBlockUiComponent extends CarSpecEditorBase {
  selected = 0;
  selectedTab = 0;
  filter = '';
  readonly usageTypes = USAGE_TYPES;
  readonly statuses = CAR_STATUSES;
  readonly samples = ENGINE_SAMPLES;
  readonly fmt = fmt;

  // the scalar fields of each subsystem, edited through the generic field editors
  readonly groups: { [sub: string]: string[] } = {
    engine: ['idle_rpm', 'redline_rpm', 'max_rpm', 'inertia'],
    drive_train: ['num_gears', 'clutch_stiffness', 'clutch_rate', 'shift_up_fraction', 'unused_4'],
    rigid_body: ['mass', 'dimensions'],
    aero: ['drag', 'front_downforce', 'rear_downforce'],
    controls: [
      'brake_torque',
      'handbrake_torque',
      'speed_limiter',
      'yaw_boost',
      'yaw_boost_ebrake',
      'max_moment_z',
      'max_moment_z_sim',
    ],
    engine_sound: [
      'region',
      'sample_prefix',
      'ai_sample',
      'rpm_offset',
      'rpm_pitch',
      'pitch_offset',
      'redline_offset',
      'top_gear_offset',
      'unused_20',
    ],
    camera: ['num_views', 'num_split_screen_views'],
    identity: [
      'name',
      'model_name',
      'manufacturer',
      'geometry_path',
      'compressed_geometry_path',
      'dashboard_geometry_path',
      'compressed_dashboard_geometry_path',
    ],
    front_end: [
      'is_hp',
      'car_class',
      'usage_type',
      'car_type',
      'num_skins',
      'skins',
      'default_skin',
      'default_status',
      'cop_default_status',
      'open_top',
    ],
    body: ['center_of_gravity', 'driver_position'],
  };

  readonly sliders: { [sub: string]: [string, SliderSpec][] } = {
    drive_train: [['rear_torque_split', { min: 0, max: 1, step: 0.01, scale: 100, unit: '% rear' }]],
    aero: [['downforce_factor', { min: 0, max: 1, step: 0.01, unit: '×' }]],
    controls: [
      ['steering_scale', { min: 0.5, max: 2, step: 0.01, unit: '×' }],
      ['brake_balance', { min: 0, max: 1, step: 0.01, scale: 100, unit: '% front' }],
    ],
  };

  carSchema?: BlockSchema;
  tiles: StatTile[] = [];
  gears: Nfs6Ps2GearRow[] = [];

  // engine
  engineSeries: CurveSeries[] = [];
  engineMarkers: CurveMarker[] = [];
  readonly rpmAxis: CurveAxis = { label: 'Engine speed (rpm)', min: 0, format: v => fmt(v, 0) };
  readonly torqueAxis: CurveAxis = { label: 'Torque (N·m)', min: 0 };
  readonly powerAxis: CurveAxis = { label: 'Power (hp)', min: 0 };
  readonly describeRpm = (rpm: number) => `${fmt(rpm, 0)} rpm`;

  // gearbox
  gearSeries: CurveSeries[] = [];
  gearMarkers: CurveMarker[] = [];
  accelSeries: CurveSeries[] = [];
  readonly speedAxis: CurveAxis = { label: 'Speed (km/h)', min: 0, format: v => fmt(v, 0) };
  readonly accelAxis: CurveAxis = { label: 'Acceleration (m/s²)', min: 0 };
  readonly describeSpeed = (kmh: number) => `${fmt(kmh, 1)} km/h · ${fmt(kmh / MPS_TO_KMH, 1)} m/s`;

  // chassis
  wheelSeries: CurveSeries[] = [];
  readonly planXAxis: CurveAxis = { label: 'Y, left (m)', format: v => fmt(v, 2) };
  readonly planYAxis: CurveAxis = { label: 'X, forward (m)' };
  gripSeries: CurveSeries[] = [];
  readonly gripAxis: CurveAxis = {
    label: 'Grip',
    categories: ['Front lateral', 'Front sliding', 'Rear lateral', 'Rear sliding'],
  };
  readonly gripYAxis: CurveAxis = { label: 'Grip × load', min: 0 };
  springSeries: CurveSeries[] = [];
  readonly heightAxis: CurveAxis = { label: 'Suspension height (m, compression +)', format: v => fmt(v, 3) };
  readonly forceAxis: CurveAxis = { label: 'Spring force' };

  // aero
  aeroSeries: CurveSeries[] = [];
  aeroMarkers: CurveMarker[] = [];
  readonly kNAxis: CurveAxis = { label: 'Force (kN)', min: 0 };

  // steering
  steerSeries: CurveSeries[] = [];
  radiusSeries: CurveSeries[] = [];
  readonly steerAxis: CurveAxis = { label: 'Front wheels at full lock (°)', min: 0 };
  readonly radiusAxis: CurveAxis = { label: 'Turning radius (m)', min: 0 };

  // sound
  pitchSeries: CurveSeries[] = [];
  sampleSeries: CurveSeries[] = [];
  mixSeries: CurveSeries[] = [];
  readonly positionAxis: CurveAxis = { label: 'Sound rpm position (0-127)', min: 0, max: 127, format: v => fmt(v, 0) };
  readonly octaveAxis: CurveAxis = { label: 'Pitch (octaves)' };
  readonly sampleAxis: CurveAxis = { label: 'Sample', categories: ENGINE_SAMPLES };
  readonly centsAxis: CurveAxis = { label: 'Pitch (cents)' };
  readonly volumeAxis: CurveAxis = { label: 'Volume ×', min: 0 };
  readonly viewAxis: CurveAxis = { label: 'Camera view', categories: ['View 0', 'View 1', 'View 2', 'View 3'] };
  readonly mixAxis: CurveAxis = { label: 'Exhaust share (0-127)', min: 0, max: 127, format: v => fmt(v, 0) };

  // camera
  viewSeries: CurveSeries[] = [];
  readonly distanceAxis: CurveAxis = { label: 'Distance behind (m)', format: v => fmt(v, 1) };
  readonly camHeightAxis: CurveAxis = { label: 'Height (m)' };

  // gauges
  gaugeSeries: CurveSeries[] = [];
  readonly fractionAxis: CurveAxis = { label: 'Share of the scale (%)', min: 0, max: 100, format: v => fmt(v, 0) };
  readonly angleAxis: CurveAxis = { label: 'Needle angle (°)', min: 0, max: 360 };

  // front end
  weightSeries: CurveSeries[] = [];
  readonly locationAxis: CurveAxis = { label: 'Location index', categories: LOCATIONS };
  readonly weightAxis: CurveAxis = { label: 'Weight', min: 0 };

  // ---------- data ----------

  get carTypes(): any[] {
    return (this.resourceData?.['car_types'] as any[]) || [];
  }

  get car(): any {
    return this.carTypes[this.selected];
  }

  get carId(): string {
    return joinId(this.resourceId!, 'car_types', this.selected);
  }

  subId(...path: (string | number)[]): string {
    return joinId(this.carId, ...path);
  }

  subSchema(...path: (string | number)[]): BlockSchema | undefined {
    let s: BlockSchema | undefined = this.carSchema;
    for (const p of path) {
      if (!s) return undefined;
      if (typeof p === 'number') s = s['child_schema'];
      else {
        // a name under an array: its items' field
        if (!s.fields && s['child_schema']) s = s['child_schema'];
        s = s!.fields?.find((f: any) => f.name === p)?.schema;
      }
    }
    return s;
  }

  describe(...path: string[]): string {
    const name = path[path.length - 1];
    let parent = this.subSchema(...path.slice(0, -1));
    if (parent && !parent.fields && parent['child_schema']) parent = parent['child_schema'];
    return parent?.fields?.find((f: any) => f.name === name)?.description || '';
  }

  get visibleCars(): { index: number; car: any }[] {
    const f = this.filter.trim().toUpperCase();
    return this.carTypes
      .map((car, index) => ({ index, car }))
      .filter(x => !f || `${x.car.name} ${x.car.manufacturer}`.toUpperCase().includes(f));
  }

  select(index: number) {
    this.selected = index;
    this.refresh();
    this.cdr.markForCheck();
  }

  private get engine(): Nfs6Ps2Engine {
    return this.car.engine;
  }

  private get driveTrain(): Nfs6Ps2DriveTrain {
    return this.car.drive_train;
  }

  get isHp(): boolean {
    return !!this.car?.is_hp;
  }

  get radii(): [number, number] {
    const w = this.car.wheels;
    return [w[0]?.radius || 0, w[2]?.radius || 0];
  }

  get wheelbase(): number {
    const w = this.car.wheels;
    return (w[0]?.position?.x || 0) - (w[3]?.position?.x || 0);
  }

  setCar(path: (string | number)[], value: any) {
    this.setValue(['car_types', this.selected, ...path], value);
  }

  setCarField(sub: string | null, name: string, value: any) {
    this.setCar(sub ? [sub, name] : [name], value);
  }

  onCarNumber(path: (string | number)[], raw: string, integer: boolean = false) {
    const v = parseFloat(raw);
    if (isFinite(v)) this.setCar(path, integer ? Math.round(v) : v);
  }

  protected refresh(): void {
    const d = this.resourceData;
    if (!d || !Array.isArray(d['car_types']) || !d['car_types'].length) return;
    this.carSchema = this.resourceSchema?.fields?.find((f: any) => f.name === 'car_types')?.schema?.['child_schema'];
    if (this.selected >= this.carTypes.length) this.selected = 0;
    if (!this.car?.engine || !this.car?.drive_train) return;
    this.buildEngine();
    this.buildGears();
    this.buildChassis();
    this.buildAero();
    this.buildSteering();
    this.buildSound();
    this.buildCamera();
    this.buildGauges();
    this.buildFrontEnd();
    this.buildTiles();
  }

  // end of the speed axes: a bit past the top gear at max rpm and the limiter
  private get speedEnd(): number {
    const top = speedAt(this.driveTrain, this.radii, topGear(this.driveTrain), this.engine.max_rpm);
    const limit = speedLimitMph(this.car.controls.speed_limiter, this.isHp) / MPS_TO_MPH;
    return Math.max(30, top, limit) * 1.1;
  }

  // ---------- engine ----------

  private buildEngine(torques: number[] = this.engine.torque_curve, friction: number[] = this.engine.friction_curve) {
    const e = { ...this.engine, torque_curve: torques, friction_curve: friction };
    const nm = (v: number) => v * 1000;
    const points = torques.map((t, i) => ({ x: curveRpm(e, i, torques.length), y: nm(t) }));
    const fine: CurvePoint[] = [];
    const power: CurvePoint[] = [];
    for (let rpm = e.idle_rpm; rpm <= e.max_rpm; rpm += 50) {
      const t = engineTorque(e, Math.min(rpm, e.max_rpm - 100.001), this.isHp);
      fine.push({ x: rpm, y: nm(t) });
      power.push({ x: rpm, y: powerKw(t, rpm) * KW_TO_HP });
    }
    this.engineSeries = [
      {
        id: 'torque_curve',
        label: 'Torque curve',
        color: '#3f51b5',
        points,
        style: 'points',
        editable: 'y',
        y: { min: 0, step: 1 },
        pointLabels: points.map((_, i) => `point ${i}`),
        formatY: v => fmt(v, 0) + ' N·m',
      },
      {
        id: 'torque_used',
        label: this.isHp ? 'Torque × 1.05 (HP)' : 'Torque',
        color: '#7986cb',
        points: fine,
        inTooltip: false,
      },
      {
        id: 'friction_curve',
        label: 'Engine braking',
        color: '#8d6e63',
        dashed: true,
        points: friction.map((t, i) => ({ x: curveRpm(e, i, friction.length), y: nm(t) })),
        editable: 'y',
        y: { min: 0, step: 1 },
        formatY: v => fmt(v, 0) + ' N·m',
      },
      {
        id: 'power',
        label: 'Power',
        color: '#e64a19',
        axis: 'right',
        points: power,
        formatY: v => `${fmt(v, 0)} hp · ${fmt(v / KW_TO_HP, 0)} kW`,
      },
    ];
    const marker = (id: string, label: string, color: string): CurveMarker => ({
      id,
      label,
      color,
      value: (e as any)[id],
      editable: true,
      constraints: { min: 0, step: 50 },
      format: v => fmt(v, 0),
    });
    this.engineMarkers = [
      marker('idle_rpm', 'Idle', '#757575'),
      marker('redline_rpm', 'Redline', '#d32f2f'),
      marker('max_rpm', 'Max (limiter from -100)', '#424242'),
    ];
  }

  onEnginePreview(e: CurveSeriesChange) {
    if (e.seriesId === 'torque_curve') this.buildEngine(e.points.map(p => p.y / 1000));
  }

  onEngineChange(e: CurveSeriesChange) {
    if (e.seriesId !== 'torque_curve' && e.seriesId !== 'friction_curve') return;
    const curve = [...this.engine[e.seriesId]];
    for (const i of e.changed) curve[i] = Math.max(0, Math.round(e.points[i].y) / 1000);
    this.setCar(['engine', e.seriesId], curve);
  }

  onEngineMarker(e: CurveMarkerChange) {
    this.setCar(['engine', e.markerId], Math.round(e.value));
  }

  // ---------- gearbox ----------

  private buildGears(ratios: number[] = this.driveTrain.gear_ratios) {
    const d = { ...this.driveTrain, gear_ratios: ratios };
    const e = this.engine;
    const radii = this.radii;
    const top = topGear(d);
    const { up, down } = shiftPoints(d, e);
    const mass = this.car.rigid_body.mass || 0;
    this.gears = [];
    for (let g = 0; g <= top; g++) {
      const peak = enginePeaks(e, this.isHp).torque;
      const k = clutchRadPerMps(d, radii) * Math.abs(ratios[g] || 0);
      this.gears.push({
        index: g,
        name: gearName(g),
        color: g >= 2 ? GEAR_COLORS[(g - 2) % GEAR_COLORS.length] : '#9e9e9e',
        ratio: ratios[g],
        maxSpeed: speedAt(d, radii, g, e.max_rpm) * MPS_TO_KMH,
        shiftUp: g >= 2 && g < top ? up[g] : null,
        shiftDown: g >= 3 ? down[g] : null,
        peakAccel: mass ? (peak.value * k) / mass : 0,
      });
    }
    const forward = this.gears.filter(g => g.index >= 2 && g.ratio > 0);
    this.gearSeries = forward.map(g => ({
      id: 'gear-' + g.index,
      label: g.name,
      color: g.color,
      points: [
        { x: 0, y: 0 },
        { x: g.maxSpeed, y: e.max_rpm },
      ],
      editable: 'x' as const,
      lockedIndices: [0],
      x: { min: 1, step: 0.1 },
      pointLabels: ['', 'speed at max rpm, drag to change the ratio'],
      formatY: v => fmt(v, 0) + ' rpm',
    }));
    const shifts = forward.filter(g => g.shiftUp !== null);
    const drops: CurvePoint[] = [];
    for (const g of shifts) {
      const next = this.gears[g.index + 1];
      if (!next) continue;
      const v = speedAt(d, radii, g.index, g.shiftUp!) * MPS_TO_KMH;
      drops.push({ x: v, y: g.shiftUp! }, { x: v, y: (g.shiftUp! * next.ratio) / g.ratio }, { x: NaN, y: NaN });
    }
    this.gearSeries.push(
      {
        id: 'drops',
        label: 'Rpm drop',
        color: '#9e9e9e',
        points: drops,
        dashed: true,
        strokeWidth: 1,
        hideInLegend: true,
        inTooltip: false,
      },
      {
        id: 'up',
        label: 'Shift up',
        color: '#424242',
        style: 'points',
        points: shifts.map(g => ({ x: speedAt(d, radii, g.index, g.shiftUp!) * MPS_TO_KMH, y: g.shiftUp! })),
        pointLabels: shifts.map(g => `${g.name} → ${gearName(g.index + 1)}`),
        formatY: v => fmt(v, 0) + ' rpm',
      },
      {
        id: 'down',
        label: 'Shift down',
        color: '#90a4ae',
        style: 'points',
        points: forward
          .filter(g => g.shiftDown !== null)
          .map(g => ({ x: speedAt(d, radii, g.index, g.shiftDown!) * MPS_TO_KMH, y: g.shiftDown! })),
        pointLabels: forward.filter(g => g.shiftDown !== null).map(g => `${g.name} → ${gearName(g.index - 1)}`),
        formatY: v => fmt(v, 0) + ' rpm',
      },
    );
    this.gearMarkers = [
      {
        id: 'redline_rpm',
        value: e.redline_rpm,
        orientation: 'horizontal',
        label: 'Redline',
        color: '#d32f2f',
        format: v => fmt(v, 0),
      },
      this.limiterMarker(),
    ];

    // acceleration from the drive force of each gear, and the air drag, at full throttle
    const formatY = (v: number) => `${fmt(v, 2)} m/s²`;
    this.accelSeries = forward.map(g => {
      const points: CurvePoint[] = [];
      for (let rpm = e.idle_rpm; rpm < e.max_rpm - 100; rpm += 100) {
        points.push({
          x: speedAt(d, radii, g.index, rpm) * MPS_TO_KMH,
          y: mass ? driveForce(d, e, radii, g.index, rpm, this.isHp) / mass : 0,
        });
      }
      return { id: 'accel-' + g.index, label: g.name, color: g.color, points, formatY };
    });
    const drag: CurvePoint[] = [];
    for (let v = 0; v <= this.speedEnd; v += 1)
      drag.push({ x: v * MPS_TO_KMH, y: mass ? dragForce(this.car.aero.drag, v) / mass : 0 });
    this.accelSeries.push({ id: 'drag', label: 'Air drag', color: '#00897b', dashed: true, points: drag, formatY });
  }

  private limiterMarker(): CurveMarker {
    const limit = speedLimitMph(this.car.controls.speed_limiter, this.isHp) / MPS_TO_MPH;
    return {
      id: 'speed_limiter',
      value: limit * MPS_TO_KMH,
      label: 'Speed limiter',
      color: '#455a64',
      editable: !!this.car.controls.speed_limiter,
      constraints: { min: 10, step: 1 },
      format: v => `${fmt(v, 0)} km/h · ${fmt((v / MPS_TO_KMH) * MPS_TO_MPH, 0)} mph`,
    };
  }

  onGearPreview(e: CurveSeriesChange) {
    if (!e.seriesId.startsWith('gear-')) return;
    const ratios = [...this.driveTrain.gear_ratios];
    ratios[+e.seriesId.substring(5)] = this.ratioForSpeed(e.points[1].x);
    this.buildGears(ratios);
  }

  onGearChange(e: CurveSeriesChange) {
    if (!e.seriesId.startsWith('gear-')) return;
    this.setCar(['drive_train', 'gear_ratios', +e.seriesId.substring(5)], this.ratioForSpeed(e.points[1].x));
  }

  // the gear ratio reaching `kmh` at max rpm
  ratioForSpeed(kmh: number): number {
    const k = clutchRadPerMps(this.driveTrain, this.radii);
    return kmh > 0 && k > 0 ? this.round((this.engine.max_rpm * RPM_TO_RAD) / (kmh / MPS_TO_KMH) / k, 3) : 0;
  }

  onLimiterMarker(e: CurveMarkerChange) {
    if (e.markerId !== 'speed_limiter') return;
    const mph = (e.value / MPS_TO_KMH) * MPS_TO_MPH;
    this.setCar(['controls', 'speed_limiter'], this.round(this.limiterForMph(mph), 2));
  }

  // the speed_limiter value giving a limit of `mph` (the inverse of speedLimitMph)
  limiterForMph(mph: number): number {
    return Math.max(0, mph / (this.isHp ? 1.03 : 1) - 1.9);
  }

  // ---------- chassis ----------

  private buildChassis() {
    const c = this.car;
    const names = ['FL', 'FR', 'RR', 'RL'];
    const wheels: any[] = c.wheels;
    this.wheelSeries = [
      {
        id: 'wheels',
        label: 'Wheels',
        color: '#3f51b5',
        style: 'points',
        points: wheels.map(w => ({ x: w.position.y, y: w.position.x })),
        editable: 'xy',
        x: { step: 0.005 },
        y: { step: 0.005 },
        pointLabels: names,
        formatY: v => fmt(v, 3) + ' m',
      },
      {
        id: 'cog',
        label: 'Centre of gravity',
        color: '#e53935',
        style: 'points',
        points: [{ x: c.center_of_gravity.y, y: c.center_of_gravity.x }],
        editable: 'xy',
        x: { step: 0.005 },
        y: { step: 0.005 },
        formatY: v => fmt(v, 3) + ' m',
      },
      {
        id: 'driver',
        label: 'Driver',
        color: '#43a047',
        style: 'points',
        points: [{ x: c.driver_position.y, y: c.driver_position.x }],
        editable: 'xy',
        x: { step: 0.005 },
        y: { step: 0.005 },
        formatY: v => fmt(v, 3) + ' m',
      },
      {
        id: 'body',
        label: 'Body (dimensions)',
        color: '#9e9e9e',
        dashed: true,
        points: this.bodyOutline(),
        inTooltip: false,
      },
    ];
    const t = c.tires;
    this.gripSeries = [
      {
        id: 'grip',
        label: 'Grip',
        color: '#6d4c41',
        style: 'bars',
        points: [t[0].lateral_grip, t[0].longitudinal_grip, t[1].lateral_grip, t[1].longitudinal_grip].map((y, x) => ({
          x,
          y,
        })),
        editable: 'y',
        y: { min: 0, step: 0.01 },
        formatY: v => '× ' + fmt(v, 2),
      },
    ];
    this.springSeries = c.suspensions.map((s: any, i: number) => {
      const points: CurvePoint[] = [];
      const n = 40;
      for (let k = 0; k <= n; k++) {
        const h = s.min_height + ((s.max_height - s.min_height) * k) / n;
        points.push({ x: h, y: springForce(s.stiffness, s.progression, h) });
      }
      return {
        id: 'spring-' + i,
        label: i ? 'Rear' : 'Front',
        color: i ? '#f4511e' : '#1e88e5',
        points,
        formatY: (v: number) => fmt(v, 2),
      };
    });
  }

  private bodyOutline(): CurvePoint[] {
    const d = this.car.rigid_body.dimensions;
    const cog = this.car.center_of_gravity;
    const hl = d.x / 2;
    const hw = d.y / 2;
    return [
      { x: cog.y - hw, y: cog.x - hl },
      { x: cog.y + hw, y: cog.x - hl },
      { x: cog.y + hw, y: cog.x + hl },
      { x: cog.y - hw, y: cog.x + hl },
      { x: cog.y - hw, y: cog.x - hl },
    ];
  }

  onPlanChange(e: CurveSeriesChange) {
    const r = (v: number) => this.round(v, 4);
    if (e.seriesId === 'wheels') {
      const entries: [(string | number)[], any][] = [];
      for (const i of e.changed) {
        const pos = this.car.wheels[i].position;
        entries.push([
          ['car_types', this.selected, 'wheels', i, 'position'],
          { ...pos, x: r(e.points[i].y), y: r(e.points[i].x) },
        ]);
      }
      this.setValues(entries);
    } else if (e.seriesId === 'cog' || e.seriesId === 'driver') {
      const key = e.seriesId === 'cog' ? 'center_of_gravity' : 'driver_position';
      const pos = this.car[key];
      this.setCar([key], { ...pos, x: r(e.points[0].y), y: r(e.points[0].x) });
    }
  }

  onGripChange(e: CurveSeriesChange) {
    const keys: [number, string][] = [
      [0, 'lateral_grip'],
      [0, 'longitudinal_grip'],
      [1, 'lateral_grip'],
      [1, 'longitudinal_grip'],
    ];
    this.setValues(
      e.changed.map(i => [['car_types', this.selected, 'tires', keys[i][0], keys[i][1]], this.round(e.points[i].y, 3)]),
    );
  }

  // the inertia tensor of the dimensions, as every car type of the game has it (box formula, yaw doubled)
  get boxTensor(): number[] {
    const rb = this.car.rigid_body;
    const [a, b, c] = boxInertia(rb.mass, rb.dimensions.x, rb.dimensions.y, rb.dimensions.z);
    return [a, 0, 0, 0, 0, b, 0, 0, 0, 0, c, 0, 0, 0, 0, 1];
  }

  get tensorMatchesBox(): boolean {
    const t: number[] = this.car.rigid_body.inertia_tensor;
    return this.boxTensor.every((v, i) => Math.abs(v - t[i]) <= Math.max(1e-4, Math.abs(v) * 1e-4));
  }

  applyBoxTensor() {
    this.setCar(
      ['rigid_body', 'inertia_tensor'],
      this.boxTensor.map(v => Math.fround(v)),
    );
  }

  // ---------- aero ----------

  private buildAero() {
    const a = this.car.aero;
    const drag: CurvePoint[] = [];
    const front: CurvePoint[] = [];
    const rear: CurvePoint[] = [];
    for (let v = 0; v <= this.speedEnd; v += 1) {
      drag.push({ x: v * MPS_TO_KMH, y: dragForce(a.drag, v) });
      front.push({ x: v * MPS_TO_KMH, y: a.front_downforce * v });
      rear.push({ x: v * MPS_TO_KMH, y: a.rear_downforce * v });
    }
    const formatY = (v: number) => fmt(v, 2) + ' kN';
    this.aeroSeries = [
      { id: 'drag', label: 'Drag, full throttle', color: '#00897b', points: drag, formatY },
      { id: 'front', label: 'Front downforce', color: '#1e88e5', points: front, formatY },
      { id: 'rear', label: 'Rear downforce', color: '#f4511e', points: rear, formatY },
    ];
    this.aeroMarkers = [this.limiterMarker()];
  }

  // ---------- steering ----------

  private buildSteering() {
    const scale = this.car.controls.steering_scale || 0;
    const pad: CurvePoint[] = [];
    const wheel: CurvePoint[] = [];
    const padR: CurvePoint[] = [];
    const wheelR: CurvePoint[] = [];
    const end = Math.min(STEER_TABLE_MAX_SPEED, this.speedEnd);
    for (let v = 0; v <= end; v += 1) {
      const ap = maxWheelAngle(v, scale, false);
      const aw = maxWheelAngle(v, scale, true);
      pad.push({ x: v * MPS_TO_KMH, y: ap });
      wheel.push({ x: v * MPS_TO_KMH, y: aw });
      padR.push({ x: v * MPS_TO_KMH, y: Math.min(2000, turningRadius(this.wheelbase, ap)) });
      wheelR.push({ x: v * MPS_TO_KMH, y: Math.min(2000, turningRadius(this.wheelbase, aw)) });
    }
    const deg = (v: number) => fmt(v, 1) + '°';
    const m = (v: number) => fmt(v, 0) + ' m';
    this.steerSeries = [
      { id: 'pad', label: 'Pad', color: '#5e35b1', points: pad, formatY: deg },
      { id: 'wheel', label: 'Steering wheel', color: '#5e35b1', dashed: true, points: wheel, formatY: deg },
    ];
    this.radiusSeries = [
      { id: 'pad', label: 'Pad', color: '#00897b', points: padR, formatY: m },
      { id: 'wheel', label: 'Steering wheel', color: '#00897b', dashed: true, points: wheelR, formatY: m },
    ];
  }

  // ---------- sound ----------

  private buildSound() {
    const s = this.car.engine_sound;
    const cents = (v: number) => fmt(v, 0) + ' cents';
    this.sampleSeries = [
      {
        id: 'sample_pitches',
        label: 'Sample pitch',
        color: '#7b1fa2',
        style: 'bars',
        points: (s.sample_pitches as number[]).map((y, x) => ({ x, y })),
        editable: 'y',
        y: { min: -32768, max: 32767, step: 1 },
        formatY: cents,
      },
      {
        id: 'sample_volumes',
        label: 'Volume',
        color: '#ef6c00',
        axis: 'right',
        style: 'points',
        points: (s.sample_volumes as number[]).map((y, x) => ({ x, y })),
        editable: 'y',
        y: { min: 0, step: 0.05 },
        formatY: v => '× ' + fmt(v, 2),
      },
    ];
    this.mixSeries = [
      {
        id: 'exhaust_mix',
        label: 'Exhaust share',
        color: '#455a64',
        style: 'bars',
        points: (s.exhaust_mix as number[]).map((y, x) => ({ x, y })),
        editable: 'y',
        y: { min: 0, max: 127, step: 1 },
        formatY: v => fmt(v, 0),
      },
    ];
    this.pitchSeries = ENGINE_SAMPLES.map((name, i) => {
      const points: CurvePoint[] = [];
      for (let p = 0; p <= 127; p += 4)
        points.push({ x: p, y: samplePitchOctaves(s.pitch_offset, s.sample_pitches[i], s.rpm_pitch, p) });
      return {
        id: 'pitch-' + i,
        label: name,
        color: GEAR_COLORS[i % GEAR_COLORS.length],
        dashed: i >= 6,
        points,
        formatY: (v: number) => fmt(v, 2) + ' oct',
      };
    });
  }

  onSoundChange(e: CurveSeriesChange) {
    const s = this.car.engine_sound;
    if (!(e.seriesId in s)) return;
    const values = [...s[e.seriesId]];
    for (const i of e.changed) {
      values[i] = e.seriesId === 'sample_volumes' ? this.round(e.points[i].y, 3) : Math.round(e.points[i].y);
    }
    this.setCar(['engine_sound', e.seriesId], values);
  }

  // ---------- camera ----------

  private buildCamera() {
    const cam = this.car.camera;
    const series = (key: 'views' | 'split_screen_views', count: number, color: string, label: string): CurveSeries => ({
      id: key,
      label,
      color,
      style: 'points',
      points: (cam[key] as any[]).slice(0, Math.max(0, Math.min(4, count))).map(v => ({ x: v.distance, y: v.height })),
      editable: 'xy',
      x: { step: 0.01 },
      y: { step: 0.01 },
      pointLabels: (cam[key] as any[]).map((v, i) => `view ${i}: ${v.type}, pitch ${fmt(angle16ToDeg(v.pitch), 1)}°`),
      formatY: v => fmt(v, 2) + ' m',
    });
    this.viewSeries = [
      series('views', cam.num_views, '#3949ab', 'Views'),
      series('split_screen_views', cam.num_split_screen_views, '#00897b', 'Split screen views'),
    ];
  }

  onViewChange(e: CurveSeriesChange) {
    if (e.seriesId !== 'views' && e.seriesId !== 'split_screen_views') return;
    const r = (v: number) => this.round(v, 3);
    this.setValues(
      e.changed.map(i => [
        ['car_types', this.selected, 'camera', e.seriesId, i],
        { ...this.car.camera[e.seriesId][i], distance: r(e.points[i].x), height: r(e.points[i].y) },
      ]),
    );
  }

  pitchDeg(v: number): number {
    return this.round(angle16ToDeg(v), 1);
  }

  setPitch(key: string, i: number, field: string, raw: string) {
    const deg = parseFloat(raw);
    if (!isFinite(deg)) return;
    let a = Math.round((deg * 0x10000) / 360);
    a = Math.max(-0x8000, Math.min(0x7fff, a));
    this.setCar(['camera', key, i, field], a);
  }

  // ---------- gauges ----------

  private buildGauges() {
    const g = this.car.gauges;
    const line = (
      id: string,
      label: string,
      color: string,
      min: number,
      max: number,
      a0: number,
      a1: number,
      unit: string,
    ): CurveSeries => {
      const points: CurvePoint[] = [];
      for (let f = 0; f <= 100; f += 2)
        points.push({ x: f, y: needleAngle(min + ((max - min) * f) / 100, min, max, a0, a1) });
      return {
        id,
        label: `${label} (${fmt(min, 0)}..${fmt(max, 0)} ${unit})`,
        color,
        points,
        formatY: v => fmt(v, 1) + '°',
      };
    };
    this.gaugeSeries = [
      line('tach', 'Tachometer', '#d32f2f', 0, this.engine.max_rpm, g.tach_min_angle, g.tach_max_angle, 'rpm'),
      line('mph', 'Speedometer mph', '#3949ab', g.mph_min, g.mph_max, g.mph_min_angle, g.mph_max_angle, 'mph'),
      line('kmh', 'Speedometer km/h', '#00897b', g.kmh_min, g.kmh_max, g.kmh_min_angle, g.kmh_max_angle, 'km/h'),
    ];
  }

  // ---------- front end ----------

  private buildFrontEnd() {
    this.weightSeries = [
      {
        id: 'traffic_weights',
        label: 'Weight',
        color: '#6d4c41',
        style: 'bars',
        points: (this.car.traffic_weights as number[]).map((y, x) => ({ x, y })),
        editable: 'y',
        y: { min: 0, step: 0.1 },
        formatY: v => fmt(v, 2),
      },
    ];
  }

  onWeightChange(e: CurveSeriesChange) {
    const w = [...this.car.traffic_weights];
    for (const i of e.changed) w[i] = Math.max(0, this.round(e.points[i].y, 2));
    this.setCar(['traffic_weights'], w);
  }

  statusName(v: number): string {
    return CAR_STATUSES[v] ?? `${v}`;
  }

  // ---------- summary ----------

  private buildTiles() {
    const c = this.car;
    const e = this.engine;
    const d = this.driveTrain;
    const { power, torque } = enginePeaks(e, this.isHp);
    const hp = power.value * KW_TO_HP;
    const mass = c.rigid_body.mass || 0;
    const top = topSpeedEstimate(d, e, this.radii, c.aero.drag, c.controls.speed_limiter, this.isHp);
    const limitMph = speedLimitMph(c.controls.speed_limiter, this.isHp);
    const split = d.rear_torque_split;
    const layout = split >= 0.999 ? 'RWD' : split <= 0.001 ? 'FWD' : `AWD ${fmt(split * 100, 0)}% rear`;
    this.tiles = [
      {
        id: 'peak_power',
        label: 'Peak power',
        value: `${fmt(hp, 0)} hp`,
        edit: { value: Math.round(hp), step: 1, min: 1, unit: 'hp' },
        sub: `${fmt(power.value, 0)} kW @ ${fmt(power.rpm, 0)} rpm`,
        hint: 'torque × rpm × π / 30 with the torque in kN·m (the units of the tonne mass), x 1.05 for HP cars (Engine::GetTorque 0x18aa28). A new value scales the torque curve',
        tone: 'accent',
      },
      {
        id: 'peak_torque',
        label: 'Peak torque',
        value: `${fmt(torque.value * 1000, 0)} N·m`,
        edit: { value: Math.round(torque.value * 1000), step: 1, min: 1, unit: 'N·m' },
        sub: `@ ${fmt(torque.rpm, 0)} rpm${this.isHp ? ' · HP × 1.05' : ''}`,
        hint: 'A new value scales the whole torque curve',
        tone: 'accent',
      },
      {
        id: 'mass',
        label: 'Mass',
        value: `${fmt(mass * 1000, 0)} kg`,
        edit: { value: Math.round(mass * 1000), step: 5, min: 1, unit: 'kg' },
        sub: `${fmt(mass ? hp / mass : 0, 0)} hp/t`,
        hint: 'rigid_body.mass (tonnes). The inertia tensor is not changed: "Inertia from dimensions" on the Chassis tab makes it again',
      },
      {
        label: 'Top speed',
        value: `${fmt(top.value * MPS_TO_KMH, 0)} km/h`,
        sub: `${fmt(top.value * MPS_TO_MPH, 0)} mph · ${top.by}`,
        hint: "Estimate: the lowest of the speed limiter, the top gear at the rev limiter and the speed where the best gear's drive force (no slip, no losses) meets the air drag at full throttle",
      },
      {
        id: 'speed_limiter',
        label: 'Speed limiter',
        value: limitMph ? `${fmt(limitMph, 0)} mph` : 'none',
        edit: c.controls.speed_limiter ? { value: this.round(limitMph, 1), step: 1, min: 10, unit: 'mph' } : undefined,
        sub: limitMph
          ? `${fmt((limitMph / MPS_TO_MPH) * MPS_TO_KMH, 0)} km/h, (${fmt(c.controls.speed_limiter, 1)} + 1.9)${this.isHp ? ' × 1.03' : ''}`
          : 'traffic',
        hint: 'RigidBody::GetDerivative 0x19d4d0: (speed_limiter + 1.9) mph, x 1.03 for HP cars, x 0.9..1.1 on slopes',
      },
      {
        label: 'Drivetrain',
        value: layout,
        sub: `${d.num_gears}-speed · top gear ${fmt(speedAt(d, this.radii, topGear(d), e.max_rpm) * MPS_TO_KMH, 0)} km/h`,
        hint: 'rear_torque_split; the speed is the top gear at max rpm without slip',
      },
      {
        label: 'Grid strength',
        value: fmt(gridScore(e, d, mass, this.radii[1]), 1),
        sub: 'torque / mass × 1st × final / radius',
        hint: 'The front end orders the grid by it, highest first (0x185fe8): the highest torque point / mass × first gear × rear final drive / rear wheel radius',
      },
      {
        label: 'Class',
        value: `${(c.car_class ?? 0) + 1}`,
        sub: `${USAGE_TYPES[c.usage_type] ?? c.usage_type}${c.is_hp ? ' · HP' : ''} · ${this.statusName(c.default_status)}`,
        hint: 'car_class + 1 as the car selector shows it, usage_type, default_status',
        tone: 'muted',
      },
    ];
    if (!mass) this.tiles.push({ label: 'Mass', value: '0', sub: 'the car cannot move', tone: 'warn' });
  }

  onTileChange(e: { id: string; value: number }) {
    const c = this.car;
    if (e.id === 'peak_power' || e.id === 'peak_torque') {
      const { power, torque } = enginePeaks(this.engine, this.isHp);
      const old = e.id === 'peak_power' ? power.value * KW_TO_HP : torque.value * 1000;
      if (!old) return;
      const k = e.value / old;
      this.setCar(
        ['engine', 'torque_curve'],
        (this.engine.torque_curve as number[]).map(t => this.round(Math.max(0, t * k), 4)),
      );
    } else if (e.id === 'mass') {
      this.setCar(['rigid_body', 'mass'], this.round(e.value / 1000, 4));
    } else if (e.id === 'speed_limiter') {
      this.setCar(['controls', 'speed_limiter'], this.round(this.limiterForMph(e.value), 2));
    } else if (e.id in c) {
      this.setCar([e.id], e.value);
    }
  }

  round(v: number, digits: number): number {
    const k = Math.pow(10, digits);
    return Math.round(v * k) / k;
  }

  get frictionAt(): number {
    return frictionTorque(this.engine, this.engine.max_rpm) * 1000;
  }
}
