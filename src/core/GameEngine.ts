import { AssetLoader } from '../assets/AssetLoader';
import { createEngineConfig, EngineConfig } from './EngineConfig';
import { GameLoop } from './GameLoop';
import { GameState, StateMachine } from './StateMachine';
import { RenderEngine } from '../graphics/RenderEngine';

export class GameEngine {
  private readonly config: EngineConfig;
  private readonly renderEngine: RenderEngine;
  private readonly assetLoader: AssetLoader;
  private readonly stateMachine: StateMachine;
  private readonly gameLoop: GameLoop;
  private started = false;

  constructor(canvas?: HTMLCanvasElement | string | null, config: Partial<EngineConfig> = {}) {
    this.config = createEngineConfig(config);
    this.renderEngine = new RenderEngine(canvas);
    this.assetLoader = new AssetLoader();
    this.stateMachine = new StateMachine();
    this.stateMachine.register('boot', {
      enter: () => undefined,
      update: () => undefined,
      leave: () => undefined,
      render: () => this.renderEngine.render(),
    });

    this.gameLoop = new GameLoop((delta) => this.tick(delta), this.config);
  }

  registerState(name: string, state: GameState): void {
    this.stateMachine.register(name, state);
  }

  getRenderEngine(): RenderEngine {
    return this.renderEngine;
  }

  async start(): Promise<void> {
    if (this.started) {
      return;
    }

    this.started = true;
    await this.assetLoader.loadAll();
    this.stateMachine.enter('boot');
    this.gameLoop.start();
  }

  stop(): void {
    this.gameLoop.stop();
  }

  private tick(delta: number): void {
    this.renderEngine.beginFrame();
    this.stateMachine.update(delta);
    this.stateMachine.render();
  }
}
