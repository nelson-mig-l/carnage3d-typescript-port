import * as BABYLON from 'babylonjs';
import { LoadedAsset, LoadedAssetBuckets } from '../assets/AssetLoader';

export class SceneManager {
  private readonly scene: BABYLON.Scene;
  private readonly generatedTextures: BABYLON.BaseTexture[] = [];
  private sound: LoadedAsset | null = null;
  private soundClickHandler: (() => void) | null = null;

  constructor(scene: BABYLON.Scene) {
    this.scene = scene;
    this.configureScene();
  }

  showLoadedAssets(assets: LoadedAssetBuckets): void {
    this.disposeAssetShowcase();

    const wood = assets.textures['test.texture'];
    const grass = assets.sprites['test.sprite'];
    const font = assets.fonts['test.font'];
    this.sound = assets.sounds['test.click'];

    const woodTexture = this.createImageTexture(wood);
    const grassTexture = this.createImageTexture(grass);

    const ground = this.scene.getMeshByName('ground');
    if (ground && woodTexture) {
      const material = new BABYLON.StandardMaterial('test-wood-material', this.scene);
      material.diffuseTexture = woodTexture;
      material.specularColor = BABYLON.Color3.Black();
      ground.material = material;
    }

    const spriteBox = BABYLON.MeshBuilder.CreateBox(
      'test-sprite-box',
      { size: 2.2 },
      this.scene,
    );
    spriteBox.position = new BABYLON.Vector3(0, 1.1, 0);

    if (grassTexture) {
      const material = new BABYLON.StandardMaterial('test-sprite-material', this.scene);
      material.diffuseTexture = grassTexture;
      material.specularColor = BABYLON.Color3.Black();
      spriteBox.material = material;
    }

    if (font?.ready && font.resource instanceof FontFace) {
      this.addFontShowcase(font.resource);
    }

    if (this.sound?.ready && this.sound.resource) {
      this.soundClickHandler = () => {
        this.sound?.resource && (this.sound.resource as { play: () => unknown }).play();
      };
      this.scene.getEngine().getRenderingCanvas()?.addEventListener('click', this.soundClickHandler);
    }

    console.info(
      '[AssetShowcase]',
      Object.values(assets.textures).filter((asset) => asset.ready).length,
      'texture(s),',
      Object.values(assets.sprites).filter((asset) => asset.ready).length,
      'sprite(s),',
      Object.values(assets.fonts).filter((asset) => asset.ready).length,
      'font(s),',
      Object.values(assets.sounds).filter((asset) => asset.ready).length,
      'sound(s) loaded',
    );
  }

  private createImageTexture(asset: LoadedAsset | undefined): BABYLON.RawTexture | null {
    if (!asset?.ready || !(asset.resource instanceof HTMLImageElement)) {
      return null;
    }

    const image = asset.resource;
    const canvas = document.createElement('canvas');
    canvas.width = image.naturalWidth || image.width;
    canvas.height = image.naturalHeight || image.height;

    const context = canvas.getContext('2d');
    if (!context || canvas.width === 0 || canvas.height === 0) {
      return null;
    }

    context.drawImage(image, 0, 0);
    const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
    const texture = BABYLON.RawTexture.CreateRGBATexture(
      pixels,
      canvas.width,
      canvas.height,
      this.scene,
      false,
      false,
      BABYLON.Texture.NEAREST_SAMPLINGMODE,
    );
    this.generatedTextures.push(texture);
    return texture;
  }

  private addFontShowcase(font: FontFace): void {
    const plane = BABYLON.MeshBuilder.CreatePlane(
      'test-font-sign',
      { width: 7, height: 2 },
      this.scene,
    );
    plane.position = new BABYLON.Vector3(0, 4, 1);
    plane.billboardMode = BABYLON.Mesh.BILLBOARDMODE_ALL;

    const texture = new BABYLON.DynamicTexture(
      'test-font-texture',
      { width: 1024, height: 256 },
      this.scene,
      true,
    );
    const context = texture.getContext();
    context.clearRect(0, 0, 1024, 256);
    context.fillStyle = '#111827';
    context.fillRect(0, 0, 1024, 256);
    context.fillStyle = '#f8fafc';
    context.font = `64px "${font.family}"`;
    context.textAlign = 'center';
    context.textBaseline = 'middle';
    context.fillText('Typewriter font loaded', 512, 128);
    texture.update();

    const material = new BABYLON.StandardMaterial('test-font-material', this.scene);
    material.diffuseTexture = texture;
    material.emissiveColor = BABYLON.Color3.White();
    material.specularColor = BABYLON.Color3.Black();
    plane.material = material;

    this.generatedTextures.push(texture);
  }

  private disposeAssetShowcase(): void {
    if (this.soundClickHandler) {
      this.scene.getEngine().getRenderingCanvas()?.removeEventListener('click', this.soundClickHandler);
      this.soundClickHandler = null;
    }

    this.generatedTextures.splice(0).forEach((texture) => texture.dispose());
    this.scene.getMeshByName('test-sprite-box')?.dispose();
    this.scene.getMeshByName('test-font-sign')?.dispose();
  }

  private configureScene(): void {
    this.scene.clearColor = new BABYLON.Color4(0.06, 0.08, 0.12, 1);

    const light = new BABYLON.HemisphericLight('light', new BABYLON.Vector3(0, 1, 0), this.scene);
    light.intensity = 0.9;

    const ground = BABYLON.MeshBuilder.CreateGround('ground', { width: 20, height: 20 }, this.scene);
    ground.position.y = -1;

    const testSphere = BABYLON.MeshBuilder.CreateSphere('test-sphere', { diameter: 1.5 }, this.scene);
    testSphere.position = new BABYLON.Vector3(-3, 1, 0);
  }
}
