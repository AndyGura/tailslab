import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BehaviorSubject, Subject } from 'rxjs';
import { Nfs5CarPartsBlockUiComponent } from './nfs5-car-parts.block-ui.component';
import { MainService } from '../../../../services/main.service';
import { ChangesService } from '../../../../services/changes.service';
import { nfs5PartEffects, nfs5PartPrice, nfs5PartRepairCost, nfs5PartUsedValue, nfs5TyreFactors } from './nfs5-parts';

const part = (patch: { [k: string]: any } = {}) => ({
  id: 40,
  type: 2,
  name: 'Brakes',
  family: '356',
  year: 1950,
  mass: 0,
  top_speed_divisor: 0,
  sort_key: 1000,
  durability: 90,
  value_a: 1.5,
  value_b: 0,
  drive_type: 0,
  num_geometry_entries: 0,
  geometry_entries: Array.from({ length: 8 }, () => ({ a: 0, b: 0, value: 0 })),
  torque_curve: Array(21).fill(0),
  gear_ratios: Array(8).fill(0),
  damage: 0,
  ...patch,
});

describe('NFS5 part helpers', () => {
  it('inflates the price by the yearly table', () => {
    expect(nfs5PartPrice(part(), 1950)).toBe(1000);
    // 1 + 2 + 2 = 5%
    expect(nfs5PartPrice(part(), 1953)).toBe(1050);
  });

  it('values a used part and its repair by the damage', () => {
    expect(nfs5PartUsedValue(part(), 1950, 0)).toBe(800);
    expect(nfs5PartUsedValue(part(), 1950, 10)).toBe(600);
    expect(nfs5PartUsedValue(part(), 1950, 50)).toBe(0);
    expect(nfs5PartRepairCost(part(), 1950, 10)).toBe(200);
  });

  it('describes the effects as the race applies them', () => {
    const brakes = nfs5PartEffects(part());
    expect(brakes[0]).toEqual(jasmine.objectContaining({ target: 'Brake force', value: '× 1.125' }));
    const tyres = nfs5TyreFactors(1.9, 1, 1);
    expect(tyres.grip).toBeCloseTo(1, 9);
    expect(tyres.frontWeight).toBeCloseTo(1, 9);
    const supercharger = nfs5PartEffects(part({ type: 1, name: 'Supercharger' }));
    expect(supercharger.find(e => e.target === 'Aspiration')!.value).toBe('unchanged');
  });
});

describe('Nfs5CarPartsBlockUiComponent', () => {
  let fixture: ComponentFixture<Nfs5CarPartsBlockUiComponent>;
  let component: Nfs5CarPartsBlockUiComponent;
  let appendChanges: jasmine.Spy;

  beforeEach(async () => {
    appendChanges = jasmine.createSpy('appendChanges').and.returnValue(Promise.resolve());
    await TestBed.configureTestingModule({
      imports: [Nfs5CarPartsBlockUiComponent],
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
    fixture = TestBed.createComponent(Nfs5CarPartsBlockUiComponent);
    component = fixture.componentInstance;
    component.resourceId = '/games/nfs5/FEData/Data/nfs5.prt';
    component.resourceSchema = { block_class_mro: 'Nfs5CarParts__DeclarativeCompoundBlock', fields: [] };
    component.resourceData = { parts: [part(), part({ id: 41, type: 9, name: '', drive_type: 2 })] };
    fixture.detectChanges();
  });

  it('groups the parts by type and names unnamed tyres', () => {
    expect(component.items.map(i => i.group)).toEqual(['Brakes', 'Tyres']);
    expect(component.items[1].label).toBe('Tyres (Race)');
  });

  it('edits the selected part', () => {
    component.onTileChange({ id: 'sort_key', value: 1200 });
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.id).toBe('/games/nfs5/FEData/Data/nfs5.prt__parts/0/sort_key');
    expect(change.newValue).toBe(1200);
  });

  it('prices the part by year', () => {
    const newPrices = component.priceSeries.find(s => s.id === 'new')!;
    expect(newPrices.points[0]).toEqual({ x: 1950, y: 1000 });
  });

  it('duplicates a part with a new id after it', () => {
    component.duplicatePart();
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.op).toBe('array_insert');
    expect(change.value.id).toBe(42);
  });
});
