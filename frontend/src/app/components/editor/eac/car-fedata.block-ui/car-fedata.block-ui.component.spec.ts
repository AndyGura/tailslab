import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BehaviorSubject, Subject } from 'rxjs';
import { CarFeDataBlockUiComponent, classNames, isLatin1 } from './car-fedata.block-ui.component';
import { MainService } from '../../../../services/main.service';
import { ChangesService } from '../../../../services/changes.service';

// resources/eac/fedata.py text names (sections only matter here)
const textNames = (nfs4: boolean) => {
  const names: { name: string; label: string; section: string }[] = [
    { name: 'make', label: 'Make', section: 'Names' },
    { name: 'model', label: 'Model', section: 'Names' },
    { name: 'full_name', label: 'Full name', section: 'Names' },
    ...['price', 'status', 'weight', 'weight_distribution', 'length', 'width', 'height'].map(n => ({
      name: n,
      label: n,
      section: 'General',
    })),
    ...['engine_type', 'displacement', 'horsepower', 'torque', 'max_engine_speed', 'brakes', 'tires'].map(n => ({
      name: n,
      label: n,
      section: 'Mechanical',
    })),
  ];
  if (nfs4) names.push({ name: 'special', label: 'Special', section: 'Mechanical' });
  names.push(
    ...['top_speed', 'accel_0_60', 'accel_0_100'].map(n => ({ name: n, label: n, section: 'Performance' })),
    ...['transmission_type', 'gearbox'].map(n => ({ name: n, label: n, section: 'Transmission' })),
    { name: 'history_title', label: 'History title', section: 'History' },
    ...[1, 2, 3, 4, 5, 6, 7].map(i => ({ name: `history_${i}`, label: `History ${i}`, section: 'History' })),
    ...[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(i => ({ name: `color_${i}`, label: `Colour ${i}`, section: 'Colours' })),
  );
  return names;
};

// NFS3 Diab fedata.eng as parsed (Nfs3CarFeData)
const nfs3Data = () => ({
  car_id: 'Diab',
  format_version: 9,
  bonus: 0,
  filter_flag: 1,
  car_class: 0,
  game: 3,
  own_art: 0,
  police: 0,
  driver_seat: 0,
  unused_0x13: 0,
  shared_car: 1,
  interior_view_heading: 311,
  serial_number: 16,
  guid_data2: 0,
  guid_data3: 0,
  guid_data4: [0, 0, 0, 0, 0, 0, 0, 0],
  acceleration: 18,
  top_speed: 17,
  handling: 13,
  braking: 15,
  overall_rating: 5,
  texts: [
    'Lamborghini',
    'Diablo SV',
    'Lamborghini Diablo SV',
    '$195,900 usd',
    'production',
    '3575 lbs',
    '40% / 60%',
    '178.8 in.',
    '81.6 in.',
    '44.2 in.',
    '48 valve, V12',
    '5707 cc',
    '529 bhp @ 7100 rpm',
    '443 lb-ft @ 5500 rpm',
    '7300 rpm',
    '14.2 in. / 13.4 in.',
    '245/40ZR17 / 335/35ZR18',
    '208 mph',
    '3.8 sec',
    '8.0 sec',
    'manual',
    '5 speed',
    'Lamborghini',
    'company founded - 1962',
    '350 GTV - 1963',
    'Miura P400 - 1967',
    'Countach LP400 - 1973',
    'Jalpa - 1982',
    'Diablo - 1990',
    'Diablo SV - 1997',
    'Giallo',
    'Blu Le Mans',
    'Bianco',
    'Rosso Imola L.D.',
    'White',
    'White',
    'White',
    'White',
    'White',
    'White',
  ],
});

// NFS4 B911 fedata.eng (Nfs4CarFeData), the fields the editor reads
const nfs4Data = () => ({
  game: 4,
  car_id: 'B911',
  serial_number: 42,
  flags: { bonus: true, filter_flag: true, police: false, no_upgrades: true, fixed_color: true },
  car_class: 1,
  interior_view_heading: 437,
  format_version: 10,
  acceleration: [17, 17, 17, 17],
  top_speed: [19, 19, 19, 19],
  handling: [19, 19, 19, 19],
  braking: [14, 14, 14, 14],
  overall_rating: [18, 18, 18, 18],
  price: 200000,
  upgrade_prices: [30000, 60000, 100000],
  driver_seat: 0,
  engine_position: 2,
  texts: ['Porsche', 'Bonus 911 Turbo', 'Bonus Porsche', ...Array(38).fill('')],
});

describe('CarFeDataBlockUiComponent', () => {
  let fixture: ComponentFixture<CarFeDataBlockUiComponent>;
  let component: CarFeDataBlockUiComponent;
  let appendChanges: jasmine.Spy;

  const setup = (nfs4: boolean) => {
    component.resourceId = 'car.viv__data/children/7/item/data';
    component.resourceSchema = {
      block_class_mro: (nfs4 ? 'Nfs4CarFeData' : 'Nfs3CarFeData') + '__DeclarativeCompoundBlock__DataBlock',
      fields: [{ name: 'texts', schema: { text_names: textNames(nfs4) } as any, description: '' } as any],
    };
    component.resourceData = nfs4 ? nfs4Data() : nfs3Data();
    fixture.detectChanges();
  };

  beforeEach(async () => {
    appendChanges = jasmine.createSpy('appendChanges').and.returnValue(Promise.resolve());
    await TestBed.configureTestingModule({
      declarations: [CarFeDataBlockUiComponent],
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
    fixture = TestBed.createComponent(CarFeDataBlockUiComponent);
    component = fixture.componentInstance;
  });

  it('lays out the NFS3 spec sheet as the showroom', () => {
    setup(false);
    expect(component.isNfs4).toBeFalse();
    expect(component.names.map(r => r.value)).toEqual(['Lamborghini', 'Diablo SV', 'Lamborghini Diablo SV']);
    expect(component.sheet.map(s => s.title)).toEqual(['General', 'Performance', 'Transmission', 'Mechanical']);
    expect(component.sheet[0].rows[0].value).toBe('$195,900 usd');
    expect(component.sheet[1].rows.map(r => r.index)).toEqual([17, 18, 19]);
    expect(component.history.length).toBe(8);
    expect(component.colors[0].value).toBe('Giallo');
    const tile = (label: string) => component.tiles.find(t => t.label === label)!;
    expect(tile('Car').value).toBe('Lamborghini Diablo SV');
    expect(tile('Class').value).toBe('A');
    expect(tile('Ratings').value).toBe('18 / 17 / 13 / 15');
    expect(tile('Driver seat').value).toBe('Left (-0.4 m)');
    expect(component.headingDegrees()).toBeCloseTo((311 * 360) / 1280, 6);
  });

  it('puts NFS4 special under Mechanical and its texts one index on', () => {
    setup(true);
    const mechanical = component.sheet.find(s => s.title === 'Mechanical')!;
    expect(mechanical.rows.map(r => r.name).pop()).toBe('special');
    expect(component.sheet.find(s => s.title === 'Performance')!.rows[0].index).toBe(18);
    expect(component.colors[0].index).toBe(31);
    expect(component.levelPrices()).toEqual([200000, 230000, 290000, 390000]);
    expect(component.statusFlags()).toEqual(['bonus', 'no upgrades', 'fixed colour']);
    expect(component.ratingSeries.length).toBe(5);
    expect(component.ratingSeries[4].points.map(p => p.y)).toEqual([18, 18, 18, 18]);
    expect(component.tiles.find(t => t.label === 'Engine')!.value).toBe('Rear');
  });

  it('edits texts, refusing what the game cannot show', () => {
    setup(false);
    component.setText(3, 'n/a');
    expect(appendChanges.calls.mostRecent().args[0].id).toBe('car.viv__data/children/7/item/data/texts/3');
    expect(appendChanges.calls.mostRecent().args[0].newValue).toBe('n/a');
    appendChanges.calls.reset();
    component.setText(4, 'race 🏁');
    expect(appendChanges).not.toHaveBeenCalled();
    component.setText(42, 'Rosso');
    const texts = appendChanges.calls.mostRecent().args[0].newValue as string[];
    expect(texts.length).toBe(43);
    expect(texts[40]).toBe('');
    expect(texts[42]).toBe('Rosso');
  });

  it('writes edited ratings as one change, rounded to bytes', () => {
    setup(false);
    component.onRatingsChange({
      seriesId: 'ratings',
      points: [18, 20, 13.4, 15].map((y, x) => ({ x, y })),
      changed: [1, 2],
    });
    const change = appendChanges.calls.mostRecent().args[0];
    expect([change.id.split('/').pop(), change.newValue]).toEqual(['top_speed', 20]);
    component.onRatingsChange({ seriesId: 'ratings', points: [19, 20, 14, 16].map((y, x) => ({ x, y })), changed: [] });
    expect(appendChanges.calls.mostRecent().args[0].op).toBe('bundle');
  });

  it('knows the class names and Latin-1', () => {
    expect(classNames(false)[255]).toBe('None');
    expect(classNames(true)[0]).toBe('Race (AA)');
    expect(isLatin1('Niña Weiß')).toBeTrue();
    expect(isLatin1('€')).toBeFalse();
  });
});
