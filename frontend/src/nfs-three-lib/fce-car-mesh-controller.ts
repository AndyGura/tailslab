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
  Scene,
  SphereGeometry,
  SRGBColorSpace,
  Texture,
  TextureLoader,
  Vector3,
  Vector4,
  WebGLRenderer,
} from 'three';
import { sceneSkyCube, sceneSkyTopColor, sceneTrackLight } from './scene-sky';
import { Fce4CarParts, Fce4CarPartsOptions, fce4PartOf } from './fce4-car-parts';

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
 * nfs4.exe 0x4edf60: 0xRRGGBB to HSB (hue, saturation, brightness), every component 0..255, the exe's integer math:
 * brightness = max, saturation = delta * 256 / max (truncated), the hue as 16.16 sectors (sector * 2 + (c1 - c2) /
 * delta, its integer part and fraction each truncated) / 6 (truncated), + 1 turn when negative, then * 256 rounded
 * (bit 15); each clamped to 0..255. A grey (delta 0) or black has hue and saturation 0
 */
export const fce4RgbToHsb = (rgb: number): [number, number, number] => {
  const [r, g, b] = [(rgb >> 16) & 0xff, (rgb >> 8) & 0xff, rgb & 0xff];
  const max = Math.max(r, g, b);
  const delta = max - Math.min(r, g, b);
  const clamp = (c: number) => Math.max(0, Math.min(255, c));
  if (max === 0 || delta === 0) {
    return [0, 0, clamp(max)];
  }
  const [x, base] = r === max ? [g - b, 0] : g === max ? [b - r, 0x20000] : [r - g, 0x40000];
  let hue = Math.trunc(x / delta) * 0x10000 + Math.trunc(((x % delta) * 0x10000) / delta) + base;
  hue = Math.trunc(hue / 6);
  if (hue < 0) {
    hue += 0x10000;
  }
  return [clamp(Math.floor((hue * 256 + 0x8000) / 0x10000)), clamp(Math.trunc((delta * 256) / max)), clamp(max)];
};

/** nfs4.exe 0x439880: the track light off any road polygon (and of a wheel on none, Render_CarTrackLight) */
export const FCE4_DEFAULT_TRACK_LIGHT = 0x7f7f7f;

/**
 * nfs4.exe Render_CarTrackLight 0x50dc00: a race car's track light (car+0x98c) as 0xRRGGBB, per channel the mean
 * (sum >> 2) of the track light (0x439880, SceneTrackLight) under its 4 wheels (front left, front right, rear left,
 * rear right: the road polygons of car+0x328, +0x378, +0x3c8, +0x418); a wheel on none (null, or missing)
 * FCE4_DEFAULT_TRACK_LIGHT. SKIPPED: at night (0x7c4cf8) for a car nearer than 100 (car+0x908), 0x50c580 and 0x50c200
 * add the headlights of the cars nearby and the lights of the track to it
 */
export const fce4CarTrackLight = (wheels: (number | null)[]): number => {
  const lights = [0, 1, 2, 3].map(i => wheels[i] ?? FCE4_DEFAULT_TRACK_LIGHT);
  return [16, 8, 0].reduce(
    (rgb, shift) => rgb | ((lights.reduce((sum, c) => sum + ((c >> shift) & 0xff), 0) >> 2) << shift),
    0,
  );
};

/**
 * nfs4.exe Render_CarChrome 0x50d6f0: the vertex colours of a race car's chrome pass, 0xAARRGGBB (unsigned), the exe's
 * integer math (all values 0..255):
 * - `trackLight` 0xRRGGBB: the car's track light (car+0x98c, fce4CarTrackLight),
 * - `skyTop` 0xRRGGBB: the track's sky top colour (0x7c8b64..66, Tr.ini [strip] hrzSkyTopColor; SCENE_SKY_TOP_COLOR),
 * - `paintBrightness`: the HSB brightness of the car's paint (car+0xa28: fce4RgbToHsb of the game setup car's paint
 *   when the car is loaded, 0x508770),
 * - `coveredSlices`: 0 on an open road (car+0x910 0), else 1..8: the count of the loop over the road slices on both
 *   sides of the car's slice (BWorld_SliceCovered 0x4399d0: from 1, up while slice + n and slice - n are covered).
 *
 * Covered, f1 = 256 - 16 n and f2 = 256 - 32 n: each sky channel is blended towards the track light, ((256 - f2) light
 * >> 8) + (sky f2 >> 8). Of the sky's HSB (h, s, v) and the track light's brightness b: "normal" = HSB->RGB(h, s * 96
 * >> 8, (v b >> 9) + 0x80 - (paintBrightness >> 2)), "high" (the high_chrome triangles) = HSB->RGB(h, s >> 1, (v b >>
 * 9) + 0x80), hue and saturation clamped to 0..255, the brightness to 0x7f..0xff, which is the colour's alpha too
 * (HSB->RGB: nfs4.exe 0x4ee210, nfs3.exe 0x49ca50's code, fce3HsbToRgb). Covered, every byte of both colours, the
 * alpha too, is then scaled by f1 (c f1 >> 8, 0x50db59). CarDraw_SetChromeColors 0x4f0350 stores them for
 * CarDraw_QueuePolys 0x4f0a70 (0x5bcffc normal, 0x5bd008 high)
 */
export const fce4ChromeColors = (
  trackLight: number,
  skyTop: number,
  paintBrightness: number,
  coveredSlices: number,
): { normal: number; high: number } => {
  const n = Math.max(0, Math.min(8, Math.trunc(coveredSlices)));
  const f1 = n ? 256 - 16 * n : 256;
  const f2 = n ? 256 - 32 * n : 256;
  const channels = (c: number) => [(c >> 16) & 0xff, (c >> 8) & 0xff, c & 0xff];
  const light = channels(trackLight);
  const lightBrightness = fce4RgbToHsb(trackLight)[2];
  const sky = channels(skyTop).map((c, i) => (n ? (((256 - f2) * light[i]) >> 8) + ((c * f2) >> 8) : c));
  const [h, s, v] = fce4RgbToHsb((sky[0] << 16) | (sky[1] << 8) | sky[2]);
  const clamp = (x: number, min: number, max: number) => Math.max(min, Math.min(max, x));
  const color = (saturation: number, brightness: number) => {
    const b = clamp(brightness, 0x7f, 0xff);
    const rgb = fce3HsbToRgb({
      hue: clamp(h, 0, 255),
      saturation: clamp(saturation, 0, 255),
      brightness: b,
      transparency: 0,
    });
    const argb = [b, ...rgb].map(c => (f1 < 256 ? (c * f1) >> 8 : c));
    return ((argb[0] << 24) | (argb[1] << 16) | (argb[2] << 8) | argb[3]) >>> 0;
  };
  const brightness = ((v * lightBrightness) >> 9) + 0x80;
  return { normal: color((s * 96) >> 8, brightness - (paintBrightness >> 2)), high: color(s >> 1, brightness) };
};

/**
 * nfs3.exe 0x49cc50 (nfs4.exe Car_PaintTexel 0x4ee550 the same): the paint of a car texel, 0..255 RGB before the exe's
 * reduction to 5 bits. The texel's blue channel (5 bits, << 3) shades the color's brightness: brightness * blue /
 * (255 - transparency) (transparency 255: brightness * blue), truncated, at most 255; float32 as the exe stores the
 * factor
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

/**
 * nfs4.exe Fce_NearestColorSet 0x4ef310: the index of the FCE4 color set whose primary color is the nearest (RGB
 * distance, fce3HsbToRgb) to the chosen color; its interior, secondary and driver hair colors paint the car with it
 */
export const fce4NearestColorSet = (primaries: FceColor[], chosen: FceColor): number => {
  const [r, g, b] = fce3HsbToRgb(chosen);
  let nearest = 0;
  let distance = 1000;
  primaries.forEach((color, i) => {
    const [cr, cg, cb] = fce3HsbToRgb(color);
    const d = Math.fround(Math.hypot(cr - r, cg - g, cb - b));
    if (d < distance) {
      nearest = i;
      distance = d;
    }
  });
  return nearest;
};

// FCE3: part indices of car.fce wheels, by LOD. Order: front left, front right, rear left, rear right
const FCE3_HIGH_POLY_WHEELS = [1, 2, 3, 4];
const FCE3_MEDIUM_POLY_WHEELS = [7, 6, 9, 8];

// FCE4: car.fce wheel part name: high/medium LOD, left/right, front/middle/rear
const FCE4_WHEEL_REGEX = /^(?:hp|mp)_\d+_[HM]([LR])([FMR])W(?=__|_|$)/i;
// FCE4: front brakes steer together with wheels, but don't spin
const FCE4_BRAKE_REGEX = /^hp_\d+_O([LR])B(?=__|_|$)/i;

// nfs3.exe, nfs4.exe: wheel spin steps per second (one per sim tick)
const FCE_WHEEL_TICKS_PER_SECOND = 64;

/** nfs4.exe 0x50bbb0 / 0x50bdd0: a damaged wheel (car+0x568.. 0..1) tilts 0.025 turn per unit about the forward axis */
const FCE4_WHEEL_DAMAGE_TILT = 0.025 * 2 * Math.PI;

/** Wheel places: FCE3 wheels 1..4 / 6..9, FCE4 ":H<L|R><F|R>W" (the middle wheels ":H<L|R>MW" follow the rear ones) */
export type FceWheelPosition = 'frontLeft' | 'frontRight' | 'rearLeft' | 'rearRight';

/**
 * nfs3.exe 0x4b9140 (front wheels) / 0x4b9280 (rear wheels): the spin of a wheel in one sim tick (1/64 s), in turns,
 * positive rolls forward: 0.25 * clamp(speed / 30, -0.5, 0.5), so at most 8 turns per second (from 15 m/s on); the
 * rear wheels with the handbrake (car+0x50d) at most +-0.05 * 0.25. The speed is the car's forward speed in m/s
 * (car+0x4f4). SKIPPED: + 0.1 to the clamped value of the front wheels with car+0x598 set, of the rear ones at the
 * rev limiter (car+0x594), the random up and down offset of the wheels (0x4b90e0, car+0x930).
 * nfs4.exe the same (0x50bbb0 front, 0x50bdd0 rear: forward speed car+0x43c, handbrake car+0x455; SKIPPED: its + 0.1
 * before the clamp with car+0x4e8 / the rev limiter car+0x4e4), but a sliding wheel pair does not turn (car+0x4ec
 * bit 0 front, bit 1 rear: FceCarMeshController.frontSliding / rearSliding)
 */
export const fce3WheelSpinStep = (speed: number, isFront: boolean, handbrake: boolean): number => {
  const limit = !isFront && handbrake ? 0.05 : 0.5;
  return 0.25 * Math.max(-limit, Math.min(limit, speed / 30));
};

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
 * sync with fcePaint in the fragment shader. FCE3 as nfs3.exe 0x49cd00: 1..127 primary, 128..254 secondary. FCE4 as
 * nfs4.exe Car_PaintTexture 0x4ee620: 0xc4..0xfe primary, 0x80..0xc3 interior, 0x40..0x7f secondary, 1..0x3f driver
 * hair. Alpha 0 is a transparent texel, never painted
 */
export const fcePaintIndexOfAlpha = (version: FceVersion, alpha: number): number => {
  if (alpha === 0 || alpha === 255) {
    return -1;
  }
  if (version === 3) {
    return alpha < 0x80 ? 0 : 1;
  }
  return alpha >= 0xc4 ? 0 : alpha >= 0x80 ? 1 : alpha >= 0x40 ? 2 : 3;
};

/**
 * nfs4.exe Car_PaintTexture 0x4ee620: a texel of car00.tga (RGB, its alpha) as the game draws it, 0..255 RGB: painted
 * by fce3PaintColor with the color of its alpha (fcePaintIndexOfAlpha, `colors`: primary, interior, secondary, driver
 * hair), then every channel reduced to 5 bits (the 16-bit 1555 texture) as FCE3
 */
export const fce4TexelColor = (rgb: [number, number, number], alpha: number, colors: FceColor[]): number[] => {
  const index = fcePaintIndexOfAlpha(4, alpha);
  const painted = index >= 0 && colors[index] ? fce3PaintColor(rgb[2], colors[index]) : rgb;
  return painted.map(c => Math.round(((c >> 3) * 255) / 31));
};

/** Uniforms of one texture: its paint mask, and the controller's paints */
class PaintUniforms {
  readonly mask: { value: Texture | null } = { value: null };
  readonly enabled = { value: 0 };

  constructor(
    /** hue, saturation, brightness, transparency */
    readonly colors: { value: Vector4[] },
    readonly fce4: { value: number },
  ) {}
}

/**
 * The material paints its texels in the fragment shader (reading a canvas back gets noise from anti-fingerprinting),
 * as fce3TexelColor / fce4TexelColor. Each texel is painted before filtering: with a nearest filter the sample
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
          // fcePaintIndexOfAlpha; every texel of the texture goes through the 16-bit texture (fce3TexelColor,
          // fce4TexelColor)
          if ( alpha > 0.0 && alpha < 255.0 ) {
            int index = fcePaintFce4 < 0.5 ? ( alpha < 128.0 ? 0 : 1 )
              : alpha >= 196.0 ? 0 : alpha >= 128.0 ? 1 : alpha >= 64.0 ? 2 : 3;
            texel = fce3PaintColor( texel.b, fcePaintColors[ index ] );
          }
          vec3 painted = floor( floor( texel / 8.0 ) * 255.0 / 31.0 + 0.5 );
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
 * "fceChrome" extras); its alpha is the same value as its grey. SKIPPED: both are scaled by [0x6fbc38] when it is
 * below 1 (hardware renderers)
 */
const FCE3_CHROME_COLORS = { normal: 0x7f / 255, high: 1 };

/**
 * One chrome pass color added over the framebuffer, 0..255: the chrome texel (ARGB4444, texture type 7 of the
 * Direct3D driver D3DA.DLL: every channel 8 bits >> 4, shown as c / 15) times the vertex color, alpha included: D3DA.DLL
 * sets D3DRENDERSTATE_TEXTUREMAPBLEND to D3DTBLEND_MODULATEALPHA (texture x vertex, for the alpha too) with the device
 * (0x6000410c) and never changes it; blended with source alpha and one (THRASH state 0x68 = 1). The vertex color
 * (FCE3_CHROME_COLORS) is a grey with the same alpha: texel.rgb x c x texel.a x c. The reduction of the SKY.FSH texel to
 * 4 bits is assumed (the exe's 32-bit to 4444 conversion is not verified)
 */
export const fce3ChromeAdd = (texel: [number, number, number, number], vertexColor: number): number[] => {
  const [r, g, b, a] = texel.map(c => (c >> 4) / 15);
  return [r, g, b].map(c => c * vertexColor * a * vertexColor * 255);
};

/**
 * One FCE4 chrome pass color added over the framebuffer, 0..255: the chrome texel (as fce3ChromeAdd's, 4 bits) times
 * the vertex color 0xAARRGGBB (fce4ChromeColors), alpha included: nfs4.exe draws the pass with THRASH state 0x68 = 1
 * (source alpha, one; its Direct3D driver d3da.dll THRASH_setstate 0x600044d6), texture stage 0 as THRASH_treset sets
 * it (the game never sets state 0x29): COLOROP and ALPHAOP MODULATE (texture x diffuse) with
 * D3DPTBLENDCAPS_MODULATEALPHA, which every card has. So texel.rgb x color.rgb x texel.a x color.a.
 * SKIPPED: the reduction of nfs4.exe's sky.qfs CHRD texel (assumed 4 bits, as NFS3); SELECTARG1 for the alpha
 * without MODULATEALPHA
 */
export const fce4ChromeAdd = (texel: [number, number, number, number], color: number): number[] => {
  const [r, g, b, a] = texel.map(c => (c >> 4) / 15);
  const [ca, cr, cg, cb] = [24, 16, 8, 0].map(shift => ((color >>> shift) & 0xff) / 255);
  return [r * cr, g * cg, b * cb].map(c => c * a * ca * 255);
};

/**
 * FCE4: the parts nfs4.exe draws the chrome pass over (Render_CarParts 0x50dd60: CarDraw_Part 0x4f0e00 with
 * Render_CarChrome's texture, the part names of the tables 0x5bed14..; only for body LOD 0..2, so never :TB). Not
 * the wheels, brakes, driver (:OD, :OH, :OND: CarDraw_PartNoChrome 0x4f1120). TailsLab's FCE4_CHROME_PARTS
 */
const FCE4_CHROME_PARTS = ['HB', 'MB', 'LB', 'OC', 'ODL', 'OLM', 'ORM', 'OS', 'OT', 'OL'];

/**
 * The chrome class of a mesh (TailsLab's FCE3 / FCE4 export): its node extras `fceChrome` ("normal", "high", "none"),
 * else its name's suffix before the FCE4 window class: "_matte" none, "_high_chrome" high, else normal
 */
export const fceChromeClassOf = (mesh: Object3D): string => {
  const kind = mesh.userData?.['fceChrome'];
  if (typeof kind === 'string') {
    return kind;
  }
  const name = mesh.name.replace(/_damaged$/, '').replace(/_window(?:_(?:front|left|back|right))*(?:_breakaway)?$/, '');
  return /_matte$/.test(name) ? 'none' : /_high_chrome$/.test(name) ? 'high' : 'normal';
};

/**
 * The alpha of the chrome texel of a direction of the scene's sky (no texture alpha there), by the direction's height
 * (unit vector, up = 1): the game's CHR* textures of SKY.FSH reflect the sky with an alpha of 0.4..1 (0.6 in most
 * tracks) and the ground with about 0, the horizon in between
 */
export const fce3SkyChromeAlpha = (up: number): number => {
  const t = Math.max(0, Math.min(1, (up + 0.1) / 0.2));
  return 0.6 * t * t * (3 - 2 * t);
};

/** Chrome pass sources: none, a sphere map of the game (CHRD), the scene's sky (a cube texture) */
const enum ChromeMode {
  OFF = 0,
  SPHERE_MAP = 1,
  SKY = 2,
}

/** Uniforms of the chrome pass of one car, shared by its chrome materials */
class ChromeUniforms {
  // the vertex color of each class (0..1 RGBA): FCE3 FCE3_CHROME_COLORS (alpha = grey), FCE4 fce4ChromeColors
  readonly colors = {
    normal: {
      value: new Vector4(
        FCE3_CHROME_COLORS.normal,
        FCE3_CHROME_COLORS.normal,
        FCE3_CHROME_COLORS.normal,
        FCE3_CHROME_COLORS.normal,
      ),
    },
    high: { value: new Vector4(1, 1, 1, 1) },
  };
  readonly map: { value: Texture | null } = { value: null };
  readonly cube: { value: Texture | null } = { value: null };
  readonly mode = { value: ChromeMode.OFF };
  // mesh normal (local axes of the GLB / OBJ: x, y forward, z up) to the environment matrix space
  readonly matrix = { value: new Matrix3() };
  // mesh normal to the world, unit direction from the car to the camera in the world
  readonly worldMatrix = { value: new Matrix3() };
  readonly eye = { value: new Vector3(0, 0, 1) };
  // world direction to the direction to look up in the cube texture, as three.js draws it as a background
  readonly cubeMatrix = { value: new Matrix3() };
}

/**
 * The chrome pass of nfs3.exe (Render_CarPolyList 0x434120, a second pass of every body triangle but matte ones) and
 * nfs4.exe (the FCE4_CHROME_PARTS), added in the fragment shader of the material over its own color: texture
 * coordinates per vertex from the game's normal (`_game_normal`, else `normal`), the chrome texel times the class's
 * vertex color (`color`, a uniform of ChromeUniforms.colors) as fce3ChromeAdd / fce4ChromeAdd (alpha included), added in the
 * output color space (the game blends in the framebuffer's), divided by the fragment's alpha (or premultiplied) so
 * that blending adds it whole. Sky mode (ChromeMode.SKY): the texel is the scene's sky cube texture in the direction
 * the normal reflects the camera's direction to (per vertex, interpolated, as the game's coordinates), alpha
 * fce3SkyChromeAlpha, reduced to 4 bits as the game's texture
 */
function chromeInShader(material: Material, uniforms: ChromeUniforms, color: { value: Vector4 }, gameNormals: boolean) {
  const previous = material.onBeforeCompile;
  const previousKey = material.customProgramCacheKey;
  material.onBeforeCompile = (shader, renderer) => {
    previous.call(material, shader, renderer);
    shader.uniforms['fceChromeMap'] = uniforms.map;
    shader.uniforms['fceChromeCube'] = uniforms.cube;
    shader.uniforms['fceChromeMode'] = uniforms.mode;
    shader.uniforms['fceChromeMatrix'] = uniforms.matrix;
    shader.uniforms['fceChromeWorldMatrix'] = uniforms.worldMatrix;
    shader.uniforms['fceChromeEye'] = uniforms.eye;
    shader.uniforms['fceChromeCubeMatrix'] = uniforms.cubeMatrix;
    shader.uniforms['fceChromeColor'] = color;
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
        uniform mat3 fceChromeWorldMatrix;
        uniform vec3 fceChromeEye;
        uniform float fceChromeFlipY;
        varying vec2 vFceChromeUv;
        varying vec3 vFceChromeReflect;`,
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
        }
        vec3 fceChromeWorldNormal = normalize( fceChromeWorldMatrix * ${gameNormals ? '_game_normal' : 'normal'} );
        vFceChromeReflect = reflect( -fceChromeEye, fceChromeWorldNormal );`,
      );
    shader.fragmentShader = shader.fragmentShader
      .replace(
        '#include <fog_pars_fragment>',
        `#include <fog_pars_fragment>
        uniform sampler2D fceChromeMap;
        uniform samplerCube fceChromeCube;
        uniform mat3 fceChromeCubeMatrix;
        uniform float fceChromeMode;
        uniform vec4 fceChromeColor;
        uniform float fceChromeFiltered;
        uniform float fceChromeSrgb;
        varying vec2 vFceChromeUv;
        varying vec3 vFceChromeReflect;
        // a texel of the 4444 chrome texture, 0..1
        vec4 fceChromeTexel( ivec2 c ) {
          vec4 t = texelFetch( fceChromeMap, c, 0 );
          if ( fceChromeSrgb > 0.5 ) {
            t = vec4( sRGBTransferOETF( t ).rgb, t.a );
          }
          return floor( floor( t * 255.0 + 0.5 ) / 16.0 ) / 15.0;
        }
        // the scene's sky in a world direction as a 4444 chrome texel, 0..1 (linear texels to the output's sRGB)
        vec4 fceChromeSkyTexel( vec3 direction ) {
          vec3 d = normalize( direction );
          vec4 t = vec4(
            sRGBTransferOETF( vec4( textureCube( fceChromeCube, fceChromeCubeMatrix * d ).rgb, 1.0 ) ).rgb,
            // fce3SkyChromeAlpha
            0.6 * smoothstep( -0.1, 0.1, d.z ) );
          return floor( floor( clamp( t, 0.0, 1.0 ) * 255.0 + 0.5 ) / 16.0 ) / 15.0;
        }`,
      )
      .replace(
        '#include <premultiplied_alpha_fragment>',
        `#include <premultiplied_alpha_fragment>
        if ( fceChromeMode > 0.5 ) {
          vec4 env;
          if ( fceChromeMode > 1.5 ) {
            env = fceChromeSkyTexel( vFceChromeReflect );
          } else {
            ivec2 size = textureSize( fceChromeMap, 0 );
            ivec2 last = size - 1;
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
          }
          vec3 fceChromeAdd = env.rgb * fceChromeColor.rgb * env.a * fceChromeColor.a;
          #ifdef PREMULTIPLIED_ALPHA
          gl_FragColor.rgb += fceChromeAdd;
          #else
          gl_FragColor.rgb += fceChromeAdd / max( gl_FragColor.a, 1.0 / 255.0 );
          #endif
        }`,
      );
  };
  material.customProgramCacheKey = () => `${previousKey.call(material)}|fce-chrome-${gameNormals ? 'game' : 'normal'}`;
  material.needsUpdate = true;
}

/** FceCarMeshController's FCE4 options (Fce4CarParts) */
export type FceCarMeshOptions = Omit<Fce4CarPartsOptions, 'dummies'>;

type Wheel = {
  // one per texture (and the damaged copy of FCE3)
  meshes: Mesh[];
  isFront: boolean;
  spins: boolean;
  // FCE4: its place (middle wheels: the rear one of their side), the group that hides it
  position: FceWheelPosition | null;
  middle: boolean;
  group: Group | null;
};

/**
 * Animates car.fce model: steers and spins wheels, shows light dummies, paints the car in the fragment shader of its
 * materials (the textures stay as they are). Expects meshes, exported by Fce3GeometrySerializer/Fce4GeometrySerializer:
 * "<lod>_<part index>_<part name>[__<texture>][_damaged]". A texture is painted by its paint mask (`paintMaskUrl`, the
 * alpha channel of car00.tga, see fcePaintIndexOfAlpha; fce3TexelColor / fce4TexelColor, the whole texture as the
 * exe uploads it, at 5 bits per channel). Materials are changed in place:
 * a material shared with another copy of the model gets this controller's paint.
 * FCE4 (NFS4): `parts` draws the car's parts as nfs4.exe (pop-up headlights, roof, driver, spoiler, body lean,
 * damage), the wheels tilt when damaged (setWheelDamage), hide (setWheelHidden), stop while sliding.
 * Chrome (hasChrome): the exe's environment mapped second pass (chromeInShader), FCE3 on the body, FCE4 on the
 * FCE4_CHROME_PARTS with nfs4.exe's colours (fce4ChromeColors: the track light, the sky top colour, the paint)
 */
export class FceCarMeshController {
  private wheels: Wheel[] = [];
  private lights: Group | null = null;
  // light spheres by dummy index
  private readonly lightMeshes = new Map<number, Mesh>();

  /** FCE4: the parts nfs4.exe draws by the car's state (Fce4CarParts), null for FCE3 */
  readonly parts: Fce4CarParts | null = null;
  // spin of the front and the rear wheels, turns (positive rolls forward)
  private readonly spinTurns = { front: 0, rear: 0 };
  // paint uniforms by texture
  private readonly paintTextures = new Map<Texture, PaintUniforms>();
  private readonly paintedMaterials = new Set<Material>();
  private disposed = false;
  private readonly chrome = new ChromeUniforms();
  // meshes with a chrome pass: FCE3 body (part 0), FCE4 FCE4_CHROME_PARTS
  private readonly chromeMeshes: Mesh[] = [];

  /** Whether the model has meshes with chrome (FCE3 body, FCE4 FCE4_CHROME_PARTS: their triangles but matte ones) */
  get hasChrome(): boolean {
    return this.chromeMeshes.length > 0;
  }

  /** Whether the chrome pass is drawn (the game's "carchrome" option, NFS4 g_opt_car_chrome 0x7c3d38) */
  chromeEnabled = true;

  /**
   * The chrome (environment) texture as nfs3.exe draws it: the track's SKY.FSH `CHRD` (day; `CHRN` night, `CHRW` /
   * `CHNW` in the rain); nfs4.exe the same of the track's sky.qfs (Hrz_LoadSkyQfs). Null: the chrome reflects the sky
   * of the scene drawing the car (sceneSkyCube: the cube texture `scene.userData[SCENE_SKY_CUBE]`, else
   * `scene.background` when it is one, e.g. gg-web-engine's baked sky), no chrome without one. Not owned by the
   * controller
   */
  chromeTexture: Texture | null = null;

  /**
   * FCE4: the car's track light, 0xRRGGBB (nfs4.exe car+0x98c, FCE4_DEFAULT_TRACK_LIGHT off the road), the chrome
   * colours' light (fce4ChromeColors) when the scene drawing the car has no SceneTrackLight (SCENE_TRACK_LIGHT); with
   * one, the car's is fce4CarTrackLight of its wheels' places
   */
  chromeTrackLight = FCE4_DEFAULT_TRACK_LIGHT;

  /**
   * FCE4: the covered road slices around the car for the chrome colours (fce4ChromeColors `coveredSlices`): 0 on an
   * open road (nfs4.exe car+0x910 0), else 1..8
   */
  chromeCoveredSlices = 0;

  // FCE4: the wheel meshes fce4CarTrackLight reads the track light under (front left, front right, rear left, rear
  // right), and the renderer and frame the chrome colours were last computed for
  private readonly trackLightWheels: (Mesh | null)[] = [null, null, null, null];
  private chromeColorsFrame: { renderer: WebGLRenderer; frame: number } | null = null;

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
  /**
   * Car speed in m/s, the wheels spin at it (backwards when negative). Can be set every frame. As nfs3.exe and
   * nfs4.exe spin them (fce3WheelSpinStep)
   */
  get speed(): number {
    return this._speed;
  }

  set speed(value: number) {
    this._speed = value;
    this.updateAnimationTimer();
  }

  private _handbrake = false;
  /** The handbrake slows the rear wheels down (fce3WheelSpinStep) */
  get handbrake(): boolean {
    return this._handbrake;
  }

  set handbrake(value: boolean) {
    this._handbrake = value;
  }

  /** FCE4: the front wheels slide, they don't turn (nfs4.exe 0x50bbb0: car+0x4ec bit 0) */
  frontSliding = false;

  /** FCE4: the rear wheels slide, they don't turn (nfs4.exe 0x50bdd0: car+0x4ec bit 1) */
  rearSliding = false;

  // sim ticks of the spin done since the timer started, and that time (ms)
  private spinTicks = 0;
  private spinStart = 0;

  // the timer runs while the wheels spin
  private updateAnimationTimer() {
    if (!!this.animationTimer === (this._speed !== 0 && !this.disposed)) {
      return;
    }
    if (this.animationTimer) {
      clearInterval(this.animationTimer);
      this.animationTimer = null;
      return;
    }
    this.spinTicks = 0;
    this.spinStart = performance.now();
    this.animationTimer = setInterval(() => this.spinWheels(), 1000 / 60);
  }

  private spinWheels() {
    const ticks = Math.floor(((performance.now() - this.spinStart) * FCE_WHEEL_TICKS_PER_SECOND) / 1000);
    for (; this.spinTicks < ticks; this.spinTicks++) {
      for (const key of ['front', 'rear'] as const) {
        if (this.version === 4 && (key === 'front' ? this.frontSliding : this.rearSliding)) {
          continue;
        }
        const turns = this.spinTurns[key] + fce3WheelSpinStep(this._speed, key === 'front', this._handbrake);
        // wrapped to -1..1 as the exe
        this.spinTurns[key] = turns - Math.trunc(turns);
      }
    }
    this.updateWheels();
  }

  private _steeringAngle: number = 0;
  /** The front wheels' angle in radians, positive to the left (FCE4: the driver's steering wheel turns with them) */
  get steeringAngle(): number {
    return this._steeringAngle;
  }

  set steeringAngle(value: number) {
    this._steeringAngle = value;
    this.updateWheels();
    if (this.parts) {
      this.parts.steeringAngle = value;
    }
  }

  private readonly wheelDamage: { [position in FceWheelPosition]?: number } = {};
  private readonly wheelHidden: { [position in FceWheelPosition]?: boolean } = {};

  /**
   * FCE4: a wheel's damage 0..1 (nfs4.exe car+0x568 front left, +0x56c front right, +0x570 rear left, +0x574 rear
   * right) tilts it FCE4_WHEEL_DAMAGE_TILT per unit about the forward axis (0x50bbb0 / 0x50bdd0: RotZ before its spin,
   * so a bent wheel wobbles as it turns; the same way on both sides)
   */
  setWheelDamage(position: FceWheelPosition, damage: number) {
    this.wheelDamage[position] = damage;
    this.updateWheels();
  }

  /**
   * FCE4: a wheel not drawn, its front brake neither: Render_CarParts skips the wheels of car+0xa0c's bits (1 front
   * left, 2 front right, 4 rear right, 8 rear left), the tyres the spike strips hit (0x4496d0, pursuit; SKIPPED: what
   * the spike strip effects draw instead, 0x526d90). The middle wheels (Knoc's) go with the rear wheel of the other
   * side (the exe tests :HLMW with bit 4, :HRMW with bit 8)
   */
  setWheelHidden(position: FceWheelPosition, hidden: boolean) {
    this.wheelHidden[position] = hidden;
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
   * @param options FCE4: the data of `parts` (Fce4CarPartsOptions)
   */
  constructor(
    mesh: Object3D,
    private readonly version: FceVersion,
    dummies: FceDummy[],
    colors: FceColor[],
    paintMaskUrl: (texture: Texture) => string | null = fcePaintMaskNextToTexture,
    options: FceCarMeshOptions = {},
  ) {
    this.colors = colors.map(c => ({ ...c }));
    this.updateColorUniforms();
    this.root = mesh;
    if (version === 4) {
      // first: it takes the damaged copies out of the model
      this.parts = new Fce4CarParts(mesh, { ...options, dummies });
      this.parts.onDummyBroken = (index, broken) => {
        const light = this.lightMeshes.get(index);
        if (light) {
          light.visible = !broken;
        }
      };
    }
    // before the paint: the chrome meshes' own materials are painted too
    this.setupChrome(mesh);
    this.setupPaint(mesh, paintMaskUrl);
    // wheel meshes by part index
    const parts: { [index: number]: Wheel } = {};
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
      let wheel: Omit<Wheel, 'meshes' | 'group'> | null = null;
      if (version === 3) {
        for (const wheelIndices of [FCE3_HIGH_POLY_WHEELS, FCE3_MEDIUM_POLY_WHEELS]) {
          if (wheelIndices.includes(index)) {
            wheel = { isFront: wheelIndices.indexOf(index) < 2, spins: true, position: null, middle: false };
          }
        }
      } else {
        const wheelMatch = FCE4_WHEEL_REGEX.exec(o.name);
        const brakeMatch = FCE4_BRAKE_REGEX.exec(o.name);
        const left = (wheelMatch ?? brakeMatch)?.[1].toUpperCase() === 'L';
        if (wheelMatch) {
          const axle = wheelMatch[2].toUpperCase();
          wheel = {
            isFront: axle === 'F',
            spins: true,
            // the middle wheels: hidden with the rear wheel of the other side (setWheelHidden)
            position:
              axle === 'F' ? (left ? 'frontLeft' : 'frontRight') : left === (axle === 'R') ? 'rearLeft' : 'rearRight',
            middle: axle === 'M',
          };
        } else if (brakeMatch) {
          wheel = { isFront: true, spins: false, position: left ? 'frontLeft' : 'frontRight', middle: false };
        }
      }
      if (wheel) {
        (parts[index] = parts[index] || { meshes: [], group: null, ...wheel }).meshes.push(o);
      }
    });
    for (const [index, wheel] of Object.entries(parts)) {
      if (version === 4) {
        // shown and hidden through a group of its own: the meshes' `visible` stays the app's
        wheel.group = new Group();
        wheel.group.name = `wheel_${index}`;
        mesh.add(wheel.group);
        wheel.meshes.forEach(m => wheel.group!.attach(m));
      }
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
      const place = ['frontLeft', 'frontRight', 'rearLeft', 'rearRight'].indexOf(wheel.position ?? '');
      if (version === 4 && wheel.spins && !wheel.middle && place >= 0 && !this.trackLightWheels[place]) {
        this.trackLightWheels[place] = wheel.meshes[0];
      }
    }
    if (body && dummies.some(d => FceCarMeshController.lightColor(version, d.name) !== null)) {
      this.lights = new Group();
      dummies.forEach((dummy, i) => {
        const color = FceCarMeshController.lightColor(version, dummy.name);
        if (color === null) {
          return;
        }
        const light = new Mesh(new SphereGeometry(0.05, 8, 8), new MeshBasicMaterial({ color }));
        light.name = dummy.name;
        light.position.set(...dummy.position);
        light.visible = !this.parts?.brokenDummies.has(i);
        this.lightMeshes.set(i, light);
        this.lights!.add(light);
      });
      (body as Mesh).add(this.lights);
    }
    this.updateWheels();
  }

  private readonly root: Object3D;

  /**
   * Gives every chrome mesh but matte ones its own copies of its materials, with the chrome pass (shared materials: the
   * wheels and the other parts draw the same textures without it). FCE3: the body (part 0, high and medium level of
   * detail). FCE4: the FCE4_CHROME_PARTS of the high, medium and low levels. The class (fceChromeClassOf) picks the
   * vertex color uniform. SKIPPED: FCE4's chrome over cracked windows (Fce4CarParts' glass meshes)
   */
  private setupChrome(mesh: Object3D) {
    const meshes: Mesh[] = [];
    mesh.traverse(o => {
      if (o instanceof Mesh) {
        meshes.push(o);
      }
    });
    for (const o of meshes) {
      const part = this.version === 4 ? fce4PartOf(o.name) : null;
      const isChromePart =
        this.version === 3
          ? /^(hp|mp)_0(?:_|$)/.test(o.name)
          : !!part && /^(hp|mp|lp)_/.test(part.key) && FCE4_CHROME_PARTS.includes(part.name);
      if (!isChromePart) {
        continue;
      }
      const kind = fceChromeClassOf(o);
      const color = kind === 'normal' || kind === 'high' ? this.chrome.colors[kind] : undefined;
      if (color === undefined) {
        continue;
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
      // turned to every camera that draws it, before the draw of each mesh (the shown ones depend on the LOD)
      const previous = o.onBeforeRender;
      o.onBeforeRender = (renderer, scene, camera, ...rest) => {
        previous.call(o, renderer, scene, camera, ...rest);
        if (!this.disposed) {
          this.updateChrome(camera.getWorldPosition(this.cameraPosition), scene, o, renderer);
        }
      };
      this.chromeMeshes.push(o);
    }
  }

  private readonly cameraPosition = new Vector3();

  /**
   * Turns the chrome to the camera (CarDraw_SetupChrome 0x4ba350: the environment matrix from the camera's
   * direction, fce3ChromeEnvMatrix; nfs4.exe Render_CarChrome 0x50d6f0 -> CarDraw_SetEnvMatrix 0x4f02b0, the same
   * code) and picks its source (chromeTexture, else the sky of `scene`); FCE4: its colours too
   * (updateFce4ChromeColors), once per frame of `renderer` (every call without one). Called before a chrome mesh
   * (`mesh`, default the first one) is drawn, with the camera drawing it. The world is expected in TailsLab's export
   * axes (x, y = game z, z up = game y): the GLB / OBJ axes, nfs-web's world and TailsLab's viewers
   */
  updateChrome(cameraPosition: Vector3, scene?: Scene, mesh: Mesh = this.chromeMeshes[0], renderer?: WebGLRenderer) {
    const chrome = this.chrome;
    // the cube matrix as three.js turns a background cube texture (WebGLBackground)
    const sky = sceneSkyCube(scene, chrome.cubeMatrix.value);
    chrome.map.value = this.chromeTexture;
    chrome.cube.value = sky;
    chrome.mode.value =
      !mesh || !this.chromeEnabled
        ? ChromeMode.OFF
        : this.chromeTexture
          ? ChromeMode.SPHERE_MAP
          : sky
            ? ChromeMode.SKY
            : ChromeMode.OFF;
    if (chrome.mode.value === ChromeMode.OFF) {
      return;
    }
    if (this.version === 4) {
      const frame = renderer?.info.render.frame;
      const last = this.chromeColorsFrame;
      if (!renderer || frame === undefined || last?.renderer !== renderer || last.frame !== frame) {
        this.chromeColorsFrame = renderer && frame !== undefined ? { renderer, frame } : null;
        this.updateFce4ChromeColors(scene);
      }
    }
    this.root.updateWorldMatrix(true, false);
    mesh.updateWorldMatrix(true, false);
    const d = cameraPosition.clone().sub(new Vector3().setFromMatrixPosition(this.root.matrixWorld));
    const rotation = new Matrix3().setFromMatrix4(new Matrix4().extractRotation(mesh.matrixWorld));
    chrome.worldMatrix.value.copy(rotation);
    chrome.eye.value.copy(d).normalize();
    const e = fce3ChromeEnvMatrix([d.x, d.z, d.y]);
    // column vectors: env normal = Env^T (game normal), game normal = S (world normal), world normal = R (mesh normal)
    const envT = new Matrix3().set(e[0], e[3], e[6], e[1], e[4], e[7], e[2], e[5], e[8]);
    const swap = new Matrix3().set(1, 0, 0, 0, 0, 1, 0, 1, 0);
    chrome.matrix.value.copy(envT.multiply(swap).multiply(rotation));
  }

  private readonly wheelPosition = new Vector3();

  /**
   * FCE4: the chrome colour uniforms of fce4ChromeColors: the track light (the scene's SceneTrackLight at the wheels,
   * fce4CarTrackLight; without one chromeTrackLight), the scene's sky top colour (sceneSkyTopColor), the brightness of
   * the primary paint (fce4RgbToHsb of fce3HsbToRgb(colors[0]): nfs4.exe car+0xa28 from the paint's RGB),
   * chromeCoveredSlices
   */
  private updateFce4ChromeColors(scene: Scene | undefined) {
    const trackLight = sceneTrackLight(scene);
    let light = this.chromeTrackLight;
    if (trackLight) {
      light = fce4CarTrackLight(
        this.trackLightWheels.map(wheel => {
          if (!wheel) {
            return null;
          }
          const p = wheel.getWorldPosition(this.wheelPosition);
          return trackLight(p.x, p.y, p.z);
        }),
      );
    }
    const paint = this.colors[0];
    const [r, g, b] = paint ? fce3HsbToRgb(paint) : [0, 0, 0];
    const paintBrightness = fce4RgbToHsb((r << 16) | (g << 8) | b)[2];
    const colors = fce4ChromeColors(light, sceneSkyTopColor(scene), paintBrightness, this.chromeCoveredSlices);
    for (const kind of ['normal', 'high'] as const) {
      const c = colors[kind];
      this.chrome.colors[kind].value.set(
        ((c >>> 16) & 0xff) / 255,
        ((c >>> 8) & 0xff) / 255,
        (c & 0xff) / 255,
        ((c >>> 24) & 0xff) / 255,
      );
    }
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
    this.colors.forEach((c, i) => this.colorUniforms.value[i]?.set(c.hue, c.saturation, c.brightness, c.transparency));
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
    for (const { meshes, isFront, spins, position, middle, group } of this.wheels) {
      // a negative angle rolls the wheels forward
      const spin = spins ? -this.spinTurns[isFront ? 'front' : 'rear'] * 2 * Math.PI : 0;
      // FCE4: tilted by its damage before its spin (order ZXY: steering, spin, tilt), positive tilts the right up
      const damage = position && !middle && spins ? (this.wheelDamage[position] ?? 0) : 0;
      const tilt = damage ? -damage * FCE4_WHEEL_DAMAGE_TILT : 0;
      for (const m of meshes) {
        m.rotation.set(spin, tilt, isFront ? this._steeringAngle : 0);
      }
      if (group && position) {
        group.visible = !this.wheelHidden[position];
      }
    }
  }

  dispose() {
    this.disposed = true;
    this.parts?.dispose();
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
