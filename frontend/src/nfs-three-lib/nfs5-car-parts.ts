/**
 * The rules of an NFS5 (Porsche Unleashed) car model's state, as Porsche.exe keeps them (nfs-web
 * `decomp/nfs5/Porsche.exe.gzf`): the geometry configuration of a car in a race, the lights, the damage of hits, the
 * paint bands. Pure functions and the export's data types: `Nfs5CarMeshController` draws them.
 */

/** TailsLab's `nfs5Car` (the car export's `.meta` and the OBJ's `_extra.json`, `serializers/misc/nfs5_car_model.py`) */
export type Nfs5CarData = {
  formatVersion: number;
  articles: Nfs5CarArticle[];
  styles: Nfs5CarStyle[];
  header: {
    driverCamPos: number[];
    driverCamRot: number[];
    doorAxis: number[];
    noRoof: boolean;
    hoodExtent: number;
    trunkExtent: number;
    headlightExtent: number;
    moveSpoilerExtent: number;
  };
  damageZones: { [key: string]: number };
  pages: Nfs5CarPage[];
  /** per `packages.ini` package the colour index (0 body, 1 / 2 accents, 3 interior) of each of the 18 bands */
  packages: number[][];
  /** the CRP's `tm` materials (format 2): the meshes' `_nfs5_material` (the OBJ's `nfs5Materials`) index them */
  materials?: Nfs5CarMaterial[];
};

/**
 * A CRP `tm` material (TailsLab's `nfs5_car_material`): its render method (the CRP's `htMR` part of that name, EAGL:
 * CarExtEnv, CarExtEnvNS, CarExt, CarWindow, CarWheel, CarInt, CarIntShd in every car), its texture page and the
 * reflection layers of the method
 */
export type Nfs5CarMaterial = {
  index: number;
  method: string;
  page: number;
  /** R3DSpecularTextureLayer (0x445520): carcmn.fsh's specular texture, sphere mapped by the view-space normal */
  specular: Nfs5CarMaterialLayer | null;
  /** R3DSkyMapTextureLayer (0x445b10): the track's `.env` texture projected from above (not drawn by the controller) */
  skyMap: Nfs5CarMaterialLayer | null;
};

/**
 * A reflection layer of a material: `param` the float the material binds to it (nfs5SpecularLevel picks the texture
 * by it), `passes` the caps mask of each group (pass) of the render method holding the layer (nfs5LayerDrawn)
 */
export type Nfs5CarMaterialLayer = { param: number; passes: number[] };

/** An article (by its CRP index) and its base part's car data (CRP `CrpBasePartData`) */
export type Nfs5CarArticle = {
  index: number;
  name: string;
  /** base part flags: 1 drawn in the second (alpha) pass too, 0x600 a glare article */
  flags?: number;
  /** the geometry slot and the value drawing it (car+0x56c[slot] == value: R3DCarLOD_Build 0x43c1b0) */
  slot?: number;
  value?: number;
  order?: number;
  id?: number;
  /** the wheel 0..3 moving it (R3DCar+0x6d0, always 0), -1 none */
  wheel?: number;
  /** the pivot turning it, 0 none (`NFS5_PIVOTS`) */
  pivot?: number;
  frames?: number;
  /** the animation picking its frame, 0 none (`NFS5_ANIMATIONS`) */
  animation?: number;
  /** NFS5_DRAW_*: the draw passes drawing it, NFS5_DRAW_DAMAGE dented */
  drawFlags?: number;
  /** glare articles: the light drawing the glare */
  light?: number;
  /** drawn in the in-car view */
  cockpit?: boolean;
  /** drawn only in the in-car view (the hands) */
  insideOnly?: boolean;
  /** CRP levels (1..7) with meshes */
  lods: number[];
  /** `rt` parts by level: 16 floats, CRP axes, row vectors (translation 12..14) = column-major for three.js */
  transforms: { [lod: string]: number[] };
  glares?: Nfs5CarGlare[];
};

/** A light glare (effect type 5, CRP `EffectPartData`), in the article's axes */
export type Nfs5CarGlare = {
  position: number[];
  width: number[];
  height: number[];
  depth: number[];
  /** 0xAARRGGBB */
  glowColor: number;
  sourceColor: number;
  /** drawn again mirrored (x negated) for `mirrorLight` */
  mirrored: boolean;
  mirrorLight: number;
  /** its flare on the road at night (0x43d4f0) */
  nightFlare: boolean;
};

/** A `.tpg` `[style<n>]`: slots (texture slots + 60) and values */
export type Nfs5CarStyle = { name: string; slots: [number, number][]; stripe: boolean };

export type Nfs5CarPage = { index: number; width: number; height: number; format: number; file: number | null };

/** R3DCar_Draw 0x444e00 passes: the draw flags (base part `car_draw_flags`) of each */
export const NFS5_DRAW_BODY = 0x10;
export const NFS5_DRAW_WHEELS = 0x20;
export const NFS5_DRAW_STEERING_WHEEL = 0x40;
export const NFS5_DRAW_DRIVER = 0x80;
/** dented by the damage: its `vt` parts have damaged copies and `zd` zones (R3DCarLOD_Damage 0x43e390) */
export const NFS5_DRAW_DAMAGE = 0x08;

/**
 * Pivots (R3DCar+0x2d0, set by R3DCar_UpdatePivots 0x438440): 1..4 the wheels (0 front left, 1 front right, 2 rear
 * left, 3 rear right), 5 the steering wheel, 6 / 7 the left / right door, 8 hood, 9 trunk, 0xb rev counter, 0xc
 * speedometer, 0x10 moving spoiler, 0x11 pop-up headlights, 0x12..0x15 the wheels without rotation, 0x16 a rotating
 * light (y = the game's tick / 128 turns)
 */
export const NFS5_PIVOT_COUNT = 0x17;
export const NFS5_PIVOTS: { [pivot: number]: string } = {
  1: 'front left wheel',
  2: 'front right wheel',
  3: 'rear left wheel',
  4: 'rear right wheel',
  5: 'steering wheel',
  6: 'left door',
  7: 'right door',
  8: 'hood',
  9: 'trunk',
  0xb: 'rev counter needle',
  0xc: 'speedometer needle',
  0x10: 'moving spoiler',
  0x11: 'pop-up headlights',
  0x12: 'front left wheel shadow',
  0x13: 'front right wheel shadow',
  0x14: 'rear left wheel shadow',
  0x15: 'rear right wheel shadow',
  0x16: 'rotating light',
};

/** Animations (R3DCar+0x568, 8 of 0x14 bytes): 1 convertible top, 2 speed wing, 3 wiper, 4 right arm, 5 left arm, 6 driver's body, 7 antenna */
export const NFS5_ANIMATION_COUNT = 8;
export const NFS5_ANIMATIONS = [
  '',
  'convertible top',
  'speed wing',
  'wiper',
  'right arm',
  'left arm',
  'driver',
  'antenna',
];

/** R3DCar_Draw 0x444e00: the driver's level (0-based) outside by `lod` 0..3 (table 0x5cdb28; no driver from lod 4) */
export const NFS5_OUTSIDE_DRIVER_LOD = [0, 0, 0, 1];
/** the in-car driver's level by the car detail (table 0x5cdb1c; detail 0 draws none) */
export const NFS5_COCKPIT_DRIVER_LOD = [1, 0, 0];
/** the wheels' level by the car detail and `lod` (table 0x5cdb44) */
export const NFS5_WHEEL_LODS = [
  [0, 0, 1, 1, 1, 5, 6],
  [0, 0, 0, 0, 1, 5, 6],
  [0, 0, 0, 0, 1, 5, 6],
];

/** 0x438440: the steering wheel turns by the front wheels' angles summed, at most 4.5 / 23 turn (0x5b369c / 0x5b3590) */
export const NFS5_STEERING_WHEEL_LIMIT = 4.5 / 23;

/** Damage zones (car+0x4e4[10], the `zd` parts' zones; the side of the CRP's +x is the left: the driver's, `DecalDoorL`) */
export const NFS5_ZONES = 10;
export const NFS5_ZONE_NAMES = [
  'front left',
  'front',
  'front right',
  'right',
  'rear right',
  'rear',
  'rear left',
  'left',
  'roof',
  'underside',
];
/** R3DCarLOD_Damage 0x43e390: a zone's vertices move by the damaged offsets x min(1, damage x 0.02) (0x5b3714) */
export const NFS5_DAMAGE_WEIGHT = 0.02;
/** R3DCar_DrawnDamage 0x4382e0: the in-car view's limits per zone (0x5b35d4: no dents left, right, roof) */
export const NFS5_COCKPIT_ZONE_LIMITS = [1, 1, 1, 0, 1, 1, 1, 0, 0, 1];
/** R3DCar_UpdateLights 0x439360: a zone damaged more than this breaks its lights (0x5b2408) */
export const NFS5_LIGHT_BREAK_DAMAGE = 30;
/** the tail lights' intensity: the brake lights with the headlights on, not braking (0x5b35a8) */
export const NFS5_TAIL_LIGHT_INTENSITY = 0.6;
/** the lights a zone's damage breaks (0x439360) */
const ZONE_LIGHTS: [number, number[]][] = [
  [0, [0, 4]],
  [2, [1, 5]],
  [4, [3, 7, 11]],
  [6, [2, 6, 10]],
  [5, [8]],
  [8, [12, 13]],
];

/** R3DCar_SetupGeometry 0x43ae50: the driver's body (slot 9) of the front end's driver 0..7 (table 0x5cd5c4) */
export const NFS5_DRIVER_BODIES = [2, 3, 4, 5, 10, 8, 9, 7];

/**
 * The geometry configuration of a car in a race (120 slots: 0..59 geometry, 60..119 texture): all 0, the style's
 * slots (R3DCar_SetBodyStyle 0x437b00), slot 10 = the race number decals (when the style exists); then
 * R3DCar_SetupGeometry 0x43ae50: slot 41 = 2 x slot 37 (the convertible top down) or 2 x slot 37 - 1 (up), slot 37 = 0
 * (the animated top is the front end's), the driver (slot 9 the body, 43 the arms and legs, 56 the hands; null: an
 * empty car, car flag 0x10, slot 9 = 0), slot 42 = 0, slot 59 = the passenger (record +0x520), the parts' GEOMCONFIG
 * entries >= 0 over them, slot 58 = the tiny car cheat (the antenna). SKIPPED: a factory driver mission's drivers
 */
export function nfs5RaceSlots(
  style: [number, number][] | null,
  options: {
    driver?: number | null;
    cabrioDown?: boolean;
    raceNumber?: boolean;
    passenger?: number;
    tinyCar?: boolean;
    geometryConfig?: number[];
  } = {},
): number[] {
  const slots = new Array<number>(120).fill(0);
  for (const [slot, value] of style ?? []) {
    if (slot >= 0 && slot < 120) {
      slots[slot] = value;
    }
  }
  if (style) {
    slots[10] = options.raceNumber ? 1 : 0;
  }
  const top = slots[37];
  slots[41] = options.cabrioDown ? 2 * top : 2 * top - 1;
  slots[37] = 0;
  const driver = options.driver === undefined ? 0 : options.driver;
  if (driver === null) {
    slots[9] = 0;
  } else if (driver >= 0 && driver < 8) {
    slots[9] = NFS5_DRIVER_BODIES[driver];
    slots[43] = Math.floor(driver / 4) * 2 + 2;
    slots[56] = Math.floor(driver / 4) + 1;
  } else {
    slots[9] = slots[43] = slots[56] = 1;
  }
  slots[42] = 0;
  slots[59] = options.passenger ?? 0;
  (options.geometryConfig ?? []).forEach((value, slot) => {
    if (value >= 0 && slot < 120) {
      slots[slot] = value;
    }
  });
  slots[58] = options.tinyCar ? 1 : 0;
  return slots;
}

export type Nfs5Lights = { on: boolean[]; intensity: number[] };

/**
 * The 14 lights (R3DCar_UpdateLights 0x439360; their glares: R3DCarLOD_DrawGlares 0x43d800): 0 / 1 the headlights
 * (left / right), 2 / 3 brake lights, 4 / 5 front indicators, 6 / 7 rear indicators, 8 reverse light, 9 off in a race,
 * 10 / 11 brake lights blinking with the indicators, 12 / 13 always on (a cop's roof lights).
 * - Headlights: on with `headlights`; pop-up headlights (`popUp` not null: raised 0..1) also while lowering, as
 *   bright as raised; else intensity 1.
 * - Brake lights 2 / 3 on braking; with the headlights on and not braking on at 0.6 (tail lights).
 * - Indicators: `left` lights 4 with the blink phase, 6 against it, 10 with it (else 10 is a brake / tail light);
 *   `right` the same for 5, 7, 11.
 * - Reverse light 8 in reverse.
 * - A zone damaged more than 30 breaks its lights (zone 0: 0, 4; 2: 1, 5; 4: 3, 7, 11; 6: 2, 6, 10; 5: 8; 8: 12, 13)
 */
export function nfs5Lights(
  input: {
    headlights: boolean;
    brake: boolean;
    reverse: boolean;
    left: boolean;
    right: boolean;
    blink: boolean;
    popUp: number | null;
  },
  damage: number[],
): Nfs5Lights {
  const on = new Array<boolean>(14).fill(false);
  const intensity = new Array<number>(14).fill(1);
  const { brake, left, right, blink } = input;
  on[8] = input.reverse;
  on[2] = on[3] = brake;
  on[4] = left && blink;
  on[6] = left && !blink;
  on[5] = right && blink;
  on[7] = right && !blink;
  on[10] = left ? blink : brake;
  on[11] = right ? blink : brake;
  on[0] = on[1] = input.headlights;
  on[9] = false;
  on[12] = on[13] = true;
  let raised = input.headlights ? 1 : 0;
  if (input.popUp !== null) {
    raised = input.popUp;
    if (!input.headlights && raised > 0) {
      on[0] = on[1] = true;
    }
  }
  intensity[0] = intensity[1] = raised;
  if (input.headlights && !brake) {
    intensity[2] = intensity[3] = NFS5_TAIL_LIGHT_INTENSITY;
    intensity[10] = left ? 1 : NFS5_TAIL_LIGHT_INTENSITY;
    intensity[11] = right ? 1 : NFS5_TAIL_LIGHT_INTENSITY;
    on[2] = on[3] = true;
    if (!left) {
      on[10] = true;
    }
    if (!right) {
      on[11] = true;
    }
  }
  for (const [zone, lights] of ZONE_LIGHTS) {
    if ((damage[zone] ?? 0) > NFS5_LIGHT_BREAK_DAMAGE) {
      lights.forEach(l => (on[l] = false));
    }
  }
  return { on, intensity };
}

/**
 * The zones a hit damages (Car_HitDamage 0x494df0), `normal` the push on the car in the CRP's axes (the car's right
 * is -x, up +y, forward -z): none at a speed of 10 or below; the roof (8) when the push is downwards (n . up < -0.5,
 * a car with wheels); then by r = n . right, f = n . forward the first of: |r| < 0.1, f < -0.1: 1 (front); |r| < 0.1,
 * f > 0.1: 5 (rear); |f| < 0.1, r > 0.1: 7 (left); |f| < 0.1, r < -0.1: 3 (right); f < -0.1: r > 0.1 0, r < -0.1 2;
 * f > 0.1: r > 0.1 6, r < -0.1 4
 */
export function nfs5HitZones(normal: { x: number; y: number; z: number }, speed: number, hasWheels = true): number[] {
  if (speed <= 10) {
    return [];
  }
  const r = -normal.x;
  const up = normal.y;
  const f = -normal.z;
  const zones: number[] = [];
  if (up < -0.5 && hasWheels) {
    zones.push(8);
  }
  let zone: number | null = null;
  if (Math.abs(r) < 0.1 && f < -0.1) {
    zone = 1;
  } else if (Math.abs(r) < 0.1 && f > 0.1) {
    zone = 5;
  } else if (Math.abs(f) < 0.1 && r > 0.1) {
    zone = 7;
  } else if (Math.abs(f) < 0.1 && r < -0.1) {
    zone = 3;
  } else if (f < -0.1 && r > 0.1) {
    zone = 0;
  } else if (f < -0.1 && r < -0.1) {
    zone = 2;
  } else if (f > 0.1 && r > 0.1) {
    zone = 6;
  } else if (f > 0.1 && r < -0.1) {
    zone = 4;
  }
  if (zone !== null) {
    zones.push(zone);
  }
  return zones;
}

/**
 * The zone damage after a hit on a zone (Car_Damage 0x494500): d = speed x 0.5 (x 1.5 in a derby), at most 100; the
 * zone keeps the larger; a ring zone (0..7) lifts both neighbours to at least the mean of their own neighbours
 */
export function nfs5ZoneDamageAfterHit(damage: number[], zone: number, speed: number, derby = false): number[] {
  const result = Array.from({ length: NFS5_ZONES }, (_, z) => damage[z] ?? 0);
  const d = Math.min(100, speed * (derby ? 1.5 : 0.5));
  result[zone] = Math.max(result[zone], d);
  if (zone < 8) {
    const at = (z: number) => result[(z + 8) % 8];
    const next = (zone + 1) % 8;
    const previous = (zone + 7) % 8;
    result[next] = Math.max(result[next], (at(zone) + at(zone + 2)) * 0.5);
    result[previous] = Math.max(result[previous], (at(zone - 2) + at(zone)) * 0.5);
  }
  return result;
}

/**
 * The paint bands (R3DCar_SetStripePackage 0x443db0): band k = colors[package[k]] (`packages.ini`; no package: bands 14, 15
 * the interior, the rest the body), band 6 = accent 1 with the style's `stripe`. Colours 0xRRGGBB
 */
export function nfs5Bands(colors: number[], stripePackage: number[] | null, styleStripe: boolean): number[] {
  const bands = Array.from({ length: 18 }, (_, k) => {
    const index = stripePackage ? (stripePackage[k] ?? 0) : k === 14 || k === 15 ? 3 : 0;
    return colors[index] ?? colors[0] ?? 0xffffff;
  });
  if (styleStripe) {
    bands[6] = colors[1] ?? bands[6];
  }
  return bands;
}

/** A texel alpha's paint band 0..17, or null untinted (CarTex_BlitTinted 0x444130: k = (A + 1) x 20 >> 8) */
export function nfs5PaintBand(alpha: number): number | null {
  const k = ((alpha + 1) * 20) >> 8;
  if (k === 0 || k === 10 || k === 20) {
    return null;
  }
  return k < 10 ? 18 - k : 19 - k;
}

/**
 * The needles' turns (0x438440): the rev counter record+0x528 x rpm (car+0xdb4) x 0.001 + record+0x524, the
 * speedometer record+0x530 x speed (m/s) x 0.144 + record+0x52c (the car record's `_TACH0RPM`, `_TACH1000RPM`,
 * `_SPEEDO0KM`, `_SPEEDO100KM`, nfs5.car)
 */
export function nfs5NeedleTurns(
  rpm: number,
  speed: number,
  calibration: { tach0: number; tachScale: number; speedo0: number; speedoScale: number },
): { tachometer: number; speedometer: number } {
  return {
    tachometer: calibration.tachScale * rpm * 0.001 + calibration.tach0,
    speedometer: calibration.speedoScale * speed * 0.144 + calibration.speedo0,
  };
}

/**
 * The render caps of the game's car chrome option `Graphics.CarChrome` (CARCHROME, 0x657d60: 0 off, 1, 2) as
 * 0x44ed10 sets them (0x6197f8, the key 0x44bb70 compiles a material's render method with, 0x44bf70): 0 -> 1, 1 or 2
 * -> 3. Level 2 also sets 0x6197cb (the sky map textures, 0x43a560) and 0x6197ca (the track shadow map). SKIPPED: the
 * caps 4 of hardware flag 0x6197a8 (one multi-texture pass, the same textures: groups of caps mask 4)
 */
export function nfs5RenderCaps(carChrome: number): number {
  return carChrome <= 0 ? 1 : 3;
}

/**
 * Whether a reflection layer is drawn with the render caps: a render method group is compiled when its caps mask is
 * 0 or shares a bit with the caps (0x44bf70). CarExtEnv's specular and sky map passes have the mask 2 (car chrome 1
 * and 2), CarWindow's 0 (always)
 */
export function nfs5LayerDrawn(layer: Nfs5CarMaterialLayer | null | undefined, caps: number): boolean {
  return !!layer && layer.passes.some(mask => mask === 0 || (mask & caps) !== 0);
}

/**
 * The texture level of a reflection layer's parameter (R3DSpecularTextureLayer 0x445520, R3DSkyMapTextureLayer
 * 0x445b10): below 0.05 (0x5b38b0) 0, below 0.95 (0x5b38b4) 1, else 2. The game's materials bind 0, 0.5 or 1
 */
export function nfs5SpecularLevel(param: number): number {
  return param < 0.05 ? 0 : param < 0.95 ? 1 : 2;
}

/**
 * The specular textures of `CarModel/carcmn.fsh` by level (CarTex_LoadGlobals 0x443760 loads the file; 0x441a10 puts
 * them into R3DCar+0x3b8 by 0x440940): a race's SPC1 (empty: alpha 0), SPC2, SPC3, the front end's FEDU (empty), "FE  ",
 * FESH. A level without a texture draws nothing (0x445520)
 */
export const NFS5_SPECULAR_TEXTURES = { race: ['SPC1', 'SPC2', 'SPC3'], frontEnd: ['FEDU', 'FE  ', 'FESH'] };

/**
 * The specular texture coordinates of a view-space normal `n` (x right, y up, z towards the camera; three.js's view
 * space) as R3DSpecularTextureLayer 0x445520 computes them per vertex from the game's normals (the `mn` part, layer
 * `nm`) turned by the model-view rotation: u = 0.5 + x f, v = 0.5 + y f, f = 0.5 / sqrt(|z| + 1) (a fast inverse
 * square root with 1.47 / 0.47 Newton constants, 0x5b38d8 / 0x5b38e0), Direct3D's v (0 the top row). A sphere map with
 * the front and back alike; the textures' lights are at the bottom: normals turned up reflect them. GUESS: EAGL's view
 * space has y up (as nfs3.exe's sphere maps, the sky at the bottom), not checked in the camera code
 */
export function nfs5SpecularUv(n: [number, number, number]): [number, number] {
  const f = 0.5 / Math.sqrt(Math.abs(n[2]) + 1);
  return [0.5 + n[0] * f, 0.5 + n[1] * f];
}

/**
 * The specular pass's colour over the car's (0..1 display values): the pass (a group of its own) sets its render
 * state block (1, 2, 0, 1, 0, -1) (EAGL 0x540660: THRASH states 6, 0xa, 0x38, 2, 0x18): state 0xa = 2 blends
 * (D3DRENDERSTATE_ALPHABLENDENABLE, dx7z.dll THRASH_setstate 0x60003f23), state 0x38 = 0 with source alpha and inverse
 * source alpha (0x600046d2), and draws the texel times the vertex colour over the framebuffer. The vertex colour is the
 * base pass's lighting (R3DLightLayer 0x446530 writes it, alpha 0xff): `light` (1 in the controller, which has no game
 * lighting). GUESS: texture stage 0 modulates colour and alpha by the vertex colour (THRASH state 0x29's stage 0 case,
 * dx7z.dll 0x600041aa); the value the game leaves in state 0x29 is not traced
 */
export function nfs5SpecularBlend(
  base: [number, number, number],
  texel: [number, number, number, number],
  light: [number, number, number] = [1, 1, 1],
): [number, number, number] {
  const a = texel[3];
  return [0, 1, 2].map(c => base[c] * (1 - a) + texel[c] * light[c] * a) as [number, number, number];
}

/**
 * The alpha of the scene's sky drawn as the specular pass of `level` (for a scene with no game texture), by `up`, the y
 * of the view-space normal: what the race's texture of the level adds on average with the pass's blend
 * (nfs5SpecularBlend), mean texel alpha x luminance over the normals of each band of `up` (normals uniform over the
 * sphere, mapped by nfs5SpecularUv; decomp/nfs5/port-work/car-render/probes/specular_strength.py), over the
 * brightness of a usual sky, 0.68 (the one fce3SkyChromeAlpha assumes): SPC2 and SPC3 reflect up-facing normals only
 * (bands of 0.2 from -1: SPC2 0, 0.001, 0.005, 0.005, 0.007, 0.031, 0.082, 0.261, 0.338, 0.260; SPC3 0 up to 0.2,
 * then 0.028, 0.153, 0.357, 0.308), mean alpha 0.077 / 0.065 over all normals, their lights' grey about 0.85. Linear
 * between the bands' middles; level 0 (SPC1, empty) none
 */
export function nfs5SkySpecularAlpha(level: number, up: number): number {
  const table = NFS5_SKY_SPECULAR_ALPHA[level];
  if (!table) {
    return 0;
  }
  const x = Math.max(0, Math.min(table.length - 1, (up + 0.9) / 0.2));
  const i = Math.min(table.length - 2, Math.floor(x));
  return table[i] + (table[i + 1] - table[i]) * (x - i);
}

/** nfs5SkySpecularAlpha's bands (up -0.9, -0.7 .. 0.9) by level */
export const NFS5_SKY_SPECULAR_ALPHA: number[][] = [
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0.001, 0.005, 0.005, 0.007, 0.031, 0.082, 0.261, 0.338, 0.26],
  [0, 0, 0, 0, 0, 0, 0.028, 0.153, 0.357, 0.308],
];
