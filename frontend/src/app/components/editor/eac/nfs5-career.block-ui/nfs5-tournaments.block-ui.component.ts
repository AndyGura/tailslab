import { ChangeDetectionStrategy, Component } from '@angular/core';
import { CurveAxis, CurveSeries, CurveSeriesChange } from '../../common/curve-editor/curve-editor.component';
import { StatTile } from '../../common/stat-tiles/stat-tiles.component';
import { RecordListItem } from '../../common/record-list/record-list.component';
import { joinId } from '../../../../utils/join-id';
import { Nfs5CareerEditorBase, Nfs5IdRow } from './nfs5-career-base';

export const NFS5_TOURNAMENT_ERAS: { [id: number]: string } = {
  521: 'Classic era (1950-69)',
  522: 'Golden era (1970-88)',
  523: 'Modern era (1989-2000)',
  524: 'Club events 1',
  525: 'Club events 2',
  526: 'Club events 3',
};

const POSITIONS = ['1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th'];

// Rich editor of the NFS5 Evolution tournaments (FEData/Data/nfs5.trn, Nfs5Tournaments): the tournaments by era, one
// at a time: entry fee and prize money (editable bars), the cars allowed, the opponents' cars, parts and paint (names
// from nfs5.car / nfs5.prt next to the file, links), the races, every field
@Component({
  selector: 'app-nfs5-tournaments-block-ui',
  templateUrl: './nfs5-tournaments.block-ui.component.html',
  styleUrls: [
    '../player-car-physics.block-ui/player-car-physics.block-ui.component.scss',
    '../nfs5-car-parts.block-ui/nfs5-car-parts.block-ui.component.scss',
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: false,
})
export class Nfs5TournamentsBlockUiComponent extends Nfs5CareerEditorBase {
  readonly groups = {
    general: ['id', 'era', 'era_year', 'kind', 'club_event', 'rally', 'skill', 'entry_fee', 'final_car_id'],
    texts: ['name_id', 'long_name_id', 'description_id', 'car_restriction_id'],
    traffic: ['traffic', 'use_traffic_list', 'traffic_cars'],
    unlocks: ['unlock_track_count', 'unlock_tracks'],
    unknown: ['unk_e9', 'unk_10e', 'unk_110', 'unk_390', 'unk_392'],
    progress: ['times_completed'],
  };
  readonly positions = POSITIONS;
  readonly raceKeys = ['track_id', 'laps', 'reverse', 'mirror', 'safe_bonus', 'ai_skill_scale'];

  items: RecordListItem[] = [];
  selected: number | null = null;
  selectedTab = 0;
  opponent = 0;
  tiles: StatTile[] = [];
  allowedRows: Nfs5IdRow[] = [];
  opponentPartRows: Nfs5IdRow[] = [];
  newCarId: number | null = null;
  newPartId: number | null = null;

  prizeSeries: CurveSeries[] = [];
  readonly positionAxis: CurveAxis = { label: 'Final standing', categories: POSITIONS };
  readonly moneyAxis: CurveAxis = { label: 'Prize money ($)', min: 0, format: v => '$' + this.fmt(v, 0) };

  get tournamentSchema(): any {
    return this.resourceSchema?.fields?.find((f: any) => f.name === 'tournaments')?.schema?.child_schema;
  }

  get tournaments(): any[] {
    return this.resourceData?.['tournaments'] || [];
  }

  get tournament(): any | null {
    return this.selected !== null ? this.tournaments[this.selected] || null : null;
  }

  get tournamentId(): string {
    return joinId(this.resourceId!, 'tournaments', this.selected!);
  }

  get base(): (string | number)[] {
    return ['tournaments', this.selected!];
  }

  get opponentId(): string {
    return joinId(this.resourceId!, 'tournaments', this.selected!, 'opponents', this.opponent);
  }

  get opponentSchema(): any {
    return this.tournamentSchema?.fields?.find((f: any) => f.name === 'opponents')?.schema?.child_schema;
  }

  get races(): any[] {
    const t = this.tournament;
    return t ? (t['races'] || []).slice(0, Math.max(0, t['race_count'] || 0)) : [];
  }

  protected refresh(): void {
    const list = this.tournaments;
    if (this.selected === null || this.selected >= list.length) this.selected = list.length ? 0 : null;
    this.items = list.map((t, i) => ({
      index: i,
      label: `Tournament ${t['id']}${t['kind'] === 2 ? ' · era final' : ''}`,
      sub: `${t['race_count']} races · fee $${this.fmt(t['entry_fee'] || 0, 0)} · 1st $${this.fmt((t['prize_money'] || [])[0] || 0, 0)}`,
      tag: '#' + t['id'],
      group: NFS5_TOURNAMENT_ERAS[t['era']] || `Era ${t['era']}`,
    }));
    this.buildTournament();
  }

  onSelect(index: number) {
    this.selected = index;
    this.opponent = 0;
    this.buildTournament();
    this.cdr.markForCheck();
  }

  onOpponent(index: number) {
    this.opponent = index;
    this.buildTournament();
    this.cdr.markForCheck();
  }

  private buildTournament() {
    const t = this.tournament;
    if (!t) {
      this.tiles = [];
      return;
    }
    this.tiles = [
      {
        label: 'Era',
        value: NFS5_TOURNAMENT_ERAS[t['era']] || `${t['era']}`,
        sub: t['kind'] === 2 ? 'era final' : t['club_event'] ? 'club event' : '',
      },
      { label: 'Races', value: `${t['race_count']}`, sub: t['rally'] ? 'ranked by time' : 'ranked by points' },
      {
        id: 'entry_fee',
        label: 'Entry fee',
        value: '$' + this.fmt(t['entry_fee'] || 0, 0),
        edit: { value: t['entry_fee'] || 0, step: 100, min: 0, unit: '$' },
      },
      { label: 'Prize, 1st', value: '$' + this.fmt((t['prize_money'] || [])[0] || 0, 0) },
      { label: 'Cars allowed', value: `${t['allowed_car_count']}` },
      { label: 'Opponents', value: `${t['opponent_count']}`, sub: `skill ${t['skill']}` },
    ];
    if (t['kind'] === 2) this.tiles.push({ label: 'Final car', value: this.carName(t['final_car_id']) });
    this.allowedRows = this.idRows(t['allowed_cars'], t['allowed_car_count'], id => this.carName(id));
    const o = (t['opponents'] || [])[this.opponent];
    this.opponentPartRows = o ? this.idRows(o['part_ids'], o['part_count'], id => this.partName(id)) : [];
    this.buildPrizes();
  }

  private buildPrizes(prizes: number[] = this.tournament?.['prize_money'] || []) {
    this.prizeSeries = [
      {
        id: 'prize',
        label: 'Prize money',
        color: '#2e7d32',
        style: 'bars',
        points: prizes.map((v, i) => ({ x: i, y: v })),
        editable: 'y',
        y: { min: 0, step: 100 },
        formatY: v => '$' + this.fmt(v, 0),
      },
    ];
  }

  onPrizePreview(e: CurveSeriesChange) {
    this.buildPrizes(e.points.map(p => p.y));
  }

  onPrizeChange(e: CurveSeriesChange) {
    const t = this.tournament;
    if (!t) return;
    const prizes = [...t['prize_money']];
    for (const i of e.changed) prizes[i] = Math.max(0, Math.round(e.points[i].y));
    this.setValue([...this.base, 'prize_money'], prizes);
  }

  onTileChange(e: { id: string; value: number }) {
    this.setValue([...this.base, e.id], Math.round(e.value));
  }

  fieldDescription(name: string): string {
    return this.tournamentSchema?.fields?.find((f: any) => f.name === name)?.description || '';
  }

  setField2(path: (string | number)[], value: any) {
    if (this.selected !== null) this.setValue([...this.base, ...path], value);
  }

  removeAllowed(slot: number) {
    if (this.tournament) this.removeId(this.base, 'allowed_cars', 'allowed_car_count', slot, this.tournament);
  }

  addAllowed() {
    if (this.tournament) this.addId(this.base, 'allowed_cars', 'allowed_car_count', this.newCarId, this.tournament);
  }

  removeOpponentPart(slot: number) {
    const o = this.tournament?.['opponents']?.[this.opponent];
    if (o) this.removeId([...this.base, 'opponents', this.opponent], 'part_ids', 'part_count', slot, o);
  }

  addOpponentPart() {
    const o = this.tournament?.['opponents']?.[this.opponent];
    if (o) this.addId([...this.base, 'opponents', this.opponent], 'part_ids', 'part_count', this.newPartId, o);
  }

  onRaceInput(race: number, key: string, raw: string) {
    this.onNumberInput([...this.base, 'races', race, key], raw, key !== 'ai_skill_scale');
  }

  onRacePrize(race: number, pos: number, raw: string) {
    this.onNumberInput([...this.base, 'races', race, 'prize', pos], raw, true);
  }
}
