import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AssetLoader } from '../AssetLoader';
import { createDefaultAssetManifest } from '../AssetManifest';

vi.mock('howler', () => ({
  Howl: class {
    constructor(options: { onload?: () => void }) {
      queueMicrotask(() => options.onload?.());
    }
  },
}));

describe('AssetLoader', () => {
  beforeEach(() => {
    const loadedFonts = new Set<FontFace>();

    class MockImage {
      onload?: () => void;
      onerror?: () => void;

      set src(_value: string) {
        queueMicrotask(() => this.onload?.());
      }
    }

    class MockFontFace {
      family: string;

      constructor(family: string, _source: string) {
        this.family = family;
      }

      load(): Promise<FontFace> {
        return Promise.resolve(this as unknown as FontFace);
      }
    }

    vi.stubGlobal('Image', MockImage);
    vi.stubGlobal('FontFace', MockFontFace);
    Object.defineProperty(document, 'fonts', {
      configurable: true,
      value: {
        add: (font: FontFace) => loadedFonts.add(font),
      },
    });
  });

  it('loads every asset from the real default manifest', async () => {
    const manifest = createDefaultAssetManifest();
    const loader = new AssetLoader(manifest);

    const loaded = await loader.loadAll();

    expect(manifest.assets).toHaveLength(4);
    expect(loaded.textures['test.texture']).toMatchObject({
      id: 'test.texture',
      type: 'texture',
      src: 'test/wood.png',
      url: './assets/test/wood.png',
      ready: true,
    });
    expect(loaded.fonts['test.font']).toMatchObject({
      id: 'test.font',
      type: 'font',
      src: 'test/typewriter.ttf',
      url: './assets/test/typewriter.ttf',
      ready: true,
    });
    expect(loaded.sprites['test.sprite']).toMatchObject({
      id: 'test.sprite',
      type: 'sprite',
      src: 'test/grass.png',
      url: './assets/test/grass.png',
      ready: true,
    });
    expect(loaded.sounds['test.click']).toMatchObject({
      id: 'test.click',
      type: 'sound',
      src: 'test/click.wav',
      url: './assets/test/click.wav',
      ready: true,
    });

    expect(Object.values(loaded.textures).every((asset) => asset.ready)).toBe(true);
    expect(Object.values(loaded.fonts).every((asset) => asset.ready)).toBe(true);
    expect(Object.values(loaded.sprites).every((asset) => asset.ready)).toBe(true);
    expect(Object.values(loaded.sounds).every((asset) => asset.ready)).toBe(true);
  });

  it('reports failed image resources instead of marking them ready', async () => {
    class FailingImage {
      onload?: () => void;
      onerror?: () => void;

      set src(_value: string) {
        queueMicrotask(() => this.onerror?.());
      }
    }

    vi.stubGlobal('Image', FailingImage);

    const loader = new AssetLoader({
      version: '1.0.0',
      basePath: './assets',
      assets: [{ id: 'missing.texture', type: 'texture', src: 'textures/missing.png' }],
    });

    const asset = await loader.loadAsset(loader.getManifest().assets[0]);

    expect(asset.ready).toBe(false);
    expect(asset.error).toContain('Failed to load image');
  });
});
