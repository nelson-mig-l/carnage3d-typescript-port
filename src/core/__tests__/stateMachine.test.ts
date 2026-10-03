import { describe, expect, it } from 'vitest';
import { StateMachine } from '../StateMachine';

describe('StateMachine', () => {
  it('transitions between states and updates the active state', () => {
    const machine = new StateMachine();

    machine.register('menu', {
      enter: () => 'menu-entered',
      update: (delta) => `menu:${delta}`,
      leave: () => 'menu-left',
    });

    machine.register('game', {
      enter: () => 'game-entered',
      update: (delta) => `game:${delta}`,
      leave: () => 'game-left',
    });

    machine.enter('menu');
    expect(machine.currentState).toBe('menu');
    expect(machine.update(0.5)).toBe('menu:0.5');

    machine.enter('game');
    expect(machine.currentState).toBe('game');
    expect(machine.update(0.25)).toBe('game:0.25');
  });
});
