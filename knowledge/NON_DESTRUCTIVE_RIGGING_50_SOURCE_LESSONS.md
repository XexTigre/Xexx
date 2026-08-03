# Síntese permanente — rig corporal e facial sem alterar o que já está correto

## Regra central

Em `rig_only`, o rig é uma camada adicional. Os arrays preexistentes `POSITION`, `NORMAL`, `TEXCOORD_0`, índices e bytes de imagem ficam bloqueados por hash. Só podem ser adicionados joints, inverse bind matrices, `JOINTS_0`, `WEIGHTS_0`, controles e evidências. Qualquer alteração geométrica exige outro contrato.

## Aprendizado cruzado das 50 fontes

1. Separar rest pose, pose animada e artefato exportado.
2. Usar hierarquia R15 reconhecível; os joints faciais ficam sob `DynamicHead`, marcado como `RootFaceJoint`.
3. Limitar a quatro influências por vértice, normalizar a soma e manter zero peso no `Root`.
4. Automatic Weights, Data Transfer, Mirror e Preserve Volume nunca são aprovação; exigem poses e inspeção local.
5. Posicionar os joints dos olhos no centro dos globos e usar pálpebras separadas.
6. Preservar Frame 0 neutro e separar rig facial de mapeamento FACS. Ossos corretos não provam as poses mapeadas.
7. O número de poses FACS não é o número de ossos; usar o menor conjunto estável que reproduza os movimentos necessários.
8. Reabrir o GLB final, validar skin e inverse bind matrices, medir drift da rest pose e renderizar provas de deformação.
9. Provar o rosto externamente e internamente. Dentes e língua ocluídos exigem vistas isoladas ligadas ao mesmo hash.
10. Avatar Setup, Studio e UGC permanecem gates externos.

## Caso de regressão local

- saída: `RBX_ANIME_DOLL_RIGGED_FACE_BONES_V1.glb`;
- SHA-256: `68bf4a9b71ee8861536d254d78e7d51e2bc652f1828601fa1edd45ef47d07fc9`;
- fonte: `b551a526e6d613132fb6b5dd2ae3a6c0cf4ff44a980a31c00906fcadc976a142`;
- 49 joints: 17 corporais e 32 faciais;
- máximo de 4 influências e zero pesos no Root;
- erro máximo da soma dos pesos: `1.0058283805847168e-07`;
- delta máximo da rest pose: `5.266404692189068e-07` stud;
- 50 vistas externas e 50 vistas internas do rosto;
- FACS mapping: `NOT_IMPLEMENTED`;
- Studio/UGC: `NOT_RUN`.

## Proibido em rig_only

- mover, suavizar, remesclar ou decimar geometria;
- modificar UV, normais, índices, textura, cages ou attachments;
- aplicar transformações cegamente depois do binding;
- aceitar pesos automáticos sem normalização e poses;
- esconder vértices sem peso ou com mais de quatro influências;
- declarar `dynamic_head_ready` sem FACS mapeado e teste no Studio.
