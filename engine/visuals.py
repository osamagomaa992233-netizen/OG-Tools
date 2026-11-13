"""Original local design generators: safe zones, icons, title style plates, carousels and drawing overlays."""
import json
import math
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from .media import run,need,safe_output

FORMATS={'reels':(1080,1920,235,320),'story':(1080,1920,250,340),'portrait':(1080,1440,100,120),'square':(1080,1080,80,100),'youtube':(1920,1080,80,80)}
COLORS={'cream':'#F2F0EB','lime':'#CEED69','plum':'#4B2A5A','white':'#FFFFFF','charcoal':'#242129'}
STYLES={
 'editorial':{'fg':'#FFFFFF','bg':None,'accent':'#FFFFFF','stroke':0,'layout':'center'},
 'ivory':{'fg':'#242129','bg':'#F2F0EB','accent':'#4B2A5A','stroke':0,'layout':'center'},
 'plum':{'fg':'#FFFFFF','bg':'#4B2A5A','accent':'#C7B48A','stroke':0,'layout':'center'},
 'outline':{'fg':'#FFFFFF','bg':None,'accent':'#FFFFFF','stroke':3,'layout':'center'},
 'impact':{'fg':'#CEED69','bg':'#242129','accent':'#CEED69','stroke':0,'layout':'center'},
 'lower-third':{'fg':'#FFFFFF','bg':'#242129','accent':'#CEED69','stroke':0,'layout':'lower'},
 'minimal':{'fg':'#FFFFFF','bg':None,'accent':'#FFFFFF','stroke':0,'layout':'lower'},
 'mono':{'fg':'#F2F0EB','bg':'#181818','accent':'#F2F0EB','stroke':0,'layout':'center'},
 'sand':{'fg':'#242129','bg':'#C7B48A','accent':'#242129','stroke':0,'layout':'center'},
 'redline':{'fg':'#FFFFFF','bg':'#242129','accent':'#F15153','stroke':0,'layout':'center'},
 'studio':{'fg':'#242129','bg':'#FFFFFF','accent':'#CEED69','stroke':0,'layout':'center'},
 'caption':{'fg':'#FFFFFF','bg':'#242129','accent':'#CEED69','stroke':0,'layout':'lower'},
}

def get_font(text,size=60,font=None):
    if font:
        if not Path(font).is_file():raise FileNotFoundError(f'Font not found: {font}')
        return ImageFont.truetype(str(font),int(size))
    from .motion import font_path
    return ImageFont.truetype(font_path(text),int(size))

def guide_overlay(output,mode='reels',width=None,height=None):
    if mode not in FORMATS:raise ValueError('Unknown social format')
    fw,fh,t,b=FORMATS[mode];width=width or fw;height=height or fh
    scale=height/fh;t=round(t*scale);b=round(b*scale)
    canvas=Image.new('RGBA',(width,height),(0,0,0,0))
    d=ImageDraw.Draw(canvas)
    d.rectangle((0,0,width,t),fill=(232,82,82,70))
    d.rectangle((0,height-b,width,height),fill=(232,82,82,70))
    d.line((0,t,width,t),fill=(240,90,90,210),width=max(2,width//400))
    d.line((0,height-b,width,height-b),fill=(240,90,90,210),width=max(2,width//400))
    d.rectangle((int(.05*width),t+int(.04*height),int(.95*width),height-b-int(.04*height)),outline=(255,255,255,125),width=2)
    out=Path(output);out.parent.mkdir(parents=True,exist_ok=True);canvas.save(out)
    return {'output':str(out.resolve()),'safe_top':t,'safe_bottom':b,'width':width,'height':height}

def title_plate(text,width=1080,height=1920,size=90,style='editorial',font=None):
    if style not in STYLES:raise ValueError('Unknown title style')
    spec=STYLES[style]
    canvas=Image.new('RGBA',(width,height),(0,0,0,0))
    d=ImageDraw.Draw(canvas);f=get_font(text,size,font)
    while d.textbbox((0,0),text,font=f,stroke_width=spec['stroke'])[2]>width*.89 and size>22:
        size=int(size*.9);f=get_font(text,size,font)
    box=d.textbbox((0,0),text,font=f,stroke_width=spec['stroke'])
    tw,th=box[2]-box[0],box[3]-box[1]
    x=(width-tw)/2-box[0]
    y=(height-th)/2-box[1] if spec['layout']=='center' else height*.76-th/2-box[1]
    if spec['bg']:
        pad=max(12,size//3)
        boxcoords=(x+box[0]-pad,y+box[1]-pad,x+box[2]+pad,y+box[3]+pad)
        d.rounded_rectangle(boxcoords,radius=min(20,size//8),fill=spec['bg'])
    if style in ('lower-third','caption','redline'):
        d.rounded_rectangle((x+box[0],y+box[3]+10,x+box[0]+tw*.35,y+box[3]+max(15,size//9)),radius=2,fill=spec['accent'])
    if style=='outline':
        d.text((x,y),text,font=f,fill=(0,0,0,0),stroke_width=spec['stroke'],stroke_fill=spec['fg'])
    else:d.text((x,y),text,font=f,fill=spec['fg'],stroke_width=spec['stroke'],stroke_fill=spec['fg'])
    return canvas

def title_png(text,output,**kwargs):
    img=title_plate(text,**kwargs);p=Path(output);p.parent.mkdir(parents=True,exist_ok=True);img.save(p)
    return {'output':str(p.resolve()),'style':kwargs.get('style','editorial')}

def carousel(images,output,width=540,height=960,slide_duration=2.,fps=25):
    """Slideshow; each input gets a subtle directional pan/zoom; non-destructive output MP4."""
    need('ffmpeg')
    if not 2<=len(images)<=20:raise ValueError('Carousel needs 2..20 images')
    if not .5<=slide_duration<=10:raise ValueError('Slide duration outside .5..10s')
    for image in images:
        if not Path(image).is_file():raise FileNotFoundError(image)
    from tempfile import TemporaryDirectory
    import subprocess
    target=Path(output).resolve();target.parent.mkdir(parents=True,exist_ok=True)
    with TemporaryDirectory(prefix='og-slides-') as directory:
        pngs=[]
        for idx,path in enumerate(images):
            with Image.open(path) as raw:
                im=raw.convert('RGB'); w,h=im.size
                scale=max(width/w,height/h); newsize=(round(w*scale),round(h*scale))
                im=im.resize(newsize,Image.Resampling.LANCZOS)
                left=(im.width-width)//2;top=(im.height-height)//2
                im=im.crop((left,top,left+width,top+height))
                p=Path(directory)/f'{idx:03}.png';im.save(p);pngs.append(p)
        # Each slide is created separately: deterministic cross-platform FFmpeg workflow.
        segs=[]
        for idx,p in enumerate(pngs):
            dest=Path(directory)/f'seg{idx:03}.mp4'
            frames=max(1,round(float(slide_duration)*fps))
            zoom="'min(zoom+0.0008,1.08)'" if idx%2 else "'min(zoom+0.0006,1.07)'"
            run(['ffmpeg','-hide_banner','-loglevel','error','-y','-loop','1','-framerate',str(fps),'-i',p,
                 '-vf',f'zoompan=z={zoom}:d=1:x=iw/2-(iw/zoom/2):y=ih/2-(ih/zoom/2):s={width}x{height}:fps={fps},format=yuv420p',
                 '-frames:v',str(frames),'-c:v','libx264','-preset','ultrafast','-crf','20',dest])
            segs.append(dest)
        concat=Path(directory)/'concat.txt'
        concat.write_text(''.join("file '"+str(p).replace("'", "'\\''")+"'\n" for p in segs),encoding='utf8')
        run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',concat,'-c','copy',target])
    return {'output':str(target),'slides':len(images)}

def draw_overlay(output,width=1080,height=1920,fps=25,duration=1.2,shape='arrow',color='#FFFFFF'):
    """Export draw-on transparent ProRes overlay for import to Premiere."""
    if shape not in ('arrow','underline','circle','rectangle','diagonal'):raise ValueError('Unknown draw shape')
    need('ffmpeg');p=Path(output).resolve();p.parent.mkdir(parents=True,exist_ok=True)
    n=max(2,round(fps*duration))
    args=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgba',
       '-video_size',f'{width}x{height}','-framerate',str(fps),'-i','-','-c:v','prores_ks','-profile:v','4','-pix_fmt','yuva444p10le',p]
    from PIL import ImageColor
    rgb=ImageColor.getrgb(color);points=[]
    if shape=='underline':points=[(width*.18+i*width*.64/80,height*.72) for i in range(81)]
    elif shape=='diagonal':points=[(width*.2+i*width*.6/80,height*.8-i*height*.5/80) for i in range(81)]
    elif shape=='rectangle':
        # perimeter param
        corners=[(.22,.32),(.78,.32),(.78,.67),(.22,.67),(.22,.32)]
        for i in range(4):
            a,b=corners[i],corners[i+1]
            points.extend([(width*(a[0]+(b[0]-a[0])*j/20),height*(a[1]+(b[1]-a[1])*j/20)) for j in range(20)])
    elif shape=='circle':points=[(width*(.5+.27*math.cos(i*2*math.pi/90)),height*(.5+.18*math.sin(i*2*math.pi/90))) for i in range(91)]
    else:
        points=[(width*(.2+i*.6/80),height*(.7-i*.37/80)) for i in range(81)]
    with subprocess.Popen([str(x) for x in args],stdin=subprocess.PIPE,stderr=subprocess.PIPE) as proc:
        try:
            for i in range(n):
                im=Image.new('RGBA',(width,height),(0,0,0,0));d=ImageDraw.Draw(im)
                count=max(2,round(len(points)*min(1,i/(n-1))))
                d.line(points[:count],fill=rgb+(255,),width=max(3,width//150),joint='curve')
                if shape=='arrow' and count>=len(points)-3:
                    end=points[-1];d.line([end,(end[0]-width*.085,end[1]+height*.005)],fill=rgb+(255,),width=max(3,width//150))
                    d.line([end,(end[0]-width*.02,end[1]+height*.075)],fill=rgb+(255,),width=max(3,width//150))
                proc.stdin.write(im.tobytes())
        except BrokenPipeError:pass
        finally:
            proc.stdin.close();err=proc.stderr.read().decode(errors='replace');proc.wait()
            if proc.returncode:raise RuntimeError(err[-1200:])
    return {'output':str(p),'shape':shape,'frames':n}

ICONS={
 'play':'M 8 5 L 19 12 L 8 19 Z',
 'pause':'M 7 5 L 10 5 L 10 19 L 7 19 Z M 14 5 L 17 5 L 17 19 L 14 19 Z',
 'check':'M 5 12 L 10 17 L 19 7',
 'close':'M 5 5 L 19 19 M 19 5 L 5 19',
 'arrow-right':'M 4 12 L 20 12 M 13 5 L 20 12 L 13 19',
 'arrow-left':'M 20 12 L 4 12 M 11 5 L 4 12 L 11 19',
 'plus':'M 12 4 L 12 20 M 4 12 L 20 12',
 'minus':'M 4 12 L 20 12',
 'menu':'M 4 6 L 20 6 M 4 12 L 20 12 M 4 18 L 20 18',
 'search':'M 15 15 L 21 21 M 18 10 A 8 8 0 1 0 2 10 A 8 8 0 1 0 18 10',
 'user':'M 16 8 A 4 4 0 1 0 8 8 A 4 4 0 1 0 16 8 M 4 21 Q 4 14 12 14 Q 20 14 20 21',
 'home':'M 3 11 L 12 3 L 21 11 L 21 21 L 3 21 Z',
 'heart':'M 12 21 L 3 12 C -1 6 6 1 12 7 C 18 1 25 6 21 12 Z',
 'location':'M 12 22 Q 2 12 4 8 A 8 8 0 1 1 20 8 Q 22 12 12 22 M 12 9 A 2 2 0 1 0 12 13 A 2 2 0 1 0 12 9',
 'clock':'M 12 3 A 9 9 0 1 0 12 21 A 9 9 0 1 0 12 3 M 12 6 L 12 12 L 16 15',
 'mail':'M 3 6 L 21 6 L 21 18 L 3 18 Z M 3 6 L 12 13 L 21 6',
 'camera':'M 3 7 L 7 7 L 9 4 L 15 4 L 17 7 L 21 7 L 21 20 L 3 20 Z M 12 10 A 4 4 0 1 0 12 18 A 4 4 0 1 0 12 10',
 'volume':'M 3 9 L 7 9 L 12 5 L 12 19 L 7 15 L 3 15 Z M 16 8 Q 21 12 16 16',
 'download':'M 12 3 L 12 16 M 6 10 L 12 16 L 18 10 M 4 18 L 4 21 L 20 21 L 20 18',
 'calendar':'M 4 6 L 20 6 L 20 21 L 4 21 Z M 8 3 L 8 9 M 16 3 L 16 9 M 4 12 L 20 12',
 'star':'M 12 2 L 15 9 L 22 9 L 16.5 14 L 19 22 L 12 17.5 L 5 22 L 7.5 14 L 2 9 L 9 9 Z',
 'bolt':'M 14 2 L 5 13 L 11 13 L 10 22 L 20 9 L 14 9 Z'
}
def icon_export(name,output,color='#FFFFFF',size=256):
    if name not in ICONS:raise ValueError('Unknown icon name')
    from xml.sax.saxutils import escape
    from PIL import ImageColor
    ImageColor.getrgb(color)
    path=ICONS[name];p=Path(output);p.parent.mkdir(parents=True,exist_ok=True)
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{int(size)}" height="{int(size)}"><path d="{path}" fill="none" stroke="{escape(color)}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    p.write_text(svg,encoding='utf8')
    return {'output':str(p.resolve()),'name':name}

def extruded_text(text,output,width=1080,height=1920,size=104,font=None,depth=28):
    """Stylized 2.5D/extruded raster title. NOT a Premiere 3D text layer."""
    if not text or len(text)>160:raise ValueError('Text length must be 1..160')
    f=get_font(text,size,font)
    image=Image.new('RGBA',(width,height),(0,0,0,0));draw=ImageDraw.Draw(image)
    bbox=draw.textbbox((0,0),text,font=f)
    tw,th=bbox[2]-bbox[0],bbox[3]-bbox[1]
    x=(width-tw)/2-bbox[0]-depth/2;y=(height-th)/2-bbox[1]-depth/2
    for d in range(int(depth),0,-1):
        a=d/int(depth)
        col=(58+int(50*a),37+int(25*a),80+int(30*a),255)
        draw.text((x+d,y+d*.65),text,font=f,fill=col)
    draw.text((x,y),text,font=f,fill=(242,240,235,255),stroke_width=max(1,size//90),stroke_fill=(255,255,255,255))
    p=Path(output).resolve();p.parent.mkdir(parents=True,exist_ok=True);image.save(p)
    return {'output':str(p),'mode':'2.5d raster extrusion; not editable native 3D'}

def arc_text(text,output,width=1080,height=1920,size=65,font=None,curvature=.48):
    """Raster arc text. Arabic is shaped by WORD to preserve intra-word joins.
    Not a fully editable path in Premiere; complex connected Arabic across words differs.
    """
    if not text or len(text)>120:raise ValueError('Text length must be 1..120')
    if not .15<=curvature<=1:raise ValueError('curvature must be 0.15..1')
    import re
    is_ar=any('\u0600'<=c<='\u06ff' for c in text)
    units=text.split(' ') if is_ar else list(text)
    if is_ar:units=list(reversed(units))
    f=get_font(text,size,font)
    measure=ImageDraw.Draw(Image.new('RGBA',(4,4)))
    widths=[max(1,measure.textlength(s+' ' if is_ar else s,font=f)) for s in units]
    total=sum(widths);scale=min(1,(width*.85)/total)
    radius=max(1,width/(2*curvature));center=(width/2,height*.49)
    location=-total*scale/2
    canvas=Image.new('RGBA',(width,height),(0,0,0,0))
    for unit,unit_width in zip(units,widths):
        wscaled=unit_width*scale;angle=(location+wscaled/2)/radius
        angle=max(-math.pi*.45,min(math.pi*.45,angle))
        box=measure.textbbox((0,0),unit,font=f);uw=box[2]-box[0];uh=box[3]-box[1]
        layer=Image.new('RGBA',(max(1,uw+26),max(1,uh+36)),(0,0,0,0))
        ImageDraw.Draw(layer).text((13-box[0],16-box[1]),unit,font=f,fill='#FFFFFF')
        if scale<1:layer=layer.resize((max(1,round(layer.width*scale)),max(1,round(layer.height*scale))),Image.Resampling.LANCZOS)
        layer=layer.rotate(-angle*180/math.pi,expand=True,resample=Image.Resampling.BICUBIC)
        px=center[0]+radius*math.sin(angle)
        py=center[1]+radius*(1-math.cos(angle))
        canvas.alpha_composite(layer,(round(px-layer.width/2),round(py-layer.height/2)))
        location+=wscaled
    p=Path(output).resolve();p.parent.mkdir(parents=True,exist_ok=True);canvas.save(p)
    return {'output':str(p),'mode':'raster curved text; Arabic placed by shaped words'}
