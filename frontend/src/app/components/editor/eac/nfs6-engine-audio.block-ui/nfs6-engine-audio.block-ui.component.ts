import { ChangeDetectionStrategy, Component } from '@angular/core';
import { CurveAxis, CurveSeries, CurveSeriesChange } from '../../common/curve-editor/curve-editor.component';
import { CarSpecEditorBase, GEAR_COLORS } from '../player-car-physics.block-ui/car-specs';

// CRDl layout (Nfs6EngineAudioTable, resources/eac/nfs6_car_specs.py): the offsets at 0x128 / 0x148 count from their
// own entry, the tables start at 0x168, 512 bytes each
export const CRDL_TABLES_OFFSET = 0x168;
export const CRDL_TABLE_SIZE = 0x200;
// the engine sound index the game reads the tables at (EngineAudio_RpmIndex 0x435430)
export const CRDL_USED_ENTRIES = 128;

export const crdlTableIndex = (kind: 'volume' | 'pitch', slot: number, offset: number): number | null => {
  if (!offset) return null;
  const pos = (kind === 'volume' ? 0x128 : 0x148) + 4 * slot + offset - CRDL_TABLES_OFFSET;
  return pos >= 0 && pos % CRDL_TABLE_SIZE === 0 ? pos / CRDL_TABLE_SIZE : null;
};

export type CrdlSlot = { slot: number; patch: number; volumeTable: number | null; pitchTable: number | null };

// Engine sound tables of NFS HP2 PC (`Cars/cartable.viv` items engine.ctb / engine.ltb / engine.rpm...): per slot its
// engine sample, the volume and the pitch by engine sound index (0 = MinRPM .. 127 = RedLine), editable charts
@Component({
  selector: 'app-nfs6-engine-audio-block-ui',
  templateUrl: './nfs6-engine-audio.block-ui.component.html',
  styleUrls: ['../player-car-physics.block-ui/player-car-physics.block-ui.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: false,
})
export class Nfs6EngineAudioBlockUiComponent extends CarSpecEditorBase {
  slots: CrdlSlot[] = [];
  volumeSeries: CurveSeries[] = [];
  pitchSeries: CurveSeries[] = [];
  readonly indexAxis: CurveAxis = { label: 'Engine sound index (0 = MinRPM, 127 = RedLine)', min: 0, max: 127 };
  readonly volumeAxis: CurveAxis = { label: 'Volume (0..127)', min: 0, max: 127 };
  readonly pitchAxis: CurveAxis = { label: "Pitch (64 = the sample's)", min: 0, max: 127 };

  protected refresh() {
    const d: any = this.resourceData || {};
    const slots: CrdlSlot[] = [];
    for (let i = 0; i < 8; i++) {
      const patch = d.slots?.[i] ?? -1;
      if (patch < 0) continue;
      slots.push({
        slot: i,
        patch,
        volumeTable: crdlTableIndex('volume', i, d.volume_table_offsets?.[i] ?? 0),
        pitchTable: crdlTableIndex('pitch', i, d.pitch_table_offsets?.[i] ?? 0),
      });
    }
    this.slots = slots;
    const series = (kind: 'volume' | 'pitch'): CurveSeries[] =>
      slots
        .map(s => ({ s, table: kind === 'volume' ? s.volumeTable : s.pitchTable }))
        .filter(x => x.table !== null && d.tables?.[x.table!])
        .map(({ s, table }) => ({
          id: `${table}`,
          label: `Slot ${s.slot} (patch ${s.patch})`,
          color: GEAR_COLORS[s.slot % GEAR_COLORS.length],
          points: (d.tables[table!] as number[]).slice(0, CRDL_USED_ENTRIES).map((y, x) => ({ x, y })),
          editable: 'y',
          y: { min: -128, max: 127, step: 1 },
        }));
    this.volumeSeries = series('volume');
    this.pitchSeries = series('pitch');
  }

  onTableChange(change: CurveSeriesChange) {
    const table = parseInt(change.seriesId, 10);
    const old: number[] = this.resourceData?.['tables']?.[table] || [];
    const next = old.map((v, i) =>
      change.changed.includes(i) ? Math.max(-128, Math.min(127, Math.round(change.points[i].y))) : v,
    );
    this.setValue(['tables', table], next);
  }
}
