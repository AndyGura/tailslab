export const fileFormatIcon = (blockClassStr: string): string => {
  for (const className of blockClassStr.split('__')) {
    if (iconMap[className]) {
      return iconMap[className];
    }
  }
  return fallbackIcon;
};

const iconMap: Record<string, string> = {
  FfnFont: 'text_fields',

  EacImage: 'image',
  TargaImage: 'image',
  PsxImage: 'image',

  EacPalette: 'palette',

  BytesBlock: 'data_object',

  ShpiBlock: 'photo_library',
  ShppBlock: 'photo_library',

  WwwwBlock: 'archive',
  BigfBlock: 'archive',
  C0fbBlock: 'archive',
  RefPackBlock: 'archive',
  Qfs2Block: 'archive',
  Qfs3Block: 'archive',
  EacCompressedBlock: 'archive',

  OripGeometry: 'view_in_ar',
  OrixGeometry: 'view_in_ar',
  GeoGeometry: 'view_in_ar',
  Fce3Geometry: 'view_in_ar',
  Fce4Geometry: 'view_in_ar',
  CrpGeometry: 'view_in_ar',
  NfsuBinGeometry: 'view_in_ar',
  TnfsSaturnCarBundle: 'directions_car',
  TnfsPsxGouraudColors: 'gradient',

  TriMap: 'layers',
  TrkMap: 'layers',
  FrdMap: 'layers',
  MapColFile: 'layers',
  Nfs5WallEdges: 'layers',
  Nfs3SimHeights: 'height',
  Nfs4HeightsSim: 'height',
  Nfs6AiPaths: 'route',
  Nfs3CanAnimation: 'animation',
  Nfs2HorizonInfo: 'wb_twilight',
  Nfs4TrackIni: 'wb_twilight',

  EacsAudioFile: 'audiotrack',
  AsfAudio: 'audiotrack',
  EaAudioStreams: 'audiotrack',
  Nfs6Ps2Jukebox: 'audiotrack',
  Nfs6Ps2JukeboxTrack: 'audiotrack',
  TnfsPsxVagSample: 'audiotrack',
  SoundBank: 'library_music',
  EaSoundBank: 'library_music',
  TnfsPsxPatchBank: 'library_music',
  TnfsPsxVagBank: 'library_music',
  EaMusicMap: 'queue_music',
  Nfs6EngineAudioTable: 'graphic_eq',

  PlayerCarPhysics: 'speed',
  CarAiAndCrashBody: 'speed',
  Nfs2CarPhysics: 'speed',
  Nfs2CarAi: 'speed',
  Nfs2SimTune: 'speed',
  Nfs2TrafficConfig: 'speed',
  Nfs2Personalities: 'speed',
  Nfs3CarPhysics: 'speed',
  Nfs5CarPhysics: 'speed',
  Nfs5CarAi: 'speed',
  IniFile: 'tune',

  TnfsReplay: 'replay',
  Nfs2Replay: 'replay',
  TnfsConfigDat: 'settings',
  EaFieldDescriptions: 'description',
};
const fallbackIcon = 'question_mark';
