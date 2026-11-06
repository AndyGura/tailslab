import {
  Box3,
  Group,
  Material,
  Matrix3,
  Matrix4,
  Mesh,
  MeshBasicMaterial,
  NearestFilter,
  Object3D,
  SphereGeometry,
  SRGBColorSpace,
  Texture,
  TextureLoader,
  Vector3,
  Vector4,
} from 'three';

export type FceDummy = { name: string; position: [number, number, number] };

export type FceColor = { hue: number; saturation: number; brightness: number; transparency: number };

/** FCE color (HSB, every component is 0..255) to 0xRRGGBB */
export const fceColorToRgb = (color: FceColor): number => {
  const h = (color.hue / 255) * 6;
  const s = color.saturation / 255;
  const v = color.brightness / 255;
  const f = (n: number) => {
    const k = (n + h) % 6;
    return Math.round(255 * (v - v * s * Math.max(0, Math.min(k, 4 - k, 1))));
  };
  return (f(5) << 16) | (f(3) << 8) | f(1);
};

/** 0xRRGGBB to an FCE color with the given transparency (HSB as nfs3.exe reads it: hue sector = hue * 6 >> 8) */
export const rgbToFceColor = (rgb: number, transparency: number): FceColor => {
  const [r, g, b] = [rgb >> 16, (rgb >> 8) & 0xff, rgb & 0xff];
  const max = Math.max(r, g, b);
  const delta = max - Math.min(r, g, b);
  let hue = 0;
  if (delta > 0) {
    const sector = max === r ? (g - b) / delta : max === g ? (b - r) / delta + 2 : (r - g) / delta + 4;
    hue = Math.min(255, Math.floor((((sector + 6) % 6) / 6) * 256));
  }
  return { hue, saturation: max ? Math.round((delta / max) * 255) : 0, brightness: max, transparency };
};

/**
 * nfs3.exe 0x49ca50: FCE color (HSB) to RGB, every component 0..255, integer math of the exe (sector = hue * 6 >> 8,
 * its fraction as 16.16, rounded fixed-point products)
 */
export const fce3HsbToRgb = (color: FceColor): [number, number, number] => {
  const { hue: h, saturation: s, brightness: v } = color;
  const clamp = (c: number) => Math.max(0, Math.min(255, c));
  if (v <= 0) {
    return [0, 0, 0];
  }
  if (s <= 0) {
    return [clamp(v), clamp(v), clamp(v)];
  }
  const sector = (h * 6) >> 8;
  // trunc(h * 6.0 - sector * 256) as 16.16 of x / 256
  const x = h * 6 - sector * 256;
  const p = (v * (256 - s)) >> 8;
  // fixmul(s, x * 256) and fixmul(s, 0x10000 - x * 256), rounded: (s * k + 128) >> 8
  const q = ((256 - ((s * x + 128) >> 8)) * v) >> 8;
  const t = ((256 - ((s * (256 - x) + 128) >> 8)) * v) >> 8;
  const rgb: [number, number, number][] = [
    [v, t, p],
    [q, v, p],
    [p, v, t],
    [p, q, v],
    [t, p, v],
    [v, p, q],
  ];
  return rgb[sector].map(clamp) as [number, number, number];
};

/**
 * nfs3.exe 0x49cc50: the paint of a car texel, 0..255 RGB before the exe's reduction to 5 bits. The texel's blue
 * channel (5 bits, << 3) shades the color's brightness: brightness * blue / (255 - transparency) (transparency 255:
 * brightness * blue), truncated, at most 255; float32 as the exe stores the factor
 */
export const fce3PaintColor = (blue: number, color: FceColor): [number, number, number] => {
  const blue8 = (blue >> 3) << 3;
  const factor = color.transparency === 255 ? blue8 : Math.fround(blue8 / (255 - color.transparency));
  const brightness = Math.min(255, Math.trunc(color.brightness * factor));
  return fce3HsbToRgb({ ...color, brightness });
};

/**
 * nfs3.exe 0x49cd00 (car texture upload): a texel of car00.tga (RGB, its alpha) as the game draws it, 0..255 RGB. Alpha
 * 1..127: primary paint, 128..254: secondary paint, 255: the texel; every channel then reduced to 5 bits (the 16-bit
 * 1555 texture), shown as 5-bit unorm (c / 31). Alpha 0 is a transparent texel.
 * SKIPPED: an opaque black texel (0x8000) becomes 0x8001 when the renderer asks for it (flag 0x7a3a6c, colour key)
 */
export const fce3TexelColor = (
  rgb: [number, number, number],
  alpha: number,
  primary: FceColor,
  secondary: FceColor,
): [number, number, number] => {
  const color = alpha > 0 && alpha < 0x80 ? primary : alpha > 0 && alpha < 0xff ? secondary : null;
  const painted = color ? fce3PaintColor(rgb[2], color) : rgb;
  return painted.map(c => Math.round(((c >> 3) * 255) / 31)) as [number, number, number];
};

export type FceVersion = 3 | 4;

// FCE4: texture alpha of pixels, painted with primary, interior, secondary and driver hair color
const FCE4_COLOR_ALPHAS = [224, 164, 96, 32];

// FCE3: part indices of car.fce wheels, by LOD. Order: front left, front right, rear left, rear right
const FCE3_HIGH_POLY_WHEELS = [1, 2, 3, 4];
const FCE3_MEDIUM_POLY_WHEELS = [7, 6, 9, 8];

// FCE4: car.fce wheel part name: high/medium LOD, left/right, front/middle/rear
const FCE4_WHEEL_REGEX = /^(?:hp|mp)_\d+_[HM][LR]([FMR])W(?=__|_damaged$|$)/i;
// FCE4: front brakes steer together with wheels, but don't spin
const FCE4_BRAKE_REGEX = /^hp_\d+_O[LR]B(?=__|_damaged$|$)/i;

// wheel radius (m) for the spin rate at a speed
const WHEEL_RADIUS = 0.33;

/**
 * Paint mask of a texture: "<texture>_paint_mask.png" next to the texture file (TailsLab's OBJ textures), null when
 * the texture has no file URL
 */
export const fcePaintMaskNextToTexture = (texture: Texture): string | null => {
  const url: string | undefined = (texture.source.data as HTMLImageElement)?.src;
  return url && /\.png(\?.*)?$/.test(url) ? url.replace(/\.png(\?.*)?$/, '_paint_mask.png$1') : null;
};

/**
 * Index of the paint (see FceCarMeshController.colors) of a paint mask alpha, -1 for unpainted (0 and 255). Kept in
 * sync with fcePaint in the fragment shader. FCE3 as nfs3.exe 0x49cd00: 1..127 primary, 128..254 secondary. FCE4: the
 * nearest of FCE4_COLOR_ALPHAS, the first one on a tie (not verified in nfs4.exe yet)
 */
export const fcePaintIndexOfAlpha = (version: FceVersion, alpha: number): number => {
  if (alpha === 0 || alpha === 255) {
    return -1;
  }
  if (version === 3) {
    return alpha < 0x80 ? 0 : 1;
  }
  let result = 0;
  FCE4_COLOR_ALPHAS.forEach((value, i) => {
    if (Math.abs(alpha - value) < Math.abs(alpha - FCE4_COLOR_ALPHAS[result])) {
      result = i;
    }
  });
  return result;
};

/**
 * FCE4: painted 0..255 sRGB channel, the texture a greyscale shading of the paint, mid-grey exactly the paint (not
 * verified in nfs4.exe yet)
 */
export const fcePaintChannel = (texel: number, paint: number): number =>
  Math.min(255, Math.round((texel * paint) / 128));

/** Uniforms of one texture: its paint mask, and the controller's paints */
class PaintUniforms {
  readonly mask: { value: Texture | null } = { value: null };
  readonly enabled = { value: 0 };

  constructor(
    /** FCE3: hue, saturation, brightness, transparency. FCE4: RGB */
    readonly colors: { value: Vector4[] },
    readonly fce4: { value: number },
  ) {}
}

/**
 * The material paints its texels in the fragment shader (reading a canvas back gets noise from anti-fingerprinting),
 * as fcePaintIndexOfAlpha / fcePaintChannel. Each texel is painted before filtering: with a nearest filter the sample
 * is the texel, a linearly filtered map is sampled texel by texel (base level), every texel with the mask texel at its
 * centre (the mask can have another size). The sRGB value is read back to 0..255
 */
function paintInShader(material: Material, uniforms: PaintUniforms) {
  const previous = material.onBeforeCompile;
  const previousKey = material.customProgramCacheKey;
  material.onBeforeCompile = (shader, renderer) => {
    previous.call(material, shader, renderer);
    shader.uniforms['fcePaintColors'] = uniforms.colors;
    shader.uniforms['fcePaintFce4'] = uniforms.fce4;
    shader.uniforms['fcePaintMask'] = uniforms.mask;
    shader.uniforms['fcePaintEnabled'] = uniforms.enabled;
    shader.uniforms['fcePaintFiltered'] = {
      get value() {
        const map = (material as MeshBasicMaterial).map;
        return map && map.magFilter !== NearestFilter ? 1 : 0;
      },
    };
    shader.fragmentShader = shader.fragmentShader
      .replace(
        '#include <map_pars_fragment>',
        `#include <map_pars_fragment>
        uniform vec4 fcePaintColors[ 4 ];
        uniform float fcePaintFce4;
        uniform sampler2D fcePaintMask;
        uniform float fcePaintEnabled;
        uniform float fcePaintFiltered;
        float fceShr8( float a ) { return floor( a / 256.0 ); }
        // fce3HsbToRgb: integer math in floats, exact below 2^24
        vec3 fce3HsbToRgb( vec4 hsb ) {
          float h = hsb.x, s = hsb.y, v = hsb.z;
          if ( v <= 0.0 ) {
            return vec3( 0.0 );
          }
          if ( s <= 0.0 ) {
            return vec3( clamp( v, 0.0, 255.0 ) );
          }
          float sector = fceShr8( h * 6.0 );
          float x = h * 6.0 - sector * 256.0;
          float p = fceShr8( v * ( 256.0 - s ) );
          float q = fceShr8( ( 256.0 - fceShr8( s * x + 128.0 ) ) * v );
          float t = fceShr8( ( 256.0 - fceShr8( s * ( 256.0 - x ) + 128.0 ) ) * v );
          vec3 rgb = sector < 0.5 ? vec3( v, t, p ) : sector < 1.5 ? vec3( q, v, p ) : sector < 2.5 ? vec3( p, v, t )
            : sector < 3.5 ? vec3( p, q, v ) : sector < 4.5 ? vec3( t, p, v ) : vec3( v, p, q );
          return clamp( rgb, 0.0, 255.0 );
        }
        // fce3PaintColor
        vec3 fce3PaintColor( float blue, vec4 color ) {
          float blue8 = floor( blue / 8.0 ) * 8.0;
          float factor = color.w == 255.0 ? blue8 : blue8 / ( 255.0 - color.w );
          return fce3HsbToRgb( vec4( color.xy, min( 255.0, floor( color.z * factor ) ), color.w ) );
        }
        vec4 fcePaint( vec4 sampled, vec2 uv ) {
          float alpha = floor( textureLod( fcePaintMask, uv, 0.0 ).a * 255.0 + 0.5 );
          vec3 texel = floor( sRGBTransferOETF( sampled ).rgb * 255.0 + 0.5 );
          vec3 painted;
          if ( fcePaintFce4 < 0.5 ) {
            // fce3TexelColor: every texel of the texture goes through the 16-bit texture
            if ( alpha > 0.0 && alpha < 128.0 ) {
              texel = fce3PaintColor( texel.b, fcePaintColors[ 0 ] );
            } else if ( alpha > 0.0 && alpha < 255.0 ) {
              texel = fce3PaintColor( texel.b, fcePaintColors[ 1 ] );
            }
            painted = floor( floor( texel / 8.0 ) * 255.0 / 31.0 + 0.5 );
          } else {
            if ( alpha == 0.0 || alpha == 255.0 ) {
              return sampled;
            }
            vec3 paint = alpha >= ${(FCE4_COLOR_ALPHAS[0] + FCE4_COLOR_ALPHAS[1]) / 2}.0 ? fcePaintColors[ 0 ].rgb
              : alpha >= ${(FCE4_COLOR_ALPHAS[1] + FCE4_COLOR_ALPHAS[2]) / 2}.0 ? fcePaintColors[ 1 ].rgb
              : alpha >= ${(FCE4_COLOR_ALPHAS[2] + FCE4_COLOR_ALPHAS[3]) / 2}.0 ? fcePaintColors[ 2 ].rgb
              : fcePaintColors[ 3 ].rgb;
            painted = min( floor( texel * paint / 128.0 + 0.5 ), 255.0 );
          }
          return vec4( sRGBTransferEOTF( vec4( painted / 255.0, 1.0 ) ).rgb, sampled.a );
        }`,
      )
      .replace(
        '#include <map_fragment>',
        `#include <map_fragment>
        #ifdef USE_MAP
        if ( fcePaintEnabled > 0.5 ) {
          ivec2 size = textureSize( map, 0 );
          vec4 painted;
          if ( fcePaintFiltered > 0.5 ) {
            // the 4 texels of a bilinear sample painted, then blended (base level only)
            vec2 p = vMapUv * vec2( size ) - 0.5;
            ivec2 i0 = ivec2( floor( p ) );
            vec2 f = p - floor( p );
            ivec2 last = size - 1;
            ivec2 c00 = clamp( i0, ivec2( 0 ), last );
            ivec2 c10 = clamp( i0 + ivec2( 1, 0 ), ivec2( 0 ), last );
            ivec2 c01 = clamp( i0 + ivec2( 0, 1 ), ivec2( 0 ), last );
            ivec2 c11 = clamp( i0 + ivec2( 1, 1 ), ivec2( 0 ), last );
            vec2 texelSize = 1.0 / vec2( size );
            vec4 t00 = fcePaint( texelFetch( map, c00, 0 ), ( vec2( c00 ) + 0.5 ) * texelSize );
            vec4 t10 = fcePaint( texelFetch( map, c10, 0 ), ( vec2( c10 ) + 0.5 ) * texelSize );
            vec4 t01 = fcePaint( texelFetch( map, c01, 0 ), ( vec2( c01 ) + 0.5 ) * texelSize );
            vec4 t11 = fcePaint( texelFetch( map, c11, 0 ), ( vec2( c11 ) + 0.5 ) * texelSize );
            painted = mix( mix( t00, t10, f.x ), mix( t01, t11, f.x ), f.y );
          } else {
            // nearest: the sample is the texel, the mask is read at its centre
            vec2 texel = clamp( floor( vMapUv * vec2( size ) ), vec2( 0.0 ), vec2( size - 1 ) );
            painted = fcePaint( sampledDiffuseColor, ( texel + 0.5 ) / vec2( size ) );
          }
          diffuseColor = vec4( diffuse, opacity ) * painted;
        }
        #endif`,
      );
  };
  material.customProgramCacheKey = () => `${previousKey.call(material)}|fce-paint`;
  material.needsUpdate = true;
}

/**
 * nfs3.exe 0x49d780 (CarDraw_SetEnvMatrix): the chrome environment matrix (3x3, rows) from the direction `d` from the
 * car to the camera (CarDraw_SetupChrome 0x4ba350: camera position - car position), game axes (x right, y up, z
 * forward): RotY(atan2(d.x, d.z) - 0.5 turn) RotX(atan2(hypot(d.x, d.z), d.y) - 0.25 turn), the exe's rotation
 * matrices (RotY rows (c 0 -s) (0 1 0) (s 0 c), RotX rows (1 0 0) (0 c s) (0 -s c)). A normal n (row vector, world
 * game axes) gets the chrome texture coordinates of fce3ChromeUv(n M)
 */
export const fce3ChromeEnvMatrix = (d: [number, number, number]): number[] => {
  const turn = 2 * Math.PI;
  const a = (Math.atan2(d[0], d[2]) / turn - 0.5) * turn;
  const b = (Math.atan2(Math.hypot(d[0], d[2]), d[1]) / turn - 0.25) * turn;
  const [sy, cy, sx, cx] = [Math.sin(a), Math.cos(a), Math.sin(b), Math.cos(b)];
  const rotY = [cy, 0, -sy, 0, 1, 0, sy, 0, cy];
  const rotX = [1, 0, 0, 0, cx, sx, 0, -sx, cx];
  const m: number[] = [];
  for (let r = 0; r < 3; r++) {
    for (let c = 0; c < 3; c++) {
      m.push(rotY[r * 3] * rotX[c] + rotY[r * 3 + 1] * rotX[3 + c] + rotY[r * 3 + 2] * rotX[6 + c]);
    }
  }
  return m;
};

/**
 * nfs3.exe 0x49db70 (CarDraw_EnvMapUVs): chrome texture coordinates (D3D's: v = 0 at the top row) of a normal in the
 * environment matrix space, a sphere map with both hemispheres alike. Computed per vertex, interpolated over triangles
 */
export const fce3ChromeUv = (n: [number, number, number]): [number, number] => {
  const m = 0.707106 / Math.sqrt((Math.abs(n[2]) + 1) * 2);
  return [n[0] * m + 0.5, n[1] * m + 0.5];
};

/**
 * Vertex color of the chrome pass (CarDraw_QueuePolys 0x49dbf0, CarDraw_SetChromeColors 0x49d800): 0x7f7f7f7f, a
 * "high_chrome" triangle 0xffffffff, none for a "matte" one (Fce3GeometrySerializer's mesh name suffixes and
 * "fceChrome" extras). SKIPPED: both are scaled by [0x6fbc38] when it is below 1 (hardware renderers)
 */
const FCE3_CHROME_COLORS = { normal: 0x7f / 255, high: 1 };

/**
 * One chrome pass color added over the framebuffer, 0..255: the chrome texel (ARGB4444, texture type 7 of the
 * Direct3D driver D3DA.DLL: every channel 8 bits >> 4, shown as c / 15) times the vertex color, D3D's
 * D3DTBLEND_MODULATE (the texture's alpha, the vertex alpha is not used), blended with source alpha and one (THRASH
 * state 0x68 = 1). The reduction of the SKY.FSH texel to 4 bits is assumed (the exe's 32-bit to 4444 conversion is
 * not verified)
 */
export const fce3ChromeAdd = (texel: [number, number, number, number], vertexColor: number): number[] => {
  const [r, g, b, a] = texel.map(c => (c >> 4) / 15);
  return [r, g, b].map(c => c * vertexColor * a * 255);
};

/** Uniforms of the chrome pass of one car, shared by its chrome materials */
class ChromeUniforms {
  readonly map: { value: Texture | null } = { value: null };
  readonly enabled = { value: 0 };
  // mesh normal (local axes of the GLB / OBJ: x, y forward, z up) to the environment matrix space
  readonly matrix = { value: new Matrix3() };
}

/**
 * The chrome pass of nfs3.exe (Render_CarPolyList 0x434120, a second pass of every body triangle but matte ones),
 * added in the fragment shader of the material over its own color: texture coordinates per vertex from the game's
 * normal (`_game_normal`, else `normal`), the chrome texel as fce3ChromeAdd, added in the output color space (the game
 * blends in the framebuffer's), divided by the fragment's alpha (or premultiplied) so that blending adds it whole
 */
function chromeInShader(material: Material, uniforms: ChromeUniforms, vertexColor: number, gameNormals: boolean) {
  const previous = material.onBeforeCompile;
  const previousKey = material.customProgramCacheKey;
  material.onBeforeCompile = (shader, renderer) => {
    previous.call(material, shader, renderer);
    shader.uniforms['fceChromeMap'] = uniforms.map;
    shader.uniforms['fceChromeEnabled'] = uniforms.enabled;
    shader.uniforms['fceChromeMatrix'] = uniforms.matrix;
    shader.uniforms['fceChromeColor'] = { value: vertexColor };
    shader.uniforms['fceChromeFlipY'] = {
      get value() {
        return uniforms.map.value?.flipY ? 1 : 0;
      },
    };
    shader.uniforms['fceChromeFiltered'] = {
      get value() {
        return uniforms.map.value && uniforms.map.value.magFilter !== NearestFilter ? 1 : 0;
      },
    };
    shader.uniforms['fceChromeSrgb'] = {
      get value() {
        return uniforms.map.value?.colorSpace === SRGBColorSpace ? 1 : 0;
      },
    };
    shader.vertexShader = shader.vertexShader
      .replace(
        '#include <fog_pars_vertex>',
        `#include <fog_pars_vertex>
        ${gameNormals ? 'attribute vec3 _game_normal;' : ''}
        uniform mat3 fceChromeMatrix;
        uniform float fceChromeFlipY;
        varying vec2 vFceChromeUv;`,
      )
      .replace(
        '#include <fog_vertex>',
        `#include <fog_vertex>
        vec3 fceChromeNormal = fceChromeMatrix * ${gameNormals ? '_game_normal' : 'normal'};
        float fceChromeM = 0.707106 / sqrt( ( abs( fceChromeNormal.z ) + 1.0 ) * 2.0 );
        vFceChromeUv = fceChromeNormal.xy * fceChromeM + 0.5;
        // D3D: v = 0 is the top row
        if ( fceChromeFlipY > 0.5 ) {
          vFceChromeUv.y = 1.0 - vFceChromeUv.y;
        }`,
      );
    shader.fragmentShader = shader.fragmentShader
      .replace(
        '#include <fog_pars_fragment>',
        `#include <fog_pars_fragment>
        uniform sampler2D fceChromeMap;
        uniform float fceChromeEnabled;
        uniform float fceChromeColor;
        uniform float fceChromeFiltered;
        uniform float fceChromeSrgb;
        varying vec2 vFceChromeUv;
        // a texel of the 4444 chrome texture, 0..1
        vec4 fceChromeTexel( ivec2 c ) {
          vec4 t = texelFetch( fceChromeMap, c, 0 );
          if ( fceChromeSrgb > 0.5 ) {
            t = vec4( sRGBTransferOETF( t ).rgb, t.a );
          }
          return floor( floor( t * 255.0 + 0.5 ) / 16.0 ) / 15.0;
        }`,
      )
      .replace(
        '#include <premultiplied_alpha_fragment>',
        `#include <premultiplied_alpha_fragment>
        if ( fceChromeEnabled > 0.5 ) {
          ivec2 size = textureSize( fceChromeMap, 0 );
          ivec2 last = size - 1;
          vec4 env;
          if ( fceChromeFiltered > 0.5 ) {
            vec2 p = vFceChromeUv * vec2( size ) - 0.5;
            ivec2 i0 = ivec2( floor( p ) );
            vec2 f = p - floor( p );
            env = mix(
              mix( fceChromeTexel( clamp( i0, ivec2( 0 ), last ) ), fceChromeTexel( clamp( i0 + ivec2( 1, 0 ), ivec2( 0 ), last ) ), f.x ),
              mix( fceChromeTexel( clamp( i0 + ivec2( 0, 1 ), ivec2( 0 ), last ) ), fceChromeTexel( clamp( i0 + ivec2( 1, 1 ), ivec2( 0 ), last ) ), f.x ),
              f.y );
          } else {
            env = fceChromeTexel( clamp( ivec2( floor( vFceChromeUv * vec2( size ) ) ), ivec2( 0 ), last ) );
          }
          vec3 fceChromeAdd = env.rgb * fceChromeColor * env.a;
          #ifdef PREMULTIPLIED_ALPHA
          gl_FragColor.rgb += fceChromeAdd;
          #else
          gl_FragColor.rgb += fceChromeAdd / max( gl_FragColor.a, 1.0 / 255.0 );
          #endif
        }`,
      );
  };
  material.customProgramCacheKey = () =>
    `${previousKey.call(material)}|fce-chrome-${gameNormals ? 'game' : 'normal'}-${vertexColor}`;
  material.needsUpdate = true;
}

/**
 * Animates car.fce model: steers and spins wheels, shows light dummies, paints the car in the fragment shader of its
 * materials (the textures stay as they are). Expects meshes, exported by Fce3GeometrySerializer/Fce4GeometrySerializer:
 * "<lod>_<part index>_<part name>[__<texture>][_damaged]". A texture is painted by its paint mask (`paintMaskUrl`, the
 * alpha channel of car00.tga, see fcePaintIndexOfAlpha; FCE3: fce3TexelColor, the whole texture as nfs3.exe uploads
 * it, at 5 bits per channel). Materials are changed in place:
 * a material shared with another copy of the model gets this controller's paint
 */
export class FceCarMeshController {
  // every wheel can consist of a few meshes (one per texture, damaged copy)
  private wheels: { meshes: Mesh[]; isFront: boolean; spins: boolean }[] = [];
  private lights: Group | null = null;
  private spinAngle = 0;
  // paint uniforms by texture
  private readonly paintTextures = new Map<Texture, PaintUniforms>();
  private readonly paintedMaterials = new Set<Material>();
  private disposed = false;
  private readonly chrome = new ChromeUniforms();
  // FCE3 body meshes with a chrome pass
  private readonly chromeMeshes: Mesh[] = [];

  /** Whether the model has meshes with chrome (FCE3 body triangles but matte ones) */
  get hasChrome(): boolean {
    return this.chromeMeshes.length > 0;
  }

  /**
   * The chrome (environment) texture, nfs3.exe: the track's SKY.FSH `CHRD` (day; `CHRN` night, `CHRW` / `CHNW` in
   * the rain), null for no chrome (the game's "carchrome" option off). Not owned by the controller
   */
  get chromeTexture(): Texture | null {
    return this.chrome.map.value;
  }

  set chromeTexture(value: Texture | null) {
    this.chrome.map.value = value;
    this.chrome.enabled.value = value && this.chromeMeshes.length ? 1 : 0;
  }

  // FCE3: primary, secondary. FCE4: primary, interior, secondary, driver hair
  private readonly colors: FceColor[];
  private readonly colorUniforms = { value: [new Vector4(), new Vector4(), new Vector4(), new Vector4()] };

  getColor(index: number): FceColor {
    return this.colors[index];
  }

  setColor(index: number, value: FceColor) {
    this.colors[index] = { ...value };
    this.updateColorUniforms();
  }

  get isPaintable(): boolean {
    return this.paintTextures.size > 0;
  }
  private animationTimer: any = null;

  private _speed = 0;
  /** Car speed in m/s, the wheels spin at it (backwards when negative). Can be set every frame */
  get speed(): number {
    return this._speed;
  }

  set speed(value: number) {
    // the timer keeps running while the wheels spin
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
        this.spinAngle -= this._speed / WHEEL_RADIUS / 60;
        this.updateWheels();
      }, 1000 / 60);
    }
  }

  private _steeringAngle: number = 0;
  get steeringAngle(): number {
    return this._steeringAngle;
  }

  set steeringAngle(value: number) {
    this._steeringAngle = value;
    this.updateWheels();
  }

  get showLights(): boolean {
    return !!this.lights?.visible;
  }

  set showLights(value: boolean) {
    if (this.lights) {
      this.lights.visible = value;
    }
  }

  get hasWheels(): boolean {
    return this.wheels.length > 0;
  }

  get hasLights(): boolean {
    return !!this.lights;
  }

  /**
   * @param paintMaskUrl URL of a texture's paint mask, null for a texture never painted. Default: next to the texture
   * file (fcePaintMaskNextToTexture)
   */
  constructor(
    mesh: Object3D,
    private readonly version: FceVersion,
    dummies: FceDummy[],
    colors: FceColor[],
    paintMaskUrl: (texture: Texture) => string | null = fcePaintMaskNextToTexture,
  ) {
    this.colors = colors.map(c => ({ ...c }));
    this.updateColorUniforms();
    this.root = mesh;
    if (version === 3) {
      this.setupChrome(mesh);
    }
    this.setupPaint(mesh, paintMaskUrl);
    // wheel meshes by part index
    const parts: { [index: number]: { meshes: Mesh[]; isFront: boolean; spins: boolean } } = {};
    let body: Mesh | null = null;
    mesh.traverse(o => {
      if (!(o instanceof Mesh)) {
        return;
      }
      const match = /^(hp|mp)_(\d+)/.exec(o.name);
      if (!match) {
        return;
      }
      const index = +match[2];
      const isBody = version === 3 ? index === 0 : /^hp_\d+_HB(?=__|$)/i.test(o.name);
      if (isBody && !body) {
        body = o;
      }
      let wheel: { isFront: boolean; spins: boolean } | null = null;
      if (version === 3) {
        for (const wheelIndices of [FCE3_HIGH_POLY_WHEELS, FCE3_MEDIUM_POLY_WHEELS]) {
          if (wheelIndices.includes(index)) {
            wheel = { isFront: wheelIndices.indexOf(index) < 2, spins: true };
          }
        }
      } else {
        const wheelMatch = FCE4_WHEEL_REGEX.exec(o.name);
        if (wheelMatch) {
          wheel = { isFront: wheelMatch[1].toUpperCase() === 'F', spins: true };
        } else if (FCE4_BRAKE_REGEX.test(o.name)) {
          wheel = { isFront: true, spins: false };
        }
      }
      if (wheel) {
        (parts[index] = parts[index] || { meshes: [], ...wheel }).meshes.push(o);
      }
    });
    for (const wheel of Object.values(parts)) {
      // move pivot to the wheel center, so it rotates in place
      const box = new Box3();
      for (const m of wheel.meshes) {
        m.geometry.computeBoundingBox();
        box.union(m.geometry.boundingBox!);
      }
      const center = box.getCenter(new Vector3());
      for (const m of wheel.meshes) {
        m.geometry.translate(-center.x, -center.y, -center.z);
        m.position.copy(center);
        m.rotation.order = 'ZXY';
      }
      this.wheels.push(wheel);
    }
    const lightDummies = dummies.filter(d => FceCarMeshController.lightColor(version, d.name) !== null);
    if (body && lightDummies.length > 0) {
      this.lights = new Group();
      for (const dummy of lightDummies) {
        const light = new Mesh(
          new SphereGeometry(0.05, 8, 8),
          new MeshBasicMaterial({ color: FceCarMeshController.lightColor(version, dummy.name)! }),
        );
        light.name = dummy.name;
        light.position.set(...dummy.position);
        this.lights.add(light);
      }
      (body as Mesh).add(this.lights);
    }
  }

  private readonly root: Object3D;

  /**
   * Gives every FCE3 body mesh (part 0) but matte ones its own copies of its materials, with the chrome pass (shared
   * materials: the wheels and the other parts draw the same textures without it)
   */
  private setupChrome(mesh: Object3D) {
    mesh.traverse(o => {
      if (!(o instanceof Mesh) || !/^(hp|mp)_0(?:_|$)/.test(o.name)) {
        return;
      }
      const name = o.name.replace(/_damaged$/, '');
      const kind: string =
        o.userData?.['fceChrome'] ?? (/_matte$/.test(name) ? 'none' : /_high_chrome$/.test(name) ? 'high' : 'normal');
      const color = FCE3_CHROME_COLORS[kind as keyof typeof FCE3_CHROME_COLORS];
      if (color === undefined) {
        return;
      }
      const gameNormals = !!o.geometry.getAttribute('_game_normal');
      const copy = (material: Material) => {
        const clone = material.clone();
        if (clone.transparent) {
          // the base pass blended as before, the chrome added whole (source alpha, one)
          clone.premultipliedAlpha = true;
        }
        chromeInShader(clone, this.chrome, color, gameNormals);
        return clone;
      };
      o.material = o.material instanceof Array ? o.material.map(copy) : copy(o.material);
      if (!this.chromeMeshes.length) {
        // turned to every camera that draws it, before the draw
        const previous = o.onBeforeRender;
        o.onBeforeRender = (renderer, scene, camera, ...rest) => {
          previous.call(o, renderer, scene, camera, ...rest);
          if (!this.disposed) {
            this.updateChrome(camera.getWorldPosition(this.cameraPosition));
          }
        };
      }
      this.chromeMeshes.push(o);
    });
  }

  private readonly cameraPosition = new Vector3();

  /**
   * Turns the chrome to the camera (CarDraw_SetupChrome 0x4ba350: the environment matrix from the camera's
   * direction, fce3ChromeEnvMatrix). Called before the body is drawn, with the camera drawing it. The world is expected in TailsLab's export
   * axes (x, y = game z, z up = game y): the GLB / OBJ axes, nfs-web's world and TailsLab's viewers
   */
  updateChrome(cameraPosition: Vector3) {
    const body = this.chromeMeshes[0];
    if (!body || !this.chrome.enabled.value) {
      return;
    }
    this.root.updateWorldMatrix(true, false);
    body.updateWorldMatrix(true, false);
    const d = cameraPosition.clone().sub(new Vector3().setFromMatrixPosition(this.root.matrixWorld));
    const e = fce3ChromeEnvMatrix([d.x, d.z, d.y]);
    // column vectors: env normal = Env^T (game normal), game normal = S (world normal), world normal = R (mesh normal)
    const envT = new Matrix3().set(e[0], e[3], e[6], e[1], e[4], e[7], e[2], e[5], e[8]);
    const swap = new Matrix3().set(1, 0, 0, 0, 0, 1, 0, 1, 0);
    const rotation = new Matrix3().setFromMatrix4(new Matrix4().extractRotation(body.matrixWorld));
    this.chrome.matrix.value.copy(envT.multiply(swap).multiply(rotation));
  }

  /** Every material with a texture that has a paint mask URL paints in its shader once the mask is loaded */
  private setupPaint(mesh: Object3D, paintMaskUrl: (texture: Texture) => string | null) {
    const fce4 = { value: this.version === 4 ? 1 : 0 };
    mesh.traverse(o => {
      if (!(o instanceof Mesh)) {
        return;
      }
      const materials = o.material instanceof Array ? o.material : [o.material];
      for (const material of materials) {
        const map: Texture | null = (material as MeshBasicMaterial).map;
        if (!map || this.paintedMaterials.has(material)) {
          continue;
        }
        let uniforms = this.paintTextures.get(map);
        if (!uniforms) {
          const url = paintMaskUrl(map);
          if (!url) {
            continue;
          }
          const paint = new PaintUniforms(this.colorUniforms, fce4);
          this.paintTextures.set(map, paint);
          new TextureLoader().load(
            url,
            mask => {
              if (this.disposed) {
                mask.dispose();
                return;
              }
              // texels as they are: the alpha is the paint index
              mask.flipY = map.flipY;
              mask.magFilter = NearestFilter;
              mask.minFilter = NearestFilter;
              mask.generateMipmaps = false;
              mask.needsUpdate = true;
              paint.mask.value = mask;
              paint.enabled.value = 1;
            },
            undefined,
            // no paint mask: the texture is not painted
            () => {},
          );
          uniforms = paint;
        }
        paintInShader(material, uniforms);
        this.paintedMaterials.add(material);
      }
    });
  }

  private updateColorUniforms() {
    this.colors.forEach((c, i) => {
      if (this.version === 3) {
        this.colorUniforms.value[i]?.set(c.hue, c.saturation, c.brightness, c.transparency);
      } else {
        const rgb = fceColorToRgb(c);
        this.colorUniforms.value[i]?.set(rgb >> 16, (rgb >> 8) & 0xff, rgb & 0xff, 0);
      }
    });
  }

  /** Color of light dummy, null if dummy is not a light */
  private static lightColor(version: FceVersion, name: string): number | null {
    const kind = name.toUpperCase();
    if (version === 4) {
      // FCE4: special dummies start with ":" (license plate, smoke, water), lights have color as 2nd letter
      if (kind.startsWith(':')) {
        return null;
      }
      const color = { W: 0xffffcc, R: 0xff0000, B: 0x0000ff, O: 0xff8000, Y: 0xffff00 }[kind[1]];
      return color === undefined ? 0xff00ff : color;
    }
    // FCE3: light kind is the first letter: H - headlight, T - taillight, M - siren (with side as 3rd letter)
    if (kind.startsWith('H')) {
      return 0xffffcc;
    } else if (kind.startsWith('T')) {
      return 0xff0000;
    } else if (kind.startsWith('M')) {
      return kind[2] === 'L' ? 0xff0000 : 0x0000ff;
    }
    return 0xff00ff;
  }

  private updateWheels() {
    for (const { meshes, isFront, spins } of this.wheels) {
      for (const m of meshes) {
        m.rotation.set(spins ? this.spinAngle : 0, 0, isFront ? this._steeringAngle : 0);
      }
    }
  }

  dispose() {
    this.disposed = true;
    if (this.animationTimer) {
      clearInterval(this.animationTimer);
      this.animationTimer = null;
    }
    for (const paint of this.paintTextures.values()) {
      paint.enabled.value = 0;
      paint.mask.value?.dispose();
      paint.mask.value = null;
    }
  }
}
