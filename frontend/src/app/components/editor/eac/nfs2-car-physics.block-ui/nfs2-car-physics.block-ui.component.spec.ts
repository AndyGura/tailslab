import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BehaviorSubject, Subject } from 'rxjs';
import { Nfs2CarPhysicsBlockUiComponent } from './nfs2-car-physics.block-ui.component';
import { MainService } from '../../../../services/main.service';
import { ChangesService } from '../../../../services/changes.service';

// pcala.dat figures (rounded)
const spec = () => ({
  mass: 1350,
  num_gears: 8,
  gear_shift_delay: 8,
  velocity_to_rpm_ratio: [-404.51, 0, 361.62, 231.34, 164.58, 129.47, 108.32, 91],
  gear_efficiency: [0.8, 1, 0.95, 0.75, 0.85, 0.9, 1, 1.15],
  torque_curve: [
    310, 310, 315, 325, 350, 360, 370, 380, 380, 385, 390, 395, 395, 390, 385, 380, 375, 374, 373, 372, 370, 365, 358,
    340, 330, 330, 325, 320, 315, 310, 305, 300, 280, 260, 240, 210, 180, 150, 130, 100, 100,
  ],
  engine_redline_rpm: 7550,
  max_velocity: 81,
  front_drive_ratio: 0,
  max_braking_deceleration: 12,
  front_bias_brake_ratio: 0.6,
  gas_increasing_curve: [16, 16, 16, 16, 16, 16, 16, 16],
  gas_decreasing_curve: [32, 32, 32, 32, 32, 32, 32, 32],
  brake_increasing_curve: [64, 32, 16, 8, 4, 2, 1, 1],
  brake_decreasing_curve: [32, 32, 32, 32, 32, 32, 32, 32],
  wheel_base: 2.52,
  front_grip_bias: 0.492,
  max_steering_acceleration: 19,
  turn_in_ramp: 16,
  turn_out_ramp: 32,
  lateral_acceleration_grip_multiplier: 3.2,
  aerodynamic_downforce_multiplier: 0.00075,
  gas_off_factor: 0.2,
  g_transfer_factor: 0.6,
  slide_multiplier: 1,
  spin_velocity_cap: 0.35,
  slide_velocity_cap: 0.2,
  slide_assistance_factor: 128,
  push_factor: 9000,
  low_turn_factor: 0.021,
  high_turn_factor: 0.026,
});

describe('Nfs2CarPhysicsBlockUiComponent', () => {
  let fixture: ComponentFixture<Nfs2CarPhysicsBlockUiComponent>;
  let component: Nfs2CarPhysicsBlockUiComponent;
  let appendChanges: jasmine.Spy;

  beforeEach(async () => {
    appendChanges = jasmine.createSpy('appendChanges').and.returnValue(Promise.resolve());
    await TestBed.configureTestingModule({
      imports: [Nfs2CarPhysicsBlockUiComponent],
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
    fixture = TestBed.createComponent(Nfs2CarPhysicsBlockUiComponent);
    component = fixture.componentInstance;
    component.resourceId = 'CARDATA.VIV__data/children/3/item/data';
    component.resourceSchema = { block_class_mro: 'Nfs2CarPhysics__DataBlock', fields: [] };
    component.resourceData = spec();
    fixture.detectChanges();
  });

  it('summarizes the car', () => {
    const tile = (label: string) => component.tiles.find(t => t.label === label)!;
    expect(tile('Peak torque').value).toBe('395 N·m');
    expect(tile('Peak torque').sub).toBe('@ 2,816 rpm');
    expect(tile('Mass').value).toBe('1,350 kg');
    expect(tile('Top speed').value).toBe('292 km/h');
    expect(tile('Drivetrain').value).toBe('RWD');
    expect(tile('Drivetrain').sub).toContain('6-speed');
    expect(tile('Braking').sub).toContain('arcade 24 · 60% front');
  });

  it('reads only the torque entries up to the redline', () => {
    // 7550 / 256 = entry 29
    expect(component.torqueActiveCount).toBe(30);
    expect(component.torqueAt(7550)).toBe(310);
    expect(component.torqueAt(20000)).toBe(100);
  });

  it('lists the gears with the arcade upshifts', () => {
    expect(component.gears.map(g => g.name)).toEqual(['R', 'N', '1st', '2nd', '3rd', '4th', '5th', '6th']);
    // 7550 rpm / 361.62 rpm per m/s
    expect(component.gears[2].redlineSpeed).toBeCloseTo((7550 / 361.62) * 3.6, 3);
    expect(component.gears[2].upshiftSpeed).toBeCloseTo((7050 / 361.62) * 3.6, 3);
    expect(component.gears[7].upshiftSpeed).toBeNull();
    // drive = ratio / mass / 10 * efficiency; sim capped at 10 m/s² in 1st
    expect(component.gears[2].drive).toBeCloseTo((361.62 / 1350 / 10) * 0.95, 6);
    expect(component.gears[2].arcadePeak).toBeCloseTo(395 * component.gears[2].drive * 1.5, 6);
    expect(component.gears[2].simPeak).toBe(10);
  });

  it('sets the simulation air drag to the top gear drive at max_velocity', () => {
    const drag = component.simAccelSeries.find(s => s.id === 'drag')!;
    // 81 m/s * 91 = 7371 rpm: entry 28
    const atTop = drag.points.find(p => Math.abs(p.x - 81 * 3.6) < 1e-6)!;
    expect(atTop.y).toBeCloseTo(315 * component.drive(7), 6);
  });

  it('writes a torque drag as one change of the table', () => {
    const points = component.torqueSeries[0].points.map(p => ({ ...p }));
    points[3] = { x: points[3].x, y: 333.4 };
    component.onTorqueChange({ seriesId: 'torque_curve', points, changed: [3] });
    expect(appendChanges).toHaveBeenCalledTimes(1);
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.op).toBe('set');
    expect(change.id).toBe('CARDATA.VIV__data/children/3/item/data/torque_curve');
    expect(change.newValue[3]).toBe(333);
    expect(change.newValue[4]).toBe(350);
  });

  it('turns a dragged gear end into the ratio that reaches that speed at the redline', () => {
    const series = component.gearSeries.find(s => s.id === 'gear-4')!;
    const points = series.points.map(p => ({ ...p }));
    points[1] = { x: 180, y: 7550 };
    component.onGearChange({ seriesId: 'gear-4', points, changed: [1] });
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.id).toBe('CARDATA.VIV__data/children/3/item/data/velocity_to_rpm_ratio/4');
    expect(change.newValue).toBeCloseTo(7550 / 50, 2);
  });

  it('ramps the brake pedal by the step of its level', () => {
    const press = component.pedalSeries.find(s => s.id === 'brake_on')!.points.map(p => p.y);
    expect(press.slice(0, 5)).toEqual([0, 64, 80, 96, 104]);
    const release = component.pedalSeries.find(s => s.id === 'brake_off')!.points.map(p => p.y);
    expect(release.slice(0, 3)).toEqual([255, 223, 191]);
  });

  it('edits the ramp steps as bytes', () => {
    const points = component.rampSeries[0].points.map(p => ({ ...p }));
    points[2] = { ...points[2], y: 300 };
    component.onRampChange({ seriesId: 'brake_increasing_curve', points, changed: [2] });
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.id).toBe('CARDATA.VIV__data/children/3/item/data/brake_increasing_curve');
    expect(change.newValue).toEqual([64, 32, 255, 8, 4, 2, 1, 1]);
  });

  it('turns a dragged arcade braking step into max_braking_deceleration', () => {
    const points = component.brakeSeries[0].points.map(p => ({ ...p }));
    points[1] = { ...points[1], y: 30 };
    component.onBrakeChange({ seriesId: 'arcade', points, changed: [1] });
    expect(appendChanges.calls.mostRecent().args[0].newValue).toBe(15);
    const sim = component.brakeSeries.find(s => s.id === 'sim')!.points.map(p => ({ ...p }));
    sim[1] = { ...sim[1], y: 9.5 };
    component.onBrakeChange({ seriesId: 'sim', points: sim, changed: [1] });
    expect(appendChanges.calls.mostRecent().args[0].newValue).toBe(9.5);
  });

  it('follows the arcade steering gain and push limit', () => {
    // 5..20 m/s: max_steering_acceleration / 64 / 128 * 127
    expect(component.yawAtFullLock(10, 0.026)).toBeCloseTo((19 / 64 / 128) * 127, 6);
    expect(component.yawAtFullLock(40, 0.026)).toBeCloseTo((19 / 64 / (1 + 40 * 0.026) / 128) * 127, 6);
    expect(component.pushLimit(30.5)).toBeCloseTo(((9000 + 0x6667) * 512) / 900 / 0x10000, 6);
  });

  it('scales the torque curve to a new peak power', () => {
    const tile = component.tiles.find(t => t.id === 'peak_power')!;
    component.onTileChange({ id: 'peak_power', value: tile.edit!.value * 2 });
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.id).toBe('CARDATA.VIV__data/children/3/item/data/torque_curve');
    expect(change.newValue[11]).toBeCloseTo(790, -1);
  });

  it('splits the simulation grip between the axles with the downforce above 5 m/s', () => {
    // 10 m/s² × lateral_acceleration_grip_multiplier
    expect(component.simGrip).toBeCloseTo(32, 9);
    const still = component.simAxleGrip(5);
    expect(still.front).toBeCloseTo(32 * 0.492, 9);
    expect(still.rear).toBeCloseTo(32 * 0.508, 9);
    const fast = component.simAxleGrip(40);
    expect(fast.front).toBeCloseTo(32 * 0.492 * (1 + 40 * 0.00075), 9);
    expect(fast.rear).toBeCloseTo(32 * 0.508 * (1 + 40 * 0.00075 * 1.5), 9);
    const front = component.axleGripSeries.find(s => s.id === 'front')!;
    expect(front.points[0]).toEqual({ x: 0, y: 32 * 0.492 });
  });

  it('moves grip to the rear under acceleration and to the front under braking', () => {
    const braking = component.transferGrip(-12);
    expect(braking.front).toBeCloseTo(32 * 0.492 + 12 * 0.6, 9);
    expect(braking.rear).toBeCloseTo(32 * 0.508 - 12 * 0.6, 9);
    // the chart goes from full braking to the peak 1st gear drive (395 N·m × drive, capped at 10 m/s²)
    expect(component.simPeakFirstDrive).toBe(10);
    const rear = component.transferSeries.find(s => s.id === 'rear')!.points;
    expect(rear[0].x).toBe(-12);
    expect(rear[rear.length - 1].x).toBeCloseTo(10, 9);
    expect(rear[rear.length - 1].y).toBeCloseTo(32 * 0.508 + 10 * 0.6, 9);
  });

  it('turns the simulation front wheels by max_steering_acceleration, less above 60 m/s', () => {
    const lock = 19 * (127 / 128) * (360 / 256);
    expect(component.simSteerLock(0)).toBeCloseTo(lock, 9);
    expect(component.simSteerLock(60)).toBeCloseTo(lock, 9);
    expect(component.simSteerLock(90)).toBeCloseTo(lock / 1.5, 9);
    const tile = component.tiles.find(t => t.id === 'sim_steer')!;
    expect(tile.value).toBe('26.5°');
    component.onTileChange({ id: 'sim_steer', value: lock * 2 });
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.id).toBe('CARDATA.VIV__data/children/3/item/data/max_steering_acceleration');
    expect(change.newValue).toBeCloseTo(38, 3);
  });

  it('sets the simulation grip multiplier from the grip tile', () => {
    expect(component.tiles.find(t => t.id === 'sim_grip')!.value).toBe('32 m/s²');
    component.onTileChange({ id: 'sim_grip', value: 25 });
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.id).toBe('CARDATA.VIV__data/children/3/item/data/lateral_acceleration_grip_multiplier');
    expect(change.newValue).toBe(2.5);
  });

  it('derives the yaw lever from the wheel base with the speed bands', () => {
    expect(component.yawLever).toBeCloseTo((2.52 / 2) * 0.0245 * 256, 9);
    expect([30, 50, 70, 80, 90].map(v => component.yawBand(v))).toEqual([0.5, 0.75, 1, 1, 1.5]);
    const side = component.yawSeries[0].points;
    expect(side[0].y).toBeCloseTo(32 * component.yawLever * 0.5, 9);
  });

  it('damps the yaw rate of a slide by slip × slide_velocity_cap, at least to half', () => {
    expect(component.slideKeep(0.05)).toBe(1);
    expect(component.slideKeep(0.5)).toBeCloseTo(1 - 0.5 * 0.2, 9);
    expect(component.slideKeep(0.5, 2)).toBeCloseTo(1 - 0.5 * 0.4, 9);
    expect(component.slideKeep(0.5, 1 / 8)).toBeCloseTo(1 - 0.5 * 0.025, 9);
    expect(component.slideKeep(1, 4)).toBe(0.5);
    expect(component.slideSeries.map(s => s.id)).toEqual(['normal', 'counter', 'brake', 'handbrake']);
    const counter = component.slideSeries.find(s => s.id === 'counter')!;
    expect(counter.points[counter.points.length - 1]).toEqual({ x: 1, y: 1 - 0.1 });
  });

  it('brakes with the engine by gas_off_factor, in arcade also by the speed', () => {
    // 20 m/s × 231.34 = 4627 rpm: entry 18
    const sim = 373 * component.drive(3) * 0.2;
    expect(component.engineBrakeSim(20, 3)).toBeCloseTo(sim, 9);
    expect(component.engineBrakeArcade(20, 3)).toBeCloseTo(sim * 20 * 0.1, 9);
    // above the redline: the redline entry
    expect(component.engineBrakeSim(100, 2)).toBeCloseTo(310 * component.drive(2) * 0.2, 9);
    expect(component.engineBrakeSimSeries.map(s => s.label)).toEqual(['1st', '2nd', '3rd', '4th', '5th', '6th']);
  });

  it('caps the simulation brakes at 32 × speed and splits them by front_bias_brake_ratio', () => {
    const fast = component.simBrake(10);
    expect(fast.total).toBe(12);
    expect(fast.front).toBeCloseTo(7.2, 9);
    expect(fast.rear).toBeCloseTo(4.8, 9);
    expect(component.simBrake(0.1).total).toBeCloseTo(3.2, 9);
    const front = component.brakeSeries.find(s => s.id === 'sim-front')!;
    expect(front.points[1].y).toBeCloseTo(7.2, 9);
  });

  it('marks the simulation over-rev on the gearing chart', () => {
    expect(component.gearMarkers.find(m => m.id === 'over_rev')!.value).toBe(7550 * 1.5);
  });

  it('labels the gas curves as not read', () => {
    expect(component.rampSeries.find(s => s.id === 'gas_increasing_curve')!.label).toContain('not read');
  });
});
