import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';

export type RecordListItem = {
  // the record's index in the file (what `select` emits)
  index: number;
  label: string;
  // smaller second line
  sub?: string;
  // short tag at the right (an id, a type)
  tag?: string;
  // items of one group are listed under its header, in the order given
  group?: string;
  // dimmed (e.g. a record the game does not use)
  muted?: boolean;
};

export type RecordListGroup = { name: string; items: RecordListItem[] };

// A filterable list of the records of a database file (car database, parts...), for the bespoke editors that show one
// record at a time next to it. The filter matches the label, the sub line, the tag and the group, ignoring case
@Component({
  selector: 'app-record-list',
  templateUrl: './record-list.component.html',
  styleUrls: ['./record-list.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: false,
})
export class RecordListComponent {
  private _items: RecordListItem[] = [];
  groups: RecordListGroup[] = [];
  filter = '';

  @Input() set items(value: RecordListItem[] | null | undefined) {
    this._items = value || [];
    this.applyFilter();
  }

  get items(): RecordListItem[] {
    return this._items;
  }

  @Input() selected: number | null = null;
  @Input() placeholder = 'Filter';

  @Output() select = new EventEmitter<number>();

  get shownCount(): number {
    return this.groups.reduce((n, g) => n + g.items.length, 0);
  }

  onFilter(value: string) {
    this.filter = value;
    this.applyFilter();
  }

  applyFilter() {
    this.groups = filterRecordList(this._items, this.filter);
  }

  // up / down move the selection through the shown items
  onKey(event: KeyboardEvent) {
    if (event.key !== 'ArrowDown' && event.key !== 'ArrowUp') return;
    const shown = this.groups.flatMap(g => g.items);
    if (!shown.length) return;
    event.preventDefault();
    const at = shown.findIndex(i => i.index === this.selected);
    const next = at < 0 ? 0 : Math.max(0, Math.min(shown.length - 1, at + (event.key === 'ArrowDown' ? 1 : -1)));
    this.select.emit(shown[next].index);
  }

  trackItem(_: number, item: RecordListItem) {
    return item.index;
  }
}

// the items matching the filter, grouped in the order the groups first appear
export function filterRecordList(items: RecordListItem[], filter: string): RecordListGroup[] {
  const words = filter
    .toLowerCase()
    .split(/\s+/)
    .filter(w => !!w);
  const groups: RecordListGroup[] = [];
  const byName = new Map<string, RecordListGroup>();
  for (const item of items) {
    const text = [item.label, item.sub, item.tag, item.group].join(' ').toLowerCase();
    if (!words.every(w => text.includes(w))) continue;
    const name = item.group || '';
    let group = byName.get(name);
    if (!group) {
      group = { name, items: [] };
      byName.set(name, group);
      groups.push(group);
    }
    group.items.push(item);
  }
  return groups;
}
