import json,math,shutil,tempfile,unittest
from pathlib import Path
from engine import creator,media,core
FF=bool(shutil.which('ffmpeg') and shutil.which('ffprobe'))
SAMPLE=[{'start':.12,'end':.36,'text':'إحنا'},{'start':.37,'end':.68,'text':'بنعمل'},
        {'start':.71,'end':1.02,'text':'فيديوهات'},{'start':1.25,'end':1.56,'text':'احترافية'},
        {'start':1.57,'end':1.86,'text':'دلوقتي'}]
class CreatorPureTests(unittest.TestCase):
 def test_word_groups_ar(self):
  groups=creator.group_words(SAMPLE,max_words=3)
  self.assertEqual(len(groups),2)
  self.assertEqual(groups[0][0]['text'],'إحنا')
 def test_timing_and_sequence_offset(self):
  groups=creator.group_words(SAMPLE)
  txt=creator.srt_from_groups(groups,11.0)
  self.assertIn('00:00:11,120',txt)
  self.assertIn('إحنا',txt)
 def test_styles_generate_ass(self):
  for sty in creator.STYLES:
   ass=creator.ass_from_groups(creator.group_words(SAMPLE),style=sty,width=540,height=960)
   self.assertIn('إحنا',ass)
   self.assertIn('Dialogue:',ass)
 def test_bad_timing(self):
  with self.assertRaises(ValueError):creator.validate_words([{'start':1,'end':0,'text':'x'}])
 def test_ramp_envelope(self):
  for p in creator.RAMP_PRESETS:
   vals=creator.ramp_curve(p,15)
   self.assertEqual(len(vals),15)
   self.assertTrue(all(0.25<x<5 for x in vals))
 def test_captions_package(self):
  with tempfile.TemporaryDirectory() as t:
   res=creator.create_caption_package('',str(Path(t)/'demo.srt'),words=SAMPLE,style='editorial-accent',timeline_offset=4.2)
   self.assertTrue(Path(res['ass']).is_file())
   doc=json.loads(Path(res['words_json']).read_text())
   self.assertAlmostEqual(doc['words'][0]['sequence_start'],4.32)
   self.assertTrue(Path(res['output']).is_file())
 @unittest.skipUnless(FF,'FFmpeg missing')
 def test_real_media_zoom_ramp_and_subtitle(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);src=root/'source.mp4'
   media.run(['ffmpeg','-hide_banner','-loglevel','error','-y',
    '-f','lavfi','-i','testsrc2=size=320x180:rate=25:duration=3',
    '-f','lavfi','-i','sine=frequency=440:sample_rate=16000:duration=3',
    '-c:v','libx264','-preset','ultrafast','-pix_fmt','yuv420p','-c:a','aac',str(src)])
   z=creator.zoom_render(str(src),str(root/'zoom.mp4'),preset='reaction-hit',duration=.45)
   self.assertTrue(media.probe(z['output'])['video'])
   self.assertTrue(media.probe(z['output'])['audio'])
   # 5 sampling chunks; do not confuse approximate ramp with Premiere Time Remapping.
   rr=creator.creator_speed_ramp(str(src),str(root/'ramp.mp4'),preset='whip',steps=5)
   self.assertEqual(len(json.loads(Path(rr['profile']).read_text())['speed_multipliers']),5)
   self.assertTrue(media.probe(rr['output'])['audio'])
   cap=creator.create_caption_package(str(src),str(root/'cap.srt'),words=SAMPLE,style='kinetic-pop',burn=True,width=320,height=180)
   self.assertTrue(Path(cap['preview_mp4']).is_file())
   self.assertTrue(media.probe(cap['preview_mp4'])['video'])
if __name__=='__main__':unittest.main()

@unittest.skipUnless(FF,'FFmpeg missing')
class SelectedAudioClipTests(unittest.TestCase):
 def test_selected_cut_exact_trim_and_timeline_time(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);src=r/'source.wav'
   media.run(['ffmpeg','-hide_banner','-loglevel','error','-y',
    '-f','lavfi','-i','sine=frequency=500:sample_rate=16000:duration=1',
    '-f','lavfi','-i','anullsrc=r=16000:cl=mono:d=1',
    '-f','lavfi','-i','sine=frequency=660:sample_rate=16000:duration=1',
    '-filter_complex','[0:a][1:a][2:a]concat=n=3:v=0:a=1[a]',
    '-map','[a]','-c:a','pcm_s16le',str(src)])
   data=creator.selected_silence(str(src),str(r/'plan.json'),noise=-32,minimum=.3,padding=.03,
       start=.4,end=2.6,timeline_offset=8,analyze_only=True)
   self.assertGreater(data['removed_seconds'],.7)
   self.assertAlmostEqual(data['keep_sequence_before_ripple'][0][0],8,delta=.03)
   self.assertAlmostEqual(data['keep_source'][0][0],.4,delta=.03)
   output=creator.selected_silence(str(src),str(r/'cut.wav'),start=.4,end=2.6,noise=-32,
                       minimum=.3,padding=.03,timeline_offset=8)
   self.assertLess(media.probe(output['output'])['duration'],2)
