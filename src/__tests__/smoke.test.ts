import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('babylonjs', () => {
  class MockEngine {
    canvas: HTMLCanvasElement;
    scene: MockScene;

    constructor(canvas: HTMLCanvasElement) {
      this.canvas = canvas;
      this.scene = new MockScene();
    }

    resize = vi.fn();
    dispose = vi.fn();
    getDeltaTime = vi.fn(() => 16.67);
  }

  class MockScene {
    clearColor: unknown;
    render = vi.fn();
    dispose = vi.fn();
    getEngine = vi.fn(() => ({ getRenderingCanvas: vi.fn(() => document.createElement('canvas')) }));
    getMeshByName = vi.fn(() => undefined);
  }

  class MockCamera {
    position = { x: 0, y: 0, z: 0 };
    setTarget = vi.fn();
    attachControl = vi.fn();
  }

  class MockLight {}

  class MockGround {
    position = { y: 0 };
  }

  return {
    Engine: MockEngine,
    Scene: MockScene,
    FreeCamera: MockCamera,
    HemisphericLight: MockLight,
    Vector3: class {
      static Zero = vi.fn(() => new (class {
        x = 0;
        y = 0;
        z = 0;
      })());

      constructor(public x: number, public y: number, public z: number) {}
    },
    Color4: class {
      constructor(public r: number, public g: number, public b: number, public a: number) {}
    },
    MeshBuilder: {
      CreateGround: vi.fn(() => new MockGround()),
      CreateSphere: vi.fn(() => ({ position: { y: 0 } })),
      CreateBox: vi.fn(() => ({ position: { x: 0, y: 0, z: 0 }, material: undefined, dispose: vi.fn() })),
    },
  };

});

import { GameEngine } from '../core/GameEngine';
import { StateMachine } from '../core/StateMachine';
import { AssetLoader } from '../assets/AssetLoader';
import { Howl } from 'howler';
import { createDefaultAssetManifest } from '../assets/AssetManifest';
import { RenderEngine } from '../graphics/RenderEngine';

vi.mock('howler', () => ({
  Howl: class {
    constructor(options: { onload?: () => void }) {
      queueMicrotask(() => options.onload?.());
    }

    play = vi.fn();
  },
}));


describe('Phase 1 smoke tests', () => {
  beforeEach(() => {
    document.body.innerHTML = '';

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
        add: vi.fn(),
      },
    });
  });
  it('constructs GameEngine without throwing', () => {
    const canvas = document.createElement('canvas');

    expect(() => new GameEngine(canvas)).not.toThrow();
  });

  it('renders the scene once per game-loop tick', async () => {
    const callbacks: FrameRequestCallback[] = [];
    const requestAnimationFrame = vi.spyOn(window, 'requestAnimationFrame').mockImplementation((callback) => {
      callbacks.push(callback);
      return callbacks.length;
    });
    const engine = new GameEngine(document.createElement('canvas'));
    const scene = engine.getRenderEngine().getScene();
    const render = vi.spyOn(scene!, 'render');

    await engine.start();

    expect(render).not.toHaveBeenCalled();
    expect(requestAnimationFrame).toHaveBeenCalledTimes(1);

    callbacks.shift()?.(16.67);

    expect(render).toHaveBeenCalledTimes(1);
    expect(requestAnimationFrame).toHaveBeenCalledTimes(2);

    engine.stop();
    requestAnimationFrame.mockRestore();
  });

  it('binds and updates the input manager during engine startup', async () => {
    const callbacks: FrameRequestCallback[] = [];
    const requestAnimationFrame = vi.spyOn(window, 'requestAnimationFrame').mockImplementation((callback) => {
      callbacks.push(callback);
      return callbacks.length;
    });

    const engine = new GameEngine(document.createElement('canvas'));
    const inputManager = engine.getInputManager();
    const bindKeyboard = vi.spyOn(inputManager, 'bindKeyboard');
    const update = vi.spyOn(inputManager, 'update');

    await engine.start();

    expect(bindKeyboard).toHaveBeenCalledTimes(1);
    expect(update).not.toHaveBeenCalled();

    callbacks.shift()?.(16.67);

    expect(update).toHaveBeenCalledTimes(1);

    engine.stop();
    requestAnimationFrame.mockRestore();
  });

  it('creates a RenderEngine with a canvas and valid Babylon scene', () => {
    const canvas = document.createElement('canvas');
    const renderEngine = new RenderEngine(canvas);

    expect(renderEngine.getCanvas()).toBe(canvas);
    expect(renderEngine.getScene()).toBeTruthy();
    expect(renderEngine.getCamera()).toBeTruthy();
  });

  it('transitions a state machine between states', () => {
    const machine = new StateMachine();

    machine.register('boot', {
      enter: () => undefined,
      update: () => undefined,
      leave: () => undefined,
      render: () => undefined,
    });

    machine.register('mainMenu', {
      enter: () => undefined,
      update: () => undefined,
      leave: () => undefined,
      render: () => undefined,
    });

    machine.enter('boot');
    machine.enter('mainMenu');

    expect(machine.currentState).toBe('mainMenu');
    expect(() => machine.update(0.016)).not.toThrow();
    expect(() => machine.render()).not.toThrow();
  });

  it('enters the runtime main menu state during engine startup', async () => {
    const engine = new GameEngine(document.createElement('canvas'));

    await engine.start();

    expect(engine.getCurrentState()).toBe('mainMenu');
    engine.stop();
  });

  it('initializes an asset manifest via the loader', async () => {
    const loader = new AssetLoader(createDefaultAssetManifest());
    const result = await loader.loadAll();

    expect(result).toBeTruthy();
    expect(Object.keys(result.textures)).toHaveLength(1);
    expect(Object.keys(result.fonts)).toHaveLength(1);
    expect(Object.keys(result.sounds)).toHaveLength(1);
    expect(Object.keys(result.sprites)).toHaveLength(1);
    expect(loader.getAsset('test.texture')).toMatchObject({
      id: 'test.texture',
      type: 'texture',
      url: './assets/test/wood.png',
      ready: true,
    });
    expect(loader.getAsset('test.font')).toMatchObject({
      id: 'test.font',
      type: 'font',
      url: './assets/test/typewriter.ttf',
      ready: true,
    });
    expect(loader.getAsset('test.sprite')).toMatchObject({
      id: 'test.sprite',
      type: 'sprite',
      url: './assets/test/grass.png',
      ready: true,
    });
    expect(loader.getAsset('test.click')).toMatchObject({
      id: 'test.click',
      type: 'sound',
      url: './assets/test/click.wav',
      ready: true,
    });
  });
});
