import { GameState } from './GameState';

export class MainMenuState implements GameState {
  private readonly id = 'mainMenu';

  enter(): void {
    console.log(`Entered ${this.id} state`);
  }

  update(_delta: number): void {
    // menu logic placeholder
  }

  render(): void {
    // menu render placeholder
  }

  leave(): void {
    console.log(`Left ${this.id} state`);
  }
}
