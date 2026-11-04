import { Qtrn } from '@gg-web-engine/core';
import { Vector3 } from 'three';
import { isTouchpadScroll, OrbitCamera, SelectionOrbit } from './selection-orbit';

describe('SelectionOrbit', () => {
  let canvas: HTMLCanvasElement;
  let camera: OrbitCamera;
  let orbit: SelectionOrbit;
  let blocked: boolean;

  const eye = () => new Vector3(camera.position.x, camera.position.y, camera.position.z);

  // a wheel event with the `wheelDeltaY` a device sends (Chrome makes one up for constructed events)
  function wheel(init: WheelEventInit, wheelDeltaY: number): WheelEvent {
    const event = new WheelEvent('wheel', { bubbles: true, cancelable: true, ...init });
    Object.defineProperty(event, 'wheelDeltaY', { value: wheelDeltaY });
    return event;
  }

  beforeEach(() => {
    canvas = document.createElement('canvas');
    document.body.appendChild(canvas);
    camera = {
      position: { x: 0, y: -10, z: 0 },
      rotation: Qtrn.lookAt({ x: 0, y: -10, z: 0 }, { x: 0, y: 0, z: 0 }, { x: 0, y: 0, z: 1 }),
    };
    blocked = false;
    orbit = new SelectionOrbit(camera, canvas, () => blocked);
    orbit.pivot = new Vector3(0, 0, 0);
    orbit.enabled = true;
  });

  afterEach(() => {
    orbit.dispose();
    canvas.remove();
  });

  function drag(button: number, dx: number, keys: PointerEventInit = {}) {
    const init = { button, bubbles: true, pointerId: 1, pointerType: 'mouse', ...keys };
    canvas.dispatchEvent(new PointerEvent('pointerdown', { ...init, clientX: 100, clientY: 100 }));
    canvas.dispatchEvent(new PointerEvent('pointermove', { ...init, clientX: 100 + dx, clientY: 100 }));
    canvas.dispatchEvent(new PointerEvent('pointerup', { ...init, clientX: 100 + dx, clientY: 100 }));
  }

  it('should turn around the pivot with a right drag, keeping the distance', () => {
    drag(2, 100);
    expect(eye().x).not.toBeCloseTo(0, 3);
    expect(eye().length()).toBeCloseTo(10, 6);
  });

  it('should not turn with a plain left drag (it selects) nor while the pointer is taken', () => {
    drag(0, 100);
    expect(eye().toArray()).toEqual([0, -10, 0]);
    blocked = true;
    drag(2, 100);
    expect(eye().toArray()).toEqual([0, -10, 0]);
    blocked = false;
    drag(0, 100, { altKey: true });
    expect(eye().x).not.toBeCloseTo(0, 3);
  });

  it('should turn with a touchpad swipe and zoom with a pinch or a wheel notch', () => {
    // a swipe: Chrome's wheelDeltaY is -3 x deltaY
    canvas.dispatchEvent(wheel({ deltaX: 30, deltaY: 6 }, -18));
    expect(eye().x).not.toBeCloseTo(0, 3);
    expect(eye().length()).toBeCloseTo(10, 6);
    // a pinch: Ctrl
    canvas.dispatchEvent(wheel({ deltaY: 50, ctrlKey: true }, -150));
    expect(eye().length()).toBeCloseTo(10 * Math.exp(0.5), 4);
    // a mouse notch: wheelDeltaY 120
    const before = eye().length();
    canvas.dispatchEvent(wheel({ deltaY: -100 }, 120));
    expect(eye().length()).toBeCloseTo(before / 1.15, 4);
  });

  it('should tell touchpad swipes from wheel notches', () => {
    expect(isTouchpadScroll(wheel({ deltaX: 3, deltaY: 0 }, 0))).toBeTrue();
    expect(isTouchpadScroll(wheel({ deltaY: 2.5 }, -7.5))).toBeTrue();
    expect(isTouchpadScroll(wheel({ deltaY: 4 }, -12))).toBeTrue();
    // Windows / macOS mouse notches
    expect(isTouchpadScroll(wheel({ deltaY: 100 }, -120))).toBeFalse();
    expect(isTouchpadScroll(wheel({ deltaY: -4 }, 120))).toBeFalse();
    expect(isTouchpadScroll(wheel({ deltaY: 3, deltaMode: WheelEvent.DOM_DELTA_LINE }, -120))).toBeFalse();
  });

  it('should do nothing without a selection', () => {
    orbit.enabled = false;
    drag(2, 100);
    canvas.dispatchEvent(wheel({ deltaY: -100 }, 120));
    expect(eye().toArray()).toEqual([0, -10, 0]);
  });
});
