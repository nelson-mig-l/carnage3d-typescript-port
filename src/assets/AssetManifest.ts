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
    basePath: '/assets',
    assets: [
      {
        id: 'ui.cursor',
        type: 'texture',
        src: 'textures/ui/cursor.png',
        metadata: { fallback: 'cursor' },
      },
      {
        id: 'ui.font',
        type: 'font',
        src: 'fonts/ui/default.ttf',
        metadata: { fallback: 'system-ui' },
      },
      {
        id: 'ui.button',
        type: 'sprite',
        src: 'sprites/ui/button.png',
        metadata: { atlas: 'ui' },
      },
      {
        id: 'sfx.click',
        type: 'sound',
        src: 'sounds/ui/click.wav',
        metadata: { loop: false },
      },
    ],
  };
}
