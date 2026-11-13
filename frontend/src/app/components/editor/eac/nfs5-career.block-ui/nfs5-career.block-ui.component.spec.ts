import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BehaviorSubject, Subject } from 'rxjs';
import { Nfs5FactoryMissionsBlockUiComponent, nfs5MissionRules } from './nfs5-factory-missions.block-ui.component';
import { Nfs5TournamentsBlockUiComponent } from './nfs5-tournaments.block-ui.component';
import { MainService } from '../../../../services/main.service';
import { ChangesService } from '../../../../services/changes.service';

const providers = (appendChanges: jasmine.Spy) => [
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
];

const mission = () => ({
  level: 1,
  mission_number: 1,
  map_picture: '1m01',
  car_id: 161,
  track_id: 14,
  laps: 2,
  direction: 0,
  part_count: 2,
  part_ids: [120, 121, ...Array(20).fill(0)],
  body_colours: [0xffff0000, 0, 0],
  interior_colours: [0xff000000, 0, 0],
  time_limit_on: 1,
  time_limit: 27,
  damage_limit_on: 0,
  cones_on: 1,
  cone_mode: 0,
  cone_limit: 0,
  min_rank_on: 0,
  opponents: Array.from({ length: 5 }, () => ({ personality_id: 0, car_id: 0 })),
});

describe('Nfs5FactoryMissionsBlockUiComponent', () => {
  let component: Nfs5FactoryMissionsBlockUiComponent;
  let appendChanges: jasmine.Spy;

  beforeEach(async () => {
    appendChanges = jasmine.createSpy('appendChanges').and.returnValue(Promise.resolve());
    await TestBed.configureTestingModule({
      imports: [Nfs5FactoryMissionsBlockUiComponent],
      providers: providers(appendChanges),
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
    const fixture: ComponentFixture<Nfs5FactoryMissionsBlockUiComponent> = TestBed.createComponent(
      Nfs5FactoryMissionsBlockUiComponent,
    );
    component = fixture.componentInstance;
    component.resourceId = '/g/nfs5.fac';
    component.resourceSchema = { block_class_mro: 'Nfs5FactoryMissions__DeclarativeCompoundBlock', fields: [] };
    component.resourceData = { missions: [mission()] };
    fixture.detectChanges();
  });

  it('states the rules as the race judges them', () => {
    expect(nfs5MissionRules(mission())).toEqual(['within 27 s', 'at most 0 cones hit']);
    expect(nfs5MissionRules({ ...mission(), min_rank_on: 1, min_rank: 1 })).toEqual(['finish 1 or better']);
  });

  it('adds a part to the car', () => {
    component.newPartId = 300;
    component.addPart();
    const [ids, count] = appendChanges.calls.mostRecent().args[0].changes;
    expect(ids.id).toBe('/g/nfs5.fac__missions/0/part_ids');
    expect(ids.newValue.slice(0, 3)).toEqual([120, 121, 300]);
    expect(count.newValue).toBe(3);
  });
});

describe('Nfs5TournamentsBlockUiComponent', () => {
  let component: Nfs5TournamentsBlockUiComponent;
  let appendChanges: jasmine.Spy;

  beforeEach(async () => {
    appendChanges = jasmine.createSpy('appendChanges').and.returnValue(Promise.resolve());
    await TestBed.configureTestingModule({
      imports: [Nfs5TournamentsBlockUiComponent],
      providers: providers(appendChanges),
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
    const fixture = TestBed.createComponent(Nfs5TournamentsBlockUiComponent);
    component = fixture.componentInstance;
    component.resourceId = '/g/nfs5.trn';
    component.resourceSchema = { block_class_mro: 'Nfs5Tournaments__DeclarativeCompoundBlock', fields: [] };
    component.resourceData = {
      tournaments: [
        {
          id: 1,
          era: 521,
          kind: 0,
          race_count: 1,
          entry_fee: 0,
          prize_money: [5000, 4000, 3000, 2500, 2000, 1500, 1000, 500],
          allowed_car_count: 1,
          allowed_cars: [76, ...Array(84).fill(0)],
          opponent_count: 1,
          opponents: [
            {
              personality_id: 1,
              car_id: 76,
              part_count: 0,
              part_ids: Array(22).fill(0),
              body_colours: [0, 0, 0],
              interior_colours: [0, 0, 0],
            },
          ],
          races: [{ track_id: 14, laps: 2, prize: Array(8).fill(0) }],
        },
      ],
    };
    fixture.detectChanges();
  });

  it('lists the tournaments by era', () => {
    expect(component.items[0].group).toBe('Classic era (1950-69)');
    expect(component.races.length).toBe(1);
  });

  it('writes edited prize bars', () => {
    const points = component.prizeSeries[0].points.map((p, i) => (i === 0 ? { x: 0, y: 6000.4 } : p));
    component.onPrizeChange({ seriesId: 'prize', points, changed: [0] });
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.id).toBe('/g/nfs5.trn__tournaments/0/prize_money');
    expect(change.newValue[0]).toBe(6000);
  });

  it('removes an allowed car', () => {
    component.removeAllowed(0);
    const [ids, count] = appendChanges.calls.mostRecent().args[0].changes;
    expect(ids.newValue[0]).toBe(0);
    expect(count.newValue).toBe(0);
  });
});
