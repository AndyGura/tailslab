import { NearestFilter, Texture } from 'three';

/** NFS1 textures as the game draws them: sRGB, texels without filtering */
export const setupNfs1Texture = (texture: Texture) => {
  texture.colorSpace = 'srgb';
  texture.anisotropy = 8;
  texture.magFilter = NearestFilter;
  texture.minFilter = NearestFilter;
};
