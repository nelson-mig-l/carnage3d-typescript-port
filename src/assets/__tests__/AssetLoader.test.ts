import { describe, expect, it } from 'vitest';
import { AssetLoader } from '../AssetLoader';
import { createDefaultAssetManifest } from '../AssetManifest';

describe('AssetLoader', () => {
  it('loads a manifest and exposes placeholder assets without crashing', async () => {
    const loader = new AssetLoader(createDefaultAssetManifest());

    const loaded = await loader.loadAll();

    expect(loaded).toBeTruthy();
    expect(Object.keys(loaded)).toHaveLength(4);
    expect(loader.getAsset('ui.cursor')).toMatchObject({ id: 'ui.cursor', type: 'texture' });
    expect(loader.getAsset('ui.font')).toMatchObject({ id: 'ui.font', type: 'font' });
  });
});
