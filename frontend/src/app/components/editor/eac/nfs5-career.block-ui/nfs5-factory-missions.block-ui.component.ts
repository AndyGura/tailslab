import { ChangeDetectionStrategy, Component } from '@angular/core';
import { StatTile } from '../../common/stat-tiles/stat-tiles.component';
import { RecordListItem } from '../../common/record-list/record-list.component';
import { joinId } from '../../../../utils/join-id';
import { Nfs5CareerEditorBase, Nfs5IdRow } from './nfs5-career-base';

export const NFS5_FACTORY_LEVELS = ['', 'Junior', 'Test Driver', 'Chief'];
export const NFS5_FACTORY_NARRATORS = ['Billy', 'Stephanie', 'Dieter', 'Frank', 'Klaus', 'Rolf'];

// the rules of a mission as `Factory_RaceJudge` 0x4293f0 applies them, as text
export function nfs5MissionRules(m: { [k: string]: any }): string[] {
  const rules: string[] = [];
  if (m['min_rank_on']) return [`finish ${m['min_rank']} or better`];
  if (m['time_limit_on']) rules.push(`within ${m['time_limit']} s`);
  if (m['cones_on']) {
    rules.push(m['cone_mode'] ? `${m['cone_penalty']} s per cone hit` : `at most ${m['cone_limit']} cones hit`);
  }
  if (m['damage_limit_on']) rules.push(`damage at most ${m['damage_limit']}`);
  return rules;
}

// Rich editor of the NFS5 Factory Driver missions (FEData/Data/nfs5.fac, Nfs5FactoryMissions): the missions by level,
// one at a time: brief and race, the pass / fail rules, the player's car with its parts and paint (names from nfs5.car
// / nfs5.prt next to the file, links), the opponents, every field
@Component({
  selector: 'app-nfs5-factory-missions-block-ui',
  templateUrl: './nfs5-factory-missions.block-ui.component.html',
  styleUrls: [
    '../player-car-physics.block-ui/player-car-physics.block-ui.component.scss',
    '../nfs5-car-parts.block-ui/nfs5-car-parts.block-ui.component.scss',
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: false,
})
export class Nfs5FactoryMissionsBlockUiComponent extends Nfs5CareerEditorBase {
  readonly groups = {
    brief: [
      'desc_id',
      'level',
      'mission_number',
      'narrator',
      'end_of_level_id',
      'prize_car_id',
      'map_picture',
      'pass_ids',
      'fail_ids',
    ],
    race: ['track_id', 'laps', 'direction', 'skill_test_scene', 'traffic', 'skill', 'cops', 'passenger', 'flag_c0'],
    rules: [
      'time_limit_on',
      'time_limit',
      'damage_limit_on',
      'damage_limit',
      'cones_on',
      'cone_mode',
      'cone_limit',
      'cone_penalty',
      'min_rank_on',
      'min_rank',
    ],
    paint: ['stripe_package', 'race_number'],
    progress: ['passed', 'result_rank', 'result_damage', 'result_time'],
  };
  readonly narrators = NFS5_FACTORY_NARRATORS;

  items: RecordListItem[] = [];
  selected: number | null = null;
  selectedTab = 0;
  tiles: StatTile[] = [];
  partRows: Nfs5IdRow[] = [];
  newPartId: number | null = null;

  get missionSchema(): any {
    return this.resourceSchema?.fields?.find((f: any) => f.name === 'missions')?.schema?.child_schema;
  }

  get missions(): any[] {
    return this.resourceData?.['missions'] || [];
  }

  get mission(): any | null {
    return this.selected !== null ? this.missions[this.selected] || null : null;
  }

  get missionId(): string {
    return joinId(this.resourceId!, 'missions', this.selected!);
  }

  get base(): (string | number)[] {
    return ['missions', this.selected!];
  }

  protected refresh(): void {
    const missions = this.missions;
    if (this.selected === null || this.selected >= missions.length) this.selected = missions.length ? 0 : null;
    this.items = missions.map((m, i) => ({
      index: i,
      label: `${m['map_picture'] || 'Mission'} · ${this.carName(m['car_id'])}`,
      sub: `track ${m['track_id']} · ${nfs5MissionRules(m).join(', ') || 'no rule'}`,
      tag: '#' + i,
      group: `Level ${m['level']} · ${NFS5_FACTORY_LEVELS[m['level']] || ''}`,
    }));
    this.buildMission();
  }

  onSelect(index: number) {
    this.selected = index;
    this.buildMission();
    this.cdr.markForCheck();
  }

  private buildMission() {
    const m = this.mission;
    if (!m) {
      this.tiles = [];
      this.partRows = [];
      return;
    }
    const opponents = (m['opponents'] || []).filter((o: any) => o['personality_id']).length;
    this.tiles = [
      { label: 'Level', value: `${m['level']}`, sub: NFS5_FACTORY_LEVELS[m['level']] || '' },
      { label: 'Car', value: this.carName(m['car_id']), sub: `#${m['car_id']} · ${m['part_count']} parts` },
      {
        label: 'Track',
        value: `${m['track_id']}`,
        sub: `${m['laps'] || 1} lap(s)${m['direction'] === 2 ? ' · reverse' : ''}`,
      },
      { label: 'Rules', value: nfs5MissionRules(m)[0] || '–', sub: nfs5MissionRules(m).slice(1).join(', ') },
      { label: 'Opponents', value: `${opponents}`, sub: m['cops'] ? 'and 2 cops' : '' },
      { label: 'Narrator', value: NFS5_FACTORY_NARRATORS[m['narrator']] ?? `${m['narrator']}` },
    ];
    if (m['prize_car_id'] && m['end_of_level_id'] > 0) {
      this.tiles.push({ label: 'Prize car', value: this.carName(m['prize_car_id']), sub: 'at the end of the level' });
    }
    this.partRows = this.idRows(m['part_ids'], m['part_count'], id => this.partName(id));
  }

  fieldDescription(name: string): string {
    return this.missionSchema?.fields?.find((f: any) => f.name === name)?.description || '';
  }

  setMissionField(path: (string | number)[], value: any) {
    if (this.selected !== null) this.setValue([...this.base, ...path], value);
  }

  removePart(slot: number) {
    if (this.mission) this.removeId(this.base, 'part_ids', 'part_count', slot, this.mission);
  }

  addPart() {
    if (this.mission) this.addId(this.base, 'part_ids', 'part_count', this.newPartId, this.mission);
  }
}
