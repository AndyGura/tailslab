// NFS5 car parts (FEData/Data/nfs5.prt, Nfs5CarParts): what each part type does to the car's physics when it is
// installed, as Porsche.exe's Cars_ProcessSpecs (0x49cb50) applies it (nfs-web src/nfs5/nfs5-physics/src/cars.c).
// The values are the part record's (`value_a`, `value_b`...); `s` stands for the car specs (the .sim, scaled)

export const NFS5_PART_TYPES: { [type: number]: string } = {
  1: 'Engine',
  2: 'Brakes',
  3: 'Gearbox',
  4: 'Springs',
  5: 'Shocks',
  6: 'Aerodynamics',
  7: 'Body panels',
  8: 'Sway bars',
  9: 'Tyres',
  10: 'Body and rims',
};

export const NFS5_TYRE_TYPES = ['Road', 'Rain', 'Race'];

export function nfs5PartTypeName(type: number): string {
  return NFS5_PART_TYPES[type] ?? `Type ${type}`;
}

export type Nfs5Part = { [field: string]: any };

export type Nfs5PartEffect = {
  // what changes
  target: string;
  // the factor or the new value, as text
  value: string;
  // the exe's formula
  formula: string;
};

const f = (v: number, d: number = 3) =>
  isFinite(v) ? v.toLocaleString('en-US', { maximumFractionDigits: d, minimumFractionDigits: 0 }) : '–';
const factor = (v: number) => `× ${f(v)}`;

// the physics effects of one part, the menus' setup aside (0x49cb50; none for the AI spec names 959, 928, GT2, GT3)
export function nfs5PartEffects(part: Nfs5Part, grip?: number): Nfs5PartEffect[] {
  const a = part['value_a'] || 0;
  const b = part['value_b'] || 0;
  const effects: Nfs5PartEffect[] = [];
  const type = part['type'];
  if (!type) return effects;
  if (part['mass']) {
    effects.push({
      target: 'Mass',
      value: `${part['mass'] > 0 ? '+' : ''}${f(part['mass'], 1)} kg`,
      formula: 's.mass + mass',
    });
  }
  const tsd = part['top_speed_divisor'] || 0;
  if (tsd) {
    effects.push({
      target: 'Top speed',
      value: factor(1 / (1 + tsd * 0.01)),
      formula: 's.top_speed / (1 + top_speed_divisor × 0.01)',
    });
  }
  switch (type) {
    case 1: {
      const name = part['name'];
      const torques: number[] = part['torque_curve'] || [];
      const peak = Math.max(0, ...torques);
      if (name === 'Engine') {
        effects.push({
          target: 'Torque curve',
          value: `replaced (peak ${f(peak, 0)} lb·ft)`,
          formula: 's.torque = torque_curve',
        });
      } else {
        if (peak) {
          effects.push({
            target: 'Torque curve',
            value: `+ 0.67 × (peak ${f(peak, 0)} lb·ft)`,
            formula: 's.torque + torque_curve × 0.67',
          });
        }
        if (name === 'Turbo')
          effects.push({ target: 'Aspiration', value: 'turbo (1)', formula: 'name "Turbo": s.aspiration = 1' });
        if (name === 'Supercharger') {
          effects.push({
            target: 'Aspiration',
            value: 'unchanged',
            formula: 'the race compares with "Supercharged" (aspiration 2): "Supercharger" never matches',
          });
        }
      }
      effects.push({
        target: 'Top speed',
        value: 'with the torque change',
        formula: 's.top_speed × (peak torque after / before + 3) / 4, after every part',
      });
      break;
    }
    case 2:
      effects.push({ target: 'Brake force', value: factor((a + 3) / 4), formula: 's.brake_force × (value_a + 3) / 4' });
      break;
    case 3:
      if (part['name'] === 'Gear Box') {
        effects.push(
          { target: 'Gear ratios', value: 'replaced', formula: 's.gear_ratios = gear_ratios' },
          { target: 'Forward gears', value: f(part['forward_gears'], 0), formula: 's.forward_gears = forward_gears' },
          { target: 'Final drive', value: f(a, 3), formula: 's.final_drive = value_a' },
          { target: 'Shift time', value: `${f(part['shift_time'], 0)} steps`, formula: 's.shift_time = shift_time' },
        );
      } else {
        const st = part['shift_time'] || 0;
        effects.push({
          target: 'Shift time',
          value: `${st > 0 ? '+' : ''}${f(st, 0)} steps`,
          formula: 's.shift_time + shift_time',
        });
      }
      break;
    case 4:
      effects.push(
        {
          target: 'Load transfer divisors',
          value: factor((a + 4) * 0.2),
          formula: 's.spring_load_transfer and s.lateral_load_transfer_divisor × (value_a + 4) × 0.2',
        },
        { target: 'Grip', value: factor((a + 15) / 16), formula: 's.grip × (value_a + 15) / 16' },
        { target: 'Roll gain', value: factor(1 / ((a + 3) / 4)), formula: 's.roll_gain / ((value_a + 3) / 4)' },
        {
          target: 'Ride height',
          value: `none (${f(b, 1)} mm)`,
          formula: 's.ride_height = value_b × 0.001, overwritten by the setup ride height right after (0x49d567)',
        },
      );
      break;
    case 5:
      effects.push(
        {
          target: 'Pitch and roll damping',
          value: factor(1 / ((a + 4) * 0.2)),
          formula: 's.damping / ((value_a + 4) × 0.2)',
        },
        { target: 'Grip', value: factor((a + 11) / 12), formula: 's.grip × (value_a + 11) / 12' },
      );
      break;
    case 6:
      effects.push(
        {
          target: 'Front downforce',
          value: factor(a * 0.005 + 1),
          formula: 's.front_downforce × (value_a × 0.005 + 1)',
        },
        { target: 'Rear downforce', value: factor(b * 0.005 + 1), formula: 's.rear_downforce × (value_b × 0.005 + 1)' },
      );
      break;
    case 8:
      effects.push(
        {
          target: 'Load transfer divisor',
          value: factor((a + 4) * 0.2),
          formula: 's.spring_load_transfer × (value_a + 4) × 0.2',
        },
        { target: 'Grip', value: factor((a + 11) / 12), formula: 's.grip × (value_a + 11) / 12' },
        { target: 'Roll gain', value: factor(1 / ((a + 3) / 4)), formula: 's.roll_gain / ((value_a + 3) / 4)' },
      );
      break;
    case 9: {
      const tyre = NFS5_TYRE_TYPES[part['drive_type']] ?? `${part['drive_type']}`;
      effects.push({ target: 'Tyre type', value: tyre, formula: 's.tyre_type = drive_type (grip table column)' });
      if (grip !== undefined) {
        const t = nfs5TyreFactors(grip, a, b);
        effects.push(
          { target: 'Grip', value: `${factor(t.grip)} (car grip ${f(grip, 2)} g)`, formula: tyreFormula },
          { target: 'Front weight share', value: factor(t.frontWeight), formula: tyreFormula },
        );
      } else {
        effects.push({ target: 'Grip and front weight share', value: 'by the car grip', formula: tyreFormula });
      }
      break;
    }
    default:
      effects.push({
        target: 'Physics',
        value: 'none',
        formula: 'only the geometry switches (the car model shows other parts)',
      });
  }
  return effects;
}

const tyreFormula =
  'g3 = s.grip × 3; front = (g3 + value_a) / (g3 + 1); sum = (g3 + value_b) / (g3 + 1) + front; s.grip × (sum + 1) / 3; s.front_weight_share × (2 front / sum + 1) / 2';

// the tyres' grip and front weight factors (type 9, 0x49cb50) for a car grip in g
export function nfs5TyreFactors(grip: number, a: number, b: number): { grip: number; frontWeight: number } {
  const g3 = grip * 3;
  const d = g3 + 1;
  const front = (g3 + a) / d;
  const sum = (g3 + b) / d + front;
  return { grip: ((sum + 1) * 1) / 3, frontWeight: ((front + front) / sum + 1) * 0.5 };
}

// Porsche.exe 0x5ba4a4: the parts' yearly price inflation, % (62 years)
export const NFS5_PART_INFLATION = [
  1, 2, 2, 2, 2, 3, 4, 5, 4, 5, 6, 7, 8, 12, 4, 5, 4, 2, 3, 2, 3, 4, 3, 5, 6, 7, 2, 4, 5, 8, 9, 2, 5, 4, 6, 3, 7, 4, 7,
  6, 6, 4, 7, 3, 6, 8, 3, 4, 5, 2, 4, 3, 4, 2, 5, 2, 1, 3, 7, 5, 4, 3,
];

// int32 division as the exe's IDIV (towards zero)
const idiv = (a: number, b: number) => Math.trunc(a / b);

// `Parts_Price` 0x5181c0: the price of a new part in a year: price + price x (the inflation of the years since the
// part's year) / 100
export function nfs5PartPrice(part: Nfs5Part, year: number): number {
  const price = part['sort_key'] || 0;
  const years = year - (part['year'] || 0);
  let sum = 0;
  for (let i = 0; i < Math.min(years, NFS5_PART_INFLATION.length); i++) sum += NFS5_PART_INFLATION[i];
  return idiv(price * sum, 100) + price;
}

// the share of the new price a damaged part loses, % (0x518220): clamp(ftol(2 x damage + 20), 0, 100)
export function nfs5PartLoss(damage: number): number {
  return Math.max(0, Math.min(100, Math.trunc(2 * damage + 20)));
}

// `Parts_UsedValue` 0x518220: what the part sells for
export function nfs5PartUsedValue(part: Nfs5Part, year: number, damage: number = part['damage'] || 0): number {
  return idiv(nfs5PartPrice(part, year) * (100 - nfs5PartLoss(damage)), 100);
}

// 0x518880: repairing it
export function nfs5PartRepairCost(part: Nfs5Part, year: number, damage: number = part['damage'] || 0): number {
  return idiv(nfs5PartPrice(part, year) * Math.trunc(2 * damage), 100);
}

// the wear factor of the part's durability (0x4938d9..): 1.5 - durability x 0.005
export function nfs5PartWearFactor(part: Nfs5Part): number {
  return 1.5 - (part['durability'] || 0) * 0.005;
}
