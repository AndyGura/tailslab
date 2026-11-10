import { nfs6Route } from './nfs6-route';
import { NFS6_TRACK_ADAPTER } from './track-map-adapters';

function path(pathType: number, ...xz: [number, number][]) {
  return { path_type: pathType, points: xz.map(([x, z]) => ({ position: { x, y: 0, z } })) };
}

// A square loop of main road paths (type 1), a shortcut across it (type 3), a dead end branch (type 11) and the
// helicopter's flight path
function aiPaths() {
  return {
    road_paths: {
      paths: [
        path(1, [0, 0], [50, 0], [100, 0]),
        path(1, [100, 0], [100, 50], [100, 100]),
        path(3, [100, 0], [50, 50], [0, 100]),
        path(1, [100, 100], [50, 100], [0, 100]),
        path(1, [0, 100], [0, 50], [0, 0]),
        path(11, [0, 100], [-30, 130]),
        path(2, [500, 500]),
      ],
    },
    helicopter_paths: { paths: [path(1, [0, 0], [100, 100])] },
  };
}

describe('nfs6Route', () => {
  it('takes the loop of main road paths as the race route', () => {
    const route = nfs6Route(aiPaths());
    expect(route.closed).toBeTrue();
    expect(route.points.length).toBe(8);
  });

  it('gives the road paths the route does not use as other roads', () => {
    const route = nfs6Route(aiPaths());
    expect(route.roads).toEqual([
      {
        points: [
          { x: 100, y: 0, z: 0 },
          { x: 50, y: 0, z: 50 },
          { x: 0, y: 0, z: 100 },
        ],
        closed: false,
      },
      {
        points: [
          { x: 0, y: 0, z: 100 },
          { x: -30, y: 0, z: 130 },
        ],
        closed: false,
      },
    ]);
  });

  it('is used by the NFS6 track adapter', () => {
    const data = aiPaths();
    expect(NFS6_TRACK_ADAPTER.roads!(data)).toBe(nfs6Route(data).roads);
  });
});
