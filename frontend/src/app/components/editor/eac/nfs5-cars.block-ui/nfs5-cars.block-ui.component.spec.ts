import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BehaviorSubject, Subject } from 'rxjs';
import { Nfs5CarsBlockUiComponent } from './nfs5-cars.block-ui.component';
import { nfs5CarValue, nfs5DealerPrice } from './nfs5-cars';
import { MainService } from '../../../../services/main.service';
import { ChangesService } from '../../../../services/changes.service';
import { argbToCss, cssToArgb } from '../nfs5-car-physics.block-ui/nfs5-files';
import { filterRecordList } from '../../common/record-list/record-list.component';

// the first record of nfs5.car, trimmed to what the editor reads
export const nfs5Car76 = (): { [key: string]: any } => ({
  id: 76,
  display_name: "'50 356 1100 Cabriolet",
  short_name: '356',
  kind: 0,
  class_string_id: 501,
  era_string_id: 521,
  first_year: 1950,
  last_year: 1954,
  availability: 1,
  price: 11000,
  value_by_year: [100, 100, 100, 95, 93, 88, ...Array.from({ length: 47 }, () => 80)],
  ratings: [30, 40, 56, 30, 41],
  num_upgrade_parts: 2,
  upgrade_parts: [40, 56, ...Array(68).fill(0)],
  num_stock_parts: 2,
  stock_parts: [629, 42, ...Array(18).fill(0)],
  num_paints: 1,
  paints: Array.from({ length: 20 }, (_, i) =>
    i
      ? { flag: 0, body: 0, accent_1: 0, accent_2: 0 }
      : { flag: 205, body: 0xfff3ffcc, accent_1: 0xffff0000, accent_2: 0xff000000 },
  ),
  num_interiors: 0,
  interiors: Array.from({ length: 20 }, () => ({ unused_0: 0, colour: 0, unused_8: 0, unused_c: 0 })),
});

describe('NFS5 car database helpers', () => {
  it('ages the dealer price from the first year and the value from 1948', () => {
    const car = nfs5Car76();
    // 1950: the first year, the price as it is
    expect(nfs5DealerPrice(car, 1950)).toBe(11000);
    // 1953: entry 1953 - 1950 = 3 (95%)
    expect(nfs5DealerPrice(car, 1953)).toBe(10450);
    // the value reads entry 1953 - 1948 = 5 (88%)
    expect(nfs5CarValue(car, 1953)).toBe(9680);
  });

  it('converts colours keeping the alpha', () => {
    expect(argbToCss(0xfff3ffcc)).toBe('#f3ffcc');
    expect(cssToArgb('#102030', 0x80ffffff)).toBe(0x80102030);
  });

  it('filters and groups record lists', () => {
    const groups = filterRecordList(
      [
        { index: 0, label: '356 Coupé', group: 'Classic' },
        { index: 1, label: '911 Turbo', group: 'Golden', tag: '#134' },
        { index: 2, label: '356 Speedster', group: 'Classic' },
      ],
      '356',
    );
    expect(groups.map(g => g.name)).toEqual(['Classic']);
    expect(groups[0].items.map(i => i.index)).toEqual([0, 2]);
    expect(filterRecordList([{ index: 1, label: 'x', tag: '#134' }], '#134')[0].items.length).toBe(1);
  });
});

describe('Nfs5CarsBlockUiComponent', () => {
  let fixture: ComponentFixture<Nfs5CarsBlockUiComponent>;
  let component: Nfs5CarsBlockUiComponent;
  let appendChanges: jasmine.Spy;

  beforeEach(async () => {
    appendChanges = jasmine.createSpy('appendChanges').and.returnValue(Promise.resolve());
    await TestBed.configureTestingModule({
      imports: [Nfs5CarsBlockUiComponent],
      providers: [
        {
          provide: MainService,
          useValue: {
            focusedResourceId$: new BehaviorSubject(null),
            api: { findFiles: () => Promise.resolve([]), retrieveValue: () => Promise.resolve(null) },
          },
        },
        {
          provide: ChangesService,
          useValue: {
            change$: new Subject<string>(),
            hasUnsavedChanges$: new BehaviorSubject(false),
            appendChanges,
            subscribeComponent: () => {},
            unsubscribeComponent: () => {},
          },
        },
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
    fixture = TestBed.createComponent(Nfs5CarsBlockUiComponent);
    component = fixture.componentInstance;
    component.resourceId = '/games/nfs5/FEData/Data/nfs5.car';
    component.resourceSchema = { block_class_mro: 'Nfs5Cars__DeclarativeCompoundBlock', fields: [] };
    component.resourceData = { cars: [nfs5Car76(), { ...nfs5Car76(), id: 186, kind: 1, display_name: 'Eden 1' }] };
    fixture.detectChanges();
  });

  it('lists the cars grouped by era and the traffic apart', () => {
    expect(component.items.map(i => i.group)).toEqual(['Classic era', 'Traffic']);
    expect(component.selected).toBe(0);
    expect(component.tiles[0].value).toBe('$11,000');
  });

  it('removes a part from a list as one change', () => {
    component.removePart('stock_parts', 0);
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.op).toBe('bundle');
    const [ids, count] = change.changes;
    expect(ids.id).toBe('/games/nfs5/FEData/Data/nfs5.car__cars/0/stock_parts');
    expect(ids.newValue.slice(0, 2)).toEqual([42, 0]);
    expect(count.newValue).toBe(1);
  });

  it('adds a paint as a copy of the last one', () => {
    component.addPaint('paints');
    const [paints, count] = appendChanges.calls.mostRecent().args[0].changes;
    expect(paints.newValue[1].body).toBe(0xfff3ffcc);
    expect(count.newValue).toBe(2);
  });

  it('writes a picked colour keeping the alpha', () => {
    component.onColour('paints', 0, 'body', '#000080');
    expect(appendChanges.calls.mostRecent().args[0].newValue).toBe(0xff000080);
  });

  it('duplicates a car with a new id', () => {
    component.duplicateCar();
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.op).toBe('array_insert');
    expect(change.value.id).toBe(187);
    expect(change.index).toBe(1);
  });
});
