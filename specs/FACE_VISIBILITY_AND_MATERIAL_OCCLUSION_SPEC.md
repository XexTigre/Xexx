# Face Visibility and Material Occlusion Specification

## Purpose

Prevent delivery of a GLB whose mouth exists structurally but is hidden by a repair patch, mouthbag, teeth, tongue, or material mismatch.

## Mandatory gates

1. Bind the exact GLB by SHA-256.
2. Parse the exported GLB, not the Blender scene.
3. Identify the external upper and lower lips, the head, mouthbag, upper teeth, lower teeth, and tongue.
4. Build the external mouth envelope from the lip bounds.
5. Ray-test a deterministic front-view grid against the actual triangles.
6. Reject an opaque, untextured head primitive that overlaps the mouth envelope and reaches the lip plane.
7. Reject any such patch that is wider than 1.5 times the external lip width.
8. Reject any suspicious face patch that is double-sided.
9. Reject when a suspicious face patch is frontmost in more than 0.5% of tested mouth samples.
10. Reject when the mouthbag is frontmost from an external front view.
11. Require a close-up proof rendered from the exact exported GLB with the same material path used for delivery.
12. Keep Avatar Setup, Studio, and Marketplace gates separate.

## Truth boundary

A valid GLB container, correct triangle count, preserved hashes, or 50-view boards do not prove that the mouth is visible. A semantic depth-order and material-equivalence gate is mandatory before delivery.
