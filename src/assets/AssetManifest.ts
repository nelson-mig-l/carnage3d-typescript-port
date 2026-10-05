export type AssetType = 'texture' | 'font' | 'sound' | 'sprite';

export interface AssetDescriptor {
  id: string;
  type: AssetType;
  src: string;
  path?: string;
  metadata?: Record<string, unknown>;
}

export interface AssetManifest {
  version: string;
  basePath: string;
  assets: AssetDescriptor[];
}

export function createDefaultAssetManifest(): AssetManifest {
  return {
    version: '1.0.0',
    basePath: './assets',
    assets: [
      {
        id: 'test.texture',
        type: 'texture',
        src: 'test/wood.png',
        metadata: { fallback: 'cursor' },
      },
      {
        id: 'test.font',
        type: 'font',
        src: 'test/typewriter.ttf',
        metadata: { fallback: 'system-ui' },
      },
      {
        id: 'test.sprite',
        type: 'sprite',
        src: 'test/grass.png',
        metadata: { atlas: 'ui' },
      },
      {
        id: 'test.click',
        type: 'sound',
        src: 'test/click.wav',
        metadata: { loop: false },
      },
    ],
  };
}
