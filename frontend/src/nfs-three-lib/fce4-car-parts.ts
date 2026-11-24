import {
  BufferAttribute,
  BufferGeometry,
  Group,
  Material,
  Matrix4,
  Mesh,
  MeshBasicMaterial,
  Object3D,
  SRGBColorSpace,
  Texture,
  TextureLoader,
  Vector3,
} from 'three';

/**
 * The parts of an NFS4 car.fce (FCE4) as nfs4.exe draws them in a race (Render_CarParts 0x50dd60) and damages them
 * (Car_DamageVisual 0x44a510): which parts show, the parts it turns, the body's lean, and the damage of a hit (the
 * vertices blended towards their damaged positions, broken windows, mirrors and lights). Every state is set by the
 * app that draws the car (TailsLab's viewer: its controls; a game: its car's state), nothing changes by itself.
 *
 * Meshes are found by TailsLab's names: "<lod>_<part index>_<part name>__<texture>[_translucent][_matte|_high_chrome]
 * [_window...][_damaged]" (part names without ":", e.g. "hp_4_HB__car00"). Data from TailsLab's export: the part
 * positions (`partPositions`, the pivots), the damaged positions (GLB morph target "damaged", or the "<mesh>_damaged"
 * copy of an OBJ, same vertices) and normals (the chrome's: GLB `_game_normal` and `_game_normal_damaged`, OBJ
 * `normal` and the copy's `normal`), the window classes (mesh name suffix "_window[_front][_left][_back][_right]
 * [_breakaway]") and the vertices of :OD and :OH that turn (geometry attribute `_fce_turns`, > 0.5: the FCE animation
 * flag without bit 2).
 * Positions are in the model's axes as TailsLab exports them: x right, y forward, z up, metres.
 *
 * Each part's meshes go into a group of their own (`<part key>__part`, all of them in the group `fce4_body`, which
 * leans): the parts are shown, hidden and turned through these groups, so the meshes' own `visible` stays the app's.
 * Wheels and brakes stay where they are (FceCarMeshController turns them).
 */

/** nfs4.exe 0x5bed14 tables: the parts a race draws, by name; the body by LOD (H, M, L, T) */
export type Fce4PartName =
  'HB' | 'MB' | 'LB' | 'TB' | 'OT' | 'OL' | 'OS' | 'OLM' | 'ORM' | 'OC' | 'ODL' | 'OH' | 'OD' | 'OND';

/** FCE4 window sides: triangle flag bits 6..9 (front, left, back, right) */
const WINDOW_SIDES = ['front', 'left', 'back', 'right'] as const;
export type Fce4WindowSide = (typeof WINDOW_SIDES)[number];

/** Car_DamageVisual 0x44a510: the parts a hit damages (Fce_DamageVertices 0x4ed390), every LOD */
const DAMAGED_PARTS = ['HB', 'MB', 'LB', 'OL', 'OT'];

/** Car_DamageVisual: a hit of more than this breaks the lights and the license plate within its radius (0x593215) */
export const FCE4_LIGHT_BREAK_AMOUNT = 0.25;

/**
 * Fce_BreakWindows 0x4ed0e0: a window triangle's vertex 0 damaged more than this (0x59a26c) breaks the glass of its
 * sides away
 */
export const FCE4_WINDOW_BREAK_AWAY_WEIGHT = 0.5;

/** Light dummies a hit breaks, by their first letter (kind): headlight, taillight, reverse, brake, indicator; not the sirens */
const BREAKABLE_LIGHT_KINDS = 'HTRBP';

/** nfs4.exe: the steering wheel turns -128 / 0x10000 turn per steering step, the front wheels 36 / 0x10000 */
export const FCE4_STEERING_WHEEL_RATIO = 128 / 36;

/** The vertex alpha of translucent polygons (CarDraw_SetAlphas 0x4f01e0: car+0xd4 >> 2, car+0xd4 0xff) */
export const FCE4_TRANSLUCENT_ALPHA = 0x3f / 255;

/** Part key and name of a mesh name: "hp_9_OS__car00_damaged" -> "hp_9_OS", "OS" */
export function fce4PartOf(meshName: string): { key: string; name: string } | null {
  const match = /^((?:hp|mp|lp|tp)_\d+_([A-Za-z0-9]+))(?=__|_|$)/.exec(meshName);
  return match ? { key: match[1], name: match[2].toUpperCase() } : null;
}

/** Window class of a mesh name (TailsLab's suffix of FCE4 window triangles): side bits (1 front .. 8 right) */
export function fce4WindowOf(meshName: string): { sides: number; breaksAway: boolean } | null {
  const match = /_window((?:_(?:front|left|back|right))*)(_breakaway)?(?:_damaged)?$/.exec(meshName);
  if (!match) {
    return null;
  }
  const sides = WINDOW_SIDES.reduce((bits, side, i) => (match[1].includes(`_${side}`) ? bits | (1 << i) : bits), 0);
  return { sides, breaksAway: !!match[2] };
}

/** What a hit broke, for the app's sounds and effects (the exe's events 0xc: glass, 0xd: mirror or light) */
export type Fce4HitResult = {
  /** vertices moved */
  damaged: boolean;
  /** window triangles cracked by this hit */
  windowsCracked: number;
  /** window triangles whose glass broke away by this hit */
  windowsBrokenAway: number;
  /** mirror part names broken by this hit ("OLM", "ORM") */
  mirrorsBroken: string[];
  /** dummy indices (lights, license plate) broken by this hit */
  dummiesBroken: number[];
};

/** The damage of a car, to keep and restore (nfs4.exe keeps its per-vertex weights, 0x4ed8a0) */
export type Fce4DamageState = {
  /** damage weight 0..1 per vertex, by mesh name */
  weights: { [mesh: string]: number[] };
  mirrorsBroken: string[];
  dummiesBroken: number[];
};

export type Fce4CarPartsOptions = {
  /** part position (pivot) by part key ("hp_9_OS"), model axes: TailsLab's `fcePartPositions` */
  partPositions?: { [key: string]: number[] };
  /** half size of the model, FCE header +0x4c (game axes: x right, y up, z forward): the body's lift when it leans */
  halfSize?: { x: number; y: number; z: number } | null;
  /** dummies (name, position in model axes), the lights and license plate a hit breaks */
  dummies?: { name: string; position: number[] }[];
  /** broken window glass, `Data/FeArt/3dobj.fsh` shat (URL or texture). None: cracked windows look as before */
  brokenGlassTexture?: string | Texture | null;
};

type Part = {
  key: string;
  name: string;
  group: Group;
  pivot: Vector3;
};

type Window = {
  sides: number;
  breaksAway: boolean;
  // corner vertex indices, 3 per triangle
  triangles: Uint32Array;
  // per triangle: cracked, broken away
  cracked: Uint8Array;
  brokenAway: Uint8Array;
  glass: Mesh | null;
};

type DamageMesh = {
  mesh: Mesh;
  part: Part;
  // inverse of the mesh's place in the model at setup (identity for TailsLab's meshes)
  toLocal: Matrix4;
  base: Float32Array;
  damaged: Float32Array | null;
  // the normals blended with the positions: the geometry attribute, its undamaged and damaged values
  normals: { attribute: string; base: Float32Array; damaged: Float32Array } | null;
  weights: Float32Array;
  window: Window | null;
};

type TurningMesh = {
  mesh: Mesh;
  part: Part;
  toLocal: Matrix4;
  base: Float32Array;
  // vertex indices that turn
  turning: number[];
};

export class Fce4CarParts {
  /** the group of the body's parts (everything but the wheels and the brakes), leaned by bodyPitch / bodyRoll */
  readonly body = new Group();
  private readonly parts = new Map<string, Part>();
  private readonly damageMeshes: DamageMesh[] = [];
  private readonly turningMeshes: TurningMesh[] = [];
  private readonly ownGeometries = new Set<BufferGeometry>();
  private readonly ownMaterials = new Set<Material>();
  // `<mesh>_damaged` copies (OBJ) by the mesh's name, taken out of the model
  private readonly damagedCopies = new Map<string, Mesh>();
  private readonly mirrorsBroken = new Set<string>();
  private readonly dummiesBroken = new Set<number>();
  private readonly dummies: { name: string; position: Vector3 }[];
  private readonly halfSize: { x: number; y: number; z: number } | null;
  private glassTexture: Texture | null = null;
  private damageReady = false;
  private disposed = false;

  /** called when a dummy breaks (the controller hides its light) */
  onDummyBroken: ((index: number, broken: boolean) => void) | null = null;

  constructor(
    private readonly root: Object3D,
    options: Fce4CarPartsOptions = {},
  ) {
    this.halfSize = options.halfSize ?? null;
    this.dummies = (options.dummies ?? []).map(d => ({ name: d.name, position: new Vector3().fromArray(d.position) }));
    this.body.name = 'fce4_body';
    root.add(this.body);
    root.updateMatrixWorld(true);
    const rootInverse = new Matrix4().copy(root.matrixWorld).invert();
    const meshes: Mesh[] = [];
    root.traverse(o => {
      // the root itself stays where it is
      if (o instanceof Mesh && o !== root) {
        meshes.push(o);
      }
    });
    for (const mesh of meshes) {
      if (/_damaged$/.test(mesh.name)) {
        const base = mesh.name.replace(/_damaged$/, '');
        if (meshes.some(m => m.name === base)) {
          this.damagedCopies.set(base, mesh);
          mesh.removeFromParent();
        }
        continue;
      }
      const part = fce4PartOf(mesh.name);
      if (!part || /^[HM][LR][FMR]W$/.test(part.name) || /^O[LR]B$/.test(part.name)) {
        // wheels and brakes: FceCarMeshController's
        continue;
      }
      let entry = this.parts.get(part.key);
      if (!entry) {
        const position = options.partPositions?.[part.key];
        const pivot = position ? new Vector3().fromArray(position) : this.boxCentre(meshes, part.key);
        entry = { key: part.key, name: part.name, group: new Group(), pivot };
        entry.group.name = `${part.key}__part`;
        this.body.add(entry.group);
        this.parts.set(part.key, entry);
      }
      const place = new Matrix4().multiplyMatrices(rootInverse, mesh.matrixWorld);
      entry.group.attach(mesh);
      const toLocal = place.invert();
      if (part.name === 'OD' || part.name === 'OH') {
        this.setupTurning(mesh, entry, toLocal);
      }
      if (DAMAGED_PARTS.includes(part.name)) {
        this.damageMeshes.push({
          mesh,
          part: entry,
          toLocal,
          base: new Float32Array(0),
          damaged: null,
          normals: null,
          weights: new Float32Array(0),
          window: null,
        });
      }
      if (/_translucent/.test(mesh.name)) {
        // translucent polygons: the texture times the vertex alpha 0x3f
        for (const material of Array.isArray(mesh.material) ? mesh.material : [mesh.material]) {
          material.opacity = FCE4_TRANSLUCENT_ALPHA;
        }
      }
    }
    if (options.brokenGlassTexture instanceof Texture) {
      this.glassTexture = options.brokenGlassTexture;
    } else if (options.brokenGlassTexture) {
      new TextureLoader().load(options.brokenGlassTexture, texture => {
        if (this.disposed) {
          texture.dispose();
          return;
        }
        texture.colorSpace = SRGBColorSpace;
        // texture coordinates as the exe's: v = 0 is the top row
        texture.flipY = false;
        texture.needsUpdate = true;
        this.glassTexture = texture;
        this.ownedGlassTexture = texture;
        this.updateWindows(null);
      });
    }
    this.update();
  }

  private ownedGlassTexture: Texture | null = null;

  private boxCentre(meshes: Mesh[], key: string): Vector3 {
    const centre = new Vector3();
    let count = 0;
    for (const mesh of meshes) {
      if (fce4PartOf(mesh.name)?.key !== key || /_damaged$/.test(mesh.name)) {
        continue;
      }
      mesh.geometry.computeBoundingBox();
      centre.add(mesh.geometry.boundingBox!.getCenter(new Vector3()));
      count++;
    }
    return count ? centre.divideScalar(count) : centre;
  }

  /** Whether the model has a part (any LOD), e.g. "OL" for pop-up headlights */
  has(name: Fce4PartName): boolean {
    return [...this.parts.values()].some(p => p.name === name);
  }

  /** Whether the model has a part damaged by hits (the bodies, :OL, :OT) */
  get hasDamage(): boolean {
    return this.damageMeshes.length > 0;
  }

  private _headlights = false;
  /**
   * Headlights on: the pop-up headlights :OL and the lit dashboard :ODL show (Render_CarParts: car+0x5f4, the
   * headlights state, or car+0x6ec, a chasing cop's flag)
   */
  get headlights(): boolean {
    return this._headlights;
  }

  set headlights(value: boolean) {
    this._headlights = value;
    this.update();
  }

  private _roofClosed = true;
  /** The convertible's top :OT shows (Render_CarParts: car+0xad0 0, or 1 with the top closed; 2 open, FeCars_IsOpenTop) */
  get roofClosed(): boolean {
    return this._roofClosed;
  }

  set roofClosed(value: boolean) {
    this._roofClosed = value;
    this.update();
  }

  private _driverInCar = true;
  /** The driver :OD and the head :OH show, else the empty seat :OND (a cop out of his car, car+0xa14 +0x1f8 bit 0) */
  get driverInCar(): boolean {
    return this._driverInCar;
  }

  set driverInCar(value: boolean) {
    this._driverInCar = value;
    this.update();
  }

  private _driverHeadYaw = 0;
  /**
   * The driver's head (:OH) turn in radians, positive to the left: the turning vertices about the part position, up
   * axis (nfs4.exe: RotY(car+0x988 turns), positive to the right: this is -car+0x988 x 2 pi). The game turns it
   * 0.01 turn per tick towards the direction to a car nearby plus 24 / 0x10000 turn per steering step above 3 m/s,
   * at most 0.2 turn (0x44c430)
   */
  get driverHeadYaw(): number {
    return this._driverHeadYaw;
  }

  set driverHeadYaw(value: number) {
    this._driverHeadYaw = value;
    this.updateTurning();
  }

  private _steeringAngle = 0;
  /**
   * The front wheels' angle in radians, positive to the left (FceCarMeshController.steeringAngle): the steering wheel
   * of :OD (its turning vertices) turns FCE4_STEERING_WHEEL_RATIO times as far about the part position, forward
   * axis (RotZ(-car+0x464 x 0x80 / 0x10000 turn))
   */
  get steeringAngle(): number {
    return this._steeringAngle;
  }

  set steeringAngle(value: number) {
    if (value !== this._steeringAngle) {
      this._steeringAngle = value;
      this.updateTurning();
    }
  }

  private _spoilerAngle = 0;
  /**
   * The spoiler :OS (air brake) in radians about its part position, right axis, positive lifts its rear edge
   * (RotX(car+0x96c turns)). The game moves car+0x96c 0.00556 turn per tick towards the air brake's angle car+0x970
   * (0x44c430): 0.25 turn braking, 0.0694 / (forward speed - 11.18) + 0.0278 above 11.18 m/s, else 0
   */
  get spoilerAngle(): number {
    return this._spoilerAngle;
  }

  set spoilerAngle(value: number) {
    this._spoilerAngle = value;
    this.update();
  }

  private _bodyPitch = 0;
  /**
   * The body's lean forward in radians, positive dips the nose (Render_CarParts 0x50bfa0: RotX(car+0x974 turns),
   * from the car's acceleration, body damage and shaking: 0x44bd80). Not the wheels
   */
  get bodyPitch(): number {
    return this._bodyPitch;
  }

  set bodyPitch(value: number) {
    this._bodyPitch = value;
    this.update();
  }

  private _bodyRoll = 0;
  /** The body's lean sideways in radians, positive lifts the right side (RotZ(car+0x978 turns)). Not the wheels */
  get bodyRoll(): number {
    return this._bodyRoll;
  }

  set bodyRoll(value: number) {
    this._bodyRoll = value;
    this.update();
  }

  private _bodyLift = true;
  /**
   * A leaning body is lifted by max(|sin roll| x half width, |sin pitch| x half length) (0x50bfa0: while the car is
   * upright, car+0x80 >= 0.9), with `halfSize`
   */
  get bodyLift(): boolean {
    return this._bodyLift;
  }

  set bodyLift(value: boolean) {
    this._bodyLift = value;
    this.update();
  }

  /** Whether a mirror (part name "OLM", "ORM") broke off */
  isMirrorBroken(name: 'OLM' | 'ORM'): boolean {
    return this.mirrorsBroken.has(name);
  }

  /** Dummy indices broken by hits (lights, the license plate): the app stops drawing them */
  get brokenDummies(): ReadonlySet<number> {
    return this.dummiesBroken;
  }

  private update() {
    if (this.disposed) {
      return;
    }
    for (const part of this.parts.values()) {
      part.group.visible = this.partShown(part.name);
      if (part.name === 'OS') {
        // T(pivot) R T(-pivot); positive lifts the rear edge (-y)
        part.group.rotation.set(-this._spoilerAngle, 0, 0);
        part.group.position.copy(part.pivot).sub(part.pivot.clone().applyEuler(part.group.rotation));
      }
    }
    // RotX(pitch) after RotZ(roll) in the exe's row vectors: nose down is -x here, right side up -y
    this.body.rotation.set(-this._bodyPitch, -this._bodyRoll, 0, 'XYZ');
    const half = this.halfSize;
    this.body.position.z =
      this._bodyLift && half
        ? Math.max(Math.abs(Math.sin(this._bodyRoll)) * half.x, Math.abs(Math.sin(this._bodyPitch)) * half.z)
        : 0;
  }

  private partShown(name: string): boolean {
    switch (name) {
      case 'OL':
      case 'ODL':
        return this._headlights;
      case 'OT':
        return this._roofClosed;
      case 'OD':
      case 'OH':
        return this._driverInCar;
      case 'OND':
        return !this._driverInCar;
      case 'OLM':
      case 'ORM':
        return !this.mirrorsBroken.has(name);
      default:
        return true;
    }
  }

  private setupTurning(mesh: Mesh, part: Part, toLocal: Matrix4) {
    const turns = mesh.geometry.getAttribute('_fce_turns');
    const count = mesh.geometry.getAttribute('position').count;
    const turning: number[] = [];
    for (let i = 0; i < count; i++) {
      // no data: the head turns whole (all its vertices have the flag clear in NFS4's cars), the driver stays
      if (turns ? turns.getX(i) > 0.5 : part.name === 'OH') {
        turning.push(i);
      }
    }
    if (turning.length) {
      this.turningMeshes.push({ mesh, part, toLocal, base: new Float32Array(0), turning });
    }
  }

  private readonly rotation = new Matrix4();

  private updateTurning() {
    for (const t of this.turningMeshes) {
      const angle = t.part.name === 'OH' ? this._driverHeadYaw : -this._steeringAngle * FCE4_STEERING_WHEEL_RATIO;
      if (!t.base.length && angle === 0) {
        continue;
      }
      const position = this.ownPositions(t.mesh);
      if (!t.base.length) {
        t.base = Float32Array.from(position.array as Float32Array);
      }
      // the pivot in the mesh's space: about z (up) for the head, y (forward) for the steering wheel
      const pivot = t.part.pivot.clone().applyMatrix4(t.toLocal);
      this.rotation.makeRotationAxis(new Vector3(0, t.part.name === 'OH' ? 0 : 1, t.part.name === 'OH' ? 1 : 0), angle);
      const v = new Vector3();
      for (const i of t.turning) {
        v.fromArray(t.base, i * 3)
          .sub(pivot)
          .applyMatrix4(this.rotation)
          .add(pivot);
        position.setXYZ(i, v.x, v.y, v.z);
      }
      position.needsUpdate = true;
    }
  }

  /** The mesh's position attribute, on a geometry of its own (the app may share geometries between cars) */
  private ownPositions(mesh: Mesh): BufferAttribute {
    if (!this.ownGeometries.has(mesh.geometry)) {
      mesh.geometry = mesh.geometry.clone();
      this.ownGeometries.add(mesh.geometry);
    }
    return mesh.geometry.getAttribute('position') as BufferAttribute;
  }

  private setupDamage() {
    if (this.damageReady) {
      return;
    }
    this.damageReady = true;
    for (const d of this.damageMeshes) {
      const geometry = d.mesh.geometry;
      const source = geometry.getAttribute('position');
      const count = source.count;
      d.base = new Float32Array(count * 3);
      for (let i = 0; i < count; i++) {
        d.base.set([source.getX(i), source.getY(i), source.getZ(i)], i * 3);
      }
      d.weights = new Float32Array(count);
      // GLB: morph target "damaged" (relative); OBJ: the "_damaged" copy with the same vertices
      const morph = d.mesh.morphTargetDictionary?.['damaged'];
      const target = morph === undefined ? null : geometry.morphAttributes['position']?.[morph];
      const copy = this.damagedCopies.get(d.mesh.name)?.geometry.getAttribute('position');
      if (target && target.count === count) {
        d.damaged = new Float32Array(count * 3);
        const relative = geometry.morphTargetsRelative;
        for (let i = 0; i < count; i++) {
          d.damaged.set(
            [target.getX(i), target.getY(i), target.getZ(i)].map((x, c) => (relative ? d.base[i * 3 + c] + x : x)),
            i * 3,
          );
        }
      } else if (copy && copy.count === count) {
        d.damaged = new Float32Array(count * 3);
        for (let i = 0; i < count; i++) {
          d.damaged.set([copy.getX(i), copy.getY(i), copy.getZ(i)], i * 3);
        }
      }
      // the normals the chrome reads (FceCarMeshController: the game's, else the OBJ's), damaged as the positions:
      // GLB `_game_normal_damaged` (the vertices of the morph target), OBJ the copy's normals
      const normalName = geometry.getAttribute('_game_normal') ? '_game_normal' : 'normal';
      const normals = geometry.getAttribute(normalName);
      const damagedNormals =
        target && target.count === count
          ? geometry.getAttribute('_game_normal_damaged')
          : d.damaged
            ? this.damagedCopies.get(d.mesh.name)?.geometry.getAttribute(normalName)
            : undefined;
      if (normals && normals.count === count && damagedNormals && damagedNormals.count === count) {
        const values = (attribute: typeof normals) => {
          const array = new Float32Array(count * 3);
          for (let i = 0; i < count; i++) {
            array.set([attribute.getX(i), attribute.getY(i), attribute.getZ(i)], i * 3);
          }
          return array;
        };
        d.normals = { attribute: normalName, base: values(normals), damaged: values(damagedNormals) };
      }
      const window = fce4WindowOf(d.mesh.name);
      if (window && !Array.isArray(d.mesh.material)) {
        const index = geometry.getIndex();
        const triangles = index
          ? Uint32Array.from(index.array as ArrayLike<number>)
          : Uint32Array.from({ length: count - (count % 3) }, (_, i) => i);
        const n = triangles.length / 3;
        d.window = { ...window, triangles, cracked: new Uint8Array(n), brokenAway: new Uint8Array(n), glass: null };
      }
    }
  }

  /**
   * A hit at `point` (model axes, metres) of `amount` (0..1) within `radius` (metres), as Car_DamageVisual 0x44a510
   * (the race's crash code 0x44c430 calls it with the contact point, the amount and radius of the contact type):
   * every vertex of the bodies (all LODs), :OL and :OT whose undamaged position is within the radius and whose
   * damage is below the amount gets it: its position is undamaged x (1 - amount) + damaged x amount, its normal the
   * same of the undamaged and damaged normals, not normalized (Fce_DamageVertices 0x4ed390: FCE header tables +0x2c /
   * +0x34 -> +0x14, +0x30 / +0x38 -> +0x18, which the chrome pass reads); the windows of those parts crack and break
   * away (Fce_BreakWindows 0x4ed0e0: see updateWindows); a mirror whose part position is within the radius breaks off;
   * above FCE4_LIGHT_BREAK_AMOUNT the first ":LICENSE" dummy and the lights (BREAKABLE_LIGHT_KINDS) within the radius
   * break. SKIPPED: the game's options (damage off, the arrested car) are the app's
   */
  hit(point: { x: number; y: number; z: number }, amount: number, radius: number): Fce4HitResult {
    const result: Fce4HitResult = {
      damaged: false,
      windowsCracked: 0,
      windowsBrokenAway: 0,
      mirrorsBroken: [],
      dummiesBroken: [],
    };
    if (this.disposed) {
      return result;
    }
    this.setupDamage();
    const a = Math.max(0, Math.min(1, amount));
    const r2 = radius * radius;
    const hit = new Vector3(point.x, point.y, point.z);
    const local = new Vector3();
    const touched = new Set<DamageMesh>();
    for (const d of this.damageMeshes) {
      local.copy(hit).applyMatrix4(d.toLocal);
      for (let i = 0; i < d.weights.length; i++) {
        const dx = d.base[i * 3] - local.x;
        const dy = d.base[i * 3 + 1] - local.y;
        const dz = d.base[i * 3 + 2] - local.z;
        if (d.weights[i] < a && dx * dx + dy * dy + dz * dz < r2) {
          d.weights[i] = a;
          touched.add(d);
        }
      }
    }
    for (const d of touched) {
      this.applyWeights(d);
    }
    result.damaged = touched.size > 0;
    const windows = this.updateWindows(new Set([...touched].map(d => d.part)));
    result.windowsCracked = windows.cracked;
    result.windowsBrokenAway = windows.brokenAway;
    for (const part of this.parts.values()) {
      if (
        (part.name === 'OLM' || part.name === 'ORM') &&
        !this.mirrorsBroken.has(part.name) &&
        part.pivot.distanceTo(hit) < radius
      ) {
        this.mirrorsBroken.add(part.name);
        result.mirrorsBroken.push(part.name);
      }
    }
    if (a > FCE4_LIGHT_BREAK_AMOUNT) {
      const license = this.dummies.findIndex(d => d.name.toUpperCase().includes(':LICENSE'));
      const breaks = (i: number) => !this.dummiesBroken.has(i) && this.dummies[i].position.distanceTo(hit) < radius;
      if (license >= 0 && breaks(license)) {
        this.breakDummy(license, result);
      }
      this.dummies.forEach((d, i) => {
        const kind = d.name.charAt(0).toUpperCase();
        if (!d.name.startsWith(':') && BREAKABLE_LIGHT_KINDS.includes(kind) && breaks(i)) {
          this.breakDummy(i, result);
        }
      });
    }
    this.update();
    return result;
  }

  private breakDummy(index: number, result: Fce4HitResult) {
    this.dummiesBroken.add(index);
    result.dummiesBroken.push(index);
    this.onDummyBroken?.(index, true);
  }

  private applyWeights(d: DamageMesh) {
    if (!d.damaged) {
      return;
    }
    const position = this.ownPositions(d.mesh);
    const normals = d.normals;
    const normal = normals ? (d.mesh.geometry.getAttribute(normals.attribute) as BufferAttribute) : null;
    for (let i = 0; i < d.weights.length; i++) {
      const w = d.weights[i];
      for (let c = 0; c < 3; c++) {
        (position.array as Float32Array)[i * 3 + c] = d.base[i * 3 + c] * (1 - w) + d.damaged[i * 3 + c] * w;
        if (normal) {
          (normal.array as Float32Array)[i * 3 + c] =
            normals!.base[i * 3 + c] * (1 - w) + normals!.damaged[i * 3 + c] * w;
        }
      }
    }
    position.needsUpdate = true;
    if (normal) {
      normal.needsUpdate = true;
    }
    d.mesh.geometry.computeBoundingSphere();
    if (d.window?.glass?.visible) {
      this.updateGlassPositions(d);
    }
  }

  /**
   * Fce_BreakWindows 0x4ed0e0, per damaged part: window triangles with a damaged vertex crack, and so do all window
   * triangles of the part on their sides; the "_breakaway" ones break away (not drawn: the software renderer's
   * flag 0x20) once a cracked window triangle of their side has vertex 0 damaged more than
   * FCE4_WINDOW_BREAK_AWAY_WEIGHT. Cracked triangles are drawn with the broken glass texture, (0, 0), (0, 1), (1, 1)
   * on their vertices 0, 1, 2. `parts` null: every part (the glass texture loaded)
   */
  private updateWindows(parts: Set<Part> | null): { cracked: number; brokenAway: number } {
    const count = { cracked: 0, brokenAway: 0 };
    const byPart = new Map<Part, DamageMesh[]>();
    for (const d of this.damageMeshes) {
      if (d.window && (!parts || parts.has(d.part))) {
        byPart.set(d.part, [...(byPart.get(d.part) ?? []), d]);
      }
    }
    for (const meshes of byPart.values()) {
      let crackedSides = 0;
      let brokenSides = 0;
      for (const d of meshes) {
        const { triangles, sides } = d.window!;
        for (let t = 0; t < triangles.length / 3; t++) {
          const [a, b, c] = [triangles[t * 3], triangles[t * 3 + 1], triangles[t * 3 + 2]];
          if (d.weights[a] > 0 || d.weights[b] > 0 || d.weights[c] > 0) {
            crackedSides |= sides;
            if (d.weights[a] > FCE4_WINDOW_BREAK_AWAY_WEIGHT) {
              brokenSides |= sides;
            }
          }
        }
      }
      for (const d of meshes) {
        const w = d.window!;
        let changed = false;
        for (let t = 0; t < w.triangles.length / 3; t++) {
          const [a, b, c] = [w.triangles[t * 3], w.triangles[t * 3 + 1], w.triangles[t * 3 + 2]];
          const cracked = d.weights[a] > 0 || d.weights[b] > 0 || d.weights[c] > 0 || (w.sides & crackedSides) !== 0;
          const brokenAway = w.breaksAway && (w.sides & brokenSides) !== 0;
          if (cracked && !w.cracked[t]) {
            w.cracked[t] = 1;
            count.cracked++;
            changed = true;
          }
          if (brokenAway && !w.brokenAway[t]) {
            w.brokenAway[t] = 1;
            count.brokenAway++;
            changed = true;
          }
        }
        if (changed || !parts) {
          this.drawWindow(d);
        }
      }
    }
    return count;
  }

  /** The window mesh draws its intact triangles, its glass mesh (with the texture) the cracked ones */
  private drawWindow(d: DamageMesh) {
    const w = d.window!;
    const intact: number[] = [];
    const cracked: number[] = [];
    for (let t = 0; t < w.triangles.length / 3; t++) {
      if (w.brokenAway[t]) {
        continue;
      }
      (w.cracked[t] && this.glassTexture ? cracked : intact).push(t);
    }
    const geometry = d.mesh.geometry;
    if (!this.ownGeometries.has(geometry)) {
      this.ownPositions(d.mesh);
    }
    d.mesh.geometry.setIndex(intact.flatMap(t => [w.triangles[t * 3], w.triangles[t * 3 + 1], w.triangles[t * 3 + 2]]));
    if (!cracked.length) {
      if (w.glass) {
        w.glass.visible = false;
      }
      return;
    }
    if (!w.glass) {
      const material = (d.mesh.material as Material).clone() as MeshBasicMaterial;
      material.map = this.glassTexture;
      material.needsUpdate = true;
      this.ownMaterials.add(material);
      w.glass = new Mesh(new BufferGeometry(), material);
      w.glass.name = `${d.mesh.name}__glass`;
      this.ownGeometries.add(w.glass.geometry);
      d.mesh.add(w.glass);
    }
    w.glass.visible = true;
    const uv = [0, 0, 0, 1, 1, 1];
    w.glass.geometry.setAttribute('uv', new BufferAttribute(new Float32Array(cracked.flatMap(() => uv)), 2));
    w.glass.userData['triangles'] = cracked;
    this.updateGlassPositions(d);
  }

  private updateGlassPositions(d: DamageMesh) {
    const glass = d.window!.glass!;
    const cracked: number[] = glass.userData['triangles'];
    const source = d.mesh.geometry.getAttribute('position');
    const positions = new Float32Array(cracked.length * 9);
    cracked.forEach((t, k) => {
      for (let c = 0; c < 3; c++) {
        const i = d.window!.triangles[t * 3 + c];
        positions.set([source.getX(i), source.getY(i), source.getZ(i)], k * 9 + c * 3);
      }
    });
    glass.geometry.setAttribute('position', new BufferAttribute(positions, 3));
    glass.geometry.computeBoundingSphere();
  }

  /** Undamaged again: every vertex, window, mirror and light (as a car repaired in the game's career) */
  repair() {
    this.setDamage({ weights: {}, mirrorsBroken: [], dummiesBroken: [] });
  }

  /** The damage to keep (setDamage restores it) */
  getDamage(): Fce4DamageState {
    const weights: { [mesh: string]: number[] } = {};
    for (const d of this.damageMeshes) {
      if (d.weights.some(w => w > 0)) {
        weights[d.mesh.name] = Array.from(d.weights);
      }
    }
    return { weights, mirrorsBroken: [...this.mirrorsBroken], dummiesBroken: [...this.dummiesBroken] };
  }

  /** Restores the damage of getDamage (the windows follow from the weights) */
  setDamage(state: Fce4DamageState) {
    if (this.disposed) {
      return;
    }
    this.setupDamage();
    for (const d of this.damageMeshes) {
      const weights = state.weights[d.mesh.name];
      const changed = !!weights || d.weights.some(w => w > 0);
      d.weights.fill(0);
      if (weights && weights.length === d.weights.length) {
        d.weights.set(weights);
      }
      if (d.window) {
        d.window.cracked.fill(0);
        d.window.brokenAway.fill(0);
      }
      if (changed) {
        this.applyWeights(d);
      }
    }
    this.updateWindows(null);
    this.mirrorsBroken.clear();
    state.mirrorsBroken.forEach(name => this.mirrorsBroken.add(name));
    for (const i of [...this.dummiesBroken]) {
      if (!state.dummiesBroken.includes(i)) {
        this.dummiesBroken.delete(i);
        this.onDummyBroken?.(i, false);
      }
    }
    for (const i of state.dummiesBroken) {
      if (!this.dummiesBroken.has(i)) {
        this.dummiesBroken.add(i);
        this.onDummyBroken?.(i, true);
      }
    }
    this.update();
  }

  dispose() {
    this.disposed = true;
    for (const geometry of this.ownGeometries) {
      geometry.dispose();
    }
    for (const material of this.ownMaterials) {
      material.dispose();
    }
    this.ownedGlassTexture?.dispose();
  }
}
