/* Resolve trimmed media directly from a selected Premiere timeline clip.
   This does not export a mixed track or mutate any timeline content.
   It deliberately refuses ambiguous selections and non-1x speed media. */
(function(root,factory){
 if(typeof module==='object'&&module.exports)module.exports=factory();
 else root.OGClipSelection=factory();
})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 async function resolve(ppro){
   if(!ppro||!ppro.Project)throw Error('Premiere UXP required');
   const project=await ppro.Project.getActiveProject();if(!project)throw Error('Open a Premiere project');
   const seq=await project.getActiveSequence();if(!seq)throw Error('Open a sequence');
   const sel=await seq.getSelection();const items=await sel.getTrackItems();
   if(!items.length)throw Error('Select an audio or video clip on the timeline');
   const choices=[];
   for(const item of items){
    try{
     const projectItem=await item.getProjectItem();
     if(!projectItem||typeof projectItem.getMediaFilePath!=='function')continue;
     const path=await projectItem.getMediaFilePath();if(!path)continue;
     const st=await item.getStartTime(),pin=await item.getInPoint(),pout=await item.getOutPoint(),speed=await item.getSpeed();
     const info={path,start:Number(pin.seconds),end:Number(pout.seconds),offset:Number(st.seconds),speed:Number(speed),name:await item.getName()};
     if(Object.values(info).some(x=>typeof x==='number'&&!Number.isFinite(x)))throw Error('Invalid clip timing');
     if(info.end<=info.start)throw Error('Invalid clip trim');
     choices.push(info);
    }catch(e){
     // Missing media path: ignore nonfile graphic/item; do not fabricate a file path.
     if(/Invalid clip/.test(String(e.message||e)))throw e;
    }
   }
   if(!choices.length)throw Error('Selection has no accessible local media path');
   const first=choices[0];
   if(choices.some(o=>o.path!==first.path||Math.abs(o.start-first.start)>.05||Math.abs(o.end-first.end)>.05||Math.abs(o.offset-first.offset)>.05))
     throw Error('Select one clip or one matching linked audio/video pair');
   if(choices.some(o=>Math.abs(o.speed-1)>.02))throw Error('This clip has altered playback speed; export a copy first to avoid out-of-sync captions');
   return first;
 }
 return {resolve};
});
