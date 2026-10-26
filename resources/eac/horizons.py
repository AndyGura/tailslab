"""
Sky ("horizon") settings of the tracks of NFS2 SE (3D accelerated version), NFS3 and NFS4, all read by EA Canada's
horizon code of the same lineage (`hrzsku.c`): a band around the camera of an EARTH Gouraud gradient, a SKY Gouraud
gradient whose bottom colour turns from the sun colour to the opposite colour around the turn, a horizon pixmap of 8
strips, a cloud dome and (NFS3, NFS4) a sun sprite. `library/utils/eac_horizon_to_spherical.py` says how the games
draw them. Also the NFS2 / NFS2 SE software renderer's `TR<nn>.HRZ` (other values, other code).

The values are kept as the text of the file; `parse_*` functions give them as named settings, in the units the files
use.
"""

import re
from typing import Dict, List, NamedTuple, Optional, Tuple

from library.read_blocks import DeclarativeCompoundBlock, UTF8Block

Rgb = Tuple[int, int, int]


def _whole_file(ctx):
    return ctx.read_bytes_remaining


def hrz_numbers(text: str) -> List[int]:
    """The numbers of an `.HRZ` file in order, as the games read them (NFS3 `FUN_004be020`, NFS2 SE `FUN_00470ec0`):
    characters that are not part of a number are skipped, a `/` skips everything up to the next `/` (so `/* ... */`
    comments, numbers in them included), a number is an optional `-` and digits"""
    numbers = []
    i = 0
    while i < len(text):
        c = text[i]
        if c == '/':
            end = text.find('/', i + 1)
            i = len(text) if end < 0 else end + 1
            continue
        match = re.match(r'-?\d+', text[i:])
        if match:
            numbers.append(int(match.group(0)))
            i += len(match.group(0))
        else:
            i += 1
    return numbers


def _rgb(values, i) -> Rgb:
    return tuple(values[i : i + 3])


class _HrzText(DeclarativeCompoundBlock):
    class Fields(DeclarativeCompoundBlock.Fields):
        text = (
            UTF8Block(length=(_whole_file, 'the whole file')),
            {'description': 'The settings text: C comments (`/* ... */`) and comma separated numbers'},
        )

    def serializer_class(self):
        from serializers import EacHorizonSettingsSerializer

        return EacHorizonSettingsSerializer

    def parse(self, text: str):
        raise NotImplementedError


class Nfs2SeHorizonSettings(NamedTuple):
    """`3TR<nn>.HRZ` of NFS2 SE (3D accelerated renderer `nfs2sea.exe`), values in file order (`Hrz_ReadHorizonData`
    0x42e910)"""

    cloud_dome_offset: int
    cloud_dome_height: int
    black_horizon: int
    mirror: int
    radius: int
    angle_degrees: int
    flat_projection_distance: int
    base_y: int
    gouraud_height: int
    gouraud_middle: int
    pixmap_top: int
    pixmap_bottom: int
    earth_top_color: Rgb
    earth_bottom_color: Rgb
    sky_top_color: Rgb
    sun_color: Rgb
    opposite_sun_color: Rgb

    def as_dict(self) -> dict:
        return {k: list(v) if isinstance(v, tuple) else v for k, v in self._asdict().items()}


def parse_nfs2se_horizon_settings(text: str) -> Optional[Nfs2SeHorizonSettings]:
    """Settings of an NFS2 SE `3TR<nn>.HRZ`, None when it has fewer than the 27 values the game reads"""
    v = hrz_numbers(text)
    if len(v) < 27:
        return None
    return Nfs2SeHorizonSettings(*v[:12], _rgb(v, 12), _rgb(v, 15), _rgb(v, 18), _rgb(v, 21), _rgb(v, 24))


class Nfs2SeHorizonInfo(_HrzText):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Sky of an NFS2 SE track for the 3D accelerated renderer, '
            '`GAMEDATA/TRACKS/SE/3TR<nn>.HRZ`, read by nfs2sea.exe `Hrz_ReadHorizonData` (0x42e910, '
            '`c:\\nfs2se\\game\\3rash\\hrzsku.c`; nfs2sen.exe, the software renderer, reads `TR<nn>.HRZ` instead). '
            'Text with C comments, 27 numbers in this order: cloud dome offset and height (the dome of `CLD<track>` '
            'of `SKY.FSH`: y = offset + height * cos(2 pi r / 4000) at horizontal distance r from the camera, a 13 x '
            '13 grid from -1000 to 800 in steps of 150 around it), black horizon flag (1: the screen is cleared black, '
            'nothing else drawn), mirror flag (sectors 8..15 of the ring show strips 7..0 mirrored), radius of the '
            'ring, rotation angle in degrees (ring point k at heading angle + k * 22.5 degrees, clockwise from +Z '
            'seen from above), flat projection distance D (every ring point is projected as if at depth D: a world '
            'height h is at screen height f * h / D), base y (bottom of the band, relative to the eye), Gouraud '
            'height (top of the band = base + height), Gouraud middle (EARTH from base to base + middle, SKY above '
            'it), pixmap top and bottom (the horizon strips: the first 8 images of `TR<nn>0.QFS`, shorter strips end '
            'lower), all offsets from base and turned into fractions of the height with 16.16 integer maths, then '
            'the colours (r, g, b 0..255): EARTH top, EARTH base, SKY top (also the clear colour above the band), '
            'SKY base at the sun and opposite to it (ring vertex k gets sun + (opposite - sun) * k / 8 for k = 0..7 '
            'and vertex 15 - k the same). See `library/utils/eac_horizon_to_spherical.py`',
        }

    def parse(self, text: str):
        return parse_nfs2se_horizon_settings(text)


class Nfs2HorizonSettings(NamedTuple):
    """`TR<nn>.HRZ` of the NFS2 / NFS2 SE software renderer (`nfs2sen.exe` `hrzsku.c` of `game\\vga`), values in file
    order as the comments of the files name them. Not verified in the executable"""

    black_horizon: int
    mirror: int
    radius: int
    angle_degrees: int
    flat_projection_distance: int
    base_y: int
    horizon_height: int
    pixmap_base_percent: int
    flat_sky_color: Rgb
    horizon_base_color: Rgb
    depth_cueing_distances: Tuple[int, int, int, int]
    depth_cueing_light: Tuple[int, int, int, int]
    color_system: int
    color: Rgb

    def as_dict(self) -> dict:
        return {k: list(v) if isinstance(v, tuple) else v for k, v in self._asdict().items()}


def parse_nfs2_horizon_settings(text: str) -> Optional[Nfs2HorizonSettings]:
    """Settings of an NFS2 software renderer `TR<nn>.HRZ`, None when it has fewer than its 26 values"""
    v = hrz_numbers(text)
    if len(v) < 26:
        return None
    return Nfs2HorizonSettings(*v[:8], _rgb(v, 8), _rgb(v, 11), tuple(v[14:18]), tuple(v[18:22]), v[22], _rgb(v, 23))


class Nfs2HorizonInfo(_HrzText):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Sky of an NFS2 / NFS2 SE track for the software renderer, '
            '`GAMEDATA/TRACKS/PC/TR<nn>.HRZ` (nfs2sen.exe `c:\\nfs2se\\game\\vga\\hrzsku.c` builds the name '
            '`%sTr%02d.hrz`). Text with C comments, 26 numbers named by the comments of the files: black horizon '
            'flag, mirror flag, radius, rotation angle in degrees, distance for the flat projection (<= radius), base '
            'y of the flat shaded area (world offset), height of the horizon (offset from base), pixmap base '
            '(percentage of the height), flat shaded sky colour (r, g, b), horizon base colour, 4 depth cueing '
            'distances (0..1100), 4 depth cueing light values (0..15), colour system (0 rgb, 1 hsv) and a colour. '
            'The converter reads these names from the comments only: the software renderer is not ported, so this '
            'file does not make a sky texture',
        }

    def parse(self, text: str):
        return parse_nfs2_horizon_settings(text)


class Nfs3FogRegion(NamedTuple):
    start_color: Rgb
    start_density: int
    apex_color: Rgb
    apex_density: int
    end_color: Rgb
    end_density: int
    before_slice: int
    center_slice: int
    after_slice: int


class Nfs3HorizonSettings(NamedTuple):
    """`3TR<nn>.HRZ` of NFS3 (and its `N` night, `W` weather, `NW` variants), values in file order
    (nfs3.exe 0x478340)"""

    fog_color: Rgb
    fog_density: int
    fog_pixmap_effect_percent: int
    fog_regions: Tuple[Nfs3FogRegion, ...]
    cloud_type: int
    fog_clouds: int
    has_lightning: int
    lightning_chance: int
    cloud_visual_height: int
    cloud_dome_offset: int
    cloud_dome_height: int
    cloud_bright: int
    cloud_variance: int
    cloud_nimbus_percent: int
    wind_speed: int
    wind_direction: int
    black_horizon: int
    mirror: int
    radius: int
    angle_degrees: int
    has_pixmap: int
    base_y: int
    gouraud_height: int
    gouraud_middle: int
    pixmap_top: int
    pixmap_bottom: int
    earth_top_color: Rgb
    earth_bottom_color: Rgb
    sky_top_color: Rgb
    sun_color: Rgb
    opposite_sun_color: Rgb
    weather: Tuple[int, ...]
    ambient_percent: Rgb

    def as_dict(self) -> dict:
        def plain(value):
            if isinstance(value, tuple) and hasattr(value, '_asdict'):
                return {k: plain(v) for k, v in value._asdict().items()}
            if isinstance(value, tuple):
                return [plain(x) for x in value]
            return value

        return {k: plain(v) for k, v in self._asdict().items()}


def parse_nfs3_horizon_settings(text: str) -> Optional[Nfs3HorizonSettings]:
    """Settings of an NFS3 `3TR<nn>*.HRZ`, None when it has fewer values than the game reads"""
    v = hrz_numbers(text)
    if len(v) < 6:
        return None
    region_count = max(0, v[5])
    i = 6 + region_count * 15
    if len(v) < i + 45:
        return None
    regions = tuple(
        Nfs3FogRegion(
            _rgb(v, j), v[j + 3], _rgb(v, j + 4), v[j + 7], _rgb(v, j + 8), v[j + 11], v[j + 12], v[j + 13], v[j + 14]
        )
        for j in range(6, i, 15)
    )
    return Nfs3HorizonSettings(
        _rgb(v, 0),
        v[3],
        v[4],
        regions,
        *v[i : i + 22],
        _rgb(v, i + 22),
        _rgb(v, i + 25),
        _rgb(v, i + 28),
        _rgb(v, i + 31),
        _rgb(v, i + 34),
        tuple(v[i + 37 : i + 45]),
        _rgb(v, i + 45) if len(v) >= i + 48 else (100, 100, 100),
    )


class Nfs3HorizonInfo(_HrzText):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Sky, fog and weather of an NFS3 track, `GameData/Tracks/TRK<nnn>/3TR<nn>.HRZ` '
            '(day; `N` night, `W` weather, `NW` night with weather), read by nfs3.exe 0x478340. Text with C comments, '
            'numbers in this order: fog colour (r, g, b) and density (%), effect of the fog on the pixmap (%, 1..100: '
            'without hardware fog the EARTH colours and the white of the pixmap strips are mixed with the fog colour '
            'by it), number of dynamic fog regions, per region 15 numbers (start r, g, b, density; apex r, g, b, '
            'density; end r, g, b, density; before, centre and after slice), cloud type (0 none, 1 additive, 2 blend), '
            'fog clouds flag, has lightning, lightning chance (% per ticks), cloud visual height (the texture scrolls '
            'one tile when the camera moves this far), cloud dome offset and height (the game multiplies the height '
            'by 3: y = offset + 3 * height * cos(2 pi r / 12000) on a 13 x 13 grid from -3000 to 2400 in steps of '
            '450, one texture tile per grid cell), cloud bright, variance (the brightness of each grid vertex is '
            'bright minus a random value below variance, smoothed), nimbus effect (%, truncated to 0 or 1, so only '
            '100 counts: lowers '
            'bright vertices by up to 1.5 * height), wind speed (mph) and direction (degrees), black horizon flag, '
            'mirror flag, radius R of the horizon, rotation angle in degrees, has a pixmap (the strips: the first 8 images '
            'of `TR<nn>0.QFS`), base y (relative to the eye), Gouraud height, Gouraud middle, pixmap top and bottom '
            '(offsets from base), colours (r, g, b): EARTH top, EARTH base, SKY top, SKY base at the sun and opposite '
            'to it, 8 weather values (type, start slice, end slice, fade, stay time on, fade time off, stay time off, '
            'fade time on, in ticks) and the ambient light (R, G, B %). The sun sprite is set by the text of the '
            '`SUN*` images of `SKY.FSH` (`A<azimuth degrees> B<degrees> R<size / 10>` and the words `ROTATE`, '
            '`NOADD`, `INFRONT`). See `library/utils/eac_horizon_to_spherical.py`',
        }

    def parse(self, text: str):
        return parse_nfs3_horizon_settings(text)


def _ini_float(text: str) -> float:
    match = re.match(r'\s*[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?', text)
    return float(match.group(0)) if match else 0.0


def _ini_int(text: str) -> int:
    match = re.match(r'\s*[-+]?\d+', text)
    return int(match.group(0)) if match else 0


def _ini_rgb(text: str) -> Rgb:
    numbers = [int(x) for x in re.findall(r'-?\d+', text)[:3]]
    return tuple(numbers + [0] * (3 - len(numbers)))


# key: (section, kind, default) of the Tr.ini keys the sky code of nfs4.exe reads (0x4c70a0)
NFS4_SKY_KEYS = {
    'hrzShouldDrawBlack': ('strip', 'int', 0),
    'hrzMirror': ('strip', 'int', 0),
    'hrzHasPMX': ('strip', 'int', 0),
    'hrzBottomYOff': ('strip', 'float', 0.0),
    'hrzGouraudHeight': ('strip', 'float', 0.0),
    'hrzGouraudMiddle': ('strip', 'float', 0.0),
    'hrzPmxTop': ('strip', 'float', 0.0),
    'hrzPmxBottom': ('strip', 'float', 0.0),
    'hrzSunColor': ('strip', 'rgb', (0, 0, 0)),
    'hrzOppositeSunColor': ('strip', 'rgb', (0, 0, 0)),
    'hrzEarthTopColor': ('strip', 'rgb', (0, 0, 0)),
    'hrzEarthBotColor': ('strip', 'rgb', (0, 0, 0)),
    'hrzSkyTopColor': ('strip', 'rgb', (0, 0, 0)),
    'hrzfRadius': ('strip', 'float', 0.0),
    'hrzAngle': ('strip', 'float', 0.0),
    'cloudType': ('clouds', 'int', 0),
    'cloudBright': ('clouds', 'int', 0),
    'cloudVariance': ('clouds', 'int', 0),
    'cloudNimbus': ('clouds', 'float', 0.0),
    'cloudFog': ('clouds', 'int', 0),
    'cloudVisualHeight': ('clouds', 'int', 0),
    'windSpeed': ('clouds', 'int', 0),
    'windDir': ('clouds', 'int', 0),
    'cloudYOffset': ('clouds', 'float', 0.0),
    'cloudHeight': ('clouds', 'float', 0.0),
    'cloudUscale': ('clouds', 'float', 1.0),
    'cloudVscale': ('clouds', 'float', 1.0),
    'fogColor': ('fog', 'rgb', (0, 0, 0)),
    'fogDensity': ('fog', 'int', 0),
    'fogHorizon': ('fog', 'float', 0.0),
    'hasSun': ('sun', 'int', 0),
    'angleTheta': ('sun', 'float', 0.0),
    'angleRho': ('sun', 'float', 0.0),
    'radius': ('sun', 'float', 0.0),
    'rotates': ('sun', 'int', 0),
    'additive': ('sun', 'int', 0),
    'inFront': ('sun', 'int', 0),
}


class Nfs4SkySettings(NamedTuple):
    """The sky keys of an NFS4 `Tr.ini` (`[strip]`, `[clouds]`, `[fog]`, `[sun]`), as nfs4.exe 0x4c70a0 reads them
    (`GetPrivateProfileString` and `sscanf`: `%d`, `%f`, `[%d,%d,%d]`), with its clamps: cloud type 0..2, cloud
    bright 0..255, variance 0..bright, nimbus 0..1, cloud fog 0..1, visual height >= 0, wind speed >= 0, wind
    direction 0..360. Keys missing in the file keep the defaults"""

    hrzShouldDrawBlack: int
    hrzMirror: int
    hrzHasPMX: int
    hrzBottomYOff: float
    hrzGouraudHeight: float
    hrzGouraudMiddle: float
    hrzPmxTop: float
    hrzPmxBottom: float
    hrzSunColor: Rgb
    hrzOppositeSunColor: Rgb
    hrzEarthTopColor: Rgb
    hrzEarthBotColor: Rgb
    hrzSkyTopColor: Rgb
    hrzfRadius: float
    hrzAngle: float
    cloudType: int
    cloudBright: int
    cloudVariance: int
    cloudNimbus: float
    cloudFog: int
    cloudVisualHeight: int
    windSpeed: int
    windDir: int
    cloudYOffset: float
    cloudHeight: float
    cloudUscale: float
    cloudVscale: float
    fogColor: Rgb
    fogDensity: int
    fogHorizon: float
    hasSun: int
    angleTheta: float
    angleRho: float
    radius: float
    rotates: int
    additive: int
    inFront: int

    def as_dict(self) -> dict:
        return {k: list(v) if isinstance(v, tuple) else v for k, v in self._asdict().items()}


def nfs4_ini_sections(text: str) -> Dict[str, Dict[str, str]]:
    """Sections of an NFS4 `.ini` file as `GetPrivateProfileString` sees them: names and keys ignoring case, the
    first of repeated keys, values with their trailing spaces dropped"""
    sections = {}
    current = None
    for line in text.replace('\r', '').split('\n'):
        stripped = line.strip()
        if stripped.startswith('[') and ']' in stripped:
            current = sections.setdefault(stripped[1 : stripped.index(']')].strip().lower(), {})
        elif current is not None and '=' in stripped and not stripped.startswith(';'):
            key, value = stripped.split('=', 1)
            current.setdefault(key.strip().lower(), value.strip())
    return sections


def parse_nfs4_sky_settings(text: str) -> Nfs4SkySettings:
    """The sky settings of the text of an NFS4 `Tr.ini`"""
    sections = nfs4_ini_sections(text)
    values = {}
    for key, (section, kind, default) in NFS4_SKY_KEYS.items():
        raw = sections.get(section, {}).get(key.lower())
        if raw is None or raw == '':
            values[key] = default
        elif kind == 'int':
            values[key] = _ini_int(raw)
        elif kind == 'float':
            values[key] = _ini_float(raw)
        else:
            values[key] = _ini_rgb(raw)
    values['cloudType'] = min(max(values['cloudType'], 0), 2)
    values['cloudBright'] = min(max(values['cloudBright'], 0), 255)
    values['cloudVariance'] = 0 if values['cloudVariance'] < 0 else min(values['cloudVariance'], values['cloudBright'])
    values['cloudNimbus'] = min(max(values['cloudNimbus'], 0.0), 1.0)
    values['cloudFog'] = min(max(values['cloudFog'], 0), 1)
    values['cloudVisualHeight'] = max(values['cloudVisualHeight'], 0)
    values['windSpeed'] = max(values['windSpeed'], 0)
    values['windDir'] = min(max(values['windDir'], 0), 360)
    return Nfs4SkySettings(**values)


class Nfs4TrackIni(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Track settings of NFS4, `Data/Tracks/<track>/Tr.ini` (day; `TrN.ini` night, '
            '`TrW.ini` weather, `TrNW.ini` night with weather), a Windows INI file read by nfs4.exe 0x4c70a0 with '
            '`GetPrivateProfileString`. Sky sections: `[strip]` the horizon band (`hrzShouldDrawBlack`, `hrzMirror`, '
            '`hrzHasPMX`, `hrzBottomYOff` base y relative to the eye, `hrzGouraudHeight`, `hrzGouraudMiddle`, '
            '`hrzPmxTop`, `hrzPmxBottom` offsets from the base, colours `[r,g,b]` `hrzSunColor`, '
            '`hrzOppositeSunColor`, `hrzEarthTopColor`, `hrzEarthBotColor`, `hrzSkyTopColor`, `hrzfRadius` and '
            '`hrzAngle` in turns: NFS3 `3TR<nn>.HRZ` values under names, the strips are `HDC0`..`HDC7` of `sky.qfs`); '
            '`[clouds]` (`cloudType` 0 none, 1 additive, 2 blend; `cloudBright`, `cloudVariance`, `cloudNimbus` '
            "0..1, `cloudFog`, `cloudVisualHeight`, `windSpeed`, `windDir`, `cloudYOffset`, `cloudHeight` (NFS3's "
            'dome height already multiplied by 3), `cloudUscale` / `cloudVscale` texture repeats per grid cell); '
            '`[fog]` (`fogColor`, `fogDensity`, `fogHorizon`, `fogNumRegions`, regions in `[fog region <n>]`); '
            '`[sun]` (`hasSun`, `angleTheta` azimuth and `angleRho` in turns: direction (cos theta, cos rho, '
            'sin theta), `radius` of the sprite, `rotates`, `additive`, `inFront` drawn after the clouds). Other '
            'sections: `[lightning]`, `[weather]`, `[light]`, `[special]`, `[track glows]`. See '
            '`library/utils/eac_horizon_to_spherical.py`',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        text = (UTF8Block(length=(_whole_file, 'the whole file')), {'description': 'The INI text'})

    def serializer_class(self):
        from serializers import EacHorizonSettingsSerializer

        return EacHorizonSettingsSerializer

    def parse(self, text: str):
        return parse_nfs4_sky_settings(text)


def hrz_block_class(text_start: bytes, file_name: str):
    """The block of an `.HRZ` file: NFS3 files start with the fog colour comment, NFS2 SE 3D ones with the cloud
    dome, software renderer ones with the black horizon flag"""
    head = text_start.decode('utf-8', errors='replace').lower()
    if 'fog' in head:
        return Nfs3HorizonInfo
    if 'cloud' in head:
        return Nfs2SeHorizonInfo
    return Nfs2HorizonInfo
