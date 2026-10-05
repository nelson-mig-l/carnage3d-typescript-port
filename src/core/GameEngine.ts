import { AssetLoader } from '../assets/AssetLoader';
import { GameplayState } from '../game/GameplayState';
import { MainMenuState } from '../game/MainMenuState';
import { InputManager } from '../input/InputManager';
import { RenderEngine } from '../graphics/RenderEngine';
import { createEngineConfig, EngineConfig } from './EngineConfig';
import { GameLoop } from './GameLoop';
import { GameState, StateMachine } from './StateMachine';

export class GameEngine {
  private readonly config: EngineConfig;
  private readonly renderEngine: RenderEngine;
  private readonly assetLoader: AssetLoader;
  private readonly inputManager: InputManager;
  private readonly stateMachine: StateMachine;
  private readonly gameLoop: GameLoop;
  private started = false;

  constructor(canvas?: HTMLCanvasElement | string | null, config: Partial<EngineConfig> = {}) {
    this.config = createEngineConfig(config);
    this.renderEngine = new RenderEngine(canvas);
    this.assetLoader = new AssetLoader();
    this.inputManager = new InputManager();
    this.stateMachine = new StateMachine();
    this.stateMachine.register('boot', {
      enter: () => undefined,
      update: () => undefined,
      leave: () => undefined,
      render: () => this.renderEngine.render(),
    });
    this.stateMachine.register('mainMenu', new MainMenuState());
    this.stateMachine.register('gameplay', new GameplayState());

    this.gameLoop = new GameLoop((delta) => this.tick(delta), this.config);
  }

  registerState(name: string, state: GameState): void {
    this.stateMachine.register(name, state);
  }

  getRenderEngine(): RenderEngine {
    return this.renderEngine;
  }

  getInputManager(): InputManager {
    return this.inputManager;
  }

  getCurrentState(): string | null {
    return this.stateMachine.currentState;
  }

  async start(): Promise<void> {
    if (this.started) {
      return;
    }

    this.started = true;
    const assets = await this.assetLoader.loadAll();
    this.renderEngine.showLoadedAssets(assets);
    this.inputManager.bindKeyboard();
    this.stateMachine.enter('mainMenu');
    this.gameLoop.start();
  }

  stop(): void {
    this.gameLoop.stop();
  }

  private tick(delta: number): void {
    this.renderEngine.beginFrame();
    this.inputManager.update(delta);
    this.stateMachine.update(delta);
    this.stateMachine.render();
    this.renderEngine.render();
  }
}
