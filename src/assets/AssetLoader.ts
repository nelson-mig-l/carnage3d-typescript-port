import { Howl } from 'howler';
import { AssetDescriptor, AssetManifest, AssetType, createDefaultAssetManifest } from './AssetManifest';

export type LoadedAsset = {
  id: string;
  type: AssetType;
  src: string;
  ready: boolean;
  url: string;
  metadata?: Record<string, unknown>;
  resource?: HTMLImageElement | FontFace | Howl;
  error?: string;
};

export type LoadedAssetBuckets = {
  textures: Record<string, LoadedAsset>;
  fonts: Record<string, LoadedAsset>;
  sounds: Record<string, LoadedAsset>;
  sprites: Record<string, LoadedAsset>;
};

export class AssetLoader {
  private readonly manifest: AssetManifest;
  private readonly loadedAssets = new Map<string, LoadedAsset>();

  constructor(manifest: AssetManifest = createDefaultAssetManifest()) {
    this.manifest = manifest;
  }

  getManifest(): AssetManifest {
    return { ...this.manifest, assets: [...this.manifest.assets] };
  }

  getAsset(id: string): LoadedAsset | undefined {
    return this.loadedAssets.get(id);
  }

  async loadAll(): Promise<LoadedAssetBuckets> {
    const buckets: LoadedAssetBuckets = {
      textures: {},
      fonts: {},
      sounds: {},
      sprites: {},
    };

    for (const asset of this.manifest.assets) {
      const loaded = await this.loadAsset(asset);
      buckets[`${asset.type}s` as keyof LoadedAssetBuckets][asset.id] = loaded;
      this.loadedAssets.set(asset.id, loaded);
    }

    return buckets;
  }

  async loadAsset(asset: AssetDescriptor): Promise<LoadedAsset> {
    const url = this.resolveAssetUrl(asset);

    try {
      const resource = await this.loadResource(asset, url);
      const loaded: LoadedAsset = { id: asset.id, type: asset.type, src: asset.src, ready: true, url, metadata: asset.metadata, resource };
      this.loadedAssets.set(asset.id, loaded);
      return loaded;
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      const loaded: LoadedAsset = { id: asset.id, type: asset.type, src: asset.src, ready: false, url, metadata: asset.metadata, error: message };
      this.loadedAssets.set(asset.id, loaded);
      return loaded;
    }
  }

  private async loadResource(asset: AssetDescriptor, url: string): Promise<HTMLImageElement | FontFace | Howl> {
    switch (asset.type) {
      case 'texture':
      case 'sprite':
        return this.loadImage(url);
      case 'font':
        return this.loadFont(asset, url);
      case 'sound':
        return this.loadSound(asset, url);
    }
  }

  private loadImage(url: string): Promise<HTMLImageElement> {
    if (typeof Image === 'undefined') return Promise.reject(new Error(`Cannot load image outside a browser: ${url}`));
    return new Promise((resolve, reject) => {
      const image = new Image();
      image.onload = () => resolve(image);
      image.onerror = () => reject(new Error(`Failed to load image: ${url}`));
      image.src = url;
    });
  }

  private async loadFont(asset: AssetDescriptor, url: string): Promise<FontFace> {
    if (typeof FontFace === 'undefined' || typeof document === 'undefined') throw new Error(`Cannot load font outside a browser: ${url}`);
    const family = typeof asset.metadata?.family === 'string' ? asset.metadata.family : asset.id;
    const font = new FontFace(family, `url("${url}")`);
    await font.load();
    document.fonts.add(font);
    return font;
  }

  private loadSound(asset: AssetDescriptor, url: string): Promise<Howl> {
    return new Promise((resolve, reject) => {
      let sound: Howl;
      sound = new Howl({
        src: [url],
        loop: asset.metadata?.loop === true,
        onload: () => resolve(sound),
        onloaderror: (_id, error) => reject(new Error(`Failed to load sound ${asset.id}: ${String(error)}`)),
      });
    });
  }

  private resolveAssetUrl(asset: AssetDescriptor): string {
    const relativeSource = asset.path ?? asset.src;
    const normalizedBase = this.manifest.basePath.replace(/\/$/, '');
    return `${normalizedBase}/${relativeSource.replace(/^\//, '')}`;
  }

  private async isAssetReachable(url: string): Promise<boolean> {
    if (typeof fetch !== 'function') {
      return true;
    }

    if (typeof window !== 'undefined' && window.location.protocol === 'file:') {
      return true;
    }

    if (typeof document === 'undefined' || !document.body) {
      return true;
    }

    try {
      const response = await fetch(url, { method: 'HEAD' });
      return response.ok;
    } catch {
      return true;
    }
  }
}
