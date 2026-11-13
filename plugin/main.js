// UXP panel lifecycle; the markup is shipped in index.html.
try {
  const { entrypoints } = require('uxp');
  entrypoints.setup({panels:{'ogtools.panel':{show(){ /* existing markup stays in DOM */ }}}});
} catch (e) { /* standalone syntax checks run outside Premiere */ }
/* OG Tools UXP panel. Local bridge and Premiere APIs are feature-detected.
   No promise of native timeline cuts: outputs are new media files. */
const ENGINE='http://127.0.0.1:8734';
const toolMeta=[
 ['captions','AI Captions','optional','faster-whisper → Arabic/English SRT'],
 ['title-motion','30 Text Animations','ready','Transparent ProRes 4444 motion titles'],
 ['3d-text','3D Text','ready','2.5D raster extrusion; not native editable 3D'],
 ['text-path','Text on Path','ready','Curved PNG, Arabic shaped word-by-word'],
 ['draw-overlay','Draw-on Video','ready','Animated transparent ink/draw overlays'],
 ['title-still','Graphic Templates','ready','12 original title styles'],
 ['carousel','Animated Carousel','ready','Ken Burns slideshow from images'],
 ['icon','Icon Library','ready','22 original SVG symbols'],
 ['web-assets','Web Assets','planned','No external asset search yet'],
 ['download','Media Download','optional','Requires yt-dlp and permission to download'],
 ['remove-bg','Remove Background','optional','Still image matting with rembg'],
 ['sfx','SFX Generator','ready','12 synthesised sound effects'],
 ['silence-cut','Silence Remover','ready','Export cut copy; optional auto-editor Premiere XML'],
 ['podcast','Podcast Studio','ready','Voice-focused noise/compression chain'],
 ['enhance-audio','Enhance Audio','ready','Voice, denoise or normalize'],
 ['transition','Transitions','ready','16 offline video-only transition presets'],
 ['easing','Easing Curves','ready','Export motion curves as CSV'],
 ['speed-ramp','Speed Ramping','ready','3-segment video speed variations'],
 ['tracking','Motion Tracking','optional','ROI tracker to CSV (OpenCV)'],
 ['safe-guide','Social Guides','ready','5 transparent social safe zones'],
 ['organizer','Project Organizer','ready','Safe non-destructive copy plan'],
 ['creator-captions','Creator Captions · Arabic / English','optional','Word-level local captions, 8 fresh creator styles, SRT + ASS + JSON'],
 ['creator-zoom','Creator Zoom Render','ready','Creator punch / snap / reaction zooms in exported MP4'],
 ['creator-speed-ramp','Creator Velocity Ramp','ready','5 eased-speed presets, audio preserved as offline MP4'],
];
const MOTIONS='fade-in fade-out slide-up slide-down slide-left slide-right zoom-in zoom-out pop bounce elastic rotate-in rotate-out spin blur-in blur-out reveal-left reveal-right reveal-up reveal-down typewriter word-rise word-fade letter-rise letter-pop drift-up drift-down scale-fade drop-in float-in'.split(' ');
const STYLES='editorial ivory plum outline impact lower-third minimal mono sand redline studio caption'.split(' ');
const TRANSITIONS='fade wipeleft wiperight wipeup wipedown slideleft slideright slideup slidedown circlecrop radial pixelize smoothleft smoothright dissolve hblur'.split(' ');
const ICONS='play pause check close arrow-right arrow-left plus minus menu search user home heart location clock mail camera volume download calendar star bolt'.split(' ');
const sel=id=>document.getElementById(id), log=(txt,good=null)=>{const el=sel('log');el.className='log'+(good===true?' good':good===false?' bad':'');el.textContent=typeof txt==='string'?txt:JSON.stringify(txt,null,2)};
let active='title-motion',lastOutput='',images=[],currentJob=null,selectionFields=null;
function createField(label,key,type='text',options=null,def=''){
 const wrap=document.createElement('div');wrap.className='field';const lbl=document.createElement('label');lbl.className='field-label';lbl.textContent=label;lbl.setAttribute('for','f-'+key);wrap.appendChild(lbl);
 let el;if(options){el=document.createElement('select');for(const value of options){const opt=document.createElement('option');opt.value=value;opt.textContent=value;el.appendChild(opt)}}else{el=document.createElement('input');el.type=type};el.id='f-'+key;el.value=String(def);wrap.appendChild(el);sel('fields').appendChild(wrap)
}
function drawTools(query=''){
 const root=sel('tools');root.replaceChildren();for(const [id,name,state] of toolMeta){if(!(name+' '+id).toLowerCase().includes(query.toLowerCase()))continue;
 const el=document.createElement('button');el.className='tool'+(id===active?' active':'');
 const span=document.createElement('span');span.textContent=name;const status=document.createElement('small');status.className='state '+state;status.textContent=state==='ready'?'LOCAL ENGINE':state==='optional'?'OPTIONAL PACKAGE':'NOT BUILT';el.append(span,status);
 el.addEventListener('click',()=>setTool(id));root.appendChild(el)}
}
function setTool(id){active=id;const meta=toolMeta.find(t=>t[0]===id);sel('tool-title').textContent=meta[1];sel('tool-status').textContent=meta[2];sel('tool-desc').textContent=meta[3];sel('fields').replaceChildren();
 sel('secondary').classList.toggle('hide',id!=='transition');sel('imageArea').classList.toggle('hide',id!=='carousel');
 const noSource=['title-motion','title-still','3d-text','text-path','draw-overlay','sfx','safe-guide','easing','icon','download'].includes(id);
 sel('source').parentElement.previousElementSibling.classList.toggle('hide',noSource||id==='carousel');sel('source').parentElement.classList.toggle('hide',noSource||id==='carousel');
 if(['title-motion','title-still','3d-text','text-path'].includes(id)){
   createField('Title text (Arabic / English)','text','text',null,'خطوة بخطوة');if(!['3d-text','text-path'].includes(id))createField('Visual style','style','select',STYLES,'editorial');
   if(id==='title-motion')createField('Animation','motion','select',MOTIONS,'slide-up');
   createField('Width (px)','width','number',null,540);createField('Height (px)','height','number',null,960);createField('Font size','size','number',null,62);
   if(id==='title-motion')createField('Animation duration (seconds)','duration','number',null,1.2);
 }
 if(id==='draw-overlay'){createField('Draw shape','shape','select',['arrow','underline','circle','rectangle','diagonal'],'arrow');createField('Duration','duration','number',null,1.2)}
 if(id==='captions'||id==='creator-captions'){
   createField('Language','language','select',['ar','en','auto'],'ar');createField('Whisper model','model','select',['tiny','base','small','medium','large-v3','turbo'],'small');
   if(id==='creator-captions'){
     createField('Creator caption style','caption_style','select',['kinetic-pop','clean-focus','editorial-accent','word-flash','micro-bounce','mono-underline','hook-punch','quiet-lower'],'kinetic-pop');
     createField('Color palette','palette','select',['ivory','plum','acid','amber'],'ivory');
     createField('Caption font (installed font family)','caption_font','text',null,'');
     createField('Max words per phrase','max_words','number',null,3);
     createField('Sequence-aligned subtitle offset (seconds)','timeline_offset','number',null,0);
     createField('Original media in-point (seconds)','source_start','number',null,0);
     createField('Original media out-point (blank = end)','source_end','text',null,'');
     createField('Render captioned preview MP4','burn','checkbox',null,false);
     createField('Output width','width','number',null,1080);createField('Output height','height','number',null,1920);
   }
 }
 if(id==='silence-cut'){createField('Silence threshold (dB)','noise','number',null,-35);createField('Minimum silence (sec)','minimum','number',null,.5);createField('Padding (sec)','padding','number',null,.1);createField('Analyze only — do not render video','analyze_only','checkbox',null,false);createField('Premiere XML via auto-editor (requires optional installation)','premiere_xml','checkbox',null,false);createField('Selected clip source in-point (sec)','source_start','number',null,0);createField('Selected clip source out-point (blank = end)','source_end','text',null,'');createField('Timeline alignment (sec)','timeline_offset','number',null,0)}
 if(id==='enhance-audio')createField('Audio mode','mode','select',['voice','podcast','normalize','denoise'],'voice');
 if(id==='sfx'){createField('SFX type','kind','select',['whoosh','click','pop','rise','impact','beep','notification','success','error','sweep','glitch','tick'],'whoosh');createField('Duration (seconds)','duration','number',null,.7)}
 if(id==='transition'){createField('Transition','transition','select',TRANSITIONS,'fade');createField('Duration (seconds)','transition_duration','number',null,.5)}
 if(id==='creator-zoom'){
   createField('Creator zoom look','zoom_preset','select',['punch-in','punch-out','snap-zoom','slow-push','reaction-hit','breath'],'punch-in');
   createField('Zoom strength (e.g. .16 = +16%)','strength','number',null,.16);
   createField('Zoom duration / ramp span (seconds)','zoom_duration','number',null,.45);
   createField('Selected clip source in-point (sec)','source_start','number',null,0);createField('Selected clip source out-point (blank = end)','source_end','text',null,'');
 }
 if(id==='creator-speed-ramp'){
   createField('Creator velocity preset','ramp_preset','select',['whip','impact','smooth','hyper','reverse-feel'],'whip');
   createField('Speed samples (3–48; 9 default)','steps','number',null,9);
   createField('Selected clip source in-point (sec)','source_start','number',null,0);createField('Selected clip source out-point (blank = end)','source_end','text',null,'');
 }
 if(id==='speed-ramp'){createField('First third speed','speed1','number',null,.7);createField('Middle third speed','speed2','number',null,1.8);createField('Last third speed','speed3','number',null,.85)}
 if(id==='carousel')createField('Slide seconds','slide_duration','number',null,2);
 if(id==='icon')createField('Icon','icon','select',ICONS,'play');
 if(id==='easing')createField('Easing curve','easing','select',['linear','ease-in-cubic','ease-out-cubic','ease-in-out-cubic','ease-out-back','ease-out-elastic'],'ease-out-cubic');
 if(id==='safe-guide')createField('Social format','format','select',['reels','story','portrait','square','youtube'],'reels');
 if(id==='organizer')createField('Copy files into organized folders (unchecked = plan only)','copy','checkbox',null,false);
 if(id==='tracking'){for(const key of ['x','y','w','h'])createField('ROI '+key,key,'number',null,key==='w'||key==='h'?100:0)}
 if(id==='download')createField('Owned/authorized media URL','url','url',null,'https://');
 sel('run').disabled=meta[2]==='planned';sel('import').disabled=!lastOutput||!canImport(lastOutput);drawTools(sel('search').value)
}
function canImport(path){return /\.(mov|mp4|srt|png|jpg|jpeg|wav|mp3|xml)$/i.test(path||'')}
async function getFile(multiple=false,folder=false){
 let fs;try{fs=require('uxp').storage.localFileSystem}catch(e){throw new Error('File picker requires Premiere UXP host: '+e.message)}
 let choice=folder?await fs.getFolder():await fs.getFileForOpening({allowMultiple:multiple});
 if(!choice)return null;const arr=Array.isArray(choice)?choice:[choice];return arr.map(x=>fs.getNativePath(x))
}
async function browseInto(id,folder=false){try{const picks=await getFile(false,folder);if(picks&&picks.length)sel(id).value=picks[0]}catch(e){log(String(e),false)}}
async function ping(){try{const r=await fetch(ENGINE+'/api/health');if(!r.ok)throw Error('HTTP '+r.status);const info=await r.json();sel('connection').textContent='ENGINE ONLINE';sel('connection').classList.add('on');return info}catch(e){sel('connection').textContent='ENGINE OFF';sel('connection').classList.remove('on');return null}}
function readSpec(){const data={tool:active,source:sel('source').value.trim(),output:sel('output').value.trim()};if(active==='transition')data.second=sel('second').value.trim();if(active==='carousel')data.images=images;
 for(const field of sel('fields').querySelectorAll('input,select')){const key=field.id.slice(2);data[key]=field.type==='checkbox'?field.checked:field.type==='number'?Number(field.value):field.value}
 return data}
async function runTool(){const meta=toolMeta.find(t=>t[0]===active);if(meta[2]==='planned'){log('Not implemented.',false);return}
 const info=await ping();if(!info){log('Engine offline. Run OG Tools Launcher, then click Reconnect.',false);return}
 const spec=readSpec();sel('run').disabled=true;sel('import').disabled=true;lastOutput='';log('Job submitted. Processing local media...');
 try{const r=await fetch(ENGINE+'/api/jobs',{method:'POST',headers:{'Content-Type':'application/json','X-OG-Tools':'local'},body:JSON.stringify(spec)});const js=await r.json();if(!r.ok)throw Error(js.error||r.status);
 const id=js.id;currentJob=id;for(let attempts=0;attempts<2400;attempts++){
  await new Promise(resolve=>setTimeout(resolve,600));const response=await fetch(ENGINE+'/api/jobs/'+id);const state=await response.json();
  if(state.status==='done'){const res=state.result||{};lastOutput=res.output||(res.render&&res.render.output)||'';
   log('Completed.\n'+JSON.stringify(res,null,2),true);sel('import').disabled=!canImport(lastOutput);return}
  if(state.status==='error')throw Error(state.error||'Unknown processing error');
  if(attempts%10===0)log('OG Tools job is '+state.status+'...\nWorking locally. Large media and Whisper may need extra time.');
 }throw Error('Job polling timed out. Query engine logs for final status.')
 }catch(e){log('Processing failed: '+(e.message||e),false)}finally{sel('run').disabled=meta[2]==='planned'?true:false}
}
async function inspect(){try{const premiere=require('premierepro');const p=await premiere.Project.getActiveProject();if(!p){sel('project').textContent='No active project';return}
 const s=await p.getActiveSequence();sel('project').textContent='Project: '+(p.name||'Untitled')+' · Sequence: '+(s?s.name:'None')}
 catch(e){sel('project').textContent='Premiere API not available here: '+String(e.message||e)}}
async function importOutput(){if(!lastOutput||!canImport(lastOutput))return;try{
 const premiere=require('premierepro'),p=await premiere.Project.getActiveProject();if(!p)throw Error('Open a Premiere project first');
 const root=await p.getRootItem();const ok=await p.importFiles([lastOutput],false,root,false);
 if(!ok)throw Error('Premiere importFiles returned false');log('Imported media into Project bin: '+lastOutput,true)
 }catch(e){log('Could not import into project: '+String(e.message||e),false)}}
async function useSelectedClip(){
 try{
  const first=await globalThis.OGClipSelection.resolve(require('premierepro'));
  sel('source').value=first.path;selectionFields=first;
  if(['creator-captions','silence-cut','creator-zoom','creator-speed-ramp'].includes(active)){
    const fields={source_start:first.start,source_end:first.end,timeline_offset:first.offset};
    for(const [key,v] of Object.entries(fields)){const f=sel('f-'+key);if(f)f.value=String(v)}
  }
  sel('selectedInfo').textContent=`Selected: ${first.name} | In ${first.start.toFixed(2)}s · Out ${first.end.toFixed(2)}s · Sequence start ${first.offset.toFixed(2)}s. Timeline unmodified.`;
  log('Selected source linked. Run tool to process a new copy.',true);
 }catch(e){log('Selected clip: '+(e.message||e),false)}
}
sel('fromSelection').addEventListener('click',useSelectedClip);
sel('search').addEventListener('input',e=>drawTools(e.target.value));sel('run').addEventListener('click',runTool);sel('refresh').addEventListener('click',async()=>log(await ping()||'Engine offline'));
sel('inspect').addEventListener('click',inspect);sel('import').addEventListener('click',importOutput);
sel('browse').addEventListener('click',()=>browseInto('source',active==='organizer'));
sel('browseSecond').addEventListener('click',()=>browseInto('second'));
sel('browseImages').addEventListener('click',async()=>{try{const paths=await getFile(true,false);if(paths){images=paths;sel('imageCount').textContent=images.length+' images selected'}}catch(e){log(String(e),false)}});
setTool('title-motion');ping();
