import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BehaviorSubject, Subject } from 'rxjs';
import { EaFieldDescriptionsBlockUiComponent } from './ea-field-descriptions.block-ui.component';
import { MainService } from '../../../../services/main.service';
import { ChangesService } from '../../../../services/changes.service';
import {
  checkDesRow,
  DatLeaf,
  DesBody,
  desCheck,
  desNameProblem,
  desRows,
  desValue,
  desValueText,
  filterDesRows,
} from './ea-field-descriptions';

const ID = 'TEST.DES__data';

const le32 = (v: number) => [v & 0xff, (v >> 8) & 0xff, (v >> 16) & 0xff, (v >>> 24) & 0xff];
const garbage = (n: number) => ({ choice_index: 2, data: { $bytes: new Array(n).fill(0) } });

// 4 Fixed + 4 Integer + Chain (8 bytes: Array of 2) + 1 Char + 4 CArray + 3 Import = 24 bytes
const levers = (): DesBody => ({
  data: { $bytes: [...le32(-1), ...le32(0x18000)] },
  records: [
    {
      type: 'Array',
      name: 'Pair',
      data_size: 8,
      extra: { choice_index: 1, data: { dimensions: 1, size_1: 2, size_2: 2 } },
    },
  ],
});
const body = (): DesBody & { dat_block: string | null; dat_fields: DatLeaf[] } => ({
  data: {
    $bytes: [...le32(0x28000), ...le32(-7), ...le32(-1), ...le32(0x18000), 0x41, 0x41, 0x42, 0, 0, 1, 2, 3],
  },
  records: [
    { type: 'Fixed', name: 'mass', data_size: 4, extra: garbage(56) },
    { type: 'Integer', name: 'gears', data_size: 4, extra: garbage(56) },
    { type: 'Chain', name: 'Levers', data_size: 8, extra: { choice_index: 0, data: levers() } },
    { type: 'Char', name: 'letter', data_size: 1, extra: garbage(56) },
    {
      type: 'CArray',
      name: 'code',
      data_size: 4,
      extra: { choice_index: 1, data: { dimensions: 1, size_1: 4, size_2: 4 } },
    },
    { type: 'Import', name: 'table', data_size: 3, extra: { choice_index: 2, data: { $bytes: [0x41] } } },
  ],
  dat_block: 'TestBlock',
  dat_fields: [
    { path: 'mass', offset: 0, size: 4, kind: 'fixed', element_size: 4, description: 'Mass' },
    // the Integer described as a fixed: a mismatch
    { path: 'gears', offset: 4, size: 4, kind: 'fixed', element_size: 4 },
    { path: 'levers.pair', offset: 8, size: 8, kind: 'array', element_kind: 'fixed', element_size: 4 },
    { path: 'letter', offset: 16, size: 1, kind: 'int', element_size: 1 },
    { path: 'code', offset: 17, size: 4, kind: 'text', element_size: 1 },
    { path: 'table', offset: 21, size: 3, kind: 'bytes', element_size: 3 },
  ],
});

describe('ea-field-descriptions helpers', () => {
  it('flattens the records with their offsets and values', () => {
    const rows = desRows(body());
    expect(rows.map(r => [r.path, r.type, r.offset, r.size, r.depth])).toEqual([
      ['mass', 'Fixed', 0, 4, 0],
      ['gears', 'Integer', 4, 4, 0],
      ['Levers', 'Chain', 8, 8, 0],
      ['Levers/Pair', 'Array', 8, 8, 1],
      ['letter', 'Char', 16, 1, 0],
      ['code', 'CArray', 17, 4, 0],
      ['table', 'Import', 21, 3, 0],
    ]);
    expect(rows[0].value).toBe(2.5);
    expect(rows[1].value).toBe(-7);
    expect(rows[3].value).toEqual([-1, 0x18000]);
    expect(rows[3].shape).toEqual([1, 2, 2]);
    expect(rows[3].parentKey).toBe(rows[2].key);
    expect(rows[3].recordPath).toEqual(['records', 2, 'extra', 'data', 'records', 0]);
    expect(rows[4].value).toBe(0x41);
    expect(rows[5].value).toEqual([0x41, 0x42, 0, 0]);
    expect(rows[6].value).toEqual([1, 2, 3]);
  });

  it('reads the values as the .DES types do', () => {
    expect(desValue('Fixed', le32(-0x8000))).toBe(-0.5);
    expect(desValue('Integer', le32(0x7fffffff))).toBe(0x7fffffff);
    expect(desValue('Fixed', [1, 2])).toEqual([1, 2]);
    expect(desValue('Char', [7])).toBe(7);
  });

  it('checks the fields against the TailsLab layout as des_check', () => {
    const b = body();
    expect(desCheck(b, b.dat_fields)).toEqual(['gears: Integer does not fit gears (fixed)']);
    const layout: DatLeaf[] = [
      { path: 'a', offset: 0, size: 2, kind: 'int', element_size: 2 },
      { path: 'b', offset: 2, size: 4, kind: 'int', element_size: 4 },
    ];
    expect(checkDesRow({ path: 'x', type: 'Integer', offset: 0, size: 4 }, layout).problems).toEqual([
      'x: 0x0..0x4 cuts a, b',
    ]);
    expect(checkDesRow({ path: 'y', type: 'Integer', offset: 8, size: 4 }, layout).problems).toEqual([
      'y: no field at 0x8',
    ]);
    // inside one leaf, and a run of leaves
    expect(checkDesRow({ path: 'z', type: 'CArray', offset: 2, size: 2 }, layout).problems).toEqual([
      'z: CArray does not fit b (int)',
    ]);
    expect(checkDesRow({ path: 'w', type: 'Import', offset: 0, size: 6 }, layout).problems).toEqual([]);
  });

  it('shows values shortly with the full one in the tooltip', () => {
    const b = body();
    const rows = desRows(b);
    for (const r of rows) r.leaves = checkDesRow(r, b.dat_fields).leaves;
    expect(desValueText(rows[0]).text).toBe('2.5');
    expect(desValueText(rows[2]).text).toBe('group of 8 bytes');
    expect(desValueText(rows[3]).text).toBe('[-1, 98304]');
    expect(desValueText(rows[3]).title).toContain('as 16.16: -0.000015, 1.5');
    expect(desValueText(rows[4]).text).toBe("65 'A'");
    expect(desValueText(rows[5]).text).toBe('"AB"');
    expect(desValueText(rows[6]).text).toBe('3 bytes');
    expect(desValueText(rows[6]).title).toBe('01 02 03');
  });

  it('filters rows and keeps the chains holding them', () => {
    const b = body();
    const rows = desRows(b);
    expect(filterDesRows(rows, 'pair').map(r => r.path)).toEqual(['Levers', 'Levers/Pair']);
    expect(filterDesRows(rows, 'levers.pair').map(r => r.path)).toEqual([]);
    for (const r of rows) Object.assign(r, checkDesRow(r, b.dat_fields));
    expect(filterDesRows(rows, 'levers.pair').map(r => r.path)).toEqual(['Levers', 'Levers/Pair']);
    expect(filterDesRows(rows, '', true).map(r => r.path)).toEqual(['gears']);
  });

  it('refuses names the file cannot hold', () => {
    expect(desNameProblem('Grip')).toBeNull();
    expect(desNameProblem('ä')).toBeNull();
    expect(desNameProblem('x'.repeat(81))).toBe('At most 80 characters');
    expect(desNameProblem('€')).toContain('Latin-1');
  });
});

describe('EaFieldDescriptionsBlockUiComponent', () => {
  let fixture: ComponentFixture<EaFieldDescriptionsBlockUiComponent>;
  let component: EaFieldDescriptionsBlockUiComponent;
  let appendChanges: jasmine.Spy;

  beforeEach(async () => {
    appendChanges = jasmine.createSpy('appendChanges').and.returnValue(Promise.resolve());
    await TestBed.configureTestingModule({
      imports: [EaFieldDescriptionsBlockUiComponent],
      providers: [
        { provide: MainService, useValue: { focusedResourceId$: new BehaviorSubject(null) } },
        {
          provide: ChangesService,
          useValue: {
            change$: new Subject<string>(),
            appendChanges,
            subscribeComponent: () => {},
            unsubscribeComponent: () => {},
          },
        },
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
    fixture = TestBed.createComponent(EaFieldDescriptionsBlockUiComponent);
    component = fixture.componentInstance;
    component.resourceId = ID;
    component.resourceName = 'TEST.DES';
    component.resourceSchema = { block_class_mro: 'EaFieldDescriptions__DataBlock', fields: [] };
    component.resourceData = body();
    fixture.detectChanges();
  });

  it('summarizes the file', () => {
    expect(component.datBlock).toBe('TestBlock');
    expect(component.dataSize).toBe(24);
    expect(component.fieldCount).toBe(6);
    expect(component.chainCount).toBe(1);
    expect(component.problemCount).toBe(1);
    expect(component.uncoveredLeaves).toEqual([]);
    expect(component.rows.map(r => r.status)).toEqual(['ok', 'problem', 'chain', 'ok', 'ok', 'ok', 'ok']);
    expect(component.rows[3].offsetHex).toBe('0x008');
    expect(component.rows[0].leafTitle).toContain('Mass');
  });

  it('shows no status without a TailsLab block', () => {
    component.resourceData = { ...body(), dat_block: null, dat_fields: [] };
    expect(component.problemCount).toBe(0);
    expect(component.rows[0].status).toBe('none');
  });

  it('renames a record in a chain as one change', () => {
    const input = document.createElement('input');
    input.value = 'Pair of values';
    component.onNameInput(component.rows[3], input);
    expect(appendChanges).toHaveBeenCalledTimes(1);
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.op).toBe('set');
    expect(change.id).toBe(ID + '/records/2/extra/data/records/0/name');
    expect(change.oldValue).toBe('Pair');
    expect(change.newValue).toBe('Pair of values');
  });

  it('keeps a name the file cannot hold', () => {
    const input = document.createElement('input');
    input.value = '€uro';
    component.onNameInput(component.rows[0], input);
    expect(appendChanges).not.toHaveBeenCalled();
    expect(input.value).toBe('mass');
    expect(component.nameErrors[component.rows[0].key]).toContain('Latin-1');
  });

  it('filters the table', () => {
    component.onFilter('letter');
    expect(component.shownRows.map(r => r.path)).toEqual(['letter']);
    component.onFilter('');
    component.onProblemsOnly(true);
    expect(component.shownRows.map(r => r.path)).toEqual(['gears']);
  });
});
