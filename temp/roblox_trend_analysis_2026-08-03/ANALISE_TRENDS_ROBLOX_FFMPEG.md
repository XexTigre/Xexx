# Análise técnica de trends Roblox — 3 de agosto de 2026

## Status da coleta

- Fontes solicitadas: 3
- Vídeos baixados e analisados: 0
- Vídeos não baixados: 3

## Método verificável

- FFprobe para metadados de contêiner, streams, FPS e resolução.
- OpenCV percorreu cada frame decodificado e mediu brilho, saturação, densidade de bordas, mudança de histograma e fluxo óptico.
- FFmpeg `astats` mediu o áudio.
- Whisper tiny estimou idioma, janelas de fala e contagem de palavras. O texto bruto não foi preservado para evitar reprodução de letras protegidas.
- Keyframes foram amostrados periodicamente e em cortes detectados.

## Resultados por vídeo

### pega_pega_aug02
- URL: https://www.youtube.com/shorts/ViAD2FfHsRc
- Status: DOWNLOAD_FAILED

### skyfall_aug01
- URL: https://www.youtube.com/shorts/A7sRDc3W6QQ
- Status: DOWNLOAD_FAILED

### no_batidao_2026
- URL: https://www.youtube.com/shorts/znoKsfh8UDY
- Status: DOWNLOAD_FAILED

## Schema do aprendizado

```yaml
source_video: [slug, video_id, url, status, duration_s, resolution, fps]
frame_observation: [frame, timestamp_s, brightness, saturation, edge_density, histogram_change, motion_score]
audio_observation: [ffmpeg_astats, speech_windows, language, word_count, confidence]
edit_pattern: [detected_cuts, estimated_mean_shot_s, motion_mean, motion_p90, keyframes]
validation: [frames_reported, frames_processed, frame_count_delta, raw_text_stored, errors]
```

## Revisão automática

- PASS somente quando `frames_processed > 0`, o CSV existir, o resumo JSON existir e a contagem processada for compatível com a contagem reportada.
- Qualquer falha de download permanece marcada como `DOWNLOAD_FAILED`; não é convertida em análise por título ou miniatura.
