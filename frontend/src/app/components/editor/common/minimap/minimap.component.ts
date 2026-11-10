import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnDestroy,
  Output,
} from '@angular/core';
import { BehaviorSubject, combineLatest, fromEvent, Observable, Subject } from 'rxjs';
import { map, takeUntil } from 'rxjs/operators';
import { Pnt2, Pnt3, Point2, Point3 } from '@gg-web-engine/core';

type Projection = 'x' | 'nx' | 'y' | 'ny' | 'z' | 'nz';

// A road drawn besides the main spline: alternative routes, branches, roads of junctions
export interface MinimapRoad {
  points: Point3[];
  closed: boolean;
}

@Component({
  selector: 'app-minimap',
  templateUrl: './minimap.component.html',
  styleUrls: ['./minimap.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: false,
})
export class MinimapComponent implements AfterViewInit, OnDestroy {
  _roadSpline$: BehaviorSubject<Point3[]> = new BehaviorSubject<Point3[]>([]);
  _roads$: BehaviorSubject<MinimapRoad[]> = new BehaviorSubject<MinimapRoad[]>([]);
  _pointer$: BehaviorSubject<Point3 | null> = new BehaviorSubject<Point3 | null>(null);
  _projection$: BehaviorSubject<Projection> = new BehaviorSubject<Projection>('nz');

  _roadSplineProjected$: BehaviorSubject<Point2[]> = new BehaviorSubject<Point2[]>([]);
  // the polylines of the main spline (closing point included) and of the other roads, projected; with the 3D points
  private lines: { points: Point3[]; projected: Point2[] }[] = [];
  _pointerProjected$: BehaviorSubject<Point2> = new BehaviorSubject<Point2>(Pnt2.O);

  @Input('roadSpline') set roadSpline(value: Point3[]) {
    this._roadSpline$.next(value);
  }

  // Other roads of the track, drawn thinner under the main spline. The pointer snaps (Shift) to them too
  @Input('roads') set roads(value: MinimapRoad[] | null) {
    this._roads$.next(value || []);
  }

  @Input('pointer') set pointer(value: Point3 | null) {
    this._pointer$.next(value);
  }

  @Input('projection') set projection(value: Projection) {
    this._projection$.next(value);
  }

  _splineClosed$: BehaviorSubject<boolean> = new BehaviorSubject<boolean>(false);

  @Input('splineClosed') set splineClosed(value: boolean) {
    this._splineClosed$.next(value);
  }
  // Draw spline points as dots, without connecting them (e.g. chunk centers of a city instead of a road)
  _pointsOnly$: BehaviorSubject<boolean> = new BehaviorSubject<boolean>(false);

  @Input() set pointsOnly(value: boolean) {
    this._pointsOnly$.next(value);
  }

  get pointsOnly(): boolean {
    return this._pointsOnly$.value;
  }
  @Output() pointerChange = new EventEmitter<Point3>();

  svgSize$: BehaviorSubject<Point2> = new BehaviorSubject({ x: 100, y: 100 });
  scalingSquare$: BehaviorSubject<{ x: number; y: number; width: number; height: number }> = new BehaviorSubject<{
    x: number;
    y: number;
    width: number;
    height: number;
  }>({ x: 0, y: 0, width: 100, height: 100 });
  mapPolyline$: BehaviorSubject<string> = new BehaviorSubject<string>('');
  mapRoadPolylines$: BehaviorSubject<string[]> = new BehaviorSubject<string[]>([]);
  mapPoints$: BehaviorSubject<Point2[]> = new BehaviorSubject<Point2[]>([]);
  mapPointer$: BehaviorSubject<Point2 | null> = new BehaviorSubject<Point2 | null>(null);

  private isShiftPressed = false;

  get trackLength$(): Observable<number> {
    return this._roadSpline$.pipe(
      map(s => {
        let ret = 0;
        for (let i = 1; i < s.length; i++) {
          ret += Pnt3.dist(s[i], s[i - 1]);
        }
        return ret;
      }),
    );
  }

  private readonly destroyed$: Subject<void> = new Subject<void>();
  private isDragging = false;

  constructor(private readonly ref: ElementRef) {}

  private projectionKeys(): ['x' | 'y' | 'z', 'x' | 'y' | 'z', 'x' | 'y' | 'z', boolean] {
    switch (this._projection$.getValue()) {
      case 'nz':
        return ['x', 'y', 'z', false];
      case 'z':
        return ['x', 'y', 'z', true];
      case 'ny':
        return ['x', 'z', 'y', false];
      case 'y':
        return ['x', 'z', 'y', true];
      case 'nx':
        return ['y', 'z', 'x', false];
      case 'x':
        return ['y', 'z', 'x', true];
    }
  }

  private unproject(point: Point2, z: number): Point3 {
    let [xKey, yKey, zKey, invert] = this.projectionKeys();
    let out = { x: 0, y: 0, z: 0 };
    out[xKey] = point.x;
    out[yKey] = invert ? -point.y : point.y;
    out[zKey] = invert ? -z : z;
    return out;
  }

  private projectionZ(point: Point3): number {
    let [_, __, zKey, invert] = this.projectionKeys();
    return invert ? -point[zKey] : point[zKey];
  }

  private project(point: Point3): Point2 {
    let [xKey, yKey, _, invertY] = this.projectionKeys();
    return { x: point[xKey], y: invertY ? -point[yKey] : point[yKey] };
  }

  ngAfterViewInit() {
    fromEvent(window, 'keydown')
      .pipe(takeUntil(this.destroyed$))
      .subscribe(event => {
        if ((event as KeyboardEvent).key === 'Shift') {
          this.isShiftPressed = true;
        }
      });
    fromEvent(window, 'keyup')
      .pipe(takeUntil(this.destroyed$))
      .subscribe(event => {
        if ((event as KeyboardEvent).key === 'Shift') {
          this.isShiftPressed = false;
        }
      });
    combineLatest([this._roadSpline$, this._roads$, this._splineClosed$, this._pointsOnly$, this._projection$])
      .pipe(takeUntil(this.destroyed$))
      .subscribe(([roadSpline, roads, splineClosed, pointsOnly, _]) => {
        const closedPoints = (points: Point3[], closed: boolean) =>
          closed && points.length > 1 ? [...points, points[0]] : points;
        this.lines = [
          ...(pointsOnly ? [] : [closedPoints(roadSpline, splineClosed)]),
          ...roads.map(road => closedPoints(road.points, road.closed)),
        ].map(points => ({ points, projected: points.map(p => this.project(p)) }));
        this._roadSplineProjected$.next(roadSpline.map(p => this.project(p)));
      });
    combineLatest([this._pointer$, this._projection$])
      .pipe(takeUntil(this.destroyed$))
      .subscribe(([pointer, _]) => {
        this._pointerProjected$.next(this.project(pointer || Pnt3.O));
      });
    this._roadSplineProjected$
      .pipe(
        takeUntil(this.destroyed$),
        map((spline: Point2[]) => {
          const points = [...spline, ...this.lines.flatMap(line => line.projected)];
          let minPoint: Point2 = { x: Number.MAX_SAFE_INTEGER, y: Number.MAX_SAFE_INTEGER };
          let maxPoint: Point2 = { x: Number.MIN_SAFE_INTEGER, y: Number.MIN_SAFE_INTEGER };
          points.forEach(p => {
            minPoint = { x: Math.min(minPoint.x, p.x), y: Math.min(minPoint.y, p.y) };
            maxPoint = { x: Math.max(maxPoint.x, p.x), y: Math.max(maxPoint.y, p.y) };
          });
          const roadActualSize: Point2 = { x: maxPoint.x - minPoint.x, y: maxPoint.y - minPoint.y };
          // +10% margins
          return {
            x: minPoint.x - roadActualSize.x * 0.1,
            y: minPoint.y - roadActualSize.y * 0.1,
            width: roadActualSize.x * 1.2,
            height: roadActualSize.y * 1.2,
          };
        }),
      )
      .subscribe(this.scalingSquare$);

    combineLatest([this._roadSplineProjected$, this.scalingSquare$, this.svgSize$, this._splineClosed$])
      .pipe(
        takeUntil(this.destroyed$),
        map(([points, scalingSquare, svgSize, splineClosed]) => {
          const toSvg = (p: Point2): Point2 => ({
            x: ((p.x - scalingSquare.x) * svgSize.x) / scalingSquare.width,
            y: ((scalingSquare.y - p.y) * svgSize.y) / scalingSquare.height + svgSize.y,
          });
          const polyline = (line: Point2[]) => line.map(v => Math.round(v.x) + ',' + Math.round(v.y)).join(' ');
          const polygonToDraw: Point2[] = points.map(toSvg);
          this.mapPoints$.next(this.pointsOnly ? polygonToDraw : []);
          this.mapRoadPolylines$.next(
            this.lines.slice(this.pointsOnly ? 0 : 1).map(line => polyline(line.projected.map(toSvg))),
          );
          if (this.pointsOnly) {
            return '';
          }
          if (splineClosed && polygonToDraw.length) {
            polygonToDraw.push(polygonToDraw[0]);
          }
          return polyline(polygonToDraw);
        }),
      )
      .subscribe(this.mapPolyline$);

    combineLatest([this._pointerProjected$, this.scalingSquare$.asObservable(), this.svgSize$])
      .pipe(
        takeUntil(this.destroyed$),
        map(([point, scalingSquare, svgSize]) => {
          if (!point) {
            return null;
          }
          return {
            x: ((point.x - scalingSquare.x) * svgSize.x) / scalingSquare.width,
            y: ((scalingSquare.y - point.y) * svgSize.y) / scalingSquare.height + svgSize.y,
          };
        }),
      )
      .subscribe(this.mapPointer$);

    const updateSize = () => {
      this.svgSize$.next({ x: this.ref.nativeElement.clientWidth, y: this.ref.nativeElement.clientHeight });
    };
    new ResizeObserver(updateSize).observe(this.ref.nativeElement);
    updateSize();
  }

  ngOnDestroy(): void {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  startDrag(event: MouseEvent) {
    this.isDragging = true;
    this.updatePointer(event);
  }

  drag(event: MouseEvent) {
    if (this.isDragging) {
      this.updatePointer(event);
    }
  }

  endDrag() {
    this.isDragging = false;
  }

  // The nearest point of the drawn lines: line, segment index in it and position along the segment; line -1 for none
  private getClosestProjectedLineIndex(pos: Point2): [number, number, number] {
    let closest: [number, number, number] = [-1, -1, 0];
    let minDistance = Number.MAX_SAFE_INTEGER;
    this.lines.forEach(({ projected }, line) => {
      for (let i = 1; i < projected.length; i++) {
        const p = projected[i - 1];
        const d = Pnt2.sub(projected[i], p);
        const lenSq = Pnt2.lenSq(d);
        const t = lenSq ? Math.max(0, Math.min(1, ((pos.x - p.x) * d.x + (pos.y - p.y) * d.y) / lenSq)) : 0;
        const distance = Math.hypot(pos.x - (p.x + t * d.x), pos.y - (p.y + t * d.y));
        if (distance < minDistance) {
          minDistance = distance;
          closest = [line, i - 1, t];
        }
      }
    });
    return closest;
  }

  private closestProjectedPoint(pos: Point2): Point2 | null {
    const [line, i, t] = this.getClosestProjectedLineIndex(pos);
    if (line == -1) {
      return null;
    }
    const projected = this.lines[line].projected;
    return Pnt2.lerp(projected[i], projected[i + 1], t);
  }

  private getRoadSplineProjectionZ(pos: Point2): number {
    const [line, i, t] = this.getClosestProjectedLineIndex(pos);
    if (line == -1) {
      return 0;
    }
    const points = this.lines[line].points;
    return this.projectionZ(points[i]) + t * (this.projectionZ(points[i + 1]) - this.projectionZ(points[i]));
  }

  private updatePointer(event: MouseEvent) {
    const boundingRect = this.ref.nativeElement.querySelector('svg')?.getBoundingClientRect();
    if (boundingRect) {
      const localPos = {
        x: event.clientX - boundingRect.left,
        y: boundingRect.height - event.clientY + boundingRect.top,
      };
      const scalingSquare = this.scalingSquare$.getValue();
      const svgSize = this.svgSize$.getValue();

      const oldPtr = this._pointerProjected$.getValue() || Pnt2.O;
      let newPtr = {
        x: localPos.x * (scalingSquare.width / svgSize.x) + scalingSquare.x,
        y: localPos.y * (scalingSquare.height / svgSize.y) + scalingSquare.y,
      };

      if (this.isShiftPressed) {
        const oldClosest = this.closestProjectedPoint(oldPtr);
        const newClosest = this.closestProjectedPoint(newPtr);
        if (oldClosest && newClosest) {
          newPtr = Pnt2.add(Pnt2.sub(oldPtr, oldClosest), newClosest);
        }
      }
      const elevation = this.projectionZ(this._pointer$.getValue() || Pnt3.O) - this.getRoadSplineProjectionZ(oldPtr);
      this.pointerChange.emit(this.unproject(newPtr, elevation + this.getRoadSplineProjectionZ(newPtr)));
    }
  }
}
