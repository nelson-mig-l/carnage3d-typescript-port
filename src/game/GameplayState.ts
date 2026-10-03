import { GameState } from './GameState';

export class GameplayState implements GameState {
  private readonly id = 'gameplay';

  enter(): void {
    console.log(`Entered ${this.id} state`);
  }

  update(_delta: number): void {
    // gameplay logic placeholder
  }

  render(): void {
    // gameplay render placeholder
  }

  leave(): void {
    console.log(`Left ${this.id} state`);
  }
}
