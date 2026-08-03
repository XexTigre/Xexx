#!/usr/bin/env python3
import csv
import hashlib
import json
import math
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw
import whisper

WORK = Path(os.environ.get('WORK_DIR', '/tmp/roblox_ia_trends'))
RESULT = Path(os.environ.get('RESULT_DIR', 'temp/roblox_ia_analysis_2026-08-03'))
VIDEOS = WORK / 'videos'
RESULT.mkdir(parents=True, exist_ok=True)

STOPWORDS = {
    'the','a','an','and','or','but','to','of','in','on','for','with','is','it','this','that','you','i','we','they','he','she','my','your','our','so','just','not','do','did','be','are','was','were','have','has','had','at','as','from','what','when','how','why','who','me','can','like','get','got','all','up','out','if','then','there','here','one','go','going','oh','yeah','yes','no',
    'o','a','os','as','um','uma','e','ou','mas','de','da','do','das','dos','em','no','na','nos','nas','para','por','com','é','isso','isto','você','eu','nós','eles','ela','ele','meu','minha','seu','sua','que','como','quando','porque','quem','não','sim','já','só','muito','mais','vai','vou','foi','ser','ter','tem','aqui','ali',
    'el','la','los','las','un','una','y','o','pero','de','del','en','por','para','con','es','esto','eso','yo','tú','usted','nosotros','ellos','ella','él','mi','su','que','como','cuando','porque','quién','no','sí','muy','más','va','voy','fue','ser','tener','tiene','aquí','allí'
}


def ffprobe(path):
    proc = subprocess.run([
        'ffprobe','-v','error','-show_entries',
        'format=duration,size,bit_rate,format_name:stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,sample_rate,channels,bit_rate',
        '-of','json',str(path)
    ], capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open('rb') as file:
        while True:
            chunk = file.read(1024 * 1024)
            if not chunk: break
            digest.update(chunk)
    return digest.hexdigest()


def optical_flow(prev_gray, gray):
    if prev_gray is None:
        return 0.0
    a = cv2.resize(prev_gray, (160, 90), interpolation=cv2.INTER_AREA)
    b = cv2.resize(gray, (160, 90), interpolation=cv2.INTER_AREA)
    flow = cv2.calcOpticalFlowFarneback(a, b, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    return float(np.mean(np.linalg.norm(flow, axis=2)))


def region_edge_density(gray, y0, y1):
    h = gray.shape[0]
    crop = gray[int(h*y0):max(int(h*y1), int(h*y0)+1), :]
    if crop.size == 0: return 0.0
    return float((cv2.Canny(crop, 100, 200) > 0).mean())


def make_contact_sheet(paths, timestamps, output, cols=4, thumb=(240, 426)):
    cells = []
    for path, timestamp in zip(paths, timestamps):
        image = Image.open(path).convert('RGB')
        image.thumbnail(thumb)
        canvas = Image.new('RGB', thumb, 'white')
        canvas.paste(image, ((thumb[0]-image.width)//2, (thumb[1]-image.height)//2))
        draw = ImageDraw.Draw(canvas)
        label = f'{timestamp:.2f}s'
        box = draw.textbbox((0,0), label)
        draw.rectangle((4,4,12+box[2],10+box[3]), fill='black')
        draw.text((8,7), label, fill='white')
        cells.append(canvas)
    if not cells: return
    rows = math.ceil(len(cells)/cols)
    sheet = Image.new('RGB', (cols*thumb[0], rows*thumb[1]), 'white')
    for index, cell in enumerate(cells):
        sheet.paste(cell, ((index%cols)*thumb[0], (index//cols)*thumb[1]))
    sheet.save(output, quality=88, optimize=True)


def parse_audio(path, output_dir):
    wav = output_dir / 'audio_mono_16k.wav'
    subprocess.run([
        'ffmpeg','-y','-hide_banner','-loglevel','error','-i',str(path),
        '-vn','-ac','1','-ar','16000','-c:a','pcm_s16le',str(wav)
    ], check=False)
    if not wav.exists() or wav.stat().st_size < 100:
        return {'has_audio': False}
    raw = subprocess.run([
        'ffmpeg','-hide_banner','-loglevel','error','-i',str(wav),'-f','s16le','-ac','1','-ar','16000','-'
    ], capture_output=True, check=True).stdout
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if samples.size == 0:
        return {'has_audio': False}
    frame = 800
    usable = samples[:(samples.size//frame)*frame]
    blocks = usable.reshape(-1, frame) if usable.size else np.empty((0,frame))
    rms = np.sqrt(np.mean(blocks*blocks, axis=1) + 1e-12) if len(blocks) else np.array([])
    db = 20*np.log10(rms + 1e-9) if rms.size else np.array([])
    flux = np.maximum(0, np.diff(rms, prepend=rms[:1])) if rms.size else np.array([])
    threshold = np.median(flux) + 2.5*np.std(flux) if flux.size else 0
    peaks = int(np.sum(flux > threshold)) if threshold > 0 else 0
    duration = samples.size/16000
    audio = {
        'has_audio': True,
        'sample_rate': 16000,
        'duration_s': duration,
        'rms_mean': float(np.mean(rms)) if rms.size else None,
        'rms_p90': float(np.percentile(rms,90)) if rms.size else None,
        'db_mean': float(np.mean(db)) if db.size else None,
        'db_p10': float(np.percentile(db,10)) if db.size else None,
        'db_p90': float(np.percentile(db,90)) if db.size else None,
        'dynamic_range_db_p10_p90': float(np.percentile(db,90)-np.percentile(db,10)) if db.size else None,
        'onset_peaks': peaks,
        'onset_rate_per_min': peaks/max(duration/60,1e-9),
        'silence_ratio_below_minus40db': float(np.mean(db < -40)) if db.size else None,
    }
    wav.unlink(missing_ok=True)
    return audio


def transcript_signals(model, video, duration):
    try:
        result = model.transcribe(str(video), fp16=False, verbose=False)
        segments = result.get('segments') or []
        full_text = ' '.join((segment.get('text') or '').strip() for segment in segments).strip()
        words = re.findall(r"[\wÀ-ÿ']+", full_text.lower(), flags=re.UNICODE)
        content_words = [word for word in words if len(word) > 2 and word not in STOPWORDS and not word.isdigit()]
        top = [word for word, _ in Counter(content_words).most_common(10)]
        speech_duration = sum(max(0.0, float(s.get('end',0))-float(s.get('start',0))) for s in segments)
        excerpt_words = words[:8]
        return {
            'attempted': True,
            'raw_text_stored': False,
            'language': result.get('language'),
            'segment_count': len(segments),
            'word_count': len(words),
            'words_per_second': len(words)/max(duration,1e-9),
            'speech_duration_s': speech_duration,
            'speech_coverage_ratio': speech_duration/max(duration,1e-9),
            'mean_avg_logprob': float(np.mean([s.get('avg_logprob',-10) for s in segments])) if segments else None,
            'mean_no_speech_prob': float(np.mean([s.get('no_speech_prob',1) for s in segments])) if segments else None,
            'top_keywords': top,
            'short_excerpt_max_8_words': ' '.join(excerpt_words),
            'speech_windows': [
                {'start': round(float(s.get('start',0)),2), 'end': round(float(s.get('end',0)),2), 'word_count': len(re.findall(r"[\wÀ-ÿ']+", s.get('text') or '', flags=re.UNICODE))}
                for s in segments
            ],
        }
    except Exception as exc:
        return {'attempted': True, 'raw_text_stored': False, 'error': str(exc)}


sources_path = RESULT / 'selected_sources.json'
sources = json.loads(sources_path.read_text(encoding='utf-8')) if sources_path.exists() else []
source_by_slug = {item.get('slug'): item for item in sources}
model = whisper.load_model('tiny')
master = []

for video in sorted(VIDEOS.glob('*.mp4')):
    slug = video.stem
    source = source_by_slug.get(slug, {})
    out = RESULT / slug
    key_dir = out / 'keyframes'
    out.mkdir(parents=True, exist_ok=True)
    key_dir.mkdir(parents=True, exist_ok=True)
    probe = ffprobe(video)
    (out/'ffprobe.json').write_text(json.dumps(probe, indent=2), encoding='utf-8')

    cap = cv2.VideoCapture(str(video))
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    reported_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    duration = float(probe.get('format',{}).get('duration') or (reported_frames/fps if fps else 0))

    rows=[]; brightness=[]; saturation=[]; edge=[]; top_edge=[]; bottom_edge=[]; hist_change=[]; motion=[]
    prev_gray=None; prev_hist=None; index=0; cuts=[]
    candidates=[]
    sample_interval=max(1,round(fps*max(0.75,duration/24 if duration else 1)))
    while True:
        ok, frame = cap.read()
        if not ok: break
        gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        hsv=cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
        br=float(gray.mean()); sa=float(hsv[:,:,1].mean()); ed=float((cv2.Canny(gray,100,200)>0).mean())
        te=region_edge_density(gray,0,0.22); be=region_edge_density(gray,0.78,1.0)
        hist=cv2.calcHist([hsv],[0,1],None,[24,16],[0,180,0,256]); cv2.normalize(hist,hist)
        hc=0.0 if prev_hist is None else float(cv2.compareHist(prev_hist,hist,cv2.HISTCMP_BHATTACHARYYA))
        mo=optical_flow(prev_gray,gray); ts=index/fps
        is_cut=hc>0.40
        if is_cut: cuts.append(ts)
        rows.append([index,round(ts,4),round(br,4),round(sa,4),round(ed,6),round(te,6),round(be,6),round(hc,6),round(mo,6),int(is_cut)])
        brightness.append(br); saturation.append(sa); edge.append(ed); top_edge.append(te); bottom_edge.append(be); hist_change.append(hc); motion.append(mo)
        if index % sample_interval == 0 or (is_cut and (not candidates or index-candidates[-1][0]>fps*0.4)):
            candidates.append((index,ts,frame.copy(),hc,mo))
        prev_gray=gray; prev_hist=hist; index+=1
    cap.release()

    with (out/'frame_metrics.csv').open('w',newline='',encoding='utf-8') as file:
        writer=csv.writer(file)
        writer.writerow(['frame','timestamp_s','brightness','saturation','edge_density','top_edge_density','bottom_edge_density','histogram_change','motion_score','scene_cut'])
        writer.writerows(rows)

    # Keep at most 24 representative frames, prioritizing time coverage and strong cuts/motion.
    if len(candidates)>24:
        base_indices=np.linspace(0,len(candidates)-1,18,dtype=int).tolist()
        priority=sorted(range(len(candidates)), key=lambda i:(candidates[i][3],candidates[i][4]), reverse=True)[:10]
        chosen=sorted(set(base_indices+priority), key=lambda i:candidates[i][1])[:24]
        candidates=[candidates[i] for i in chosen]
    key_paths=[]; key_times=[]
    for frame_index, ts, frame, _, _ in candidates:
        target_w=360; target_h=max(1,round(target_w*height/max(width,1)))
        small=cv2.resize(frame,(target_w,target_h),interpolation=cv2.INTER_AREA)
        path=key_dir/f'{frame_index:07d}_{ts:08.3f}s.jpg'
        cv2.imwrite(str(path),small,[int(cv2.IMWRITE_JPEG_QUALITY),82])
        key_paths.append(path); key_times.append(ts)
    make_contact_sheet(key_paths,key_times,out/'contact_sheet.jpg')

    audio=parse_audio(video,out)
    transcript=transcript_signals(model,video,duration)
    (out/'audio_metrics.json').write_text(json.dumps(audio,indent=2),encoding='utf-8')
    (out/'transcription_signals.json').write_text(json.dumps(transcript,indent=2,ensure_ascii=False),encoding='utf-8')

    frame_delta=index-reported_frames
    overlay_edge_ratio=(float(np.mean(top_edge)+np.mean(bottom_edge))/(2*float(np.mean(edge)))) if edge and np.mean(edge)>0 else None
    summary={
        'slug':slug,
        'identifier':source.get('identifier'),
        'title':source.get('title'),
        'creator':source.get('creator'),
        'publicdate':source.get('publicdate'),
        'archive_url':f"https://archive.org/details/{source.get('identifier')}" if source.get('identifier') else None,
        'download_url':source.get('download_url'),
        'sha256':sha256_file(video),
        'duration_s':duration,
        'resolution':[width,height],
        'orientation':'vertical' if height>width else ('square' if height==width else 'horizontal'),
        'fps':fps,
        'frames_reported':reported_frames,
        'frames_processed':index,
        'frame_count_delta':frame_delta,
        'brightness_mean':float(np.mean(brightness)) if brightness else None,
        'brightness_std':float(np.std(brightness)) if brightness else None,
        'saturation_mean':float(np.mean(saturation)) if saturation else None,
        'saturation_std':float(np.std(saturation)) if saturation else None,
        'edge_density_mean':float(np.mean(edge)) if edge else None,
        'top_edge_density_mean':float(np.mean(top_edge)) if top_edge else None,
        'bottom_edge_density_mean':float(np.mean(bottom_edge)) if bottom_edge else None,
        'overlay_edge_ratio_proxy':overlay_edge_ratio,
        'motion_mean':float(np.mean(motion)) if motion else None,
        'motion_p90':float(np.percentile(motion,90)) if motion else None,
        'histogram_change_mean':float(np.mean(hist_change)) if hist_change else None,
        'scene_cuts_detected':len(cuts),
        'cut_rate_per_min':len(cuts)/max(duration/60,1e-9),
        'estimated_mean_shot_s':duration/max(len(cuts)+1,1),
        'representative_keyframes':len(key_paths),
        'audio':audio,
        'transcription':transcript,
        'validation':{
            'video_decoded':index>0,
            'frame_csv_written':(out/'frame_metrics.csv').exists(),
            'frame_count_compatible':abs(frame_delta)<=max(3,reported_frames*0.01) if reported_frames else index>0,
            'contact_sheet_written':(out/'contact_sheet.jpg').exists(),
            'raw_transcript_not_stored':transcript.get('raw_text_stored') is False,
        }
    }
    summary['validation']['pass']=all(summary['validation'].values())
    (out/'summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
    master.append(summary)

(RESULT/'master_summary.json').write_text(json.dumps(master,indent=2,ensure_ascii=False),encoding='utf-8')
validation={
    'videos_expected':3,
    'videos_analyzed':len(master),
    'total_frames_processed':sum(item['frames_processed'] for item in master),
    'all_video_validations_pass':bool(master) and all(item['validation']['pass'] for item in master),
    'raw_transcripts_stored':False,
}
validation['review_pass']=validation['videos_analyzed']==validation['videos_expected'] and validation['all_video_validations_pass']
(RESULT/'validation.json').write_text(json.dumps(validation,indent=2),encoding='utf-8')
if not validation['review_pass']:
    sys.exit('Analysis validation did not pass')
