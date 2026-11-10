import math
import unittest
from unittest.mock import patch

from library import require_file
from resources.blackbox.maps.nfsmw import NFSMW_ROAD_NETWORK_TAGS, NFSMW_ROAD_SEGMENT_LENGTH_UNIT
from serializers.maps import NfsuTrackBundleSerializer
from serializers.misc.nfsmw_road_network import (
    nfsmw_road_network,
    nfsmw_roads,
    nfsmw_segment_points,
    nfsmw_world_point,
)

# the road network chunk of NFSMW TRACKS/L2RA.BUN cut down to the nodes of a junction area, with their segments
SAMPLE = 'test/samples/NFSMW_L2RA_ROAD_NETWORK.BUN'


def _node(x, z, segments):
    return {'position': {'x': x, 'y': 0.0, 'z': z}, 'num_segments': len(segments), 'segments': segments}


def _segment(start, end):
    # a straight segment: control points on the line
    return {
        'start_node': start,
        'end_node': end,
        'length': 0,
        'start_handle': 0,
        'end_handle': 0,
        'start_direction': {'x': 0, 'y': 0, 'z': 0},
        'end_direction': {'x': 0, 'y': 0, 'z': 0},
    }


class TestNfsmwRoadNetwork(unittest.TestCase):
    def test_road_network_should_be_read_and_remain_the_same(self):
        (name, block, data) = require_file(SAMPLE, lazy=False)
        with open(SAMPLE, 'rb') as f:
            self.assertEqual(f.read(), block.pack(data, name=name))
        network = nfsmw_road_network(data)
        self.assertEqual([x['tag'] for x in network['entries']], NFSMW_ROAD_NETWORK_TAGS)
        header = network['header']
        self.assertEqual(
            (header['num_nodes'], header['num_segments'], header['num_profiles'], header['num_roads']),
            (len(network['nodes']), len(network['segments']), len(network['profiles']), len(network['roads'])),
        )
        for i, node in enumerate(network['nodes']):
            self.assertEqual(node['index'], i)
            for k in node['segments'][: node['num_segments']]:
                segment = network['segments'][k]
                self.assertIn(i, (segment['start_node'], segment['end_node']))

    def test_segment_curves_should_have_their_length(self):
        (_, _, data) = require_file(SAMPLE)
        network = nfsmw_road_network(data)
        # 16 pieces per curve: the curve itself, not a coarse polyline
        with (
            patch('serializers.misc.nfsmw_road_network.NFSMW_ROAD_SAMPLE_STEP', 0.01),
            patch('serializers.misc.nfsmw_road_network.NFSMW_ROAD_SAMPLE_ANGLE', 0.01),
        ):
            for segment in network['segments']:
                points = nfsmw_segment_points(network['nodes'], segment)
                length = sum(math.dist(a, b) for a, b in zip(points, points[1:]))
                self.assertAlmostEqual(length / (segment['length'] / NFSMW_ROAD_SEGMENT_LENGTH_UNIT), 1, delta=0.01)

    def test_track_paths_should_be_every_segment_without_route(self):
        (_, _, data) = require_file(SAMPLE)
        network = nfsmw_road_network(data)
        route, roads = NfsuTrackBundleSerializer().track_paths(data)
        self.assertIsNone(route)
        ends = [nfsmw_world_point(n['position']) for n in network['nodes']]
        for road in roads:
            self.assertTrue(all(z is not None for _, _, z in road.points))
            for point in (road.points[0], road.points[-1]):
                self.assertLess(min(math.dist(point, x) for x in ends), 0.01)
        # a road per run of segments through nodes with two segments
        runs = sum(1 for n in network['nodes'] for _ in range(n['num_segments']) if n['num_segments'] != 2)
        self.assertEqual(len(roads), runs // 2 + runs % 2 if runs else 0)

    def test_roads_should_join_segments_through_nodes_with_two(self):
        # a junction 0 with a dead end road 0 - 1 - 2 and a loop 0 - 3 - 4 - 0
        nodes = [
            _node(0, 0, [0, 2, 4]),
            _node(10, 0, [0, 1]),
            _node(20, 0, [1]),
            _node(0, 10, [2, 3]),
            _node(10, 10, [3, 4]),
        ]
        segments = [_segment(0, 1), _segment(2, 1), _segment(0, 3), _segment(3, 4), _segment(4, 0)]
        roads = nfsmw_roads({'nodes': nodes, 'segments': segments})
        self.assertEqual(
            [([(x, y) for x, y, _ in points], closed) for points, closed in roads],
            [([(0, 0), (0, -10), (0, -20)], False), ([(0, 0), (10, 0), (10, -10), (0, 0)], False)],
        )
        # nodes with two segments only: a loop
        loop = [_node(0, 0, [0, 2]), _node(10, 0, [0, 1]), _node(0, 10, [1, 2])]
        roads = nfsmw_roads({'nodes': loop, 'segments': [_segment(0, 1), _segment(1, 2), _segment(2, 0)]})
        self.assertEqual([(len(points), closed) for points, closed in roads], [(3, True)])
