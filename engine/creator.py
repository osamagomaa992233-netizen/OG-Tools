"""Creator-focused, original motion captions and clip automation.

Word timings come from faster-whisper (optional), not a paid API. Arabic stays
in natural Unicode order; libass handles bidi/shaping when available. ASS is
renderable but not a Premiere-native text graphic. SRT remains editable text.
"""
from __future__ import annotations
import json, math, os, re, tempfile
from pathlib import Path
from . import media, trend_text

STYLES = ('kinetic-pop','clean-focus','editorial-accent','word-flash',
          'micro-bounce','mono-underline','hook-punch','quiet-lower') + tuple(trend_text.PRESETS)
PALETTES = {
  'ivory': ('F3F1EA','CBEE7B','1D1B20'),
  'plum': ('F9F6EF','D3B6E4','30203E'),
  'acid': ('FFFFFF','ACF34D','242424'),
  'amber': ('FFFFFF','F9C85C','242424'),
}
# All ASS numbers, positions and words are escaped by our serializer.

def ass_escape(s):
    return str(s).replace('\\','\\\\').replace('{','\\{').replace('}','\\}').replace('\n',' ')

def asstime(s):
    cs=max(0,int(round(float(s)*100)))
    return f'{cs//360000}:{(cs//6000)%60:02d}:{(cs//100)%60:02d}.{cs%100:02d}'

def srttime(s):
    ms=max(0,round(float(s)*1000))
    return f'{ms//3600000:02d}:{(ms//60000)%60:02d}:{(ms//1000)%60:02d},{ms%1000:03d}'

def validate_words(words):
    clean=[];last=0
    for item in words:
        text=str(item.get('text','')).strip()
        if not text:continue
        start=float(item['start']);end=float(item['end'])
        if not all(map(math.isfinite,[start,end])) or start<0 or end<=start:
            raise ValueError('Invalid word time')
        if start+0.015<last:raise ValueError('Word timestamps must be ordered')
        clean.append({'start':round(start,3),'end':round(end,3),'text':text})
        last=start
    if not clean:raise ValueError('No valid words')
    return clean

def group_words(words,max_words=3,max_gap=.37,max_chars=32):
    words=validate_words(words)
    result=[];chunk=[]
    def flush():
        nonlocal chunk
        if chunk:result.append(chunk);chunk=[]
    for word in words:
        if chunk and (len(chunk)>=max_words or word['start']-chunk[-1]['end']>max_gap or
           len(' '.join(w['text'] for w in chunk+[word]))>max_chars or
           bool(re.search(r'[.!؟!?]$',chunk[-1]['text']))):flush()
        chunk.append(word)
    flush()
    return result

def srt_from_groups(groups,offset=0):
    lines=[]
    for i,group in enumerate(groups,1):
        a=group[0]['start']+offset;b=group[-1]['end']+offset
        lines.append(f"{i}\n{srttime(a)} --> {srttime(b)}\n{' '.join(w['text'] for w in group)}\n")
    return '\n'.join(lines)+'\n'

def ass_color(rgb):
    rgb=rgb.strip('#');return '&H'+rgb[4:6]+rgb[2:4]+rgb[0:2]+'&'

def ass_from_groups(groups,style='kinetic-pop',palette='ivory',width=1080,height=1920,
                    font=None,position=.68):
    if style not in STYLES:raise ValueError('Unknown creator caption style')
    if palette not in PALETTES:raise ValueError('Unknown creator color palette')
    if style in trend_text.PRESETS:
        primary, accent, bg = PALETTES[palette]
        return trend_text.generate(groups, style, white=primary, accent=accent,
            background=bg, width=width, height=height, font=font, position=position)
    if not (320<=width<=4320 and 180<=height<=7680):raise ValueError('Invalid frame size')
    if not (.25<=position<=.9):raise ValueError('Position must be 0.25..0.9')
    color,accent,bg=PALETTES[palette]
    f=font or ('Noto Sans Arabic' if any('\u0600'<=ch<='\u08ff' for g in groups for w in g for ch in w['text']) else 'Montserrat')
    size=int(width*.125);small=int(width*.092)
    line_y=int(height*position)
    header=('''[Script Info]\nScriptType: v4.00+\nWrapStyle: 2\nScaledBorderAndShadow: yes\n'''+
            f'PlayResX: {width}\nPlayResY: {height}\nYCbCr Matrix: TV.709\n\n'+
            '[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n'+
            f'Style: Base,{f},{size},{ass_color(color)},{ass_color(accent)},{ass_color(bg)},&H7F000000&,-1,0,0,0,100,100,0,0,1,2,0,5,55,55,45,1\n'+
            f'Style: Subtle,{f},{small},{ass_color(color)},{ass_color(accent)},{ass_color(bg)},&H7F000000&,0,0,0,0,100,100,0,0,1,1,0,5,55,55,45,1\n\n'+
            '[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n')
    out=[header]
    ac=ass_color(accent);white=ass_color(color)
    for group in groups:
        phrase=' '.join(w['text'] for w in group)
        words=[ass_escape(w['text']) for w in group]
        for idx,w in enumerate(group):
            start=w['start'];end=w['end']
            # For phrase styles, do not let a gap produce a blank gap/overlap.
            if idx<len(group)-1:end=max(end,group[idx+1]['start'])
            duration=max(.06,end-start)
            if style in ('kinetic-pop','word-flash','micro-bounce','hook-punch'):
                txt=words[idx]
                if style=='kinetic-pop':
                    tags=f'\\an5\\pos({width//2},{line_y})\\c{ac}\\fscx68\\fscy68\\t(0,90,\\fscx115\\fscy115)\\t(90,180,\\fscx100\\fscy100)'
                elif style=='word-flash':
                    tags=f'\\an5\\pos({width//2},{line_y})\\c{ac}\\bord1\\fscx104\\fscy104\\fad(35,45)'
                elif style=='micro-bounce':
                    tags=f'\\an5\\move({width//2},{line_y+18},{width//2},{line_y},0,140)\\c{ac}\\fscx92\\fscy92\\t(0,170,\\fscx100\\fscy100)'
                else:
                    tags=f'\\an5\\pos({width//2},{line_y})\\c{ac}\\fscx72\\fscy72\\t(0,110,\\fscx135\\fscy135)\\t(110,220,\\fscx108\\fscy108)'
            else:
                arr=list(words)
                arr[idx]='{\\c'+ac+'\\b1}'+arr[idx]+'{\\rSubtle}'
                txt=' '.join(arr)
                if style=='clean-focus':tags=f'\\an5\\pos({width//2},{line_y})\\fscx100\\fscy100'
                elif style=='editorial-accent':tags=f'\\an5\\pos({width//2},{line_y})\\fad(35,80)\\fsp1'
                elif style=='mono-underline':tags=f'\\an5\\pos({width//2},{line_y})\\u1'
                else:tags=f'\\an5\\pos({width//2},{int(height*.78)})\\fad(50,80)\\bord0'
            text='{'+tags+'}'+txt
            mode='Subtle' if style in ('clean-focus','mono-underline','quiet-lower') else 'Base'
            out.append(f'Dialogue: 0,{asstime(start)},{asstime(end)},{mode},,0,0,0,,{text}\n')
    return ''.join(out)

def extract_clip_audio(source,output,start=0,end=None):
    if not Path(source).is_file():raise FileNotFoundError(source)
    info=media.probe(source)
    if not info['audio']:raise ValueError('Selected clip does not contain audio')
    start=float(start or 0);end=float(end) if end not in (None,'') else info['duration']
    if not 0<=start<end<=info['duration']+.12:raise ValueError('Clip trim outside original source')
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(start),'-i',str(source),'-t',str(end-start),'-vn','-ac','1','-ar','16000','-c:a','pcm_s16le',str(output)]
    media.run(cmd)
    return str(output)

def transcribe_words(source,language='ar',model='small',start=0,end=None):
    try:from faster_whisper import WhisperModel
    except ImportError as e:raise RuntimeError('Install optional faster-whisper first (model download required once).') from e
    if language not in ('ar','en','auto'):raise ValueError('Language must be ar/en/auto')
    if model not in ('tiny','base','small','medium','large-v3','turbo'):raise ValueError('Unsupported model')
    with tempfile.TemporaryDirectory(prefix='og-caption-') as tmp:
        input_wav=extract_clip_audio(source,Path(tmp)/'selection.wav',start,end)
        machine=WhisperModel(model,device='cpu',compute_type='int8')
        segments,_=machine.transcribe(input_wav,language=None if language=='auto' else language,word_timestamps=True,vad_filter=True,beam_size=5)
        words=[]
        for seg in segments:
            if getattr(seg,'words',None):
                for word in seg.words:
                    if word.start is not None and word.end is not None and word.word.strip():
                        words.append({'start':float(word.start),'end':float(word.end),'text':word.word.strip()})
            elif seg.text.strip():
                words.append({'start':float(seg.start),'end':float(seg.end),'text':seg.text.strip()})
        return validate_words(words)

def create_caption_package(source,output,language='ar',model='small',style='kinetic-pop',
                           palette='ivory',start=0,end=None,timeline_offset=0,
                           words=None,burn=False,width=1080,height=1920,max_words=3,font=None):
    """Creates ASS + SRT + word JSON; optional MP4 captioned cut.
    JSON input words is explicitly supported for retiming/preview without re-transcription.
    Media retains original untouched. Timeline offset applies only to sequence-aligned SRT/JSON.
    """
    path=Path(output).expanduser().resolve()
    if path.suffix.lower() not in ('.srt','.ass','.json','.mp4'):
        raise ValueError('Choose .srt/.ass/.json/.mp4 output')
    path.parent.mkdir(parents=True,exist_ok=True)
    root=path.with_suffix('')
    if words is None:
        words=transcribe_words(source,language,model,start,end)
    words=validate_words(words)
    groups=group_words(words,max_words=max(1,min(int(max_words),5)))
    srt=root.with_suffix('.srt');ass=root.with_suffix('.ass');js=root.with_suffix('.words.json')
    if any(Path(source).resolve()==p for p in (srt,ass,js) if source):raise ValueError('Cannot overwrite source')
    srt.write_text(srt_from_groups(groups,float(timeline_offset)),encoding='utf-8-sig')
    ass.write_text(ass_from_groups(groups,style,palette,width,height,font=font),encoding='utf-8-sig')
    js.write_text(json.dumps({'language':language,'source':str(source),'source_in':float(start or 0),
         'source_out':end,'timeline_offset':float(timeline_offset),'style':style,'palette':palette,
         'words':[{**w,'sequence_start':round(w['start']+float(timeline_offset),3),
                          'sequence_end':round(w['end']+float(timeline_offset),3)} for w in words]},
         ensure_ascii=False,indent=2),encoding='utf-8')
    result={'output':str(srt),'ass':str(ass),'words_json':str(js),'word_count':len(words),
            'caption_count':len(groups),'style':style,'language':language,'timeline_offset':float(timeline_offset)}
    if burn:
        if not source:raise ValueError('Provide source for burn-in')
        target=root.with_suffix('.captioned.mp4')
        if Path(source).resolve()==target:raise ValueError('Cannot overwrite source')
        # ASS script paths with quotes/backslashes/colon require FFmpeg filter escaping.
        safe=str(ass).replace('\\','\\\\').replace(':','\\:').replace("'","\\'").replace('[','\\[').replace(']','\\]')
        cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(float(start or 0)),'-i',str(source)]
        if end not in (None,''):cmd+=['-t',str(float(end)-float(start or 0))]
        cmd+=['-vf',f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,ass=filename='{safe}'",
              '-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k',str(target)]
        media.run(cmd);result['preview_mp4']=str(target)
    return result

# Keyframed zooms in the Premiere panel use UXP native component parameters.
# This fallback exports an MP4 from a physical file, not native Premiere keys.
def zoom_render(source,output,preset='punch-in',strength=.16,duration=.35,width=None,height=None,start=0,end=None):
    if preset not in ('punch-in','punch-out','snap-zoom','slow-push','reaction-hit','breath'):
        raise ValueError('Unknown zoom type')
    info=media.probe(source)
    if not info['video']:raise ValueError('Video required')
    strength=float(strength);duration=float(duration)
    if not (.015<=strength<=.6 and .10<=duration<=20):raise ValueError('Invalid zoom settings')
    start=float(start or 0);end=float(end) if end not in (None,'') else info['duration']
    if not 0<=start<end<=info['duration']+.12:raise ValueError('Zoom trim outside source file')
    w=width or info.get('width') or 1080;h=height or info.get('height') or 1920
    if w%2:w+=1
    if h%2:h+=1
    d=min(end-start,duration);peak=1+strength
    # zoompan reuses the same source frames with frame-by-frame smooth interpolation.
    # Expressions evaluated in output frames; zoom is limited to initial effect duration.
    if preset=='punch-in':expr=f'1+{strength}*min(1,on/{max(1,int(d*25*.28))})'
    elif preset=='punch-out':expr=f'1+{strength}*max(0,1-on/{max(1,int(d*25*.36))})'
    elif preset=='snap-zoom':expr=f'1+{strength}*max(0,1-abs(on-{int(d*25*.35)})/{max(1,int(d*25*.3))})'
    elif preset=='slow-push':expr=f'1+{strength}*min(1,on/{max(1,int(d*25))})'
    elif preset=='reaction-hit':expr=f'1+{strength}*(0.8+0.2*min(1,on/{max(1,int(d*25*.15))}))'
    else:expr=f'1+{strength}*(0.5-0.5*cos(2*PI*on/{max(1,int(d*25))}))'
    target=media.safe_output(source,output)
    # Use zoompan d=1 so input frames are not duplicated; actual output length roughly source.
    vf=f'fps=25,scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},zoompan=z=\'{expr}\':x=\'iw/2-(iw/zoom/2)\':y=\'ih/2-(ih/zoom/2)\':d=1:s={w}x{h}:fps=25,format=yuv420p'
    media.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(start),'-i',str(source),'-t',str(end-start),'-vf',vf,'-c:v','libx264','-crf','21','-preset','veryfast','-c:a','aac','-b:a','160k',str(target)])
    return {'output':str(target),'preset':preset,'native_keyframes':False}

RAMP_PRESETS={
 'whip':(.85,3.0,.9),
 'impact':(.65,2.5,.65),
 'smooth':(.55,1.4,1.0),
 'hyper':(1.0,3.8,.8),
 'reverse-feel':(1.8,.45,1.4),
}
def ramp_curve(preset='whip',steps=9):
    """Smooth, sampleable speed envelope; rendered as small constant-speed chunks.
    This is NOT editable Premiere Time Remapping. Each segment has matching atempo.
    """
    if preset not in RAMP_PRESETS:raise ValueError('Unknown speed ramp')
    if not 3<=int(steps)<=48:raise ValueError('Steps must be 3..48')
    a,b,c=RAMP_PRESETS[preset]
    def smoother(t):return 6*t**5-15*t**4+10*t**3
    out=[]
    for idx in range(int(steps)):
        u=(idx+.5)/int(steps)
        speed=a+(b-a)*smoother(u/.5) if u<.5 else b+(c-b)*smoother((u-.5)/.5)
        out.append(round(speed,5))
    return out

def creator_speed_ramp(source,output,preset='whip',steps=9,start=0,end=None):
    info=media.probe(source)
    if not info['video']:raise ValueError('Video required for speed ramp')
    speeds=ramp_curve(preset,steps)
    start=float(start or 0);end=float(end) if end not in (None,'') else info['duration']
    if not 0<=start<end<=info['duration']+.12:raise ValueError('Ramp trim outside source file')
    d=end-start;ivals=[[start+d*i/len(speeds),start+d*(i+1)/len(speeds)] for i in range(len(speeds))]
    result=media.render_intervals(source,output,ivals,speeds)
    profile=str(Path(output).with_suffix('.speed.json'))
    Path(profile).write_text(json.dumps({'preset':preset,'source_duration':info['duration'],'selected_duration':d,'selected_in':start,'selected_out':end,'intervals':ivals,'speed_multipliers':speeds},indent=2),encoding='utf8')
    return {**result,'preset':preset,'profile':profile,'native_speed_keyframes':False,'approximate':True}

def selected_silence(source,output,noise=-35,minimum=.45,padding=.1,
                     start=0,end=None,timeline_offset=0,analyze_only=False):
    """Silence cut for a *trimmed selected source clip* (not the whole sequence).

    All analysis timestamps are relative to the selected clip; render intervals
    refer to absolute original source time. Sequence markers are reported as
    timeline_offset + relative timestamp, but we never ripple-delete linked tracks.
    """
    info=media.probe(source)
    if not info['audio']:raise ValueError('Source has no audio')
    start=float(start or 0)
    end=float(end) if end not in ('',None) else info['duration']
    if not 0<=start<end<=info['duration']+.12:raise ValueError('Invalid selected clip bounds')
    if not -90<=float(noise)<=0:raise ValueError('Invalid silence threshold')
    if not .05<=float(minimum)<=30:raise ValueError('Invalid minimum silence')
    if not 0<=float(padding)<=3:raise ValueError('Invalid padding')
    # Analyze exactly the clip time range and never split outside this selection.
    result=media.run(['ffmpeg','-hide_banner','-nostats','-ss',str(start),'-i',str(source),
                '-t',str(end-start),'-map','0:a:0','-af',f'silencedetect=noise={float(noise)}dB:d={float(minimum)}',
                '-f','null','-'])
    silences=media.parse_silence(result.stderr,end-start)
    keep=media.complement_intervals(silences,end-start,float(padding))
    if not keep:raise ValueError('Selected portion entirely silent; no file created')
    output=Path(output).expanduser().resolve();output.parent.mkdir(parents=True,exist_ok=True)
    absolute=[[round(start+a,4),round(start+b,4)] for a,b in keep]
    seqkeep=[[round(timeline_offset+a,4),round(timeline_offset+b,4)] for a,b in keep]
    data={'source':str(Path(source).resolve()),'clip_source_in':start,'clip_source_out':end,
          'timeline_start':timeline_offset,'silence':silences,'keep_relative':keep,
          'keep_source':absolute,'keep_sequence_before_ripple':seqkeep,
          'removed_seconds':round((end-start)-sum(b-a for a,b in keep),4),
          'ripple_applied':False,'selected_clip_only':True}
    if analyze_only:
        path=output if output.suffix.lower()=='.json' else output.with_suffix('.json')
        path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
        return {**data,'output':str(path)}
    rendered=media.render_intervals(source,output,absolute)
    return {**data,'render':rendered,'output':rendered['output']}
