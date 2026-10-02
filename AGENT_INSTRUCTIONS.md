# Carnage3D TypeScript Port - Agent Instructions

## Overview

This repository is a TypeScript port of the **Carnage3D** game engine, originally written in C++. The goal is to bring the classic GTA-style game engine to the web platform using modern TypeScript, Babylon.js, and web APIs.

### Project Goal

Port the Carnage3D game engine from C++ to TypeScript, creating a fully functional browser-based game that matches the original game's mechanics and gameplay experience.

**Key Objectives:**
- Replace the native C++ engine with a TypeScript implementation
- Render graphics using Babylon.js on an HTML5 canvas
- Implement game physics, input handling, and state management in TypeScript
- Support loading and rendering original Carnage3D assets (with compatibility layers)
- Maintain architectural parity with the original engine where possible

---

## Phase Structure

The port is divided into **8 phases**, each building on the previous one:

### **Phase 1: Engine Bootstrap & Architecture** (Current)
Establish the runtime shell and core systems architecture.

**Deliverables:**
- TypeScript + Babylon.js project scaffold
- GameEngine and GameLoop core classes
- RenderEngine with basic scene rendering
- InputManager with keyboard/gamepad support
- GameStateMachine for state transitions
- AssetLoader foundation
- Smoke tests and build validation

**Key Files to Create:**
- `src/core/GameEngine.ts`
- `src/core/GameLoop.ts`
- `src/graphics/RenderEngine.ts`
- `src/input/InputManager.ts`
- `src/game/GameStateMachine.ts`
- `src/assets/AssetLoader.ts`

**Reference:** See [PHASE_1.md](./PHASE_1.md) for detailed phase breakdown and acceptance criteria.

### **Phase 2-8: Incremental Feature Porting**
- **Phase 2:** Sprite rendering and texture mapping
- **Phase 3:** Input flow and state management refinement
- **Phase 4:** Physics and vehicle mechanics
- **Phase 5:** Game objects and AI systems
- **Phase 6:** HUD and UI
- **Phase 7:** Audio system
- **Phase 8:** Asset loading and GTA1 resource compatibility

---

## Original Carnage3D Resources

### Repository
- **Original Project:** [carnage3d/carnage3d](https://github.com/carnage3d/carnage3d)
- **Source Language:** C++
- **Original Renderer:** OpenGL
- **Game Inspiration:** Grand Theft Auto 1 & 2 (isometric view, top-down gameplay)

### Key Game Mechanics to Port
- Isometric 3D rendering perspective
- Vehicle physics and driving mechanics
- Character animation and movement
- Weapon systems and combat
- Mission and dialogue systems
- HUD and menu systems
- Asset loading (GTA1 data files)

---

## Architecture & Design Patterns

### Core Architecture (from PHASE_1.md)

```
GameEngine (main controller)
├── RenderEngine (Babylon.js scene management)
├── InputManager (keyboard/gamepad input)
├── GameStateMachine (state transitions)
├── AssetLoader (resource management)
└── PhysicsEngine (Cannon.js / Rapier)
    └── GameLoop (requestAnimationFrame cycle)
```

### Key Design Decisions
1. **State Machine Pattern:** All game states inherit from `GameState` interface with `enter()`, `update()`, `render()`, `leave()` lifecycle methods
2. **Input Abstraction:** Normalize keyboard, mouse, and gamepad events into action types
3. **Asset Manifest:** Decouple asset loading from rendering; use JSON manifest for asset definitions
4. **Modular Structure:** Clear separation between graphics, physics, input, and game logic

---

## Development Stack

### Dependencies
- **Framework:** TypeScript 5.x
- **Bundler:** Vite
- **Graphics:** Babylon.js
- **Physics:** Cannon-es or Rapier
- **Audio:** Howler.js
- **Testing:** Vitest
- **Linting:** ESLint + Prettier
- **Validation:** Zod
- **Image Processing:** Jimp (for asset pipeline)

### Project Structure
```
carnage3d-typescript-port/
├── src/
│   ├── core/              # Engine core (GameEngine, GameLoop, StateMachine)
│   ├── graphics/          # Rendering (RenderEngine, CameraRig, SceneManager)
│   ├── input/             # Input handling
│   ├── game/              # Game states and logic
│   ├── physics/           # Physics simulation
│   ├── assets/            # Asset loading
│   ├── ui/                # UI and HUD
│   ├── __tests__/         # Unit and integration tests
│   ├── index.ts           # Application entry point
│   └── styles.css         # Global styles
├── public/                # Static assets
├── package.json
├── tsconfig.json
├── vite.config.ts
├── vitest.config.ts
└── PHASE_1.md             # Phase 1 detailed specification
```

---

## Current Phase (Phase 1) Deliverables

By the end of Phase 1, the agent should have completed:

1. ✅ Project scaffolding and dependency setup
2. ✅ TypeScript configuration with strict mode
3. ✅ Babylon.js render engine with scene initialization
4. ✅ Input manager with keyboard support
5. ✅ Game state machine implementation
6. ✅ Asset loader skeleton
7. ✅ Smoke tests confirming engine bootstrap
8. ✅ Build and dev tooling validation

**Exit Criteria:**
- Application boots without errors
- Canvas renders a Babylon scene
- State machine transitions work
- Keyboard input is captured
- Unit tests pass
- No blocking architectural decisions remain

---

## Important Notes for the Agent

### Asset Handling
- **Phase 1:** Use placeholder/test assets only
- **Phase 2-8:** Gradually add GTA1 resource compatibility
- Do NOT attempt to parse original GTA1 binary formats in Phase 1

### Maintaining Parity
- Keep the architecture similar to the original C++ engine for easier porting later
- Document any deviations or web-specific changes
- Use similar naming conventions where possible

### Testing Strategy
- Start with smoke tests to confirm bootstrap
- Add unit tests for core systems as features are added
- Consider integration tests for multi-system interactions

### Browser Compatibility
- Target modern browsers (Chrome, Firefox, Safari, Edge)
- Use `requestAnimationFrame` for the main game loop
- Ensure canvas resizing and responsive behavior

---

## How to Use This File

This file serves as:
1. **Agent Briefing:** Quick reference for understanding the project scope and goals
2. **Checkpoints:** Verify completion of phase milestones
3. **Navigation:** Links to detailed phase specifications and original resources
4. **Context:** Maintain architectural consistency across iterations

---

## References

- **Phase 1 Details:** [PHASE_1.md](./PHASE_1.md)
- **Original Carnage3D:** [github.com/carnage3d/carnage3d](https://github.com/carnage3d/carnage3d)
- **Babylon.js Docs:** [doc.babylonjs.com](https://doc.babylonjs.com/)
- **Cannon.js Physics:** [github.com/react-three/cannon-es](https://github.com/react-three/cannon-es)

---

**Project Owner:** nelson-mig-l  
**Last Updated:** 2026-10-02  
**Status:** Phase 1 - In Progress
