import json
import shutil
import tempfile
import unittest
from pathlib import Path
from PIL import Image,ImageDraw
from engine import media,visuals,motion,extras

FFMPEG=bool(shutil.which('ffmpeg') and shutil.which('ffprobe'))

@unittest.skipUnless(FFMPEG,'FFmpeg is not installed')
class TestMedia(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.t=tempfile.TemporaryDirectory(prefix='og-media-test-')
  cls.root=Path(cls.t.name)
  cls.src=cls.root/'sample.mp4'
  # 3-second video with 1s speech-like tone, 1s silence, 1s tone.
  media.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i','testsrc2=size=320x180:rate=25:duration=3',
   '-f','lavfi','-i','sine=frequency=550:sample_rate=22050:duration=1',
   '-f','lavfi','-i','anullsrc=r=22050:cl=mono:d=1',
   '-f','lavfi','-i','sine=frequency=660:sample_rate=22050:duration=1',
   '-filter_complex','[1:a][2:a][3:a]concat=n=3:v=0:a=1[a]',
   '-map','0:v','-map','[a]','-t','3','-c:v','libx264','-preset','ultrafast','-c:a','aac',cls.src])
 @classmethod
 def tearDownClass(cls):cls.t.cleanup()
 def test_01_silence_detect_and_render(self):
  result=media.detect_silence(self.src,-32,.3,.08)
  self.assertGreaterEqual(len(result['silence']),1,result)
  target=self.root/'cut.mp4'
  edited=media.remove_silence(self.src,target,-32,.3,.08)
  self.assertTrue(target.is_file())
  self.assertLess(media.probe(target)['duration'],3)
 def test_02_audio_enhance(self):
  out=self.root/'enhanced.wav'
  media.enhance_audio(self.src,out,'voice')
  self.assertGreater(media.probe(out)['duration'],2.9)
 def test_03_speed_ramp(self):
  out=self.root/'ramp.mp4'
  media.make_speed_ramp(self.src,out,[.75,1.8,1.1])
  self.assertTrue(out.is_file())
  self.assertTrue(media.probe(out)['audio'])
 def test_04_transitions(self):
  target=self.root/'transition.mp4'
  media.transition(self.src,self.src,target,'wipeleft',.4,width=320,height=180)
  self.assertTrue(target.is_file())
  self.assertTrue(media.probe(target)['video'])
 def test_05_title_prores_alpha_ar_en(self):
  for text,motion_type,style in [('أهلا','typewriter','plum'),('OG TOOLS','pop','impact')]:
   out=self.root/('ar.mov' if text=='أهلا' else 'en.mov')
   motion.render(text,out,motion_type,width=320,height=180,fps=10,duration=.4,size=37,style=style)
   details=media.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=pix_fmt','-of','default=nw=1',out]).stdout
   self.assertIn('yuva',details)
 def test_06_carousel(self):
  paths=[]
  for i in range(2):
   p=self.root/f'slide{i}.png';Image.new('RGB',(320,180),(i*80+80,80,135)).save(p);paths.append(p)
  target=self.root/'carousel.mp4'
  visuals.carousel(paths,target,width=320,height=180,slide_duration=.5,fps=10)
  self.assertTrue(target.is_file())
 def test_07_draw_overlay(self):
  output=self.root/'draw.mov'
  visuals.draw_overlay(output,320,180,fps=10,duration=.4,shape='arrow')
  self.assertIn('yuva',media.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=pix_fmt','-of','default=nw=1',output]).stdout)

if __name__=='__main__':unittest.main()
