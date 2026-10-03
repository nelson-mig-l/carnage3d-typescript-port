# Agent Guidelines

## Repository scope

This repository is a TypeScript/Babylon.js port of Carnage3D.

The active implementation lives primarily in:

- `src/`
- `docs/`
- Root TypeScript/configuration files
- Tests and test configuration

The `carnage/` directory contains the original C++ Carnage3D project and should be treated as a **reference implementation**, not as part of the TypeScript codebase.

## Do not modify

### `carnage/`

**Do not modify, refactor, rename, delete, or reformat files under `carnage/` unless the user explicitly asks for changes to the original C++ project.**

Use `carnage/` for:

- Understanding original game behavior
- Comparing algorithms and data structures
- Porting functionality to TypeScript
- Checking original constants and formats
- Resolving ambiguities in the TypeScript implementation

When porting code from `carnage/`, translate the relevant behavior into the TypeScript architecture rather than modifying the C++ source.

### `node_modules/`

Never modify or commit files under `node_modules/`.

Treat it as generated dependency state.

## Generated files

Do not manually edit generated/build output when a source/configuration change can regenerate it.

Examples include:

- `dist/`
- Build output
- Coverage output
- Generated caches
- Other tool-generated artifacts

Prefer changing the source and running the appropriate project command.

## Documentation

Before making architectural changes, consult the existing project documentation.

In particular:

- `docs/PHASE_1.md`
- `docs/TYPESCRIPT_PORT_PLAN.md`

Do not duplicate large portions of these documents in agent instructions.

## Porting principle

When implementing a feature from the original Carnage3D code:

1. Inspect the corresponding C++ implementation in `carnage/`.
2. Understand the behavior rather than mechanically translating syntax.
3. Identify the appropriate TypeScript/Babylon.js abstraction.
4. Implement the behavior in `src/`.
5. Add or update tests where practical.
6. Preserve the original game's observable behavior unless the port plan explicitly calls for a change.

## Architecture

Do not introduce new engine abstractions, dependencies, or framework layers without a concrete need.

Prefer the existing Phase 1 architecture and keep the runtime shell small and explicit.

Current Phase 1 choices include:

- Babylon.js for rendering
- Cannon-es for physics
- Babylon Sound for audio
- Custom image loading

Refer to the phase documentation for the authoritative project direction.

## Dependency changes

Do not add dependencies merely for convenience.

Before adding a package:

- Check whether the functionality can reasonably be implemented with existing dependencies or browser APIs.
- Consider bundle size and browser compatibility.
- Make sure the dependency fits the current port architecture.
- Update the relevant package files consistently.

## Code changes

Keep changes focused on the requested task.

Avoid:

- Unrelated refactors
- Broad formatting changes
- Renaming unrelated APIs
- Changing established architecture without justification
- Rewriting working code simply to make it stylistically different

## Verification

After making changes, run the smallest relevant verification available.

Prefer, where applicable:

- TypeScript type checking
- Unit tests
- Existing smoke tests
- Production build

If verification cannot be run, state that explicitly rather than assuming the change works.

## Git hygiene

Do not commit:

- `node_modules/`
- Local environment files containing secrets
- Build artifacts unless the repository explicitly tracks them
- Editor-specific temporary files
- Unrelated changes

Keep commits and patches focused on the requested work.
