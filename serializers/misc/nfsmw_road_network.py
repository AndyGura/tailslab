"""Roads of the NFS Most Wanted road network (`NfsmwRoadNetwork`, chunk 0x3b800 of TRACKS/L2RA.BUN) as polylines in
world axes (Z up) for the track viewer's minimap. Segments are cubic Bezier curves between nodes; runs of segments
through nodes with exactly two segments make one road, a run coming back to its first node a loop"""

import math
from typing import Dict, List, Optional, Tuple

from resources.blackbox.maps.nfsmw import NFSMW_ROAD_SEGMENT_HANDLE_UNIT, NFSMW_ROAD_SEGMENT_LENGTH_UNIT

Point = Tuple[float, float, float]

# a curved segment gets a point every so many meters and degrees of its turn (2..16 pieces); one with both control
# points this close to the straight line between its nodes stays a line
NFSMW_ROAD_SAMPLE_STEP = 10.0
NFSMW_ROAD_SAMPLE_ANGLE = 15.0
NFSMW_ROAD_STRAIGHT_TOLERANCE = 0.25


def nfsmw_road_network(data: dict) -> Optional[dict]:
    """The road network chunk of a chunk bundle, None if it has none"""
    if 'chunks' not in data and isinstance(data.get('data'), dict):
        data = data['data']
    for chunk in data.get('chunks', []):
        chunk_data = chunk['data']
        if isinstance(chunk_data, dict) and chunk_data.get('chunk_id') == 0x0003B800 and 'segments' in chunk_data:
            return chunk_data
    return None


def nfsmw_world_point(p: Dict[str, float]) -> Point:
    """World position (Z up, the axes of the scenery) of a position in simulation axes (Y up)"""
    return p['z'], -p['x'], p['y']


def _rounded(p: Point) -> Point:
    # centimetres: a smaller "track_route.json"
    return round(p[0], 2), round(p[1], 2), round(p[2], 2)


def _distance_to_line(p: Point, a: Point, b: Point) -> float:
    ab = [y - x for x, y in zip(a, b)]
    ap = [y - x for x, y in zip(a, p)]
    length2 = sum(x * x for x in ab)
    t = sum(x * y for x, y in zip(ab, ap)) / length2 if length2 > 1e-12 else 0.0
    return math.dist(p, [x + t * y for x, y in zip(a, ab)])


def nfsmw_segment_points(nodes: List[dict], segment: dict) -> List[Point]:
    """Points along a segment from its start node to its end node, world axes"""
    p0 = nodes[segment['start_node']]['position']
    p3 = nodes[segment['end_node']]['position']
    start_handle = segment['start_handle'] / NFSMW_ROAD_SEGMENT_HANDLE_UNIT / 127
    end_handle = segment['end_handle'] / NFSMW_ROAD_SEGMENT_HANDLE_UNIT / 127
    p1 = {k: p0[k] + segment['start_direction'][k] * start_handle for k in 'xyz'}
    p2 = {k: p3[k] + segment['end_direction'][k] * end_handle for k in 'xyz'}
    a, b, c, d = (nfsmw_world_point(p) for p in (p0, p1, p2, p3))
    if max(_distance_to_line(b, a, d), _distance_to_line(c, a, d)) < NFSMW_ROAD_STRAIGHT_TOLERANCE:
        return [_rounded(a), _rounded(d)]
    length = segment['length'] / NFSMW_ROAD_SEGMENT_LENGTH_UNIT
    # the end direction points back along the curve
    cosine = -sum(segment['start_direction'][k] * segment['end_direction'][k] for k in 'xyz') / 127**2
    turn = math.degrees(math.acos(max(-1.0, min(1.0, cosine))))
    pieces = max(2, min(16, math.ceil(max(length / NFSMW_ROAD_SAMPLE_STEP, turn / NFSMW_ROAD_SAMPLE_ANGLE))))
    points = []
    for i in range(pieces + 1):
        t = i / pieces
        u = 1 - t
        weights = (u * u * u, 3 * u * u * t, 3 * u * t * t, t * t * t)
        points.append(_rounded(tuple(sum(w * p[k] for w, p in zip(weights, (a, b, c, d))) for k in range(3))))
    return points


def nfsmw_roads(network: dict) -> List[Tuple[List[Point], bool]]:
    """Roads (points in world axes, is a loop) of the road network: chains of segments joined at nodes with two
    segments, from and to the other nodes (junctions, dead ends); chains of nodes with two segments only are loops"""
    nodes, segments = network['nodes'], network['segments']
    node_segments = [[] for _ in nodes]
    for i, segment in enumerate(segments):
        node_segments[segment['start_node']].append(i)
        node_segments[segment['end_node']].append(i)
    visited = [False] * len(segments)

    def walk(node: int, first_segment: int) -> Tuple[List[Point], int]:
        points, i = [], first_segment
        while True:
            visited[i] = True
            segment = segments[i]
            forward = segment['start_node'] == node
            piece = nfsmw_segment_points(nodes, segment)
            piece = piece if forward else piece[::-1]
            points.extend(piece if not points else piece[1:])
            node = segment['end_node'] if forward else segment['start_node']
            following = [k for k in node_segments[node] if not visited[k]]
            if len(node_segments[node]) != 2 or not following:
                return points, node
            i = following[0]

    roads = []
    for node, own in enumerate(node_segments):
        if len(own) == 2:
            continue
        for i in own:
            if not visited[i]:
                points, _ = walk(node, i)
                roads.append((points, False))
    # what is left: loops of nodes with two segments each
    for i, segment in enumerate(segments):
        if not visited[i]:
            points, end = walk(segment['start_node'], i)
            closed = end == segment['start_node']
            roads.append((points[:-1] if closed else points, closed))
    return roads
