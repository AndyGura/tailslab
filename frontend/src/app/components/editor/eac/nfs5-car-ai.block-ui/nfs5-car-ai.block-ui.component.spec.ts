import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BehaviorSubject, Subject } from 'rxjs';
import { Nfs5CarAiBlockUiComponent, nfs5AiRescale } from './nfs5-car-ai.block-ui.component';
import { MainService } from '../../../../services/main.service';
import { ChangesService } from '../../../../services/changes.service';

const ais = () => ({
  name: 'Porsche 993',
  lookahead_slices: Array.from({ length: 24 }, (_, i) => 8 + i),
  speeds: Array.from({ length: 40 }, (_, i) => 90 - i * 2),
  unused: [0, 0, 0, 0],
});

describe('Nfs5CarAiBlockUiComponent', () => {
  let fixture: ComponentFixture<Nfs5CarAiBlockUiComponent>;
  let component: Nfs5CarAiBlockUiComponent;
  let appendChanges: jasmine.Spy;

  beforeEach(async () => {
    appendChanges = jasmine.createSpy('appendChanges').and.returnValue(Promise.resolve());
    await TestBed.configureTestingModule({
      imports: [Nfs5CarAiBlockUiComponent],
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
    fixture = TestBed.createComponent(Nfs5CarAiBlockUiComponent);
    component = fixture.componentInstance;
    component.resourceId = 'x/993.ais';
    component.resourceSchema = { block_class_mro: 'Nfs5CarAi__DeclarativeCompoundBlock', fields: [] };
    component.resourceData = ais();
    fixture.detectChanges();
  });

  it('rescales the speeds above the slowest one like the loader', () => {
    // min 12: (90 - 12) x 1.1 + 12, x 0.9
    expect(nfs5AiRescale([90, 50, 12], 1.1, 0.9)).toEqual([(78 * 1.1 + 12) * 0.9, (38 * 1.1 + 12) * 0.9, 12 * 0.9]);
    // the minimum search starts at 100
    expect(nfs5AiRescale([120, 110], 2, 1)).toEqual([140, 120]);
  });

  it('shows the speeds in km/h and greys out the entry never picked', () => {
    const s = component.speedSeries[0];
    expect(s.points[0].y).toBeCloseTo(90 * 3.6, 6);
    expect(s.activeCount).toBe(39);
    expect(component.tiles[0].value).toBe('324 km/h');
  });

  it('stores look-ahead edits as whole slices', () => {
    component.onLookaheadChange({
      seriesId: 'lookahead',
      points: component.lookaheadSeries[0].points.map((p, i) => (i === 3 ? { x: p.x, y: 100 } : p)),
      changed: [3],
    });
    const change = appendChanges.calls.mostRecent().args[0];
    expect(change.id).toBe('x/993.ais__lookahead_slices');
    expect(change.newValue[3]).toBe(17);
  });

  it('stores speed edits in m/s', () => {
    component.onSpeedsChange({
      seriesId: 'speeds',
      points: component.speedSeries[0].points.map((p, i) => (i === 0 ? { x: p.x, y: 360 } : p)),
      changed: [0],
    });
    expect(appendChanges.calls.mostRecent().args[0].newValue[0]).toBe(100);
  });
});
