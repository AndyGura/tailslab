from library.read_blocks import (
    DeclarativeCompoundBlock,
    IntegerBlock,
    ArrayBlock,
    BytesBlock,
    BitFlagsBlock,
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
