export interface GameState {
  enter?: () => unknown;
  update?: (delta: number) => unknown;
  leave?: () => unknown;
  render?: () => unknown;
}

export class StateMachine<StateKey extends string = string> {
  private readonly states = new Map<StateKey, GameState>();
  private currentKey: StateKey | null = null;
  private activeState: GameState | null = null;

  register(name: StateKey, state: GameState): void {
    this.states.set(name, state);
  }

  get currentState(): StateKey | null {
    return this.currentKey;
  }

  get currentStateName(): StateKey | null {
    return this.currentKey;
  }

  has(name: StateKey): boolean {
    return this.states.has(name);
  }

  enter(name: StateKey): void {
    const nextState = this.states.get(name);

    if (!nextState) {
      throw new Error(`Unknown game state: ${name}`);
    }

    if (this.activeState?.leave) {
      this.activeState.leave();
    }

    this.currentKey = name;
    this.activeState = nextState;

    if (this.activeState.enter) {
      this.activeState.enter();
    }
  }

  update(delta: number): unknown {
    if (!this.activeState || !this.activeState.update) {
      return undefined;
    }

    return this.activeState.update(delta);
  }

  render(): void {
    if (this.activeState?.render) {
      this.activeState.render();
    }
  }
}
