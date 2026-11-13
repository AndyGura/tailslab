import { Directive, inject, OnInit } from '@angular/core';
import { CarSpecEditorBase, fmt } from '../player-car-physics.block-ui/car-specs';
import { MainService } from '../../../../services/main.service';
import {
  argbToCss,
  cssToArgb,
  dirOf,
  loadNfs5Cars,
  loadNfs5Parts,
  Nfs5CarInfo,
  nfs5PendingSelection,
  Nfs5PartInfo,
  resourcePath,
} from '../nfs5-car-physics.block-ui/nfs5-files';

export type Nfs5IdRow = { slot: number; id: number; label: string; missing: boolean };

// Base of the NFS5 career data editors (nfs5.fac, nfs5.trn): the car and part names of nfs5.car / nfs5.prt next to
// the file, id lists (a count + an array) edited as rows, colours, links that open those files at a record
@Directive()
export abstract class Nfs5CareerEditorBase extends CarSpecEditorBase implements OnInit {
  protected readonly main = inject(MainService);

  carsPath: string | null = null;
  cars: Map<number, Nfs5CarInfo> | null = null;
  partsPath: string | null = null;
  parts: Map<number, Nfs5PartInfo> | null = null;
  lookupNote = '';

  get hasUnsavedChanges(): boolean {
    return !!this.changes.hasUnsavedChanges$?.value;
  }

  override ngOnInit(): void {
    super.ngOnInit();
    this.loadLookups().then();
  }

  private async loadLookups() {
    if (!this.resourceId || !this.main?.api) return;
    const dir = dirOf(resourcePath(this.resourceId));
    const [cars, parts] = await Promise.all([loadNfs5Cars(this.main.api, dir), loadNfs5Parts(this.main.api, dir)]);
    this.carsPath = cars?.path || null;
    this.cars = cars?.byId || null;
    this.partsPath = parts?.path || null;
    this.parts = parts?.byId || null;
    const missing = [!cars && 'nfs5.car', !parts && 'nfs5.prt'].filter(x => !!x);
    this.lookupNote = missing.length ? `${missing.join(' and ')} not next to this file: shown by id only.` : '';
    if (this.resourceData) this.refresh();
    this.cdr.markForCheck();
  }

  carName(id: number): string {
    if (!id) return '–';
    const c = this.cars?.get(id);
    return c ? c.name : this.cars ? `#${id} (not in nfs5.car)` : `#${id}`;
  }

  partName(id: number): string {
    const p = this.parts?.get(id);
    return p ? p.label : this.parts ? '(not in nfs5.prt)' : '';
  }

  get carOptions(): Nfs5CarInfo[] {
    return this.cars ? [...this.cars.values()] : [];
  }

  get partOptions(): Nfs5PartInfo[] {
    return this.parts ? [...this.parts.values()].sort((a, b) => a.type - b.type || a.label.localeCompare(b.label)) : [];
  }

  idRows(ids: number[], count: number, name: (id: number) => string): Nfs5IdRow[] {
    return (ids || []).slice(0, Math.max(0, count)).map((id, slot) => {
      const label = name(id);
      return { slot, id, label, missing: label.includes('not in') };
    });
  }

  // removes slot `slot` of an id list (the ids after it move up, the freed last slot becomes 0)
  removeId(base: (string | number)[], list: string, countField: string, slot: number, record: any) {
    const ids = [...record[list]];
    ids.splice(slot, 1);
    ids.push(0);
    this.setValues([
      [[...base, list], ids],
      [[...base, countField], Math.max(0, (record[countField] || 0) - 1)],
    ]);
  }

  addId(base: (string | number)[], list: string, countField: string, id: number | null, record: any) {
    const n = record[countField] || 0;
    const ids = [...record[list]];
    if (!id || n >= ids.length) return;
    ids[n] = id;
    this.setValues([
      [[...base, list], ids],
      [[...base, countField], n + 1],
    ]);
  }

  async openCar(id: number) {
    if (!this.carsPath || this.hasUnsavedChanges) return;
    nfs5PendingSelection.carId = id;
    await this.main.api.openFile(this.carsPath, true);
  }

  async openPart(id: number) {
    if (!this.partsPath || this.hasUnsavedChanges) return;
    nfs5PendingSelection.partId = id;
    await this.main.api.openFile(this.partsPath, true);
  }

  readonly argbToCss = argbToCss;

  setColour(path: (string | number)[], css: string, old: number) {
    this.setValue(path, cssToArgb(css, old));
  }

  readonly fmt = fmt;
}
