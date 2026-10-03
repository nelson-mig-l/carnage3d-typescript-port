export type GamepadAction = 'moveUp' | 'moveDown' | 'moveLeft' | 'moveRight' | 'action' | 'shoot' | 'hudToggle' | 'interact';

export class GamepadInput {
  private readonly state = new Map<GamepadAction, boolean>();

  update(): void {
    const gamepads = typeof navigator === 'undefined' ? [] : navigator.getGamepads ? navigator.getGamepads() : [];

    this.state.clear();

    for (const gamepad of gamepads) {
      if (!gamepad) {
        continue;
      }

      this.state.set('moveUp', (gamepad.axes[1] ?? 0) < -0.2 || this.state.get('moveUp') === true);
      this.state.set('moveDown', (gamepad.axes[1] ?? 0) > 0.2 || this.state.get('moveDown') === true);
      this.state.set('moveLeft', (gamepad.axes[0] ?? 0) < -0.2 || this.state.get('moveLeft') === true);
      this.state.set('moveRight', (gamepad.axes[0] ?? 0) > 0.2 || this.state.get('moveRight') === true);

      const actionPressed = gamepad.buttons[0]?.pressed ?? false;
      const shootPressed = gamepad.buttons[7]?.pressed ?? false;
      const interactPressed = gamepad.buttons[1]?.pressed ?? false;
      const hudTogglePressed = gamepad.buttons[9]?.pressed ?? false;

      this.state.set('action', actionPressed || this.state.get('action') === true);
      this.state.set('shoot', shootPressed || this.state.get('shoot') === true);
      this.state.set('interact', interactPressed || this.state.get('interact') === true);
      this.state.set('hudToggle', hudTogglePressed || this.state.get('hudToggle') === true);
    }
  }

  isPressed(action: GamepadAction): boolean {
    return this.state.get(action) ?? false;
  }
}
