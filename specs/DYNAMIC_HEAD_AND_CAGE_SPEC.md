# Dynamic Head, Cage, and Facial Validation Spec v1.1

## Head cage

- `Head_OuterCage` MUST exist for a final Marketplace-compatible head.
- Cage template topology and UV identity MUST be preserved.
- The head render mesh MUST fit the cage without invalid projection, major intersections, or displaced landmarks.
- Three distinct cage landmarks MUST project to the render mesh: left eye, right eye, and mouth.

## Facial animation contract

- The final head MUST expose at least 17 required FACS poses for UGC validation.
- Evidence MUST demonstrate visually detectable deformation for:
  - left/right blink or eye closure as required;
  - mouth opening;
  - happy expression;
  - sad expression.
- Pose existence by name is insufficient: the projected landmarks must move appropriately.
- Facial bones/weights MUST be finite and must not unintentionally deform the neck, torso, eyes, teeth, or tongue.

## Internal components

Eyes, teeth, tongue, mouthbag, and face mesh connectivity MUST match the selected production route. A component preserved from Avatar Setup input MUST remain separately auditable after partitioning/export.

## Neutral-pose and extreme-pose tests

The proof set MUST include:

- neutral front and two profile views;
- eye closure at minimum and maximum;
- mouth-open extreme;
- smile/happy extreme;
- frown/sad extreme;
- combined pose stress test;
- wireframe/cage overlay for each critical expression;
- intersection and inversion report.

## Decision

- Missing cage/landmark/FACS evidence: `BLOCKED`.
- Invalid projection, missing detectable motion, inverted faces, severe intersections, or incorrect binding: `REJECTED`.
- Local pose tests do not replace Roblox head validation; final approval requires the exact-artifact Studio/UGC result.
