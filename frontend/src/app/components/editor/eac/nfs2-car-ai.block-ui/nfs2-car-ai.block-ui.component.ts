import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
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
import { CarSpecEditorBase, fmt, G, GEAR_COLORS, MPS_TO_KMH, ordinal } from '../player-car-physics.block-ui/car-specs';

// acceleration table: one entry per m/s (nfs2sen.exe 0x42e7d0 reads entry abs(speed) >> 16, clamped to 0..111)
const TABLE_LENGTH = 112;
// 8.8 fixed point
const TABLE_STEP = 1 / 256;
const TABLE_MAX = 32767 / 256;
const GEAR_SLOTS = 7;
// AI steps per second at the full step rate (0x45e4c0: every 2nd tick of the 64 Hz sim, factor 1, scale 1/32)
const STEPS = 32;
// AI engine (0x42e9e0): from 3000 rpm in the gears above the first, 3000 rpm while a shift lasts
const SHIFT_RPM = 3000;
// in-control model (0x42d140): the grip grows with the forward speed, 1 + v * 0x62 / 0x10000
const GRIP_PER_MPS = 0x62 / 0x10000;
const SIM_SECONDS = 60;
const STYLES = ['simulation', 'arcade'] as const;
type Style = (typeof STYLES)[number];
const STYLE_COLORS: { [s in Style]: string } = { simulation: '#6a1b9a', arcade: '#ef6c00' };
const STYLE_LABELS: { [s in Style]: string } = { simulation: 'Simulation', arcade: 'Arcade' };

// car models below 15, in the order of the exe's model names (0x4c5fe0)
const MODEL_NAMES = [
  'MCF1',
  'FF50',
  'F355',
  'GT90',
  'IDGO',
  'MACH',
  'JAGR',
  'LGT1',
  'ESPR',
  'NAZC',
  'CALA',
  'ISDE',
  'CHEV',
  'DAYT',
  'FUTR',
];
// 0x4c4e38: the loader scales the acceleration table of these models by (simulation, arcade) (0x42efc0)
const MODEL_TABLE_SCALE: [number, number][] = [
  [0x10f5c, 0x10b85],
  [0x10f5c, 0x10b85],
  [0x10f5c, 0x1051e],
  [0x111eb, 0x10b85],
  [0x10f5c, 0x10b85],
  [0x10f5c, 0x1051e],
  [0xfae1, 0xfae1],
  [0x111eb, 0x10b85],
  [0x10a3d, 0x10000],
  [0x10000, 0x1051e],
  [0x1147a, 0x1051e],
  [0xfd70, 0xf5c2],
  [0xfd70, 0xf5c2],
  [0xfd70, 0xf5c2],
  [0x10f5c, 0x10b85],
].map(([s, a]) => [s / 0x10000, a / 0x10000]);
// 0x4c54cc: the AI drive stops above this speed of the model (m/s, 0x42e7d0)
const MODEL_TOP_SPEED = [
  0x674ccc, 0x5a4ccc, 0x51cccc, 0x626666, 0x508000, 0x504ccc, 0x5e3333, 0x573333, 0x4e3333, 0x564ccc, 0x50e666,
  0x5ecccc, 0x49b333, 0x5de666, 0x7ae666,
].map(v => v / 0x10000);

export type Nfs2AiModel = { index: number; name: string; tableScale: [number, number]; topSpeed: number };

export type Nfs2AiGearRow = {
  index: number;
  name: string;
  color: string;
  // m/s
  low: number;
  top: number;
};

export type Nfs2AiRun = {
  points: CurvePoint[];
  // seconds to 100 km/h, null when never reached
  to100: number | null;
  // m/s
  topSpeed: number;
};

// Rich editor of the NFS2 SE car AI data (<car>.dat in CARDATA.VIV): the acceleration tables of both game styles with
// the gear top speeds, a speed run made of them, the AI gearbox and the handling values. The derived curves follow
// the field descriptions (AI port `ai.c` of nfs-web's nfs2-physics)
@Component({
  selector: 'app-nfs2-car-ai-block-ui',
  templateUrl: './nfs2-car-ai.block-ui.component.html',
  styleUrls: ['../player-car-physics.block-ui/player-car-physics.block-ui.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: false,
})
export class Nfs2CarAiBlockUiComponent extends CarSpecEditorBase {
  override get resourceName(): string | undefined {
    return super.resourceName;
  }

  // the car model, and with it the table scale and the top speed, comes from the file name
  @Input()
  override set resourceName(value: string | undefined) {
    super.resourceName = value;
    if (this.resourceData) this.refresh();
  }

  readonly groups = {
    gearbox: ['ai_shift_duration'],
    handling: ['hi_handling_yaw', 'low_handling_yaw', 'handling_importance'],
    traffic: ['speed_factor_2', 'lane_slack_prob', 'speed_factor'],
  };

  readonly styles = STYLES;
  readonly styleLabels = STYLE_LABELS;
  readonly turnRateSlider: SliderSpec = { min: 0, max: 2, step: 0.01 };

  selectedTab = 0;
  tiles: StatTile[] = [];
  model: Nfs2AiModel | null = null;

  // acceleration
  tableSeries: CurveSeries[] = [];
  tableMarkers: CurveMarker[] = [];
  runSeries: CurveSeries[] = [];
  runs: { [s in Style]?: Nfs2AiRun } = {};
  readonly speedAxis: CurveAxis = { label: 'Speed (km/h)', min: 0, format: v => fmt(v, 0) };
  readonly accelAxis: CurveAxis = { label: 'Acceleration (m/s²)', min: 0 };
  readonly timeAxis: CurveAxis = { label: 'Time (s)', min: 0 };
  readonly runSpeedAxis: CurveAxis = { label: 'Speed (km/h)', min: 0, format: v => fmt(v, 0) };
  readonly describeSpeed = (kmh: number) =>
    `${fmt(kmh, 1)} km/h · ${fmt(kmh / MPS_TO_KMH, 1)} m/s · entry ${Math.max(0, Math.min(TABLE_LENGTH - 1, Math.floor(kmh / MPS_TO_KMH + 1e-9)))}`;
  readonly describeTime = (s: number) => `${fmt(s, 2)} s`;

  // gearbox
  gears: Nfs2AiGearRow[] = [];
  gearSeries: CurveSeries[] = [];
  gearMarkers: CurveMarker[] = [];
  readonly rpmAxis: CurveAxis = { label: 'Engine speed (rpm)', min: 0, format: v => fmt(v, 0) };

  // handling
  gripSeries: CurveSeries[] = [];
  readonly gripAxis: CurveAxis = { label: 'Lateral correction cap (m/s²)', min: 0 };
  handlingSeries: CurveSeries[] = [];
  handlingAxis: CurveAxis = { label: 'Yaw value', min: 0 };
  factorAxis: CurveAxis = { label: 'Speed multiplier', min: 0.5, max: 1.5, format: v => fmt(v, 2) };

  protected refresh(): void {
    const d = this.d;
    if (!d || !Array.isArray(d['gear_top_speeds']) || !d['simulation'] || !d['arcade']) return;
    this.model = this.findModel();
    this.buildAcceleration();
    this.buildGears();
    this.buildHandling();
    this.buildTiles();
  }

  // ---------- derived values ----------

  private findModel(): Nfs2AiModel | null {
    const name = (this.resourceName || '')
      .replace(/^.*[\\/]/, '')
      .replace(/\.dat$/i, '')
      .toUpperCase();
    const index = MODEL_NAMES.indexOf(name);
    if (index < 0) return null;
    return { index, name, tableScale: MODEL_TABLE_SCALE[index] as [number, number], topSpeed: MODEL_TOP_SPEED[index] };
  }

  get redline(): number {
    return this.d['redline'] || 0;
  }

  // forward gears: the top speeds up to the first 0
  get gearTops(): number[] {
    const tops: number[] = [];
    for (const v of this.d['gear_top_speeds'] as number[]) {
      if (!v) break;
      tops.push(v);
    }
    return tops;
  }

  tableScale(style: Style): number {
    return this.model ? this.model.tableScale[style === 'simulation' ? 0 : 1] : 1;
  }

  // the table as the game uses it, scaled for the car model (0x42efc0, in 8.8)
  scaledTable(style: Style, table: number[] = this.d[style]['acceleration_table']): number[] {
    const k = this.tableScale(style);
    return k === 1 ? table : table.map(v => Math.floor(Math.round(v * 256) * k) / 256);
  }

  // AI engine rpm at `v` m/s in a gear (0x42e9e0)
  rpmAt(v: number, gear: number, tops: number[] = this.gearTops): number {
    const low = gear > 0 ? tops[gear - 1] : 0;
    const base = gear > 0 ? SHIFT_RPM : 0;
    const range = tops[gear] - low;
    return range > 0 ? ((v - low) / range) * (this.redline - base) + base : base;
  }

  // full drive from standstill on a flat road, at the full AI step rate: the gearbox of 0x42e9e0 (a gear change stops
  // the drive for ai_shift_duration steps), the drive of 0x42e7d0 (table entry of the whole m/s, nothing above the
  // model's top speed). Without the race factors (glue, skill, personality)
  run(style: Style, table: number[] = this.scaledTable(style), tops: number[] = this.gearTops): Nfs2AiRun {
    const shiftDuration = Math.max(0, this.d['ai_shift_duration'] || 0);
    const topSpeed = this.model?.topSpeed ?? Infinity;
    const points: CurvePoint[] = [{ x: 0, y: 0 }];
    let v = 0;
    let gear = 0;
    let shift = 0;
    let to100: number | null = null;
    let still = 0;
    for (let step = 1; step <= SIM_SECONDS * STEPS; step++) {
      if (shift > 0) {
        shift--;
      } else if (tops.length) {
        for (;;) {
          if (gear < tops.length - 1 && tops[gear] < v) gear++;
          else if (gear > 0 && v < tops[gear - 1]) gear--;
          else break;
          shift = shiftDuration;
        }
      }
      let a = 0;
      if (shift <= 0 && v <= topSpeed) a = table[Math.max(0, Math.min(TABLE_LENGTH - 1, Math.floor(v)))] || 0;
      const before = v;
      v = Math.max(0, v + a / STEPS);
      const t = step / STEPS;
      if (to100 === null && v * MPS_TO_KMH >= 100) to100 = t;
      points.push({ x: t, y: v * MPS_TO_KMH });
      // no drive and no shift to come: the speed stays
      still = v === before && shift <= 0 ? still + 1 : 0;
      if (still > STEPS) break;
    }
    return { points, to100, topSpeed: v };
  }

  private get speedEnd(): number {
    const tops = this.gearTops;
    let lastDrive = 0;
    for (const style of STYLES) {
      const table = this.d[style]['acceleration_table'] as number[];
      for (let i = 0; i < table.length; i++) if (table[i]) lastDrive = Math.max(lastDrive, i + 1);
    }
    return Math.max(30, tops[tops.length - 1] || 0, lastDrive) * 1.05;
  }

  // ---------- acceleration ----------

  private buildAcceleration(tables?: { [s in Style]?: number[] }, tops: number[] = this.gearTops) {
    const formatY = (v: number) => `${fmt(v, 2)} m/s² · ${fmt(v / G, 2)} g`;
    this.tableSeries = STYLES.map(style => ({
      id: style,
      label: STYLE_LABELS[style],
      color: STYLE_COLORS[style],
      style: 'step' as const,
      points: (tables?.[style] ?? (this.d[style]['acceleration_table'] as number[])).map((y, i) => ({
        x: i * MPS_TO_KMH,
        y,
      })),
      editable: 'y' as const,
      y: { min: 0, max: TABLE_MAX, step: TABLE_STEP },
      formatY,
    }));
    this.tableMarkers = this.gearTopMarkers(tops);
    if (this.model) {
      this.tableMarkers.push({
        id: 'model_top_speed',
        value: this.model.topSpeed * MPS_TO_KMH,
        label: `${this.model.name} top speed`,
        color: '#455a64',
        format: v => fmt(v, 0) + ' km/h',
      });
    }

    this.runs = {};
    for (const style of STYLES) {
      const table = tables?.[style] ? this.scaledTable(style, tables[style]) : this.scaledTable(style);
      this.runs[style] = this.run(style, table, tops);
    }
    const end = Math.max(
      5,
      ...STYLES.map(s => {
        const pts = this.runs[s]!.points;
        const top = pts[pts.length - 1].y;
        // where the run gets within 1% of its final speed
        const reached = pts.find(p => p.y >= top * 0.99);
        return (reached?.x ?? SIM_SECONDS) * 1.15;
      }),
    );
    this.runSeries = STYLES.map(style => ({
      id: style,
      label: STYLE_LABELS[style],
      color: STYLE_COLORS[style],
      points: this.runs[style]!.points.filter(p => p.x <= end),
      formatY: (v: number) => `${fmt(v, 1)} km/h`,
    }));
  }

  private gearTopMarkers(tops: number[]): CurveMarker[] {
    return tops.map((top, i) => ({
      id: 'gear-' + i,
      value: top * MPS_TO_KMH,
      label: ordinal(i + 1),
      color: GEAR_COLORS[i % GEAR_COLORS.length],
      editable: true,
      constraints: {
        min: ((i > 0 ? tops[i - 1] : 0) + 0.5) * MPS_TO_KMH,
        max: i < tops.length - 1 ? (tops[i + 1] - 0.5) * MPS_TO_KMH : (TABLE_LENGTH + 20) * MPS_TO_KMH,
        step: 0.1,
      },
      format: v => `${fmt(v, 0)} km/h`,
    }));
  }

  onTablePreview(e: CurveSeriesChange) {
    const style = e.seriesId as Style;
    // live speed run and tiles while dragging
    const tables = { [style]: e.points.map(p => p.y) };
    this.buildAcceleration(tables);
    this.buildTiles();
  }

  onTableChange(e: CurveSeriesChange) {
    const style = e.seriesId as Style;
    const table = [...this.d[style]['acceleration_table']];
    for (const i of e.changed) table[i] = this.toTable(e.points[i].y);
    this.setValue([style, 'acceleration_table'], table);
  }

  private toTable(v: number): number {
    return Math.max(-128, Math.min(TABLE_MAX, Math.round(v / TABLE_STEP) * TABLE_STEP));
  }

  onMarkerPreview(e: CurveMarkerChange) {
    if (!e.markerId.startsWith('gear-')) return;
    const tops = [...this.gearTops];
    tops[+e.markerId.substring(5)] = e.value / MPS_TO_KMH;
    this.buildAcceleration(undefined, tops);
    this.buildGears(tops);
  }

  onMarker(e: CurveMarkerChange) {
    if (e.markerId === 'redline') {
      this.setValue(['redline'], Math.round(e.value));
    } else if (e.markerId.startsWith('gear-')) {
      this.setValue(['gear_top_speeds', +e.markerId.substring(5)], this.round(e.value / MPS_TO_KMH, 2));
    }
  }

  // ---------- gearbox ----------

  private buildGears(tops: number[] = this.gearTops) {
    this.gears = tops.map((top, i) => ({
      index: i,
      name: ordinal(i + 1),
      color: GEAR_COLORS[i % GEAR_COLORS.length],
      low: i > 0 ? tops[i - 1] : 0,
      top,
    }));
    const redline = this.redline;
    this.gearSeries = this.gears.map(g => ({
      id: 'gear-' + g.index,
      label: g.name,
      color: g.color,
      points: [
        { x: g.low * MPS_TO_KMH, y: this.rpmAt(g.low, g.index, tops) },
        { x: g.top * MPS_TO_KMH, y: redline },
      ],
      editable: 'x' as const,
      lockedIndices: [0],
      x: {
        min: (g.low + 0.5) * MPS_TO_KMH,
        max: g.index < tops.length - 1 ? (tops[g.index + 1] - 0.5) * MPS_TO_KMH : undefined,
        step: 0.1,
      },
      pointLabels: [g.index ? 'shift down below' : '', 'top speed: shift up above, drag to change'],
      formatY: (v: number) => fmt(v, 0) + ' rpm',
    }));
    this.gearMarkers = [
      {
        id: 'redline',
        value: redline,
        orientation: 'horizontal',
        label: 'Redline',
        color: '#d32f2f',
        editable: true,
        constraints: { min: SHIFT_RPM + 100, max: 20000, step: 50 },
        format: v => fmt(v, 0),
      },
      {
        id: 'shift',
        value: SHIFT_RPM,
        orientation: 'horizontal',
        label: 'Shift / gear start',
        color: '#90a4ae',
        format: v => fmt(v, 0),
      },
    ];
  }

  onGearPreview(e: CurveSeriesChange) {
    if (!e.seriesId.startsWith('gear-')) return;
    const tops = [...this.gearTops];
    tops[+e.seriesId.substring(5)] = e.points[1].x / MPS_TO_KMH;
    this.buildGears(tops);
  }

  onGearChange(e: CurveSeriesChange) {
    if (!e.seriesId.startsWith('gear-')) return;
    this.setValue(['gear_top_speeds', +e.seriesId.substring(5)], this.round(e.points[1].x / MPS_TO_KMH, 2));
  }

  // a gear can be added after the last one (the last slot stays 0) and removed from the end only
  get canAddGear(): boolean {
    return this.gearTops.length < GEAR_SLOTS - 1;
  }

  addGear() {
    const tops = this.gearTops;
    const last = tops[tops.length - 1] || 0;
    const prev = tops[tops.length - 2] || 0;
    this.setValue(['gear_top_speeds', tops.length], this.round(last + Math.max(5, last - prev), 2));
  }

  removeGear() {
    const n = this.gearTops.length;
    if (n > 1) this.setValue(['gear_top_speeds', n - 1], 0);
  }

  onGearTopInput(index: number, raw: string) {
    const v = parseFloat(raw);
    if (!isFinite(v) || v <= 0) return;
    this.setValue(['gear_top_speeds', index], this.round(v / MPS_TO_KMH, 2));
  }

  // ---------- handling ----------

  gripAt(style: Style, v: number): number {
    return (this.d[style]['grip'] || 0) * (1 + v * GRIP_PER_MPS);
  }

  private buildHandling() {
    const end = this.speedEnd;
    this.gripSeries = STYLES.map(style => ({
      id: style,
      label: STYLE_LABELS[style],
      color: STYLE_COLORS[style],
      points: [
        { x: 0, y: this.gripAt(style, 0) },
        { x: end * MPS_TO_KMH, y: this.gripAt(style, end) },
      ],
      editable: 'y' as const,
      lockedIndices: [1],
      y: { min: 0, step: 0.5 },
      pointLabels: ['grip, drag to change', ''],
      formatY: (v: number) => `${fmt(v, 1)} m/s²`,
    }));

    const d = this.d;
    const low = d['low_handling_yaw'] || 0;
    const high = d['hi_handling_yaw'] || 0;
    const importance = d['handling_importance'] || 0;
    const xEnd = Math.max(high, low) + 4;
    this.handlingAxis = { label: 'Yaw value', min: 0, max: xEnd, format: v => fmt(v, 0) };
    const drop = high > low ? importance : 0;
    // 0.68 to 1.2 at the high yaw in the shipped files, with room to drag either way
    this.factorAxis = {
      ...this.factorAxis,
      min: Math.min(0.5, 1 - drop - 0.1),
      max: Math.max(1.5, 1 - drop + 0.1),
    };
    this.handlingSeries = [
      {
        id: 'handling',
        label: 'Speed multiplier',
        color: '#00897b',
        points: [
          { x: 0, y: 1 },
          { x: low, y: 1 },
          { x: high, y: 1 - drop },
          { x: xEnd, y: 1 - drop },
        ],
        editable: 'xy',
        lockedIndices: [0, 3],
        x: { min: 0, max: xEnd, step: 1 },
        y: { min: 0, max: 2, step: 0.01 },
        // the low yaw end moves along 1 only
        constrain: (i, p) => (i === 1 ? { x: Math.min(p.x, high - 1), y: 1 } : { x: Math.max(p.x, low + 1), y: p.y }),
        pointLabels: ['', 'low_handling_yaw', 'hi_handling_yaw · 1 - handling_importance', ''],
        formatY: (v: number) => '× ' + fmt(v, 3),
      },
    ];
  }

  onGripChange(e: CurveSeriesChange) {
    const style = e.seriesId as Style;
    this.setValue([style, 'grip'], this.round(Math.max(0, e.points[0].y), 2));
  }

  onHandlingChange(e: CurveSeriesChange) {
    const entries: [(string | number)[], any][] = [];
    if (e.changed.includes(1)) entries.push([['low_handling_yaw'], Math.max(0, Math.round(e.points[1].x))]);
    if (e.changed.includes(2)) {
      entries.push([['hi_handling_yaw'], Math.max(1, Math.round(e.points[2].x))]);
      entries.push([['handling_importance'], this.round(1 - e.points[2].y, 3)]);
    }
    this.setValues(entries);
  }

  setLeverField(style: Style, name: string, value: number) {
    this.setValue([style, name], value);
  }

  // ---------- summary ----------

  private buildTiles() {
    const d = this.d;
    const tops = this.gearTops;
    const shift = d['ai_shift_duration'] || 0;
    const sim = this.runs.simulation!;
    const arcade = this.runs.arcade!;
    const time = (t: number | null) => (t === null ? 'never' : `${fmt(t, 1)} s`);
    this.tiles = [
      {
        id: 'redline',
        label: 'Redline',
        value: `${fmt(this.redline, 0)} rpm`,
        edit: { value: this.redline, step: 50, min: SHIFT_RPM + 100, unit: 'rpm' },
        sub: `from ${fmt(SHIFT_RPM, 0)} rpm in each gear`,
        hint: 'redline: the AI engine rpm at the top speed of each gear (sound and rev counter only)',
      },
      {
        id: 'top_gear',
        label: 'Top gear',
        value: `${fmt((tops[tops.length - 1] || 0) * MPS_TO_KMH, 0)} km/h`,
        edit: { value: this.round((tops[tops.length - 1] || 0) * MPS_TO_KMH, 1), step: 1, min: 1, unit: 'km/h' },
        sub: `${tops.length}-speed`,
        hint: 'Top speed of the last gear (gear_top_speeds). The car is as fast as its acceleration table drives it',
      },
      {
        id: 'ai_shift_duration',
        label: 'Shift',
        value: `${fmt(shift / STEPS, 2)} s`,
        edit: { value: shift, step: 1, min: 0, unit: 'steps' },
        sub: `${shift} steps, no drive`,
        hint: 'ai_shift_duration in AI steps (32 per second at the full step rate)',
      },
      {
        label: '0-100 km/h',
        value: time(sim.to100),
        sub: `arcade ${time(arcade.to100)}`,
        hint: 'Simulation / arcade, from the speed run in the Acceleration tab',
        tone: 'accent',
      },
      {
        label: 'Top speed',
        value: `${fmt(sim.topSpeed * MPS_TO_KMH, 0)} km/h`,
        sub: `arcade ${fmt(arcade.topSpeed * MPS_TO_KMH, 0)} km/h`,
        hint: 'Simulation / arcade: where the speed run stops, at the first table entry of 0 or the model top speed',
        tone: 'accent',
      },
      {
        label: 'Grip',
        value: `${fmt(d['simulation']['grip'] || 0, 1)} m/s²`,
        sub: `arcade ${fmt(d['arcade']['grip'] || 0, 1)} m/s²`,
        hint: 'grip of the simulation / arcade levers: the cap of the lateral correction at standstill',
      },
    ];
    if (this.model) {
      const [s, a] = this.model.tableScale;
      this.tiles.push({
        label: 'Model',
        value: this.model.name,
        sub: `table × ${fmt(s, 2)} / ${fmt(a, 2)}`,
        hint:
          `Model ${this.model.index} (by the file name): the loader scales the simulation / arcade table by these ` +
          `factors, and the AI drive stops above ${fmt(this.model.topSpeed * MPS_TO_KMH, 0)} km/h. The charts and ` +
          'the speed run use the scaled tables',
        tone: 'muted',
      });
    }
  }

  onTileChange(e: { id: string; value: number }) {
    if (e.id === 'top_gear') {
      const n = this.gearTops.length;
      if (n) this.setValue(['gear_top_speeds', n - 1], this.round(e.value / MPS_TO_KMH, 2));
    } else if (e.id === 'redline') {
      this.setValue(['redline'], Math.round(e.value));
    } else if (e.id === 'ai_shift_duration') {
      this.setValue(['ai_shift_duration'], Math.max(0, Math.round(e.value)));
    }
  }

  readonly fmt = fmt;
  readonly MPS_TO_KMH = MPS_TO_KMH;

  round(v: number, digits: number): number {
    const k = Math.pow(10, digits);
    return Math.round(v * k) / k;
  }
}
