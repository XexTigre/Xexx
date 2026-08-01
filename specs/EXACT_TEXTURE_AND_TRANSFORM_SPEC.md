# Exact Texture and Rigid Transform Specification v1.4

## Objetivo

Permitir correções de escala, origem e orientação sem recodificar a textura nem deformar a malha, e impedir que uma preservação bem-sucedida seja confundida com prontidão Roblox.

## Escopo

Esta spec se aplica a jobs `texture_preservation`, `transform_bake` e `axis_correction`. Não autoriza fechamento de buracos, remoção de componentes, rigging, caging ou particionamento.

## Entradas bloqueadas

Antes da edição, registrar:

- SHA-256 do GLB original;
- SHA-256 dos bytes da imagem incorporada;
- SHA-256 de `TEXCOORD_0`;
- SHA-256 dos índices;
- matriz do nó;
- bounds avaliados;
- orientação visual declarada;
- contagem de componentes e arestas abertas.

## Operações permitidas

- aplicar a matriz do nó às posições;
- transformar normals por inversa transposta;
- transformar tangentes pela parte linear e renormalizar;
- aplicar rotação rígida de eixo;
- atualizar `min` e `max` do accessor de posições;
- remover a matriz do nó somente depois de incorporar seu efeito aos atributos.

## Locks obrigatórios

- bytes da imagem incorporada: idênticos;
- `TEXCOORD_0`: idêntico;
- índices: idênticos;
- contagem de vértices e triângulos: idêntica;
- material e sampler: idênticos, salvo autorização separada;
- nenhuma mudança de conectividade.

## Provas

O relatório deve incluir:

- hashes antes/depois;
- confirmação de transform identidade após reabrir o GLB;
- dimensões e origem calculadas do artefato reaberto;
- 12 vistas ortográficas do arquivo exato;
- prancha com linhas de medida;
- status separado para geometria, Avatar Setup, R15, Studio e Marketplace.

## Decisão

- `PRESERVED`: imagem, UV e índices idênticos; transformação comprovadamente rígida.
- `REJECTED`: qualquer hash protegido mudou, normals/tangentes não foram atualizadas ou o GLB não reabriu.
- `BLOCKED`: faltam dados, ferramenta ou evidência.

`PRESERVED` nunca produz `release_eligible=true` por si só.

## Regras de pipeline

### Avatar Setup input

A variante deve olhar para `-Z`, mas continua exigindo corpo humanoide A/T, contiguidade, watertightness fora de olhos/boca, pescoço distinto, head internals e ausência de acessórios.

### Corpo R15 final

A variante deve olhar para `+Z`, ficar em `+Y`, ter transforms congelados e 15 partes corporais, além de rig, skinning, cages, attachments e prova no Studio.

## Caso aceito de preservação

`RBX_ANIME_DOLL_PRESERVED_BAKED_V2` comprovou imagem, UV e topologia idênticas após bake e rotação. O caso permanece falho para Avatar Setup devido a 139 componentes e 2.684 arestas abertas. Essa separação de estados é obrigatória em trabalhos futuros.
