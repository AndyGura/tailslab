import {
  AdditiveBlending,
  BufferAttribute,
  BufferGeometry,
  Box3,
  DataTexture,
  DoubleSide,
  LinearFilter,
  Material,
  Matrix4,
  Mesh,
  MeshBasicMaterial,
  NearestFilter,
  Object3D,
  RGBAFormat,
  Vector3,
} from 'three';
import {
  Nfs5CarData,
  Nfs5CarArticle,
  Nfs5CarGlare,
  Nfs5Lights,
  NFS5_ANIMATION_COUNT,
  NFS5_COCKPIT_DRIVER_LOD,
  NFS5_COCKPIT_ZONE_LIMITS,
  NFS5_DAMAGE_WEIGHT,
  NFS5_DRAW_BODY,
  NFS5_DRAW_DAMAGE,
  NFS5_DRAW_DRIVER,
  NFS5_DRAW_STEERING_WHEEL,
  NFS5_DRAW_WHEELS,
  NFS5_OUTSIDE_DRIVER_LOD,
  NFS5_PIVOT_COUNT,
  NFS5_STEERING_WHEEL_LIMIT,
  NFS5_WHEEL_LODS,
  NFS5_ZONES,
  nfs5Bands,
  nfs5HitZones,
  nfs5Lights,
  nfs5RaceSlots,
  nfs5ZoneDamageAfterHit,
} from './nfs5-car-parts';

export * from './nfs5-car-parts';

// wheel radius (m) for the spin rate at a speed, without a wheel to measure
const WHEEL_RADIUS = 0.33;

// mesh name: <article name>[_a<article index>]_LOD<lod>_ai<animation frame>[_<texture>][_damaged], with an optional
// duplicate suffix ".001", which three.js GLTFLoader turns into "001" (it strips dots and replaces spaces with
// underscores)
const NFS5_MESH_NAME_REGEX =
  /^(.*?)(?:_a(\d+))?_LOD(\d+)_ai(\d+?)(?:\.?\d{3})?(?:_(.*?))?(_damaged)?(?:\.?\d{3})?(?:_\d+)?$/;

// wheel articles: "WheelFront", "WheelRear", alternative rims "WheelRear1", low LOD "TreadFront"
const NFS5_WHEEL_REGEX = /^(?:Wheel|Tread)(Front|Rear)\d*$/i;

// without the model data: articles, which are never a part of the car exterior: driver (10 variants of body, arms,
// hands and legs), passenger, wheel shadow planes, cabrio roof (convertible top, its folded and unfolded states),
// race decals
const NFS5_HIDDEN_ARTICLES_REGEX =
  /^(?:DriverBody\d*|LODDriver\d*|(?:Left|Right)(?:Arm|Hand)\d*|Legs\d*|Passenger|WheelShadow.*|Cabrio.*|InteriorCabrio|DecalDoor.*|Decal.*R)$/i;

// a material of a texture page: "page_<n>" (its alpha the paint bands), "page_<n>_alpha" (wheels, windows)
const PAGE_MATERIAL_REGEX = /^page_(\d+)(_alpha)?(?:\.?\d{3})?$/;

const TURN = 2 * Math.PI;

export type Nfs5MeshNameInfo = {
  article: string;
  /** the article's index in the CRP (TailsLab's car export since the `nfs5Car` data), null in older names */
  articleIndex: number | null;
  lod: number;
  animationFrame: number;
  isDamaged: boolean;
};

export type Nfs5View = 'outside' | 'cockpit';

export type Nfs5CarMeshControllerOptions = {
  /** turn the model around (meshes' geometry is modified): X right, Y forward, Z up, as other controllers expect */
  turnToYForward?: boolean;
  /** TailsLab's `nfs5Car` (the `.meta` of the GLB, the OBJ's `_extra.json`). Without it: a guessed default look */
  car?: Nfs5CarData | null;
  /** the OBJ's `nfs5DamageZones` (mesh name -> zone per face corner); the GLB has `_nfs5_damage_zone` */
  damageZones?: { [mesh: string]: number[] } | null;
  /** the body style (0-based `.tpg` `[style<n + 1>]`), default 0 */
  bodyStyle?: number;
  /** the game's car detail (0x6197c4: 0 low, 1 medium, 2 high), default 2 */
  detail?: number;
};

type MeshEntry = {
  mesh: Mesh;
  info: Nfs5MeshNameInfo;
  article: Nfs5CarArticle | null;
  /** the mesh's matrix as loaded (after the turn) */
  base: Matrix4;
  /** the article's transformation of the mesh's level (CRP axes, column vectors) and its inverse */
  transform: Matrix4;
  inverse: Matrix4;
};

type AnimatedMesh = {
  entry: MeshEntry;
  // GLB: the morph target index of frame k (1..); else (OBJ) the positions of frame k (0..), from the frames' meshes
  morphIndices: (number | undefined)[] | null;
  framePositions: (Float32Array | undefined)[];
  count: number;
};

type DamageMesh = {
  entry: MeshEntry;
  base: Float32Array;
  offsets: Float32Array;
  zones: Uint8Array;
};

type GlareMesh = {
  mesh: Mesh;
  article: Nfs5CarArticle;
  light: number;
  base: Matrix4;
  transform: Matrix4;
  inverse: Matrix4;
};

type Animation = { frame: number; next: number; fraction: number; max: number };

/**
 * An NFS5 (Porsche Unleashed) car model (*.crp) as Porsche.exe draws it in a race (nfs-web
 * `decomp/nfs5/Porsche.exe.gzf`, the class R3DCar and its levels of detail R3DCarLOD): which meshes show, the pivots
 * it turns (wheels, steering wheel, needles, doors, hood, trunk, pop-up headlights, spoiler), the animations
 * (driver, arms, convertible top, speed wing), the damage (dents by zone), the lights (glares) and the paint. Every
 * state is set by the app that draws the car (TailsLab's viewer: its controls; a game: its car's state); nothing
 * changes by itself but the wheels spinning at `speed`.
 *
 * Meshes are found by TailsLab's names: "<article>_a<article index>_LOD<lod>_ai<animation frame>[_<texture>]
 * [_damaged]", X left, Y backward (the car front is at -Y), Z up (the CRP's x, z, y). The model data (`car`, the
 * export's `nfs5Car`) gives each article's slot, flags, pivot, animation and transformation:
 * - An article shows when the car's geometry configuration has its value at its slot (R3DCarLOD_Build 0x43c1b0;
 *   `slots`, from the body style, the race and the parts: `nfs5RaceSlots`), at the level of detail the draw passes
 *   take for its draw flags and the view (R3DCar_Draw 0x444e00), only the first animation frame and never the damaged
 *   copies (the frames and the dents are blended into the first frame's mesh).
 * - A pivot turns its articles about their origin (the CRP `rt` part): x, then y, then z in the article's axes,
 *   angles in turns (R3DCarLOD_Draw 0x43c830); the doors about the `.tpg` `dooraxis`.
 * - The animations blend the frames (GLB morph targets "frame<n>", the OBJ's frame meshes), the damage blends the
 *   damaged offsets (GLB morph target "damaged", the OBJ's copies) by the zone of each vertex.
 * Without the model data the controller only spins and steers the wheels, and `defaultExteriorFilter` guesses a look.
 */
export class Nfs5CarMeshController {
  private readonly entries: MeshEntry[] = [];
  private readonly animated: AnimatedMesh[] = [];
  private readonly damageMeshes: DamageMesh[] = [];
  private readonly glares: GlareMesh[] = [];
  private readonly materials = new Map<Material, number>();
  private readonly ownGeometries = new Set<BufferGeometry>();
  private readonly ownMaterials = new Set<Material>();
  private readonly toModel = new Matrix4();
  private readonly fromModel = new Matrix4();
  private readonly car: Nfs5CarData | null;
  private readonly wheelRadius: number;
  private readonly spinSign: number;
  private glareTexture: DataTexture | null = null;
  private disposed = false;

  // guessed wheels without model data
  private wheels: { meshes: Mesh[]; isFront: boolean }[] = [];

  /** R3DCar+0x2d0: per pivot the angles about x, y, z in turns (R3DCar_UpdatePivots 0x438440 sets them) */
  private readonly pivots: number[][] = Array.from({ length: NFS5_PIVOT_COUNT }, () => [0, 0, 0]);
  /** R3DCar+0x568: per animation its frames (R3DCar_SetAnimationFrame 0x4380d0) */
  private readonly animations: Animation[] = Array.from({ length: NFS5_ANIMATION_COUNT }, () => ({
    frame: 0,
    next: 1,
    fraction: 0,
    max: 0,
  }));
  /** car+0x4e4: damage per zone, 0..100 */
  private readonly zoneDamage = new Array<number>(NFS5_ZONES).fill(0);
  /** car+0x56c: the geometry configuration, 120 slots (0..59 geometry, 60..119 texture) */
  private readonly slotValues = new Array<number>(120).fill(0);
  /** the record's GEOMCONFIG (+0x32c): the parts' slots, -1 none */
  private readonly geometryConfig = new Array<number>(120).fill(-1);
  private lights: Nfs5Lights = { on: new Array(14).fill(false), intensity: new Array(14).fill(1) };
  private bands: number[] = new Array(18).fill(0xffffff);
  private readonly bandUniforms = { value: Array.from({ length: 18 }, () => new Vector3(255, 255, 255)) };
  private readonly paintEnabledUniform = { value: 0 };

  constructor(root: Object3D, options: Nfs5CarMeshControllerOptions | boolean = {}) {
    const opts: Nfs5CarMeshControllerOptions = typeof options === 'boolean' ? { turnToYForward: options } : options;
    this.car = opts.car ?? null;
    this._bodyStyle = opts.bodyStyle ?? 0;
    this._detail = opts.detail ?? 2;
    const turn = !!opts.turnToYForward;
    this.spinSign = turn ? -1 : 1;
    // CRP (x left, y up, z backward) -> the model: y and z swapped, turned about z
    const swap = new Matrix4().set(1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1);
    this.toModel.copy(turn ? new Matrix4().makeRotationZ(Math.PI).multiply(swap) : swap);
    this.fromModel.copy(this.toModel).invert();
    const meshes: Mesh[] = [];
    root.traverse(o => {
      if (o instanceof Mesh && o !== root) {
        meshes.push(o);
      }
    });
    if (turn) {
      for (const mesh of meshes) {
        this.turnGeometry(mesh);
        mesh.position.applyAxisAngle(new Vector3(0, 0, 1), Math.PI);
      }
    }
    this.wheelRadius = WHEEL_RADIUS;
    if (!this.car) {
      this.setupGuessedWheels(meshes);
      return;
    }
    const byName = new Map(meshes.map(m => [m.name, m]));
    for (const mesh of meshes) {
      const info = Nfs5CarMeshController.parseMeshName(mesh.name);
      if (!info) {
        continue;
      }
      const article = info.articleIndex !== null ? (this.car.articles[info.articleIndex] ?? null) : null;
      mesh.updateMatrix();
      const transform = this.articleTransform(article, info.lod);
      const entry: MeshEntry = {
        mesh,
        info,
        article,
        base: mesh.matrix.clone(),
        transform,
        inverse: transform.clone().invert(),
      };
      this.entries.push(entry);
    }
    this.wheelRadius = this.measureWheelRadius() ?? WHEEL_RADIUS;
    for (const entry of this.entries) {
      if (!entry.article || entry.info.isDamaged || entry.info.animationFrame !== 0) {
        continue;
      }
      if ((entry.article.animation ?? 0) > 0) {
        this.setupAnimated(entry, byName);
      } else if ((entry.article.drawFlags ?? 0) & NFS5_DRAW_DAMAGE) {
        this.setupDamage(entry, byName, opts.damageZones ?? null);
      }
    }
    // R3DCarLOD_Build 0x43c1b0: an animation's last frame is the most frames of its articles
    for (const a of this.car.articles) {
      if (a.animation && a.animation < NFS5_ANIMATION_COUNT) {
        this.animations[a.animation].max = Math.max(this.animations[a.animation].max, a.frames ?? 0);
      }
    }
    this.setupGlares(root);
    this.setupDrawOrder();
    this.setupPaint();
    this.applySlots();
    // the driver sits straight, the arms on a straight steering wheel
    this.updateAnimations();
    this.update();
  }

  // ---- mesh names

  static parseMeshName(name: string): Nfs5MeshNameInfo | null {
    const match = NFS5_MESH_NAME_REGEX.exec(name);
    if (!match) {
      return null;
    }
    return {
      // article names can have trailing spaces ("Light2 "), which become underscores in three.js
      article: match[1].replace(/[\s_]+$/, ''),
      articleIndex: match[2] !== undefined ? +match[2] : null,
      lod: +match[3],
      animationFrame: +match[4],
      isDamaged: !!match[6],
    };
  }

  /**
   * Without the model data: a filter of meshes, which form a plausible default exterior of the car: the most
   * detailed LOD, the first animation frame, not damaged, without driver and cabrio roof, without alternative
   * variants of parts (an article, named as another article plus a number or a letter, e.g. "Body1", "Light2a", is a
   * variant of it), spoiler down. With the model data use the controller (`isShown`)
   */
  static defaultExteriorFilter(meshNames: string[]): (name: string) => boolean {
    const infos = meshNames.map(x => Nfs5CarMeshController.parseMeshName(x)).filter(x => !!x) as Nfs5MeshNameInfo[];
    const minLod = Math.min(...infos.map(x => x.lod));
    const isDefaultArticle = Nfs5CarMeshController.defaultArticleFilter(infos.map(x => x.article));
    return (name: string) => {
      const info = Nfs5CarMeshController.parseMeshName(name);
      return (
        !!info && info.lod === minLod && info.animationFrame === 0 && !info.isDamaged && isDefaultArticle(info.article)
      );
    };
  }

  /** Like `defaultExteriorFilter`, but only by article names: for any LOD, animation frame and damage */
  static defaultArticleFilter(allArticles: string[]): (article: string) => boolean {
    const articles = new Set(allArticles.map(x => x.toLowerCase()));
    const hasSpoilerDown = [...articles].some(x => x === 'spoiler' || x.startsWith('spoilerdown'));
    const isVariant = (article: string) =>
      [/^(.*\D)\d+$/, /^(.*\d)[a-z]$/].some(regex => {
        const base = regex.exec(article)?.[1];
        return !!base && articles.has(base.toLowerCase());
      });
    return (article: string) =>
      !NFS5_HIDDEN_ARTICLES_REGEX.test(article) &&
      !/^SpoilerUp/i.test(article) &&
      !(hasSpoilerDown && /^SpoilerW/i.test(article)) &&
      !isVariant(article);
  }

  /**
   * Whether a mesh is drawn now (with the model data): its article's slot value, its level for the view and the
   * draw flags, the first frame, not a damaged copy
   */
  isShown(mesh: Object3D): boolean {
    const entry = this.entries.find(e => e.mesh === mesh);
    return !!entry && this.entryShown(entry);
  }

  /** Whether the model data came with the model: every state below works, else only the wheels */
  get hasModelData(): boolean {
    return !!this.car;
  }

  get hasWheels(): boolean {
    return this.car ? this.entries.some(e => (e.article?.drawFlags ?? 0) & NFS5_DRAW_WHEELS) : this.wheels.length > 0;
  }

  // ---- the geometry configuration

  private _bodyStyle = 0;
  /** The body style, 0-based (`.tpg` `[style<n + 1>]`, nfs5.car `body_style`; R3DCar_SetBodyStyle 0x437b00) */
  get bodyStyle(): number {
    return this._bodyStyle;
  }

  set bodyStyle(value: number) {
    this._bodyStyle = value;
    this.applySlots();
  }

  /** The `.tpg` body styles' names */
  get styleNames(): string[] {
    return (this.car?.styles ?? []).map(s => s.name);
  }

  private _driver: number | null = 0;
  /**
   * The front end's driver 0..7 (record +0x150, FE_SendCarRecord 0x4eeda0: the AI's rand() % 8), null an empty car
   * (car flag 0x10): the driver's body, arms and legs, hands (slots 9, 43, 56; R3DCar_SetupGeometry 0x43ae50)
   */
  get driver(): number | null {
    return this._driver;
  }

  set driver(value: number | null) {
    this._driver = value;
    this.applySlots();
  }

  private _cabrioDown = false;
  /** The convertible top down (record +0x50c `_CABRIODOWN`: slot 41 = 2 x slot 37, up 2 x slot 37 - 1; 0x43ae50) */
  get cabrioDown(): boolean {
    return this._cabrioDown;
  }

  set cabrioDown(value: boolean) {
    this._cabrioDown = value;
    this.applySlots();
  }

  /** Whether a body style has a convertible top (its slot 37) */
  get hasCabrio(): boolean {
    return this.styleSlot(37) > 0;
  }

  private _raceNumber = false;
  /** A race number (record +0x510 >= 0): slot 10 shows the race number decals (0x437b00) */
  get raceNumber(): boolean {
    return this._raceNumber;
  }

  set raceNumber(value: boolean) {
    this._raceNumber = value;
    this.applySlots();
  }

  private _tinyCar = false;
  /** The tiny car cheat (record +0x518): slot 58 shows the antenna (0x43ae50) */
  get tinyCar(): boolean {
    return this._tinyCar;
  }

  set tinyCar(value: boolean) {
    this._tinyCar = value;
    this.applySlots();
  }

  /** The parts' geometry choices (the record's GEOMCONFIG +0x32c, nfs5.prt geometry switches): slot -> value, -1 none */
  setGeometryConfig(config: number[]) {
    for (let i = 0; i < 120; i++) {
      this.geometryConfig[i] = config[i] ?? -1;
    }
    this.applySlots();
  }

  getGeometryConfig(): number[] {
    return [...this.geometryConfig];
  }

  /** The value of a slot of the geometry configuration as the race has it (car+0x56c) */
  slot(index: number): number {
    return this.slotValues[index] ?? 0;
  }

  /** The slots with articles, the values the model has for each */
  get slotChoices(): { slot: number; values: number[]; articles: string[] }[] {
    const bySlot = new Map<number, { values: Set<number>; articles: Set<string> }>();
    for (const a of this.car?.articles ?? []) {
      if (a.slot === undefined || !a.lods.length) {
        continue;
      }
      const s = bySlot.get(a.slot) ?? { values: new Set<number>(), articles: new Set<string>() };
      s.values.add(a.value ?? 0);
      s.articles.add(a.name.trim());
      bySlot.set(a.slot, s);
    }
    return [...bySlot.entries()]
      .sort(([a], [b]) => a - b)
      .map(([slot, s]) => ({ slot, values: [...s.values].sort((a, b) => a - b), articles: [...s.articles] }));
  }

  private styleSlot(slot: number): number {
    const style = this.car?.styles[this._bodyStyle];
    return style?.slots.find(([s]) => s === slot)?.[1] ?? 0;
  }

  private applySlots() {
    if (!this.car) {
      return;
    }
    const slots = nfs5RaceSlots(this.car.styles[this._bodyStyle]?.slots ?? null, {
      driver: this._driver,
      cabrioDown: this._cabrioDown,
      raceNumber: this._raceNumber,
      tinyCar: this._tinyCar,
      geometryConfig: this.geometryConfig,
    });
    for (let i = 0; i < 120; i++) {
      this.slotValues[i] = slots[i];
    }
    this.applyPaint();
    this.update();
  }

  // ---- view and level of detail

  private _view: Nfs5View = 'outside';
  /**
   * The view (R3DCar_Draw 0x444e00): "outside" draws the driver (level 1, 2 at level 3), the body and steering
   * wheel at `lod`, the wheels at the detail's level; "cockpit" (the player's in-car camera, 0x627f43 bit 3) the
   * in-car articles of level 2 (`cockpit` set), the steering wheel of level 1, the driver's in-car articles (the
   * hands) at detail 1 and 2, no wheels
   */
  get view(): Nfs5View {
    return this._view;
  }

  set view(value: Nfs5View) {
    this._view = value;
    this.applyDamage();
    this.update();
  }

  private _lod = 0;
  /** The level of detail by distance (R3DCar+0x2c0), 0 the most detailed (the CRP's level 1) .. 6 */
  get lod(): number {
    return this._lod;
  }

  set lod(value: number) {
    this._lod = Math.max(0, Math.min(6, Math.round(value)));
    this.update();
  }

  private _detail = 2;
  /** The game's car detail (0x6197c4 from option 0x657d68: 0 low, 1 medium, 2 high): wheels' level, damage, driver */
  get detail(): number {
    return this._detail;
  }

  set detail(value: number) {
    this._detail = Math.max(0, Math.min(2, Math.round(value)));
    this.updateAnimations();
    this.applyDamage();
    this.update();
  }

  /** The CRP levels (1..7) the draw passes take for an article (R3DCar_Draw 0x444e00, R3DCarLOD_Draw 0x43c830) */
  private articleLevels(article: Nfs5CarArticle): number[] {
    const flags = article.drawFlags ?? 0;
    const levels: number[] = [];
    if (this._view === 'cockpit') {
      if (!article.cockpit) {
        return levels;
      }
      if (flags & NFS5_DRAW_BODY) {
        levels.push(2);
      }
      if (flags & NFS5_DRAW_STEERING_WHEEL) {
        levels.push(1);
      }
      if (flags & NFS5_DRAW_DRIVER && this._detail > 0) {
        levels.push(NFS5_COCKPIT_DRIVER_LOD[this._detail] + 1);
      }
      return levels;
    }
    if (article.insideOnly) {
      return levels;
    }
    if (flags & NFS5_DRAW_DRIVER && this._lod < NFS5_OUTSIDE_DRIVER_LOD.length) {
      levels.push(NFS5_OUTSIDE_DRIVER_LOD[this._lod] + 1);
    }
    if (flags & (NFS5_DRAW_BODY | NFS5_DRAW_STEERING_WHEEL)) {
      levels.push(this._lod + 1);
    }
    if (flags & NFS5_DRAW_WHEELS) {
      levels.push(NFS5_WHEEL_LODS[this._detail][this._lod] + 1);
    }
    return levels;
  }

  private entryShown(entry: MeshEntry): boolean {
    const a = entry.article;
    if (!a || entry.info.isDamaged || entry.info.animationFrame !== 0 || a.slot === undefined) {
      return false;
    }
    return this.slotValues[a.slot] === (a.value ?? 0) && this.articleLevels(a).includes(entry.info.lod);
  }

  // ---- wheels, steering, needles

  private _speed = 0;
  private spin = 0;
  private animationTimer: any = null;
  /**
   * Car speed in m/s, the wheels spin at it (the game turns wheel+0x88 by the physics; pivots 1..4 x = -rotation).
   * It can be set every frame: the timer restarts only when the wheels start or stop; negative spins backwards
   */
  get speed(): number {
    return this._speed;
  }

  set speed(value: number) {
    const wasSpinning = this._speed !== 0;
    this._speed = value;
    if (wasSpinning === (value !== 0)) {
      return;
    }
    if (this.animationTimer) {
      clearInterval(this.animationTimer);
      this.animationTimer = null;
    }
    if (value !== 0) {
      this.animationTimer = setInterval(() => {
        this.spin += this._speed / this.wheelRadius / 60;
        this.updateWheels();
      }, 1000 / 60);
    }
  }

  private _steeringAngle = 0;
  /**
   * The front wheels' angle in radians, positive to the left (pivots 1, 2 y = wheel+0xb4 / 216 turns). The steering
   * wheel (pivot 5) turns by the sum of both, at most NFS5_STEERING_WHEEL_LIMIT, and the driver's arms follow it
   * (R3DCar_UpdatePivots 0x438440)
   */
  get steeringAngle(): number {
    return this._steeringAngle;
  }

  set steeringAngle(value: number) {
    this._steeringAngle = value;
    this.updateWheels();
  }

  private readonly camber = [0, 0, 0, 0];
  /**
   * A wheel's tilt about the car's length in turns, as the game has it (pivots 1..4 z = wheel+0x70, +-asin of the
   * suspension's compression / 10), wheels 0 front left, 1 front right, 2 rear left, 3 rear right
   */
  setWheelCamber(wheel: number, turns: number) {
    this.camber[wheel] = turns;
    this.updateWheels();
  }

  /**
   * The needles in turns about their axes (pivot 0xb the rev counter: record+0x528 x rpm x 0.001 + record+0x524;
   * 0xc the speedometer: record+0x530 x speed (m/s) x 0.144 + record+0x52c: nfs5.car `_TACH0RPM`..`_SPEEDO100KM`;
   * `nfs5NeedleTurns`)
   */
  setNeedles(tachometer: number, speedometer: number) {
    this.pivots[0xb][2] = tachometer;
    this.pivots[0xc][2] = speedometer;
    this.update();
  }

  private updateWheels() {
    if (!this.car) {
      for (const { meshes, isFront } of this.wheels) {
        for (const m of meshes) {
          m.rotation.set(this.spinSign * this.spin, 0, isFront ? this._steeringAngle : 0);
        }
      }
      return;
    }
    // positive to the left is clockwise about the CRP's up axis (the CRP is mirrored against the model)
    const steer = -this._steeringAngle / TURN;
    for (let w = 0; w < 4; w++) {
      const p = this.pivots[1 + w];
      p[0] = -this.spin / TURN;
      p[1] = w < 2 ? steer : 0;
      p[2] = this.camber[w];
      // 0x12..0x15: the same without the rotation (wheel shadows, treads)
      this.pivots[0x12 + w] = [0, p[1], p[2]];
    }
    this.pivots[5][2] = Math.max(
      -NFS5_STEERING_WHEEL_LIMIT,
      Math.min(NFS5_STEERING_WHEEL_LIMIT, this.pivots[1][1] + this.pivots[2][1]),
    );
    this.updateArms();
    this.update();
  }

  // ---- lids, doors, spoiler

  private _hoodOpen = 0;
  /** The hood open 0..1 (pivot 8 x = `hoodextent` turns x this; the front end opens it over a timed ramp) */
  get hoodOpen(): number {
    return this._hoodOpen;
  }

  set hoodOpen(value: number) {
    this._hoodOpen = value;
    this.pivots[8][0] = (this.car?.header.hoodExtent ?? 0) * value;
    this.update();
  }

  private _trunkOpen = 0;
  /** The trunk open 0..1 (pivot 9 x = `trunkextent` turns x this) */
  get trunkOpen(): number {
    return this._trunkOpen;
  }

  set trunkOpen(value: number) {
    this._trunkOpen = value;
    this.pivots[9][0] = (this.car?.header.trunkExtent ?? 0) * value;
    this.update();
  }

  /** A door's angle in turns about the `.tpg` `dooraxis` (pivots 6 left, 7 right: the axis x negated; front end) */
  setDoorOpen(side: 'left' | 'right', turns: number) {
    this.pivots[side === 'left' ? 6 : 7][1] = turns;
    this.update();
  }

  private _moveSpoiler = 0;
  /**
   * The moving spoiler raised 0..1 (pivot 0x10 x = `movespoilerextent` turns x this): the front end raises it while
   * the convertible top moves (0x438440); the race leaves it down
   */
  get moveSpoiler(): number {
    return this._moveSpoiler;
  }

  set moveSpoiler(value: number) {
    this._moveSpoiler = value;
    this.pivots[0x10][0] = (this.car?.header.moveSpoilerExtent ?? 0) * value;
    this.update();
  }

  private _wing = 0;
  /**
   * The speed wing 0..1 (animation 2, `SpoilerW*`: frames 0..last): the race raises it above 22.22 m/s (80 km/h),
   * lowers it below 13.89 m/s (50 km/h), each over 2000 ms (0x438440)
   */
  get wing(): number {
    return this._wing;
  }

  set wing(value: number) {
    this._wing = value;
    this.setAnimation(2, value * this.animations[2].max);
  }

  // ---- animations

  /** The frame of an animation (R3DCar_SetAnimationFrame 0x4380d0: clamped to 0..its frame count, blended frames) */
  setAnimation(animation: number, frame: number) {
    const a = this.animations[animation];
    if (!a) {
      return;
    }
    const f = Math.max(0, Math.min(a.max, frame));
    a.frame = Math.floor(f);
    a.next = a.frame + 1;
    a.fraction = f - a.frame;
    this.applyAnimation(animation);
  }

  /** An animation's frames as R3DCar+0x568 holds them: `frame` blended towards `next` by `fraction` */
  setAnimationBlend(animation: number, frame: number, next: number, fraction: number) {
    const a = this.animations[animation];
    if (!a) {
      return;
    }
    a.frame = frame;
    a.next = next;
    a.fraction = fraction;
    this.applyAnimation(animation);
  }

  /** The frame count of an animation (its articles' most frames), 0 without articles */
  animationFrames(animation: number): number {
    return this.animations[animation]?.max ?? 0;
  }

  private _horn = false;
  /** The horn held (car+0xd86): the right arm's frame 19 (0x438440) */
  get horn(): boolean {
    return this._horn;
  }

  set horn(value: boolean) {
    this._horn = value;
    this.updateArms();
  }

  private _cabrioFrame = 0;
  /**
   * The front end's convertible top (animation 1, `Cabrio`, slot 37; the race shows `CabrioUp` / `CabrioDown`
   * instead): 0 up .. 1 down
   */
  get cabrioAnimation(): number {
    return this._cabrioFrame;
  }

  set cabrioAnimation(value: number) {
    this._cabrioFrame = value;
    this.setAnimation(1, value * this.animations[1].max);
  }

  private driverMotion = { lateral: 0, longitudinal: 0, reverse: false };
  /**
   * The driver's body (animation 6) by the car's smoothed accelerations in m/s/s (0x438440): lateral car+0xe08 (|a| <
   * 0.1 counts 0): frame 2 - 0.1 x a; braking (longitudinal car+0xe04 < -0.1): that frame blended towards frame 5 by
   * -0.1 x a; reversing (gear 0): frame 7. SKIPPED: the sequences played when reverse is put in or out (0x5cd568)
   */
  setDriverMotion(lateral: number, longitudinal: number, reverse = false) {
    this.driverMotion = { lateral, longitudinal, reverse };
    this.updateDriverBody();
  }

  private updateDriverBody() {
    if (this._detail < 1) {
      this.setAnimation(6, 5);
      return;
    }
    const { lateral, longitudinal, reverse } = this.driverMotion;
    if (reverse) {
      this.setAnimation(6, 7);
      return;
    }
    const lean = 0.1 * -(Math.abs(lateral) < 0.1 ? 0 : lateral) + 2;
    if (Math.abs(longitudinal) < 0.1 || longitudinal >= 0) {
      this.setAnimation(6, lean);
    } else {
      this.setAnimationBlend(6, Math.floor(Math.max(0, lean)), 5, -0.1 * longitudinal);
    }
  }

  /**
   * The arms (animations 5 left, 4 right): frame 23 x the steering wheel's turn + 4.5; the right arm frame 19 while
   * the horn is held. SKIPPED: the gear change sequences of the right arm (while car+0xd84 > 0, 0x5cd3ac)
   */
  private updateArms() {
    if (!this.car) {
      return;
    }
    if (this._detail < 1) {
      this.setAnimation(4, 4.5);
      this.setAnimation(5, 4.5);
      return;
    }
    const frame = 23 * this.pivots[5][2] + 4.5;
    this.setAnimation(5, frame);
    this.setAnimation(4, this._horn ? 19 : frame);
  }

  private updateAnimations() {
    this.updateArms();
    this.updateDriverBody();
  }

  // ---- lights

  private lightInput = {
    headlights: false,
    brake: false,
    reverse: false,
    left: false,
    right: false,
    hazard: false,
    blink: false,
    popUp: 0,
  };

  /**
   * The lights' inputs (R3DCar_UpdateLights 0x439360): headlights (car+0xd87 bit 0), braking (car+0xd80), reverse
   * gear, the indicators (car+0xd87 bits 3 left, 4 right; both when out of the race, car+0xb50 3) and their blink
   * phase (the game's tick / half the blink period, 0x5deb48), the pop-up headlights raised 0..1 (pivot 0x11 x =
   * `headlightextent` x this: the game moves them over 1000 ms; their glares as bright as raised). Damage above 30
   * breaks the lights of its zone. `nfs5Lights` has the rule
   */
  setLights(input: Partial<Nfs5CarMeshController['lightInput']>) {
    this.lightInput = { ...this.lightInput, ...input };
    this.pivots[0x11][0] = (this.car?.header.headlightExtent ?? 0) * this.lightInput.popUp;
    this.updateLights();
  }

  /** Light flags and intensities (R3DCar+0x2d4, +0x2d8), 14 lights: `nfs5Lights` */
  get lightState(): Nfs5Lights {
    return this.lights;
  }

  private _showGlares = true;
  /** The light glares drawn (flat additive quads: the game's sprite grows and fades by the view angle, 0x43cdd0) */
  get showGlares(): boolean {
    return this._showGlares;
  }

  set showGlares(value: boolean) {
    this._showGlares = value;
    this.updateGlares();
  }

  get hasGlares(): boolean {
    return this.glares.length > 0;
  }

  get hasPopUpHeadlights(): boolean {
    return (this.car?.header.headlightExtent ?? 0) !== 0;
  }

  private updateLights() {
    const i = this.lightInput;
    this.lights = nfs5Lights(
      {
        headlights: i.headlights,
        brake: i.brake,
        reverse: i.reverse,
        left: i.left || i.hazard,
        right: i.right || i.hazard,
        blink: i.blink,
        popUp: this.hasPopUpHeadlights ? i.popUp : null,
      },
      this.zoneDamage,
    );
    this.update();
  }

  // ---- damage

  /** Damage of a zone 0..100 (car+0x4e4: `NFS5_ZONE_NAMES`) */
  getZoneDamage(zone: number): number {
    return this.zoneDamage[zone] ?? 0;
  }

  setZoneDamage(zone: number, damage: number) {
    this.zoneDamage[zone] = Math.max(0, Math.min(100, damage));
    this.applyDamage();
    this.updateLights();
  }

  /** The damage of every zone, to keep (setDamage restores it) */
  getDamage(): number[] {
    return [...this.zoneDamage];
  }

  setDamage(damage: number[]) {
    for (let z = 0; z < NFS5_ZONES; z++) {
      this.zoneDamage[z] = Math.max(0, Math.min(100, damage[z] ?? 0));
    }
    this.applyDamage();
    this.updateLights();
  }

  /** Undamaged again */
  repair() {
    this.setDamage([]);
  }

  /** Whether the model has dents (articles with damaged copies) */
  get hasDamage(): boolean {
    return this.damageMeshes.length > 0;
  }

  /**
   * A hit (Car_HitDamage 0x494df0, Car_Damage 0x494500): `normal` the push on the car in the model's axes, `speed`
   * the hit's speed (car+0x430, m/s; nothing at 10 or below). The zones it damages (`nfs5HitZones`) get speed x 0.5
   * (x 1.5 in a derby), at most 100, half of it spread into their ring neighbours. Returns the zones damaged.
   * SKIPPED: the game's damage option and the crash events (sounds), the app's
   */
  hit(normal: { x: number; y: number; z: number }, speed: number, derby = false): number[] {
    const n = new Vector3(normal.x, normal.y, normal.z).applyMatrix4(new Matrix4().extractRotation(this.fromModel));
    const zones = nfs5HitZones({ x: n.x, y: n.y, z: n.z }, speed);
    for (const zone of zones) {
      const after = nfs5ZoneDamageAfterHit(this.zoneDamage, zone, speed, derby);
      this.zoneDamage.splice(0, NFS5_ZONES, ...after);
    }
    if (zones.length) {
      this.applyDamage();
      this.updateLights();
    }
    return zones;
  }

  private applyDamage() {
    const cockpit = this._view === 'cockpit';
    const weights = this.zoneDamage.map((d, z) => {
      // R3DCar_DrawnDamage 0x4382e0: at most 100 x the zone's limit (the in-car view's 0x5b35d4); 0x43e390: x 0.02
      const limit = cockpit ? NFS5_COCKPIT_ZONE_LIMITS[z] : 1;
      return this._detail > 0 ? Math.min(1, Math.min(d, 100 * limit) * NFS5_DAMAGE_WEIGHT) : 0;
    });
    for (const d of this.damageMeshes) {
      const position = this.ownPositions(d.entry.mesh);
      const array = position.array as Float32Array;
      for (let v = 0; v < d.zones.length; v++) {
        const w = d.zones[v] < NFS5_ZONES ? weights[d.zones[v]] : 0;
        for (let c = 0; c < 3; c++) {
          array[v * 3 + c] = d.base[v * 3 + c] + d.offsets[v * 3 + c] * w;
        }
      }
      position.needsUpdate = true;
      d.entry.mesh.geometry.computeBoundingSphere();
    }
  }

  // ---- paint

  private colors: number[] = [0xffffff, 0xffffff, 0xffffff, 0x404040];
  private _stripePackage = 0;

  /**
   * The paint (R3DCar_SetStripePackage 0x443db0, the texels tinted by CarTex_BlitTinted 0x444130): `colors` the record's
   * `_COLORCONFIG` (0xRRGGBB: body, accent 1, accent 2, interior: nfs5.car paints), `stripePackage` 0-based
   * `packages.ini` package (record `_STRIPEPACKAGE`); the style's `stripe` takes band 6 from accent 1
   */
  setPaint(colors: number[], stripePackage = this._stripePackage) {
    this.colors = [...colors];
    this._stripePackage = stripePackage;
    this.applyPaint();
    this.paintEnabled = true;
  }

  get stripePackages(): number {
    return this.car?.packages.length ?? 0;
  }

  get paintEnabled(): boolean {
    return this.paintEnabledUniform.value > 0.5;
  }

  /**
   * Painting on (`setPaint` turns it on): the band coded texels of the pages tinted, as the game draws them; off: the
   * textures as exported (the bands' grey shades)
   */
  set paintEnabled(value: boolean) {
    this.paintEnabledUniform.value = value && this.materials.size ? 1 : 0;
  }

  get isPaintable(): boolean {
    return this.materials.size > 0;
  }

  private applyPaint() {
    if (!this.car) {
      return;
    }
    this.bands = nfs5Bands(
      this.colors,
      this.car.packages[this._stripePackage] ?? null,
      !!this.car.styles[this._bodyStyle]?.stripe,
    );
    this.bands.forEach((c, i) => this.bandUniforms.value[i].set((c >> 16) & 0xff, (c >> 8) & 0xff, c & 0xff));
  }

  /**
   * R3DCarLOD_Build 0x43c1b0 sorts a level's articles by their draw order (the tag's third byte, a signed one:
   * compared signed by the sort, 0x43e910; the inside's 129.. = -127.. come first, a trunk lid's 246 = -10 before the
   * body's 0) and the game draws them so: an overlay (a lamp's lens, a decal, the license plate, the gauges) lies on the triangles of an
   * article drawn before it (the body's lamp, the trunk, the dash) and covers them. three.js has no such rule for
   * surfaces at the same depth: each mesh is drawn in its article's order (`renderOrder`) and the later orders are
   * pulled towards the camera by their rank (polygon offset), on copies of the materials
   */
  private setupDrawOrder() {
    const orderOf = (entry: MeshEntry) => ((entry.article?.order ?? 0) << 24) >> 24;
    const ranks = new Map(
      [...new Set(this.entries.map(orderOf))].sort((a, b) => a - b).map((order, rank) => [order, rank] as const),
    );
    const copies = new Map<Material, Map<number, Material>>();
    const offsetCopy = (material: Material, rank: number): Material => {
      const byRank = copies.get(material) ?? copies.set(material, new Map()).get(material)!;
      let copy = byRank.get(rank);
      if (!copy) {
        copy = material.clone();
        copy.polygonOffset = true;
        copy.polygonOffsetFactor = -rank;
        copy.polygonOffsetUnits = -rank;
        byRank.set(rank, copy);
        this.ownMaterials.add(copy);
      }
      return copy;
    };
    for (const entry of this.entries) {
      const order = orderOf(entry);
      entry.mesh.renderOrder = order;
      const rank = ranks.get(order) ?? 0;
      if (rank > 0) {
        const mesh = entry.mesh;
        mesh.material = Array.isArray(mesh.material)
          ? mesh.material.map(m => offsetCopy(m, rank))
          : offsetCopy(mesh.material, rank);
      }
    }
  }

  private setupPaint() {
    const pages = new Map((this.car?.pages ?? []).map(p => [p.index, p]));
    for (const entry of this.entries) {
      for (const material of Array.isArray(entry.mesh.material) ? entry.mesh.material : [entry.mesh.material]) {
        const match = PAGE_MATERIAL_REGEX.exec(material.name);
        if (!match || this.materials.has(material) || !(material as MeshBasicMaterial).map) {
          continue;
        }
        const format = pages.get(+match[1])?.format ?? 1555;
        this.materials.set(material, format);
        paintInShader(material, format, this.bandUniforms, this.paintEnabledUniform);
      }
    }
    this.applyPaint();
  }

  // ---- setup

  private turnGeometry(mesh: Mesh) {
    const geometry = mesh.geometry;
    geometry.rotateZ(Math.PI);
    // three.js turns the positions and normals only
    for (const target of geometry.morphAttributes['position'] ?? []) {
      for (let i = 0; i < target.count; i++) {
        target.setXY(i, -target.getX(i), -target.getY(i));
      }
      target.needsUpdate = true;
    }
  }

  private articleTransform(article: Nfs5CarArticle | null, lod: number): Matrix4 {
    const values = article?.transforms[String(lod)] ?? Object.values(article?.transforms ?? {})[0];
    // the CRP's row vector matrix is column-major for three.js
    return values && values.length === 16 ? new Matrix4().fromArray(values) : new Matrix4();
  }

  private measureWheelRadius(): number | null {
    const entry = this.entries.find(
      e => e.info.lod === 1 && /^WheelFront/i.test(e.info.article) && !e.info.isDamaged && e.info.animationFrame === 0,
    );
    if (!entry) {
      return null;
    }
    entry.mesh.geometry.computeBoundingBox();
    const size = entry.mesh.geometry.boundingBox!.getSize(new Vector3());
    return size.z > 0 ? size.z / 2 : null;
  }

  private setupGuessedWheels(meshes: Mesh[]) {
    // wheel meshes by article name, LOD and side
    const wheels: { [key: string]: { meshes: Mesh[]; isFront: boolean } } = {};
    for (const o of meshes) {
      const info = Nfs5CarMeshController.parseMeshName(o.name);
      const match = info && NFS5_WHEEL_REGEX.exec(info.article);
      if (!info || !match) {
        continue;
      }
      o.geometry.computeBoundingBox();
      const center = o.geometry.boundingBox!.getCenter(new Vector3()).add(o.position);
      const key = `${info.article}_${info.lod}_${info.animationFrame}_${info.isDamaged}_${center.x > 0}`;
      (wheels[key] = wheels[key] || { meshes: [], isFront: match[1].toLowerCase() === 'front' }).meshes.push(o);
    }
    for (const wheel of Object.values(wheels)) {
      // move pivot to the wheel center, so it rotates in place
      const box = new Box3();
      for (const m of wheel.meshes) {
        box.union(m.geometry.boundingBox!.clone().translate(m.position));
      }
      const center = box.getCenter(new Vector3());
      for (const m of wheel.meshes) {
        m.geometry = this.ownGeometry(m.geometry);
        m.geometry.translate(m.position.x - center.x, m.position.y - center.y, m.position.z - center.z);
        m.position.copy(center);
        m.rotation.order = 'ZXY';
      }
      this.wheels.push(wheel);
    }
  }

  private setupAnimated(entry: MeshEntry, byName: Map<string, Mesh>) {
    const count = entry.article!.frames ?? 1;
    const dictionary = entry.mesh.morphTargetDictionary;
    if (dictionary && (count < 2 || dictionary['frame1'] !== undefined)) {
      const morphIndices = Array.from({ length: count }, (_, k) => (k > 0 ? dictionary[`frame${k}`] : undefined));
      this.animated.push({ entry, morphIndices, framePositions: [], count });
      return;
    }
    // OBJ: the frames' own meshes, the same vertices in the same order
    const vertices = entry.mesh.geometry.getAttribute('position').count;
    const framePositions = Array.from({ length: count }, (_, k) => {
      const geometry =
        k > 0 ? byName.get(entry.mesh.name.replace(/_ai0(?=_|$)/, `_ai${k}`))?.geometry : entry.mesh.geometry;
      const position = geometry?.getAttribute('position');
      return position && position.count === vertices
        ? Float32Array.from({ length: vertices * 3 }, (_, i) => position.getComponent(Math.floor(i / 3), i % 3))
        : undefined;
    });
    this.animated.push({ entry, morphIndices: null, framePositions, count });
  }

  private setupDamage(entry: MeshEntry, byName: Map<string, Mesh>, objZones: { [mesh: string]: number[] } | null) {
    const geometry = entry.mesh.geometry;
    const position = geometry.getAttribute('position');
    const count = position.count;
    const base = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      base.set([position.getX(i), position.getY(i), position.getZ(i)], i * 3);
    }
    const offsets = new Float32Array(count * 3);
    const morph = entry.mesh.morphTargetDictionary?.['damaged'];
    const target = morph === undefined ? null : geometry.morphAttributes['position']?.[morph];
    const copy = byName.get(`${entry.mesh.name}_damaged`)?.geometry.getAttribute('position');
    if (target && target.count === count) {
      for (let i = 0; i < count; i++) {
        const t = [target.getX(i), target.getY(i), target.getZ(i)];
        offsets.set(geometry.morphTargetsRelative ? t : t.map((x, c) => x - base[i * 3 + c]), i * 3);
      }
    } else if (copy && copy.count === count) {
      for (let i = 0; i < count; i++) {
        offsets.set(
          [copy.getX(i) - base[i * 3], copy.getY(i) - base[i * 3 + 1], copy.getZ(i) - base[i * 3 + 2]],
          i * 3,
        );
      }
    } else {
      return;
    }
    const zones = new Uint8Array(count).fill(255);
    const attribute = geometry.getAttribute('_nfs5_damage_zone');
    const corners = objZones?.[entry.mesh.name];
    if (attribute && attribute.count === count) {
      for (let i = 0; i < count; i++) {
        zones[i] = Math.round(attribute.getX(i) * (attribute.normalized ? 255 : 1));
      }
    } else if (corners && corners.length === count) {
      zones.set(corners);
    } else {
      return;
    }
    this.damageMeshes.push({ entry, base, offsets, zones });
  }

  private setupGlares(root: Object3D) {
    if (!this.car) {
      return;
    }
    for (const article of this.car.articles) {
      for (const glare of article.glares ?? []) {
        this.addGlare(root, article, glare, article.light ?? 0, false);
        if (glare.mirrored) {
          this.addGlare(root, article, glare, glare.mirrorLight, true);
        }
      }
    }
  }

  /** A glare's quad: position + (+-1) x width + (+-1) x height in the article's axes (0x43cdd0's corners) */
  private addGlare(root: Object3D, article: Nfs5CarArticle, glare: Nfs5CarGlare, light: number, mirrored: boolean) {
    const sign = mirrored ? -1 : 1;
    const p = new Vector3(sign * glare.position[0], glare.position[1], glare.position[2]);
    const w = new Vector3(sign * glare.width[0], glare.width[1], glare.width[2]);
    const h = new Vector3(sign * glare.height[0], glare.height[1], glare.height[2]);
    const transform = this.articleTransform(article, 1);
    const corners = [
      [-1, -1],
      [1, -1],
      [1, 1],
      [-1, 1],
    ].map(([u, v]) =>
      p.clone().addScaledVector(w, u).addScaledVector(h, v).applyMatrix4(transform).applyMatrix4(this.toModel),
    );
    const geometry = new BufferGeometry();
    geometry.setAttribute('position', new BufferAttribute(new Float32Array(corners.flatMap(c => [c.x, c.y, c.z])), 3));
    geometry.setAttribute('uv', new BufferAttribute(new Float32Array([0, 0, 1, 0, 1, 1, 0, 1]), 2));
    geometry.setIndex([0, 1, 2, 0, 2, 3]);
    this.ownGeometries.add(geometry);
    const color = glare.sourceColor & 0xffffff;
    const material = new MeshBasicMaterial({
      color,
      map: this.getGlareTexture(),
      transparent: true,
      blending: AdditiveBlending,
      depthWrite: false,
      side: DoubleSide,
    });
    this.ownMaterials.add(material);
    const mesh = new Mesh(geometry, material);
    mesh.name = `${article.name.trim()}_a${article.index}__glare${mirrored ? '_mirrored' : ''}`;
    mesh.visible = false;
    mesh.matrixAutoUpdate = false;
    root.add(mesh);
    this.glares.push({ mesh, article, light, base: new Matrix4(), transform, inverse: transform.clone().invert() });
  }

  /** A round falloff (computed, no canvas) */
  private getGlareTexture(): DataTexture {
    if (!this.glareTexture) {
      const size = 32;
      const data = new Uint8Array(size * size * 4);
      for (let y = 0; y < size; y++) {
        for (let x = 0; x < size; x++) {
          const d = Math.hypot((x + 0.5) / size - 0.5, (y + 0.5) / size - 0.5) * 2;
          const a = Math.max(0, 1 - d) ** 2;
          data.set([255, 255, 255, Math.round(a * 255)], (y * size + x) * 4);
        }
      }
      this.glareTexture = new DataTexture(data, size, size, RGBAFormat);
      this.glareTexture.magFilter = LinearFilter;
      this.glareTexture.minFilter = LinearFilter;
      this.glareTexture.needsUpdate = true;
    }
    return this.glareTexture;
  }

  private ownGeometry(geometry: BufferGeometry): BufferGeometry {
    if (this.ownGeometries.has(geometry)) {
      return geometry;
    }
    const own = geometry.clone();
    this.ownGeometries.add(own);
    return own;
  }

  /** The mesh's position attribute, on a geometry of its own (the app may share geometries between cars) */
  private ownPositions(mesh: Mesh): BufferAttribute {
    mesh.geometry = this.ownGeometry(mesh.geometry);
    return mesh.geometry.getAttribute('position') as BufferAttribute;
  }

  // ---- drawing

  private applyAnimation(animation: number) {
    const a = this.animations[animation];
    for (const m of this.animated) {
      if (m.entry.article?.animation !== animation) {
        continue;
      }
      // R3DCarLOD_Animate 0x43e120: frame a blended towards b; a missing frame b: frame a; a missing: unchanged
      if (a.frame < 0 || a.frame >= m.count) {
        continue;
      }
      const b = a.next >= 0 && a.next < m.count ? a.next : -1;
      const t = b >= 0 ? a.fraction : 0;
      const mesh = m.entry.mesh;
      if (m.morphIndices) {
        const influences = mesh.morphTargetInfluences;
        if (!influences) {
          continue;
        }
        influences.fill(0);
        const add = (k: number, w: number) => {
          const index = m.morphIndices![k];
          if (index !== undefined) {
            influences[index] += w;
          }
        };
        add(a.frame, 1 - t);
        if (b >= 0) {
          add(b, t);
        }
        continue;
      }
      const from = m.framePositions[a.frame];
      const to = b >= 0 ? m.framePositions[b] : undefined;
      if (!from) {
        continue;
      }
      const position = this.ownPositions(mesh);
      const array = position.array as Float32Array;
      for (let i = 0; i < from.length; i++) {
        array[i] = to ? from[i] + (to[i] - from[i]) * t : from[i];
      }
      position.needsUpdate = true;
      mesh.geometry.computeBoundingSphere();
    }
  }

  private readonly pivotMatrix = new Matrix4();
  private readonly tmp = new Matrix4();

  /** The pivot's turn in the CRP's axes (R3DCarLOD_Draw 0x43c830: RotX, RotY, RotZ in the article's axes) */
  private pivotRotation(pivot: number, out: Matrix4): Matrix4 {
    const p = this.pivots[pivot] ?? [0, 0, 0];
    if (pivot === 6 || pivot === 7) {
      const axis = this.car?.header.doorAxis ?? [0, 1, 0];
      const v = new Vector3(pivot === 7 ? -axis[0] : axis[0], axis[1], axis[2]);
      return v.lengthSq() > 0 ? out.makeRotationAxis(v.normalize(), p[1] * TURN) : out.identity();
    }
    // row vectors v Rx Ry Rz: column vectors Rz Ry Rx v
    out.makeRotationZ(p[2] * TURN);
    out.multiply(this.tmp.makeRotationY(p[1] * TURN));
    return out.multiply(this.tmp.makeRotationX(p[0] * TURN));
  }

  /** The model matrix that turns an article's mesh about its origin: model <- CRP <- M R M^-1 <- CRP <- model */
  private placed(pivot: number, transform: Matrix4, inverse: Matrix4, base: Matrix4, out: Matrix4): Matrix4 {
    if (!pivot) {
      return out.copy(base);
    }
    this.pivotRotation(pivot, this.pivotMatrix);
    return out
      .copy(this.toModel)
      .multiply(transform)
      .multiply(this.pivotMatrix)
      .multiply(inverse)
      .multiply(this.fromModel)
      .multiply(base);
  }

  private update() {
    if (this.disposed || !this.car) {
      return;
    }
    for (const entry of this.entries) {
      const shown = this.entryShown(entry);
      entry.mesh.visible = shown;
      const pivot = entry.article?.pivot ?? 0;
      if (shown || pivot) {
        entry.mesh.matrixAutoUpdate = false;
        this.placed(pivot, entry.transform, entry.inverse, entry.base, entry.mesh.matrix);
        entry.mesh.matrixWorldNeedsUpdate = true;
      }
    }
    this.updateGlares();
  }

  private updateGlares() {
    if (this.disposed) {
      return;
    }
    for (const g of this.glares) {
      // R3DCarLOD_DrawGlares 0x43d800: its light on; the glare articles have level 1 only (their level record), the
      // pass drawing them is not traced: shown outside at lod 0
      const inLevel = this._view === 'outside' && this._lod === 0;
      const on = this._showGlares && inLevel && !!this.lights.on[g.light];
      g.mesh.visible = on;
      if (on) {
        (g.mesh.material as MeshBasicMaterial).opacity = this.lights.intensity[g.light] ?? 1;
        this.placed(g.article.pivot ?? 0, g.transform, g.inverse, g.base, g.mesh.matrix);
        g.mesh.matrixWorldNeedsUpdate = true;
      }
    }
  }

  dispose() {
    this.disposed = true;
    if (this.animationTimer) {
      clearInterval(this.animationTimer);
      this.animationTimer = null;
    }
    for (const g of this.glares) {
      g.mesh.removeFromParent();
    }
    for (const geometry of this.ownGeometries) {
      geometry.dispose();
    }
    for (const material of this.ownMaterials) {
      material.dispose();
    }
    this.glareTexture?.dispose();
  }
}

/**
 * The material tints the band coded texels of its page in the fragment shader (reading a canvas back gets noise from
 * anti-fingerprinting), as CarTex_BlitTinted 0x444130 tints them into the page: k = (A + 1) x 20 >> 8 of the texel's
 * alpha A; k 0, 10, 20 untinted (the alpha kept: 1555 pages A != 0, 4444 A >> 4), else band 18 - k (k < 10) or 19 - k,
 * colour band x the texel's red >> 8, opaque. 4444 pages are copied untinted (0x444130 tints 32-bit images into 32 and
 * 1555 pages only). Each texel is tinted before filtering: a linearly filtered map is sampled texel by texel (base
 * level), as the game's page holds the tinted texels
 */
function paintInShader(material: Material, format: number, bands: { value: Vector3[] }, enabled: { value: number }) {
  const previous = material.onBeforeCompile;
  const previousKey = material.customProgramCacheKey;
  material.onBeforeCompile = (shader, renderer) => {
    previous.call(material, shader, renderer);
    shader.uniforms['nfs5Bands'] = bands;
    shader.uniforms['nfs5PaintEnabled'] = enabled;
    shader.uniforms['nfs5PaintFiltered'] = {
      get value() {
        const map = (material as MeshBasicMaterial).map;
        return map && map.magFilter !== NearestFilter ? 1 : 0;
      },
    };
    shader.fragmentShader = shader.fragmentShader
      .replace(
        '#include <map_pars_fragment>',
        `#include <map_pars_fragment>
        uniform vec3 nfs5Bands[ 18 ];
        uniform float nfs5PaintEnabled;
        uniform float nfs5PaintFiltered;
        vec4 nfs5Paint( vec4 sampled ) {
          float a = floor( sampled.a * 255.0 + 0.5 );
          float k = floor( ( a + 1.0 ) * 20.0 / 256.0 );
          if ( ${format === 4444 ? 'true' : 'false'} || k == 0.0 || k == 10.0 || k == 20.0 ) {
            ${
              format === 1555
                ? 'return vec4( sampled.rgb, a > 0.0 ? 1.0 : 0.0 );'
                : format === 4444
                  ? 'return vec4( sampled.rgb, floor( a / 16.0 ) / 15.0 );'
                  : 'return sampled;'
            }
          }
          int band = int( k < 10.0 ? 18.0 - k : 19.0 - k );
          float red = floor( sRGBTransferOETF( sampled ).r * 255.0 + 0.5 );
          vec3 painted = floor( nfs5Bands[ band ] * red / 256.0 );
          return vec4( sRGBTransferEOTF( vec4( painted / 255.0, 1.0 ) ).rgb, 1.0 );
        }`,
      )
      .replace(
        '#include <map_fragment>',
        `#include <map_fragment>
        #ifdef USE_MAP
        if ( nfs5PaintEnabled > 0.5 ) {
          vec4 painted;
          if ( nfs5PaintFiltered > 0.5 ) {
            ivec2 size = textureSize( map, 0 );
            vec2 p = vMapUv * vec2( size ) - 0.5;
            ivec2 i0 = ivec2( floor( p ) );
            vec2 f = p - floor( p );
            ivec2 last = size - 1;
            vec4 t00 = nfs5Paint( texelFetch( map, clamp( i0, ivec2( 0 ), last ), 0 ) );
            vec4 t10 = nfs5Paint( texelFetch( map, clamp( i0 + ivec2( 1, 0 ), ivec2( 0 ), last ), 0 ) );
            vec4 t01 = nfs5Paint( texelFetch( map, clamp( i0 + ivec2( 0, 1 ), ivec2( 0 ), last ), 0 ) );
            vec4 t11 = nfs5Paint( texelFetch( map, clamp( i0 + ivec2( 1, 1 ), ivec2( 0 ), last ), 0 ) );
            painted = mix( mix( t00, t10, f.x ), mix( t01, t11, f.x ), f.y );
          } else {
            painted = nfs5Paint( sampledDiffuseColor );
          }
          diffuseColor = vec4( diffuse, opacity ) * painted;
        }
        #endif`,
      );
  };
  material.customProgramCacheKey = () => `${previousKey.call(material)}|nfs5-paint-${format}`;
  material.needsUpdate = true;
}
