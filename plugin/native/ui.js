(function(){'use strict';
 const api=globalThis.OGNativeKeyframes;
 const $=id=>document.getElementById(id);
 if(!api||!$('nativePreset'))return;
 let lastInfo=null;
 for(const name of api.PRESETS){const opt=document.createElement('option');opt.value=name;opt.textContent=name.replace(/-/g,' ').replace(/\b\w/g,x=>x.toUpperCase());$('nativePreset').append(opt)}
 $('nativePreset').value='slide-up';
 const status=(msg,good)=>{const el=$('nativeLog');el.textContent=msg;el.className='log '+(good===true?'good':good===false?'bad':'')};
 function selectedMap(){const m={};for(const ch of api.CHANNELS){const el=$('nativeMap-'+ch);if(el&&el.value)m[ch]=el.value}return m}
 async function inspect(){const ppro=require('premierepro');const info=await api.scanSelected(ppro);lastInfo=info;
   const suggests=api.suggest(info.params);const container=$('nativeMappingFields');container.replaceChildren();
   for(const ch of api.CHANNELS){
     const wrap=document.createElement('div');const label=document.createElement('label');label.className='field-label';label.textContent=ch.toUpperCase();
     const select=document.createElement('select');select.id='nativeMap-'+ch;
     const empty=document.createElement('option');empty.value='';empty.textContent='(not assigned)';select.append(empty);
     for(const p of info.params.filter(p=>(ch==='position')===(p.kind==='point'))){const o=document.createElement('option');o.value=p.id;o.textContent=p.component+' / '+p.name+' ['+JSON.stringify(p.base)+']';select.append(o)}
     select.value=suggests[ch]||'';wrap.append(label,select);container.append(wrap)
   }
   $('nativeMappings').classList.remove('hide');
   status(`Selected: ${info.itemName} (${info.duration.toFixed(2)}s)\nAvailable animatable parameters: ${info.params.length}\nAssign required parameters, then Apply.`,true);
   return info;
 }
 for(const b of document.querySelectorAll('[data-creatorzoom]'))b.addEventListener('click',()=>{
   $('nativePreset').value=b.dataset.creatorzoom;
   $('nativeDuration').value= b.dataset.creatorzoom==='creator-snap-zoom'?'0.65':'1.0';
   $('nativeApply').click();
 });
 $('nativeInspect').addEventListener('click',async()=>{try{await inspect()}catch(e){status('Inspect failed: '+(e.message||e),false)}});
 $('nativeApply').addEventListener('click',async()=>{
   $('nativeApply').disabled=true;
   try{if(!lastInfo)await inspect();const ppro=require('premierepro');
     const res=await api.applySelected(ppro,{preset:$('nativePreset').value,duration:Number($('nativeDuration').value),samples:Number($('nativeSamples').value),map:selectedMap()});
     status(`Done: ${res.preset}\n${res.keyframeCount} native keyframes added on ${res.selectedClip}.\nProperties: ${res.channels.join(', ')}.\nEditable in Premiere Effect Controls.`,true);
   }catch(e){status('Keyframe operation failed: '+(e.message||e),false)}finally{$('nativeApply').disabled=false}
 });
})();
