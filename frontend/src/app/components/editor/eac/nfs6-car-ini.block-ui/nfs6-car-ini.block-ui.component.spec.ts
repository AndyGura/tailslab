import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BehaviorSubject, Subject } from 'rxjs';
import { MainService } from '../../../../services/main.service';
import { ChangesService } from '../../../../services/changes.service';
import { Nfs6CarIniBlockUiComponent } from './nfs6-car-ini.block-ui.component';
import {
  driveForce,
  driveLayout,
  gameTorqueCurve,
  nfs6Car,
  rpmPerMps,
  shiftSpeed,
  steeringLimit,
  steeringLockDeg,
  tireRadius,
  topSpeed,
  torqueAt,
} from './nfs6-car-specs';

// Cars/911t/car.ini as TailsLab reads it (keys the file has)
export const car911t = (): any => ({
  basic: {
    Mass: 1439.0,
    BodyShape: 6,
    WheelBase: 2.35,
    FrontTrackWidth: 1.465,
    RearTrackWidth: 1.522,
    VehicleHeight: 1.214,
    HeightOfGravity: 0.3517,
    RearSlideFactor: 0.0,
    FrontGripBias: 0.48,
    AeroDragCoefficient: 0.31,
    AeroFrontDownforceCoefficient: 9.0,
    AeroRearDownforceCoefficient: 10.0,
    BodyLiftCoefficient: 0.0,
    UnderBodyDragCoefficient: 8.0,
    SpeedGovernor: 0.0,
    TurningCircleRadius: 5.0,
    TurninRamp: 12.0,
    TurnoutRamp: 24.0,
    BaseDampingVelocity: 10.0,
    RangeDampingVelocity: 25.0,
    DampingLimit: 0.28,
    FrontDriveRatio: 0.4,
    driveWheels: [1, 1, 1, 1],
    YawInertiaFactor: 1.0,
    FrontRollStiffness: 2700.0,
    RearRollStiffness: 2800.0,
    AntiDive: 0.38,
    AntiSquat: 0.38,
    FrontAntiRoll: 0.85,
    RearAntiRoll: 0.75,
    Damper: 0.45,
    TravelFront: 0.3,
    TravelRear: 0.3,
    MaterialType: 4,
  },
  engineblock: {
    FlyWheelInertiaFactor: 1.0,
    MinRPM: 1500,
    RedLine: 7500,
    WarningLine: 6500,
    torqueCurve: [
      0.0,
      0.0,
      280.0,
      380.0,
      505.0,
      520.0,
      520.0,
      520.0,
      520.0,
      520.0,
      515.0,
      507.0,
      500.0,
      430.0,
      380.0,
      0.0,
      0.0,
      0.0,
      0.0,
      0.0,
      0.0,
      0.0,
      0.0,
      0.0,
      null,
    ],
  },
  transmission: {
    NumberOfGears: 8,
    GearShiftDelay: 4,
    Automatic: 1,
    GearRatios: [3.82, 0.0, 3.82, 2.05, 1.41, 1.12, 0.92, 0.75],
    GearEfficiency: [0.9, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
    TorqueConverterRatio: 1.5,
    TorqueConverterMaxRPM: 3000,
    GearShiftPointCoefficient: 0.95,
  },
  rearend: {
    FinalGearRatio: 3.44,
    FrontFinalGearRatio: 3.44,
  },
  tire_front: {
    TypeCode: 10,
    attach: 10,
    SectionWidth: 225,
    AspectRatio: 40,
    WheelDiameter: 18,
    RollingResistanceFactor: 0.9,
    PeakFriction: 1.6,
    ForceScale: 1.15,
    SlipAngleScale: 1.0,
    AligningMomentScale: 1.0,
    SlipRatio: 1.0,
    MaxRenderTravelUp: 0.0,
  },
  tire_rear: {
    TypeCode: 10,
    attach: 11,
    SectionWidth: 295,
    AspectRatio: 30,
    WheelDiameter: 18,
    RollingResistanceFactor: 0.9,
    PeakFriction: 1.6,
    ForceScale: 1.15,
    SlipAngleScale: 1.0,
    AligningMomentScale: 1.0,
    SlipRatio: 1.0,
    MaxRenderTravelUp: 0.0,
  },
});

describe('nfs6-car-specs', () => {
  it('fills the torque curve past its last entry as CarIni_ReadEngine does', () => {
    const curve = gameTorqueCurve([100, 200, 150, null]);
    expect(curve.slice(0, 3)).toEqual([100, 200, 150]);
    // last decrease ratio 0.75, squared each entry
    expect(curve[3]).toBeCloseTo(150 * 0.75, 6);
    expect(curve[4]).toBeCloseTo(150 * 0.75 * 0.5625, 6);
    expect(curve.length).toBe(25);
    // without a decrease: 0.8
    expect(gameTorqueCurve([100, 200])[2]).toBeCloseTo(160, 6);
  });

  it('interpolates the torque every 500 rpm', () => {
    const curve = gameTorqueCurve([0, 0, 280, 380]);
    expect(torqueAt(curve, 1000, 7500)).toBe(280);
    expect(torqueAt(curve, 1250, 7500)).toBeCloseTo(330, 6);
  });

  it('computes the tyre radius and gearing like the exe', () => {
    expect(tireRadius(295, 30, 18)).toBeCloseTo(0.3171, 6);
    const car = nfs6Car(car911t());
    expect(car.mass).toBe(1439 + 40);
    expect(car.rearRadius).toBeCloseTo(0.3171, 6);
    expect(rpmPerMps(car, 2)).toBeCloseTo(395.7281506, 4);
    expect(rpmPerMps(car, 0)).toBeLessThan(0);
    expect(rpmPerMps(car, 1)).toBe(0);
    // 20 m/s in 1st: 7914 rpm, past the red line: no drive
    expect(driveForce(car, 2, 20)).toBe(0);
    expect(driveForce(car, 2, 10)).toBeGreaterThan(0);
    expect(steeringLockDeg(car)).toBeCloseTo((Math.atan(2.35 / 5) * 180) / Math.PI, 6);
  });

  it('derives shift speeds, top speed and the steering limit', () => {
    const car = nfs6Car(car911t());
    const s2 = shiftSpeed(car, 2);
    expect(s2).toBeGreaterThan(0);
    expect(s2 * rpmPerMps(car, 2)).toBeLessThanOrEqual(car.redLine * 1.2);
    const top = topSpeed(car);
    expect(top * 3.6).toBeGreaterThan(250);
    expect(top * 3.6).toBeLessThan(340);
    expect(steeringLimit(car, 0)).toBe(1);
    expect(steeringLimit(car, 100)).toBeCloseTo(car.dampingLimit, 6);
    expect(driveLayout([1, 1, 1, 1], 0.4)).toEqual({ name: 'AWD', front: 0.4 });
    expect(driveLayout([0, 0, 0, 0], 0.4).name).toBe('RWD');
    expect(driveLayout([1, 1, 0, 0], 0).name).toBe('FWD');
  });
});

describe('Nfs6CarIniBlockUiComponent', () => {
  let fixture: ComponentFixture<Nfs6CarIniBlockUiComponent>;
  let component: Nfs6CarIniBlockUiComponent;
  let appendChanges: jasmine.Spy;

  beforeEach(async () => {
    appendChanges = jasmine.createSpy('appendChanges').and.returnValue(Promise.resolve());
    await TestBed.configureTestingModule({
      declarations: [Nfs6CarIniBlockUiComponent],
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
    fixture = TestBed.createComponent(Nfs6CarIniBlockUiComponent);
    component = fixture.componentInstance;
    component.resourceId = 'car.ini';
    component.resourceSchema = { block_class_mro: 'Nfs6CarIni__IniFile__DataBlock', fields: [] };
    component.resourceData = car911t();
    fixture.detectChanges();
  });

  it('summarizes the car', () => {
    const labels = component.tiles.map(t => t.label);
    expect(labels).toContain('Peak power');
    expect(component.tiles.find(t => t.label === 'Drive')!.value).toBe('AWD');
    expect(component.tiles.find(t => t.label === 'Mass')!.value).toBe('1,479 kg');
    expect(component.gears.length).toBe(8);
    expect(component.torqueSeries[0].points.length).toBe(25);
    expect(component.tires[1].size).toBe('295/30 R18');
  });

  it('writes a dragged torque point as one change', () => {
    const points = component.torqueSeries[0].points.map(p => ({ ...p }));
    points[5] = { x: 2500, y: 600 };
    component.onTorqueChange({ seriesId: 'torque', points, changed: [5] });
    expect(appendChanges).toHaveBeenCalledTimes(1);
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.op).toBe('set');
    expect(change.id).toBe('car.ini__engineblock/torqueCurve');
    expect(change.newValue[5]).toBe(600);
    expect(change.newValue[4]).toBe(505);
    expect(change.newValue[24]).toBeNull();
  });

  it('sets a missing gear value to null', () => {
    component.onGearInput('GearRatios', 7, '');
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.newValue[7]).toBeNull();
  });
});
