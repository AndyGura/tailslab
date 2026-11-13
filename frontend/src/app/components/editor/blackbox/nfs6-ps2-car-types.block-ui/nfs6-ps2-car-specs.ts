// NFS Hot Pursuit 2 (PS2) car types table (GLOBALB chunk 0x34600, `Nfs6Ps2CarTypeInfo`): the executable's formulas
// over its values (SLUS_203.62 addresses; nfs-web's C port src/nfs6/nfs6-physics). Units: tonnes, metres, seconds,
// kN and kN·m (the torque curves work as kN·m with the mass in tonnes), rpm, speed limiter in mph

export type Nfs6Ps2Engine = {
  idle_rpm: number;
  redline_rpm: number;
  max_rpm: number;
  inertia: number;
  torque_curve: number[];
  friction_curve: number[];
};

export type Nfs6Ps2DriveTrain = {
  shift_up_fraction: number;
  front_final_drive: number;
  rear_final_drive: number;
  rear_torque_split: number;
  num_gears: number;
  gear_ratios: number[];
};

export const RPM_TO_RAD = Math.PI / 30;
export const MPS_TO_MPH = 2.236025; // 0x32e55c (3600 / 1610), the speed limiter's
export const HP_TORQUE_FACTOR = 1.05; // 0x3308a4
export const HP_SPEED_LIMIT_FACTOR = 1.03; // 0x330b60
export const SPEED_LIMIT_OFFSET = 1.9; // 0x32e558, mph
export const REV_LIMIT_FACTOR = -15; // 0x3308a0: from max_rpm - 100
export const SHIFT_POINT_SCALE = 0.95; // 0x3308ac (DriveTrainShiftPointScale)
export const SHIFT_DOWN_FACTOR = 0.95; // 0x3308b0
export const REAR_DRIVEN_MIN_SPLIT = 0.001; // 0x32e33c
export const FRONT_DRIVEN_MAX_SPLIT = 0.999; // 0x32e340
// RealDriver::DoSteering's max front wheel angle (degrees) over the forward speed 0..160 m/s, before steering_scale
export const STEER_MAX_ANGLE_PAD = [45, 13, 8, 5.5, 4.2, 3.6, 3.1, 2.9, 2.9, 2.9]; // 0x2f0770
export const STEER_MAX_ANGLE_WHEEL = [45, 15, 11, 9, 8, 7, 6, 6, 6, 6]; // 0x2f0748
export const STEER_TABLE_MAX_SPEED = 160;
// the HUD tachometer's angles without the car's own ones (HUD flag 0x20 clear, 0x17f040)
export const ENGINE_SAMPLES = [
  'lelo',
  'lemd',
  'lehi',
  'lxlo',
  'lxmd',
  'lxhi',
  'ceid',
  'cemd',
  'cehi',
  'cxid',
  'cxmd',
  'cxhi',
];
export const VIEW_TYPES = ['bumper', 'in_car', 'chase'];
export const LOCATIONS = ['Location 0', 'Location 1', 'Location 2', 'Location 3', 'Location 4'];

// Table::GetValue 0x18f838: `data` evenly spaced from min to max, clamped, linear between the points
export function tableValue(data: number[], min: number, max: number, x: number): number {
  const n = data.length;
  if (!n) return 0;
  if (n === 1 || max <= min) return data[0];
  x = Math.max(min, Math.min(max, x));
  const t = ((x - min) * (n - 1)) / (max - min);
  const i = Math.floor(t);
  if (i >= n - 1) return data[n - 1];
  return data[i] + (data[i + 1] - data[i]) * (t - i);
}

// x of point i of a curve over idle..max rpm
export const curveRpm = (e: Nfs6Ps2Engine, i: number, count: number) =>
  count > 1 ? e.idle_rpm + ((e.max_rpm - e.idle_rpm) * i) / (count - 1) : e.idle_rpm;

// Engine::GetEngineTorque 0x18ab70 at full throttle, no catch-up: the curve (x 1.05 for HP), x -15 from max - 100
export function engineTorque(e: Nfs6Ps2Engine, rpm: number, isHp: boolean = false): number {
  let t = tableValue(e.torque_curve, e.idle_rpm, e.max_rpm, rpm);
  if (isHp) t *= HP_TORQUE_FACTOR;
  if (e.max_rpm - 100 <= rpm) t *= REV_LIMIT_FACTOR;
  return t;
}

export const frictionTorque = (e: Nfs6Ps2Engine, rpm: number) =>
  tableValue(e.friction_curve, e.idle_rpm, e.max_rpm, rpm);

// power (kW with the torque in kN·m)
export const powerKw = (torque: number, rpm: number) => torque * rpm * RPM_TO_RAD;

// peak torque and power over the curve below the rev limiter, 50 rpm steps
export function enginePeaks(e: Nfs6Ps2Engine, isHp: boolean = false) {
  let torque = { value: 0, rpm: e.idle_rpm };
  let power = { value: 0, rpm: e.idle_rpm };
  for (let rpm = e.idle_rpm; rpm < e.max_rpm - 100; rpm += 50) {
    const t = engineTorque(e, rpm, isHp);
    if (t > torque.value) torque = { value: t, rpm };
    const p = powerKw(t, rpm);
    if (p > power.value) power = { value: p, rpm };
  }
  return { torque, power };
}

export const topGear = (d: Nfs6Ps2DriveTrain) => Math.max(2, Math.min(7, (d.num_gears | 0) + 1));

// CalculateShiftPoints 0x18ac38 with UseOptimalShiftPoints 1 (0x3308b4) and the DriveTrain's scale 0.95: up[g] for
// the forward gears 2..top (top: max_rpm), down[g] for 3..top
export function shiftPoints(d: Nfs6Ps2DriveTrain, e: Nfs6Ps2Engine, optimal: boolean = true) {
  const up: number[] = [];
  const down: number[] = [];
  const top = topGear(d);
  const torque = (rpm: number) => tableValue(e.torque_curve, e.idle_rpm, e.max_rpm, rpm);
  for (let g = 2; g < top; g++) {
    const r = d.gear_ratios[g];
    const next = d.gear_ratios[g + 1];
    let u: number;
    if (!optimal) {
      u = d.shift_up_fraction * (e.redline_rpm - e.idle_rpm) + e.idle_rpm;
    } else {
      const limit = e.max_rpm - 200;
      let found: number | null = null;
      for (let rpm = (e.idle_rpm + e.max_rpm) * 0.5; rpm < limit && found === null; rpm += 50) {
        if (r && torque(rpm) < (torque((rpm * next) / r) * next) / r) found = rpm;
      }
      u = (found ?? e.max_rpm - 200) * SHIFT_POINT_SCALE;
    }
    up[g] = u;
    down[g + 1] = r ? (SHIFT_DOWN_FACTOR * u * next) / r : 0;
  }
  up[top] = e.max_rpm;
  return { up, down };
}

export const rearDriven = (d: Nfs6Ps2DriveTrain) => REAR_DRIVEN_MIN_SPLIT <= d.rear_torque_split;
export const frontDriven = (d: Nfs6Ps2DriveTrain) => d.rear_torque_split <= FRONT_DRIVEN_MAX_SPLIT;

// DriveTrain::GetDifferentialAngularVelocity 0x18b008 without wheel slip: clutch side rad/s per m/s of road speed in
// gear 1 (the mean of the driven axles' w x final drive), `radii` = [front, rear] wheel radius
export function clutchRadPerMps(d: Nfs6Ps2DriveTrain, radii: [number, number]): number {
  const rear = rearDriven(d) ? d.rear_final_drive / (radii[1] || 1) : 0;
  const front = frontDriven(d) ? d.front_final_drive / (radii[0] || 1) : 0;
  return rearDriven(d) && frontDriven(d) ? (rear + front) / 2 : rear + front;
}

// road speed (m/s) at `rpm` in gear g
export function speedAt(d: Nfs6Ps2DriveTrain, radii: [number, number], gear: number, rpm: number): number {
  const k = clutchRadPerMps(d, radii) * Math.abs(d.gear_ratios[gear] || 0);
  return k > 0 ? (rpm * RPM_TO_RAD) / k : 0;
}

// drive force (kN) at the wheels in gear g at `rpm`, full throttle, no slip, no losses
export function driveForce(
  d: Nfs6Ps2DriveTrain,
  e: Nfs6Ps2Engine,
  radii: [number, number],
  gear: number,
  rpm: number,
  isHp: boolean = false,
): number {
  return engineTorque(e, rpm, isHp) * Math.abs(d.gear_ratios[gear] || 0) * clutchRadPerMps(d, radii);
}

// Aerodynamics::ResolveForces 0x1add70: drag (kN) = v² x drag x (2 - throttle)
export const dragForce = (drag: number, v: number, throttle: number = 1) => v * v * drag * (2 - throttle);

// RigidBody::GetDerivative 0x19d4d0 on the flat without catch-up: the speed limit in mph (0: none)
export const speedLimitMph = (limiter: number, isHp: boolean) =>
  limiter ? (limiter + SPEED_LIMIT_OFFSET) * (isHp ? HP_SPEED_LIMIT_FACTOR : 1) : 0;

// the front end's grid order (0x185fe8): highest torque point / mass x first gear x rear final drive / rear radius
export function gridScore(e: Nfs6Ps2Engine, d: Nfs6Ps2DriveTrain, mass: number, rearRadius: number): number {
  const peak = Math.max(0, ...(e.torque_curve || []));
  return mass && rearRadius ? ((peak / mass) * (d.gear_ratios[2] || 0) * d.rear_final_drive) / rearRadius : 0;
}

// estimated top speed (m/s): the lowest of the speed limiter, the top gear at max rpm and the speed where the drive
// force of the best gear meets the air drag (ground forces and slip left out)
export function topSpeedEstimate(
  d: Nfs6Ps2DriveTrain,
  e: Nfs6Ps2Engine,
  radii: [number, number],
  drag: number,
  limiterMph: number,
  isHp: boolean,
) {
  const top = topGear(d);
  const gearLimit = speedAt(d, radii, top, e.max_rpm - 100);
  let dragLimit = Infinity;
  if (drag > 0) {
    for (let v = 1; v < 200; v += 0.25) {
      let best = 0;
      for (let g = 2; g <= top; g++) {
        const k = clutchRadPerMps(d, radii) * Math.abs(d.gear_ratios[g] || 0);
        if (!k) continue;
        // below idle the clutch slips with the engine at idle at least
        const rpm = Math.max(e.idle_rpm, (v * k) / RPM_TO_RAD);
        if (rpm >= e.max_rpm - 100) continue;
        best = Math.max(best, driveForce(d, e, radii, g, rpm, isHp));
      }
      if (best <= dragForce(drag, v)) {
        dragLimit = v;
        break;
      }
    }
  }
  const limit = speedLimitMph(limiterMph, isHp) / MPS_TO_MPH || Infinity;
  const value = Math.min(limit, gearLimit || Infinity, dragLimit);
  const by = value === limit ? 'limiter' : value === dragLimit ? 'drag' : 'gearing';
  return { value: isFinite(value) ? value : 0, by };
}

// RealDriver::DoSteering's front wheel angle at full lock (degrees) at a forward speed (m/s)
export const maxWheelAngle = (speed: number, steeringScale: number, wheel: boolean) =>
  tableValue(wheel ? STEER_MAX_ANGLE_WHEEL : STEER_MAX_ANGLE_PAD, 0, STEER_TABLE_MAX_SPEED, speed) * steeringScale;

// turning circle radius (m) of the front wheel angle, Ackermann
export const turningRadius = (wheelbase: number, angleDeg: number) =>
  angleDeg > 0 ? wheelbase / Math.tan((angleDeg * Math.PI) / 180) : Infinity;

// Suspension::ComputeAuxiliaries 0x1a5fc0: spring force at a height (m, compression positive), without damping
export const springForce = (stiffness: number, progression: number, height: number) =>
  height * stiffness * (1 + progression * Math.max(height, 0));

// the diagonal of the inertia tensor of every car type: the box formula of the dimensions, yaw doubled
export const boxInertia = (mass: number, l: number, w: number, h: number) => [
  (mass / 12) * (w * w + h * h),
  (mass / 12) * (l * l + h * h),
  ((2 * mass) / 12) * (l * l + w * w),
];

// the HUD speedometer / tachometer needle angle (degrees) of a value on a scale (0x17f040)
export function needleAngle(value: number, min: number, max: number, minAngle: number, maxAngle: number): number {
  let f = max > min ? (value - min) / (max - min) : 0;
  f = Math.max(0, Math.min(1, f));
  const span = minAngle < maxAngle ? maxAngle - minAngle : 360 - minAngle + maxAngle;
  let a = minAngle + f * span;
  if (a > 360) a -= 360;
  return a;
}

// PlayerEngineSound::UpdateEngine 0x210bf8: sample pitch (octaves) at an rpm position 0..127
export const samplePitchOctaves = (pitchOffset: number, samplePitch: number, rpmPitch: number, position: number) =>
  (pitchOffset + samplePitch + ((Math.trunc(position) - 64) * rpmPitch) / 64) / 1200;

// 16-bit angle to degrees
export const angle16ToDeg = (a: number) => (a * 360) / 0x10000;
