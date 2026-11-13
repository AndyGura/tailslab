import { ChangeDetectionStrategy, Component, inject, OnInit } from '@angular/core';
import {
  CurveAxis,
  CurvePoint,
  CurveSeries,
  CurveSeriesChange,
  CurveEditorComponent,
} from '../../common/curve-editor/curve-editor.component';
import { StatTile, StatTilesComponent } from '../../common/stat-tiles/stat-tiles.component';
import { RecordListItem, RecordListComponent } from '../../common/record-list/record-list.component';
import { CarSpecEditorBase, fmt } from '../player-car-physics.block-ui/car-specs';
import { MainService } from '../../../../services/main.service';
import { joinId } from '../../../../utils/join-id';
import {
  LBFT_TO_NM,
  NFS5_GEAR_NAMES,
  NFS5_TORQUE_STEP,
  nfs5PowerHp,
} from '../nfs5-car-physics.block-ui/nfs5-car-physics';
import {
  dirOf,
  findNfs5File,
  loadNfs5File,
  nfs5PendingSelection,
  resourcePath,
  takePendingSelection,
} from '../nfs5-car-physics.block-ui/nfs5-files';
import {
  NFS5_TYRE_TYPES,
  Nfs5Part,
  Nfs5PartEffect,
  nfs5PartEffects,
  nfs5PartPrice,
  nfs5PartRepairCost,
  nfs5PartTypeName,
  nfs5PartUsedValue,
  nfs5PartWearFactor,
} from './nfs5-parts';
import { MatTooltip } from '@angular/material/tooltip';
import { BlockActionsComponent } from '../../common/block-actions/block-actions.component';
import { MatButton } from '@angular/material/button';
import { MatIcon } from '@angular/material/icon';
import { MatTabGroup, MatTab, MatTabContent } from '@angular/material/tabs';
import { SliderFieldComponent } from '../../common/slider-field/slider-field.component';
import { CompoundBlockUiComponent } from '../../library/compound.block-ui/compound.block-ui.component';

// the part record's field names (Nfs5CarPart)
export const NFS5_PART_FIELDS = {
  price: 'sort_key',
  durability: 'durability',
};

export type Nfs5PartCarUse = { carIndex: number; carId: number; name: string; stock: boolean; buyable: boolean };

// Rich editor of the NFS5 car parts (FEData/Data/nfs5.prt, Nfs5CarParts): the parts by type with a filter, one
// part at a time: what it does to the car's physics (Porsche.exe 0x49cb50), its torque curve or gear ratios, its
// geometry switches, the cars of nfs5.car that have it as a stock or buyable part (links), every field
@Component({
  selector: 'app-nfs5-car-parts-block-ui',
  templateUrl: './nfs5-car-parts.block-ui.component.html',
  styleUrls: [
    '../player-car-physics.block-ui/player-car-physics.block-ui.component.scss',
    './nfs5-car-parts.block-ui.component.scss',
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    MatTooltip,
    BlockActionsComponent,
    RecordListComponent,
    MatButton,
    MatIcon,
    StatTilesComponent,
    MatTabGroup,
    MatTab,
    MatTabContent,
    CurveEditorComponent,
    SliderFieldComponent,
    CompoundBlockUiComponent,
  ],
})
export class Nfs5CarPartsBlockUiComponent extends CarSpecEditorBase implements OnInit {
  private readonly main = inject(MainService);

  readonly F = NFS5_PART_FIELDS;
  readonly tyreTypes = NFS5_TYRE_TYPES;
  readonly gearNames = NFS5_GEAR_NAMES;
  // Nfs5PartGeometryEntry fields
  readonly geometryKeys = ['a', 'b', 'value'];

  items: RecordListItem[] = [];
  selected: number | null = null;
  selectedTab = 0;
  tiles: StatTile[] = [];
  effects: Nfs5PartEffect[] = [];
  torqueSeries: CurveSeries[] = [];
  readonly rpmAxis: CurveAxis = { label: 'Engine speed (rpm)', min: 0, format: v => fmt(v, 0) };
  readonly torqueAxis: CurveAxis = { label: 'Torque (lb·ft)' };
  readonly powerAxis: CurveAxis = { label: 'Power (hp)' };
  readonly describeRpm = (rpm: number) => `${fmt(rpm, 0)} rpm · entry ${fmt(rpm / NFS5_TORQUE_STEP, 2)}`;

  // prices by year (Parts_Price 0x5181c0) for a damage preview
  priceSeries: CurveSeries[] = [];
  previewDamage = 0;
  readonly yearAxis: CurveAxis = { label: 'Year', format: v => '' + Math.round(v) };
  readonly moneyAxis: CurveAxis = { label: 'Dollars', min: 0, format: v => '$' + fmt(v, 0) };
  readonly describeYear = (y: number) => '' + Math.round(y);

  // the car database next to the file (nfs5.car), for the cars using a part
  carsPath: string | null = null;
  cars: any[] | null = null;
  carUses: Nfs5PartCarUse[] = [];
  carsNote = '';

  // the record's schema (child of the `parts` array)
  get partSchema(): any {
    return this.resourceSchema?.fields?.find((f: any) => f.name === 'parts')?.schema?.child_schema;
  }

  get parts(): Nfs5Part[] {
    return this.resourceData?.['parts'] || [];
  }

  get part(): Nfs5Part | null {
    return this.selected !== null ? this.parts[this.selected] || null : null;
  }

  get partId(): string {
    return joinId(this.resourceId!, 'parts', this.selected!);
  }

  get hasUnsavedChanges(): boolean {
    return !!this.changes.hasUnsavedChanges$?.value;
  }

  override ngOnInit(): void {
    super.ngOnInit();
    this.loadCars().then();
  }

  protected refresh(): void {
    const parts = this.parts;
    const pending = takePendingSelection('partId');
    if (pending !== undefined) {
      const i = parts.findIndex(p => p['id'] === pending);
      if (i >= 0) this.selected = i;
    }
    if (this.selected === null || this.selected >= parts.length) this.selected = parts.length ? 0 : null;
    this.items = parts.map((p, i) => ({
      index: i,
      label: partLabel(p),
      sub: [p['family'], p['year'] || '', p[this.F.price] !== undefined ? '$' + fmt(p[this.F.price], 0) : '']
        .filter(s => s !== '')
        .join(' · '),
      tag: '#' + p['id'],
      group: nfs5PartTypeName(p['type']),
    }));
    this.buildPart();
  }

  onSelect(index: number) {
    this.selected = index;
    this.buildPart();
    this.cdr.markForCheck();
  }

  private buildPart() {
    const p = this.part;
    if (!p) {
      this.tiles = [];
      this.effects = [];
      return;
    }
    this.effects = nfs5PartEffects(p);
    const torques: number[] = p['torque_curve'] || [];
    const peak = Math.max(0, ...torques);
    this.tiles = [
      { label: 'Type', value: nfs5PartTypeName(p['type']), sub: `type ${p['type']} · id ${p['id']}` },
      {
        id: this.F.price,
        label: 'Price',
        value: '$' + fmt(p[this.F.price] || 0, 0),
        edit: { value: p[this.F.price] || 0, step: 1, min: 0, unit: '$' },
        hint: this.fieldDescription(this.F.price),
      },
      {
        id: 'year',
        label: 'Year',
        value: '' + (p['year'] || '–'),
        edit: { value: p['year'] || 0, step: 1, min: 0 },
        hint: this.fieldDescription('year'),
      },
      {
        id: 'mass',
        label: 'Mass',
        value: `${p['mass'] > 0 ? '+' : ''}${fmt(p['mass'] || 0, 1)} kg`,
        edit: { value: p['mass'] || 0, step: 1, unit: 'kg' },
        hint: this.fieldDescription('mass'),
      },
      {
        label: 'Fits',
        value: p['family'] || '–',
        hint: this.fieldDescription('family'),
      },
    ];
    if (p['type'] === 1 && peak > 0) {
      let best = { hp: 0, rpm: 0 };
      torques.forEach((t, i) => {
        const hp = nfs5PowerHp(t, i * NFS5_TORQUE_STEP);
        if (hp > best.hp) best = { hp, rpm: i * NFS5_TORQUE_STEP };
      });
      this.tiles.push({
        label: p['name'] === 'Engine' ? 'Engine' : 'Torque added',
        value: `${fmt(p['name'] === 'Engine' ? peak : peak * 0.67, 0)} lb·ft`,
        sub: `peak ${fmt(peak * LBFT_TO_NM, 0)} N·m · ${fmt(best.hp, 0)} hp @ ${fmt(best.rpm, 0)}`,
      });
    }
    this.tiles.push({
      id: this.F.durability,
      label: 'Durability',
      value: fmt(p[this.F.durability] || 0, 0),
      edit: { value: p[this.F.durability] || 0, step: 1 },
      sub: `wear × ${fmt(nfs5PartWearFactor(p), 3)}`,
      hint: this.fieldDescription(this.F.durability),
    });
    this.buildTorque();
    this.buildPrices();
    this.buildCarUses();
  }

  private buildPrices() {
    const p = this.part;
    if (!p) return;
    const from = Math.max(1948, Math.min(2000, p['year'] || 1948));
    const years: number[] = [];
    for (let y = from; y <= 2000; y++) years.push(y);
    const money = (v: number) => '$' + fmt(v, 0);
    this.priceSeries = [
      {
        id: 'new',
        label: 'New',
        color: '#3f51b5',
        style: 'step',
        points: years.map(y => ({ x: y, y: nfs5PartPrice(p, y) })),
        formatY: money,
      },
      {
        id: 'used',
        label: `Sells for (${fmt(this.previewDamage, 0)}% damage)`,
        color: '#2e7d32',
        style: 'step',
        points: years.map(y => ({ x: y, y: nfs5PartUsedValue(p, y, this.previewDamage) })),
        formatY: money,
      },
      {
        id: 'repair',
        label: 'Repair',
        color: '#c62828',
        style: 'step',
        dashed: true,
        points: years.map(y => ({ x: y, y: nfs5PartRepairCost(p, y, this.previewDamage) })),
        formatY: money,
      },
    ];
  }

  onPreviewDamage(value: number) {
    this.previewDamage = value;
    this.buildPrices();
    this.cdr.markForCheck();
  }

  private buildTorque(torques: number[] = this.part?.['torque_curve'] || []) {
    const power: CurvePoint[] = torques.map((t, i) => ({
      x: i * NFS5_TORQUE_STEP,
      y: nfs5PowerHp(t, i * NFS5_TORQUE_STEP),
    }));
    this.torqueSeries = [
      {
        id: 'torque',
        label: 'Torque',
        color: '#3f51b5',
        points: torques.map((t, i) => ({ x: i * NFS5_TORQUE_STEP, y: t })),
        editable: 'y',
        y: { step: 1 },
        formatY: v => `${fmt(v, 1)} lb·ft · ${fmt(v * LBFT_TO_NM, 0)} N·m`,
      },
      {
        id: 'power',
        label: 'Power',
        color: '#e64a19',
        axis: 'right',
        points: power,
        formatY: v => `${fmt(v, 0)} hp`,
      },
    ];
  }

  onTorquePreview(e: CurveSeriesChange) {
    if (e.seriesId === 'torque') this.buildTorque(e.points.map(p => p.y));
  }

  onTorqueChange(e: CurveSeriesChange) {
    if (e.seriesId !== 'torque' || this.selected === null) return;
    const torques = [...(this.part!['torque_curve'] as number[])];
    for (const i of e.changed) torques[i] = Math.round(e.points[i].y * 100) / 100;
    this.setValue(['parts', this.selected, 'torque_curve'], torques);
  }

  onTileChange(e: { id: string; value: number }) {
    if (this.selected === null) return;
    this.setValue(['parts', this.selected, e.id], e.value);
  }

  setPartField(name: string, value: any) {
    if (this.selected === null) return;
    this.setValue(['parts', this.selected, name], value);
  }

  onPartNumberInput(path: (string | number)[], raw: string, integer: boolean = false) {
    if (this.selected === null) return;
    this.onNumberInput(['parts', this.selected, ...path], raw, integer);
  }

  fieldDescription(name: string): string {
    return this.partSchema?.fields?.find((f: any) => f.name === name)?.description || '';
  }

  // ---------- geometry switches ----------

  get geometryEntries(): any[] {
    const p = this.part;
    if (!p) return [];
    return (p['geometry_entries'] || []).slice(0, Math.max(0, p['num_geometry_entries'] || 0));
  }

  addGeometryEntry() {
    const p = this.part;
    if (!p || this.selected === null) return;
    const n = p['num_geometry_entries'] || 0;
    if (n >= (p['geometry_entries'] || []).length) return;
    this.setValue(['parts', this.selected, 'num_geometry_entries'], n + 1);
  }

  removeGeometryEntry() {
    const p = this.part;
    if (!p || this.selected === null) return;
    const n = p['num_geometry_entries'] || 0;
    if (n <= 0) return;
    const entries = [...p['geometry_entries']];
    entries[n - 1] = { ...entries[n - 1], a: 0, b: 0, value: 0 };
    this.setValues([
      [['parts', this.selected, 'num_geometry_entries'], n - 1],
      [['parts', this.selected, 'geometry_entries'], entries],
    ]);
  }

  // ---------- records ----------

  duplicatePart() {
    const p = this.part;
    if (!p || !this.resourceId || this.disabled) return;
    const copy = JSON.parse(JSON.stringify(p));
    copy['id'] = Math.max(0, ...this.parts.map(x => x['id'] || 0)) + 1;
    const index = this.selected! + 1;
    this.changes
      .appendChanges({
        timestamp: Date.now(),
        op: 'array_insert',
        id: joinId(this.resourceId, 'parts'),
        index,
        value: copy,
      })
      .then(() => this.onSelect(index));
  }

  deletePart() {
    const p = this.part;
    if (!p || !this.resourceId || this.disabled) return;
    const index = this.selected!;
    this.changes
      .appendChanges({
        timestamp: Date.now(),
        op: 'array_remove',
        id: joinId(this.resourceId, 'parts'),
        index,
        oldValue: p,
      })
      .then(() => this.onSelect(Math.max(0, Math.min(index, this.parts.length - 1))));
  }

  // ---------- the cars using the part (nfs5.car next to the file) ----------

  private async loadCars() {
    if (!this.resourceId || !this.main?.api) return;
    const dir = dirOf(resourcePath(this.resourceId));
    this.carsPath = await findNfs5File(this.main.api, dir, ['nfs5.car']);
    if (!this.carsPath) {
      this.carsNote = 'nfs5.car is not next to this file: the cars using a part are not shown.';
      this.cdr.markForCheck();
      return;
    }
    const data = await loadNfs5File<any>(this.main.api, this.carsPath);
    this.cars = data?.['cars'] || null;
    this.carsNote = this.cars ? '' : 'nfs5.car could not be read.';
    this.buildCarUses();
    this.cdr.markForCheck();
  }

  private buildCarUses() {
    const p = this.part;
    this.carUses = [];
    if (!p || !this.cars) return;
    const id = p['id'];
    this.cars.forEach((car, i) => {
      const stock = (car['stock_parts'] || []).slice(0, car['num_stock_parts'] || 0).includes(id);
      const buyable = (car['upgrade_parts'] || []).slice(0, car['num_upgrade_parts'] || 0).includes(id);
      if (stock || buyable) {
        this.carUses.push({ carIndex: i, carId: car['id'], name: car['display_name'], stock, buyable });
      }
    });
  }

  // opens nfs5.car at that car (the GUI shows one file at a time)
  async openCar(use: Nfs5PartCarUse) {
    if (!this.carsPath || this.hasUnsavedChanges) return;
    nfs5PendingSelection.carId = use.carId;
    await this.main.api.openFile(this.carsPath, true);
  }

  readonly fmt = fmt;
  readonly typeName = nfs5PartTypeName;

  round(v: number, digits: number): number {
    const k = Math.pow(10, digits);
    return Math.round(v * k) / k;
  }
}

export function partLabel(p: Nfs5Part): string {
  const name = p['name'] || nfs5PartTypeName(p['type']);
  return p['type'] === 9 && !p['name'] ? `Tyres (${NFS5_TYRE_TYPES[p['drive_type']] ?? p['drive_type']})` : name;
}
