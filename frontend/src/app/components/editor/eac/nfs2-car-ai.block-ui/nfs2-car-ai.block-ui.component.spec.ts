import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BehaviorSubject, Subject } from 'rxjs';
import { Nfs2CarAiBlockUiComponent } from './nfs2-car-ai.block-ui.component';
import { MainService } from '../../../../services/main.service';
import { ChangesService } from '../../../../services/changes.service';

const ID = 'CARDATA.VIV__data/children/40/item/data';

// cala.dat gearbox and handling, a flat 10 m/s² table up to 50 m/s
const levers = (grip: number) => ({
  acceleration_table: Array.from({ length: 112 }, (_, i) => (i < 50 ? 10 : 0)),
  grip,
  turn_rate: 0.8,
});
const ai = () => ({
  ai_shift_duration: 16,
  redline: 7500,
  gear_top_speeds: [10, 20, 30, 40, 0, 0, 0],
  simulation: levers(37),
  arcade: levers(60),
  speed_factor: 1,
  hi_handling_yaw: 10,
  low_handling_yaw: 3,
  handling_importance: 0.2,
  speed_factor_2: 1,
  lane_slack_prob: 40,
});

describe('Nfs2CarAiBlockUiComponent', () => {
  let fixture: ComponentFixture<Nfs2CarAiBlockUiComponent>;
  let component: Nfs2CarAiBlockUiComponent;
  let appendChanges: jasmine.Spy;

  beforeEach(async () => {
    appendChanges = jasmine.createSpy('appendChanges').and.returnValue(Promise.resolve());
    await TestBed.configureTestingModule({
      declarations: [Nfs2CarAiBlockUiComponent],
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
    fixture = TestBed.createComponent(Nfs2CarAiBlockUiComponent);
    component = fixture.componentInstance;
    component.resourceId = ID;
    component.resourceName = 'test.dat';
    component.resourceSchema = { block_class_mro: 'Nfs2CarAi__DataBlock', fields: [] };
    component.resourceData = ai();
    fixture.detectChanges();
  });

  it('summarizes the AI car', () => {
    const tile = (label: string) => component.tiles.find(t => t.label === label)!;
    expect(tile('Redline').value).toBe('7,500 rpm');
    expect(tile('Top gear').value).toBe('144 km/h');
    expect(tile('Top gear').sub).toBe('4-speed');
    expect(tile('Shift').value).toBe('0.5 s');
    expect(tile('Grip').value).toBe('37 m/s²');
    expect(tile('Grip').sub).toBe('arcade 60 m/s²');
    expect(component.tiles.find(t => t.label === 'Model')).toBeUndefined();
  });

  it('runs the speed with the shift pauses of the AI gearbox', () => {
    const run = component.run('simulation');
    // 27.78 m/s at 10 / 32 per step: 89 steps of drive, then the 16 steps of the shift above 10 and 20 m/s
    expect(run.to100).toBeCloseTo((89 + 2 * 16) / 32, 6);
    // the table is 0 from 50 m/s on
    expect(run.topSpeed).toBeGreaterThanOrEqual(50);
    expect(run.topSpeed).toBeLessThan(50 + 10 / 32 + 1e-9);
  });

  it('scales the tables of a known car model and stops at its top speed', () => {
    component.resourceName = 'cala.dat';
    expect(component.model?.index).toBe(10);
    // 0x1147a / 0x10000, floor of the 8.8 value
    expect(component.scaledTable('simulation')[0]).toBe(Math.floor(2560 * (0x1147a / 0x10000)) / 256);
    expect(component.scaledTable('arcade')[0]).toBe(Math.floor(2560 * (0x1051e / 0x10000)) / 256);
    const cala = { ...ai(), simulation: { ...levers(37), acceleration_table: new Array(112).fill(10) } };
    component.resourceData = cala;
    expect(component.run('simulation').topSpeed).toBeLessThan(0x50e666 / 0x10000 + 1);
    expect(component.tiles.find(t => t.label === 'Model')!.value).toBe('CALA');
  });

  it('sets the AI engine rpm from 3000 rpm to the redline within a gear', () => {
    expect(component.rpmAt(5, 0)).toBe(3750);
    expect(component.rpmAt(15, 1)).toBe(3000 + 0.5 * 4500);
    expect(component.gearSeries.length).toBe(4);
    expect(component.gearSeries[1].points[0]).toEqual({ x: 36, y: 3000 });
  });

  it('writes table edits in 8.8 steps as one change', () => {
    const points = component.tableSeries[1].points.map(p => ({ ...p }));
    points[4] = { ...points[4], y: 12.3456 };
    component.onTableChange({ seriesId: 'arcade', points, changed: [4] });
    expect(appendChanges).toHaveBeenCalledTimes(1);
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.id).toBe(ID + '/arcade/acceleration_table');
    expect(change.newValue[4]).toBe(Math.round(12.3456 * 256) / 256);
    expect(change.newValue[5]).toBe(10);
  });

  it('turns a dragged gear marker into its top speed in m/s', () => {
    component.onMarker({ markerId: 'gear-2', value: 117 });
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.id).toBe(ID + '/gear_top_speeds/2');
    expect(change.newValue).toBe(32.5);
  });

  it('adds and removes gears at the end', () => {
    component.addGear();
    expect(appendChanges.calls.mostRecent().args[0].id).toBe(ID + '/gear_top_speeds/4');
    expect(appendChanges.calls.mostRecent().args[0].newValue).toBe(50);
    component.removeGear();
    expect(appendChanges.calls.mostRecent().args[0].id).toBe(ID + '/gear_top_speeds/3');
    expect(appendChanges.calls.mostRecent().args[0].newValue).toBe(0);
  });

  it('edits the handling yaw and importance on the slowdown chart', () => {
    const points = component.handlingSeries[0].points.map(p => ({ ...p }));
    expect(points[2]).toEqual({ x: 10, y: 0.8 });
    points[2] = { x: 12, y: 0.75 };
    component.onHandlingChange({ seriesId: 'handling', points, changed: [2] });
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.op).toBe('bundle');
    expect(change.changes.map((c: any) => [c.id, c.newValue])).toEqual([
      [ID + '/hi_handling_yaw', 12],
      [ID + '/handling_importance', 0.25],
    ]);
  });

  it('grows the grip cap with the speed and edits the grip', () => {
    expect(component.gripAt('simulation', 100)).toBeCloseTo(37 * (1 + (100 * 0x62) / 0x10000), 9);
    const points = component.gripSeries[0].points.map(p => ({ ...p }));
    points[0] = { ...points[0], y: 41.5 };
    component.onGripChange({ seriesId: 'simulation', points, changed: [0] });
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.id).toBe(ID + '/simulation/grip');
    expect(change.newValue).toBe(41.5);
  });
});
