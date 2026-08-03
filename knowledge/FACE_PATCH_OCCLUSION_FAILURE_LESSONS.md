# Face Patch Occlusion Failure — Permanent Lesson

The V15 artifact contained a structurally present 3D mouth, but the exported head also contained an opaque primitive named `MouthRepairSkin3D`. It had no base-color texture, was double-sided, overlapped the mouth envelope, and reached the lip plane. In a deterministic front-depth grid it was the frontmost surface in 227 of 493 mouth samples. The mouthbag was frontmost in another 17 samples.

The prior gates checked hashes, triangle counts, symmetry, topology, orientation, and multiview coverage, but did not ask the decisive question: **which primitive is actually frontmost over the external mouth after export?**

Permanent rules:

- Never approve a mouth from component existence alone.
- Parse the exact exported GLB.
- Reject opaque untextured repair geometry over the external face.
- Reject external mouthbag visibility.
- Bind every close-up to the delivered SHA-256.
- A locally attractive Blender render is insufficient when it does not use the exact exported material path.
- Any failure in this gate blocks delivery before Avatar Setup.
