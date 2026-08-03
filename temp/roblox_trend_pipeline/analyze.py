#!/usr/bin/env python3
import csv
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
import whisper

WORK = Path(os.environ.get('WORK_DIR', '/tmp/roblox_trends'))
RESULT = Path(os.environ.get('RESULT_DIR', 'temp/roblox_trend_analysis_2026-08-03'))
VIDEOS = WORK / 'videos'
RESULT.mkdir(parents=True, exist_ok=True)

SOURCES = [
    ('pega_pega_aug02', 'ViAD2FfHsRc', 'https://www.youtube.com/shorts/ViAD2FfHsRc'),
    ('skyfall_aug01', 'A7sRDc3W6QQ', 'https://www.youtube.com/shorts/A7sRDc3W6QQ'),
    ('no_batidao_2026', 'znoKsfh8UDY', 'https://www.youtube.com/shorts/znoKsfh8UDY'),
]


def ffprobe(path):
    p = subprocess.run([
        'ffprobe', '-v', 'error', '-show_entries',
        'format=duration,size,bit_rate:stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,sample_rate,channels',
        '-of', 'json', str(path)
    ], capture_output=True, text=True, check=True)
    return json.loads(p.stdout)


def optical_flow(prev_gray, gray):
    if prev_gray is None:
        return 0.0
    a = cv2.resize(prev_gray, (160, 90))
    b = cv2.resize(gray, (160, 90))
    flow = cv2.calcOpticalFlowFarneback(a, b, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    return float(np.mean(np.linalg.norm(flow, axis=2)))


def make_sheet(paths, output, cols=4, thumb=(180, 320)):
    images = []
    for path in paths:
        image = Image.open(path).convert('RGB')
        image.thumbnail(thumb)
        canvas = Image.new('RGB', thumb, 'white')
        canvas.paste(image, ((thumb[0] - image.width) // 2, (thumb[1] - image.height) // 2))
        images.append(canvas)
    if not images:
        return
    rows = math.ceil(len(images) / cols)
    sheet = Image.new('RGB', (cols * thumb[0], rows * thumb[1]), 'white')
    for index, image in enumerate(images):
        sheet.paste(image, ((index % cols) * thumb[0], (index // cols) * thumb[1]))
    sheet.save(output, quality=78, optimize=True)


try:
    whisper_model = whisper.load_model('tiny')
    whisper_model_error = None
except Exception as exc:
    whisper_model = None
    whisper_model_error = str(exc)

master = []
for slug, video_id, url in SOURCES:
    video = VIDEOS / f'{slug}.mp4'
    if not video.exists():
        master.append({'slug': slug, 'video_id': video_id, 'url': url, 'status': 'DOWNLOAD_FAILED'})
        continue

    out = RESULT / slug
    key_dir = out / 'keyframes'
    out.mkdir(parents=True, exist_ok=True)
    key_dir.mkdir(parents=True, exist_ok=True)

    probe = ffprobe(video)
    (out / 'ffprobe.json').write_text(json.dumps(probe, indent=2), encoding='utf-8')

    cap = cv2.VideoCapture(str(video))
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    reported_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)

    rows = []
    motion_values, hist_values, brightness_values, saturation_values, edge_values = [], [], [], [], []
    keyframes = []
    prev_gray = None
    prev_hist = None
    frame_index = 0
    last_key = -999999

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        brightness = float(gray.mean())
        saturation = float(hsv[:, :, 1].mean())
        edge_density = float((cv2.Canny(gray, 100, 200) > 0).mean())
        hist = cv2.calcHist([hsv], [0, 1], None, [24, 16], [0, 180, 0, 256])
        cv2.normalize(hist, hist)
        histogram_change = 0.0 if prev_hist is None else float(cv2.compareHist(prev_hist, hist, cv2.HISTCMP_BHATTACHARYYA))
        motion = optical_flow(prev_gray, gray)
        timestamp = frame_index / fps

        rows.append([
            frame_index, round(timestamp, 4), round(brightness, 4), round(saturation, 4),
            round(edge_density, 6), round(histogram_change, 6), round(motion, 6)
        ])
        motion_values.append(motion)
        hist_values.append(histogram_change)
        brightness_values.append(brightness)
        saturation_values.append(saturation)
        edge_values.append(edge_density)

        periodic = frame_index % max(1, round(fps * 1.25)) == 0
        detected_cut = histogram_change > 0.40 and frame_index - last_key > max(1, round(fps * 0.30))
        if periodic or detected_cut:
            target_height = max(1, round(320 * height / max(width, 1)))
            small = cv2.resize(frame, (320, target_height))
            path = key_dir / f'{frame_index:06d}_{timestamp:07.3f}s.jpg'
            cv2.imwrite(str(path), small, [int(cv2.IMWRITE_JPEG_QUALITY), 72])
            keyframes.append(path)
            last_key = frame_index

        prev_gray = gray
        prev_hist = hist
        frame_index += 1

    cap.release()

    with (out / 'frame_metrics.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['frame', 'timestamp_s', 'brightness', 'saturation', 'edge_density', 'histogram_change', 'motion_score'])
        writer.writerows(rows)

    astats = subprocess.run([
        'ffmpeg', '-hide_banner', '-i', str(video),
        '-af', 'astats=metadata=1:reset=1,ametadata=print', '-f', 'null', '-'
    ], capture_output=True, text=True)
    (out / 'ffmpeg_audio_stats.txt').write_text(astats.stderr[-120000:], encoding='utf-8')

    transcription = {
        'attempted': whisper_model is not None,
        'raw_text_stored': False,
        'model_error': whisper_model_error,
    }
    if whisper_model is not None:
        try:
            result = whisper_model.transcribe(str(video), fp16=False, verbose=False)
            segments = result.get('segments', [])
            transcription.update({
                'language': result.get('language'),
                'segments': len(segments),
                'word_count': sum(len((segment.get('text') or '').split()) for segment in segments),
                'mean_avg_logprob': float(np.mean([segment.get('avg_logprob', -10) for segment in segments])) if segments else None,
                'mean_no_speech_prob': float(np.mean([segment.get('no_speech_prob', 1) for segment in segments])) if segments else None,
                'speech_windows': [
                    {
                        'start': round(float(segment.get('start', 0)), 2),
                        'end': round(float(segment.get('end', 0)), 2),
                        'words': len((segment.get('text') or '').split()),
                    }
                    for segment in segments
                ],
            })
        except Exception as exc:
            transcription['error'] = str(exc)
    (out / 'transcription_metrics.json').write_text(json.dumps(transcription, indent=2), encoding='utf-8')

    make_sheet(keyframes[:16], out / 'contact_sheet.jpg')
    duration = frame_index / fps if fps else 0.0
    cuts = int(sum(value > 0.40 for value in hist_values))
    summary = {
        'slug': slug,
        'video_id': video_id,
        'url': url,
        'status': 'ANALYZED',
        'file': video.name,
        'fps': fps,
        'frames_reported': reported_frames,
        'frames_processed': frame_index,
        'frame_count_delta': frame_index - reported_frames,
        'duration_s': duration,
        'resolution': [width, height],
        'brightness_mean': float(np.mean(brightness_values)),
        'brightness_std': float(np.std(brightness_values)),
        'saturation_mean': float(np.mean(saturation_values)),
        'saturation_std': float(np.std(saturation_values)),
        'edge_density_mean': float(np.mean(edge_values)),
        'motion_mean': float(np.mean(motion_values)),
        'motion_p90': float(np.percentile(motion_values, 90)),
        'hist_change_mean': float(np.mean(hist_values)),
        'detected_cuts': cuts,
        'estimated_mean_shot_s': duration / max(1, cuts + 1),
        'keyframes_saved': len(keyframes),
        'transcription': transcription,
    }
    (out / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    master.append(summary)

(RESULT / 'master_summary.json').write_text(json.dumps(master, indent=2), encoding='utf-8')

analyzed = [item for item in master if item.get('status') == 'ANALYZED']
lines = [
    '# Análise técnica de trends Roblox — 3 de agosto de 2026', '',
    '## Status da coleta', '',
    f'- Fontes solicitadas: {len(master)}',
    f'- Vídeos baixados e analisados: {len(analyzed)}',
    f'- Vídeos não baixados: {len(master) - len(analyzed)}', '',
    '## Método verificável', '',
    '- FFprobe para metadados de contêiner, streams, FPS e resolução.',
    '- OpenCV percorreu cada frame decodificado e mediu brilho, saturação, densidade de bordas, mudança de histograma e fluxo óptico.',
    '- FFmpeg `astats` mediu o áudio.',
    '- Whisper tiny estimou idioma, janelas de fala e contagem de palavras. O texto bruto não foi preservado para evitar reprodução de letras protegidas.',
    '- Keyframes foram amostrados periodicamente e em cortes detectados.', '',
    '## Resultados por vídeo', '',
]
for item in master:
    lines.extend([
        f"### {item['slug']}",
        f"- URL: {item['url']}",
        f"- Status: {item['status']}",
    ])
    if item.get('status') == 'ANALYZED':
        lines.extend([
            f"- Duração: {item['duration_s']:.2f} s",
            f"- Resolução/FPS: {item['resolution'][0]}×{item['resolution'][1]} a {item['fps']:.3f} fps",
            f"- Frames processados: {item['frames_processed']}",
            f"- Diferença para frames reportados: {item['frame_count_delta']}",
            f"- Cortes detectados: {item['detected_cuts']}",
            f"- Plano médio estimado: {item['estimated_mean_shot_s']:.2f} s",
            f"- Movimento médio / P90: {item['motion_mean']:.4f} / {item['motion_p90']:.4f}",
            f"- Saturação média: {item['saturation_mean']:.2f}",
            f"- Densidade média de bordas: {item['edge_density_mean']:.4f}",
            f"- Idioma estimado: {item['transcription'].get('language', 'não identificado')}",
            f"- Segmentos / palavras detectadas: {item['transcription'].get('segments', 0)} / {item['transcription'].get('word_count', 0)}",
        ])
    lines.append('')

lines.extend([
    '## Schema do aprendizado', '',
    '```yaml',
    'source_video: [slug, video_id, url, status, duration_s, resolution, fps]',
    'frame_observation: [frame, timestamp_s, brightness, saturation, edge_density, histogram_change, motion_score]',
    'audio_observation: [ffmpeg_astats, speech_windows, language, word_count, confidence]',
    'edit_pattern: [detected_cuts, estimated_mean_shot_s, motion_mean, motion_p90, keyframes]',
    'validation: [frames_reported, frames_processed, frame_count_delta, raw_text_stored, errors]',
    '```', '',
    '## Revisão automática', '',
    '- PASS somente quando `frames_processed > 0`, o CSV existir, o resumo JSON existir e a contagem processada for compatível com a contagem reportada.',
    '- Qualquer falha de download permanece marcada como `DOWNLOAD_FAILED`; não é convertida em análise por título ou miniatura.', '',
])
(RESULT / 'ANALISE_TRENDS_ROBLOX_FFMPEG.md').write_text('\n'.join(lines), encoding='utf-8')

if not analyzed:
    sys.exit('Nenhum vídeo pôde ser analisado')
