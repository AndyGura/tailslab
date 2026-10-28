import { ProceduralSky3dOpts } from '@gg-web-engine/core';
import { ThreeGgWorld } from '@gg-web-engine/three';

// Background and environment light of the 3D viewers: a still afternoon sky with a few clouds, drawn once into a
// cube texture (no drifting clouds). A track's own sky (the skybox sphere of the track viewer) is drawn over it
export const VIEWER_SKY: ProceduralSky3dOpts = {
  type: 'PROCEDURAL',
  mode: 'BAKED',
  bakeResolution: 1024,
  timeOfDay: 15,
  sunAzimuth: Math.PI / 4,
  haze: 0.15,
  clouds: { coverage: 0.35, density: 0.75, scale: 1.2 },
  cirrus: { coverage: 0.25, density: 0.4 },
  stars: 0,
  groundColor: 0x77726a,
};

export function setViewerSky(world: ThreeGgWorld) {
  world.visualScene.setEnvironment({ background: VIEWER_SKY, environmentMap: VIEWER_SKY });
}
