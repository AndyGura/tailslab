import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ComponentRef,
  Input,
  OnDestroy,
  Type,
  ViewChild,
} from '@angular/core';
import { DataBlockUIDirective } from './data-block-ui.directive';
import { GuiComponent } from './gui.component';
import { MainService } from '../../services/main.service';
import { Subject, Subscription } from 'rxjs';
import { BlockData, BlockSchema, Resource, ResourceError, schemaEquals } from './types';
import { CompoundBlockUiComponent } from './library/compound.block-ui/compound.block-ui.component';
import { NumberBlockUiComponent } from './library/number.block-ui/number.block-ui.component';
import { StringBlockUiComponent } from './library/string.block-ui/string.block-ui.component';
import { ArrayBlockUiComponent } from './library/array.block-ui/array.block-ui.component';
import { DelegateBlockUiComponent } from './library/delegate.block-ui/delegate.block-ui.component';
import { TrailingOptionalBlockUiComponent } from './library/trailing-optional.block-ui/trailing-optional.block-ui.component';
import { EnumBlockUiComponent } from './library/enum.block-ui/enum.block-ui.component';
import { BinaryBlockUiComponent } from './library/binary.block-ui/binary.block-ui.component';
import { SubByteCompoundBlockUiComponent } from './library/sub-byte-compound.block-ui/sub-byte-compound.block-ui.component';
import { AngleBlockUiComponent } from './eac/angle.block-ui/angle.block-ui.component';
import { ChangesService } from '../../services/changes.service';
import { ArchiveBlockUiComponent } from './library/archive.block-ui/archive.block-ui.component';
import { isLazyStub } from '../../utils/lazy';
import { MatIcon } from '@angular/material/icon';
import { MatProgressSpinner } from '@angular/material/progress-spinner';

@Component({
  selector: 'app-editor',
  templateUrl: './editor.component.html',
  styleUrls: ['./editor.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatIcon, MatProgressSpinner, DataBlockUIDirective],
})
export class EditorComponent implements OnDestroy {
  // Built on first use: the container editors import EditorComponent back, so they are not defined yet with this class
  private static dataBlockComponents?: { [key: string]: Type<GuiComponent> };
  static get DATA_BLOCK_COMPONENTS_MAP(): { [key: string]: Type<GuiComponent> } {
    return (EditorComponent.dataBlockComponents ??= {
      // basic primitives
      IntegerBlock: NumberBlockUiComponent,
      DecimalBlock: NumberBlockUiComponent,
      UTF8Block: StringBlockUiComponent,
      NullTerminatedUTF8Block: StringBlockUiComponent,
      EnumByteBlock: EnumBlockUiComponent,
      BytesBlock: BinaryBlockUiComponent,

      // basic containers
      ArchiveBlock: ArchiveBlockUiComponent,
      ArrayBlock: ArrayBlockUiComponent,
      SubByteArrayBlock: ArrayBlockUiComponent,
      CompoundBlock: CompoundBlockUiComponent,
      SubByteCompoundBlock: SubByteCompoundBlockUiComponent,
      DelegateBlock: DelegateBlockUiComponent,
      TrailingOptionalBlock: TrailingOptionalBlockUiComponent,

      // misc
      AngleBlock: AngleBlockUiComponent,
      IntegerAngleBlock: AngleBlockUiComponent,
    });
  }

  // Bespoke editors, each loaded on first use: they pull three.js, charts... out of the initial bundle
  static readonly LAZY_DATA_BLOCK_COMPONENTS_MAP: { [key: string]: () => Promise<Type<GuiComponent>> } = {
    // common
    TargaImage: () =>
      import('./common/targa-image.block-ui/targa-image.block-ui.component').then(m => m.TargaImageBlockUiComponent),

    // Common classic Need For Speed blocks
    EacImage: () => import('./eac/image.block-ui/image.block-ui.component').then(m => m.ImageBlockUiComponent),
    EacPalette: () => import('./eac/palette.block-ui/palette.block-ui.component').then(m => m.PaletteBlockUiComponent),
    // PSX images (SHPP) and their CLUTs
    PsxImage: () =>
      import('./eac/psx-image.block-ui/psx-image.block-ui.component').then(m => m.PsxImageBlockUiComponent),
    PsxClut: () => import('./eac/psx-clut.block-ui/psx-clut.block-ui.component').then(m => m.PsxClutBlockUiComponent),
    FfnFont: () => import('./eac/font.block-ui/font.block-ui.component').then(m => m.FontBlockUiComponent),
    // EA audio streams: NFS2 SE, NFS5, NFS6 music
    EaAudioStreams: () =>
      import('./eac/eacs-audio.block-ui/eacs-audio.block-ui.component').then(m => m.EacsAudioBlockUiComponent),

    // TNFS-specific blocks
    OripGeometry: () =>
      import('./eac/orip-geometry.block-ui/orip-geometry.block-ui.component').then(m => m.OripGeometryBlockUiComponent),
    OrixGeometry: () =>
      import('./eac/orip-geometry.block-ui/orip-geometry.block-ui.component').then(m => m.OripGeometryBlockUiComponent),
    EacsAudioFile: () =>
      import('./eac/eacs-audio.block-ui/eacs-audio.block-ui.component').then(m => m.EacsAudioBlockUiComponent),
    AsfAudio: () =>
      import('./eac/eacs-audio.block-ui/eacs-audio.block-ui.component').then(m => m.EacsAudioBlockUiComponent),
    SoundBank: () =>
      import('./eac/soundbank.block-ui/soundbank.block-ui.component').then(m => m.SoundbankBlockUiComponent),
    TriMap: () => import('./eac/track-map.block-ui/track-map.block-ui.component').then(m => m.TrackMapBlockUiComponent),
    PlayerCarPhysics: () =>
      import('./eac/player-car-physics.block-ui/player-car-physics.block-ui.component').then(
        m => m.PlayerCarPhysicsBlockUiComponent,
      ),
    CarAiAndCrashBody: () =>
      import('./eac/car-ai-and-crash-body.block-ui/car-ai-and-crash-body.block-ui.component').then(
        m => m.CarAiAndCrashBodyBlockUiComponent,
      ),

    // NFS2-specific blocks
    GeoGeometry: () =>
      import('./eac/geo-geometry.block-ui/geo-geometry.block-ui.component').then(m => m.GeoGeometryBlockUiComponent),
    TrkMap: () => import('./eac/track-map.block-ui/track-map.block-ui.component').then(m => m.TrackMapBlockUiComponent),
    Nfs2CarPhysics: () =>
      import('./eac/nfs2-car-physics.block-ui/nfs2-car-physics.block-ui.component').then(
        m => m.Nfs2CarPhysicsBlockUiComponent,
      ),
    Nfs2CarAi: () =>
      import('./eac/nfs2-car-ai.block-ui/nfs2-car-ai.block-ui.component').then(m => m.Nfs2CarAiBlockUiComponent),
    Nfs2SimTune: () =>
      import('./eac/nfs2-sim-tune.block-ui/nfs2-sim-tune.block-ui.component').then(m => m.Nfs2SimTuneBlockUiComponent),
    EaFieldDescriptions: () =>
      import('./eac/ea-field-descriptions.block-ui/ea-field-descriptions.block-ui.component').then(
        m => m.EaFieldDescriptionsBlockUiComponent,
      ),

    // NFS3-specific blocks
    FrdMap: () => import('./eac/track-map.block-ui/track-map.block-ui.component').then(m => m.TrackMapBlockUiComponent),
    Fce3Geometry: () =>
      import('./eac/fce-geometry.block-ui/fce-geometry.block-ui.component').then(m => m.FceGeometryBlockUiComponent),
    Nfs3CarPhysics: () =>
      import('./eac/nfs3-car-physics.block-ui/nfs3-car-physics.block-ui.component').then(
        m => m.Nfs3CarPhysicsBlockUiComponent,
      ),
    Nfs3CarFeData: () =>
      import('./eac/car-fedata.block-ui/car-fedata.block-ui.component').then(m => m.CarFeDataBlockUiComponent),
    Nfs4CarFeData: () =>
      import('./eac/car-fedata.block-ui/car-fedata.block-ui.component').then(m => m.CarFeDataBlockUiComponent),

    // NFS4-specific blocks
    Fce4Geometry: () =>
      import('./eac/fce-geometry.block-ui/fce-geometry.block-ui.component').then(m => m.FceGeometryBlockUiComponent),
    Nfs4FrdMap: () =>
      import('./eac/track-map.block-ui/track-map.block-ui.component').then(m => m.TrackMapBlockUiComponent),

    // NFS5-specific blocks
    CrpGeometry: () =>
      import('./eac/crp-geometry.block-ui/crp-geometry.block-ui.component').then(m => m.CrpGeometryBlockUiComponent),
    Nfs5CarPhysics: () =>
      import('./eac/nfs5-car-physics.block-ui/nfs5-car-physics.block-ui.component').then(
        m => m.Nfs5CarPhysicsBlockUiComponent,
      ),
    Nfs5CarParts: () =>
      import('./eac/nfs5-car-parts.block-ui/nfs5-car-parts.block-ui.component').then(
        m => m.Nfs5CarPartsBlockUiComponent,
      ),
    Nfs5CarAi: () =>
      import('./eac/nfs5-car-ai.block-ui/nfs5-car-ai.block-ui.component').then(m => m.Nfs5CarAiBlockUiComponent),
    Nfs5Cars: () =>
      import('./eac/nfs5-cars.block-ui/nfs5-cars.block-ui.component').then(m => m.Nfs5CarsBlockUiComponent),
    Nfs5FactoryMissions: () =>
      import('./eac/nfs5-career.block-ui/nfs5-factory-missions.block-ui.component').then(
        m => m.Nfs5FactoryMissionsBlockUiComponent,
      ),
    Nfs5Tournaments: () =>
      import('./eac/nfs5-career.block-ui/nfs5-tournaments.block-ui.component').then(
        m => m.Nfs5TournamentsBlockUiComponent,
      ),

    // NFS6-specific blocks
    Nfs6AiPaths: () =>
      import('./eac/track-map.block-ui/track-map.block-ui.component').then(m => m.TrackMapBlockUiComponent),
    NfsuTrackBundle: () =>
      import('./eac/track-map.block-ui/track-map.block-ui.component').then(m => m.TrackMapBlockUiComponent),
    EaglModel: () =>
      import('./eac/eagl-model.block-ui/eagl-model.block-ui.component').then(m => m.EaglModelBlockUiComponent),
    // NFS HP2 PC car spec files (and any typed INI file)
    IniFile: () =>
      import('./common/ini-file.block-ui/ini-file.block-ui.component').then(m => m.IniFileBlockUiComponent),
    Nfs6CarIni: () =>
      import('./eac/nfs6-car-ini.block-ui/nfs6-car-ini.block-ui.component').then(m => m.Nfs6CarIniBlockUiComponent),
    Nfs6EngineAudioTable: () =>
      import('./eac/nfs6-engine-audio.block-ui/nfs6-engine-audio.block-ui.component').then(
        m => m.Nfs6EngineAudioBlockUiComponent,
      ),

    // NFS6 PS2-specific blocks
    Nfs6Ps2TrackBundle: () =>
      import('./eac/track-map.block-ui/track-map.block-ui.component').then(m => m.TrackMapBlockUiComponent),
    Nfs6Ps2CarGeometry: () =>
      import('./blackbox/nfs6-ps2-car.block-ui/nfs6-ps2-car.block-ui.component').then(
        m => m.Nfs6Ps2CarBlockUiComponent,
      ),
    Nfs6Ps2CarTypeInfos: () =>
      import('./blackbox/nfs6-ps2-car-types.block-ui/nfs6-ps2-car-types.block-ui.component').then(
        m => m.Nfs6Ps2CarTypesBlockUiComponent,
      ),
    Nfs6Ps2JukeboxTrack: () =>
      import('./eac/eacs-audio.block-ui/eacs-audio.block-ui.component').then(m => m.EacsAudioBlockUiComponent),

    // NFSU-specific blocks
    NfsuBinGeometry: () =>
      import('./blackbox/nfsu-bin-geometry.block-ui/nfsu-bin-geometry.block-ui.component').then(
        m => m.NfsuBinGeometryBlockUiComponent,
      ),
  };

  _resourceId?: string;
  _resourceName?: string;
  _resourceSchema?: BlockSchema;
  _resourceData?: BlockData;

  @Input()
  public set resourceOrError(value: Resource | ResourceError | null) {
    this._resourceId = value?.id;
    this._resourceName = value?.name;
    this.resourceError = null;
    this._componentLoadResource = null;
    if (value?.data?.error_class !== undefined) {
      this.resourceError = { class: value?.data?.error_class, message: value?.data?.error_text };
      this._resourceSchema = undefined;
      this._resourceData = undefined;
      return;
    }

    if (value && isLazyStub(value.data)) {
      // unloaded lazy part: show the spinner, render once the backend has parsed it (the stub is filled in place)
      this._resourceData = undefined;
      this._lazyResource = value;
      this.mainService.ensureLoaded(value.id, value.data).then(
        () => {
          if (this._lazyResource === value) {
            this._lazyResource = null;
            this.resourceOrError = value;
          }
        },
        () => {
          if (this._lazyResource === value) {
            this._lazyResource = null;
            this.resourceError = { message: 'Failed to load ' + value.id };
            this.cdr.markForCheck();
          }
        },
      );
      this.cdr.markForCheck();
      return;
    }
    this._lazyResource = null;

    if (this._resourceSchema !== value?.schema && value?.schema?.block_class_mro) {
      const lookup = EditorComponent.findComponent(value.schema.block_class_mro);
      if (lookup instanceof Promise) {
        // bespoke editor not loaded yet: show the spinner, render once its chunk is there
        this._resourceData = undefined;
        this._componentLoadResource = value;
        lookup.then(
          () => {
            if (this._componentLoadResource === value) {
              this._componentLoadResource = null;
              this.resourceOrError = value;
            }
          },
          err => {
            if (this._componentLoadResource === value) {
              this._componentLoadResource = null;
              this.resourceError = { message: 'Failed to load the editor: ' + err };
              this.cdr.markForCheck();
            }
          },
        );
        this.cdr.markForCheck();
        return;
      }
    }

    this._resourceData = value?.data;
    if (this._resourceSchema !== value?.schema) {
      let reuseComponent =
        !!this._component &&
        value &&
        this._resourceSchema &&
        value.schema?.block_class_mro === this._resourceSchema.block_class_mro;
      this._resourceSchema = value?.schema;

      if (!reuseComponent) {
        this.dataBlockUiHost.viewContainerRef.clear();
      }
      if (this._resourceSchema?.block_class_mro) {
        if (!reuseComponent) {
          const component = EditorComponent.findComponent(this._resourceSchema.block_class_mro) as
            Type<GuiComponent> | undefined;
          if (!component) {
            this.resourceError = {
              message: 'UI not implemented for ' + this._resourceSchema.block_class_mro.replace(/__/g, ' &rarr; '),
            };
            this._resourceSchema = undefined;
            this._resourceData = undefined;
            return;
          }
          if (this._componentChangedSub) {
            this.componentSet$.next();
          }
          this._component = this.dataBlockUiHost.viewContainerRef.createComponent(component);
          this.componentSet$.next();
        }
        if (!reuseComponent || !schemaEquals(this._component!.instance.resourceSchema, this._resourceSchema)) {
          this._component!.setInput('resourceSchema', this._resourceSchema);
        }
      }
    }
    if (this._component) {
      this._component.setInput('resourceId', this._resourceId);
      this._component.setInput('resourceName', this._resourceName);
      this._component.setInput('resourceDescription', this._resourceDescription);
      this._component.setInput('hideName', this._hideName);
      this._component.setInput('hideBlockActions', this._hideBlockActions);
      this._component.setInput('disabled', this._disabled);
      // data last: a component that fails on it must still get the inputs above (e.g. a shown top-level name)
      this._component.setInput('resourceData', this._resourceData);
      this.cdr.markForCheck();
    }
  }

  // the resource whose lazy part is being loaded now, if any
  _lazyResource: Resource | ResourceError | null = null;
  // the resource whose editor component is being loaded now, if any
  _componentLoadResource: Resource | ResourceError | null = null;

  // lazy editors already loaded, by class name of LAZY_DATA_BLOCK_COMPONENTS_MAP
  private static readonly loadedComponents: { [key: string]: Type<GuiComponent> } = {};

  // The editor of the first class of the MRO having one, a promise while that is a lazy editor not loaded yet
  static findComponent(blockClassMro: string): Type<GuiComponent> | Promise<Type<GuiComponent>> | undefined {
    for (const className of blockClassMro.split('__')) {
      const component = EditorComponent.DATA_BLOCK_COMPONENTS_MAP[className];
      if (component) {
        return component;
      }
      const loader = EditorComponent.LAZY_DATA_BLOCK_COMPONENTS_MAP[className];
      if (loader) {
        return (
          EditorComponent.loadedComponents[className] ??
          loader().then(loaded => (EditorComponent.loadedComponents[className] = loaded))
        );
      }
    }
    return undefined;
  }

  _resourceDescription?: string;
  @Input()
  set resourceDescription(value: string | undefined) {
    this._resourceDescription = value;
    if (this._component) {
      this._component.setInput('resourceDescription', value);
    }
  }

  _hideName?: boolean;
  @Input()
  set hideName(value: boolean | undefined) {
    this._hideName = value;
    if (this._component) {
      this._component.setInput('hideName', value);
    }
  }

  _hideBlockActions?: boolean;
  @Input()
  set hideBlockActions(value: boolean | undefined) {
    this._hideBlockActions = value;
    if (this._component) {
      this._component.setInput('hideBlockActions', value);
    }
  }

  _disabled?: boolean;
  @Input()
  set disabled(value: boolean | undefined) {
    this._disabled = value;
    if (this._component) {
      this._component.setInput('disabled', value);
    }
  }

  @ViewChild(DataBlockUIDirective, { static: true }) dataBlockUiHost!: DataBlockUIDirective;

  _component: ComponentRef<GuiComponent> | null = null;
  _componentChangedSub: Subscription | null = null;

  private destroyed$: Subject<void> = new Subject<void>();
  private componentSet$: Subject<void> = new Subject<void>();

  resourceError: { class?: string; message: string } | null = null;

  constructor(
    readonly mainService: MainService,
    readonly changes: ChangesService,
    readonly cdr: ChangeDetectorRef,
  ) {}

  ngOnDestroy(): void {
    this.destroyed$.next();
    this.destroyed$.complete();
  }
}
