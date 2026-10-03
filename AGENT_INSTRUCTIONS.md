# Carnage3D TypeScript Port - Agent Instructions

This repository already contains the project documentation. Use the files below as the source of truth instead of duplicating the same information here.

## Source of truth

- Phase 1 architecture and delivery plan: [PHASE_1.md](./docs/PHASE_1.md)
- Broader TypeScript port strategy and roadmap: [TYPESCRIPT_PORT_PLAN.md](./docs/TYPESCRIPT_PORT_PLAN.md)
- Original C++ project: [carnage3d/carnage3d](https://github.com/carnage3d/carnage3d) available on this repository as `subtree` in ./carnage

## Working rule

- Keep this file brief and directional only.
- Do not restate architecture, phase goals, stack choices, or roadmap details that already exist in the linked files.
- Add only instructions that are not already captured in the repo docs.

## Current focus

- Phase 1 bootstrap and runtime shell
- Babylon.js rendering shell
- Input abstraction and state machine
- Asset-loading foundation and smoke tests

## Chosen stack for Phase 1

- Physics: Cannon-es
  - Chosen for a lightweight browser-first physics layer that fits the early engine-shell milestone without introducing a second full engine abstraction.
- Audio: Babylon Sound
  - Chosen to keep audio tied to the current scene lifecycle and reduce cross-system coordination during the bootstrap stage.
- Image handling: custom image loader
  - Chosen because the project is still stubbing asset loading and does not yet need a full image-processing library; this leaves room for future GTA1 resource conversion without premature dependency weight.

## Working preferences

- Keep the runtime shell intentionally small and explicit.
- Favor straightforward browser-safe abstractions over deep engine framework integration during Phase 1.
- When a design choice is not yet proven by gameplay needs, prefer the least complex option that keeps the later port path open.

For the detailed plan, acceptance criteria, and implementation guidance, see the files above.
