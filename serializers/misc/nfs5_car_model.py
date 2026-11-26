"""An NFS5 (Porsche Unleashed) car model as Porsche.exe draws it in a race (nfs-web `decomp/nfs5/Porsche.exe.gzf`,
work files `decomp/nfs5/port-work/car-render/`): which images go onto the car's texture pages, and the data a viewer
needs to draw the car's articles by their state (`nfs5_car_model_info`, the `nfs5Car` key of the export, read by
nfs-three-lib's `Nfs5CarMeshController`).

- The geometry configuration (car+0x56c, 120 slots: 0..59 geometry, 60..119 texture): all 0, then the `.tpg` style
  section `[style<body style + 1>]` (`count` entries `geometry<i>` = slot or `texture<i>` = slot - 60, `type<i>` =
  value; R3DCar_SetBodyStyle 0x437b00), slot 10 = 1 with a race number (record +0x510 >= 0, 0x437b00), the race's
  slots (R3DCar_SetupGeometry 0x43ae50: the convertible top, the driver, the antenna...), then every slot the parts
  set (the record's GEOMCONFIG +0x32c, entries >= 0).
- A car level of detail draws the articles whose base part's slot has the article's value (R3DCarLOD_Build
  0x43c1b0).
- The texture pages are built once, as the model loads (R3DObject_BuildTexturePages 0x442790): each `[fileN.details]
  tpage` page gets its file's FSH images in file order, a later image over an earlier one, each image whose
  `[fileN.<alias>]` section passes (R3DCar_IsImageUsed 0x439c60, `crp_car_is_image_used`), with `mirror=1` a second
  copy at (`mirroroffsetx`, `mirroroffsety`) (0x443f60); the file is the CRP's FSH part or, with `global=k`, the global
  file k of `NFS5_CAR_GLOBAL_FILES`. The paint tints the band coded texels as they are drawn (0x444130,
  `nfs5_paint_band`).
- The materials (`tm` parts) draw with the render methods of the CRP (`htMR` parts, `nfs5_render_method`); the car
  reflections are two of their layers, by a parameter of the material (`nfs5_car_material`)."""

import re
import struct
from configparser import ConfigParser
from typing import Dict, List, Optional, Tuple

# `[fileN.details] global=k`: the FSH file k - 1 of the game's CarModel folder (Porsche.exe 0x443760, table 0x5cdafc)
NFS5_CAR_GLOBAL_FILES = ['shadow.fsh', 'intglass.fsh', 'suit.fsh', 'head.fsh', 'cabrio.fsh']

# `[tpageN.details] bpp` (decimal, default 1555): the page's texel format (0x442790)
NFS5_PAGE_FORMATS = {32: 32, 1555: 1555, 4444: 4444}

NFS5_CAR_MODEL_FORMAT_VERSION = 2

# EAGL layer types of Porsche.exe's car render methods (the layer factory 0x449b70): R3DSpecularTextureLayer
# (0x445520: the specular texture of carcmn.fsh, sphere mapped by the view-space normal), R3DSkyMapTextureLayer
# (0x445b10: the track's `.env` texture projected from above, per road section of the track's `.map`)
NFS5_LAYER_SPECULAR_TEXTURE = 0x8100
NFS5_LAYER_SKY_MAP = 0x8101

# the specular textures of carcmn.fsh by level (nfs5_specular_level): a race's (0x441a10 at 0x441aa1: SPC1, SPC2,
# SPC3 into R3DCar+0x3b8 by 0x440940) and the front end's (FEDU, "FE  ", FESH)
NFS5_SPECULAR_TEXTURES = {'race': ['SPC1', 'SPC2', 'SPC3'], 'frontEnd': ['FEDU', 'FE  ', 'FESH']}


def nfs5_paint_band(alpha: int) -> Optional[int]:
    """The paint band (0..17) of a texel's alpha, or None for an untinted texel (Porsche.exe 0x444130): k = (A + 1) x 20
    >> 8; k 0, 10 and 20 are not tinted, k 1..9 is band 18 - k, k 11..19 band 19 - k. A tinted texel is band colour x
    its red channel >> 8, opaque"""
    k = ((alpha + 1) * 20) >> 8
    if k in (0, 10, 20):
        return None
    return 18 - k if k < 10 else 19 - k


def nfs5_tpg_slot_entries(tpg: ConfigParser, section: str) -> List[Tuple[int, int]]:
    """(slot, value) of the `count` entries of a `.tpg` section (Porsche.exe 0x437b00, 0x439c60): `geometry<i>` (slot
    0..59) or, without it, `texture<i>` + 60; value `type<i>` (default 0)"""
    if not tpg.has_section(section):
        return []
    entries = []
    for i in range(1, tpg.getint(section, 'count', fallback=0) + 1):
        slot = tpg.getint(section, f'geometry{i}', fallback=-1)
        if slot < 0:
            slot = tpg.getint(section, f'texture{i}', fallback=0) + 60
        entries.append((slot, tpg.getint(section, f'type{i}', fallback=0)))
    return entries


def nfs5_style_slots(tpg: ConfigParser, body_style: int = 0, race_number: bool = False) -> Dict[int, int]:
    """The geometry configuration of a body style (0-based: section `[style<body_style + 1>]`), slots not listed 0
    (R3DCar_SetBodyStyle 0x437b00): slot -> value. Slot 10 (the race number decals) = 1 with a race number, when the
    style section exists"""
    section = f'style{body_style + 1}'
    slots = dict(nfs5_tpg_slot_entries(tpg, section))
    if tpg.has_section(section):
        slots[10] = 1 if race_number else 0
    return slots


# R3DCar_SetupGeometry 0x43ae50: the driver's body (slot 9) of the front end's driver 0..7 (table 0x5cd5c4)
NFS5_DRIVER_BODIES = [2, 3, 4, 5, 10, 8, 9, 7]


def nfs5_race_slots(
    tpg: ConfigParser,
    body_style: int = 0,
    driver: Optional[int] = 0,
    cabrio_down: bool = False,
    race_number: bool = False,
    passenger: int = 0,
    tiny_car: bool = False,
) -> Dict[int, int]:
    """The geometry configuration of a car in a race (R3DCar_SetupGeometry 0x43ae50) without parts (the record's
    GEOMCONFIG all -1): the style's (`nfs5_style_slots`), then the convertible top slot 41 = 2 x slot 37 (down) or 2 x
    slot 37 - 1 (up) and slot 37 = 0 (its animated top is the showroom's), the driver (slot 9 its body, 43 the arms
    and legs, 56 the hands; None: an empty car, flag 0x10, slot 9 = 0), slot 42 = 0, slot 59 = the passenger, slot 58
    = the tiny car cheat (the antenna). Not ported: a factory driver mission's own drivers"""
    slots = nfs5_style_slots(tpg, body_style, race_number)
    top = slots.get(37, 0)
    slots[41] = 2 * top if cabrio_down else 2 * top - 1
    slots[37] = 0
    if driver is None:
        slots[9] = 0
    elif 0 <= driver < 8:
        slots[9] = NFS5_DRIVER_BODIES[driver]
        slots[43] = driver // 4 * 2 + 2
        slots[56] = driver // 4 + 1
    else:
        slots[9] = slots[43] = slots[56] = 1
    slots[42] = 0
    slots[59] = passenger
    slots[58] = 1 if tiny_car else 0
    return slots


def crp_car_is_image_used(
    tpg: ConfigParser,
    file_index: int,
    alias: str,
    slots: Dict[int, int],
    night: int = 0,
    skidpad: bool = False,
    factory_mission: bool = False,
) -> bool:
    """Whether a race draws an image of a car's FSH file (1-based `.tpg` file index) onto its texture page (Porsche.exe
    R3DCar_IsImageUsed 0x439c60, with the front end flag 0): by the image's section `[file<N>.<alias>]` (alias without
    trailing spaces), none: drawn; `count` entries: one of them must match the geometry configuration `slots`
    (missing slots 0); `frontend` must be 0 (the showroom's images are 1); `night` must be the track's time of day
    (0x628a28: 0 day); `testdrive`: on the skid pad it must be 1 in a factory driver mission, else 0; elsewhere only 0"""
    section = f'file{file_index}.{alias.rstrip(" ")}'
    if not tpg.has_section(section):
        return True
    used = True
    entries = nfs5_tpg_slot_entries(tpg, section)
    if entries:
        used = any(slots.get(slot, 0) == value for slot, value in entries)
    frontend = tpg.getint(section, 'frontend', fallback=-1)
    if frontend >= 0 and frontend != 0:
        used = False
    image_night = tpg.getint(section, 'night', fallback=-1)
    if image_night >= 0 and image_night != night:
        used = False
    testdrive = tpg.getint(section, 'testdrive', fallback=-1)
    if testdrive >= 0:
        if skidpad:
            if testdrive != (1 if factory_mission else 0):
                used = False
        elif testdrive != 0:
            used = False
    return used


def nfs5_car_file_details(tpg: ConfigParser, file_index: int) -> dict:
    """`[file<N>.details]` of a `.tpg` (1-based): the page, the global file, the mirrored copy (Porsche.exe 0x442790,
    0x443f60)"""
    section = f'file{file_index}.details'
    return {
        'tpage': tpg.getint(section, 'tpage', fallback=0),
        'global': tpg.getint(section, 'global', fallback=0),
        'mirror': tpg.getint(section, 'mirror', fallback=0) != 0,
        'mirrorOffset': [
            tpg.getint(section, 'mirroroffsetx', fallback=0),
            tpg.getint(section, 'mirroroffsety', fallback=0),
        ],
    }


def nfs5_car_pages(tpg: ConfigParser) -> List[dict]:
    """The texture pages of a `.tpg` (Porsche.exe 0x442790): index (0-based), size, texel format (`bpp`), the file drawn
    on it (0-based, the source page's with `sourcetpage`)"""
    num_files = tpg.getint('header', 'numfiles', fallback=0)
    file_of_page = {}
    for f in range(1, num_files + 1):
        page = nfs5_car_file_details(tpg, f)['tpage']
        if page > 0:
            file_of_page[page] = f - 1
    pages = []
    for p in range(1, tpg.getint('header', 'numtpages', fallback=0) + 1):
        section = f'tpage{p}.details'
        source = tpg.getint(section, 'sourcetpage', fallback=p)
        pages.append(
            {
                'index': p - 1,
                'width': tpg.getint(section, 'width', fallback=0),
                'height': tpg.getint(section, 'height', fallback=0),
                'format': NFS5_PAGE_FORMATS.get(tpg.getint(section, 'bpp', fallback=1555), 1555),
                'file': file_of_page.get(source, file_of_page.get(p)),
            }
        )
    return pages


def nfs5_car_packages(packages: Optional[ConfigParser]) -> List[List[int]]:
    """The stripe packages of `packages.ini` (Porsche.exe 0x443760 reads, 0x443db0 applies): per package (0-based, the
    record's `_STRIPEPACKAGE`) the colour (`_COLORCONFIG` index: 0 body, 1 and 2 the accents, 3 the interior) of each
    of the 18 paint bands, `band<k>` (default 0, bands 14 and 15 default 3)"""
    if packages is None:
        return []
    result = []
    for n in range(1, packages.getint('header', 'count', fallback=0) + 1):
        section = f'package{n}'
        result.append(
            [packages.getint(section, f'band{k}', fallback=3 if k in (14, 15) else 0) for k in range(18)]
            if packages.has_section(section)
            else [3 if k in (14, 15) else 0 for k in range(18)]
        )
    return result


def _floats(text: Optional[str], default: List[float]) -> List[float]:
    if not text:
        return default
    try:
        values = [float(x) for x in text.split(',')]
    except ValueError:
        return default
    return values if len(values) == len(default) else default


def nfs5_car_tpg_info(tpg: Optional[ConfigParser]) -> dict:
    """What a viewer needs of a car's `.tpg`: the body styles (`[style<n>]` name, slots, `stripe`), the `[header]` keys
    the race reads (CarModel_LoadBoundingPoints 0x441a10: the driver's camera, the door axis, the extents of the hood,
    trunk, pop-up headlights and moving spoiler; defaults as the exe's), `[damagezones]` as it is and the pages"""
    if tpg is None:
        return {'styles': [], 'header': {}, 'damageZones': {}, 'pages': []}
    styles = []
    numbers = sorted(int(m.group(1)) for m in (re.fullmatch(r'style(\d+)', x) for x in tpg.sections()) if m)
    for n in range(1, (numbers[-1] if numbers else 0) + 1):
        section = f'style{n}'
        styles.append(
            {
                'name': tpg.get(section, 'name', fallback=f'style{n}'),
                'slots': [[slot, value] for slot, value in sorted(nfs5_tpg_slot_entries(tpg, section))],
                'stripe': tpg.getint(section, 'stripe', fallback=0) != 0,
            }
        )
    get = (lambda key: tpg.get('header', key, fallback=None)) if tpg.has_section('header') else (lambda key: None)

    def number(key: str, default: float) -> float:
        try:
            return float(get(key)) if get(key) is not None else default
        except ValueError:
            return default

    header = {
        'driverCamPos': _floats(get('drivercampos'), [-0.36, 0.4, -0.25]),
        'driverCamRot': _floats(get('drivercamrot'), [0.0, 0.0, 0.0]),
        'doorAxis': _floats(get('dooraxis'), [0.0, 1.0, 0.0]),
        'noRoof': number('noroof', 0) != 0,
        'hoodExtent': number('hoodextent', 0.15),
        'trunkExtent': number('trunkextent', -0.15),
        'headlightExtent': number('headlightextent', 0.0),
        'moveSpoilerExtent': number('movespoilerextent', 0.0),
    }
    damage_zones = {}
    if tpg.has_section('damagezones'):
        for key, value in tpg.items('damagezones'):
            try:
                damage_zones[key] = float(value)
            except ValueError:
                pass
    return {'styles': styles, 'header': header, 'damageZones': damage_zones, 'pages': nfs5_car_pages(tpg)}


def nfs5_damage_zones(part_data: dict) -> Dict[int, int]:
    """Vertex index -> damage zone of a `zd` part's data ([CrpDamageZonesData], Porsche.exe 0x43e390)"""
    zones = {}
    indices = part_data['vertex_indices']
    for zone in part_data['zones']:
        for vertex in indices[zone['first_index'] : zone['first_index'] + zone['num_vertices']]:
            zones[vertex] = zone['zone']
    return zones


def _point(p: dict) -> List[float]:
    return [p['x'], p['y'], p['z']]


def nfs5_car_article_info(index: int, name: str, parts: List[Tuple[str, dict]]) -> dict:
    """An article's entry of `nfs5Car.articles`: the base part's car data (R3DCarLOD_Build 0x43c1b0, R3DCarLOD_Draw
    0x43c830), its levels of detail, transformations (`rt` parts: 16 floats by level, CRP axes, row vectors with the
    translation in 12..14) and light glares (effect type 5, R3DCarLOD_DrawGlares 0x43d800)"""
    base = next((d['data'] for n, d in parts if n == 'CrpBasePart'), None)
    info = {'index': index, 'name': name}
    if base is not None:
        tag = bytes(base['tag'])
        info.update(
            {
                'flags': base['flags'],
                'slot': tag[0],
                'value': tag[1],
                'order': tag[2],
                'id': tag[3],
                'wheel': base['car_wheel'],
                'pivot': base['car_pivot'],
                'frames': base['car_frames'],
                'animation': base['car_animation'],
                'drawFlags': base['car_draw_flags'],
                'light': base['light'],
                'cockpit': base['car_cockpit'] != 0,
                'insideOnly': base['car_inside_only'] != 0,
            }
        )
    info['lods'] = sorted({d['part_info']['lod'] for n, d in parts if n == 'VertexPart'})
    info['transforms'] = {
        str(d['part_info']['lod']): [float(x) for x in d['data']] for n, d in parts if n == 'TransformationPart'
    }
    glares = []
    for n, d in parts:
        if n != 'EffectPart' or d['data']['unk0'] != 5:
            continue
        e = d['data']
        glares.append(
            {
                'position': _point(e['position']),
                'width': _point(e['width']),
                'height': _point(e['height']),
                'depth': _point(e['depth']),
                'glowColor': e['glow_color'],
                'sourceColor': e['source_color'],
                'mirrored': (e['mirror'] & 8) != 0,
                'mirrorLight': e['mirror_light'],
                'nightFlare': e['night_flare'] != 0,
            }
        )
    if glares:
        info['glares'] = glares
    return info


def nfs5_render_method(data: bytes) -> dict:
    """An EAGL render method of a CRP (an `htMR` common part, registered by name by MaterialTable_Load 0x44a770,
    compiled per material by 0x44bf70 for the render caps): the name (16 bytes), then the counts of groups, layers
    and constant data blocks (+0x10, +0x14, +0x18), the groups (16 bytes each from +0x1c: first layer, layer count,
    caps mask, a pass kind), the layers (16 bytes each: key = tag << 16 | group, layer type, binding, stream mask),
    the data blocks (16 bytes each: key, offset, size) and their data. A group is compiled when its caps mask is 0 or
    shares a bit with the render caps (`nfs5_render_caps`). `keys`: the layers' keys, sorted, once each: a material's
    texture layers and parameters name their layer by its position in it (0x44a220)"""
    name = data[:16].split(b'\0')[0].decode('latin-1')
    num_groups, num_layers, num_blocks = struct.unpack_from('<3I', data, 0x10)
    groups = []
    for i in range(num_groups):
        start, count, caps, kind = struct.unpack_from('<4I', data, 0x1C + 16 * i)
        groups.append({'start': start, 'count': count, 'caps': caps, 'kind': kind})
    layers_at = 0x1C + 16 * num_groups
    layers = []
    for i in range(num_layers):
        key, layer_type, binding, mask = struct.unpack_from('<4I', data, layers_at + 16 * i)
        group = next((g for g in groups if g['start'] <= i < g['start'] + g['count']), None)
        layers.append(
            {'key': key, 'type': layer_type, 'binding': binding, 'mask': mask, 'caps': group and group['caps']}
        )
    return {'name': name, 'groups': groups, 'layers': layers, 'keys': sorted({x['key'] for x in layers})}


def nfs5_material_parameters(data: bytes) -> Dict[int, bytes]:
    """The parameters of a `tm` material (`MaterialPartData`, 312 bytes): +8 the counts (low 16 bits the texture
    layers, 0x2c bytes each from +0x20, high 16 bits the parameters, 16 bytes each after them: key, offset, size),
    the parameter data after those (MaterialTable_Load 0x44a770). Key (the position in the render method's `keys`) ->
    data"""
    counts = struct.unpack_from('<I', data, 8)[0]
    num_textures, num_parameters = counts & 0xFFFF, counts >> 16
    at = 0x20 + num_textures * 0x2C
    data_at = at + num_parameters * 16
    parameters = {}
    for i in range(num_parameters):
        key, offset, size = struct.unpack_from('<3I', data, at + 16 * i)
        parameters[key] = data[data_at + offset : data_at + offset + size]
    return parameters


def nfs5_car_material(index: int, data: bytes, methods: Dict[str, dict]) -> dict:
    """A `tm` material's entry of `nfs5Car.materials`: its render method (`desc`), texture page (`tex_page_index`)
    and the reflection layers of its method, `specular` (R3DSpecularTextureLayer) and `skyMap`
    (R3DSkyMapTextureLayer), each {`param`: the float the material binds to the layer (0x445520 / 0x445b10 pick the
    texture of level `nfs5_specular_level(param)` by it; 0 when unbound), `passes`: the caps mask of each group the
    layer is in}, None when the method has no such layer"""
    method_name = data[0x10:0x20].split(b'\0')[0].decode('latin-1')
    method = methods.get(method_name)
    parameters = nfs5_material_parameters(data)

    def layer(layer_type: int) -> Optional[dict]:
        if method is None:
            return None
        found = [x for x in method['layers'] if x['type'] == layer_type]
        if not found:
            return None
        param = 0.0
        for x in found:
            value = parameters.get(method['keys'].index(x['key']))
            if value is not None and len(value) == 4:
                param = struct.unpack('<f', value)[0]
                break
        return {'param': round(param, 6), 'passes': sorted({x['caps'] or 0 for x in found})}

    return {
        'index': index,
        'method': method_name,
        'page': struct.unpack_from('<I', data, 0x28)[0],
        'specular': layer(NFS5_LAYER_SPECULAR_TEXTURE),
        'skyMap': layer(NFS5_LAYER_SKY_MAP),
    }


def nfs5_car_model_info(
    articles: List[dict],
    tpg: Optional[ConfigParser],
    packages: Optional[ConfigParser],
    materials: Optional[List[dict]] = None,
) -> dict:
    """The `nfs5Car` key of a car export (`.meta` and the OBJ's `_extra.json`)"""
    return {
        'formatVersion': NFS5_CAR_MODEL_FORMAT_VERSION,
        'articles': articles,
        **nfs5_car_tpg_info(tpg),
        'packages': nfs5_car_packages(packages),
        'materials': materials or [],
    }
