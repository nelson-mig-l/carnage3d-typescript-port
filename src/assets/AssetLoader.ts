import { AssetDescriptor, AssetManifest, AssetType, createDefaultAssetManifest } from './AssetManifest';

export type LoadedAsset = {
  id: string;
  type: AssetType;
  src: string;
  ready: boolean;
  url: string;
  metadata?: Record<string, unknown>;
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
    const loadedAsset: LoadedAsset = {
      id: asset.id,
      type: asset.type,
      src: asset.src,
      ready: true,
      url,
      metadata: asset.metadata,
    };

    this.loadedAssets.set(asset.id, loadedAsset);
    return loadedAsset;
  }

  private resolveAssetUrl(asset: AssetDescriptor): string {
    const relativeSource = asset.path ?? asset.src;
    return `${this.manifest.basePath.replace(/\/$/, '')}/${relativeSource.replace(/^\//, '')}`;
  }
}
