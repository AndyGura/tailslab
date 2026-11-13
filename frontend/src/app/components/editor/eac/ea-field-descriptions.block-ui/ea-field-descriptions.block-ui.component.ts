import { ChangeDetectionStrategy, Component } from '@angular/core';
import { CarSpecEditorBase } from '../player-car-physics.block-ui/car-specs';
import {
  checkDesRows,
  DatLeaf,
  DesBody,
  desBytes,
  desNameProblem,
  desRows,
  desValueText,
  DesRow,
  filterDesRows,
} from './ea-field-descriptions';

export type DesRowView = DesRow & {
  offsetHex: string;
  valueText: string;
  valueTitle: string;
  leafText: string;
  leafTitle: string;
  // ok: fits the TailsLab field(s); problem: see `problems`; none: no TailsLab block to compare with; chain: a group
  status: 'ok' | 'problem' | 'none' | 'chain';
};

// Viewer of EA's field description files (`.DES`, EaFieldDescriptions): every field the developers described, groups
// (`Chain`) as indented rows, with its offset in the described data, its value in the file's copy of the data, the
// TailsLab field(s) at that offset and whether they agree (`des_check` of resources/eac/field_descriptions.py). Names
// can be edited in place
@Component({
  selector: 'app-ea-field-descriptions-block-ui',
  templateUrl: './ea-field-descriptions.block-ui.component.html',
  styleUrls: [
    '../player-car-physics.block-ui/player-car-physics.block-ui.component.scss',
    './ea-field-descriptions.block-ui.component.scss',
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: false,
})
export class EaFieldDescriptionsBlockUiComponent extends CarSpecEditorBase {
  selectedTab = 0;

  rows: DesRowView[] = [];
  shownRows: DesRowView[] = [];
  datBlock: string | null = null;
  datFields: DatLeaf[] = [];
  dataSize = 0;
  fieldCount = 0;
  chainCount = 0;
  problemCount = 0;
  // fields whose bytes no TailsLab leaf covers, and leaves no field covers
  uncoveredLeaves: DatLeaf[] = [];

  filterText = '';
  problemsOnly = false;
  nameErrors: { [key: string]: string } = {};

  protected refresh(): void {
    const d = this.d as DesBody & { dat_block?: string | null; dat_fields?: DatLeaf[] };
    if (!d || !Array.isArray(d.records)) return;
    this.datBlock = d.dat_block ?? null;
    this.datFields = Array.isArray(d.dat_fields) ? d.dat_fields : [];
    this.dataSize = desBytes(d.data).length;
    const rows = checkDesRows(desRows(d), this.datFields);
    this.rows = rows.map(r => this.view(r));
    this.fieldCount = rows.filter(r => !r.isChain).length;
    this.chainCount = rows.length - this.fieldCount;
    this.problemCount = rows.filter(r => r.problems.length).length;
    const covered = rows.filter(r => !r.isChain);
    this.uncoveredLeaves = this.datFields.filter(
      l => !covered.some(r => r.offset < l.offset + l.size && l.offset < r.offset + r.size),
    );
    this.applyFilter();
  }

  private view(r: DesRow): DesRowView {
    const { text, title } = desValueText(r);
    const status = r.isChain ? 'chain' : r.problems.length ? 'problem' : this.datFields.length ? 'ok' : 'none';
    return {
      ...r,
      offsetHex: '0x' + r.offset.toString(16).padStart(3, '0'),
      valueText: text,
      valueTitle: title,
      leafText: r.isChain ? '' : r.leaves.map(l => l.path).join(', '),
      leafTitle: r.isChain
        ? ''
        : r.leaves
            .map(
              l =>
                `${l.path} (${l.element_kind ?? l.kind}, 0x${l.offset.toString(16)}, ${l.size} bytes)` +
                (l.description ? `: ${l.description}` : ''),
            )
            .join('\n\n'),
      status,
    };
  }

  applyFilter() {
    this.shownRows = filterDesRows(this.rows, this.filterText, this.problemsOnly) as DesRowView[];
  }

  onFilter(text: string) {
    this.filterText = text;
    this.applyFilter();
  }

  onProblemsOnly(value: boolean) {
    this.problemsOnly = value;
    this.applyFilter();
  }

  // one undoable change of the record's name
  onNameInput(row: DesRowView, input: HTMLInputElement) {
    const name = input.value;
    const problem = desNameProblem(name);
    if (problem) {
      this.nameErrors = { ...this.nameErrors, [row.key]: problem };
      input.value = row.name;
      return;
    }
    if (this.nameErrors[row.key]) {
      const { [row.key]: _, ...rest } = this.nameErrors;
      this.nameErrors = rest;
    }
    if (name !== row.name) this.setValue([...row.recordPath, 'name'], name);
  }

  shapeText(row: DesRow): string {
    return row.shape ? `${row.shape[0]} × ${row.shape[1]} × ${row.shape[2]}` : '';
  }

  statusTitle(row: DesRowView): string {
    if (row.status === 'problem') return row.problems.join('\n');
    if (row.status === 'ok') return `Fits ${row.leafText}`;
    if (row.status === 'none') return 'No TailsLab block of the described data to compare with';
    return '';
  }

  get uncoveredText(): string {
    return this.uncoveredLeaves.map(l => l.path).join(', ');
  }
}
