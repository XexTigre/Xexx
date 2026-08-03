# Validação visual exponencial V4

## Artefato

- `RBX_ANIME_DOLL_AVATAR_SETUP_SAFE_REPAIR_V2.glb`
- SHA-256: `b551a526e6d613132fb6b5dd2ae3a6c0cf4ff44a980a31c00906fcadc976a142`

## Cobertura real

- 62 vistas canônicas;
- 4 passes essenciais em 62 vistas;
- 8 passes estendidos em 12 azimutes;
- escalas 1×, 2×, 4× e 8×;
- grades 1×1, 2×2, 4×4 e 8×8, total de 85 células por imagem;
- 344 renders vista/passe;
- 5270 células de silhueta;
- 1020 células de aparência;
- 7170 observações quantitativas.

## Resultado local

- GLB estrutural: **PASS**
- Triângulos: **9864/10742**
- Arestas físicas abertas: **0**
- Non-manifold físico: **0**
- Sobreposição UV exata: **0 pares**
- Textura byte-exata: **True**
- MS-SSIM mínimo: **0.998335**
- SSIM p05 das células de aparência: **0.988921**
- IoU p05 das células de silhueta: **1.000000**
- ΔE00 p95 máximo: **1.335575**

## Revisões adversariais confirmadas

1. Células vazias em fonte e saída foram corrigidas para equivalência neutra, evitando falso IoU zero.
2. Dentes e língua internos deixaram de exigir visibilidade externa e passaram a exigir geometria nomeada mais prancha isolada ligada ao hash.
3. A primeira repetição dos testes em ambiente isolado encontrou uma falha de importação do pacote Python. O teste foi corrigido para inserir explicitamente a raiz do repositório e a suíte foi repetida.
4. Resultado final: JSON Schema Draft 2020-12 válido, exemplo válido, Python compilado, gate real sem rejeições/bloqueios/avisos e **8 testes adversariais aprovados**.

## Estado

`LOCAL_EXPONENTIAL_REVIEWED`. Khronos, reabertura do GLB no Blender bloqueado, Avatar Setup, Studio e UGC permanecem `NOT_RUN`; portanto `release_eligible=false`.
