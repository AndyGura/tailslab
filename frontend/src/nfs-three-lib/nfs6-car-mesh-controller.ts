import {
  AdditiveBlending,
  Group,
  Material,
  Mesh,
  MeshBasicMaterial,
  NormalBlending,
  Object3D,
  SphereGeometry,
  SRGBColorSpace,
  Texture,
  TextureLoader,
  Vector3,
} from 'three';

export type Nfs6CarDummy = { name: string; position: [number, number, number] };

/** Specular lighting of a skin: the keys of its vehicle.ini section, as read by NFSHP2.exe 0x42f240 */
export type Nfs6CarSkinSpecular = {
  // 0..255
  specular_red?: number;
  specular_green?: number;
  specular_blue?: number;
  specular_paint_exponent?: number;
  specular_glass_exponent?: number;
  specular_rubber_exponent?: number;
  // 0..255, the share of the sun's color in the paint's specular color
  specular_sun_intensity?: number;
};

export type Nfs6CarSkin = { name: string; label: string; texture: string; specular?: Nfs6CarSkinSpecular | null };

/** A track location's lighting.ini (colors 0..255, sun position in the track's axes: x, y up, z) */
export type Nfs6Location = {
  name: string;
  ambient_sky: [number, number, number];
  ambient_ground: [number, number, number];
  sun: [number, number, number];
  sun_position: [number, number, number];
  // staticenvmap.fsh of the location, relative to the export folder
  environment_map?: string | null;
};

/** "lighting.json" of EaglModelSerializer's car export */
export type Nfs6CarLighting = {
  vehicle_type?: string | null;
  specular_hotspot_exponent?: number | null;
  // Cars/common.fsh "refl", the frontend's environment map
  environment_map?: string | null;
  locations?: Nfs6Location[];
};

/** Microcode of a car mesh: EASVehiclePaint, EASVehicleRubber, EASVehicleGlass, EASVehicleGeneric */
export type Nfs6CarShader = 'paint' | 'rubber' | 'glass' | 'generic';

export type Nfs6CarBlend = 'opaque' | 'trans' | 'add';

/** Mesh properties of the export ("<obj>_extra.json" objects, GLB node extras) */
export type Nfs6CarMeshProperties = {
  eaglShader?: Nfs6CarShader;
  eaglBlend?: Nfs6CarBlend;
  // glass: the vertex alpha, for an OBJ (no vertex alpha there)
  eaglVertexAlpha?: number;
};

// wheel radius (m) for the spin rate at a speed
const WHEEL_RADIUS = 0.33;

// geometry names of wheels ("ALPHA_OPAQUE_RUBBER_1Shape", "ALPHA_OPAQUE_RUBBER_LOD_WHEEL_2Shape") and brake calipers
// ("ALPHA_OPAQUE_BRAKE_3Shape"). Which wheel is which is not in the name, it is taken from the mesh position
const NFS6_WHEEL_REGEX = /^(?:hp|mp|lp)_\d+_\w*RUBBER/i;
const NFS6_BRAKE_REGEX = /^(?:hp|mp|lp)_\d+_\w*BRAKE/i;

// skeleton bones, drawn as lights
const NFS6_LIGHT_COLORS: [RegExp, number][] = [
  [/^LIGHT_TAIL/i, 0xff0000],
  [/^LIGHT_REVERSE/i, 0xffffff],
  [/^LIGHT_HEAD/i, 0xffffcc],
  [/^LIGHT_(?:COP|SIREN)/i, 0x0000ff],
];

/**
 * Lighting of tracks/Parkland/lighting.ini (the same in every level), for a car exported without "lighting.json"
 */
export const NFS6_DEFAULT_LOCATION: Nfs6Location = {
  name: 'Parkland',
  ambient_sky: [186, 181, 168],
  ambient_ground: [63, 65, 59],
  sun: [255, 254, 248],
  sun_position: [782.69, 3489.32, 6281.44],
};

/**
 * gVehicleStandardConstants (NFSHP2.exe 0x412f00): (0, 0.5, 1, 0.4). w: how much the vertex position (model space, m)
 * bends the normal of the environment map lookup
 */
export const NFS6_NORMAL_BEND = 0.4;

/** gSphereMapScale (0x412f00): 0.85; gSphereMapConstants: 0.5 */
export const NFS6_SPHERE_MAP_SCALE = 0.85;

/**
 * D3D vertex shader `lit` (z): the specular factor of a vertex, n.h raised to the power (clamped to +-127.9961), 0
 * when n.h <= 0
 */
export const nfs6Lit = (nh: number, power: number): number => {
  const p = Math.max(-127.9961, Math.min(127.9961, power));
  return nh > 0 ? Math.pow(nh, p) : 0;
};

/**
 * The environment map normal of the EASVehicle* vertex shaders: normalize(n + 0.4 * (p - gGlossColourConstants.xyz)),
 * model space (gGlossColourConstants = (0, 0, 0, 1), 0x412f00), so the reflection bends over the car as over a ball
 */
export const nfs6BentNormal = (
  normal: [number, number, number],
  position: [number, number, number],
): [number, number, number] => {
  const b = normal.map((n, i) => n + NFS6_NORMAL_BEND * position[i]);
  const length = Math.hypot(...b) || 1;
  return b.map(c => c / length) as [number, number, number];
};

/**
 * Sphere map texture coordinates (D3D's: v = 0 is the top row) of the bent normal in view space (EAGL's view space:
 * x right, y up, looking at -z, the same as three.js): 1 - (n.xy * 0.85 * 0.5 + 0.5). Per vertex (oT1), interpolated
 */
export const nfs6SphereMapUv = (viewNormal: [number, number, number]): [number, number] => [
  1 - (viewNormal[0] * NFS6_SPHERE_MAP_SCALE * 0.5 + 0.5),
  1 - (viewNormal[1] * NFS6_SPHERE_MAP_SCALE * 0.5 + 0.5),
];

/**
 * Vertex color of the paint, rubber and generic microcodes (oD0, every component 0..1): the hemisphere light,
 * gAmbientGround to gAmbientSky by the world normal's height (`up`: n.y in the game, -1..1), at most 1. lighting.ini
 * [ambientsky] / [ambientground] / 255 (0x5430f0). There is no sun diffuse light
 */
export const nfs6HemisphereAmbient = (
  up: number,
  sky: [number, number, number],
  ground: [number, number, number],
): [number, number, number] => {
  const t = up * 0.5 + 0.5;
  return [0, 1, 2].map(i => Math.min(1, (t * sky[i] + (1 - t) * ground[i]) / 255)) as [number, number, number];
};

/**
 * gPaintSpecularColour (0x412f00, 0x431d30): specular_sun_intensity / 255 * sun color / 255 + specular_red / green /
 * blue / 255, every component at most 1. A missing key counts 0
 */
export const nfs6PaintSpecular = (
  specular: Nfs6CarSkinSpecular | null | undefined,
  sun: [number, number, number],
): [number, number, number] => {
  const s = specular || {};
  const intensity = (s.specular_sun_intensity ?? 0) / 255;
  return [s.specular_red, s.specular_green, s.specular_blue].map((c, i) =>
    Math.min(1, (intensity * sun[i]) / 255 + (c ?? 0) / 255),
  ) as [number, number, number];
};

/**
 * gVehicleLightConstants.x (0x412f00): the car's light level (car+0x81c: the light bytes of the road under the car /
 * 255, 0x432330, 0x43b600), at least 0.4. The pixel shaders multiply the whole color by it
 */
export const nfs6Brightness = (lightLevel: number): number => Math.max(lightLevel, 0.4);

/**
 * gHotSpecularColour (0x413670), when it has settled: the paint's specular color towards white (racers and cops:
 * car+0x970 = 1; traffic: 0) by the light level + 0.2 (at most 1), not at all when the light level is 0.2 or less.
 * SKIPPED: the target moves 0.1 per frame (0x4137b0), 0 in the frontend
 */
export const nfs6HotSpecular = (
  paintSpecular: [number, number, number],
  lightLevel: number,
  traffic: boolean,
): [number, number, number] => {
  const t = lightLevel > 0.2 ? Math.min(1, lightLevel + 0.2) : 0;
  const target = traffic ? 0 : 1;
  return paintSpecular.map(c => (target - c) * t + c) as [number, number, number];
};

/**
 * One pixel of the EASVehicle* pixel shaders (ps.1.1, EAGL/eaglrm.o, technique 0 of slot 0), every component 0..1,
 * each instruction clamped as the ps.1.1 registers are: t0 the texture (its alpha is the reflection mask), t1 the
 * environment map, d0 / d1 the vertex colors (d1.a the brightness). rgb = (d0 * t0 + t0.a * t1 + t0.a * d1) * d1.a;
 * alpha: glass the vertex alpha (d0.a), the others are opaque. The paint's damage texture (t2, lerp by the damage
 * zone in d0.a) is left out: an undamaged car
 */
export const nfs6PixelColor = (
  t0: [number, number, number, number],
  t1: [number, number, number],
  d0: [number, number, number, number],
  d1: [number, number, number, number],
  glass: boolean,
): [number, number, number, number] => {
  const sat = (x: number) => Math.max(0, Math.min(1, x));
  const rgb = [0, 1, 2].map(i => {
    let r = sat(t0[3] * t1[i]);
    r = sat(d0[i] * t0[i] + r);
    r = sat(t0[3] * d1[i] + r);
    return sat(r * d1[3]);
  });
  return [rgb[0], rgb[1], rgb[2], glass ? d0[3] : 1];
};

/**
 * The microcode's blend (NFSHP2.exe 0x42e880 by the geometry name, the technique's render states): paint, rubber and
 * generic draw opaque (source one, destination zero, whatever the name), glass by the geometry name: "ALPHA_TRANS"
 * alpha blended, "ALPHA_ADD" added
 */
export const nfs6CarBlend = (shader: Nfs6CarShader, name: string): Nfs6CarBlend =>
  shader !== 'glass'
    ? 'opaque'
    : name.includes('ALPHA_ADD')
      ? 'add'
      : name.includes('ALPHA_TRANS')
        ? 'trans'
        : 'opaque';

/** World up: TailsLab's export axes (x, y = game -z, z up), the GLB / OBJ axes, nfs-web's world and the GUI viewers */
const WORLD_UP_GLSL = 'z';

/** Track axes (x, y up, z) to the world: the track export's (x, z, y) */
export const nfs6TrackToWorld = (p: [number, number, number]): [number, number, number] => [p[0], p[2], p[1]];

/** Uniforms of one car, shared by its materials */
class Nfs6CarUniforms {
  readonly ambientSky = { value: new Vector3() };
  readonly ambientGround = { value: new Vector3() };
  // world
  readonly sunPosition = { value: new Vector3() };
  readonly rootPosition = { value: new Vector3() };
  readonly paintSpecular = { value: new Vector3() };
  readonly hotSpecular = { value: new Vector3() };
  // gGlassSpecularColour / gRubberSpecularColour: white (0x412f00)
  readonly white = { value: new Vector3(1, 1, 1) };
  readonly exponents = { paint: 0, hot: 0, glass: 0, rubber: 0 };
  readonly brightness = { value: 1 };
  readonly envMap: { value: Texture | null } = { value: null };
}

type ShaderOptions = {
  shader: Nfs6CarShader;
  gameNormals: boolean;
  // glass: vertex colors of the geometry: 0 none, 3 OBJ (rgb, sRGB-decoded by OBJLoader), 4 GLB (raw rgba)
  colorSize: number;
  vertexAlpha: number;
};

/**
 * The vertex and pixel shaders of the EASVehicle* microcodes (EAGL/eaglrm.o, technique 0 of slot 0: the one drawn
 * with ps.1.1 at graphics detail 2..4), in the material's shader: replaces the material's own lighting. Per vertex
 * (vs.1.1): the sphere map coordinates (nfs6BentNormal, nfs6SphereMapUv), the specular (Blinn half vector of the
 * camera and the sun position, nfs6Lit: paint gPaintSpecularColour ^ specular_paint_exponent +
 * gHotSpecularColour ^ specular_hotspot_exponent, generic only the first, rubber / glass white ^ their exponent), the
 * hemisphere ambient (nfs6HemisphereAmbient; glass: the vertex color instead). Per pixel nfs6PixelColor, in the
 * game's color values (textures and vertex colors as stored, no sRGB decoding), written as the output's sRGB.
 * SKIPPED: vertex fog (the scene's fog applies), the paint's damage texture, the sampler states of the technique
 * (the texture's own filtering)
 */
function vehicleShaderInMaterial(material: Material, uniforms: Nfs6CarUniforms, options: ShaderOptions) {
  const { shader, gameNormals, colorSize } = options;
  const glass = shader === 'glass';
  const exponentKey = shader === 'generic' ? 'paint' : shader;
  const previous = material.onBeforeCompile;
  const previousKey = material.customProgramCacheKey;
  material.onBeforeCompile = (program, renderer) => {
    previous.call(material, program, renderer);
    program.uniforms['eaglAmbientSky'] = uniforms.ambientSky;
    program.uniforms['eaglAmbientGround'] = uniforms.ambientGround;
    program.uniforms['eaglSunPosition'] = uniforms.sunPosition;
    program.uniforms['eaglRootPosition'] = uniforms.rootPosition;
    program.uniforms['eaglSpecular'] =
      shader === 'paint' || shader === 'generic' ? uniforms.paintSpecular : uniforms.white;
    program.uniforms['eaglHotSpecular'] = uniforms.hotSpecular;
    program.uniforms['eaglExponent'] = {
      get value() {
        return uniforms.exponents[exponentKey];
      },
    };
    program.uniforms['eaglHotExponent'] = {
      get value() {
        return uniforms.exponents.hot;
      },
    };
    program.uniforms['eaglBrightness'] = uniforms.brightness;
    program.uniforms['eaglVertexAlpha'] = { value: options.vertexAlpha };
    program.uniforms['eaglEnvMap'] = uniforms.envMap;
    program.uniforms['eaglEnvEnabled'] = {
      get value() {
        return uniforms.envMap.value ? 1 : 0;
      },
    };
    program.uniforms['eaglEnvFlipY'] = {
      get value() {
        return uniforms.envMap.value?.flipY ? 1 : 0;
      },
    };
    program.uniforms['eaglEnvSrgb'] = {
      get value() {
        return uniforms.envMap.value?.colorSpace === SRGBColorSpace ? 1 : 0;
      },
    };
    program.uniforms['eaglMapSrgb'] = {
      get value() {
        return (material as MeshBasicMaterial).map?.colorSpace === SRGBColorSpace ? 1 : 0;
      },
    };
    const normal = gameNormals ? '_game_normal' : 'normal';
    let color = 'vec4( 1.0, 1.0, 1.0, eaglVertexAlpha )';
    if (colorSize === 4) {
      color = 'color';
    } else if (colorSize === 3) {
      // OBJLoader decoded the stored values as sRGB
      color = 'vec4( sRGBTransferOETF( vec4( color.rgb, 1.0 ) ).rgb, eaglVertexAlpha )';
    }
    program.vertexShader = program.vertexShader
      .replace(
        '#include <fog_pars_vertex>',
        `#include <fog_pars_vertex>
        ${gameNormals ? 'attribute vec3 _game_normal;' : ''}
        ${glass && colorSize ? 'attribute vec4 color;' : ''}
        uniform vec3 eaglAmbientSky;
        uniform vec3 eaglAmbientGround;
        uniform vec3 eaglSunPosition;
        uniform vec3 eaglRootPosition;
        uniform vec3 eaglSpecular;
        uniform vec3 eaglHotSpecular;
        uniform float eaglExponent;
        uniform float eaglHotExponent;
        uniform float eaglBrightness;
        uniform float eaglVertexAlpha;
        varying vec4 vEaglD0;
        varying vec4 vEaglD1;
        varying vec2 vEaglEnvUv;
        // nfs6Lit
        float eaglLit( float nh, float power ) {
          return nh > 0.0 ? pow( nh, clamp( power, -127.9961, 127.9961 ) ) : 0.0;
        }
        ${
          colorSize === 3
            ? `vec4 sRGBTransferOETF( in vec4 value ) {
          return vec4( mix( pow( value.rgb, vec3( 0.41666 ) ) * 1.055 - vec3( 0.055 ), value.rgb * 12.92,
            vec3( lessThanEqual( value.rgb, vec3( 0.0031308 ) ) ) ), value.a );
        }`
            : ''
        }`,
      )
      .replace(
        '#include <fog_vertex>',
        `#include <fog_vertex>
        {
          vec4 eaglWorld = modelMatrix * vec4( position, 1.0 );
          vec3 eaglWorldNormal = mat3( modelMatrix ) * ${normal};
          // nfs6BentNormal (model space = the car's, turned with it) and nfs6SphereMapUv
          vec3 eaglBent = normalize( eaglWorldNormal + ${NFS6_NORMAL_BEND} * ( eaglWorld.xyz - eaglRootPosition ) );
          vec3 eaglViewBent = mat3( viewMatrix ) * eaglBent;
          vEaglEnvUv = 1.0 - ( eaglViewBent.xy * ${NFS6_SPHERE_MAP_SCALE} * 0.5 + 0.5 );
          // specular: half vector of the camera and the sun position
          vec3 eaglEye = normalize( cameraPosition - eaglWorld.xyz );
          vec3 eaglSun = normalize( eaglSunPosition - eaglWorld.xyz );
          float eaglNH = dot( normalize( eaglWorldNormal ), normalize( eaglEye + eaglSun ) );
          vec3 eaglSpec = max( 0.0, eaglLit( eaglNH, eaglExponent ) ) * eaglSpecular;
          ${shader === 'paint' ? 'eaglSpec += eaglLit( eaglNH, eaglHotExponent ) * eaglHotSpecular;' : ''}
          vEaglD1 = clamp( vec4( eaglSpec, eaglBrightness ), 0.0, 1.0 );
          ${
            glass
              ? `vEaglD0 = clamp( ${color}, 0.0, 1.0 );`
              : `float eaglSky = eaglWorldNormal.${WORLD_UP_GLSL} * 0.5 + 0.5;
          vEaglD0 = vec4( min( eaglSky * eaglAmbientSky + ( 1.0 - eaglSky ) * eaglAmbientGround, vec3( 1.0 ) ), 1.0 );`
          }
        }`,
      );
    program.fragmentShader = program.fragmentShader
      .replace(
        '#include <fog_pars_fragment>',
        `#include <fog_pars_fragment>
        uniform sampler2D eaglEnvMap;
        uniform float eaglEnvEnabled;
        uniform float eaglEnvFlipY;
        uniform float eaglEnvSrgb;
        uniform float eaglMapSrgb;
        varying vec4 vEaglD0;
        varying vec4 vEaglD1;
        varying vec2 vEaglEnvUv;`,
      )
      .replace(
        '#include <opaque_fragment>',
        `{
          // nfs6PixelColor, in the stored color values
          #ifdef USE_MAP
          vec4 eaglT0 = texture2D( map, vMapUv );
          if ( eaglMapSrgb > 0.5 ) {
            eaglT0 = vec4( sRGBTransferOETF( eaglT0 ).rgb, eaglT0.a );
          }
          #else
          vec4 eaglT0 = vec4( 1.0 );
          #endif
          vec3 eaglT1 = vec3( 0.0 );
          if ( eaglEnvEnabled > 0.5 ) {
            // D3D: v = 0 is the top row
            vec4 env = texture2D( eaglEnvMap, vec2( vEaglEnvUv.x, eaglEnvFlipY > 0.5 ? 1.0 - vEaglEnvUv.y : vEaglEnvUv.y ) );
            eaglT1 = eaglEnvSrgb > 0.5 ? sRGBTransferOETF( env ).rgb : env.rgb;
          }
          vec3 eaglR0 = clamp( eaglT0.a * eaglT1, 0.0, 1.0 );
          eaglR0 = clamp( vEaglD0.rgb * eaglT0.rgb + eaglR0, 0.0, 1.0 );
          eaglR0 = clamp( eaglT0.a * vEaglD1.rgb + eaglR0, 0.0, 1.0 );
          eaglR0 = clamp( eaglR0 * vEaglD1.a, 0.0, 1.0 );
          outgoingLight = sRGBTransferEOTF( vec4( eaglR0, 1.0 ) ).rgb;
          diffuseColor.a = ${glass ? 'vEaglD0.a' : '1.0'};
        }
        #include <opaque_fragment>`,
      );
  };
  material.customProgramCacheKey = () =>
    `${previousKey.call(material)}|eagl-vehicle-${shader}-${gameNormals ? 'game' : 'normal'}-${colorSize}`;
  material.needsUpdate = true;
}

/**
 * Animates NFS6 car model (car.o) in preview: steers and spins wheels (brake calipers steer only), switches skins,
 * shows light bones, and draws every mesh as NFSHP2.exe does (vehicleShaderInMaterial, by its "eaglShader" /
 * "eaglBlend" properties), lit by a track location's lighting.ini and environment map. Expects meshes, exported by
 * EaglModelSerializer for a car: "<lod>_<index>_<geometry name>", X right, Y forward, Z up, game normals (`normal` of
 * an OBJ, `_game_normal` of a GLB), glass vertex colors (`color`). The paint is the texture "textures/skin.png", every
 * skin has its own texture. Materials are cloned per microcode and blend (an OBJ's are shared per texture). Depends
 * only on three.js, so it can be reused outside the GUI
 */
export class Nfs6CarMeshController {
  private wheels: { meshes: Mesh[]; isFront: boolean; spins: boolean }[] = [];
  private lights: Group | null = null;
  private spinAngle = 0;
  // materials, which use the skin texture
  private skinMaterials: MeshBasicMaterial[] = [];
  private readonly textureLoader = new TextureLoader();
  private animationTimer: any = null;
  private baseUrl: string | null = null;
  private readonly uniforms = new Nfs6CarUniforms();
  private readonly root: Object3D;
  private disposed = false;

  private _skin: string | null = null;
  get skin(): string | null {
    return this._skin;
  }

  set skin(name: string | null) {
    const skin = this.skins.find(x => x.name === name);
    // folder of the exported model: skin textures are relative to it. Taken from the original skin texture URL
    if (!this.baseUrl) {
      const url: string | undefined = (this.skinMaterials[0]?.map?.source.data as HTMLImageElement)?.src;
      this.baseUrl = (url && /^(.*\/)textures\/skin\.png(\?.*)?$/.exec(url)?.[1]) || null;
    }
    const baseUrl = this.baseUrl;
    if (!skin || !baseUrl) {
      return;
    }
    this._skin = name;
    this.updateLighting();
    this.textureLoader.load(baseUrl + skin.texture, texture => {
      for (const material of this.skinMaterials) {
        const original = material.map!;
        texture.flipY = original.flipY;
        texture.wrapS = original.wrapS;
        texture.wrapT = original.wrapT;
        texture.colorSpace = original.colorSpace;
        texture.anisotropy = original.anisotropy;
        texture.magFilter = original.magFilter;
        texture.minFilter = original.minFilter;
        texture.needsUpdate = true;
        material.map = texture;
        material.needsUpdate = true;
      }
    });
  }

  private _location: Nfs6Location = NFS6_DEFAULT_LOCATION;
  /** Lighting of a track location (lighting.ini) */
  get location(): Nfs6Location {
    return this._location;
  }

  set location(value: Nfs6Location) {
    this._location = value;
    this.updateLighting();
  }

  /**
   * The environment map (gTextureEnviro): the location's staticenvmap.fsh in a race, Cars/common.fsh "refl" in the
   * frontend. Texels as stored (any color space: sRGB ones are read back). Not owned by the controller
   */
  get environmentMap(): Texture | null {
    return this.uniforms.envMap.value;
  }

  set environmentMap(value: Texture | null) {
    this.uniforms.envMap.value = value;
  }

  private _lightLevel = 1;
  /** The light level of the road under the car, 0..1 (tunnels are darker): nfs6Brightness, nfs6HotSpecular */
  get lightLevel(): number {
    return this._lightLevel;
  }

  set lightLevel(value: number) {
    this._lightLevel = value;
    this.updateLighting();
  }

  private _speed = 0;
  /** Car speed in m/s, the wheels spin at it */
  get speed(): number {
    return this._speed;
  }

  set speed(value: number) {
    this._speed = value;
    if (this.animationTimer) {
      clearInterval(this.animationTimer);
      this.animationTimer = null;
    }
    if (value > 0) {
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
   * @param objects mesh properties by mesh name ("objects" of "<obj>_extra.json"), default: the mesh's `userData`
   * (GLB node extras)
   */
  constructor(
    mesh: Object3D,
    dummies: Nfs6CarDummy[],
    readonly skins: Nfs6CarSkin[],
    readonly lighting: Nfs6CarLighting | null = null,
    objects: { [name: string]: Nfs6CarMeshProperties } | null = null,
  ) {
    this.root = mesh;
    this.setupWheels(mesh);
    this.setupShaders(mesh, objects);
    this.setupSkinMaterials(mesh);
    const lightDummies = dummies.filter(d => Nfs6CarMeshController.lightColor(d.name) !== null);
    if (lightDummies.length > 0) {
      this.lights = new Group();
      this.lights.visible = false;
      for (const dummy of lightDummies) {
        const light = new Mesh(
          new SphereGeometry(0.05, 8, 8),
          new MeshBasicMaterial({ color: Nfs6CarMeshController.lightColor(dummy.name)! }),
        );
        light.name = dummy.name;
        light.position.set(...dummy.position);
        this.lights.add(light);
      }
      mesh.add(this.lights);
    }
    if (this.skins.length > 0 && this.skinMaterials.length > 0) {
      this._skin = this.skins[0].name;
    }
    this._location =
      lighting?.locations?.find(x => x.name === NFS6_DEFAULT_LOCATION.name) ||
      lighting?.locations?.[0] ||
      NFS6_DEFAULT_LOCATION;
    this.updateLighting();
  }

  private setupWheels(mesh: Object3D) {
    const wheelMeshes: Mesh[] = [];
    const brakeMeshes: Mesh[] = [];
    mesh.traverse(o => {
      if (o instanceof Mesh) {
        if (NFS6_WHEEL_REGEX.test(o.name)) {
          wheelMeshes.push(o);
        } else if (NFS6_BRAKE_REGEX.test(o.name)) {
          brakeMeshes.push(o);
        }
      }
    });
    const wheelCenters: Vector3[] = [];
    const centerOf = (m: Mesh) => {
      m.geometry.computeBoundingBox();
      return m.geometry.boundingBox!.getCenter(new Vector3());
    };
    const setPivot = (m: Mesh, pivot: Vector3) => {
      m.geometry.translate(-pivot.x, -pivot.y, -pivot.z);
      m.position.copy(pivot);
      m.rotation.order = 'ZXY';
    };
    for (const m of wheelMeshes) {
      // move pivot to the wheel center, so it rotates in place
      const center = centerOf(m);
      wheelCenters.push(center);
      setPivot(m, center);
      this.wheels.push({ meshes: [m], isFront: center.y > 0, spins: true });
    }
    for (const m of brakeMeshes) {
      // brake caliper turns around the center of its wheel
      const center = centerOf(m);
      const pivot = wheelCenters.reduce<Vector3 | null>(
        (best, c) => (!best || c.distanceTo(center) < best.distanceTo(center) ? c : best),
        null,
      );
      setPivot(m, pivot ? new Vector3(center.x, pivot.y, pivot.z) : center);
      this.wheels.push({ meshes: [m], isFront: center.y > 0, spins: false });
    }
  }

  /**
   * Every mesh gets a copy of its materials with the shaders of its microcode (shared by the meshes of the same
   * material, microcode and blend) and the game's blend: opaque writes depth, "trans" (alpha blended) and "add"
   * (source alpha, one) do not and are drawn after the opaque meshes, "add" last (0x413890). SKIPPED: the draw order
   * within a pass (the model's; here three.js sorts the translucent meshes by depth), addons (ADDON_ geometries are
   * drawn as the others, whatever the skin's addons_enable)
   */
  private setupShaders(mesh: Object3D, objects: { [name: string]: Nfs6CarMeshProperties } | null) {
    const copies = new Map<string, Material>();
    mesh.traverse(o => {
      if (!(o instanceof Mesh) || o.parent === this.lights) {
        return;
      }
      const properties: Nfs6CarMeshProperties = objects?.[o.name] ?? o.userData ?? {};
      const shader: Nfs6CarShader = properties.eaglShader ?? 'paint';
      const blend: Nfs6CarBlend = properties.eaglBlend ?? nfs6CarBlend(shader, o.name);
      const gameNormals = !!o.geometry.getAttribute('_game_normal');
      const color = o.geometry.getAttribute('color');
      const colorSize = shader === 'glass' && color ? color.itemSize : 0;
      const vertexAlpha = properties.eaglVertexAlpha ?? 1;
      const copy = (material: Material) => {
        const key = `${material.uuid}|${shader}|${blend}|${gameNormals}|${colorSize}|${vertexAlpha}`;
        let result = copies.get(key);
        if (!result) {
          result = material.clone();
          (result as MeshBasicMaterial).vertexColors = false;
          result.alphaTest = 0;
          result.premultipliedAlpha = false;
          result.transparent = blend !== 'opaque';
          result.depthWrite = blend === 'opaque';
          result.blending = blend === 'add' ? AdditiveBlending : NormalBlending;
          vehicleShaderInMaterial(result, this.uniforms, { shader, gameNormals, colorSize, vertexAlpha });
          copies.set(key, result);
        }
        return result;
      };
      o.material = o.material instanceof Array ? o.material.map(copy) : copy(o.material);
      o.renderOrder = blend === 'add' ? 2 : blend === 'trans' ? 1 : 0;
      // the car's position, for the environment map normal (model space)
      const previous = o.onBeforeRender;
      o.onBeforeRender = (...args) => {
        previous.apply(o, args);
        if (!this.disposed) {
          this.root.updateWorldMatrix(true, false);
          this.uniforms.rootPosition.value.setFromMatrixPosition(this.root.matrixWorld);
        }
      };
    });
  }

  /** Materials, named after the texture "skin" (the paint) */
  private setupSkinMaterials(mesh: Object3D) {
    mesh.traverse(o => {
      if (!(o instanceof Mesh)) {
        return;
      }
      const materials = o.material instanceof Array ? o.material : [o.material];
      for (const material of materials) {
        if (material.name === 'skin' && (material as MeshBasicMaterial).map && !this.skinMaterials.includes(material)) {
          this.skinMaterials.push(material as MeshBasicMaterial);
        }
      }
    });
  }

  /** The shader constants of the skin and the location (0x412f00, 0x4134c0) */
  private updateLighting() {
    const u = this.uniforms;
    const location = this._location;
    const skin = this.skins.find(x => x.name === this._skin) ?? this.skins[0];
    const specular = skin?.specular;
    u.ambientSky.value.set(...(location.ambient_sky.map(c => c / 255) as [number, number, number]));
    u.ambientGround.value.set(...(location.ambient_ground.map(c => c / 255) as [number, number, number]));
    u.sunPosition.value.set(...nfs6TrackToWorld(location.sun_position));
    const paint = nfs6PaintSpecular(specular, location.sun);
    u.paintSpecular.value.set(...paint);
    u.hotSpecular.value.set(...nfs6HotSpecular(paint, this._lightLevel, this.lighting?.vehicle_type === 'traffic'));
    u.exponents.paint = specular?.specular_paint_exponent ?? 0;
    u.exponents.glass = specular?.specular_glass_exponent ?? 0;
    u.exponents.rubber = specular?.specular_rubber_exponent ?? 0;
    u.exponents.hot = this.lighting?.specular_hotspot_exponent ?? 0;
    u.brightness.value = nfs6Brightness(this._lightLevel);
  }

  /** Color of light bone, null if bone is not a light */
  private static lightColor(name: string): number | null {
    return NFS6_LIGHT_COLORS.find(([regex]) => regex.test(name))?.[1] ?? null;
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
  }
}
