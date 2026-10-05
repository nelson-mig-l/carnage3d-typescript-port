# Phase 1 TODO / Completion Checklist

Phase 1 is the **Foundation & Architecture** milestone. It is complete when the TypeScript/Vite application has a stable browser runtime, the core engine shell is wired together, the state machine and input abstraction work, assets can be loaded through the runtime path model, and the validation checks pass.

## 1. Real browser render proof [DONE]

* Launch the application in a real browser and visually confirm that a Babylon.js scene renders on the canvas.
* Confirm that the canvas, camera, lighting, and scene remain stable during normal rendering.
* This satisfies the Phase 1 render-shell acceptance criterion.

## 2. Live input wiring in the engine loop [DONE]

* `InputManager.ts` is bound during engine startup.
* Keyboard actions are normalized through the input abstraction.
* Input is polled during each game-loop tick.
* The live runtime responds to the configured movement/action bindings.
* Gamepad support exists as an optional browser input path.

## 3. Real state boot flow [DONE]

* `StateMachine.ts` supports state registration, enter/update/render/leave, and transitions.
* `MainMenuState.ts` and `GameplayState.ts` are registered by `GameEngine`.
* The application enters `mainMenu` during startup.
* A state can safely update and render without runtime exceptions.

## 4. App bootstrap smoke test in the browser [DONE]

* The game starts cleanly in the browser.
* A Babylon scene is created and rendered.
* The state machine enters a runtime state.
* The game loop continues running after startup.
* No blocking JavaScript, module, Babylon/WebGL, or state-runtime errors appear in the browser console.

This is the Phase 1 **"App boots / Scene renders / State machine works"** definition-of-done check.

> Note: this is a browser acceptance test. Passing TypeScript compilation or unit tests alone does not prove the browser runtime is healthy.

## 5. Asset loader runtime wiring [DONE]

* `AssetLoader.ts` no longer treats an HTTP/resource reachability check as a successful load.
* Texture and sprite resources are loaded as real browser `Image` resources.
* Fonts are loaded through `FontFace` and registered with `document.fonts`.
* Sounds are loaded through Howler.
* Failed resources are reported with `ready: false` and an error instead of being falsely marked ready.
* Asset URLs are resolved through the manifest's `basePath` plus the asset descriptor path.
* The loader stores successfully loaded resources for later runtime use.

## 6. Remaining asset validation [TODO]

The loader implementation is complete, but Phase 1 should **not** be declared fully complete until the default manifest points at resources that actually exist.

### Required

* Add minimal real placeholder assets for every entry in the default manifest:
  * `public/assets/textures/ui/cursor.png`
  * `public/assets/fonts/ui/default.ttf`
  * `public/assets/sprites/ui/button.png`
  * `public/assets/sounds/ui/click.wav`
* Confirm the default manifest can load those resources successfully in the browser.
* Update/add smoke coverage so the real default asset-loading path is validated without relying on fake success.

### Why this matters

Phase 1 explicitly requires:

* the asset loader to initialize without crashing;
* placeholder assets to load into a real runtime;
* a path model that is ready for later GTA1 asset integration.

The current loader satisfies the implementation side of that requirement, but the repository currently does not contain the default placeholder resources. Until those files exist and load successfully, the asset-loading acceptance criterion remains incomplete.

## 7. Validation commands [TODO]

Before declaring Phase 1 complete, all of the following should pass:

* `npm test`
* `npm run build`
* `npm run bundle`
* Browser bootstrap smoke test with the default asset manifest

The browser check should confirm:

```
App loads
  -> Babylon initializes
  -> default assets load
  -> mainMenu state is entered
  -> game loop runs
  -> scene continues rendering
  -> no blocking console errors
```

## 8. Phase 1 scope boundary

The following are **not Phase 1 blockers** and should remain deferred to later phases:

* Cannon/Cannon-es physics implementation
* GTA1 `.cmp` map parsing
* GTA1 `.sty` resource parsing
* Sprite atlas/rendering system
* Gameplay entities
* Vehicles and vehicle physics
* Pedestrians and AI
* Weapons/projectiles
* HUD and full UI
* Full audio/gameplay integration
* GTA1 demo-level conversion

The strategic `TYPESCRIPT_PORT_PLAN.md` places physics in Phase 3 and the broader gameplay systems after the foundation. Do not pull those systems into Phase 1 merely because the initial `GameEngine` architecture anticipates them.

## 9. Tooling cleanup [OPTIONAL]

The repository declares an `npm run lint` command, but Phase 1 does not currently require linting as an exit criterion.

* Add/verify an ESLint configuration if linting is intended to be part of the project gate.
* Do not block Phase 1 completion on this unless the project explicitly adopts lint as a required validation gate.

## 10. Phase 1 final Definition of Done

Phase 1 can be declared **COMPLETE** when:

* [x] TypeScript project and Vite tooling are in place.
* [x] Babylon.js render shell works in the browser.
* [x] Input abstraction is wired into the live engine loop.
* [x] State machine boots and updates runtime states.
* [x] Browser bootstrap smoke test passes.
* [x] Asset loader performs real resource loading.
* [ ] Default placeholder assets exist and load successfully.
* [ ] `npm test` passes.
* [ ] `npm run build` passes.
* [ ] `npm run bundle` passes.
* [ ] Final browser smoke test passes with the real default asset manifest.
* [x] No blocking Phase 1 architecture decisions remain.
* [x] Repo is structurally ready for Phase 2.

### Final gate

When every required unchecked item above is green, update this document to mark Phase 1 **COMPLETE** and begin Phase 2:

* sprite system
* texture mapping
* scene graph for game objects
* graphics-layer conversion
