from typing import Dict, List

from library.context import ReadContext, WriteContext
from library.exceptions import DataIntegrityException, EndOfBufferException
from library.read_blocks import (
    DeclarativeCompoundBlock,
    IntegerBlock,
    ArrayBlock,
    BytesBlock,
    BitFlagsBlock,
    FittedBytesBlock,
    UTF8Block,
)
from resources.eac.fields.numbers import fixed16, s32, u16, u32, u8


# TNFS SE replay (`*.RPL`) is a dump of the game's replay buffers, there is no header and no length fields. The game
# writes five consecutive blocks (`FUN_0044d420` in the Win95 SE executable, `tnfs_replay_save_buffer` in the DOS
# demo): the race setup, the highlights, the recording buffer, the world state and the stats of 9 cars.
# Sizes are fixed, the file is always 100374 bytes.
#
# Time: the game counts a 60/s clock (`g_sim_clock`), which advances by 2 per 30 Hz simulation tick; the race timer
# starts at 300 (5 s). Every time value of the replay (named "clock" here) is in units of this clock; a "simulation
# tick" is one 30 Hz step.
# Controls are read and recorded every 4 clock units (every 2nd simulation tick, simulation flags 4, the "control
# step"), keyframes are taken every 0x708 clock units (30 s).
# The recording buffer is circular and keeps 8 minutes: control sample index = (clock % 0x7080) / 4, keyframe slot =
# (clock % 0x7080) / 0x708. It is not cleared between races, so everything past the recorded end (`world_state`
# `end_clock`) is stale data of earlier races.
# Positions and speeds are 16.16 fixed point numbers, angles are 24-bit numbers (0x1000000 is a full turn).
#
# Random generator: `tnfs_random_seed` (SE 0x428fe0) sets the LCG multiplier to the seed (`setup.random_seed`) and
# the state to seed * 3, both made odd. Each step is `nbr = state * multiplier; state = nbr & 0xffff`, so the state
# (`g_lcg_random_mod` in the game code) changes with every number drawn; only the state is kept in the keyframes.
# Playback: `tnfs_replay_reinstate` (SE 0x44e354) restores the keyframe before the wanted clock, then simulates the
# race again with the recorded control words. Keyframes don't hold the whole game state, so only a playback from
# the start of the race is exact.
#
# This format is the Win95 SE one. DOS TNFS (163053 bytes) has the same blocks with other sizes:
# - setup 0x185 bytes: car counts at 0x1f..0x2f, seed at 0x37, player records of 0x59 bytes, grid order at 0xed,
#   player id at 0x179;
# - highlights 0xb84 bytes: same layout with `seconds[600]` (10 minutes), the playback state tail at 0xb60;
# - recording buffer 150000 bytes: 9000 control samples per player, player keyframes at 36000 (30 of 0x1a4 bytes
#   per player), other cars' keyframes at 0xef10 (30 of 0xb90 bytes);
# - world state 0x15a4 bytes: same header, 30 + 4 records, saved timers;
# - stats 0x1d0 bytes per car (0x1c8 int unknown, 0x1cc int car model);
# - keyframes every 0x4b0 clock units.
# PSX TNFS takes keyframes every 0x708 clock units and keeps 0x5460 clock units (6 minutes).

REPLAY_KEYFRAMES = 16
REPLAY_WORLD_KEYFRAMES = 20
REPLAY_CONTROL_SAMPLES = 7200
REPLAY_PLAYERS = 2
REPLAY_PLAYER_RECORDS = 8
REPLAY_OTHER_CARS = 8
REPLAY_CARS = 9

_CAR_MODELS = '0 TSupra, 1 LDiabl, 2 P911, 3 CZR1, 4 F512TR, 5 DVIPER, 6 ANSX, 7 MRX7'
_INPUT_DEVICES = '0 keyboard, 1 joystick, 2 mouse, 3 joystick buttons'


def _device_description(kind):
    return (
        f'{kind} input device: {_INPUT_DEVICES}. Copied to the input device globals (SE 0x4fb724 / 0x4fb728 / '
        '0x4fb72c, stride 0xc per player) by `tnfs_game_enter_drive_sim` (SE 0x4275f8) when the replay is played'
    )


class TnfsReplayPlayer(DeclarativeCompoundBlock):
    block_description = 'Settings of one player, 0x4b bytes'

    class Fields(DeclarativeCompoundBlock.Fields):
        unk0 = (BytesBlock(length=2), {'is_unknown': True, 'description': '0 in every file'})
        name = (UTF8Block(length=8), {'description': 'Player name, first 8 bytes of the 9-byte name buffer'})
        name_terminator = (
            u8(),
            {
                'description': 'Last byte of the 9-byte name buffer, the null terminator of an 8-character name. '
                'Can hold a leftover character after a shorter name'
            },
        )
        car_model = (s32(), {'description': f'Car model: {_CAR_MODELS}'})
        automatic_transmission = (
            s32(),
            {
                'description': 'Boolean, gearbox option. Used as the "automatic gear" flag of the car, and selects the '
                'variant of the car physics'
            },
        )
        traction_control = (
            s32(),
            {'description': 'Boolean, traction control option. Applied only if the car PBS `has_tcs` (0x338) is set'},
        )
        abs = (
            s32(),
            {'description': 'Boolean, ABS option. Applied only if the car PBS `has_abs` (0x334) is set'},
        )
        unk1 = (s32(), {'is_unknown': True, 'description': 'Front-end / sound configuration value'})
        sound_on = (
            s32(),
            {
                'description': 'Sound configuration, non-zero when the sound is on (taken when the replay is '
                'saved, 0 without a sound card)'
            },
        )
        sound_value_1 = (
            s32(),
            {
                'description': 'Front-end / sound configuration value, taken when the replay is saved, 0 without '
                'a sound card'
            },
        )
        unk2 = (s32(), {'is_unknown': True, 'description': 'Front-end / sound configuration value'})
        sound_value_2 = (
            s32(),
            {
                'description': 'Front-end / sound configuration value, taken when the replay is saved, 0 without '
                'a sound card'
            },
        )
        unk3 = (s32(), {'is_unknown': True, 'description': 'Front-end / sound configuration value'})
        steering_device = (s32(), {'description': _device_description('Steering')})
        pedal_device = (s32(), {'description': _device_description('Throttle / brake')})
        shift_device = (s32(), {'description': _device_description('Gear shift')})
        unk4 = (
            s32(),
            {'is_unknown': True, 'description': 'Set to 0 by the game code, the files hold leftover values here'},
        )
        unk5 = (
            s32(),
            {'is_unknown': True, 'description': 'Set to 0 by the game code, the files hold leftover values here'},
        )
        unk6 = (s32(), {'is_unknown': True})


class TnfsReplaySetup(DeclarativeCompoundBlock):
    block_description = 'Settings of the race the replay was recorded in, 0x348 bytes'

    class Fields(DeclarativeCompoundBlock.Fields):
        unk0 = (BytesBlock(length=2), {'is_unknown': True})
        track_segment = (
            s32(),
            {
                'description': '0-based segment of an open track (`cl2` is segment 1 of CL). With `track_id`, an '
                "index of the game's track tables (`track_id * 0xa6b + track_segment * 0x27`)"
            },
        )
        track_id = (
            s32(),
            {'description': 'Track: 0 CY, 1 CL, 2 AL (the open tracks), 3 TR1, 4 TR2, 5 TR6, 6 TR3, 7 TR7, 8 TR4'},
        )
        track_name = (
            UTF8Block(length=10),
            {'description': 'Track file name without extension, e.g. `cl2` for CL2.TRI'},
        )
        race_type = (
            s32(),
            {'description': 'Race type: 0 time trial, 1 head to head, 2 single race, 3 tournament'},
        )
        is_linked_game = (s32(), {'description': 'Boolean. 1 for the linked (multiplayer) game'})
        game_settings = (
            s32(),
            {'description': 'Bit flags `g_game_settings`. The game checks 4, 8 and 0x20; 4 is No Mercy (head to head)'},
        )
        racer_count = (s32(), {'description': 'Number of racing cars, players included'})
        player_count = (s32(), {'description': 'Number of players'})
        cop_count = (
            s32(),
            {
                'description': 'Number of police cars. The race setup (SE 0x42702c) sets 1 in a single-player head to '
                'head on an open track (`track_id` below 3) without No Mercy (`game_settings` 4), 0 otherwise'
            },
        )
        car_count = (s32(), {'description': 'Total number of cars: racers, cops and traffic'})
        traffic_count = (
            s32(),
            {'description': 'Number of traffic cars: 6 under the same conditions as `cop_count`, 0 otherwise'},
        )
        opponent_difficulty = (
            s32(),
            {'description': 'Opponent difficulty, the front-end option. Index of the table at SE 0x4c5ce0'},
        )
        random_seed = (
            s32(),
            {
                'description': 'Seed of the random generator of the race: unix time in seconds of the moment '
                'the race started (`time()`, SE FUN_00487bbf)'
            },
        )
        players = (
            ArrayBlock(child=TnfsReplayPlayer(), length=REPLAY_PLAYERS),
            {
                'description': 'Settings of the players of this machine (up to 2 in the linked game). Only the first '
                '`player_count` records are set for the race, the other one holds leftovers in the files (car model '
                '8, device values out of range)'
            },
        )
        unk1 = (
            BytesBlock(length=(REPLAY_PLAYER_RECORDS - REPLAY_PLAYERS) * 0x4B),
            {
                'is_unknown': True,
                'description': '0 in every file. Exactly the room of 6 more player records (0x3c + 8 * 0x4b = 0x294)',
            },
        )
        grid_order = (ArrayBlock(child=s32(), length=8), {'description': 'Grid order (race positions)'})
        car_slot_models = (
            ArrayBlock(child=s32(), length=REPLAY_CARS),
            {
                'description': 'Car model per car slot, 99 for none. Player slots hold 99 too, and in the files '
                'the stats `car_model` of a slot is not always the model of this table'
            },
        )
        car_slot_ids = (
            ArrayBlock(child=s32(), length=REPLAY_CARS),
            {
                'description': 'Id per car slot: 200 + car model for the racers (same model as the stats '
                '`car_model`), small numbers for the cop and traffic slots'
            },
        )
        has_cops = (s32(), {'description': 'Boolean, there is a police car in the race'})
        unk2 = (s32(), {'is_unknown': True})
        live_player_glue = (s32(), {'description': 'Live player glue (multiplayer)'})
        lap_count = (s32(), {'description': 'Number of laps'})
        link_latency = (s32(), {'description': 'Latency of the linked game'})
        player_id = (
            s32(),
            {'description': 'Index of the player car of this machine (`g_player_id` in the game code)'},
        )
        unk3 = (s32(), {'is_unknown': True})
        unk4 = (s32(), {'is_unknown': True})
        is_mirrored = (s32(), {'description': 'Boolean, mirror mode'})
        is_rally = (s32(), {'description': 'Boolean, rally mode'})
        track_variants = (
            ArrayBlock(child=s32(), length=9),
            {'description': 'Time of day / variant of every track, indexed by `track_id`'},
        )


class TnfsReplayHighlightClip(DeclarativeCompoundBlock):
    block_description = 'Interesting part of the race to be shown on the replay summary'

    class Fields(DeclarativeCompoundBlock.Fields):
        start_clock = (s32(), {'description': 'Clock of the clip start'})
        end_clock = (s32(), {'description': 'Clock of the clip end'})
        coolness = (s32(), {'description': 'Highlight score of the clip'})


class TnfsReplayHighlights(DeclarativeCompoundBlock):
    block_description = (
        'Highlights of the race, found by the game during the race, 0x9a4 bytes. Highlight '
        'scores: rollover 0x5c, landing after more than 10 simulation ticks (1/3 s) airborne 0x54, hard fence '
        'hit 0x32, sideways / spin 0x57, fast skid 0x28, first move 0x78, race order swap 0x50, cop spun out '
        '0x52, car-car hit from the table at SE 0x4b909c (20 30 32 34 60 70 80 0 37 38 38 39 92 95 98 0; index '
        '+1 when the car in slot 2 is involved, +2 when the car of the pointer at DOS 0x153bc4 (second player '
        'car?) is involved, +4 when a player is involved, +8 for a crash)'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        clips = (
            ArrayBlock(child=TnfsReplayHighlightClip(), length=30),
            {
                'description': 'Clips, selected at the end of the race (SE 0x44d7d8): 30 passes pick the best '
                'marked `seconds`, a clip of second s is (s - 2) * 60 .. (s + 5) * 60 rounded down to 4, '
                'overlapping clips are merged. Without a highlight, one clip of the whole race with coolness 200. '
                'First `clip_count` used'
            },
        )
        best_seconds = (
            ArrayBlock(child=s32(), length=30),
            {
                'description': 'Numbers of the best seconds of the race (absolute seconds, `seconds` value >> 8), '
                'picked by the highest `seconds` score'
            },
        )
        clip_count = (s32(), {'description': 'Amount of used `clips`'})
        state = (
            s32(),
            {
                'description': 'Current clip index during playback: -2 none, -1 replay without clips, 0 and '
                'more the clip index'
            },
        )
        return_pending = (s32(), {'description': 'Playback state: return pending'})
        saved_camera = (s32(), {'description': 'Playback state: camera saved before the replay'})
        loop_clocks = (
            ArrayBlock(child=s32(), length=4),
            {
                'description': 'Playback state: loop / return clocks. `tnfs_replay_reinstate` with return point n sets '
                'the clock to `loop_clocks[n]` and restores the world state keyframe record 16 + n'
            },
        )
        seconds = (
            ArrayBlock(child=u32(), length=480),
            {
                'description': 'The score of every second of the race, indexed by the wrapped second (clock % '
                '0x7080 / 60), so a race longer than 8 minutes reuses the entries. The value is the absolute second '
                '`clock / 60 << 8 | score`, plus 0x80 (a mark) until the second is selected for a clip. Written (SE '
                '0x44d744) when the stored low byte, mark included, is less than the new score; an entry of an '
                'earlier second (stored second less than the current one) is reset to 0 first'
            },
        )
        current_second = (
            s32(),
            {
                'description': 'Wrapped recording clock divided by 60 (clock % 0x7080 / 60, the `seconds` index), '
                'updated each time a highlight is recorded'
            },
        )
        play_count = (s32(), {'description': 'Playback state: play count'})
        tv_camera = (s32(), {'description': 'Playback state: TV camera'})
        play_to_clock = (s32(), {'description': 'Playback state: clock to play to'})
        seek_target = (s32(), {'description': 'Playback state: seek target clock'})
        camera_restart = (s32(), {'description': 'Playback state: camera restart'})
        is_reinstating = (s32(), {'description': 'Playback state: a keyframe is being reinstated'})
        panel_state = (s32(), {'description': 'Playback state: replay panel state'})
        sound_restart = (s32(), {'description': 'Playback state: sound restart'})


class TnfsReplayCollisionData(DeclarativeCompoundBlock):
    block_description = 'Rigid body of the car for the crash model and the collisions, 0x94 bytes'

    class Fields(DeclarativeCompoundBlock.Fields):
        matrix = (ArrayBlock(child=fixed16(), length=9), {'description': 'Rotation matrix'})
        position = (ArrayBlock(child=fixed16(), length=3), {'description': 'Position x, y, z'})
        speed = (ArrayBlock(child=fixed16(), length=3), {'description': 'Speed x, y, z'})
        angular_speed = (ArrayBlock(child=s32(), length=3), {'description': 'Angular speed x, y, z'})
        unk0 = (
            ArrayBlock(child=fixed16(), length=3),
            {'is_unknown': True, 'description': '(0, -9.81, 0) in every active car of the files, gravity?'},
        )
        unk1 = (ArrayBlock(child=fixed16(), length=3), {'is_unknown': True})
        mass = (fixed16(), {'description': 'Mass'})
        inertia = (fixed16(), {'description': 'Moment of inertia'})
        linear_acceleration_factor = (fixed16(), {'description': 'Linear acceleration factor'})
        angular_acceleration_factor = (fixed16(), {'description': 'Angular acceleration factor'})
        edge_length = (fixed16(), {'description': 'Edge length'})
        half_size = (ArrayBlock(child=fixed16(), length=3), {'description': 'Half size of the body x, y, z'})
        crash_timer = (s32(), {'description': 'Crash timer'})
        ai_countdown = (s32(), {'description': 'AI countdown'})
        car_type_value = (
            s32(),
            {'description': '0xa0 for traffic and cop cars, about 100 for racers, 0 for players'},
        )
        unk2 = (s32(), {'is_unknown': True})
        traffic_speed_factor = (fixed16(), {'description': 'Speed factor of a traffic car'})


class TnfsReplayCarState(DeclarativeCompoundBlock):
    block_description = (
        'Physics state of a car, copied from the car data structure (0x168 bytes). Field '
        'names are the names of the car data fields in the game code. Restoring it (SE 0x44dd9c) also zeroes '
        '`slide_front` / `slide_rear` and recomputes `track_slice_lap`; a player restore sets `tire_skid_front` '
        'to 0 and `tire_skid_rear` to 0 or 2'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        control_handler = (s32(), {'description': 'Control handler: 1 player, 2 AI'})
        crash_state = (
            s32(),
            {
                'description': 'Crash state: 1 busted, 2 player driving, 3 AI driving, 4 crash model, 5 wrecked, '
                '6 hidden'
            },
        )
        unk0 = (u8(), {'is_unknown': True, 'description': 'Always 0'})
        collision_flags = (u16(), {'description': 'Collision flags (car field +0x4e9)'})
        car_index = (u8(), {'description': 'Index of the car, 0 is the first player'})
        position = (ArrayBlock(child=fixed16(), length=3), {'description': 'Position x, y, z'})
        angle = (ArrayBlock(child=s32(), length=3), {'description': 'Angle x, y, z (24-bit angles)'})
        steer_angle = (s32(), {})
        target_angle = (s32(), {})
        is_crashed = (s32(), {})
        matrix = (ArrayBlock(child=fixed16(), length=9), {'description': 'Rotation matrix of the car'})
        track_slice = (s32(), {'description': 'Index of the track node'})
        lap_number = (s32(), {})
        speed_x = (fixed16(), {})
        speed_y = (fixed16(), {})
        speed_z = (fixed16(), {})
        speed_local_lat = (fixed16(), {})
        speed_local_vert = (fixed16(), {})
        speed_local_lon = (fixed16(), {})
        speed = (fixed16(), {})
        angular_speed = (s32(), {})
        car_length = (fixed16(), {})
        car_width = (fixed16(), {})
        center_line_distance = (fixed16(), {})
        side_width = (fixed16(), {})
        road_normals = (
            ArrayBlock(child=fixed16(), length=9),
            {'description': 'Road fence normal, road surface normal and road heading, 3 vectors'},
        )
        road_position = (ArrayBlock(child=fixed16(), length=3), {})
        ai_state = (s32(), {'description': 'Bit flags of the AI state of the car'})
        collision_height_offset = (s32(), {})
        collision_data = (TnfsReplayCollisionData(), {'description': 'Rigid body of the car'})
        car_road_speed = (s32(), {})
        field_158 = (s32(), {'description': 'Random group index'})
        lane_slack = (s32(), {})
        is_wrecked = (s32(), {'description': 'Boolean, the car is wrecked'})


class TnfsReplayPlayerFrame(DeclarativeCompoundBlock):
    block_description = 'State of a car driven by a player, 0x1a4 bytes'

    class Fields(DeclarativeCompoundBlock.Fields):
        car = (TnfsReplayCarState(), {})
        throttle = (u8(), {})
        throttle_previous_pos = (u8(), {})
        brake = (u8(), {})
        is_shifting_gears = (u8(), {'description': 'Game value + 100'})
        rpm_engine = (u16(), {})
        rpm_vehicle = (u16(), {})
        road_grip_increment = (s32(), {})
        tire_grip_rear = (s32(), {})
        tire_grip_front = (s32(), {})
        speed_drivetrain = (s32(), {})
        tire_grip_loss = (s32(), {})
        gear_auto_selected = (u8(), {})
        gear_selected = (u8(), {'description': 'Game value + 2'})
        flags = (
            BitFlagsBlock(
                length=1,
                flag_names=[
                    (0, 'wheels_on_ground'),
                    (1, 'is_engine_cutoff'),
                    (2, 'handbrake'),
                    (3, 'is_gear_engaged'),
                    (5, 'tire_skid_rear'),
                ],
            ),
            {},
        )
        unused = (u8(), {'description': 'Never written by the game, a leftover byte'})
        time_off_ground = (s32(), {})
        last_shift_button = (s32(), {'description': 'Last gear shift button: 0 none, 1 down, 2 up'})
        slope_force_lat = (s32(), {})
        unk0 = (s32(), {'is_unknown': True, 'description': 'Car data field +0x3dd'})
        slope_force_lon = (s32(), {})
        thrust = (s32(), {})
        surface_type = (s32(), {})


class TnfsReplayOtherFrame(DeclarativeCompoundBlock):
    block_description = (
        'State of a car that is not driven by a player (its index is not less than the '
        'number of players), 0x172 bytes. Slots go in the order of the car indexes'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        car = (TnfsReplayCarState(), {})
        speed_target = (s32(), {})
        target_center_line = (s32(), {})
        wheels_on_ground = (u8(), {})
        unused = (u8(), {'description': 'Byte at car data +0x340, not used'})


class TnfsReplayRecording(DeclarativeCompoundBlock):
    block_description = (
        'Replay recording buffer (0x15e00 bytes), circular. A replay is played by '
        'restoring the state of the cars from a keyframe and then simulating the game with the recorded '
        'controls. Control words are built by SE 0x43915c and decoded by SE 0x438f00 (DOS 0x5e9c9). Bits 0-5: '
        'steering (keyboard: 0 left, 0x20 centre, 0x3c right; joystick: `g_joy_x` + 0x20); bits 6-11: '
        'throttle / brake axis (keyboard: 0x1e released, 5 throttle, 0x3c brake, brake wins when both are '
        'pressed; joystick: `g_joy_y` + 0x1e); bit 12 shift up, bit 13 shift down, bit 14 horn, bit 15 '
        'handbrake. The neutral word 0x7a0 is forced before clock 0x78, a disconnected linked player gets '
        '0xffff87a0'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        controls_low = (
            ArrayBlock(child=BytesBlock(length=REPLAY_CONTROL_SAMPLES), length=REPLAY_PLAYERS),
            {
                'description': 'Low bytes of the control word of every player, one sample per control step (4 clock '
                'units), sample index (clock % 0x7080) / 4'
            },
        )
        controls_high = (
            ArrayBlock(child=BytesBlock(length=REPLAY_CONTROL_SAMPLES), length=REPLAY_PLAYERS),
            {
                'description': 'High bytes of the control word of every player, one sample per control step (4 '
                'clock units), sample index (clock % 0x7080) / 4'
            },
        )
        player_frames = (
            ArrayBlock(child=ArrayBlock(child=TnfsReplayPlayerFrame(), length=REPLAY_KEYFRAMES), length=REPLAY_PLAYERS),
            {
                'description': 'Keyframes of the player cars, a keyframe every 0x708 clock units (30 seconds), slot '
                '(clock % 0x7080) / 0x708'
            },
        )
        other_frames = (
            ArrayBlock(
                child=ArrayBlock(child=TnfsReplayOtherFrame(), length=REPLAY_OTHER_CARS), length=REPLAY_KEYFRAMES
            ),
            {
                'description': 'Keyframes of the other cars, a keyframe every 0x708 clock units (30 seconds), slot '
                '(clock % 0x7080) / 0x708'
            },
        )


class TnfsReplayWorldKeyframe(DeclarativeCompoundBlock):
    block_description = 'Race state that is not stored in the cars, taken with every keyframe, 0xa2 bytes'

    class Fields(DeclarativeCompoundBlock.Fields):
        handler_order = (ArrayBlock(child=s32(), length=REPLAY_CARS), {'description': 'Car handler order'})
        race_order = (ArrayBlock(child=s32(), length=REPLAY_CARS), {'description': 'Race order of the cars'})
        unused_0 = (s32(), {'description': 'Not used'})
        unused_1 = (s32(), {'description': 'Not used'})
        other_car_count = (s32(), {'description': 'Number of cars other than the player'})
        ai_frame_counter = (s32(), {'description': 'AI frame counter'})
        is_police_chasing = (s32(), {'description': 'Boolean, the police is chasing'})
        random_state_0 = (
            BytesBlock(length=12),
            {'description': '12 bytes of `g_random_struct[0]`, from its offset 2'},
        )
        random_state_1 = (
            BytesBlock(length=12),
            {'description': '12 bytes of `g_random_struct[1]`, from its offset 2'},
        )
        police_chase_time = (s32(), {'description': 'Police chase time'})
        is_siren_on = (s32(), {'description': 'Boolean, siren sound flag'})
        random_lcg_state = (
            s32(),
            {
                'description': 'State of the random generator (`g_lcg_random_mod` in the game code): seed * 3, made '
                'odd, at the race start, then the low 16 bits of the last product state * multiplier, so it differs '
                'from keyframe to keyframe'
            },
        )
        cop_park_position = (s32(), {'description': 'Park position of the cop (track node)'})
        random_direction_counter_0 = (s32(), {'description': 'Random direction counter'})
        random_direction_counter_1 = (s32(), {'description': 'Random direction counter'})
        hidden_traffic_count = (s32(), {'description': 'Number of hidden traffic cars'})
        unused_2 = (s32(), {'description': 'Dead global, not used'})
        unused_3 = (s32(), {'description': 'Not used'})
        unused_4 = (u8(), {'description': 'Dead byte, not used'})
        speeding_tickets = (u8(), {'description': 'Number of speeding tickets'})
        player_split_checkpoint = (s32(), {'description': 'Split checkpoint index of the player'})
        opponent_split_checkpoint = (s32(), {'description': 'Split checkpoint index of the opponent'})


class TnfsReplayWorldState(DeclarativeCompoundBlock):
    block_description = 'State of the race that is not stored in the cars, 0xcc8 bytes'

    class Fields(DeclarativeCompoundBlock.Fields):
        unk0 = (s32(), {'is_unknown': True, 'description': '0 in every file'})
        end_clock = (s32(), {'description': 'Last recorded clock, the end of the recording'})
        unused_0 = (s32(), {'description': 'Not used'})
        unused_1 = (s32(), {'description': 'Not used'})
        keyframe_countdown = (
            s32(),
            {
                'description': 'Control steps until the next keyframe (set to 0x1c2 = 450 in SE, 300 in DOS, at '
                'every keyframe)'
            },
        )
        keyframes = (
            ArrayBlock(child=TnfsReplayWorldKeyframe(), length=REPLAY_WORLD_KEYFRAMES),
            {
                'description': 'One record per keyframe slot ((clock % 0x7080) / 0x708) in 0..15. Records 16..19 '
                'belong to the return points: `tnfs_replay_reinstate` with return point n restores record 16 + n '
                'along with `highlights.loop_clocks[n]` (no caller found in the game code). Records past `end_clock` '
                'are stale'
            },
        )
        saved_timers = (ArrayBlock(child=s32(), length=3), {'description': '3 saved timers'})


class TnfsReplayStats(DeclarativeCompoundBlock):
    block_description = 'Race stats of one car, 0x1d2 bytes. Times are in clock units (1/60 of second)'

    class Fields(DeclarativeCompoundBlock.Fields):
        lap_times = (
            ArrayBlock(child=s32(), length=17),
            {'description': 'Race time at the end of each lap (0 until the lap is finished)'},
        )
        split_times = (
            ArrayBlock(child=s32(), length=85),
            {'description': 'Race time at every split checkpoint, 5 checkpoints per lap / segment'},
        )
        best_accel_time_1 = (s32(), {'description': 'Best acceleration time, 99999 if none'})
        best_accel_time_2 = (s32(), {'description': 'Best acceleration time, 99999 if none'})
        best_brake_time_1 = (s32(), {'description': 'Best braking time, 999 if none'})
        best_brake_time_2 = (s32(), {'description': 'Best braking time, 999 if none'})
        quarter_mile_speed = (fixed16(), {})
        quarter_mile_time = (s32(), {'description': '99999 if none'})
        penalty_count = (s32(), {})
        warning_count = (s32(), {})
        wreck_count = (s32(), {'description': 'Number of crash model resets while racing'})
        finish_time = (
            s32(),
            {
                'description': 'Race time when the car finished the race. 0 if not finished, 999999 if timed out. '
                'Estimated for the cars that did not finish when the race ends (SE 0x45af80)'
            },
        )
        race_distance = (s32(), {'description': 'Race distance: finish node * 0x30 / 10'})
        top_speed = (fixed16(), {})
        tournament_points = (IntegerBlock(length=2, is_signed=True), {'description': 'Tournament points'})
        finishing_position = (s32(), {'description': 'Finishing position'})
        car_model = (s32(), {'description': f'Car model: {_CAR_MODELS}'})


class TnfsReplay(DeclarativeCompoundBlock):
    block_description = (
        'Replay of the race, saved in `GAMEDATA\\REPLAY`. Reverse engineered from the '
        "decompiled game code, the cars' states are copied from its physics data structures. The 4 replays "
        'REPLAY, REPLAY1, REPLAY2 and REPLAY3 are the replays of the game that cannot be replaced. Time values '
        'are in units of the 60/s game clock, which starts at 300 (5 s) for the race. The recording buffer is '
        'circular (8 minutes) and not cleared between races: data past `world_state.end_clock` is stale'
    )
    serializer = 'JsonSerializer'

    class Fields(DeclarativeCompoundBlock.Fields):
        setup = (TnfsReplaySetup(), {'description': 'Race settings'})
        highlights = (TnfsReplayHighlights(), {'description': 'Highlights of the race'})
        recording = (TnfsReplayRecording(), {'description': 'Controls and car states'})
        world_state = (
            TnfsReplayWorldState(),
            {'description': 'State of the race that is not stored in the cars, every keyframe'},
        )
        stats = (ArrayBlock(child=TnfsReplayStats(), length=REPLAY_CARS), {'description': 'Stats of the cars'})


# NFS2 SE replay (`replay.rpy`, in the game's folder): nfs2sen.exe 0x45cf70 saves it after a race, 0x45cf00 loads it
# whole and Replay_InitReplay 0x45d6e0 (from the race start, when the GameSetup's REPLAY field is 2) copies its
# GameSetup over the game's GameSetup_gData (0x4df518), keeping 11 local dwords of the current setup (+0x3c..+0x67),
# takes the tick count and plays the packet stream back. Little-endian, always 0x5b4 + 0x1e000 = 124340 bytes:
# - +0x000 the GameSetup block: 0x16c dwords (0x5b0 bytes), a copy of GameSetup_gData, its REPLAY field set to 2
# - +0x5b0 u32 the number of sim ticks recorded (64 ticks per second)
# - +0x5b4 the packet stream, 0x1e000 bytes, unused bytes 0.
# Recording (Controls_ReadPacket 0x45d170) keeps, per human player, the control packet of every second sim tick
# (32 per second) in 4 planes of 32 bytes (steering, gas, brake, buttons); every 32 packets 0x45d3f0 appends one chunk
# to the stream: 4 packed records, one per plane in that order. A record (0x45d7c0 packs, 0x45d750 unpacks): byte 0 =
# the record's length in bytes, itself included, then items up to that length: `0xff, count, value` = `value` count
# times (runs of 3 or more), any other byte = itself; a record unpacks to 32 bytes. A record length of 0 ends the
# stream: the last chunk of a race, under 32 packets, is never saved. Playback (0x45cfe0, every even tick from the
# human's packet callback Controls_GetPacket 0x45ced0) unpacks a chunk (0x45d230) and gives packet i as steer =
# (plane0[i] << 2) & 0xff, gas = plane1[i] << 3, brake = plane2[i] << 3, buttons = plane3[i]; at the end of the
# stream the race starts again (a looping replay). With two human players their chunks interleave in the order each
# player's 32 packets fill (only one human verified).

NFS2_REPLAY_SETUP_SIZE = 0x5B0
NFS2_REPLAY_STREAM_SIZE = 0x1E000
NFS2_REPLAY_SIZE = NFS2_REPLAY_SETUP_SIZE + 4 + NFS2_REPLAY_STREAM_SIZE
NFS2_REPLAY_CHUNK_PACKETS = 32
NFS2_REPLAY_SETUP_CARS = 16
# the run marker of a packed plane record
NFS2_REPLAY_RUN = 0xFF

_NFS2_CAR_TYPES = (
    "Car model, index of the exe's model names (0x4c5fe0): 0..14 the race cars 0 MCF1, 1 FF50, 2 F355, 3 GT90, "
    '4 IDGO, 5 MACH, 6 JAGR, 7 LGT1, 8 ESPR, 9 NAZC, 10 CALA, 11 ISDE, 12 CHEV, 13 DAYT, 14 FUTR; 15 and up '
    'traffic and other models'
)
_NFS2_FIXED_TUNING = 'Car tuning value, 16.16 fixed point'


def nfs2_replay_unpack(record: bytes) -> List[int]:
    """The plane values of a packed NFS2 SE replay record (nfs2sen.exe 0x45d750): `record` without its length byte;
    `0xff, count, value` = value count times, any other byte = itself"""
    values = []
    i = 0
    while i < len(record):
        if record[i] == NFS2_REPLAY_RUN:
            if i + 2 >= len(record):
                raise ValueError('A run marker 0xff without its count and value at the end of the record')
            values.extend([record[i + 2]] * record[i + 1])
            i += 3
        else:
            values.append(record[i])
            i += 1
    return values


def nfs2_replay_pack(values: List[int]) -> bytes:
    """A packed NFS2 SE replay record of plane values, its length byte included, as nfs2sen.exe 0x45d7c0 packs them:
    runs of 3 or more equal values as `0xff, count, value`, other values as they are. A value 0xff (none in a
    recorded plane) is always written as a run, so that it unpacks again"""
    res = bytearray()
    i = 0
    while i < len(values):
        j = i
        while j < len(values) and values[j] == values[i] and j - i < 0xFF:
            j += 1
        if j - i >= 3 or values[i] == NFS2_REPLAY_RUN:
            res += bytes([NFS2_REPLAY_RUN, j - i, values[i]])
        else:
            res += bytes(values[i:j])
        i = j
    if len(res) + 1 > 0xFF:
        raise ValueError(f'Packed record of {len(res) + 1} bytes, at most 255')
    return bytes([len(res) + 1]) + bytes(res)


def nfs2_replay_packets(chunks: List[Dict]) -> List[Dict]:
    """The control packets of the chunks of an NFS2 SE replay (`Nfs2Replay` `stream/chunks`), in stream order, as the
    game plays them back (0x45cfe0): steer (the unsigned steering byte, 0x80..0x7c of a signed steer -128..124), gas and
    brake (0..248), buttons (the bits of `Nfs2ReplayChunk.buttons`). One human player: packet k is the one of sim tick
    2 * k"""
    packets = []
    for chunk in chunks:
        for steer, gas, brake, buttons in zip(chunk['steering'], chunk['gas'], chunk['brake'], chunk['buttons']):
            packets.append(
                {
                    'steer': (steer << 2) & 0xFF,
                    'gas': (gas << 3) & 0xFF,
                    'brake': (brake << 3) & 0xFF,
                    'buttons': buttons,
                }
            )
    return packets


class Nfs2ReplayPlane(ArrayBlock):
    """One plane of a chunk of the NFS2 SE replay stream: a packed record (nfs2sen.exe 0x45d7c0 / 0x45d750) whose data
    is the 32 unpacked values. Read records must be packed as the game packs them (`nfs2_replay_pack`), so that the
    stream is written back byte-exact and its size is known from the values"""

    def __init__(self, **kwargs):
        super().__init__(child=u8(), length=NFS2_REPLAY_CHUNK_PACKETS, **kwargs)

    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Packed record of 32 bytes, the values unpacked: byte 0 = the length of the record '
            'in bytes (itself included), then up to that length `0xff, count, value` (value count times; runs of 3 '
            'or more) or a byte that is itself',
        }

    @property
    def size_doc_str(self):
        return '4..33'

    def read(self, ctx: ReadContext, name: str = '', read_bytes_amount=None, resolved_length=None):
        head = ctx.buffer.read(1)
        if not head:
            raise EndOfBufferException(ctx=ctx)
        if head[0] == 0:
            raise DataIntegrityException(ctx=ctx, message='Record length 0: the end of the stream')
        record = ctx.buffer.read(head[0] - 1)
        if len(record) < head[0] - 1:
            raise EndOfBufferException(ctx=ctx)
        try:
            values = nfs2_replay_unpack(record)
        except ValueError as ex:
            raise DataIntegrityException(ctx=ctx, message=str(ex))
        if len(values) != NFS2_REPLAY_CHUNK_PACKETS:
            raise DataIntegrityException(ctx=ctx, message=f'Record of {len(values)} values instead of 32')
        if nfs2_replay_pack(values) != head + record:
            raise DataIntegrityException(ctx=ctx, message='Record not packed as nfs2sen.exe packs it')
        return values

    def _packed(self, data, ctx: WriteContext = None) -> bytes:
        if len(data) != NFS2_REPLAY_CHUNK_PACKETS or any(not 0 <= v <= 0xFF for v in data):
            raise DataIntegrityException(ctx=ctx, message='A plane holds 32 values of 0..255')
        return nfs2_replay_pack(data)

    def estimate_packed_size(self, data, ctx: WriteContext = None):
        return len(self._packed(data, ctx))

    def write(self, data, ctx: WriteContext = None, name: str = '') -> bytes:
        return self._packed(data, ctx)


class Nfs2ReplayChunk(DeclarativeCompoundBlock):
    block_description = (
        '32 control packets of a human player (64 sim ticks, 1 s), one plane per packet field (nfs2sen.exe 0x45d3f0 '
        'writes, 0x45d230 reads): value i of each plane belongs to packet i'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        steering = (
            Nfs2ReplayPlane(),
            {
                'description': 'Steering: the signed steering byte (-128 left .. 127 right) / 4 (C division) + 0x40, '
                '0x20..0x5f. Played back as steer = (value << 2) & 0xff'
            },
        )
        gas = (Nfs2ReplayPlane(), {'description': 'Gas pedal / 8, 0..31. Played back as gas = value << 3'})
        brake = (Nfs2ReplayPlane(), {'description': 'Brake pedal / 8, 0..31. Played back as brake = value << 3'})
        buttons = (
            Nfs2ReplayPlane(),
            {
                'description': 'Buttons, bit flags: bit 0 shift down, 1 shift up, 2 horn, 3 handbrake, 6 reset. '
                'Played back as they are'
            },
        )


class Nfs2GameSetupCar(DeclarativeCompoundBlock):
    block_description = (
        'A car of the NFS2 SE GameSetup, 0x40 bytes (car keys of the setup config file: .carType .carClass '
        '.Transmission .Colour .RampSteering .RampGas .RampBrake .FrontDownForce .RearDownForce '
        '.SteeringSensitivity .BrakeBias .GearRatio)'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        car_type = (s32(), {'description': _NFS2_CAR_TYPES})
        car_class = (
            s32(),
            {'description': 'Car class: 1 human, 2 AI racer, 4 traffic, 8 cop (never raced), 0x10 object'},
        )
        transmission = (s32(), {'description': 'Gearbox: 1 automatic'})
        colour = (s32(), {'description': 'Paint colour'})
        ramp_steering = (s32(), {'description': 'Steering ramp option (boolean)'})
        ramp_gas = (s32(), {'description': 'Gas ramp option (boolean)'})
        ramp_brake = (s32(), {'description': 'Brake ramp option (boolean)'})
        front_down_force = (fixed16(), {'description': f'Front down force. {_NFS2_FIXED_TUNING}'})
        rear_down_force = (fixed16(), {'description': f'Rear down force. {_NFS2_FIXED_TUNING}'})
        steering_sensitivity = (fixed16(), {'description': f'Steering sensitivity. {_NFS2_FIXED_TUNING}'})
        brake_bias = (fixed16(), {'description': f'Brake bias. {_NFS2_FIXED_TUNING}'})
        gear_ratio = (
            fixed16(),
            {
                'description': f"Gear ratio. {_NFS2_FIXED_TUNING}; the simulation style divides the car physics' "
                '`velocity_to_rpm_ratio` by it at load'
            },
        )
        unk0 = (BytesBlock(length=16), {'is_unknown': True})


class Nfs2GameSetup(DeclarativeCompoundBlock):
    block_description = (
        "The NFS2 SE race setup, 0x16c dwords (0x5b0 bytes): the game's GameSetup_gData (nfs2sen.exe 0x4df518; "
        'offsets here = address - 0x4df518). Its setup config file has the tokens RACETYPE NUMLAPS SKILL STYLE '
        'COMMMODE RAMP LOCALCAR CATCHUPLOGIC TRACK TIME RANDOM NUMCARS REPLAY NUMSMACKABLES NUMPLAYERRACECARS '
        'NUMOPPONENTRACECARS OPPONENTCARTYPE LANGUAGE SGGE WINDOWSIZE GRAPHICSDETAIL FEI_CARDETAIL VIEWDISTANCE '
        'HORIZONDISPLAY MUSICLEVEL SFXLEVEL INTERACTIVE BESTLAP BACKWARD MIRRORED WILDARCADE LINEUP (in this order '
        'in the exe), which name the fields; which token is which field is not confirmed past the fields named here'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        race_type = (s32(), {'description': 'Race type: 0 single race, 1 tournament, 2 knockout'})
        laps = (s32(), {'description': 'Number of laps'})
        skill = (s32(), {'description': 'Skill: 0 beginner, 1 expert'})
        style = (s32(), {'description': 'Driving style: 0 simulation, 1 arcade'})
        comm_mode = (
            s32(),
            {'description': 'Communication mode: 0 none, 1 split screen, 2 and up modem, serial or network'},
        )
        local_player = (s32(), {'description': 'Local player'})
        catch_up_logic = (s32(), {'description': 'Catch-up logic option'})
        replay = (
            s32(),
            {
                'description': 'Replay mode: 2 in a saved replay (0x45cf70 sets it), the race start then plays the '
                'replay back (Replay_InitReplay 0x45d6e0)'
            },
        )
        flags = (
            BitFlagsBlock(
                length=4,
                flag_names=[
                    (2, 'jaguar_specs_for_traffic'),
                    (3, 'alternate_surface_table'),
                    (4, 'player_1_analog'),
                    (5, 'player_2_analog'),
                    (8, 'psycho_opponents'),
                    (11, 'horn_affects_cars'),
                    (12, 'body_variant_kept'),
                ],
            ),
            {
                'description': 'Bit flags: 0x04 Jaguar specs for traffic, 0x08 the alternate surface table, 0x10 / '
                '0x20 player 1 / 2 on an analog controller, 0x100 psycho opponents, 0x800 the horn affects other '
                'cars, 0x1000 body variant kept'
            },
        )
        track = (s32(), {'description': 'Track number (`TR<nn>` files)'})
        unk0 = (s32(), {'is_unknown': True})
        random_seed = (s32(), {'description': 'Random seed of the race'})
        backward = (
            s32(),
            {'description': 'Boolean, the track is driven backward (AI speed files `TR<nn>B.*`)'},
        )
        unk1 = (s32(), {'is_unknown': True})
        wild_arcade = (s32(), {'description': 'Boolean, Wild arcade style'})
        local_settings = (
            ArrayBlock(child=s32(), length=11),
            {
                'description': 'At +0x3c..+0x67: 11 local settings, which the replay loader keeps from the current '
                'setup (not taken from the file)',
                'is_unknown': True,
            },
        )
        num_cars = (s32(), {'description': 'Number of cars: racers and traffic'})
        num_player_race_cars = (s32(), {'description': 'Number of race cars of the players'})
        num_opponent_race_cars = (s32(), {'description': 'Number of race cars of AI opponents'})
        unk2 = (s32(), {'is_unknown': True})
        cars = (
            ArrayBlock(child=Nfs2GameSetupCar(), length=NFS2_REPLAY_SETUP_CARS),
            {'description': 'At +0x78: the cars, the first `num_cars` used'},
        )
        grid_ranks = (
            ArrayBlock(child=s32(), length=NFS2_REPLAY_SETUP_CARS),
            {'description': 'At +0x478: start grid rank of each car; rank 0 is the last grid slot'},
        )
        unk3 = (
            BytesBlock(length=NFS2_REPLAY_SETUP_SIZE - 0x4B8),
            {
                'is_unknown': True,
                'description': 'At +0x4b8 (the sample replay has 4, 3, 2, 1 in its dwords +0x4bc..+0x4c8)',
            },
        )


def _nfs2_replay_stream_rest(ctx) -> int:
    chunk = Nfs2ReplayChunk()
    return NFS2_REPLAY_STREAM_SIZE - sum(chunk.estimate_packed_size(c) for c in ctx.data('chunks'))


class Nfs2ReplayStream(DeclarativeCompoundBlock):
    block_description = (
        "The packet stream of an NFS2 SE replay, 0x1e000 bytes: chunks of 32 control packets, one human player's each, "
        'up to a record length 0 (nfs2sen.exe 0x45d3f0 writes, playback 0x45cfe0 stops there). One human: chunk c '
        'holds the packets of sim ticks 64 * c + 2 * i (i 0..31)'
    )

    @property
    def size_doc_str(self):
        return str(NFS2_REPLAY_STREAM_SIZE)

    class Fields(DeclarativeCompoundBlock.Fields):
        chunks = (
            ArrayBlock(
                child=Nfs2ReplayChunk(),
                stop_before=(lambda ctx: ctx.peek(1) in (b'', b'\0'), 'up to a record length 0'),
            ),
            {'description': 'The chunks, in the order they were recorded'},
        )
        unused = (
            FittedBytesBlock(length=(_nfs2_replay_stream_rest, '0x1e000 - size of chunks')),
            {
                'usage': 'io,doc',
                'description': 'The rest of the stream, 0: its first byte, a record length 0, ends the stream',
            },
        )


class Nfs2Replay(DeclarativeCompoundBlock):
    block_description = (
        'NFS2 SE replay `replay.rpy`, in the game folder: saved after a race by nfs2sen.exe 0x45cf70, loaded by '
        '0x45cf00 / Replay_InitReplay 0x45d6e0, which take the race setup from it (but its 11 local settings) and '
        'play the control packets of the human player back, from the race start. Always 124340 bytes. The packet '
        'of every second sim tick is recorded, in chunks of 32 packets: the last chunk of a race, under 32 packets, '
        'is not saved. With two human players their chunks interleave in the order they fill (not verified)'
    )
    serializer = 'Nfs2ReplaySerializer'

    class Fields(DeclarativeCompoundBlock.Fields):
        setup = (Nfs2GameSetup(), {'description': 'Race setup, a copy of GameSetup_gData with `replay` 2'})
        tick_count = (u32(), {'description': 'Number of sim ticks recorded (64 per second)'})
        stream = (Nfs2ReplayStream(), {'description': 'The control packets'})
