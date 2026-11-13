import { ChangeDetectionStrategy, Component } from '@angular/core';
import { CurveAxis, CurveSeries, CurveSeriesChange } from '../../common/curve-editor/curve-editor.component';
import { StatTile } from '../../common/stat-tiles/stat-tiles.component';
import { SliderSpec } from '../../common/slider-field/slider-field.component';
import { CarSpecEditorBase, fmt, MPS_TO_KMH } from '../player-car-physics.block-ui/car-specs';

// track spline slices are 6 m apart on every NFS5 track
export const NFS5_SLICE_LENGTH = 6;
// one look-ahead speed slot per 5 m/s (Porsche.exe 0x40b6ca), at most slot 23
export const NFS5_AI_SLOT_SPEED = 5;
// corner sharpness index = round(min(degrees x scale, 115) / 3) (0x40ba64): 3 degrees per entry, 38 at most
export const NFS5_AI_DEGREES_PER_ENTRY = 3;
export const NFS5_AI_MAX_INDEX = Math.round(115 / 3);

// the speeds as the race uses them (0x49ca30): with m their minimum (from 100), ((x - m) x grip ratio + m) x factor
export function nfs5AiRescale(speeds: number[], gripRatio: number, trackFactor: number): number[] {
  let m = 100;
  for (const x of speeds) if (m > x) m = x;
  return speeds.map(x => ((x - m) * gripRatio + m) * trackFactor);
}

// Rich editor of the NFS5 car AI data (GameData/Simulation/AICarData/<ai>.ais, Nfs5CarAi): how far ahead the AI
// looks for corners at each speed and the speed it takes each corner at, both editable, with the load-time rescale
// of the speeds (grip ratio, track factor). Porsche.exe 0x40b650 (target speed), 0x49ca30 (load)
@Component({
  selector: 'app-nfs5-car-ai-block-ui',
  templateUrl: './nfs5-car-ai.block-ui.component.html',
  styleUrls: ['../player-car-physics.block-ui/player-car-physics.block-ui.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: false,
})
export class Nfs5CarAiBlockUiComponent extends CarSpecEditorBase {
  selectedTab = 0;
  tiles: StatTile[] = [];
  // preview of the load-time rescale, not in the file
  gripRatio = 1;
  trackFactor = 1;
  readonly ratioSlider: SliderSpec = { min: 0.5, max: 1.5, step: 0.01, unit: '×' };

  lookaheadSeries: CurveSeries[] = [];
  speedSeries: CurveSeries[] = [];
  readonly slotAxis: CurveAxis = { label: 'Car speed (km/h)', min: 0, format: v => fmt(v, 0) };
  readonly distanceAxis: CurveAxis = { label: 'Look-ahead (m)', min: 0 };
  readonly turnAxis: CurveAxis = { label: 'Turn of the road ahead (°)', min: 0, format: v => fmt(v, 0) };
  readonly targetAxis: CurveAxis = { label: 'Target speed (km/h)', min: 0, format: v => fmt(v, 0) };
  readonly describeSlot = (kmh: number) =>
    `${fmt(kmh, 0)} km/h · slot ${Math.round(kmh / MPS_TO_KMH / NFS5_AI_SLOT_SPEED)}`;
  readonly describeTurn = (deg: number) => `${fmt(deg, 0)}° · entry ${Math.round(deg / NFS5_AI_DEGREES_PER_ENTRY)}`;

  protected refresh(): void {
    const d = this.d;
    if (!d || !Array.isArray(d['lookahead_slices']) || !Array.isArray(d['speeds'])) return;
    this.buildLookahead();
    this.buildSpeeds();
    this.buildTiles();
  }

  private buildLookahead(values: number[] = this.d['lookahead_slices']) {
    this.lookaheadSeries = [
      {
        id: 'lookahead',
        label: 'Look-ahead',
        color: '#3f51b5',
        style: 'step',
        points: values.map((v, i) => ({ x: i * NFS5_AI_SLOT_SPEED * MPS_TO_KMH, y: v * NFS5_SLICE_LENGTH })),
        editable: 'y',
        y: { min: 0, step: NFS5_SLICE_LENGTH },
        formatY: v => `${fmt(v, 0)} m · ${fmt(v / NFS5_SLICE_LENGTH, 0)} slices`,
      },
    ];
  }

  onLookaheadPreview(e: CurveSeriesChange) {
    if (e.seriesId === 'lookahead') this.buildLookahead(e.points.map(p => p.y / NFS5_SLICE_LENGTH));
  }

  onLookaheadChange(e: CurveSeriesChange) {
    if (e.seriesId !== 'lookahead') return;
    const values = [...this.d['lookahead_slices']];
    // the game rounds the entry to whole slices (FISTP)
    for (const i of e.changed) values[i] = Math.max(0, Math.round(e.points[i].y / NFS5_SLICE_LENGTH));
    this.setValue(['lookahead_slices'], values);
  }

  private buildSpeeds(speeds: number[] = this.d['speeds']) {
    const formatY = (v: number) => `${fmt(v, 1)} km/h · ${fmt(v / MPS_TO_KMH, 1)} m/s`;
    this.speedSeries = [
      {
        id: 'speeds',
        label: 'In the file',
        color: '#ef6c00',
        points: speeds.map((v, i) => ({ x: i * NFS5_AI_DEGREES_PER_ENTRY, y: v * MPS_TO_KMH })),
        editable: 'y',
        activeCount: NFS5_AI_MAX_INDEX + 1,
        y: { min: 0, step: 0.5 },
        formatY,
      },
    ];
    if (this.gripRatio !== 1 || this.trackFactor !== 1) {
      this.speedSeries.push({
        id: 'raced',
        label: 'As raced',
        color: '#6a1b9a',
        dashed: true,
        points: nfs5AiRescale(speeds, this.gripRatio, this.trackFactor).map((v, i) => ({
          x: i * NFS5_AI_DEGREES_PER_ENTRY,
          y: v * MPS_TO_KMH,
        })),
        formatY,
      });
    }
  }

  onSpeedsPreview(e: CurveSeriesChange) {
    if (e.seriesId === 'speeds') this.buildSpeeds(e.points.map(p => p.y / MPS_TO_KMH));
  }

  onSpeedsChange(e: CurveSeriesChange) {
    if (e.seriesId !== 'speeds') return;
    const speeds = [...this.d['speeds']];
    for (const i of e.changed) speeds[i] = Math.max(0, Math.round((e.points[i].y / MPS_TO_KMH) * 100) / 100);
    this.setValue(['speeds'], speeds);
  }

  onRescale(gripRatio: number, trackFactor: number) {
    this.gripRatio = gripRatio;
    this.trackFactor = trackFactor;
    this.buildSpeeds();
    this.cdr.markForCheck();
  }

  private buildTiles() {
    const d = this.d;
    const speeds: number[] = d['speeds'];
    const look: number[] = d['lookahead_slices'];
    this.tiles = [
      {
        label: 'Straights',
        value: `${fmt(speeds[0] * MPS_TO_KMH, 0)} km/h`,
        sub: `${fmt(speeds[0], 1)} m/s target, entry 0`,
        hint: 'The AI target speed with no turn ahead',
        tone: 'accent',
      },
      {
        label: 'Hairpins',
        value: `${fmt(speeds[NFS5_AI_MAX_INDEX] * MPS_TO_KMH, 0)} km/h`,
        sub: `entry ${NFS5_AI_MAX_INDEX}, ${NFS5_AI_MAX_INDEX * NFS5_AI_DEGREES_PER_ENTRY}° and more`,
        hint: 'The slowest entry the AI can pick (entry 39 is never picked)',
      },
      {
        label: 'Look-ahead',
        value: `${fmt(look[0] * NFS5_SLICE_LENGTH, 0)}–${fmt(look[look.length - 1] * NFS5_SLICE_LENGTH, 0)} m`,
        sub: `${fmt(look[0], 0)}–${fmt(look[look.length - 1], 0)} slices`,
      },
      { label: 'Name', value: d['name'] || '–' },
    ];
  }

  readonly fmt = fmt;
}
