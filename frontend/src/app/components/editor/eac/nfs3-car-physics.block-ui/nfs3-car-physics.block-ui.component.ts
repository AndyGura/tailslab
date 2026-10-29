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
  G,
  GEAR_COLORS,
  KW_TO_HP,
  MPS_TO_KMH,
  powerKw,
} from '../player-car-physics.block-ui/car-specs';
import { gearName } from '../player-car-physics.block-ui/player-car-physics.block-ui.component';

// nfs3.exe, as ported in nfs-web (src/nfs3/nfs3-physics): the torque curve has 41 entries 256 rpm apart, read
// interpolated at rpm / 256 (0x4a8a99); nfs4.exe (Nfs4CarPhysics, src/nfs4/nfs4-physics): 21 entries 500 rpm apart,
// read at rpm x 0.002 (0x4fdac0). The rest of the model these charts follow is the same in both games
const NFS3_TORQUE = { step: 256, length: 41 };
const NFS4_TORQUE = { step: 500, length: 21 };
// car physics steps per second: every 2nd tick of the 64 Hz simulation
const STEPS = 32;
// the controls' gas ramp per step (0x4a9bc4), up and down (faster down with the steering tuning slider above 1)
const GAS_RAMP_STEP = 16;
const STEER_MAX = 127;
// drive acceleration caps (0x4aaed1): 1st gear (gear 2), the other forward gears, reverse
const DRIVE_CAP_FIRST = 10;
const DRIVE_CAP = 8;
const DRIVE_CAP_REVERSE = -6;
// air drag (0x4a78d6, 0x4aaed1): at max velocity 0.98 x the top gear's drive at efficiency 1; above it + 0.01 x over²
const DRAG_SHARE = 0.98;
const OVERSPEED_DRAG = 0.01;
// downforce on the wheels' grip (0x4aab41): above 10 m/s 1 + speed x it (rear x 1.5), below 1 + it
const DOWNFORCE_MIN_SPEED = 10;
const REAR_DOWNFORCE = 1.5;
// steering angle (0x4ad2e1): full lock = min steering acceleration x 1.5 / 360 turns, reduced above 40 m/s
const LOCK_DEG_PER_ACCEL = 1.5;
const FAST_STEER_SPEED = 40;
// example slip ratio of the "steering into a slide" curve
const EXAMPLE_SLIP = 0.25;
// driving aid turn angles (0x4a83d3): 1/1024 turns
const AID_ANGLE_DEG = 360 / 1024;
// AI acceleration table (0x4064f0): 8 sections of 14 entries, entry round(speed - 0.5)
const AI_SECTIONS = 8;
const AI_SECTION_LENGTH = 14;
// the menus' default tuning (0x55d024): engine, brake balance, steering, gear ratio, suspension, aero, tyres
const TUNING_DEFAULT = [1, 0, 1, 1, 1, 1, 1];
const PEDAL_LEVELS = ['0-31', '32-63', '64-95', '96-127', '128-159', '160-191', '192-223', '224-255'];

type GearSet = { gears: string; ratio: string; gearRatio: string; efficiency: string; finalGear: string };
const MANUAL: GearSet = {
  gears: 'num_gears',
  ratio: 'vel_to_rpm',
  gearRatio: 'gear_ratio',
  efficiency: 'gear_efficiency',
  finalGear: 'final_gear',
};
const AUTOMATIC: GearSet = {
  gears: 'num_gears_auto',
  ratio: 'vel_to_rpm_auto',
  gearRatio: 'gear_ratio_auto',
  efficiency: 'gear_efficiency_auto',
  finalGear: 'final_gear_auto',
};

export type Nfs3GearRow = {
  index: number;
  name: string;
  color: string;
  // rpm per m/s
  ratio: number;
  gearRatio: number;
  efficiency: number;
  // gear ratio x final gear x 60 / (2 pi x rear tyre radius): what the shipped files have in `ratio`
  fromRatios: number;
  // m/s² per N·m
  drive: number;
  redlineSpeed: number;
  peakDrive: number;
  upshiftSpeed: number | null;
  downshiftSpeed: number | null;
};

export type Nfs3TunedCarp = {
  min_steering_accel: number;
  front_grip_bias: number;
  turning_circle: number;
  front_brake_bias: number;
  g_transfer: number;
  pitch_roll: number;
  aero_downforce: number;
  max_velocity: number;
  torque: number[];
  vel_to_rpm: number[];
  gas_release: number;
};

export type Nfs3TunedRow = { label: string; field: string; file: string; tuned: string; changed: boolean };

// Rich editor of NFS3 car physics (carp.txt in GameData/CarModel/<car>/car.viv) and NFS4 car physics (carp.txt in
// Data/Cars/<car>/car.viv, Nfs4CarPhysics, a subclass picked through block_class_mro): dyno, gearing with the
// automatic gearbox and the air drag, brake and steering ramps, steering lock, grip and downforce, the AI acceleration
// table and driving aid, and the menus' tuning, every parameter grouped by subsystem. The derived curves follow the
// field descriptions (nfs3.exe / nfs4.exe as ported in nfs-web)
@Component({
  selector: 'app-nfs3-car-physics-block-ui',
  templateUrl: './nfs3-car-physics.block-ui.component.html',
  styleUrls: ['../player-car-physics.block-ui/player-car-physics.block-ui.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: false,
})
export class Nfs3CarPhysicsBlockUiComponent extends CarSpecEditorBase {
  readonly groups = {
    engine: ['min_rpm', 'redline', 'shift_delay', 'shift_blip', 'brake_blip'],
    gearbox: ['num_gears', 'num_gears_auto', 'final_gear', 'final_gear_auto', 'max_velocity', 'top_speed_cap'],
    // the ramp curves are edited on their chart
    brakes: ['max_brake_decel', 'abs'],
    steering: ['min_steering_accel', 'turn_in_ramp', 'turn_out_ramp', 'turning_circle', 'power_steering'],
    // understeer_gradient: NFS4 only
    grip: ['mass', 'understeer_gradient', 'tire_front', 'tire_rear', 'suspension_stiffness'],
    body: ['pitch_roll', 'road_bumpiness', 'spoiler_type', 'spoiler_speed', 'camera_arm', 'subdivide_level'],
    identity: ['serial_number', 'car_class'],
    aid: [
      'gradual_turn_cutoff',
      'medium_turn_cutoff',
      'sharp_turn_cutoff',
      'medium_turn_speed',
      'sharp_turn_speed',
      'extreme_turn_speed',
    ],
    tuning: ['engine_tuning', 'brake_balance', 'steering_speed', 'gear_ratio_factor', 'aero_factor', 'tire_factor'],
    // fields no code of nfs3.exe was found reading
    unread: [
      'wheel_base',
      'tire_wear',
      'slide_mult',
      'spin_velocity_cap',
      'slide_velocity_cap',
      'slide_assist',
      'push_factor',
      'low_turn_factor',
      'high_turn_factor',
      'body_damage',
      'engine_damage',
      'suspension_damage',
    ],
  };

  // bounded fractions and factors as sliders, over the range of the shipped files with some room
  readonly sliders: { [group: string]: [string, SliderSpec][] } = {
    engine: [['gas_off_factor', { min: 0, max: 1, step: 0.005, unit: '×' }]],
    gearbox: [['front_drive_ratio', { min: 0, max: 1, step: 0.01, scale: 100, unit: '% front' }]],
    brakes: [['front_brake_bias', { min: 0, max: 1, step: 0.005, scale: 100, unit: '% front' }]],
    grip: [
      ['lateral_grip', { min: 0, max: 6, step: 0.05, unit: '×' }],
      ['front_grip_bias', { min: 0.3, max: 0.7, step: 0.005, unit: '×' }],
      ['g_transfer', { min: 0, max: 1, step: 0.01, unit: '×' }],
      ['aero_downforce', { min: 0, max: 0.004, step: 0.00005 }],
    ],
  };

  selectedTab = 0;
  automatic = false;
  tiles: StatTile[] = [];

  // engine
  torqueSeries: CurveSeries[] = [];
  torqueMarkers: CurveMarker[] = [];
  readonly rpmAxis: CurveAxis = { label: 'Engine speed (rpm)', min: 0, format: v => fmt(v, 0) };
  readonly torqueAxis: CurveAxis = { label: 'Torque (N·m)', min: 0 };
  readonly powerAxis: CurveAxis = { label: 'Power (hp)', min: 0 };
  readonly describeRpm = (rpm: number) => `${fmt(rpm, 0)} rpm · entry ${fmt(rpm / this.torqueStep, 2)}`;

  // gearbox
  gears: Nfs3GearRow[] = [];
  gearSeries: CurveSeries[] = [];
  gearMarkers: CurveMarker[] = [];
  accelSeries: CurveSeries[] = [];
  accelMarkers: CurveMarker[] = [];
  dragNote = '';
  readonly speedAxis: CurveAxis = { label: 'Speed (km/h)', min: 0, format: v => fmt(v, 0) };
  readonly gearRpmAxis: CurveAxis = { label: 'Engine speed (rpm)', min: 0, format: v => fmt(v, 0) };
  readonly accelAxis: CurveAxis = { label: 'Acceleration (m/s²)', min: 0 };
  readonly describeSpeed = (kmh: number) => `${fmt(kmh, 1)} km/h · ${fmt(kmh / MPS_TO_KMH, 1)} m/s`;

  // brakes and pedals
  pedalSeries: CurveSeries[] = [];
  rampSeries: CurveSeries[] = [];
  brakeSeries: CurveSeries[] = [];
  readonly timeAxis: CurveAxis = { label: 'Time (s)', min: 0 };
  readonly pedalAxis: CurveAxis = { label: 'Pedal (0-255)', min: 0, max: 255, format: v => fmt(v, 0) };
  readonly levelAxis: CurveAxis = { label: 'Pedal level', categories: PEDAL_LEVELS };
  readonly rampAxis: CurveAxis = { label: 'Step per physics step', min: 0 };
  readonly decelAxis: CurveAxis = { label: 'Braking (m/s²)', min: 0 };
  readonly describeTime = (s: number) => `${fmt(s, 2)} s · step ${Math.round(s * STEPS)}`;
  readonly describeLevel = (x: number) => `brake value ${PEDAL_LEVELS[Math.round(x)] ?? ''}`;

  // steering
  lockSeries: CurveSeries[] = [];
  steerRampSeries: CurveSeries[] = [];
  yawSeries: CurveSeries[] = [];
  readonly lockAxis: CurveAxis = { label: 'Front wheel angle (°)', min: 0 };
  readonly steerRampAxis: CurveAxis = {
    label: 'Steering (-127..127)',
    min: -STEER_MAX,
    max: STEER_MAX,
    format: v => fmt(v, 0),
  };
  readonly yawAxis: CurveAxis = { label: 'Yaw rate (°/s)', min: 0 };

  // grip
  downforceSeries: CurveSeries[] = [];
  readonly gripAxis: CurveAxis = { label: 'Grip ×', min: 1 };

  // AI and driving aid
  aiSeries: CurveSeries[] = [];
  aiMarkers: CurveMarker[] = [];
  aidSeries: CurveSeries[] = [];
  aidMarkers: CurveMarker[] = [];
  readonly aiAxis: CurveAxis = { label: 'AI acceleration (m/s²)', min: 0 };
  readonly aidAngleAxis: CurveAxis = { label: 'Turn of the road ahead (°)', min: 0, format: v => fmt(v, 0) };
  readonly aidSpeedAxis: CurveAxis = { label: 'Target speed ×', min: 0, max: 1.1 };
  readonly describeAiSpeed = (kmh: number) =>
    `${fmt(kmh, 1)} km/h · entry ${Math.max(0, Math.min(AI_SECTIONS * AI_SECTION_LENGTH - 1, Math.round(kmh / MPS_TO_KMH - 0.5)))}`;
  readonly describeAidAngle = (deg: number) => `${fmt(deg, 1)}° · ${fmt(deg / AID_ANGLE_DEG, 0)} / 1024 turn`;

  // tuning (the menus' sliders, local to the editor: they are not in the file)
  tuning: number[] = [...TUNING_DEFAULT];
  brakingAid = false;
  readonly tuningNames = ['Engine', 'Brake balance', 'Steering', 'Gear ratio', 'Suspension', 'Aero', 'Tyres'];
  tunedRows: Nfs3TunedRow[] = [];
  tunedTorqueSeries: CurveSeries[] = [];

  protected refresh(): void {
    const d = this.d;
    if (!d || !Array.isArray(d['torque']) || !Array.isArray(d['vel_to_rpm'])) return;
    this.buildEngine();
    this.buildGears();
    this.buildPedals();
    this.buildBrakes();
    this.buildSteering();
    this.buildGrip();
    this.buildAi();
    this.buildTuning();
    this.buildTiles();
  }

  // ---------- derived values ----------

  get set(): GearSet {
    return this.automatic ? AUTOMATIC : MANUAL;
  }

  // NFS4 carp.txt (Nfs4CarPhysics extends Nfs3CarPhysics)
  get isNfs4(): boolean {
    return (this.resourceSchema?.block_class_mro || '').startsWith('Nfs4CarPhysics');
  }

  get exeName(): string {
    return this.isNfs4 ? 'nfs4.exe' : 'nfs3.exe';
  }

  get torqueStep(): number {
    return (this.isNfs4 ? NFS4_TORQUE : NFS3_TORQUE).step;
  }

  get torqueLength(): number {
    return (this.isNfs4 ? NFS4_TORQUE : NFS3_TORQUE).length;
  }

  get redline(): number {
    return this.d['redline'] || 0;
  }

  get minRpm(): number {
    return this.d['min_rpm'] || 0;
  }

  private ratios(): number[] {
    return this.d[this.set.ratio] || [];
  }

  private get numGears(): number {
    return Math.max(0, Math.min(this.ratios().length, this.d[this.set.gears] || 0));
  }

  // torque entries the engine can read: the interpolation at the redline reads the entry after it
  get torqueActiveCount(): number {
    return Math.max(1, Math.min(this.torqueLength, Math.floor(this.redline / this.torqueStep) + 2));
  }

  // 0x4a8a99 (NFS4 0x4fdac0): linear between the entries at rpm / step, clamped to the curve
  torqueAt(rpm: number, torques: number[] = this.d['torque']): number {
    const x = Math.max(0, Math.min(this.torqueLength - 1, rpm / this.torqueStep));
    const i = Math.floor(x);
    if (x === i) return torques[i] || 0;
    const a = torques[i] || 0;
    const b = torques[i + 1] || 0;
    return a + (b - a) * (x - i);
  }

  // drive acceleration of a gear in m/s² per N·m (car+0x56c, 0x4a78d6): ratio / mass x 0.1 x efficiency
  drive(gear: number, ratios: number[] = this.ratios()): number {
    const mass = this.d['mass'] || 0;
    if (!mass) return 0;
    return ((ratios[gear] || 0) / mass) * 0.1 * ((this.d[this.set.efficiency] || [])[gear] ?? 0);
  }

  private cap(gear: number, accel: number): number {
    if (gear === 2) return Math.min(DRIVE_CAP_FIRST, accel);
    if (gear === 0) return Math.max(DRIVE_CAP_REVERSE, accel);
    return Math.min(DRIVE_CAP, accel);
  }

  speedAt(rpm: number, gear: number, ratios: number[] = this.ratios()): number {
    const ratio = Math.abs(ratios[gear] || 0);
    return ratio > 0 ? rpm / ratio : 0;
  }

  // rear tyre radius in m from `tire_rear` (width mm, aspect %, rim in): what the shipped rpm per m/s follow
  get rearTyreRadius(): number {
    const [w, a, r] = (this.d['tire_rear'] || []) as number[];
    return ((r || 0) * 25.4) / 2000 + ((w || 0) * (a || 0)) / 100000;
  }

  // the air drag of 0x4aaed1 with the coefficient of 0x4a78d6 (default tuning): 0.98 x the top gear's drive at
  // efficiency 1 at max velocity (torque entry trunc(round(max velocity x top ratio) / step)), x (speed / max)³
  private dragModel(ratios: number[] = this.ratios()) {
    const d = this.d;
    const n = this.numGears;
    const maxV = d['max_velocity'] || 0;
    const mass = d['mass'] || 0;
    if (n < 3 || maxV <= 0 || !mass) return null;
    const top = ratios[n - 1] || 0;
    const entry = Math.trunc(Math.round(maxV * top) / this.torqueStep);
    if (entry < 0 || entry >= this.torqueLength) return { entry, atMax: 0, maxV };
    const atMax = DRAG_SHARE * (d['torque'][entry] || 0) * (top / mass) * 0.1;
    return { entry, atMax, maxV };
  }

  dragAt(v: number, model = this.dragModel()): number {
    if (!model || !model.atMax) return 0;
    const r = v / model.maxV;
    let drag = model.atMax * r * r * r;
    if (v > model.maxV) drag += OVERSPEED_DRAG * (v - model.maxV) * (v - model.maxV);
    return drag;
  }

  // the automatic gearbox (0x4a90a0): no top gear when gear num_gears - 2 already reaches max velocity at the redline
  private get topGearSkipped(): boolean {
    const n = this.numGears;
    if (n < 3) return false;
    const r = this.ratios()[n - 2];
    const speedPerRpm = r ? 1 / r : 0.01;
    return this.redline * speedPerRpm > (this.d['max_velocity'] || 0);
  }

  private peak(torques: number[]) {
    let power = { kw: 0, rpm: 0 };
    let torque = { nm: 0, rpm: 0 };
    for (let rpm = 0; rpm <= this.redline; rpm += 32) {
      const t = this.torqueAt(rpm, torques);
      const kw = powerKw(t, rpm);
      if (kw > power.kw) power = { kw, rpm };
      if (t > torque.nm) torque = { nm: t, rpm };
    }
    return { power, torque };
  }

  private get speedEnd(): number {
    const n = this.numGears;
    const top = n >= 3 ? this.speedAt(this.redline, n - 1) : 0;
    return Math.max(30, top, this.d['max_velocity'] || 0) * 1.1;
  }

  // ---------- engine ----------

  private buildEngine(torques: number[] = this.d['torque']) {
    const active = this.torqueActiveCount;
    const points = torques.map((t, i) => ({ x: i * this.torqueStep, y: t }));
    const power: CurvePoint[] = [];
    for (let rpm = 0; rpm <= (active - 1) * this.torqueStep; rpm += 64) {
      power.push({ x: rpm, y: powerKw(this.torqueAt(rpm, torques), rpm) * KW_TO_HP });
    }
    this.torqueSeries = [
      {
        id: 'torque',
        label: 'Torque',
        color: '#3f51b5',
        points,
        editable: 'y',
        activeCount: active,
        y: { min: 0, step: 1 },
        formatY: v => fmt(v, 1) + ' N·m',
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
    this.torqueMarkers = [
      {
        id: 'min_rpm',
        value: this.minRpm,
        label: 'Min rpm',
        color: '#78909c',
        editable: true,
        constraints: { min: 0, max: (this.torqueLength - 1) * this.torqueStep, step: 10 },
        format: v => fmt(v, 0),
      },
      {
        id: 'redline',
        value: this.redline,
        label: 'Redline',
        color: '#d32f2f',
        editable: true,
        constraints: { min: 1000, max: (this.torqueLength - 1) * this.torqueStep, step: 50 },
        format: v => fmt(v, 0),
      },
    ];
  }

  onTorquePreview(e: CurveSeriesChange) {
    if (e.seriesId !== 'torque') return;
    const torques = e.points.map(p => p.y);
    this.buildEngine(torques);
    this.buildTiles(torques);
  }

  onTorqueChange(e: CurveSeriesChange) {
    if (e.seriesId !== 'torque') return;
    const torques = [...this.d['torque']];
    for (const i of e.changed) torques[i] = Math.max(0, this.round(e.points[i].y, 2));
    this.setValue(['torque'], torques);
  }

  onRpmMarker(e: CurveMarkerChange) {
    if (e.markerId === 'min_rpm' || e.markerId === 'redline') this.setValue([e.markerId], Math.round(e.value));
  }

  // ---------- gearbox ----------

  private buildGears(ratios: number[] = this.ratios()) {
    const d = this.d;
    const set = this.set;
    const redline = this.redline;
    const n = this.numGears;
    const up = redline - Math.trunc(redline / 8);
    const down = redline - Math.trunc(redline / 6);
    const half = Math.trunc(redline / 2);
    const lastUp = n - 1 - (this.topGearSkipped ? 1 : 0);
    const maxTorque = Math.max(0, ...(d['torque'] as number[]).slice(0, this.torqueActiveCount));
    const tyre = this.rearTyreRadius;
    const finalGear = d[set.finalGear] || 0;
    this.gears = [];
    for (let i = 0; i < n; i++) {
      const drive = this.drive(i, ratios);
      const forward = i >= 2 && ratios[i] > 0;
      this.gears.push({
        index: i,
        name: gearName(i),
        color: i >= 2 ? GEAR_COLORS[(i - 2) % GEAR_COLORS.length] : '#9e9e9e',
        ratio: ratios[i],
        gearRatio: (d[set.gearRatio] || [])[i],
        efficiency: (d[set.efficiency] || [])[i],
        fromRatios: tyre > 0 ? (((d[set.gearRatio] || [])[i] || 0) * finalGear * 60) / (2 * Math.PI * tyre) : 0,
        drive,
        redlineSpeed: this.speedAt(redline, i, ratios) * MPS_TO_KMH,
        peakDrive: i === 1 ? 0 : this.cap(i, maxTorque * drive),
        upshiftSpeed: forward && i < lastUp ? this.speedAt(up, i, ratios) * MPS_TO_KMH : null,
        downshiftSpeed: forward && i > 2 ? this.speedAt(i - 1 === 2 ? half : down, i - 1, ratios) * MPS_TO_KMH : null,
      });
    }
    const forward = this.gears.filter(g => g.index >= 2 && g.ratio > 0);
    this.gearSeries = forward.map(g => ({
      id: 'gear-' + g.index,
      label: g.name,
      color: g.color,
      points: [
        { x: 0, y: 0 },
        { x: g.redlineSpeed, y: redline },
      ],
      editable: 'x' as const,
      lockedIndices: [0],
      x: { min: 1, step: 0.1 },
      pointLabels: ['', 'speed at the redline, drag to change the rpm per m/s'],
      formatY: v => fmt(v, 0) + ' rpm',
    }));
    const drops: CurvePoint[] = [];
    const ups = forward.filter(g => g.upshiftSpeed !== null);
    for (const g of ups) {
      const next = this.gears[g.index + 1];
      if (!next) continue;
      drops.push(
        { x: g.upshiftSpeed!, y: up },
        { x: g.upshiftSpeed!, y: (g.upshiftSpeed! / MPS_TO_KMH) * Math.abs(next.ratio) },
        { x: NaN, y: NaN },
      );
    }
    const downs = forward.filter(g => g.downshiftSpeed !== null);
    this.gearSeries.push(
      {
        id: 'shift-drops',
        label: 'Rpm drop',
        color: '#9e9e9e',
        points: drops,
        dashed: true,
        strokeWidth: 1,
        hideInLegend: true,
        inTooltip: false,
      },
      {
        id: 'upshifts',
        label: 'Automatic up-shift',
        color: '#424242',
        style: 'points',
        points: ups.map(g => ({ x: g.upshiftSpeed!, y: up })),
        pointLabels: ups.map(g => `${g.name} → ${gearName(g.index + 1)}`),
        formatY: v => fmt(v, 0) + ' rpm',
      },
      {
        id: 'downshifts',
        label: 'Automatic down-shift below',
        color: '#90a4ae',
        style: 'points',
        points: downs.map(g => ({ x: g.downshiftSpeed!, y: (g.downshiftSpeed! / MPS_TO_KMH) * g.ratio })),
        pointLabels: downs.map(g => `${g.name} → ${gearName(g.index - 1)}`),
        formatY: v => fmt(v, 0) + ' rpm',
      },
    );
    this.gearMarkers = [
      {
        id: 'redline',
        value: redline,
        orientation: 'horizontal',
        label: 'Redline',
        color: '#d32f2f',
        editable: true,
        constraints: { min: 1000, max: (this.torqueLength - 1) * this.torqueStep, step: 50 },
        format: v => fmt(v, 0),
      },
      {
        id: 'upshift',
        value: up,
        orientation: 'horizontal',
        label: 'Up-shift (7/8)',
        color: '#424242',
        format: v => fmt(v, 0),
      },
      this.maxVelocityMarker(),
    ];

    // drive acceleration by speed in each gear, full gas on a flat road: torque at the wheels' rpm (min rpm ..
    // redline) x the gear's drive, capped; against the air drag
    const model = this.dragModel(ratios);
    const end = this.speedEnd;
    const formatY = (v: number) => `${fmt(v, 2)} m/s² · ${fmt(v / G, 2)} g`;
    this.accelSeries = forward.map(g => {
      const points: CurvePoint[] = [];
      const vMax = g.redlineSpeed / MPS_TO_KMH;
      for (let k = 0; k <= 80; k++) {
        const v = (vMax * k) / 80;
        const rpm = Math.max(this.minRpm, Math.min(redline, v * g.ratio));
        points.push({ x: v * MPS_TO_KMH, y: this.cap(g.index, this.torqueAt(rpm) * g.drive) });
      }
      return { id: 'accel-' + g.index, label: g.name, color: g.color, points, formatY };
    });
    if (model && model.atMax > 0) {
      const drag: CurvePoint[] = [];
      for (let k = 0; k <= 120; k++) {
        const v = (end * k) / 120;
        drag.push({ x: v * MPS_TO_KMH, y: this.dragAt(v, model) });
      }
      this.accelSeries.push({ id: 'drag', label: 'Air drag', color: '#00897b', dashed: true, points: drag, formatY });
      this.dragNote = `Drag coefficient from torque entry ${model.entry} (${fmt(model.entry * this.torqueStep, 0)} rpm)`;
    } else {
      this.dragNote = model
        ? `Max velocity × top gear rpm per m/s reads torque entry ${model.entry}, past the 41 entries: the game reads other fields there`
        : '';
    }
    this.accelMarkers = [this.maxVelocityMarker()];
  }

  private maxVelocityMarker(): CurveMarker {
    return {
      id: 'max_velocity',
      value: (this.d['max_velocity'] || 0) * MPS_TO_KMH,
      label: 'Max velocity',
      color: '#455a64',
      editable: true,
      constraints: { min: 1, step: 0.5 },
      format: v => fmt(v, 0) + ' km/h',
    };
  }

  onAutomaticChange(value: boolean) {
    this.automatic = value;
    this.refresh();
  }

  onGearPreview(e: CurveSeriesChange) {
    if (!e.seriesId.startsWith('gear-')) return;
    const ratios = [...this.ratios()];
    ratios[+e.seriesId.substring(5)] = this.ratioForSpeed(e.points[1].x);
    this.buildGears(ratios);
  }

  onGearChange(e: CurveSeriesChange) {
    if (!e.seriesId.startsWith('gear-')) return;
    this.setValue([this.set.ratio, +e.seriesId.substring(5)], this.ratioForSpeed(e.points[1].x));
  }

  onSpeedMarker(e: CurveMarkerChange) {
    if (e.markerId === 'max_velocity') {
      this.setValue(['max_velocity'], this.round(e.value / MPS_TO_KMH, 4));
    } else if (e.markerId === 'redline') {
      this.setValue(['redline'], Math.round(e.value));
    }
  }

  onGearInput(field: 'ratio' | 'gearRatio' | 'efficiency', gear: number, raw: string) {
    this.onNumberInput([this.set[field], gear], raw);
  }

  // rpm per m/s of the gear ratios, final gear and rear tyre (the shipped files' relation)
  applyRatiosFromGearbox() {
    const tyre = this.rearTyreRadius;
    if (!(tyre > 0)) return;
    const ratios = this.gears.map(g => this.round(g.fromRatios, 6));
    const all = [...this.ratios()];
    ratios.forEach((r, i) => (all[i] = r));
    this.setValue([this.set.ratio], all);
  }

  // rpm per m/s that reaches `kmh` at the redline
  private ratioForSpeed(kmh: number): number {
    return kmh > 0 ? this.round(this.redline / (kmh / MPS_TO_KMH), 6) : 0;
  }

  // ---------- brakes and pedals ----------

  private buildPedals() {
    const d = this.d;
    // the brake value moves toward the pedal by min(round(entry of value >> 5), what is left) per step (0x4a9bc4)
    const ramp = (start: number, step: (v: number) => number, rising: boolean): CurvePoint[] => {
      const pts: CurvePoint[] = [{ x: 0, y: start }];
      let v = start;
      for (let t = 1; t <= 10 * STEPS; t++) {
        const s = step(v);
        if (!(s > 0)) break;
        v = rising ? Math.min(255, v + s) : Math.max(0, v - s);
        pts.push({ x: t / STEPS, y: v });
        if (v === (rising ? 255 : 0)) break;
      }
      return pts;
    };
    const level = (curve: number[], v: number) => Math.round(curve[Math.min(7, v >> 5)] || 0);
    this.pedalSeries = [
      { id: 'gas_on', label: 'Gas press', color: '#43a047', points: ramp(0, () => GAS_RAMP_STEP, true) },
      {
        id: 'gas_off',
        label: 'Gas release',
        color: '#43a047',
        dashed: true,
        points: ramp(255, () => GAS_RAMP_STEP, false),
      },
      {
        id: 'brake_on',
        label: 'Brake press',
        color: '#e53935',
        points: ramp(0, v => level(d['brake_increasing'], v), true),
      },
      {
        id: 'brake_off',
        label: 'Brake release',
        color: '#e53935',
        dashed: true,
        points: ramp(255, v => level(d['brake_decreasing'], v), false),
      },
    ].map(s => ({ ...s, style: 'step' as const, formatY: (v: number) => fmt(v, 0) }));

    const steps = (id: string, label: string, color: string, dashed: boolean, editable: boolean): CurveSeries => ({
      id,
      label,
      color,
      dashed,
      points: ((d[id] || []) as number[]).map((y, x) => ({ x, y })),
      editable: editable ? 'y' : 'none',
      y: { min: 0, max: 255, step: 1 },
      formatY: v => fmt(v, 2),
    });
    this.rampSeries = [
      steps('brake_increasing', 'Brake up', '#e53935', false, true),
      steps('brake_decreasing', 'Brake down', '#e53935', true, true),
      steps('gas_increasing', 'Gas up (not read)', '#9e9e9e', false, false),
      steps('gas_decreasing', 'Gas down (not read)', '#9e9e9e', true, false),
    ];
  }

  onRampChange(e: CurveSeriesChange) {
    if (e.seriesId !== 'brake_increasing' && e.seriesId !== 'brake_decreasing') return;
    const curve = [...this.d[e.seriesId]];
    for (const i of e.changed) curve[i] = Math.max(0, Math.min(255, Math.round(e.points[i].y)));
    this.setValue([e.seriesId], curve);
  }

  // front share after Carp_TuneCar's clamp (default tuning, no braking aid)
  get frontBrakeShare(): number {
    return Math.max(0.3, Math.min(0.75, this.d['front_brake_bias'] || 0));
  }

  private buildBrakes() {
    const m = this.d['max_brake_decel'] || 0;
    const front = this.frontBrakeShare;
    const end = this.speedEnd * MPS_TO_KMH;
    const formatY = (v: number) => `${fmt(v, 2)} m/s² · ${fmt(v / G, 2)} g`;
    const flat = (y: number) => [
      { x: 0, y },
      { x: end / 3, y },
      { x: (2 * end) / 3, y },
      { x: end, y },
    ];
    this.brakeSeries = [
      {
        id: 'total',
        label: 'Full brake',
        color: '#c62828',
        style: 'step',
        points: flat(m),
        editable: 'y',
        lockedIndices: [1, 2, 3],
        y: { min: 0, step: 0.1 },
        pointLabels: ['max_brake_decel, drag to change it', '', '', ''],
        formatY,
      },
      { id: 'front', label: 'Front wheels', color: '#1e88e5', style: 'step', points: flat(m * front), formatY },
      { id: 'rear', label: 'Rear wheels', color: '#f4511e', style: 'step', points: flat(m * (1 - front)), formatY },
    ];
  }

  onBrakeChange(e: CurveSeriesChange) {
    if (e.seriesId !== 'total' || e.changed[0] === undefined) return;
    this.setValue(['max_brake_decel'], this.round(e.points[e.changed[0]].y, 3));
  }

  // ---------- steering ----------

  // full lock front wheel angle in degrees (0x4ad2e1)
  lockAngle(v: number, factor: number = 1): number {
    let a = (this.d['min_steering_accel'] || 0) * LOCK_DEG_PER_ACCEL * factor;
    if (v > FAST_STEER_SPEED) a /= Math.max(1, Math.min(1.5, v * 0.015));
    return a;
  }

  private buildSteering() {
    const d = this.d;
    const end = this.speedEnd;
    const lock: CurvePoint[] = [];
    const handbrake: CurvePoint[] = [];
    const slide: CurvePoint[] = [];
    for (let k = 0; k <= 120; k++) {
      const v = (end * k) / 120;
      lock.push({ x: v * MPS_TO_KMH, y: this.lockAngle(v) });
      handbrake.push({ x: v * MPS_TO_KMH, y: this.lockAngle(v, Math.max(0.55, 0.85 - v * 0.0056)) });
      // steering toward the slide: above 13.4 m/s with |slip| beyond 0.15 (26.7 m/s: 0.05), x 2 |slip| below 1
      const into = v > 13.4 && Math.abs(EXAMPLE_SLIP) > 0.15 ? Math.min(1, 2 * Math.abs(EXAMPLE_SLIP)) : 1;
      slide.push({ x: v * MPS_TO_KMH, y: this.lockAngle(v, into) });
    }
    const formatY = (v: number) => fmt(v, 1) + '°';
    this.lockSeries = [
      { id: 'lock', label: 'Full lock', color: '#5e35b1', points: lock, formatY },
      {
        id: 'handbrake',
        label: 'Handbrake, against the slide',
        color: '#8e24aa',
        dashed: true,
        points: handbrake,
        formatY,
      },
      {
        id: 'into_slide',
        label: `Toward the slide, slip ratio ${EXAMPLE_SLIP}`,
        color: '#ef6c00',
        dashed: true,
        points: slide,
        formatY,
      },
    ];

    // steering value per physics step with keyboard steering: toward the request by round(turn in), back toward 0
    // by round(turn out), also first when the request is on the other side
    const ramp = (start: number, target: number): CurvePoint[] => {
      const inStep = Math.round(d['turn_in_ramp'] || 0);
      const outStep = Math.round(d['turn_out_ramp'] || 0);
      const pts: CurvePoint[] = [{ x: 0, y: start }];
      let s = start;
      for (let t = 1; t <= 10 * STEPS && s !== target; t++) {
        const back = (target >= 0 && s < 0) || (target <= 0 && s > 0);
        const step = back ? outStep : inStep;
        const goal = back ? 0 : target;
        if (!(step > 0)) break;
        s = s < goal ? Math.min(goal, s + step) : Math.max(goal, s - step);
        pts.push({ x: t / STEPS, y: s });
      }
      return pts;
    };
    this.steerRampSeries = [
      { id: 'turn_in', label: 'Turn in', color: '#5e35b1', points: ramp(0, STEER_MAX) },
      { id: 'turn_out', label: 'Back to centre', color: '#5e35b1', dashed: true, points: ramp(STEER_MAX, 0) },
      { id: 'reverse', label: 'Full left to full right', color: '#ef6c00', points: ramp(-STEER_MAX, STEER_MAX) },
    ].map(s => ({ ...s, style: 'step' as const, formatY: (v: number) => fmt(v, 0) }));

    // yaw damping (0x4aea88): driving forward, a yaw rate above |vz| / (pi x radius) turns/s is damped
    const radius = d['turning_circle'] || 0;
    const yawAt = (v: number) => (radius > 0 ? (v / (Math.PI * radius)) * 360 : 0);
    this.yawSeries = [
      {
        id: 'yaw',
        label: 'Yaw rate damped above',
        color: '#00897b',
        points: [
          { x: 0, y: 0 },
          { x: end * MPS_TO_KMH, y: yawAt(end) },
        ],
        editable: 'y',
        lockedIndices: [0],
        y: { min: 1, step: 1 },
        pointLabels: ['', 'drag to change turning_circle'],
        formatY: v => fmt(v, 0) + ' °/s',
      },
    ];
  }

  onYawChange(e: CurveSeriesChange) {
    if (e.seriesId !== 'yaw') return;
    const p = e.points[1];
    if (!(p.y > 0)) return;
    const v = p.x / MPS_TO_KMH;
    this.setValue(['turning_circle'], this.round((v * 360) / (Math.PI * p.y), 3));
  }

  // ---------- grip ----------

  private buildGrip() {
    const aero = this.d['aero_downforce'] || 0;
    const end = this.speedEnd;
    const front: CurvePoint[] = [];
    const rear: CurvePoint[] = [];
    for (let k = 0; k <= 120; k++) {
      const v = (end * k) / 120;
      const fast = v > DOWNFORCE_MIN_SPEED;
      front.push({ x: v * MPS_TO_KMH, y: fast ? 1 + v * aero : 1 + aero });
      rear.push({ x: v * MPS_TO_KMH, y: fast ? 1 + v * aero * REAR_DOWNFORCE : 1 + aero });
    }
    const formatY = (v: number) => '× ' + fmt(v, 3);
    this.downforceSeries = [
      { id: 'front', label: 'Front', color: '#1e88e5', points: front, formatY },
      { id: 'rear', label: 'Rear', color: '#f4511e', points: rear, formatY },
    ];
  }

  // static grip of each wheel per unit of surface grip (0x4ad7a3): 9.81 x lateral_grip x front_grip_bias
  get staticGrip(): number {
    return G * (this.d['lateral_grip'] || 0) * (this.d['front_grip_bias'] || 0);
  }

  // ---------- AI and driving aid ----------

  private aiTable(): number[] {
    const table: number[] = [];
    for (let s = 0; s < AI_SECTIONS; s++) {
      const section = (this.d['ai_acc' + s] || []) as number[];
      for (let k = 0; k < AI_SECTION_LENGTH; k++) table.push(section[k] ?? 0);
    }
    return table;
  }

  private buildAi() {
    const d = this.d;
    this.aiSeries = [
      {
        id: 'ai_acc',
        label: 'AI acceleration',
        color: '#6d4c41',
        style: 'step',
        points: this.aiTable().map((y, i) => ({ x: i * MPS_TO_KMH, y })),
        editable: 'y',
        y: { min: 0, step: 0.01 },
        pointLabels: this.aiTable().map(
          (_, i) => `ai_acc${Math.floor(i / AI_SECTION_LENGTH)}[${i % AI_SECTION_LENGTH}]`,
        ),
        formatY: v => `${fmt(v, 3)} m/s²`,
      },
    ];
    this.aiMarkers = [
      {
        id: 'top_speed_cap',
        value: (d['top_speed_cap'] || 0) * MPS_TO_KMH,
        label: 'Top speed cap',
        color: '#455a64',
        editable: true,
        constraints: { min: 1, step: 0.5 },
        format: v => fmt(v, 0) + ' km/h',
      },
    ];

    // driving aid (0x4a83d3): target speed factor by the turn of the road ahead
    const g = (d['gradual_turn_cutoff'] || 0) * AID_ANGLE_DEG;
    const m = (d['medium_turn_cutoff'] || 0) * AID_ANGLE_DEG;
    const s = (d['sharp_turn_cutoff'] || 0) * AID_ANGLE_DEG;
    const end = Math.max(90, s * 1.4);
    this.aidSeries = [
      {
        id: 'aid',
        label: 'Target speed factor',
        color: '#5e35b1',
        style: 'step',
        points: [
          { x: 0, y: 1 },
          { x: g, y: d['medium_turn_speed'] || 0 },
          { x: m, y: d['sharp_turn_speed'] || 0 },
          { x: s, y: d['extreme_turn_speed'] || 0 },
          { x: end, y: d['extreme_turn_speed'] || 0 },
        ],
        editable: 'y',
        lockedIndices: [0, 4],
        y: { min: 0, max: 1.1, step: 0.01 },
        pointLabels: ['', 'medium_turn_speed', 'sharp_turn_speed', 'extreme_turn_speed', ''],
        formatY: v => '× ' + fmt(v, 3),
      },
    ];
    const cutoff = (id: string, value: number, label: string): CurveMarker => ({
      id,
      value,
      label,
      color: '#90a4ae',
      editable: true,
      constraints: { min: 0, step: AID_ANGLE_DEG },
      format: v => `${fmt(v, 1)}° (${fmt(v / AID_ANGLE_DEG, 0)})`,
    });
    this.aidMarkers = [
      cutoff('gradual_turn_cutoff', g, 'Gradual'),
      cutoff('medium_turn_cutoff', m, 'Medium'),
      cutoff('sharp_turn_cutoff', s, 'Sharp'),
    ];
  }

  onAiChange(e: CurveSeriesChange) {
    if (e.seriesId !== 'ai_acc') return;
    const sections: number[][] = [];
    for (let s = 0; s < AI_SECTIONS; s++) sections.push([...(this.d['ai_acc' + s] || [])]);
    const touched = new Set<number>();
    for (const i of e.changed) {
      const s = Math.floor(i / AI_SECTION_LENGTH);
      sections[s][i % AI_SECTION_LENGTH] = Math.max(0, this.round(e.points[i].y, 6));
      touched.add(s);
    }
    this.setValues([...touched].map(s => [['ai_acc' + s], sections[s]] as [string[], number[]]));
  }

  onAiMarker(e: CurveMarkerChange) {
    if (e.markerId === 'top_speed_cap') this.setValue(['top_speed_cap'], this.round(e.value / MPS_TO_KMH, 4));
  }

  onAidChange(e: CurveSeriesChange) {
    if (e.seriesId !== 'aid') return;
    const names = ['', 'medium_turn_speed', 'sharp_turn_speed', 'extreme_turn_speed'];
    this.setValues(
      e.changed.filter(i => names[i]).map(i => [[names[i]], this.round(e.points[i].y, 4)] as [string[], number]),
    );
  }

  onAidMarker(e: CurveMarkerChange) {
    this.setValue([e.markerId], Math.max(0, Math.round(e.value / AID_ANGLE_DEG)));
  }

  // ---------- tuning (Carp_TuneCar 0x4a78d6, a single player race of race type 0) ----------

  tunedCarp(): Nfs3TunedCarp {
    const d = this.d;
    const t = this.tuning;
    const set = this.set;
    const c: Nfs3TunedCarp = {
      min_steering_accel: d['min_steering_accel'] || 0,
      front_grip_bias: d['front_grip_bias'] || 0,
      turning_circle: d['turning_circle'] || 0,
      front_brake_bias: d['front_brake_bias'] || 0,
      g_transfer: d['g_transfer'] || 0,
      pitch_roll: d['pitch_roll'] || 0,
      aero_downforce: d['aero_downforce'] || 0,
      max_velocity: d['max_velocity'] || 0,
      torque: [...(d['torque'] || [])] as number[],
      vel_to_rpm: [...(d[set.ratio] || [])] as number[],
      gas_release: GAS_RAMP_STEP,
    };
    if (t[2] !== TUNING_DEFAULT[2]) {
      c.min_steering_accel *= t[2];
      c.front_grip_bias *= (t[2] - TUNING_DEFAULT[2]) * 0.625 + TUNING_DEFAULT[2];
      c.front_grip_bias = Math.min(0.56, Math.max(0.46, c.front_grip_bias));
      c.turning_circle += (1 - t[2]) * 0.5 * c.turning_circle;
    }
    if (t[2] > 1) c.gas_release = GAS_RAMP_STEP + Math.round((t[2] - 1) * 60);
    if (t[1] !== TUNING_DEFAULT[1]) c.front_brake_bias -= t[1];
    if (this.brakingAid) c.front_brake_bias += 0.05;
    c.front_brake_bias = Math.max(0.3, Math.min(0.75, c.front_brake_bias));
    if (t[4] !== TUNING_DEFAULT[4]) {
      c.g_transfer = Math.min(0.7, Math.max(0.3, t[4] * c.g_transfer));
      c.pitch_roll /= Math.sqrt(t[4]);
    }
    if (this.brakingAid) c.g_transfer -= 0.05;
    if (t[5] !== TUNING_DEFAULT[5]) {
      c.aero_downforce *= (t[5] - 1) * 0.25 + 1;
      c.max_velocity /= (t[5] - TUNING_DEFAULT[0]) * 0.05 + 1;
    }
    if (t[0] !== TUNING_DEFAULT[0]) {
      const lo = Math.trunc(Math.trunc((this.redline + this.minRpm) / 2) / this.torqueStep) + 3;
      const hi = Math.trunc(this.redline / this.torqueStep) + 3;
      c.torque = c.torque.map((v, i) => v + ((lo - i) / (hi - lo)) * ((t[0] - 1) * -0.1 * v));
      c.max_velocity *= (t[0] - TUNING_DEFAULT[0]) * 0.1 + 1;
    }
    if (t[3] !== TUNING_DEFAULT[3]) {
      for (let i = 0; i < this.numGears; i++) c.vel_to_rpm[i] *= t[3];
      c.max_velocity /= t[3];
    }
    return c;
  }

  private buildTuning() {
    const d = this.d;
    const c = this.tunedCarp();
    const row = (label: string, field: string, file: number, tuned: number, digits: number): Nfs3TunedRow => ({
      label,
      field,
      file: fmt(file, digits),
      tuned: fmt(tuned, digits),
      changed: Math.abs(file - tuned) > 1e-9,
    });
    const peak = (torques: number[]) => this.peak(torques).torque.nm;
    this.tunedRows = [
      row('Min. steering accel.', 'min_steering_accel', d['min_steering_accel'] || 0, c.min_steering_accel, 3),
      row('Front grip bias', 'front_grip_bias', d['front_grip_bias'] || 0, c.front_grip_bias, 4),
      row('Turning circle (m)', 'turning_circle', d['turning_circle'] || 0, c.turning_circle, 3),
      row('Gas release per step', '', GAS_RAMP_STEP, c.gas_release, 0),
      row('Front brake bias', 'front_brake_bias', d['front_brake_bias'] || 0, c.front_brake_bias, 4),
      row('G transfer', 'g_transfer', d['g_transfer'] || 0, c.g_transfer, 3),
      row('Pitch roll', 'pitch_roll', d['pitch_roll'] || 0, c.pitch_roll, 3),
      row('Aero downforce', 'aero_downforce', d['aero_downforce'] || 0, c.aero_downforce, 6),
      row('Max velocity (km/h)', 'max_velocity', (d['max_velocity'] || 0) * MPS_TO_KMH, c.max_velocity * MPS_TO_KMH, 1),
      row('Peak torque (N·m)', 'torque', peak(d['torque'] || []), peak(c.torque), 1),
      ...c.vel_to_rpm
        .slice(2, this.numGears)
        .map((r: number, i: number) =>
          row(`${gearName(i + 2)} rpm per m/s`, this.set.ratio, this.ratios()[i + 2] || 0, r, 2),
        ),
    ];
    const points = (torques: number[]) => torques.map((y, i) => ({ x: i * this.torqueStep, y }));
    const active = this.torqueActiveCount;
    this.tunedTorqueSeries = [
      { id: 'file', label: 'File', color: '#3f51b5', points: points(d['torque']), activeCount: active },
      { id: 'tuned', label: 'Tuned', color: '#e64a19', dashed: true, points: points(c.torque), activeCount: active },
    ];
  }

  onTuningInput(i: number, raw: string) {
    const v = parseFloat(raw);
    if (!isFinite(v)) return;
    this.tuning = this.tuning.map((t, k) => (k === i ? v : t));
    this.buildTuning();
  }

  resetTuning() {
    this.tuning = [...TUNING_DEFAULT];
    this.brakingAid = false;
    this.buildTuning();
  }

  onBrakingAidChange(value: boolean) {
    this.brakingAid = value;
    this.buildTuning();
  }

  // ---------- summary ----------

  private buildTiles(torques: number[] = this.d['torque']) {
    const d = this.d;
    const { power, torque } = this.peak(torques);
    const hp = power.kw * KW_TO_HP;
    const mass = d['mass'] || 0;
    const fdr = d['front_drive_ratio'] || 0;
    const drive = fdr <= 0 ? 'RWD' : fdr >= 1 ? 'FWD' : 'AWD';
    const top = d['max_velocity'] || 0;
    const n = this.numGears;
    const topGearSpeed = n >= 3 ? this.speedAt(this.redline, n - 1) * MPS_TO_KMH : 0;
    const brake = d['max_brake_decel'] || 0;
    const lock = this.lockAngle(0);
    this.tiles = [
      {
        id: 'peak_power',
        label: 'Peak power',
        value: `${fmt(hp, 0)} hp`,
        edit: { value: Math.round(hp), step: 1, min: 1, unit: 'hp' },
        sub: `${fmt(power.kw, 0)} kW @ ${fmt(power.rpm, 0)} rpm`,
        hint: 'Peak of the interpolated torque curve up to the redline. A new value scales the whole torque curve',
        tone: 'accent',
      },
      {
        id: 'peak_torque',
        label: 'Peak torque',
        value: `${fmt(torque.nm, 0)} N·m`,
        edit: { value: Math.round(torque.nm), step: 1, min: 1, unit: 'N·m' },
        sub: `@ ${fmt(torque.rpm, 0)} rpm`,
        hint: 'A new value scales the whole torque curve',
        tone: 'accent',
      },
      {
        id: 'redline',
        label: 'Redline',
        value: `${fmt(this.redline, 0)} rpm`,
        edit: { value: this.redline, step: 50, min: 1000, max: (this.torqueLength - 1) * this.torqueStep, unit: 'rpm' },
        sub: `idle ${fmt(this.minRpm, 0)} rpm`,
        hint: 'redline. The automatic gearbox shifts up above 7/8 of it',
      },
      {
        id: 'mass',
        label: 'Mass',
        value: `${fmt(mass, 0)} kg`,
        edit: { value: Math.round(mass), step: 5, min: 1, unit: 'kg' },
        sub: `${fmt(mass ? (hp / mass) * 1000 : 0, 0)} hp/t`,
        hint: 'mass: divides the drive acceleration of every gear',
      },
      {
        id: 'max_velocity',
        label: 'Top speed',
        value: `${fmt(top * MPS_TO_KMH, 0)} km/h`,
        edit: { value: Math.round(top * MPS_TO_KMH), step: 1, min: 1, unit: 'km/h' },
        sub: `top gear ${fmt(topGearSpeed, 0)} km/h at the redline`,
        hint: 'max_velocity: the air drag coefficient is set to stop the car there (with a top gear efficiency of 0.98)',
      },
      {
        label: 'Drivetrain',
        value: drive,
        sub: `${Math.max(0, n - 2)}-speed ${this.automatic ? 'automatic' : 'manual'} · shift ${d['shift_delay']}`,
        hint:
          (drive === 'AWD' ? `${fmt(fdr * 100, 0)}% of the drive force on the front wheels. ` : '') +
          'Set by the front_drive_ratio slider in the Gearbox tab. Shift: shift_delay in physics steps (32 per second)',
      },
      {
        id: 'max_brake_decel',
        label: 'Braking',
        value: `${fmt(brake, 1)} m/s²`,
        edit: { value: this.round(brake, 2), step: 0.5, min: 0, unit: 'm/s²' },
        sub: `${fmt(this.frontBrakeShare * 100, 0)}% front · ABS ${d['abs'] ? 'on' : 'off'}`,
        hint: 'max_brake_decel: brake value x it; the front share is front_brake_bias clamped to 0.3..0.75',
      },
      {
        id: 'lock',
        label: 'Full lock',
        value: `${fmt(lock, 1)}°`,
        edit: { value: this.round(lock, 1), step: 0.5, min: 0, unit: '°' },
        sub: `lateral force cap ${fmt(2 * (d['min_steering_accel'] || 0), 1)} m/s²`,
        hint: "Front wheel angle at full lock: min_steering_accel x 1.5 degrees; each wheel's lateral force is capped at 2 x min_steering_accel",
      },
    ];
    if (!mass) {
      this.tiles.push({ label: 'Mass', value: '0', sub: 'the car has no drive force', tone: 'warn' });
    }
  }

  onTileChange(e: { id: string; value: number }) {
    const d = this.d;
    if (e.id === 'peak_power' || e.id === 'peak_torque') {
      const { power, torque } = this.peak(d['torque']);
      const old = e.id === 'peak_power' ? power.kw * KW_TO_HP : torque.nm;
      if (!old) return;
      const k = e.value / old;
      this.setValue(
        ['torque'],
        (d['torque'] as number[]).map(t => this.round(Math.max(0, t * k), 2)),
      );
    } else if (e.id === 'max_velocity') {
      this.setValue(['max_velocity'], this.round(e.value / MPS_TO_KMH, 4));
    } else if (e.id === 'lock') {
      this.setValue(['min_steering_accel'], this.round(e.value / LOCK_DEG_PER_ACCEL, 3));
    } else if (e.id === 'redline' || e.id === 'mass') {
      this.setValue([e.id], e.id === 'redline' ? Math.round(e.value) : e.value);
    } else {
      this.setValue([e.id], e.value);
    }
  }

  readonly fmt = fmt;

  round(v: number, digits: number): number {
    const k = Math.pow(10, digits);
    return Math.round(v * k) / k;
  }
}
