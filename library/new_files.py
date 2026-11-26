"""The formats the GUI's "New file" dialog creates: the block's `new_data` written under a default file name the loader
recognises. Every format here is tested by `test/library/test_new_files.py` (create, write, read back as the same
block, the same bytes): a format whose empty file the loader does not recognise, or which does not read back, stays
out of the list"""

from dataclasses import dataclass
from importlib import import_module
from io import BytesIO
from typing import Callable, List, Optional, Tuple

from library.utils.id import path_to_name

# the dialog's games, in this order: (id, name)
TNFS_PC = 'tnfs_pc'
TNFS_3DO = 'tnfs_3do'
TNFS_PSX = 'tnfs_psx'
TNFS_SATURN = 'tnfs_saturn'
NFS2 = 'nfs2'
NFS3 = 'nfs3'
NFS4 = 'nfs4'
NFS5 = 'nfs5'
NFS6 = 'nfs6'
NFSU = 'nfsu'
NEW_FILE_GAMES = [
    (TNFS_PC, 'TNFS (PC)'),
    (TNFS_3DO, 'TNFS (3DO)'),
    (TNFS_PSX, 'TNFS (PlayStation)'),
    (TNFS_SATURN, "Over Drivin' GT-R (Saturn)"),
    (NFS2, 'NFS 2 / NFS 2 SE'),
    (NFS3, 'NFS 3 Hot Pursuit'),
    (NFS4, 'NFS 4 High Stakes'),
    (NFS5, 'NFS 5 Porsche Unleashed'),
    (NFS6, 'NFS 6 Hot Pursuit 2 (PC)'),
    (NFSU, 'NFSU / U2 / Most Wanted'),
]

# the sections of a game's formats, in this order
CARS = 'Cars'
TRACKS = 'Tracks'
IMAGES = 'Images and fonts'
AUDIO = 'Audio'
ARCHIVES = 'Archives'
GAME_DATA = 'Game data'
NEW_FILE_KINDS = [CARS, TRACKS, IMAGES, AUDIO, ARCHIVES, GAME_DATA]

EAC_COMPRESSED = 'resources.eac.archives.EacCompressedBlock'


@dataclass(frozen=True)
class NewFileFormat:
    id: str
    # the games the format is listed in
    games: Tuple[str, ...]
    # the section it is listed in
    kind: str
    label: str
    # what the file is in the game, one sentence
    description: str
    # default name of the new file
    file_name: str
    # `module.Class` of the file's block
    block: str
    # class name of the compressed data, `block` being a compressed block
    compressed: Optional[str] = None
    # the folder the loader recognises the file in only (`Cars/<car>`)
    folder: Optional[str] = None
    # builds the new file's data from the block (an archive with its items), else the block's `new_data`
    template: Optional[Callable] = None

    def block_class(self) -> type:
        module, name = self.block.rsplit('.', 1)
        return getattr(import_module(module), name)

    @property
    def data_class_name(self) -> str:
        """Class name of the block holding the data: the compressed one, or the file's"""
        return self.compressed or self.block.rsplit('.', 1)[1]

    def new(self):
        """(block, data) of a new file"""
        block = self.block_class()()
        if self.template:
            return block, self.template(block)
        if self.compressed:
            return block, block.new_data({'choice_index': block.get_choice_index_by_class_name(self.compressed)})
        return block, block.new_data()

    def as_dict(self) -> dict:
        data_class = self.block_class()
        if self.compressed:
            data_class = next(type(b) for b in data_class().possible_blocks if type(b).__name__ == self.compressed)
        return {
            'id': self.id,
            'games': list(self.games),
            'kind': self.kind,
            'label': self.label,
            'description': self.description,
            'file_name': self.file_name,
            'folder': self.folder,
            # the GUI picks the format icon by it, as by a schema's `block_class_mro`
            'block_class_mro': '__'.join(x.__name__ for x in data_class.mro() if x.__name__ not in ['object', 'ABC']),
        }


def _format(id, games, kind, label, file_name, block, description, **kwargs) -> NewFileFormat:
    return NewFileFormat(id, tuple(games), kind, label, description, file_name, block, **kwargs)


def archive_data(block, items: list) -> dict:
    """New data of the archive `block` holding `items`: (class name of the item's block, its data; None: the block's
    new data)"""
    data = block.new_data()
    entry_block = block.field_blocks_map['children'].child
    data['children'] = []
    for class_name, item in items:
        entry = entry_block.new_data(
            {'item': {'choice_index': block.item_block.get_choice_index_by_class_name(class_name)}}
        )
        if item is not None:
            entry['item']['data'] = item
        data['children'].append(entry)
    return data


def _shpi(directory: str = None) -> dict:
    from resources.eac.archives import ShpiBlock

    data = ShpiBlock().new_data()
    if directory:
        data['shpi_dir'] = directory
    return data


def _cfm_template(block) -> dict:
    """TNFS car: high-poly model, its textures, low-poly model, its textures (directory WRAP, as the game's)"""
    return archive_data(
        block,
        [('OripGeometry', None), ('ShpiBlock', _shpi('WRAP')), ('OripGeometry', None), ('ShpiBlock', _shpi('WRAP'))],
    )


def _fam_template(block) -> dict:
    """TNFS track: background (terrain textures) and foreground (prop textures) archives of one image archive each,
    the skybox image archive, the props archive (an archive of model + textures per prop) without props"""
    return archive_data(
        block,
        [
            ('WwwwBlock', archive_data(block, [('ShpiBlock', None)])),
            ('WwwwBlock', archive_data(block, [('ShpiBlock', None)])),
            ('ShpiBlock', None),
            ('WwwwBlock', archive_data(block, [])),
        ],
    )


NEW_FILE_FORMATS: List[NewFileFormat] = [
    # TNFS PC
    _format(
        'pbs',
        [TNFS_PC],
        CARS,
        'Car physics',
        'Untitled.PBS',
        EAC_COMPRESSED,
        'Player car physics: engine, gearbox, grip, brakes (compressed, SIMDATA/CARSPECS).',
        compressed='PlayerCarPhysics',
    ),
    _format(
        'pdn',
        [TNFS_PC],
        CARS,
        'Car AI and crash body',
        'Untitled.PDN',
        EAC_COMPRESSED,
        "The car's opponent speeds and crash body (compressed, SIMDATA/CARFAMS).",
        compressed='CarAiAndCrashBody',
    ),
    _format(
        'cfm',
        [TNFS_PC],
        CARS,
        'Car model (CFM)',
        'Untitled.CFM',
        'resources.eac.archives.WwwwBlock',
        'High-poly and low-poly 3D models of a car with their textures (SIMDATA/CARFAMS); import an OBJ into each model.',
        template=_cfm_template,
    ),
    _format(
        'fam',
        [TNFS_PC],
        TRACKS,
        'Track textures and props (FAM)',
        'Untitled.FAM',
        'resources.eac.archives.WwwwBlock',
        'Background and foreground textures, skybox and 3D props of a track (SIMDATA/ETRACKFM/<TRI name>_001.FAM).',
        template=_fam_template,
    ),
    _format(
        'tri',
        [TNFS_PC],
        TRACKS,
        'Track',
        'Untitled.TRI',
        'resources.eac.maps.TriMap',
        'Road spline, terrain and props of a track (SIMDATA/MISC).',
    ),
    _format(
        'rpl',
        [TNFS_PC],
        GAME_DATA,
        'Replay',
        'Untitled.RPL',
        'resources.eac.replays.TnfsReplay',
        'A saved race replay.',
    ),
    _format(
        'config_dat',
        [TNFS_PC],
        GAME_DATA,
        'Player records',
        'CONFIG.DAT',
        'resources.eac.configs.TnfsConfigDat',
        'Player name, best times and top speeds of every track, unlocks (GAMEDATA/CONFIG/CONFIG.DAT).',
    ),
    _format(
        'asf',
        [TNFS_PC],
        AUDIO,
        'Music (ASF / AS4)',
        'Untitled.ASF',
        'resources.eac.audios.AsfAudio',
        'A music stream of the menus and races (FRONTEND/MUSIC).',
    ),
    # TNFS 3DO
    _format(
        'bigspecsfam',
        [TNFS_3DO],
        CARS,
        'Car physics',
        'Untitled.BigSpecsFam',
        'resources.eac.car_specs.Tnfs3doCarPhysics',
        'Player car physics of the 3DO version (DriveData/CarData).',
    ),
    # TNFS PlayStation
    _format(
        'psh',
        [TNFS_PSX],
        IMAGES,
        'Image archive (PSH)',
        'Untitled.PSH',
        'resources.eac.archives.ShppBlock',
        'Car and track textures, horizons.',
    ),
    _format(
        'vh',
        [TNFS_PSX],
        AUDIO,
        'Sound bank patches',
        'Untitled.VH',
        'resources.eac.psx_audios.TnfsPsxPatchBank',
        'Which sample of the .VB plays at which pitch and volume.',
    ),
    _format(
        'vb',
        [TNFS_PSX],
        AUDIO,
        'Sound bank samples',
        'Untitled.VB',
        'resources.eac.psx_audios.TnfsPsxVagBank',
        'The samples of a sound bank, played by its .VH patches.',
    ),
    _format(
        'vag',
        [TNFS_PSX],
        AUDIO,
        'Sound sample',
        'Untitled.VAG',
        'resources.eac.psx_audios.TnfsPsxVagSample',
        'A single PlayStation SPU ADPCM sample.',
    ),
    # Over Drivin' GT-R
    _format(
        'all',
        [TNFS_SATURN],
        CARS,
        'Car bundle',
        'Untitled.ALL',
        'resources.eac.tnfs_saturn.TnfsSaturnCarBundle',
        'Physics, textures and cockpit pictures of a car (CARS/<car>.ALL).',
    ),
    # NFS 2 / NFS 2 SE
    _format(
        'geo',
        [NFS2],
        CARS,
        'Car 3D model',
        'Untitled.GEO',
        'resources.eac.geometries.GeoGeometry',
        'The parts of a car model (CARMODEL/PC).',
    ),
    _format(
        'nfs2_car_physics',
        [NFS2],
        CARS,
        'Car physics (SE)',
        'PCAR.DAT',
        'resources.eac.car_specs.Nfs2CarPhysics',
        'Car physics, an item of CARDATA.VIV (SIM/CARDATA/P<car>.DAT).',
    ),
    _format(
        'nfs2_car_physics_qda',
        [NFS2],
        CARS,
        'Car physics, compressed (SE)',
        'PCAR.QDA',
        EAC_COMPRESSED,
        'Compressed copy of P<car>.DAT (SIM/CARDATA/P<car>.QDA).',
        compressed='Nfs2CarPhysics',
    ),
    _format(
        'nfs2_car_ai_qda',
        [NFS2],
        CARS,
        'Car AI (compressed)',
        'CAR0.QDA',
        EAC_COMPRESSED,
        'Compressed car AI (NFS 2 SIM/AICARDT/<car>.QDA).',
        compressed='Nfs2CarAi',
    ),
    _format(
        'col',
        [NFS2],
        TRACKS,
        'Track data (COL)',
        'Untitled.COL',
        'resources.eac.maps.nfs_common.MapColFile',
        'Texture table, track props and the road line of the physics (TR<nn>.COL).',
    ),
    _format(
        'hrz',
        [NFS2],
        TRACKS,
        'Horizon (software renderer)',
        'TR01.HRZ',
        'resources.eac.horizons.Nfs2HorizonInfo',
        'Horizon settings of a track (TRACKS/PC/TR<nn>.HRZ).',
    ),
    _format(
        'simtune',
        [NFS2],
        GAME_DATA,
        'Driving models tuning (SE)',
        'SIMTUNE.DAT',
        'resources.eac.car_specs.Nfs2SimTune',
        'Tuning of the simulation and arcade driving models, an item of CARDATA.VIV.',
    ),
    _format(
        'simtune_qda',
        [NFS2],
        GAME_DATA,
        'Driving models tuning, compressed (SE)',
        'SIMTUNE.QDA',
        EAC_COMPRESSED,
        'Compressed copy of SIMTUNE.DAT (CARMODEL/PC/SIMTUNE.QDA).',
        compressed='Nfs2SimTune',
    ),
    _format(
        'trafcfg',
        [NFS2],
        GAME_DATA,
        'Traffic and AI settings (SE)',
        'TRAFCFG.DAT',
        'resources.eac.car_specs.Nfs2TrafficConfig',
        'Traffic, opponent catch-up and AI driving settings (SIM/AI/TRAFCFG.DAT).',
    ),
    _format(
        'prsonal',
        [NFS2],
        GAME_DATA,
        'AI personalities (SE)',
        'PRSONAL.DAT',
        'resources.eac.car_specs.Nfs2Personalities',
        'Driving personalities of the opponents (SIM/AI/PRSONAL.DAT).',
    ),
    _format(
        'rpy',
        [NFS2],
        GAME_DATA,
        'Replay (SE)',
        'replay.rpy',
        'resources.eac.replays.Nfs2Replay',
        'The race setup and the controls of the last saved race, in the game folder.',
    ),
    # NFS 3
    _format(
        'fce3',
        [NFS3],
        CARS,
        '3D model (FCE)',
        'Untitled.FCE',
        'resources.eac.geometries.Fce3Geometry',
        'A car or prop model: car.fce of a car.viv, the cones and cop cars of GameData/Render/PC.',
    ),
    _format(
        'simhts',
        [NFS3],
        TRACKS,
        'Slice heights',
        'SIMHTS.DAT',
        'resources.eac.maps.nfs3.Nfs3SimHeights',
        'Ceiling height of every road slice of a track.',
    ),
    # NFS 4
    _format(
        'heights_sim',
        [NFS4],
        TRACKS,
        'Slice heights',
        'heights.sim',
        'resources.eac.maps.nfs4.Nfs4HeightsSim',
        'Ceiling height of every road slice of a track.',
        folder='Data/Tracks/<track>',
    ),
    _format(
        'tr_ini',
        [NFS4],
        TRACKS,
        'Track sky and fog',
        'Tr.ini',
        'resources.eac.horizons.Nfs4TrackIni',
        'Horizon strip, clouds, fog and sun of a track.',
        folder='Data/Tracks/<track>',
    ),
    # NFS 5
    _format(
        'nfs5_sim',
        [NFS5],
        CARS,
        'Car physics',
        'Untitled.sim',
        'resources.eac.car_specs.Nfs5CarPhysics',
        'Physics of a car spec.',
        folder='GameData/Simulation/CarData',
    ),
    _format(
        'ais',
        [NFS5],
        CARS,
        'Car AI',
        'Untitled.ais',
        'resources.eac.car_specs.Nfs5CarAi',
        'Corner look-ahead and target speeds of the AI (Simulation/AICarData).',
    ),
    _format(
        'edg',
        [NFS5],
        TRACKS,
        'Track wall edges',
        'Untitled.edg',
        'resources.eac.maps.nfs5.Nfs5WallEdges',
        'The walls along a track (GameData/Track/<track>.edg).',
    ),
    # NFS 6
    *[
        _format(
            f'nfs6_{file_name.lower().replace(".", "_")}',
            [NFS6],
            CARS,
            label,
            file_name,
            f'resources.eac.nfs6_car_specs.{block}',
            description,
            folder=folder,
        )
        for file_name, label, block, folder, description in [
            ('car.ini', 'Car physics', 'Nfs6CarIni', 'Cars/<car>', 'The car physics as the player drives it.'),
            (
                'vehicle.ini',
                'Car looks',
                'Nfs6VehicleIni',
                'Cars/<car>',
                'Shading, skins and paint swatches, visual damage, wheels, light glows.',
            ),
            ('bounds.ini', 'Car bounds', 'Nfs6BoundsIni', 'Cars/<car>', "The car's bounding boxes."),
            (
                'geomdata.ini',
                'Car geometry settings',
                'Nfs6GeomDataIni',
                'Cars/<car>',
                'Levels of detail and damage zone of every geometry of the car model.',
            ),
            ('damage.ini', 'Car damage', 'Nfs6DamageIni', 'Cars/<car>', 'Damage settings (the game does not read it).'),
            (
                'lod.ini',
                'Car levels of detail',
                'Nfs6LodIni',
                'Cars/<car>',
                'Empty in every car (the game does not read it).',
            ),
            ('Cars.ini', 'Car list', 'Nfs6CarsIni', 'Cars', 'The cars of the game.'),
            ('Cameras.ini', 'Race cameras', 'Nfs6CamerasIni', 'Cars', 'The race cameras, the same for every car.'),
            (
                'RearView.ini',
                'Rear view mirror',
                'Nfs6RearViewIni',
                'Cars',
                'Rear view mirror settings (the game does not read it).',
            ),
            ('reflection.ini', 'Car reflections', 'Nfs6ReflectionIni', 'Cars', 'The dynamic car reflections.'),
        ]
    ],
    _format(
        'aipaths',
        [NFS6],
        TRACKS,
        'Track AI paths',
        'aipaths.dat',
        'resources.eac.maps.nfs6.Nfs6AiPaths',
        'Road graph of the AI cars and flight paths of the police helicopter (levelNN/aipaths.dat).',
    ),
    # NFS Underground, U2, Most Wanted
    _format(
        'nfsu_geometry',
        [NFSU],
        CARS,
        'Car 3D models',
        'GEOMETRY.BIN',
        'resources.blackbox.geometries.nfsu.NfsuBinGeometry',
        'The models of a car (CARS/<car>/GEOMETRY.BIN).',
    ),
    # formats of several games
    _format(
        'fsh',
        [TNFS_PC, NFS2, NFS3, NFS4, NFS5, NFS6],
        IMAGES,
        'FSH image archive',
        'Untitled.FSH',
        'resources.eac.archives.ShpiBlock',
        'Images: textures, menus, dashboards, horizons.',
    ),
    _format(
        'qfs',
        [TNFS_PC, NFS2, NFS3, NFS4],
        IMAGES,
        'QFS image archive',
        'Untitled.QFS',
        EAC_COMPRESSED,
        'A compressed FSH image archive: track and car textures.',
        compressed='ShpiBlock',
    ),
    _format(
        'ffn',
        [TNFS_PC, NFS2, NFS3, NFS4, NFS5, NFS6],
        IMAGES,
        'Font',
        'Untitled.FFN',
        'resources.eac.fonts.FfnFont',
        'A bitmap font of the menus and the HUD.',
    ),
    _format(
        'bnkl',
        [NFS2, NFS3, NFS4, NFS5, NFS6],
        AUDIO,
        'Sound bank',
        'Untitled.BNK',
        'resources.eac.archives.EaSoundBank',
        'Engine, horn and collision sounds (BNKl).',
    ),
    _format(
        'music_map',
        [NFS2, NFS3],
        AUDIO,
        'Interactive music map',
        'Untitled.MAP',
        'resources.eac.audios.EaMusicMap',
        'Which part of the .MUS / .ASF music plays next (PFDx).',
    ),
    _format(
        'can',
        [NFS2, NFS3, NFS4],
        TRACKS,
        'Animation path',
        'Untitled.CAN',
        'resources.eac.maps.nfs3.Nfs3CanAnimation',
        'The path of an animated track object (TR<nn><k>.CAN).',
    ),
    _format(
        'viv',
        [TNFS_PSX, NFS2, NFS3, NFS4, NFS5, NFS6],
        ARCHIVES,
        'VIV archive',
        'Untitled.VIV',
        'resources.eac.archives.BigfBlock',
        'An archive of game files (BIGF): car.viv, CARDATA.VIV, the PlayStation Z<car>.VSM.',
    ),
    _format(
        'c0fb',
        [TNFS_PSX, NFS5],
        ARCHIVES,
        'VIV archive (C0FB)',
        'Untitled.VIV',
        'resources.eac.archives.C0fbBlock',
        'A compact BIGF archive: Skyline Memorial car archives, NFS 5 tr<nn>a.viv.',
    ),
    _format(
        'des',
        [NFS2, NFS5],
        GAME_DATA,
        'Field descriptions',
        'Untitled.DES',
        'resources.eac.field_descriptions.EaFieldDescriptions',
        "The developers' description of the fields of a .DAT file.",
    ),
]


def new_file_formats() -> dict:
    """The dialog's games and sections in order, and the formats"""
    return {
        'games': [{'id': id, 'name': name} for id, name in NEW_FILE_GAMES],
        'kinds': NEW_FILE_KINDS,
        'formats': [f.as_dict() for f in NEW_FILE_FORMATS],
    }


def new_file_format(format_id: str) -> NewFileFormat:
    """The format of the id, ignoring case"""
    for fmt in NEW_FILE_FORMATS:
        if fmt.id == format_id.lower():
            return fmt
    raise ValueError(f'Unsupported format: {format_id}')


def data_class_name(block, data) -> str:
    """Class name of the block holding the data, through compressed and auto-detected wrappers"""
    while isinstance(data, dict) and 'choice_index' in data:
        block = block.possible_blocks[data['choice_index']]
        data = data['data']
    return type(block).__name__


def read_as(path: str, bts: bytes) -> Optional[str]:
    """Class name of the data the loader reads the bytes of the file `path` as, None when it does not read them"""
    from library.context import ReadContext
    from library.loader import probe_block_class

    buffer = BytesIO(bts)
    # as the file `require_file` reads: some blocks look at its name
    buffer.name = path
    try:
        block = probe_block_class(buffer, path, len(bts))()
        return data_class_name(
            block, block.unpack(ReadContext(buffer), name=path_to_name(path), read_bytes_amount=len(bts))
        )
    except Exception:
        return None


def new_file_bytes(format_id: str, path: str) -> Tuple[NewFileFormat, bytes]:
    """A new file of the format, written at `path`: the format and the file bytes. Raises when the loader would not
    read the file at that path as the format, telling the name or the folder it needs"""
    fmt = new_file_format(format_id)
    block, data = fmt.new()
    bts = block.pack(data)
    if read_as(path, bts) != fmt.data_class_name:
        where = f'in a "{fmt.folder}" folder, named like "{fmt.file_name}"' if fmt.folder else f'as "{fmt.file_name}"'
        raise ValueError(f'This {fmt.label} file ({fmt.file_name}) would not open at {path}. Save it {where}')
    return fmt, bts
