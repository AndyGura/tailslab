import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MinimapComponent } from './minimap.component';

describe('MinimapComponent', () => {
  let fixture: ComponentFixture<MinimapComponent>;
  let component: MinimapComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MinimapComponent],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
    fixture = TestBed.createComponent(MinimapComponent);
    component = fixture.componentInstance;
    fixture.nativeElement.style.display = 'block';
    fixture.nativeElement.style.width = '100px';
    fixture.nativeElement.style.height = '100px';
    fixture.detectChanges();
  });

  it('draws the other roads besides the spline, fitting all of them', () => {
    component.roadSpline = [
      { x: 0, y: 0, z: 0 },
      { x: 10, y: 0, z: 0 },
    ];
    component.splineClosed = false;
    component.roads = [
      {
        points: [
          { x: 0, y: 0, z: 0 },
          { x: 0, y: 10, z: 0 },
        ],
        closed: false,
      },
    ];
    expect(component.mapRoadPolylines$.value.length).toBe(1);
    expect(component.scalingSquare$.value).toEqual({ x: -1, y: -1, width: 12, height: 12 });
  });

  it('draws the spline as dots when told so after the spline came', () => {
    component.roadSpline = [
      { x: 0, y: 0, z: 0 },
      { x: 10, y: 0, z: 0 },
    ];
    component.roads = [
      {
        points: [
          { x: 0, y: 0, z: 0 },
          { x: 0, y: 10, z: 0 },
        ],
        closed: false,
      },
    ];
    component.pointsOnly = true;
    expect(component.mapPolyline$.value).toBe('');
    expect(component.mapPoints$.value.length).toBe(2);
    expect(component.mapRoadPolylines$.value.length).toBe(1);
  });

  it('closes a closed road', () => {
    component.roads = [
      {
        points: [
          { x: 0, y: 0, z: 0 },
          { x: 10, y: 0, z: 0 },
          { x: 10, y: 10, z: 0 },
        ],
        closed: true,
      },
    ];
    expect(component.mapRoadPolylines$.value[0].split(' ').length).toBe(4);
  });
});
