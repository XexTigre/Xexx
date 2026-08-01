# Blender Environment Review — v1.7

## Environment identity

- Blender: `4.5.12 LTS`;
- build hash: `84afd5f785f7`;
- embedded Python: `3.11.11`;
- execution: Linux x64 GitHub Actions;
- workspace artifact: `ROBLOX_CONTRACT_WORKSPACE_4_5.blend`;
- workspace SHA-256: `9186b6cb96ccd44a237740195801d96331a00e0e8f9a219417e4d19c32eb3e4d`.

## Review 1 — static contracts

GitHub Actions `Validate contracts` completed successfully after the regression assertion was corrected.

Confirmed:

- environment lock parses;
- Blender version and commit are pinned;
- Windows and Linux bootstraps require SHA-256 verification;
- safe command-line flags are present;
- workspace generator contains the Roblox unit and axis contract;
- the workflow executes a real Blender smoke test.

## Review 2 — real Blender execution

GitHub Actions `Blender environment` completed successfully.

Environment checks:

- version matches `4.5.12 LTS`;
- build hash matches `84afd5f785f7`;
- background mode active;
- factory startup active;
- automatic Python execution disabled;
- Python exception exit propagation active;
- glTF import operator available;
- glTF export operator available;
- Unit System `None`;
- Rotation `Degrees`.

## Review 3 — generated workspace

The generated `.blend` was reopened by Blender and all checks passed:

- all protected collections exist;
- 12 orthographic audit cameras exist;
- ground-center origin exists;
- export root exists;
- environment identity is embedded;
- 1 Blender Unit = 1 stud is embedded;
- Avatar Setup front `-Z` is embedded;
- R15 final front `+Z` is embedded;
- the environment manifest text block exists.

## Truth boundary

This proves the reproducible Blender environment and generated workspace. It does not prove that a particular avatar passed Avatar Setup, Roblox Studio or Marketplace validation.
