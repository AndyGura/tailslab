from typing import Dict

from library.read_blocks import (
    ArrayBlock,
    BytesBlock,
    DecimalBlock,
    DeclarativeCompoundBlock,
    IntegerBlock,
)
from library.read_blocks.misc.value_validators import Lte
from resources.eac.car_specs import Latin1Block

# NFS5 (Porsche Unleashed) front end data holding cars of the career modes: FEData/Data/nfs5.fac (Factory Driver
# missions), nfs5.trn (Evolution tournaments, era finals, club events), nfs5.per (AI personalities). Field meanings
# from Porsche.exe (nfs-web `decomp/nfs5/Porsche.exe.gzf`, addresses in the descriptions). No headers, little endian.
# Colours are stored A, R, G, B (read as 0xAARRGGBB, the exe byte-swaps the dword, 0x51aaf6). Car ids are nfs5.car
# record ids ([Nfs5CarRecord](#nfs5carrecord)), part ids nfs5.prt ids ([Nfs5CarPart](#nfs5carpart)), personality ids
# nfs5.per ids, track ids nfs5.trk ids, texts FEStrings ids (FEData/Locale)


def _s16(text: str, **extras):
    return IntegerBlock(length=2, is_signed=True), {'description': text, **extras}


def _s32(text: str, **extras):
    return IntegerBlock(length=4, is_signed=True), {'description': text, **extras}


def _u8(text: str, **extras):
    return IntegerBlock(length=1), {'description': text, **extras}


def _pad(n: int, text: str = 'Zeros, read by no code (padding)'):
    return BytesBlock(length=n), {'description': text}


def _argb(n: int, text: str):
    return (
        ArrayBlock(child=IntegerBlock(length=4, byte_order='big'), length=n),
        {'description': text + ' (0xAARRGGBB, stored A, R, G, B)'},
    )


def _car_paint_fields(prefix_text: str):
    """the paint of a car of a mission or an opponent: 3 body colours, a pad, 3 interior colours, the stripe, race
    number (nfs5.fac +0xa0, nfs5.trn opponent +0x34)"""
    return {
        'body_colours': _argb(
            3,
            f'Body colours: the first is the body colour (FE car +0x674, `_COLORCONFIG` 0; {prefix_text}), the others '
            'read by no code',
        ),
        'padding_colours': _pad(4, 'Zeros, read by no code (no paint flag here, unlike nfs5.car paints)'),
        'interior_colours': _argb(
            3,
            'Interior colours: the first is the interior colour (FE car +0x678, `_COLORCONFIG` 3), the others read by '
            'no code',
        ),
        'stripe_package': _s16(
            'Stripe package by its values (0, 2..6): the front end passes it as the colours of slots 1 and 2 '
            '(`_COLORCONFIG` 1 / 2, FE car +0x67c / +0x680) and sends stripe package 0 (`FECar_Construct` 0x4ee3b0), so '
            'the car shows no stripes'
        ),
        'race_number': _s16('Race number (`_RACENUMBER`), -1 none'),
    }


# ---------------------------------------------------------------------------------------------------------------------
# nfs5.fac: Factory Driver missions
# ---------------------------------------------------------------------------------------------------------------------


class Nfs5FactoryOpponent(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {**super().schema, 'block_description': 'An opponent of a Factory Driver mission, 4 bytes'}

    class Fields(DeclarativeCompoundBlock.Fields):
        personality_id = _s16(
            'nfs5.per personality id ([Nfs5Personality](#nfs5personality)) [9, 30]: 0 = no opponent '
            '(`FE_SendFactoryOpponents` 0x4ec1e9); its skills are sent as they are'
        )
        car_id = _s16(
            'nfs5.car id ([Nfs5CarRecord](#nfs5carrecord)) [126, 180]: stock parts, random paint, stripe and race '
            'number'
        )


class Nfs5FactoryMission(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A Factory Driver mission, 0xf0 bytes: the brief, the track, the car the player must '
            'drive (with its parts and paint), the opponents and the pass / fail rules (`Factory_RaceJudge` 0x4293f0: '
            'time + cones x penalty over the limit, the mean of the 10 damage zones over the limit, more cones than '
            'the limit, a worse position than the minimum rank: missions with a minimum rank skip the other checks; '
            'a disabled rule is sent as -1). The current mission is the first one not passed (0x51ae80). The whole '
            'array goes into the save game (block "Missions", 0x51a870), so the result fields are game progress',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        desc_id = _s32(
            'FEStrings id of the mission brief (%s = the player name) [3001, 3500] (0x519d67); 3015 = the first '
            'mission (the factfirst screen, 0x519912)'
        )
        unused_04 = _pad(4, 'Zeros, read by no code')
        level = _s16('Level: 1 Junior, 2 Test Driver, 3 Chief [1, 3] (0x51a9a5, 0x51af90)')
        padding_0a = _pad(2)
        end_of_level_id = _s32(
            'FEStrings id of the level victory text (%s = the player name) [3191, 3495], on the last mission of a '
            'level (0x519e31, 0x51affa); the game sets it to -1 once shown (0x51af85)'
        )
        prize_car_id = _s16(
            'nfs5.car id of the car given at the level end (222 F901, 221 FBoxster, 223 F996; `Factory_AcceptPrizeCar` '
            '0x51a6d0: white, stock parts)'
        )
        unused_12 = _pad(10, 'Zeros, read by no code')
        mission_number = _s16('Number of the mission in its level [1, 13], read by no code')
        narrator = _s16(
            'Who briefs it [0, 5]: 0 Billy, 1 Stephanie, 2 Dieter, 3 Frank, 4 Klaus, 5 Rolf (FEStrings 2500 + it, the '
            'FactoryPeople.fsh portrait, race option CHARACTER; 0x519dca, 0x51a184, 0x4ec0a7)'
        )
        track_id = _s16('nfs5.trk track id [8, 34] (32 the skid pad; 0x4fc52a)')
        laps = _s16('Laps, 0 means 1 [0, 3] (0x4fc55b)')
        skill_test_scene = _s16(
            'Skill test scene (race option SCENENUMBER, 0x4ece61): with it the race type is 4 and the race loads '
            '`<track>_ST<n>.scn` (0x46d330); 0 none'
        )
        cops = _u8("Not 0: two cops join (COPS; the track record's cop cars, 0x4ed0c1)")
        padding_27 = _pad(1)
        direction = _s16('Direction: 2 reverse, 0 / 1 forward (0x4fc596)')
        passenger = _u8('1: a passenger rides along (`_PASSENGER`, human car only, 0x4eef4f)')
        unused_2b = _pad(0x14, 'Zeros, read by no code')
        map_picture = (
            Latin1Block(length=0x15),
            {'description': 'Mission map picture `FEData/Factory/<name>.fsh` ("1m01"; 0x51a324)'},
        )
        traffic = _s16('Traffic: 0, 1, 2 = 0, 2, 4 cars (table 0x5db448; 0x4fc5a4)')
        skill = _s16("Opponents' skill (SKILL, as Game.Difficulty) [0, 2] (0x4eb57a)")
        pass_ids = (
            ArrayBlock(child=IntegerBlock(length=4, is_signed=True), length=3),
            {
                'description': 'hud.loc ids of the lines said on a pass (0 none; one picked at random, options 0xf4..0xf6)'
            },
        )
        fail_ids = (
            ArrayBlock(child=IntegerBlock(length=4, is_signed=True), length=3),
            {'description': 'hud.loc ids of the lines said on a fail (options 0xf7..0xf9)'},
        )
        car_id = _s16('nfs5.car id of the car the player drives [126, 184] (`Factory_MakeMissionCar` 0x51aa50)')
        part_count = (
            IntegerBlock(length=2, is_signed=True, value_validator=Lte(22)),
            {'description': 'Number of `part_ids` [12, 17] (0x51ab80)'},
        )
        part_ids = (
            ArrayBlock(child=IntegerBlock(length=2, is_signed=True), length=22),
            {
                'description': 'nfs5.prt ids installed on the car, the first `part_count`: each replaces the part of '
                'its type and name (`Factory_InstallParts` 0x51b240)'
            },
        )
        body_colours = _car_paint_fields('0x51aab9')['body_colours']
        padding_colours = _car_paint_fields('')['padding_colours']
        interior_colours = _car_paint_fields('')['interior_colours']
        stripe_package = _car_paint_fields('')['stripe_package']
        race_number = _car_paint_fields('')['race_number']
        flag_c0 = _u8(
            '1 in missions 0 and 29, read by no code: the exe forces a manual gearbox in mission 29 and traction '
            'control in mission 14 by their index (`FE_SendHumanCar` 0x4eb9b8)'
        )
        time_limit_on = _u8('1: the time limit counts (0x4ec0ba)')
        time_limit = _s16('Time limit, s [15, 385] (0x4ec0c7)')
        damage_limit_on = _u8('1: the damage limit counts')
        padding_c5 = _pad(1)
        damage_limit = _s16('Damage limit: the mean of the 10 damage zones (%?) [5, 50] (0x434fa0)')
        cones_on = _u8('1: the cones count')
        padding_c9 = _pad(1)
        cone_mode = _s16('Cones: 0 a limit (`cone_limit`), 1 a time penalty (`cone_penalty`) (0x4ec10f)')
        cone_limit = _s16('Most cones hit to pass [0, 1]')
        cone_penalty = _s16('Seconds per cone hit [1, 4]')
        min_rank_on = _u8('1: the minimum rank counts (and the other rules not)')
        padding_d1 = _pad(1)
        min_rank = _s16('Worst position that passes [1] (0x4ec16b)')
        opponents = (
            ArrayBlock(child=Nfs5FactoryOpponent(), length=5),
            {'description': 'Opponents; an entry counts when its personality is not 0'},
        )
        passed = _s16('Progress: 1 passed (0 in the file; 0x51af4c)')
        result_rank = _s16('Progress: the position of the last run, written only')
        result_damage = _s16('Progress: the damage of the last run, written only')
        result_time = _s16('Progress: the time of the last run, written only')


class Nfs5FactoryMissions(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'NFS5 Factory Driver missions, `FEData/Data/nfs5.fac`: 34 '
            '[Nfs5FactoryMission](#nfs5factorymission) records of 0xf0 bytes (`Factory_LoadMissions` 0x51aba0)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        missions = (
            ArrayBlock(
                child=Nfs5FactoryMission(), length=(lambda ctx: ctx.read_bytes_remaining // 0xF0, 'file size / 240')
            ),
            {'description': 'The missions'},
        )

    def serializer_class(self):
        from serializers import CompleteJsonSerializer

        return CompleteJsonSerializer


# ---------------------------------------------------------------------------------------------------------------------
# nfs5.trn: Evolution tournaments, era finals, club events
# ---------------------------------------------------------------------------------------------------------------------


class Nfs5TournamentOpponent(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'An opponent of a tournament, 0x58 bytes, read by `FE_SendTournamentOpponents` '
            '0x4ebda0 only',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        personality_id = _s16('nfs5.per personality id ([Nfs5Personality](#nfs5personality)) (0x4ebee2)')
        car_id = _s16('nfs5.car id ([Nfs5CarRecord](#nfs5carrecord)) (0x4ebe12)')
        part_count = (
            IntegerBlock(length=2, is_signed=True, value_validator=Lte(22)),
            {'description': 'Number of `part_ids` [11, 18]'},
        )
        part_ids = (
            ArrayBlock(child=IntegerBlock(length=2, is_signed=True), length=22),
            {
                'description': 'nfs5.prt ids installed over the stock parts, the first `part_count` (each replaces '
                'the part of its type and name; `FE_InstallPartList` 0x4ed880 stops at a 0)'
            },
        )
        padding_32 = _pad(2)
        body_colours = _car_paint_fields('0x4ebe1c')['body_colours']
        padding_colours = _car_paint_fields('')['padding_colours']
        interior_colours = _car_paint_fields('')['interior_colours']
        stripe_package = _car_paint_fields('')['stripe_package']
        race_number = _car_paint_fields('')['race_number']
        unk_54 = _s16('0 / 1, read by no code', is_unknown=True)
        unused_56 = _pad(2, 'Zeros, read by no code')


class Nfs5TournamentRace(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'A race of a tournament, 0xa4 bytes; the second half is progress',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        track_id = _s16('nfs5.trk track id (0x503408)')
        laps = _s16('Laps, 0 means 1 [0, 4] (0x4fc492)')
        reverse = _u8('1: driven backwards')
        mirror = _u8('1: mirrored')
        unused_06 = _pad(2, 'Zeros, read by no code')
        prize = (
            ArrayBlock(child=IntegerBlock(length=4, is_signed=True), length=8),
            {'description': 'Prize money, $, by finishing position 1..8 (TOURNRACEPRIZEMONEY1..8; 0x503fd5)'},
        )
        safe_bonus = _s32(
            'Safe driving bonus, $ [250, 25000]: x 1 / 0.5 / 0.25 for the 1st / 2nd / 3rd when the race was driven '
            'safely (`Tourn_StoreRaceResult` 0x503960)'
        )
        ai_skill_scale = (
            DecimalBlock(length=4),
            {'description': "Scales the opponents' personality skills (not the ranges) [0.5, 1] (0x4ebf44)"},
        )
        done = _u8('Progress: the race is done (0 in the file)')
        padding_31 = _pad(1)
        points = (
            ArrayBlock(child=IntegerBlock(length=2, is_signed=True), length=8),
            {'description': 'Progress: points (9 - position) of each racer'},
        )
        padding_42 = _pad(2)
        time = (
            ArrayBlock(child=IntegerBlock(length=4, is_signed=True), length=8),
            {'description': 'Progress: race time of each racer'},
        )
        bonus_won = (
            ArrayBlock(child=IntegerBlock(length=4, is_signed=True), length=8),
            {'description': 'Progress: safe driving bonus won'},
        )
        prize_won = (
            ArrayBlock(child=IntegerBlock(length=4, is_signed=True), length=8),
            {'description': 'Progress: prize money won'},
        )


class Nfs5Tournament(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'An Evolution tournament, era final or club event, 0xd40 bytes: the cars allowed, '
            'the entry fee and prizes, the opponents with their cars, parts and paint, the races. The player car must '
            'be in `allowed_cars` (`Tourn_CarAllowed` 0x504a70) and pay the entry fee before the first race. A '
            'tournament ranked in the top 3 (by points, or total time for a rally) counts as completed; the first '
            'completion advances the career year (`Tourn_Complete` 0x503ad0). The whole array goes into the save '
            'game (0x502ae0), so the progress fields are game state',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        id = _s16('Tournament id [1, 59] (`Tourn_Find` 0x503f20)')
        padding_02 = _pad(2)
        era = _s32(
            'Era, an FEStrings id: 521 Classic (1950-69), 522 Golden (1970-88), 523 Modern (1989-2000), 524..526 the '
            'club events (0x502d53)'
        )
        era_year = _s16('First year of the era (1950, 1970, 1989), read by no code (0x5049e0 has its own)')
        unlock_track_count = _s16('Number of `unlock_tracks` [0, 6]')
        unlock_tracks = (
            ArrayBlock(child=IntegerBlock(length=2, is_signed=True), length=10),
            {
                'description': 'nfs5.trk ids of locked tracks (track +0x6c = 3) opened for single races once the '
                'career reaches the end of the era (`Track_BuildLists` 0x4fbc10)'
            },
        )
        name_id = _s32('FEStrings id of the short name (SHORT)')
        long_name_id = _s32('FEStrings id of the long name (ENDERAHEADER of an era final)')
        description_id = _s32('FEStrings id of the description (DESCRIPTION / ENDERADESCRIP)')
        car_restriction_id = _s32('FEStrings id of the car restriction text (CARRESTRICTION)')
        allowed_cars = (
            ArrayBlock(child=IntegerBlock(length=2, is_signed=True), length=85),
            {'description': 'nfs5.car ids of the cars allowed, the first `allowed_car_count` (0x504a70)'},
        )
        allowed_car_count = (
            IntegerBlock(length=2, is_signed=True, value_validator=Lte(85)),
            {'description': 'Number of `allowed_cars` [1, 80]'},
        )
        entry_fee = _s32('Entry fee, $ [0, 50000] (`Tourn_EntryFee` 0x503430)')
        traffic = _s16('Traffic: 0, 1, 2 = 0, 2, 4 cars (table 0x5db438), unless `use_traffic_list`')
        club_event = _s16('1: a club event (no end-of-era screen; completed any number of times)')
        kind = _s16("2: the era final (raced in `final_car_id` on race 0's track); 0 otherwise")
        skill = _s16("Opponents' skill (SKILL) [0, 2]")
        rally = _u8('1: ranked by total time (TOURNAMENTRALLY)')
        unk_e9 = _u8('1 in some club events with traffic, read by no code', is_unknown=True)
        unused_ea = _pad(2, 'Zeros, read by no code')
        prize_money = (
            ArrayBlock(child=IntegerBlock(length=4, is_signed=True), length=8),
            {'description': 'Tournament prize money, $, by final standing 1..8 (`Tourn_PrizeMoney` 0x5034b0)'},
        )
        final_car_id = _s16(
            "nfs5.car id of the era final's car (168 550 A Spyder, 169 935, 170 GT1; `Tourn_EraFinalCar` 0x5048d0); "
            'leftovers in other records, read only for era finals'
        )
        unk_10e = _s16('0 / 1, read by no code', is_unknown=True)
        unk_110 = _s16('0 / 13, read by no code', is_unknown=True)
        unused_112 = _pad(2, 'Zeros, read by no code')
        opponent_count = (
            IntegerBlock(length=2, is_signed=True, value_validator=Lte(7)),
            {'description': 'Number of `opponents` [7] (0x4ebded)'},
        )
        padding_116 = _pad(2)
        opponents = (
            ArrayBlock(child=Nfs5TournamentOpponent(), length=7),
            {'description': 'Opponents, the first `opponent_count`'},
        )
        use_traffic_list = _u8('1: the traffic is the cars of `traffic_cars` (their count) instead of `traffic`')
        padding_381 = _pad(1)
        traffic_cars = (
            ArrayBlock(child=IntegerBlock(length=2, is_signed=True), length=7),
            {'description': 'nfs5.car traffic car ids (0 none), red (0x4ecf00)'},
        )
        unk_390 = _s16('1 in tournament 26 only, read by no code', is_unknown=True)
        unk_392 = _s16('211 in tournament 26 only (a car id?), read by no code', is_unknown=True)
        unused_394 = _pad(8, 'Zeros, read by no code')
        race_count = (
            IntegerBlock(length=2, is_signed=True, value_validator=Lte(15)),
            {'description': 'Number of `races` [1, 9]; the loader clamps it to 10 (0x502d36)'},
        )
        padding_39e = _pad(2)
        races = (
            ArrayBlock(child=Nfs5TournamentRace(), length=15),
            {'description': 'Races, the first `race_count` (at most 10 usable)'},
        )
        times_completed = _s16('Progress: times completed (TIMESCOMPLETED; 0 in the file)')
        padding_d3e = _pad(2)


class Nfs5Tournaments(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'NFS5 Evolution tournaments, `FEData/Data/nfs5.trn`: 35 '
            '[Nfs5Tournament](#nfs5tournament) records of 0xd40 bytes (`Tourn_Load` 0x502ff0)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        tournaments = (
            ArrayBlock(
                child=Nfs5Tournament(), length=(lambda ctx: ctx.read_bytes_remaining // 0xD40, 'file size / 3392')
            ),
            {'description': 'The tournaments'},
        )

    def serializer_class(self):
        from serializers import CompleteJsonSerializer

        return CompleteJsonSerializer


# ---------------------------------------------------------------------------------------------------------------------
# nfs5.per: AI personalities
# ---------------------------------------------------------------------------------------------------------------------


def _f32(text: str):
    return DecimalBlock(length=4), {'description': text}


class Nfs5Personality(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'An AI personality (an opponent driver), 0x2c bytes: its skills by the corner band '
            'the AI drives (the race draws a skill factor uniform in skill +- range; `_SKILL*`, read by the AI target '
            'speed 0x40b650)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        id = _s16('Personality id [1, 37] (`FE_FindPersonality` 0x4e3120)')
        padding_02 = _pad(2)
        name_id = _s32('FEStrings id of the name (18000.., 2500..2505 the factory people)')
        difficulty_pool = _s16('Quick races pick personalities whose pool is Game.Difficulty [0, 2] (0x4e3160)')
        padding_0a = _pad(2)
        skill_slow = _f32('Skill in slow corners (`_SKILLSLOW`, corner index > 20) [0.4, 0.99]')
        range_slow = _f32('Its random range (`_SKILLRANGESLOW`) [0, 0.06]')
        skill_medium = _f32('Skill in medium corners (`_SKILLMEDIUM`, index 10..20)')
        range_medium = _f32('Its random range (`_SKILLRANGEMEDIUM`)')
        skill_fast = _f32('Skill in fast corners (`_SKILLFAST`, index <= 10)')
        range_fast = _f32('Its random range (`_SKILLRANGEFAST`)')
        skill_default = _f32('Default skill (`_SKILLDEFAULT`)')
        range_default = _f32('Its random range (`_SKILLRANGEDEFAULT`)')


class Nfs5Personalities(DeclarativeCompoundBlock):
    @property
    def schema(self) -> Dict:
        return {
            **super().schema,
            'block_description': 'NFS5 AI personalities, `FEData/Data/nfs5.per`: 35 [Nfs5Personality](#nfs5personality) '
            'records of 0x2c bytes (`FE_LoadPersonalities` 0x4e2f30)',
        }

    class Fields(DeclarativeCompoundBlock.Fields):
        personalities = (
            ArrayBlock(
                child=Nfs5Personality(), length=(lambda ctx: ctx.read_bytes_remaining // 0x2C, 'file size / 44')
            ),
            {'description': 'The personalities'},
        )

    def serializer_class(self):
        from serializers import CompleteJsonSerializer

        return CompleteJsonSerializer
