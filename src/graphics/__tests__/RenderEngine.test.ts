import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('babylonjs', () => {
  class MockEngine {
    public canvas: HTMLCanvasElement;
    public scene: MockScene;

    constructor(canvas: HTMLCanvasElement) {
      this.canvas = canvas;
      this.scene = new MockScene();
    }

    resize = vi.fn();
    dispose = vi.fn();
  }

  class MockScene {
    clearColor: unknown;
    render = vi.fn();
    dispose = vi.fn();
    getEngine = vi.fn(() => ({
      getRenderingCanvas: vi.fn(() => document.createElement('canvas')),
    }));
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
    },
  };
});

import { RenderEngine } from '../RenderEngine';

describe('RenderEngine', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
  });

  it('creates a scene, camera and light setup without throwing', () => {
    const canvas = document.createElement('canvas');
    const engine = new RenderEngine(canvas);

    expect(engine.getCanvas()).toBe(canvas);
    expect(engine.getScene()).toBeDefined();
    expect(engine.getCamera()).toBeDefined();
    expect(engine.getDeltaTime()).toBe(0);

    engine.dispose();
  });

  it('renders only when explicitly requested', () => {
    const renderer = new RenderEngine(document.createElement('canvas'));
    const scene = renderer.getScene();
    const render = vi.spyOn(scene!, 'render');

    renderer.render();

    expect(render).toHaveBeenCalledTimes(1);

    renderer.dispose();
  });

  it('removes the resize listener when disposed', () => {
    const addEventListener = vi.spyOn(window, 'addEventListener');
    const removeEventListener = vi.spyOn(window, 'removeEventListener');
    const engine = new RenderEngine(document.createElement('canvas'));
    const resizeHandler = addEventListener.mock.calls.find(([type]) => type === 'resize')?.[1];

    expect(resizeHandler).toBeDefined();

    engine.dispose();

    expect(removeEventListener).toHaveBeenCalledWith('resize', resizeHandler);

    addEventListener.mockRestore();
    removeEventListener.mockRestore();
  });
});
