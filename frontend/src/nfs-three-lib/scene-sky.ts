import { proceduralSkyBodies, ProceduralSky3dOpts } from '@gg-web-engine/core';
import { Matrix3, Matrix4, Scene, Texture } from 'three';

/**
 * The sun of a scene's sky, for car shaders lit by the scene instead of the game's lights: unit direction towards it
 * in the world (z up), color 0..1 (display values, times its intensity)
 */
export type SceneSun = { direction: [number, number, number]; color: [number, number, number] };

/** The sun of a gg-web-engine procedural sky (proceduralSkyBodies) */
export const proceduralSkySun = (sky: ProceduralSky3dOpts): SceneSun => {
  const { sunDirection, sunLight } = proceduralSkyBodies(sky);
  const c = sunLight.color;
  return {
    direction: [sunDirection.x, sunDirection.y, sunDirection.z],
    color: [(c >> 16) & 0xff, (c >> 8) & 0xff, c & 0xff].map(x => (x / 255) * sunLight.intensity) as [
      number,
      number,
      number,
    ],
  };
};

// three.js WebGLBackground: a cube texture of images (not a render target) is mirrored in x
const CUBE_FLIP = new Matrix3().set(-1, 0, 0, 0, 1, 0, 0, 0, 1);

/**
 * The sky of `scene`: `scene.background` when it is a cube texture, else null. Sets `matrix` to turn a world direction
 * into the direction to look up in it, as three.js turns it as the background (WebGLBackground)
 */
export const sceneSkyCube = (scene: Scene | null | undefined, matrix: Matrix3): Texture | null => {
  const background = scene?.background as Texture | null | undefined;
  const sky = background && (background as any).isCubeTexture ? background : null;
  if (sky && scene) {
    matrix.setFromMatrix4(new Matrix4().makeRotationFromEuler(scene.backgroundRotation)).transpose();
    if (!(sky as any).isRenderTargetTexture) {
      matrix.premultiply(CUBE_FLIP);
    }
  }
  return sky;
};

/**
 * GLSL (vertex shader): `sceneSkyMean( cube, matrix, side )`, the mean color of the sky cube above (side 1.0) or
 * below (side -1.0) the horizon (world z up), in display values 0..1: cosine-weighted samples of 3 rings of 8
 * directions (15, 45 and 75 degrees from the horizon), averaged in linear values. The game's hemisphere ambient
 * (sky and ground colors) of a scene
 */
export const SCENE_SKY_MEAN_GLSL = `
vec3 sceneSkyMean( samplerCube cube, mat3 matrix, float side ) {
  vec3 sum = vec3( 0.0 );
  float weight = 0.0;
  for ( int i = 0; i < 3; i++ ) {
    float e = ( float( i ) + 0.5 ) * 0.5235988;
    for ( int j = 0; j < 8; j++ ) {
      float a = float( j ) * 0.7853982;
      vec3 d = vec3( cos( e ) * cos( a ), cos( e ) * sin( a ), side * sin( e ) );
      sum += textureLod( cube, matrix * d, 0.0 ).rgb * sin( e );
      weight += sin( e );
    }
  }
  vec3 c = clamp( sum / weight, 0.0, 1.0 );
  return mix( c * 12.92, pow( c, vec3( 1.0 / 2.4 ) ) * 1.055 - 0.055, step( 0.0031308, c ) );
}`;
