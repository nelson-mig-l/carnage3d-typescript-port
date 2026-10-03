import { GamepadInput } from './GamepadInput';
import { KeyboardInput } from './KeyboardInput';

export type InputAction =
  | 'moveUp'
  | 'moveDown'
  | 'moveLeft'
  | 'moveRight'
  | 'action'
  | 'shoot'
  | 'hudToggle'
  | 'interact';

export type InputKeyMap = Partial<Record<InputAction, string[]>>;

export class InputManager {
  private readonly keyboard = new KeyboardInput();
  private readonly gamepad = new GamepadInput();
  private readonly actionState = new Map<InputAction, boolean>();

  private readonly keyMap: InputKeyMap = {
    moveUp: ['arrowup', 'w', 'w', 'space'],
    moveDown: ['arrowdown', 's'],
    moveLeft: ['arrowleft', 'a'],
    moveRight: ['arrowright', 'd'],
    action: [' ', 'space', 'spacebar'],
    shoot: ['control', 'ctrl'],
    hudToggle: ['tab'],
    interact: ['enter'],
  };

  bindKeyboard(): void {
    this.keyboard.bindKeyboard();
  }

  pressKey(key: string): void {
    this.keyboard.pressKey(key);
    this.logActionStateForKey(key);
  }

  releaseKey(key: string): void {
    this.keyboard.releaseKey(key);
    this.logActionStateForKey(key);
  }

  update(_delta: number): void {
    this.gamepad.update();

    for (const action of Object.keys(this.keyMap) as InputAction[]) {
      const isPressed = this.isPressed(action);
      const previous = this.actionState.get(action) ?? false;

      if (previous !== isPressed) {
        this.actionState.set(action, isPressed);
        console.log(`Input action ${action}: ${isPressed ? 'enabled' : 'disabled'}`);
      }
    }
  }

  isPressed(action: InputAction): boolean {
    const mappedKeys = this.keyMap[action] ?? [];

    if (mappedKeys.some((key) => this.keyboard.isKeyDown(key))) {
      return true;
    }

    return this.gamepad.isPressed(action);
  }

  getKeyMap(): InputKeyMap {
    return { ...this.keyMap };
  }

  private logActionStateForKey(key: string): void {
    for (const action of Object.keys(this.keyMap) as InputAction[]) {
      const mappedKeys = this.keyMap[action] ?? [];

      if (mappedKeys.includes(key.toLowerCase())) {
        const isPressed = this.isPressed(action);
        console.log(`Input action ${action}: ${isPressed ? 'enabled' : 'disabled'} via key ${key}`);
      }
    }
  }
}
