// Pure computations of the NFS2 SE SIMTUNE.DAT editor (Nfs2SimTune). The formulas come from the field descriptions of
// `Nfs2SimTuneRecord` / `Nfs2SimTuneGlueLogic` (resources/eac/car_specs.py), which cite nfs2sen.exe

import { CurvePoint } from '../../common/curve-editor/curve-editor.component';

// physics steps per second
export const SIM_TICKS = 32;
// the wreck timer runs this many times faster with the car still / no longer tumbling (0x43fde0)
export const STILL_TIMER_SPEEDUP = 8;
// a crash strength is 6 * the speed into a wall (car+0x160)
export const CRASH_STRENGTH_PER_MPS = 6;
// the gas pedal above this (of 255) resets a car whose wreck timer is below `full_gas_reset_tick_advance`
export const FULL_GAS_PEDAL = 200;
// no speed loss sliding along a wall below this speed (0x459120)
export const WALL_LOSS_MIN_SPEED = 5;

export const SIM_TUNE_STYLES = ['simulation', 'arcade'] as const;
export type SimTuneStyle = (typeof SIM_TUNE_STYLES)[number];
export const SIM_TUNE_STYLE_COLORS: { [s in SimTuneStyle]: string } = { simulation: '#6a1b9a', arcade: '#ef6c00' };
export const SIM_TUNE_STYLE_LABELS: { [s in SimTuneStyle]: string } = { simulation: 'Simulation', arcade: 'Arcade' };

export type SimTuneGlue = { slice_distance: number; speed_boost_multiplier: number };

export type SimTuneRecord = {
  telepole_launch_value: number;
  initial_jump_roll_attenuate: number;
  jump_roll_due_to_car_turn: number;
  initial_jump_road_pitch_damp: number;
  jump_pitch_due_to_acc_and_brake: number;
  extra_flight_gravity: number;
  bad_collision_reset_ticks: number;
  full_gas_reset_tick_advance: number;
  invincibility_ticks_after_reset: number;
  reset_forward_slices: number;
  stop_tumbling_speed: number;
  collision_reset_altitude: number;
  collision_reset_launch_speed: number;
  bounce_threshold: number;
  bounce_elasticity: number;
  bounce_shock_absorb_speed: number;
  ground_max_speed_change: number;
  ground_rise_smoothing: number;
  ground_fall_smoothing: number;
  barrier_speed_loss_multiplier: number;
  deflection_angular_range: number;
  glue_logic: SimTuneGlue[];
};

export const ticksToSeconds = (ticks: number) => ticks / SIM_TICKS;
export const secondsToTicks = (s: number) => s * SIM_TICKS;

// acos of a dot product threshold in degrees (clamped to the valid range)
export const acosDeg = (v: number) => (Math.acos(Math.max(-1, Math.min(1, v))) * 180) / Math.PI;
export const cosDeg = (deg: number) => Math.cos((deg * Math.PI) / 180);

// ---------- flight & landing ----------

// landing on the wheels (0x44d840): rebound speed = (landing speed - absorb speed) * elasticity, at least 0
export function reboundSpeed(landingSpeed: number, absorbSpeed: number, elasticity: number): number {
  return Math.max(0, (landingSpeed - absorbSpeed) * elasticity);
}

// the rebound line over landing speeds 0..`maxSpeed`: 0 up to the absorb speed, then linear (3 points, the last one
// at `maxSpeed`)
export function reboundCurve(absorbSpeed: number, elasticity: number, maxSpeed: number): CurvePoint[] {
  const knee = Math.max(0, Math.min(maxSpeed, absorbSpeed));
  return [
    { x: 0, y: reboundSpeed(0, absorbSpeed, elasticity) },
    { x: knee, y: reboundSpeed(knee, absorbSpeed, elasticity) },
    { x: maxSpeed, y: reboundSpeed(maxSpeed, absorbSpeed, elasticity) },
  ];
}

// the elasticity giving `rebound` m/s at a landing speed of `landingSpeed` (inverse of `reboundSpeed`)
export function elasticityFor(landingSpeed: number, rebound: number, absorbSpeed: number): number {
  const over = landingSpeed - absorbSpeed;
  return over > 0 ? Math.max(0, rebound / over) : 0;
}

// the smoothed vertical speed of the ground under the car (car+0x158) after a step of the ground speed from 0 to 1:
// f += (target - f) * factor each step; point k is the value after k steps, x in seconds
export function smoothingResponse(factor: number, steps: number = SIM_TICKS): CurvePoint[] {
  const points: CurvePoint[] = [{ x: 0, y: 0 }];
  let f = 0;
  for (let k = 1; k <= steps; k++) {
    f += (1 - f) * factor;
    points.push({ x: k / SIM_TICKS, y: f });
  }
  return points;
}

// steps until the smoothed ground speed covers `part` of a step change, null when it never does
export function smoothingStepsTo(factor: number, part: number = 0.9): number | null {
  if (factor <= 0) return null;
  if (factor >= 1) return 1;
  return Math.ceil(Math.log(1 - part) / Math.log(1 - factor));
}

// in the air the car falls with (1 + extra) times the gravity (0x44d840)
export const flightGravityFactor = (extra: number) => 1 + extra;

// the step a car leaves the ground (0x43ef10): human cars get roll -= lateral acceleration / 2 * value and
// pitch += forward acceleration / 2 * value, in rad/s for an acceleration in m/s²
export const jumpRateFromAcceleration = (acceleration: number, value: number) => (acceleration / 2) * value;

// ---------- crash & reset ----------

export type WreckTimeline = {
  // the timer counting down one tick per step
  normal: CurvePoint[];
  // eight ticks per step: the car still / stopped tumbling
  still: CurvePoint[];
  // seconds to the reset: normally, with the car still, and with the gas pedal held (the timer below the advance)
  seconds: number;
  stillSeconds: number;
  gasSeconds: number;
};

// the wreck timer (car+0x578) from `ticks` down to 0, x in seconds, y in ticks
export function wreckTimeline(ticks: number, gasAdvance: number): WreckTimeline {
  const t = Math.max(0, ticks);
  const seconds = ticksToSeconds(t);
  const stillSeconds = seconds / STILL_TIMER_SPEEDUP;
  return {
    normal: [
      { x: 0, y: t },
      { x: seconds, y: 0 },
    ],
    still: [
      { x: 0, y: t },
      { x: stillSeconds, y: 0 },
    ],
    seconds,
    stillSeconds,
    // the reset comes as soon as the timer is below the advance with the gas held
    gasSeconds: t <= gasAdvance ? 0 : ticksToSeconds(t - gasAdvance),
  };
}

// the wall speed a crash strength threshold stands for: strength = 6 * the speed into the wall
export const crashSpeedFor = (threshold: number) => threshold / CRASH_STRENGTH_PER_MPS;

// ---------- walls ----------

// forward speed kept after sliding along a wall (`Physics_WallSlide` 0x459120) at `speed` m/s hitting it at `angleDeg`
// (0 = parallel): the part along the wall, less |the sideways part| / 2 * multiplier / 4 above 5 m/s, not past 0
export function wallSpeedKept(speed: number, angleDeg: number, multiplier: number): number {
  const a = (angleDeg * Math.PI) / 180;
  const along = speed * Math.cos(a);
  if (speed <= WALL_LOSS_MIN_SPEED) return Math.max(0, along);
  const side = Math.abs(speed * Math.sin(a));
  return Math.max(0, along - ((side / 2) * multiplier) / 4);
}

export function wallCurve(speed: number, multiplier: number, stepDeg: number = 1): CurvePoint[] {
  const points: CurvePoint[] = [];
  for (let d = 0; d <= 90 + 1e-9; d += stepDeg) points.push({ x: d, y: wallSpeedKept(speed, d, multiplier) });
  return points;
}

// the impact angle from which nothing is kept
export function wallStopAngle(speed: number, multiplier: number): number {
  // v cos a = v sin a * k / 8: tan a = 8 / k
  if (speed <= WALL_LOSS_MIN_SPEED || multiplier <= 0) return 90;
  return (Math.atan(8 / multiplier) * 180) / Math.PI;
}

// ---------- catch-up ----------

// speed boost multiplier of a human car `behind` slices behind the leader (`Race_HumanGlue` 0x4619b0): the last pair
// whose distance it reaches, 1.0 below the first
export function glueBoostAt(behind: number, glue: SimTuneGlue[]): number {
  let m = 1;
  for (const pair of glue) if (behind >= pair.slice_distance) m = pair.speed_boost_multiplier;
  return m;
}

// the boost as step points: (0, 1), then (distance k, multiplier k) for each pair, then the end of the axis
export function glueSteps(glue: SimTuneGlue[], end: number): CurvePoint[] {
  const points: CurvePoint[] = [{ x: 0, y: 1 }];
  for (const pair of glue) points.push({ x: pair.slice_distance, y: pair.speed_boost_multiplier });
  const last = glue.length ? glue[glue.length - 1] : null;
  points.push({ x: Math.max(end, (last?.slice_distance ?? 0) + 1), y: last ? last.speed_boost_multiplier : 1 });
  return points;
}

// the indices of the pairs whose distance does not increase over the previous one
export function glueOrderProblems(glue: SimTuneGlue[]): number[] {
  const res: number[] = [];
  for (let i = 1; i < glue.length; i++) if (glue[i].slice_distance <= glue[i - 1].slice_distance) res.push(i);
  return res;
}

export const maxGlueBoost = (glue: SimTuneGlue[]) => Math.max(1, ...glue.map(p => p.speed_boost_multiplier));
