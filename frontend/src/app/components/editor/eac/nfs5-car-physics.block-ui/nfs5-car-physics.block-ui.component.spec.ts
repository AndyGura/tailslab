import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BehaviorSubject, Subject } from 'rxjs';
import { Nfs5CarPhysicsBlockUiComponent } from './nfs5-car-physics.block-ui.component';
import { MainService } from '../../../../services/main.service';
import { ChangesService } from '../../../../services/changes.service';
import {
  nfs5DragAt,
  nfs5DragModel,
  nfs5GearTorque,
  nfs5SimRpmPerMps,
  nfs5SteeringLock,
  nfs5TopGearSkipped,
  nfs5TorqueActiveCount,
  nfs5TorqueAt,
  nfs5TyreCircumference,
} from './nfs5-car-physics';
import { pathToResourceId, resourcePath } from './nfs5-files';

// GameData/Simulation/CarData/993coupe36.sim as parsed
export const nfs5Sim993 = (): { [key: string]: any } => ({
  name: '1994 993 Carrera 3.6L',
  mass: 1370.0,
  wheelbase: 2272.0,
  engine_position: 0,
  ai_speed_slot_scale: 1.0,
  ai_steer_lookahead: 1.0,
  ai_corner_scale: 1.0,
  aspiration: 0,
  forward_gears: 6,
  shift_time: 6,
  gear_acceleration_factor: 90.0,
  front_drive_share: 0.0,
  gear_ratios: [-2.86, 0.0, 3.82, 2.15, 1.56, 1.24, 1.02, 0.82],
  final_drive: 3.444,
  tyre_width: 245.0,
  tyre_aspect_ratio: 45.0,
  rim_diameter: 16.0,
  top_speed: 168.0,
  redline: 6700.0,
  engine_braking: 20.0,
  torque_curve: [
    122.0, 138.0, 150.0, 165.0, 201.0, 209.0, 209.0, 209.0, 224.0, 240.0, 243.0, 240.0, 232.0, 207.0, 161.0, 0.0, 0.0,
    0.0, 0.0, 0.0, 0.0,
  ],
  front_weight_share: 46.0,
  grip: 1.9,
  load_transfer_lever: 30.0,
  steering_lock: 16.5,
  toe: 0.0,
  brake_force: 9.5,
  front_brake_share: 60.0,
  front_downforce: 1.0,
  rear_downforce: 1.1,
  damping_1: 77.5,
  damping_2: 75.0,
  spring_load_transfer: 1.0,
  ride_height: 0.0,
  suspension_travel: 110.0,
  pitch_gain: 3.0,
  roll_gain: 2.0,
  lateral_load_transfer_divisor: 1.0,
  pitch_rate_limit: 1.0,
  roll_rate_limit: 1.0,
});

describe('NFS5 car physics helpers', () => {
  it('computes the tyre circumference like the loader', () => {
    // ((45 x 0.02) x 245 + 16 x 25.4) x 0.0031416
    expect(nfs5TyreCircumference(245, 45, 16)).toBeCloseTo((0.9 * 245 + 406.4) * 0.0031416, 9);
  });

  it('reads the torque curve at the rpm clamped to the redline', () => {
    const t = nfs5Sim993()['torque_curve'];
    expect(nfs5TorqueAt(t, 5000, 6700)).toBe(243);
    expect(nfs5TorqueAt(t, 5250, 6700)).toBeCloseTo((243 + 240) / 2, 6);
    // above the redline the engine reads the curve at the redline
    expect(nfs5TorqueAt(t, 9000, 6700)).toBeCloseTo(nfs5TorqueAt(t, 6700, 6700), 6);
    expect(nfs5TorqueAt(t, -100, 6700)).toBe(122);
    expect(nfs5TorqueActiveCount(6700)).toBe(15);
  });

  it('turns gear ratios into rpm per m/s and drive per lb·ft', () => {
    const d = nfs5Sim993();
    const c = nfs5TyreCircumference(245, 45, 16);
    const rpm = nfs5SimRpmPerMps(d);
    expect(rpm[2]).toBeCloseTo((3.444 * 3.82 * 60) / c, 6);
    expect(nfs5GearTorque(rpm[2], 1370, 90, false)).toBeCloseTo((rpm[2] / 1370) * 0.1 * 0.9, 9);
    expect(nfs5GearTorque(rpm[2], 1370, 90, true)).toBeCloseTo((rpm[2] / 1370) * 0.1 * 0.9 * 1.05, 9);
  });

  it('balances the air drag against the top gear at the top speed', () => {
    const d = nfs5Sim993();
    const model = nfs5DragModel(d, false)!;
    const top = 168 * 0.446428567;
    const rpm6 = nfs5SimRpmPerMps(d)[7];
    expect(model.rpm).toBe(Math.trunc(rpm6 * top));
    const drive = nfs5TorqueAt(d['torque_curve'], model.rpm, 6700) * nfs5GearTorque(rpm6, 1370, 90, false);
    expect(nfs5DragAt(model, top)).toBeCloseTo(drive, 9);
    expect(nfs5DragAt(model, top / 2)).toBeCloseTo(drive / 8, 9);
  });

  it('skips the top gear only when the gear below reaches the top speed', () => {
    const d = nfs5Sim993();
    expect(nfs5TopGearSkipped(d)).toBeFalse();
    d['top_speed'] = 100;
    expect(nfs5TopGearSkipped(d)).toBeTrue();
  });

  it('opens the steering lock at low speed and closes it above 80 m/s', () => {
    // at a standstill 16.5 x 1.75 = 28.875, capped at 20, x 17 / 16.5
    expect(nfs5SteeringLock(16.5, 0)).toBeCloseTo(20 * (17 / 16.5), 6);
    expect(nfs5SteeringLock(16.5, 40)).toBeCloseTo(17, 6);
    expect(nfs5SteeringLock(16.5, 100)).toBeCloseTo(17 / 1.25, 6);
  });

  it('maps resource ids and paths like the backend', () => {
    expect(resourcePath('C---DRIVE/Games/my_%5Fdir/nfs5.car__cars/3')).toBe('C:/Games/my__dir/nfs5.car');
    expect(pathToResourceId('C:\\Games\\my__dir\\nfs5.prt')).toBe('C---DRIVE/Games/my_%5Fdir/nfs5.prt');
  });
});

describe('Nfs5CarPhysicsBlockUiComponent', () => {
  let fixture: ComponentFixture<Nfs5CarPhysicsBlockUiComponent>;
  let component: Nfs5CarPhysicsBlockUiComponent;
  let appendChanges: jasmine.Spy;

  beforeEach(async () => {
    appendChanges = jasmine.createSpy('appendChanges').and.returnValue(Promise.resolve());
    await TestBed.configureTestingModule({
      imports: [Nfs5CarPhysicsBlockUiComponent],
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
    fixture = TestBed.createComponent(Nfs5CarPhysicsBlockUiComponent);
    component = fixture.componentInstance;
    component.resourceId = '/games/nfs5/GameData/Simulation/CarData/993coupe36.sim';
    component.resourceSchema = { block_class_mro: 'Nfs5CarPhysics__DeclarativeCompoundBlock', fields: [] };
    component.resourceData = nfs5Sim993();
    fixture.detectChanges();
  });

  it('summarizes the car', () => {
    const tile = (label: string) => component.tiles.find(t => t.label === label)!;
    expect(tile('Redline').value).toBe('6,700 rpm');
    expect(tile('Mass').value).toBe('1,370 kg');
    // 168 mph x 0.446428567 x 3.6
    expect(tile('Top speed').value).toBe('270 km/h');
    expect(tile('Drivetrain').value).toBe('RWD');
    expect(tile('Peak torque').value).toBe('243 lb·ft');
    // 240 lb·ft at 6000 rpm: 274 hp
    expect(component.peak().power.rpm).toBe(6000);
  });

  it('lists the gears with the automatic gearbox', () => {
    expect(component.gears.length).toBe(8);
    const first = component.gears[2];
    expect(first.redlineSpeed).toBeCloseTo((6700 / first.rpmPerMps) * 3.6, 6);
    expect(first.upshiftSpeed!).toBeCloseTo(((6700 * 0.9) / first.rpmPerMps) * 3.6, 6);
    expect(component.gears[3].downshiftSpeed!).toBeCloseTo(((6700 * 0.8) / first.rpmPerMps) * 3.6, 6);
    // the top gear never shifts up
    expect(component.gears[7].upshiftSpeed).toBeNull();
  });

  it('runs an idealized speed run', () => {
    expect(component.run!.to100).not.toBeNull();
    expect(component.run!.to100!).toBeGreaterThan(3);
    expect(component.run!.to100!).toBeLessThan(10);
    // never faster than the top speed
    expect(component.run!.topSpeed).toBeLessThan(168 * 0.446428567 + 0.01);
  });

  it('writes a dragged gear line as a ratio that reaches that speed at the redline', () => {
    const kmh = 100;
    const r = component.ratioForSpeed(kmh);
    const c = component.circumference;
    expect((6700 / ((3.444 * r * 60) / c)) * 3.6).toBeCloseTo(kmh, 1);
    component.onGearChange({
      seriesId: 'gear-2',
      points: [
        { x: 0, y: 0 },
        { x: kmh, y: 6700 },
      ],
      changed: [1],
    });
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.id).toBe('/games/nfs5/GameData/Simulation/CarData/993coupe36.sim__gear_ratios/2');
    expect(change.newValue).toBe(r);
  });

  it('scales the torque curve from the peak torque tile', () => {
    component.onTileChange({ id: 'peak_torque', value: 486 });
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.id).toBe('/games/nfs5/GameData/Simulation/CarData/993coupe36.sim__torque_curve');
    expect(change.newValue[10]).toBe(486);
    expect(change.newValue[0]).toBe(244);
  });

  it('stores the top speed in mph', () => {
    component.onTileChange({ id: 'top_speed', value: 300 });
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.newValue).toBeCloseTo(300 / 3.6 / 0.446428567, 2);
  });
});
