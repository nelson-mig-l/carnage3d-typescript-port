# Carnage3D TypeScript + Babylon.js Port Plan

A strategic plan to port the Carnage3D GTA1 reimplementation from C++/OpenGL to TypeScript using Babylon.js and related modern libraries.

---

## Phase 1: Foundation & Architecture (Weeks 1-3)

### 1.1 Project Setup
- Initialize a TypeScript project with Webpack or Vite for bundling
- Set up strict TypeScript configuration
- Create a folder structure mirroring the current C++ organization:
  ```
  src/
    core/          (system lifecycle, engine loop)
    graphics/      (Babylon.js rendering layer)
    physics/       (Cannon.js physics)
    game/          (game logic, entities, gamestates)
    ui/            (ImGui replacement; Babylon GUI or imgui-js)
    assets/        (asset loaders and resource processing)
    input/         (keyboard, mouse, gamepad input)
    utils/         (math, strings, JSON helpers)
  ```

### 1.2 Core Dependencies
| C++ Library | TypeScript Replacement | Notes |
|---|---|---|
| GLFW | Babylon.js Engine | Unified rendering + windowing |
| GLEW | Babylon.js (built-in) | Automatic WebGL context |
| OpenGL | Babylon.js WebGL abstraction | High-level 3D API |
| Box2D | Cannon.js or Rapier | 2D/3D physics |
| cJSON | JSON + zod | Native JSON plus validation |
| Dear ImGui | Babylon GUI or imgui-js | Immediate-mode or retained-mode UI |
| GLM | Babylon.js math or math.gl | Vector/matrix math |
| STB Image | jimp or sharp | Image loading |
| OpenAL-Soft | Babylon.js Sound or Howler.js | Audio playback |

---

## Phase 2: Graphics Layer (Weeks 4-7)

### 2.1 Babylon.js Scene Setup
Create `graphics/RenderEngine.ts`:

```typescript
class RenderEngine {
  engine: Babylon.Engine;
  scene: Babylon.Scene;
  camera: Babylon.Camera;

  constructor(canvas: HTMLCanvasElement) {
    this.engine = new Babylon.Engine(canvas, true);
    this.scene = new Babylon.Scene(this.engine);
    // Setup lighting, shadows, post-processing
  }
}
```

### 2.2 Convert Rendering Systems
- `GpuTexture2D` → Babylon `Texture` / `DynamicTexture`
- `TrimeshBuffer` → Babylon `Mesh` with vertex/index buffers
- `Sprite2D` → 2D sprites via planes or billboards
- GLSL shaders → Babylon `ShaderMaterial`
- HUD / GUI → Babylon UI or DOM overlay

### 2.3 Asset Pipeline
Create `assets/AssetLoader.ts` to:
- Parse original GTA1 `.sty` files
- Load sprite sheets and textures
- Convert block data into Babylon meshes
- Cache compiled resources

---

## Phase 3: Physics & Input (Weeks 8-10)

### 3.1 Physics: Box2D → Cannon.js
Create `physics/PhysicsEngine.ts`:
- Map C++ `b2World` → Cannon `World`
- Convert rigid bodies for vehicles and characters
- Port constraints for suspension and joints

```typescript
const world = new CANNON.World();
world.gravity.set(0, -9.82, 0);
world.defaultContactMaterial.friction = 0.4;
```

### 3.2 Input System
Create `input/InputManager.ts`:
- Keyboard: arrow keys, WASD, Space, Ctrl, Tab, Z, X, Enter
- Mouse: movement, buttons, scroll
- Gamepad API
- Event dispatcher matching current architecture

---

## Phase 4: Game Logic (Weeks 11-14)

### 4.1 Core Game Systems
Port in this order:
1. Game state machine (`GenericGamestate`)
2. Game time and frame updates (`OnGamestateFrame`)
3. Level loading and map data (`.cmp` parsing)
4. Game objects (peds, vehicles, projectiles)
5. Collision and interaction logic

### 4.2 Game Entities
- Vehicle class → steering, acceleration, damage
- Pedestrian class → movement, animation, AI
- Weapons system → shooting and hit detection
- Explosion system → sprite-based animation

### 4.3 Main Game Loop
```typescript
class GameEngine {
  gamestate: GenericGamestate;

  async gameLoop(deltaTime: number) {
    this.gamestate.OnGamestateFrame();
    await this.physics.update(deltaTime);
    this.graphics.render();
  }
}
```

---

## Phase 5: UI Layer (Weeks 15-16)

### 5.1 Menu System
- Replace Dear ImGui with Babylon GUI or HTML/CSS UI
- Options:
  - Babylon GUI for native 3D menus
  - imgui-js for closer fidelity to the original
  - DOM/HTML UI for quick iteration

### 5.2 HUD Display
- Map HUD panels to Babylon `AdvancedDynamicTexture`
- Replace STB TrueType with Canvas API or Babylon text rendering

---

## Phase 6: Audio System (Weeks 17-18)

### 6.1 Audio Engine
Replace OpenAL-Soft with:
- Babylon.js Sound
- or Howler.js

Requirements:
- background music
- vehicle engine sounds
- weapon effects
- ambient city sounds
- positional audio

---

## Phase 7: Data Loading & Config (Weeks 19-20)

### 7.1 GTA1 Asset Loading
Convert C++ file I/O to TypeScript:
- `cJSON` → native JSON parsing
- game data directory → asset manifest
- `.cmp` map files → custom parser
- sprite and texture data → Babylon texture atlases

### 7.2 Configuration
- `gamedata/config/sys_config.json` → keep as-is
- input bindings (`inputs.json`) → custom schema

---

## Phase 8: Testing & Optimization (Weeks 21-24)

### 8.1 Testing Strategy
- Unit tests for physics, input, and game logic
- Integration tests for the game loop
- Performance profiling with Babylon.js inspector

### 8.2 Optimization
- Object pooling for projectiles and explosions
- LOD for sprites
- Lazy loading of assets
- Texture compression (WebP, Basis)

### 8.3 Multiplayer / Split-screen
- Babylon multi-viewport rendering
- optional future network support

---

## Key Migration Challenges & Solutions

| Challenge | Solution |
|---|---|
| GTA1 isometric view | Use orthographic camera with custom projection in Babylon |
| Sprite-based rendering | Use billboards and pre-rendered sprite atlases |
| 2D physics in a 3D engine | Use Cannon.js with 2D constraints or a custom wrapper |
| Original GTA1 assets | Use the original GTA1 demo asset flow |
| Cross-platform differences | Babylon handles browser rendering |
| WASM performance | Babylon runs natively in browser; fallback if needed |

---

## Recommended Library Stack

```json
{
  "dependencies": {
    "babylonjs": "^6.x",
    "cannon-es": "^0.20.x",
    "howler": "^2.2.x",
    "zod": "^3.x",
    "jimp": "^0.22.x"
  },
  "devDependencies": {
    "typescript": "^5.x",
    "vite": "^5.x",
    "vitest": "^1.x",
    "eslint": "^8.x",
    "prettier": "^3.x"
  }
}
```

---

## Milestone Checkpoints

1. ✅ Week 3: Basic Babylon scene renders
2. ✅ Week 7: Sprites/textures display correctly
3. ✅ Week 10: Physics and input working
4. ✅ Week 14: First level playable (walk/drive, collision)
5. ✅ Week 16: UI menus functional
6. ✅ Week 20: Full GTA1 demo level with audio
7. ✅ Week 24: Optimized, cross-browser tested

---

## High-Level Architecture

```typescript
class GameEngine {
  private renderEngine: RenderEngine;
  private physicsEngine: PhysicsEngine;
  private inputManager: InputManager;
  private audioManager: AudioManager;
  private stateMachine: GameStateMachine;
  private assetLoader: AssetLoader;

  constructor() {
    this.renderEngine = new RenderEngine();
    this.physicsEngine = new PhysicsEngine();
    this.inputManager = new InputManager();
    this.audioManager = new AudioManager();
    this.assetLoader = new AssetLoader();
    this.stateMachine = new GameStateMachine();
  }

  async start() {
    await this.assetLoader.loadAssets();
    this.stateMachine.enter("mainMenu");
    this.loop();
  }

  private loop() {
    const deltaTime = this.renderEngine.getDeltaTime();

    this.stateMachine.update(deltaTime);
    this.physicsEngine.update(deltaTime);
    this.inputManager.update(deltaTime);
    this.renderEngine.render();

    requestAnimationFrame(() => this.loop());
  }
}
```

---

## Implementation Priority

1. Babylon.js rendering foundation
2. Input handling
3. Physics integration
4. Game state machine
5. Asset pipeline
6. Audio and HUD
7. Gameplay polish
8. Browser optimization and testing

---

## Summary

The best path is:
- keep the existing gameplay architecture
- replace rendering, physics, and UI with Babylon.js-first technology
- move as much as possible to TypeScript and browser-friendly abstractions
- preserve original GTA1 data and assets

This gives the best chance of a successful port while minimizing rework.

---

## Suggested Next Step

Start with:
- Babylon.js project bootstrapping
- minimal render engine
- sprite rendering
- then port the main game loop and state machine
