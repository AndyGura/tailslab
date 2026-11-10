import math
import unittest

from serializers.misc.nfs5_road_network import (
    nfs5_race_route,
    nfs5_spline_junctions,
    nfs5_spline_sections,
    nfs5_track_roads,
)


def _slice(x: float, z: float, fx: float = 1.0, fz: float = 0.0) -> dict:
    return {'position': {'x': x, 'y': 0.0, 'z': z}, 'forward': {'x': fx, 'y': 0.0, 'z': fz}}


def _main_road_with_bypass(bypass_slices: int):
    """A straight road of 101 slices 6 m apart along x, then a bypass leaving it next to slice 30 and joining it again
    next to slice 70, 10 m to the side of it at both ends and 60 m in the middle"""
    main = [_slice(6 * i, 0) for i in range(101)]
    bypass = []
    for i in range(bypass_slices):
        t = i / (bypass_slices - 1)
        bypass.append(_slice(180 + 240 * t, 10 + 50 * math.sin(math.pi * t)))
    return main + bypass, [101, bypass_slices]


def _circle(count: int, lengths: list):
    radius = 6 * count / (2 * math.pi)
    slices = []
    for i in range(count):
        a = 2 * math.pi * i / count
        slices.append(_slice(radius * math.cos(a), radius * math.sin(a), -math.sin(a), math.cos(a)))
    return slices, lengths


class TestNfs5RoadNetwork(unittest.TestCase):
    def test_sections_split_where_another_section_ends(self):
        slices, lengths = _main_road_with_bypass(20)
        positions = [s['position'] for s in slices]
        sections = nfs5_spline_sections(positions, lengths)
        self.assertEqual(sections, [[0, 30], [101, 120], [31, 70], [71, 100]])

    def test_junctions_of_section_ends_within_16_m(self):
        slices, lengths = _main_road_with_bypass(20)
        positions = [s['position'] for s in slices]
        sections = nfs5_spline_sections(positions, lengths)
        junctions = nfs5_spline_junctions(positions, sections)
        self.assertEqual(junctions, [[(0, 0)], [(0, 1), (1, 0), (2, 0)], [(1, 1), (2, 1), (3, 0)], [(3, 1)]])

    def test_race_route_is_the_longest_walk(self):
        for bypass_slices, route in [(20, [0, 2, 3]), (60, [0, 1, 3])]:
            slices, lengths = _main_road_with_bypass(bypass_slices)
            positions = [s['position'] for s in slices]
            sections = nfs5_spline_sections(positions, lengths)
            self.assertEqual(nfs5_race_route(sections, nfs5_spline_junctions(positions, sections)), (route, False))

    def test_circuit(self):
        slices, lengths = _circle(100, [50, 50])
        positions = [s['position'] for s in slices]
        sections = nfs5_spline_sections(positions, lengths)
        self.assertEqual(nfs5_race_route(sections, nfs5_spline_junctions(positions, sections)), ([0, 1], True))

    def test_single_looped_section_is_a_circuit(self):
        slices, lengths = _circle(100, [100])
        positions = [s['position'] for s in slices]
        sections = nfs5_spline_sections(positions, lengths)
        self.assertEqual(nfs5_race_route(sections, nfs5_spline_junctions(positions, sections)), ([0], True))

    def test_track_roads(self):
        slices, lengths = _main_road_with_bypass(20)
        roads = nfs5_track_roads(slices, lengths)
        self.assertFalse(roads['closed'])
        self.assertEqual([p['position']['x'] for p in roads['route']], [6 * i for i in range(101)])
        self.assertEqual(roads['route'][0]['orientation'], math.pi / 2)
        self.assertEqual(len(roads['roads']), 1)
        road = roads['roads'][0]
        self.assertFalse(road['closed'])
        # the bypass slices between the centres of its junctions
        self.assertEqual(len(road['points']), 22)
        self.assertAlmostEqual(road['points'][0]['x'], (180 + 186 + 180) / 3)
        self.assertAlmostEqual(road['points'][0]['z'], 10 / 3)
        self.assertAlmostEqual(road['points'][-1]['x'], (420 + 420 + 426) / 3)
        self.assertEqual(road['points'][1], slices[101]['position'])

    def test_no_spline(self):
        self.assertEqual(nfs5_track_roads([], []), {'route': [], 'closed': False, 'roads': []})


if __name__ == '__main__':
    unittest.main()
