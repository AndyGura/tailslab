import { BufferAttribute, Material, Mesh, Object3D } from 'three';
import { TnfsCarColors, TnfsCarMeshController } from './tnfs-car-mesh-controller';

/**
 * Geometry attribute of the Gouraud colours of the Japanese PSX TNFS (Over Drivin' Skyline Memorial, SLPS-01024) cars,
 * TailsLab's GLB attribute `_PSX_GOURAUD` (unsigned bytes, normalized: value / 255). Per corner (r, g, b, 255) on the
 * polygons the game draws with Gouraud colours, (0x80, 0x80, 0x80, 0) on the others of the mesh. Meshes without such a
 * polygon have none
 */
export const PSX_GOURAUD_ATTRIBUTE = '_psx_gouraud';

const meshMaterials = (mesh: Mesh): Material[] => (Array.isArray(mesh.material) ? mesh.material : [mesh.material]);

const hasGouraud = (mesh: Mesh): boolean => !!mesh.geometry?.getAttribute(PSX_GOURAUD_ATTRIBUTE);

/** Whether a mesh of the model has the Gouraud colours of a Japanese PSX car (`PSX_GOURAUD_ATTRIBUTE`) */
export function hasPsxGouraudColors(model: Object3D): boolean {
  let found = false;
  model.traverse(o => {
    found ||= o instanceof Mesh && hasGouraud(o);
  });
  return found;
}

/**
 * The material draws the Gouraud colours of its geometry as the PSX GPU does (on top of its other shader changes, after
 * the recolored texels of the tail lights, see `recolorInShader`): a textured polygon (POLY_GT4) texel × colour / 128 on
 * the texel's own values (the PNG's, sRGB), clamped; an untextured one (POLY_G3 / POLY_G4: the windows) the colour
 * itself, instead of the material's (TailsLab's `flat_<rrggbb>`: the mean of the corners). A corner of alpha 0 keeps
 * the material's colour. In the fragment shader: no canvas readback (anti-fingerprinting noise)
 */
function gouraudInShader(material: Material) {
  const previous = material.onBeforeCompile;
  const previousKey = material.customProgramCacheKey;
  material.onBeforeCompile = (shader, renderer) => {
    previous.call(material, shader, renderer);
    shader.vertexShader = shader.vertexShader
      .replace(
        '#include <common>',
        `#include <common>
        attribute vec4 ${PSX_GOURAUD_ATTRIBUTE};
        varying vec4 vPsxGouraud;`,
      )
      .replace(
        '#include <begin_vertex>',
        `#include <begin_vertex>
        vPsxGouraud = ${PSX_GOURAUD_ATTRIBUTE};`,
      );
    shader.fragmentShader = shader.fragmentShader
      .replace(
        '#include <common>',
        `#include <common>
        varying vec4 vPsxGouraud;`,
      )
      .replace(
        '#include <color_fragment>',
        `#include <color_fragment>
        {
          #ifdef USE_MAP
          vec3 psxTexel = sRGBTransferOETF( vec4( diffuseColor.rgb, 1.0 ) ).rgb;
          vec3 psxShaded = min( psxTexel * vPsxGouraud.rgb * ( 255.0 / 128.0 ), vec3( 1.0 ) );
          #else
          vec3 psxShaded = vPsxGouraud.rgb;
          #endif
          diffuseColor.rgb = mix( diffuseColor.rgb, sRGBTransferEOTF( vec4( psxShaded, 1.0 ) ).rgb, vPsxGouraud.a );
        }`,
      );
  };
  material.customProgramCacheKey = () => `${previousKey.call(material)}|psx-gouraud`;
  material.needsUpdate = true;
}

/**
 * Gives the meshes with Gouraud colours their own copy of a material they share with meshes without them (the GUI's OBJ
 * loader gives the meshes of a material one material object), before the base controller sets its shaders up
 */
function separateGouraudMaterials(model: Object3D, copies: Material[]): Object3D {
  const withGouraud = new Set<Material>();
  const without = new Set<Material>();
  model.traverse(o => {
    if (o instanceof Mesh) {
      meshMaterials(o).forEach(m => (hasGouraud(o) ? withGouraud : without).add(m));
    }
  });
  const copyOf = new Map<Material, Material>();
  model.traverse(o => {
    if (!(o instanceof Mesh) || !hasGouraud(o)) {
      return;
    }
    const replaced = meshMaterials(o).map(m => {
      if (!without.has(m)) {
        return m;
      }
      if (!copyOf.has(m)) {
        const copy = m.clone();
        copyOf.set(m, copy);
        copies.push(copy);
      }
      return copyOf.get(m)!;
    });
    o.material = Array.isArray(o.material) ? replaced : replaced[0];
  });
  return model;
}

/**
 * A car of the Japanese PSX disc Over Drivin' Skyline Memorial (SLPS-01024): `TnfsCarMeshController` with the Gouraud
 * colours of its high-poly model (`<car>.GRO`, TailsLab's GLB attribute `_PSX_GOURAUD`) drawn as the game does
 * (SLPS_010.24: `oriload` FUN_8007f358 turns the polygons with `mapping` bit 0x40, and of draw type 10, into POLY_G3 /
 * POLY_G4 / POLY_GT4, FUN_80084944 fills their colours; none is semi-transparent), see `gouraudInShader`. Create it
 * through `createTnfsCarMeshController`
 */
export class TnfsSkylineMemorialCarMeshController extends TnfsCarMeshController {
  // materials copied for the meshes with Gouraud colours, see separateGouraudMaterials
  private readonly gouraudCopies: Material[];

  constructor(mesh: Object3D, carColors: TnfsCarColors | null, assetsPath: string, blackLightBar: boolean) {
    const copies: Material[] = [];
    super(separateGouraudMaterials(mesh, copies), carColors, assetsPath, blackLightBar);
    this.gouraudCopies = copies;
    // the wheels have the base controller's tyre materials, shared by an axle: a wheel without the colours gets
    // neutral ones when the other one has them (none of the game's wheels has)
    const materials = new Set<Material>();
    const sharing = new Map<Material, Mesh[]>();
    mesh.traverse(o => {
      if (o instanceof Mesh) {
        meshMaterials(o).forEach(m => sharing.set(m, [...(sharing.get(m) || []), o]));
      }
    });
    for (const [material, meshes] of sharing) {
      if (!meshes.some(hasGouraud)) {
        continue;
      }
      for (const o of meshes.filter(o => !hasGouraud(o))) {
        const neutral = new Uint8Array(o.geometry.getAttribute('position').count * 4);
        for (let i = 0; i < neutral.length; i += 4) {
          neutral.set([0x80, 0x80, 0x80, 0], i);
        }
        o.geometry.setAttribute(PSX_GOURAUD_ATTRIBUTE, new BufferAttribute(neutral, 4, true));
      }
      materials.add(material);
    }
    materials.forEach(gouraudInShader);
  }

  public override dispose() {
    super.dispose();
    this.gouraudCopies.forEach(m => m.dispose());
    this.gouraudCopies.length = 0;
  }
}

/**
 * The car mesh controller of a TNFS car model: `TnfsSkylineMemorialCarMeshController` for a model with the Gouraud
 * colours of the Japanese PSX cars (`PSX_GOURAUD_ATTRIBUTE` on any mesh), else `TnfsCarMeshController`
 */
export function createTnfsCarMeshController(
  mesh: Object3D,
  carColors: TnfsCarColors | null,
  assetsPath: string,
  blackLightBar: boolean,
): TnfsCarMeshController {
  return hasPsxGouraudColors(mesh)
    ? new TnfsSkylineMemorialCarMeshController(mesh, carColors, assetsPath, blackLightBar)
    : new TnfsCarMeshController(mesh, carColors, assetsPath, blackLightBar);
}
