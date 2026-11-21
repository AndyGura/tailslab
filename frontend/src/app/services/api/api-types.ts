export type GeneralConfig = {
  blender_executable: string;
  ffmpeg_executable: string;
  print_blender_log: boolean;
  recent_files: string[];
  show_hidden_fields: boolean;
  lazy_loading: boolean;
  file_cache_size: number;
  show_orip_import_guide: boolean;
  // the game the New file dialog opened at last
  new_file_game: string;
};

// a format of the New file dialog (`library/new_files.py`)
export type NewFileFormat = {
  id: string;
  // ids of the games it is listed in
  games: string[];
  // the section it is listed in
  kind: string;
  label: string;
  // what the file is in the game
  description: string;
  // default name of the new file
  file_name: string;
  // the folder the file is recognised in only (`Cars/<car>`)
  folder: string | null;
  // of the file's data block, for its icon
  block_class_mro: string;
};

// the New file dialog's games and sections, in order, and its formats
export type NewFileFormats = {
  games: { id: string; name: string }[];
  kinds: string[];
  formats: NewFileFormat[];
};

export type ExecutableKind = 'blender' | 'ffmpeg';

export type ExecutableDetectionResult = {
  success: boolean;
  path: string | null;
  message: string;
};

export type ConversionConfig = {
  multiprocess_processes_count: number;
  input_path: string;
  output_path: string;
  images__save_image_positions: boolean;
  images__save_palettes: boolean;
  images__save_mipmaps: boolean;
  images__save_embedded_palette: boolean;
  images__save_texts: boolean;
  maps__save_as_chunked: boolean;
  maps__tnfs_chunks_per_file: number;
  maps__save_spherical_skybox_texture: boolean;
  maps__add_props_to_obj: boolean;
  maps__save_all_lods: boolean;
  geometry__save_obj: boolean;
  geometry__save_blend: boolean;
  geometry__export_to_gg_web_engine: boolean;
};

export type ConversionPresets = {
  // user-defined presets, "no preset" (default settings) is null
  presets: string[];
  selected: string | null;
};
