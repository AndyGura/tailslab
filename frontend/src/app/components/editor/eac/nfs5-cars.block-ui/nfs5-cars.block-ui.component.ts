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
  argbToCss,
  cssToArgb,
  dirOf,
  findNfs5File,
  loadNfs5Parts,
  NFS5_FEDATA_TO_AIS,
  NFS5_FEDATA_TO_SIM,
  nfs5PendingSelection,
  Nfs5PartInfo,
  resourcePath,
  takePendingSelection,
} from '../nfs5-car-physics.block-ui/nfs5-files';
import {
  NFS5_AVAILABILITY,
  NFS5_CAR_KINDS,
  NFS5_CLASSES,
  NFS5_ERAS,
  NFS5_FIRST_VALUE_YEAR,
  NFS5_LAST_VALUE_YEAR,
  NFS5_RATINGS,
  Nfs5Car,
  nfs5CarValue,
  nfs5CarYears,
  nfs5DealerPrice,
} from './nfs5-cars';
import { nfs5PartPrice } from '../nfs5-car-parts.block-ui/nfs5-parts';
import { MatTooltip } from '@angular/material/tooltip';
import { BlockActionsComponent } from '../../common/block-actions/block-actions.component';
import { CompoundBlockUiComponent } from '../../library/compound.block-ui/compound.block-ui.component';
import { MatIconButton, MatButton } from '@angular/material/button';
import { MatIcon } from '@angular/material/icon';
import { MatTabGroup, MatTab, MatTabContent } from '@angular/material/tabs';
import { NgTemplateOutlet } from '@angular/common';
import { FormsModule } from '@angular/forms';

export type Nfs5PartRow = {
  slot: number;
  id: number;
  label: string;
  type: string;
  price: number | null;
  missing: boolean;
};
export type Nfs5PaintRow = { slot: number; fields: { key: string; label: string; value: number; css: string }[] };

const PART_TYPES: { [t: number]: string } = {
  1: 'Engine',
  2: 'Brakes',
  3: 'Gearbox',
  4: 'Springs',
  5: 'Shocks',
  6: 'Aero',
  7: 'Body panel',
  8: 'Sway bars',
  9: 'Tyres',
  10: 'Body',
};

// Rich editor of the NFS5 car database (FEData/Data/nfs5.car, Nfs5Cars): the cars, traffic cars and cops with a
// filter, one record at a time: names and the files it names (links to its .sim and .ais), prices and the value by
// year with the dealer price and the car's value (Porsche.exe 0x4ee220, 0x4f8e50), ratings, the stock and buyable
// parts by name (nfs5.prt next to the file, links), the paints and interiors as colours, the dashboard dials, every
// field
@Component({
  selector: 'app-nfs5-cars-block-ui',
  templateUrl: './nfs5-cars.block-ui.component.html',
  styleUrls: [
    '../player-car-physics.block-ui/player-car-physics.block-ui.component.scss',
    '../nfs5-car-parts.block-ui/nfs5-car-parts.block-ui.component.scss',
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    MatTooltip,
    BlockActionsComponent,
    CompoundBlockUiComponent,
    MatIconButton,
    MatIcon,
    RecordListComponent,
    MatButton,
    StatTilesComponent,
    MatTabGroup,
    MatTab,
    MatTabContent,
    NgTemplateOutlet,
    CurveEditorComponent,
    FormsModule,
  ],
})
export class Nfs5CarsBlockUiComponent extends CarSpecEditorBase implements OnInit {
  private readonly main = inject(MainService);

  readonly kinds = NFS5_CAR_KINDS;
  readonly classes = NFS5_CLASSES;
  readonly eras = NFS5_ERAS;
  readonly availabilityNames = NFS5_AVAILABILITY;
  readonly ratingNames = NFS5_RATINGS;
  readonly groups = {
    names: ['display_name', 'short_name', 'locale_id', 'showcase_picture'],
    files: ['model', 'spec', 'ai_spec', 'sound', 'logos', 'logo_index'],
    body: ['body_text', 'convertible', 'body_style', 'engine_text', 'class_string_id', 'era_string_id', 'kind'],
    market: ['price', 'first_year', 'last_year', 'availability', 'abs_available', 'traction_available'],
    dash: ['gauges', 'speedo_kmh', 'speedo_mph', 'tachometer'],
    unknown: ['unk_2e0', 'unk_2e8', 'unk_2ec'],
  };

  items: RecordListItem[] = [];
  selected: number | null = null;
  selectedTab = 0;
  tiles: StatTile[] = [];
  year = 1990;

  valueSeries: CurveSeries[] = [];
  readonly yearAxis: CurveAxis = {
    label: 'Year',
    min: NFS5_FIRST_VALUE_YEAR,
    max: NFS5_LAST_VALUE_YEAR,
    format: v => '' + Math.round(v),
  };
  readonly percentAxis: CurveAxis = { label: 'Value (% of the price)', min: 0 };
  readonly moneyAxis: CurveAxis = { label: 'Dollars', min: 0, format: v => '$' + fmt(v, 0) };
  readonly describeYear = (y: number) => '' + Math.round(y);

  // nfs5.prt next to the file
  partsPath: string | null = null;
  parts: Map<number, Nfs5PartInfo> | null = null;
  partsNote = '';
  stockRows: Nfs5PartRow[] = [];
  upgradeRows: Nfs5PartRow[] = [];
  newStockId: number | null = null;
  newUpgradeId: number | null = null;

  paintRows: Nfs5PaintRow[] = [];
  interiorRows: Nfs5PaintRow[] = [];

  // the car's .sim / .ais next to the game folder
  simPath: string | null = null;
  aisPath: string | null = null;

  get carSchema(): any {
    return this.resourceSchema?.fields?.find((f: any) => f.name === 'cars')?.schema?.child_schema;
  }

  get cars(): Nfs5Car[] {
    return this.resourceData?.['cars'] || [];
  }

  get car(): Nfs5Car | null {
    return this.selected !== null ? this.cars[this.selected] || null : null;
  }

  get carId(): string {
    return joinId(this.resourceId!, 'cars', this.selected!);
  }

  get dir(): string {
    return this.resourceId ? dirOf(resourcePath(this.resourceId)) : '';
  }

  get hasUnsavedChanges(): boolean {
    return !!this.changes.hasUnsavedChanges$?.value;
  }

  override ngOnInit(): void {
    super.ngOnInit();
    this.loadParts().then();
  }

  protected refresh(): void {
    const cars = this.cars;
    const pending = takePendingSelection('carId');
    if (pending !== undefined) {
      const i = cars.findIndex(c => c['id'] === pending);
      if (i >= 0) this.selected = i;
    }
    if (this.selected === null || this.selected >= cars.length) this.selected = cars.length ? 0 : null;
    this.items = cars.map((c, i) => ({
      index: i,
      label: c['display_name'] || '(no name)',
      sub: `${nfs5CarYears(c)} · $${fmt(c['price'] || 0, 0)}${c['availability'] ? ' · ' + ['', 'limited', 'bonus', 'factory'][c['availability']] : ''}`,
      tag: '#' + c['id'],
      group: c['kind'] === 1 ? 'Traffic' : c['kind'] === 2 ? 'Cops' : NFS5_ERAS[c['era_string_id']] || 'Cars',
      muted: c['availability'] === 3,
    }));
    this.buildCar();
  }

  onSelect(index: number) {
    this.selected = index;
    this.buildCar();
    this.findLinkedFiles().then();
    this.cdr.markForCheck();
  }

  private buildCar() {
    const c = this.car;
    if (!c) {
      this.tiles = [];
      return;
    }
    const year = Math.max(c['first_year'] || NFS5_FIRST_VALUE_YEAR, Math.min(NFS5_LAST_VALUE_YEAR, this.year));
    this.tiles = [
      {
        id: 'price',
        label: 'Price',
        value: '$' + fmt(c['price'] || 0, 0),
        edit: { value: c['price'] || 0, step: 100, min: 0, unit: '$' },
        sub: `${nfs5CarYears(c)} · ${NFS5_CLASSES[c['class_string_id']] || '–'}`,
        hint: this.fieldDescription('price'),
        tone: 'accent',
      },
      {
        label: `Value in ${year}`,
        value: '$' + fmt(nfs5CarValue(c, year), 0),
        sub: `dealer $${fmt(nfs5DealerPrice(c, year), 0)}`,
        hint: 'The current value base (0x4f8e50) and the dealer price (0x4ee220) in the year of the Market tab',
      },
      {
        label: 'Kind',
        value: NFS5_CAR_KINDS[c['kind']] ?? '' + c['kind'],
        sub: NFS5_ERAS[c['era_string_id']] || '',
      },
      {
        label: 'Availability',
        value: '' + c['availability'],
        sub: NFS5_AVAILABILITY[c['availability']] ?? '',
        hint: this.fieldDescription('availability'),
      },
      {
        label: 'Parts',
        value: `${c['num_stock_parts'] || 0} stock`,
        sub: `${c['num_upgrade_parts'] || 0} in the shop`,
      },
      {
        label: 'Paints',
        value: `${c['num_paints'] || 0}`,
        sub: `${c['num_interiors'] || 0} interiors`,
      },
    ];
    this.buildValue();
    this.buildParts();
    this.buildPaints();
  }

  fieldDescription(name: string): string {
    return this.carSchema?.fields?.find((f: any) => f.name === name)?.description || '';
  }

  setCarField(path: (string | number)[], value: any) {
    if (this.selected === null) return;
    this.setValue(['cars', this.selected, ...path], value);
  }

  onCarNumberInput(path: (string | number)[], raw: string, integer: boolean = false) {
    if (this.selected === null) return;
    this.onNumberInput(['cars', this.selected, ...path], raw, integer);
  }

  onTileChange(e: { id: string; value: number }) {
    this.setCarField([e.id], Math.round(e.value));
  }

  // ---------- market ----------

  private buildValue(values: number[] = this.car?.['value_by_year'] || []) {
    const c: Nfs5Car = { ...this.car!, value_by_year: values };
    const years = values.map((_, i) => NFS5_FIRST_VALUE_YEAR + i);
    const value: CurvePoint[] = [];
    const dealer: CurvePoint[] = [];
    for (const y of years) {
      if (y < (c['first_year'] || 0)) continue;
      value.push({ x: y, y: nfs5CarValue(c, y) });
      dealer.push({ x: y, y: nfs5DealerPrice(c, y) });
    }
    const money = (v: number) => '$' + fmt(v, 0);
    this.valueSeries = [
      {
        id: 'value',
        label: 'Value (%)',
        color: '#3f51b5',
        points: values.map((v, i) => ({ x: years[i], y: v })),
        editable: 'y',
        y: { min: 0, step: 1 },
        formatY: v => fmt(v, 1) + '%',
      },
      { id: 'car_value', label: 'Car value', color: '#2e7d32', axis: 'right', points: value, formatY: money },
      {
        id: 'dealer',
        label: 'Dealer price',
        color: '#ef6c00',
        axis: 'right',
        dashed: true,
        points: dealer,
        formatY: money,
      },
    ];
  }

  onValuePreview(e: CurveSeriesChange) {
    if (e.seriesId === 'value') this.buildValue(e.points.map(p => p.y));
  }

  onValueChange(e: CurveSeriesChange) {
    if (e.seriesId !== 'value' || !this.car) return;
    const values = [...this.car['value_by_year']];
    for (const i of e.changed) values[i] = Math.max(0, Math.round(e.points[i].y * 10) / 10);
    this.setCarField(['value_by_year'], values);
  }

  onYear(raw: string) {
    const y = parseInt(raw, 10);
    if (!isFinite(y)) return;
    this.year = Math.max(NFS5_FIRST_VALUE_YEAR, Math.min(NFS5_LAST_VALUE_YEAR, y));
    this.buildCar();
  }

  // ---------- parts ----------

  private async loadParts() {
    if (!this.resourceId || !this.main?.api) return;
    const loaded = await loadNfs5Parts(this.main.api, this.dir);
    this.partsPath = loaded?.path || null;
    this.parts = loaded?.byId || null;
    this.partsNote = loaded ? '' : 'nfs5.prt is not next to this file: the parts are listed by id only.';
    this.buildParts();
    this.findLinkedFiles().then();
    this.cdr.markForCheck();
  }

  private partRows(ids: number[], count: number): Nfs5PartRow[] {
    return ids.slice(0, Math.max(0, count)).map((id, slot) => {
      const info = this.parts?.get(id);
      return {
        slot,
        id,
        label: info ? info.label : this.parts ? '(not in nfs5.prt)' : '',
        type: info ? PART_TYPES[info.type] || '' + info.type : '',
        price: info ? nfs5PartPrice(info.part, info.part['year'] || 0) : null,
        missing: !!this.parts && !info,
      };
    });
  }

  private buildParts() {
    const c = this.car;
    if (!c) return;
    this.stockRows = this.partRows(c['stock_parts'] || [], c['num_stock_parts'] || 0);
    this.upgradeRows = this.partRows(c['upgrade_parts'] || [], c['num_upgrade_parts'] || 0);
  }

  // removes the part at a slot of a list (the ids after it move up, the freed last slot becomes 0)
  removePart(list: 'stock_parts' | 'upgrade_parts', slot: number) {
    const c = this.car;
    if (!c || this.selected === null) return;
    const countField = list === 'stock_parts' ? 'num_stock_parts' : 'num_upgrade_parts';
    const n = c[countField] || 0;
    const ids = [...c[list]];
    ids.splice(slot, 1);
    ids.push(0);
    this.setValues([
      [['cars', this.selected, list], ids],
      [['cars', this.selected, countField], Math.max(0, n - 1)],
    ]);
  }

  addPart(list: 'stock_parts' | 'upgrade_parts', id: number | null) {
    const c = this.car;
    if (!c || this.selected === null || !id) return;
    const countField = list === 'stock_parts' ? 'num_stock_parts' : 'num_upgrade_parts';
    const n = c[countField] || 0;
    const ids = [...c[list]];
    if (n >= ids.length) return;
    ids[n] = id;
    this.setValues([
      [['cars', this.selected, list], ids],
      [['cars', this.selected, countField], n + 1],
    ]);
  }

  get partOptions(): Nfs5PartInfo[] {
    return this.parts ? [...this.parts.values()].sort((a, b) => a.type - b.type || a.label.localeCompare(b.label)) : [];
  }

  async openPart(id: number) {
    if (!this.partsPath || this.hasUnsavedChanges) return;
    nfs5PendingSelection.partId = id;
    await this.main.api.openFile(this.partsPath, true);
  }

  // ---------- links to the .sim / .ais ----------

  private async findLinkedFiles() {
    const c = this.car;
    if (!c || !this.main?.api) return;
    this.simPath = c['spec']
      ? await findNfs5File(this.main.api, this.dir, [`${NFS5_FEDATA_TO_SIM}/${c['spec']}.sim`])
      : null;
    this.aisPath = c['ai_spec']
      ? await findNfs5File(this.main.api, this.dir, [`${NFS5_FEDATA_TO_AIS}/${c['ai_spec']}.ais`])
      : null;
    this.cdr.markForCheck();
  }

  async openFile(path: string | null) {
    if (!path || this.hasUnsavedChanges) return;
    await this.main.api.openFile(path, true);
  }

  // ---------- paint ----------

  private buildPaints() {
    const c = this.car;
    if (!c) return;
    const row = (slot: number, rec: any, keys: [string, string][]) => ({
      slot,
      fields: keys.map(([key, label]) => ({ key, label, value: rec[key] >>> 0, css: argbToCss(rec[key]) })),
    });
    this.paintRows = (c['paints'] || []).slice(0, c['num_paints'] || 0).map((p: any, i: number) =>
      row(i, p, [
        ['body', 'Body'],
        ['accent_1', 'Accent 1'],
        ['accent_2', 'Accent 2'],
      ]),
    );
    this.interiorRows = (c['interiors'] || [])
      .slice(0, c['num_interiors'] || 0)
      .map((p: any, i: number) => row(i, p, [['colour', 'Interior']]));
  }

  onColour(list: 'paints' | 'interiors', slot: number, key: string, css: string) {
    const c = this.car;
    if (!c) return;
    this.setCarField([list, slot, key], cssToArgb(css, c[list][slot][key]));
  }

  addPaint(list: 'paints' | 'interiors') {
    const c = this.car;
    if (!c || this.selected === null) return;
    const countField = list === 'paints' ? 'num_paints' : 'num_interiors';
    const n = c[countField] || 0;
    if (n >= (c[list] || []).length) return;
    const records = [...c[list]];
    // a copy of the last colour, or opaque white
    records[n] =
      n > 0
        ? { ...records[n - 1] }
        : list === 'paints'
          ? { flag: 0, body: 0xffffffff, accent_1: 0xff000000, accent_2: 0xff000000 }
          : { unused_0: 0, colour: 0xffffffff, unused_8: 0xff000000, unused_c: 0xff000000 };
    this.setValues([
      [['cars', this.selected, list], records],
      [['cars', this.selected, countField], n + 1],
    ]);
  }

  removeLastPaint(list: 'paints' | 'interiors') {
    const c = this.car;
    if (!c || this.selected === null) return;
    const countField = list === 'paints' ? 'num_paints' : 'num_interiors';
    const n = c[countField] || 0;
    if (n <= 0) return;
    this.setCarField([countField], n - 1);
  }

  // ---------- ratings ----------

  onRating(i: number, raw: string) {
    this.onCarNumberInput(['ratings', i], raw, true);
  }

  // ---------- records ----------

  duplicateCar() {
    const c = this.car;
    if (!c || !this.resourceId || this.disabled) return;
    const copy = JSON.parse(JSON.stringify(c));
    copy['id'] = Math.max(0, ...this.cars.map(x => x['id'] || 0)) + 1;
    const index = this.selected! + 1;
    this.changes
      .appendChanges({
        timestamp: Date.now(),
        op: 'array_insert',
        id: joinId(this.resourceId, 'cars'),
        index,
        value: copy,
      })
      .then(() => this.onSelect(index));
  }

  deleteCar() {
    const c = this.car;
    if (!c || !this.resourceId || this.disabled) return;
    const index = this.selected!;
    this.changes
      .appendChanges({
        timestamp: Date.now(),
        op: 'array_remove',
        id: joinId(this.resourceId, 'cars'),
        index,
        oldValue: c,
      })
      .then(() => this.onSelect(Math.max(0, Math.min(index, this.cars.length - 1))));
  }

  readonly fmt = fmt;
}
