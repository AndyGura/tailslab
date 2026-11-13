import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { BlockSchema } from '../../types';
import { CarSpecEditorBase } from '../../eac/player-car-physics.block-ui/car-specs';
import { joinId } from '../../../../utils/join-id';
import { MatTooltip } from '@angular/material/tooltip';
import { BlockActionsComponent } from '../block-actions/block-actions.component';
import { MatIconButton, MatButton } from '@angular/material/button';
import { MatIcon } from '@angular/material/icon';
import { NgTemplateOutlet } from '@angular/common';
import { MatCheckbox } from '@angular/material/checkbox';
import { FormsModule } from '@angular/forms';
import {
  MatExpansionPanel,
  MatExpansionPanelHeader,
  MatExpansionPanelTitle,
  MatExpansionPanelDescription,
  MatExpansionPanelContent,
} from '@angular/material/expansion';

export type IniKeyKind = 'int' | 'float' | 'string';

export type IniKeyRow = {
  field: string;
  // the key the game looks up (`torqueCurve_%d` for an array)
  key: string;
  kind: IniKeyKind;
  unit: string;
  default: any;
  description: string;
  // the game never reads it
  notRead: boolean;
  // null: one value; else the keys of the items
  itemKeys: string[] | null;
};

export type IniSectionView = {
  field: string;
  // `[name]` of a single section, the pattern of a group
  title: string;
  description: string;
  group: boolean;
  rows: IniKeyRow[];
  newItem?: any;
};

// what an INI value block is, from its schema (IniInt / IniFloat / IniString, resources/eac/ini.py)
export const iniKind = (schema: BlockSchema | undefined): IniKeyKind => {
  const mro: string = schema?.block_class_mro || '';
  if (mro.includes('IniInt')) return 'int';
  if (mro.includes('IniFloat')) return 'float';
  return 'string';
};

export const isNotReadDescription = (description: string) => /^Not read\b/.test(description || '');

// the rows of a section schema (IniSection / IniGroupSection): every typed key, not `section` / `other_keys`
export const iniKeyRows = (sectionSchema: BlockSchema | undefined): IniKeyRow[] => {
  const rows: IniKeyRow[] = [];
  for (const f of sectionSchema?.fields || []) {
    if (f.name === 'other_keys' || f.name === 'section') continue;
    const schema = f.schema || {};
    const isArray = (schema.block_class_mro || '').includes('IniArray');
    const valueSchema = isArray ? schema.child_schema : schema;
    const keyFormat: string = schema.ini_key || f.name;
    let itemKeys: string[] | null = null;
    if (isArray) {
      itemKeys = [];
      const first = keyFormat.includes('%d') ? (schema.first_index ?? 0) : 0;
      for (let i = 0; i < (schema.length || 0); i++) itemKeys.push(keyFormat.replace('%d', String(i + first)));
    }
    rows.push({
      field: f.name,
      key: isArray ? keyFormat : valueSchema?.ini_key || f.name,
      kind: iniKind(valueSchema),
      unit: valueSchema?.ini_unit || '',
      default: valueSchema?.ini_default,
      description: f.description || '',
      notRead: isNotReadDescription(f.description || ''),
      itemKeys,
    });
  }
  return rows;
};

// an input's text as the value of a key: '' = the key is missing (null)
export const parseIniInput = (raw: string, kind: IniKeyKind): any => {
  if (kind === 'string') return raw;
  if (raw.trim() === '') return null;
  const v = parseFloat(raw);
  if (!isFinite(v)) return undefined;
  return kind === 'int' ? Math.round(v) : v;
};

// Generic editor of typed INI files (IniFile, resources/eac/ini.py; NFS HP2 PC car spec files): every section with
// its keys, their values, units, the game's defaults and descriptions; numbered section groups with add / remove;
// keys and sections the definition does not name. An empty input removes the key from the file
@Component({
  selector: 'app-ini-file-block-ui',
  templateUrl: './ini-file.block-ui.component.html',
  styleUrls: ['./ini-file.block-ui.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    MatTooltip,
    BlockActionsComponent,
    MatIconButton,
    MatIcon,
    NgTemplateOutlet,
    MatButton,
    MatCheckbox,
    FormsModule,
    MatExpansionPanel,
    MatExpansionPanelHeader,
    MatExpansionPanelTitle,
    MatExpansionPanelDescription,
    MatExpansionPanelContent,
  ],
})
export class IniFileBlockUiComponent extends CarSpecEditorBase {
  private _sectionWhitelist?: string[];

  // only these sections (field names); all when unset
  @Input() set sectionWhitelist(value: string[] | undefined) {
    this._sectionWhitelist = value;
    if (this.resourceData) this.refresh();
  }

  get sectionWhitelist(): string[] | undefined {
    return this._sectionWhitelist;
  }
  // embedded in another editor: no title, no description
  @Input() embedded = false;

  sections: IniSectionView[] = [];
  showNotRead = true;
  onlyInFile = false;
  readonly joinId = joinId;

  protected refresh() {
    const schema = this.resourceSchema;
    const sections: IniSectionView[] = [];
    for (const f of schema?.fields || []) {
      if (f.usage && f.usage !== 'everywhere' && !String(f.usage).includes('ui')) continue;
      if (f.name === 'other_sections' || f.name === 'source_text') continue;
      if (this.sectionWhitelist && !this.sectionWhitelist.includes(f.name)) continue;
      const mro: string = f.schema?.block_class_mro || '';
      if (mro.includes('IniSectionGroup')) {
        sections.push({
          field: f.name,
          title: f.schema.ini_section_pattern || f.name,
          description: f.description || '',
          group: true,
          rows: iniKeyRows(f.schema.child_schema),
        });
      } else if (mro.includes('IniSection')) {
        sections.push({
          field: f.name,
          title: `[${f.schema.ini_section || f.name}]`,
          description: f.description || '',
          group: false,
          rows: iniKeyRows(f.schema),
        });
      }
    }
    this.sections = sections;
  }

  visibleRows(section: IniSectionView, values: any): IniKeyRow[] {
    return section.rows.filter(r => {
      if (r.notRead && !this.showNotRead) return false;
      if (this.onlyInFile) {
        const v = values?.[r.field];
        return Array.isArray(v) ? v.some(x => x !== null && x !== undefined) : v !== null && v !== undefined;
      }
      return true;
    });
  }

  keysInFile(values: any): number {
    if (!values) return 0;
    let n = 0;
    for (const [k, v] of Object.entries(values)) {
      if (k === 'other_keys' || k === 'section') continue;
      if (Array.isArray(v)) n += v.filter(x => x !== null && x !== undefined).length;
      else if (v !== null && v !== undefined) n++;
    }
    return n + (values.other_keys?.length || 0);
  }

  display(value: any): string {
    return value === null || value === undefined ? '' : String(value);
  }

  placeholder(row: IniKeyRow): string {
    return row.default === null || row.default === undefined ? 'missing' : `missing: ${row.default}`;
  }

  onKeyInput(path: (string | number)[], raw: string, kind: IniKeyKind) {
    const value = parseIniInput(raw, kind);
    if (value === undefined) return;
    this.setValue(path, value);
  }

  removeKey(path: (string | number)[]) {
    this.setValue(path, null);
  }

  private insert(path: (string | number)[], index: number, value: any) {
    if (!this.resourceId || this.disabled) return;
    this.emitNewChange({ op: 'array_insert', id: joinId(this.resourceId, ...path), index, value });
  }

  private remove(path: (string | number)[], index: number, oldValue: any) {
    if (!this.resourceId || this.disabled) return;
    this.emitNewChange({ op: 'array_remove', id: joinId(this.resourceId, ...path), index, oldValue });
  }

  addGroupItem(section: IniSectionView) {
    const items: any[] = this.resourceData?.[section.field] || [];
    const item: any = { section: this.nextSectionName(section, items), other_keys: [] };
    for (const r of section.rows) {
      item[r.field] = r.itemKeys ? r.itemKeys.map(() => r.default ?? null) : (r.default ?? null);
    }
    this.insert([section.field], items.length, item);
  }

  // the next number after the items' names (`skin00` -> `skin01`), keeping the digits' width
  nextSectionName(section: IniSectionView, items: any[]): string {
    const last: string = items.length ? items[items.length - 1].section || '' : '';
    const match = /^(.*?)(\d+)$/.exec(last);
    if (match) return match[1] + String(parseInt(match[2], 10) + 1).padStart(match[2].length, '0');
    return `${section.field}${items.length}`;
  }

  removeGroupItem(section: IniSectionView, index: number) {
    this.remove([section.field], index, this.resourceData?.[section.field]?.[index]);
  }

  addOtherKey(path: (string | number)[]) {
    let list: any = this.resourceData;
    for (const p of path) list = list?.[p];
    this.insert(path, (list || []).length, { key: 'NewKey', value: '' });
  }

  removeOtherKey(path: (string | number)[], index: number) {
    let list: any = this.resourceData;
    for (const p of path) list = list?.[p];
    this.remove(path, index, list?.[index]);
  }

  addOtherSection() {
    const list: any[] = this.resourceData?.['other_sections'] || [];
    this.insert(['other_sections'], list.length, { section: 'new_section', keys: [] });
  }

  removeOtherSection(index: number) {
    this.remove(['other_sections'], index, this.resourceData?.['other_sections']?.[index]);
  }

  trackIndex = (i: number) => i;
}
