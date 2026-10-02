# Detailed Phase 1 plan

1. Define the target runtime architecture Goal:

Replace the native C++ engine bootstrap with a TypeScript app shell that can render a Babylon.js scene and start a game loop.

Deliverables:
* `src/core/GameEngine.ts`
* `src/core/GameLoop.ts`
* `src/core/EngineConfig.ts`
* `src/core/StateMachine.ts`
* `src/graphics/RenderEngine.ts`

Plan:
* Model the current top-level runtime in a simpler way:
* boot entry point
* engine lifecycle
* state machine
* render/update loop
* configuration layer
* Keep the structure similar to the C++ version so later gameplay code is easier to port.

Recommended architecture:
  GameEngine owns:
  * `RenderEngine`
  * `InputManager`
  * `AssetLoader`
  * `PhysicsEngine`
  * `StateMachine`
  GameLoop calls:
  * `stateMachine.update(delta)`
  * `physicsEngine.update(delta)`
  * `renderEngine.render()`

Example skeleton:
```ts
export class GameEngine {
  private renderEngine: RenderEngine;
  private inputManager: InputManager;
  private stateMachine: GameStateMachine;
  private assetLoader: AssetLoader;
  private physicsEngine: PhysicsEngine;

  constructor(canvas: HTMLCanvasElement) {
    this.renderEngine = new RenderEngine(canvas);
    this.inputManager = new InputManager();
    this.stateMachine = new GameStateMachine();
    this.assetLoader = new AssetLoader();
    this.physicsEngine = new PhysicsEngine();
  }

  async start(): Promise<void> {
    await this.assetLoader.loadAll();
    this.stateMachine.enter("mainMenu");
    this.runLoop();
  }

  private runLoop(): void {
    const delta = this.renderEngine.getDeltaTime();
    this.stateMachine.update(delta);
    this.physicsEngine.update(delta);
    this.inputManager.update(delta);
    this.renderEngine.render();
    requestAnimationFrame(() => this.runLoop());
  }
}
```
2. Set up the project scaffold Goal:

Create a working TypeScript + Babylon.js project with bundling and dev tooling.
Recommended structure:
* `package.json`
* `tsconfig.json`
* `vite.config.ts`
* `src/index.ts`
* `src/styles.css`
* `public/` for static assets
* `src/core/`
* `src/graphics/`
* `src/game/`
* `src/input/`
* `src/assets/`
* `src/physics/`
* `src/ui/`

Package setup:
* Use Vite for simple web dev experience
* Use TypeScript strict mode
* Add:
  * Babylon.js
  * Cannon-es or Rapier
  * Howler.js or Babylon Sound
  * Zod
  * Jimp or a custom image loader
  * Vitest for tests
  * ESLint + Prettier

Initial dependencies:
* babylonjs
* cannon-es
* howler
* zod
* jimp
* typescript
* vite
* vitest

3. Build the Babylon.js render shell Goal:
Replace the desktop OpenGL bootstrap with a browser canvas scene.

Create:
* `src/graphics/RenderEngine.ts`
* `src/graphics/SceneManager.ts`
* `src/graphics/CameraRig.ts`

Tasks:
* Create a canvas element for Babylon
* Initialize Babylon.Engine
* Create a Babylon.Scene
* Add:
  * camera
  * lights
  * ground or test plane
  * basic sky/background
* Add a basic render loop
* Ensure the engine can render at least one visible object immediately

Example:

```ts
export class RenderEngine {
  private engine: BABYLON.Engine;
  private scene: BABYLON.Scene;
  private camera: BABYLON.FreeCamera;

  constructor(canvas: HTMLCanvasElement) {
    this.engine = new BABYLON.Engine(canvas, true);
    this.scene = new BABYLON.Scene(this.engine);

    this.camera = new BABYLON.FreeCamera("camera", new BABYLON.Vector3(0, 5, -10), this.scene);
    this.camera.setTarget(BABYLON.Vector3.Zero());

    const light = new BABYLON.HemisphericLight("light", new BABYLON.Vector3(0, 1, 0), this.scene);

    const ground = BABYLON.MeshBuilder.CreateGround("ground", { width: 20, height: 20 }, this.scene);
    ground.position.y = -1;

    this.engine.runRenderLoop(() => this.scene.render());
  }

  getDeltaTime(): number {
    return this.engine.getDeltaTime() / 1000;
  }

  render(): void {
    this.scene.render();
  }
}
```
Acceptance criteria:

* Canvas renders a visible Babylon scene
* No runtime exceptions on load
* Scene updates on each frame
* Camera and lighting are stable
* 
4. Create a basic input abstraction Goal:
Replace the current GLFW-based input flow with a browser-safe abstraction.
Create:

* `src/input/InputManager.ts`
* `src/input/KeyboardInput.ts`
* `src/input/GamepadInput.ts`

Requirements:

* Keyboard events for movement and actions
* Basic mouse support
* Optional gamepad support via browser Gamepad API
* Configurable action mapping

Plan:
* Begin with a simple mapping:
  * Arrow keys / WASD = movement
  * Space = jump / action
  * Enter = interact
  * Ctrl = shoot
  * Tab = toggle HUD
* Mirror the key usage described in the repo README
Example mapping:

```ts
export type InputAction =
  | "moveUp"
  | "moveDown"
  | "moveLeft"
  | "moveRight"
  | "action"
  | "shoot"
  | "hudToggle";

export class InputManager {
  private keyState = new Map<string, boolean>();

  bindKeyboard(): void {
    window.addEventListener("keydown", (e) => {
      this.keyState.set(e.key.toLowerCase(), true);
    });

    window.addEventListener("keyup", (e) => {
      this.keyState.set(e.key.toLowerCase(), false);
    });
  }

  isPressed(action: InputAction): boolean {
    // map action to keys
    return false;
  }

  update(_delta: number): void {
    // poll keys / gamepad
  }
}
```
Acceptance criteria:
* Input events are normalized into actions
* Keyboard movement fires reliably
* Basic actions are mapped

5. Build the state system Goal:
Match the original game-state approach without depending on C++ code.
Create:
* `src/game/GameState.ts`
* `src/game/MainMenuState.ts`
* `src/game/GameplayState.ts`
* `src/game/GameStateMachine.ts`

Core design:

* Every state has:
  * enter()
  * update(delta)
  * render()
  * leave()
This matches the conceptual flow in the repo:

* `GenericGamestate`
* `MainMenuGamestate`

Example:

```ts
export interface GameState {
  enter(): void;
  update(delta: number): void;
  render(): void;
  leave(): void;
}

export class GameStateMachine {
  private current: GameState | null = null;

  enter(state: GameState): void {
    this.current?.leave();
    this.current = state;
    this.current.enter();
  }

  update(delta: number): void {
    this.current?.update(delta);
  }

  render(): void {
    this.current?.render();
  }
}
```
Acceptance criteria:

* State transitions work
* There is a menu state and at least one gameplay state
* A blank game state can safely run without runtime errors

6. Add the asset loading foundation Goal:
Prepare the project to load game assets, even if they are not fully ported yet.

Create:
* `src/assets/AssetLoader.ts`
****src/assets/AssetManifest.ts`
Tasks:

* Create data structures for textures, fonts, sounds, and sprites
* Add placeholder loaders
* Decide how to handle original GTA1 files and config JSON
* Define the path model for:
  * `gamedata/`
  * static public resources
  * runtime bundles
Important early decision:

* For Phase 1, do not try to parse original GTA1 binary resources yet.
* Instead, stub in asset loading using placeholder textures and a manifest-based loader.
Example:

```ts
export class AssetLoader {
  async loadAll(): Promise<void> {
    // placeholder textures
    // config JSON
    // fonts
    // sounds
    // sprite atlases
  }
}
```
Acceptance criteria:

* Asset loader can initialize without crashing
* Placeholder assets load into a real runtime
* Future GTA1 data integration fits cleanly into this system

7. Create a test harness and smoke test Goal:
Confirm the engine bootstraps correctly before porting gameplay systems.
Create:

* `src/__tests__/smoke.test.ts`
* `vitest.config.ts`
Tests:

* `GameEngine` can instantiate without throwing
* `RenderEngine` can be created with a mock canvas
* `StateMachine` transitions
* `AssetLoader` can initialize a manifest
Minimal smoke test example:

```ts
import { describe, it, expect } from "vitest";

describe("GameEngine", () => {
  it("constructs without failing", () => {
    expect(true).toBe(true);
  });
});
```
Acceptance criteria:

* Tests run locally
* A basic smoke test passes
* Future port work can attach to the same validation flow
8. Decide the porting sequence for later phases Phase 1 is not the time to port everything. It should freeze the engine shell and confirm the architecture.
Recommended order after Phase 1:

* Phase 2: rendering and sprite layer
* Phase 3: input + state flow
* Phase 4: physics + vehicle motion
* Phase 5: game objects and AI
* Phase 6: HUD + UI
* Phase 7: audio
* Phase 8: asset loading and GTA1 resource compatibility

9. Deliverables for Phase 1 completion The phase is complete when all of the following exist:
* TypeScript project builds successfully
* Babylon scene renders on a canvas
* Input abstraction exists and responds to keyboard actions
* State machine can enter and update states
* Asset loader skeleton exists
* Unit test/smoke test passes
* Repo is ready for actual gameplay porting

10. Exit criteria / Definition of Done Go/no-go check:
* App boots
* Scene renders
* State machine works
* No blocking architecture decisions remain
* The repo has a stable runtime structure to port the engine

If all checks pass, proceed to Phase 2:
* sprite system
* texture mapping
* scene graph for game objects
* more realistic game-shell behavior

Recommended Phase 1 milestone structure

Milestone 1: Project bootstrap

* package setup, Vite, TS, lint/test config
* basic app shell
Milestone 2: Render skeleton

* Babylon canvas
* camera + lighting
* render loop
Milestone 3: App core

* input manager
* state machine
* engine bootstrap
Milestone 4: Validation

* smoke tests
* build confirmation
* repo ready for gameplay porting
