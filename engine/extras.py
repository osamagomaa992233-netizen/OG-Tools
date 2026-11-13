"""Optional adapters and deterministic utilities used by OG Tools.
External projects are called as separate installed tools, not silently bundled.
"""
import csv
import json
import shutil
from pathlib import Path

def srt_seconds(seconds):
    ms=max(0,round(float(seconds)*1000));h,ms=divmod(ms,3600000)
    m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'

def write_srt(rows,out):
    text='\n\n'.join(f'{i}\n{srt_seconds(r["start"])} --> {srt_seconds(r["end"])}\n{r["text"].strip()}' for i,r in enumerate(rows,1))
    p=Path(out).resolve();p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(text+'\n' if text else '',encoding='utf-8-sig')
    return {'output':str(p),'lines':len(rows)}

def transcribe(media,output,language='auto',model='small',device='cpu'):
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError('faster-whisper not installed. Run: python -m pip install faster-whisper') from exc
    if not Path(media).is_file():raise FileNotFoundError(media)
    if language not in ('auto','ar','en'):raise ValueError('Use auto, ar, en')
    if model not in ('tiny','base','small','medium','large-v3','turbo'):
        raise ValueError('Unsupported Whisper model')
    whisper=WhisperModel(model,device=device,compute_type='int8' if device=='cpu' else 'float16')
    segs,_=whisper.transcribe(str(media),language=None if language=='auto' else language,beam_size=5,vad_filter=True)
    rows=[{'start':round(float(s.start),3),'end':round(float(s.end),3),'text':s.text.strip()} for s in segs if s.text.strip()]
    return write_srt(rows,output)

def format_srt(source,output,max_chars=35):
    import re
    if not Path(source).is_file():raise FileNotFoundError(source)
    raw=Path(source).read_text(encoding='utf-8-sig')
    sections=re.split(r'\n\s*\n',raw.replace('\r\n','\n').strip());rows=[]
    for block in sections:
        lines=block.strip().splitlines();timeline=next((idx for idx,line in enumerate(lines) if '-->' in line),None)
        if timeline is None:continue
        match=re.match(r'\s*(\d\d:\d\d:\d\d[,\.]\d+)\s*-->\s*(\d\d:\d\d:\d\d[,\.]\d+)',lines[timeline])
        if not match:continue
        def sec(st):
            h,m,s=st.replace(',','.').split(':');return int(h)*3600+int(m)*60+float(s)
        text=' '.join(lines[timeline+1:]).strip()
        if not text:continue
        chunks=[];line=''
        for word in text.split():
            if line and len(line)+len(word)+1>max_chars:chunks.append(line);line=word
            else:line=(line+' '+word).strip()
        if line:chunks.append(line)
        rows.append({'start':sec(match.group(1)),'end':sec(match.group(2)),'text':'\n'.join(chunks)})
    return write_srt(rows,output)

def remove_background(source,output,model='u2net'):
    if not Path(source).is_file():raise FileNotFoundError(source)
    # rembg MIT code; ONNX model weights can have distinct commercial licenses.
    try:
        from rembg import remove,new_session
    except ImportError as exc:
        raise RuntimeError('rembg unavailable: pip install "rembg[cpu]"') from exc
    if model not in ('u2net','u2netp','silueta'):
        raise ValueError('Only u2net/u2netp/silueta adapters enabled; check model licenses')
    p=Path(output).resolve();p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes(remove(Path(source).read_bytes(),session=new_session(model)))
    return {'output':str(p),'model':model}

def organizer(source,output,apply=False):
    """Safe copy-only asset organizer. Existing source files are never moved."""
    root=Path(source).resolve()
    if not root.is_dir():raise ValueError('Source should be a directory')
    dest=Path(output).resolve()
    if root==dest or root in dest.parents:raise ValueError('Destination cannot be nested inside source')
    categories={
      'Video':{'.mp4','.mov','.mxf','.avi','.mkv','.webm'},
      'Audio':{'.wav','.mp3','.m4a','.aiff','.flac'},
      'Images':{'.jpg','.jpeg','.png','.tif','.tiff','.webp','.psd'},
      'Graphics':{'.svg','.ai','.eps','.mogrt'},
      'Captions':{'.srt','.vtt','.ass'},
      'Projects':{'.prproj','.aep','.xml','.otio'}
    }
    result=[]
    for src in sorted(root.rglob('*')):
        if not src.is_file():continue
        cat=next((name for name,exts in categories.items() if src.suffix.lower() in exts),'Other')
        # Duplicate names from different subfolders retain source's relative path.
        dst=dest/cat/src.relative_to(root)
        result.append({'src':str(src),'dst':str(dst),'category':cat})
        if apply:
            dst.parent.mkdir(parents=True,exist_ok=True)
            if dst.exists():raise FileExistsError(f'Never overwrite existing file: {dst}')
            shutil.copy2(src,dst)
    return {'files':len(result),'copied':bool(apply),'plan':result,'note':'Only copies, never relocates original Premiere-linked media.'}

def easing_csv(output,kind='ease-out-cubic',steps=60):
    if not 5<=steps<=1000:raise ValueError('Invalid steps')
    import math
    def calc(x):
        if kind=='linear':return x
        if kind=='ease-in-cubic':return x**3
        if kind=='ease-out-cubic':return 1-(1-x)**3
        if kind=='ease-in-out-cubic':return 4*x*x*x if x<.5 else 1-(-2*x+2)**3/2
        if kind=='ease-out-back':return 1+2.70158*(x-1)**3+1.70158*(x-1)**2
        if kind=='ease-out-elastic':return 0 if x==0 else 1 if x==1 else 2**(-10*x)*math.sin((x*10-.75)*2*math.pi/3)+1
        raise ValueError('Unknown easing')
    p=Path(output).resolve();p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',newline='',encoding='utf8') as handle:
        w=csv.writer(handle);w.writerow(('t','value'))
        for i in range(steps+1):
            x=i/steps;w.writerow((round(x,6),round(calc(x),6)))
    return {'output':str(p),'kind':kind,'samples':steps+1}

def track_motion(source,output,x,y,w,h,step=1,max_frames=500):
    """ROI template tracker -> CSV coordinates; OFFLINE estimate, not native keyframes."""
    try:import cv2
    except ImportError as exc:raise RuntimeError('opencv-python missing') from exc
    cap=cv2.VideoCapture(str(source))
    try:
        ok,prev=cap.read()
        if not ok:raise ValueError('Cannot decode first video frame')
        gray=cv2.cvtColor(prev,cv2.COLOR_BGR2GRAY);H,W=gray.shape
        x,y,w,h=map(int,(x,y,w,h))
        if min(w,h)<5 or x<0 or y<0 or x+w>W or y+h>H:raise ValueError('ROI is outside video frame')
        template=gray[y:y+h,x:x+w].copy()
        p=Path(output).resolve();p.parent.mkdir(parents=True,exist_ok=True)
        records=[(0,x,y,w,h,1.)];idx=0;last=(x,y)
        while len(records)<max_frames:
            ok,frame=cap.read()
            if not ok:break
            idx+=1
            if idx%step:continue
            gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
            # search near previous location avoids matching distant repeated patterns
            radius=max(w,h)*2
            sx=max(0,last[0]-radius);sy=max(0,last[1]-radius)
            ex=min(W,last[0]+w+radius);ey=min(H,last[1]+h+radius)
            roi=gray[sy:ey,sx:ex]
            if roi.shape[0]<h or roi.shape[1]<w:break
            score=cv2.matchTemplate(roi,template,cv2.TM_CCOEFF_NORMED)
            _,maxv,_,point=cv2.minMaxLoc(score)
            last=(sx+point[0],sy+point[1]);records.append((idx,last[0],last[1],w,h,round(float(maxv),4)))
        with p.open('w',newline='',encoding='utf8') as handle:
            writer=csv.writer(handle);writer.writerow(('frame','x','y','width','height','confidence'));writer.writerows(records)
        return {'output':str(p),'tracked_frames':len(records),'note':'Visual tracking estimates require review; CSV is not applied as keyframes.'}
    finally:cap.release()
