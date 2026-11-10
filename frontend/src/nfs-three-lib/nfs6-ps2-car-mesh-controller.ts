import { BufferGeometry, Material, Mesh, MeshBasicMaterial, Object3D, Texture, TextureLoader, Vector3 } from 'three';

/** A paint of the car: "skins.json" of the TailsLab export */
export type Nfs6Ps2CarSkin = { name: string; label: string; texture: string; texture_b?: string };

/** "car.json" of the TailsLab export: wheels (X right, Y forward, Z up) and light textures by state */
export type Nfs6Ps2CarInfo = {
  model: string;
  car_type: string | null;
  wheels: { name: string; position: [number, number, number]; radius: number }[];
  lights: { [light: string]: { off?: string; on?: string; damaged?: string } };
};

// object "<lod>_<part>__<material>": wheel parts at a wheel
const WHEEL_PART_REGEX = /^(?:hp|mp|lp|vlp)_(tire|brake|wheel_blur)_(fl|fr|rr|rl)(?:__|$)/;

/**
 * NFS Hot Pursuit 2 (PS2) car model, exported by TailsLab's Nfs6Ps2CarSerializer (OBJ or gg-web-engine GLB): objects
 * "<lod>_<part>__<material>", X right, Y forward, Z up, with "skins.json" and "car.json" in the same folder
 * (`baseUrl`, with trailing slash). Switches paints (materials "skin" and "skin_b"), head and brake lights (materials
 * "headlight", "brakelight": their "on" textures), spins and steers the wheels (tyres and blur discs spin, brakes
 * steer only), and turns on the vertex colours of a GLB (COLOR_0: the game's baked shading, the textures are saved at
 * double brightness for it). Depends only on three.js, so it can be reused outside the GUI
 */
export class Nfs6Ps2CarMeshController {
  private wheels: { mesh: Mesh; isFront: boolean; spins: boolean }[] = [];
  private spinAngle = 0;
  private readonly materials: { [name: string]: Material[] } = {};
  private readonly originalMaps = new Map<Material, Texture | null>();
  private readonly textureLoader = new TextureLoader();
  private readonly textures: { [url: string]: Promise<Texture> } = {};
  private animationTimer: any = null;

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
  ) {
    mesh.traverse(o => {
      if (!(o instanceof Mesh)) {
        return;
      }
      const geometry = o.geometry as BufferGeometry;
      for (const material of o.material instanceof Array ? o.material : [o.material]) {
        // GLB: the game's shading in COLOR_0
        if (geometry.getAttribute('color') && !material.vertexColors) {
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
