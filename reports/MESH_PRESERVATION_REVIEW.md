# Mesh Preservation Review

## Revisão 1 — coerência com Roblox

PASS estrutural. A spec reforça 15 partes finais, malhas fechadas, transformações congeladas, orientação por pipeline, no máximo quatro influências, zero pesos no Root e preservação da topologia/UV dos cages Roblox.

## Revisão 2 — controle de deformação

PASS. O contrato separa textura, correção local, pesos, cages e reconstrução. Cada escopo possui locks distintos e comparação baseline × saída.

## Revisão 3 — práticas destrutivas

PASS. Operações como Decimate, Remesh, Weld, Merge by Distance, Boolean, Smooth global, aplicação cega de transformações e pesos automáticos sem teste são rejeitadas por padrão.

## Revisão 4 — testes adversariais

Nove cenários foram executados:

- caso completo aprovado;
- textura alterando geometria rejeitada;
- Smooth global rejeitado;
- pose ausente bloqueada;
- colapso de volume articular rejeitado;
- autoaprovação rejeitada;
- evidência adulterada rejeitada;
- transformação cega de armature rejeitada;
- Corrective Smooth global/não local rejeitado.

## Revisão 5 — segunda passagem independente

PASS. A segunda passagem corrigiu três lacunas: cabeça dinâmica agora usa poses faciais próprias em vez das poses corporais; o schema registra a configuração do Corrective Smooth; e o gate rejeita aplicação de transformações na armature após o binding sem autorização e regressão completa. A correção de cage também compara os hashes reais de topologia e UV.

## Limite honesto

A spec e o gate verificam contrato, hashes e métricas fornecidas. Eles não substituem a extração real das métricas no Blender, Khronos Validator ou Roblox Studio. Um GLB só pode ser aprovado quando as evidências do arquivo exato forem produzidas e verificadas.
