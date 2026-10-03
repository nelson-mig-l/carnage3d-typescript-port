import { EngineConfig, DEFAULT_ENGINE_CONFIG } from './EngineConfig';

export class GameLoop {
  private rafId: number | null = null;
  private active = false;
  private lastFrameTimestamp = 0;

  constructor(
    private readonly onTick: (deltaTime: number) => void,
    private readonly config: EngineConfig = DEFAULT_ENGINE_CONFIG,
  ) {}

  start(): void {
    if (this.active) {
      return;
    }

    this.active = true;
    this.lastFrameTimestamp = 0;
    this.rafId = window.requestAnimationFrame((timestamp) => this.step(timestamp));
  }

  stop(): void {
    this.active = false;

    if (this.rafId !== null) {
      window.cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
  }

  private step(timestamp: number): void {
    if (!this.active) {
      return;
    }

    const deltaTime = this.lastFrameTimestamp === 0 ? 0 : (timestamp - this.lastFrameTimestamp) / 1000;
    this.lastFrameTimestamp = timestamp;

    this.onTick(Math.min(deltaTime, 1 / this.config.targetFps));

    this.rafId = window.requestAnimationFrame((nextTimestamp) => this.step(nextTimestamp));
  }
}
