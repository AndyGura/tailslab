import { ChangeDetectionStrategy, Component } from '@angular/core';
import {
  CurveAxis,
  CurveMarker,
  CurveMarkerChange,
  CurveSeries,
  CurveSeriesChange,
  CurveEditorComponent,
} from '../../common/curve-editor/curve-editor.component';
import { StatTile, StatTilesComponent } from '../../common/stat-tiles/stat-tiles.component';
import { SliderSpec, SliderFieldComponent } from '../../common/slider-field/slider-field.component';
import { CarSpecEditorBase, fmt, GEAR_COLORS, MPS_TO_KMH } from '../player-car-physics.block-ui/car-specs';
import {
  aeroDrag,
  bodyLift,
  driveForce,
  driveLayout,
  ENGINE_INERTIA,
  frontalArea,
  frontDownforce,
  KW_TO_HP,
  Nfs6Car,
  nfs6Car,
  powerKw,
  rearDownforce,
  resistance,
  rpmPerMps,
  shiftSpeed,
  steeringLimit,
  steeringLockDeg,
  stepsAcross,
  stepsToFullLock,
  TIRE_TYPES,
  tireRadius,
  topSpeed,
  torqueAt,
  TORQUE_ENTRIES,
  TORQUE_STEP_RPM,
} from './nfs6-car-specs';
import { MatTooltip } from '@angular/material/tooltip';
import { BlockActionsComponent } from '../../common/block-actions/block-actions.component';
import { IniFileBlockUiComponent } from '../../common/ini-file.block-ui/ini-file.block-ui.component';
import { MatTabGroup, MatTab, MatTabContent } from '@angular/material/tabs';
import { NgTemplateOutlet } from '@angular/common';
import { MatCheckbox } from '@angular/material/checkbox';
import { FormsModule } from '@angular/forms';

export type Nfs6GearRow = {
  index: number;
  name: string;
  color: string;
  ratio: number | null;
  efficiency: number | null;
  rpmPerMps: number;
  redlineKmh: number;
  shiftKmh: number | null;
};

export type Nfs6TireRow = {
  section: string;
  axle: string;
  typeCode: number | null;
  width: number | null;
  aspect: number | null;
  diameter: number | null;
  radius: number;
  size: string;
};

const gearName = (i: number) => (i === 0 ? 'R' : i === 1 ? 'N' : String(i - 1));

// Rich editor of NFS Hot Pursuit 2 PC car physics: car.ini, car_hp.ini, car_cop.ini, carracer.ini (Nfs6CarIni and its
// subclasses, resources/eac/nfs6_car_specs.py). The derived numbers follow NFSHP2.exe as nfs6-car-specs.ts ports it
@Component({
  selector: 'app-nfs6-car-ini-block-ui',
  templateUrl: './nfs6-car-ini.block-ui.component.html',
  styleUrls: ['../player-car-physics.block-ui/player-car-physics.block-ui.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    MatTooltip,
    BlockActionsComponent,
    SliderFieldComponent,
    IniFileBlockUiComponent,
    StatTilesComponent,
    MatTabGroup,
    MatTab,
    MatTabContent,
    CurveEditorComponent,
    NgTemplateOutlet,
    MatCheckbox,
    FormsModule,
  ],
})
export class Nfs6CarIniBlockUiComponent extends CarSpecEditorBase {
  readonly tireTypes = TIRE_TYPES;
  readonly fmt = fmt;
  readonly steeringLockDeg = steeringLockDeg;

  // bounded factors as sliders: [section, key, spec]
  readonly bodySliders: [string, string, SliderSpec][] = [
    ['basic', 'FrontGripBias', { min: 0.3, max: 0.7, step: 0.005, scale: 100, unit: '% front' }],
    ['basic', 'YawInertiaFactor', { min: 0.3, max: 2, step: 0.05, unit: '×' }],
    ['basic', 'RearSlideFactor', { min: 0, max: 8, step: 0.05 }],
    ['basic', 'FrontAntiRoll', { min: 0, max: 1, step: 0.01 }],
    ['basic', 'RearAntiRoll', { min: 0, max: 1, step: 0.01 }],
  ];
  readonly driveSliders: [string, string, SliderSpec][] = [
    ['basic', 'FrontDriveRatio', { min: 0, max: 1, step: 0.01, scale: 100, unit: '% front' }],
    ['engineblock', 'FlyWheelInertiaFactor', { min: 0.25, max: 3, step: 0.05, unit: '×' }],
    ['transmission', 'GearShiftPointCoefficient', { min: 0.75, max: 1.2, step: 0.01, unit: '×' }],
  ];
  readonly steeringSliders: [string, string, SliderSpec][] = [
    ['basic', 'DampingLimit', { min: 0, max: 1, step: 0.01, scale: 100, unit: '% of lock' }],
  ];

  selectedTab = 0;
  automatic = true;
  car?: Nfs6Car;
  tiles: StatTile[] = [];

  torqueSeries: CurveSeries[] = [];
  torqueMarkers: CurveMarker[] = [];
  readonly rpmAxis: CurveAxis = { label: 'Engine speed (rpm)', min: 0, format: v => fmt(v, 0) };
  readonly torqueAxis: CurveAxis = { label: 'Torque (N·m)', min: 0 };
  readonly powerAxis: CurveAxis = { label: 'Power (hp)', min: 0 };
  readonly describeRpm = (rpm: number) => `${fmt(rpm, 0)} rpm · entry ${fmt(rpm / TORQUE_STEP_RPM, 2)}`;

  gears: Nfs6GearRow[] = [];
  gearSeries: CurveSeries[] = [];
  forceSeries: CurveSeries[] = [];
  forceMarkers: CurveMarker[] = [];
  readonly speedAxis: CurveAxis = { label: 'Speed (km/h)', min: 0, format: v => fmt(v, 0) };
  readonly gearRpmAxis: CurveAxis = { label: 'Engine speed (rpm)', min: 0, format: v => fmt(v, 0) };
  readonly forceAxis: CurveAxis = { label: 'Force (N)', min: 0, format: v => fmt(v, 0) };
  readonly describeSpeed = (kmh: number) => `${fmt(kmh, 1)} km/h · ${fmt(kmh / MPS_TO_KMH, 1)} m/s`;

  tires: Nfs6TireRow[] = [];
  aeroSeries: CurveSeries[] = [];
  steeringSeries: CurveSeries[] = [];
  steeringMarkers: CurveMarker[] = [];
  readonly shareAxis: CurveAxis = { label: 'Steering available (% of full lock)', min: 0, max: 100 };

  override get d(): any {
    return this.resourceData || {};
  }

  protected refresh() {
    const car = nfs6Car(this.d, this.automatic);
    this.car = car;
    this.refreshTiles(car);
    this.refreshEngine(car);
    this.refreshGears(car);
    this.refreshTires();
    this.refreshAero(car);
    this.refreshSteering(car);
  }

  private refreshTiles(car: Nfs6Car) {
    let peakT = 0;
    let peakTRpm = 0;
    let peakP = 0;
    let peakPRpm = 0;
    for (let rpm = Math.max(car.minRpm, 0); rpm <= car.redLine; rpm += 50) {
      const t = torqueAt(car.torque, rpm, car.redLine);
      const p = powerKw(t, rpm);
      if (t > peakT) [peakT, peakTRpm] = [t, rpm];
      if (p > peakP) [peakP, peakPRpm] = [p, rpm];
    }
    const top = topSpeed(car);
    const layout = driveLayout(this.d.basic?.driveWheels, this.d.basic?.FrontDriveRatio ?? 0);
    const gearsForward = Math.max(car.gears - 2, 0);
    this.tiles = [
      {
        label: 'Mass',
        value: `${fmt(car.mass, 0)} kg`,
        sub: `Mass ${fmt(this.d.basic?.Mass ?? 0, 0)} + 40 (brakes, tyres)`,
        hint: 'CarIni_Load 0x422bd0 adds 8 kg per brake section and 12 kg per tyre section',
      },
      {
        label: 'Peak power',
        value: `${fmt(peakP * KW_TO_HP, 0)} hp`,
        sub: `${fmt(peakP, 0)} kW at ${fmt(peakPRpm, 0)} rpm`,
      },
      { label: 'Peak torque', value: `${fmt(peakT, 0)} N·m`, sub: `at ${fmt(peakTRpm, 0)} rpm` },
      {
        label: 'Top speed',
        value: `${fmt(top * MPS_TO_KMH, 0)} km/h`,
        sub: car.speedGovernor > 0 ? `governor ${fmt(car.speedGovernor * MPS_TO_KMH, 0)} km/h` : 'drive = drag',
        hint: 'Highest speed where a forward gear drives harder than the air drag and rolling resistance of the gearbox model (0x415780), capped by SpeedGovernor',
      },
      {
        label: 'Weight',
        value: `${fmt(car.frontGripBias * 100, 1)} % front`,
        sub: `CG ${fmt((1 - car.frontGripBias) * car.wheelBase, 2)} m behind the front axle`,
      },
      { label: 'Drive', value: layout.name, sub: `${gearsForward} gears · ${car.automatic ? 'automatic' : 'manual'}` },
      {
        label: 'Steering lock',
        value: `${fmt(steeringLockDeg(car), 1)}°`,
        sub: `${stepsToFullLock(car)} steps to full lock`,
      },
      {
        label: 'Drag area',
        value: `${fmt(car.dragWithTires * frontalArea(car), 3)} m²`,
        sub: `Cd ${fmt(car.dragWithTires, 3)} × ${fmt(frontalArea(car), 2)} m²`,
      },
      {
        label: 'Engine inertia',
        value: `${fmt(ENGINE_INERTIA * (this.d.engineblock?.FlyWheelInertiaFactor ?? 1), 3)} kg·m²`,
      },
    ];
  }

  private refreshEngine(car: Nfs6Car) {
    const raw: (number | null)[] = this.d.engineblock?.torqueCurve || [];
    const points = [];
    for (let i = 0; i < TORQUE_ENTRIES; i++) points.push({ x: i * TORQUE_STEP_RPM, y: raw[i] ?? 0 });
    const game = car.torque.map((y, i) => ({ x: i * TORQUE_STEP_RPM, y }));
    const power = [];
    for (let rpm = 0; rpm <= Math.max(car.redLine, 1000); rpm += 100) {
      power.push({ x: rpm, y: powerKw(torqueAt(car.torque, rpm, car.redLine), rpm) * KW_TO_HP });
    }
    this.torqueSeries = [
      {
        id: 'torque',
        label: 'torqueCurve (file)',
        color: '#3f51b5',
        points,
        editable: 'y',
        y: { min: 0 },
        pointLabels: points.map((_, i) => `torqueCurve_${i}`),
      },
      { id: 'game', label: 'As the game keeps it', color: '#9e9e9e', points: game, dashed: true },
      { id: 'power', label: 'Power', color: '#e91e63', points: power, axis: 'right' },
    ];
    const markers: CurveMarker[] = [
      { id: 'MinRPM', value: car.minRpm, label: 'MinRPM', color: '#009688', editable: true, constraints: { min: 0 } },
      {
        id: 'RedLine',
        value: car.redLine,
        label: 'RedLine',
        color: '#f44336',
        editable: true,
        constraints: { min: 0 },
      },
    ];
    const warning = this.d.engineblock?.WarningLine;
    markers.push({
      id: 'WarningLine',
      value: warning ?? Math.trunc((car.redLine * 7) / 8),
      label: warning === null || warning === undefined ? 'WarningLine (default)' : 'WarningLine',
      color: '#ff9800',
      editable: true,
      constraints: { min: 0 },
    });
    this.torqueMarkers = markers;
  }

  private refreshGears(car: Nfs6Car) {
    const ratios: (number | null)[] = this.d.transmission?.GearRatios || [];
    const effs: (number | null)[] = this.d.transmission?.GearEfficiency || [];
    const rows: Nfs6GearRow[] = [];
    for (let i = 0; i < 8; i++) {
      const per = rpmPerMps(car, i);
      const shift = shiftSpeed(car, i);
      rows.push({
        index: i,
        name: gearName(i),
        color: GEAR_COLORS[i % GEAR_COLORS.length],
        ratio: ratios[i] ?? null,
        efficiency: effs[i] ?? null,
        rpmPerMps: per,
        redlineKmh: per ? (car.redLine / Math.abs(per)) * MPS_TO_KMH : 0,
        shiftKmh: shift >= 0 ? shift * MPS_TO_KMH : null,
      });
    }
    this.gears = rows;
    const forward = rows.filter(r => r.index >= 2 && r.index < car.gears && r.rpmPerMps > 0);
    this.gearSeries = forward.map(r => ({
      id: `gear${r.index}`,
      label: `Gear ${r.name}`,
      color: r.color,
      points: [
        { x: 0, y: 0 },
        { x: r.redlineKmh, y: car.redLine },
      ],
    }));
    this.forceSeries = forward.map(r => {
      const points = [];
      for (let v = 0; v <= 110; v += 1) points.push({ x: v * MPS_TO_KMH, y: driveForce(car, r.index, v) });
      return { id: `force${r.index}`, label: `Gear ${r.name}`, color: r.color, points };
    });
    const res = [];
    for (let v = 0; v <= 110; v += 1) res.push({ x: v * MPS_TO_KMH, y: resistance(car, v) });
    this.forceSeries.push({ id: 'resistance', label: 'Drag + rolling', color: '#000', points: res, dashed: true });
    this.forceMarkers = forward
      .filter(r => r.shiftKmh !== null)
      .map(r => ({
        id: `shift${r.index}`,
        value: r.shiftKmh!,
        label: `${r.name}→${gearName(r.index + 1)}`,
        color: r.color,
      }));
    const top = topSpeed(car);
    if (top) this.forceMarkers.push({ id: 'top', value: top * MPS_TO_KMH, label: 'top speed', color: '#000' });
  }

  private refreshTires() {
    this.tires = ['tire_front', 'tire_rear'].map(section => {
      const t = this.d[section] || {};
      const r = tireRadius(t.SectionWidth, t.AspectRatio, t.WheelDiameter);
      return {
        section,
        axle: t.attach === 10 ? 'front record' : 'rear record',
        typeCode: t.TypeCode ?? null,
        width: t.SectionWidth ?? null,
        aspect: t.AspectRatio ?? null,
        diameter: t.WheelDiameter ?? null,
        radius: r,
        size: `${t.SectionWidth ?? '?'}/${t.AspectRatio ?? '?'} R${t.WheelDiameter ?? '?'}`,
      };
    });
  }

  private refreshAero(car: Nfs6Car) {
    const series = (id: string, label: string, color: string, f: (v: number) => number, dashed = false) => {
      const points = [];
      for (let v = 0; v <= 100; v += 2) points.push({ x: v * MPS_TO_KMH, y: f(v) });
      return { id, label, color, points, dashed } as CurveSeries;
    };
    this.aeroSeries = [
      series('drag', 'Air drag', '#3f51b5', v => aeroDrag(car, v)),
      series('front', 'Front downforce', '#009688', v => frontDownforce(car, v)),
      series('rear', 'Rear downforce', '#ff9800', v => rearDownforce(car, v)),
      series('lift', 'Body lift (+ unloads)', '#e91e63', v => bodyLift(car, v), true),
    ];
  }

  private refreshSteering(car: Nfs6Car) {
    const points = [];
    for (let v = 0; v <= 100; v += 1) points.push({ x: v * MPS_TO_KMH, y: steeringLimit(car, v) * 100 });
    this.steeringSeries = [{ id: 'limit', label: 'Steering limit', color: '#3f51b5', points }];
    this.steeringMarkers = [
      {
        id: 'BaseDampingVelocity',
        value: car.baseDampingVelocity * MPS_TO_KMH,
        label: 'BaseDampingVelocity',
        color: '#009688',
        editable: true,
        constraints: { min: 0 },
      },
      {
        id: 'RangeEnd',
        value: (car.baseDampingVelocity + car.rangeDampingVelocity) * MPS_TO_KMH,
        label: '+ RangeDampingVelocity',
        color: '#f44336',
        editable: true,
        constraints: { min: 0 },
      },
    ];
  }

  stepsAcross(): number {
    return this.car ? stepsAcross(this.car) : 0;
  }

  stepsToLock(): number {
    return this.car ? stepsToFullLock(this.car) : 0;
  }

  // edits

  onTorqueChange(change: CurveSeriesChange) {
    if (change.seriesId !== 'torque') return;
    const old: (number | null)[] = [...(this.d.engineblock?.torqueCurve || [])];
    while (old.length < TORQUE_ENTRIES) old.push(null);
    const next = old.map((v, i) => (change.changed.includes(i) ? Math.round(change.points[i].y * 10) / 10 : v));
    this.setValue(['engineblock', 'torqueCurve'], next);
  }

  onRpmMarker(change: CurveMarkerChange) {
    this.setValue(['engineblock', change.markerId], Math.round(change.value));
  }

  onSteeringMarker(change: CurveMarkerChange) {
    const v = Math.max(change.value / MPS_TO_KMH, 0);
    if (change.markerId === 'BaseDampingVelocity') {
      this.setValue(['basic', 'BaseDampingVelocity'], Math.round(v * 1000) / 1000);
    } else if (this.car) {
      this.setValue(
        ['basic', 'RangeDampingVelocity'],
        Math.round(Math.max(v - this.car.baseDampingVelocity, 0.1) * 1000) / 1000,
      );
    }
  }

  onGearInput(field: 'GearRatios' | 'GearEfficiency', index: number, raw: string) {
    const v = raw.trim() === '' ? null : parseFloat(raw);
    if (v !== null && !isFinite(v)) return;
    const list: (number | null)[] = [...(this.d.transmission?.[field] || [])];
    while (list.length < 8) list.push(null);
    list[index] = v;
    this.setValue(['transmission', field], list);
  }

  onTireInput(section: string, key: string, raw: string | number) {
    const v = typeof raw === 'number' ? raw : raw.trim() === '' ? null : Math.round(parseFloat(raw));
    if (v !== null && !isFinite(v)) return;
    this.setValue([section, key], v);
  }

  onAutomaticChange(value: boolean) {
    this.automatic = value;
    this.refresh();
  }

  sectionValue(section: string, key: string): any {
    return this.d[section]?.[key];
  }

  sectionDescription(section: string, key: string): string {
    const s = this.resourceSchema?.fields?.find((f: any) => f.name === section)?.schema;
    return s?.fields?.find((f: any) => f.name === key)?.description || '';
  }

  round(v: number | null, digits: number): string {
    return v === null || v === undefined || !isFinite(v) ? '' : String(Math.round(v * 10 ** digits) / 10 ** digits);
  }
}
