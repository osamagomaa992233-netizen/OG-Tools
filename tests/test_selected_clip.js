const {test}=require('node:test'),assert=require('node:assert/strict');
const select=require('../plugin/native/selection.js');
function fake({two=false,wrong=false,speed=1}={}){
 const item=(path)=>({getProjectItem:async()=>({getMediaFilePath:async()=>path}),getStartTime:async()=>({seconds:10}),getInPoint:async()=>({seconds:2}),getOutPoint:async()=>({seconds:5}),getSpeed:async()=>speed,getName:async()=> 'A1 voice'});
 const items=[item('C:/AUDIO/sample.wav')];if(two)items.push(item(wrong?'D:/other.wav':'C:/AUDIO/sample.wav'));
 return {Project:{getActiveProject:async()=>({getActiveSequence:async()=>({getSelection:async()=>({getTrackItems:async()=>items})})})}};
}
test('selects trimmed source and sequence offset',async()=>{const x=await select.resolve(fake());assert.equal(x.path,'C:/AUDIO/sample.wav');assert.equal(x.start,2);assert.equal(x.end,5);assert.equal(x.offset,10)});
test('allows matching linked video/audio pair',async()=>{const x=await select.resolve(fake({two:true}));assert.equal(x.end,5)});
test('rejects different selected source paths',async()=>{await assert.rejects(select.resolve(fake({two:true,wrong:true})),/matching linked/)});
test('rejects pre-retimed clip, avoids caption drift',async()=>{await assert.rejects(select.resolve(fake({speed:1.5})),/altered playback speed/)});
