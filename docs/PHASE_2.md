Sure. Here’s a Python script that creates `docs/PHASE_2.md` in your local clone. It uses only the Python standard library, so there are no dependencies.

Save this as `create_phase2.py` in the repository root:

````python
from pathlib import Path

CONTENT = r"""# Phase 2: Graphics Layer

## Goal

Build the browser-based 3D rendering foundation for the TypeScript port using Babylon.js, while keeping the rendering layer isolated from game logic and asset-loading concerns.

Phase 2 should establish the renderer, basic scene/camera setup, texture and mesh primitives, sprite rendering, shader support, and the first version of the runtime asset pipeline.

---

## 2.1 Babylon.js Scene Setup

Create the core rendering abstraction:

    src/
      graphics/
        RenderEngine.ts

Responsibilities:

- Create and own the Babylon.js `Engine`
- Create and own the Babylon.js `Scene`
- Configure the rendering canvas
- Configure the camera
- Set up basic lighting
- Configure shadows where required
- Provide the render/update entry points
- Keep Babylon.js-specific implementation details inside the graphics layer

Initial shape:

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
````

### Acceptance Criteria

* A Babylon.js engine can be created from the application's canvas.
* A scene is created successfully.
* A camera is configured and can render the scene.
* The renderer can render a minimal test scene in the browser.
* Rendering responsibilities are not mixed into game-state or entity classes.

---

## 2.2 Rendering Systems

Port the existing rendering concepts into Babylon.js abstractions.

### Texture Rendering

Replace:

```
GpuTexture2D
```

with Babylon.js:

* `Texture`
* `DynamicTexture`

Support the texture operations required by the existing game renderer.

### Mesh Rendering

Replace:

```
TrimeshBuffer
```

with Babylon.js meshes using:

* vertex buffers
* index buffers
* materials
* transforms

The first implementation should favour correctness and a clear abstraction over premature optimization.

### Sprite Rendering

Replace:

```
Sprite2D
```

with billboard or plane-based sprites.

The renderer should support:

* sprite textures
* sprite positioning
* scaling
* rotation where required
* texture regions / atlas coordinates
* camera-facing billboards where appropriate

### Shader Rendering

Replace GLSL shader usage with Babylon.js `ShaderMaterial`.

The abstraction should make it possible to add custom shaders without leaking shader-specific details into unrelated game code.

### HUD / GUI

Keep the game HUD separate from world rendering.

Initial options:

* Babylon GUI
* DOM/CSS overlay

The implementation should make it possible to replace the UI approach later without rewriting the renderer.

---

## 2.3 Asset Pipeline

Create:

```
src/
  assets/
    AssetLoader.ts
```

The asset loader should provide a single entry point for loading runtime resources.

Responsibilities:

* Resolve runtime asset paths
* Load textures
* Load sprite sheets
* Load model/mesh data
* Parse original GTA1 `.sty` data where required
* Convert block data into Babylon meshes
* Cache loaded resources
* Avoid loading the same resource multiple times

Runtime assets should live under:

```
public/
  assets/
    textures/
    models/
    sounds/
    music/
    shaders/
```

Keep the source asset organization predictable and avoid coupling game code to individual file paths.

### Asset Path Requirements

Runtime paths should remain relative so the application works both on the GitHub Pages project URL and on a custom domain.

Example:

```typescript
const texturePath = './assets/textures/vehicles/car.png';
```

Do not use root-relative runtime paths such as:

```typescript
'/assets/textures/vehicles/car.png'
```

---

## 2.4 Camera and GTA1 View

The original game uses an isometric-style view.

The Babylon.js implementation should use an orthographic camera with a projection suitable for the game's presentation.

Requirements:

* orthographic projection
* stable camera orientation
* configurable zoom
* configurable camera position
* support for the game's world coordinate system
* camera behaviour isolated from gameplay entities

Do not hard-code camera behaviour into individual game objects.

---

## 2.5 Rendering Architecture

The graphics layer should remain independent from the rest of the engine as much as practical.

Target architecture:

```
GameEngine
    |
    +-- RenderEngine
    |     +-- Scene
    |     +-- Camera
    |     +-- Materials
    |     +-- Meshes
    |     +-- Sprites
    |     +-- Shaders
    |
    +-- AssetLoader
```

The renderer should expose game-oriented operations rather than requiring gameplay code to manipulate Babylon.js directly wherever possible.

For example:

```typescript
renderEngine.createSprite(...);
renderEngine.createMesh(...);
renderEngine.setCamera(...);
renderEngine.render();
```

This keeps the future option of changing rendering implementation without rewriting gameplay systems.

---

## 2.6 Integration With the Game Loop

Phase 2 should establish the rendering side of the main engine loop.

Target flow:

```
Input
  ↓
Game State
  ↓
World / Entities
  ↓
Render State
  ↓
RenderEngine
  ↓
Babylon.js Scene
  ↓
Canvas
```

The renderer should expose enough functionality for the application to:

1. Initialize the rendering engine.
2. Load required graphical resources.
3. Create a scene.
4. Create the camera.
5. Create test geometry/sprites.
6. Render each frame.
7. Resize correctly when the browser viewport changes.

---

## 2.7 Browser and Canvas Requirements

The rendering layer must behave correctly as a browser game.

Requirements:

* Canvas fills the available viewport.
* Browser page scrolling is disabled during gameplay.
* Canvas resizes with the window.
* Rendering remains responsive across common desktop resolutions.
* Pointer/touch interaction can be supported by later input systems.
* Fullscreen rendering should remain possible.

The renderer should not depend on a fixed canvas resolution.

---

## 2.8 Performance Considerations

Do not optimize prematurely, but establish boundaries that allow optimization later.

Initial considerations:

* Reuse meshes and materials where possible.
* Cache loaded textures.
* Avoid recreating Babylon objects every frame.
* Keep asset loading asynchronous.
* Avoid unnecessary draw calls.
* Keep sprite rendering batched where practical.
* Leave room for object pooling in later phases.

Advanced optimization such as texture compression, lazy loading, and LOD belongs primarily to the later optimization phase.

---

## 2.9 Phase 2 Deliverables

By the end of Phase 2, the project should have:

* [ ] Babylon.js installed and configured.
* [ ] A working `RenderEngine`.
* [ ] A Babylon.js scene.
* [ ] An orthographic/isometric-style camera.
* [ ] Basic lighting and shadow configuration.
* [ ] Texture loading.
* [ ] Basic mesh creation.
* [ ] Sprite rendering.
* [ ] ShaderMaterial support.
* [ ] Initial HUD/GUI integration point.
* [ ] An `AssetLoader` abstraction.
* [ ] Runtime asset directories under `public/assets/`.
* [ ] Asset caching.
* [ ] Browser resize handling.
* [ ] A minimal rendered test scene.
* [ ] Rendering integrated with the application lifecycle.

---

## 2.10 Acceptance Test

Phase 2 is complete when the application can:

1. Start the Babylon.js rendering engine.
2. Create a scene and orthographic camera.
3. Load a texture through the asset loader.
4. Display a textured sprite or mesh.
5. Render the scene continuously.
6. Resize correctly with the browser window.
7. Use relative asset paths.
8. Keep renderer implementation isolated from game logic.
9. Run successfully through the project's normal TypeScript/build workflow.

---

## Migration Notes

The TypeScript port should preserve the existing game's rendering concepts where they are useful, but should not reproduce the C++/OpenGL API literally.

The target is a browser-friendly rendering architecture:

* OpenGL → Babylon.js
* GpuTexture2D → Babylon Texture / DynamicTexture
* TrimeshBuffer → Babylon Mesh + vertex/index buffers
* Sprite2D → billboard/plane-based sprites
* GLSL shaders → Babylon ShaderMaterial
* Dear ImGui rendering → Babylon GUI or DOM/CSS overlay

The graphics layer should be designed around the needs of the TypeScript game rather than around a one-to-one translation of the original implementation.

---

## Phase 2 Milestone

**Expected milestone: Week 7**

At the end of this phase, sprites and textures should display correctly in a Babylon.js scene and the project should have the rendering/asset foundation required for the Physics & Input phase.

---

## Next Phase

Phase 3 will build on this rendering foundation by introducing:

* physics integration
* vehicle and character rigid bodies
* keyboard/mouse/gamepad input
* the input manager
* physics/render synchronization
  """

def main() -> None:
repo_root = Path(**file**).resolve().parent
output = repo_root / "docs" / "PHASE_2.md"

```
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(CONTENT, encoding="utf-8")

print(f"Created: {output}")
```

if **name** == "**main**":
main()

````

Then run:

```bash
python create_phase2.py
````

Verify it:

```bash
git diff -- docs/PHASE_2.md
```

Then commit and push:

```bash
git add docs/PHASE_2.md
git commit -m "Add Phase 2 graphics layer plan"
git push origin main
```

If you want to do **everything in one command after creating the script**:

```bash
python create_phase2.py && git add docs/PHASE_2.md && git commit -m "Add Phase 2 graphics layer plan" && git push origin main
```

This approach bypasses the broken GitHub connector entirely.
