import {
  AdditiveBlending,
  BufferGeometry,
  Material,
  Matrix3,
  Mesh,
  MeshBasicMaterial,
  NormalBlending,
  Object3D,
  RepeatWrapping,
  Scene,
  SRGBColorSpace,
  Texture,
  TextureLoader,
  Vector2,
  Vector3,
  Vector4,
} from 'three';
import { SCENE_SKY_MEAN_GLSL, SceneSun, sceneSkyCube } from './scene-sky';

/** A paint of the car: "skins.json" of the TailsLab export */
export type Nfs6Ps2CarSkin = {
  name: string;
  label: string;
  texture: string;
  texture_b?: string;
  // the game's paint name, e.g. "Guards Red"
  paint_name?: string;
  // the lighting material of the paint, for the objects with lighting material "CARSKIN"
  lighting_material?: string;
};

/** GS settings of a material's texture ("textures" of car.json) */
export type Nfs6Ps2TextureSettings = {
  // GS ALPHA A, B, C, D: 0x0a opaque, 0x44 alpha blended, 0x48 added by alpha
  alpha_blend: number;
  // the lit vertex colours shade the environment map pass (car paints)
  vertex_lit_env: boolean;
  // texels with alpha below 0x30 (texture alpha * vertex alpha / 0x80) are not drawn
  alpha_test: boolean;
  repeat: [boolean, boolean];
};

/** "car.json" of the TailsLab export: wheels (X right, Y forward, Z up) and light textures by state, lighting */
export type Nfs6Ps2CarInfo = {
  model: string;
  car_type: string | null;
  wheels: { name: string; position: [number, number, number]; radius: number }[];
  lights: { [light: string]: { off?: string; on?: string; damaged?: string } };
  textures?: { [material: string]: Nfs6Ps2TextureSettings };
  // lighting of every object: its lighting material ("CARSKIN": the paint's) and VU1 flags (0x80 lit, 0x100 env)
  meshes?: { [name: string]: { lighting_material: string | null; vu_flags: number } };
  // the 4 VU1 vectors (16 floats) of every lighting material, front end and race sets
  lighting_materials?: { [name: string]: { frontend: number[]; race: number[] } };
};

/**
 * The 3 directional lights and the ambient colour of the VU1 lighting (SLUS_203.62 0x115978 builds them into the VU1
 * light context, 18 vectors at VU address 0x35c): colours 0..255, directions towards the lights (normalized by the
 * shader), alpha of the ambient colour 128. Directions in "camera" space are PS2 camera axes (x right, y down, z
 * forward: inferred, the game turns them by the inverse of the view matrix), in "world" space TailsLab's export axes
 * (X right, Y forward, Z up)
 */
export type Nfs6Ps2Lighting = {
  space: 'camera' | 'world';
  directions: [number, number, number][];
  colors: [number, number, number][];
  ambient: [number, number, number];
};

/**
 * The car showroom of the front end (game state GAMEFLOW_STATE_IN_FRONTEND with front end cars, 0x115978): the light
 * colours and camera space directions of SLUS_203.62 0x1157c0 (data of Lighting_InitDefaults 0x117098: colours 0x3328c0,
 * 0x3328b0, 0x3328a0 plus a brightness of 0, directions 0x332840, 0x332830, 0x332820, ambient 0x332890)
 */
export const NFS6_PS2_FRONTEND_LIGHTING: Nfs6Ps2Lighting = {
  space: 'camera',
  directions: [
    [6.82, -6.1, -8.56],
    [-5, -1, 0],
    [1.28, -1.17, 1.28],
  ],
  colors: [
    [80, 80, 80],
    [64, 64, 64],
    [128, 128, 180],
  ],
  ambient: [32, 32, 32],
};

const f32 = new Float32Array(1);
const i32 = new Int32Array(f32.buffer);

/** IEEE single bit pattern of a float, as a signed integer */
export const nfs6Ps2FloatBits = (x: number): number => {
  f32[0] = x;
  return i32[0];
};

/** The float of an IEEE single bit pattern */
export const nfs6Ps2BitsFloat = (bits: number): number => {
  i32[0] = bits;
  return f32[0];
};

/**
 * The VU1 power of .vutext 0x2c4 / 0x333 / 0x42b with float bit patterns: itof0 of the bits of x, times n plus bias,
 * ftoi0 (truncated) back to bits. With bias = float(bits(s)) - n * float(bits(1.0)) it is about s * x ^ n
 */
export const nfs6Ps2Pow = (x: number, n: number, bias: number): number =>
  nfs6Ps2BitsFloat(Math.trunc(Math.fround(Math.fround(Math.fround(nfs6Ps2FloatBits(x)) * n) + bias)));

/** Exponent and bias of nfs6Ps2Pow for s * x ^ n, float32 math of SLUS_203.62 0x116828 */
export const nfs6Ps2PowParams = (n: number, s: number): [number, number] => {
  n = Math.fround(n);
  return [n, Math.fround(Math.fround(nfs6Ps2FloatBits(Math.fround(s))) - Math.fround(n * 1065353216))];
};

/**
 * The reflection vector normalization of .vutext 0x2c4 and 0x42b: nfs6Ps2Pow of the squared length with the VU1
 * vector 0x29c that SLUS_203.62 0x10ac50 uploads, -0.5 and 0.9405 (0x32f750..0x32f75c): 0.94 / length
 */
export const NFS6_PS2_RSQRT = nfs6Ps2PowParams(-0.5, nfs6Ps2BitsFloat(0x3f70c49c));

/**
 * The colour of a lit vertex, 0..255 RGBA integers as the VU1 lighting (.vutext 0x333, `vu_flags` 0x80) writes it:
 * ambient (alpha 128) + per light colour * (diffuse * max(N.L, 0) + specular * pow(max(R.L, q0.z))), RGB times
 * 1 + (vertex colour - 255) * q0.w, clamped to 0..255, truncated. N the game normal (/ 127, not normalized), L unit
 * directions to the lights, R the reflected camera ray (nfs6Ps2Reflect). `q` the 4 VU1 vectors of the lighting
 * material: q0 (exponent, bias, least R.L, vertex colour weight), q1 diffuse, q2 specular, q3 the paint's exponent,
 * bias, alpha and alpha per specular. `paint` (texture `vertex_lit_env`, VU1 flag 4, 0x34b): every specular takes q3's
 * exponent and the alpha is q3.z + q3.w * specular of light 0
 */
export const nfs6Ps2VertexLight = (
  normal: Vector3,
  reflect: Vector3,
  color: [number, number, number],
  q: number[],
  lights: { directions: Vector3[]; colors: [number, number, number][]; ambient: [number, number, number] },
  paint: boolean,
): [number, number, number, number] => {
  const [n, bias] = paint ? [q[12], q[13]] : [q[0], q[1]];
  const rgb = [...lights.ambient];
  let alpha = paint ? q[14] : 128;
  const speculars = lights.directions.map(l => nfs6Ps2Pow(Math.max(reflect.dot(l), q[2]), n, bias));
  lights.directions.forEach((l, i) => {
    const d = Math.max(normal.dot(l), 0);
    for (let c = 0; c < 3; c++) {
      rgb[c] += lights.colors[i][c] * q[4 + c] * d;
    }
  });
  lights.directions.forEach((_, i) => {
    for (let c = 0; c < 3; c++) {
      rgb[c] += lights.colors[i][c] * q[8 + c] * speculars[i];
    }
  });
  if (paint) {
    alpha += q[15] * speculars[0];
  }
  const clamp = (v: number) => Math.trunc(Math.max(0, Math.min(255, v)));
  return [...rgb.map((v, c) => clamp(v * (1 + (color[c] - 255) * q[3]))), clamp(alpha)] as [
    number,
    number,
    number,
    number,
  ];
};

/**
 * .vutext 0x2c4: the camera ray to the vertex (vertex - eye) reflected by the game normal (not normalized, as the
 * VU1: 2 * N.V), times NFS6_PS2_RSQRT of its squared length
 */
export const nfs6Ps2Reflect = (normal: Vector3, eyeToVertex: Vector3): Vector3 => {
  const r = eyeToVertex.clone().addScaledVector(normal, -2 * normal.dot(eyeToVertex));
  return r.multiplyScalar(nfs6Ps2Pow(Math.fround(r.lengthSq()), ...NFS6_PS2_RSQRT));
};

/**
 * The vertex alpha of the environment map pass (.vutext 0x42b): q1.w + q2.w * the z of the reflection in the
 * environment map view (R'z = -R.forward: 1 where the reflection comes back towards the camera), truncated, the low
 * byte as the GS takes it
 */
export const nfs6Ps2EnvAlpha = (reflectZ: number, q: number[]): number =>
  Math.trunc(Math.fround(q[7] + Math.fround(q[11] * reflectZ))) & 0xff;

/** The GS MODULATE texture function of a channel: texture * vertex / 128, truncated, at most 255 */
export const nfs6Ps2Modulate = (texel: number, vertex: number): number => Math.min(255, (texel * vertex) >> 7);

/** Uniforms of the car shading, shared by its materials */
class LightingUniforms {
  readonly directions = { value: [new Vector3(), new Vector3(), new Vector3()] };
  readonly colors = { value: [new Vector3(), new Vector3(), new Vector3()] };
  readonly ambient = { value: new Vector4() };
  // 1: the directions are PS2 camera axes
  readonly cameraSpace = { value: 1 };
  readonly cube = { value: null as Texture | null };
  readonly cubeMatrix = { value: new Matrix3() };
  // 0 no environment pass, 1 front end (vertex alpha), 2 race (paints by the destination alpha)
  readonly envMode = { value: 1 };
  // 1: the ambient is the scene's sky (sceneSkyMean), light 0 its sun
  readonly sceneLight = { value: 0 };
}

/** Per material uniforms of the car shading */
class MaterialUniforms {
  // the 4 VU1 vectors of the lighting material
  readonly vectors = { value: [new Vector4(), new Vector4(), new Vector4(), new Vector4()] };
  readonly lit = { value: 0 };
  readonly env = { value: 0 };
  readonly paint = { value: 0 };
  readonly alphaTest = { value: 1 };
  readonly blend = { value: 0x0a };
  readonly repeat = { value: new Vector2() };
}

/**
 * The game's shading of the car in the shader of a material, replacing three.js' lighting (the material's own lights,
 * tone mapping and alpha test are not used):
 * - vertex shader: the VU1 microprogram's vertex colour (nfs6Ps2VertexLight from the game normal `_game_normal`,
 *   else `normal`, and the raw vertex colour, for `vu_flags` 0x80; else the vertex colour as it is), the reflected
 *   camera ray and the environment pass colour and alpha (nfs6Ps2EnvAlpha; 128 grey, the lit colour for a paint);
 * - fragment shader, GS math on 0..255 values: the stored texel (bilinear from texelFetch, the PNG holds the texture as
 *   stored, alpha doubled) times the vertex colour (nfs6Ps2Modulate), the alpha test, the environment pass added
 *   (environment texel * its vertex colour / 128 * alpha / 128; race paints by the main pass alpha), the result in the
 *   output colour space.
 * Lit by the scene (Nfs6Ps2CarMeshController.sceneLighting): the ambient is the scene's sky above and below the
 * horizon by the normal's height (sceneSkyMean, like the PC game's hemisphere ambient), light 0 the scene's sun.
 * SKIPPED: the GS interpolates vertex colours in screen space (no perspective), mipmaps, the environment map is the
 * scene's sky in the reflected direction instead of the game's run time sphere map of the surroundings (rendered
 * views of the car's position, SLUS_203.62 0x1175c8, alpha assumed 0x80), the environment pass over texels the alpha
 * test discards, GS alpha weights above 1
 */
function ps2ShadingInShader(
  material: Material,
  lighting: LightingUniforms,
  uniforms: MaterialUniforms,
  gameNormals: boolean,
  srgbVertexColors: boolean,
) {
  const previous = material.onBeforeCompile;
  const previousKey = material.customProgramCacheKey;
  material.onBeforeCompile = (shader, renderer) => {
    previous.call(material, shader, renderer);
    Object.assign(shader.uniforms, {
      ps2LightDirections: lighting.directions,
      ps2LightColors: lighting.colors,
      ps2Ambient: lighting.ambient,
      ps2CameraSpace: lighting.cameraSpace,
      ps2Cube: lighting.cube,
      ps2CubeMatrix: lighting.cubeMatrix,
      ps2EnvMode: lighting.envMode,
      ps2SceneLight: lighting.sceneLight,
      ps2Vectors: uniforms.vectors,
      ps2Lit: uniforms.lit,
      ps2Env: uniforms.env,
      ps2Paint: uniforms.paint,
      ps2AlphaTest: uniforms.alphaTest,
      ps2Blend: uniforms.blend,
      ps2Repeat: uniforms.repeat,
    });
    shader.uniforms['ps2MapSrgb'] = {
      get value() {
        return (material as MeshBasicMaterial).map?.colorSpace === SRGBColorSpace ? 1 : 0;
      },
    };
    shader.vertexShader = shader.vertexShader
      .replace(
        '#include <fog_pars_vertex>',
        `#include <fog_pars_vertex>
        ${gameNormals ? 'attribute vec3 _game_normal;' : ''}
        uniform vec3 ps2LightDirections[ 3 ];
        uniform vec3 ps2LightColors[ 3 ];
        uniform vec4 ps2Ambient;
        uniform float ps2CameraSpace;
        uniform vec4 ps2Vectors[ 4 ];
        uniform float ps2Lit;
        uniform float ps2Paint;
        uniform float ps2EnvMode;
        uniform float ps2Env;
        uniform float ps2SceneLight;
        uniform samplerCube ps2Cube;
        uniform mat3 ps2CubeMatrix;
        varying vec4 vPs2Color;
        varying vec4 vPs2EnvColor;
        varying vec3 vPs2Reflect;
        ${SCENE_SKY_MEAN_GLSL}
        // nfs6Ps2Pow
        float ps2Pow( float x, vec2 q ) {
          return intBitsToFloat( int( float( floatBitsToInt( x ) ) * q.x + q.y ) );
        }`,
      )
      .replace(
        '#include <fog_vertex>',
        `#include <fog_vertex>
        {
          vec3 n = ${gameNormals ? '_game_normal' : 'normal'};
          vec3 ps2N = length( n ) > 0.0 ? normalize( mat3( modelMatrix ) * n ) * length( n ) : vec3( 0.0 );
          vec3 ps2V = ( modelMatrix * vec4( transformed, 1.0 ) ).xyz - cameraPosition;
          vec3 ps2R = ps2V - 2.0 * dot( ps2N, ps2V ) * ps2N;
          // nfs6Ps2Reflect, NFS6_PS2_RSQRT
          ps2R *= ps2Pow( dot( ps2R, ps2R ), vec2( ${NFS6_PS2_RSQRT[0].toFixed(1)}, ${NFS6_PS2_RSQRT[1].toFixed(1)} ) );
          vPs2Reflect = ps2R;
          // the raw vertex colour, 0..255 (OBJ colours are sRGB to three.js, GLB COLOR_0 alpha is / 128)
          #if defined( USE_COLOR_ALPHA )
          vec4 c = vec4( color.rgb, color.a * 128.0 / 255.0 );
          #elif defined( USE_COLOR )
          vec4 c = vec4( color.rgb, 128.0 / 255.0 );
          #else
          vec4 c = vec4( 128.0 / 255.0 );
          #endif
          ${
            srgbVertexColors
              ? 'c.rgb = mix( c.rgb * 12.92, pow( max( c.rgb, 0.0 ), vec3( 1.0 / 2.4 ) ) * 1.055 - 0.055, step( 0.0031308, c.rgb ) );'
              : ''
          }
          c = floor( c * 255.0 + 0.5 );
          vec4 q0 = ps2Vectors[ 0 ];
          vec4 q3 = ps2Vectors[ 3 ];
          if ( ps2Lit > 0.5 ) {
            // nfs6Ps2VertexLight
            vec2 q = ps2Paint > 0.5 ? q3.xy : q0.xy;
            vec3 rgb = ps2Ambient.rgb;
            if ( ps2SceneLight > 0.5 ) {
              // the hemisphere ambient of the scene's sky, 128 = 1
              float up = length( ps2N ) > 0.0 ? normalize( ps2N ).z * 0.5 + 0.5 : 0.5;
              rgb = mix( sceneSkyMean( ps2Cube, ps2CubeMatrix, -1.0 ), sceneSkyMean( ps2Cube, ps2CubeMatrix, 1.0 ), up )
                * 128.0;
            }
            float alpha = ps2Paint > 0.5 ? q3.z : ps2Ambient.w;
            float s0 = 0.0;
            for ( int i = 0; i < 3; i++ ) {
              vec3 l = ps2CameraSpace > 0.5
                ? transpose( mat3( viewMatrix ) ) * ( ps2LightDirections[ i ] * vec3( 1.0, -1.0, -1.0 ) )
                : ps2LightDirections[ i ];
              l = normalize( l );
              float s = ps2Pow( max( dot( ps2R, l ), q0.z ), q );
              s0 = i == 0 ? s : s0;
              rgb += ps2LightColors[ i ] * ( ps2Vectors[ 1 ].rgb * max( dot( ps2N, l ), 0.0 ) + ps2Vectors[ 2 ].rgb * s );
            }
            alpha += q3.w * s0 * ps2Paint;
            rgb *= 1.0 + ( c.rgb - 255.0 ) * q0.w;
            vPs2Color = floor( clamp( vec4( rgb, alpha ), 0.0, 255.0 ) );
          } else {
            vPs2Color = c;
          }
          // nfs6Ps2EnvAlpha: R'z of the environment map view, the camera's (forward = -z of the view matrix rows)
          vec3 forward = -vec3( viewMatrix[ 0 ][ 2 ], viewMatrix[ 1 ][ 2 ], viewMatrix[ 2 ][ 2 ] );
          float envAlpha = mod( trunc( ps2Vectors[ 1 ].w + ps2Vectors[ 2 ].w * -dot( ps2R, forward ) ), 256.0 );
          vPs2EnvColor = vec4( ps2Paint > 0.5 ? vPs2Color.rgb : vec3( 128.0 ), envAlpha );
        }`,
      );
    shader.fragmentShader = shader.fragmentShader
      .replace(
        '#include <fog_pars_fragment>',
        `#include <fog_pars_fragment>
        uniform samplerCube ps2Cube;
        uniform mat3 ps2CubeMatrix;
        uniform float ps2EnvMode;
        uniform float ps2Env;
        uniform float ps2Paint;
        uniform float ps2AlphaTest;
        uniform float ps2Blend;
        uniform float ps2MapSrgb;
        uniform vec2 ps2Repeat;
        varying vec4 vPs2Color;
        varying vec4 vPs2EnvColor;
        varying vec3 vPs2Reflect;
        #ifdef USE_MAP
        // a texel as stored, 0..255 RGB, alpha 0..128 (the PNG alpha is doubled)
        vec4 ps2Texel( ivec2 p ) {
          ivec2 size = textureSize( map, 0 );
          p = ivec2(
            ps2Repeat.x > 0.5 ? ( p.x % size.x + size.x ) % size.x : clamp( p.x, 0, size.x - 1 ),
            ps2Repeat.y > 0.5 ? ( p.y % size.y + size.y ) % size.y : clamp( p.y, 0, size.y - 1 ) );
          vec4 t = texelFetch( map, p, 0 );
          if ( ps2MapSrgb > 0.5 ) {
            t = vec4( sRGBTransferOETF( t ).rgb, t.a );
          }
          t = floor( t * 255.0 + 0.5 );
          return vec4( t.rgb, t.a >= 255.0 ? 128.0 : floor( t.a / 2.0 ) );
        }
        #endif`,
      )
      .replace(
        '#include <opaque_fragment>',
        `#include <opaque_fragment>
        {
          #ifdef USE_MAP
          // bilinear (GS TEX1 MMAG 1)
          vec2 p = vMapUv * vec2( textureSize( map, 0 ) ) - 0.5;
          ivec2 i0 = ivec2( floor( p ) );
          vec2 f = p - floor( p );
          vec4 texel = mix(
            mix( ps2Texel( i0 ), ps2Texel( i0 + ivec2( 1, 0 ) ), f.x ),
            mix( ps2Texel( i0 + ivec2( 0, 1 ) ), ps2Texel( i0 + ivec2( 1, 1 ) ), f.x ),
            f.y );
          texel = floor( texel );
          #else
          vec4 texel = vec4( 128.0 );
          #endif
          // nfs6Ps2Modulate
          vec4 ps2Out = min( floor( texel * vPs2Color / 128.0 ), 255.0 );
          if ( ps2AlphaTest > 0.5 && ps2Out.a < 48.0 ) {
            discard;
          }
          vec3 ps2Add = vec3( 0.0 );
          if ( ps2Env > 0.5 && ps2EnvMode > 0.5 ) {
            vec3 d = normalize( vPs2Reflect );
            vec3 envTexel = floor(
              sRGBTransferOETF( vec4( textureCube( ps2Cube, ps2CubeMatrix * d ).rgb, 1.0 ) ).rgb * 255.0 + 0.5 );
            vec3 cs = min( floor( envTexel * vPs2EnvColor.rgb / 128.0 ), 255.0 );
            // front end: the vertex alpha (environment texel alpha 0x80); race paints: the main pass alpha
            float a = ps2EnvMode > 1.5 && ps2Paint > 0.5 ? ps2Out.a : vPs2EnvColor.a;
            ps2Add = floor( cs * a / 128.0 );
          }
          float alpha = ps2Blend == 10.0 ? 1.0 : min( ps2Out.a / 128.0, 1.0 );
          // blending adds the environment pass whole
          vec3 rgb = ps2Blend == 10.0
            ? min( ps2Out.rgb + ps2Add, 255.0 )
            : ps2Out.rgb + ps2Add / max( alpha, 1.0 / 255.0 );
          gl_FragColor = vec4( sRGBTransferEOTF( vec4( clamp( rgb / 255.0, 0.0, 1.0 ), 1.0 ) ).rgb, alpha );
        }`,
      );
  };
  material.customProgramCacheKey = () =>
    `${previousKey.call(material)}|nfs6-ps2-car-${gameNormals ? 'game' : 'normal'}-${srgbVertexColors ? 'srgb' : 'linear'}`;
  material.needsUpdate = true;
}

// object "<lod>_<part>__<material>": wheel parts at a wheel
const WHEEL_PART_REGEX = /^(?:hp|mp|lp|vlp)_(tire|brake|wheel_blur)_(fl|fr|rr|rl)(?:__|$)/;

/** Options of Nfs6Ps2CarMeshController */
export type Nfs6Ps2CarMeshOptions = {
  // vertex colours read by three.js' OBJLoader (sRGB values to linear); a GLB's COLOR_0 are the raw values / 255
  srgbVertexColors?: boolean;
};

/**
 * NFS Hot Pursuit 2 (PS2) car model, exported by TailsLab's Nfs6Ps2CarSerializer (OBJ or gg-web-engine GLB): objects
 * "<lod>_<part>__<material>[__<n>]", X right, Y forward, Z up, with "skins.json" and "car.json" in the same folder
 * (`baseUrl`, with trailing slash). Draws the car as the game (ps2ShadingInShader: the VU1 lighting of the front end
 * showroom, NFS6_PS2_FRONTEND_LIGHTING, the environment map pass, GS texture and blend math; every object with a
 * car.json "meshes" entry gets a material of its own), switches paints (materials "skin" and "skin_b", and the
 * lighting material "CARSKIN"), head and brake lights (materials "headlight", "brakelight": their "on" textures), spins
 * and steers the wheels (tyres and blur discs spin, brakes steer only). An export without "meshes" (older) shows its
 * vertex colours. Depends only on three.js, so it can be reused outside the GUI
 */
export class Nfs6Ps2CarMeshController {
  private wheels: { mesh: Mesh; isFront: boolean; spins: boolean }[] = [];
  private spinAngle = 0;
  private readonly materials: { [name: string]: Material[] } = {};
  private readonly originalMaps = new Map<Material, Texture | null>();
  private readonly textureLoader = new TextureLoader();
  private readonly textures: { [url: string]: Promise<Texture> } = {};
  private animationTimer: any = null;
  private readonly lightingUniforms = new LightingUniforms();
  // shaded objects: their uniforms and lighting material ("CARSKIN": the paint's)
  private readonly shaded: { uniforms: MaterialUniforms; lightingMaterial: string | null }[] = [];

  /**
   * Environment map pass: the scene's sky (sceneSkyCube: the cube texture `scene.userData[SCENE_SKY_CUBE]` or
   * `scene.background`) reflected, else none
   */
  envEnabled = true;

  private _skin: string | null = null;
  get skin(): string | null {
    return this._skin;
  }

  set skin(name: string | null) {
    const skin = this.skins.find(x => x.name === name);
    if (!skin) {
      return;
    }
    this._skin = name;
    this.setMap('skin', skin.texture);
    if (skin.texture_b) {
      this.setMap('skin_b', skin.texture_b);
    }
    this.updateMaterials();
  }

  private _raceMaterials = false;
  /** The race parameter sets of the lighting materials and the race environment pass (else the front end's) */
  get raceMaterials(): boolean {
    return this._raceMaterials;
  }

  set raceMaterials(value: boolean) {
    this._raceMaterials = value;
    this.updateMaterials();
  }

  private _lighting: Nfs6Ps2Lighting = NFS6_PS2_FRONTEND_LIGHTING;
  /** The lights of the VU1 lighting, NFS6_PS2_FRONTEND_LIGHTING by default */
  get lighting(): Nfs6Ps2Lighting {
    return this._lighting;
  }

  set lighting(value: Nfs6Ps2Lighting) {
    this._lighting = value;
    this.updateLights();
  }

  private _sceneLighting: SceneSun | null = null;
  /**
   * Lit by the scene drawing the car instead of `lighting`: the ambient from its sky (sceneSkyCube: the cube texture
   * `scene.userData[SCENE_SKY_CUBE]` or `scene.background`, sceneSkyMean) and this sun as light 0, the other lights
   * off. Null: `lighting`
   */
  get sceneLighting(): SceneSun | null {
    return this._sceneLighting;
  }

  set sceneLighting(value: SceneSun | null) {
    this._sceneLighting = value;
    this.updateLights();
  }

  /** Whether the export has the game's lighting (car.json "meshes") */
  get hasGameShading(): boolean {
    return this.shaded.length > 0;
  }

  private _headlightsOn = false;
  get headlightsOn(): boolean {
    return this._headlightsOn;
  }

  set headlightsOn(value: boolean) {
    this._headlightsOn = value;
    this.setLight('headlight', value);
  }

  private _brakeLightsOn = false;
  get brakeLightsOn(): boolean {
    return this._brakeLightsOn;
  }

  set brakeLightsOn(value: boolean) {
    this._brakeLightsOn = value;
    this.setLight('brakelight', value);
  }

  private _speed = 0;
  /** Car speed in m/s, the wheels spin at it */
  get speed(): number {
    return this._speed;
  }

  set speed(value: number) {
    const wasSpinning = this._speed !== 0;
    this._speed = value;
    if (wasSpinning === (value !== 0)) {
      return;
    }
    if (this.animationTimer) {
      clearInterval(this.animationTimer);
      this.animationTimer = null;
    }
    if (value !== 0) {
      this.animationTimer = setInterval(() => {
        // negative angle rolls wheels forward
        this.spinAngle -= this._speed / this.wheelRadius / 60;
        this.updateWheels();
      }, 1000 / 60);
    }
  }

  private _steeringAngle = 0;
  /** Front wheels' angle in radians, positive to the left */
  get steeringAngle(): number {
    return this._steeringAngle;
  }

  set steeringAngle(value: number) {
    this._steeringAngle = value;
    this.updateWheels();
  }

  get hasWheels(): boolean {
    return this.wheels.length > 0;
  }

  get hasLights(): boolean {
    return Object.keys(this.info.lights).some(x => !!this.materials[x]);
  }

  private get wheelRadius(): number {
    return this.info.wheels[0]?.radius || 0.33;
  }

  constructor(
    mesh: Object3D,
    readonly info: Nfs6Ps2CarInfo,
    readonly skins: Nfs6Ps2CarSkin[],
    private readonly baseUrl: string,
    options: Nfs6Ps2CarMeshOptions = {},
  ) {
    this.lighting = NFS6_PS2_FRONTEND_LIGHTING;
    mesh.traverse(o => {
      if (!(o instanceof Mesh)) {
        return;
      }
      const geometry = o.geometry as BufferGeometry;
      const lighting = info.meshes?.[o.name] || info.meshes?.[o.parent?.name || ''];
      if (lighting && !(o.material instanceof Array)) {
        this.shade(o, lighting, !!options.srgbVertexColors);
      }
      for (const material of o.material instanceof Array ? o.material : [o.material]) {
        // the game's shading in the vertex colours (exports without lighting)
        if (!lighting && geometry.getAttribute('color') && !material.vertexColors) {
          material.vertexColors = true;
          material.needsUpdate = true;
        }
        const list = (this.materials[material.name] ||= []);
        if (!list.includes(material)) {
          list.push(material);
          this.originalMaps.set(material, (material as MeshBasicMaterial).map || null);
        }
      }
      const match = WHEEL_PART_REGEX.exec(o.name);
      const wheel = match && info.wheels.find(w => w.name === match[2]);
      if (match && wheel) {
        const pivot = new Vector3(...wheel.position);
        geometry.translate(-pivot.x, -pivot.y, -pivot.z);
        o.position.add(pivot);
        o.rotation.order = 'ZXY';
        this.wheels.push({ mesh: o, isFront: match[2].startsWith('f'), spins: match[1] !== 'brake' });
      }
    });
    if (this.skins.length > 0 && this.materials['skin']) {
      this._skin = this.skins[0].name;
    }
    this.updateMaterials();
  }

  /** A material of its own for `mesh`, drawn with the game's shading (ps2ShadingInShader) */
  private shade(mesh: Mesh, lighting: { lighting_material: string | null; vu_flags: number }, srgbColors: boolean) {
    const material = (mesh.material as Material).clone();
    mesh.material = material;
    const settings = this.info.textures?.[material.name];
    const uniforms = new MaterialUniforms();
    uniforms.lit.value = lighting.vu_flags & 0x80 ? 1 : 0;
    uniforms.env.value = lighting.vu_flags & 0x100 ? 1 : 0;
    uniforms.paint.value = settings?.vertex_lit_env ? 1 : 0;
    uniforms.alphaTest.value = settings ? (settings.alpha_test ? 1 : 0) : 0;
    uniforms.blend.value = settings?.alpha_blend ?? 0x0a;
    const map = (material as MeshBasicMaterial).map;
    uniforms.repeat.value.set(
      settings ? (settings.repeat[0] ? 1 : 0) : map?.wrapS === RepeatWrapping ? 1 : 0,
      settings ? (settings.repeat[1] ? 1 : 0) : map?.wrapT === RepeatWrapping ? 1 : 0,
    );
    // GS ALPHA: 0x0a opaque, 0x44 blended by alpha, 0x48 added by alpha
    material.transparent = uniforms.blend.value !== 0x0a;
    material.blending = uniforms.blend.value === 0x48 ? AdditiveBlending : NormalBlending;
    if (uniforms.blend.value !== 0x0a) {
      material.depthWrite = false;
    }
    material.alphaTest = 0;
    material.toneMapped = false;
    const geometry = mesh.geometry as BufferGeometry;
    if (geometry.getAttribute('color')) {
      material.vertexColors = true;
    }
    ps2ShadingInShader(material, this.lightingUniforms, uniforms, !!geometry.getAttribute('_game_normal'), srgbColors);
    this.shaded.push({ uniforms, lightingMaterial: lighting.lighting_material });
    const previous = mesh.onBeforeRender;
    mesh.onBeforeRender = (renderer, scene, camera, ...rest) => {
      previous.call(mesh, renderer, scene, camera, ...rest);
      this.updateEnvironment(scene);
    };
  }

  /** The VU1 lights of `lighting`, or the scene's sun (colours 0..255, 128 = 1) */
  private updateLights() {
    const u = this.lightingUniforms;
    const sun = this._sceneLighting;
    const value: Nfs6Ps2Lighting = sun
      ? {
          space: 'world',
          directions: [sun.direction, [0, 0, 1], [0, 0, 1]],
          colors: [sun.color.map(c => c * 128) as [number, number, number], [0, 0, 0], [0, 0, 0]],
          ambient: this._lighting.ambient,
        }
      : this._lighting;
    value.directions.forEach((d, i) => u.directions.value[i].set(...d));
    value.colors.forEach((c, i) => u.colors.value[i].set(...c));
    u.ambient.value.set(...value.ambient, 128);
    u.cameraSpace.value = value.space === 'camera' ? 1 : 0;
  }

  /** The lighting material vectors of every shaded object, the paint's for "CARSKIN" */
  private updateMaterials() {
    const paint = this.skins.find(x => x.name === this._skin)?.lighting_material || null;
    for (const { uniforms, lightingMaterial } of this.shaded) {
      const name = lightingMaterial === 'CARSKIN' ? paint : lightingMaterial;
      const sets = (name && this.info.lighting_materials?.[name]) || this.info.lighting_materials?.['Default'];
      const vectors = sets ? (this._raceMaterials ? sets.race : sets.frontend) : new Array(16).fill(0);
      uniforms.vectors.value.forEach((v, i) => v.fromArray(vectors, i * 4));
    }
  }

  /** The environment pass source and mode and the scene's lighting, before an object is drawn in `scene` */
  private updateEnvironment(scene: Scene) {
    const u = this.lightingUniforms;
    const sky = sceneSkyCube(scene, u.cubeMatrix.value);
    u.cube.value = sky;
    u.envMode.value = this.envEnabled && sky ? (this._raceMaterials ? 2 : 1) : 0;
    u.sceneLight.value = this._sceneLighting && sky ? 1 : 0;
  }

  private texture(url: string): Promise<Texture> {
    return (this.textures[url] ||= this.textureLoader.loadAsync(this.baseUrl + url));
  }

  private setMap(materialName: string, url: string | null) {
    for (const material of this.materials[materialName] || []) {
      const original = this.originalMaps.get(material);
      if (!url || !original) {
        continue;
      }
      this.texture(url).then(loaded => {
        const texture = loaded.clone();
        texture.flipY = original.flipY;
        texture.wrapS = original.wrapS;
        texture.wrapT = original.wrapT;
        texture.colorSpace = original.colorSpace;
        texture.anisotropy = original.anisotropy;
        texture.magFilter = original.magFilter;
        texture.minFilter = original.minFilter;
        texture.needsUpdate = true;
        (material as MeshBasicMaterial).map = texture;
        material.needsUpdate = true;
      });
    }
  }

  private setLight(light: string, on: boolean) {
    const states = this.info.lights[light];
    const url = on ? states?.on : states?.off;
    if (url) {
      this.setMap(light, url);
    }
  }

  private updateWheels() {
    for (const { mesh, isFront, spins } of this.wheels) {
      mesh.rotation.set(spins ? this.spinAngle : 0, 0, isFront ? this._steeringAngle : 0);
    }
  }

  dispose() {
    if (this.animationTimer) {
      clearInterval(this.animationTimer);
      this.animationTimer = null;
    }
  }
}
