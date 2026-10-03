export type KeyboardKey = string;

export class KeyboardInput {
  private readonly keyState = new Map<string, boolean>();
  private keyboardReady = false;

  bindKeyboard(): void {
    if (this.keyboardReady || typeof window === 'undefined') {
      return;
    }

    this.keyboardReady = true;

    const handleKeyDown = (event: KeyboardEvent): void => {
      this.keyState.set(this.normalizeKey(event.key), true);
      this.keyState.set(this.normalizeKey(event.code), true);
    };

    const handleKeyUp = (event: KeyboardEvent): void => {
      this.keyState.set(this.normalizeKey(event.key), false);
      this.keyState.set(this.normalizeKey(event.code), false);
    };

    const handleBlur = (): void => {
      this.keyState.clear();
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    window.addEventListener('blur', handleBlur);
  }

  pressKey(key: KeyboardKey): void {
    this.keyState.set(this.normalizeKey(key), true);
  }

  releaseKey(key: KeyboardKey): void {
    this.keyState.set(this.normalizeKey(key), false);
  }

  isKeyDown(key: KeyboardKey): boolean {
    return this.keyState.get(this.normalizeKey(key)) ?? false;
  }

  normalizeKey(key: KeyboardKey): string {
    return key.toLowerCase().trim();
  }
}
