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

// the game reads torque entry rpm / 256, clamped to the 41 entries (nfs2sen.exe 0x4590e0)
const TORQUE_RPM_STEP = 256;
const TORQUE_LENGTH = 41;
// physics steps per second: the car schedule runs on every 2nd tick of the 64 Hz sim
const STEPS = 32;
// arcade gas ramp per step with the gas ramp option (0x457d80)
const GAS_RAMP_STEP = 16;
const STEER_MAX = 127;
// arcade automatic gearbox (0x458280): up above redline - 500, down when the lower gear stays below redline - 1500
const UPSHIFT_MARGIN = 500;
const DOWNSHIFT_MARGIN = 1500;
// arcade drive (0x454210): torque * drive * 1.5 * gas * surface grip
const ARCADE_DRIVE = 1.5;
// arcade braking (0x454210): brake * 2 * max braking deceleration, * 0.75 below 10 m/s
const ARCADE_BRAKE = 2;
const ARCADE_SLOW_BRAKE = 0.75;
const ARCADE_SLOW_BRAKE_SPEED = 10;
// simulation drive caps (0x456f80): 1st gear, other gears
const SIM_CAP_FIRST = 10;
const SIM_CAP = 8;
// simulation downforce (0x4575a0) above 5 m/s; rear * 1.5
const DOWNFORCE_MIN_SPEED = 5;
const REAR_DOWNFORCE = 1.5;
// arcade steering gain (0x4539e0): scaled by speed * 0.2 below 5 m/s, divided by 1 + speed * turn factor above 20 m/s
const STEER_SLOW_SPEED = 5;
const STEER_FAST_SPEED = 20;
// arcade push slide (0x452fa0): (speed in whole m/s)² * yaw / 512 over push_factor + 0x6667 (yaw in 1/65536)
const PUSH_MARGIN = 0x6667;
const PEDAL_LEVELS = ['0-31', '32-63', '64-95', '96-127', '128-159', '160-191', '192-223', '224-255'];

export type Nfs2GearRow = {
  index: number;
  name: string;
  color: string;
  ratio: number;
  efficiency: number;
  // m/s² per N·m of torque
  drive: number;
  redlineSpeed: number;
  arcadePeak: number;
  simPeak: number;
  upshiftSpeed: number | null;
};

// Rich editor of NFS2 SE car physics (GAMEDATA/SIM/CARDATA/P*.DAT, p<car>.dat in CARDATA.VIV): dyno chart, gearing
// with the arcade automatic gearbox, arcade and simulation drive, pedal and steering ramps, steering response and
// downforce, with every parameter grouped by subsystem. The derived curves follow the field descriptions
@Component({
  selector: 'app-nfs2-car-physics-block-ui',
  templateUrl: './nfs2-car-physics.block-ui.component.html',
  styleUrls: ['../player-car-physics.block-ui/player-car-physics.block-ui.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: false,
})
export class Nfs2CarPhysicsBlockUiComponent extends CarSpecEditorBase {
  readonly groups = {
    engine: ['engine_redline_rpm'],
    gearbox: ['num_gears', 'gear_shift_delay', 'max_velocity'],
    // the ramp curves are edited on their chart
    brakes: ['max_braking_deceleration'],
    handling: ['max_steering_acceleration', 'turn_in_ramp', 'turn_out_ramp', 'push_factor', 'slide_assistance_factor'],
    chassis: ['mass', 'wheel_base', 'lateral_acceleration_grip_multiplier', 'spin_velocity_cap', 'slide_velocity_cap'],
  };

  // bounded fractions and factors as sliders, over the range of the shipped files with some room
  readonly sliders: { [group: string]: [string, SliderSpec][] } = {
    engine: [['gas_off_factor', { min: 0, max: 1, step: 0.01, unit: '×' }]],
    gearbox: [['front_drive_ratio', { min: 0, max: 1, step: 0.01, scale: 100, unit: '% front' }]],
    brakes: [['front_bias_brake_ratio', { min: 0, max: 1, step: 0.01, scale: 100, unit: '% front' }]],
    handling: [
      ['low_turn_factor', { min: 0, max: 0.06, step: 0.0005 }],
      ['high_turn_factor', { min: 0, max: 0.06, step: 0.0005 }],
      ['slide_multiplier', { min: 0, max: 2, step: 0.01, unit: '×' }],
    ],
    chassis: [
      ['front_grip_bias', { min: 0, max: 1, step: 0.005, scale: 100, unit: '% front' }],
      ['g_transfer_factor', { min: 0, max: 1, step: 0.01, unit: '×' }],
      ['aerodynamic_downforce_multiplier', { min: 0, max: 0.003, step: 0.00005 }],
    ],
  };

  selectedTab = 0;
  tiles: StatTile[] = [];

  // engine
  torqueSeries: CurveSeries[] = [];
  torqueMarkers: CurveMarker[] = [];
  readonly rpmAxis: CurveAxis = { label: 'Engine speed (rpm)', min: 0, format: v => fmt(v, 0) };
  readonly torqueAxis: CurveAxis = { label: 'Torque (N·m)', min: 0 };
  readonly powerAxis: CurveAxis = { label: 'Power (hp)', min: 0 };
  readonly describeRpm = (rpm: number) =>
    `${fmt(rpm, 0)} rpm · entry ${Math.max(0, Math.min(TORQUE_LENGTH - 1, Math.floor(rpm / TORQUE_RPM_STEP)))}`;

  // gearbox
  gears: Nfs2GearRow[] = [];
  gearSeries: CurveSeries[] = [];
  gearMarkers: CurveMarker[] = [];
  arcadeAccelSeries: CurveSeries[] = [];
  simAccelSeries: CurveSeries[] = [];
  simAccelMarkers: CurveMarker[] = [];
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
  readonly decelAxis: CurveAxis = { label: 'Max braking (m/s²)', min: 0 };
  readonly describeTime = (s: number) => `${fmt(s, 2)} s · step ${Math.round(s * STEPS)}`;
  readonly describeLevel = (x: number) => `pedal ${PEDAL_LEVELS[Math.round(x)] ?? ''}`;

  // handling
  steerSeries: CurveSeries[] = [];
  steerAxis: CurveAxis = { label: 'Yaw rate (game units)', min: 0 };
  steerRampSeries: CurveSeries[] = [];
  readonly steerRampAxis: CurveAxis = { label: 'Steering (0-127)', min: 0, max: STEER_MAX, format: v => fmt(v, 0) };

  // chassis
  downforceSeries: CurveSeries[] = [];
  readonly gripAxis: CurveAxis = { label: 'Grip ×', min: 1 };

  protected refresh(): void {
    const d = this.d;
    if (!d || !Array.isArray(d['torque_curve']) || !Array.isArray(d['velocity_to_rpm_ratio'])) return;
    this.buildEngine();
    this.buildGears();
    this.buildPedals();
    this.buildBrakes();
    this.buildHandling();
    this.buildChassis();
    this.buildTiles();
  }

  // ---------- derived values ----------

  get redline(): number {
    return this.d['engine_redline_rpm'] || 0;
  }

  private get numGears(): number {
    return Math.max(0, Math.min(this.d['velocity_to_rpm_ratio'].length, this.d['num_gears'] || 0));
  }

  // torque entries the game can read: up to the redline
  get torqueActiveCount(): number {
    return Math.max(1, Math.min(TORQUE_LENGTH, Math.floor(this.redline / TORQUE_RPM_STEP) + 1));
  }

  torqueAt(rpm: number, torques: number[] = this.d['torque_curve']): number {
    return torques[Math.max(0, Math.min(TORQUE_LENGTH - 1, Math.floor(rpm / TORQUE_RPM_STEP)))] || 0;
  }

  // drive acceleration of a gear in m/s² per N·m (specs+0x1a8)
  drive(gear: number): number {
    const mass = this.d['mass'] || 0;
    if (!mass) return 0;
    return ((this.d['velocity_to_rpm_ratio'][gear] || 0) / mass / 10) * (this.d['gear_efficiency'][gear] ?? 0);
  }

  // m/s at `rpm` in a gear
  speedAt(rpm: number, gear: number): number {
    const ratio = Math.abs(this.d['velocity_to_rpm_ratio'][gear] || 0);
    return ratio > 0 ? rpm / ratio : 0;
  }

  private simCap(gear: number): number {
    return gear === 2 ? SIM_CAP_FIRST : SIM_CAP;
  }

  // simulation air drag factor (specs+0x1c8, 0x459560): top gear drive at max_velocity / max_velocity³, whole m/s
  get simDragFactor(): number {
    const top = this.numGears - 1;
    const v = Math.trunc(this.d['max_velocity'] || 0);
    if (top < 2 || v < 1) return 0;
    const rpm = Math.trunc((this.d['max_velocity'] || 0) * (this.d['velocity_to_rpm_ratio'][top] || 0));
    return (this.torqueAt(rpm) * this.drive(top)) / (v * v * v);
  }

  private peak(torques: number[]) {
    let power = { kw: 0, rpm: 0 };
    let torque = { nm: 0, rpm: 0 };
    for (let i = 0; i < this.torqueActiveCount; i++) {
      const rpm = i * TORQUE_RPM_STEP;
      const t = torques[i] || 0;
      const kw = powerKw(t, rpm);
      if (kw > power.kw) power = { kw, rpm };
      if (t > torque.nm) torque = { nm: t, rpm };
    }
    return { power, torque };
  }

  // end of the speed axes: a bit past the faster of the top gear and max_velocity
  private get speedEnd(): number {
    const top = this.numGears - 1;
    const topGear = top >= 2 ? this.speedAt(this.redline, top) : 0;
    return Math.max(30, topGear, this.d['max_velocity'] || 0) * 1.1;
  }

  // ---------- engine ----------

  private buildEngine(torques: number[] = this.d['torque_curve']) {
    const points = torques.map((t, i) => ({ x: i * TORQUE_RPM_STEP, y: t }));
    const active = this.torqueActiveCount;
    this.torqueSeries = [
      {
        id: 'torque_curve',
        label: 'Torque',
        color: '#3f51b5',
        style: 'step',
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
        points: points.map(p => ({ x: p.x, y: powerKw(p.y, p.x) * KW_TO_HP })),
        activeCount: active,
        formatY: v => `${fmt(v, 0)} hp · ${fmt(v / KW_TO_HP, 0)} kW`,
      },
    ];
    this.torqueMarkers = [
      {
        id: 'engine_redline_rpm',
        value: this.redline,
        label: 'Redline',
        color: '#d32f2f',
        editable: true,
        constraints: { min: 1000, max: (TORQUE_LENGTH - 1) * TORQUE_RPM_STEP, step: 50 },
        format: v => fmt(v, 0),
      },
    ];
  }

  onTorquePreview(e: CurveSeriesChange) {
    // live power curve and peaks while dragging
    const torques = e.points.map(p => p.y);
    this.torqueSeries = [
      this.torqueSeries[0],
      { ...this.torqueSeries[1], points: e.points.map(p => ({ x: p.x, y: powerKw(p.y, p.x) * KW_TO_HP })) },
    ];
    this.buildTiles(torques);
  }

  onTorqueChange(e: CurveSeriesChange) {
    const torques = [...this.d['torque_curve']];
    for (const i of e.changed) torques[i] = Math.max(0, Math.round(e.points[i].y));
    this.setValue(['torque_curve'], torques);
  }

  onRedlineMarker(e: CurveMarkerChange) {
    this.setValue(['engine_redline_rpm'], Math.round(e.value));
  }

  // ---------- gearbox ----------

  private buildGears(ratios: number[] = this.d['velocity_to_rpm_ratio']) {
    const d = this.d;
    const redline = this.redline;
    const maxTorque = Math.max(0, ...(d['torque_curve'] as number[]).slice(0, this.torqueActiveCount));
    const top = this.numGears - 1;
    const speedAt = (rpm: number, i: number) => (Math.abs(ratios[i]) > 0 ? rpm / Math.abs(ratios[i]) : 0);
    this.gears = [];
    for (let i = 0; i < this.numGears; i++) {
      const drive = Math.abs(this.drive(i));
      const shifts = i >= 2 && i < top;
      this.gears.push({
        index: i,
        name: gearName(i),
        color: i >= 2 ? GEAR_COLORS[(i - 2) % GEAR_COLORS.length] : '#9e9e9e',
        ratio: ratios[i],
        efficiency: d['gear_efficiency'][i],
        drive,
        redlineSpeed: speedAt(redline, i) * MPS_TO_KMH,
        arcadePeak: maxTorque * drive * ARCADE_DRIVE,
        simPeak: Math.min(this.simCap(i), maxTorque * drive),
        upshiftSpeed: shifts ? speedAt(redline - UPSHIFT_MARGIN, i) * MPS_TO_KMH : null,
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
      pointLabels: ['', 'speed at the redline, drag to change the ratio'],
      formatY: v => fmt(v, 0) + ' rpm',
    }));
    const shifts = forward.filter(g => g.upshiftSpeed !== null);
    const drops: CurvePoint[] = [];
    for (const g of shifts) {
      const next = this.gears[g.index + 1];
      if (!next) continue;
      drops.push(
        { x: g.upshiftSpeed!, y: redline - UPSHIFT_MARGIN },
        { x: g.upshiftSpeed!, y: (g.upshiftSpeed! / MPS_TO_KMH) * Math.abs(next.ratio) },
        { x: NaN, y: NaN },
      );
    }
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
        label: 'Arcade upshift',
        color: '#424242',
        style: 'points',
        points: shifts.map(g => ({ x: g.upshiftSpeed!, y: redline - UPSHIFT_MARGIN })),
        pointLabels: shifts.map(g => `${g.name} → ${gearName(g.index + 1)}`),
        formatY: v => fmt(v, 0) + ' rpm',
      },
    );
    this.gearMarkers = [
      {
        id: 'engine_redline_rpm',
        value: redline,
        orientation: 'horizontal',
        label: 'Redline',
        color: '#d32f2f',
        editable: true,
        constraints: { min: 1000, max: (TORQUE_LENGTH - 1) * TORQUE_RPM_STEP, step: 50 },
        format: v => fmt(v, 0),
      },
      {
        id: 'downshift',
        value: redline - DOWNSHIFT_MARGIN,
        orientation: 'horizontal',
        label: 'Arcade downshift below',
        color: '#90a4ae',
        format: v => fmt(v, 0),
      },
      this.maxVelocityMarker(),
    ];

    // drive acceleration by speed in each gear, full gas on a dry road, from the torque entries up to the redline
    const curve = (g: Nfs2GearRow, accel: (torque: number) => number): CurvePoint[] => {
      const points: CurvePoint[] = [];
      for (let i = 1; i < this.torqueActiveCount; i++) {
        const rpm = i * TORQUE_RPM_STEP;
        points.push({ x: speedAt(rpm, g.index) * MPS_TO_KMH, y: accel(d['torque_curve'][i]) });
      }
      points.push({ x: g.redlineSpeed, y: accel(this.torqueAt(redline)) });
      return points;
    };
    const formatY = (v: number) => `${fmt(v, 2)} m/s² · ${fmt(v / G, 2)} g`;
    this.arcadeAccelSeries = forward.map(g => ({
      id: 'arcade-' + g.index,
      label: g.name,
      color: g.color,
      style: 'step' as const,
      points: curve(g, t => t * g.drive * ARCADE_DRIVE),
      formatY,
    }));
    this.simAccelSeries = forward.map(g => ({
      id: 'sim-' + g.index,
      label: g.name,
      color: g.color,
      style: 'step' as const,
      points: curve(g, t => Math.min(this.simCap(g.index), t * g.drive)),
      formatY,
    }));
    const k = this.simDragFactor;
    if (k > 0) {
      const drag: CurvePoint[] = [];
      for (let v = 0; v <= this.speedEnd; v++) drag.push({ x: v * MPS_TO_KMH, y: k * v * v * v });
      this.simAccelSeries.push({
        id: 'drag',
        label: 'Air drag',
        color: '#00897b',
        style: 'step',
        dashed: true,
        points: drag,
        formatY,
      });
    }
    this.simAccelMarkers = [this.maxVelocityMarker()];
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

  onGearPreview(e: CurveSeriesChange) {
    if (!e.seriesId.startsWith('gear-')) return;
    const ratios = [...this.d['velocity_to_rpm_ratio']];
    ratios[+e.seriesId.substring(5)] = this.ratioForSpeed(e.points[1].x);
    this.buildGears(ratios);
  }

  onGearChange(e: CurveSeriesChange) {
    if (!e.seriesId.startsWith('gear-')) return;
    this.setValue(['velocity_to_rpm_ratio', +e.seriesId.substring(5)], this.ratioForSpeed(e.points[1].x));
  }

  onSpeedMarker(e: CurveMarkerChange) {
    if (e.markerId === 'max_velocity') {
      this.setValue(['max_velocity'], this.round(e.value / MPS_TO_KMH, 2));
    } else if (e.markerId === 'engine_redline_rpm') {
      this.setValue(['engine_redline_rpm'], Math.round(e.value));
    }
  }

  // gear ratio (rpm per m/s) that reaches `kmh` at the redline
  private ratioForSpeed(kmh: number): number {
    return kmh > 0 ? this.round(this.redline / (kmh / MPS_TO_KMH), 2) : 0;
  }

  // ---------- brakes and pedals ----------

  private buildPedals() {
    const d = this.d;
    // pedal value per physics step: up by min(step, what is left), the step from the table of the pedal level
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
    const level = (curve: number[], v: number) => curve[Math.min(7, Math.floor(v / 32))];
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
        points: ramp(0, v => level(d['brake_increasing_curve'], v), true),
      },
      {
        id: 'brake_off',
        label: 'Brake release',
        color: '#e53935',
        dashed: true,
        points: ramp(255, v => level(d['brake_decreasing_curve'], v), false),
      },
    ].map(s => ({ ...s, style: 'step' as const, formatY: (v: number) => fmt(v, 0) }));

    const steps = (id: string, label: string, color: string, dashed: boolean): CurveSeries => ({
      id,
      label,
      color,
      dashed,
      points: (d[id] as number[]).map((y, x) => ({ x, y })),
      editable: 'y',
      y: { min: 0, max: 255, step: 1 },
      formatY: v => fmt(v, 0),
    });
    this.rampSeries = [
      steps('brake_increasing_curve', 'Brake up', '#e53935', false),
      steps('brake_decreasing_curve', 'Brake down', '#e53935', true),
      steps('gas_increasing_curve', 'Gas up (unused)', '#9e9e9e', false),
      steps('gas_decreasing_curve', 'Gas down (unused)', '#9e9e9e', true),
    ];
  }

  onRampChange(e: CurveSeriesChange) {
    const curve = [...this.d[e.seriesId]];
    for (const i of e.changed) curve[i] = Math.max(0, Math.min(255, Math.round(e.points[i].y)));
    this.setValue([e.seriesId], curve);
  }

  private buildBrakes() {
    const m = this.d['max_braking_deceleration'] || 0;
    const end = this.speedEnd * MPS_TO_KMH;
    const formatY = (v: number) => `${fmt(v, 1)} m/s² · ${fmt(v / G, 2)} g`;
    this.brakeSeries = [
      {
        id: 'arcade',
        label: 'Arcade',
        color: '#c62828',
        style: 'step',
        points: [
          { x: 0, y: m * ARCADE_BRAKE * ARCADE_SLOW_BRAKE },
          { x: ARCADE_SLOW_BRAKE_SPEED * MPS_TO_KMH, y: m * ARCADE_BRAKE },
          // 4 points: the chart reads sparser lines as straight lines in the tooltip
          { x: end / 2, y: m * ARCADE_BRAKE },
          { x: end, y: m * ARCADE_BRAKE },
        ],
        editable: 'y',
        lockedIndices: [2, 3],
        y: { min: 0, step: 0.1 },
        pointLabels: ['below 10 m/s: 1.5 × max_braking_deceleration', 'above: 2 × max_braking_deceleration', '', ''],
        formatY,
      },
      {
        id: 'sim',
        label: 'Simulation',
        color: '#6a1b9a',
        style: 'step',
        points: [
          { x: 0, y: m },
          { x: end, y: m },
        ],
        editable: 'y',
        lockedIndices: [1],
        y: { min: 0, step: 0.1 },
        pointLabels: ['max_braking_deceleration', ''],
        formatY,
      },
    ];
  }

  onBrakeChange(e: CurveSeriesChange) {
    const i = e.changed[0];
    if (i === undefined) return;
    const y = e.points[i].y;
    const k = e.seriesId === 'sim' ? 1 : i === 0 ? ARCADE_BRAKE * ARCADE_SLOW_BRAKE : ARCADE_BRAKE;
    this.setValue(['max_braking_deceleration'], this.round(y / k, 2));
  }

  // ---------- handling ----------

  // arcade yaw rate at full lock (0x4539e0), in 1/65536 units of car+0x30c as a fraction
  yawAtFullLock(v: number, turnFactor: number): number {
    let gain = (this.d['max_steering_acceleration'] || 0) / 64;
    if (v < STEER_SLOW_SPEED) gain *= v * 0.2;
    else if (v > STEER_FAST_SPEED) gain /= 1 + v * turnFactor;
    return (gain / 128) * STEER_MAX;
  }

  // arcade push slide limit (0x452fa0): yaw rate above which a push slide starts with the gas below 64
  pushLimit(v: number): number {
    const s = Math.trunc(v);
    if (s < 1) return Infinity;
    return (((this.d['push_factor'] || 0) + PUSH_MARGIN) * 512) / (s * s) / 0x10000;
  }

  private buildHandling() {
    const d = this.d;
    const end = this.speedEnd;
    const on: CurvePoint[] = [];
    const off: CurvePoint[] = [];
    const push: CurvePoint[] = [];
    const n = 120;
    for (let i = 0; i <= n; i++) {
      const v = (end * i) / n;
      on.push({ x: v * MPS_TO_KMH, y: this.yawAtFullLock(v, d['high_turn_factor'] || 0) });
      off.push({ x: v * MPS_TO_KMH, y: this.yawAtFullLock(v, d['low_turn_factor'] || 0) });
    }
    const yMax = Math.max(0.01, ...on.map(p => p.y), ...off.map(p => p.y)) * 1.25;
    for (let v = 1; v <= end; v++) {
      const limit = this.pushLimit(v);
      if (limit <= yMax) push.push({ x: v * MPS_TO_KMH, y: limit });
    }
    this.steerAxis = { label: 'Yaw rate (game units)', min: 0, max: yMax };
    const formatY = (v: number) => fmt(v, 3);
    this.steerSeries = [
      { id: 'on_gas', label: 'Full lock, on gas', color: '#5e35b1', points: on, formatY },
      { id: 'off_gas', label: 'Full lock, off gas', color: '#5e35b1', dashed: true, points: off, formatY },
      { id: 'push', label: 'Push slide above (off gas)', color: '#ef6c00', style: 'step', points: push, formatY },
    ];

    const ramp = (start: number, step: number, rising: boolean): CurvePoint[] => {
      const pts: CurvePoint[] = [{ x: 0, y: start }];
      let v = start;
      for (let t = 1; t <= 10 * STEPS && step > 0; t++) {
        v = rising ? Math.min(STEER_MAX, v + step) : Math.max(0, v - step);
        pts.push({ x: t / STEPS, y: v });
        if (v === (rising ? STEER_MAX : 0)) break;
      }
      return pts;
    };
    this.steerRampSeries = [
      { id: 'turn_in', label: 'Turn in', color: '#5e35b1', points: ramp(0, d['turn_in_ramp'] || 0, true) },
      {
        id: 'turn_out',
        label: 'Back to centre',
        color: '#5e35b1',
        dashed: true,
        points: ramp(STEER_MAX, d['turn_out_ramp'] || 0, false),
      },
    ].map(s => ({ ...s, style: 'step' as const, formatY: (v: number) => fmt(v, 0) }));
  }

  // ---------- chassis ----------

  private buildChassis() {
    const aero = this.d['aerodynamic_downforce_multiplier'] || 0;
    const end = this.speedEnd;
    const front: CurvePoint[] = [];
    const rear: CurvePoint[] = [];
    for (let v = 0; v <= end; v += 1) {
      const on = v > DOWNFORCE_MIN_SPEED;
      front.push({ x: v * MPS_TO_KMH, y: on ? 1 + v * aero : 1 });
      rear.push({ x: v * MPS_TO_KMH, y: on ? 1 + v * aero * REAR_DOWNFORCE : 1 });
    }
    const formatY = (v: number) => '× ' + fmt(v, 3);
    this.downforceSeries = [
      { id: 'front', label: 'Front', color: '#1e88e5', points: front, formatY },
      { id: 'rear', label: 'Rear', color: '#f4511e', points: rear, formatY },
    ];
  }

  // ---------- summary ----------

  private buildTiles(torques: number[] = this.d['torque_curve']) {
    const d = this.d;
    const { power, torque } = this.peak(torques);
    const hp = power.kw * KW_TO_HP;
    const mass = d['mass'] || 0;
    const fdr = d['front_drive_ratio'] || 0;
    const drive = fdr <= 0 ? 'RWD' : fdr >= 1 ? 'FWD' : 'AWD';
    const top = d['max_velocity'] || 0;
    const topGear = this.numGears - 1;
    const topGearSpeed = topGear >= 2 ? this.speedAt(this.redline, topGear) * MPS_TO_KMH : 0;
    const brake = d['max_braking_deceleration'] || 0;
    this.tiles = [
      {
        id: 'peak_power',
        label: 'Peak power',
        value: `${fmt(hp, 0)} hp`,
        edit: { value: Math.round(hp), step: 1, min: 1, unit: 'hp' },
        sub: `${fmt(power.kw, 0)} kW @ ${fmt(power.rpm, 0)} rpm`,
        hint: 'Peak of the torque curve up to the redline. A new value scales the whole torque curve',
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
        id: 'engine_redline_rpm',
        label: 'Redline',
        value: `${fmt(this.redline, 0)} rpm`,
        edit: { value: this.redline, step: 50, min: 1000, max: (TORQUE_LENGTH - 1) * TORQUE_RPM_STEP, unit: 'rpm' },
        sub: `upshift ${fmt(this.redline - UPSHIFT_MARGIN, 0)} rpm`,
        hint: 'engine_redline_rpm. The arcade automatic gearbox shifts up 500 rpm below it',
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
        sub: `top gear ${fmt(topGearSpeed, 0)} km/h`,
        hint: 'max_velocity: the simulation style air drag stops the car there. The arcade style has no air drag: its top speed is the top gear at the redline',
      },
      {
        label: 'Drivetrain',
        value: drive,
        sub: `${Math.max(0, this.numGears - 2)}-speed · shift ${d['gear_shift_delay']}`,
        hint:
          (drive === 'AWD' ? `${fmt(fdr * 100, 0)}% of the drive force on the front axle (simulation). ` : '') +
          'Set by the front_drive_ratio slider in the Gearbox tab. Shift: gear_shift_delay in physics steps (32 per second)',
      },
      {
        id: 'max_braking_deceleration',
        label: 'Braking',
        value: `${fmt(brake, 1)} m/s²`,
        edit: { value: this.round(brake, 2), step: 0.5, min: 0, unit: 'm/s²' },
        sub: `arcade ${fmt(brake * ARCADE_BRAKE, 1)} · ${fmt((d['front_bias_brake_ratio'] || 0) * 100, 0)}% front`,
        hint: 'max_braking_deceleration: the simulation style brakes with it, the arcade style with twice it',
      },
    ];
    if (!mass) {
      this.tiles.push({ label: 'Mass', value: '0', sub: 'the car has no drive force', tone: 'warn' });
    }
  }

  onTileChange(e: { id: string; value: number }) {
    const d = this.d;
    if (e.id === 'peak_power' || e.id === 'peak_torque') {
      const { power, torque } = this.peak(d['torque_curve']);
      const old = e.id === 'peak_power' ? power.kw * KW_TO_HP : torque.nm;
      if (!old) return;
      const k = e.value / old;
      this.setValue(
        ['torque_curve'],
        (d['torque_curve'] as number[]).map(t => this.round(Math.max(0, t * k), 1)),
      );
    } else if (e.id === 'max_velocity') {
      this.setValue(['max_velocity'], this.round(e.value / MPS_TO_KMH, 2));
    } else if (e.id === 'engine_redline_rpm') {
      this.setValue(['engine_redline_rpm'], Math.round(e.value));
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
