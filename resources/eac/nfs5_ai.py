from library.read_blocks import (
    REMAINING,
    ArrayBlock,
    DecimalBlock,
    DeclarativeCompoundBlock,
    FixedPointBlock,
)
from resources.eac.fields.numbers import fixed16, s32, u32

# NFS5 (Porsche Unleashed) AI data files: GameData/Simulation/AI/*.BIN, TRAFCFG.DAT and the racing lines of
# GameData/Track/racer/work/*.lsp. Field meanings from Porsche.exe (nfs-web `decomp/nfs5/Porsche.exe.gzf`, the port of
# its AI in nfs-web `src/nfs5/nfs5-physics/src/ai_*.c`, addresses in the descriptions). The .BIN files and TRAFCFG.DAT
# are streams of little-endian int32 read one after the other (Udff_ReadInt 0x4a55d0); their names, rows and symbols
# come from the developers' sources next to them (prsonal.csv, SCRIPTS.CSV, glue.csv, hhglue.csv, TRAFCFG.DES), which
# the game does not read.

_HEADER_DESCRIPTION = '0 in the file; skipped by the loader'

_LEVELS = "level 0 low, 1 medium, 2 high, 3 extreme (the CSV's LOW / LO, Medium / med, high / hi, extreme)"

# the personalities of prsonal.csv / SCRIPTS.CSV in file order (SCRIPTS.CSV names the five racers otherwise: Nemesis,
# Blurrr, Zippy, JetBoy, Menace)
_PERSONALITIES = 'Nemesis, Bullit, Frost, Ranger, Chump, Cop 1, Cop 2, Cop 3, Traffic (prsonal.csv)'


def _trait(text: str):
    return s32(), {'description': f'{text}; {_LEVELS}'}


class Nfs5AiTraits(DeclarativeCompoundBlock):
    block_description = (
        "The 14 trait levels of an AI personality (prsonal.csv's rows), each 0..3. Ai_ParsePersonalities "
        '(Porsche.exe 0x407d30) turns them into the 0x54-byte personality record of the race (0x5e67c0) through '
        'tables of 4 values per trait (0x5cc1a4..0x5cc2ec), given here for levels 0..3'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        blocking_distance = _trait('Blocking distance: 35, 50, 80, 120 (0x5cc1a4)')
        cutoff_distance = _trait('Cutoff distance (tendency to cut the player off): 35, 20, 10, 0 (0x5cc1b4)')
        lookahead = _trait(
            'Lookahead: 90, 160, 210, 250 m (0x5cc1c4); the lane choice does not see cars ahead farther than it '
            '(0x401f20)'
        )
        swervyness = _trait(
            'Swervyness: the swerve offsets in m, {0, 0, 0, 0}, {-1, -0.5, 0, 1}, {-2, 0, 1, 2}, {-3, -1.5, 1.5, 3} '
            '(0x5cc1d4: one picked at random, 0x401060), and the swerve period 400, 100, 40, 10 (0x5cc214: a new '
            'pick about once in that many lane updates)'
        )
        braking = _trait('Braking: 0.85, 1, 1.2, 1.35 (0x5cc224)')
        road_rage = _trait('Road rage: 10000, 15, 40, 40 (0x5cc234) and 0, 0x60, 0x140, 0x500 (0x5cc244)')
        driving_skill = _trait('Driving skill: (35, 40, 45, 50) / 1024 (0x5cc254)')
        acceleration = _trait('Acceleration: read and not used')
        wipe_out_frequency = _trait(
            "Wipe out frequency: with the weather added, the AI racer's ticks to its next wipe out, 0x10000, 0x1000, "
            '0x800, 0x400, 0x400, plus a random part masked by 0xffff, 0x1fff, 0xfff, 0x7ff, 0x7ff (0x5cc294 / '
            '0x5cc2a8, read by 0x408360)'
        )
        cornering_ability = _trait(
            'Cornering ability: 0.5, 0.5, 0.5, 0 (0x5cc264), 0.3, 0.4, 0.5, 0.99 and 0.00109375, 0.0009375, '
            "0.000625, 1 (0x5cc274, 0x5cc284: the in control traffic model's grip factor grows back by the latter "
            'each step and returns to 1 above the former + a quarter of the rest, 0x40a900)'
        )
        best_line_ability = _trait('Best line ability: 0.3, 0.5, 0.8, 1 (0x5cc2dc)')
        rear_end_tendency = _trait('Rear end tendency: 0xffff, 0x300, 0x700, 0x200 (0x5cc2bc)')
        aggression = _trait('Aggression: 0xffff, 0x300, 0x700, 0x600 (0x5cc2cc)')
        cop_collision_firmness = _trait('Cop collision firmness: the level kept as it is')


class Nfs5AiPersonalityTraits(DeclarativeCompoundBlock):
    block_description = (
        'NFS5 AI personality traits, `GameData/Simulation/AI/prsonal.bin` (508 bytes): a header int, then 9 '
        f'personalities of [Nfs5AiTraits](#nfs5aitraits): {_PERSONALITIES}. Read by Ai_ParsePersonalities '
        '(Porsche.exe 0x407d30) at the race start; each AI racer gets the personality of its car record '
        '(`_PERSONALITY`) modulo 5 (0x407ef0)'
    )
    serializer = 'CompleteJsonSerializer'

    class Fields(DeclarativeCompoundBlock.Fields):
        header = (s32(), {'description': _HEADER_DESCRIPTION})
        personalities = (
            ArrayBlock(child=Nfs5AiTraits(), length=9),
            {'description': f'The personalities: {_PERSONALITIES}'},
        )


_REACTIONS = (
    '0 INIT, 1 END (the end of the script), 2 SPEED_BURST, 3 HONK_HORN, 4 HARD_BRAKE, 5 SWIPE, 6 ATTACK, 7 PAUSE, 8 '
    'REAR_END, 9 SWERVE, 10 MOVE_AWAY, 11 WIPE_OUT, 12 CRAZY_HORN, 13..16 DEBUG1..4 (SCRIPTS.CSV)'
)


class Nfs5AiScriptStep(DeclarativeCompoundBlock):
    block_description = 'A step of an AI script: a reaction and its time (8 bytes in the file, two bytes in the game)'

    class Fields(DeclarativeCompoundBlock.Fields):
        reaction = (
            s32(),
            {
                'description': f'Reaction: {_REACTIONS}. Kept as a byte (0x407ef0); the AI low object sets bit '
                '(reaction & 0x1f) of its mask while the step runs (0x40ab80). The lane code reacts to HONK_HORN, '
                'CRAZY_HORN, SWERVE (+30 on the left / right lane score by the step timer) and SWIPE (+5 towards the '
                "human's lane when it is less than 4 m ahead) (0x4013d0)"
            },
        )
        time = (
            s32(),
            {
                'description': 'Time: kept as a signed byte (0x407ef0); a step with a time other than 0 runs for '
                'time x 16 steps of the AI timer and ends the walk through the steps (0x40ab80)'
            },
        )


class Nfs5AiScriptAction(DeclarativeCompoundBlock):
    block_description = (
        'The script of a personality for one player action: 4 steps. 0x40ab80 walks them from where the last run '
        'ended, up to the 4th or a step whose reaction is END, the reactions and times stored per action as 4 '
        'reaction bytes and 4 time bytes'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        steps = (ArrayBlock(child=Nfs5AiScriptStep(), length=4), {'description': 'The steps'})


class Nfs5AiScript(DeclarativeCompoundBlock):
    block_description = (
        "The scripts of a personality, one per player action in the order 0x401580 asks for them (SCRIPTS.CSV's "
        'rows), none in the first 800 m of a race'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        collision = (Nfs5AiScriptAction(), {'description': 'Collision: the human hit this car less than 15 ticks ago'})
        opp_wizzed_by = (
            Nfs5AiScriptAction(),
            {
                'description': 'Opp wizzed by: this car passes the human more than 40 m/s faster along its '
                'direction, within 12 m along the slices'
            },
        )
        human_block_opp = (
            Nfs5AiScriptAction(),
            {'description': 'Human block opp: the same lane within 12 m, this car behind'},
        )
        opp_block_human = (
            Nfs5AiScriptAction(),
            {'description': 'Opp block human: the same lane within 12 m, this car ahead'},
        )
        opp_pass_human = (
            Nfs5AiScriptAction(),
            {'description': 'Opp pass human: this car passed the human within 15 ticks'},
        )
        human_pass_opp = (
            Nfs5AiScriptAction(),
            {'description': 'Human pass opp: the human passed this car within 15 ticks'},
        )
        human_honk = (Nfs5AiScriptAction(), {'description': 'Human honk: the horn held within 30 m'})


class Nfs5AiScripts(DeclarativeCompoundBlock):
    block_description = (
        'NFS5 AI scripts, `GameData/Simulation/AI/SCRIPTS.BIN` (2020 bytes): a header int, then the '
        '[Nfs5AiScript](#nfs5aiscript) of each of the 9 personalities (SCRIPTS.CSV: Nemesis, Blurrr, Zippy, JetBoy, '
        'Menace, Cop1, Cop2, Cop3, Traffic): how a car reacts to what the human player does. Read by 0x407ef0 at '
        'the race start'
    )
    serializer = 'CompleteJsonSerializer'

    class Fields(DeclarativeCompoundBlock.Fields):
        header = (s32(), {'description': _HEADER_DESCRIPTION})
        personalities = (
            ArrayBlock(child=Nfs5AiScript(), length=9),
            {'description': 'The scripts of the personalities'},
        )


class Nfs5AiGlue(DeclarativeCompoundBlock):
    block_description = (
        'NFS5 AI catch-up factors, `GameData/Simulation/AI/GLUE.BIN` and `hhglue.bin` (88 bytes each): a header '
        'int, then 21 factors (16.16) by the distance of the player to the AI car (glue.csv: player 600 m and more '
        'ahead, 540 m, .. 60 m, beside, player 60 m behind .. 600 m and more behind). 0x407ef0 loads hhglue.bin in '
        'single races and tournaments (RACE_TYPE 0 or 1) with exactly one AI racer, else GLUE.BIN, into 0x5e6ab4, '
        'the factors x 1.15 above 1 and x 0.85 below 1 with cops; nothing reads them'
    )
    serializer = 'CompleteJsonSerializer'

    class Fields(DeclarativeCompoundBlock.Fields):
        header = (s32(), {'description': _HEADER_DESCRIPTION})
        factors = (
            ArrayBlock(child=fixed16(), length=21),
            {
                'description': 'Factors, from the player 600 m or more ahead to 600 m or more behind, 60 m apart, '
                'entry 10 beside the AI car (glue.csv)'
            },
        )


def _fixed(name: str, use: str):
    return fixed16(), {'description': f'`.DES`: "{name}". {use}'}


def _int1024(name: str, use: str):
    return (
        FixedPointBlock(fraction_bits=10, length=4, is_signed=True),
        {'description': f'`.DES`: "{name}", type `Fixed` there; read as an integer x 1/1024 (0x5b25b8). {use}'},
    )


class Nfs5AiControl(DeclarativeCompoundBlock):
    block_description = (
        'AI physics parameters of the traffic car model (`.DES` chains "In Control AI Physics parameters" / "Out Of '
        'Control AI Physics parameters"), 11 values: the in control set at 0x5e6d1c (read by the in control model '
        '0x409c70), the out of control set at 0x5e6d48 (the out of control model 0x409720)'
    )

    class Fields(DeclarativeCompoundBlock.Fields):
        dlpos_to_dlvel = _fixed(
            'dlpos_to_dlvel:delta lateral position to desired lateral velocity',
            'In control: only into values nothing reads; out of control: not read ("not used for ooc")',
        )
        max_dlvel = _fixed(
            'max_dlvel:maximum desired lateral velocity',
            'In control: only into values nothing reads; out of control: read',
        )
        dlvel_to_clacc = _fixed('dlvel_to_clacc:delta desired lateral velocity to lateral acceleration', 'Read')
        max_clacc = _fixed('NOT USED:---max_clacc:maximum lateral acceleration', 'Not read')
        dangle_to_dav = _fixed('dangle_to_dav:delta angle to desired angular velocity', 'Read')
        max_dav = _int1024('max_dav', 'Read')
        dav_to_aa = _fixed('dav_to_aa:delta desired ang vel to angular acceleration', 'Read')
        max_aa = _int1024('NOT USED:---max_aa:maximum desired angular acceleration', 'Not read')
        vel_limit_range = _fixed(
            'vel_limit_range:under this speed we limit lateral and ang vel',
            'Read; a car slower than the out of control value - 3 is out of control (0x409570)',
        )
        lat_vel_limit_factor = _fixed(
            'lat_vel_limit_factor:limit lat vel by speed/vel_limit_range * this #',
            'In control: only into values nothing reads; out of control: read',
        )
        ang_vel_limit_factor = _int1024(
            'ang_vel_limit_factor:limit ang vel by speed/vel_limit_range * this #',
            'Read',
        )


class Nfs5TrafficConfig(DeclarativeCompoundBlock):
    block_description = (
        'NFS5 AI physics configuration, `GameData/Simulation/AI/TRAFCFG.DAT` (108 bytes, 27 int32). The game never '
        'opens it: Ai_Start parses its built-in copy 0x5cc0e0, the same bytes (Ai_ParseTrafCfg 0x406ba0). Names '
        "and order from the developers' field descriptions `TRAFCFG.DES` next to it (`Fixed` = 16.16)"
    )
    serializer = 'CompleteJsonSerializer'

    class Fields(DeclarativeCompoundBlock.Fields):
        latvelcalc_lookahead = (
            s32(),
            {
                'description': '`.DES`: "latvelcalc_lookahead: how far do we look ahead to calc lateral '
                'velocity(sl)". Slices (0x5e6d08); only feeds 0x40ee20, whose result the out of control model '
                '0x409720 drops'
            },
        )
        min_lookahead = (
            s32(),
            {
                'description': '`.DES`: "min_lookahead:what is the min # meters to look ahead to find trget direc". '
                "The traffic's target point looks at least this / 6 slices ahead (0x5e6d0c)"
            },
        )
        max_lookahead = (
            s32(),
            {
                'description': '`.DES`: "max_lookahead:what is the max # of meters to look to find target '
                'direction". At most this / 6 slices ahead (0x5e6d10)'
            },
        )
        look_ahead_factor = _fixed(
            'look_ahead_factor:convert from speed to # slices ahead to calc target dir',
            'Kept at 0x5e6d14, not read (the target point 0x4090c0 uses its own 0.7, 0x5b2618)',
        )
        skid_value = _fixed('skid_value:for calculating front skid/rear skid', 'Kept at 0x5e6d18, not read')
        in_control = (Nfs5AiControl(), {'description': '`.DES` chain "In Control AI Physics parameters"'})
        out_of_control = (Nfs5AiControl(), {'description': '`.DES` chain "Out Of Control AI Physics parameters"'})


class Nfs5AiLinePoint(DeclarativeCompoundBlock):
    block_description = 'A point of the racing line, world coordinates in meters'

    class Fields(DeclarativeCompoundBlock.Fields):
        x = (DecimalBlock(length=4), {'description': 'X'})
        z = (DecimalBlock(length=4), {'description': 'Z'})


class Nfs5AiRacingLine(DeclarativeCompoundBlock):
    block_description = (
        'NFS5 AI racing line, `GameData/Track/racer/work/<track><reverse>.lsp` (`<track>0.lsp` forward, '
        '`<track>1.lsp` reversed): the line speed record of Porsche.exe (AIDataRecord_LineSpeed_t, 0x4031f0 / '
        "0x4033d0; at 0x5e671c): 4 + 8 x the track's slice count bytes (every file of the 15 tracks). A missing "
        'file is a zeroed block'
    )
    serializer = 'CompleteJsonSerializer'

    class Fields(DeclarativeCompoundBlock.Fields):
        header = (u32(), {'description': '1 in every file; not read (the points start at +4)'})
        points = (
            ArrayBlock(child=Nfs5AiLinePoint(), byte_length=(REMAINING, 'file size - 4')),
            {
                'description': 'The racing line point of each road spline slice ([CrpSplineSlice](#crpsplineslice) '
                "of the track's CRP), about 6 m apart (0x403450). The AI racers aim at the mean of the points of "
                "4 slices from their steering look-ahead on, at the slice centre's height + 1 m, and keep to the "
                "side of another car's line point (0x40bfe0); the reset (0x40f540) puts an AI racer on the point of "
                'its slice'
            },
        )
