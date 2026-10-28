import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BehaviorSubject, Subject } from 'rxjs';
import { Nfs3CarPhysicsBlockUiComponent } from './nfs3-car-physics.block-ui.component';
import { MainService } from '../../../../services/main.service';
import { ChangesService } from '../../../../services/changes.service';

// Diab carp.txt as parsed
const spec = (): { [key: string]: any } => ({
  serial_number: 16,
  car_class: 0,
  mass: 1625.0,
  num_gears: 7,
  num_gears_auto: 7,
  shift_delay: 6,
  shift_blip: [0, 0, 250, 250, 200, 150, 100, 100],
  brake_blip: [0, 0, 270, 250, 200, 150, 100, 100],
  vel_to_rpm: [-224.831268, 0.0, 244.4048, 160.82048, 118.499298, 93.10659, 71.946007, 0.0],
  vel_to_rpm_auto: [-224.831268, 0.0, 244.4048, 160.82048, 118.499298, 93.10659, 71.946007, 0.0],
  gear_ratio: [2.125, 0.0, 2.31, 1.52, 1.12, 0.88, 0.68, 0.0],
  gear_ratio_auto: [2.125, 0.0, 2.31, 1.52, 1.12, 0.88, 0.68, 0.0],
  gear_efficiency: [0.8, 0.0, 0.98, 0.94, 0.8, 0.9, 1.1, 0.0],
  gear_efficiency_auto: [0.8, 0.0, 0.96, 0.92, 0.78, 0.88, 1.01, 0.0],
  torque: [
    200.0, 251.199997, 301.200012, 326.799988, 352.447998, 378.559998, 402.727997, 415.015991, 427.399994, 440.200012,
    450.0, 450.0, 451.440002, 456.559998, 469.23999, 497.399994, 521.719971, 539.640015, 555.400024, 568.200012, 581.0,
    600.0, 596.039978, 588.359985, 574.919983, 557.0, 534.400024, 508.799988, 483.200012, 457.600006, 432.0, 406.399994,
    380.799988, 355.200012, 329.600006, 304.0, 278.399994, 252.800003, 227.199997, 201.600006, 176.0,
  ],
  final_gear: 3.8319,
  final_gear_auto: 3.8319,
  min_rpm: 1030,
  redline: 7300,
  max_velocity: 93.055557,
  top_speed_cap: 93.055557,
  front_drive_ratio: 0.5,
  abs: 1,
  max_brake_decel: 10.51,
  front_brake_bias: 0.55624,
  gas_increasing: [16, 16, 16, 16, 16, 16, 16, 16],
  gas_decreasing: [32, 32, 32, 32, 32, 32, 32, 32],
  brake_increasing: [64.0, 32.0, 16.0, 8.0, 4.0, 2.0, 1.0, 1.0],
  brake_decreasing: [32.0, 32.0, 32.0, 32.0, 32.0, 32.0, 32.0, 32.0],
  wheel_base: 2.65,
  front_grip_bias: 0.47,
  power_steering: 1,
  min_steering_accel: 19.0,
  turn_in_ramp: 18.0,
  turn_out_ramp: 32.0,
  lateral_grip: 3.45,
  aero_downforce: 0.00212,
  gas_off_factor: 0.35,
  g_transfer: 0.46,
  turning_circle: 12.55,
  tire_front: [245, 40, 17],
  tire_rear: [335, 35, 18],
  tire_wear: 0.0,
  slide_mult: 1.25,
  spin_velocity_cap: 0.349991,
  slide_velocity_cap: 0.299988,
  slide_assist: 128,
  push_factor: 9000,
  low_turn_factor: 0.022995,
  high_turn_factor: 0.029,
  pitch_roll: 0.78,
  road_bumpiness: 0.72997,
  spoiler_type: 0,
  spoiler_speed: 5.0,
  gradual_turn_cutoff: 55,
  medium_turn_cutoff: 95,
  sharp_turn_cutoff: 150,
  medium_turn_speed: 0.95,
  sharp_turn_speed: 0.93,
  extreme_turn_speed: 0.9,
  subdivide_level: 3,
  camera_arm: 0.25,
  body_damage: 0.0,
  engine_damage: 0.0,
  suspension_damage: 0.0,
  engine_tuning: 1.0,
  brake_balance: 0.0,
  steering_speed: 1.0,
  gear_ratio_factor: 1.0,
  suspension_stiffness: 1.0,
  aero_factor: 1.0,
  tire_factor: 1.0,
  ai_acc0: [
    4.266667, 5.69718, 6.686867, 7.218466, 7.41979, 7.502289, 7.584114, 7.621973, 7.568377, 7.443275, 7.277295,
    7.130982, 7.068186, 7.098461,
  ],
  ai_acc1: [
    7.220324, 7.414387, 7.616909, 7.808165, 8.05417, 8.348123, 8.56897, 8.701547, 8.804519, 8.7483, 8.284791, 7.416515,
    6.488037, 5.806163,
  ],
  ai_acc2: [
    5.400309, 5.177514, 5.070873, 5.04432, 5.052013, 5.048112, 4.988134, 4.782425, 4.391487, 3.933207, 3.562806,
    3.337551, 3.236243, 3.218879,
  ],
  ai_acc3: [
    3.243245, 3.266305, 3.262723, 3.231236, 3.183981, 3.137559, 3.099553, 3.060645, 3.008057, 2.939529, 2.857754,
    2.768349, 2.667154, 2.53386,
  ],
  ai_acc4: [
    2.39084, 2.309029, 2.311198, 2.351753, 2.38281, 2.383609, 2.353744, 2.302386, 2.239446, 2.172119, 2.103385,
    2.031254, 1.952488, 1.862853,
  ],
  ai_acc5: [
    1.760417, 1.668866, 1.627625, 1.63811, 1.66328, 1.673859, 1.662092, 1.631512, 1.587119, 1.529581, 1.45977, 1.382786,
    1.303077, 1.220757,
  ],
  ai_acc6: [
    1.134639, 1.045146, 0.95267, 0.856744, 0.757287, 0.654247, 0.547914, 0.439717, 0.330999, 0.222222, 0.104575, 0.0,
    0.0, 0.0,
  ],
  ai_acc7: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
});

describe('Nfs3CarPhysicsBlockUiComponent', () => {
  let fixture: ComponentFixture<Nfs3CarPhysicsBlockUiComponent>;
  let component: Nfs3CarPhysicsBlockUiComponent;
  let appendChanges: jasmine.Spy;

  beforeEach(async () => {
    appendChanges = jasmine.createSpy('appendChanges').and.returnValue(Promise.resolve());
    await TestBed.configureTestingModule({
      declarations: [Nfs3CarPhysicsBlockUiComponent],
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
    fixture = TestBed.createComponent(Nfs3CarPhysicsBlockUiComponent);
    component = fixture.componentInstance;
    component.resourceId = 'car.viv__data/children/14/item/data';
    component.resourceSchema = { block_class_mro: 'Nfs3CarPhysics__DataBlock', fields: [] };
    component.resourceData = spec();
    fixture.detectChanges();
  });

  it('summarizes the car', () => {
    const tile = (label: string) => component.tiles.find(t => t.label === label)!;
    expect(tile('Redline').value).toBe('7,300 rpm');
    expect(tile('Mass').value).toBe('1,625 kg');
    expect(tile('Top speed').value).toBe('335 km/h');
    expect(tile('Drivetrain').value).toBe('AWD');
    expect(tile('Full lock').value).toBe('28.5°');
    expect(tile('Peak torque').value).toBe('600 N·m');
  });

  it('interpolates the torque curve like the game', () => {
    expect(component.torqueAt(256 * 21)).toBe(600);
    expect(component.torqueAt(256 * 21.5)).toBeCloseTo((600 + 596.039978) / 2, 4);
    expect(component.torqueAt(20000)).toBeCloseTo(176, 4);
  });

  it('shifts the automatic gearbox at 7/8 of the redline and down below 5/6 or half', () => {
    const first = component.gears.find(g => g.index === 2)!;
    expect(first.upshiftSpeed!).toBeCloseTo(((7300 - 912) / 244.4048) * 3.6, 3);
    const second = component.gears.find(g => g.index === 3)!;
    expect(second.downshiftSpeed!).toBeCloseTo((3650 / 244.4048) * 3.6, 3);
    const third = component.gears.find(g => g.index === 4)!;
    expect(third.downshiftSpeed!).toBeCloseTo(((7300 - 1216) / 160.82048) * 3.6, 3);
    // the top gear (6th, index 6) has no up-shift, 5th (index 5) shifts into it
    expect(component.gears.find(g => g.index === 6)!.upshiftSpeed).toBeNull();
    expect(component.gears.find(g => g.index === 5)!.upshiftSpeed).not.toBeNull();
    // gear ratio x final gear x 60 / (2 pi r), r of the 335/35 R18 rear tyre
    expect(first.fromRatios).toBeCloseTo(244.4048, 1);
  });

  it('sets the air drag from the top gear at the max velocity', () => {
    // torque entry trunc(round(93.055557 x 71.946007) / 256) = 26
    const atMax = ((0.98 * 534.400024 * 71.946007) / 1625) * 0.1;
    expect(component.dragAt(93.055557)).toBeCloseTo(atMax, 6);
    expect(component.dragAt(93.055557 / 2)).toBeCloseTo(atMax / 8, 6);
  });

  it('ramps the brake by the rounded curve entry of the brake value', () => {
    const press = component.pedalSeries.find(s => s.id === 'brake_on')!;
    expect(press.points.slice(0, 4).map(p => p.y)).toEqual([0, 64, 80, 96]);
  });

  it('applies the tuning sliders like Carp_TuneCar', () => {
    component.onTuningInput(2, '1.2');
    const tuned = (label: string) => component.tunedRows.find(r => r.label === label)!.tuned;
    expect(tuned('Min. steering accel.')).toBe('22.8');
    expect(component.tunedCarp().front_grip_bias).toBeCloseTo(0.47 * 1.125, 6);
    expect(tuned('Turning circle (m)')).toBe('11.295');
    expect(tuned('Gas release per step')).toBe('28');
  });

  it('writes AI table edits into their section', () => {
    const points = component.aiSeries[0].points.map(p => ({ ...p }));
    points[15] = { ...points[15], y: 9 };
    component.onAiChange({ seriesId: 'ai_acc', points, changed: [15] });
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.id).toBe('car.viv__data/children/14/item/data/ai_acc1');
    expect(change.newValue[1]).toBe(9);
  });

  it('edits the rpm per m/s of the selected gear set', () => {
    component.onAutomaticChange(true);
    component.onGearInput('ratio', 2, '250');
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.id).toBe('car.viv__data/children/14/item/data/vel_to_rpm_auto/2');
    expect(change.newValue).toBe(250);
  });
});
