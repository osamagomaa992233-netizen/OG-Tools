"""OG Tools: deterministic non-destructive media transforms using local FFmpeg.

Original implementation. Inspired by workflows available in auto-editor (Unlicense)
and other open-source editing projects; no upstream source code is bundled.
"""
import json
import math
import os
import re
import shutil
import struct
import subprocess
import tempfile
import wave
from pathlib import Path

SILENCE_RE = re.compile(r'silence_(start|end):\s*([0-9.]+)')
XFADE_TYPES = ('fade','wipeleft','wiperight','wipeup','wipedown','slideleft','slideright','slideup','slidedown','circlecrop','radial','pixelize','smoothleft','smoothright','dissolve','hblur')
SFX_TYPES = ('click','pop','whoosh','rise','impact','beep','notification','success','error','sweep','glitch','tick')

def need(command):
    executable = shutil.which(command)
    if not executable:
        raise RuntimeError(f'{command} is not installed or on PATH')
    return executable

def run(args, timeout=1800):
    try:
        result = subprocess.run([str(v) for v in args], capture_output=True, text=True, timeout=timeout, errors='replace')
    except subprocess.TimeoutExpired as e:
        raise RuntimeError('Process timed out') from e
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or 'External program failed')[-2200:])
    return result

def probe(path):
    need('ffprobe')
    p=Path(path)
    if not p.is_file():
        raise FileNotFoundError(f'Media not found: {path}')
    out=run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',p])
    info=json.loads(out.stdout)
    try: duration=float(info.get('format',{}).get('duration',0))
    except (TypeError,ValueError): duration=0
    streams=info.get('streams',[])
    return {'duration':duration,'audio':any(x.get('codec_type')=='audio' for x in streams),
            'video':any(x.get('codec_type')=='video' for x in streams),
            'width':next((x.get('width') for x in streams if x.get('codec_type')=='video'),None),
            'height':next((x.get('height') for x in streams if x.get('codec_type')=='video'),None)}

def parse_silence(log, duration):
    result=[]; start=None
    for kind, val in SILENCE_RE.findall(log):
        t=max(0,min(duration,float(val)))
        if kind=='start': start=t
        elif start is not None:
            if t>start: result.append([start,t])
            start=None
    if start is not None and duration>start:result.append([start,duration])
    return [[round(a,3),round(b,3)] for a,b in result]

def complement_intervals(silences,duration,padding=.1):
    result=[]; t=0
    for a,b in sorted(silences):
        a=max(0,min(float(a),duration));b=max(a,min(float(b),duration))
        if a>t:result.append([max(0,t-padding),min(duration,a+padding)])
        t=max(t,b)
    if t<duration:result.append([max(0,t-padding),duration])
    merged=[]
    for a,b in result:
        if b-a<.015:continue
        if merged and a<=merged[-1][1]:merged[-1][1]=max(merged[-1][1],b)
        else:merged.append([a,b])
    return [[round(a,3),round(b,3)] for a,b in merged]

def detect_silence(source, noise=-35,minimum=.5,padding=.1):
    need('ffmpeg');info=probe(source)
    if not info['audio']:raise ValueError('Selected media has no audio stream')
    if not (-90<=float(noise)<=0):raise ValueError('noise must be between -90 and 0 dB')
    if not (.05<=float(minimum)<=30):raise ValueError('min silence must be 0.05..30s')
    if not (0<=float(padding)<=3):raise ValueError('padding must be 0..3s')
    # ffmpeg silencedetect logs to stderr, returns success for valid audio.
    r=run(['ffmpeg','-hide_banner','-nostats','-i',source,'-map','0:a:0','-af',f'silencedetect=noise={float(noise)}dB:d={float(minimum)}','-f','null','-'])
    intervals=parse_silence(r.stderr,info['duration'])
    keep=complement_intervals(intervals,info['duration'],float(padding))
    return {'source':str(Path(source).resolve()),'duration':round(info['duration'],3),
        'silence':intervals,'keep':keep,'removed_seconds':round(info['duration']-sum(b-a for a,b in keep),3),
        'parameters':{'noise_db':float(noise),'min_silence':float(minimum),'padding':float(padding)}}

def safe_output(source,output):
    target=Path(output).expanduser().resolve();inp=Path(source).expanduser().resolve()
    if target==inp:raise ValueError('Refusing to overwrite the source file')
    target.parent.mkdir(parents=True,exist_ok=True)
    return target

def render_intervals(source,output,intervals,speeds=None):
    """Non-destructive rendering of keep intervals (and optional per-interval speeds).
    Media is rendered to a new MP4. Works for video, audio-only outputs WAV.
    Does not mutate a Premiere sequence or assume media maps 1:1 to timeline.
    """
    need('ffmpeg');info=probe(source)
    if not intervals:raise ValueError('No media intervals to render')
    if speeds is None:speeds=[1.]*len(intervals)
    if len(speeds)!=len(intervals):raise ValueError('speeds must match intervals')
    if any(float(s)<=0 or float(s)>16 for s in speeds):raise ValueError('Speed outside 0..16')
    target=safe_output(source,output)
    with tempfile.TemporaryDirectory(prefix='og-tools-') as directory:
        segments=[]
        for i,((a,b),speed) in enumerate(zip(intervals,speeds)):
            a,b=float(a),float(b);speed=float(speed)
            if a<0 or b<=a or b>info['duration']+.08:raise ValueError('Invalid interval')
            segment=Path(directory)/f'{i:04}.mp4' if info['video'] else Path(directory)/f'{i:04}.wav'
            args=['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',f'{a:.4f}','-i',source,'-t',f'{b-a:.4f}']
            if info['video']:
                args+=['-vf',f'setpts=(PTS-STARTPTS)/{speed:.6f},fps=25,format=yuv420p','-c:v','libx264','-preset','veryfast','-crf','20']
            else:args+=['-vn']
            if info['audio']:
                # atempo natively accepts 0.5–2; chain for any positive speed.
                fs=[];remaining=speed
                while remaining>2:fs.append('atempo=2');remaining/=2
                while remaining<.5:fs.append('atempo=0.5');remaining/=.5
                fs.append(f'atempo={remaining:.6f}')
                args+=['-af',','.join(fs),'-c:a','aac','-b:a','160k'] if info['video'] else ['-af',','.join(fs),'-c:a','pcm_s16le']
            else:args+=['-an']
            args+=[segment]
            run(args)
            segments.append(segment)
        listpath=Path(directory)/'concat.txt'
        # The paths here are known temp paths, never user-supplied concat syntax.
        listpath.write_text(''.join("file '"+str(s).replace("'", "'\\''")+"'\n" for s in segments),encoding='utf8')
        args=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',listpath]
        if info['video']:
            args+=['-c','copy','-movflags','+faststart',target]
        else:
            args+=['-c:a','pcm_s16le',target]
        run(args)
    return {'output':str(target),'segments':len(intervals),'duration':round(probe(target)['duration'],3)}

def remove_silence(source,output,noise=-35,minimum=.5,padding=.1):
    d=detect_silence(source,noise,minimum,padding)
    if not d['keep']:raise ValueError('Entire recording is silent; refusing to produce an empty file')
    d['render']=render_intervals(source,output,d['keep'])
    return d

def export_premiere_xml(source,output):
    """Adapter to WyattBlue/auto-editor (Unlicense). Requires separate install.
    Exports an editable Premiere XML sequence when the installed version supports it.
    """
    need('auto-editor')
    from pathlib import Path
    if not Path(source).is_file():raise FileNotFoundError(source)
    target=safe_output(source,output)
    run(['auto-editor',source,'--export','premiere','-o',target])
    if not target.is_file():raise RuntimeError('auto-editor did not create the requested XML')
    return {'output':str(target),'format':'Premiere XML','note':'Import this XML to create a new editable sequence; no active sequence is changed'}

def make_speed_ramp(source,output,speeds=(.65,1.8,.85)):
    info=probe(source);duration=info['duration']
    if not duration:raise ValueError('Invalid duration')
    intervals=[[duration*i/len(speeds),duration*(i+1)/len(speeds)] for i in range(len(speeds))]
    return render_intervals(source,output,intervals,speeds)

def enhance_audio(source,output,mode='voice'):
    info=probe(source)
    if not info['audio']:raise ValueError('No audio in media')
    target=safe_output(source,output)
    modes={
      'voice':'highpass=f=75,lowpass=f=12500,afftdn=nf=-24,dynaudnorm=f=150:g=12',
      'podcast':'highpass=f=80,lowpass=f=14000,afftdn=nf=-30,acompressor=threshold=-20dB:ratio=2.5:attack=15:release=180',
      'normalize':'loudnorm=I=-16:TP=-1.5:LRA=11',
      'denoise':'highpass=f=65,afftdn=nf=-24'
    }
    if mode not in modes:raise ValueError('Unknown audio mode')
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',source,'-vn','-af',modes[mode],'-c:a','pcm_s16le',target])
    return {'output':str(target),'mode':mode}

def transition(first,second,output,kind='fade',duration=.6,width=720,height=1280,fps=25):
    if kind not in XFADE_TYPES:raise ValueError('Unknown transition')
    for p in (first,second):
        if not probe(p)['video']:raise ValueError('Both sources must contain video')
    d1=probe(first)['duration'];d2=probe(second)['duration'];duration=float(duration)
    if not (.08<=duration<min(d1,d2)):raise ValueError('Transition duration too long')
    target=safe_output(first,output)
    if target==Path(second).resolve():raise ValueError('Refusing to overwrite source 2')
    # Video-only output; we intentionally do NOT silently alter/replace music tracks.
    fil=f'[0:v]fps={fps},scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,settb=AVTB,format=yuv420p[v0];'
    fil+=f'[1:v]fps={fps},scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,settb=AVTB,format=yuv420p[v1];'
    fil+=f'[v0][v1]xfade=transition={kind}:duration={duration}:offset={d1-duration:.3f}[v]'
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',first,'-i',second,'-filter_complex',fil,
        '-map','[v]','-an','-c:v','libx264','-preset','veryfast','-pix_fmt','yuv420p',target])
    return {'output':str(target),'transition':kind,'audio':'not included'}

def sfx(output,kind='whoosh',duration=.7,frequency=440,sr=24000):
    if kind not in SFX_TYPES:raise ValueError('Unknown sound effect')
    if not .08<=float(duration)<=5:raise ValueError('Duration must be .08..5 seconds')
    import random
    rng=random.Random(707) # deterministic reproducible procedural SFX
    target=Path(output).expanduser().resolve();target.parent.mkdir(parents=True,exist_ok=True)
    n=int(float(duration)*sr)
    with wave.open(str(target),'wb') as handle:
        handle.setnchannels(1);handle.setsampwidth(2);handle.setframerate(sr)
        frames=bytearray(); phase=0.
        for i in range(n):
            t=i/sr;u=i/max(1,n-1)
            envelope=(1-u)**(2 if kind in ('click','pop','impact','tick') else 1)
            noise=rng.uniform(-1,1)
            f=float(frequency)
            if kind in ('rise','sweep','whoosh'):f*=.5+2.5*u
            if kind in ('success','notification'):f*=1.0 if u<.5 else 1.5
            if kind=='error':f*=1 if u<.4 else .7
            phase+=2*math.pi*f/sr
            if kind in ('whoosh','sweep'):waveval=noise*(.25+.4*math.sin(math.pi*u))
            elif kind in ('click','impact','glitch','tick'):waveval=noise*(.9 if kind!='glitch' or int(t*80)%3 else 0)
            elif kind in ('pop','success','notification','beep','error','rise'):waveval=math.sin(phase)+.15*math.sin(phase*2)
            else:waveval=math.sin(phase)
            attack=min(1.,t/.012)
            sample=int(max(-1,min(1,waveval*envelope*attack*.55))*32767)
            frames+=struct.pack('<h',sample)
        handle.writeframes(frames)
    return {'output':str(target),'kind':kind,'duration':round(n/sr,3)}

def download_owned(url,output_dir):
    """Opt-in use of yt-dlp for media the user owns/has permission to download."""
    need('yt-dlp');folder=Path(output_dir).resolve();folder.mkdir(parents=True,exist_ok=True)
    if not url.startswith(('https://','http://')):raise ValueError('Only HTTP(S) URLs allowed')
    # Safeguards avoid browser cookies and credential extraction by default.
    result=run(['yt-dlp','--no-playlist','--restrict-filenames','-P',folder,'--print','after_move:filepath',url])
    return {'output':result.stdout.strip().splitlines()[-1] if result.stdout.strip() else str(folder)}
