// NFS Hot Pursuit 2 PC car physics (car.ini, car_hp.ini, car_cop.ini, carracer.ini: Nfs6CarIni in
// resources/eac/nfs6_car_specs.py) as NFSHP2.exe computes from it. Every function cites the exe code it follows; the
// field descriptions of the Python definition say the same: keep the two in sync

export const G = 9.81;
// air density / 2 of the drag and lift (0x424660, 0x65db98)
export const HALF_AIR_DENSITY = 0.601;
// the automatic gearbox's air drag constant (0x415780, 0x65d888)
export const SHIFT_AIR_DRAG = 0.5905;
export const TORQUE_STEP_RPM = 500;
export const TORQUE_ENTRIES = 25;
// HCVehicle_Steering 0x4286f0: TurninRamp / TurnoutRamp per physics step
export const RAMP_SCALE = 1 / 128;
// each brake section adds 8 kg, each tyre section 12 kg (0x422bd0, 0x4222c0)
export const BRAKES_AND_TYRES_KG = 2 * 8 + 2 * 12;
// engine inertia per FlyWheelInertiaFactor, kg m^2 (HCVehicle_SetupDrivetrain 0x415d30)
export const ENGINE_INERTIA = 0.18076808750629425;
export const MAX_RPM = 12000;

// the built-in tyre table 0x691890, indexed by TypeCode
export const TIRE_TYPES = [
  'Bias Ply',
  'Bias Belted',
  'Radial',
  'Performance',
  'Stock Car',
  'Bias Ply Rain',
  'Bias Belted Rain',
  'Radial Rain',
  'Performance Rain',
  'Eagle GTS',
  'High Performance',
  'T7000 Radial',
  'MVD HP Radial Type II',
];

// HCVehicle_SetupInertia 0x415570: (pitch, roll) factors of the inertia by BodyShape
export const bodyShapeFactors = (shape: number): { pitch: number; roll: number } => {
  if (shape === 1 || shape === 3 || shape === 7) return { pitch: 0.6, roll: 0.7 };
  if (shape === 4 || shape === 5) return { pitch: 0.65, roll: 0.85 };
  if (shape === 6) return { pitch: 0.65, roll: 0.8 };
  return { pitch: 0.83, roll: 0.84 };
};

const num = (v: any, fallback: number) => (typeof v === 'number' && isFinite(v) ? v : fallback);

// CarIni_ReadEngine 0x4218b0: the curve as the game keeps it. A missing entry is 0; past the last non-zero entry the
// curve falls: each entry the last one times r, r squared every step, r = the last decrease ratio (0.8 without one)
export const gameTorqueCurve = (curve: (number | null | undefined)[]): number[] => {
  const out: number[] = [];
  let last = 0;
  let lastIndex = 0;
  let ratio = 0.8;
  for (let i = 0; i < TORQUE_ENTRIES; i++) {
    const v = num(curve[i], 0);
    out.push(v);
    if (v !== 0) {
      if (last !== 0 && v < last) ratio = v / last;
      last = v;
      lastIndex = i;
    }
  }
  for (let i = lastIndex + 1; i < TORQUE_ENTRIES; i++) {
    last = ratio * last;
    ratio = ratio * ratio;
    out[i] = last;
  }
  return out;
};

// Engine_TorqueAtRpm 0x41fde0 over the game's curve
export const torqueAt = (curve: number[], rpm: number, redLine: number): number => {
  const r = Math.trunc(rpm);
  const i = Math.max(0, Math.trunc(r / TORQUE_STEP_RPM));
  const a = curve[Math.min(i, curve.length - 1)] ?? 0;
  const t = r - i * TORQUE_STEP_RPM;
  if (i <= Math.trunc(redLine / TORQUE_STEP_RPM)) {
    const b = curve[Math.min(i + 1, curve.length - 1)] ?? 0;
    return (b - a) * t * 0.002 + a;
  }
  const v = (-a / (redLine - i * TORQUE_STEP_RPM)) * t + a;
  return v <= 0 ? 0 : v;
};

export const powerKw = (torqueNm: number, rpm: number) => (torqueNm * rpm) / 9549.2966;
export const KW_TO_HP = 1.3410221;

// HCVehicle_SetupWheels 0x414a50: tyre radius, m
export const tireRadius = (sectionWidthMm: number, aspectRatio: number, wheelDiameterIn: number) =>
  (num(sectionWidthMm, 0) * 0.001 * num(aspectRatio, 0) * 0.01 * 2 + num(wheelDiameterIn, 0) * 0.0254) * 0.5;

export type Nfs6Car = {
  mass: number;
  wheelBase: number;
  frontTrack: number;
  height: number;
  frontGripBias: number;
  drag: number;
  frontDownforce: number;
  rearDownforce: number;
  lift: number;
  speedGovernor: number;
  turningCircle: number;
  turnIn: number;
  turnOut: number;
  baseDampingVelocity: number;
  rangeDampingVelocity: number;
  dampingLimit: number;
  minRpm: number;
  redLine: number;
  torque: number[];
  gears: number;
  ratios: number[];
  efficiencies: number[];
  finalGear: number;
  shiftPoint: number;
  automatic: boolean;
  rearRadius: number;
  frontRadius: number;
  // tyre widths over 215 mm add to the drag coefficient (CarIni_ReadTire 0x4222c0)
  dragWithTires: number;
};

const sectionOf = (data: any, name: string) => (data && data[name]) || {};

// the values the game derives from car.ini data (missing keys take the readers' defaults)
export const nfs6Car = (data: any, automatic = true): Nfs6Car => {
  const basic = sectionOf(data, 'basic');
  const engine = sectionOf(data, 'engineblock');
  const trans = sectionOf(data, 'transmission');
  const rear = sectionOf(data, 'rearend');
  const tireFront = sectionOf(data, 'tire_front');
  const tireRear = sectionOf(data, 'tire_rear');
  // the tyre records go by `attach` (10 front), not by the section
  const [front, back] = num(tireRear.attach, 11) === 10 ? [tireRear, tireFront] : [tireFront, tireRear];
  const extraDrag = (w: any) => {
    const width = num(w, 0);
    return width > 215 ? Math.min(Math.max((width - 215) * 0.00004, 0), 0.005) : 0;
  };
  const drag = num(basic.AeroDragCoefficient, 0);
  return {
    mass: num(basic.Mass, 0) + BRAKES_AND_TYRES_KG,
    wheelBase: num(basic.WheelBase, 0),
    frontTrack: num(basic.FrontTrackWidth, 0),
    height: num(basic.VehicleHeight, 0),
    frontGripBias: num(basic.FrontGripBias, 0.5),
    drag,
    dragWithTires: drag + extraDrag(tireFront.SectionWidth) + extraDrag(tireRear.SectionWidth),
    frontDownforce: num(basic.AeroFrontDownforceCoefficient, 0),
    rearDownforce: num(basic.AeroRearDownforceCoefficient, 0),
    lift: num(basic.BodyLiftCoefficient, 0),
    speedGovernor: num(basic.SpeedGovernor, 0),
    turningCircle: num(basic.TurningCircleRadius, 0),
    turnIn: num(basic.TurninRamp, 0),
    turnOut: num(basic.TurnoutRamp, 0),
    baseDampingVelocity: num(basic.BaseDampingVelocity, 8.9406),
    rangeDampingVelocity: num(basic.RangeDampingVelocity, 22.3515),
    dampingLimit: num(basic.DampingLimit, 1),
    minRpm: num(engine.MinRPM, 0),
    redLine: num(engine.RedLine, 0),
    torque: gameTorqueCurve(engine.torqueCurve || []),
    gears: num(trans.NumberOfGears, 0),
    ratios: (trans.GearRatios || []).map((v: any) => num(v, 0)),
    efficiencies: (trans.GearEfficiency || []).map((v: any) =>
      Math.min(Math.max(num(v, 1) * (automatic ? 0.97 : 1), 0), 1),
    ),
    finalGear: Math.max(num(rear.FinalGearRatio, 0), num(rear.FrontFinalGearRatio, 0)),
    shiftPoint: Math.min(Math.max(num(trans.GearShiftPointCoefficient, 0.9), 0.75), 1.2),
    automatic,
    frontRadius: tireRadius(front.SectionWidth, front.AspectRatio, front.WheelDiameter),
    rearRadius: tireRadius(back.SectionWidth, back.AspectRatio, back.WheelDiameter),
  };
};

// HCVehicle_SetupGeometry 0x415a30
export const frontalArea = (car: Nfs6Car) => car.height * car.frontTrack * 0.8;
export const steeringLockDeg = (car: Nfs6Car) =>
  car.turningCircle > 0 ? (Math.atan2(car.wheelBase, car.turningCircle) * 180) / Math.PI : 0;

// Gearbox_ComputeRpmPerMps 0x419550: rpm per m/s of gear i (0 reverse, 1 neutral, 2.. forward)
export const rpmPerMps = (car: Nfs6Car, gear: number): number => {
  if (gear >= car.gears) return 0;
  const ratio = car.ratios[gear] ?? 0;
  if (!car.rearRadius || car.finalGear * ratio === 0) return 0;
  const v = (car.redLine / 60 / (car.finalGear * ratio)) * (2 * Math.PI * car.rearRadius);
  const r = v ? Math.abs(car.redLine / v) : 0;
  return gear === 0 ? -r : gear === 1 ? 0 : r;
};

// Gearbox_ThrustBySpeed 0x419700: drive force, N, at a speed in a gear
export const driveForce = (car: Nfs6Car, gear: number, speed: number): number => {
  let rpm = speed * rpmPerMps(car, gear);
  if (rpm < 0) rpm = 0;
  if (rpm >= MAX_RPM) rpm = MAX_RPM;
  if (rpm > car.redLine || rpm < car.minRpm || !car.rearRadius) return 0;
  return (
    (((car.efficiencies[gear] ?? 1) * car.finalGear * (car.ratios[gear] ?? 0)) / car.rearRadius) *
    torqueAt(car.torque, Math.round(rpm), car.redLine)
  );
};

// rolling resistance of the gearbox's model (0x426e30), times 9.81 x mass x 1.1 in 0x415780
export const rollingFactor = (speed: number) => (speed < 1 ? 0 : speed * speed * 2.74e-6 + 0.011);
export const resistance = (car: Nfs6Car, speed: number) =>
  G * car.mass * rollingFactor(speed) * 1.1 + speed * speed * car.dragWithTires * frontalArea(car) * SHIFT_AIR_DRAG;

// HCVehicle_AeroDrag 0x424660 / HCVehicle_Downforce 0x424530: forces at a speed, N
export const aeroDrag = (car: Nfs6Car, speed: number) =>
  HALF_AIR_DENSITY * car.dragWithTires * frontalArea(car) * speed * speed;
export const frontDownforce = (car: Nfs6Car, speed: number) => car.frontDownforce * Math.abs(speed) * G;
export const rearDownforce = (car: Nfs6Car, speed: number) => car.rearDownforce * Math.abs(speed) * G;
export const bodyLift = (car: Nfs6Car, speed: number) => HALF_AIR_DENSITY * car.lift * frontalArea(car) * speed * speed;

// Gearbox_ShiftSpeed 0x415780: automatic up-shift speed out of gear (2.. top - 1), m/s; -1 for no up-shift
export const shiftSpeed = (car: Nfs6Car, gear: number): number => {
  if (gear < 2 || gear > car.gears - 2) return -1;
  const net = (g: number) => {
    const a: number[] = [];
    for (let v = 0; v < 135; v++) a.push(Math.max(driveForce(car, g, v) - resistance(car, v), 0));
    return a;
  };
  const lo = net(gear);
  const hi = net(gear + 1);
  for (let v = 1; v < 135; v++) {
    if (lo[v] < hi[v] && hi[v - 1] <= lo[v - 1]) {
      const x =
        (v * lo[v - 1] + ((v - 1) * hi[v] - v * hi[v - 1]) - (v - 1) * lo[v]) / (lo[v - 1] - lo[v] + hi[v] - hi[v - 1]);
      if (Math.round(rpmPerMps(car, gear) * x) >= Math.trunc((car.redLine + car.minRpm) / 2)) return car.shiftPoint * x;
    }
  }
  const per = rpmPerMps(car, gear);
  if (!per) return -1;
  return gear === 2 ? Math.trunc((car.redLine * 7) / 10) / per : Math.trunc((car.redLine * 3) / 4) / per;
};

// highest speed (m/s, whole) at which some forward gear's drive beats the resistance of the gearbox model; capped by
// SpeedGovernor
export const topSpeed = (car: Nfs6Car): number => {
  let best = 0;
  for (let v = 1; v < 200; v++) {
    let drive = 0;
    for (let g = 2; g < car.gears; g++) drive = Math.max(drive, driveForce(car, g, v));
    if (drive > resistance(car, v)) best = v;
  }
  return car.speedGovernor > 0 ? Math.min(best, car.speedGovernor) : best;
};

// HCVehicle_SteeringLimit 0x4289a0: share of full lock available at a speed
export const steeringLimit = (car: Nfs6Car, speed: number) => {
  const f = car.rangeDampingVelocity
    ? Math.min(Math.max((Math.abs(speed) - car.baseDampingVelocity) / car.rangeDampingVelocity, 0), 1)
    : 0;
  return car.dampingLimit * f + 1 - f;
};

// HCVehicle_Steering 0x4286f0: physics steps from the centre to full lock, and back across
export const stepsToFullLock = (car: Nfs6Car) => (car.turnIn > 0 ? Math.ceil(1 / (car.turnIn * RAMP_SCALE)) : Infinity);
export const stepsAcross = (car: Nfs6Car) => (car.turnOut > 0 ? Math.ceil(2 / (car.turnOut * RAMP_SCALE)) : Infinity);

export const driveLayout = (wheels: (number | null | undefined)[], frontDriveRatio: number) => {
  const w = [0, 1, 2, 3].map(i => num(wheels?.[i], 0) !== 0);
  const front = w[0] && w[1];
  const rear = w[2] && w[3];
  if (!w.some(x => x)) return { name: 'RWD', front: 0 };
  if (front && rear) return { name: 'AWD', front: frontDriveRatio };
  if (front && !w[2] && !w[3]) return { name: 'FWD', front: 1 };
  return { name: 'RWD', front: 0 };
};
