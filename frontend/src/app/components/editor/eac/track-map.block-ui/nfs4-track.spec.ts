import { nfs4Roads, nfs4SplinePoints } from './nfs4-track';
import { NFS4_TRACK_ADAPTER } from './track-map-adapters';

// A straight road of 12 slices along +z, 10 apart. Slices 2..4 open on the right onto 10..8 (a shortcut whose ends
// link each other), slices 6..7 on the left onto 11..10 (one end only)
function frd() {
  const vroad = Array.from({ length: 12 }, (_, i) => ({
    ref_point: { x: 0, y: 1, z: i * 10 },
    forward: { x: 0, y: 0, z: 1 },
    left_link: -1,
    right_link: -1,
  }));
  [
    [2, 10],
    [3, 9],
    [4, 8],
  ].forEach(([a, b]) => {
    vroad[a].right_link = b;
    vroad[b].right_link = a;
  });
  vroad[6].left_link = 11;
  vroad[7].left_link = 10;
  return { vroad, blocks_headers: [{ position: { x: 0, y: 0, z: 35 } }, { position: { x: 0, y: 0, z: 95 } }] };
}

describe('NFS4 track', () => {
  it('takes the vroad slice centres in meters as the road spline', () => {
    const points = nfs4SplinePoints(frd());
    expect(points.length).toBe(12);
    expect(points[3].position.z).toBeCloseTo(39);
    expect(points[3].position.y).toBeCloseTo(1.3);
    expect(points[3].orientation).toBe(0);
  });

  it('draws a road from the middle of each linked run of slices to its link, mirrored runs once', () => {
    const roads = nfs4Roads(frd());
    expect(roads.length).toBe(2);
    expect(roads[0].closed).toBeFalse();
    expect(roads[0].points.map(p => Math.round(p.z))).toEqual([39, 117]);
    expect(roads[1].points.map(p => Math.round(p.z))).toEqual([91, 130]);
  });

  it('is used by the NFS4 track adapter', () => {
    const data = frd();
    expect(NFS4_TRACK_ADAPTER.splinePoints!(data).length).toBe(12);
    expect(NFS4_TRACK_ADAPTER.roads!(data).length).toBe(2);
    expect(NFS4_TRACK_ADAPTER.chunkPositions!(data).length).toBe(2);
  });
});
