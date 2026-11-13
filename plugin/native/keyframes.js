/* OG Tools Native Keyframe Studio — UXP Premiere Pro 26.x.
   Original code using documented UXP ComponentParam Actions.
   Applies animation to the selected *existing editable Graphic / MOGRT / clip*.
   Existing keyframes are NEVER silently overwritten. No rasterized output.
*/
(function(root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.OGNativeKeyframes = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function() {
  'use strict';
  const PRESETS = Object.freeze([
    'fade-in','fade-out','slide-up','slide-down','slide-left','slide-right',
    'zoom-in','zoom-out','pop','bounce','elastic','rotate-in','rotate-out','spin',
    'drift-up','drift-down','scale-fade','drop-in','float-in','pulse',
    'shake-x','shake-y','tilt-in','overshoot',
    'creator-punch-in','creator-punch-out','creator-snap-zoom','creator-reaction',
    'creator-jumpcut','creator-slow-push','creator-breathe','creator-focus-pull',
    'creator-hook-slam','creator-beat-nudge','creator-snap-hold','creator-recoil','creator-soft-land','creator-staccato'
  ]);
  const CHANNELS = ['position','scale','opacity','rotation'];
  const clamp = (x,lo,hi) => Math.max(lo,Math.min(hi,x));
  const easeOut = t => 1-Math.pow(1-t,3);
  const easeIn = t => t*t*t;
  const easeInOut = t => t < .5 ? 4*t*t*t : 1-Math.pow(-2*t+2,3)/2;
  function valuesAt(preset,t) {
    t=clamp(Number(t),0,1);
    const o={x:0,y:0,scale:1,opacity:1,rotation:0};
    const e=easeOut(t), u=1-e;
    switch(preset) {
      // Social creator edits: intentionally held zooms instead of classic enter/exit titling.
      case 'creator-punch-in':o.scale=1+.16*easeOut(clamp(t/.23,0,1));break;
      case 'creator-punch-out':o.scale=1+.16*(1-easeOut(clamp(t/.27,0,1)));break;
      case 'creator-snap-zoom':o.scale=1+.28*(t<.18?easeOut(t/.18):t<.5?1:1-easeInOut((t-.5)/.5));break;
      case 'creator-reaction':o.scale=1+.22*easeOut(clamp(t/.12,0,1))-.055*easeOut(clamp((t-.12)/.22,0,1));break;
      case 'creator-jumpcut':o.scale=1+.12*easeOut(clamp(t/.09,0,1));break;
      case 'creator-slow-push':o.scale=1+.08*easeInOut(t);break;
      case 'creator-breathe':o.scale=1+.07*Math.sin(Math.PI*t);break;
      case 'creator-focus-pull':o.scale=1+.12*easeInOut(t);o.x=.023*(1-easeInOut(t));break;
      case 'creator-hook-slam':{
        const hit=easeOut(clamp(t/.18,0,1));const settle=easeOut(clamp((t-.18)/.26,0,1));
        o.scale=.62+.65*hit-.27*settle;o.rotation=-3+5*hit-2*settle;break;
      }
      case 'creator-beat-nudge':{
        const envelope=Math.pow(1-t,2);o.x=.022*Math.sin(Math.PI*11*t)*envelope;
        o.rotation=1.6*Math.sin(Math.PI*7*t)*envelope;break;
      }
      case 'creator-snap-hold':o.scale=1+.17*easeOut(clamp(t/.11,0,1));break;
      case 'creator-recoil':{
        const hit=easeOut(clamp(t/.1,0,1));const settle=easeOut(clamp((t-.1)/.3,0,1));
        o.scale=1+.28*hit-.23*settle;break;
      }
      case 'creator-soft-land':{
        const land=easeOut(clamp(t/.32,0,1));o.y=-.14*(1-land);o.scale=.88+.12*land;
        o.opacity=clamp(t/.16,0,1);break;
      }
      case 'creator-staccato':{
        const burst=t<.1?easeOut(t/.1):t<.26?1:1-easeOut((t-.26)/.2);
        o.scale=1+.16*burst;o.rotation=2.5*burst;break;
      }
      case 'fade-in': o.opacity=e;break;
      case 'fade-out': o.opacity=1-e;break;
      case 'slide-up':o.y=.21*u;o.opacity=e;break;
      case 'slide-down':o.y=-.21*u;o.opacity=e;break;
      case 'slide-left':o.x=.34*u;o.opacity=e;break;
      case 'slide-right':o.x=-.34*u;o.opacity=e;break;
      case 'zoom-in':o.scale=.55+.45*e;o.opacity=e;break;
      case 'zoom-out':o.scale=1.45-.45*e;o.opacity=e;break;
      case 'pop':o.scale=.65+.35*e+.14*Math.sin(Math.PI*t)*(1-t);o.opacity=e;break;
      case 'bounce':o.y=-.22*Math.abs(Math.sin(Math.PI*t*3))*(1-t);o.opacity=e;break;
      case 'elastic':o.scale=1+.26*Math.sin(Math.PI*5*t)*u;o.opacity=e;break;
      case 'rotate-in':o.rotation=-48*u;o.opacity=e;break;
      case 'rotate-out':o.rotation=48*e;o.opacity=1-e;break;
      case 'spin':o.rotation=-360*u;o.opacity=e;break;
      case 'drift-up':o.y=.10*u;o.opacity=e;break;
      case 'drift-down':o.y=-.10*u;o.opacity=e;break;
      case 'scale-fade':o.scale=.8+.2*e;o.opacity=e;break;
      case 'drop-in':o.y=-.5*u*u;o.opacity=clamp(t*2,0,1);break;
      case 'float-in':o.y=.12*u+.015*Math.sin(Math.PI*2*t)*u;o.opacity=e;break;
      case 'pulse':o.scale=1+.14*Math.sin(Math.PI*2*t)*(1-t);break;
      case 'shake-x':o.x=.06*Math.sin(Math.PI*12*t)*u;break;
      case 'shake-y':o.y=.05*Math.sin(Math.PI*10*t)*u;break;
      case 'tilt-in':o.rotation=-16*u;o.scale=.92+.08*e;o.opacity=e;break;
      case 'overshoot':o.y=-.14*Math.sin(Math.PI*1.5*t)*u;o.scale=.8+.2*e+.10*Math.sin(Math.PI*t)*u;o.opacity=e;break;
      default:throw new Error('Unsupported native preset: '+preset);
    }
    return o;
  }
  function requiredChannels(preset) {
    const a=[valuesAt(preset,0),valuesAt(preset,.25),valuesAt(preset,.5),valuesAt(preset,.75),valuesAt(preset,1)];
    return CHANNELS.filter(k=>a.some(o=>{
      const v=k==='position'?[o.x,o.y]:[o[k]];
      return v.some(x=>Math.abs(x - (k==='scale'||k==='opacity'?1:0))>1e-5);
    }));
  }
  function unwrapValue(v) {
    if (v && typeof v==='object' && 'value' in v) return unwrapValue(v.value);
    if (Array.isArray(v) && v.length===2) return v.map(Number);
    if (v && typeof v==='object' && 'x' in v && 'y' in v) return [Number(v.x),Number(v.y)];
    return v;
  }
  async function scanSelected(ppro) {
    if (!ppro || !ppro.Project) throw new Error('Requires Premiere Pro UXP host.');
    const project=await ppro.Project.getActiveProject();
    if(!project) throw new Error('Open a Premiere project first.');
    const sequence=await project.getActiveSequence();
    if(!sequence)throw new Error('Open a sequence first.');
    const selection=await sequence.getSelection();
    const items=await selection.getTrackItems();
    const videos=[];
    for(const item of items){
      if(typeof item.getComponentChain!=='function')continue;
      try {
        const chain=await item.getComponentChain();
        if(!chain||typeof chain.getComponentCount!=='function')continue;
        let likelyVideo=false;
        for(let i=0;i<chain.getComponentCount();i++){
          const component=chain.getComponentAtIndex(i);
          const name=String(await component.getDisplayName());
          if(/\bmotion\b|\btransform\b|الحركة|الموضع|موشن/i.test(name))likelyVideo=true;
          // Audio panning and volume are not video transform properties.
        }
        if(likelyVideo||items.length===1)videos.push({item,chain});
      }catch(e) { /* ignore unsupported selected items */ }
    }
    if(videos.length!==1)throw new Error('Select exactly one Graphic, MOGRT or video clip on the timeline (one video item).');
    const {item,chain}=videos[0];
    const d=await item.getDuration();
    const duration=Number(d.seconds);
    if(!(duration>0))throw new Error('Selected clip has invalid duration.');
    const frame=typeof sequence.getFrameSize==='function'?await sequence.getFrameSize():null;
    const width=Number(frame?.width)||1920, height=Number(frame?.height)||1080;
    const params=[];
    const count=chain.getComponentCount();
    for(let i=0;i<count;i++){
      let c;try{c=chain.getComponentAtIndex(i)}catch(e){continue}
      const cn=await c.getDisplayName();const pn=c.getParamCount();
      for(let j=0;j<pn;j++){
        const p=c.getParam(j);let can=false;try{can=await p.areKeyframesSupported()}catch(e){}
        if(!can)continue;
        let raw;try{raw=unwrapValue(await p.getStartValue())}catch(e){continue}
        const kind=Array.isArray(raw)&&raw.length===2&&raw.every(Number.isFinite)?'point':typeof raw==='number'&&Number.isFinite(raw)?'number':null;
        if(!kind)continue;
        params.push({id:`${i}:${j}`,component:cn,name:p.displayName,kind,base:raw,param:p});
      }
    }
    return {project,sequence,item,duration,width,height,params,itemName:await item.getName()};
  }
  function suggest(params){
    const res={};
    const patterns={position:/\bposition\b|موضع|الموضع/i,scale:/\bscale\b|حجم|مقياس/i,opacity:/\bopacity\b|شفافي|عتامة/i,rotation:/\brotation\b|تدوير|دوران/i};
    for(const ch of CHANNELS){
      const candidates=params.filter(p=>(ch==='position')===(p.kind==='point'));
      const match=candidates.find(p=>patterns[ch].test(p.name)&&/motion|transform|opacity|الحركة|تحويل|شفاف/i.test(p.component))||candidates.find(p=>patterns[ch].test(p.name));
      if(match)res[ch]=match.id;
    }
    return res;
  }
  function createValue(ppro,channel,base,sample,width,height){
    if(channel==='position'){
      const norm=Math.max(Math.abs(base[0]),Math.abs(base[1]))<=2;
      const dx=sample.x*(norm?1:width),dy=sample.y*(norm?1:height);
      return new ppro.PointF(base[0]+dx,base[1]+dy);
    }
    if(channel==='scale')return base*sample.scale;
    if(channel==='opacity')return clamp(base*sample.opacity,0,Math.max(1,base));
    if(channel==='rotation')return base+sample.rotation;
    throw new Error('Unknown parameter channel '+channel);
  }
  async function applySelected(ppro,{preset='slide-up',duration=1.2,samples=13,map=null}={}){
    if(!PRESETS.includes(preset))throw new Error('Unknown preset');
    if(!Number.isFinite(duration)||duration<=0)throw new Error('Duration must be positive');
    if(!Number.isInteger(samples)||samples<3||samples>65)throw new Error('Sample count must be 3..65');
    const info=await scanSelected(ppro);
    if(duration>info.duration+.001)throw new Error(`Animation (${duration}s) is longer than selected clip (${info.duration.toFixed(2)}s).`);
    const lookup=Object.fromEntries(info.params.map(p=>[p.id,p]));
    const ids=map||suggest(info.params);
    const channels=requiredChannels(preset);
    const chosen=channels.filter(c=>ids[c]&&lookup[ids[c]]).map(c=>({channel:c,...lookup[ids[c]]}));
    if(chosen.length===0)throw new Error('No matching animatable parameters. Use Inspect and manually assign the Position, Scale, Opacity or Rotation parameters.');
    const missing=channels.filter(c=>!chosen.some(p=>p.channel===c));
    // Safety: no silent partial presets, because it can look wrong (e.g. slide with opacity only).
    if(missing.length)throw new Error('Required motion parameters unavailable: '+missing.join(', ')+'. Inspect and assign them.');
    for(const c of chosen){
      if(c.channel==='position'&&c.kind!=='point'||c.channel!=='position'&&c.kind!=='number')throw new Error('Wrong parameter type for '+c.channel);
      const keys=c.param.getKeyframeListAsTickTimes();
      if(keys&&keys.length)throw new Error(`Existing keyframes on ${c.name}: refusing to overwrite. Choose an unanimated clip or remove its keys yourself first.`);
    }
    // All actions are Undoable via Premiere's native transaction system.
    let success=false;
    info.project.lockedAccess(()=>{
      success=info.project.executeTransaction(tx=>{
        for(const c of chosen){if(!c.param.isTimeVarying())tx.addAction(c.param.createSetTimeVaryingAction(true));}
      },'OG Tools: enable animation');
    });
    if(success===false)throw new Error('Premiere rejected enabling keyframes');
    info.project.lockedAccess(()=>{
      success=info.project.executeTransaction(tx=>{
        for(let i=0;i<samples;i++){
          const t=i/(samples-1),sample=valuesAt(preset,t);
          for(const c of chosen){
            const v=createValue(ppro,c.channel,c.base,sample,info.width,info.height);
            const k=c.param.createKeyframe(v);
            k.position=ppro.TickTime.createWithSeconds(Number((t*duration).toFixed(6)));
            tx.addAction(c.param.createAddKeyframeAction(k));
          }
        }
      },`OG Tools: ${preset} keyframes`);
    });
    if(success===false)throw new Error('Premiere rejected keyframe transaction');
    // Dense native keyframes encode a cubic-eased timing curve without requiring private Bezier handles.
    return {preset,selectedClip:info.itemName,duration,samples,keyframeCount:samples*chosen.length,channels:chosen.map(c=>c.channel),nativeEditable:true};
  }
  return {PRESETS, CHANNELS, valuesAt,requiredChannels,unwrapValue,suggest,scanSelected,applySelected};
});
