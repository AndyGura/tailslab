import { Point3, Point4, Qtrn } from '@gg-web-engine/core';
import { Quaternion, Vector3 } from 'three';

// The camera the orbit moves: a gg-web-engine renderer entity
export interface OrbitCamera {
  position: Point3;
  rotation: Point4;
}

const UP = new Vector3(0, 0, 1);
// radians per CSS pixel of a drag
const TURN_PER_PIXEL = 0.005;
// a mouse wheel step changes the distance to the pivot by this factor
const WHEEL_FACTOR = 1.15;
// a pinch (wheel event with Ctrl, deltaY in pixels) changes the distance by e^(deltaY * this)
const PINCH_ZOOM_PER_PIXEL = 0.01;
const MIN_DISTANCE = 1;
// the camera never looks straighter up or down than this (|z| of its view direction)
const MAX_PITCH_Z = 0.995;

// Whether a wheel event comes from a touchpad swipe rather than a mouse wheel notch. Browsers do not tell: a swipe
// has a sideways part or fractional deltas, or (Chrome, Safari) a `wheelDeltaY` of -3 x `deltaY` (a mouse notch has
// +-120 there)
export function isTouchpadScroll(e: WheelEvent): boolean {
  if (e.deltaMode !== WheelEvent.DOM_DELTA_PIXEL) {
    return false;
  }
  const wheelDelta: number | undefined = (e as any).wheelDeltaY;
  return (
    e.deltaX !== 0 ||
    !Number.isInteger(e.deltaY) ||
    (wheelDelta !== undefined && e.deltaY !== 0 && wheelDelta === -3 * e.deltaY)
  );
}

/**
 * The orbit camera around a selection, the way Blender does it (the left button selects): a right button drag (also a
 * middle button drag, Alt + left drag) or a two finger touchpad swipe turns the camera around the pivot (around the
 * vertical axis and its own horizontal one); the mouse wheel or a touchpad pinch moves it to and from the pivot. It
 * turns from where the camera is and how it looks (the pivot need not be in the middle of the view), so the view never
 * jumps when the pivot changes; `frame` brings the pivot into the middle. The viewer turns its other camera controller
 * off while `enabled` (and keeps the context menu off the canvas).
 */
export class SelectionOrbit {
  // the centre of the selection
  pivot: Vector3 | null = null;
  enabled = false;
  private dragFrom: { x: number; y: number } | null = null;
  private readonly listeners: [EventTarget, string, (e: any) => void, any?][] = [];

  constructor(
    private readonly camera: OrbitCamera,
    canvas: HTMLCanvasElement,
    // the pointer belongs to something else (a gizmo, a selection box)
    private readonly blocked: () => boolean,
  ) {
    this.listen(canvas, 'pointerdown', (e: PointerEvent) => {
      const orbitButton = e.button === 2 || e.button === 1 || (e.button === 0 && e.altKey);
      this.dragFrom = orbitButton && this.active && !this.blocked() ? { x: e.clientX, y: e.clientY } : null;
      if (this.dragFrom && e.button === 1) {
        // no middle button auto scroll
        e.preventDefault();
      }
    });
    // the middle button pressed on the canvas does not start auto scroll in browsers listening to mousedown only
    this.listen(canvas, 'mousedown', (e: MouseEvent) => e.button === 1 && this.active && e.preventDefault());
    this.listen(window, 'pointermove', (e: PointerEvent) => this.onPointerMove(e));
    this.listen(window, 'pointerup', () => (this.dragFrom = null));
    this.listen(canvas, 'wheel', (e: WheelEvent) => this.onWheel(e), { passive: false });
  }

  private get active(): boolean {
    return this.enabled && !!this.pivot;
  }

  // Looks at the pivot from the side the camera is on, `distance` away
  frame(distance: number) {
    if (!this.pivot) {
      return;
    }
    const eye = this.cameraPosition();
    const direction = eye.clone().sub(this.pivot);
    if (direction.lengthSq() < 1e-6) {
      direction.set(0, -1, 0.3);
    }
    eye.copy(this.pivot).addScaledVector(direction.normalize(), distance);
    this.camera.position = { x: eye.x, y: eye.y, z: eye.z };
    this.camera.rotation = Qtrn.lookAt(this.camera.position, this.pivot, UP);
  }

  dispose() {
    for (const [target, type, listener, options] of this.listeners) {
      target.removeEventListener(type, listener, options);
    }
  }

  private listen(target: EventTarget, type: string, listener: (e: any) => void, options?: any) {
    target.addEventListener(type, listener, options);
    this.listeners.push([target, type, listener, options]);
  }

  private cameraPosition(): Vector3 {
    const p = this.camera.position;
    return new Vector3(p.x, p.y, p.z);
  }

  private onPointerMove(e: PointerEvent) {
    if (!this.dragFrom) {
      return;
    }
    if (!this.active || this.blocked()) {
      this.dragFrom = null;
      return;
    }
    const dx = e.clientX - this.dragFrom.x;
    const dy = e.clientY - this.dragFrom.y;
    this.dragFrom = { x: e.clientX, y: e.clientY };
    this.turn(-dx * TURN_PER_PIXEL, -dy * TURN_PER_PIXEL);
  }

  // Turns the camera around the pivot: `yaw` around the vertical axis, `pitch` around the camera's horizontal one
  private turn(yaw: number, pitch: number) {
    const r = this.camera.rotation;
    const rotation = new Quaternion(r.x, r.y, r.z, r.w);
    const right = new Vector3(1, 0, 0).applyQuaternion(rotation);
    const yawTurn = new Quaternion().setFromAxisAngle(UP, yaw);
    let turn = yawTurn.clone().multiply(new Quaternion().setFromAxisAngle(right, pitch));
    const forward = new Vector3(0, 0, -1).applyQuaternion(turn.clone().multiply(rotation));
    if (Math.abs(forward.z) > MAX_PITCH_Z) {
      turn = yawTurn;
    }
    const eye = this.cameraPosition().sub(this.pivot!).applyQuaternion(turn).add(this.pivot!);
    const newRotation = turn.multiply(rotation);
    this.camera.position = { x: eye.x, y: eye.y, z: eye.z };
    this.camera.rotation = { x: newRotation.x, y: newRotation.y, z: newRotation.z, w: newRotation.w };
  }

  private onWheel(e: WheelEvent) {
    if (!this.active || (e.deltaX === 0 && e.deltaY === 0)) {
      return;
    }
    e.preventDefault();
    if (e.ctrlKey) {
      // a touchpad pinch (or Ctrl + wheel)
      this.zoom(Math.exp(e.deltaY * PINCH_ZOOM_PER_PIXEL));
    } else if (isTouchpadScroll(e)) {
      // a two finger swipe turns the view like a drag of it would
      this.turn(e.deltaX * TURN_PER_PIXEL, e.deltaY * TURN_PER_PIXEL);
    } else if (e.deltaY !== 0) {
      this.zoom(e.deltaY > 0 ? WHEEL_FACTOR : 1 / WHEEL_FACTOR);
    }
  }

  // Multiplies the distance to the pivot
  private zoom(factor: number) {
    const offset = this.cameraPosition().sub(this.pivot!);
    if (offset.length() * factor < MIN_DISTANCE && factor < 1) {
      return;
    }
    const eye = offset.multiplyScalar(factor).add(this.pivot!);
    this.camera.position = { x: eye.x, y: eye.y, z: eye.z };
  }
}
