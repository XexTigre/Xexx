# Trends Roblox: análise de aceleração com yt-dlp + FFmpeg

**Execução:** 2026-08-03T18:56:50.399046+00:00  
**Data de referência:** 2026-08-03  
**Revisão:** **REJEITADO**  

## Conclusão

Não foi possível confirmar aceleração: nenhuma amostra passou simultaneamente por download, ffprobe e decodificação completa de frames.

## Como “acelerado” foi medido

- **Cortes por segundo** e duração média das cenas: medem ritmo de edição.
- **Fluxo óptico P90**: mede movimento visual entre frames.
- **Palavras por segundo**: usa legendas automáticas quando disponíveis.
- **Playback literalmente acelerado** é apenas uma suspeita quando há fala e movimento muito rápidos sem muitos cortes; não é tratado como certeza.

## Amostras aprovadas

Nenhuma.

## Auditoria

- Candidatos descobertos: **0**
- Downloads/decodificações aprovados: **0**
- Falhas registradas: **3**
- Todos os frames de cada amostra aprovada foram percorridos e gravados em CSV.
- Resultados sem download ou sem decodificação completa foram excluídos da conclusão.

## Arquivos

- `analysis.json`: métricas e revisão por vídeo.
- `failures.json`: comandos e erros de download.
- `candidates.json`: descoberta do yt-dlp.
- `*_frames.csv`: métrica de cada frame decodificado.
- `discovery_logs.txt`: auditoria da busca.
