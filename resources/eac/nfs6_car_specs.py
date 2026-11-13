"""
NFS Hot Pursuit 2 PC car spec files (`Cars/<car>/*.ini`, `Cars/*.ini`, `Cars/cartable.viv`), typed INI files
(`resources/eac/ini.py`) with every key the shipped files have and every key NFSHP2.exe reads.

Key descriptions come from NFSHP2.exe (nfs-web `decomp/nfs6/NFSHP2.exe.gzf`, names there): the reader and what it does
with a missing key, where the value goes and the code that uses it. A key "not read" has no string in the executable
(checked with a scan of every string of the exe), or its string is read only in other sections (said so).
Readers: `Ini_GetString` 0x527460 (copies at most n - 1 characters), `Ini_GetInt` 0x527560 (`sscanf("%d")`),
`Ini_GetFloat` 0x527650 (`sscanf("%f")`); a missing key leaves the variable as it was, so the value set before the
read is the default. "Required": a missing key logs `ERROR: [section] key missing from <car>` (0x538140) and makes
the car's load fail; the car loads on with "HCVehicle <car> has a fatal physic problem!" (0x415030), the key's field
taking the value of the key read before it.
"""

from typing import Dict

from library.read_blocks import ArrayBlock, DeclarativeCompoundBlock, IntegerBlock, UTF8Block
from library.read_blocks.misc.value_validators import Eq
from resources.eac.ini import (
    IniArray,
    IniFile,
    IniFloat,
    IniGroupSection,
    IniInt,
    IniSection,
    IniSectionGroup,
    IniString,
    ini_fields_class,
)

_REQ = ' Required.'


def _k(name, block, text):
    return (name, block, {'description': text})


def _not_read(name, block=None, why='no such string in the executable'):
    return _k(name, block or IniString(), f'Not read by NFSHP2.exe ({why}).')


def _section(field, section, keys, text):
    return (field, IniSection(section, keys, text), {'description': text})


# ---------------------------------------------------------------------------------------------------------------------
# car.ini, car_hp.ini, car_cop.ini, carracer.ini
# ---------------------------------------------------------------------------------------------------------------------

_BASIC = 'CarIni_ReadBasic 0x420020'
_VEH = 'the car physics object (HCVehicle)'

_CAR_BASIC_KEYS = [
    _k(
        'Mass',
        IniFloat(unit='kg'),
        f'Car mass, kg. {_BASIC} -> HCVehicle +0x208; +0x20c (unsprung mass) = Mass x 0.1. Each brake section adds 8 kg '
        'and each tyre section 12 kg to both (0x422bd0, 0x4222c0), so the simulated mass is Mass + 40 kg. Used for the '
        'wheel loads (Mass / 4 per wheel, HCVehicle_SetupWheels 0x414a50; axle loads 0x419a40), the roll terms of the '
        'sprung mass (Mass - unsprung, 0x415a30, 0x4271a0) and the automatic gearbox (0x415780).' + _REQ,
    ),
    _not_read('PercentUnsprungMass', IniFloat()),
    _k(
        'BodyShape',
        IniInt(),
        f'Mass distribution of the body for its inertia. {_BASIC} -> +0x228; HCVehicle_SetupInertia 0x415570 picks the '
        'pitch and roll factors of the inertia tensor (pitch = (height^2 + length^2) x mass x factor, roll = (width^2 + '
        'height^2) x mass x factor / 3, from the body box): 1, 3, 7: pitch 0.60, roll 0.70; 4, 5: 0.65, 0.85; 6: '
        '0.65, 0.80; any other: 0.83, 0.84. Shipped: 0, 1, 3, 4, 6.' + _REQ,
    ),
    _k(
        'WheelBase',
        IniFloat(unit='m'),
        f'Distance between the axles, m. {_BASIC} -> +0x210: axles at +/- WheelBase / 2 (HCVehicle_SetupGeometry '
        '0x415a30), the steering lock atan(WheelBase / TurningCircleRadius), the pitch limits atan(Travel / '
        'WheelBase), the aerodynamic pitch moment (0x424660).' + _REQ,
    ),
    _k(
        'FrontTrackWidth',
        IniFloat(unit='m'),
        f'Front track, m. {_BASIC} -> +0x214: front wheels at x = -/+ FrontTrackWidth / 2 (0x414a50); frontal area = '
        'VehicleHeight x FrontTrackWidth x 0.8 (0x415a30).' + _REQ,
    ),
    _k(
        'RearTrackWidth',
        IniFloat(unit='m'),
        f'Rear track, m. {_BASIC} -> +0x218: rear wheels at x = +/- RearTrackWidth / 2 (0x414a50).' + _REQ,
    ),
    _k(
        'VehicleHeight',
        IniFloat(unit='m'),
        f'Body height, m. {_BASIC} -> +0x21c: frontal area for the air drag = VehicleHeight x FrontTrackWidth x 0.8 '
        '(0x415a30).' + _REQ,
    ),
    _k(
        'HeightOfGravity',
        IniFloat(unit='m'),
        f"Height of the centre of gravity, m. {_BASIC} -> +0x220: the rigid body's centre of gravity height (0x415a30), "
        'load transfer of the drag (x 0.909, 0x424660) and the roll terms (0.455 / 0.318 / 0.591 x height x g x '
        'sprung mass against the roll stiffnesses, 0x415a30).' + _REQ,
    ),
    _k(
        'RearSlideFactor',
        IniFloat(default=0.85),
        f'Rear slide damping (driving aid). {_BASIC} -> +0x234 = max(value, 0); missing: 0.85. HCVehicle_Update '
        '0x424f70: while it is above 0, the car is on the ground and faster than 6 m/s, each step takes value / 30 of '
        "the rear's sideways speed away when it slides against the steering. 0 in car.ini / car_hp.ini, 1.85..6.2 in "
        'carracer.ini (AI racers) and car_cop.ini.',
    ),
    _k(
        'FrontGripBias',
        IniFloat(),
        f"Front axle's share of the static weight, 0..1. {_BASIC} -> +0x224: the centre of gravity is (1 - value) x "
        'WheelBase behind the front axle (+0x70) and value x WheelBase ahead of the rear one (+0x74, 0x415a30); static '
        'axle loads (0x419830, 0x419a40).' + _REQ,
    ),
    _k(
        'AISpeedFactor',
        IniFloat(default=1.0),
        f'{_BASIC} -> +0x240, clamped to 0..1; missing: 1.0 (error logged, not required). No reader of the value '
        'found: no float load of HCVehicle +0x240 in the executable.',
    ),
    _k(
        'AeroDragCoefficient',
        IniFloat(),
        f'Air drag coefficient (Cd). {_BASIC} -> +0x1f4: drag force = 0.601 x Cd x frontal area x speed^2 '
        "(HCVehicle_AeroDrag 0x424660, 0.601 = air density / 2), also in the automatic gearbox's shift speeds "
        '(0x415780). Each tyre section wider than 215 mm adds min((width - 215) x 0.00004, 0.005) (0x4222c0).' + _REQ,
    ),
    _k(
        'AeroFrontDownforceCoefficient',
        IniFloat(unit='kg per m/s'),
        f'Front downforce, kg-force per m/s of speed on the front axle. {_BASIC} -> +0x1f8: each front wheel gets value '
        'x |speed| x 9.81 x 0.5 N (HCVehicle_Downforce 0x424530): linear in speed.' + _REQ,
    ),
    _k(
        'AeroRearDownforceCoefficient',
        IniFloat(unit='kg per m/s'),
        f'Rear downforce, kg-force per m/s on the rear axle. {_BASIC} -> +0x1fc: each rear wheel gets value x |speed| '
        'x 9.81 x 0.5 N (0x424530).' + _REQ,
    ),
    _k(
        'BodyLiftCoefficient',
        IniFloat(),
        f'Lift coefficient. {_BASIC} -> +0x200: with the four wheels on the ground each wheel load changes by -0.601 x '
        'value x frontal area x speed^2 / 4 (0x424660): positive values lift the car (less grip), negative ones press '
        'it.' + _REQ,
    ),
    _k(
        'UnderBodyDragCoefficient',
        IniFloat(default=1.1),
        f'{_BASIC} -> +0x204; missing: 1.1. HCVehicle_UnderbodyDrag 0x424430: while the body touches the ground and '
        "the car moves down, an upward force 0.601 x value x vertical speed^2 x the body's floor area x 4 slows the "
        'fall.',
    ),
    _k(
        'SpeedGovernor',
        IniFloat(default=0.0, unit='m/s'),
        f'Top speed limit, m/s, 0 = none. {_BASIC} -> +0x23c; missing: 0. Engine_Update 0x429210: at or above it the '
        "engine gives no drive torque and its rpm is held at the gear's rpm of that speed. Shipped: 0 in car.ini, "
        "the racers' top speeds in carracer.ini (55.88..107.29).",
    ),
    _k(
        'TurningCircleRadius',
        IniFloat(unit='m'),
        f'Turning radius, m. {_BASIC} -> +0x24c: full steering lock = atan(WheelBase / radius) (+0x7c, 0x415a30).'
        + _REQ,
    ),
    _k(
        'TurninRamp',
        IniFloat(),
        f'Steering speed. {_BASIC} -> +0x250 = value / 128. HCVehicle_Steering 0x4286f0: per physics step the wheel '
        'position (-1..1) moves towards the input by at most value / 128, while input and wheel are on the same side '
        'of the centre.' + _REQ,
    ),
    _k(
        'TurnoutRamp',
        IniFloat(),
        f'Steering speed back across the centre. {_BASIC} -> +0x254 = value / 128 (0x4286f0): the step limit while the '
        'input is on the other side of the centre than the wheel.' + _REQ,
    ),
    _k(
        'BaseDampingVelocity',
        IniFloat(default=8.9406, unit='m/s'),
        f'Speed where the steering limit starts, m/s. {_BASIC} -> +0x258; missing: 8.9406 (20 mph). '
        'HCVehicle_SteeringLimit 0x4289a0: f = clamp((|speed| - base) / range, 0, 1); the wheel position is '
        'f x input^2 + (1 - f) x |input| and at most DampingLimit x f + 1 - f of full lock (counter-steering into a '
        'slide may go further).',
    ),
    _k(
        'RangeDampingVelocity',
        IniFloat(default=22.3515, unit='m/s'),
        f'Speed range over which the steering limit comes in, m/s. {_BASIC} -> +0x25c; missing: 22.3515 (50 mph) '
        '(0x4289a0).',
    ),
    _k(
        'DampingLimit',
        IniFloat(default=1.0),
        f'Steering range left above BaseDampingVelocity + RangeDampingVelocity, fraction of full lock. {_BASIC} -> '
        '+0x260; missing: 1.0 (0x4289a0).',
    ),
    _not_read('DampeningLimit', IniFloat(), 'a misspelling of DampingLimit'),
    _not_read('AllWheelSteering', IniInt()),
    _not_read('PowerSteering', IniInt()),
    _k(
        'FrontDriveRatio',
        IniFloat(),
        f"Front axle's share of the drive torque. {_BASIC} -> +0x230. HCVehicle_SetupWheels 0x414a50 keeps it only "
        'for four driven wheels; front wheels only: 1, otherwise 0. Each front wheel gets value / 2, each rear one '
        '(1 - value) / 2 (HCVehicle_SetupDrivetrain 0x415d30).' + _REQ,
    ),
    _k(
        'driveWheels',
        IniArray(IniInt(), 4, 'driveWheels_%d'),
        f'Driven wheels, 0 / 1: 0 front left, 1 front right, 2 rear right, 3 rear left. {_BASIC} -> bytes +0x238..; '
        'all 0: the rear ones. Each key required.',
    ),
    _k(
        'YawInertiaFactor',
        IniFloat(default=1.0),
        f'Scale of the yaw inertia. {_BASIC} -> +0x264, clamped to 0.3..2; missing: 1.0. 0x415570: yaw inertia = '
        '(length^2 + width^2) x mass x 0.8 x value.',
    ),
    _k(
        'FrontRollStiffness',
        IniFloat(unit='N m/deg'),
        f'Front roll stiffness, N m per degree. {_BASIC} -> +0x268: with the rear one, the body roll (0x415a30: '
        "stiffness sum against the sprung mass's roll moment) and the front share of the lateral load transfer = "
        'front / (front + rear) (0x4271a0, 0x419a40).' + _REQ,
    ),
    _k(
        'RearRollStiffness',
        IniFloat(unit='N m/deg'),
        f'Rear roll stiffness. {_BASIC} -> +0x26c, see the front one.' + _REQ,
    ),
    _k(
        'AntiDive',
        IniFloat(),
        f'{_BASIC} reads it into +0x270 and then FrontAntiRoll overwrites it: its value is never used, but a missing '
        'key fails the load.' + _REQ,
    ),
    _k(
        'AntiSquat',
        IniFloat(),
        f'{_BASIC} reads it into +0x274 and then RearAntiRoll overwrites it: never used, but required.' + _REQ,
    ),
    _k(
        'FrontAntiRoll',
        IniFloat(default=0.0),
        f'{_BASIC} -> +0x270 (over AntiDive); missing: 0. 0x42a310 takes 1 - value (clamped 0..1) as the body pitch '
        'factor while +0xc54 (the pitch rate) is negative: it acts as anti-dive.',
    ),
    _k(
        'RearAntiRoll',
        IniFloat(default=0.0),
        f'{_BASIC} -> +0x274 (over AntiSquat); missing: 0. 0x42a310: 1 - value while +0xc54 is positive (anti-squat).',
    ),
    _k(
        'Damper',
        IniFloat(),
        f'Suspension damping. {_BASIC} -> +0x280 and +0x284 (front and rear), used by the suspension (0x428bc0, '
        '0x42a850: their mean).' + _REQ,
    ),
    _k(
        'TravelFront',
        IniFloat(unit='m'),
        f'Front suspension travel, m. {_BASIC} -> +0x288: travel of wheels 0 and 1 (0x414a50), pitch limit '
        'atan(travel / WheelBase) (0x415a30), roll limit of the larger travel (0x42a310).' + _REQ,
    ),
    _k('TravelRear', IniFloat(unit='m'), f'Rear suspension travel, m. {_BASIC} -> +0x28c, as TravelFront.' + _REQ),
    _not_read('MaterialType', IniInt()),
    _not_read('attach', IniInt(), 'the exe reads `attach` in the brake and tyre sections only'),
    _not_read('carIDX', IniInt()),
    _not_read('OpponentVolume', IniInt()),
    _not_read('Time0To60', IniFloat()),
    _not_read('TimeQuarterMile', IniFloat()),
    _not_read('TimeMile', IniFloat()),
    _not_read('RetractableLights', IniInt()),
    _not_read('MinTireSmokeForce', IniFloat()),
    _not_read('MinSkidMarkForce', IniFloat()),
    _not_read('MinSquealForce', IniFloat()),
    _not_read('MinTireSmokeForceFront', IniFloat()),
    _not_read('MinSkidMarkForceFront', IniFloat()),
    _not_read('MinTireSmokeForceRear', IniFloat()),
    _not_read('MinSkidMarkForceRear', IniFloat()),
    _not_read('MinSquealForceFront', IniFloat()),
    _not_read('MinSquealForceRear', IniFloat()),
    _not_read('MaxRenderTravelUp', IniFloat(), 'the exe reads it in the tyre sections only'),
    _not_read('MaxRenderTravelDown', IniFloat(), 'the exe reads it in the tyre sections only'),
]

_ENGINE = 'CarIni_ReadEngine 0x4218b0'
_CAR_ENGINE_KEYS = [
    _k(
        'FlyWheelInertiaFactor',
        IniFloat(default=1.0),
        f"Scale of the engine's inertia. {_ENGINE} -> +0x300; missing: 1.0 (error logged). Engine inertia = 0.18077 x "
        'value kg m^2 (HCVehicle_SetupDrivetrain 0x415d30).',
    ),
    _not_read('mass', IniFloat(), 'the exe reads `Mass` in [basic] only'),
    _k(
        'MinRPM',
        IniInt(unit='rpm'),
        f'Idle rpm. {_ENGINE} -> +0x290: the engine never turns slower (0x414f20, Engine_Update 0x429210), the drive '
        'is zero below it (0x419700), engine sounds play from it (0x435430: sound index = (rpm - MinRPM) x 127 / '
        '(RedLine - MinRPM)).' + _REQ,
    ),
    _k(
        'RedLine',
        IniInt(unit='rpm'),
        f"Maximum rpm. {_ENGINE} -> +0x294: each gear's rpm per m/s comes from its speed at the red line "
        '(Gearbox_ComputeRpmPerMps 0x419550), no drive above it (0x419700), top of the engine sound tables.' + _REQ,
    ),
    _k(
        'WarningLine',
        IniInt(unit='rpm'),
        f'{_ENGINE} -> +0x304 = min(value, RedLine); missing: RedLine x 7 / 8 (error logged). No reader of the value '
        'found.',
    ),
    _k(
        'torqueCurve',
        IniArray(IniFloat(unit='N m'), 25, 'torqueCurve_%d'),
        f'Full throttle torque, N m, entry i at i x 500 rpm, linear in between (Engine_TorqueAtRpm 0x41fde0). {_ENGINE} '
        'reads 25 entries (0..24) -> +0x29c; a missing one logs an error and is 0 (every shipped file stops at 23). '
        'Past the last non-zero entry the reader fills the curve falling: each entry the last one times r, r squared '
        'every step, r = the last decrease ratio of the curve (0.8 when it never decreased).',
    ),
    _k(
        'dbAudio',
        IniArray(IniString(max_length=4), 6, 'dbAudio_%d'),
        f'Engine sound codes. {_ENGINE} reads only dbAudio_1 (required; 3 characters kept, `NULL` = none) into +0x298 '
        '(0x41fd90), the engine sound bank code. dbAudio_0, _2.._5 are not read.',
    ),
    _not_read('attach', IniInt(), 'the exe reads `attach` in the brake and tyre sections only'),
    _not_read('basename'),
    _not_read('displayname', why='the exe reads `displayname` in Cars.ini only'),
    _not_read('Bore', IniFloat()),
    _not_read('Stroke', IniFloat()),
    _not_read('Displacement', IniFloat()),
    _not_read('NumCylinders', IniInt()),
    _not_read('EngineBlockType', IniInt()),
    _not_read('MaterialType', IniInt()),
    _not_read('CompressionRatio', IniFloat()),
]

_TRANS = 'CarIni_ReadTransmission 0x421120'
_CAR_TRANSMISSION_KEYS = [
    _not_read('Mass', IniFloat(), 'the exe reads `Mass` in [basic] only'),
    _k(
        'NumberOfGears',
        IniInt(),
        f'Gears with reverse and neutral (8 = R, N, 6 forward). {_TRANS} -> +0x30c.' + _REQ,
    ),
    _k(
        'GearShiftDelay',
        IniInt(unit='steps'),
        f'Shift time in physics steps. {_TRANS} -> +0x310 = value, + 12 with the manual gearbox; the clutch '
        'engages over it (0x4290c0, 0x42a010).' + _REQ,
    ),
    _not_read('Automatic', IniInt(), "the gearbox is the player's choice, passed to CarIni_Load 0x422bd0"),
    _k(
        'GearRatios',
        IniArray(IniFloat(), 8, 'GearRatios_%d'),
        f'Gear ratios: 0 reverse, 1 neutral (0), 2.. forward. {_TRANS} -> +0x314; a missing one logs an error and is '
        '0. Rpm per m/s = ratio x max(FinalGearRatio, FrontFinalGearRatio) x 60 / rear tyre circumference '
        '(0x419550; reverse negative); drive force = torque x ratio x final x efficiency / rear tyre radius (0x419700).',
    ),
    _k(
        'GearEfficiency',
        IniArray(IniFloat(default=1.0), 8, 'GearEfficiency_%d'),
        f'Efficiency of each gear, 0..1. {_TRANS} -> +0x334 (x 0.97 with the automatic gearbox); missing: 1 (error '
        'logged); clamped to 0..1 by 0x415a30. Scales the drive force.',
    ),
    _k(
        'TorqueConverterRatio',
        IniFloat(default=0.0),
        f'{_TRANS} -> +0x384; missing: 0 (error logged). No reader: no load of +0x384 in the executable.',
    ),
    _k(
        'TorqueConverterMaxRPM',
        IniInt(default=0),
        f'{_TRANS} -> +0x388; missing: 0 (error logged). No reader: no load of +0x388 in the executable.',
    ),
    _k(
        'GearShiftPointCoefficient',
        IniFloat(default=0.9),
        f'Automatic up-shift point. {_TRANS} -> +0x38c, clamped to 0.75..1.2; missing: 0.9 (error logged). '
        'Gearbox_ShiftSpeed 0x415780: up-shift speed = value x the speed from which the next gear accelerates more '
        '(drive minus air drag and rolling resistance); when they never cross, 70 % (1st) or 75 % of the red line.',
    ),
    _not_read('attach', IniInt(), 'the exe reads `attach` in the brake and tyre sections only'),
    _not_read('basename'),
    _not_read('displayname', why='the exe reads `displayname` in Cars.ini only'),
]

_CAR_REAREND_KEYS = [
    _not_read('attach', IniInt(), 'the exe reads `attach` in the brake and tyre sections only'),
    _not_read('basename'),
    _not_read('displayname', why='the exe reads `displayname` in Cars.ini only'),
    _not_read('Mass', IniFloat(), 'the exe reads `Mass` in [basic] only'),
    _k(
        'FinalGearRatio',
        IniFloat(),
        'Final drive ratio. CarIni_Load 0x422bd0 -> +0x374. The gearbox uses max(FinalGearRatio, FrontFinalGearRatio) '
        '(0x419550, 0x419700, 0x415a30).' + _REQ,
    ),
    _k(
        'FrontFinalGearRatio',
        IniFloat(default=0.0),
        'Front final drive ratio. 0x422bd0 -> +0x378; missing: 0 (error logged). Only the larger of the two final '
        'ratios is used.',
    ),
    _not_read('LockingDifferential', IniInt()),
]

_TIRE = 'CarIni_ReadTire 0x4222c0 / 0x422550'
_TIRE_TYPES = (
    '0 Bias Ply, 1 Bias Belted, 2 Radial, 3 Performance, 4 Stock Car, 5 Bias Ply Rain, 6 Bias Belted Rain, 7 Radial '
    'Rain, 8 Performance Rain, 9 Eagle GTS, 10 High Performance, 11 T7000 Radial, 12 MVD HP Radial Type II'
)


def _tire_keys(which: str):
    return [
        _k(
            'TypeCode',
            IniInt(),
            f'Tyre type, an index of the built-in tyre table 0x691890 (0xe8 bytes each: name, its index, two curves of '
            f'25 floats): {_TIRE_TYPES}. {_TIRE} copies the type to the tyre record +0x110 and its curves (0x423ee0, '
            '0x423f00). Shipped: 10.' + _REQ,
        ),
        _k(
            'attach',
            IniInt(),
            f'Which tyre record the section fills: 10 = front (HCVehicle +0x390), any other value = rear (+0x4a4); the '
            f'section name does not decide it ({_TIRE}). Shipped: 10 in [tire_front], 11 in [tire_rear].' + _REQ,
        ),
        _not_read('basename'),
        _not_read('displayname', why='the exe reads `displayname` in Cars.ini only'),
        _not_read('mass', IniFloat(), 'the exe reads `Mass` in [basic] only; the tyre adds a fixed 12 kg'),
        _k(
            'SectionWidth',
            IniInt(unit='mm'),
            f'Tyre width, mm. {_TIRE} -> tyre record +0; radius = width x AspectRatio / 100000 + WheelDiameter x 0.0127 '
            'm (0x414a50); a width over 215 adds min((width - 215) x 0.00004, 0.005) to AeroDragCoefficient.' + _REQ,
        ),
        _k('AspectRatio', IniInt(unit='%'), f'Sidewall height, % of the width. {_TIRE} -> record +4.' + _REQ),
        _k('WheelDiameter', IniInt(unit='in'), f'Rim diameter, inches. {_TIRE} -> record +8.' + _REQ),
        _not_read('SpeedIndex', IniInt()),
        _not_read('CamberAngle', IniFloat()),
        _k(
            'RollingResistanceFactor',
            IniFloat(default=1.0),
            f'{_TIRE} -> record +0x14; missing: 1.0 (error logged).',
        ),
        _k(
            'PeakFriction',
            IniFloat(default=1.6),
            f"{_TIRE} -> record +0x18; missing: 1.6 (error logged); then raised to the largest of the type's first "
            'curve x ForceScale x 0.00025.',
        ),
        _k(
            'ForceScale',
            IniFloat(default=1.0),
            f"Scale of the type's force curve. {_TIRE} -> record +0x24; missing: 1.0.",
        ),
        _k('SlipAngleScale', IniFloat(default=1.0), f'{_TIRE} -> record +0x28; missing: 1.0.'),
        _not_read('SlipAngle', IniFloat(), 'the exe reads `SlipAngleScale`'),
        _k('AligningMomentScale', IniFloat(default=1.0), f'{_TIRE} -> record +0x2c; missing: 1.0.'),
        _k('SlipRatio', IniFloat(default=1.0), f'{_TIRE} -> record +0x108; missing: 1.0.'),
        _k(
            'MaxRenderTravelUp',
            IniFloat(default=0.0762, unit='m'),
            f'How far the drawn wheel moves up, m. {_TIRE} -> record +0x34; missing: 0.0762 (3 in, error logged).',
        ),
        _k(
            'MaxRenderTravelDown',
            IniFloat(default=-0.1524, unit='m'),
            f'How far the drawn wheel moves down, m (negative). {_TIRE} -> record +0x30; missing: -0.1524 (6 in, error '
            'logged).',
        ),
        _k('TractionCoefft', IniFloat(default=0.4), f'{_TIRE} -> record +0x10c; missing: 0.4 (error logged).'),
        _not_read('NominalPressure', IniFloat()),
    ]


_BRAKE = 'CarIni_ReadBrake 0x422060'


def _brake_keys(which: str):
    return [
        _k(
            'attach',
            IniInt(),
            f'Which brake record the section fills: 10 = front (HCVehicle +0x5b8), any other value = rear (+0x5c8); the '
            'section name does not decide it (CarIni_Load 0x422bd0). Each brake section adds 8 kg to the mass.' + _REQ,
        ),
        _not_read('basename'),
        _not_read('displayname', why='the exe reads `displayname` in Cars.ini only'),
        _not_read('Mass', IniFloat(), 'the exe reads `Mass` in [basic] only'),
        _not_read('Efficiency', IniFloat()),
        _not_read('Thickness', IniFloat()),
        _not_read('BrakeType', IniInt()),
        _k('BrakeMaterialType', IniInt(), f'{_BRAKE} -> brake record +4. Shipped: 2, 3.' + _REQ),
        _k('BrakeDiameter', IniInt(unit='mm'), f'Disc diameter, mm. {_BRAKE} -> record +8 in m (x 0.001).' + _REQ),
        _k('ABS', IniInt(), f'Anti-lock brakes, 0 / 1. {_BRAKE} -> record +0xc.' + _REQ),
    ]


_CAR_INI_SECTIONS = [
    _section('basic', 'basic', _CAR_BASIC_KEYS, 'Body, aerodynamics, steering, drive layout and suspension'),
    _section(
        'display_data',
        'Display_Data',
        [
            _not_read('Time0To60'),
            _not_read('TimeQuarterMile'),
            _not_read('TimeMile'),
            _not_read('TopSpeed'),
            _not_read('MaxHP'),
        ],
        "Front end text ids of the car's figures; not read (the front end takes them from Cars.ini)",
    ),
    _section('engineblock', 'engineblock', _CAR_ENGINE_KEYS, 'Engine: rpm range, torque curve, sound'),
    _section('transmission', 'transmission', _CAR_TRANSMISSION_KEYS, 'Gearbox'),
    _section('rearend', 'rearend', _CAR_REAREND_KEYS, 'Final drive'),
    _section('tire_rear', 'tire_rear', _tire_keys('rear'), 'Rear tyres (record by `attach`)'),
    _section('tire_front', 'tire_front', _tire_keys('front'), 'Front tyres (record by `attach`)'),
    _section('brake_rear', 'brake_rear', _brake_keys('rear'), 'Rear brakes (record by `attach`)'),
    _section('brake_front', 'brake_front', _brake_keys('front'), 'Front brakes (record by `attach`)'),
    _section(
        'horn',
        'horn',
        [
            _k(
                'dbAudio',
                IniString(max_length=32),
                'Horn sound code. CarIni_Load 0x422bd0 reads it (32 characters; missing: error logged) and keeps it '
                'in HCVehicle +0x5dc (+0x5d8 = 1) unless empty or `NULL`. In no shipped file.',
            )
        ],
        'Horn sound (not in the shipped files)',
    ),
    _section('skins', 'Skins', [_not_read('NumberSkins', IniInt())], 'Not read'),
    _section(
        'audio',
        'audio',
        [
            _k(
                'enginetype',
                IniInt(),
                'Engine sound type. The car sound setup 0x51b990 opens car.ini again and reads it (0x51ba04...) into '
                'its engine sound slot (0x7a0c6c).',
            ),
            _k('horntype', IniInt(default=99), 'Horn sound type. 0x51b990; missing: 99.'),
        ],
        'Sounds (read by the sound setup, not the physics)',
    ),
    _section('render', 'render', [_not_read('vehicletype', IniInt())], 'Not read'),
    _section('addon', 'addon', [_not_read('num', IniInt()), _not_read('addon01')], 'Not read'),
]


class Nfs6CarIni(IniFile):
    """`Cars/<car>/car.ini`: the car's physics as the player drives it"""

    ini_role = (
        '`car.ini`: the car as the player drives it (CarIni_Load 0x422bd0 with role 0 or 4: the player, network '
        'cars, traffic: the only file traffic cars have)'
    )

    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': f'NFS Hot Pursuit 2 PC car physics, {self.ini_role}. HCVehicle_Load 0x415030 copies '
            'the values of a car of the same type already loaded (0x4de9f0), else CarIni_Load 0x422bd0 picks the file '
            "by the car's role: car_hp.ini for role 1 or while 0x83a5f4 is set (hot pursuit), car_cop.ini for role 3 "
            'or while 0x83a5f8 is set, carracer.ini for role 2 (AI racers), car.ini otherwise; the four files have '
            'the same keys. Sections read in order: [basic] (0x420020), [engineblock] (0x4218b0), [transmission] '
            '(0x421120), [rearend], [brake_front] / [brake_rear] (0x422060), [tire_front] / [tire_rear] (0x4222c0), '
            '[horn]; [audio] by the sound setup (0x51b990). INI rules: `resources/eac/ini.py` `parse_ini` (EA CINI '
            'parser 0x5b5180: no comment syntax, keys ignoring case, the first of repeated sections)',
        }

    Fields = ini_fields_class(_CAR_INI_SECTIONS)


class Nfs6CarHpIni(Nfs6CarIni):
    ini_role = '`car_hp.ini`: the car in hot pursuit races (role 1, or the global flag 0x83a5f4)'
    Fields = ini_fields_class(_CAR_INI_SECTIONS)


class Nfs6CarCopIni(Nfs6CarIni):
    ini_role = '`car_cop.ini`: the car as a police car (role 3, or the global flag 0x83a5f8)'
    Fields = ini_fields_class(_CAR_INI_SECTIONS)


class Nfs6CarRacerIni(Nfs6CarIni):
    ini_role = '`carracer.ini`: the car as an AI racer (role 2)'
    Fields = ini_fields_class(_CAR_INI_SECTIONS)


# ---------------------------------------------------------------------------------------------------------------------
# vehicle.ini
# ---------------------------------------------------------------------------------------------------------------------

_VR = 'Cars_ReadCarsIni 0x42f240'


def _skin_keys(with_color: bool = True):
    keys = []
    if with_color:
        keys.append(
            _k(
                'color_id',
                IniString(max_length=32),
                f'Colour name (`red`, `silver`...): {_VR} turns it into a colour code (0x4a7f50) for the menus; '
                'missing: -1.',
            )
        )
    keys += [
        _k(
            'specular_red',
            IniInt(),
            f'Paint specular colour, red 0..255. {_VR} reads a skin only when it has this key (skinNN: the skins end '
            'at the first without it); Vehicle_SetSkinLighting 0x431d30: / 255 -> car +0x82c, the paint highlight '
            'colour of the vehicle shaders.',
        ),
        _k('specular_green', IniInt(), 'Paint specular colour, green 0..255 (see specular_red).'),
        _k('specular_blue', IniInt(), 'Paint specular colour, blue 0..255.'),
        _k('specular_paint_exponent', IniFloat(), 'Specular exponent of the paint (EASVehiclePaint) -> car +4.'),
        _k('specular_glass_exponent', IniFloat(), 'Specular exponent of the glass (EASVehicleGlass) -> car +8.'),
        _k('specular_rubber_exponent', IniFloat(), 'Specular exponent of the rubber (EASVehicleRubber) -> car +0xc.'),
        _k(
            'specular_sun_intensity',
            IniInt(),
            'Sun share of the paint specular, 0..255: / 255 -> car +0x83c (added as intensity x sun colour).',
        ),
        _k('addons_enable', IniInt(default=0), f'Shows the add-on geometries (`ADDON_` names) with this skin, 0 / 1.'),
        _not_read('addons_enabled', IniInt(), 'a misspelling of addons_enable'),
        _not_read('m_price', IniInt(), 'the exe reads `paintcost`'),
    ]
    return keys


_PAINT_KEYS = [
    _k(
        'paintname',
        IniString(max_length=80),
        f'Text id of the paint name (kTxt...). {_VR} reads [paintcolorN] only for a skin it reads (same N); missing: '
        'name id 0x325, swatch 0xffa000a0, cost 100.',
    ),
    _k('painta', IniInt(default=0), "Swatch alpha 0..255 (the menu's paint swatch, ARGB)."),
    _k('paintr', IniInt(default=0), 'Swatch red 0..255.'),
    _k('paintg', IniInt(default=0), 'Swatch green 0..255.'),
    _k('paintb', IniInt(default=0), 'Swatch blue 0..255.'),
    _k('paintcost', IniInt(default=0), 'Paint price; 0 keeps the default 100. In no shipped file.'),
    _not_read('m_price', IniInt(), 'the exe reads `paintcost`'),
]

_GLOW = 'VehicleLightGlow_ReadGlows 0x430900'
_GLOW_KEYS = [
    _k('glow_sizex', IniFloat(unit='m'), f'Glow sprite width. {_GLOW} -> glow +0xc.'),
    _k('glow_sizey', IniFloat(unit='m'), f'Glow sprite height -> glow +0x10.'),
    _k('glow_red', IniInt(default=0), 'Colour, red 0..255.'),
    _k('glow_green', IniInt(default=0), 'Colour, green 0..255.'),
    _k('glow_blue', IniInt(default=0), 'Colour, blue 0..255.'),
    _k('glow_alpha', IniInt(default=0), 'Opacity 0..255 (also / 255 at +0xe8).'),
    _k('glow_flashfreq', IniFloat(), 'Flash frequency, 0 = steady (cop lights 0.1..0.13) -> glow +0.'),
    _k('glow_fadeonangle', IniInt(default=0), 'Non-zero: the glow fades with the viewing angle. In no shipped file.'),
    _k('glow_shape', IniString(max_length=32), 'Texture name of the glow sprite (`0001`..`0003`).'),
]


def _light_group(field, section, text):
    return _section(
        field,
        section,
        [
            _k(
                'glow_num',
                IniInt(),
                f'Number of glows of the group. VehicleLightGlow_ReadGroup 0x430cf0 reads attach_bone1.. and '
                'attach_glow1.. up to it.',
            ),
            _k(
                'attach_bone',
                IniArray(IniString(max_length=256), 8, 'attach_bone%d', first_index=1),
                'Skeleton bone of each glow (`LIGHT_TAIL_LEFT1`...; missing: `unknown.bone`).',
            ),
            _k(
                'attach_glow',
                IniArray(IniInt(), 8, 'attach_glow%d', first_index=1),
                'Index of the [lightglowN] each glow draws (missing: 0).',
            ),
        ],
        text,
    )


_VEHICLE_INI_SECTIONS = [
    _section(
        'effects',
        'effects',
        [
            _k(
                'specular_hotspot_exponent',
                IniFloat(),
                f"{_VR} -> car record; Vehicle_SetSkinLighting -> car +0x814: exponent of the paint's hot spot "
                'highlight (gHotSpecularColour). Racers and cops only.',
            ),
            _k('fresnel_scaler', IniFloat(), f'{_VR}; -> car +0x810, the fresnel factor of the vehicle shaders.'),
            _k('wheelAnimSpeed', IniFloat(default=2.5), f'Wheel spin drawing speed factor. {_VR}; missing: 2.5.'),
        ],
        'Shading constants',
    ),
    _section('splatshadow', 'splatshadow', [_k('scale', IniFloat(), f"Scale of the car's shadow. {_VR}.")], 'Shadow'),
    _section(
        'verticalfudge',
        'verticalfudge',
        [_k('height', IniFloat(default=0.0), f'{_VR}; missing: 0. In no shipped file.')],
        'Not in the shipped files',
    ),
    _section(
        'damage',
        'damage',
        [
            _k('bouncetrunk', IniFloat(default=0.0), f'How far the damaged trunk lid bounces. {_VR}; missing: 0.'),
            _k('bouncehood', IniFloat(default=0.0), f'How far the damaged hood bounces. {_VR}; missing: 0.'),
            _k('disabled', IniInt(default=0), f'Non-zero: no visual damage. {_VR}; missing: 0.'),
        ],
        'Visual damage (the first [damage] section: cl55amg has two)',
    ),
    _section(
        'wheel_front',
        'wheel_front',
        [_k('renderoffset', IniFloat(default=0.0, unit='m'), f'Sideways offset of the drawn front wheels. {_VR}.')],
        'Front wheel drawing',
    ),
    _section(
        'wheel_rear',
        'wheel_rear',
        [_k('renderoffset', IniFloat(default=0.0, unit='m'), f'Sideways offset of the drawn rear wheels. {_VR}.')],
        'Rear wheel drawing',
    ),
    _section(
        'driver',
        'driver',
        [_k('leftsidedrive', IniInt(default=0), f'Non-zero: the driver sits on the left. {_VR}.')],
        'Driver model',
    ),
    _section(
        'vehicletype',
        'vehicletype',
        [_not_read('type', why="no `vehicletype` string; TailsLab's car export reads it for lighting.json")],
        'Not read by the game',
    ),
    (
        'skins',
        IniSectionGroup(
            IniGroupSection(_skin_keys(), 'Section name, `skin00`..`skin19` (the game reads only these, in order)'),
            r'skin\d+',
            lambda i: f'skin{i:02d}',
            'Paint skins [skin00]..[skin19]: the skins of `skin.viv`',
        ),
        {
            'description': f'Paint skins `[skin00]`..`[skin19]` ({_VR}): read in order up to the first without '
            'specular_red (later ones are not read); a racer without any gets one. The car record keeps 20 (0xc '
            'dwords each).'
        },
    ),
    (
        'paint_colors',
        IniSectionGroup(
            IniGroupSection(_PAINT_KEYS, 'Section name, `paintcolor<N>` of skin N'),
            r'paintcolor\d+',
            lambda i: f'paintcolor{i}',
            'Front end paint swatches [paintcolor0]..',
        ),
        {'description': 'Front end paint swatches `[paintcolorN]`, read for each skin read (same N).'},
    ),
    _section(
        'skinhp',
        'skinhp',
        _skin_keys(),
        'Skin of the hot pursuit version (`skinhp.fsh`); read when it has specular_red (flag at car record +0x400)',
    ),
    _section(
        'skincop',
        'skincop',
        [k for k in _skin_keys(with_color=False)],
        'Police skin (`skincop.fsh`); read when it has specular_red; no colour name',
    ),
    _section(
        'lightglows',
        'lightglows',
        [_k('glow_num', IniInt(), f'Number of [lightglowN] sections read ({_GLOW} -> +0x44).')],
        'Light glow sprites',
    ),
    (
        'light_glows',
        IniSectionGroup(
            IniGroupSection(_GLOW_KEYS, 'Section name, `lightglow<N>`'),
            r'lightglow\d+',
            lambda i: f'lightglow{i}',
            'Glow sprites [lightglow0]..',
        ),
        {'description': f'Glow sprites `[lightglow0]`.. ({_GLOW}, VehicleLightGlow_Load 0x4307c0), up to glow_num.'},
    ),
    _light_group('brakelights', 'brakelights', 'Brake light glows (group 0, facing back)'),
    _light_group('coplights', 'coplights', 'Police light glows (group 1)'),
    _light_group('headlights', 'headlights', 'Head light glows (group 2, facing forward)'),
    _light_group('reverselights', 'reverselights', 'Reversing light glows (group 3, facing back)'),
]


class Nfs6VehicleIni(IniFile):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'NFS Hot Pursuit 2 PC `Cars/<car>/vehicle.ini`: shading, skins and paint swatches, '
            'visual damage, wheel drawing, light glows. Read by Cars_ReadCarsIni 0x42f240 (after Cars.ini, for every '
            'car) into the car record (0x4cc bytes) and by VehicleLightGlow_Load 0x4307c0',
        }

    Fields = ini_fields_class(_VEHICLE_INI_SECTIONS)


# ---------------------------------------------------------------------------------------------------------------------
# Cars.ini
# ---------------------------------------------------------------------------------------------------------------------

_CR = 'Cars_ReadCarsIni 0x42f240'
_CARS_KEYS = [
    _k('name', IniString(max_length=80), f'Car folder name (`Cars/<name>/`). {_CR} -> car record +4.'),
    _k('mfrname', IniString(max_length=80), 'Text id of the maker (kTxt...), -> record +0x10 (0x547900).'),
    _k('displayname', IniString(max_length=80), 'Text id of the car name -> +0x14.'),
    _k(
        'class',
        IniInt(default=-1),
        'Car class 1..5 -> +0x1c as class + 0x25; missing: -1. Shipped: 1 (exotics) .. 5 (Elise class and traffic 4).',
    ),
    _k('traffic', IniString(max_length=24), 'Traffic car when the value contains `true` (strstr, case-sensitive).'),
    _k(
        'price',
        IniInt(default=0),
        "Price -> +0x24; 0 on a racing car (not traffic): owned from the start (the profile's car flag).",
    ),
    _k('nfsprice', IniInt(default=0), 'Price in NFS points -> +0x28, at least 2000 (0..2000 become 2000).'),
    _k('stat0to60ID', IniString(max_length=80), 'Text id of the 0-60 figure -> +0x2c (missing: -1).'),
    _k('statTSID', IniString(max_length=80), 'Text id of the top speed -> +0x30.'),
    _k('statTSKPHID', IniString(max_length=80), 'Text id of the top speed in km/h -> +0x34.'),
    _k('statHPID', IniString(max_length=80), 'Text id of the power -> +0x38.'),
]


class Nfs6CarsIni(IniFile):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'NFS Hot Pursuit 2 PC `Cars/Cars.ini`: the car list. Cars_ReadCarsIni 0x42f240 reads '
            '[car0], [car1].. while the section has `name` (the first gap ends the list) into car records of 0x4cc '
            "bytes, then each car's bounds.ini and vehicle.ini. The comment says the list must match GameRules.h",
        }

    Fields = ini_fields_class(
        [
            (
                'cars',
                IniSectionGroup(
                    IniGroupSection(_CARS_KEYS, 'Section name, `car<N>` (the list index)'),
                    r'car\d+',
                    lambda i: f'car{i}',
                    'The cars [car0]..',
                ),
                {'description': 'The cars `[car0]`.., read in order up to the first without `name`'},
            )
        ]
    )


# ---------------------------------------------------------------------------------------------------------------------
# bounds.ini, geomdata.ini, damage.ini, lod.ini
# ---------------------------------------------------------------------------------------------------------------------


def _bounds_keys(base: int):
    names = ['min_x', 'min_y', 'min_z', 'max_x', 'max_y', 'max_z']
    return [
        _k(
            n,
            IniFloat(unit='m'),
            f'Box {n.replace("_", " ")}, m, car space (X right, Y up, Z along the car) -> car '
            f'record +0x{base + 4 * i:x}.',
        )
        for i, n in enumerate(names)
    ]


class Nfs6BoundsIni(IniFile):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': "NFS Hot Pursuit 2 PC `Cars/<car>/bounds.ini`: the car's bounding boxes, read by "
            'Cars_ReadBounds 0x42fca0 (only when the file exists) into the car record',
        }

    Fields = ini_fields_class(
        [
            _section('boundsnormal', 'boundsnormal', _bounds_keys(0x488), 'Box of the car without add-ons'),
            _section('boundsaddon', 'boundsaddon', _bounds_keys(0x4A0), 'Box with the add-ons (police light bar)'),
        ]
    )


_GEOM = 'VehicleGeom_ReadGeomData 0x42e880'


class Nfs6GeomDataIni(IniFile):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'NFS Hot Pursuit 2 PC `Cars/<car>/geomdata.ini`: per geometry of the car model '
            f'(`car.viv` `car.o`) its levels of detail and damage zone. {_GEOM} reads one section per geometry of the '
            'model, named as the geometry (`ALPHA_OPAQUE_HOODShape`, `...~EASVehicleGlass`), and takes the blending '
            'from the name (ALPHA_TRANS 2, ALPHA_ADD 4, else 1; ADDON_ | 8; GEOM_STEERINGWHEEL)',
        }

    Fields = ini_fields_class(
        [
            _section(
                'geomdata',
                'geomdata',
                [
                    _k(
                        'geomnum',
                        IniInt(),
                        f"Number of geometries. {_GEOM} -> +0x738; the loop uses the model's own count instead.",
                    )
                ],
                'Header',
            ),
            (
                'geometries',
                IniSectionGroup(
                    IniGroupSection(
                        [
                            _k('damageversion', IniInt(default=0), 'Non-zero: the geometry has a damaged version.'),
                            _k(
                                'lodon', IniFloat(default=100.0), 'Level of detail from which it is drawn (100 = near).'
                            ),
                            _k('lodoff', IniFloat(default=0.0), 'Level of detail below which it is not drawn.'),
                            _k('damagezoneid', IniInt(default=-1), 'Damage zone 0..9 of the geometry, -1 none.'),
                            _not_read('type', why='no reader of `type` in geomdata.ini'),
                        ],
                        'Geometry name as in the model',
                    ),
                    r'(?!geomdata$).+',
                    lambda i: f'geometry{i}',
                    'Geometries',
                ),
                {'description': f'One section per geometry ({_GEOM}): lodon / lodoff / damage of each'},
            ),
        ]
    )


class Nfs6DamageIni(IniFile):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'NFS Hot Pursuit 2 PC `Cars/<car>/damage.ini`. Not read: VehicleDamage_Init 0x42d390 '
            'formats its path and never opens it (10 damage zones are built in)',
        }

    Fields = ini_fields_class(
        [_section('damage', 'damage', [_not_read('zonenum', IniInt(), 'the file is never opened')], 'Not read')]
    )


class Nfs6LodIni(IniFile):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'NFS Hot Pursuit 2 PC `Cars/<car>/lod.ini`, empty in every shipped car. Not read (no '
            'such name in the executable; the levels of detail are `EAGL/LOD.ini` and geomdata.ini)',
        }

    Fields = ini_fields_class([])


# ---------------------------------------------------------------------------------------------------------------------
# Cameras.ini, RearView.ini, reflection.ini
# ---------------------------------------------------------------------------------------------------------------------


def _chase_keys(reader: str, arm: float, height: float, pitch: float, fov: float, rotation: float, acc: bool = True):
    keys = [
        _k('ArmLength', IniFloat(default=arm, unit='m'), f'Distance behind the car, m. {reader}; missing: {arm}.'),
        _k('ArmHeight', IniFloat(default=height, unit='m'), f'Height above the car, m; missing: {height}.'),
        _k('YawBackTension', IniFloat(default=0.2), 'How fast the camera swings back behind the car; missing: 0.2.'),
        _k('YawOutTension', IniFloat(default=0.5), 'How fast it swings out in turns; missing: 0.5.'),
        _k('PitchBackTension', IniFloat(default=0.25), 'Pitch follow speed back; missing: 0.25.'),
        _k('PitchOutTension', IniFloat(default=1.5), 'Pitch follow speed out; missing: 1.5.'),
        _k('Pitch', IniFloat(default=pitch), f'Look-at pitch; missing: {pitch}.'),
    ]
    if acc:
        keys += [
            _k('AccSpring', IniFloat(default=3.0), 'Spring of the distance when accelerating; missing: 3.'),
            _k('AccDamper', IniFloat(default=2.0), 'Its damping; missing: 2.'),
            _k('DeAccSpring', IniFloat(default=20.0), 'Spring when braking; missing: 20.'),
            _k('DeAccDamper', IniFloat(default=12.0), 'Its damping; missing: 12.'),
        ]
    keys += [
        _k('FOV', IniFloat(default=fov, unit='deg'), f'Field of view, degrees; missing: {fov}.'),
        _k('RotationTension', IniFloat(default=rotation), f'Roll follow speed; missing: {rotation}.'),
    ]
    return keys


def _bumper_keys():
    return [
        _k(
            'FOV', IniFloat(unit='deg'), 'Field of view, degrees (Cameras_ReadBumper 0x410520; 90 for the split views).'
        ),
        _k('ArmHeight', IniFloat(default=0.38, unit='m'), 'Camera height, m; missing: 0.38.'),
        _k('Pitch', IniFloat(default=0.418), 'Pitch; missing: 0.418.'),
    ]


_CAMERA_VIEWS = [
    ('high', 'Cameras_ReadHigh 0x40f360', 6.3, 1.5, 0.026, 71.5, 4.0, True),
    ('low', 'Cameras_ReadLow 0x40e970', 5.1, 1.5, 0.026, 71.5, 4.0, True),
    ('bird', 'Cameras_ReadBird 0x40fd50', 17.0, 3.75, 1.009, 55.0, 4.0, False),
]


def _camera_sections():
    sections = [
        _section(
            'master',
            'master',
            [
                _k('JumpCamera', IniInt(default=2), 'Jump camera: 0 off, 1 on, else 2 (Cameras_ReadMaster 0x40e730).'),
                _k(
                    'AccelerationEnhancement',
                    IniInt(default=1),
                    "Non-zero: the chase cameras' distance follows the acceleration (behaviour +0x61).",
                ),
                _k('SpeedEnhancement', IniInt(default=1), 'Non-zero: the field of view follows the speed.'),
                _k('LookBackTarget', IniInt(default=1), 'Non-zero: the look-back view aims at the car behind.'),
            ],
            'Camera options',
        )
    ]
    for view, reader, arm, height, pitch, fov, rotation, acc in _CAMERA_VIEWS:
        for suffix, who in (
            ('', 'one player'),
            ('-2plr', 'split screen, side by side'),
            ('-2ptb', 'split screen, top / bottom'),
        ):
            name = view + suffix
            sections.append(
                _section(
                    name.replace('-', '_'),
                    name,
                    _chase_keys(reader, arm, height, pitch, fov, rotation, acc),
                    f'{view.capitalize()} chase view, {who}',
                )
            )
    for suffix, who in (('', 'one player'), ('-2plr', 'side by side'), ('-2ptb', 'top / bottom')):
        name = 'bumper' + suffix
        sections.append(_section(name.replace('-', '_'), name, _bumper_keys(), f'Bumper view, {who}'))
    sections.append(
        _section(
            'jump',
            'jump',
            [
                _k(
                    'JumpThreshold',
                    IniFloat(default=16.0),
                    'Jump camera trigger (Cameras_ReadJump 0x410f50); missing: 16.',
                ),
                _k('JumpMinimumHold', IniFloat(default=0.75, unit='s'), 'Shortest time it shows; missing: 0.75.'),
                _k('JumpMaximumHold', IniFloat(default=2.75, unit='s'), 'Longest time; missing: 2.75.'),
            ]
            + [
                item
                for i in (1, 2, 3)
                for item in (
                    _k(f'JumpClockSpeed{i}', IniFloat(default=0.5), f'Time scale of jump shot {i}; missing: 0.5.'),
                    _k(
                        f'JumpFOV{i}',
                        IniFloat(default=None if i == 1 else 45.0, unit='deg'),
                        f'Field of view of shot {i}.',
                    ),
                    _k(
                        f'JumpAmountLeadCar{i}',
                        IniFloat(default=5.0),
                        f'How far ahead of the car shot {i} aims; missing: 5.',
                    ),
                    _k(f'JumpCameraHeight{i}', IniFloat(default=3.0), f'Camera height of shot {i}; missing: 3.'),
                )
            ],
            'Jump camera',
        )
    )
    sections.append(
        _section(
            'matrix',
            'matrix',
            [
                _k(
                    'MatrixSpeed',
                    IniFloat(default=0.1),
                    'Time scale of the "matrix" camera (Cameras_ReadMatrix 0x410ce0).',
                ),
                _k('MatrixFOV', IniFloat(default=60.0, unit='deg'), 'Its field of view; missing: 60.'),
                _k('MatrixArmVectorX', IniFloat(default=4.5, unit='m'), 'Camera offset x; missing: 4.5.'),
                _k('MatrixArmVectorY', IniFloat(default=0.0, unit='m'), 'Camera offset y; missing: 0.'),
                _k('MatrixArmVectorZ', IniFloat(default=7.88, unit='m'), 'Camera offset z; missing: 7.88.'),
            ],
            'Slow motion camera',
        )
    )
    return sections


class Nfs6CamerasIni(IniFile):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'NFS Hot Pursuit 2 PC `Cars/Cameras.ini`: the race cameras (the same for every car), '
            'read when the file exists by Cameras_ReadMaster 0x40e730 and one reader per view; `-2plr` / `-2ptb` are '
            "the split screen views. Missing keys keep the readers' defaults",
        }

    Fields = ini_fields_class(_camera_sections())


class Nfs6RearViewIni(IniFile):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'NFS Hot Pursuit 2 PC `Cars/RearView.ini`. Not read: no `RearView.ini`, `ScreenX`, '
            "`topCrop`, `persist`... string in the executable (the HUD's rear view mirror has its own settings)",
        }

    Fields = ini_fields_class(
        [
            _section(
                'mirror',
                'mirror',
                [_not_read(n, IniFloat()) for n in ('ScreenX', 'ScreenY', 'width', 'height')],
                'Not read',
            ),
            _section(
                'texture',
                'texture',
                [_not_read(n, IniInt()) for n in ('width', 'height', 'bpp')]
                + [_not_read(n, IniFloat()) for n in ('topCrop', 'botCrop')],
                'Not read',
            ),
            _section(
                'rendering',
                'rendering',
                [
                    _not_read(n, IniInt())
                    for n in (
                        'on',
                        'fov',
                        'AspectRatio',
                        'rate',
                        'sky',
                        'persist',
                        'gobs',
                        'particles',
                        'cars',
                        'effects',
                    )
                ],
                'Not read',
            ),
        ]
    )


class Nfs6ReflectionIni(IniFile):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'NFS Hot Pursuit 2 PC `Cars/reflection.ini`: the dynamic car reflections, read by '
            'Reflection_Init 0x53dfc0',
        }

    Fields = ini_fields_class(
        [
            _section(
                'brightness',
                'brightness',
                [
                    _k(c, IniInt(), f'Environment map brightness, {c} 0..255 -> reflection +{o}.')
                    for c, o in (('red', '0x8'), ('green', '0xc'), ('blue', '0x10'))
                ],
                'Reflection brightness',
            ),
            _section(
                'render',
                'render',
                [_not_read('cubeface_dimension', IniInt()), _not_read('enviromap_dimension', IniInt())],
                'Not read',
            ),
        ]
    )


# ---------------------------------------------------------------------------------------------------------------------
# cartable.viv: engine sound tables (CRDl)
# ---------------------------------------------------------------------------------------------------------------------

CRDL_TABLES_OFFSET = 0x168
CRDL_TABLE_SIZE = 0x200


class Nfs6EngineAudioTable(DeclarativeCompoundBlock):
    """`Cars/cartable.viv` items `engine.rpm`, `engine.ctb`, `engine.htb`, `engine.ltb`, `engine.btb` ("CRDl")"""

    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'NFS Hot Pursuit 2 PC engine sound table ("CRDl"), an item of `Cars/cartable.viv`. '
            'EngineAudio_Load 0x4355e0 loads `engine.ltb`, `engine.ctb` and `engine.rpm` (`engine.htb` / '
            '`engine.btb` are never loaded) and EngineAudio_RelocateTables 0x4354c0 turns the table offsets into '
            'pointers (flag +5). EngineAudio_Update 0x4349e0 plays up to 16 engine samples at once: the 8 slots of '
            'engine.ctb (the engine without load) and the 8 of engine.ltb (under load), crossfaded by the engine load; '
            "each slot's volume table is read at the sound index = (rpm - MinRPM) x 127 / (RedLine - MinRPM) "
            '(0x435430, 0..127) and its pitch table bends the sample (64 = its own pitch). engine.rpm (one slot, '
            'identity table) is loaded but only checked for presence: the FakeRPM debug line shows the same index',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        magic = (UTF8Block(length=4, value_validator=Eq('CRDl')), {'description': 'Magic "CRDl"'})
        version = (IntegerBlock(length=1), {'description': '2 in every file'})
        relocated = (
            IntegerBlock(length=1),
            {'description': 'Set to 1 by the game once the offsets are pointers (0x4354c0); 0 in the files'},
        )
        unk0 = (IntegerBlock(length=1), {'description': '0 in every file', 'is_unknown': True})
        unk1 = (IntegerBlock(length=1), {'description': '0 (engine.rpm) or 100', 'is_unknown': True})
        header_values = (
            ArrayBlock(child=IntegerBlock(length=2), length=12),
            {
                'description': 'Header values, the same in every file (20, 15, 500, 0, 200, 0, 100, 40, 300, 0, 100, '
                '0: 16-bit words); no reader found',
                'is_unknown': True,
            },
        )
        slots = (
            ArrayBlock(child=IntegerBlock(length=1, is_signed=True), length=8),
            {
                'description': "Engine sample of each slot: index of the patch in the car's engine sound bank "
                '(cxhi, cxmd, cxid, cehi... / lxhi...), -1 = slot unused; the game counts slots up to the last used one'
            },
        )
        reserved = (
            ArrayBlock(child=IntegerBlock(length=1), length=0x100),
            {'description': 'Zeros in every file', 'is_unknown': True},
        )
        volume_table_offsets = (
            ArrayBlock(child=IntegerBlock(length=4), length=8),
            {
                'description': 'Per slot: offset of its volume table from this entry (pointer = entry address + '
                'value), 0 for an unused slot'
            },
        )
        pitch_table_offsets = (
            ArrayBlock(child=IntegerBlock(length=4), length=8),
            {'description': 'Per slot: offset of its pitch table from this entry, 0 for an unused slot'},
        )
        tables = (
            ArrayBlock(
                child=ArrayBlock(child=IntegerBlock(length=1, is_signed=True), length=CRDL_TABLE_SIZE),
                length=(lambda ctx: ctx.read_bytes_remaining // CRDL_TABLE_SIZE, '(file size - 0x168) / 512'),
            ),
            {
                'description': 'The tables, 512 signed bytes each: volume 0..127 per sound index, pitch (64 = the '
                "sample's pitch) per sound index; the game reads entries 0..127"
            },
        )
        trailing = (
            ArrayBlock(child=IntegerBlock(length=1), length=(lambda ctx: ctx.read_bytes_remaining, 'rest')),
            {'description': 'Bytes after the last whole table (none in the files)'},
        )

    def serializer_class(self):
        from serializers import BlockJsonSerializer

        return BlockJsonSerializer

    def from_json(self, json_data: dict, current: dict = None) -> dict:
        res = dict(current) if current is not None else self.new_data()
        for name, _ in self.field_blocks:
            if name in json_data:
                res[name] = json_data[name]
        return res

    @staticmethod
    def table_index(offsets_field: str, slot: int, offset: int):
        """Index in `tables` of a slot's table: entry address + offset, from the start of the tables"""
        if not offset:
            return None
        base = 0x128 if offsets_field == 'volume_table_offsets' else 0x148
        pos = base + 4 * slot + offset - CRDL_TABLES_OFFSET
        return pos // CRDL_TABLE_SIZE if pos >= 0 and pos % CRDL_TABLE_SIZE == 0 else None


# file name (lower case) -> block class
NFS6_CAR_INI_FILES = {
    'car.ini': Nfs6CarIni,
    'car_hp.ini': Nfs6CarHpIni,
    'car_cop.ini': Nfs6CarCopIni,
    'carracer.ini': Nfs6CarRacerIni,
    'vehicle.ini': Nfs6VehicleIni,
    'bounds.ini': Nfs6BoundsIni,
    'geomdata.ini': Nfs6GeomDataIni,
    'damage.ini': Nfs6DamageIni,
    'lod.ini': Nfs6LodIni,
    'cars.ini': Nfs6CarsIni,
    'cameras.ini': Nfs6CamerasIni,
    'rearview.ini': Nfs6RearViewIni,
    'reflection.ini': Nfs6ReflectionIni,
}


def nfs6_car_ini_class(file_path: str):
    """The block of an NFS HP2 PC car spec INI file: by its name, in a `Cars` folder (`Cars/<car>/` or `Cars/`)"""
    parts = file_path.replace('\\', '/').split('/')
    name = parts[-1].lower()
    block = NFS6_CAR_INI_FILES.get(name)
    if block is None:
        return None
    folders = [p.lower() for p in parts[:-1]]
    if name in ('cars.ini', 'cameras.ini', 'rearview.ini', 'reflection.ini'):
        return block if folders and folders[-1] == 'cars' else None
    return block if len(folders) >= 2 and folders[-2] == 'cars' else None


def _camel(name: str) -> str:
    return ''.join(p[:1].upper() + p[1:] for p in name.replace('-', '_').split('_') if p)


# every section and section group block, under a class name of its own (`Nfs6CarIniBasic`...): the docs list each
# one's keys, the GUI's block_class_mro starts with it
NFS6_CAR_SPEC_SECTIONS = []


def _name_sections(file_class):
    for name, field_block in file_class().field_blocks:
        block = field_block.child if isinstance(field_block, IniSectionGroup) else field_block
        if isinstance(block, IniSection) and block.__class__ in (IniSection, IniGroupSection):
            block.__class__ = type(f'{file_class.__name__}{_camel(name)}', (block.__class__,), {})
            NFS6_CAR_SPEC_SECTIONS.append(block)


for _file_class in (
    Nfs6CarIni,
    Nfs6VehicleIni,
    Nfs6CarsIni,
    Nfs6BoundsIni,
    Nfs6GeomDataIni,
    Nfs6DamageIni,
    Nfs6CamerasIni,
    Nfs6RearViewIni,
    Nfs6ReflectionIni,
):
    _name_sections(_file_class)
