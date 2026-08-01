# Ambiente Blender reproduzível para Roblox

Este diretório define o ambiente que o agente deve usar para criar, revisar e validar ativos Roblox no Blender.

## Limite importante

O GitHub armazena a versão, scripts, contratos e resultados. Ele não mantém uma sessão Blender permanentemente aberta. Cada execução baixa a versão bloqueada, verifica o SHA-256 oficial, inicia o Blender em modo limpo e gera relatórios ligados ao artefato exato.

## Versão bloqueada

- Blender 4.5.12 LTS;
- commit oficial `84afd5f785f7`;
- instalação portátil e isolada por projeto;
- checksum obtido do manifesto oficial da mesma versão.

Uma única versão LTS é usada porque mudanças de versão podem alterar resultados e compatibilidade de arquivos. O upgrade exige Pull Request, relatório de migração e testes de regressão.

## Segurança

As execuções automatizadas usam:

```text
--background
--factory-startup
--disable-autoexec
--python-exit-code 1
```

Arquivos `.blend` não confiáveis nunca são abertos com autoexec habilitado. Nenhum script incorporado ao arquivo é considerado fonte confiável.

## Configuração Roblox

O workspace segue:

- Unit System: `None`;
- Rotation: `Degrees`;
- 1 Blender Unit = 1 stud;
- Blender trabalha nativamente com `+Z` para cima;
- exportação/importação para Studio usa escala 1 e conversão para `+Y` para cima;
- entrada do Avatar Setup usa frente `-Z`;
- corpo R15 final usa frente `+Z`;
- origem de trabalho no solo e centro do corpo;
- transformações precisam ser aplicadas antes da decisão final.

## Instalação local

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File blender_env/bootstrap_windows.ps1
```

### Linux

```bash
bash blender_env/bootstrap_linux.sh
```

Os scripts:

1. baixam o arquivo oficial;
2. baixam o manifesto SHA-256 oficial;
3. verificam o arquivo antes de extrair;
4. instalam em `.tools/blender/4.5.12`;
5. executam o teste de ambiente;
6. geram o workspace `.blend` determinístico.

## Executar uma tarefa

Linux:

```bash
bash blender_env/run_blender.sh blender_env/scripts/verify_environment.py
```

Windows:

```powershell
blender_env/run_blender.ps1 blender_env/scripts/verify_environment.py
```

Para criar o workspace:

```bash
bash blender_env/run_blender.sh blender_env/scripts/create_roblox_workspace.py -- artifacts/ROBLOX_CONTRACT_WORKSPACE_4_5.blend
```

## Aprendizado do agente

O ambiente não aprende alterando os pesos de uma IA. Ele acumula conhecimento operacional versionado:

- scripts aprovados;
- configurações de exportação;
- casos de regressão;
- relatórios reais;
- operações proibidas;
- correções com teste antes/depois.

Uma lição só entra no índice confiável após fonte, reprodução, teste que falhava, correção, teste aprovado e revisão em PR.
