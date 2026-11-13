from library.read_blocks import DataBlock
from serializers.base import BaseFileSerializer, DelegateBlockSerializer, PlainBinarySerializer
from .archives import (
    ShpiArchiveSerializer,
    ShppArchiveSerializer,
    WwwwArchiveSerializer,
    SoundBankSerializer,
    BigfArchiveSerializer,
)
from .audios import (
    EacsAudioSerializer,
    FfmpegSupportedAudioSerializer,
    EaSoundBankSerializer,
    EaAudioStreamsSerializer,
    Nfs6Ps2JukeboxSerializer,
    Nfs6Ps2JukeboxTrackSerializer,
)
from .bitmaps import (
    ImageSerializer,
    TargaImageSerializer,
    PsxImageSerializer,
    PaletteSerializer,
    ShpiTextSerializer,
    NfsuTexturePackSerializer,
    Nfs6Ps2TexturePackSerializer,
)
from .fonts import FfnFontSerializer
from .geometries import (
    OripGeometrySerializer,
    OrixGeometrySerializer,
    GeoGeometrySerializer,
    CrpGeometrySerializer,
    Fce3GeometrySerializer,
    Fce4GeometrySerializer,
    EaglModelSerializer,
    Nfs6Ps2CarSerializer,
)
from .json import JsonSerializer, TnfsPsxHorizonInfoSerializer, Nfs3CarPhysicsSerializer, CarFeDataSerializer
from .horizons import EacHorizonSettingsSerializer
from .nfs6_ps2_car_specs import Nfs6Ps2ChunkBundleSerializer
from .ini import IniFileSerializer, BlockJsonSerializer
from .maps import (
    TriMapSerializer,
    TrkMapSerializer,
    FrdMapSerializer,
    Nfs4FrdMapSerializer,
    Nfs6AiPathsSerializer,
    NfsuTrackBundleSerializer,
    Nfs6Ps2TrackBundleSerializer,
)
from .videos import FfmpegSupportedVideoSerializer


def get_serializer(block: DataBlock, data) -> BaseFileSerializer:
    if isinstance(block, Exception):
        raise block
    serializer_class = block.serializer_class()
    if not serializer_class:
        raise NotImplementedError(f'Serializer for resource {block.__class__.__name__} not implemented!')
    return serializer_class()
