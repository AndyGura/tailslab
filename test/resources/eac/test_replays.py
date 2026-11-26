import unittest
from copy import deepcopy

from library import require_file
from resources.eac.replays import (
    Nfs2GameSetup,
    Nfs2GameSetupCar,
    Nfs2Replay,
    nfs2_replay_pack,
    nfs2_replay_packets,
    nfs2_replay_unpack,
    TnfsReplay,
    TnfsReplaySetup,
    TnfsReplayPlayer,
    TnfsReplayHighlights,
    TnfsReplayRecording,
    TnfsReplayPlayerFrame,
    TnfsReplayOtherFrame,
    TnfsReplayCarState,
    TnfsReplayCollisionData,
    TnfsReplayWorldState,
    TnfsReplayWorldKeyframe,
    TnfsReplayStats,
)


class TestTnfsReplay(unittest.TestCase):
    def test_replay_is_parsed(self):
        (name, block, data) = require_file('test/samples/REPLAY3.RPL')
        self.assertEqual('TnfsReplay', type(block).__name__)
        setup = data['setup']
        self.assertEqual('cl1', setup['track_name'])
        self.assertEqual(1, setup['track_id'])
        self.assertEqual(0, setup['track_segment'])
        self.assertEqual(1, setup['race_type'])
        self.assertEqual(0, setup['is_linked_game'])
        self.assertEqual(
            (2, 1, 1, 9, 6),
            (
                setup['racer_count'],
                setup['player_count'],
                setup['cop_count'],
                setup['car_count'],
                setup['traffic_count'],
            ),
        )
        self.assertEqual(834889156, setup['random_seed'])
        self.assertEqual(2, len(setup['players']))
        player = setup['players'][0]
        self.assertEqual('Mom?', player['name'])
        self.assertEqual(5, player['car_model'])
        self.assertEqual((1, 3, 0), (player['steering_device'], player['pedal_device'], player['shift_device']))
        self.assertEqual(1, setup['has_cops'])
        self.assertEqual([205, 200], setup['car_slot_ids'][:2])
        self.assertEqual(0, setup['player_id'])

        highlights = data['highlights']
        self.assertEqual(8, highlights['clip_count'])
        self.assertEqual(-2, highlights['state'])
        self.assertEqual((1560, 180), (highlights['play_to_clock'], highlights['seek_target']))
        for second, value in enumerate(highlights['seconds']):
            if value:
                # the index is the second of the circular 8-minute buffer, the value holds the absolute second
                self.assertEqual(second, (value >> 8) % 480)

        car = data['recording']['player_frames'][0][0]['car']
        self.assertEqual((0, 1, 2), (car['car_index'], car['control_handler'], car['crash_state']))
        self.assertAlmostEqual(-9.81, car['collision_data']['unk0'][1], places=2)

        world = data['world_state']
        self.assertEqual(6928, world['end_clock'])
        self.assertEqual(67, world['keyframe_countdown'])
        self.assertEqual(20, len(world['keyframes']))
        self.assertEqual(8, world['keyframes'][0]['other_car_count'])
        self.assertEqual([6, 0, 1], world['saved_timers'])

        self.assertEqual(9, len(data['stats']))
        self.assertEqual(22588, data['stats'][2]['finish_time'])
        self.assertEqual(5, data['stats'][0]['car_model'])
        self.assertEqual(1, data['stats'][0]['wreck_count'])

    def test_block_sizes(self):
        expected = [
            (TnfsReplay(), 100374),
            (TnfsReplaySetup(), 0x348),
            (TnfsReplayPlayer(), 0x4B),
            (TnfsReplayHighlights(), 0x9A4),
            (TnfsReplayRecording(), 0x15E00),
            (TnfsReplayPlayerFrame(), 0x1A4),
            (TnfsReplayOtherFrame(), 0x172),
            (TnfsReplayCarState(), 0x168),
            (TnfsReplayCollisionData(), 0x94),
            (TnfsReplayWorldState(), 0xCC8),
            (TnfsReplayWorldKeyframe(), 0xA2),
            (TnfsReplayStats(), 0x1D2),
        ]
        for block, size in expected:
            with self.subTest(block=type(block).__name__):
                self.assertEqual(size, len(block.pack(block.new_data())))

    def test_replay_can_be_reconstructed(self):
        (name, block, data) = require_file('test/samples/REPLAY3.RPL')
        output = block.pack(data, name=name)
        with open('test/samples/REPLAY3.RPL', 'rb') as bdata:
            original = bdata.read()
        self.assertEqual(100374, len(original))
        self.assertEqual(len(original), len(output))
        self.assertEqual(original, output)

    def test_replay_fields_are_consistent(self):
        (name, block, data) = require_file('test/samples/REPLAY3.RPL')
        tracks = ['cy', 'cl', 'al', 'tr1', 'tr2', 'tr6', 'tr3', 'tr7', 'tr4']
        setup = data['setup']
        self.assertTrue(setup['track_name'].startswith(tracks[setup['track_id']]))
        self.assertEqual(setup['car_count'], setup['racer_count'] + setup['cop_count'] + setup['traffic_count'])
        for player in setup['players'][: setup['player_count']]:
            self.assertIn(player['car_model'], range(8))
            for device in ('steering_device', 'pedal_device', 'shift_device'):
                self.assertIn(player[device], range(4))
        world = data['world_state']
        self.assertEqual(0, world['unk0'])
        # the countdown runs to the next keyframe, one control step per 4 clock units
        self.assertEqual((0x708 - world['end_clock'] % 0x708) // 4 - 1, world['keyframe_countdown'])
        self.assertEqual(setup['car_count'] - 1, world['keyframes'][0]['other_car_count'])


NFS2_REPLAY_SAMPLE = 'test/samples/NFS2SE_replay.rpy'


class TestNfs2Replay(unittest.TestCase):
    # the sample: recorded by nfs2sen.exe's own code in an emulator (nfs-web decomp/nfs2/port-work/lockstep, replay.py
    # selftest): track 5, 12 cars (the human, 5 AI racers, 6 traffic), arcade Wild, analog controller, 6000 ticks

    def test_replay_is_parsed(self):
        (name, block, data) = require_file(NFS2_REPLAY_SAMPLE)
        self.assertEqual('Nfs2Replay', type(block).__name__)
        setup = data['setup']
        self.assertEqual((0, 2, 1, 1, 0), tuple(setup[k] for k in ('race_type', 'laps', 'skill', 'style', 'comm_mode')))
        self.assertEqual(2, setup['replay'])
        self.assertTrue(setup['flags']['player_1_analog'])
        self.assertFalse(setup['flags']['psycho_opponents'])
        self.assertEqual(
            (5, 10995, 0, 1), (setup['track'], setup['random_seed'], setup['backward'], setup['wild_arcade'])
        )
        self.assertEqual(
            (12, 1, 5), (setup['num_cars'], setup['num_player_race_cars'], setup['num_opponent_race_cars'])
        )
        cars = setup['cars'][: setup['num_cars']]
        self.assertEqual([1] + [2] * 5 + [4] * 6, [c['car_class'] for c in cars])
        self.assertEqual([10, 11, 12, 13, 14, 0, 18, 19, 20, 21, 22, 23], [c['car_type'] for c in cars])
        self.assertEqual(1.0, cars[0]['gear_ratio'])
        self.assertEqual([0, 1, 2, 3, 4, 5], setup['grid_ranks'][:6])
        self.assertEqual(6000, data['tick_count'])

        chunks = data['stream']['chunks']
        # 6000 ticks: 93 whole chunks of 32 packets (64 ticks), the last partial chunk is not saved
        self.assertEqual(93, len(chunks))
        packets = nfs2_replay_packets(chunks)
        self.assertEqual(5952, 2 * len(packets))
        self.assertEqual({'steer': 36, 'gas': 248, 'brake': 0, 'buttons': 0}, packets[0])
        for chunk in chunks:
            self.assertTrue(all(0x20 <= v <= 0x5F for v in chunk['steering']))
            self.assertTrue(all(v < 32 for v in chunk['gas'] + chunk['brake']))
        self.assertEqual(bytes(len(data['stream']['unused'])), data['stream']['unused'])

    def test_replay_can_be_reconstructed(self):
        (name, block, data) = require_file(NFS2_REPLAY_SAMPLE)
        with open(NFS2_REPLAY_SAMPLE, 'rb') as f:
            original = f.read()
        self.assertEqual(124340, len(original))
        self.assertEqual(original, block.pack(data, name=name))

    def test_edited_stream_keeps_the_file_size(self):
        (name, block, data) = require_file(NFS2_REPLAY_SAMPLE)
        edited = deepcopy(data)
        # a plane of 32 equal values (4 bytes packed) gets 32 different ones (33 bytes)
        edited['stream']['chunks'][0]['brake'] = list(range(32))
        output = block.pack(edited)
        self.assertEqual(124340, len(output))
        self.assertEqual(list(range(32)), block.unpack_from_bytes(output)['stream']['chunks'][0]['brake'])

    def test_records_pack_as_the_game(self):
        for values, packed in [
            ([7] * 32, bytes([4, 0xFF, 32, 7])),
            ([1, 1, 2] + [3] * 29, bytes([7, 1, 1, 2, 0xFF, 29, 3])),
            ([5, 5, 5] + [0] * 29, bytes([7, 0xFF, 3, 5, 0xFF, 29, 0])),
            # 0xff (never recorded) as a run, so that it unpacks again
            ([0xFF] + [0] * 31, bytes([7, 0xFF, 1, 0xFF, 0xFF, 31, 0])),
        ]:
            with self.subTest(packed=packed.hex()):
                self.assertEqual(packed, nfs2_replay_pack(values))
                self.assertEqual(values, nfs2_replay_unpack(packed[1:]))

    def test_block_sizes(self):
        for block, size in [(Nfs2Replay(), 124340), (Nfs2GameSetup(), 0x5B0), (Nfs2GameSetupCar(), 0x40)]:
            with self.subTest(block=type(block).__name__):
                self.assertEqual(size, len(block.pack(block.new_data())))
