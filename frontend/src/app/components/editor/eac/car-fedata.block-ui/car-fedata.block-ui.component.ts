import { ChangeDetectionStrategy, Component } from '@angular/core';
import {
  CurveAxis,
  CurveSeries,
  CurveSeriesChange,
  CurveEditorComponent,
} from '../../common/curve-editor/curve-editor.component';
import { StatTile, StatTilesComponent } from '../../common/stat-tiles/stat-tiles.component';
import { SliderSpec, SliderFieldComponent } from '../../common/slider-field/slider-field.component';
import { CarSpecEditorBase, fmt } from '../player-car-physics.block-ui/car-specs';
import { MatTooltip } from '@angular/material/tooltip';
import { BlockActionsComponent } from '../../common/block-actions/block-actions.component';
import { CompoundBlockUiComponent } from '../../library/compound.block-ui/compound.block-ui.component';
import { MatTabGroup, MatTab, MatTabContent } from '@angular/material/tabs';
import { NgTemplateOutlet } from '@angular/common';
import { FormsModule } from '@angular/forms';

// a text of the fedata text table, as the block's schema names it (resources/eac/fedata.py, text_names)
export type FeDataTextName = { name: string; label: string; section: string };
export type FeDataTextRow = FeDataTextName & { index: number; value: string; invalid: boolean };
export type FeDataSection = { title: string; rows: FeDataTextRow[] };

// the ratings of the front end's bars, out of 20 (nfs3.exe 0x438f60, nfs4.exe 0x4724c0: rating x 0.05)
export const RATING_MAX = 20;
const NFS3_RATINGS = ['acceleration', 'top_speed', 'handling', 'braking'];
const NFS4_RATINGS = ['acceleration', 'top_speed', 'handling', 'braking', 'overall_rating'];
const RATING_LABELS: { [field: string]: string } = {
  acceleration: 'Acceleration',
  top_speed: 'Top speed',
  handling: 'Handling',
  braking: 'Braking',
  overall_rating: 'Overall (opponent pick)',
};
const RATING_COLORS = ['#3f51b5', '#e91e63', '#009688', '#ff9800', '#795548'];
const LEVELS = ['Stock', 'Level 1', 'Level 2', 'Level 3'];
// the order the spec sheet shows its sections in (TEXT.ENG: General, Performance, Transmission, Mechanical)
const SHEET_SECTIONS = ['General', 'Performance', 'Transmission', 'Mechanical'];
// the interior view's panorama: 1280 texels per turn (nfs3.exe 0x464840)
export const INTERIOR_TEXELS = 1280;

// car class names (nfs3.exe car list +0x388; nfs4.exe record +0x380)
export const classNames = (nfs4: boolean): { [value: number]: string } =>
  nfs4 ? { 0: 'Race (AA)', 1: 'A', 2: 'B', 3: 'C', 255: 'None' } : { 0: 'A', 1: 'B', 2: 'C', 255: 'None' };
export const ENGINE_POSITIONS: { [value: number]: string } = { 0: 'Front', 1: 'Middle', 2: 'Rear' };
export const DRIVER_SEATS: { [value: number]: string } = { 0: 'Left (-0.4 m)', 1: 'Right (+0.4 m)' };

// a text the game can show: Latin-1 characters only (the files are 8-bit, nfs3.exe / nfs4.exe draw bytes)
export const isLatin1 = (text: string) => [...text].every(c => c.charCodeAt(0) <= 0xff && c.length === 1);

// Editor of NFS3 / NFS4 `fedata.<lang>` (Nfs3CarFeData, Nfs4CarFeData; resources/eac/fedata.py): the spec sheet as the
// showroom lays it out, the history and colour names, the rating bars (NFS4: by upgrade level), the car list values
// (class, flags, seat / engine, interior view, prices) and every field in "All fields"
@Component({
  selector: 'app-car-fedata-block-ui',
  templateUrl: './car-fedata.block-ui.component.html',
  styleUrls: [
    '../player-car-physics.block-ui/player-car-physics.block-ui.component.scss',
    './car-fedata.block-ui.component.scss',
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    MatTooltip,
    BlockActionsComponent,
    CompoundBlockUiComponent,
    StatTilesComponent,
    MatTabGroup,
    MatTab,
    MatTabContent,
    NgTemplateOutlet,
    CurveEditorComponent,
    FormsModule,
    SliderFieldComponent,
  ],
})
export class CarFeDataBlockUiComponent extends CarSpecEditorBase {
  readonly nfs3Groups = {
    identity: ['car_id', 'serial_number', 'guid_data2', 'guid_data3', 'guid_data4', 'format_version', 'game'],
    flags: ['bonus', 'police', 'shared_car', 'own_art', 'filter_flag', 'unused_0x13'],
    unused: ['overall_rating'],
  };
  readonly nfs4Groups = {
    identity: ['car_id', 'serial_number', 'format_version', 'game'],
    flags: ['flags'],
    runtime: [
      'runtime_list',
      'name',
      'folder',
      'runtime_0x310',
      'runtime_0x320',
      'runtime_0x37c',
      'unused_0x39d',
      'runtime_0x3ac',
      'driver_seat',
      'unused_0x3bc',
    ],
  };
  readonly headingSlider: SliderSpec = { min: 0, max: INTERIOR_TEXELS - 1, step: 1, unit: 'texels' };

  selectedTab = 0;
  tiles: StatTile[] = [];
  textNames: FeDataTextName[] = [];
  names: FeDataTextRow[] = [];
  sheet: FeDataSection[] = [];
  history: FeDataTextRow[] = [];
  colors: FeDataTextRow[] = [];
  extraTexts: FeDataTextRow[] = [];
  ratingSeries: CurveSeries[] = [];
  ratingXAxis: CurveAxis = { label: 'Rating', categories: [] };
  readonly ratingYAxis: CurveAxis = { label: 'Rating (of 20)', min: 0, max: RATING_MAX, format: v => fmt(v, 0) };
  classOptions: { value: number; label: string }[] = [];
  readonly engineOptions = Object.entries(ENGINE_POSITIONS).map(([v, label]) => ({ value: +v, label }));
  readonly seatOptions = [
    ...Object.entries(DRIVER_SEATS).map(([v, label]) => ({ value: +v, label })),
    { value: 2, label: 'Centre (other values)' },
  ];

  get isNfs4(): boolean {
    return (this.resourceSchema?.block_class_mro || '').startsWith('Nfs4CarFeData');
  }

  get exeName(): string {
    return this.isNfs4 ? 'nfs4.exe' : 'nfs3.exe';
  }

  get ratingFields(): string[] {
    return this.isNfs4 ? NFS4_RATINGS : NFS3_RATINGS;
  }

  get texts(): string[] {
    return (this.d?.['texts'] as string[]) || [];
  }

  protected refresh(): void {
    if (!this.d || !Array.isArray(this.d['texts'])) return;
    this.textNames = this.readTextNames();
    this.buildTexts();
    this.buildRatings();
    this.classOptions = Object.entries(classNames(this.isNfs4)).map(([v, label]) => ({ value: +v, label }));
    this.buildTiles();
  }

  private readTextNames(): FeDataTextName[] {
    const field = (this.resourceSchema?.fields as { name: string; schema?: any }[] | undefined)?.find(
      f => f.name === 'texts',
    );
    return ((field?.schema as any)?.text_names as FeDataTextName[]) || [];
  }

  // ---------- texts ----------

  textRow(index: number): FeDataTextRow {
    const name = this.textNames[index] || { name: `text_${index}`, label: `Text ${index}`, section: 'Other' };
    const value = this.texts[index] ?? '';
    return { ...name, index, value, invalid: !isLatin1(value) };
  }

  private buildTexts() {
    const rows = this.texts.map((_, i) => this.textRow(i));
    // the game reads texts by index: names past the file's count read empty
    for (let i = rows.length; i < this.textNames.length; i++) rows.push({ ...this.textRow(i), value: '' });
    this.names = rows.filter(r => r.section === 'Names');
    this.sheet = SHEET_SECTIONS.map(title => ({ title, rows: rows.filter(r => r.section === title) })).filter(
      s => s.rows.length,
    );
    this.history = rows.filter(r => r.section === 'History');
    this.colors = rows.filter(r => r.section === 'Colours');
    this.extraTexts = rows.filter(r => r.index >= this.textNames.length);
  }

  // a text typed into the sheet: one undoable change; the array grows to the index (empty texts before it)
  setText(index: number, value: string) {
    if (!isLatin1(value)) return;
    const texts = [...this.texts];
    if (index < texts.length) {
      this.setValue(['texts', index], value);
      return;
    }
    while (texts.length < index) texts.push('');
    texts.push(value);
    this.setValue(['texts'], texts);
  }

  // ---------- ratings ----------

  private buildRatings() {
    const d = this.d;
    if (this.isNfs4) {
      this.ratingXAxis = { label: 'Upgrade level', categories: LEVELS };
      this.ratingSeries = NFS4_RATINGS.map((field, k) => ({
        id: field,
        label: RATING_LABELS[field],
        color: RATING_COLORS[k],
        points: ((d[field] as number[]) || []).map((y, x) => ({ x, y })),
        editable: 'y',
        y: { min: 0, max: RATING_MAX, step: 1 },
        formatY: v => `${fmt(v, 0)} / ${RATING_MAX}`,
      }));
    } else {
      this.ratingXAxis = { label: 'Rating', categories: NFS3_RATINGS.map(f => RATING_LABELS[f]) };
      this.ratingSeries = [
        {
          id: 'ratings',
          label: 'Rating',
          color: RATING_COLORS[0],
          style: 'bars',
          points: NFS3_RATINGS.map((f, x) => ({ x, y: d[f] || 0 })),
          editable: 'y',
          y: { min: 0, max: RATING_MAX, step: 1 },
          pointLabels: NFS3_RATINGS.map(f => RATING_LABELS[f]),
          formatY: v => `${fmt(v, 0)} / ${RATING_MAX}`,
        },
      ];
    }
  }

  // ratings are bytes 0..20 (the bars' scale)
  static clampRating(v: number): number {
    return Math.max(0, Math.min(255, Math.round(v)));
  }

  onRatingsChange(e: CurveSeriesChange) {
    if (this.isNfs4) {
      this.setValue(
        [e.seriesId],
        e.points.map(p => CarFeDataBlockUiComponent.clampRating(p.y)),
      );
    } else {
      this.setValues(
        NFS3_RATINGS.map((f, k) => [[f], CarFeDataBlockUiComponent.clampRating(e.points[k]?.y ?? this.d[f])]),
      );
    }
  }

  // ---------- derived ----------

  // the interior view's starting heading in degrees (1280 texels per turn)
  headingDegrees(value: number = this.d['interior_view_heading'] || 0): number {
    return (value * 360) / INTERIOR_TEXELS;
  }

  className(value: number = this.d['car_class']): string {
    return classNames(this.isNfs4)[value] ?? `${value}`;
  }

  seatName(value: number = this.d['driver_seat']): string {
    return DRIVER_SEATS[value] ?? 'Centre';
  }

  // NFS4: the dealer price of each level, price + the upgrades bought up to it
  levelPrices(): number[] {
    const prices = [this.d['price'] || 0];
    for (const p of (this.d['upgrade_prices'] as number[]) || []) prices.push(prices[prices.length - 1] + p);
    return prices;
  }

  // the flags that make the car special, as the car list keeps them
  statusFlags(): string[] {
    const d = this.d;
    if (this.isNfs4) {
      const f = d['flags'] || {};
      const names: [string, string][] = [
        ['bonus', 'bonus'],
        ['police', 'police'],
        ['network_car', 'network placeholder'],
        ['no_upgrades', 'no upgrades'],
        ['fixed_color', 'fixed colour'],
        ['convertible', 'convertible'],
        ['open_top', 'open top'],
        ['no_engine_smoke', 'no engine smoke'],
      ];
      return names.filter(([k]) => f[k]).map(([, label]) => label);
    }
    const names: [string, string][] = [
      ['bonus', 'bonus'],
      ['police', 'police'],
      ['own_art', 'own art'],
    ];
    return names.filter(([k]) => d[k]).map(([, label]) => label);
  }

  setNumber(field: string, raw: any) {
    const v = typeof raw === 'number' ? raw : parseInt(raw, 10);
    if (isFinite(v)) this.setField(field, v);
  }

  private buildTiles() {
    const d = this.d;
    const ratings = this.ratingFields.slice(0, 4).map(f => (this.isNfs4 ? (d[f] || [])[0] : d[f]) || 0);
    const status = this.statusFlags();
    this.tiles = [
      {
        label: 'Car',
        value: this.texts[2] || d['car_id'] || '–',
        sub: `${d['car_id'] || '?'} · serial ${d['serial_number']}`,
        hint: 'Text 2 (full name), the car list name; the car id; the serial number the game finds the car by',
        tone: 'accent',
      },
      {
        label: 'Class',
        value: this.className(),
        sub: status.length ? status.join(' · ') : 'regular car',
        hint: 'car_class and the car list flags',
      },
      {
        label: 'Ratings',
        value: ratings.join(' / '),
        sub: 'accel / top speed / handling / braking' + (this.isNfs4 ? ' (stock)' : ''),
        hint: `The front end's bars, out of ${RATING_MAX}`,
      },
      {
        id: 'interior_view_heading',
        label: 'Interior view',
        value: `${fmt(this.headingDegrees(), 1)}°`,
        edit: { value: d['interior_view_heading'] || 0, step: 1, min: 0, max: 0xffff, unit: 'texels' },
        sub: `${d['interior_view_heading']} of ${INTERIOR_TEXELS} texels`,
        hint: "Where the showroom's interior panorama starts (1280 texels = 360°)",
      },
    ];
    if (this.isNfs4) {
      const prices = this.levelPrices();
      this.tiles.push(
        {
          id: 'price',
          label: 'Price',
          value: `$${fmt(d['price'] || 0, 0)}`,
          edit: { value: d['price'] || 0, step: 1000, min: 0, unit: '$' },
          sub: `fully upgraded $${fmt(prices[prices.length - 1], 0)}`,
          hint: 'Career mode: the dealer price, then the upgrade levels 1..3',
        },
        {
          label: 'Engine',
          value: ENGINE_POSITIONS[d['engine_position']] ?? `${d['engine_position']}`,
          sub: `overall rating ${(d['overall_rating'] || [])[0] ?? '?'}`,
          hint: 'engine_position: where the engine point is (crash smoke, damage); overall_rating picks the opponents',
        },
      );
    } else {
      this.tiles.push({
        label: 'Driver seat',
        value: this.seatName(),
        hint: "driver_seat: the in-car camera's eye left, right or in the middle of the car",
      });
    }
    const bad = this.texts.filter(t => !isLatin1(t)).length;
    if (bad)
      this.tiles.push({ label: 'Texts', value: `${bad} invalid`, sub: 'characters beyond Latin-1', tone: 'warn' });
    if (this.d['format_version'] !== (this.isNfs4 ? 10 : 9)) {
      this.tiles.push({
        label: 'Format version',
        value: `${this.d['format_version']}`,
        sub: `${this.exeName} drops the car`,
        tone: 'warn',
      });
    }
  }

  onTileChange(e: { id: string; value: number }) {
    this.setValue([e.id], Math.round(e.value));
  }

  readonly fmt = fmt;
}
