// NFS5 (Porsche Unleashed) car physics as Porsche.exe computes it, ported in nfs-web (src/nfs5/nfs5-physics, cars.c
// and physics.c). The helpers take the .sim values as the file stores them (Nfs5CarPhysics) and apply the loader's
// scaling (Cars_LoadSpecs 0x49c6c0) themselves; float32 constants of the exe are given as their float values

// torque curve: 21 entries 500 rpm apart, read at rpm x 0.002 (0x49e440)
export const NFS5_TORQUE_STEP = 500;
export const NFS5_TORQUE_LENGTH = 21;
// the .sim torque is in lb·ft (the 993 Carrera: 243, 330 N·m), power in hp = lb·ft x rpm / 5252
export const LBFT_TO_NM = 1.3558179;
export const HP_PER_LBFT_RPM = 1 / 5252.113;
// the loader's mph to m/s factor (0x3ee49249, 0x49c6c0)
export const NFS5_MPH_TO_MPS = 0.446428567;
// physics steps per second: every 2nd tick of the 64 Hz simulation (Sim_Tick 0x414ff0)
export const NFS5_STEPS = 32;
// gear slots: reverse, neutral, 1st..6th
export const NFS5_GEAR_SLOTS = 8;
export const NFS5_GEAR_NAMES = ['R', 'N', '1st', '2nd', '3rd', '4th', '5th', '6th'];
// the automatic gearbox (0x49daf0): up above 0.9 x redline + a random 0..0.1 x redline, down when the gear below
// would turn below 0.8 x redline
export const NFS5_UPSHIFT = 0.9;
export const NFS5_UPSHIFT_RANDOM = 0.1;
export const NFS5_DOWNSHIFT = 0.8;
// the rev limiter (0x49e440): the target rpm is (redline + 100) x gas, + 250 in neutral; at the redline the gas is cut
export const NFS5_REV_LIMIT_DRIVE = 100;
export const NFS5_REV_LIMIT_NEUTRAL = 250;
// turbo boost (0x49e440): type 1 builds from 1/4 to 1/2 of the redline, type 2 from 1/6 to 2/3
export const NFS5_BOOST_RANGES: { [type: number]: [number, number] } = { 1: [0.25, 0.5], 2: [1 / 6, 2 / 3] };
// brakes (0x49f160): brake force x pedal, at most 32 x |forward speed|
export const NFS5_BRAKE_SPEED_CAP = 32;
// downforce (0x4a1900): wheel load + downforce x forward speed, above 5 m/s
export const NFS5_DOWNFORCE_MIN_SPEED = 5;
// wheel loads (0x4a1900): W = grip x 9.8, each wheel W x 0.5 x its axle's weight share
export const NFS5_G = 9.8;
// steering (0x49f160): the lock grows below 30 m/s (x 1.75 - speed x 0.025), at most 20, x 17 / lock; above 80 m/s
// / (speed x 0.0125)
export const NFS5_STEER = { slowSpeed: 30, slowFactor: 1.75, slowSlope: 0.025, max: 20, scale: 17, fastSpeed: 80 };

export type Nfs5Sim = { [field: string]: any };

// tyre circumference in m (specs+0x148, 0x49cb50): ((aspect x 0.02) x width + rim x 25.4) x 0.0031416
export function nfs5TyreCircumference(width: number, aspect: number, rim: number): number {
  return (aspect * 0.02 * width + rim * 25.4) * 0.0031416;
}

export function nfs5SimCircumference(d: Nfs5Sim): number {
  return nfs5TyreCircumference(d['tyre_width'] || 0, d['tyre_aspect_ratio'] || 0, d['rim_diameter'] || 0);
}

// engine rpm per m/s of a gear (0x49cb50): final drive x ratio x 60 / tyre circumference
export function nfs5RpmPerMps(ratio: number, finalDrive: number, circumference: number): number {
  return circumference > 0 ? (finalDrive * ratio * 60) / circumference : 0;
}

export function nfs5SimRpmPerMps(d: Nfs5Sim, ratios: number[] = d['gear_ratios'] || []): number[] {
  const c = nfs5SimCircumference(d);
  return ratios.map(r => nfs5RpmPerMps(r || 0, d['final_drive'] || 0, c));
}

// forward gears: the .sim count, at most the 6 slots
export function nfs5ForwardGears(d: Nfs5Sim): number {
  return Math.max(0, Math.min(NFS5_GEAR_SLOTS - 2, d['forward_gears'] || 0));
}

// the torque the engine reads at an rpm (0x49e440): the rpm clamped to 0..redline, the entry trunc(rpm x 0.002) and
// the next one interpolated. Entries past the one after the redline are never read
export function nfs5TorqueAt(torques: number[], rpm: number, redline: number): number {
  const r = Math.max(0, Math.min(redline, rpm));
  const i = Math.min(NFS5_TORQUE_LENGTH - 1, Math.trunc(r * 0.002));
  const t0 = torques[i] || 0;
  const t1 = torques[Math.min(NFS5_TORQUE_LENGTH - 1, i + 1)] || 0;
  return (r - i * NFS5_TORQUE_STEP) * 0.002 * (t1 - t0) + t0;
}

// torque entries the engine can read: up to the one after the redline
export function nfs5TorqueActiveCount(redline: number): number {
  return Math.max(1, Math.min(NFS5_TORQUE_LENGTH, Math.trunc(Math.max(0, redline) * 0.002) + 2));
}

export function nfs5PowerHp(torqueLbft: number, rpm: number): number {
  return torqueLbft * rpm * HP_PER_LBFT_RPM;
}

// drive acceleration of a gear per lb·ft of torque (specs+0x190, 0x49cb50): rpm per m/s / mass x 0.1 x the gear
// acceleration factor (.sim x 0.01), x 1.05 for a manual gearbox (car record transmission 0)
export function nfs5GearTorque(rpmPerMps: number, mass: number, gearAccelerationFactor: number, manual: boolean) {
  if (!mass) return 0;
  return (rpmPerMps / mass) * 0.1 * gearAccelerationFactor * 0.01 * (manual ? 1.05 : 1);
}

export type Nfs5DragModel = {
  // top speed in m/s
  topSpeed: number;
  // the rpm the coefficient is taken at (top gear at the top speed, at most the redline)
  rpm: number;
  // drag acceleration = coefficient x forward speed³ (specs+0x1b0)
  coefficient: number;
};

// the air drag (specs+0x1b0, 0x49cb50): the top gear's drive at the top speed (rpm = trunc(top gear rpm per m/s x
// top speed), clamped to 0..redline) / top speed³: the car stops accelerating at the top speed in the top gear
export function nfs5DragModel(d: Nfs5Sim, manual: boolean): Nfs5DragModel | null {
  const n = nfs5ForwardGears(d);
  const mass = d['mass'] || 0;
  const top = (d['top_speed'] || 0) * NFS5_MPH_TO_MPS;
  if (n < 1 || !mass || !(top > 0)) return null;
  const rpmPerMps = nfs5SimRpmPerMps(d)[n + 1] || 0;
  const redline = d['redline'] || 0;
  const rpm = Math.max(0, Math.min(redline, Math.trunc(rpmPerMps * top)));
  const drive = nfs5TorqueAt(d['torque_curve'] || [], rpm, redline);
  const k = nfs5GearTorque(rpmPerMps, mass, d['gear_acceleration_factor'] || 0, manual);
  return { topSpeed: top, rpm, coefficient: (drive * k) / (top * top * top) };
}

export function nfs5DragAt(model: Nfs5DragModel | null, speed: number): number {
  return model ? model.coefficient * speed * speed * speed : 0;
}

// the automatic gearbox never shifts into the top gear while the gear below it reaches the top speed before the
// redline (0x49daf0: specs+0x168[gear slots] x redline > specs+0x90)
export function nfs5TopGearSkipped(d: Nfs5Sim): boolean {
  const n = nfs5ForwardGears(d);
  if (n < 2) return false;
  const below = nfs5SimRpmPerMps(d)[n] || 0;
  const speedPerRpm = below ? 1 / below : 0.1;
  return speedPerRpm * (d['redline'] || 0) > (d['top_speed'] || 0) * NFS5_MPH_TO_MPS;
}

// the steering lock factor (0x49f160) at a forward speed in m/s; the front wheels turn by steering (-127..127) x it /
// 127, toe added to the left wheel and subtracted from the right one
export function nfs5SteeringLock(lock: number, speed: number): number {
  if (!(lock > 0)) return 0;
  let l = lock;
  if (speed < NFS5_STEER.slowSpeed) l = l * (NFS5_STEER.slowFactor - speed * NFS5_STEER.slowSlope);
  l = Math.min(NFS5_STEER.max, l);
  let v = l * (NFS5_STEER.scale / lock);
  if (speed > NFS5_STEER.fastSpeed) v = v / (speed * 0.0125);
  return v;
}

export type Nfs5SpeedRun = {
  // km/h by time (s)
  points: { x: number; y: number }[];
  to100: number | null;
  to160: number | null;
  // m/s
  topSpeed: number;
};

// An idealized run from standstill, full gas, automatic gearbox: each physics step the drive of the gear minus the air
// drag; no drive while a shift lasts (shift time steps); tyres, wheel spin, the clutch and the engine's own rpm
// dynamics left out
export function nfs5SpeedRun(d: Nfs5Sim, manual: boolean, seconds: number = 60): Nfs5SpeedRun {
  const n = nfs5ForwardGears(d);
  const mass = d['mass'] || 0;
  const redline = d['redline'] || 0;
  const torques: number[] = d['torque_curve'] || [];
  const rpmPerMps = nfs5SimRpmPerMps(d);
  const model = nfs5DragModel(d, manual);
  const gaf = d['gear_acceleration_factor'] || 0;
  const lastGear = n + 1 - (nfs5TopGearSkipped(d) ? 1 : 0);
  const shiftUp = redline * (NFS5_UPSHIFT + NFS5_UPSHIFT_RANDOM / 2);
  const dt = 1 / NFS5_STEPS;
  const points = [{ x: 0, y: 0 }];
  let v = 0;
  let gear = 2;
  let shifting = 0;
  let to100: number | null = null;
  let to160: number | null = null;
  if (n < 1 || !mass || !(redline > 0)) return { points, to100, to160, topSpeed: 0 };
  const steps = Math.round(seconds * NFS5_STEPS);
  for (let s = 1; s <= steps; s++) {
    let drive = 0;
    if (shifting > 0) {
      shifting--;
    } else {
      const ratio = rpmPerMps[gear] || 0;
      if (ratio * v > shiftUp && gear < lastGear) {
        gear++;
        shifting = d['shift_time'] || 0;
      } else {
        const rpm = Math.min(redline, ratio * v);
        drive = nfs5TorqueAt(torques, rpm, redline) * nfs5GearTorque(ratio, mass, gaf, manual);
        if (ratio * v >= redline) drive = 0;
      }
    }
    v = Math.max(0, v + (drive - nfs5DragAt(model, v)) * dt);
    const t = s * dt;
    if (to100 === null && v * 3.6 >= 100) to100 = t;
    if (to160 === null && v * 3.6 >= 160) to160 = t;
    if (s % 4 === 0) points.push({ x: t, y: v * 3.6 });
  }
  return { points, to100, to160, topSpeed: v };
}
