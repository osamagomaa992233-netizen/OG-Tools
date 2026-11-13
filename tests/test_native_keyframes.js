const {test}=require('node:test');
const assert=require('node:assert/strict');
const native=require('../plugin/native/keyframes.js');
function mockPpro({existing=false,missing='',clipDuration=4,selectionCount=1}={}) {
  const base={position:[960,540],scale:100,opacity:100,rotation:0};
  const names=['Position','Scale','Opacity','Rotation'].filter(x=>x.toLowerCase()!==missing);
  const made={};
  const params=names.map(name=>{
    const val=base[name.toLowerCase()];
    const p={displayName:name,base:val,keys:existing?[{position:{seconds:.2},value:val}]:[],varying:false,
      async areKeyframesSupported(){return true},
      async getStartValue(){return {value:{value:val}}},
      getKeyframeListAsTickTimes(){return this.keys.map(k=>k.position)},
      isTimeVarying(){return this.varying},
      createSetTimeVaryingAction(on){return()=>{this.varying=on}},
      createKeyframe(v){return {value:v,position:{seconds:0}}},
      createAddKeyframeAction(k){return ()=>{this.keys.push(k)}},
    };made[name.toLowerCase()]=p;return p;
  });
  const component={getDisplayName:async()=> 'Motion',getParamCount:()=>params.length,getParam:i=>params[i]};
  const chain={getComponentCount:()=>1,getComponentAtIndex:()=>component};
  const item={getComponentChain:async()=>chain,getDuration:async()=>({seconds:clipDuration}),getName:async()=> 'My editable title'};
  const seq={getSelection:async()=>({getTrackItems:async()=>Array.from({length:selectionCount},()=>item)}),getFrameSize:async()=>({width:1920,height:1080})};
  const project={getActiveSequence:async()=>seq,lockedAccess:f=>f(),executeTransaction:fn=>{const acts=[];fn({addAction:a=>acts.push(a)});acts.forEach(a=>a());return true}};
  const ppro={Project:{getActiveProject:async()=>project},PointF:class PointF{constructor(x,y){this.x=x;this.y=y}},TickTime:{createWithSeconds:x=>({seconds:x})}};
  return {ppro,made};
}
test('presets are distinct and have 32 IDs',()=>{assert.equal(native.PRESETS.length,32);assert.equal(new Set(native.PRESETS).size,32)});
test('animation curves use finite continuous parameters',()=>{
 for(const preset of native.PRESETS)for(let i=0;i<=30;i++){const o=native.valuesAt(preset,i/30);for(const v of Object.values(o))assert.ok(Number.isFinite(v),`${preset} invalid`) }
});
test('can scan selected native title without file rendering',async()=>{
 const {ppro}=mockPpro();const x=await native.scanSelected(ppro);
 assert.equal(x.itemName,'My editable title');assert.equal(x.params.length,4);assert.equal(x.params[0].kind,'point')
});
test('slide-up adds actual keyframes for position and opacity',async()=>{
 const {ppro,made}=mockPpro();const r=await native.applySelected(ppro,{preset:'slide-up',samples:13,duration:1.2});
 assert.equal(r.keyframeCount,26);assert.equal(made.position.keys.length,13);assert.equal(made.opacity.keys.length,13);assert.equal(made.scale.keys.length,0);
 assert.equal(made.position.keys[0].position.seconds,0);assert.equal(made.position.keys.at(-1).position.seconds,1.2);
 assert.ok(made.position.keys[0].value.y > made.position.keys.at(-1).value.y);
 assert.equal(made.position.keys.at(-1).value.y,540);assert.equal(made.opacity.keys.at(-1).value,100)
});
test('zoom uses native scale and opacity, not Position',async()=>{
 const {ppro,made}=mockPpro();const r=await native.applySelected(ppro,{preset:'zoom-in',samples:9,duration:1.0});
 assert.deepEqual(r.channels,['scale','opacity']);assert.equal(made.scale.keys.length,9);assert.equal(made.position.keys.length,0);
 assert.equal(made.scale.keys.at(-1).value,100)
});
test('protects existing keyframes instead of overwriting',async()=>{
 const {ppro,made}=mockPpro({existing:true});await assert.rejects(native.applySelected(ppro,{preset:'fade-in'}),/Existing keyframes/);
 assert.equal(made.opacity.keys.length,1)
});
test('rejects missing necessary opacity for fade',async()=>{
 const {ppro}=mockPpro({missing:'opacity'});await assert.rejects(native.applySelected(ppro,{preset:'fade-in'}),/No matching|unavailable/)
});
test('refuses duration longer than selected clip',async()=>{
 const {ppro}=mockPpro({clipDuration:.6});await assert.rejects(native.applySelected(ppro,{preset:'slide-up',duration:1.2}),/longer/)
});
test('requires single selected video/graphic item',async()=>{
 const {ppro}=mockPpro({selectionCount:2});await assert.rejects(native.applySelected(ppro,{preset:'slide-up'}),/exactly one/)
});
test('normalized PointF positions are translated relative to normalized frame',async()=>{
 const {ppro,made}=mockPpro();made.position.base=[.5,.5];
 const param=made.position;param.getStartValue=async()=>({value:{value:[.5,.5]}});
 await native.applySelected(ppro,{preset:'slide-right'});
 assert.ok(param.keys[0].value.x<.5 && param.keys[0].value.x>-.1);
 assert.ok(Math.abs(param.keys.at(-1).value.x-.5)<.00001)
});
test('presets can be recognized and param names mapped',async()=>{
 const {ppro}=mockPpro();const info=await native.scanSelected(ppro);const m=native.suggest(info.params);
 assert.deepEqual(Object.keys(m),['position','scale','opacity','rotation'])
});

test('creator punch-in creates held native Scale keyframes without altering text or opacity',async()=>{
 const {ppro,made}=mockPpro();const r=await native.applySelected(ppro,{preset:'creator-punch-in',samples:21,duration:1.4});
 assert.deepEqual(r.channels,['scale']);assert.equal(made.scale.keys.length,21);
 assert.equal(made.scale.keys[0].value,100);assert.ok(made.scale.keys[7].value>111);
 assert.ok(made.scale.keys.at(-1).value>=115);assert.equal(made.opacity.keys.length,0)
});
test('creator snap zoom has zoom in and out and stays near base',()=>{
 const at=[0,.15,.3,.7,1].map(t=>native.valuesAt('creator-snap-zoom',t).scale);
 assert.ok(at[1]>at[0]);assert.ok(at[2]>at[0]);assert.ok(at.at(-1)-1<.00001)
});
