# Roblox 3D Cross-Spec Matrix v1.1

## 1. Purpose

This document is the routing specification for a contract-driven Roblox 3D agent. It prevents requirements from different pipeline stages from being mixed. The agent MUST select exactly one primary pipeline before changing orientation, topology, rigging, cages, or attachments.

Normative terms: **MUST**, **MUST NOT**, **SHOULD**, and **MAY** are contractual.

## 2. Pipeline router

| Pipeline ID | Intended artifact | Entry condition | Release condition |
|---|---|---|---|
| `avatar_setup_body_input` | Basic body submitted to Avatar Setup | One or more meshes; rig optional | Avatar Setup output is generated, re-exported, rehashed, and validated as a new artifact |
| `r15_final_body` | Final Roblox character body | 15 body-part meshes and full avatar components | Local checks + Studio import + UGC validation evidence |
| `dynamic_head` | Marketplace-compatible animated head | Head geometry, cage, facial rig/FACS | Head validation demonstrates cage landmarks and required facial motion |
| `rigid_accessory` | Non-deforming accessory | One watertight mesh | Correct attachment, size, material, and UGC validation |
| `layered_accessory` | Deforming clothing/accessory | One watertight skinned mesh | Inner cage + outer cage + attachment + wrapping tests |

The release gate MUST reject an artifact when its declared pipeline does not match the evidence being used to approve it.

## 3. Crossed requirements and intentional conflicts

| Concern | Avatar Setup body input | Final R15 body | Dynamic head | Rigid accessory | Layered accessory |
|---|---|---|---|---|---|
| Front axis | `-Z` | `+Z` | Inherits final body convention | Defined by attachment/mannequin fit | Defined by attachment/mannequin fit |
| Up axis | `+Y` | `+Y` | `+Y` | `+Y` | `+Y` |
| Mesh count | 1 or more; tool may recombine | Exactly 15 named body meshes | `Head_Geo` plus required facial components | Exactly 1 render mesh | Exactly 1 render mesh |
| Rig | Optional | Required standard or supported higher-fidelity hierarchy | Facial rig/FACS required for manual final head | MUST NOT contain skinning | Required or valid skin transfer result |
| Skinning | Optional input | Max 4 influences; no Root influence | Facial deformation must be detectable | Prohibited | Required |
| Watertight | Required except eyes and mouth | Every separated body part capped and watertight; cages treated separately | Head and facial component rules apply | Required | Required |
| Head internals | 2 separate eyes + upper teeth + lower teeth + tongue | Final head must remain compatible with body and head specs | 3 cage landmarks and required facial poses | Not applicable | Face accessories use layered rules |
| Cages | May be generated | 15 outer cages; template topology/UV preserved | Head outer cage required | Not required | Inner and outer cage required |
| Attachments | May be generated | 19 named attachment points | Head-related attachments must remain valid | Created/configured through Studio/AFT for accessory | At least one correctly named attachment |
| Triangles | Total body <= 10,742 before generated caps | Group budgets sum to 10,742 | Head group <= 4,000 | <= 4,000 | <= 4,000 |
| Textures | At least one texture; multiple maps may be baked | Marketplace texture <= 2048x2048 | Must follow head/body texture rules | Marketplace texture <= 2048x2048 | Marketplace texture <= 2048x2048 |
| Accessories embedded in body | Prohibited | Prohibited in body bundle except specifically allowed bundled face accessories | Hair/eyelash/eyebrow remain separate Accessory objects when applicable | This is the accessory itself | This is the accessory itself |
| Final Studio proof | Required after processing | Mandatory | Mandatory | Mandatory for release | Mandatory for release |

## 4. Source precedence

When requirements conflict, apply this order:

1. Current official Roblox specification for the declared asset type.
2. Current official Roblox Avatar Setup specification when the declared stage is an Avatar Setup input.
3. Current official UGC validation categories and Studio validation output.
4. Project policy, only when Roblox does not publish a numeric threshold.
5. Historical lessons and heuristics.

A project heuristic MUST be labeled `project_policy`; it MUST NOT be represented as an official Roblox rule.

## 5. Stage-transition rule

Avatar Setup output is a **new artifact**. The agent MUST NOT reuse the input artifact decision for the output. The following values must be regenerated:

- artifact SHA-256;
- mesh and triangle inventory;
- orientation and scale measurements;
- body-part names;
- rig hierarchy and weights;
- cages and attachments inventory;
- textures and material inventory;
- visual proof board;
- Studio/UGC validation evidence.

## 6. Mandatory independent gates

The following gates are independent and cannot substitute for one another:

1. File/container integrity (`glTF`/`FBX` parsing).
2. Geometry/topology.
3. UV/texture/material.
4. Rigging/skinning.
5. Cages/attachments.
6. Dynamic-head behavior when applicable.
7. Pixel-intensive visual audit.
8. Studio import/playtest.
9. UGC validation for Marketplace-targeted assets.
10. Policy/moderation readiness.

Missing a mandatory gate produces `BLOCKED`. A measured failure produces `REJECTED`.

## 7. Anti-false-PASS rules

- A successful script exit code is not proof that the exported artifact is valid.
- The final exported file, not the Blender scene, is the audit target.
- Every evidence file must bind to the exact artifact SHA-256.
- A report generated before a later edit is stale and cannot approve the edited artifact.
- `UNKNOWN`, `NOT_RUN`, `SKIPPED`, absent tool, absent view, or absent Studio result cannot become `PASS`.
- The generator cannot be the sole critical validator.
- Visual similarity cannot override wrong orientation, open geometry, bad rigging, missing cages, or Studio failure.
- A Studio screenshot without machine-readable result/context is supporting evidence only.

## 8. Required companion specifications

- `AVATAR_SETUP_INPUT_SPEC.md`
- `R15_FINAL_BODY_SPEC.md`
- `DYNAMIC_HEAD_AND_CAGE_SPEC.md`
- `ACCESSORY_PIPELINES_SPEC.md`
- `EXPORT_STUDIO_RELEASE_SPEC.md`
- `PIXEL_VISUAL_AUDIT_SPEC.md`
- `cross_asset_contract.schema.json`
