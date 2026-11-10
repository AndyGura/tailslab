"""The road network of an NFS5 (Porsche Unleashed) track, as Porsche.exe builds it from the CRP's road spline (nfs-web
`decomp/nfs5/Porsche.exe.gzf`; C port of the same functions in nfs-web `src/nfs5/nfs5-physics/src/world_query.c`).

The slices of "DmiS" are cut into sections by the slice counts of "TmiS" (Spline_Build 0x480140); a section is cut
again where the end of another one lies within 16 m of it (Spline_SplitSections 0x480900); section ends within 16 m
of each other make a junction (Spline_BuildJunctions 0x480b40). A section is driven from its first slice to its last
one. The race length is the longest walk from junction 0 along the sections, through the junctions
(Spline_MeasureJunctions 0x481910 / Spline_WalkJunction 0x4819e0): the race progress (Spline_RaceFraction 0x416290)
goes from junction 0 to the junction at its end, the finish, or back to junction 0 on a circuit. The HUD map
(HudMap_BuildPoints 0x432230, HudMap_Draw 0x433690) draws every section alike, each end linked to its junction centre.

Squared distances are compared in doubles here (floats in the game): every game track gets the junction count of its
`.jnc` file"""

import math
from typing import Dict, List, Optional, Tuple

# (squared, xz) distance within which a section end splits another section or joins a junction
NFS5_JUNCTION_REACH2 = 256.0
# at most so many ends per junction
NFS5_JUNCTION_MAX_ENDS = 8

# a section end: (section index, 0 first slice / 1 last slice)
SectionEnd = Tuple[int, int]


def _d2(a: dict, b: dict) -> float:
    return (a['x'] - b['x']) ** 2 + (a['z'] - b['z']) ** 2


def nfs5_spline_sections(positions: List[dict], lengths: List[int]) -> List[List[int]]:
    """Sections of the road spline, [first slice, last slice] each: consecutive runs of the "TmiS" slice counts (one
    section without "TmiS" or with less than 2 counts, Porsche.exe 0x480140), split where another section ends next
    to them (0x480900: the nearest slice in [first, last) of every other section to each end of every original
    section, the list growing meanwhile; within 16 m and more than 5 slices from both of its ends, the section ends
    there and the rest is a new section at the end of the list)"""
    count = len(positions)
    if not lengths or len(lengths) < 2:
        sections = [[0, count - 1]]
    else:
        sections = []
        at = 0
        for length in lengths:
            sections.append([at, at + length - 1])
            at += length
    for i in range(len(sections)):
        for k in range(2):
            end = positions[sections[i][k]]
            j = 0
            while j < len(sections):
                if j != i:
                    first, last = sections[j]
                    best, nearest = 1e9, 0
                    for s in range(first, last):
                        d = _d2(end, positions[s])
                        if d < best:
                            best, nearest = d, s
                    if best < NFS5_JUNCTION_REACH2 and nearest - first > 5 and last - nearest > 5:
                        sections[j] = [first, nearest]
                        sections.append([nearest + 1, last])
                j += 1
    return sections


def nfs5_spline_junctions(positions: List[dict], sections: List[List[int]]) -> List[List[SectionEnd]]:
    """Junctions of the sections (Porsche.exe 0x480b40): for every section end in no junction yet, in section order,
    a junction of it and every other free end within 16 m (at most 8 ends). A lone end (the start, the finish, a dead
    end) is a junction of its own"""
    junctions = []
    used = set()
    for i in range(len(sections)):
        for k in range(2):
            if (i, k) in used:
                continue
            ends = [(i, k)]
            used.add((i, k))
            position = positions[sections[i][k]]
            for m in range(len(sections)):
                for kk in range(2):
                    if (m, kk) in used or _d2(position, positions[sections[m][kk]]) >= NFS5_JUNCTION_REACH2:
                        continue
                    if len(ends) < NFS5_JUNCTION_MAX_ENDS:
                        ends.append((m, kk))
                        used.add((m, kk))
            junctions.append(ends)
    return junctions


def nfs5_junction_centre(positions: List[dict], sections: List[List[int]], ends: List[SectionEnd]) -> dict:
    """The junction's centre: the average of its end slices (Porsche.exe 0x480b40)"""
    points = [positions[sections[m][k]] for m, k in ends]
    return {axis: sum(p[axis] for p in points) / len(points) for axis in ('x', 'y', 'z')}


def nfs5_race_route(sections: List[List[int]], junctions: List[List[SectionEnd]]) -> Tuple[List[int], bool]:
    """The sections of the race route, in driving order, and whether it is a circuit: the longest walk from junction
    0, which is the race length of the game (Porsche.exe 0x4819e0: from every start end of a junction, along its
    section to the junction of the section's last slice, a junction's distance raised to the walk's + slice count;
    the walk does not go on from junction 0, a walk back to it is a lap). One junction (a single looped section, the
    skidpad): the first section, a circuit"""
    junction_of_slice: Dict[int, int] = {}
    for j, ends in enumerate(junctions):
        for m, k in ends:
            junction_of_slice.setdefault(sections[m][k], j)
    distances = [0] * len(junctions)
    previous: List[Optional[Tuple[int, int]]] = [None] * len(junctions)
    # (longest walk, last junction, last section, junction reached)
    longest = [0, None, None, None]

    def walk(j: int):
        for m, k in junctions[j]:
            if k != 0:
                continue
            first, last = sections[m]
            to = junction_of_slice.get(last)
            if to is None or to == j:
                continue
            distance = distances[j] + (last - first) + 1
            if distances[to] < distance:
                if longest[0] < distance:
                    longest[:] = [distance, j, m, to]
                if to != 0:
                    distances[to] = distance
                    previous[to] = (j, m)
                    walk(to)

    if junctions:
        walk(0)
    if longest[2] is None:
        if not sections:
            return [], False
        return [0], junction_of_slice.get(sections[0][0]) == junction_of_slice.get(sections[0][1])
    route = [longest[2]]
    j = longest[1]
    while j != 0:
        j, m = previous[j]
        route.append(m)
    route.reverse()
    return route, longest[3] == 0


def nfs5_track_roads(slices: List[dict], lengths: List[int]) -> dict:
    """The race route and the other roads of a track from the CRP's "DmiS" slices and "TmiS" slice counts:
    `route` the slices of the race route sections in driving order (`position`, `orientation`: heading of the
    slice's `forward` vector, atan2(x, z)), `closed` whether it is a circuit, `roads` every other section from its
    start junction's centre through its slices to its end junction's centre, as the HUD map links them (positions in
    CRP coordinates, Y up)"""
    positions = [s['position'] for s in slices]
    if not positions:
        return {'route': [], 'closed': False, 'roads': []}
    sections = nfs5_spline_sections(positions, lengths)
    junctions = nfs5_spline_junctions(positions, sections)
    route_sections, closed = nfs5_race_route(sections, junctions)
    junction_of_end = {end: j for j, ends in enumerate(junctions) for end in ends}
    centres = [nfs5_junction_centre(positions, sections, ends) for ends in junctions]

    def point(p: dict) -> dict:
        return {'x': p['x'], 'y': p['y'], 'z': p['z']}

    route = [
        {
            'position': point(positions[s]),
            'orientation': math.atan2(slices[s]['forward']['x'], slices[s]['forward']['z']),
        }
        for m in route_sections
        for s in range(sections[m][0], sections[m][1] + 1)
    ]
    roads = []
    on_route = set(route_sections)
    for m, (first, last) in enumerate(sections):
        if m in on_route:
            continue
        points = [point(positions[s]) for s in range(first, last + 1)]
        start, end = centres[junction_of_end[(m, 0)]], centres[junction_of_end[(m, 1)]]
        if start != points[0]:
            points.insert(0, start)
        if end != points[-1]:
            points.append(end)
        roads.append({'closed': False, 'points': points})
    return {'route': route, 'closed': closed, 'roads': roads}
