import {
  Entity3d,
  GgDummy,
  TypeDocOf,
  LoadResultWithProps,
  MapGraph,
  MapGraph3dEntity,
  MapGraphNodeType,
  Qtrn,
} from '@gg-web-engine/core';
import { BehaviorSubject, distinctUntilChanged, Subject, takeUntil } from 'rxjs';
import {
  DoubleSide,
  Euler,
  Material,
  Mesh,
  MeshBasicMaterial,
  Object3D,
  Quaternion,
  RepeatWrapping,
  SphereGeometry,
  Texture,
  TextureLoader,
} from 'three';
import { ThreeDisplayObjectComponent, ThreeGgWorld } from '@gg-web-engine/three';
import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader.js';
import { MTLLoader } from 'three/examples/jsm/loaders/MTLLoader.js';
import { setupNfs1Texture } from '../../../../../nfs-three-lib/nfs1-model-utils';
import { TrackMapAdapter } from './track-map-adapters';
import { meshTextureName, TrackProp, TrackPropsAssets, TrackPropsController } from './track-props-controller';

export type TrackEntity = Entity3d<TypeDocOf<ThreeGgWorld>>;

// Files of a terrain chunk: "<name>.obj" and its "_extra.json" (props), null when it has none. `version` changes
// when the files are written again (a part of the URL, so that the browser does not serve the old ones)
export interface TrackChunkFiles {
  obj: string;
  extra: string | null;
  version: string;
}

// A loaded chunk, made before it is added to the map (a reload makes the new one before the old one goes)
interface BuiltChunk {
  entities: TrackEntity[];
  terrain: Object3D;
  lodMeshes: Mesh[];
  props: TrackProp[];
  version: string;
}

// Level of detail of a terrain mesh exported with `maps__save_all_lods`: "block_3_lod1__TEX" (NFS2-NFS4),
// "terrain_chunk_2_5_lod1_TEX" (NFS5); null for a mesh drawn at every level (objects, tracks without levels)
export function meshLod(mesh: Object3D): number | null {
  const match = /_lod(\d+)_/i.exec(mesh.userData['name'] || mesh.name);
  return match ? +match[1] : null;
}

// A dummy of "<scene>_extra.json" written by the converter next to an OBJ, in the format of gg-web-engine meta
// dummies (what the game gets from the ".meta" of the same scene exported to gg-web-engine)
function extraJsonDummyToGgDummy(dummy: any): GgDummy {
  const [x, y, z] = dummy.position || [0, 0, 0];
  let rotation;
  if (dummy.quaternion) {
    const [qw, qx, qy, qz] = dummy.quaternion;
    rotation = { x: qx, y: qy, z: qz, w: qw };
  } else if (dummy.rotation) {
    // Blender "XYZ" Euler angles, which is three.js "ZYX" order
    const q = new Quaternion().setFromEuler(new Euler(dummy.rotation[0], dummy.rotation[1], dummy.rotation[2], 'ZYX'));
    rotation = { x: q.x, y: q.y, z: q.z, w: q.w };
  } else {
    rotation = Qtrn.O;
  }
  return { ...(dummy.properties || {}), name: dummy.name, position: { x, y, z }, rotation };
}

function setupTerrainTextureDefault(texture: Texture) {
  texture.wrapS = RepeatWrapping;
  texture.wrapT = RepeatWrapping;
  setupNfs1Texture(texture);
}

// Track terrain streamed as OBJ chunks along a MapGraph, textured from `<textureArchivePath>/<name>.png`: a texture
// archive (QFS/FAM) serialized there, or textures the track serializer wrote next to the chunks. Props of a chunk are
// the dummies of its "_extra.json", spawned by the adapter's props controller (the same controllers render tracks in
// nfs-web, see `track-props-controller.ts`), with this entity as their `TrackPropsAssets`.
export class TrackMapWorldEntity extends MapGraph3dEntity<TypeDocOf<ThreeGgWorld>> implements TrackPropsAssets {
  public readonly textureLoader = new TextureLoader();
  private readonly terrainMaterials: { [key: string]: MeshBasicMaterial } = {};
  private readonly objLoader = new OBJLoader();
  private readonly models = new Map<string, Promise<Object3D | null>>();
  private readonly propsController: TrackPropsController | null;
  // Terrain meshes with a level of detail, by chunk
  private readonly lodMeshes = new Map<MapGraphNodeType, Mesh[]>();
  // Terrain object, props and files version of each loaded chunk
  private readonly terrains = new Map<MapGraphNodeType, Object3D>();
  private readonly props = new Map<MapGraphNodeType, TrackProp[]>();
  private readonly versions = new Map<MapGraphNodeType, string>();
  private readonly reloads = new Map<MapGraphNodeType, number>();
  // A chunk was loaded, reloaded or unloaded
  readonly chunksChanged$ = new Subject<MapGraphNodeType>();

  constructor(
    public override readonly mapGraph: MapGraph,
    public readonly textureArchivePath: string | null,
    private readonly hideUnknownEntities$: BehaviorSubject<boolean>,
    // The level of detail shown, and the levels found in the loaded chunks so far
    private readonly lod$: BehaviorSubject<number>,
    private readonly lodLevels$: BehaviorSubject<number[]>,
    public readonly adapter: TrackMapAdapter,
    // Folder of the serialized chunks: "<chunksLocation>terrain_chunk_<i>.obj"
    public readonly chunksLocation: string,
    // Files written by the track serializer (chunks and what comes with them)
    public readonly serializedFiles: string[] = [],
    // Files of a chunk, written on demand (the partial export of serializers/common/chunk_export.py). Default: the
    // chunk files are among `serializedFiles`
    private readonly chunkSource: ((node: MapGraphNodeType) => Promise<TrackChunkFiles>) | null = null,
  ) {
    super(mapGraph, { loadDepth: adapter.loadDepth ?? 40, inertia: 2 });
    this.propsController = adapter.propsController ? adapter.propsController(this) : null;
  }

  private _placeholder: Texture | null = null;
  private _placeholderPromise: Promise<Texture> | null = null;

  unknownEntities: Set<Entity3d> = new Set<Entity3d>();

  override onSpawned(world: ThreeGgWorld) {
    super.onSpawned(world);
    this.hideUnknownEntities$.pipe(distinctUntilChanged(), takeUntil(this._onRemoved$)).subscribe(hide => {
      for (const e of this.unknownEntities) {
        e.visible = !hide;
      }
    });
    this.lod$.pipe(distinctUntilChanged(), takeUntil(this._onRemoved$)).subscribe(lod => {
      for (const meshes of this.lodMeshes.values()) {
        for (const mesh of meshes) {
          mesh.visible = meshLod(mesh) === lod;
        }
      }
    });
  }

  // Marks an entity as "unknown" (e.g. a prop whose model/texture couldn't be loaded): it follows the
  // global "hide hidden fields" toggle
  markUnknown(entity: TrackEntity) {
    this.unknownEntities.add(entity as Entity3d);
    entity.visible = !this.hideUnknownEntities$.getValue();
  }

  async getPlaceholderTexture(): Promise<Texture> {
    if (this._placeholder) return this._placeholder;
    if (!this._placeholderPromise) {
      this._placeholderPromise = this.textureLoader.loadAsync('assets/placeholder_texture.png');
    }
    return this._placeholderPromise;
  }

  private _placeholderTerrain: Texture | null = null;
  private _placeholderTerrainPromise: Promise<Texture> | null = null;

  async getPlaceholderTerrainTexture(): Promise<Texture> {
    if (this._placeholderTerrain) return this._placeholderTerrain;
    if (!this._placeholderTerrainPromise) {
      this._placeholderTerrainPromise = this.textureLoader.loadAsync('assets/placeholder_texture.png').then(texture => {
        this.setupTerrainTexture(texture);
        return texture;
      });
    }
    return this._placeholderTerrainPromise;
  }

  private setupTerrainTexture(texture: Texture) {
    (this.adapter.setupTerrainTexture || setupTerrainTextureDefault)(texture);
  }

  protected override async loadChunk(
    node: MapGraphNodeType,
  ): Promise<[TrackEntity[], LoadResultWithProps<TypeDocOf<ThreeGgWorld>>]> {
    const built = await this.buildChunk(node);
    this.addChunk(node, built);
    return [built.entities, null!];
  }

  // Loads the chunk's files again (written again after an edit), if it is loaded. The old version stays shown until
  // the new one is ready
  async reloadChunk(node: MapGraphNodeType) {
    if (!this.loaded.has(node)) {
      return;
    }
    const reload = (this.reloads.get(node) || 0) + 1;
    this.reloads.set(node, reload);
    const built = await this.buildChunk(node);
    if (this.reloads.get(node) !== reload || !this.loaded.has(node)) {
      return;
    }
    this.disposeChunk(node);
    this.addChunk(node, built);
  }

  // Loaded chunk nodes and the version of their files
  get loadedChunks(): Map<MapGraphNodeType, string> {
    return new Map(this.versions);
  }

  // Terrain objects of the loaded chunks
  terrainObjects(): Object3D[] {
    return [...this.terrains.values()];
  }

  terrainObject(node: MapGraphNodeType): Object3D | null {
    return this.terrains.get(node) || null;
  }

  // Loaded props whose dummy has these property values
  findProps(match: { [key: string]: any }): TrackProp[] {
    const found: TrackProp[] = [];
    for (const props of this.props.values()) {
      for (const prop of props) {
        if (Object.entries(match).every(([key, value]) => prop.dummy[key] === value)) {
          found.push(prop);
        }
      }
    }
    return found;
  }

  private async chunkFiles(node: MapGraphNodeType): Promise<TrackChunkFiles> {
    if (this.chunkSource) {
      return this.chunkSource(node);
    }
    const extra = `${node.path}_extra.json`;
    return { obj: `${node.path}.obj`, extra: this.serializedFiles.includes(extra) ? extra : null, version: '' };
  }

  private async buildChunk(node: MapGraphNodeType): Promise<BuiltChunk> {
    const files = await this.chunkFiles(node);
    const query = files.version ? `?v=${files.version}` : '';
    const object = await this.objLoader.loadAsync(files.obj + query);
    object.position.set(node.position.x, node.position.y, node.position.z);
    const lodMeshes: Mesh[] = [];
    object.traverse((child: any) => {
      if (child instanceof Mesh) {
        child.material = this.getTerrainMaterial(meshTextureName(child));
        const lod = meshLod(child);
        if (lod !== null) {
          lodMeshes.push(child);
          child.visible = lod === this.lod$.value;
        }
      }
    });
    const props = files.extra ? await this.loadChunkProps(node, files.extra + query) : [];
    const entity: TrackEntity = new Entity3d({
      object3D: new ThreeDisplayObjectComponent(object),
    });
    return {
      entities: [entity, ...props.map(p => p.entity as TrackEntity)],
      terrain: object,
      lodMeshes,
      props,
      version: files.version,
    };
  }

  private addChunk(node: MapGraphNodeType, built: BuiltChunk) {
    const levels = new Set(this.lodLevels$.value);
    for (const mesh of built.lodMeshes) {
      levels.add(meshLod(mesh)!);
      mesh.visible = meshLod(mesh) === this.lod$.value;
    }
    if (levels.size !== this.lodLevels$.value.length) {
      this.lodLevels$.next([...levels].sort((a, b) => a - b));
    }
    this.lodMeshes.set(node, built.lodMeshes);
    this.terrains.set(node, built.terrain);
    this.props.set(node, built.props);
    this.versions.set(node, built.version);
    for (const prop of built.props) {
      if (prop.isUnknown) {
        this.markUnknown(prop.entity as TrackEntity);
      }
    }
    const [terrain, ...props] = built.entities;
    this.addChildren(terrain, ...props);
    this.loaded.set(node, built.entities);
    this.chunksChanged$.next(node);
  }

  private async loadChunkProps(node: MapGraphNodeType, extraPath: string): Promise<TrackProp[]> {
    if (!this.propsController) {
      return [];
    }
    let dummies: GgDummy[];
    try {
      dummies = ((await (await fetch(extraPath)).json()).dummies || []).map(extraJsonDummyToGgDummy);
    } catch (err) {
      console.warn(`Could not load props of ${node.path}`, err);
      return [];
    }
    return this.propsController.spawnChunkProps(dummies, node.position);
  }

  // `TrackPropsAssets`: models are the OBJ files of the converter
  loadModel(dir: string, withMaterials: boolean): Promise<Object3D | null> {
    const key = `${dir}|${withMaterials}`;
    if (!this.models.has(key)) {
      this.models.set(
        key,
        (async () => {
          const loader = new OBJLoader();
          if (withMaterials) {
            try {
              const materials = await new MTLLoader().loadAsync(`${dir}/material.mtl`);
              materials.preload();
              loader.setMaterials(materials);
            } catch (err) {
              // a model without materials
            }
          }
          return loader.loadAsync(`${dir}/geometry.obj`);
        })().catch(err => {
          console.warn(`Could not load model ${dir}`, err);
          return null;
        }),
      );
    }
    return this.models.get(key)!.then(model => (model ? model.clone() : null));
  }

  async loadTexture(path: string): Promise<Texture | null> {
    return this.textureLoader.loadAsync(path).catch(() => null);
  }

  placeholderModel(): Object3D {
    const material = new MeshBasicMaterial();
    this.getPlaceholderTexture().then(texture => {
      material.map = texture;
      material.needsUpdate = true;
    });
    return new Mesh(new SphereGeometry(5), material);
  }

  placeholderTexture(): Promise<Texture> {
    return this.getPlaceholderTexture();
  }

  protected override disposeChunk(node: MapGraphNodeType) {
    const wasLoaded = this.loaded.has(node);
    this.lodMeshes.delete(node);
    this.terrains.delete(node);
    this.props.delete(node);
    this.versions.delete(node);
    for (const c of this.loaded.get(node) || []) {
      this.unknownEntities.delete(c as Entity3d);
    }
    super.disposeChunk(node);
    if (wasLoaded) {
      this.chunksChanged$.next(node);
    }
  }

  getTerrainMaterial(matId: string): Material {
    if (!this.terrainMaterials[matId]) {
      this.terrainMaterials[matId] = new MeshBasicMaterial({
        side: DoubleSide,
        transparent: true,
        visible: false,
        alphaTest: this.adapter.terrainAlphaTest || 0,
      });
      const applyTexture = (texture: Texture) => {
        this.terrainMaterials[matId].map = texture;
        this.terrainMaterials[matId].needsUpdate = true;
        this.terrainMaterials[matId].visible = true;
      };
      if (this.textureArchivePath) {
        this.textureLoader
          .loadAsync(`${this.textureArchivePath}/${matId}.png`)
          .then(texture => {
            this.setupTerrainTexture(texture);
            applyTexture(texture);
          })
          .catch(() => {
            console.warn(`Problem with loading terrain material ${matId}`);
            this.getPlaceholderTerrainTexture().then(applyTexture);
          });
      } else {
        this.getPlaceholderTerrainTexture().then(applyTexture);
      }
    }
    return this.terrainMaterials[matId];
  }
}
