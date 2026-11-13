"""Single entry point for UXP panel, CLI and integration tests."""
from pathlib import Path
from . import media,extras,visuals,motion,creator

TOOLS=[
 {'id':'captions','name':'AI Captions (Arabic / English)','state':'optional','summary':'Local faster-whisper -> SRT'},
 {'id':'title-motion','name':'30 Text Animations','state':'ready','summary':'30 original animated transparent ProRes title presets'},
 {'id':'3d-text','name':'3D Text','state':'ready','summary':'2.5D extruded PNG only (not editable 3D)'},
 {'id':'text-path','name':'Text on Path','state':'ready','summary':'Raster curved text, Arabic shaped word-by-word'},
 {'id':'draw-overlay','name':'Draw on Video','state':'ready','summary':'Original animated hand-draw overlays as transparent ProRes'},
 {'id':'title-still','name':'Motion Graphics / Title Templates','state':'ready','summary':'12 original title styles; export PNG, motion variants via Title Motion'},
 {'id':'carousel','name':'Animated Carousel','state':'ready','summary':'Pan/zoom slide MP4 from user images'},
 {'id':'icon','name':'Icon Library','state':'ready','summary':'22 original icons exported as SVG'},
 {'id':'web-assets','name':'Web Asset Search','state':'planned','summary':'No asset service integrated'},
 {'id':'download','name':'Media Downloader','state':'optional','summary':'yt-dlp adapter, only with content rights'},
 {'id':'remove-bg','name':'Background Removal','state':'optional','summary':'rembg local model adapter for still images'},
 {'id':'sfx','name':'SFX Library & Generation','state':'ready','summary':'12 original procedural offline sound effects'},
 {'id':'silence-cut','name':'Silence Remover','state':'ready','summary':'Detect / render; optional auto-editor Premiere XML'},
 {'id':'podcast','name':'Podcast Tools','state':'ready','summary':'Podcast voice processing to WAV'},
 {'id':'enhance-audio','name':'Audio Enhancement','state':'ready','summary':'4 local FFmpeg audio processing modes'},
 {'id':'transition','name':'Transitions','state':'ready','summary':'16 FFmpeg video-only transitions'},
 {'id':'easing','name':'Easing Curves','state':'ready','summary':'6 motion curve CSV exports'},
 {'id':'speed-ramp','name':'Speed Ramping','state':'ready','summary':'3 section offline media ramp render'},
 {'id':'tracking','name':'Motion Tracking','state':'optional','summary':'OpenCV ROI tracking -> CSV, not Premiere keyframes'},
 {'id':'safe-guide','name':'Social Safe Zones','state':'ready','summary':'5 transparent safe zone PNG overlays'},
 {'id':'organizer','name':'Project Organizer','state':'ready','summary':'Non-destructive folder copy plan; not native bins'},
 {'id':'creator-captions','name':'Creator Captions (Arabic / English)','state':'optional','summary':'Word-level Whisper + 8 original ASS styles + SRT and timing JSON'},
 {'id':'creator-zoom','name':'Creator Zoom Video (file export)','state':'ready','summary':'Punch/Reaction/Snap zoom render; Premiere native preset is separate'},
 {'id':'creator-speed-ramp','name':'Creator Speed Ramp (file export)','state':'ready','summary':'Smooth sampled velocity presets; output copy, not native time remapping'},
]
IDS={x['id'] for x in TOOLS}

def output_path(src,tool,ext):
    if src:
        p=Path(src)
        base=(p.parent/(p.stem+'.og-'+tool+ext)).resolve()
    else:base=(Path.home()/'Videos'/'OG Tools'/(tool+ext)).resolve()
    candidate=base;index=2
    while candidate.exists():
        candidate=base.with_name(base.stem+f'-{index}'+base.suffix);index+=1
    return str(candidate)

def execute(job):
    tool=str(job.get('tool',''))
    if tool not in IDS:raise ValueError('Unknown tool')
    if tool in ('web-assets',):raise NotImplementedError('This feature has not been implemented')
    src=str(job.get('source','')).strip()
    out=str(job.get('output','')).strip()
    if tool=='safe-guide':
        out=out or output_path('','guide','.png')
        return visuals.guide_overlay(out,str(job.get('format','reels')))
    if tool=='sfx':
        out=out or output_path('','sfx','.wav')
        return media.sfx(out,str(job.get('kind','whoosh')),float(job.get('duration',.7)))
    if tool=='title-motion':
        out=out or output_path('','title','.mov')
        return motion.render(str(job.get('text','OG TOOLS')),out,motion=str(job.get('motion','slide-up')),
            width=int(job.get('width',540)),height=int(job.get('height',960)),
            size=int(job.get('size',72)),fps=int(job.get('fps',25)),duration=float(job.get('duration',1.2)),
            font=str(job.get('font','')) or None,style=str(job.get('style','editorial')))
    if tool=='title-still':
        out=out or output_path('','title','.png')
        return visuals.title_png(str(job.get('text','OG TOOLS')),out,width=int(job.get('width',1080)),
            height=int(job.get('height',1920)),size=int(job.get('size',90)),
            style=str(job.get('style','editorial')),font=str(job.get('font','')) or None)
    if tool=='3d-text':
        out=out or output_path('','extruded','.png')
        return visuals.extruded_text(str(job.get('text','OG TOOLS')),out,int(job.get('width',1080)),int(job.get('height',1920)),int(job.get('size',104)))
    if tool=='text-path':
        out=out or output_path('','curved','.png')
        return visuals.arc_text(str(job.get('text','OG TOOLS')),out,int(job.get('width',1080)),int(job.get('height',1920)),int(job.get('size',65)))
    if tool=='draw-overlay':
        out=out or output_path('','drawing','.mov')
        return visuals.draw_overlay(out,int(job.get('width',540)),int(job.get('height',960)),
            int(job.get('fps',25)),float(job.get('duration',1.2)),str(job.get('shape','arrow')))
    if tool=='icon':
        out=out or output_path('','icon','.svg')
        return visuals.icon_export(str(job.get('icon','play')),out,str(job.get('color','#FFFFFF')))
    if tool=='easing':
        out=out or output_path('','easing','.csv')
        return extras.easing_csv(out,str(job.get('easing','ease-out-cubic')))
    if tool=='organizer':
        if not src:raise ValueError('Select a source folder')
        out=out or str(Path(src).resolve().parent/(Path(src).name+'_OG_SORTED'))
        result=extras.organizer(src,out,bool(job.get('copy',False)))
        # Plan is saved to JSON so no huge payload needs to go through panel.
        plan=str(Path(out).resolve().parent/'og-organization-plan.json')
        Path(plan).parent.mkdir(parents=True,exist_ok=True)
        Path(plan).write_text(__import__('json').dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        return {'output':plan,'files':result['files'],'copied':result['copied']}
    if tool=='carousel':
        images=job.get('images') or [s.strip() for s in src.split('|') if s.strip()]
        out=out or output_path('','carousel','.mp4')
        return visuals.carousel(images,out,int(job.get('width',540)),int(job.get('height',960)),float(job.get('slide_duration',2)))
    if tool=='download':
        url=str(job.get('url',''))
        folder=out or output_path('','downloads','')
        return media.download_owned(url,folder)
    if not src:raise ValueError('Select a source file')
    if tool=='silence-cut':
        if job.get('source_start') or job.get('source_end'):
            if job.get('premiere_xml',False):
                raise ValueError('Selected source trims cannot yet be exported as Premiere XML. Use rendered cut or Analyze only.')
            out=out or output_path(src,'selected-silence','.json' if job.get('analyze_only') else ('.mp4' if media.probe(src)['video'] else '.wav'))
            return creator.selected_silence(src,out,noise=float(job.get('noise',-35)),
                minimum=float(job.get('minimum',.5)),padding=float(job.get('padding',.1)),
                start=float(job.get('source_start',0) or 0),end=job.get('source_end') or None,
                timeline_offset=float(job.get('timeline_offset',0) or 0),
                analyze_only=bool(job.get('analyze_only',False)))
        if job.get('premiere_xml',False):
            out=out or output_path(src,'premiere-cut','.xml')
            return media.export_premiere_xml(src,out)
        if job.get('analyze_only',False):
            data=media.detect_silence(src,float(job.get('noise',-35)),float(job.get('minimum',.5)),float(job.get('padding',.1)))
            out=out or output_path(src,'silence','.json')
            Path(out).write_text(__import__('json').dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
            return {'output':out,'silences':len(data['silence']),'keep_intervals':len(data['keep'])}
        out=out or output_path(src,'silence','.mp4' if media.probe(src)['video'] else '.wav')
        return media.remove_silence(src,out,float(job.get('noise',-35)),float(job.get('minimum',.5)),float(job.get('padding',.1)))
    if tool=='creator-captions':
        out=out or output_path(src,'creator-captions','.srt')
        return creator.create_caption_package(src,out,language=str(job.get('language','ar')),
            model=str(job.get('model','small')),style=str(job.get('caption_style','kinetic-pop')),
            palette=str(job.get('palette','ivory')),start=float(job.get('source_start',0) or 0),
            end=job.get('source_end') or None,timeline_offset=float(job.get('timeline_offset',0) or 0),
            words=job.get('words'),burn=bool(job.get('burn',False)),
            width=int(job.get('width',1080)),height=int(job.get('height',1920)),
            max_words=int(job.get('max_words',3)),font=str(job.get('caption_font','')).strip() or None)
    if tool=='creator-zoom':
        out=out or output_path(src,'creator-zoom','.mp4')
        return creator.zoom_render(src,out,preset=str(job.get('zoom_preset','punch-in')),
            strength=float(job.get('strength',.16)),duration=float(job.get('zoom_duration',.45)),
            start=float(job.get('source_start',0) or 0),end=job.get('source_end') or None)
    if tool=='creator-speed-ramp':
        out=out or output_path(src,'creator-ramp','.mp4')
        return creator.creator_speed_ramp(src,out,str(job.get('ramp_preset','whip')),
                                          int(job.get('steps',9)),
                                          start=float(job.get('source_start',0) or 0),end=job.get('source_end') or None)
    if tool=='captions':
        out=out or output_path(src,'captions','.srt')
        return extras.transcribe(src,out,str(job.get('language','auto')),str(job.get('model','small')))
    if tool=='enhance-audio' or tool=='podcast':
        out=out or output_path(src,'enhanced','.wav')
        return media.enhance_audio(src,out,'podcast' if tool=='podcast' else str(job.get('mode','voice')))
    if tool=='speed-ramp':
        out=out or output_path(src,'speed','.mp4')
        speeds=[float(job.get('speed1',.7)),float(job.get('speed2',1.8)),float(job.get('speed3',.85))]
        return media.make_speed_ramp(src,out,speeds)
    if tool=='transition':
        second=str(job.get('second','')).strip()
        if not second:raise ValueError('Select the second video file')
        out=out or output_path(src,'transition','.mp4')
        return media.transition(src,second,out,str(job.get('transition','fade')),
            float(job.get('transition_duration',.5)),int(job.get('width',540)),int(job.get('height',960)))
    if tool=='remove-bg':
        out=out or output_path(src,'cutout','.png')
        return extras.remove_background(src,out)
    if tool=='tracking':
        out=out or output_path(src,'tracking','.csv')
        return extras.track_motion(src,out,int(job.get('x',0)),int(job.get('y',0)),int(job.get('w',80)),int(job.get('h',80)))
    raise NotImplementedError(tool)
