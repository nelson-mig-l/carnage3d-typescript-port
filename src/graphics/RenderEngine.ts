import * as BABYLON from 'babylonjs';
import { CameraRig } from './CameraRig';
import { SceneManager } from './SceneManager';

export class RenderEngine {
  private canvas: HTMLCanvasElement | null;
  private readonly engine: BABYLON.Engine | null;
  private readonly scene: BABYLON.Scene | null;
  private readonly camera: BABYLON.Camera | null;
  private readonly cameraRig: CameraRig | null;
  private readonly sceneManager: SceneManager | null;

  private deltaTime = 0;
  private elapsedTime = 0;
  private lastTimestamp = 0;

  constructor(canvasOrSelector?: HTMLCanvasElement | string | null) {
    this.canvas = this.resolveCanvas(canvasOrSelector ?? null);

    if (!this.canvas && typeof document !== 'undefined') {
      this.canvas = document.createElement('canvas');
    }

    if (!this.canvas) {
      this.engine = null;
      this.scene = null;
      this.camera = null;
      this.cameraRig = null;
      this.sceneManager = null;
      return;
    }

    this.engine = new BABYLON.Engine(this.canvas, true, { preserveDrawingBuffer: true, antialias: true });
    this.scene = new BABYLON.Scene(this.engine);
    this.cameraRig = new CameraRig(this.scene);
    this.camera = this.cameraRig.getCamera();
    this.sceneManager = new SceneManager(this.scene);

    this.scene.clearColor = new BABYLON.Color4(0.06, 0.08, 0.12, 1);
    this.engine.runRenderLoop(() => this.scene?.render());

    if (typeof window !== 'undefined') {
      window.addEventListener('resize', () => this.engine?.resize());
    }
  }

  private resolveCanvas(canvasOrSelector: HTMLCanvasElement | string | null): HTMLCanvasElement | null {
    if (canvasOrSelector instanceof HTMLCanvasElement) {
      return canvasOrSelector;
    }

    if (typeof canvasOrSelector === 'string' && typeof document !== 'undefined') {
      const element = document.querySelector(canvasOrSelector);
      return element instanceof HTMLCanvasElement ? element : null;
    }

    if (typeof document !== 'undefined') {
      return document.querySelector('canvas') as HTMLCanvasElement | null;
    }

    return null;
  }

  attachCanvas(canvas: HTMLCanvasElement | string | null): void {
    if (!canvas) {
      this.canvas = null;
      return;
    }

    const resolved = this.resolveCanvas(canvas);
    if (resolved) {
      this.canvas = resolved;
    }
  }

  getCanvas(): HTMLCanvasElement | null {
    return this.canvas;
  }

  getScene(): BABYLON.Scene | null {
    return this.scene;
  }

  getCamera(): BABYLON.Camera | null {
    return this.camera;
  }

  beginFrame(): void {
    const now = performance.now();

    if (this.lastTimestamp === 0) {
      this.deltaTime = 0;
    } else {
      this.deltaTime = (now - this.lastTimestamp) / 1000;
    }

    this.lastTimestamp = now;
    this.elapsedTime += this.deltaTime;
  }

  render(): void {
    if (!this.scene) {
      return;
    }

    this.scene.render();
  }

  getDeltaTime(): number {
    return this.deltaTime;
  }

  getElapsedTime(): number {
    return this.elapsedTime;
  }

  dispose(): void {
    this.engine?.dispose();
    this.scene?.dispose();
  }
}
