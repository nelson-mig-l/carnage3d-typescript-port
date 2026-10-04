import { describe, expect, it } from 'vitest';
import { AssetLoader } from '../AssetLoader';
import { createDefaultAssetManifest } from '../AssetManifest';

describe('AssetLoader', () => {
  it('loads a manifest using the public assets path model and validates resource reachability', async () => {
    const loader = new AssetLoader(createDefaultAssetManifest());

    const loaded = await loader.loadAll();

    expect(loaded).toBeTruthy();
    expect(Object.keys(loaded)).toHaveLength(4);
    expect(loader.getAsset('ui.cursor')).toMatchObject({
      id: 'ui.cursor',
      type: 'texture',
      url: './assets/textures/ui/cursor.png',
      ready: true,
    });
    expect(loader.getAsset('ui.font')).toMatchObject({
      id: 'ui.font',
      type: 'font',
      url: './assets/fonts/ui/default.ttf',
      ready: true,
    });
  });
});
