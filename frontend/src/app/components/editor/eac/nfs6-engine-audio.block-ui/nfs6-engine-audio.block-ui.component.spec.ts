import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BehaviorSubject, Subject } from 'rxjs';
import { MainService } from '../../../../services/main.service';
import { ChangesService } from '../../../../services/changes.service';
import { crdlTableIndex, Nfs6EngineAudioBlockUiComponent } from './nfs6-engine-audio.block-ui.component';

// engine.htb's slots and offsets (Cars/cartable.viv)
const table = () => ({
  slots: [15, 16, 17, -1, -1, -1, -1, -1],
  volume_table_offsets: [0x40, 0x43c, 0x838, 0, 0, 0, 0, 0],
  pitch_table_offsets: [0x220, 0x61c, 0xa18, 0, 0, 0, 0, 0],
  tables: Array.from({ length: 6 }, (_, t) =>
    Array.from({ length: 512 }, (_, i) => (i < 128 ? (t * 10 + i) % 128 : 0)),
  ),
});

describe('Nfs6EngineAudioBlockUiComponent', () => {
  let fixture: ComponentFixture<Nfs6EngineAudioBlockUiComponent>;
  let component: Nfs6EngineAudioBlockUiComponent;
  let appendChanges: jasmine.Spy;

  beforeEach(async () => {
    appendChanges = jasmine.createSpy('appendChanges').and.returnValue(Promise.resolve());
    await TestBed.configureTestingModule({
      declarations: [Nfs6EngineAudioBlockUiComponent],
      providers: [
        { provide: MainService, useValue: { focusedResourceId$: new BehaviorSubject(null) } },
        {
          provide: ChangesService,
          useValue: {
            change$: new Subject<string>(),
            appendChanges,
            subscribeComponent: () => {},
            unsubscribeComponent: () => {},
          },
        },
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
    fixture = TestBed.createComponent(Nfs6EngineAudioBlockUiComponent);
    component = fixture.componentInstance;
    component.resourceId = 'cartable.viv__children/2/item/data';
    component.resourceSchema = { block_class_mro: 'Nfs6EngineAudioTable__DataBlock', fields: [] };
    component.resourceData = table();
    fixture.detectChanges();
  });

  it('resolves the self-relative table offsets', () => {
    expect(crdlTableIndex('volume', 0, 0x40)).toBe(0);
    expect(crdlTableIndex('pitch', 0, 0x220)).toBe(1);
    expect(crdlTableIndex('volume', 2, 0x838)).toBe(4);
    expect(crdlTableIndex('pitch', 3, 0)).toBeNull();
    expect(component.slots.map(s => [s.patch, s.volumeTable, s.pitchTable])).toEqual([
      [15, 0, 1],
      [16, 2, 3],
      [17, 4, 5],
    ]);
    expect(component.volumeSeries.length).toBe(3);
    expect(component.volumeSeries[0].points.length).toBe(128);
  });

  it('writes an edited table entry, clamped to a signed byte', () => {
    const points = component.pitchSeries[1].points.map(p => ({ ...p }));
    points[3] = { x: 3, y: 300 };
    component.onTableChange({ seriesId: component.pitchSeries[1].id, points, changed: [3] });
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.id).toBe('cartable.viv__children/2/item/data/tables/3');
    expect(change.newValue[3]).toBe(127);
    expect(change.newValue.length).toBe(512);
  });
});
