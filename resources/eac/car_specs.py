import math
import re
import struct
from copy import deepcopy
from typing import Dict

from library.read_blocks import (
    DataBlock,
    DeclarativeCompoundBlock,
    IntegerBlock,
    ArrayBlock,
    CompoundBlock,
    FixedPointBlock,
    UTF8Block,
    DecimalBlock,
)
from library.read_blocks.misc.value_validators import Eq, Lte
from resources.eac.fields.numbers import IntegerAngleBlock


# TNFS when saving some of the calculated values, uses `floor` instead of `round`
def floor_16(value):
    pow16 = 2**16
    return math.floor(value * pow16) / pow16


def floor_8(value):
    return math.floor(value * 256) / 256


# rounded down inverses of the derived fields; 0 for 0, so that a new (zero-filled) file can be written
def inv_16(value):
    return floor_16(1 / value) if value else 0


def inv_8(value):
    return floor_8(1 / value) if value else 0


def _fixed(**kwargs):
    return FixedPointBlock(length=4, fraction_bits=16, is_signed=True, **kwargs)


def _ufixed(**kwargs):
    return FixedPointBlock(length=4, fraction_bits=16, is_signed=False, **kwargs)


def _fixed8(**kwargs):
    return FixedPointBlock(length=4, fraction_bits=8, is_signed=True, **kwargs)


def _int(**kwargs):
    return IntegerBlock(length=4, is_signed=True, **kwargs)


# TNFS 24-bit angle: 0x1000000 = full turn
def _angle24(**kwargs):
    return IntegerAngleBlock(full_turn=0x1000000, length=4, is_signed=True, **kwargs)


def _uint(**kwargs):
    return IntegerBlock(length=4, is_signed=False, **kwargs)


class PlayerCarPhysics(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Player car physics: the full physics specification of a car the player can drive '
            '(`SIMDATA/CARSPECS/'
            '*.PBS`, QFS-compressed, 1912 bytes uncompressed). Loaded by `Fiziks_PreInitCar` (SE 0x4400f4, DOS '
            '0x63e72, PSX 0x80038ea4); the game keeps the same layout in memory (DOS, SE, PSX). Readers are named '
            'as in [tnfs-1995](https://github.com/marcos2250/tnfs-1995) with Win95 SE addresses; "not read" = no '
            'reader in the DOS, SE and PSX executables. Physics ticks are 1/30 s, angles are 24-bit (0x1000000 = '
            'full turn). Rally mode changes some fields in memory after loading (DOS, SE): rear grip table := '
            'front, `unknown_0x320` and `thrust_scale` halved and their inverses recomputed, `friction_f/r` and '
            '`max_brake_force_1/2` halved, `cog_height` x 1.5, `efficiency` x 0x14c/256 on track 3, else x '
            '0x133/256. PSX rally: `lat_acc_cutoff` x 0.625, `cog_height` x 7/4, `efficiency` x a per-track value, '
            '`drive_bias` = 0.5. Thanks to [Five-Damned-Dollarz](https://gist.github.com/Five-Damned-Dollarz/'
            '99e955994ebbcf970532406a197b580e) and [marcos2250](https://github.com/marcos2250/tnfs-1995/blob/main/'
            'tnfs_files.c)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        mass_front = (
            _fixed(),
            {
                'description': 'Mass on the front axle (kg). Front weight fraction = `mass_front * inv_mass` '
                '(`Fiziks_InitCar`, SE 0x42ff60). Equals `mass_rear` in all files'
            },
        )
        mass_rear = (_fixed(), {'description': 'Mass on the rear axle (kg)'})
        mass = (
            _fixed(programmatic_value=lambda ctx: ctx.data('mass_front') + ctx.data('mass_rear')),
            {
                'description': 'Total car mass (kg), `mass_front + mass_rear`. Only feeds car fields that nothing '
                'reads (`Fiziks_InitCar`): the game uses `inv_mass`'
            },
        )
        inv_mass_f = (
            _fixed(programmatic_value=lambda ctx: inv_16(ctx.data('mass_front'))),
            {'description': '`1 / mass_front`, rounded down. Only feeds a car field that nothing reads'},
        )
        inv_mass_r = (
            _fixed(programmatic_value=lambda ctx: inv_16(ctx.data('mass_rear'))),
            {'description': '`1 / mass_rear`, rounded down. Only feeds a car field that nothing reads'},
        )
        inv_mass = (
            _fixed(programmatic_value=lambda ctx: inv_16(ctx.data('mass_front') + ctx.data('mass_rear'))),
            {
                'description': '`1 / mass`, rounded down. Used for the weight distribution, drag / mass '
                '(`Fiziks_InitCar`) and the torque table (`tnfs_load_torque_table`, SE 0x409990)'
            },
        )
        drive_bias = (
            _ufixed(),
            {
                'description': 'Front share of the drive force, 0.0 = RWD, 1.0 = FWD (`tnfs_physics_update`, SE '
                '0x430cb0). 0 also enables the burnout rule of `tnfs_engine_thrust` (SE 0x42f138). 0 in all files '
                'but LDIABL (0.35) and TRAFFC (0.4)'
            },
        )
        brake_bias_f = (
            _ufixed(),
            {
                'description': 'Front share of the pedal brake force, 0.0-1.0 (`tnfs_physics_update`); the rear '
                'gets the rest'
            },
        )
        brake_bias_r = (
            _ufixed(programmatic_value=lambda ctx: 1 - ctx.data('brake_bias_f')),
            {
                'description': 'Rear share of the brake force, `1 - brake_bias_f` (raw 65536 - `brake_bias_f` in '
                'all files). Not read: the game uses total - front'
            },
        )
        cog_height = (
            _fixed(),
            {
                'description': 'Height of the centre of gravity (m). Weight transfer factor = `cog_height * '
                'wheel_base_inv` (`Fiziks_InitCar`): moves grip between front and rear under longitudinal force. '
                'Rally mode x 1.5 (PSX x 7/4)'
            },
        )
        max_brake_force_1 = (
            _ufixed(),
            {
                'description': 'Cap of the absolute longitudinal tire force while braking (brake > 100 or '
                'handbrake) below 26.8 m/s (60 mph); also the brake force when the car rolls against the selected '
                'gear (`tnfs_physics_update`). Deceleration (m/s²) = this * `force_to_accel` (~10 for ANSX). Rally '
                'mode halves it'
            },
        )
        max_brake_force_2 = (
            _ufixed(),
            {
                'description': 'Same cap from 26.8 to 40 m/s; above 40 m/s the larger of `max_brake_force_1` and '
                'this. Differs from `max_brake_force_1` in 6 of 9 files (ANSX 25.5 / 37.5). Rally mode halves it'
            },
        )
        max_tire_coeff = (_fixed(), {'description': 'Maximal tire coefficient (0.84-1.35). Not read'})
        drag = (
            _fixed(),
            {
                'description': 'Air drag (kg/m, ½ * air density * drag coefficient * frontal area). `Fiziks_InitCar` '
                'replaces it in memory with `drag * inv_mass`; deceleration = that * surface factor * speed² '
                '(`tnfs_drag_force`, SE 0x42f630)'
            },
        )
        top_speed = (
            _fixed(),
            {
                'description': 'Top speed (m/s). Above it `tnfs_physics_update` raises the drag so that it cancels '
                'the thrust, except on track id 6'
            },
        )
        efficiency = (
            _fixed(),
            {
                'description': 'Drivetrain efficiency (0.5-2.0), multiplies the torque table '
                '(`tnfs_load_torque_table`); x 0xf8/256 with the automatic gearbox. `Fiziks_PreInitCar` sets it to 0 '
                'on a `checksum` mismatch, and when the file `By_R&T` can be created in the CARSPECS folder (DOS '
                'flag 0xf7bbe, SE 0x4c5ccc; probably an anti-copy trap, the folder being read-only on the CD). Rally '
                'mode: x 0x14c/256 on track 3, else x 0x133/256'
            },
        )
        wheel_base = (
            _fixed(),
            {'description': 'Distance between the front and rear axles (m): car wheelbase and yaw factors'},
        )
        wheel_base_inv = (
            _fixed(programmatic_value=lambda ctx: inv_16(ctx.data('wheel_base'))),
            {'description': '`1 / wheel_base`, rounded down. Weight transfer factor (`Fiziks_InitCar`)'},
        )
        wheel_track = (
            _fixed(),
            {'description': 'Distance between the left and right wheels (m). Not read'},
        )
        wheel_track_inv = (
            _fixed(programmatic_value=lambda ctx: inv_16(ctx.data('wheel_track'))),
            {'description': '`1 / wheel_track`, rounded down. Not read'},
        )
        rear_weight_fraction = (
            _fixed(),
            {'description': 'Rear weight fraction, `mass_rear / mass` (0.5 in all files). Not read'},
        )
        mps_to_rpm = (
            _fixed(),
            {
                'description': 'Engine rpm = speed (m/s) * this * gear ratio (`tnfs_engine_rev_limiter` SE 0x42ee68, '
                '`tnfs_engine_auto_shift_change` SE 0x4098a0, `tnfs_engine_thrust`)'
            },
        )
        num_gears = (
            _uint(),
            {
                'description': 'Number of used `gear_ratios` entries: reverse, neutral and `num_gears - 2` forward '
                'gears. Upshifts stop at gear index `num_gears - 3` (`tnfs_control_shift_gears` SE 0x438c84, '
                '`tnfs_engine_auto_shift_change`)'
            },
        )
        final_drive = (_fixed(), {'description': 'Final drive ratio. Only read by `tnfs_load_torque_table`'})
        wheel_radius = (_fixed(), {'description': 'Wheel radius (m). Not read, the game uses `inv_wheel_rad`'})
        inv_wheel_rad = (
            _fixed(programmatic_value=lambda ctx: inv_16(ctx.data('wheel_radius'))),
            {'description': '`1 / wheel_radius`, rounded down. Only read by `tnfs_load_torque_table`'},
        )
        gear_ratios = (
            ArrayBlock(length=8, child=_fixed()),
            {
                'description': 'Gear ratios, index = selected gear + 2: [0] reverse (negative), [1] neutral, [2] '
                'first gear and up (`tnfs_engine_rev_limiter`, `tnfs_engine_auto_shift_change`, '
                '`tnfs_engine_thrust`). The neutral ratio only gives the wheel rpm in neutral. The first '
                '`num_gears` entries are used, the rest is garbage'
            },
        )
        num_torques = (
            _uint(value_validator=Lte(60)),
            {
                'description': 'Number of used `torques` entries (51; 41 in P911), at most 60, the length of '
                '`torques`. The game loads that many entries and uses the last one for any higher rpm '
                '(`tnfs_load_torque_table`, `tnfs_engine_get_torque`)'
            },
        )
        roll_stiff_f = (_fixed(), {'description': 'Front roll stiffness (10000.0 in all files). Not read'})
        roll_stiff_r = (_fixed(), {'description': 'Rear roll stiffness (10000.0 in all files). Not read'})
        roll_axis_y = (_fixed(), {'description': 'Roll axis height (m). Not read'})
        front_roll_stiffness_2 = (_fixed(), {'description': '0.5 in all files. Not read'})
        rear_roll_stiffness_2 = (_fixed(), {'description': '0.5 in all files. Not read'})
        weight_transfer_factor = (
            _fixed(),
            {
                'description': '0.001-0.27. Not read: the weight transfer factor of the game is `cog_height * '
                'wheel_base_inv`'
            },
        )
        slip_cutoff = (
            _angle24(),
            {
                'description': 'Max tire slip angle, 24-bit angle: 0x1FE667 = 44.9° in all files. Larger slip '
                'angles are clamped to it and set skid bit 1 (`tnfs_tire_forces`, SE 0x42fb88)'
            },
        )
        normal_loss = (_fixed(), {'description': 'Normal coefficient loss. Not read'})
        max_rpm = (
            _uint(),
            {
                'description': 'Engine redline rpm (`rpm_redline` in the game engine). Rpm limit with the throttle '
                '= this * throttle / 256 (`tnfs_engine_rev_limiter`, `tnfs_engine_thrust`). Engine sound pitch '
                'value = rpm * 127 / (max_rpm + 2000), at most 127 (`tnfs_sfx_engine_player`, SE 0x4444b8, DOS '
                '0x668ab). Tachometer needle: min(rpm, max_rpm + 980) * 600 / max_rpm (SE 0x42221c, 0x420d0c)'
            },
        )
        min_rpm = (
            _uint(),
            {'description': 'Engine idle rpm (`rpm_idle`), engine rpm floor (`tnfs_engine_rev_limiter`)'},
        )
        torques = (
            ArrayBlock(
                length=60,
                child=CompoundBlock(
                    fields=[
                        ('rpm', IntegerBlock(length=4), {}),
                        ('torque', IntegerBlock(length=4), {}),
                    ],
                    inline_description='Two 32bit unsigned integers (little-endian): rpm and torque (N*m)',
                ),
            ),
            {
                'description': 'Engine torque by rpm, the first `num_torques` entries are used, the rest is garbage. '
                'The game reads only the first rpm and assumes 200 rpm steps (true in all files): entry = (rpm '
                'rounded to 200 - rpm[0]) / 200 (`tnfs_engine_get_torque`, SE 0x409a04). '
                '`tnfs_load_torque_table` turns each torque in memory into the 16.16 acceleration per unit of gear '
                'ratio, `torque * final_drive * efficiency * inv_wheel_rad * inv_mass`'
            },
        )
        upshifts = (
            ArrayBlock(length=7, child=IntegerBlock(length=4)),
            {
                'description': 'Automatic gearbox rpm: [g] = upshift from gear index g to g + 1; it shifts down when '
                'the rpm in the lower gear would be below 15/16 of [g - 1] (`tnfs_engine_auto_shift_change`). '
                '`tnfs_engine_thrust` uses [1] - 500 as the burnout rpm limit. The first `num_gears - 3` entries '
                'are used, the rest is garbage'
            },
        )
        gear_efficiency = (
            ArrayBlock(length=8, child=_fixed8()),
            {
                'description': 'Per-gear multiplier of the wheel torque, index = selected gear + 2 like '
                '`gear_ratios` (`tnfs_engine_thrust`). The first `num_gears` entries are used, the rest is garbage'
            },
        )
        inertia_factor = (
            _fixed(),
            {
                'description': '0.5 in all files. Only feeds the car moment of inertia (`Fiziks_InitCar`), which '
                'nothing reads'
            },
        )
        roll_factor = (
            _fixed(),
            {'description': 'Visual body roll from the lateral acceleration (`tnfs_physics_update`), no unit'},
        )
        pitch_factor = (
            _fixed(),
            {'description': 'Visual body pitch from the longitudinal acceleration (`tnfs_physics_update`), no unit'},
        )
        friction_f = (
            _fixed(),
            {
                'description': 'Front tire friction coefficient: front grip = this * front weight fraction * 9.81 '
                '(`Fiziks_InitCar`). Rally mode halves it'
            },
        )
        friction_r = (
            _fixed(),
            {'description': 'Rear tire friction coefficient, like `friction_f`. Rally mode halves it'},
        )
        body_len = (
            _fixed(),
            {
                'description': 'Body length (m). Copied to the car length, then overwritten by `half_length * 2` of '
                'the car PDN in `tnfs_ai_init_car` (SE 0x4407b8): no effect, all 9 cars have PDN sizes'
            },
        )
        body_width = (
            _fixed(),
            {'description': 'Body width (m). Overwritten by `half_width * 2` of the car PDN, like `body_len`'},
        )
        auto_steer = (
            _int(),
            {
                'description': '24-bit angle per m/s (983 in all files). Digital steering, wheel centred, moving '
                'forward: the auto-steer target (road heading) is taken only if its absolute value < this * speed '
                '(`tnfs_control_steering_a`, SE 0x438954)'
            },
        )
        steer_mult = (_uint(), {'description': 'Auto-steer ramp multiplier shift (1). Not read'})
        steer_div = (_uint(), {'description': 'Auto-steer ramp divider shift (1). Not read'})
        steer_model = (_uint(), {'description': 'Steering model (2). Not read'})
        steer_vel = (
            ArrayBlock(length=4, child=IntegerBlock(length=4)),
            {
                'description': 'Auto-steer velocities (2, 4, 8, 16). Only [1] is read: steering rate per tick = '
                'min(`steer_vel_ramp` - min(speed * `steer_vel_att`, 1.5), 1.6) * [1] (`tnfs_control_steering_a`)'
            },
        )
        steer_vel_ramp = (
            _fixed(),
            {'description': 'Base steering rate (2.2-2.5), see `steer_vel` (`tnfs_control_steering_a`)'},
        )
        steer_vel_att = (
            _fixed(),
            {'description': 'Steering rate reduction per m/s, at most 1.5 in total (`tnfs_control_steering_a`)'},
        )
        steer_ramp_mult = (
            _uint(),
            {
                'description': 'Shift count: steering rate << this when the target and the auto-steer angle are on '
                'the same side of the current angle (`tnfs_control_steering_a`)'
            },
        )
        steer_ramp_div = (
            _uint(),
            {
                'description': 'Shift count: steering rate >> this otherwise (`tnfs_control_steering_a`; SE and PSX '
                'only, DOS has no such branch)'
            },
        )
        lat_acc_cutoff = (
            _fixed(),
            {
                'description': 'Max absolute lateral acceleration (m/s², 17.5-40), also the road grip increment '
                '(`tnfs_physics_update`). PSX rally mode x 0.625'
            },
        )
        unknown_0x320 = (
            _fixed8(),
            {
                'is_unknown': True,
                'description': 'Equals `thrust_scale` in all files (2.5; TRAFFC 5.5, TSUPRA 2.7). Not read; rally '
                'mode (DOS, SE) halves it and recomputes `unknown_0x320_inv`',
            },
        )
        unknown_0x320_inv = (
            _fixed8(programmatic_value=lambda ctx: inv_8(ctx.data('unknown_0x320'))),
            {'is_unknown': True, 'description': '`1 / unknown_0x320`, rounded down (raw 65536 / raw). Not read'},
        )
        thrust_scale = (
            _fixed8(),
            {
                'description': 'Thrust multiplier (`tnfs_engine_thrust`): 2.5, TRAFFC 5.5, TSUPRA 2.7. Rally mode '
                'halves it and recomputes `force_to_accel`'
            },
        )
        force_to_accel = (
            _fixed8(programmatic_value=lambda ctx: inv_8(ctx.data('thrust_scale'))),
            {
                'description': '`1 / thrust_scale`, rounded down (raw 65536 / raw): summed longitudinal tire force '
                '* this = acceleration (m/s²) (`tnfs_physics_update`)'
            },
        )
        unknown_0x330 = (_uint(), {'is_unknown': True, 'description': '102 in all files. Not read'})
        has_abs = (
            _fixed(),
            {
                'description': 'Car has ABS if > 0 (1.0); ABS is on if this and the player option are both set '
                '(`Fiziks_PreInitCar`)'
            },
        )
        has_tcs = (_fixed(), {'description': 'Car has traction control if > 0 (1.0), like `has_abs`'})
        throttle_on_ramp = (
            _uint(),
            {'description': 'Throttle (0-255) rise per tick (`tnfs_control_throttle`, SE 0x438b70)'},
        )
        throttle_off_ramp = (_uint(), {'description': 'Throttle (0-255) fall per tick (`tnfs_control_throttle`)'})
        brake_on_ramp_1 = (
            _uint(),
            {
                'description': 'Brake (0-255) rise per tick, x 1.25, while the brake is below 144 '
                '(`tnfs_control_brake`, SE 0x438bc8)'
            },
        )
        brake_on_ramp_2 = (_uint(), {'description': 'Brake rise per tick, x 1.25, from 144 up (`tnfs_control_brake`)'})
        brake_off_ramp_1 = (
            _uint(),
            {'description': 'Brake fall per tick while the brake is below 144 (`tnfs_control_brake`)'},
        )
        brake_off_ramp_2 = (_uint(), {'description': 'Brake fall per tick from 144 up (`tnfs_control_brake`)'})
        shift_timer = (
            _uint(),
            {
                'description': 'Ticks with the gear disengaged while shifting (`tnfs_control_shift_gears`, '
                '`tnfs_engine_auto_shift_control` SE 0x42ed94). Manual downshift: half of it; automatic N -> D: '
                '+1; F512TR (car model 4): +3 when (time & 0x31) == 0x10'
            },
        )
        rpm_dec = (
            _uint(),
            {
                'description': 'Rpm fall per tick towards idle without throttle while the gear is disengaged, half '
                'in neutral (`tnfs_engine_rev_limiter`)'
            },
        )
        rpm_acc = (
            _uint(),
            {
                'description': 'Rpm rise per tick, x throttle / 256, while the gear is disengaged, half in neutral '
                '(`tnfs_engine_rev_limiter`)'
            },
        )
        drop_rpm_dec = (
            _uint(),
            {
                'description': 'In gear: engine rpm fall per tick towards the wheel rpm; / 8 while the rear wheels '
                'spin with throttle > 220 (`tnfs_engine_rev_limiter`)'
            },
        )
        drop_rpm_inc = (
            _uint(),
            {
                'description': 'In gear: engine rpm rise per tick towards the wheel rpm (`tnfs_engine_rev_limiter`; '
                'its branch multiplying this by a per-gear table is unreachable)'
            },
        )
        neg_torque = (
            _uint(),
            {
                'description': 'Engine braking: force = rpm difference * this / 256 * gear ratio, x 8 when the '
                'wheels drive the engine (`tnfs_engine_thrust`)'
            },
        )
        incar_camera_height = (
            _fixed(),
            {'description': 'In-car camera height (m, ~1.0) (in-car camera setup, SE 0x405630). Not read by PSX'},
        )
        center_y = (
            _uint(),
            {
                'description': 'In-car view vertical centre (pixels of 320x200): the in-car view windows get the y '
                'offset (center_y - 108) * screen height / 200 (in-car camera setup, SE 0x405630). Not read by PSX. '
                'The formula is certain, its meaning (projection centre) is an interpretation'
            },
        )
        grip_table_f = (
            ArrayBlock(length=512, child=IntegerBlock(length=1)),
            {
                'description': 'Front tire grip by slip angle, grip = value / 128 (the game: value << 9 as 16.16). '
                'Index = slip angle (24-bit) >> 12: 0.088° steps over 0-45° (`tnfs_tire_slide_table`, read in '
                '`tnfs_tire_forces`; DOS 0x593d5). Index 511 is unreachable with the 44.9° `slip_cutoff` and holds '
                'garbage'
            },
        )
        grip_table_r = (
            ArrayBlock(length=512, child=IntegerBlock(length=1)),
            {
                'description': 'Rear tire grip by slip angle, like `grip_table_f`. Rally mode (DOS, SE) replaces it '
                'with the front table in memory'
            },
        )
        checksum = (
            IntegerBlock(length=4, programmatic_value=lambda ctx: sum(ctx.result[:1880])),
            {
                'description': 'Byte sum of the first 1880 bytes (0x758: all but the last 28 bytes of '
                '`grip_table_r`). On a mismatch `Fiziks_PreInitCar` sets `efficiency` to 0'
            },
        )

    def serializer_class(self):
        from serializers import JsonSerializer

        return JsonSerializer


class CarAiAndCrashBody(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Car AI and crash body: the AI driving model and the collision body of a car '
            '(`SIMDATA/CARFAMS/*.PDN`, QFS-compressed, 460 bytes uncompressed), one per car slot, player included. '
            'Loaded by `tnfs_ai_pdn_file` (SE 0x40fa3c, DOS 0x47425, PSX 0x8001eaa8), applied by `tnfs_ai_init_car` '
            '(SE 0x4407b8). Angles are 24-bit (0x1000000 = full turn)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        half_width = (
            _ufixed(),
            {
                'description': 'Half width (x) of the collision body (m); car width = 2 * this, it overrides PBS '
                '`body_width` (`tnfs_ai_init_car`). Zero in all traffic and cop PDNs: if any of the three half '
                'sizes is 0, the sizes come from the car 3D model'
            },
        )
        half_height = (
            _ufixed(),
            {'description': 'Half height (y) of the collision body (m), also the collision height offset'},
        )
        half_length = (
            _ufixed(),
            {
                'description': 'Half length (z) of the collision body (m); car length = 2 * this, it overrides PBS '
                '`body_len`'
            },
        )
        moment_of_inertia = (
            _fixed(),
            {
                'description': 'Crash-body moment of inertia (1.4-2.25), no physical unit; angular acceleration '
                'factor = 1 / this (`tnfs_collision_data_reset` and the rebound functions)'
            },
        )
        mass = (
            _ufixed(),
            {
                'description': 'Relative crash-body mass (1.0 typical, 0.5-1.5), no physical unit; linear '
                'acceleration factor = 1 / this. Car to car impulses are split by the mass ratio'
            },
        )
        handling_factor = (
            _angle24(),
            {
                'description': 'Racers only (`tnfs_ai_racer_speed`, SE 0x470a9c, DOS 0x80c50, PSX 0x8005bcc8), '
                '24-bit angle (0xA0000 = 14.1°): target speed * (0.8 + 0.203 * (1 - turn / this)), turn = road '
                'heading change per track node. 0xFF0000 (TSUPRA, TRAFFC, traffic, cops) = no corner slowdown. '
                'Copied to car+0x168, its inverse to car+0x16c'
            },
        )
        speed_factor = (
            _fixed(),
            {
                'description': 'Racers only: target speed multiplier (0.92-1.0) (`tnfs_ai_racer_speed`, '
                'car+0x170). 1.0 in traffic and cop PDNs'
            },
        )
        power_curve = (
            ArrayBlock(length=100, child=_fixed()),
            {
                'description': 'AI acceleration by speed (`tnfs_ai_drive_car`, SE 0x46f3e8, DOS 0x7e961, PSX '
                '0x80059d68): speed gain per AI update at index abs(speed in m/s) + 1, x 8 (traffic), x 4 '
                '(racers), x 6 (cops), minus the drive argument of the function. The car slows down when [index - '
                '1] is 0. In racer PDNs the first 0 is at the top gear speed rounded up; traffic PDNs have a linear '
                '0.2 -> 0 curve, COPMUST the P911 curve. Uncertain: the exact time scale and the drive argument'
            },
        )
        top_speeds = (
            ArrayBlock(length=6, child=_fixed()),
            {
                'description': 'Top speed (m/s) per AI gear, 0 = gear skipped (leading zeros); all 0 in traffic and '
                "cop PDNs. Racers' engine rpm = 0.75 * `max_rpm` * speed / top speed of the gear, a shift timer "
                'starts at each gear change (`tnfs_ai_opp_engine_and_cornering`, SE 0x46c278, DOS 0x79af9)'
            },
        )
        max_rpm = (
            _fixed(),
            {'description': "Racers' engine rpm cap, drives the opponent engine sound. 0 in traffic and cop PDNs"},
        )
        gear_count = (
            IntegerBlock(length=4),
            {
                'description': 'Read only as the traffic horn pitch index, when `tnfs_ai_lane_change` starts the '
                'horn (tnfs-1995 names it `pdn_number_of_gears`). Not the number of gears: 5 in every racer PDN, '
                'also in CZR1, DVIPER, P911 and TSUPRA with 6 `top_speeds`. The game plays the traffic horn '
                '(collision bank sample 0x3f) at pitch value `table[index] * doppler >> 8`, table at DOS 0x81aa9 = '
                '0x40, 0x40, 0x64, 0x5a, 0x50, 0x46, 0x3c, 0x32, 0x2d, 0x28. Values: crx 2, bmw 3, jetta 3, sunbird '
                '4, wagon 4, pickup 5, probe 5, traffc 5, axxess 6, jeep 6, lemans 6, rodeo 8, vandura 8, copmust 0 '
                '(the cop never honks); 7 and 9 unused'
            },
        )

    def serializer_class(self):
        from serializers import JsonSerializer

        return JsonSerializer


# PBS fields the 3DO physics item doesn't have
_TNFS_3DO_MISSING_FIELDS = {'max_brake_force_2', 'gear_efficiency', 'checksum'}


def _big_endian_copy(block: DataBlock) -> DataBlock:
    block = deepcopy(block)
    stack = [block]
    while stack:
        current = stack.pop()
        if isinstance(current, IntegerBlock):
            current.byte_order = 'big'
        elif isinstance(current, ArrayBlock):
            stack.append(current.child)
        elif isinstance(current, CompoundBlock):
            stack.extend(child for _, child in current.field_blocks)
    return block


def _tnfs_3do_car_physics_fields():
    # same layout as PBS: big-endian copies of its blocks, with the 3DO meaning in the descriptions
    fields = {}
    for name, (block, _) in PlayerCarPhysics.Fields.fields:
        if name in _TNFS_3DO_MISSING_FIELDS:
            continue
        if name in _TNFS_3DO_REPLACED_FIELDS:
            (name, block) = _TNFS_3DO_REPLACED_FIELDS[name]
        else:
            block = _big_endian_copy(block)
        if name == 'torques':
            block.child.inline_description = 'Two 32bit unsigned integers (big-endian): rpm and torque (N*m)'
        fields[name] = (block, {'description': _TNFS_3DO_DESCRIPTIONS[name]})
    fields['grip_table_f'][1]['description'] += (
        '. Item 1 of the wwww archive (`tnfs_carspecs_002` 0x16de0 loads it to car+0x4a8)'
    )
    fields['grip_table_r'][1]['description'] += (
        '. Item 2 of the wwww archive (`tnfs_carspecs_002` 0x16de0 loads it to car+0x4ac)'
    )
    return type(
        'Fields',
        (DeclarativeCompoundBlock.Fields,),
        {**_TNFS_3DO_WWWW_HEADER_FIELDS, **fields},
    )


def _fixed8_be(**kwargs):
    return FixedPointBlock(length=4, fraction_bits=8, is_signed=True, byte_order='big', **kwargs)


_TNFS_3DO_WWWW_HEADER_FIELDS = {
    'resource_id': (UTF8Block(length=4, value_validator=Eq('wwww')), {'description': 'Resource ID'}),
    'num_items': (
        IntegerBlock(length=4, byte_order='big', value_validator=Eq(3)),
        {'description': 'Number of wwww items: the physics fields (up to `center_y`), `grip_table_f`, `grip_table_r`'},
    ),
    'items_descr': (
        ArrayBlock(
            length=3,
            child=IntegerBlock(length=4, byte_order='big'),
            programmatic_value=lambda ctx: [0x14, 0x364, 0x564],
        ),
        {'usage': 'io,doc', 'description': 'Item offsets: 0x14, 0x364, 0x564'},
    ),
}

# PBS fields with another meaning on 3DO: PBS name -> (3DO name, block)
_TNFS_3DO_REPLACED_FIELDS = {
    'max_brake_force_1': (
        'max_brake_force',
        FixedPointBlock(length=4, fraction_bits=16, is_signed=False, byte_order='big'),
    ),
    'unknown_0x320': ('front_grip_mult', _fixed8_be()),
    'unknown_0x320_inv': (
        'front_grip_mult_inv',
        _fixed8_be(programmatic_value=lambda ctx: inv_8(ctx.data('front_grip_mult'))),
    ),
    'thrust_scale': ('rear_grip_mult', _fixed8_be()),
    'force_to_accel': (
        'rear_grip_mult_inv',
        _fixed8_be(programmatic_value=lambda ctx: inv_8(ctx.data('rear_grip_mult'))),
    ),
    'unknown_0x330': ('burnout_div', _fixed8_be()),
}

# function names and addresses: 3DO LaunchMe (raw ARM, address = file offset), see the PlayerCarPhysics block description
_TNFS_3DO_DESCRIPTIONS = {
    'mass_front': 'Mass on the front axle (kg), `mass - mass_rear` in the spec compiler. Front weight fraction = '
    '`mass_front * inv_mass` (`tnfs_Fiziks_InitCar` 0x11530). Equals `mass_rear` in all files',
    'mass_rear': 'Mass on the rear axle (kg), `mass * rear_weight_fraction` in the spec compiler',
    'mass': 'Total car mass (kg), `mass_front + mass_rear`, the input of the spec compiler. `tnfs_Fiziks_InitCar` '
    'multiplies it by `inv_mass_f` / `inv_mass_r` into car fields',
    'inv_mass_f': '`1 / mass_front`, rounded down (`tnfs_Fiziks_InitCar`)',
    'inv_mass_r': '`1 / mass_rear`, rounded down (`tnfs_Fiziks_InitCar`)',
    'inv_mass': '`1 / mass`, rounded down. Used for the weight distribution, drag / mass (`tnfs_Fiziks_InitCar`) '
    'and the torque table (`tnfs_load_torque_table` 0x1e40)',
    'drive_bias': 'Front share of the drive force, 0.0 = RWD, 1.0 = FWD (`tnfs_physics_update` 0x11f78). 0 also '
    'enables the burnout rule of `tnfs_engine_thrust` (0x10784). 0 in all files but LDIABLO (0.3)',
    'brake_bias_f': 'Front share of the pedal brake force, 0.0-1.0 (`tnfs_physics_update`); the rear gets the rest. '
    'Pedal brake force = brake * 1.29 / 256 * (front grip + rear grip)',
    'brake_bias_r': 'Rear share of the brake force, `1 - brake_bias_f`. Not read: the game uses total - front',
    'cog_height': 'Height of the centre of gravity (m). Weight transfer factor = `cog_height * wheel_base_inv` '
    '(`tnfs_Fiziks_InitCar`): moves grip between front and rear under longitudinal acceleration',
    'max_brake_force': 'Braking cap, an acceleration (m/s², 8.3-11.5): with the brake above 100 the longitudinal '
    'acceleration from the tires is capped to this and the lateral one to 1.5 x this (`tnfs_physics_update`). '
    'Also the rear brake force with the handbrake, and the brake force when the car rolls against the selected '
    'gear. PC splits it by speed into `max_brake_force_1` / `_2`, scaled by `force_to_accel`',
    'max_tire_coeff': 'Braking deceleration in g: the spec compiler takes a speed (mph) and its stopping distance '
    '(ft) and stores v² / 2d / g (0.84-1.35). `tnfs_Fiziks_InitCar` adds `normal_loss * mass_front / 2` in memory '
    'and logs it ("Adjusted max tire co"); nothing else reads it',
    'drag': 'Air drag (kg/m, ½ * air density * drag coefficient * frontal area). `tnfs_Fiziks_InitCar` replaces it '
    'in memory with `drag * inv_mass`; deceleration = that * surface factor * speed² (`tnfs_physics_drag_forces` '
    '0x109e0)',
    'top_speed': 'Top speed (m/s). Above it `tnfs_physics_update` raises the drag so that it cancels the thrust',
    'efficiency': 'Drivetrain efficiency (0.5-0.86), multiplies the torque table (`tnfs_load_torque_table`): x '
    '0xb4/256 with the automatic gearbox, + 0xd/256 when the option byte 0x10 is 5, and, in a game mode not '
    'identified yet, + 0x37/256 (tracks 1, 4, 5), 0x44/256 (other tracks below 6) or 0x55/256 (from 6 up)',
    'wheel_base': 'Distance between the front and rear axles (m): car wheelbase, moment of inertia and yaw factors '
    '(`tnfs_Fiziks_InitCar`)',
    'wheel_base_inv': '`1 / wheel_base`, rounded down. Weight transfer factor (`tnfs_Fiziks_InitCar`)',
    'wheel_track': 'Distance between the left and right wheels (m). Not read',
    'wheel_track_inv': '`1 / wheel_track`, rounded down. Not read',
    'rear_weight_fraction': 'Rear weight fraction, the spec compiler always writes 0.5. Not read',
    'mps_to_rpm': 'Engine rpm = speed (m/s) * this * gear ratio (`tnfs_engine_rev_limiter` 0x10564, '
    '`tnfs_engine_auto_shift` 0x1d68, `tnfs_engine_thrust`)',
    'num_gears': 'Number of used `gear_ratios` entries: reverse, neutral and `num_gears - 2` forward gears. '
    'Upshifts stop at gear index `num_gears - 3` (`tnfs_control_shift_gears` 0x138bc, `tnfs_engine_auto_shift`)',
    'final_drive': 'Final drive ratio. Only read by `tnfs_load_torque_table`',
    'wheel_radius': 'Wheel radius (m). Not read, the game uses `inv_wheel_rad`',
    'inv_wheel_rad': '`1 / wheel_radius`, rounded down. Only read by `tnfs_load_torque_table`',
    'gear_ratios': 'Gear ratios, index = selected gear + 2: [0] reverse (negative), [1] neutral, [2] first gear and '
    'up (`tnfs_engine_rev_limiter`, `tnfs_engine_auto_shift`, `tnfs_engine_thrust`). The neutral ratio only gives '
    'the wheel rpm in neutral. The first `num_gears` entries are used, the rest is garbage',
    'num_torques': 'Number of used `torques` entries (51; 41 in P911), at most 60, the length of `torques`. The '
    'game uses the last one for any higher rpm (`tnfs_engine_torque_table` 0x1f2c)',
    'roll_stiff_f': 'Front roll stiffness (10000.0 in all files). Not read: only the spec compiler uses it for '
    '`front_roll_stiffness_2`',
    'roll_stiff_r': 'Rear roll stiffness (10000.0 in all files). Not read',
    'roll_axis_y': 'Roll axis height (m). Not read: only the spec compiler uses it for `weight_transfer_factor`',
    'front_roll_stiffness_2': 'Front share of the roll stiffness, `roll_stiff_f / (roll_stiff_f + roll_stiff_r)` '
    'in the spec compiler (0.5 in all files). Not read',
    'rear_roll_stiffness_2': '`1 - front_roll_stiffness_2` in the spec compiler (0.5 in all files). Not read',
    'weight_transfer_factor': '`cog_height - roll_axis_y` in the spec compiler (0.18-0.23). Not read: the weight '
    'transfer factor of the game is `cog_height * wheel_base_inv`',
    'slip_cutoff': 'Max tire slip angle, 24-bit angle: 0x200000 = 45° in all files. Larger slip angles are clamped '
    'to it and set skid bit 1 (`tnfs_tire_forces` 0x10f70)',
    'normal_loss': 'Normal coefficient loss (0.0007 in all files). Only adjusts `max_tire_coeff` in '
    '`tnfs_Fiziks_InitCar`',
    'max_rpm': 'Engine redline rpm. Rpm limit with the throttle = this * throttle / 256 (`tnfs_engine_thrust`). '
    'Tachometer needle: min(rpm, max_rpm + 1500) (0xcbb0); race statistics count the gear shifts above max_rpm - '
    '400 (0x13824)',
    'min_rpm': 'Engine idle rpm, engine rpm floor (`tnfs_engine_rev_limiter`)',
    'torques': 'Engine torque by rpm, the first `num_torques` entries are used, the rest is garbage. The game reads '
    'only the first rpm and assumes 200 rpm steps (true in all files): entry = (rpm rounded to 200 - rpm[0]) / 200 '
    '(`tnfs_engine_torque_table`). `tnfs_load_torque_table` turns each torque in memory into the 16.16 '
    'acceleration per unit of gear ratio, `torque * final_drive * efficiency * inv_wheel_rad * inv_mass`',
    'upshifts': 'Automatic gearbox rpm: [g] = upshift from gear index g to g + 1; it shifts down when the rpm in the '
    'lower gear would be below 15/16 of [g - 1] (`tnfs_engine_auto_shift`). `tnfs_engine_thrust` uses [1] - 500 '
    'as the burnout rpm limit. The first `num_gears - 3` entries are used, the rest is garbage',
    'inertia_factor': '0.5 in all files. Car moment of inertia factor (`tnfs_Fiziks_InitCar`)',
    'roll_factor': 'Visual body roll from the lateral acceleration (`tnfs_physics_update`), no unit',
    'pitch_factor': 'Visual body pitch from the longitudinal acceleration (`tnfs_physics_update`), no unit',
    'friction_f': 'Front tire friction coefficient: front grip = this * front weight fraction * 9.81 '
    '(`tnfs_Fiziks_InitCar`)',
    'friction_r': 'Rear tire friction coefficient, like `friction_f`',
    'body_len': 'Body length (m), copied to the car length of player 1 (`tnfs_carspecs_002` 0x16de0); other cars '
    'get 5.0 m',
    'body_width': 'Body width (m), copied to the car width of player 1; other cars get 2.5 m',
    'auto_steer': '24-bit angle per m/s (983 in all files). Moving forward without steering input: the auto-steer '
    'target (road heading) is taken only if its absolute value < this * speed (`tnfs_control_steering` 0x134e0)',
    'steer_mult': 'Auto-steer ramp multiplier shift (1). Not read',
    'steer_div': 'Auto-steer ramp divider shift (1). Not read',
    'steer_model': 'Steering model (2). Not read',
    'steer_vel': 'Steering rates (2, 4, 8, 16), by the pad buttons held: [0] with a 33.75° (0x180000) steering '
    'lock, [1] with 37.97° (0x1b0000) and for centring, [2] with 42.19° (0x1e0000); [3] not read. Rate per tick = '
    'min(`steer_vel_ramp` - min(speed * `steer_vel_att`, 1.5), 1.6) * entry (`tnfs_control_steering`)',
    'steer_vel_ramp': 'Base steering rate (2.2-2.5), see `steer_vel` (`tnfs_control_steering`)',
    'steer_vel_att': 'Steering rate reduction per m/s, at most 1.5 in total (`tnfs_control_steering`)',
    'steer_ramp_mult': 'Shift count: steering rate << this when the target and the auto-steer angle are on the same '
    'side of the current angle (`tnfs_control_steering`)',
    'steer_ramp_div': 'Shift count (1). Not read',
    'lat_acc_cutoff': 'Lateral acceleration cutoff (m/s², 13-17). Not read on 3DO',
    'front_grip_mult': 'Front lateral grip multiplier (1.8 in all files): front lateral force cap = grip table value '
    '* front grip * this (`tnfs_tire_forces`). The PC PBS keeps this slot unused (`unknown_0x320`)',
    'front_grip_mult_inv': '`1 / front_grip_mult`, rounded down (raw 65536 / raw): scales the lateral force back '
    'when `tnfs_tire_forces` checks lateral + longitudinal force against the grip',
    'rear_grip_mult': 'Rear lateral grip multiplier, like `front_grip_mult` (1.8 in all files). The PC PBS uses this '
    'slot as `thrust_scale`',
    'rear_grip_mult_inv': '`1 / rear_grip_mult`, rounded down (raw 65536 / raw), like `front_grip_mult_inv`',
    'burnout_div': '0.4 in all files (8.8 fixed point, "burnOutDiv" in the 3DO debug symbols). Not read',
    'has_abs': 'Car has ABS if > 0 (1.0); ABS is on if this and the player option are both set '
    '(`tnfs_carspecs_002`). Off in DVIPER and LDIABLO',
    'has_tcs': 'Car has traction control if > 0 (1.0), like `has_abs`. On in ANSX, CZR1 and TSUPRA',
    'throttle_on_ramp': 'Throttle (0-255) rise per tick (`tnfs_control_throttle` 0x13764)',
    'throttle_off_ramp': 'Throttle (0-255) fall per tick (`tnfs_control_throttle`)',
    'brake_on_ramp_1': 'Brake (0-255) rise per tick, x 1.25, while the brake is below 144 (`tnfs_control_brake` '
    '0x137ac)',
    'brake_on_ramp_2': 'Brake rise per tick, x 1.25, from 144 up (`tnfs_control_brake`)',
    'brake_off_ramp_1': 'Brake fall per tick while the brake is below 144 (`tnfs_control_brake`)',
    'brake_off_ramp_2': 'Brake fall per tick from 144 up (`tnfs_control_brake`)',
    'shift_timer': 'Ticks with the gear disengaged while shifting (`tnfs_control_shift_gears`, '
    '`tnfs_engine_autoshift` 0x10484). Manual downshift: half of it; car model 4: +3 when (time & 0x31) == 0x10',
    'rpm_dec': 'Rpm fall per tick towards idle without throttle while the gear is disengaged, half in neutral '
    '(`tnfs_engine_rev_limiter`)',
    'rpm_acc': 'Rpm rise per tick, x throttle / 256, while the gear is disengaged, half in neutral '
    '(`tnfs_engine_rev_limiter`)',
    'drop_rpm_dec': 'In gear: engine rpm fall per tick towards the wheel rpm; / 8 while the rear wheels spin with '
    'throttle > 220 (`tnfs_engine_rev_limiter`)',
    'drop_rpm_inc': 'In gear: engine rpm rise per tick towards the wheel rpm (`tnfs_engine_rev_limiter`)',
    'neg_torque': 'Engine braking: force = rpm difference * this / 256 * gear ratio, at most 16 * speed; x 4 when '
    'the wheels drive the engine (`tnfs_engine_thrust`)',
    'incar_camera_height': 'In-car camera height (m, ~1.0) (in-car camera setup 0x168c)',
    'center_y': 'In-car view vertical centre: the camera setup (0x168c) uses center_y - 120',
    'grip_table_f': 'Front tire grip by slip angle, grip = value / 128 (the game: value << 9 as 16.16). Index = slip '
    'angle (24-bit) >> 12: 0.088° steps over 0-45° (`tnfs_tire_slide_table` 0x1045c, read in `tnfs_tire_forces`); '
    'slip angles from 0x1ffffe up read index 511',
    'grip_table_r': 'Rear tire grip by slip angle, like `grip_table_f`',
}


class Tnfs3doCarPhysics(PlayerCarPhysics):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Player car physics of TNFS 3DO (`DriveData/CarData/*.BigSpecsFam`, 1892 bytes): a '
            'big-endian wwww archive of three items, the physics fields (0x350 bytes) and the front and rear grip '
            'tables. The physics fields are the PC `PlayerCarPhysics` (PBS) layout without `max_brake_force_2` and '
            '`gear_efficiency`, the grip tables are the same, there is no checksum. Readers are named as in the '
            '3DO `LaunchMe` executable (raw ARM binary, address = file offset) of '
            '[tnfs-1995](https://github.com/marcos2250/tnfs-1995); "not read" = no reader there. The file is '
            'loaded by `tnfs_carspecs_002` (0x16de0) for player 1; in a debug mode the game instead compiles a '
            'text `<car>.spec` (`tnfs_car_specs` 0x1f8c, which computes the derived fields) and writes it as '
            '`<car>.SpecsBin`. Physics ticks are 1/30 s, angles are 24-bit (0x1000000 = full turn)',
        }

    Fields = _tnfs_3do_car_physics_fields()


def _u8_curve(description: str):
    return (ArrayBlock(length=8, child=IntegerBlock(length=1)), {'description': description})


class Nfs2CarPhysics(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'NFS2 SE car physics (`p<car>.DAT` in `GAMEDATA/SIM/CARDATA/CARDATA.VIV`, 356 '
            'bytes; the loose `GAMEDATA/SIM/CARDATA/P*.DAT` files are identical copies). `Car_Init` (nfs2sen.exe '
            '0x43e2e0) loads it with 0x459970 into the car specs (car+0x2ec, 0x1dc bytes), reading the file as a '
            'raw little-endian stream (udff.c readers 0x4628a0 for 4-byte values, 0x462850 for bytes). The specs '
            'have the file layout, except that the loader swaps `gas_off_factor` and `g_transfer_factor`; the '
            "specs from 0x164 on are not in the file. Field names, types and order come from the developers' "
            'field descriptions `P*.DES` next to the loose files (`Fixed` = 16.16 fixed point, `Integer` = int), '
            'which also embed a copy of the file. The `GAMEDATA/CARMODEL/PC/P*.DAT` files have the same layout '
            'but other values, and are not what the game loads for physics',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        mass = (
            _fixed(),
            {
                'description': 'Mass in kg (`.DES`: "mass"). Drive acceleration of a gear (specs+0x1a8, Car_Init '
                'nfs2sen.exe 0x459560) = `velocity_to_rpm_ratio` / mass / 10 * `gear_efficiency`, in m/s² per N·m '
                'of torque'
            },
        )
        num_gears = (
            _int(),
            {
                'description': 'Number of gears: reverse + neutral + forward gears (6 to 8); the gear tables '
                'have 8 entries. Gear num_gears - 1 is the top gear: the automatic gearbox (0x458280) never shifts '
                'up from it, and only in it may the engine reach the redline with the gas on'
            },
        )
        gear_shift_delay = (
            _int(),
            {
                'description': 'Gear shift delay in physics steps (32 per second); the game uses the low byte as the '
                'shift timer (car+0x2db), set at every gear change. No drive force while it runs (0x454210, '
                '0x456f80)'
            },
        )
        velocity_to_rpm_ratio = (
            ArrayBlock(length=8, child=_fixed()),
            {
                'description': 'Engine rpm per m/s of road speed in each gear: reverse (negative), neutral (0), 1st '
                'to 6th; the top speed of a gear is `engine_redline_rpm` / ratio. The simulation style divides it by '
                "the car tuning's gear ratio (0x459560)"
            },
        )
        gear_efficiency = (
            ArrayBlock(length=8, child=_fixed()),
            {
                'description': 'Gear efficiency per gear: reverse, neutral, 1st to 6th; a factor of the drive '
                'acceleration of the gear (see `mass`)'
            },
        )
        torque_curve = (
            ArrayBlock(length=41, child=_fixed()),
            {
                'description': 'Engine torque in N·m (16.16) by rpm in 256 rpm steps: the game reads entry rpm / '
                '256, clamped to 0..40 (0x4590e0), so entries above `engine_redline_rpm` / 256 are never read. The '
                '`.DES` gives no element type (4-byte elements); the exe multiplies it with the 16.16 drive '
                'acceleration of the gear (see `mass`, 0x454210). Arcade style: drive acceleration (m/s²) = torque '
                '* drive * 1.5 * gas * surface grip, halved while the wheels spin; simulation style: torque * '
                'drive * gas, at most 10 m/s² in 1st gear and 8 m/s² in the others (0x456f80)'
            },
        )
        engine_redline_rpm = (
            _int(),
            {
                'description': 'Engine redline in rpm, a plain integer. Arcade style (0x454210): the wheels never '
                'turn faster than the redline in the gear; above it, except in the top gear, the drive force is '
                '-torque at the redline * drive / 2. Arcade automatic gearbox (0x458280): shifts up above redline - '
                '500 rpm, down when the lower gear stays below redline - 1500 rpm'
            },
        )
        max_velocity = (
            _fixed(),
            {
                'description': 'Top speed of the car in m/s in the simulation style: Car_Init (0x459560) sets the '
                'air drag factor (specs+0x1c8) so that the drag, factor * speed³ (whole m/s), equals the top gear '
                'drive acceleration at this speed (0x456f80). Wild arcade (0x4520e0): a human car turning hard '
                "above 0.9 * the track's speed byte * max velocity / 104 m/s starts to slide"
            },
        )
        front_drive_ratio = (
            _fixed(),
            {
                'description': 'Part of the drive force on the front wheels in the simulation style (0x455370); 0 = '
                'rear wheel drive. Game setup flag 4 sets it to 0.45 (0x459560)'
            },
        )
        max_braking_deceleration = (
            _fixed(),
            {
                'description': 'Maximum braking deceleration in m/s². Arcade style (0x454210): brake * 2 * this, '
                '* 0.75 below 10 m/s, * surface grip; the wheels lock above 0.8 of 2 * this. Simulation style '
                '(0x455370): brake * this'
            },
        )
        front_bias_brake_ratio = (
            _fixed(),
            {
                'description': 'Part of the braking force on the front wheels in the simulation style, plus the car '
                "tuning's brake balance (0x455370)"
            },
        )
        gas_increasing_curve = _u8_curve(
            'Gas increasing curve: per-level steps of a gas ramp, like `brake_increasing_curve`. The controls '
            '(nfs2sen.exe 0x457d80) ramp the gas by fixed steps instead: 16 per physics step with the gas ramp '
            'option, 24 without'
        )
        gas_decreasing_curve = _u8_curve(
            'Gas decreasing curve: per-level steps of a gas ramp, like `brake_decreasing_curve`. The controls '
            '(nfs2sen.exe 0x457d80) ramp the gas by fixed steps instead'
        )
        brake_increasing_curve = _u8_curve(
            'Brake increasing curve: steps of the brake pedal value (0..255) per physics step while it goes up, by '
            'level = pedal / 32 (nfs2sen.exe 0x457d80); only with the brake ramp option (keyboard), else the pedal '
            'follows the control at once'
        )
        brake_decreasing_curve = _u8_curve(
            'Brake decreasing curve: steps of the brake pedal value per physics step while it goes down, by level = '
            'pedal / 32 (nfs2sen.exe 0x457d80); only with the brake ramp option'
        )
        wheel_base = (
            _fixed(),
            {
                'description': 'Wheel base in m. Car_Init (0x459560) stores wheel base / 2 * 0.0245 * 256 at '
                'specs+0x1cc and its inverse at 0x1d0, read by the simulation style (0x455370)'
            },
        )
        front_grip_bias = (
            _fixed(),
            {'description': 'Part of the grip on the front wheels in the simulation style (0x455370)'},
        )
        max_steering_acceleration = (
            _fixed(),
            {
                'description': 'Maximum steering acceleration. Arcade style (0x4539e0): yaw rate (car+0x30c) = gain '
                '/ 128 * steering (-127..127), gain = this / 64, scaled by speed * 0.2 below 5 m/s and divided by 1 '
                '+ speed * `low_turn_factor` / `high_turn_factor` above 20 m/s. Simulation style: multiplied by the '
                "car tuning's steering sensitivity (0x459560)"
            },
        )
        turn_in_ramp = (
            _int(),
            {
                'description': 'Steering ramp step toward the requested steering (-127..127) per physics step, with '
                'the steering ramp option (nfs2sen.exe 0x457d80)',
            },
        )
        turn_out_ramp = (
            _int(),
            {
                'description': 'Steering ramp step back to the centre per physics step, while the request is the '
                'centre or the other side (nfs2sen.exe 0x457d80)',
            },
        )
        lateral_acceleration_grip_multiplier = (
            _fixed(),
            {
                'description': 'Lateral acceleration grip multiplier, read by the simulation style (0x456550; its '
                'inverse at specs+0x1d4, 0x455370). Game setup flag 4 multiplies it by 1.25 (0x459560)'
            },
        )
        aerodynamic_downforce_multiplier = (
            _fixed(),
            {
                'description': 'Aerodynamic downforce multiplier. Simulation style above 5 m/s (0x4575a0): front grip '
                "* (1 + speed * this * the tuning's front downforce), rear grip * (1 + speed * this * rear downforce "
                '* 1.5; * 2 instead of 1.5 while braking above 36 m/s on car types 0 and 14)'
            },
        )
        gas_off_factor = (
            _fixed(),
            {
                'description': 'Engine braking. Arcade style (0x454210): without gas the drive force is -torque * '
                'drive * this * speed * 0.1, and this fraction of the torque brakes when the engine runs faster than '
                'the gas asks. Simulation style (0x456f80) alike. The loader stores it at specs+0x144, after '
                '`g_transfer_factor` (nfs2sen.exe 0x459970)'
            },
        )
        g_transfer_factor = (
            _fixed(),
            {
                'description': 'G transfer factor: weight transfer per longitudinal acceleration in the simulation '
                'style (0x455370). The loader stores it at specs+0x140, before `gas_off_factor`'
            },
        )
        slide_multiplier = (
            _fixed(),
            {
                'description': 'Slide multiplier. Arcade style (0x452fa0): sideways push of a slide = yaw rate * this '
                '* the slide state gain (2.5 to 4) * speed'
            },
        )
        spin_velocity_cap = (
            _fixed(),
            {'description': 'Spin velocity cap, read by the simulation style (0x455370)'},
        )
        slide_velocity_cap = (
            _fixed(),
            {'description': 'Slide velocity cap: sideways speed factor of the simulation style slides (0x455370)'},
        )
        slide_assistance_factor = (
            _int(),
            {
                'description': 'Slide assistance factor. Arcade style (0x4539e0): sliding into a bend scales the '
                'steering gain by (road heading change - this) / 512 + 1 (above 0x80), or (heading change - this / '
                '2) / 128 + 0.5 within 0.75..1'
            },
        )
        push_factor = (
            _int(),
            {
                'description': 'Push factor. Arcade style (0x452fa0), gas below 64: a push slide (understeer) starts '
                'when (speed in whole m/s)² * yaw rate / 512 goes over this + 0x6667'
            },
        )
        low_turn_factor = (
            _fixed(),
            {
                'description': 'Low turn factor (`.DES`: "the lower the figure, the better the turn"). Arcade style '
                '(0x4539e0): the steering gain above 20 m/s is divided by 1 + speed * this with the gas below half'
            },
        )
        high_turn_factor = (
            _fixed(),
            {
                'description': 'High turn factor (`.DES`: "the lower the figure, the better the turn"). Arcade style '
                '(0x4539e0): the steering gain above 20 m/s is divided by 1 + speed * this with half gas or more'
            },
        )

    def serializer_class(self):
        from serializers import JsonSerializer

        return JsonSerializer


def _des(text: str, more: str = ''):
    return {'description': f'`.DES`: "{text}"' + (f'. {more}' if more else '')}


class Nfs2SimTuneGlueLogic(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A pair of the "GLUE LOGIC" values (`.DES` headings "SIM GLUE LOGIC" / "ARCADE '
            'GLUE LOGIC"): slice distance and speed boost multiplier, stored one after the other in the file. The loader '
            '(nfs2sen.exe 0x43e1f4..0x43e213) puts the slice distance of pair k (0..3) at record+0x54 + 4k and '
            'the multiplier at record+0x64 + 4k',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        slice_distance = (_int(), {'description': 'Slice distance (`.DES`: "slice distance 1" .. "4")'})
        speed_boost_multiplier = (
            _fixed(),
            {'description': 'Speed boost multiplier (`.DES`: "Speed boost multiplier 1" .. "4")'},
        )


class Nfs2SimTuneRecord(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Tuning values of one game style, 0x74 bytes: 21 values, then 4 glue logic pairs. '
            'In memory (nfs2sen.exe 0x4df0a8 + style * 0x74) the first 21 values keep their file offsets (the glue logic pairs are split, see `glue_logic`); the '
            'readers cited are in the newton vertical dynamics (nfs2sen.exe 0x44d840)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        telepole_launch_value = (_fixed(), _des('telepole launch Value'))
        initial_jump_roll_attenuate = (_fixed(), _des('initial jump roll attenuate'))
        jump_roll_due_to_car_turn = (_fixed(), _des('jump roll due to car turn'))
        initial_jump_road_pitch_damp = (_fixed(), _des('initial jump road pitch damp'))
        jump_pitch_due_to_acc_and_brake = (_fixed(), _des('jump pitch due to acc and brake'))
        extra_flight_gravity = (
            _fixed(),
            _des('extra flight gravity', 'Gravity factor while the car is in the air (record+0x14)'),
        )
        bad_collision_reset_ticks = (_int(), _des('ticks before car resets in a bad collision'))
        full_gas_reset_tick_advance = (
            _int(),
            _des(
                'advance reset tick if user pushes gas pedal to max',
                'The arcade record\'s description says "gas" instead of "gas pedal"',
            ),
        )
        invincibility_ticks_after_reset = (_int(), _des('Invicibility Time in Ticks after collision reset'))
        reset_forward_slices = (_int(), _des('Slices to move car forward from crash point after collision reset'))
        stop_tumbling_speed = (_fixed(), _des('speed at which car will stop tumbling if upright'))
        collision_reset_altitude = (_fixed(), _des('collision reset car altitude'))
        collision_reset_launch_speed = (_fixed(), _des('collision reset launch speed'))
        bounce_threshold = (
            _fixed(),
            _des(
                'Bounce threshold to use tunable bounce range (0.3 to 1.0)',
                'Compared with the dot product of the car up vector and the road normal (record+0x34)',
            ),
        )
        bounce_elasticity = (
            _fixed(),
            _des('Bounce Elasticity... how much speed is left on rebound', 'Read at record+0x38'),
        )
        bounce_shock_absorb_speed = (
            _fixed(),
            _des('Bounce - shock absorb speed. how much speed is loss before rebound in m/s', 'Read at record+0x3c'),
        )
        ground_max_speed_change = (
            _fixed(),
            _des('Ground - max speed of ground change to stop car from flight in m/s'),
        )
        ground_rise_smoothing = (
            _fixed(),
            _des(
                'Ground - ground rise smoothing factor range (0.0 to 1.0) - smaller = smoother',
                'Read at record+0x44',
            ),
        )
        ground_fall_smoothing = (
            _fixed(),
            _des('Ground - Ground Fall smoothing factor - equal or bigger than above', 'Read at record+0x48'),
        )
        barrier_speed_loss_multiplier = (_fixed(), _des('Speed Loss multiplier when colliding with barriers'))
        deflection_angular_range = (_fixed(), _des('Angular Range of deflection'))
        glue_logic = (
            ArrayBlock(length=4, child=Nfs2SimTuneGlueLogic()),
            {
                'description': 'The 4 "GLUE LOGIC" pairs (`.DES`: "slice distance 1" Integer, "Speed boost '
                'multiplier 1" Fixed, ... 4), each pair as (slice distance, multiplier). In memory the loader '
                '(nfs2sen.exe 0x43e1f4..0x43e213) splits them: slice distances at record+0x54..0x60, multipliers '
                'at record+0x64..0x70',
            },
        )


class Nfs2SimTune(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'NFS2 SE flight, bounce, ground and collision reset tuning (`simtune.dat` in '
            '`GAMEDATA/SIM/CARDATA/CARDATA.VIV`, 232 bytes; the loose `GAMEDATA/CARMODEL/PC/SIMTUNE.DAT` is an '
            'identical copy). `Cars_Init` (nfs2sen.exe 0x43dbd0) loads it with 0x43e0a0, reading the file as a '
            'little-endian stream into two records of 0x74 bytes at 0x4df0a8, one per game style. Field names, '
            "types and order come from the developers' field descriptions `GAMEDATA/CARMODEL/PC/SIMTUNE.DES` "
            '(`Fixed` = 16.16 fixed point, `Integer` = int), which also embed a copy of the file',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        simulation = (
            Nfs2SimTuneRecord(),
            {'description': 'Record 0, used in simulation style (`.DES` heading "SIM MODE")'},
        )
        arcade = (
            Nfs2SimTuneRecord(),
            {
                'description': 'Record 1, used in arcade style and in Wild, which runs on the arcade model '
                '(`.DES` heading "ARCADE MODE")'
            },
        )

    def serializer_class(self):
        from serializers import JsonSerializer

        return JsonSerializer


def _ai_accel_table():
    return ArrayBlock(length=112, child=FixedPointBlock(length=2, fraction_bits=8, is_signed=True))


class Nfs2CarAiLevers(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'AI levers of one game style (`.DES` chains "Sim Mode Levers" / "Arcade Mode '
            'Levers", 232 bytes each): acceleration table, grip and turn rate. The loader (nfs2sen.exe 0x42b7b0) '
            'keeps those of the current style only: the table at car+0x408, grip at car+0x550, turn rate at '
            'car+0x554',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        acceleration_table = (
            _ai_accel_table(),
            {
                'description': '`.DES`: "Physics acceleration Table" / "Arcade acceleration Table", an `Import` '
                "record of 0xe0 bytes: 112 signed 16-bit values, 8.8 fixed point. Entry i is the AI car's "
                'acceleration at a speed of i m/s: nfs2sen.exe 0x42e7d0 reads entry abs(speed) >> 16 (car+0x39c, '
                'clamped to 0..111) and shifts it left by 8 into 16.16 (probably m/s²; mostly up to about 9.8 in the '
                "simulation tables, with single spikes up to 27, up to about 26 in the arcade ones). The values step down at each gear's top "
                'speed and are 0 from about the top speed on; none while a shift lasts. On load the table of car '
                'types below 15 is scaled by a factor of the type and style (0x42efc0: value = fixmul(value << 8, '
                'k) >> 8, factors at 0x4c4e38, 0.96 to 1.08)',
            },
        )
        grip = (
            _fixed(),
            {
                'description': '`.DES`: "Grip" (type `Fixed`). Read by the AI driving model (nfs2sen.exe 0x42d140) as '
                'the cap of a lateral correction, scaled by 1 + speed (car+0x2b8) * 0x62 / 0x10000. 24 to 40 in the '
                'simulation levers, 24 to 75 in the arcade ones',
            },
        )
        turn_rate = (
            _fixed(),
            {
                'description': '`.DES`: "Turn Rate". Read by the AI driving model (nfs2sen.exe 0x42d140) as the '
                'cap of a steering term. 0.8 in every file',
            },
        )


class Nfs2CarAi(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'NFS2 SE car AI data (`<car>.dat` in `GAMEDATA/SIM/CARDATA/CARDATA.VIV`, 524 '
            'bytes, one per racing car; each is listed twice in the archive, as identical copies). `Car_Init` loads '
            'it for every race car with nfs2sen.exe 0x42b7b0, reading the file as a little-endian stream into the '
            'car (addresses cited in the field descriptions). Field names, types and order come from the '
            "developers' field descriptions `GAMEDATA/SIM/CARDATA/MCF1.DES` (`Fixed` = 16.16 fixed point, "
            '`Integer` = int), a tree of records: chain "AI" with the fields, the chains "Sim Mode Levers" and '
            '"Arcade Mode Levers" (`Nfs2CarAiLevers`) in the middle; it also embeds a copy of `mcf1.dat`. Five '
            'cars (futr, dayt, chev, musc, mcf1) have identical files',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        ai_shift_duration = (
            _int(),
            {
                'description': '`.DES`: "AI Shift Duration (sim ticks)" (type `Integer`), car+0x3b4. A gear change '
                'starts the shift timer (car+0x3b8) with it, which the AI engine (nfs2sen.exe 0x42e9e0) counts down '
                'by the AI step factor; meanwhile the engine runs at 3000 rpm and the acceleration table gives '
                'nothing. 10, cala 14, mach 8',
            },
        )
        redline = (
            _fixed(),
            {
                'description': '`.DES`: "Redline" (type `Fixed`), car+0x3bc: rpm in 16.16 (6300 to 8600). The AI '
                'engine (nfs2sen.exe 0x42e9e0) sets the rpm from the speed within the gear, from 3000 rpm (0 in '
                "the first gear) up to this at the gear's top speed",
            },
        )
        gear_top_speeds = (
            ArrayBlock(length=7, child=_fixed()),
            {
                'description': '`.DES`: "Top Speed in each gear (m/s)" (an `Array` record, 7 elements of 4 bytes, '
                'no element type; the values are 16.16), car+0x3d0. Entry i is the top speed of forward gear i + 1 '
                'of the AI gearbox (car+0x2da, from 0), increasing; 0 = no such gear (5 or 6 gears used, the '
                "last entry is always 0). The AI shifts up above a gear's top speed when the next entry is not 0, "
                "and down below the previous gear's (nfs2sen.exe 0x42e9e0); the loader also stores 1 / the speed "
                'range of each gear at car+0x3ec. Top gears 80.5 to 105.6 m/s',
            },
        )
        simulation = (
            Nfs2CarAiLevers(),
            {'description': '`.DES` chain "Sim Mode Levers": used in simulation style (game style 0)'},
        )
        arcade = (
            Nfs2CarAiLevers(),
            {'description': '`.DES` chain "Arcade Mode Levers": used in the other game styles (arcade)'},
        )
        speed_factor = (
            _fixed(),
            {
                'description': '`.DES`: "Speed Factor" (type `Fixed`), the first of two, car+0x4e8. No reader of '
                'car+0x4e8 found in nfs2sen.exe. 1.0 in every file',
                'is_unknown': True,
            },
        )
        hi_handling_yaw = (
            _int(),
            {
                'description': '`.DES`: "Hi Handling Yaw" (type `Integer`), car+0x4f0. Upper bound of the yaw value '
                '(0x4d7e84) that nfs2sen.exe 0x427780 turns into a speed multiplier: 1 - (clamp(abs(yaw), low, high) '
                "- low) * handling importance / (high - low) * the personality's `handling_adjust` (`Nfs2Personality`). "
                '9 to 13',
            },
        )
        low_handling_yaw = (
            _int(),
            {
                'description': '`.DES`: "Low Handling Yaw" (type `Integer`), car+0x4f4. Lower bound of that yaw '
                'value, see `hi_handling_yaw`. 1 to 3',
            },
        )
        handling_importance = (
            _fixed(),
            {
                'description': '`.DES`: "Handling Importance (usually around 0 - 0.3)" (type `Fixed`). The loader '
                'stores it divided by (high - low handling yaw) at car+0x4f8; the speed multiplier of '
                'nfs2sen.exe 0x427780 goes down by this much at the high handling yaw (up for a negative value). '
                '-0.2 to 0.32',
            },
        )
        speed_factor_2 = (
            _fixed(),
            {
                'description': '`.DES`: "Speed Factor" (type `Fixed`), the second of two, car+0x560. nfs2sen.exe '
                '0x427800 multiplies the target speed (car+0x398) of cars that are not AI racers (car kind bit 8 '
                'clear) by it. 1.0 in every file',
            },
        )
        lane_slack_prob = (
            _int(),
            {
                'description': '`.DES`: "Lane Slack Prob" (type `Integer`), car+0x564. Chance of a lane change at '
                'a checked slice for cars that are not AI racers (nfs2sen.exe 0x42c1a0: a random 16-bit value r '
                "gives one when r * value >> 16 == 1, about 1 / value); AI racers use their personality's "
                '`new_slack_probability` (`Nfs2Personality`) instead. 40 in every file',
            },
        )

    def serializer_class(self):
        from serializers import JsonSerializer

        return JsonSerializer


class Nfs2TrafficGluePair(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A pair of glue factors (`.DES`: an `Array` record of 2 elements of 4 bytes without '
            'names, the values are 16.16). nfs2sen.exe 0x42bd60 multiplies element 0 of the chosen pairs into the '
            'speed glue of the race (0x4d7fa8, 1 / it at 0x4d7f9c), element 1 into the acceleration glue (0x4d7fb4, '
            '1 / it at 0x4d7fa4)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        speed_glue = (
            _fixed(),
            {
                'description': 'Factor of the speed glue (0x4d7fa8): when the AI racer is more than 30 slices away '
                "from the player, nfs2sen.exe 0x427460 multiplies its personality's `speed_glue` value by it "
                '(by 1 / it when the value is below 1), so a larger factor makes the glue stronger',
            },
        )
        acceleration_glue = (
            _fixed(),
            {
                'description': 'Factor of the acceleration glue (0x4d7fb4): nfs2sen.exe 0x427640 multiplies the '
                "personality's `acceleration_glue` value by it (by 1 / it when the value is below 1)",
            },
        )


class Nfs2TrafficGlue(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Glue factors of one race type (`.DES` chains "Single Race Glue Factors", '
            '"Tournament Mode Glue Factors", "Knock Out Mode Glue Factors"), 24 values. nfs2sen.exe 0x42bd60 picks '
            'the table by the race type and multiplies (16.16) the `overall` pair with one pair of each group: '
            'laps, game style, skill, traffic, opponents; element 0 of the product is the speed glue of the race, '
            'element 1 the acceleration glue',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        overall = (Nfs2TrafficGluePair(), _des('Overall', 'Always used'))
        two_laps = (Nfs2TrafficGluePair(), _des('Two Laps', 'In the chain "Laps": used in races of 2 laps'))
        four_laps = (Nfs2TrafficGluePair(), _des('Four Laps', 'In the chain "Laps": used in races of 4 laps'))
        eight_laps = (
            Nfs2TrafficGluePair(),
            _des('Eight Laps', 'In the chain "Laps": used for any other number of laps (the exe checks 2 and 4 only)'),
        )
        simulation = (
            Nfs2TrafficGluePair(),
            _des('Sim Mode', 'In the chain "Simulation Mode": used in simulation style (game style 0)'),
        )
        arcade = (
            Nfs2TrafficGluePair(),
            _des('Arcade Mode', 'In the chain "Simulation Mode": used in arcade style (game style 1, Wild included)'),
        )
        beginner = (
            Nfs2TrafficGluePair(),
            _des('Beg.', 'In the chain "Skill Level": used at skill level 0 (beginner)'),
        )
        advanced = (
            Nfs2TrafficGluePair(),
            _des('Advanced', 'In the chain "Skill Level": used at skill level 1 (expert)'),
        )
        no_traffic = (
            Nfs2TrafficGluePair(),
            _des('No Traffic', 'In the chain "Traffic": used in races without traffic cars'),
        )
        with_traffic = (
            Nfs2TrafficGluePair(),
            _des('With Traffic', 'In the chain "Traffic": used in races with traffic cars'),
        )
        one_opponent = (
            Nfs2TrafficGluePair(),
            _des('One Opponent', 'In the chain "Num Opponents": used in races with one AI racer'),
        )
        multi_opponents = (
            Nfs2TrafficGluePair(),
            _des('Multi Opponents', 'In the chain "Num Opponents": used in races with more AI racers'),
        )


class Nfs2AiLookAhead(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Look-ahead of one game style (`.DES` chains "Simulation Mode look ahead" / '
            '"Arcade Mode look ahead"). nfs2sen.exe 0x42bc40 keeps the pair of the current style only',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        max_lookahead = (
            _int(),
            _des(
                'max_lookahead:what is the max # of slices to look to find target direction',
                'Kept at 0x4d7fd4, the upper bound of the slices ahead in nfs2sen.exe 0x42de90',
            ),
        )
        look_ahead_factor = (
            _fixed(),
            _des(
                'look_ahead_factor:convert from speed to # slices ahead to calc target dir',
                'Kept at 0x4d7fd8, read by nfs2sen.exe 0x42de90',
            ),
        )


class Nfs2AiControl(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'AI physics parameters of the AI driving model (`.DES` chains "In Control AI '
            'Physics parameters" / "Out Of Control AI Physics parameters"), 11 values of type `Fixed`. nfs2sen.exe '
            '0x42bc40 stores them at 0x4d7fe0 (in control) and 0x4d800c (out of control)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        dlpos_to_dlvel = (
            _fixed(),
            _des(
                'dlpos_to_dlvel:delta lateral position to desired lateral velocity',
                'The out-of-control record says "(not used for ooc)"',
            ),
        )
        max_dlvel = (_fixed(), _des('max_dlvel:maximum desired lateral velocity'))
        dlvel_to_clacc = (_fixed(), _des('dlvel_to_clacc:delta desired lateral velocity to lateral acceleration'))
        max_clacc = (
            _fixed(),
            _des('NOT USED:---max_clacc:maximum lateral acceleration'),
        )
        dangle_to_dav = (_fixed(), _des('dangle_to_dav:delta angle to desired angular velocity'))
        max_dav = (_fixed(), _des('max_dav'))
        dav_to_aa = (_fixed(), _des('dav_to_aa:delta desired ang vel to angular acceleration'))
        max_aa = (
            _fixed(),
            _des('NOT USED:---max_aa:maximum desired angular acceleration'),
        )
        vel_limit_range = (_fixed(), _des('vel_limit_range:under this speed we limit lateral and ang vel'))
        lat_vel_limit_factor = (
            _fixed(),
            _des('lat_vel_limit_factor:limit lat vel by speed/vel_limit_range * this #'),
        )
        ang_vel_limit_factor = (
            _fixed(),
            _des('ang_vel_limit_factor:limit ang vel by speed/vel_limit_range * this #'),
        )


class Nfs2TrafficConfig(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'NFS2 SE AI and traffic configuration (`GAMEDATA/SIM/AI/TRAFCFG.DAT`, 452 bytes; '
            '`GAMEDATA/SIM/CARDATA/CARDATA.VIV` holds two identical copies, `trafcfg.dat` and `TRAFCFG.DAT`). '
            'nfs2sen.exe 0x42bb60 loads `trafcfg.dat` at the start of a race, reading it as a little-endian stream: '
            'the general part (0x42bbc0), the glue factors (0x42bd60) and the AI physics parameters (0x42bc40). '
            "Field names, types and order come from the developers' field descriptions "
            '`GAMEDATA/SIM/AI/TRAFCFG.DES` (`Fixed` = 16.16 fixed point, `Integer` = int; `Array` records have no '
            'element type, their values are 16.16), a tree of records: the chains "General AI Configuration '
            'Parameters", "Glue Factors" and "AI Physics Configuration Parameters"; it also embeds a copy of the '
            'file. `MTRAF.BAT` there compiled it into the exe (`bin2src trafcfg.dat trafcfg.c`)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        opp_desired_ahead = (
            _fixed(),
            _des(
                'opp_desired_ahead:desired speed at least= players speed + desired ahead',
                'm/s, 0x4d7e8c: nfs2sen.exe 0x427800 raises the target speed of an AI racer to at least the '
                "player's speed + this",
            ),
        )
        traffic_density = (
            _int(),
            _des('NOT USED:---Traffic Density (larger number creates less density)', 'Kept at 0x4d7e90'),
        )
        num_traffic_cars = (
            _int(),
            _des('Number of traffic cars', 'Kept at 0x4d7e94; no reader found in nfs2sen.exe'),
        )
        traffic_speed_factors = (
            ArrayBlock(length=4, child=_fixed()),
            _des(
                'Traffic Speed Factors',
                'An `Array` of 4, 0x4d7e98: nfs2sen.exe 0x427280 gives a car one of them at random (car+0x3c8)',
            ),
        )
        traffic_base_speed = (
            _fixed(),
            _des(
                'Traffic Base Speed (km/h) (origianlly 150 kmh)',
                'The loader multiplies it by 0x471c (1 / 3.6) into m/s, 0x4d7ea8. The target speed of a car that '
                "is not an AI racer is the mean of this and the player's speed (nfs2sen.exe 0x427800, 0x42b4c0)",
            ),
        )
        lane_slack = (
            ArrayBlock(length=4, child=_fixed()),
            _des(
                'Lane Slack: How close the cars drive along the centre line',
                'An `Array` of 4, in m, 0x4d7eac: nfs2sen.exe 0x42c120 gives a car that is not an AI racer one of '
                "them at random as its lateral offset (car+0x3a4; AI racers use their personality's `lane_slack`)",
            ),
        )
        single_race_glue = (
            Nfs2TrafficGlue(),
            {'description': '`.DES` chain "Single Race Glue Factors" (in "Glue Factors"): used for race type 0'},
        )
        tournament_glue = (
            Nfs2TrafficGlue(),
            {'description': '`.DES` chain "Tournament Mode Glue Factors": used for race type 1'},
        )
        knockout_glue = (
            Nfs2TrafficGlue(),
            {'description': '`.DES` chain "Knock Out Mode Glue Factors": used for race type 2'},
        )
        latvelcalc_lookahead = (
            _int(),
            _des(
                'latvelcalc_lookahead: how far do we look ahead to calc lateral velocity(sl)',
                'In the chain "AI Physics Configuration Parameters". Slices, 0x4d7fcc, read by nfs2sen.exe 0x42da60',
            ),
        )
        min_lookahead = (
            _int(),
            _des(
                'min_lookahead:what is the min # of slices to look ahead to find trget direc',
                'Kept at 0x4d7fd0, read by nfs2sen.exe 0x42de90',
            ),
        )
        simulation_look_ahead = (
            Nfs2AiLookAhead(),
            {'description': '`.DES` chain "Simulation Mode look ahead": used in simulation style (game style 0)'},
        )
        arcade_look_ahead = (
            Nfs2AiLookAhead(),
            {'description': '`.DES` chain "Arcade Mode look ahead": used in the other game styles'},
        )
        skid_value = (
            _fixed(),
            _des('skid_value:for calculating front skid/rear skid', 'Kept at 0x4d7fdc, read by nfs2sen.exe 0x42d140'),
        )
        in_control = (
            Nfs2AiControl(),
            {'description': '`.DES` chain "In Control AI Physics parameters", 0x4d7fe0'},
        )
        out_of_control = (
            Nfs2AiControl(),
            {'description': '`.DES` chain "Out Of Control AI Physics parameters", 0x4d800c'},
        )

    def serializer_class(self):
        from serializers import JsonSerializer

        return JsonSerializer


class Nfs2PersonalityGrid(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Personality letters of the grid slots, one row of 12 per race kind (`.DES` chain '
            '"Grid Assignments": 48 `Char` records "slot 0" .. "Slot 11" in 4 chains). nfs2sen.exe 0x42b580 gives '
            'every AI racer the personality of the letter at its slot (race cars - 1 - its line-up position) in '
            'the row of the race (0x42bf20: knockout row 0, tournament 1, single race 2 with one AI racer, 3 with '
            "more); 0x451b60 turns the letter into the personality index (letter - 'a', 0 outside 'a'..'n')",
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        knockout = (
            UTF8Block(length=12),
            {'description': '`.DES` chain "Grid Assignment - KnockOut Mode": row 0, race type 2. "abcdefghijkl"'},
        )
        tournament = (
            UTF8Block(length=12),
            {'description': '`.DES` chain "Grid Assignment - Tournament Mode": row 1, race type 1. "abcdefghijkl"'},
        )
        single_race_one_opponent = (
            UTF8Block(length=12),
            {
                'description': '`.DES` chain "Grid Assignment - Single Race - One Opponent": row 2, single race with '
                'one AI racer. "mmmmmmmmmmmm"'
            },
        )
        single_race_multi_opponent = (
            UTF8Block(length=12),
            {
                'description': '`.DES` chain "Grid Assignment - Single Race - Multi Opponent": row 3, single race with '
                'more AI racers. "abcdefghijkl"'
            },
        )


class Nfs2Personality(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A driver personality of the AI racers (`.DES` chains "Car A - ..." .. "Car M: '
            '..." in "Personalities", 228 bytes). nfs2sen.exe 0x451bd0 keeps it as it is in the file, the letter '
            'and the 3 unnamed bytes as one int (0x4c6cc0 + index * 0xe4, offsets cited in the field descriptions)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        letter = (
            UTF8Block(length=1),
            _des(
                'Car',
                "Type `Char`: the personality's letter. The loader hangs when the letters are not 'a', 'b', ... "
                "'m' in file order",
            ),
        )
        unnamed = (
            UTF8Block(length=3),
            {
                'description': '`.DES`: three `Char` records "Unnamed", the letter again in every file. Read and '
                'dropped by the loader',
            },
        )
        speed_glue = (
            ArrayBlock(length=21, child=_fixed()),
            _des(
                'Speed Glue Values',
                'Named "Glue Values" in every personality but A. An `Array` of 21, 16.16, +0x04. nfs2sen.exe '
                "0x427460 multiplies the AI racer's target speed by entry (the car's slice - the player's slice) / "
                '15 + 10, clamped to 0..20: entry 10 when level with the player, the lower ones behind him, the '
                'higher ones ahead (2.8 .. 0.68 in A); more than 30 slices away it is first multiplied by the speed '
                'glue of the race (by 1 / it when below 1, see `Nfs2TrafficConfig`)',
            ),
        )
        acceleration_glue = (
            ArrayBlock(length=21, child=_fixed()),
            _des(
                'Acc Glue Values',
                'An `Array` of 21, 16.16, +0x58, indexed like `speed_glue` (nfs2sen.exe 0x427640) and multiplied by '
                'the acceleration glue of the race (by 1 / it when below 1). 9.0 at entry 0 and 1.0 elsewhere in every '
                'personality but M (8, 5, 3, 2 at entries 1 .. 4)',
            ),
        )
        speed_factor_adjust = (
            _fixed(),
            _des(
                'Speed Factor Adjust: the speed factor for this car is multiplied by this value',
                '+0xac; no reader found in nfs2sen.exe. 0.78 (A) up to 1.0 (L, M)',
            ),
        )
        handling_adjust = (
            _fixed(),
            _des(
                'Handling Adjust: effects of handling are multiplied by this value',
                '+0xb0: nfs2sen.exe 0x427780 multiplies the handling slowdown by it (see `Nfs2CarAi` '
                '`hi_handling_yaw`)',
            ),
        )
        block_look_behind = (
            _int(),
            _des('Block Look Behind', 'Type `Integer`, +0xb4; no reader found in nfs2sen.exe'),
        )
        block_look_ahead = (
            _fixed(),
            _des('Block Look Ahead:', '+0xb8, compared with a distance by nfs2sen.exe 0x42a3c0'),
        )
        max_lane_change_speed = (
            _fixed(),
            _des(
                'Maximum Lane change speed - default = 3.8',
                '+0xbc: the cap of the lane change speed (nfs2sen.exe 0x42eec0; 3.2 for cars that are not AI racers)',
            ),
        )
        lane_change_speed_factor = (
            _fixed(),
            _des(
                'Lane change speed factor (def=.3) speed * this number = lane change speed',
                '+0xc0, nfs2sen.exe 0x42eec0 (0.25 for cars that are not AI racers)',
            ),
        )
        look_ahead = (
            _int(),
            _des(
                'Look Ahead: this is how far ahead the opponent will look for oncoming traffic',
                'Type `Integer`, +0xc4: a distance in m (nfs2sen.exe 0x429760; 30 for other cars, five times as far '
                'when the speeds differ by more than 25 m/s)',
            ),
        )
        lane_slack = (
            ArrayBlock(length=4, child=_fixed()),
            _des(
                'Lane Slack (m)',
                'An `Array` of 4, 16.16, +0xc8: nfs2sen.exe 0x42c120 gives the car one of them at random as its '
                'lateral offset (car+0x3a4; other cars use `Nfs2TrafficConfig` `lane_slack`)',
            ),
        )
        new_slack_probability = (
            _int(),
            _des(
                'New Slack probability:smaller # = greater frequency of change: default=40',
                '+0xd8: chance of a new lane slack at a checked slice, about 1 / value (nfs2sen.exe 0x42c1a0; '
                'other cars use `Nfs2CarAi` `lane_slack_prob`); 0 = never',
            ),
        )
        psycho_trigger_count = (
            _int(),
            _des(
                'Psycho Trigger Count (how many times do you have to hit to piss off)',
                '+0xdc: nfs2sen.exe 0x42c2e0 counts the hits of one human car at expert skill (car+0x540); above '
                'this count the car turns psycho for `psycho_time`',
            ),
        )
        psycho_time = (
            _int(),
            _des(
                'Psycho Time (How long will this guy remain psycho ?)(seconds * 8)',
                '+0xe0, set to car+0x53c by nfs2sen.exe 0x42c2e0',
            ),
        )


_NFS2_PERSONALITIES = {
    'a': 'Car A - The brit very clean and fast glue keeps him at front of pack',
    'b': 'Car B - This is the "ice-man" - fast, but more aggressive',
    'c': 'Car C - stink on shit aggressive and personal glue make him stick to player mor',
    'd': 'Car D - no name generic',
    'e': 'Car E: Sticky guy, not aggressive but clings to you',
    'f': 'Car F: Floater',
    'g': 'Car G "the stragler"',
    'h': 'Car H: Car used in Head to Head Mode',
    'i': 'Car I: Undefined',
    'j': 'Car J: Undefined',
    'k': 'Car K: Undefined',
    'l': 'Car L: Undefined',
    'm': 'Car M: Single Opponent Mode',
}


def _personality(letter: str, more: str = ''):
    return (
        Nfs2Personality(),
        {
            'description': f'`.DES` chain "{_NFS2_PERSONALITIES[letter]}"'
            + (f'. {more}' if more else '')
            + f'. Personality {ord(letter) - 0x61}, letter "{letter}"'
        },
    )


class Nfs2Personalities(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'NFS2 SE driver personalities of the AI racers (`GAMEDATA/SIM/AI/PRSONAL.DAT`, '
            '3012 bytes; `prsonal.dat` in `GAMEDATA/SIM/CARDATA/CARDATA.VIV` is an identical copy): the grid '
            'assignments, then 13 personalities "a" .. "m". nfs2sen.exe 0x451ba0 points 0x4e082c / 0x4e0828 at '
            'the copy compiled into the exe (0x4c6c90 grid letters, 0x4c6cc0 personalities; `MPERS.BAT`: `bin2src '
            'prsonal.dat griddata.c 48 perdata.c`) and 0x451bd0 overwrites it from `prsonal.dat`, reading the file '
            "as a little-endian stream. Field names, types and order come from the developers' field descriptions "
            '`GAMEDATA/SIM/AI/PRSONAL.DES` (`Fixed` = 16.16 fixed point, `Integer` = int, `Char` = 1 byte; '
            '`Array` records have no element type, their values are 16.16), a tree of records: the chains "Grid '
            'Assignments" and "Personalities" (one chain per personality, named after the letter and a '
            'description); it also embeds a copy of the file',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        grid = (Nfs2PersonalityGrid(), {'description': '`.DES` chain "Grid Assignments"'})
        car_a = _personality('a')
        car_b = _personality('b')
        car_c = _personality('c', 'The name is cut off by the 80 bytes of the `.DES` record name')
        car_d = _personality('d')
        car_e = _personality('e')
        car_f = _personality('f')
        car_g = _personality('g')
        car_h = _personality(
            'h', 'Yet single races with one AI racer use "m" (grid row 2); "h" is slot 7 of the other rows'
        )
        car_i = _personality('i')
        car_j = _personality('j')
        car_k = _personality('k')
        car_l = _personality('l')
        car_m = _personality('m', 'Every slot of the single race row with one AI racer')

    def serializer_class(self):
        from serializers import JsonSerializer

        return JsonSerializer


# ---------------------------------------------------------------------------------------------------------------------
# NFS3 car physics: carp.txt (GameData/CarModel/<car>/car.viv), a text file read by nfs3.exe 0x4b1380
# ---------------------------------------------------------------------------------------------------------------------

# nfs3.exe 0x4af3b0: the parser's field table, in switch case order: (key, number). A label line selects the first
# entry whose key and "(number)" it contains (0x4b0940), after its spaces are removed and its letters lower-cased
NFS3_CARP_FIELD_TABLE = (
    ('serialnu', 0), ('carclass', 1), ('mass[kg]', 2), ('numberof', 3), ('numberof', 75), ('gearshif', 4),
    ('shiftbli', 5), ('brakebli', 6), ('citytorp', 7), ('citytorp', 76), ('gearrati', 8), ('gearrati', 77),
    ('geareffi', 9), ('geareffi', 78), ('torquecu', 10), ('finalgea', 11), ('finalgea', 79), ('nimumrpm', 12),
    ('enginere', 13), ('mumveloc', 14), ('topspeed', 15), ('frontdri', 16), ('usesanti', 17), ('kingdece', 18),
    ('frontbia', 19), ('gasincre', 20), ('gasdecre', 21), ('brakeinc', 22), ('brakedec', 23), ('wheelbas', 24),
    ('gripbias', 25), ('powerste', 26), ('ringacce', 27), ('turninra', 28), ('turnoutr', 29), ('laterala', 30),
    ('aerodyna', 31), ('gasofffa', 32), ('gtransfe', 33), ('urningci', 34), ('ecsfront', 35), ('pecsrear', 36),
    ('tirewear', 37), ('slidemul', 38), ('spinvelo', 39), ('slidevel', 40), ('slideass', 41), ('pushfact', 42),
    ('lowturnf', 43), ('highturn', 44), ('rollfact', 45), ('roadbump', 46), ('spoilerf', 47), ('leractiv', 48),
    ('gradualt', 49), ('mturncut', 50), ('pturncut', 51), ('mturnspe', 52), ('pturnspe', 53), ('eturnspe', 54),
    ('subdivid', 55), ('cameraar', 56), ('odydamag', 57), ('inedamag', 58), ('iondamag', 59), ('enginetu', 60),
    ('brakebal', 61), ('eeringsp', 62), ('ratfacto', 63), ('tiffness', 64), ('aerofact', 65), ('irefacto', 66),
    ('aiacc0ac', 67), ('aiacc1ac', 68), ('aiacc2ac', 69), ('aiacc3ac', 70), ('aiacc4ac', 71), ('aiacc5ac', 72),
    ('aiacc6ac', 73), ('aiacc7ac', 74),
)  # fmt: skip

# number readers of a value line: the characters that make a number; any other character ends it (0x4b0700 int,
# 0x4b07b0 its low byte, 0x4b07d0 float, 0x4b08b0 the float as 16.16)
_CARP_NUMBER_CHARS = {
    'int': frozenset(b'0123456789-'),
    'byte': frozenset(b'0123456789-'),
    'float': frozenset(b'0123456789.-'),
    'fixed': frozenset(b'0123456789.-'),
}
_CARP_LINE_BUFFER = 2000  # the parser's line buffer (0x4b1380), zeroed once per file


class _CarpTextValue:
    """Marks a value of a carp.txt value line. `reader` names the nfs3.exe number reader"""

    reader = 'int'
    is_text_value = True

    @property
    def size_doc_str(self):
        return '1 line'

    def read(self, ctx, name: str = '', read_bytes_amount=None):
        raise NotImplementedError('carp.txt values are read by Nfs3CarPhysics')

    def write(self, data, ctx=None, name: str = '') -> bytes:
        raise NotImplementedError('carp.txt values are written by Nfs3CarPhysics')

    def estimate_packed_size(self, data, ctx=None):
        raise NotImplementedError('carp.txt values are written by Nfs3CarPhysics')


class CarpTextInt(_CarpTextValue, IntegerBlock):
    """An integer of a carp.txt value line"""

    reader = 'int'

    def __init__(self, **kwargs):
        super().__init__(length=4, is_signed=True, **kwargs)

    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Integer in text, read with `atoi` (nfs3.exe 0x4b0700): digits and `-` make the '
            'number, any other character ends it (a `.` too: `128.000000` reads 128)',
        }


class CarpTextByte(_CarpTextValue, IntegerBlock):
    """An integer of a carp.txt value line, of which the game keeps the low byte"""

    reader = 'byte'

    def __init__(self, **kwargs):
        super().__init__(length=1, is_signed=False, **kwargs)

    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Integer in text, read as `atoi` and kept as a byte (its low 8 bits, nfs3.exe '
            '0x4b07b0)',
        }


class CarpTextFloat(_CarpTextValue, DecimalBlock):
    """A decimal number of a carp.txt value line"""

    reader = 'float'

    def __init__(self, **kwargs):
        super().__init__(length=4, **kwargs)

    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Decimal number in text, e.g. `1625.000000` (the shipped files write 6 decimals), '
            'read with `atof` into a float (nfs3.exe 0x4b07d0): digits, `.` and `-` make the number, any other '
            'character ends it',
        }


class CarpTextFixed(_CarpTextValue, DecimalBlock):
    """A decimal number of a carp.txt value line that the game keeps as 16.16 fixed point"""

    reader = 'fixed'

    def __init__(self, **kwargs):
        super().__init__(length=4, **kwargs)

    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'Decimal number in text, kept by the game as 16.16 fixed point: the float times '
            '65536, rounded (nfs3.exe 0x4b08b0)',
        }


class CarpTextArray(ArrayBlock):
    """Several numbers of one carp.txt value line"""

    is_text_value = True

    @property
    def reader(self):
        return self.child.reader

    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': f'{self._length} numbers in one value line, separated by commas (any character '
            'that is not part of a number separates them)',
        }

    @property
    def size_doc_str(self):
        return '1 line'

    def read(self, ctx, name: str = '', read_bytes_amount=None):
        raise NotImplementedError('carp.txt values are read by Nfs3CarPhysics')

    def write(self, data, ctx=None, name: str = '') -> bytes:
        raise NotImplementedError('carp.txt values are written by Nfs3CarPhysics')

    def estimate_packed_size(self, data, ctx=None):
        raise NotImplementedError('carp.txt values are written by Nfs3CarPhysics')


def _carp_atoi(text: str) -> int:
    """Watcom `atoi` of the digits / `-` collected by 0x4b0700 (32-bit, wraps)"""
    match = re.match(r'[+-]?\d+', text)
    if not match:
        return 0
    value = int(match.group(0)) & 0xFFFFFFFF
    return value - (1 << 32) if value >= 1 << 31 else value


def _carp_strtod(text: str) -> float:
    """`strtod` of the digits / `.` / `-` collected by 0x4b07d0 (the game stores it as a float)"""
    match = re.match(r'[+-]?(\d+\.?\d*|\.\d+)', text)
    return float(match.group(0)) if match else 0.0


def _carp_number(text: str, reader: str):
    if reader == 'int':
        return _carp_atoi(text)
    if reader == 'byte':
        return _carp_atoi(text) & 0xFF
    return _carp_strtod(text)


def _carp_item(buf: bytearray, index: int, chars) -> str:
    """The index-th number of the line buffer as 0x4b0700 / 0x4b07d0 collect it: characters of `chars` join the
    current number, any other one (the line's terminating 0 and whatever follows it in the buffer too) ends it"""
    i = field = 0
    num = bytearray()
    while field <= index:
        c = buf[i] if i < len(buf) else 0
        if c in chars:
            if field == index:
                num.append(c)
        else:
            field += 1
        i += 1
    return num.decode('ascii')


def _carp_find_field(label: bytes):
    """nfs3.exe 0x4b0940: the table index of the first field whose key and "(number)" the label contains"""
    for i, (key, number) in enumerate(NFS3_CARP_FIELD_TABLE):
        if key.encode() in label and f'({number})'.encode() in label:
            return i
    return None


def nfs3_carp_exe_read(raw: bytes, readers):
    """Reads carp.txt as nfs3.exe 0x4b1380 does: label lines select a field, the next value line fills it once.
    `readers[table index]` = (reader, count). Returns {table index: (values, (start, end) of the value line)};
    the values are the numbers as written (floats as doubles; the game rounds them to floats)"""
    result = {}
    length = len(raw)
    if length == 0:
        return result
    buf = bytearray(_CARP_LINE_BUFFER)
    pos = 0
    selected = None
    while pos < length - 1:
        # 0x4b09d0: skip 0 / CR / LF, then copy up to CR / LF without spaces, A-Z lower-cased, never past length - 1
        c = raw[pos]
        while not ((c != 0 and c != 13 and c != 10) or pos >= length - 1):
            pos += 1
            c = raw[pos]
        start = pos
        n = 0
        while c != 13 and c != 10 and pos < length - 1:
            if c != 32 and n < _CARP_LINE_BUFFER - 1:
                buf[n] = c + 32 if 65 <= c <= 90 else c
                n += 1
            pos += 1
            c = raw[pos]
        buf[n] = 0
        end = pos
        # 0x4b0900: a value line starts with a digit or '-'
        if not (48 <= buf[0] <= 57 or buf[0] == 45):
            selected = _carp_find_field(bytes(buf[: buf.index(0)]))
            continue
        if selected is None or selected in result:
            selected = None
            continue
        reader, count = readers[selected]
        chars = _CARP_NUMBER_CHARS[reader]
        values = [_carp_number(_carp_item(buf, k, chars), reader) for k in range(count)]
        result[selected] = (values, (start, end))
        selected = None
    return result


def _carp_format_float(value: float, decimals: int = 6) -> str:
    """Fixed-point text of a float: `decimals` digits (the files' style), more when the game would read another
    float from it (no exponent: the game's reader would stop at the `e`)"""
    value = float(value)
    target = struct.unpack('<f', struct.pack('<f', value))[0] if math.isfinite(value) else 0.0
    for d in range(decimals, 13):
        text = f'{value:.{d}f}'
        if struct.unpack('<f', struct.pack('<f', float(text)))[0] == target:
            return text
    return f'{value:.12f}'


def _carp_format_item(value, reader: str, old_item: str = None) -> str:
    """A changed value in the style of the item it replaces: its number of decimals, a whole number staying whole"""
    if reader in ('int', 'byte'):
        return str(int(round(value)))
    if old_item is not None:
        match = re.fullmatch(r'-?\d*\.(\d+)', old_item)
        if match:
            return _carp_format_float(value, len(match.group(1)))
        if re.fullmatch(r'-?\d+', old_item) and float(value).is_integer():
            return str(int(value))
    return _carp_format_float(value)


# the labels of the shipped files (identical in all 16 cars), written for fields missing from the text
_NFS3_CARP_LABELS = {
    0: 'Serial Number', 1: 'Car Classification', 2: 'mass [kg]',
    3: 'number of gears (reverse + neutral + forward gears)', 75: 'number of gears (automatic, r, n, forward)',
    4: 'gear shift delay (ticks)', 5: 'shift blip in rpm (size 8)', 6: 'brake blip in rpm (size 8)',
    7: 'velocity to rpm ratio (size 8)', 76: 'velocity to rpm ratio automatic(size 8)', 8: 'gear ratios (size 8)',
    77: 'gear ratios automatic (size 8)', 9: 'gear efficiency (size 8)', 78: 'gear efficiency automatic (size 8)',
    10: 'torque curve (size 41) in 256rpm increments', 11: 'final gear', 79: 'final gear automatic',
    12: 'engine minimum rpm', 13: 'engine redline in rpm', 14: 'maximum velocity of car [m/s]',
    15: 'top speed cap [m/s]', 16: 'front drive ratio', 17: 'Uses Antilock Brake System',
    18: 'maximum braking deceleration', 19: 'front bias brake ratio', 20: 'gas increasing curve',
    21: 'gas decreasing curve', 22: 'brake increasing curve', 23: 'brake decreasing curve', 24: 'wheel base',
    25: 'front grip bias', 26: 'power steering (boolean)', 27: 'minimum steering acceleration', 28: 'turn in ramp',
    29: 'turn out ramp', 30: 'lateral acceleration grip multiplier', 31: 'aerodynamic downforce multiplier',
    32: 'gas off factor', 33: 'g transfer factor', 34: 'turning circle radius', 35: 'tire specs front',
    36: 'tire specs rear', 37: 'tire wear', 38: 'Slide Multiplier', 39: 'Spin Velocity Cap', 40: 'Slide Velocity Cap',
    41: 'Slide Assistance Factor', 42: 'Push Factor',
    43: 'Low Turn Factor (the lower the figure, the better the turn)',
    44: 'High Turn Factor (the lower the figure, the better the turn)', 45: 'pitch roll factor',
    46: 'road bumpiness factor', 47: 'spoiler function type', 48: 'spoiler activation speed [m/s]',
    49: 'gradual turn cutoff', 50: 'medium turn cutoff', 51: 'sharp turn cutoff', 52: 'medium turn speed modifier',
    53: 'sharp turn speed modifier', 54: 'extreme turn speed modifier', 55: 'subdivide level', 56: 'camera arm',
    57: 'Body Damage', 58: 'Engine Damage', 59: 'Suspension Damage', 60: 'Engine Tuning', 61: 'Brake Balance',
    62: 'Steering Speed', 63: 'Gear Rat Factor', 64: 'Suspension Stiffness', 65: 'Aero Factor', 66: 'Tire Factor',
    **{67 + k: f'AI ACC{k} acceleration table section' for k in range(8)},
}  # fmt: skip

# the default carp of nfs3.exe (0x55f874): the values of fields missing from the file (0x4b0bb0)
_NFS3_CARP_DEFAULT_AI_ACC = [
    40.0, 33.46, 17.689, 10.68, 7.64, 6.39, 6.14, 6.1, 5.99, 6.04, 6.2, 6.19, 6.04, 6.06, 6.09, 6.17, 6.4, 6.36, 6.25,
    6.48, 7.3, 8.59, 9.65, 10.22, 10.18, 9.8, 9.1, 7.76, 6.74, 6.47, 6.41, 6.4, 6.28, 5.81, 5.25, 5.07, 5.08, 5.14,
    5.3, 5.28, 5.21, 5.17, 5.07, 5.0, 4.97, 4.8, 4.4, 4.08, 4.01, 4.06, 4.23, 4.48, 4.56, 4.74, 5.49, 5.8, 5.39, 5.61,
    5.84, 4.7, 3.2, 2.35, 2.19, 3.03, 4.3, 5.01, 5.33, 1.77,
] + [0.0] * 44  # fmt: skip


def _carp_tuning_note(slider: str) -> str:
    return (
        f'The {slider} tuning slider (game setup car +0x40..+0x58, Carp_TuneCar 0x4a78d6, single player races of '
        'race type 0 only; AI cars, multiplayer and race types 1 / 2 get the default tuning 0x55d024)'
    )


# carp.txt fields in the order of the shipped files: (name, "(n)", offset in the game's carp (None: not kept), block,
# default (0x55f874), description)
_NFS3_CARP_FIELDS = (
    ('serial_number', 0, None, CarpTextInt(), None,
     'Serial number of the car (2 to 49, one per car). The parser returns it through its fourth argument, which '
     'Car_LoadSpecs (0x42c2a0) leaves 0: the game does not keep it'),
    ('car_class', 1, 0x000, CarpTextInt(), 0,
     'Car class: 0 (Diab, Elni, Fm50, Jxjr, Lcop, Merc, Peln, Scig), 1 (Corv, Cout, Vcop, f355), 2 (Amd7, Jxk8, '
     'Sl60), 3 (Knoc). Not read by the ported physics; no reader identified in nfs3.exe. Missing: 0 (the word before '
     'the default carp, 0x55f3c8)'),
    ('mass', 2, 0x004, CarpTextFloat(), 1000.0,
     'Mass in kg (1000 to 5000). Drive acceleration of gear g (car+0x568.., Carp_TuneCar 0x4a78d6) = '
     'velocity_to_rpm_ratio[g] / mass x 0.1 x gear_efficiency[g], in m/s² per N·m of torque. The body (Car_Reset '
     '0x42bcb0) gets this mass, x 3 with the heavy cars option or as a cop player, divided for AI racers'),
    ('num_gears', 3, 0x008, CarpTextInt(), 8,
     'Number of gears of the manual gearbox: reverse + neutral + forward (7 or 8; the gear tables have 8 entries: '
     'gear 0 reverse, 1 neutral, 2.. forward); gear num_gears - 1 is the top gear. Read by the manual shift (0x48f6e0), '
     'the per gear values and the drag (0x4a78d6, from the top gear), the automatic gearbox (0x4a90a0). With the '
     'automatic gearbox Carp_TuneCar replaces it with `num_gears_auto`'),
    ('num_gears_auto', 75, 0x00c, CarpTextInt(), 8,
     'Number of gears of the automatic gearbox (reverse, neutral, forward; 6 to 8). A player driving with the '
     'automatic (unless game setup flag 4) gets the automatic gear set: Carp_TuneCar (0x4a78d6) copies this, '
     '`final_gear_auto`, `vel_to_rpm_auto`, `gear_ratio_auto` and `gear_efficiency_auto` over the manual ones'),
    ('shift_delay', 4, 0x010, CarpTextInt(), 8,
     'Gear shift time in physics steps (32 per second; 4 to 16): every shift starts the shift timer (car+0x510) at '
     'it, counted down once a step (0x4a9bc4). While it runs the engine gives no drive force, only the drag, and the '
     'rpm moves alone (0x4aaed1): shifting down it gets `shift_blip` / `brake_blip`, shifting up it rises by 75 per '
     'step, 50 when this is above 4, 25 with `spoiler_type` 8 (doubled above the redline; the exe subtracts a '
     'negative step). AI cars read it too (0x4061b0)'),
    ('shift_blip', 5, 0x014, CarpTextArray(CarpTextInt(), 8), [300, 0, 275, 250, 200, 175, 150, 0],
     'Rpm blip of a down-shift by target gear (0 reverse, 1 neutral, 2.. forward): added to the rpm every physics '
     'step of the shift while the gas is on and the brake at most 64 of 255, clamped to minimum rpm .. redline '
     '(0x4aaed1; `brake_blip` with more brake). In the air the rpm target also gets shift_blip[2] (carp+0x1c)'),
    ('brake_blip', 6, 0x034, CarpTextArray(CarpTextInt(), 8), [300, 0, 275, 250, 200, 175, 150, 0],
     'Rpm blip of a down-shift while braking (brake above 64 of 255) by target gear, as `shift_blip` (0x4aaed1)'),
    ('vel_to_rpm', 7, 0x094, CarpTextArray(CarpTextFloat(), 8), [0.0] * 8,
     'Engine rpm per m/s of forward speed in each gear (0 reverse, negative; 1 neutral, 0; 2.. forward): rpm = speed '
     'x ratio, the speed at the redline = redline / ratio. The shipped files have gear ratio x final gear x 60 / (2 '
     'pi x rear tyre radius from `tire_rear`), e.g. Diab 2.31 x 3.8319 x 27.611 = 244.40; the game reads only this '
     'table, never `gear_ratio` / `final_gear` / the tyres. Read by the drive of each gear (see `mass`), the drag '
     '(Carp_TuneCar 0x4a78d6), the automatic gearbox (0x4a90a0), the engine (0x4aaed1). Gear ratio tuning slider t: x '
     't (gears below `num_gears`). With the automatic gearbox Carp_TuneCar replaces it with `vel_to_rpm_auto`'),
    ('vel_to_rpm_auto', 76, 0x0b4, CarpTextArray(CarpTextFloat(), 8), [0.0] * 8,
     '`vel_to_rpm` of the automatic gearbox, copied over it by Carp_TuneCar (0x4a78d6) when the player drives with '
     'the automatic (unless game setup flag 4)'),
    ('gear_ratio', 8, 0x054, CarpTextArray(CarpTextFloat(), 8), [1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
     'Gearbox ratio of each gear (0 reverse, 1 neutral, 2.. forward). Not read by the physics: Carp_TuneCar only '
     'copies the automatic set over it; `vel_to_rpm` has the ratios combined with the final gear and the tyre size'),
    ('gear_ratio_auto', 77, 0x074, CarpTextArray(CarpTextFloat(), 8), [1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
     '`gear_ratio` of the automatic gearbox, copied over it by Carp_TuneCar (not read otherwise)'),
    ('gear_efficiency', 9, 0x0d4, CarpTextArray(CarpTextFloat(), 8), [1.0] * 8,
     'Efficiency of each gear (0 reverse, 1 neutral, 2.. forward): a factor of the gear\'s drive acceleration (see '
     '`mass`). The drag coefficient (0x4a78d6) divides it out: at `max_velocity` the air drag is 0.98 x the top '
     'gear\'s drive at efficiency 1, so the car reaches `max_velocity` with a top gear efficiency of 0.98 or more. '
     'Game setup flag 1: at least 1. With the automatic gearbox Carp_TuneCar replaces it with '
     '`gear_efficiency_auto`'),
    ('gear_efficiency_auto', 78, 0x0f4, CarpTextArray(CarpTextFloat(), 8), [1.0] * 8,
     '`gear_efficiency` of the automatic gearbox, copied over it by Carp_TuneCar (0x4a78d6) with the automatic'),
    ('torque', 10, 0x114, CarpTextArray(CarpTextFloat(), 41),
     [float(x) for x in range(10, 101, 10)] + [100.0] * 21 + [90.0, 80.0, 70.0, 60.0, 50.0, 40.0] + [30.0] * 4,
     'Engine torque in N·m by rpm in steps of 256 rpm (entry i at i x 256 rpm, 0 to 10240 rpm): the engine '
     '(0x4a8a99) interpolates it linearly at rpm / 256 (clamped to 0..40); the drag computation (0x4a78d6) takes '
     'entry trunc(rpm / 256) as it is. Drive acceleration (0x4aaed1) = torque x the gear\'s drive (see `mass`), at '
     'most 10 m/s² in 1st gear (gear 2), 8 in the others, -6 in reverse, x throttle x (1 + 0.6 x |slip ratio|, at '
     'most 1.5). Engine tuning slider t: entry i += (t - 1) x -0.1 x entry x (lo - i) / (hi - lo), lo = (redline + '
     'min rpm) / 2 / 256 + 3, hi = redline / 256 + 3 (the curve tilts about lo); game setup flag 1: x 1.75'),
    ('final_gear', 11, 0x1b8, CarpTextFloat(), 4.0,
     'Final drive ratio. Not read by the physics (`vel_to_rpm` includes it); with the automatic gearbox Carp_TuneCar '
     'copies `final_gear_auto` over it'),
    ('final_gear_auto', 79, 0x1bc, CarpTextFloat(), 4.0,
     '`final_gear` of the automatic gearbox. When the file lacks it, the game writes the default (4.0) into '
     '`final_gear` instead (0x4b0db1 stores to carp+0x1b8) and leaves this one as it was'),
    ('min_rpm', 12, 0x1c0, CarpTextInt(), 750,
     'Engine minimum (idle) rpm (720 to 1350): the rpm never falls below it; the rpm target is redline x throttle '
     'but at least this; below it the drive is the torque at this rpm (0x4aaed1). Also read by the automatic reverse '
     '(0x4a97cb: neutral below this + 50), the rpm of a car not upright (0x4ae4c1: down 500 a step to this), the '
     'driving aid (0x4a83d3), the engine tuning slider\'s torque tilt and AI cars (0x4088f0)'),
    ('redline', 13, 0x1c4, CarpTextInt(), 8000,
     'Engine redline in rpm (4800 to 8500). The engine (0x4aaed1): rpm capped at it (above it by a third the wheels '
     'lock), rpm target = redline x throttle, rev limit (drive cut) while the rpm is above the wheels\' rpm by more '
     'than redline / 6 in gears up to 3rd; with the gas off above 1.15 x the gear\'s speed at the redline the force '
     'scales down and the wheels lock. Automatic gearbox (0x4a90a0): up above 7/8 of it, down below half of it (into '
     '2nd) or below 5/6 of it (higher gears): the rpm the lower gear would have; it shifts up only with the gas above 0.9 '
     'or over the redline. Speed at the redline of each gear: redline / `vel_to_rpm`'),
    ('max_velocity', 14, 0x1c8, CarpTextFloat(), 50.0,
     'Top speed in m/s (31.3 to 100.9). Carp_TuneCar (0x4a78d6) sets the air drag coefficient so that the drag '
     '(coefficient x speed³ x aero factor) is 0.98 x the top gear\'s drive at efficiency 1 (torque entry trunc(this x '
     'top gear ratio / 256)) at this speed; above it the drag gets + 0.01 x (speed - this)² (0x4aaed1). The '
     'automatic gearbox (0x4a90a0) never shifts into the top gear when the gear below it (num_gears - 2) already '
     'reaches more than this at the redline. Tuning: engine slider t x (1 + (t - 1) x 0.1), gear ratio slider / t, aero slider / (1 + (t - 1) x 0.05); '
     'game setup flag 1: x 1.75'),
    ('top_speed_cap', 15, 0x1cc, CarpTextFloat(), 50.0,
     'Top speed cap in m/s (= `max_velocity` in every shipped file). Not read by the player car\'s physics: the AI '
     'acceleration (0x4064f0: none above it, times a factor), the AI target speed (0x409330) and 0x4ce280 read it'),
    ('front_drive_ratio', 16, 0x1d0, CarpTextFloat(), 0.0,
     'Part of the drive force on the front wheels (0 rear wheel drive; 0.5 Diab, Elni, Lcop, Peln), the rear wheels '
     'get the rest (0x4ad7a3)'),
    ('abs', 17, 0x1d4, CarpTextByte(), 0,
     'Anti-lock brakes, 1 on (0 only Knoc): a braking wheel whose brake force exceeds its grip has the force clamped '
     'to the grip (0x4aca4f), slide amount 3 every 4th tick; without, the wheel goes over its grip'),
    ('max_brake_decel', 18, 0x1d8, CarpTextFloat(), 10.0,
     'Maximum braking deceleration in m/s² (5.5 to 12): brake = brake value (0..1) x this, at most what stops the '
     'car in one step (|forward speed| x 32), split front / rear by `front_brake_bias` (0x4ad7a3). AI cars read it '
     'too (0x4063e0)'),
    ('front_brake_bias', 19, 0x1dc, CarpTextFloat(), 0.0,
     'Part of the braking force on the front wheels (0.5 to 0.686), + 0.05 with the handbrake (0x4ad7a3). '
     'Carp_TuneCar (0x4a78d6): minus the brake balance tuning slider, + 0.05 with the braking aid, then clamped to '
     '0.3..0.75 for every car'),
    ('gas_increasing', 20, 0x1e0, CarpTextArray(CarpTextByte(), 8), [16] * 8,
     'Gas increasing curve, a byte per pedal level (16 in every file). Not read by the player car model: the '
     'controls (0x4a9bc4) ramp the gas up by 16 per physics step'),
    ('gas_decreasing', 21, 0x1e8, CarpTextArray(CarpTextByte(), 8), [16] * 8,
     'Gas decreasing curve, a byte per pedal level (32 in every file). Not read by the player car model: the '
     'controls (0x4a9bc4) ramp the gas down by 16 per physics step, 16 + round((t - 1) x 60) with the steering '
     'tuning slider t above 1'),
    ('brake_increasing', 22, 0x1f0, CarpTextArray(CarpTextFloat(), 8), [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
     'Brake ramp up: the brake value (0..255) rises toward the pedal by round(entry) per physics step, entry = brake '
     'value >> 5 (8 levels of 32), with keyboard braking (the game setup\'s brake ramp flag, set when the brake is '
     'bound to a key, 0x43c040); an analog brake follows the pedal at once (0x4a9bc4)'),
    ('brake_decreasing', 23, 0x210, CarpTextArray(CarpTextFloat(), 8), [64.0, 32.0, 16.0, 8.0, 4.0, 2.0, 1.0, 1.0],
     'Brake ramp down: the brake value falls toward the pedal by round(entry) per physics step, entry = brake value '
     '>> 5, keyboard braking only (0x4a9bc4)'),
    ('wheel_base', 24, 0x230, CarpTextFloat(), 2.5,
     'Wheel base in m (2.45 to 3.0). Not read by the ported physics; no reader identified in nfs3.exe'),
    ('front_grip_bias', 25, 0x234, CarpTextFloat(), 0.5,
     'Front grip bias (0.45 to 0.496). The static wheel loads (9.81 x `lateral_grip` x the wheel\'s surface grip) '
     'times it give the front wheels\' grip; the rear wheels get load - (1 - bias) x load, which is also bias x load '
     '(an exe quirk: both axles get the same share, 0x4ad7a3), before the load transfer and the downforce. Steering '
     'tuning slider t: x (1 + (t - 1) x 0.625), clamped to 0.46..0.56'),
    ('power_steering', 26, 0x238, CarpTextInt(), 1,
     'Power steering, boolean (1 in every file). Read only by the force feedback (0x471860), not by the physics'),
    ('min_steering_accel', 27, 0x23c, CarpTextFloat(), 10.0,
     'Minimum steering acceleration (10 to 19.2). Front wheel angle (0x4ad2e1) = this x 1.5 / 360 turns at full lock '
     '(Diab 19: 28.5 degrees) x steering / 128, reduced: with the handbrake, steering against the slide, x max(0.85 - '
     '0.0056 x |speed|, 0.55); steering toward the slide (the sign of the slip ratio vx / vz) above 26.7 m/s with a '
     'slip ratio beyond 0.05, or above 13.4 m/s beyond 0.15, x 2 |slip ratio| while that is below 1; above 40 m/s '
     'divided by clamp(|speed| x 0.015, 1, 1.5). Each wheel\'s lateral force is capped at 2 x this (m/s², 0x4aca4f). '
     'Steering tuning slider t: x t'),
    ('turn_in_ramp', 28, 0x240, CarpTextFloat(), 2.0,
     'Steering ramp toward the requested steering (-127..127): round(this) per physics step (8 to 24), with keyboard '
     'steering (the game setup\'s steering ramp flag, set when steering is bound to keys); analog steering is direct '
     '(0x4a9bc4)'),
    ('turn_out_ramp', 29, 0x244, CarpTextFloat(), 2.0,
     'Steering ramp back to the centre: round(this) per physics step toward 0 (16 to 32), also first when the '
     'request is on the other side; keyboard steering only (0x4a9bc4)'),
    ('lateral_grip', 30, 0x248, CarpTextFloat(), 1.0,
     'Lateral acceleration grip multiplier (1.8 to 3.9). The static wheel loads are 9.81 x this x the surface grip '
     '(0x4ad7a3), so the grip and the cornering force (sin(slip angle / 2) x grip x 4) scale with it; each wheel\'s '
     'drive / brake force is multiplied by it against that grip (0x4aca4f) and the car-frame forward force divided by '
     'it again (0x4ae68e), so the acceleration does not change. AI cars read it too (0x4076b0)'),
    ('aero_downforce', 31, 0x24c, CarpTextFloat(), 0.005,
     'Aerodynamic downforce multiplier (0.0009 to 0.0023): above 10 m/s the wheels\' grip is x (1 + forward speed x '
     'this) in front, x (1 + speed x this x 1.5) at the rear, below 10 m/s x (1 + this) (this x 1.41 with traction '
     'control, 0x4aab41); upright cars above 10 m/s also lose this x forward speed of their up velocity each step '
     '(x 2 for non-human cars, 0x4a2260). Aero tuning slider t: x (1 + (t - 1) x 0.25)'),
    ('gas_off_factor', 32, 0x250, CarpTextFloat(), 0.0005,
     'Engine braking (0.195 to 0.38): with the gas off (rpm target below the wheels\' rpm) the drive force is -(torque '
     'x the gear\'s drive) x this (0x4aaed1)'),
    ('g_transfer', 33, 0x254, CarpTextFloat(), 0.2,
     'Longitudinal load transfer (0.35 to 0.56): each step the car-frame forward force x this, - gravity z x 0.1, is '
     'taken from the front wheels\' grip and added to the rear wheels\' in the next step (0x4ad7a3; x 0.75 when '
     'negative, 0x4ae5c2). Suspension tuning slider t: x t, clamped to 0.3..0.7; braking aid: - 0.05'),
    ('turning_circle', 34, 0x258, CarpTextFloat(), 25.0,
     'Turning circle radius in m (6.1 to 15), the yaw damping (0x4aea88): driving forward (|vx| < |vz|) with a yaw '
     'rate w (turns/s) where |vz| and |vx| are both below r = |w| x 2 pi x radius x 0.5, w is multiplied by min(|vz| / '
     'r, 0.98) each step (otherwise 0.95 / 0.99); the same sideways below 2 m/s. Steering tuning slider t: + (1 - t) '
     'x 0.5 x radius'),
    ('tire_front', 35, 0x25c, CarpTextArray(CarpTextInt(), 3), [275, 40, 19],
     'Front tyre size: width in mm, aspect ratio in %, rim in inches (`245,40,17` = 245/40 R17). Not read by the '
     'ported physics; no reader identified in nfs3.exe'),
    ('tire_rear', 36, 0x268, CarpTextArray(CarpTextInt(), 3), [305, 40, 19],
     'Rear tyre size: width in mm, aspect ratio in %, rim in inches. Not read by the game\'s physics; the shipped '
     '`vel_to_rpm` tables follow its radius (rim x 25.4 / 2 + width x aspect / 100 mm)'),
    ('tire_wear', 37, 0x274, CarpTextFloat(), 0.0,
     'Tyre wear (0 in every file). Not read by the ported physics; no reader identified in nfs3.exe'),
    ('slide_mult', 38, 0x278, CarpTextFloat(), 0.5,
     'Slide multiplier (0.1 to 1.25; a field of NFS2 SE\'s car physics too). Not read by the ported physics; no '
     'reader identified in nfs3.exe'),
    ('spin_velocity_cap', 39, 0x27c, CarpTextFloat(), 0.5,
     'Spin velocity cap (0.3 to 0.4; NFS2 SE has it too). Not read by the ported physics; no reader identified in '
     'nfs3.exe'),
    ('slide_velocity_cap', 40, 0x280, CarpTextFloat(), 0.5,
     'Slide velocity cap (0.2 to 0.5; NFS2 SE has it too). Not read by the ported physics; no reader identified in '
     'nfs3.exe'),
    ('slide_assist', 41, 0x284, CarpTextInt(), 10,
     'Slide assistance factor, read as an integer (the files write `128.000000` / `150.000000`: the reader stops at '
     'the `.`). Not read by the ported physics; no reader identified in nfs3.exe'),
    ('push_factor', 42, 0x288, CarpTextInt(), 10,
     'Push factor (9000 to 12000; NFS2 SE\'s arcade push slide limit). Not read by the ported physics; no reader '
     'identified in nfs3.exe'),
    ('low_turn_factor', 43, 0x28c, CarpTextFloat(), 0.5,
     'Low turn factor, "the lower the figure, the better the turn" (0.018 to 0.025; NFS2 SE\'s steering gain over '
     'speed). Not read by the ported physics; no reader identified in nfs3.exe'),
    ('high_turn_factor', 44, 0x290, CarpTextFloat(), 0.6,
     'High turn factor, "the lower the figure, the better the turn" (0.022 to 0.035). Not read by the ported '
     'physics; no reader identified in nfs3.exe'),
    ('pitch_roll', 45, 0x294, CarpTextFloat(), 1.0,
     'Pitch / roll factor (0.6 to 1.03) of the drawn body roll and pitch (0x42a7d0, 0x4295a0, read by the renderer), '
     'not the physics. Suspension tuning slider t: / sqrt(t)'),
    ('road_bumpiness', 46, 0x298, CarpTextFloat(), 0.7,
     'Road bumpiness factor (0.57 to 0.95) of the drawn body shake (0x4294e0, with the random generator), not the '
     'physics'),
    ('spoiler_type', 47, 0x29c, CarpTextInt(), 0,
     'Spoiler function type: 0, 1 (Elni, Merc, Peln) or 8 (f355). The physics only checks for 8: shifting up, the '
     'rpm then rises by 25 per step instead of 50 / 75 (0x4aaed1). No other reader identified'),
    ('spoiler_speed', 48, 0x2a0, CarpTextFloat(), 0.0,
     'Spoiler activation speed in m/s (0, 5 or 8). Not read by the ported physics; no reader identified in nfs3.exe'),
    ('gradual_turn_cutoff', 49, 0x2a4, CarpTextInt(), 96,
     'Driving aid (braking / steering aid options, 0x4a83d3, the pedals follow the track\'s speed table 7 slices '
     'ahead): the turn of the road 10 slices ahead (heading difference in 1/1024 turns, smoothed x 7/8) above this '
     'slows the target speed by `medium_turn_speed` (32 to 110, 11 to 39 degrees)'),
    ('medium_turn_cutoff', 50, 0x2a8, CarpTextInt(), 112,
     'Driving aid (0x4a83d3): a turn (1/1024 turns) of this or more uses `sharp_turn_speed` instead of '
     '`medium_turn_speed`'),
    ('sharp_turn_cutoff', 51, 0x2ac, CarpTextInt(), 128,
     'Driving aid (0x4a83d3): a turn (1/1024 turns) of this or more uses `extreme_turn_speed`'),
    ('medium_turn_speed', 52, 0x2b0, CarpTextFloat(), 0.7,
     'Driving aid (0x4a83d3): target speed factor of a turn between `gradual_turn_cutoff` and `medium_turn_cutoff`'),
    ('sharp_turn_speed', 53, 0x2b4, CarpTextFloat(), 0.6,
     'Driving aid (0x4a83d3): target speed factor of a turn between `medium_turn_cutoff` and `sharp_turn_cutoff`'),
    ('extreme_turn_speed', 54, 0x2b8, CarpTextFloat(), 0.5,
     'Driving aid (0x4a83d3): target speed factor of a turn of `sharp_turn_cutoff` or more'),
    ('subdivide_level', 55, 0x2bc, CarpTextInt(), 0,
     'Subdivide level (3; Knoc 1). Not read by the ported physics; no reader identified in nfs3.exe'),
    ('camera_arm', 56, 0x2c0, CarpTextFixed(), 0.0,
     'Camera arm (0.25 in every file), kept as 16.16 fixed point. Read by the camera code (0x4243a0), not the '
     'physics'),
    ('body_damage', 57, 0x2c4, CarpTextFloat(), 0.0,
     'Body damage (0 in every file). Not read by the ported physics; no reader identified in nfs3.exe'),
    ('engine_damage', 58, 0x2c8, CarpTextFloat(), 0.0,
     'Engine damage (0 in every file). Not read by the ported physics; no reader identified in nfs3.exe'),
    ('suspension_damage', 59, 0x2cc, CarpTextFloat(), 0.0,
     'Suspension damage (0 in every file). Not read by the ported physics; no reader identified in nfs3.exe'),
    ('engine_tuning', 60, 0x2d0, CarpTextFloat(), 1.0,
     'Engine tuning (1 in every file: the default of the engine slider; fields 60 to 66 hold the default tuning '
     '0x55d024 in every file). No reader identified: the sliders\' values are in the game setup. '
     + _carp_tuning_note('engine') + ' t: `torque` tilted (more torque above the middle of the rpm range for t > '
     '1), `max_velocity` x (1 + (t - 1) x 0.1)'),
    ('brake_balance', 61, 0x2d4, CarpTextFloat(), 0.0,
     'Brake balance (0 in every file, the slider\'s default). No reader identified. The brake balance slider t: '
     '`front_brake_bias` - t'),
    ('steering_speed', 62, 0x2d8, CarpTextFloat(), 1.0,
     'Steering speed (1 in every file, the slider\'s default). No reader identified. The steering slider t: '
     '`min_steering_accel` x t, `front_grip_bias` x (1 + (t - 1) x 0.625) clamped to 0.46..0.56, `turning_circle` + '
     '(1 - t) x 0.5 x radius, and above 1 the gas released faster (0x4a9bc4)'),
    ('gear_ratio_factor', 63, 0x2dc, CarpTextFloat(), 1.0,
     'Gear ratio factor (1 in every file, the slider\'s default). No reader identified. The gear ratio slider t: '
     '`vel_to_rpm` x t, `max_velocity` / t'),
    ('suspension_stiffness', 64, 0x2e0, CarpTextFloat(), 1.0,
     'Suspension stiffness (1 in every file). An upright car landing (0x4a1ce0) has its velocity along the road '
     'normal and its angular velocity multiplied by 0.5 + clamp(0.1 x the suspension slider x this, 0, 0.2) (0.1 x '
     'this outside single races). The suspension slider t also: `g_transfer` x t clamped to 0.3..0.7, '
     '`pitch_roll` / sqrt(t)'),
    ('aero_factor', 65, 0x2e4, CarpTextFloat(), 0.0,
     'Aero factor (1 in every file, the slider\'s default). No reader identified. The aero slider t: '
     '`aero_downforce` x (1 + (t - 1) x 0.25), `max_velocity` / (1 + (t - 1) x 0.05), the air drag x (1 + t) / 3 '
     '(0x4aaed1; the drag coefficient is computed with the same factor)'),
    ('tire_factor', 66, 0x2e8, CarpTextFloat(), 1.0,
     'Tyre factor (1 in every file, the slider\'s default). No reader identified. The tyre slider t (0x4abd9c, '
     '0x4ac027, 0x4ae68e): wheel grip x (1 - 1 / max(28 - (t - 0.8) x 40, 16)) on a dry road, slide cap trunc(12 - '
     '4 t), slide decay 0.95 - 0.25 t (at least 0.5), forward force x (1 + 0.1 t) up to 1st gear above 1 / x (1 + '
     '(t - 1) x 0.1) below 1'),
) + tuple(
    (f'ai_acc{k}', 67 + k, 0x2EC + 56 * k, CarpTextArray(CarpTextFloat(), 14),
     _NFS3_CARP_DEFAULT_AI_ACC[14 * k: 14 * k + 14],
     f'AI acceleration table, entries {14 * k} to {14 * k + 13} of a table of 112 (8 sections of 14) in m/s² by '
     'speed: an AI car accelerates by entry round(speed in m/s - 0.5), clamped to 0..111 (0x4064f0; times factors '
     'for weather, rubber banding...; none above `top_speed_cap`). Not read by the player car. The game reads one '
     'value line per section: a section split over several lines would take its missing numbers from the parser\'s '
     'line buffer (the end of an earlier, longer line) and skip the other lines. When any section is missing, all '
     'eight take the default table (0x4b0bb0)')
    for k in range(8)
)  # fmt: skip

_NFS3_CARP_TABLE_INDEX = {number: i for i, (_, number) in enumerate(NFS3_CARP_FIELD_TABLE)}
_NFS3_CARP_READERS = {
    _NFS3_CARP_TABLE_INDEX[number]: (block.reader, block._length if isinstance(block, ArrayBlock) else 1)
    for _, number, _, block, _, _ in _NFS3_CARP_FIELDS
}


def _nfs3_carp_field_description(number, offset, block, default, text):
    label = f'{_NFS3_CARP_LABELS[number]}({number})'
    where = f'carp+0x{offset:03x}' if offset is not None else 'not kept'
    if default is None:
        missing = 'missing: not set'
    elif isinstance(default, list):
        shown = default if len(default) <= 8 else default[:6] + ['...']
        missing = 'missing: ' + ', '.join(f'{x:g}' if isinstance(x, float) else str(x) for x in shown)
    else:
        missing = f'missing: {default:g}' if isinstance(default, float) else f'missing: {default}'
    return f'`{label}` ({where}; {missing}). {text}'


def _nfs3_carp_fields_class():
    fields = {
        name: (
            block,
            {
                'description': _nfs3_carp_field_description(number, offset, block, default, text),
                'custom_offset': f'({number})',
            },
        )
        for name, number, offset, block, default, text in _NFS3_CARP_FIELDS
    }
    fields['source_text'] = (
        UTF8Block(length=0),
        {
            'description': 'The file as read (bytes as Latin-1 characters). Writing puts the values over it: labels, '
            'number formats, line endings, lines the game skips and trailing bytes stay as they are, a changed '
            'number is written in the style of the one it replaces',
            'usage': 'io',
        },
    )
    return type('Fields', (DeclarativeCompoundBlock.Fields,), fields)


class Nfs3CarPhysics(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'NFS3 car physics: `carp.txt` in `GameData/CarModel/<car>/car.viv` (`CAR.VIV` for '
            'Knoc, Lcop, Peln, Vcop), plain text with CRLF line endings: pairs of a label line (`mass [kg](2)`) and '
            'a value line (`1625.000000`, arrays comma separated: `0,0,250,250,200,150,100,100`). nfs3.exe parses it '
            "with 0x4b1380 (Car_LoadSpecs 0x42c2a0) into the car's carp (0x4ac bytes): lines are read without "
            'spaces and lower-cased (0x4b09d0, empty lines skipped); a line starting with a digit or `-` is a value '
            'line, any other a label, which selects the first field of the table 0x4af3b0 whose key it contains '
            'together with its `(n)` (0x4b0940; a label selecting nothing drops the selection); the next value line '
            'fills the selected field once (a field already read keeps its first value, other value lines are '
            'skipped); fields missing from the file get the default carp 0x55f874 (0x4b0bb0). Field `(n)` numbers '
            "are not in file order: 75 to 79 are the automatic gearbox's. Then Carp_TuneCar 0x4a78d6 applies the "
            "automatic gear set and the menus' tuning sliders, and sets the per gear values and the air drag. Car "
            'physics steps run at 32 Hz (every 2nd tick of the 64 Hz simulation). Field descriptions: label, place '
            "in the game's carp, the default for a missing field, then the use, from the nfs3.exe port in nfs-web "
            '(`src/nfs3/nfs3-physics`); "no reader identified" = no code found reading it',
        }

    Fields = _nfs3_carp_fields_class()

    @property
    def size_doc_str(self):
        return '?'

    def serializer_class(self):
        from serializers import Nfs3CarPhysicsSerializer

        return Nfs3CarPhysicsSerializer

    def new_data(self, patch=None):
        res = {}
        for name, _, _, _, default, _ in _NFS3_CARP_FIELDS:
            res[name] = deepcopy(default) if default is not None else 0
        res['source_text'] = ''
        return res

    @staticmethod
    def parse_text(raw: bytes) -> dict:
        read = nfs3_carp_exe_read(raw, _NFS3_CARP_READERS)
        res = {}
        for name, number, _, block, default, _ in _NFS3_CARP_FIELDS:
            index = _NFS3_CARP_TABLE_INDEX[number]
            if index in read:
                values = read[index][0]
                res[name] = values if isinstance(block, ArrayBlock) else values[0]
            else:
                res[name] = deepcopy(default) if default is not None else 0
        res['source_text'] = raw.decode('latin-1')
        return res

    def read(self, ctx, name: str = '', read_bytes_amount=None):
        res = {}
        self_ctx = ctx.get_or_create_child(name, self, read_bytes_amount, res)
        remaining = self_ctx.read_bytes_remaining
        raw = ctx.buffer.read() if remaining is None else ctx.buffer.read(remaining)
        res.update(self.parse_text(raw))
        return res

    @staticmethod
    def _as_list(value, block):
        values = list(value) if isinstance(block, ArrayBlock) else [value]
        return [0 if v is None else v for v in values]

    @staticmethod
    def _same(old_values, new_values, reader) -> bool:
        if len(old_values) != len(new_values):
            return False
        if reader in ('int', 'byte'):
            return all(int(round(n)) == o and n == int(round(n)) for o, n in zip(old_values, new_values))
        return all(float(n) == o for o, n in zip(old_values, new_values))

    @staticmethod
    def _value_line(line: bytes, old_values, new_values, reader: str) -> bytes:
        """The value line with the changed numbers replaced, each in the style of the one it replaces; a canonical
        line (comma separated, the files' number style) when the line's items are not the ones the game reads"""
        text = line.decode('latin-1')
        if ' ' not in text and '\0' not in text:
            separator = r'([^0-9\-])' if reader in ('int', 'byte') else r'([^0-9.\-])'
            parts = re.split(separator, text)
            if (len(parts) + 1) // 2 >= len(new_values):
                for k, (old, new) in enumerate(zip(old_values, new_values)):
                    if not Nfs3CarPhysics._same([old], [new], reader):
                        parts[2 * k] = _carp_format_item(new, reader, parts[2 * k])
                return ''.join(parts).encode('latin-1')
        return ','.join(_carp_format_item(v, reader) for v in new_values).encode('latin-1')

    def _render(self, data):
        """The file bytes of data, and the offset of each field's value line in them"""
        raw = (data.get('source_text') or '').encode('latin-1')
        read = nfs3_carp_exe_read(raw, _NFS3_CARP_READERS)
        eol = b'\r\n' if b'\r\n' in raw or b'\n' not in raw else b'\n'
        edits = []  # (start, end, bytes, field name)
        added = []
        for name, number, _, block, default, _ in _NFS3_CARP_FIELDS:
            index = _NFS3_CARP_TABLE_INDEX[number]
            reader = block.reader
            values = self._as_list(data.get(name), block)
            if index in read:
                old_values, (start, end) = read[index]
                if self._same(old_values, values, reader):
                    edits.append((start, end, raw[start:end], name))
                else:
                    edits.append((start, end, self._value_line(raw[start:end], old_values, values, reader), name))
            else:
                defaults = self._as_list(default if default is not None else 0, block)
                if raw and self._same(defaults, values, reader):
                    continue
                line = ','.join(_carp_format_item(v, reader) for v in values).encode('latin-1')
                added.append((f'{_NFS3_CARP_LABELS[number]}({number})'.encode('latin-1'), line, name))
        edits.sort(key=lambda e: e[0])
        # fields the text lacks go after the last value line the game reads
        insert_at = len(raw)
        prefix = b''
        if added and raw:
            last = max((e[1] for e in edits), default=0)
            if raw[last : last + 2] == b'\r\n':
                insert_at = last + 2
            elif raw[last : last + 1] in (b'\r', b'\n'):
                insert_at = last + 1
            elif raw and raw[-1:] not in (b'\r', b'\n'):
                prefix = eol
        out = bytearray()
        offsets = {}
        pos = 0
        for start, end, line, name in edits:
            if added and pos <= insert_at < start:
                out += raw[pos:insert_at]
                pos = insert_at
                self._add_lines(out, offsets, added, eol, prefix)
                added = []
            out += raw[pos:start]
            offsets[name] = len(out)
            out += line
            pos = end
        if added:
            out += raw[pos:insert_at]
            pos = insert_at
            self._add_lines(out, offsets, added, eol, prefix)
        out += raw[pos:]
        return bytes(out), offsets

    @staticmethod
    def _add_lines(out: bytearray, offsets: dict, added, eol: bytes, prefix: bytes):
        out += prefix
        for label, line, name in added:
            out += label + eol
            offsets[name] = len(out)
            out += line + eol

    def write(self, data, ctx=None, name: str = '') -> bytes:
        return self._render(data)[0]

    def estimate_packed_size(self, data, ctx=None):
        return len(self._render(data)[0])

    def offset_to_child_when_packed(self, data, child_name: str, ctx=None):
        return self._render(data)[1].get(child_name, 0)
