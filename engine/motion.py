"""30 original alpha-channel title motion presets. Arabic shaping via Pillow/libraqm.
Renders non-editable ProRes 4444 media to import into Premiere Pro.
"""
import math
import shutil
import subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageChops

MOTIONS=('fade-in','fade-out','slide-up','slide-down','slide-left','slide-right',
    'zoom-in','zoom-out','pop','bounce','elastic','rotate-in','rotate-out','spin',
    'blur-in','blur-out','reveal-left','reveal-right','reveal-up','reveal-down',
    'typewriter','word-rise','word-fade','letter-rise','letter-pop','drift-up',
    'drift-down','scale-fade','drop-in','float-in')

def font_path(text):
    arabic=any('\u0600'<=c<='\u06ff' for c in text)
    from os import name
    candidates=([
        'C:/Windows/Fonts/tahomabd.ttf','C:/Windows/Fonts/arialbd.ttf',
        '/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf',
        '/usr/share/fonts/truetype/noto/NotoKufiArabic-Bold.ttf',
        '/usr/share/fonts/opentype/fonts-hosny-amiri/Amiri-Bold.ttf'
    ] if arabic else [
        'C:/Windows/Fonts/arialbd.ttf','C:/Windows/Fonts/segoeuib.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    ])
    for path in candidates:
        if Path(path).is_file():return path
    import glob
    matches=glob.glob('C:/Windows/Fonts/*.ttf') if name=='nt' else glob.glob('/usr/share/fonts/**/*Sans*Bold*.ttf',recursive=True)
    if not matches:raise RuntimeError('No suitable font found; set --font explicitly')
    return matches[0]

def ease(t):return 1-(1-t)**3

def frame(text,motion,t,width,height,size,color=(255,255,255,255),fontfile=None,style='editorial'):
    if motion not in MOTIONS:raise ValueError('Unknown motion '+str(motion))
    t=max(0,min(1,float(t)));e=ease(t)
    fontfile=fontfile or font_path(text)
    # Lazy import avoids visual styling cycle at module load.
    from .visuals import title_plate
    plate=title_plate(text,width,height,size,style,fontfile)
    bounds=plate.getbbox()
    if not bounds:return plate
    layer=plate.crop(bounds)
    cx=(bounds[0]+bounds[2])/2;cy=(bounds[1]+bounds[3])/2
    dx=dy=0.;sc=1.;ang=0.;opacity=1.;blur=0
    if motion=='fade-in':opacity=e
    elif motion=='fade-out':opacity=1-e
    elif motion=='slide-up':dy=height*.25*(1-e);opacity=e
    elif motion=='slide-down':dy=-height*.25*(1-e);opacity=e
    elif motion=='slide-left':dx=width*.35*(1-e);opacity=e
    elif motion=='slide-right':dx=-width*.35*(1-e);opacity=e
    elif motion=='zoom-in':sc=.25+.75*e;opacity=e
    elif motion=='zoom-out':sc=1.6-.6*e;opacity=e
    elif motion=='pop':sc=1+(.28*math.sin(math.pi*min(t*1.5,1))*(1-t));opacity=e
    elif motion=='bounce':dy=-abs(math.sin(t*math.pi*2.7))*(1-t)*height*.20;opacity=e
    elif motion=='elastic':sc=1+math.sin(t*math.pi*5)*(.3*(1-t));opacity=e
    elif motion=='rotate-in':ang=(1-e)*-55;opacity=e
    elif motion=='rotate-out':ang=e*55;opacity=1-e
    elif motion=='spin':ang=(1-e)*-360;opacity=e
    elif motion=='blur-in':blur=(1-e)*min(30,size//2);opacity=e
    elif motion=='blur-out':blur=e*min(30,size//2);opacity=1-e
    elif motion=='drift-up':dy=(1-e)*height*.10;opacity=e
    elif motion=='drift-down':dy=-(1-e)*height*.10;opacity=e
    elif motion=='scale-fade':sc=.65+.35*e;opacity=e
    elif motion=='drop-in':dy=-(1-e)**2*height*.55;opacity=min(1,t*2)
    elif motion=='float-in':dy=height*.15*(1-e)+math.sin(t*math.pi*2)*(1-t)*height*.01;opacity=e
    if sc!=1:
        layer=layer.resize((max(1,round(layer.width*sc)),max(1,round(layer.height*sc))),Image.Resampling.LANCZOS)
    if ang:layer=layer.rotate(ang,resample=Image.Resampling.BICUBIC,expand=True)
    if blur:layer=layer.filter(ImageFilter.GaussianBlur(blur))
    if opacity<1:
        layer.putalpha(layer.getchannel('A').point(lambda a:round(a*opacity)))
    if motion in ('reveal-left','reveal-right','reveal-up','reveal-down','typewriter','word-fade','letter-rise','letter-pop','word-rise'):
        w,h=layer.size
        alpha=layer.getchannel('A')
        mask=Image.new('L',(w,h),0);md=ImageDraw.Draw(mask)
        rtl=any('\u0600'<=c<='\u06ff' for c in text)
        if motion in ('reveal-left','reveal-right','typewriter'):
            from_right=(motion=='reveal-right') or (motion=='typewriter' and rtl)
            if from_right:md.rectangle((round(w*(1-e)),0,w,h),fill=255)
            else:md.rectangle((0,0,round(w*e),h),fill=255)
        elif motion in ('reveal-up','reveal-down'):
            if motion=='reveal-up':md.rectangle((0,round(h*(1-e)),w,h),fill=255)
            else:md.rectangle((0,0,w,round(h*e)),fill=255)
        else:
            # Spatial staged reveal, preserves shaping and Arabic ligatures.
            # Original text raster remains intact; avoid splitting Arabic glyph joins.
            pieces=5 if motion.startswith('word') else 12
            for j in range(pieces):
                stagger=j/pieces * .65
                local=max(0,min(1,(t-stagger)/.35))
                if motion=='letter-pop':local=ease(local)
                idx=pieces-1-j if rtl else j
                x1=round(w*idx/pieces);x2=round(w*(idx+1)/pieces)
                if motion in ('word-rise','letter-rise'):
                    # reveal piece by its vertical progress; stylistic per-region stagger
                    md.rectangle((x1,round(h*(1-local)),x2,h),fill=255)
                else:md.rectangle((x1,0,x2,h),fill=round(255*local))
        layer.putalpha(ImageChops.multiply(alpha,mask))
    im=Image.new('RGBA',(width,height),(0,0,0,0))
    x=round(cx-layer.width/2+dx);y=round(cy-layer.height/2+dy)
    im.alpha_composite(layer,(x,y))
    return im

def render(text,output,motion='slide-up',width=1080,height=1920,fps=25,duration=1.2,size=96,font=None,style='editorial'):
    if motion not in MOTIONS:raise ValueError('Unknown title motion')
    if not shutil.which('ffmpeg'):raise RuntimeError('FFmpeg is required')
    if not text or len(text)>350:raise ValueError('Title text length must be 1..350')
    if not(100<=width<=3840 and 100<=height<=3840):raise ValueError('Frame dimensions out of range')
    if not(5<=fps<=60 and .2<=duration<=30):raise ValueError('FPS or duration out of range')
    font=font or font_path(text)
    path=Path(output).resolve();path.parent.mkdir(parents=True,exist_ok=True)
    args=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgba',
        '-video_size',f'{width}x{height}','-framerate',str(fps),'-i','-',
        '-c:v','prores_ks','-profile:v','4','-pix_fmt','yuva444p10le',path]
    count=max(2,round(fps*duration))
    with subprocess.Popen([str(x) for x in args],stdin=subprocess.PIPE,stderr=subprocess.PIPE) as proc:
        try:
            for i in range(count):
                f=frame(text,motion,i/(count-1),width,height,size,fontfile=font,style=style)
                proc.stdin.write(f.tobytes())
        except BrokenPipeError:pass
        finally:
            proc.stdin.close();err=proc.stderr.read().decode(errors='replace');proc.wait()
            if proc.returncode:raise RuntimeError(err[-1500:])
    return {'output':str(path),'motion':motion,'style':style,'frames':count,'alpha':'prores_4444'}
