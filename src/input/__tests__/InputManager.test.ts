import { describe, expect, it } from 'vitest';
import { InputManager } from '../InputManager';

describe('InputManager', () => {
  it('normalizes keyboard actions and movement keys', () => {
    const manager = new InputManager();

    manager.bindKeyboard();
    manager.pressKey('w');
    manager.pressKey(' ');
    manager.pressKey('enter');

    expect(manager.isPressed('moveUp')).toBe(true);
    expect(manager.isPressed('action')).toBe(true);
    expect(manager.isPressed('interact')).toBe(true);
    expect(manager.isPressed('shoot')).toBe(false);
  });
});
