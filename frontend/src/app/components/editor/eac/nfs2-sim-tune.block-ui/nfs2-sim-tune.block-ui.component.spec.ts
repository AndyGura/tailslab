import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BehaviorSubject, Subject } from 'rxjs';
import { Nfs2SimTuneBlockUiComponent } from './nfs2-sim-tune.block-ui.component';
import { MainService } from '../../../../services/main.service';
import { ChangesService } from '../../../../services/changes.service';
import {
  acosDeg,
  elasticityFor,
  glueBoostAt,
  glueOrderProblems,
  glueSteps,
  reboundCurve,
  reboundSpeed,
  SimTuneRecord,
  smoothingResponse,
  smoothingStepsTo,
  wallSpeedKept,
  wallStopAngle,
  wreckTimeline,
} from './nfs2-sim-tune';

const ID = 'CARDATA.VIV__data/children/3/item/data';

const glue = () => [
  { slice_distance: 5, speed_boost_multiplier: 1.075 },
  { slice_distance: 10, speed_boost_multiplier: 1.15 },
  { slice_distance: 30, speed_boost_multiplier: 1.2 },
  { slice_distance: 60, speed_boost_multiplier: 1.25 },
];

// the shipped simtune.dat
const sim = (): SimTuneRecord => ({
  telepole_launch_value: 95,
  initial_jump_roll_attenuate: 0.0101,
  jump_roll_due_to_car_turn: -0.00999,
  initial_jump_road_pitch_damp: 0.4,
  jump_pitch_due_to_acc_and_brake: -0.000885,
  extra_flight_gravity: 0.5,
  bad_collision_reset_ticks: 700,
  full_gas_reset_tick_advance: 200,
  invincibility_ticks_after_reset: 0,
  reset_forward_slices: 5,
  stop_tumbling_speed: 1.0,
  collision_reset_altitude: 1.5,
  collision_reset_launch_speed: 0.0,
  bounce_threshold: 0.7,
  bounce_elasticity: 0.092,
  bounce_shock_absorb_speed: 5.0,
  ground_max_speed_change: 5.0,
  ground_rise_smoothing: 0.3,
  ground_fall_smoothing: 0.5,
  barrier_speed_loss_multiplier: 10.0,
  deflection_angular_range: 0.4,
  glue_logic: glue(),
});
const arcade = (): SimTuneRecord => ({
  telepole_launch_value: 175,
  initial_jump_roll_attenuate: 0,
  jump_roll_due_to_car_turn: -0.00058,
  initial_jump_road_pitch_damp: 0.35,
  jump_pitch_due_to_acc_and_brake: 0.000244,
  extra_flight_gravity: 0.6,
  bad_collision_reset_ticks: 110,
  full_gas_reset_tick_advance: 50,
  invincibility_ticks_after_reset: 100,
  reset_forward_slices: 0,
  stop_tumbling_speed: 0.0,
  collision_reset_altitude: 4.0,
  collision_reset_launch_speed: 30.0,
  bounce_threshold: 0.3,
  bounce_elasticity: 0.0,
  bounce_shock_absorb_speed: 0.9996,
  ground_max_speed_change: 5.0,
  ground_rise_smoothing: 0.4,
  ground_fall_smoothing: 0.6,
  barrier_speed_loss_multiplier: 6.0,
  deflection_angular_range: 0.6,
  glue_logic: glue(),
});

describe('nfs2-sim-tune computations', () => {
  it('rebounds above the absorb speed only', () => {
    expect(reboundSpeed(3, 5, 0.092)).toBe(0);
    expect(reboundSpeed(15, 5, 0.092)).toBeCloseTo(0.92, 9);
    expect(reboundCurve(5, 0.1, 30)).toEqual([
      { x: 0, y: 0 },
      { x: 5, y: 0 },
      { x: 30, y: 2.5 },
    ]);
    expect(elasticityFor(30, 2.5, 5)).toBeCloseTo(0.1, 9);
    expect(elasticityFor(30, 2.5, 40)).toBe(0);
  });

  it('smooths the ground speed step by step', () => {
    const r = smoothingResponse(0.5, 3);
    expect(r.map(p => p.y)).toEqual([0, 0.5, 0.75, 0.875]);
    expect(r[3].x).toBe(3 / 32);
    // 1 - 0.7^n >= 0.9 from n = 7
    expect(smoothingStepsTo(0.3)).toBe(7);
    expect(smoothingStepsTo(0)).toBeNull();
    expect(smoothingStepsTo(1)).toBe(1);
  });

  it('counts the wreck timer down at 32 ticks per second, 8 times faster with the car still', () => {
    const t = wreckTimeline(700, 200);
    expect(t.seconds).toBe(700 / 32);
    expect(t.stillSeconds).toBe(700 / 32 / 8);
    expect(t.gasSeconds).toBe(500 / 32);
    expect(t.normal).toEqual([
      { x: 0, y: 700 },
      { x: 700 / 32, y: 0 },
    ]);
    expect(wreckTimeline(40, 50).gasSeconds).toBe(0);
  });

  it('takes the wall slide loss off the speed along the wall', () => {
    expect(wallSpeedKept(50, 0, 10)).toBeCloseTo(50, 9);
    const a = (30 * Math.PI) / 180;
    expect(wallSpeedKept(50, 30, 10)).toBeCloseTo(50 * Math.cos(a) - ((50 * Math.sin(a)) / 2) * 2.5, 9);
    expect(wallSpeedKept(50, 90, 6)).toBe(0);
    // no loss at 5 m/s and below
    expect(wallSpeedKept(4, 30, 10)).toBeCloseTo(4 * Math.cos(a), 9);
    // v cos a = v sin a * 10 / 8
    expect(wallStopAngle(50, 10)).toBeCloseTo((Math.atan(0.8) * 180) / Math.PI, 9);
    expect(wallSpeedKept(50, wallStopAngle(50, 10) + 1, 10)).toBe(0);
  });

  it('gives the boost of the last glue pair reached', () => {
    const g = glue();
    expect(glueBoostAt(0, g)).toBe(1);
    expect(glueBoostAt(4, g)).toBe(1);
    expect(glueBoostAt(5, g)).toBe(1.075);
    expect(glueBoostAt(29, g)).toBe(1.15);
    expect(glueBoostAt(200, g)).toBe(1.25);
    expect(glueSteps(g, 100)).toEqual([
      { x: 0, y: 1 },
      { x: 5, y: 1.075 },
      { x: 10, y: 1.15 },
      { x: 30, y: 1.2 },
      { x: 60, y: 1.25 },
      { x: 100, y: 1.25 },
    ]);
    expect(glueOrderProblems(g)).toEqual([]);
    g[2].slice_distance = 10;
    expect(glueOrderProblems(g)).toEqual([2]);
  });

  it('turns dot product thresholds into angles', () => {
    expect(acosDeg(0.7)).toBeCloseTo(45.573, 3);
    expect(acosDeg(0.3)).toBeCloseTo(72.542, 3);
    expect(acosDeg(1.5)).toBe(0);
  });
});

describe('Nfs2SimTuneBlockUiComponent', () => {
  let fixture: ComponentFixture<Nfs2SimTuneBlockUiComponent>;
  let component: Nfs2SimTuneBlockUiComponent;
  let appendChanges: jasmine.Spy;

  beforeEach(async () => {
    appendChanges = jasmine.createSpy('appendChanges').and.returnValue(Promise.resolve());
    await TestBed.configureTestingModule({
      declarations: [Nfs2SimTuneBlockUiComponent],
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
    fixture = TestBed.createComponent(Nfs2SimTuneBlockUiComponent);
    component = fixture.componentInstance;
    component.resourceId = ID;
    component.resourceName = 'simtune.dat';
    component.resourceSchema = {
      block_class_mro: 'Nfs2SimTune__DataBlock',
      fields: [
        {
          name: 'simulation',
          schema: { fields: [{ name: 'bounce_threshold', description: 'Bounce threshold', schema: {} }] },
        },
      ],
    };
    component.resourceData = { simulation: sim(), arcade: arcade() };
    fixture.detectChanges();
  });

  it('summarizes both styles', () => {
    const tile = (label: string) => component.tiles.find(t => t.label === label)!;
    expect(tile('Wreck timer').value).toBe('21.88 s');
    expect(tile('Wreck timer').sub).toBe('arcade 3.44 s');
    expect(tile('Invincibility').sub).toBe('arcade 3.13 s');
    expect(tile('Flight gravity').value).toBe('× 1.5');
    expect(tile('Bounces up to').value).toBe('45.6°');
    expect(tile('Deflection range').sub).toBe('arcade 53.1°');
    expect(tile('Max catch-up').value).toBe('× 1.25');
    expect(component.recordDescriptions['bounce_threshold']).toBe('Bounce threshold');
  });

  it('draws both styles on every chart', () => {
    expect(component.reboundSeries.map(s => s.id)).toEqual(['rebound-simulation', 'rebound-arcade']);
    expect(component.smoothingSeries.length).toBe(4);
    expect(component.smoothingSeries[0].points[1].y).toBeCloseTo(0.3, 9);
    expect(component.wreckSeries.filter(s => s.id.startsWith('wreck-')).length).toBe(2);
    expect(component.wallSeries.length).toBe(3);
    expect(component.glueSeries[1].points.length).toBe(6);
    expect(component.flightRows.find(r => r.field === 'ground_max_speed_change')!.cells[0].derived).toBe(
      'not read by the game',
    );
  });

  it('writes a dragged rebound end as the elasticity', () => {
    const points = component.reboundSeries[0].points.map(p => ({ ...p }));
    points[2] = { x: 30, y: 5 };
    component.onReboundChange({ seriesId: 'rebound-simulation', points, changed: [2] });
    expect(appendChanges).toHaveBeenCalledTimes(1);
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.id).toBe(ID + '/simulation/bounce_elasticity');
    expect(change.newValue).toBe(0.2);
  });

  it('writes a dragged glue step as its pair, one undo step', () => {
    const points = component.glueSeries[1].points.map(p => ({ ...p }));
    points[3] = { x: 35, y: 1.3 };
    component.onGlueChange({ seriesId: 'glue-arcade', points, changed: [3] });
    expect(appendChanges).toHaveBeenCalledTimes(1);
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.op).toBe('bundle');
    expect(change.changes.map((c: any) => [c.id, c.newValue])).toEqual([
      [ID + '/arcade/glue_logic/2/slice_distance', 35],
      [ID + '/arcade/glue_logic/2/speed_boost_multiplier', 1.3],
    ]);
  });

  it('keeps a dragged glue step between its neighbours', () => {
    const s = component.glueSeries[0];
    expect(s.constrain!(2, { x: 3, y: 1.1 })).toEqual({ x: 6, y: 1.1 });
    expect(s.constrain!(2, { x: 40, y: 1.1 })).toEqual({ x: 29, y: 1.1 });
  });

  it('turns markers into fields', () => {
    component.onMarker({ markerId: 'deflect-arcade', value: 60 });
    let change = appendChanges.calls.mostRecent().args[0];
    expect(change.id).toBe(ID + '/arcade/deflection_angular_range');
    expect(change.newValue).toBe(0.5);
    component.onMarker({ markerId: 'gas-simulation', value: 250.4 });
    change = appendChanges.calls.mostRecent().args[0];
    expect(change.id).toBe(ID + '/simulation/full_gas_reset_tick_advance');
    expect(change.newValue).toBe(250);
  });

  it('writes the wreck ticks and the smoothing factors from the charts', () => {
    const wreck = component.wreckSeries[0].points.map(p => ({ ...p }));
    wreck[0] = { x: 0, y: 640.2 };
    component.onWreckChange({ seriesId: 'wreck-simulation', points: wreck, changed: [0] });
    expect(appendChanges.calls.mostRecent().args[0].id).toBe(ID + '/simulation/bad_collision_reset_ticks');
    expect(appendChanges.calls.mostRecent().args[0].newValue).toBe(640);
    const smooth = component.smoothingSeries[3].points.map(p => ({ ...p }));
    smooth[1] = { ...smooth[1], y: 0.25 };
    component.onSmoothingChange({ seriesId: 'fall-arcade', points: smooth, changed: [1] });
    expect(appendChanges.calls.mostRecent().args[0].id).toBe(ID + '/arcade/ground_fall_smoothing');
    expect(appendChanges.calls.mostRecent().args[0].newValue).toBe(0.25);
  });
});
