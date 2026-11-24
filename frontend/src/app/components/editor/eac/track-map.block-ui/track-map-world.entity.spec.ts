import { MeshBasicMaterial, ShaderLib } from 'three';
import { TRACK_VERTEX_SHADING_FRAGMENT, vertexShadingMaterial } from './track-map-world.entity';

describe('vertexShadingMaterial', () => {
  it('should draw a copy of the terrain material with the vertex colours as the game', () => {
    const plain = new MeshBasicMaterial({ alphaTest: 0.5, transparent: true });
    const shaded = vertexShadingMaterial(plain);
    expect(shaded).not.toBe(plain);
    expect(shaded.vertexColors).toBeTrue();
    expect(plain.vertexColors).toBeFalse();
    expect(shaded.alphaTest).toBe(0.5);
    expect(shaded.transparent).toBeTrue();
    const shader = { fragmentShader: ShaderLib.basic.fragmentShader, vertexShader: '', uniforms: {} } as any;
    expect(shader.fragmentShader).toContain('#include <color_fragment>');
    shaded.onBeforeCompile(shader, null as any);
    expect(shader.fragmentShader).not.toContain('#include <color_fragment>');
    expect(shader.fragmentShader).toContain(TRACK_VERTEX_SHADING_FRAGMENT);
    expect(TRACK_VERTEX_SHADING_FRAGMENT).toContain(
      'pow( sRGBTransferOETF( vec4( vColor.rgb, 1.0 ) ).rgb, vec3( 2.2 ) )',
    );
    // one program for every such material
    expect(shaded.customProgramCacheKey()).toBe(vertexShadingMaterial(new MeshBasicMaterial()).customProgramCacheKey());
  });
});
