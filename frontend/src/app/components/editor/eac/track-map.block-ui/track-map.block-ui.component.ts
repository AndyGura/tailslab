import {
  AfterViewInit,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  inject,
  OnChanges,
  OnDestroy,
  SimpleChanges,
  ViewChild,
} from '@angular/core';
import { GuiComponent } from '../../gui.component';
import {
  createInlineTickController,
  Entity3d,
  FreeCameraController,
  Gg3dWorld,
  MapGraph,
  MapGraphNodeType,
  Pnt3,
  Point2,
  Point3,
  Qtrn,
  Renderer3dEntity,
} from '@gg-web-engine/core';
import { BehaviorSubject, debounceTime, filter, Subject, takeUntil } from 'rxjs';
import {
  AmbientLight,
  BufferAttribute,
  Camera,
  CubeReflectionMapping,
  DoubleSide,
  Material,
  Mesh,
  MeshBasicMaterial,
  Object3D,
  Quaternion,
  Texture,
  TextureLoader,
  Vector3,
} from 'three';
import { ThreeGgWorld, ThreeSceneComponent, ThreeVisualTypeDocRepo } from '@gg-web-engine/three';
import { BlockSchema, Resource } from '../../types';
import { ViewMode, ViewModeController } from '../../common/obj-viewer/view-mode-toolbar/view-mode.controller';
import { setViewerSky } from '../../common/obj-viewer/viewer-sky';
import { joinId } from '../../../../utils/join-id';
import {
  findTrackMapAdapter,
  TrackLayout,
  TrackMapAdapter,
  TrackSplineDetailPanel,
  TrackSplinePoint,
} from './track-map-adapters';
import { TrackChunkFiles, TrackEntity, TrackMapWorldEntity } from './track-map-world.entity';
import { TrackProp } from './track-props-controller';
import { SpatialEditController, SpatialEditHost, SpatialMove } from '../../common/spatial-edit/spatial-edit.controller';
import { SpatialEditKind, SpatialHandle, spatialEditKinds } from '../../common/spatial-edit/spatial-edit.types';
import { SelectionOrbit } from '../../common/spatial-edit/selection-orbit';

// Focus brings the camera this close to the selection
const FOCUS_DISTANCE = 15;

// Mesh vertices at a terrain handle's position (the OBJ splits the terrain by texture, so a vertex has copies) are
// within this distance of it
const VERTEX_MATCH_DISTANCE = 0.005;

// What a drag moves before the files are written again, per selected handle: copies of a terrain vertex in the loaded
// meshes, props
interface SpatialPreview {
  vertices: { mesh: Mesh; attribute: BufferAttribute; index: number }[];
  props: TrackProp[];
}

// Game coordinates (Y up) -> viewer coordinates (Z up)
function toViewer(p: Point3): Point3 {
  return { x: p.x, y: p.z, z: p.y };
}

// Chunked track viewer shared by TNFS (TRI), NFS2 (TRK), NFS3 (FRD), NFS4 (FRD), NFS5 (CRP), NFS6 and NFSU tracks;
// per-game differences live in a `TrackMapAdapter`, picked by the block class
@Component({
  selector: 'app-track-map-block-ui',
  templateUrl: './track-map.block-ui.component.html',
  styleUrls: ['./track-map.block-ui.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: false,
})
export class TrackMapBlockUiComponent extends GuiComponent implements AfterViewInit, OnChanges, OnDestroy {
  @ViewChild('previewCanvasContainer') previewCanvasContainer!: ElementRef<HTMLDivElement>;
  @ViewChild('previewCanvas') previewCanvas!: ElementRef<HTMLCanvasElement>;

  previewLoading$: BehaviorSubject<boolean> = new BehaviorSubject<boolean>(true);
  // Texture archives (QFS/FAM) found next to the track, offered in the picker
  textureArchiveOptions$: BehaviorSubject<string[]> = new BehaviorSubject<string[]>([]);
  textureArchiveLoading$: BehaviorSubject<boolean> = new BehaviorSubject<boolean>(false);
  // The loaded texture archive, null when the terrain uses placeholder textures
  textureArchivePath$: BehaviorSubject<string | null> = new BehaviorSubject<string | null>(null);
  private terrainChunksObjLocation: string | undefined;
  // Files written by the track serializer for the chunked preview
  private serializedFiles: string[] = [];

  pointer$: BehaviorSubject<Point3 | null> = new BehaviorSubject<Point3 | null>(null);
  // Terrain level of detail shown (0 = highest) and the levels the track has (found in the loaded chunks)
  lod$: BehaviorSubject<number> = new BehaviorSubject<number>(0);
  lodLevels$: BehaviorSubject<number[]> = new BehaviorSubject<number[]>([]);

  selectedSplineIndex$: BehaviorSubject<number> = new BehaviorSubject<number>(0);
  selectedSplineDetails$: BehaviorSubject<{ title: string; resource: Resource }[]> = new BehaviorSubject<
    { title: string; resource: Resource }[]
  >([]);
  world!: ThreeGgWorld;
  renderer: Renderer3dEntity<ThreeVisualTypeDocRepo> | null = null;
  map: TrackMapWorldEntity | null = null;
  adapter: TrackMapAdapter | null = null;
  controller!: FreeCameraController;
  // the camera while spatial edit handles are selected: it turns around them
  selectionOrbit: SelectionOrbit | null = null;
  chunkPositions: Point3[] | null = null;
  splinePoints: TrackSplinePoint[] = [];
  minimapSpline: Point3[] = [];
  isClosed: boolean = true;
  ambientLight: AmbientLight = new AmbientLight(0xffffff, 2);
  viewModeController?: ViewModeController;
  skySphere!: TrackEntity;
  selectionSphere!: TrackEntity;

  // Spatial edits (library/spatial_edit.py): the kinds the block declares, the active one (null = view only)
  spatialKinds: SpatialEditKind[] = [];
  editKind$: BehaviorSubject<SpatialEditKind | null> = new BehaviorSubject<SpatialEditKind | null>(null);
  spatialEdit: SpatialEditController | null = null;
  // chunks being written again / reloaded after a change
  rebuilding$: BehaviorSubject<number> = new BehaviorSubject<number>(0);
  selectedHandleDetail$: BehaviorSubject<{ title: string; resource: Resource } | null> = new BehaviorSubject<{
    title: string;
    resource: Resource;
  } | null>(null);
  // Terrain chunk nodes of the map graph, by chunk index
  private chunkNodes: MapGraphNodeType[] = [];
  private readonly chunkIndices = new Map<MapGraphNodeType, number>();
  // Chunk files asked for by the map, written in one call (adapters with `chunkExport`)
  private readonly chunkRequests = new Map<
    number,
    { resolve: (f: TrackChunkFiles) => void; reject: (e: any) => void }[]
  >();
  private chunkRequestTimer: any = null;
  // Handles of the active edit kind in the loaded chunks, by chunk; chunks whose handles must be asked for again
  private readonly handlesByChunk = new Map<number, SpatialHandle[]>();
  private readonly staleHandleChunks = new Set<number>();
  private handleSyncTimer: any = null;
  private handleSync: Promise<void> = Promise.resolve();
  private chunkRefresh: Promise<void> = Promise.resolve();
  // by handle id
  private readonly spatialPreview = new Map<string, SpatialPreview>();
  private pointerOverViewport = false;

  private readonly destroyed$: Subject<void> = new Subject<void>();
  // Resolves once the 3D world is set up; inputs can arrive before that
  private markViewReady!: () => void;
  private readonly viewReady: Promise<void> = new Promise(resolve => (this.markViewReady = resolve));

  get viewMode(): ViewMode {
    return this.viewModeController?.viewMode || 'material';
  }

  readonly cdr = inject(ChangeDetectorRef);

  async ngAfterViewInit() {
    this.world = new Gg3dWorld({ visualScene: new ThreeSceneComponent() });
    await this.world.init();
    setViewerSky(this.world);
    this.viewModeController = new ViewModeController(this.world.visualScene.nativeScene!, this.ambientLight);
    this.viewModeController.onFrameAll = () => this.placeRendererAtHome();
    this.world.visualScene.nativeScene!.add(this.ambientLight);
    this.skySphere = new Entity3d({
      object3D: this.world.visualScene.factory.createPrimitive(
        {
          shape: 'SPHERE',
          radius: 1000,
        },
        { color: 0xffffff },
      ),
    });
    ((this.skySphere.object3D!.nativeMesh as Mesh).material as Material).side = DoubleSide;
    this.world.addEntity(this.skySphere);
    this.setSkyTexture(null);
    this.selectionSphere = new Entity3d({
      object3D: this.world.visualScene.factory.createPrimitive(
        { shape: 'SPHERE', radius: 0.5 },
        {
          color: 0xff0000,
          shading: 'unlit',
        },
      ),
    });
    ((this.selectionSphere.object3D!.nativeMesh as Mesh).material as Material).opacity = 0.4;
    ((this.selectionSphere.object3D!.nativeMesh as Mesh).material as Material).transparent = true;
    this.world.addEntity(this.selectionSphere);

    let rendererSize$: BehaviorSubject<Point2> = new BehaviorSubject<Point2>({ x: 1, y: 1 });
    this.renderer = this.world.addRenderer(
      this.world.visualScene.factory.createPerspectiveCamera(),
      this.previewCanvas.nativeElement,
      {
        size: rendererSize$.asObservable(),
        background: 0xaaaaaa,
      },
    );
    this.placeRendererAtHome();
    createInlineTickController(this.world)
      .pipe(takeUntil(this.destroyed$))
      .subscribe(() => {
        if (this.renderer) {
          this.skySphere.position = this.renderer.camera.position;
          this.pointer$.next(this.renderer.camera.position);
          if (this.map) {
            this.map.loaderCursor$.next(this.renderer.position);
          }
        }
      });

    this.controller = new FreeCameraController(this.world.keyboardInput, this.renderer, {
      mouseOptions: {
        canvas: this.previewCanvas.nativeElement,
        pointerLock: true,
      },
      keymap: 'wasd+arrows',
      cameraLinearSpeed: 40,
      cameraBoostMultiplier: 4,
      cameraMovementElasticity: 100,
      cameraRotationElasticity: 30,
      ignoreMouseUnlessPointerLocked: true,
      ignoreKeyboardUnlessPointerLocked: true,
      // the field of view stays as it is
      zoomOutInKeys: ['', ''],
    });
    this.world.addEntity(this.controller);
    this.setupSpatialEdit();
    const updateSize = () => {
      rendererSize$.next({
        x: this.previewCanvasContainer.nativeElement.clientWidth,
        y: this.previewCanvasContainer.nativeElement.clientHeight,
      });
    };
    new ResizeObserver(updateSize).observe(this.previewCanvasContainer.nativeElement);
    updateSize();
    this.world.start();
    // tracks exported per chunk reload the chunks a change made outdated, the others are exported again
    this.changes.change$
      .pipe(
        takeUntil(this.destroyed$),
        filter(x => !!(this.resourceId && x.startsWith(this.resourceId) && this.adapter?.chunkExport)),
        debounceTime(100),
      )
      .subscribe(() => {
        this.chunkRefresh = this.chunkRefresh.then(() => this.refreshChangedChunks()).catch(err => console.error(err));
      });
    this.changes.change$
      .pipe(
        takeUntil(this.destroyed$),
        filter(x => !!(this.resourceId && x.startsWith(this.resourceId) && !this.adapter?.chunkExport)),
        debounceTime(3000),
      )
      .subscribe(async () => {
        this.previewLoading$.next(true);
        await this.loadTerrainChunks(this.resourceId);
        await this.loadPreview();
        this.previewLoading$.next(false);
      });

    this.selectedSplineIndex$.pipe(takeUntil(this.destroyed$), debounceTime(250)).subscribe(i => {
      this.updateSplineDetails();
      const splinePoint = this.splinePoints[i];
      if (!this.resourceId || !splinePoint) {
        return;
      }
      const point = toViewer(splinePoint.position);
      this.selectionSphere.position = point;
      if (this.renderer) {
        // flying somewhere else: the free camera
        this.spatialEdit?.select([]);
        this.renderer.position = Pnt3.add(
          point,
          Pnt3.rotAround({ x: 10, y: -12, z: 5 }, { x: 0, y: 0, z: 1 }, -splinePoint.orientation),
        );
        this.renderer.rotation = Qtrn.lookAt(this.renderer.position, point, { x: 0, y: 0, z: 1 });
        this.controller.reset();
      }
    });
    this.markViewReady();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.hasOwnProperty('resourceSchema')) {
      this.adapter = findTrackMapAdapter(this.resourceSchema?.block_class_mro);
      this.spatialKinds = spatialEditKinds(this.resourceSchema);
    }
    if (changes.hasOwnProperty('resourceId')) {
      this.setEditKind(null);
    }
    if (changes.hasOwnProperty('resourceId') || changes.hasOwnProperty('resourceData')) {
      const data = this.resourceData;
      const adapter = this.adapter;
      if (!adapter?.loadLayout) {
        this.applyLayout(
          data && adapter
            ? {
                chunkPositions: adapter.chunkPositions ? adapter.chunkPositions(data) : null,
                splinePoints: adapter.splinePoints
                  ? adapter.splinePoints(data)
                  : (adapter.chunkPositions ? adapter.chunkPositions(data) : []).map(position => ({
                      position,
                      orientation: 0,
                    })),
                isClosed: !adapter.isClosed || adapter.isClosed(data),
              }
            : null,
        );
      }
      this.updateSplineDetails();
      this.previewLoading$.next(true);
      const resourceIdChanged = changes.hasOwnProperty('resourceId');
      if (resourceIdChanged) {
        this.lodLevels$.next([]);
        this.lod$.next(0);
      }
      this.loadTerrainChunks(adapter ? this.resourceId : undefined).then(async () => {
        await this.viewReady;
        if (resourceIdChanged && this.resourceId && adapter?.textureArchivePatterns) {
          await this.findTextureArchives(adapter.textureArchivePatterns(this.resourceId));
          await this.onTextureArchiveSelected(this.textureArchiveOptions$.value[0] || null, true);
        } else {
          await this.loadPreview();
        }
        this.previewLoading$.next(false);
      });
    }
  }

  private applyLayout(layout: TrackLayout | null) {
    this.chunkPositions = layout?.chunkPositions ? layout.chunkPositions.map(toViewer) : null;
    this.splinePoints = layout ? layout.splinePoints : [];
    this.minimapSpline = this.splinePoints.map(p => toViewer(p.position));
    this.isClosed = !layout || layout.isClosed;
    this.cdr.markForCheck();
  }

  private async findTextureArchives(patterns: string[]) {
    let found: string[] = [];
    try {
      found = await this.mainService.api.findFiles(patterns);
    } catch (err) {
      console.warn('Could not look up texture archives', err);
    }
    this.textureArchiveOptions$.next(found);
  }

  async browseTextureArchive() {
    const [path] = await this.mainService.api.openFileDialog();
    if (!path) {
      return;
    }
    const normalized = path.replace(/\\/g, '/');
    if (!this.textureArchiveOptions$.value.includes(normalized)) {
      this.textureArchiveOptions$.next([...this.textureArchiveOptions$.value, normalized]);
    }
    await this.onTextureArchiveSelected(normalized);
  }

  // Picker label: the path relative to the folder where the track file lies
  textureArchiveLabel(path: string): string {
    const id = this.resourceId || '';
    const dir = id.substring(0, Math.max(id.lastIndexOf('/'), id.lastIndexOf('\\')) + 1);
    const parentDir = dir.substring(0, Math.max(dir.lastIndexOf('/', dir.length - 2), 0) + 1);
    if (dir && path.startsWith(dir)) {
      return path.substring(dir.length);
    }
    if (parentDir && path.startsWith(parentDir)) {
      return '../' + path.substring(parentDir.length);
    }
    return path;
  }

  private setSkyTexture(texture: Texture | null) {
    const mesh = this.skySphere.object3D!.nativeMesh as Mesh;
    const material = mesh.material as MeshBasicMaterial;
    material.map = texture;
    material.needsUpdate = true;
    // without the track's sky the viewer's background sky shows
    mesh.visible = !!texture;
  }

  async onTextureArchiveSelected(path: string | null, force: boolean = false) {
    if (!force && this.textureArchivePath$.value == path) {
      return;
    }
    this.textureArchiveLoading$.next(true);
    try {
      if (!path) {
        this.setSkyTexture(null);
        this.textureArchivePath$.next(null);
        return;
      }
      // Serializes the archive's textures (and, for FAM, props) to disk under `resources/<path>`,
      // where `TrackMapWorldEntity` loads them from
      const files = await this.mainService.api.serializeResource(
        path,
        null,
        this.adapter?.textureArchiveSettings || {},
      );
      if (this.adapter?.hasSkybox) {
        const skyPath = files.find(x => x.endsWith('spherical.png'));
        if (skyPath) {
          const tex = await new TextureLoader().loadAsync(skyPath);
          tex.colorSpace = 'srgb';
          tex.mapping = CubeReflectionMapping;
          this.setSkyTexture(tex);
        } else {
          this.setSkyTexture(null);
        }
      }
      this.textureArchivePath$.next(path);
    } catch (err) {
      if (this.adapter?.hasSkybox) {
        this.setSkyTexture(null);
      }
      this.textureArchivePath$.next(null);
    } finally {
      this.textureArchiveLoading$.next(false);
      await this.loadPreview();
    }
  }

  private async loadTerrainChunks(blockId?: string) {
    if (blockId && this.adapter?.chunkExport) {
      // chunk files are written when the map loads them
      const result = await this.mainService.api.serializeChunks(blockId, []);
      this.serializedFiles = [];
      this.terrainChunksObjLocation = result.path;
    } else if (blockId) {
      const paths = await this.mainService.api.serializeResource(blockId, null, {
        geometry__save_obj: true,
        geometry__save_blend: false,
        geometry__export_to_gg_web_engine: false,
        maps__save_as_chunked: true,
        // the viewer loads one file per chunk of the track
        maps__tnfs_chunks_per_file: 1,
        maps__save_spherical_skybox_texture: !!this.adapter?.hasSkybox,
        maps__add_props_to_obj: false,
        // every level of detail, for the LOD switch
        maps__save_all_lods: true,
      });
      this.serializedFiles = paths;
      let anyObjPath = paths.find(x => x.endsWith('.obj') && x.includes('terrain_chunk_')) || '';
      this.terrainChunksObjLocation = anyObjPath.substring(0, anyObjPath.indexOf('terrain_chunk_'));
      if (this.adapter?.loadLayout) {
        const hadSpline = this.splinePoints.length > 0;
        this.applyLayout(await this.adapter.loadLayout(paths));
        if (!hadSpline) {
          // the layout wasn't known when the view was set up: fly to the selected spline item now
          this.selectedSplineIndex$.next(this.selectedSplineIndex$.value);
        }
      } else if (this.adapter && !this.adapter.chunkPositions) {
        this.chunkPositions = await this.loadChunkPositionsFile(paths.find(x => x.endsWith('terrain_chunks.json')));
        if (!this.adapter.splinePoints && this.chunkPositions) {
          this.splinePoints = this.chunkPositions.map(position => ({ position: toViewer(position), orientation: 0 }));
          this.minimapSpline = this.chunkPositions;
        }
      }
    } else {
      this.terrainChunksObjLocation = undefined;
      this.serializedFiles = [];
      if (this.adapter?.loadLayout) {
        this.applyLayout(null);
      }
    }
  }

  private async loadChunkPositionsFile(path: string | undefined): Promise<Point3[] | null> {
    if (!path) {
      return null;
    }
    try {
      const positions: Point3[] = await (await fetch(path)).json();
      return positions.map(toViewer);
    } catch (err) {
      console.warn('Could not load terrain chunk positions', err);
      return null;
    }
  }

  // Folder with terrain textures (`<name>.png`), null for placeholder textures
  private get terrainTexturesPath(): string | null {
    if (this.adapter?.bundledTextures) {
      return this.terrainChunksObjLocation ? `${this.terrainChunksObjLocation}textures` : null;
    }
    const textureArchivePath = this.textureArchivePath$.value;
    return (
      textureArchivePath &&
      'resources/' +
        textureArchivePath
          .split('/')
          .filter(x => !!x)
          .join('/')
    );
  }

  lodLabel(lod: number): string {
    return lod === 0 ? 'LOD 0 (highest)' : `LOD ${lod}`;
  }

  onPointerChange(pos: Point3) {
    if (!this.renderer) {
      return;
    }
    this.spatialEdit?.select([]);
    this.renderer.position = pos;
  }

  private updateSplineDetails() {
    const panels: TrackSplineDetailPanel[] = this.adapter?.splineDetailPanels || [];
    const data = this.resourceData;
    if (!this.resourceId || !data || !panels.length) {
      this.selectedSplineDetails$.next([]);
      return;
    }
    const i = this.selectedSplineIndex$.value;
    this.selectedSplineDetails$.next(
      panels.map(panel => {
        const entryIndex = Math.floor(i / panel.itemsPerEntry);
        return {
          title: panel.title,
          resource: {
            id: joinId(this.resourceId!, `${panel.field}/${entryIndex}`),
            data: (data[panel.field] || [])[entryIndex],
            schema: (this.resourceSchema?.fields || []).find(
              (x: { name: string; schema: BlockSchema }) => x.name === panel.field,
            )?.schema.child_schema,
            name: '',
          },
        };
      }),
    );
  }

  private async loadPreview() {
    if (!this.resourceData || !this.adapter) return;
    if (!this.terrainChunksObjLocation || !this.chunkPositions) {
      return;
    }
    const chunkNodes = this.chunkPositions.map((position: Point3, i: number) => ({
      path: `${this.terrainChunksObjLocation}terrain_chunk_${i}`,
      position,
      loadOptions: {},
    }));
    const chunksGraph = this.adapter.chunkGraph
      ? this.adapter.chunkGraph(chunkNodes)
      : MapGraph.fromMapArray(chunkNodes, this.isClosed);
    this.unloadPreview();
    this.chunkNodes = chunkNodes;
    chunkNodes.forEach((node, i) => this.chunkIndices.set(node, i));
    const map = new TrackMapWorldEntity(
      chunksGraph,
      this.terrainTexturesPath,
      this.mainService.hideHiddenFields$,
      this.lod$,
      this.lodLevels$,
      this.adapter,
      this.terrainChunksObjLocation,
      this.serializedFiles,
      this.adapter.chunkExport ? node => this.requestChunkFiles(node) : null,
    );
    this.map = map;
    map.chunksChanged$.pipe(takeUntil(this.destroyed$)).subscribe(node => {
      if (this.map === map) {
        this.staleHandleChunks.add(this.chunkIndices.get(node)!);
        this.scheduleHandleSync();
      }
    });
    this.world.addEntity(map);
    this.cdr.markForCheck();
  }

  private unloadPreview() {
    this.chunkNodes = [];
    this.chunkIndices.clear();
    this.handlesByChunk.clear();
    this.spatialEdit?.setHandles([]);
    if (this.map) {
      this.world.removeEntity(this.map);
      this.map.dispose();
      this.map = null;
      this.cdr.markForCheck();
    }
  }

  // Chunk files for the map, of every chunk it asks for within a few ms written in one call
  private requestChunkFiles(node: MapGraphNodeType): Promise<TrackChunkFiles> {
    const index = this.chunkIndices.get(node)!;
    return new Promise((resolve, reject) => {
      this.chunkRequests.set(index, [...(this.chunkRequests.get(index) || []), { resolve, reject }]);
      if (this.chunkRequestTimer === null) {
        this.chunkRequestTimer = setTimeout(() => this.flushChunkRequests(), 20);
      }
    });
  }

  private async flushChunkRequests() {
    this.chunkRequestTimer = null;
    const requests = new Map(this.chunkRequests);
    this.chunkRequests.clear();
    try {
      const result = await this.mainService.api.serializeChunks(this.resourceId!, [...requests.keys()]);
      for (const [i, waiting] of requests) {
        const chunk = result.chunks[i];
        const obj = chunk?.files.find(f => f.endsWith('.obj'));
        for (const w of waiting) {
          if (obj) {
            w.resolve({
              obj,
              extra: chunk.files.find(f => f.endsWith('_extra.json')) || null,
              version: chunk.fingerprint,
            });
          } else {
            w.reject(new Error(`Chunk ${i} was not exported`));
          }
        }
      }
    } catch (err) {
      requests.forEach(waiting => waiting.forEach(w => w.reject(err)));
    }
  }

  // After a change (an edit, undo / redo, a value typed in a panel): the layout from the data, then the loaded chunks
  // whose files were written again are reloaded. Chunks not loaded are exported when the map loads them
  private async refreshChangedChunks() {
    const map = this.map;
    const adapter = this.adapter;
    const data = this.resourceData;
    if (!map || !adapter?.chunkPositions || !data || !this.resourceId) {
      return;
    }
    this.applyLayout({
      chunkPositions: adapter.chunkPositions(data),
      splinePoints: adapter.splinePoints ? adapter.splinePoints(data) : [],
      isClosed: !adapter.isClosed || adapter.isClosed(data),
    });
    this.updateSplineDetails();
    const selection = this.spatialEdit?.selection$.value || [];
    this.updateSelectedHandleDetail(selection.length === 1 ? selection[0] : null);
    const positions = this.chunkPositions || [];
    if (positions.length !== this.chunkNodes.length) {
      // chunks added or removed: a new map graph
      await this.loadPreview();
      return;
    }
    // nodes are moved in place: a chunk is placed at its node when it loads
    this.chunkNodes.forEach((node, i) => (node.position = positions[i]));
    // the selected handles hold what the last move stored, which an undo right after it changes back without changing
    // the chunks loaded since
    for (const handle of this.spatialEdit?.selection$.value || []) {
      this.staleHandleChunks.add(handle.chunk);
    }
    this.scheduleHandleSync();
    const loaded = map.loadedChunks;
    const indices = [...loaded.keys()].map(node => this.chunkIndices.get(node)!);
    const result = await this.mainService.api.serializeChunks(this.resourceId, indices);
    const outdated = indices.filter(
      i => result.chunks[i] && result.chunks[i].fingerprint !== loaded.get(this.chunkNodes[i]),
    );
    if (!outdated.length || map !== this.map) {
      return;
    }
    this.rebuilding$.next(outdated.length);
    try {
      await Promise.all(outdated.map(i => map.reloadChunk(this.chunkNodes[i])));
    } finally {
      this.rebuilding$.next(0);
    }
  }

  setEditKind(kind: SpatialEditKind | null) {
    if (kind === this.editKind$.value) {
      return;
    }
    this.editKind$.next(kind);
    this.handlesByChunk.clear();
    this.spatialEdit?.setKind(kind);
    if (!kind && this.previewCanvas && document.pointerLockElement === this.previewCanvas.nativeElement) {
      document.exitPointerLock();
    }
    this.scheduleHandleSync();
    this.cdr.markForCheck();
  }

  private scheduleHandleSync() {
    if (this.handleSyncTimer !== null) {
      return;
    }
    this.handleSyncTimer = setTimeout(() => {
      this.handleSyncTimer = null;
      this.handleSync = this.handleSync.then(() => this.syncHandles()).catch(err => console.error(err));
    }, 50);
  }

  // Handles of the active kind in the loaded chunks: asked for the chunks loaded or reloaded since the last time
  private async syncHandles() {
    const kind = this.editKind$.value;
    const map = this.map;
    if (!kind || !map || !this.resourceId || !this.spatialEdit) {
      return;
    }
    const loaded = new Set([...map.loadedChunks.keys()].map(node => this.chunkIndices.get(node)!));
    for (const i of [...this.handlesByChunk.keys()]) {
      if (!loaded.has(i)) {
        this.handlesByChunk.delete(i);
      }
    }
    const missing = [...loaded].filter(i => !this.handlesByChunk.has(i) || this.staleHandleChunks.has(i));
    missing.forEach(i => this.staleHandleChunks.delete(i));
    if (missing.length) {
      const handles = await this.mainService.api.spatialHandles(this.resourceId, kind.kind, missing);
      if (kind !== this.editKind$.value || map !== this.map) {
        return;
      }
      missing.forEach(i => this.handlesByChunk.set(i, []));
      for (const handle of handles) {
        this.handlesByChunk.get(handle.chunk)?.push(handle);
      }
    }
    this.spatialEdit.setHandles([...this.handlesByChunk.values()].flat());
  }

  private setupSpatialEdit() {
    const canvas = this.previewCanvas.nativeElement;
    const container = this.previewCanvasContainer.nativeElement;
    const camera = (this.renderer!.camera as any).nativeCamera as Camera;
    this.spatialEdit = new SpatialEditController(
      this.world.visualScene.nativeScene!,
      camera,
      canvas,
      this.spatialEditHost(),
    );
    // While handles are selected the camera turns around them (left drag, the wheel for the distance), else it is the
    // free camera. The gizmo and the selection box are dragged with the same button: the orbit then holds still
    const spatialEdit = this.spatialEdit;
    this.selectionOrbit = new SelectionOrbit(this.renderer!, canvas, () => spatialEdit.pointerCaptured$.value);
    spatialEdit.selection$.pipe(takeUntil(this.destroyed$)).subscribe(selection => {
      this.updateSelectedHandleDetail(selection.length === 1 ? selection[0] : null);
      // also after a move: the orbit turns around where the selection is now
      this.selectionOrbit!.pivot = selection.length ? spatialEdit.pivotPosition : null;
      this.applyCameraMode();
    });
    const editing = () => !!this.editKind$.value;
    // While editing, a left click selects (the camera controller would lock the pointer), the right button held
    // turns the camera (and WASD flies, as with the pointer locked)
    container.addEventListener('click', e => editing() && e.target === canvas && e.stopPropagation(), true);
    container.addEventListener(
      'pointerdown',
      e => {
        if (
          editing() &&
          !this.selectionOrbit?.enabled &&
          e.target === canvas &&
          e.button === 2 &&
          !document.pointerLockElement
        ) {
          canvas.requestPointerLock();
        }
      },
      true,
    );
    container.addEventListener('contextmenu', e => editing() && e.target === canvas && e.preventDefault());
    container.addEventListener('pointerenter', () => (this.pointerOverViewport = true));
    container.addEventListener('pointerleave', () => (this.pointerOverViewport = false));
    const onPointerUp = (e: PointerEvent) => {
      if (editing() && e.button === 2 && document.pointerLockElement === canvas) {
        document.exitPointerLock();
      }
    };
    const onKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (
        !editing() ||
        !this.pointerOverViewport ||
        document.pointerLockElement ||
        e.ctrlKey ||
        e.metaKey ||
        e.altKey ||
        ['INPUT', 'TEXTAREA', 'SELECT'].includes(target?.tagName)
      ) {
        return;
      }
      const selected = !!this.spatialEdit?.selection$.value.length;
      if (e.key === 'g' || e.key === 'G') {
        this.spatialEdit?.setGizmoMode('translate');
      } else if (e.key === 'r' || e.key === 'R') {
        this.spatialEdit?.setGizmoMode('rotate');
      } else if (e.key === 'Escape') {
        this.spatialEdit?.select([]);
      } else if ((e.key === 'f' || e.key === 'F') && selected) {
        this.focusSelection();
      } else {
        return;
      }
      e.preventDefault();
    };
    window.addEventListener('pointerup', onPointerUp);
    window.addEventListener('keydown', onKeyDown);
    this.destroyed$.subscribe(() => {
      window.removeEventListener('pointerup', onPointerUp);
      window.removeEventListener('keydown', onKeyDown);
    });
    this.cdr.markForCheck();
  }

  private spatialEditHost(): SpatialEditHost {
    return {
      handleObjects: handle =>
        this.map && handle.match
          ? this.map.findProps(handle.match).map(p => p.entity.object3D!.nativeMesh as Object3D)
          : [],
      occluders: () => this.map?.terrainObjects() || [],
      previewStart: handles => this.startSpatialPreview(handles),
      preview: moves => this.updateSpatialPreview(moves),
      previewEnd: () => this.spatialPreview.clear(),
      commit: async moves => {
        const kind = this.editKind$.value;
        if (!kind || !this.resourceId) {
          return null;
        }
        const result = await this.mainService.api.spatialMove(
          this.resourceId,
          kind.kind,
          moves.map(m => ({
            id: m.handle.id,
            position: m.position.toArray(),
            rotation: m.rotation ? m.rotation.toArray() : null,
          })),
        );
        return result.handles;
      },
    };
  }

  // What a drag of the selection moves until the chunks are reloaded: the copies of each terrain vertex in the meshes
  // of its chunk and the neighbour ones (they share edge vertices), the props drawing them
  private startSpatialPreview(handles: SpatialHandle[]) {
    this.spatialPreview.clear();
    const map = this.map;
    const deforms = !!this.editKind$.value?.deforms_mesh && this.chunkNodes.length > 0;
    const local = new Vector3();
    const vertex = new Vector3();
    const count = this.chunkNodes.length;
    for (const handle of handles) {
      const preview: SpatialPreview = { vertices: [], props: [] };
      if (map && deforms) {
        const start = new Vector3().fromArray(handle.position);
        for (const i of new Set([handle.chunk - 1, handle.chunk, handle.chunk + 1].map(j => (j + count) % count))) {
          const terrain = map.terrainObject(this.chunkNodes[i]);
          terrain?.updateMatrixWorld(true);
          terrain?.traverse(o => {
            if (!(o instanceof Mesh)) return;
            const attribute = o.geometry.getAttribute('position') as BufferAttribute;
            o.worldToLocal(local.copy(start));
            for (let k = 0; k < attribute.count; k++) {
              if (vertex.fromBufferAttribute(attribute, k).distanceTo(local) < VERTEX_MATCH_DISTANCE) {
                preview.vertices.push({ mesh: o, attribute, index: k });
              }
            }
          });
        }
      }
      if (map && handle.match) {
        preview.props = map.findProps(handle.match);
      }
      this.spatialPreview.set(handle.id, preview);
    }
  }

  private updateSpatialPreview(moves: SpatialMove[]) {
    const local = new Vector3();
    const meshes = new Set<Mesh>();
    for (const { handle, position, rotation } of moves) {
      const preview = this.spatialPreview.get(handle.id);
      if (!preview) {
        continue;
      }
      for (const v of preview.vertices) {
        v.mesh.worldToLocal(local.copy(position));
        v.attribute.setXYZ(v.index, local.x, local.y, local.z);
        v.attribute.needsUpdate = true;
        meshes.add(v.mesh);
      }
      for (const prop of preview.props) {
        prop.entity.position = { x: position.x, y: position.y, z: position.z };
        if (rotation) {
          prop.entity.rotation = { x: rotation.x, y: rotation.y, z: rotation.z, w: rotation.w };
        }
      }
    }
    meshes.forEach(mesh => mesh.geometry.computeBoundingSphere());
  }

  // Brings the camera close to the selection, looking at it from the side it is on
  focusSelection() {
    if (this.spatialEdit?.selection$.value.length) {
      this.selectionOrbit?.frame(FOCUS_DISTANCE);
    }
  }

  // One camera controller at a time: the orbit around the selection while there is one, else the free camera
  private applyCameraMode() {
    const orbiting = !!this.spatialEdit?.selection$.value.length;
    if (!this.selectionOrbit || !this.controller || this.selectionOrbit.enabled === orbiting) {
      return;
    }
    if (orbiting && document.pointerLockElement === this.previewCanvas.nativeElement) {
      document.exitPointerLock();
    }
    this.selectionOrbit.enabled = orbiting;
    // activated, the free camera takes the look direction the camera has now
    this.controller.active = !orbiting;
  }

  // The data of the selected handle (its `data_path`), shown under the viewport
  private updateSelectedHandleDetail(handle: SpatialHandle | null) {
    if (!handle?.data_path || !this.resourceId || !this.resourceData) {
      this.selectedHandleDetail$.next(null);
      return;
    }
    let data: any = this.resourceData;
    let schema: BlockSchema | undefined = this.resourceSchema;
    for (const key of handle.data_path.split('/')) {
      data = data?.[key] ?? data?.[+key];
      schema = schema?.fields
        ? schema.fields.find((f: { name: string; schema: BlockSchema }) => f.name === key)?.schema
        : schema?.child_schema;
    }
    this.selectedHandleDetail$.next({
      title: handle.label,
      resource: { id: joinId(this.resourceId, handle.data_path), data, schema, name: '' },
    });
  }

  public placeRendererAtHome(): void {
    this.spatialEdit?.select([]);
    if (this.renderer) {
      this.renderer.camera.position = { x: 0, y: 0, z: 2.5 };
      this.renderer.camera.rotation = Qtrn.lookAt(
        this.renderer.camera.position,
        Pnt3.add(this.renderer.camera.position, Pnt3.Y),
        Pnt3.Z,
      );
    }
    if (this.controller) {
      this.controller.reset();
    }
  }

  public setViewMode(mode: ViewMode): void {
    this.viewModeController?.setViewMode(mode);
    this.cdr.detectChanges();
  }

  ngOnDestroy(): void {
    this.viewModeController?.dispose();
    this.spatialEdit?.dispose();
    this.selectionOrbit?.dispose();
    if (document.pointerLockElement === this.previewCanvas?.nativeElement) {
      document.exitPointerLock();
    }
    this.destroyed$.next();
    this.destroyed$.complete();
  }
}
