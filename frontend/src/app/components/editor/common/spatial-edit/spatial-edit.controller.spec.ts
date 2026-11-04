import { PerspectiveCamera, Quaternion, Scene, Vector3 } from 'three';
import { SpatialEditController, SpatialEditHost, SpatialMove } from './spatial-edit.controller';
import { SpatialEditKind, SpatialHandle } from './spatial-edit.types';

const PROP_KIND: SpatialEditKind = { kind: 'prop', title: 'Props', translate_axes: 'xyz', rotate_axes: 'z' };
const VERTEX_KIND: SpatialEditKind = {
  kind: 'terrain_vertex',
  title: 'Terrain',
  translate_axes: 'xyz',
  rotate_axes: '',
};

function handle(id: string, position: [number, number, number]): SpatialHandle {
  return { id, chunk: 0, position, rotation: [0, 0, 0, 1], label: `Handle ${id}` };
}

describe('SpatialEditController', () => {
  let canvas: HTMLCanvasElement;
  let commits: SpatialMove[][];
  let previewed: SpatialMove[][];
  let controller: SpatialEditController;

  beforeEach(() => {
    const container = document.createElement('div');
    canvas = document.createElement('canvas');
    container.appendChild(canvas);
    document.body.appendChild(container);
    commits = [];
    previewed = [];
    const host: SpatialEditHost = {
      preview: moves => previewed.push(moves),
      // the file keeps positions on a 1/8 grid
      commit: async moves => {
        commits.push(moves);
        return moves.map(m => ({
          ...m.handle,
          position: m.position.toArray().map(v => Math.round(v * 8) / 8) as [number, number, number],
          rotation: m.rotation ? (m.rotation.toArray() as [number, number, number, number]) : m.handle.rotation,
        }));
      },
    };
    controller = new SpatialEditController(new Scene(), new PerspectiveCamera(), canvas, host);
  });

  afterEach(() => {
    controller.dispose();
    canvas.parentElement!.remove();
  });

  it('should take the transform the data holds after a move', async () => {
    controller.setKind(PROP_KIND);
    controller.setHandles([handle('1', [0, 0, 0])]);
    controller.selectById('1');
    await controller.moveSelection(new Vector3(1.01, 2, 3), new Quaternion());
    expect(commits.length).toBe(1);
    expect(controller.selection$.value[0].position).toEqual([1, 2, 3]);
    expect(controller.snap$.value!.distance).toBeCloseTo(0.01, 5);
    // the preview ends where the data is
    expect(previewed[previewed.length - 1][0].position.toArray()).toEqual([1, 2, 3]);
  });

  it('should not commit a move to the same place', async () => {
    controller.setKind(PROP_KIND);
    controller.setHandles([handle('1', [1, 2, 3])]);
    controller.selectById('1');
    await controller.moveSelection(new Vector3(1, 2, 3), new Quaternion());
    expect(commits.length).toBe(0);
    expect(controller.snap$.value).toBeNull();
  });

  it('should send no rotation for a kind without rotate axes and refuse the rotate gizmo', async () => {
    controller.setKind(VERTEX_KIND);
    controller.setGizmoMode('rotate');
    expect(controller.gizmoMode$.value).toBe('translate');
    controller.setHandles([handle('1', [0, 0, 0])]);
    controller.selectById('1');
    await controller.moveSelection(new Vector3(0.5, 0, 0), null);
    expect(commits[0][0].rotation).toBeNull();
  });

  it('should keep the selection across new handles of the same id', () => {
    controller.setKind(PROP_KIND);
    controller.setHandles([handle('1', [0, 0, 0]), handle('2', [5, 0, 0])]);
    controller.selectById('2');
    controller.setHandles([handle('2', [6, 0, 0])]);
    expect(controller.selection$.value[0].position).toEqual([6, 0, 0]);
    controller.setKind(VERTEX_KIND);
    expect(controller.selection$.value).toEqual([]);
  });

  it('should move every selected handle by as much as the centre, in one commit', async () => {
    controller.setKind(VERTEX_KIND);
    controller.setHandles([handle('1', [0, 0, 0]), handle('2', [4, 0, 2]), handle('3', [9, 9, 9])]);
    controller.selectById('1', '2');
    expect(controller.pivotPosition.toArray()).toEqual([2, 0, 1]);
    await controller.moveSelection(new Vector3(3, 1, 1), null);
    expect(commits.length).toBe(1);
    expect(commits[0].map(m => [m.handle.id, m.position.toArray()])).toEqual([
      ['1', [1, 1, 0]],
      ['2', [5, 1, 2]],
    ]);
    expect(controller.selection$.value.map(h => h.position)).toEqual([
      [1, 1, 0],
      [5, 1, 2],
    ]);
  });

  it('should turn a selection around its centre', async () => {
    controller.setKind(PROP_KIND);
    controller.setHandles([handle('1', [-1, 0, 0]), handle('2', [1, 0, 0])]);
    controller.selectById('1', '2');
    // the gizmo of several handles is not turned: a typed rotation is for one handle only
    await controller.moveSelection(new Vector3(0, 0, 0), new Quaternion(0, 0, 1, 0));
    expect(commits.length).toBe(0);
    (controller as any).startMove();
    (controller as any).pivot.quaternion.setFromAxisAngle(new Vector3(0, 0, 1), Math.PI / 2);
    const moves: SpatialMove[] = (controller as any).selectionMoves();
    expect(moves[0].position.x).toBeCloseTo(0, 6);
    expect(moves[0].position.y).toBeCloseTo(-1, 6);
    expect(moves[1].position.y).toBeCloseTo(1, 6);
    // each one turns with it
    expect(
      moves[0].rotation!.angleTo(new Quaternion().setFromAxisAngle(new Vector3(0, 0, 1), Math.PI / 2)),
    ).toBeCloseTo(0, 6);
  });

  it('should add and remove handles of the selection', () => {
    controller.setKind(VERTEX_KIND);
    const [a, b] = [handle('1', [0, 0, 0]), handle('2', [2, 0, 0])];
    controller.setHandles([a, b]);
    controller.toggle(a);
    controller.toggle(b);
    expect(controller.selection$.value.map(h => h.id)).toEqual(['1', '2']);
    controller.toggle(a);
    expect(controller.selection$.value.map(h => h.id)).toEqual(['2']);
    expect(controller.pivotPosition.toArray()).toEqual([2, 0, 0]);
  });

  // a pointer gesture on the canvas, in its pixels (the camera looks along -z from the origin)
  function gesture(from: [number, number], to: [number, number], keys: PointerEventInit = {}) {
    const rect = canvas.getBoundingClientRect();
    const at = ([x, y]: [number, number]) => ({ clientX: rect.left + x, clientY: rect.top + y });
    const event = (type: string, p: [number, number]) =>
      canvas.dispatchEvent(
        new PointerEvent(type, { button: 0, bubbles: true, pointerId: 1, pointerType: 'mouse', ...keys, ...at(p) }),
      );
    event('pointerdown', from);
    event('pointermove', to);
    event('pointerup', to);
  }

  function screenX(handleX: number): number {
    const v = new Vector3(handleX, 0, -10).project(camera);
    return ((v.x + 1) / 2) * canvas.getBoundingClientRect().width;
  }

  let camera: PerspectiveCamera;

  function boxSetup() {
    camera = (controller as any).camera;
    camera.updateMatrixWorld();
    controller.setKind(VERTEX_KIND);
    controller.setHandles([handle('a', [-1, 0, -10]), handle('b', [1, 0, -10]), handle('c', [3, 0, -10])]);
  }

  it('should select in a box with a plain drag, add with Shift and remove with Ctrl', () => {
    boxSetup();
    const height = canvas.getBoundingClientRect().height;
    const ids = () => controller.selection$.value.map(h => h.id);
    // a and b
    gesture([screenX(-1) - 5, 5], [screenX(1) + 5, height - 5]);
    expect(ids()).toEqual(['a', 'b']);
    // a plain box replaces: c only
    gesture([screenX(3) - 5, 5], [screenX(3) + 5, height - 5]);
    expect(ids()).toEqual(['c']);
    // Shift adds a and b
    gesture([screenX(-1) - 5, 5], [screenX(1) + 5, height - 5], { shiftKey: true });
    expect(ids()).toEqual(['c', 'a', 'b']);
    // Ctrl removes b and c
    gesture([screenX(1) - 5, 5], [screenX(3) + 5, height - 5], { ctrlKey: true });
    expect(ids()).toEqual(['a']);
    // Alt + drag is the camera's
    gesture([screenX(-1) - 5, 5], [screenX(3) + 5, height - 5], { altKey: true });
    expect(ids()).toEqual(['a']);
  });

  it('should add and remove with Shift / Ctrl clicks', () => {
    boxSetup();
    const y = canvas.getBoundingClientRect().height / 2;
    const ids = () => controller.selection$.value.map(h => h.id);
    gesture([screenX(-1), y], [screenX(-1), y]);
    gesture([screenX(1), y], [screenX(1), y], { shiftKey: true });
    expect(ids()).toEqual(['a', 'b']);
    gesture([screenX(-1), y], [screenX(-1), y], { ctrlKey: true });
    expect(ids()).toEqual(['b']);
    // a click on empty space deselects
    gesture([2, 2], [2, 2]);
    expect(ids()).toEqual([]);
  });

  it('should move the selection to its centre in one commit', async () => {
    controller.setKind({ ...VERTEX_KIND, translate_axes: 'xy' });
    controller.setHandles([handle('1', [0, 0, 5]), handle('2', [4, 2, 1]), handle('3', [8, 4, 0])]);
    controller.selectById('1', '2', '3');
    await controller.moveSelectionToCentre();
    expect(commits.length).toBe(1);
    // z is not an axis of the kind: it stays
    expect(commits[0].map(m => m.position.toArray())).toEqual([
      [4, 2, 5],
      [4, 2, 1],
      [4, 2, 0],
    ]);
  });
});
