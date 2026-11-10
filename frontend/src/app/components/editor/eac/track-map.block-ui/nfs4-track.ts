import { Point3 } from '@gg-web-engine/core';
import { BlockData } from '../../types';
import type { TrackRoad, TrackSplinePoint } from './track-map-adapters';

// NFS4 tracks are 1 / 1.3 of their real size in the files: the converter exports them in meters, every position
// times this (`NFS4_TRACK_SCALE` of serializers/maps.py)
export const NFS4_TRACK_SCALE = 1.3;

function scaled(p: Point3): Point3 {
  return { x: p.x * NFS4_TRACK_SCALE, y: p.y * NFS4_TRACK_SCALE, z: p.z * NFS4_TRACK_SCALE };
}

// The road centre line of an NFS4 FRD track: the slice centres of its virtual road (`vroad` records, 8 per block),
// headed along their forward vector
export function nfs4SplinePoints(data: BlockData): TrackSplinePoint[] {
  return (data['vroad'] || []).map((v: any) => ({
    position: scaled(v.ref_point),
    orientation: Math.atan2(v.forward.x, v.forward.z),
  }));
}

// Shortcuts and cut-throughs of an NFS4 FRD track: a vroad record's `left_link` / `right_link` is the slice across
// its open side, where the other end of the shortcut joins the road (or the other part of a hairpin running side by
// side). A run of consecutive slices links a run of consecutive ones and both ends link each other: one straight road
// from the middle slice of each run to its link, mirrored runs once
export function nfs4Roads(data: BlockData): TrackRoad[] {
  const vroad: any[] = data['vroad'] || [];
  const runs: [number, number][][] = [];
  for (const field of ['right_link', 'left_link']) {
    let run: [number, number][] | null = null;
    vroad.forEach((v, i) => {
      const link = v[field];
      if (link === undefined || link < 0 || link >= vroad.length) {
        run = null;
        return;
      }
      const last: [number, number] | undefined = run ? run[run.length - 1] : undefined;
      if (run && last && last[0] === i - 1 && Math.abs(last[1] - link) === 1) {
        run.push([i, link]);
      } else {
        run = [[i, link]];
        runs.push(run);
      }
    });
  }
  const seen = new Set<string>();
  const roads: TrackRoad[] = [];
  for (const run of runs) {
    if (run.some(([slice, link]) => seen.has(`${link},${slice}`))) {
      continue;
    }
    run.forEach(([slice, link]) => seen.add(`${slice},${link}`));
    const [slice, link] = run[Math.floor(run.length / 2)];
    roads.push({ points: [scaled(vroad[slice].ref_point), scaled(vroad[link].ref_point)], closed: false });
  }
  return roads;
}
