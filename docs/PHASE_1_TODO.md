# What still needs to be done

## 1. Real browser render proof [DONE]
* The app should be launched in a browser and visually confirmed to show a Babylon scene.
* This is the main unproven item relative to the Phase 1 acceptance criteria.
* The render shell exists in RenderEngine.ts, but a real browser visual check is still the final validation step.
## 2. Live input wiring in the engine loop [DONE]
* `InputManager.ts` is now actively bound during engine startup and polled on each game-loop tick in `GameEngine.ts`.
* This makes keyboard action transitions visible in the live runtime rather than only in tests.
## 3. Real state boot flow [DONE]
* `StateMachine.ts` is working in tests and the engine now registers and enters runtime states such as `MainMenuState.ts` and `GameplayState.ts` during startup.
* The game boots into the live main menu state instead of remaining in the placeholder boot state.
## 4. App bootstrap smoke test in the browser [DONE]
* The game should start cleanly, enter a state, and remain stable without console errors.
* This is the “App boots / Scene renders / State machine works” definition-of-done check.
## 5. Asset loader runtime wiring [DONE]
`AssetLoader.ts` is in place, but the runtime should load from a real asset path model and not just a placeholder manifest.
