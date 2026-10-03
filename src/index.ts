import './styles.css';

export { createEngineConfig, DEFAULT_ENGINE_CONFIG } from './core/EngineConfig';
export type { EngineConfig } from './core/EngineConfig';
export { GameEngine } from './core/GameEngine';
export { GameLoop } from './core/GameLoop';
export { StateMachine } from './core/StateMachine';
export type { GameState } from './core/StateMachine';
export { RenderEngine } from './graphics/RenderEngine';
export { InputManager } from './input/InputManager';
export type { InputAction, InputKeyMap } from './input/InputManager';
export { KeyboardInput } from './input/KeyboardInput';
export { GamepadInput } from './input/GamepadInput';

const appHost = document.querySelector('#app');

if (appHost) {
  const canvases = appHost.querySelectorAll('canvas');
  if (canvases.length === 0) {
    const canvas = document.createElement('canvas');
    canvas.id = 'game-canvas';
    appHost.appendChild(canvas);

    const { GameEngine } = await import('./core/GameEngine');
    const engine = new GameEngine(canvas);
    void engine.start();
  }
}
