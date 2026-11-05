import {
  Box3,
  Group,
  Material,
  Mesh,
  MeshBasicMaterial,
  NearestFilter,
  Object3D,
  SphereGeometry,
  Texture,
  TextureLoader,
  Vector3,
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

export type FceVersion = 3 | 4;

// FCE3: texture alpha of painted pixels: below this value it is primary color (car body), above it is secondary color
const FCE3_SECONDARY_COLOR_ALPHA_THRESHOLD = 160;

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
 * sync with fcePaint in the fragment shader (FCE4: the nearest of FCE4_COLOR_ALPHAS, the first one on a tie)
 */
export const fcePaintIndexOfAlpha = (version: FceVersion, alpha: number): number => {
  if (alpha === 0 || alpha === 255) {
    return -1;
  }
  if (version === 3) {
    return alpha < FCE3_SECONDARY_COLOR_ALPHA_THRESHOLD ? 0 : 1;
  }
  let result = 0;
  FCE4_COLOR_ALPHAS.forEach((value, i) => {
    if (Math.abs(alpha - value) < Math.abs(alpha - FCE4_COLOR_ALPHAS[result])) {
      result = i;
    }
  });
  return result;
};

/** Painted 0..255 sRGB channel: the texture is a greyscale shading of the paint, mid-grey is exactly the paint */
export const fcePaintChannel = (texel: number, paint: number): number =>
  Math.min(255, Math.round((texel * paint) / 128));

/** Uniforms of one texture: its paint mask, and the controller's paints */
class PaintUniforms {
  readonly mask: { value: Texture | null } = { value: null };
  readonly enabled = { value: 0 };

  constructor(
    readonly colors: { value: Vector3[] },
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
        uniform vec3 fcePaintColors[ 4 ];
        uniform float fcePaintFce4;
        uniform sampler2D fcePaintMask;
        uniform float fcePaintEnabled;
        uniform float fcePaintFiltered;
        vec4 fcePaint( vec4 sampled, vec2 uv ) {
          float alpha = floor( textureLod( fcePaintMask, uv, 0.0 ).a * 255.0 + 0.5 );
          if ( alpha == 0.0 || alpha == 255.0 ) {
            return sampled;
          }
          vec3 paint;
          if ( fcePaintFce4 < 0.5 ) {
            paint = alpha < ${FCE3_SECONDARY_COLOR_ALPHA_THRESHOLD}.0 ? fcePaintColors[ 0 ] : fcePaintColors[ 1 ];
          } else {
            paint = alpha >= ${(FCE4_COLOR_ALPHAS[0] + FCE4_COLOR_ALPHAS[1]) / 2}.0 ? fcePaintColors[ 0 ]
              : alpha >= ${(FCE4_COLOR_ALPHAS[1] + FCE4_COLOR_ALPHAS[2]) / 2}.0 ? fcePaintColors[ 1 ]
              : alpha >= ${(FCE4_COLOR_ALPHAS[2] + FCE4_COLOR_ALPHAS[3]) / 2}.0 ? fcePaintColors[ 2 ]
              : fcePaintColors[ 3 ];
          }
          vec3 texel = floor( sRGBTransferOETF( sampled ).rgb * 255.0 + 0.5 );
          vec3 painted = min( floor( texel * paint / 128.0 + 0.5 ), 255.0 );
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
 * Animates car.fce model: steers and spins wheels, shows light dummies, paints the car in the fragment shader of its
 * materials (the textures stay as they are). Expects meshes, exported by Fce3GeometrySerializer/Fce4GeometrySerializer:
 * "<lod>_<part index>_<part name>[__<texture>][_damaged]". A texture is painted where its paint mask
 * (`paintMaskUrl`, the alpha channel of car00.tga) has an alpha other than 0 and 255. Materials are changed in place:
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

  // FCE3: primary, secondary. FCE4: primary, interior, secondary, driver hair
  private readonly colors: number[];
  private readonly colorUniforms = { value: [new Vector3(), new Vector3(), new Vector3(), new Vector3()] };

  getColor(index: number): number {
    return this.colors[index];
  }

  setColor(index: number, value: number) {
    this.colors[index] = value;
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
    colors: number[],
    paintMaskUrl: (texture: Texture) => string | null = fcePaintMaskNextToTexture,
  ) {
    this.colors = [...colors];
    this.updateColorUniforms();
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
    this.colors.forEach((c, i) => this.colorUniforms.value[i]?.set(c >> 16, (c >> 8) & 0xff, c & 0xff));
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
