# Conhecimento permanente — ambiente Blender executável

## O que foi salvo

O repositório contém um ambiente Blender reproduzível, não uma sessão permanente. Cada execução reconstrói o mesmo ambiente a partir de uma versão bloqueada, verifica o download e produz relatórios.

## Versão de produção

- Blender `4.5.12` da série `4.5 LTS`;
- commit `84afd5f785f7`;
- arquivos oficiais obtidos de `download.blender.org`;
- manifesto SHA-256 oficial verificado antes da extração.

Usar uma única versão LTS evita que mudanças de API, modificadores, importadores ou exportadores alterem silenciosamente os resultados. Atualizações exigem um novo lock e regressão completa.

## Execução segura

O agente deve executar Blender com:

```text
--background
--factory-startup
--disable-autoexec
--python-exit-code 1
```

`--disable-autoexec` é obrigatório para arquivos externos. Scripts, drivers e textos Python embutidos em `.blend` não são confiáveis por padrão.

## Configuração para Roblox

- Unit System `None`;
- Rotation `Degrees`;
- 1 Blender Unit = 1 stud;
- Blender usa `+Z` para cima internamente;
- Studio usa `+Y` para cima;
- escala de importação/exportação GLB: 1;
- entrada do Avatar Setup: frente `-Z`;
- corpo R15 final: frente `+Z`;
- source imutável, working copy, suporte técnico, evidências, quarentena e exportação em coleções separadas.

## Workspace gerado

O script `create_roblox_workspace.py` cria:

- origem no solo;
- root de exportação;
- coleções protegidas;
- 12 câmeras ortográficas em azimutes de 30 graus;
- iluminação neutra;
- manifesto embutido;
- propriedades que registram eixos e pipeline.

## Regra de uso pelo agente

Antes de executar qualquer script Blender:

1. ler `blender_env/environment.lock.json`;
2. confirmar versão e commit;
3. usar o runner seguro do sistema operacional;
4. nunca habilitar autoexec para um arquivo recebido;
5. trabalhar em cópia;
6. salvar relatório JSON;
7. reabrir o artefato exportado;
8. não declarar Studio ou Marketplace aprovado sem evidência externa.

## Aprendizado

O agente aprende operacionalmente por commits. Novas técnicas entram como scripts e casos de regressão. Uma técnica não pode ser promovida porque funcionou uma vez: precisa de entrada identificada por hash, resultado anterior, correção, resultado posterior, teste e revisão.

## Fontes

- Blender production deployment: https://docs.blender.org/manual/en/4.5/advanced/deploying_blender.html
- Blender command-line arguments: https://docs.blender.org/manual/en/4.5/advanced/command_line/arguments.html
- Roblox Blender setup: https://create.roblox.com/docs/art/blender
- Roblox character body specifications: https://create.roblox.com/docs/avatar/character-bodies/specifications
