# Carnage3D TypeScript Port — Issue List

Repository reviewed: `nelson-mig-l/javascript-theft-auto`  
Branch: `main`

## High Priority

1. **Scene rendered twice per frame**
   - `RenderEngine` starts Babylon's `engine.runRenderLoop()`.
   - `GameLoop` separately schedules the game loop.
   - `GameEngine.tick()`/state rendering can call `scene.render()` again.
   - This creates two competing render paths and can result in duplicate rendering.

2. **`fixedTimeStep` is unused**
   - `EngineConfig` exposes `fixedTimeStep`, but `GameLoop` does not implement an accumulator/fixed-step update.
   - There is also no physics update integrated into the loop.

3. **Delta time is incorrectly capped**
   - `GameLoop` uses `Math.min(deltaTime, 1 / targetFps)`.
   - This caps simulation time to the target frame interval rather than using `targetFps` as a frame-rate setting.
   - At lower target FPS values, real elapsed time can be discarded, causing simulation slowdown.

4. **Input system is not connected to the engine**
   - `InputManager` exists but is not constructed/updated by `GameEngine`.
   - Keyboard bindings are therefore never activated by the normal runtime.

5. **Engine starts in `boot` instead of the main menu**
   - `GameEngine.start()` enters the `boot` state.
   - `MainMenuState` is not registered or entered by the runtime.
   - This conflicts with the Phase 1 architecture/documentation.

## Medium Priority

6. **`AssetLoader` does not actually load assets**
   - `loadAsset()` effectively marks an asset as ready without fetching, decoding, or validating the resource.
   - Missing files can therefore appear successfully loaded.

7. **Default asset manifest points to resources that are not present**
   - Manifest entries reference paths such as:
     - `/assets/textures/ui/cursor.png`
     - `/assets/fonts/ui/default.ttf`
     - `/assets/sprites/ui/button.png`
     - `/assets/sounds/ui/click.wav`
   - The corresponding web assets are not present in the TypeScript asset tree.

8. **`RenderEngine.attachCanvas()` does not reinitialize Babylon**
   - It replaces the stored canvas reference but the Babylon `Engine` was already constructed with the original canvas.
   - Attaching a different canvas therefore does not actually move rendering to it.

9. **Resize event listener is leaked**
   - `RenderEngine` installs an anonymous `window.resize` callback.
   - `dispose()` cannot remove that callback.
   - Recreating the renderer can accumulate event listeners.

10. **Two independent render-loop owners**
    - Babylon's `runRenderLoop()` and the application's `GameLoop` both act as frame schedulers.
    - There should be one authoritative game-frame scheduler.

11. **Two state-machine implementations**
    - `src/core/StateMachine.ts`
    - `src/game/GameState.ts` / `GameStateMachine`
    - Both model state transitions.
    - `GameEngine` uses the core state machine while game states use the game-specific one.
    - This creates an architectural split.

12. **`MainMenuState` and `GameplayState` are effectively disconnected**
    - They contain little/no gameplay behavior.
    - They are not integrated into the engine's active state flow.

13. **Input mapping is not actually configurable**
    - The documentation calls for configurable action mappings.
    - `InputManager` provides no public API/constructor configuration for changing bindings.

14. **Duplicate/ambiguous keyboard mappings**
    - `moveUp` contains `w` twice.
    - `Space` is used for both `moveUp` and `action`.
    - These mappings should be deliberate and documented.

15. **Keyboard listeners cannot be removed**
    - `KeyboardInput.bindKeyboard()` installs event listeners but there is no corresponding unbind/dispose operation.
    - This can cause duplicate handlers after reinitialization.

16. **Gamepad input is globally merged**
    - Input from all connected gamepads is combined into the same action state.
    - There is no controller/player ownership model.

## Testing Issues

17. **Tests do not cover the main runtime failures**
    - No meaningful `GameLoop` tests.
    - No integration test for `GameEngine.start()`.
    - No test proving input reaches gameplay.
    - No test for delta-time behavior.
    - No test verifying actual asset loading.

18. **Babylon mocks hide render-loop problems**
    - The renderer tests mock `runRenderLoop()`.
    - The tests therefore cannot expose the application's competing render loops.

19. **Smoke tests do not validate the real Babylon runtime**
    - Babylon is mocked rather than exercised.
    - Passing tests do not prove that the browser/WebGL scene actually boots.

20. **No clear CI validation for the TypeScript application**
    - The repository does not appear to have a root-level CI workflow that validates the TypeScript build/test pipeline.
    - Existing workflows under the original `carnage` tree belong to the C++ project.

## Repository / Build Issues

21. **`node_modules` is committed**
    - This contradicts the repository's own development guidance.
    - It unnecessarily increases repository size and can introduce platform/version-specific files.

22. **`npm run build` does not create a production build**
    - The build command is effectively `tsc --noEmit`.
    - It type-checks the project but does not run Vite's production bundler.
    - A successful command therefore does not prove that a deployable web bundle can be produced.

23. **`renderScale` configuration is unused**
    - The option exists in `EngineConfig` but has no observable effect.

24. **`enableDebugOverlay` configuration is unused**
    - The option exists but is not consumed by the runtime.

25. **Major declared dependencies are not integrated**
    - `cannon-es`, `howler`, `zod`, and other planned dependencies are currently not meaningfully connected to the runtime.
    - This is acceptable for a scaffold only if the project clearly treats them as future dependencies.

## Architectural Summary

The largest structural problem is the presence of competing runtime models:

```text
Babylon runRenderLoop()
        +
GameLoop requestAnimationFrame()
        +
core StateMachine
        +
game GameStateMachine
```

The intended architecture should have one authoritative game loop:

```text
GameEngine
 ├── InputManager
 ├── AssetLoader
 ├── StateMachine
 ├── PhysicsEngine
 └── RenderEngine

GameLoop
 └── one requestAnimationFrame
      ├── input.update()
      ├── stateMachine.update()
      ├── physics.update()
      └── renderEngine.render()
```

## Recommended Fix Order
1. Unify the render/game loop.
2. Choose one state-machine implementation.
3. Integrate InputManager into GameEngine.
4. Correct delta-time/fixed-step handling.
5. Make asset loading perform real resource validation/loading.
6. Add proper lifecycle/dispose methods for event listeners.
7. Integrate the actual menu/gameplay states.
8. Replace superficial smoke tests with runtime/integration tests.
9. Make npm run build produce a real Vite production bundle.
10. Add CI for type-check, tests, and production build.
