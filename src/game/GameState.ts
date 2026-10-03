export interface GameState {
  enter?: () => unknown;
  update?: (delta: number) => unknown;
  render?: () => unknown;
  leave?: () => unknown;
}

export class GameStateMachine {
  private current: GameState | null = null;

  enter(state: GameState): void {
    this.current?.leave?.();
    this.current = state;
    this.current.enter?.();
  }

  update(delta: number): unknown {
    return this.current?.update?.(delta);
  }

  render(): void {
    this.current?.render?.();
  }
}
