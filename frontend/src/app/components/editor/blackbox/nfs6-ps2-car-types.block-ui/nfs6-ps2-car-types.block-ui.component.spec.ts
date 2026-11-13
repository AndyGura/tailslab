import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BehaviorSubject, Subject } from 'rxjs';
import { Nfs6Ps2CarTypesBlockUiComponent } from './nfs6-ps2-car-types.block-ui.component';
import { MainService } from '../../../../services/main.service';
import { ChangesService } from '../../../../services/changes.service';
import { corvette } from './nfs6-ps2-car-types.spec-data';
import {
  boxInertia,
  maxWheelAngle,
  needleAngle,
  samplePitchOctaves,
  shiftPoints,
  speedAt,
  speedLimitMph,
  tableValue,
  topSpeedEstimate,
} from './nfs6-ps2-car-specs';

const ID = 'GLOBALB.BUN__data/chunks/15/data/data';

describe('nfs6-ps2-car-specs', () => {
  it('looks tables up as Table::GetValue', () => {
    expect(tableValue([1, 3, 5], 0, 10, 2.5)).toBe(2);
    expect(tableValue([1, 3, 5], 0, 10, -5)).toBe(1);
    expect(tableValue([1, 3, 5], 0, 10, 50)).toBe(5);
  });

  it('finds the automatic shift points of CalculateShiftPoints', () => {
    const car = corvette();
    const { up, down } = shiftPoints(car.drive_train, car.engine);
    // computed with the C port's algorithm (src/nfs6/nfs6-physics/src/drivetrain.c) over the CORVETTE
    expect(up.slice(2, 7)).toEqual([5890, 5937.5, 5890, 5652.5, 5985]);
    expect(up[7]).toBe(car.engine.max_rpm);
    expect(down[3]).toBeCloseTo((0.95 * 5890 * 2.07) / 2.97, 6);
    // the fixed fraction without UseOptimalShiftPoints: idle + 0.8 * (redline - idle)
    expect(shiftPoints(car.drive_train, car.engine, false).up[2]).toBeCloseTo(1000 + 0.8 * 5500, 3);
  });

  it('limits the speed as RigidBody::GetDerivative', () => {
    expect(speedLimitMph(173, false)).toBeCloseTo(174.9, 6);
    expect(speedLimitMph(173, true)).toBeCloseTo(174.9 * 1.03, 6);
    expect(speedLimitMph(0, true)).toBe(0);
  });

  it('gives road speeds of the driven axle', () => {
    const car = corvette();
    const radii: [number, number] = [car.wheels[0].radius, car.wheels[2].radius];
    // rear wheel drive: rpm * pi / 30 * rear radius / (ratio * rear final drive)
    expect(speedAt(car.drive_train, radii, 7, 6000)).toBeCloseTo(
      (((6000 * Math.PI) / 30) * radii[1]) / (0.56 * 3.42),
      3,
    );
    const top = topSpeedEstimate(car.drive_train, car.engine, radii, car.aero.drag, car.controls.speed_limiter, false);
    expect(top.value).toBeGreaterThan(60);
    expect(top.value).toBeLessThanOrEqual(174.9 / 2.236025 + 1e-9);
  });

  it('steers, turns needles and pitches samples as the executable', () => {
    // the pad table at 0 and 160 m/s (2.9 degrees) times steering_scale
    expect(maxWheelAngle(0, 1.1, false)).toBeCloseTo(49.5, 6);
    expect(maxWheelAngle(200, 1, false)).toBeCloseTo(2.9, 6);
    expect(needleAngle(50, 0, 100, 300, 60)).toBe(360);
    expect(needleAngle(100, 0, 100, 45, 215)).toBe(215);
    expect(samplePitchOctaves(100, 0, 1200, 64)).toBeCloseTo(100 / 1200, 9);
    expect(samplePitchOctaves(0, 0, 1200, 0)).toBe(-1);
  });

  it('makes the box inertia of the game', () => {
    const car = corvette();
    const rb = car.rigid_body;
    const box = boxInertia(rb.mass, rb.dimensions.x, rb.dimensions.y, rb.dimensions.z);
    expect(box[0]).toBeCloseTo(rb.inertia_tensor[0], 4);
    expect(box[1]).toBeCloseTo(rb.inertia_tensor[5], 4);
    expect(box[2]).toBeCloseTo(rb.inertia_tensor[10], 4);
  });
});

describe('Nfs6Ps2CarTypesBlockUiComponent', () => {
  let fixture: ComponentFixture<Nfs6Ps2CarTypesBlockUiComponent>;
  let component: Nfs6Ps2CarTypesBlockUiComponent;
  let appendChanges: jasmine.Spy;

  const hp = () => ({ ...corvette(), name: 'CORVETTEHP', is_hp: 1, car_type: 1 });

  beforeEach(async () => {
    appendChanges = jasmine.createSpy('appendChanges').and.returnValue(Promise.resolve());
    await TestBed.configureTestingModule({
      declarations: [Nfs6Ps2CarTypesBlockUiComponent],
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
    fixture = TestBed.createComponent(Nfs6Ps2CarTypesBlockUiComponent);
    component = fixture.componentInstance;
    component.resourceId = ID;
    component.resourceSchema = {
      block_class_mro: 'Nfs6Ps2CarTypeInfos__DeclarativeCompoundBlock__CompoundBlock__DataBlock',
      fields: [
        {
          name: 'car_types',
          schema: {
            block_class_mro: 'ArrayBlock__DataBlock',
            child_schema: {
              block_class_mro: 'Nfs6Ps2CarTypeInfo__DataBlock',
              fields: [
                {
                  name: 'engine',
                  description: '',
                  schema: { fields: [{ name: 'torque_curve', description: 'Full throttle torque', schema: {} }] },
                },
                { name: 'traffic_weights', description: 'Weight by location', schema: {} },
              ],
            },
          },
        },
      ],
    };
    component.resourceData = { chunk_id: 0x34600, car_types: [corvette(), hp()] };
    fixture.detectChanges();
  });

  it('summarizes the car type', () => {
    const tile = (label: string) => component.tiles.find(t => t.label === label)!;
    expect(tile('Peak torque').value).toBe('620 N·m');
    expect(tile('Mass').value).toBe('1,500 kg');
    expect(tile('Drivetrain').value).toBe('RWD');
    expect(tile('Speed limiter').value).toBe('175 mph');
    expect(tile('Class').value).toBe('2');
  });

  it('switches the car type, HP versions with 5 % more torque', () => {
    component.select(1);
    expect(component.isHp).toBeTrue();
    expect(component.tiles.find(t => t.label === 'Peak torque')!.value).toBe('651 N·m');
    expect(component.tiles.find(t => t.label === 'Speed limiter')!.value).toBe('180 mph');
  });

  it('finds descriptions in the nested schemas', () => {
    expect(component.describe('engine', 'torque_curve')).toBe('Full throttle torque');
    expect(component.describe('traffic_weights')).toBe('Weight by location');
  });

  it('writes a torque drag in kN·m', () => {
    const points = component.engineSeries[0].points.map(p => ({ ...p }));
    points[4] = { ...points[4], y: 700 };
    component.onEngineChange({ seriesId: 'torque_curve', points, changed: [4] });
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.op).toBe('set');
    expect(change.id).toBe(`${ID}/car_types/0/engine/torque_curve`);
    expect(change.newValue[4]).toBe(0.7);
    expect(change.newValue[3]).toBe(0.6);
  });

  it('turns a dragged gear end into the ratio reaching that speed at max rpm', () => {
    const car = corvette();
    const speed = component.gears[3].maxSpeed * 0.9;
    const series = component.gearSeries.find(s => s.id === 'gear-3')!;
    const points = series.points.map(p => ({ ...p }));
    points[1] = { x: speed, y: car.engine.max_rpm };
    component.onGearChange({ seriesId: 'gear-3', points, changed: [1] });
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.id).toBe(`${ID}/car_types/0/drive_train/gear_ratios/3`);
    expect(change.newValue).toBeCloseTo(car.drive_train.gear_ratios[3] / 0.9, 2);
  });

  it('sets the speed limiter from a limit in mph', () => {
    component.onTileChange({ id: 'speed_limiter', value: 200 });
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.id).toBe(`${ID}/car_types/0/controls/speed_limiter`);
    expect(change.newValue).toBe(198.1);
  });

  it('moves wheels in one change', () => {
    const points = component.wheelSeries[0].points.map(p => ({ ...p }));
    points[0] = { x: 0.8, y: 1.5 };
    points[1] = { x: -0.8, y: 1.5 };
    component.onPlanChange({ seriesId: 'wheels', points, changed: [0, 1] });
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.op).toBe('bundle');
    expect(change.changes.length).toBe(2);
    expect(change.changes[0].id).toBe(`${ID}/car_types/0/wheels/0/position`);
    expect(change.changes[0].newValue.x).toBe(1.5);
    expect(change.changes[0].newValue.y).toBe(0.8);
  });

  it("keeps the game's box inertia and edits the sound tables", () => {
    expect(component.tensorMatchesBox).toBeTrue();
    const points = component.sampleSeries[1].points.map(p => ({ ...p }));
    points[0] = { ...points[0], y: 1.5 };
    component.onSoundChange({ seriesId: 'sample_volumes', points, changed: [0] });
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.id).toBe(`${ID}/car_types/0/engine_sound/sample_volumes`);
    expect(change.newValue[0]).toBe(1.5);
  });

  it('edits camera pitches in degrees', () => {
    component.setPitch('views', 1, 'pitch', '90');
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.id).toBe(`${ID}/car_types/0/camera/views/1/pitch`);
    expect(change.newValue).toBe(0x4000);
  });
});
