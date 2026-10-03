import { describe, expect, it } from 'vitest';
import { GameStateMachine } from '../GameState';
import { MainMenuState } from '../MainMenuState';
import { GameplayState } from '../GameplayState';

describe('GameStateMachine', () => {
  it('transitions between menu and gameplay states without errors', () => {
    const machine = new GameStateMachine();
    const menuState = new MainMenuState();
    const gameplayState = new GameplayState();

    machine.enter(menuState);
    expect(() => machine.update(0.016)).not.toThrow();
    expect(() => machine.render()).not.toThrow();

    machine.enter(gameplayState);
    expect(() => machine.update(0.016)).not.toThrow();
    expect(() => machine.render()).not.toThrow();
  });
});
