import { ChangeDetectionStrategy, Component } from '@angular/core';
import {
  CurveAxis,
  CurveMarker,
  CurveMarkerChange,
  CurvePoint,
  CurveSeries,
  CurveSeriesChange,
  CurveEditorComponent,
} from '../../common/curve-editor/curve-editor.component';
import { StatTile, StatTilesComponent } from '../../common/stat-tiles/stat-tiles.component';
import { SliderSpec, SliderFieldComponent } from '../../common/slider-field/slider-field.component';
import { CarSpecEditorBase, fmt, G, GEAR_COLORS, MPS_TO_KMH } from '../player-car-physics.block-ui/car-specs';
import {
  LBFT_TO_NM,
  NFS5_BOOST_RANGES,
  NFS5_BRAKE_SPEED_CAP,
  NFS5_DOWNFORCE_MIN_SPEED,
  NFS5_DOWNSHIFT,
  NFS5_G,
  NFS5_GEAR_NAMES,
  NFS5_MPH_TO_MPS,
  NFS5_REV_LIMIT_NEUTRAL,
  NFS5_STEER,
  NFS5_STEPS,
  NFS5_TORQUE_LENGTH,
  NFS5_TORQUE_STEP,
  NFS5_UPSHIFT,
  NFS5_UPSHIFT_RANDOM,
  Nfs5SpeedRun,
  nfs5DragAt,
  nfs5DragModel,
  nfs5ForwardGears,
  nfs5GearTorque,
  nfs5PowerHp,
  nfs5SimCircumference,
  nfs5SimRpmPerMps,
  nfs5SpeedRun,
  nfs5SteeringLock,
  nfs5TopGearSkipped,
  nfs5TorqueActiveCount,
  nfs5TorqueAt,
} from './nfs5-car-physics';
import { MatTooltip } from '@angular/material/tooltip';
import { BlockActionsComponent } from '../../common/block-actions/block-actions.component';
import { CompoundBlockUiComponent } from '../../library/compound.block-ui/compound.block-ui.component';
import { MatTabGroup, MatTab, MatTabContent } from '@angular/material/tabs';
import { NgTemplateOutlet } from '@angular/common';
import { MatCheckbox } from '@angular/material/checkbox';

const MPH_TO_KMH = NFS5_MPH_TO_MPS * MPS_TO_KMH;

export type Nfs5GearRow = {
  slot: number;
  name: string;
  color: string;
  ratio: number;
  // engine rpm per m/s
  rpmPerMps: number;
  // km/h at the redline
  redlineSpeed: number;
  // drive acceleration at the peak torque, full gas (m/s²)
  peakDrive: number;
  upshiftSpeed: number | null;
  downshiftSpeed: number | null;
};

// Rich editor of NFS5 car physics (GameData/Simulation/CarData/<spec>.sim, Nfs5CarPhysics): dyno (torque curve in
// lb·ft, power), gearing with the automatic gearbox, drive against the air drag and an idealized speed run, brakes,
// downforce, steering lock and suspension, every field grouped by subsystem. The derived curves follow Porsche.exe as
// the field descriptions give it (nfs-web's src/nfs5/nfs5-physics); they show the car as the file has it: the menus'
// default setup and no installed parts (nfs5.prt), which the game adds when it loads the car (0x49cb50)
@Component({
  selector: 'app-nfs5-car-physics-block-ui',
  templateUrl: './nfs5-car-physics.block-ui.component.html',
  styleUrls: ['../player-car-physics.block-ui/player-car-physics.block-ui.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    MatTooltip,
    BlockActionsComponent,
    SliderFieldComponent,
    CompoundBlockUiComponent,
    StatTilesComponent,
    MatTabGroup,
    MatTab,
    MatTabContent,
    CurveEditorComponent,
    NgTemplateOutlet,
    MatCheckbox,
  ],
})
export class Nfs5CarPhysicsBlockUiComponent extends CarSpecEditorBase {
  readonly groups = {
    engine: ['redline', 'engine_braking', 'aspiration'],
    gearbox: ['forward_gears', 'shift_time', 'final_drive', 'top_speed'],
    tyres: ['tyre_width', 'tyre_aspect_ratio', 'rim_diameter'],
    brakes: ['brake_force'],
    aero: ['front_downforce', 'rear_downforce'],
    steering: ['steering_lock', 'toe', 'wheelbase'],
    suspension: [
      'suspension_travel',
      'ride_height',
      'pitch_gain',
      'roll_gain',
      'pitch_rate_limit',
      'roll_rate_limit',
      'lateral_load_transfer_divisor',
    ],
    identity: ['name', 'mass'],
    ai: ['ai_speed_slot_scale', 'ai_steer_lookahead', 'ai_corner_scale'],
    other: ['engine_position'],
  };

  // bounded shares and factors as sliders, over the range of the shipped files with some room
  readonly sliders: { [group: string]: [string, SliderSpec][] } = {
    gearbox: [
      ['front_drive_share', { min: 0, max: 100, step: 1, unit: '% front' }],
      ['gear_acceleration_factor', { min: 50, max: 120, step: 0.5, unit: '%' }],
    ],
    engine: [['engine_braking', { min: 0, max: 60, step: 0.5, unit: '%' }]],
    tyres: [
      ['grip', { min: 0.5, max: 3.5, step: 0.05, unit: 'g' }],
      ['front_weight_share', { min: 30, max: 70, step: 0.5, unit: '% front' }],
    ],
    brakes: [['front_brake_share', { min: 30, max: 90, step: 0.5, unit: '% front' }]],
    suspension: [
      ['load_transfer_lever', { min: 10, max: 50, step: 0.5, unit: '× 0.01' }],
      ['spring_load_transfer', { min: 0.3, max: 2, step: 0.05, unit: '×' }],
      ['damping_1', { min: 50, max: 100, step: 0.5, unit: '%' }],
      ['damping_2', { min: 50, max: 100, step: 0.5, unit: '%' }],
    ],
  };

  selectedTab = 0;
  // the car record's transmission (0 manual: x 1.05 drive, 0x49cb50), a preview choice: not in the .sim
  manual = false;
  tiles: StatTile[] = [];

  // engine
  torqueSeries: CurveSeries[] = [];
  torqueMarkers: CurveMarker[] = [];
  readonly rpmAxis: CurveAxis = { label: 'Engine speed (rpm)', min: 0, format: v => fmt(v, 0) };
  readonly torqueAxis: CurveAxis = { label: 'Torque (lb·ft)', min: 0 };
  readonly powerAxis: CurveAxis = { label: 'Power (hp)', min: 0 };
  readonly describeRpm = (rpm: number) => `${fmt(rpm, 0)} rpm · entry ${fmt(rpm / NFS5_TORQUE_STEP, 2)}`;

  // gearbox and acceleration
  gears: Nfs5GearRow[] = [];
  gearSeries: CurveSeries[] = [];
  gearMarkers: CurveMarker[] = [];
  accelSeries: CurveSeries[] = [];
  accelMarkers: CurveMarker[] = [];
  runSeries: CurveSeries[] = [];
  run: Nfs5SpeedRun | null = null;
  dragNote = '';
  readonly speedAxis: CurveAxis = { label: 'Speed (km/h)', min: 0, format: v => fmt(v, 0) };
  readonly gearRpmAxis: CurveAxis = { label: 'Engine speed (rpm)', min: 0, format: v => fmt(v, 0) };
  readonly accelAxis: CurveAxis = { label: 'Acceleration (m/s²)', min: 0 };
  readonly timeAxis: CurveAxis = { label: 'Time (s)', min: 0 };
  readonly describeSpeed = (kmh: number) =>
    `${fmt(kmh, 1)} km/h · ${fmt(kmh / MPS_TO_KMH, 1)} m/s · ${fmt(kmh / MPH_TO_KMH, 1)} mph`;
  readonly describeTime = (s: number) => `${fmt(s, 2)} s · step ${Math.round(s * NFS5_STEPS)}`;

  // brakes, aero, steering
  brakeSeries: CurveSeries[] = [];
  downforceSeries: CurveSeries[] = [];
  steerSeries: CurveSeries[] = [];
  readonly decelAxis: CurveAxis = { label: 'Braking (m/s²)', min: 0 };
  readonly loadAxis: CurveAxis = { label: 'Wheel load (grip × 9.8 units)', min: 0 };
  readonly steerAxis: CurveAxis = { label: 'Steering factor at full lock', min: 0 };

  protected refresh(): void {
    const d = this.d;
    if (!d || !Array.isArray(d['torque_curve']) || !Array.isArray(d['gear_ratios'])) return;
    this.buildEngine();
    this.buildGears();
    this.buildAcceleration();
    this.buildBrakesAndAero();
    this.buildSteering();
    this.buildTiles();
  }

  // ---------- derived values ----------

  get redline(): number {
    return this.d['redline'] || 0;
  }

  get torques(): number[] {
    return this.d['torque_curve'] || [];
  }

  get circumference(): number {
    return nfs5SimCircumference(this.d);
  }

  get forwardGears(): number {
    return nfs5ForwardGears(this.d);
  }

  // m/s, as the loader scales the .sim mph
  get topSpeed(): number {
    return (this.d['top_speed'] || 0) * NFS5_MPH_TO_MPS;
  }

  torqueAt(rpm: number, torques: number[] = this.torques): number {
    return nfs5TorqueAt(torques, rpm, this.redline);
  }

  peak(torques: number[] = this.torques) {
    let power = { hp: 0, rpm: 0 };
    let torque = { lbft: 0, rpm: 0 };
    for (let rpm = 0; rpm <= this.redline; rpm += 25) {
      const t = this.torqueAt(rpm, torques);
      const hp = nfs5PowerHp(t, rpm);
      if (hp > power.hp) power = { hp, rpm };
      if (t > torque.lbft) torque = { lbft: t, rpm };
    }
    return { power, torque };
  }

  // ---------- engine ----------

  private buildEngine(torques: number[] = this.torques) {
    const active = nfs5TorqueActiveCount(this.redline);
    const power: CurvePoint[] = [];
    for (let rpm = 0; rpm <= this.redline; rpm += 50) {
      power.push({ x: rpm, y: nfs5PowerHp(this.torqueAt(rpm, torques), rpm) });
    }
    this.torqueSeries = [
      {
        id: 'torque',
        label: 'Torque',
        color: '#3f51b5',
        points: torques.map((t, i) => ({ x: i * NFS5_TORQUE_STEP, y: t })),
        editable: 'y',
        activeCount: active,
        y: { min: 0, step: 1 },
        formatY: v => `${fmt(v, 1)} lb·ft · ${fmt(v * LBFT_TO_NM, 0)} N·m`,
      },
      {
        id: 'power',
        label: 'Power',
        color: '#e64a19',
        axis: 'right',
        points: power,
        formatY: v => `${fmt(v, 0)} hp · ${fmt(v * 0.7457, 0)} kW`,
      },
    ];
    this.torqueMarkers = [
      {
        id: 'redline',
        value: this.redline,
        label: 'Redline',
        color: '#d32f2f',
        editable: true,
        constraints: { min: 1000, max: (NFS5_TORQUE_LENGTH - 2) * NFS5_TORQUE_STEP, step: 50 },
        format: v => fmt(v, 0),
      },
    ];
    const boost = NFS5_BOOST_RANGES[this.d['aspiration']];
    if (boost) {
      this.torqueMarkers.push(
        {
          id: 'boost_lo',
          value: this.redline * boost[0],
          label: 'Boost from',
          color: '#00897b',
          format: v => fmt(v, 0),
        },
        {
          id: 'boost_hi',
          value: this.redline * boost[1],
          label: 'Full boost',
          color: '#00897b',
          format: v => fmt(v, 0),
        },
      );
    }
  }

  onTorquePreview(e: CurveSeriesChange) {
    if (e.seriesId !== 'torque') return;
    const torques = e.points.map(p => p.y);
    this.buildEngine(torques);
    this.buildTiles(torques);
  }

  onTorqueChange(e: CurveSeriesChange) {
    if (e.seriesId !== 'torque') return;
    const torques = [...this.torques];
    for (const i of e.changed) torques[i] = Math.max(0, this.round(e.points[i].y, 2));
    this.setValue(['torque_curve'], torques);
  }

  onRpmMarker(e: CurveMarkerChange) {
    if (e.markerId === 'redline') this.setValue(['redline'], Math.round(e.value));
  }

  // ---------- gearbox ----------

  private buildGears(ratios: number[] = this.d['gear_ratios']) {
    const d = this.d;
    const redline = this.redline;
    const n = this.forwardGears;
    const rpmPerMps = nfs5SimRpmPerMps(d, ratios);
    const peak = this.peak().torque.lbft;
    const lastUp = n + 1 - (nfs5TopGearSkipped(d) ? 1 : 0);
    const up = redline * NFS5_UPSHIFT;
    const down = redline * NFS5_DOWNSHIFT;
    this.gears = [];
    for (let slot = 0; slot < n + 2; slot++) {
      const r = rpmPerMps[slot] || 0;
      const forward = slot >= 2 && r > 0;
      const speed = r ? (redline / Math.abs(r)) * MPS_TO_KMH : 0;
      const k = nfs5GearTorque(Math.abs(r), d['mass'] || 0, d['gear_acceleration_factor'] || 0, this.manual);
      this.gears.push({
        slot,
        name: NFS5_GEAR_NAMES[slot],
        color: slot >= 2 ? GEAR_COLORS[(slot - 2) % GEAR_COLORS.length] : '#9e9e9e',
        ratio: ratios[slot] || 0,
        rpmPerMps: r,
        redlineSpeed: speed,
        peakDrive: slot === 1 ? 0 : peak * k,
        upshiftSpeed: forward && slot < lastUp ? (up / r) * MPS_TO_KMH : null,
        downshiftSpeed:
          forward && slot > 2 && rpmPerMps[slot - 1] > 0 ? (down / rpmPerMps[slot - 1]) * MPS_TO_KMH : null,
      });
    }
    const forward = this.gears.filter(g => g.slot >= 2 && g.rpmPerMps > 0);
    this.gearSeries = forward.map(g => ({
      id: 'gear-' + g.slot,
      label: g.name,
      color: g.color,
      points: [
        { x: 0, y: 0 },
        { x: g.redlineSpeed, y: redline },
      ],
      editable: 'x' as const,
      lockedIndices: [0],
      x: { min: 1, step: 0.1 },
      pointLabels: ['', 'speed at the redline, drag to change the gear ratio'],
      formatY: v => fmt(v, 0) + ' rpm',
    }));
    const ups = forward.filter(g => g.upshiftSpeed !== null);
    const downs = forward.filter(g => g.downshiftSpeed !== null);
    this.gearSeries.push(
      {
        id: 'upshifts',
        label: 'Automatic up-shift (from)',
        color: '#424242',
        style: 'points',
        points: ups.map(g => ({ x: g.upshiftSpeed!, y: up })),
        pointLabels: ups.map(g => `${g.name} → ${NFS5_GEAR_NAMES[g.slot + 1]}`),
        formatY: v => fmt(v, 0) + ' rpm',
      },
      {
        id: 'downshifts',
        label: 'Automatic down-shift below',
        color: '#90a4ae',
        style: 'points',
        points: downs.map(g => ({ x: g.downshiftSpeed!, y: (g.downshiftSpeed! / MPS_TO_KMH) * g.rpmPerMps })),
        pointLabels: downs.map(g => `${g.name} → ${NFS5_GEAR_NAMES[g.slot - 1]}`),
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
        constraints: { min: 1000, max: (NFS5_TORQUE_LENGTH - 2) * NFS5_TORQUE_STEP, step: 50 },
        format: v => fmt(v, 0),
      },
      {
        id: 'upshift',
        value: up,
        orientation: 'horizontal',
        label: 'Up-shift from 0.9 × redline',
        color: '#424242',
        format: v => fmt(v, 0),
      },
      this.topSpeedMarker(),
    ];
  }

  private topSpeedMarker(): CurveMarker {
    return {
      id: 'top_speed',
      value: this.topSpeed * MPS_TO_KMH,
      label: 'Top speed',
      color: '#455a64',
      editable: true,
      constraints: { min: 1, step: 0.5 },
      format: v => `${fmt(v, 0)} km/h · ${fmt(v / MPH_TO_KMH, 1)} mph`,
    };
  }

  onGearPreview(e: CurveSeriesChange) {
    if (!e.seriesId.startsWith('gear-')) return;
    const ratios = [...this.d['gear_ratios']];
    ratios[+e.seriesId.substring(5)] = this.ratioForSpeed(e.points[1].x);
    this.buildGears(ratios);
  }

  onGearChange(e: CurveSeriesChange) {
    if (!e.seriesId.startsWith('gear-')) return;
    this.setValue(['gear_ratios', +e.seriesId.substring(5)], this.ratioForSpeed(e.points[1].x));
  }

  onSpeedMarker(e: CurveMarkerChange) {
    if (e.markerId === 'top_speed') {
      this.setValue(['top_speed'], this.round(e.value / MPH_TO_KMH, 2));
    } else if (e.markerId === 'redline') {
      this.setValue(['redline'], Math.round(e.value));
    }
  }

  onGearRatioInput(slot: number, raw: string) {
    this.onNumberInput(['gear_ratios', slot], raw);
  }

  onManualChange(value: boolean) {
    this.manual = value;
    this.refresh();
  }

  // the gear ratio that reaches `kmh` at the redline
  ratioForSpeed(kmh: number): number {
    const c = this.circumference;
    const fd = this.d['final_drive'] || 0;
    if (!(kmh > 0) || !c || !fd) return 0;
    return this.round((this.redline / (kmh / MPS_TO_KMH)) * (c / (fd * 60)), 4);
  }

  // ---------- acceleration ----------

  private buildAcceleration() {
    const d = this.d;
    const model = nfs5DragModel(d, this.manual);
    const forward = this.gears.filter(g => g.slot >= 2 && g.rpmPerMps > 0);
    const formatY = (v: number) => `${fmt(v, 2)} m/s² · ${fmt(v / G, 2)} g`;
    this.accelSeries = forward.map(g => {
      const points: CurvePoint[] = [];
      const vMax = g.redlineSpeed / MPS_TO_KMH;
      const k = nfs5GearTorque(g.rpmPerMps, d['mass'] || 0, d['gear_acceleration_factor'] || 0, this.manual);
      for (let i = 0; i <= 80; i++) {
        const v = (vMax * i) / 80;
        points.push({ x: v * MPS_TO_KMH, y: this.torqueAt(v * g.rpmPerMps) * k });
      }
      return { id: 'accel-' + g.slot, label: g.name, color: g.color, points, formatY };
    });
    const end = Math.max(this.topSpeed, ...forward.map(g => g.redlineSpeed / MPS_TO_KMH)) * 1.1;
    if (model) {
      const drag: CurvePoint[] = [];
      for (let i = 0; i <= 120; i++) {
        const v = (end * i) / 120;
        drag.push({ x: v * MPS_TO_KMH, y: nfs5DragAt(model, v) });
      }
      this.accelSeries.push({ id: 'drag', label: 'Air drag', color: '#00897b', dashed: true, points: drag, formatY });
      this.dragNote =
        `The air drag coefficient (${model.coefficient.toExponential(3)} × speed³) makes the top gear's drive at ` +
        `${fmt(model.rpm, 0)} rpm equal to the drag at the top speed.`;
    } else {
      this.dragNote = '';
    }
    this.accelMarkers = [this.topSpeedMarker()];
    this.run = nfs5SpeedRun(d, this.manual);
    this.runSeries = [
      {
        id: 'run',
        label: 'Speed',
        color: '#6a1b9a',
        points: this.run.points,
        formatY: v => `${fmt(v, 1)} km/h`,
      },
    ];
  }

  // ---------- brakes, aero, steering ----------

  private buildBrakesAndAero() {
    const d = this.d;
    const force = d['brake_force'] || 0;
    const front = (d['front_brake_share'] || 0) * 0.01;
    const end = Math.max(30, this.topSpeed * 1.1);
    const total: CurvePoint[] = [];
    const frontPts: CurvePoint[] = [];
    const rearPts: CurvePoint[] = [];
    for (let i = 0; i <= 100; i++) {
      const v = (end * i) / 100;
      const b = Math.min(force, Math.abs(v) * NFS5_BRAKE_SPEED_CAP);
      total.push({ x: v * MPS_TO_KMH, y: b });
      frontPts.push({ x: v * MPS_TO_KMH, y: b * front });
      rearPts.push({ x: v * MPS_TO_KMH, y: b * (1 - front) });
    }
    const formatB = (v: number) => `${fmt(v, 2)} m/s² · ${fmt(v / G, 2)} g`;
    this.brakeSeries = [
      { id: 'brake', label: 'Full brake', color: '#c62828', points: total, formatY: formatB },
      { id: 'front', label: 'Front', color: '#ef6c00', points: frontPts, formatY: formatB, dashed: true },
      { id: 'rear', label: 'Rear', color: '#6d4c41', points: rearPts, formatY: formatB, dashed: true },
    ];
    // the wheel loads (0x4a1900) on a flat road: grip x 9.8 x 0.5 x the axle's weight share, plus downforce x speed
    const w = (d['grip'] || 0) * NFS5_G * 0.5;
    const share = (d['front_weight_share'] || 0) * 0.01;
    const df = (d['front_downforce'] || 0) * 0.001;
    const dr = (d['rear_downforce'] || 0) * 0.001;
    const fl: CurvePoint[] = [];
    const rl: CurvePoint[] = [];
    for (let i = 0; i <= 100; i++) {
      const v = (end * i) / 100;
      const aero = v > NFS5_DOWNFORCE_MIN_SPEED;
      fl.push({ x: v * MPS_TO_KMH, y: w * share + (aero ? df * v : 0) });
      rl.push({ x: v * MPS_TO_KMH, y: w * (1 - share) + (aero ? dr * v : 0) });
    }
    const formatL = (v: number) => `${fmt(v, 3)} (${fmt(w ? (v / (w * 0.5)) * 50 : 0, 1)}% of a static wheel)`;
    this.downforceSeries = [
      { id: 'front_load', label: 'Front wheel', color: '#1565c0', points: fl, formatY: formatL },
      { id: 'rear_load', label: 'Rear wheel', color: '#2e7d32', points: rl, formatY: formatL },
    ];
  }

  private buildSteering() {
    const lock = this.d['steering_lock'] || 0;
    const end = Math.max(NFS5_STEER.fastSpeed * 1.4, this.topSpeed * 1.1);
    const pts: CurvePoint[] = [];
    for (let i = 0; i <= 120; i++) {
      const v = (end * i) / 120;
      pts.push({ x: v * MPS_TO_KMH, y: nfs5SteeringLock(lock, v) });
    }
    this.steerSeries = [{ id: 'lock', label: 'Full lock', color: '#5e35b1', points: pts, formatY: v => fmt(v, 2) }];
  }

  // ---------- tiles ----------

  private buildTiles(torques: number[] = this.torques) {
    const d = this.d;
    const { power, torque } = this.peak(torques);
    const mass = d['mass'] || 0;
    const fds = d['front_drive_share'] || 0;
    const drive = fds < 1 ? 'RWD' : fds > 99 ? 'FWD' : 'AWD';
    const n = this.forwardGears;
    const tyre = `${fmt(d['tyre_width'] || 0, 0)}/${fmt(d['tyre_aspect_ratio'] || 0, 0)} R${fmt(d['rim_diameter'] || 0, 0)}`;
    this.tiles = [
      {
        id: 'peak_power',
        label: 'Peak power',
        value: `${fmt(power.hp, 0)} hp`,
        edit: { value: Math.round(power.hp), step: 1, min: 1, unit: 'hp' },
        sub: `${fmt(power.hp * 0.7457, 0)} kW @ ${fmt(power.rpm, 0)} rpm`,
        hint: 'Peak of the interpolated torque curve up to the redline (hp = lb·ft × rpm / 5252). A new value scales the whole torque curve',
        tone: 'accent',
      },
      {
        id: 'peak_torque',
        label: 'Peak torque',
        value: `${fmt(torque.lbft, 0)} lb·ft`,
        edit: { value: Math.round(torque.lbft), step: 1, min: 1, unit: 'lb·ft' },
        sub: `${fmt(torque.lbft * LBFT_TO_NM, 0)} N·m @ ${fmt(torque.rpm, 0)} rpm`,
        hint: 'A new value scales the whole torque curve',
        tone: 'accent',
      },
      {
        id: 'redline',
        label: 'Redline',
        value: `${fmt(this.redline, 0)} rpm`,
        edit: { value: this.redline, step: 50, min: 1000, max: 9500, unit: 'rpm' },
        sub: `rev limiter to +${NFS5_REV_LIMIT_NEUTRAL}`,
        hint: this.descriptions['redline'],
      },
      {
        id: 'mass',
        label: 'Mass',
        value: `${fmt(mass, 0)} kg`,
        edit: { value: Math.round(mass), step: 5, min: 1, unit: 'kg' },
        sub: `${fmt(mass ? (power.hp / mass) * 1000 : 0, 0)} hp/t, before parts`,
        hint: this.descriptions['mass'],
      },
      {
        id: 'top_speed',
        label: 'Top speed',
        value: `${fmt(this.topSpeed * MPS_TO_KMH, 0)} km/h`,
        edit: { value: this.round(this.topSpeed * MPS_TO_KMH, 1), step: 1, min: 1, unit: 'km/h' },
        sub: `${fmt(d['top_speed'] || 0, 1)} mph in the file`,
        hint: this.descriptions['top_speed'],
      },
      {
        label: 'Acceleration',
        value: this.run?.to100 != null ? `${fmt(this.run.to100, 1)} s` : '–',
        sub: `0-100 km/h idealized${this.run?.to160 != null ? ` · 0-160 ${fmt(this.run.to160, 1)} s` : ''}`,
        hint: 'The speed run of the Acceleration tab: full gas, automatic gearbox, drive minus air drag; no tyres, wheel spin or clutch',
      },
      {
        label: 'Drivetrain',
        value: drive,
        sub: `${n}-speed · shift ${d['shift_time'] || 0} steps`,
        hint:
          (drive === 'AWD' ? `${fmt(fds, 0)}% of the drive force on the front wheels. ` : '') +
          'Shift time in physics steps (32 per second)',
      },
      {
        id: 'grip',
        label: 'Grip',
        value: `${fmt(d['grip'] || 0, 2)} g`,
        edit: { value: this.round(d['grip'] || 0, 2), step: 0.05, min: 0, unit: 'g' },
        sub: `${tyre} · ${fmt(this.circumference, 3)} m around`,
        hint: this.descriptions['grip'],
      },
      {
        id: 'brake_force',
        label: 'Braking',
        value: `${fmt(d['brake_force'] || 0, 1)} m/s²`,
        edit: { value: this.round(d['brake_force'] || 0, 2), step: 0.5, min: 0, unit: 'm/s²' },
        sub: `${fmt(d['front_brake_share'] || 0, 0)}% front`,
        hint: this.descriptions['brake_force'],
      },
    ];
    if (!mass) this.tiles.push({ label: 'Mass', value: '0', sub: 'the car has no drive force', tone: 'warn' });
  }

  onTileChange(e: { id: string; value: number }) {
    if (e.id === 'peak_power' || e.id === 'peak_torque') {
      const { power, torque } = this.peak();
      const old = e.id === 'peak_power' ? power.hp : torque.lbft;
      if (!old) return;
      const k = e.value / old;
      this.setValue(
        ['torque_curve'],
        this.torques.map(t => this.round(Math.max(0, t * k), 2)),
      );
    } else if (e.id === 'top_speed') {
      this.setValue(['top_speed'], this.round(e.value / MPH_TO_KMH, 2));
    } else if (e.id === 'redline') {
      this.setValue(['redline'], Math.round(e.value));
    } else {
      this.setValue([e.id], e.value);
    }
  }

  readonly fmt = fmt;
  readonly MPS_TO_KMH = MPS_TO_KMH;

  round(v: number, digits: number): number {
    const k = Math.pow(10, digits);
    return Math.round(v * k) / k;
  }
}
