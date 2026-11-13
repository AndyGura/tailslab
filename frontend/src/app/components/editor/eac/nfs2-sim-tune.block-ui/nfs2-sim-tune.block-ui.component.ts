import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
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
import { BlockSchema } from '../../types';
import { joinId } from '../../../../utils/join-id';
import { CarSpecEditorBase, fmt, MPS_TO_KMH } from '../player-car-physics.block-ui/car-specs';
import {
  acosDeg,
  cosDeg,
  crashSpeedFor,
  elasticityFor,
  flightGravityFactor,
  glueOrderProblems,
  glueSteps,
  jumpRateFromAcceleration,
  maxGlueBoost,
  reboundCurve,
  SIM_TICKS,
  SIM_TUNE_STYLE_COLORS,
  SIM_TUNE_STYLE_LABELS,
  SIM_TUNE_STYLES,
  SimTuneRecord,
  SimTuneStyle,
  smoothingResponse,
  smoothingStepsTo,
  STILL_TIMER_SPEEDUP,
  ticksToSeconds,
  wallCurve,
  wallStopAngle,
  wreckTimeline,
} from './nfs2-sim-tune';
import { MatTooltip } from '@angular/material/tooltip';
import { BlockActionsComponent } from '../../common/block-actions/block-actions.component';
import { MatTabGroup, MatTab, MatTabContent } from '@angular/material/tabs';
import { NgTemplateOutlet } from '@angular/common';
import { MatIcon } from '@angular/material/icon';
import { CompoundBlockUiComponent } from '../../library/compound.block-ui/compound.block-ui.component';

export type SimTuneField = Exclude<keyof SimTuneRecord, 'glue_logic'>;

type ParamSpec = {
  field: SimTuneField;
  label: string;
  step: number;
  integer?: boolean;
  unit?: string;
  derive?: (v: number, rec: SimTuneRecord) => string;
};

export type SimTuneParamRow = {
  field: SimTuneField;
  label: string;
  hint: string;
  step: number;
  integer: boolean;
  unit: string;
  cells: { style: SimTuneStyle; value: number; derived: string }[];
};

type SliderDef = { field: SimTuneField; label: string; spec: SliderSpec; derive: (v: number) => string };

export type SimTuneGlueRow = {
  index: number;
  cells: { style: SimTuneStyle; distance: number; multiplier: number; outOfOrder: boolean }[];
};

// landing speeds of the rebound chart, m/s
const LANDING_MAX = 30;
// impact speed of the wall chart, m/s
const WALL_SPEED = 50;
// slices behind the leader on the catch-up chart
const GLUE_END = 100;
const deg = (rad: number) => (rad * 180) / Math.PI;
const signed = (v: number, digits: number) => (v > 0 ? '+' : v < 0 ? '−' : '') + fmt(Math.abs(v), digits);

// parameter rows by tab, both styles side by side
const FLIGHT_PARAMS: ParamSpec[] = [
  {
    field: 'jump_roll_due_to_car_turn',
    label: 'Jump roll due to car turn',
    step: 0.0001,
    derive: v => `roll ${signed(-jumpRateFromAcceleration(10, v), 4)} rad/s at 10 m/s² sideways`,
  },
  {
    field: 'jump_pitch_due_to_acc_and_brake',
    label: 'Jump pitch due to acc and brake',
    step: 0.0001,
    derive: v => `pitch ${signed(jumpRateFromAcceleration(10, v), 4)} rad/s at 10 m/s² forward`,
  },
  {
    field: 'extra_flight_gravity',
    label: 'Extra flight gravity',
    step: 0.05,
    derive: v => `falls with ${fmt(flightGravityFactor(v), 2)} × the gravity`,
  },
  {
    field: 'bounce_shock_absorb_speed',
    label: 'Bounce shock absorb speed',
    step: 0.1,
    unit: 'm/s',
    derive: v => `${fmt(v * MPS_TO_KMH, 1)} km/h lost before the rebound`,
  },
  {
    field: 'ground_max_speed_change',
    label: 'Ground max speed change',
    step: 0.5,
    unit: 'm/s',
    derive: () => 'not read by the game',
  },
];

const CRASH_PARAMS: ParamSpec[] = [
  {
    field: 'telepole_launch_value',
    label: 'Telepole launch value (crash threshold)',
    step: 1,
    derive: v => `a wall hit at ${fmt(crashSpeedFor(v), 1)} m/s (${fmt(crashSpeedFor(v) * MPS_TO_KMH, 0)} km/h)`,
  },
  {
    field: 'bad_collision_reset_ticks',
    label: 'Ticks before reset in a bad collision',
    step: 1,
    integer: true,
    unit: 'ticks',
    derive: v => `${fmt(ticksToSeconds(v), 2)} s, ${fmt(ticksToSeconds(v) / STILL_TIMER_SPEEDUP, 2)} s still`,
  },
  {
    field: 'full_gas_reset_tick_advance',
    label: 'Reset advance with full gas',
    step: 1,
    integer: true,
    unit: 'ticks',
    derive: (v, r) =>
      `full gas resets ${fmt(wreckTimeline(r.bad_collision_reset_ticks, v).gasSeconds, 2)} s after the crash`,
  },
  {
    field: 'invincibility_ticks_after_reset',
    label: 'Invincibility after reset',
    step: 1,
    integer: true,
    unit: 'ticks',
    derive: v => (v > 0 ? `${fmt(ticksToSeconds(v), 2)} s without car contacts` : 'none'),
  },
  {
    field: 'reset_forward_slices',
    label: 'Slices forward on reset',
    step: 1,
    integer: true,
    unit: 'slices',
    derive: v => (v ? `${v} slices past the crash slice` : 'at the crash slice'),
  },
  {
    field: 'collision_reset_altitude',
    label: 'Reset altitude',
    step: 0.1,
    unit: 'm',
    derive: v => `${fmt(v, 2)} m above the road (half under a ceiling)`,
  },
  {
    field: 'collision_reset_launch_speed',
    label: 'Reset launch speed',
    step: 1,
    unit: 'm/s',
    derive: v => `${fmt(v * MPS_TO_KMH, 0)} km/h along the car`,
  },
  {
    field: 'stop_tumbling_speed',
    label: 'Stop tumbling speed',
    step: 0.1,
    unit: 'rad/s',
    derive: v => `${fmt(deg(v), 0)} °/s of |roll| + |pitch|`,
  },
];

const WALL_PARAMS: ParamSpec[] = [
  {
    field: 'barrier_speed_loss_multiplier',
    label: 'Barrier speed loss multiplier',
    step: 0.5,
    derive: v => `nothing kept from ${fmt(wallStopAngle(WALL_SPEED, v), 1)}° on`,
  },
  {
    field: 'deflection_angular_range',
    label: 'Deflection angular range',
    step: 0.01,
    derive: v => `${fmt(acosDeg(v), 1)}° (acos)`,
  },
];

const FRACTION: SliderSpec = { min: 0, max: 1, step: 0.005 };
const pct = (v: number) => `${fmt(v * 100, 1)} %`;
const FLIGHT_SLIDERS: SliderDef[] = [
  {
    field: 'initial_jump_roll_attenuate',
    label: 'Initial jump roll attenuate',
    spec: FRACTION,
    derive: v => `keeps ${pct(v)} of the roll rate`,
  },
  {
    field: 'initial_jump_road_pitch_damp',
    label: 'Initial jump road pitch damp',
    spec: FRACTION,
    derive: v => `keeps ${pct(v)} of the pitch rate`,
  },
  {
    field: 'bounce_threshold',
    label: 'Bounce threshold',
    spec: FRACTION,
    derive: v => `bounces up to ${fmt(acosDeg(v), 1)}° of tilt`,
  },
  {
    field: 'bounce_elasticity',
    label: 'Bounce elasticity',
    spec: FRACTION,
    derive: v => `${pct(v)} of the speed above the absorb speed`,
  },
  {
    field: 'ground_rise_smoothing',
    label: 'Ground rise smoothing',
    spec: FRACTION,
    derive: v => `90 % after ${stepsText(smoothingStepsTo(v))}`,
  },
  {
    field: 'ground_fall_smoothing',
    label: 'Ground fall smoothing',
    spec: FRACTION,
    derive: v => `90 % after ${stepsText(smoothingStepsTo(v))}`,
  },
];

const stepsText = (n: number | null) => (n === null ? 'never' : `${n} steps (${fmt(n / SIM_TICKS, 2)} s)`);

// Rich editor of NFS2 SE SIMTUNE.DAT (Nfs2SimTune): flight, landing, ground, crash reset, wall and catch-up tuning of
// both game styles, side by side (simulation purple, arcade orange, as in the AI editor). The derived curves follow
// the field descriptions of `Nfs2SimTuneRecord` / `Nfs2SimTuneGlueLogic` (nfs2sen.exe addresses there)
@Component({
  selector: 'app-nfs2-sim-tune-block-ui',
  templateUrl: './nfs2-sim-tune.block-ui.component.html',
  styleUrls: [
    '../player-car-physics.block-ui/player-car-physics.block-ui.component.scss',
    './nfs2-sim-tune.block-ui.component.scss',
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    MatTooltip,
    BlockActionsComponent,
    StatTilesComponent,
    MatTabGroup,
    MatTab,
    MatTabContent,
    CurveEditorComponent,
    SliderFieldComponent,
    NgTemplateOutlet,
    MatIcon,
    CompoundBlockUiComponent,
  ],
})
export class Nfs2SimTuneBlockUiComponent extends CarSpecEditorBase {
  override get resourceSchema(): BlockSchema | undefined {
    return super.resourceSchema;
  }

  @Input()
  override set resourceSchema(value: BlockSchema | undefined) {
    super.resourceSchema = value;
    const recordFields = (value?.fields || []).find((f: any) => f.name === 'simulation')?.schema?.fields || [];
    this.recordDescriptions = {};
    for (const f of recordFields) this.recordDescriptions[f.name] = f.description || '';
    const glue = recordFields.find((f: any) => f.name === 'glue_logic')?.schema;
    this.glueDescriptions = {};
    for (const f of glue?.child_schema?.fields || []) this.glueDescriptions[f.name] = f.description || '';
    if (this.resourceData) this.refresh();
  }

  readonly styles = SIM_TUNE_STYLES;
  readonly styleLabels = SIM_TUNE_STYLE_LABELS;
  readonly styleColors = SIM_TUNE_STYLE_COLORS;
  readonly flightSliders = FLIGHT_SLIDERS;

  recordDescriptions: { [field: string]: string } = {};
  glueDescriptions: { [field: string]: string } = {};

  selectedTab = 0;
  tiles: StatTile[] = [];

  // flight & landing
  reboundSeries: CurveSeries[] = [];
  reboundMarkers: CurveMarker[] = [];
  smoothingSeries: CurveSeries[] = [];
  flightRows: SimTuneParamRow[] = [];
  readonly landingAxis: CurveAxis = { label: 'Landing speed (m/s)', min: 0, max: LANDING_MAX };
  readonly reboundAxis: CurveAxis = { label: 'Rebound speed (m/s)', min: 0 };
  readonly smoothTimeAxis: CurveAxis = { label: 'Time (s)', min: 0, max: 1, format: v => fmt(v, 2) };
  readonly smoothAxis: CurveAxis = { label: 'Part of the ground speed change', min: 0, max: 1, format: v => fmt(v, 2) };
  readonly describeLanding = (v: number) => `${fmt(v, 1)} m/s landing · ${fmt(v * MPS_TO_KMH, 0)} km/h`;
  readonly describeSmoothTime = (s: number) => `step ${fmt(s * SIM_TICKS, 0)} · ${fmt(s, 2)} s`;

  // crash & reset
  wreckSeries: CurveSeries[] = [];
  wreckMarkers: CurveMarker[] = [];
  crashRows: SimTuneParamRow[] = [];
  readonly wreckTimeAxis: CurveAxis = { label: 'Time after the crash (s)', min: 0, format: v => fmt(v, 1) };
  readonly ticksAxis: CurveAxis = { label: 'Wreck timer (ticks)', min: 0, format: v => fmt(v, 0) };
  readonly describeWreckTime = (s: number) => `${fmt(s, 2)} s · step ${fmt(s * SIM_TICKS, 0)}`;

  // walls
  wallSeries: CurveSeries[] = [];
  wallMarkers: CurveMarker[] = [];
  wallRows: SimTuneParamRow[] = [];
  readonly angleAxis: CurveAxis = { label: 'Impact angle to the wall (°)', min: 0, max: 90, format: v => fmt(v, 0) };
  readonly wallSpeedAxis: CurveAxis = { label: 'Forward speed kept (m/s)', min: 0, max: WALL_SPEED };
  readonly describeAngle = (a: number) => `${fmt(a, 1)}° to the wall`;
  readonly wallSpeed = WALL_SPEED;

  // catch-up
  glueSeries: CurveSeries[] = [];
  glueRows: SimTuneGlueRow[] = [];
  glueProblems: { [s in SimTuneStyle]?: number[] } = {};
  readonly behindAxis: CurveAxis = { label: 'Slices behind the leader', min: 0, format: v => fmt(v, 0) };
  readonly boostAxis: CurveAxis = { label: 'Speed boost multiplier', min: 0.9, format: v => fmt(v, 2) };
  readonly describeBehind = (v: number) => `${fmt(v, 0)} slices behind the leader`;

  protected refresh(): void {
    const d = this.d;
    if (!d || !d['simulation'] || !d['arcade']) return;
    this.buildFlight();
    this.buildCrash();
    this.buildWalls();
    this.buildGlue();
    this.buildTiles();
  }

  rec(style: SimTuneStyle): SimTuneRecord {
    return this.d[style] as SimTuneRecord;
  }

  styleId(style: SimTuneStyle): string {
    return joinId(this.resourceId || '', style);
  }

  private rows(specs: ParamSpec[]): SimTuneParamRow[] {
    return specs.map(spec => ({
      field: spec.field,
      label: spec.label,
      hint: this.recordDescriptions[spec.field] || '',
      step: spec.step,
      integer: !!spec.integer,
      unit: spec.unit || '',
      cells: SIM_TUNE_STYLES.map(style => {
        const rec = this.rec(style);
        const value = rec[spec.field] ?? 0;
        return { style, value: this.round(value, 6), derived: spec.derive ? spec.derive(value, rec) : '' };
      }),
    }));
  }

  // ---------- flight & landing ----------

  private buildFlight() {
    this.reboundSeries = SIM_TUNE_STYLES.map(style => {
      const r = this.rec(style);
      const absorb = r.bounce_shock_absorb_speed;
      return {
        id: 'rebound-' + style,
        label: SIM_TUNE_STYLE_LABELS[style],
        color: SIM_TUNE_STYLE_COLORS[style],
        points: reboundCurve(absorb, r.bounce_elasticity, LANDING_MAX),
        editable: absorb < LANDING_MAX ? ('y' as const) : ('none' as const),
        lockedIndices: [0, 1],
        y: { min: 0, max: LANDING_MAX, step: 0.05 },
        // one point moves, no falloff on its neighbours
        constrain: (_: number, p: CurvePoint) => p,
        pointLabels: ['', 'bounce_shock_absorb_speed', 'drag to change bounce_elasticity'],
        formatY: (v: number) => `${fmt(v, 2)} m/s`,
      };
    });
    this.reboundMarkers = SIM_TUNE_STYLES.map(style => ({
      id: 'absorb-' + style,
      value: this.rec(style).bounce_shock_absorb_speed,
      label: `${SIM_TUNE_STYLE_LABELS[style]} absorb`,
      color: SIM_TUNE_STYLE_COLORS[style],
      editable: true,
      constraints: { min: 0, max: LANDING_MAX, step: 0.05 },
      format: v => `${fmt(v, 2)} m/s`,
    }));

    this.smoothingSeries = [];
    for (const style of SIM_TUNE_STYLES) {
      for (const kind of ['rise', 'fall'] as const) {
        const points = smoothingResponse(this.rec(style)[`ground_${kind}_smoothing`]);
        this.smoothingSeries.push({
          id: `${kind}-${style}`,
          label: `${SIM_TUNE_STYLE_LABELS[style]} ${kind}`,
          color: SIM_TUNE_STYLE_COLORS[style],
          dashed: kind === 'fall',
          points,
          editable: 'y',
          // the value after the first step is the factor itself
          lockedIndices: points.map((_, i) => i).filter(i => i !== 1),
          y: { min: 0, max: 1, step: 0.005 },
          constrain: (_: number, p: CurvePoint) => ({ x: p.x, y: Math.max(0, Math.min(1, p.y)) }),
          pointLabels: ['', `ground_${kind}_smoothing: drag to change`],
          formatY: (v: number) => pct(v),
        });
      }
    }
    this.flightRows = this.rows(FLIGHT_PARAMS);
  }

  onReboundChange(e: CurveSeriesChange) {
    const style = e.seriesId.replace(/^rebound-/, '');
    if (!this.isStyle(style) || !e.changed.includes(2)) return;
    const p = e.points[2];
    const elasticity = elasticityFor(p.x, p.y, this.rec(style).bounce_shock_absorb_speed);
    this.setValue([style, 'bounce_elasticity'], this.round(elasticity, 4));
  }

  onSmoothingChange(e: CurveSeriesChange) {
    const [kind, style] = e.seriesId.split('-');
    if (!this.isStyle(style) || (kind !== 'rise' && kind !== 'fall') || !e.changed.includes(1)) return;
    this.setValue([style, `ground_${kind}_smoothing`], this.round(Math.max(0, Math.min(1, e.points[1].y)), 4));
  }

  sliderDerived(style: SimTuneStyle, s: SliderDef): string {
    return s.derive(this.rec(style)[s.field]);
  }

  // ---------- crash & reset ----------

  private buildCrash() {
    this.wreckSeries = [];
    this.wreckMarkers = [];
    for (const style of SIM_TUNE_STYLES) {
      const r = this.rec(style);
      const t = wreckTimeline(r.bad_collision_reset_ticks, r.full_gas_reset_tick_advance);
      this.wreckSeries.push({
        id: 'wreck-' + style,
        label: SIM_TUNE_STYLE_LABELS[style],
        color: SIM_TUNE_STYLE_COLORS[style],
        points: t.normal,
        editable: 'y',
        lockedIndices: [1],
        y: { min: 0, max: 10000, step: 1 },
        constrain: (_: number, p: CurvePoint) => p,
        pointLabels: ['bad_collision_reset_ticks: drag to change', 'reset'],
        formatY: (v: number) => `${fmt(v, 0)} ticks`,
      });
      this.wreckSeries.push({
        id: 'still-' + style,
        label: `${SIM_TUNE_STYLE_LABELS[style]}, car still`,
        color: SIM_TUNE_STYLE_COLORS[style],
        dashed: true,
        points: t.still,
        formatY: (v: number) => `${fmt(v, 0)} ticks`,
      });
      this.wreckMarkers.push({
        id: 'gas-' + style,
        value: r.full_gas_reset_tick_advance,
        orientation: 'horizontal',
        label: `${SIM_TUNE_STYLE_LABELS[style]}: full gas resets below`,
        color: SIM_TUNE_STYLE_COLORS[style],
        editable: true,
        constraints: { min: 0, step: 1 },
        format: v => `${fmt(v, 0)} ticks`,
      });
    }
    this.crashRows = this.rows(CRASH_PARAMS);
  }

  onWreckChange(e: CurveSeriesChange) {
    const style = e.seriesId.replace(/^wreck-/, '');
    if (!this.isStyle(style) || !e.changed.includes(0)) return;
    this.setValue([style, 'bad_collision_reset_ticks'], Math.max(0, Math.round(e.points[0].y)));
  }

  // ---------- walls ----------

  private buildWalls() {
    this.wallSeries = [
      {
        id: 'no-loss',
        label: 'Part along the wall',
        color: '#90a4ae',
        dashed: true,
        points: wallCurve(WALL_SPEED, 0, 2),
        formatY: (v: number) => `${fmt(v, 1)} m/s`,
      },
      ...SIM_TUNE_STYLES.map(style => ({
        id: 'wall-' + style,
        label: SIM_TUNE_STYLE_LABELS[style],
        color: SIM_TUNE_STYLE_COLORS[style],
        points: wallCurve(WALL_SPEED, this.rec(style).barrier_speed_loss_multiplier),
        formatY: (v: number) => `${fmt(v, 1)} m/s · ${fmt((v / WALL_SPEED) * 100, 0)} %`,
      })),
    ];
    this.wallMarkers = SIM_TUNE_STYLES.map(style => ({
      id: 'deflect-' + style,
      value: acosDeg(this.rec(style).deflection_angular_range),
      label: `${SIM_TUNE_STYLE_LABELS[style]} deflection`,
      color: SIM_TUNE_STYLE_COLORS[style],
      editable: true,
      constraints: { min: 0, max: 90, step: 0.5 },
      format: v => `${fmt(v, 1)}°`,
    }));
    this.wallRows = this.rows(WALL_PARAMS);
  }

  onMarker(e: CurveMarkerChange) {
    const [kind, style] = e.markerId.split('-');
    if (!this.isStyle(style)) return;
    if (kind === 'absorb') {
      this.setValue([style, 'bounce_shock_absorb_speed'], this.round(Math.max(0, e.value), 4));
    } else if (kind === 'gas') {
      this.setValue([style, 'full_gas_reset_tick_advance'], Math.max(0, Math.round(e.value)));
    } else if (kind === 'deflect') {
      this.setValue([style, 'deflection_angular_range'], this.round(cosDeg(e.value), 4));
    }
  }

  // ---------- catch-up ----------

  private buildGlue() {
    this.glueProblems = {};
    const farthest = Math.max(
      0,
      ...SIM_TUNE_STYLES.flatMap(s => (this.rec(s).glue_logic || []).map(p => p.slice_distance)),
    );
    const end = Math.max(GLUE_END, Math.ceil((farthest * 1.25) / 10) * 10);
    this.glueSeries = SIM_TUNE_STYLES.map(style => {
      const glue = this.rec(style).glue_logic || [];
      this.glueProblems[style] = glueOrderProblems(glue);
      const points = glueSteps(glue, end);
      return {
        id: 'glue-' + style,
        label: SIM_TUNE_STYLE_LABELS[style],
        color: SIM_TUNE_STYLE_COLORS[style],
        style: 'step' as const,
        dashed: style === 'arcade',
        points,
        editable: 'xy' as const,
        lockedIndices: [0, points.length - 1],
        x: { min: 0, max: end - 1, step: 1 },
        y: { min: 0.5, max: 3, step: 0.005 },
        // a pair stays between its neighbours: the distances must increase
        constrain: (i: number, p: CurvePoint) => ({
          x: Math.max(points[i - 1].x + (i > 1 ? 1 : 0), Math.min(points[i + 1].x - 1, Math.round(p.x))),
          y: p.y,
        }),
        pointLabels: ['', ...glue.map((_, k) => `pair ${k + 1}`), ''],
        formatY: (v: number) => '× ' + fmt(v, 3),
      };
    });
    const count = Math.max(...SIM_TUNE_STYLES.map(s => (this.rec(s).glue_logic || []).length));
    this.glueRows = Array.from({ length: count }, (_, index) => ({
      index,
      cells: SIM_TUNE_STYLES.map(style => {
        const pair = this.rec(style).glue_logic?.[index];
        return {
          style,
          distance: pair?.slice_distance ?? 0,
          multiplier: this.round(pair?.speed_boost_multiplier ?? 1, 6),
          outOfOrder: !!this.glueProblems[style]?.includes(index),
        };
      }),
    }));
  }

  onGlueChange(e: CurveSeriesChange) {
    const style = e.seriesId.replace(/^glue-/, '');
    if (!this.isStyle(style)) return;
    const glue = this.rec(style).glue_logic || [];
    const entries: [(string | number)[], any][] = [];
    for (const i of e.changed) {
      const k = i - 1;
      if (k < 0 || k >= glue.length) continue;
      entries.push([[style, 'glue_logic', k, 'slice_distance'], Math.max(0, Math.round(e.points[i].x))]);
      entries.push([[style, 'glue_logic', k, 'speed_boost_multiplier'], this.round(e.points[i].y, 4)]);
    }
    this.setValues(entries);
  }

  get glueOutOfOrder(): boolean {
    return SIM_TUNE_STYLES.some(s => !!this.glueProblems[s]?.length);
  }

  // ---------- summary ----------

  private buildTiles() {
    const sim = this.rec('simulation');
    const arc = this.rec('arcade');
    const s = (v: number) => `${fmt(v, 2)} s`;
    this.tiles = [
      {
        label: 'Wreck timer',
        value: s(ticksToSeconds(sim.bad_collision_reset_ticks)),
        sub: `arcade ${s(ticksToSeconds(arc.bad_collision_reset_ticks))}`,
        hint:
          'bad_collision_reset_ticks of the simulation / arcade style at 32 ticks per second: the time from a bad ' +
          'crash to the reset (8 times faster with the car still; AI racers in arcade style wait 3 times longer)',
      },
      {
        label: 'Invincibility',
        value: s(ticksToSeconds(sim.invincibility_ticks_after_reset)),
        sub: `arcade ${s(ticksToSeconds(arc.invincibility_ticks_after_reset))}`,
        hint: 'invincibility_ticks_after_reset of the simulation / arcade style: no car contacts this long after a reset',
      },
      {
        label: 'Flight gravity',
        value: `× ${fmt(flightGravityFactor(sim.extra_flight_gravity), 2)}`,
        sub: `arcade × ${fmt(flightGravityFactor(arc.extra_flight_gravity), 2)}`,
        hint: 'In the air the car falls with 1 + extra_flight_gravity times the gravity (simulation / arcade)',
        tone: 'accent',
      },
      {
        label: 'Bounces up to',
        value: `${fmt(acosDeg(sim.bounce_threshold), 1)}°`,
        sub: `arcade ${fmt(acosDeg(arc.bounce_threshold), 1)}°`,
        hint:
          'acos(bounce_threshold): the tilt of the car to the road up to which a landing after at least 10 ticks in ' +
          'the air bounces on the wheels; more tilted, it lands through the corner contact (simulation / arcade)',
      },
      {
        label: 'Crash threshold',
        value: `${fmt(crashSpeedFor(sim.telepole_launch_value) * MPS_TO_KMH, 0)} km/h`,
        sub: `arcade ${fmt(crashSpeedFor(arc.telepole_launch_value) * MPS_TO_KMH, 0)} km/h`,
        hint:
          'telepole_launch_value / 6: the speed into a wall above which a hit counts as a crash (the crash strength ' +
          'is 6 times the speed into the wall; car hits and landings add their impulses)',
      },
      {
        label: 'Deflection range',
        value: `${fmt(acosDeg(sim.deflection_angular_range), 1)}°`,
        sub: `arcade ${fmt(acosDeg(arc.deflection_angular_range), 1)}°`,
        hint:
          'acos(deflection_angular_range): cars that are not human hitting a slice wall less than this angle off ' +
          "the wall's direction turn toward it, else they are steered along it (simulation / arcade)",
      },
      {
        label: 'Max catch-up',
        value: `× ${fmt(maxGlueBoost(sim.glue_logic || []), 3)}`,
        sub: `arcade × ${fmt(maxGlueBoost(arc.glue_logic || []), 3)}`,
        hint:
          'The largest speed boost multiplier of the glue logic: human cars far behind the leader, with the ' +
          'multiplayer catch-up only (simulation / arcade)',
        tone: 'muted',
      },
    ];
  }

  // ---------- inputs ----------

  onParamInput(style: SimTuneStyle, field: SimTuneField, raw: string, integer: boolean) {
    this.onNumberInput([style, field], raw, integer);
  }

  onSlider(style: SimTuneStyle, field: SimTuneField, value: number) {
    this.setValue([style, field], value);
  }

  onGlueInput(style: SimTuneStyle, index: number, field: 'slice_distance' | 'speed_boost_multiplier', raw: string) {
    this.onNumberInput([style, 'glue_logic', index, field], raw, field === 'slice_distance');
  }

  private isStyle(style: string | undefined): style is SimTuneStyle {
    return (SIM_TUNE_STYLES as readonly string[]).includes(style || '');
  }

  readonly fmt = fmt;

  round(v: number, digits: number): number {
    const k = Math.pow(10, digits);
    return Math.round(v * k) / k;
  }
}
