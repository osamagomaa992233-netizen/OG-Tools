import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from engine import media,extras,visuals,motion
from engine.core import TOOLS,execute

class TestCore(unittest.TestCase):
 def test_24_modules(self):
  self.assertEqual(len(TOOLS),24)
  self.assertEqual(len(set(v['id'] for v in TOOLS)),24)
  self.assertEqual(len(motion.MOTIONS),30)
  self.assertEqual(len(visuals.STYLES),12)
  self.assertEqual(len(media.SFX_TYPES),12)
  self.assertEqual(len(media.XFADE_TYPES),16)
  self.assertEqual(len(visuals.ICONS),22)
 def test_srt_time(self):self.assertEqual(extras.srt_seconds(3661.234),'01:01:01,234')
 def test_srt_format(self):
  with tempfile.TemporaryDirectory() as t:
   src=Path(t)/'a.srt';out=Path(t)/'clean.srt'
   src.write_text('1\n00:00:01,000 --> 00:00:02,000\nمرحبا هذا اختبار الكابشن العربي والمحتوى\n',encoding='utf-8')
   result=extras.format_srt(src,out,18)
   self.assertEqual(result['lines'],1);self.assertIn('مرحبا',out.read_text(encoding='utf-8-sig'))
 def test_silence_parse_and_merge(self):
  log='[silencedetect] silence_start: 1.2\n[silencedetect] silence_end: 2.5 | silence_duration: 1.3\n[silencedetect] silence_start: 8.0'
  self.assertEqual(media.parse_silence(log,10),[[1.2,2.5],[8.0,10]])
  self.assertEqual(media.complement_intervals([[1,2],[3,4]],5,.1),[[0,1.1],[1.9,3.1],[3.9,5]])
 def test_safe_guides(self):
  with tempfile.TemporaryDirectory() as t:
   result=visuals.guide_overlay(Path(t)/'safe.png','reels')
   self.assertEqual((result['safe_top'],result['safe_bottom']),(235,320))
   with Image.open(result['output']) as im: self.assertEqual(im.size,(1080,1920))
 def test_title_png_arabic(self):
  with tempfile.TemporaryDirectory() as t:
   out=Path(t)/'title.png'
   visual=visuals.title_png('أهلاً بالعالم',out,width=420,height=260,size=52,style='plum')
   self.assertGreater(Image.open(visual['output']).getbbox()[2],100)
 def test_motion_examples(self):
  for t in ('أهلا يا مصر','HELLO WORLD'):
   for m in ('slide-up','typewriter','bounce','letter-rise','reveal-right'):
    img=motion.frame(t,m,.64,440,250,34,style='editorial')
    self.assertTrue(img.getbbox(),(t,m))
 def test_easing(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'easing.csv'
   self.assertEqual(extras.easing_csv(p,'ease-out-elastic',20)['samples'],21)
   self.assertEqual(len(p.read_text().splitlines()),22)
 def test_organizer_copy_without_mutation(self):
  with tempfile.TemporaryDirectory() as t:
   source=Path(t)/'in';dest=Path(t)/'out';source.mkdir()
   f=source/'hello.mp4';f.write_bytes(b'fake')
   dry=extras.organizer(source,dest)
   self.assertFalse(dry['copied']);self.assertFalse(dest.exists())
   copied=extras.organizer(source,dest,apply=True)
   self.assertTrue((dest/'Video'/'hello.mp4').exists());self.assertEqual(f.read_bytes(),b'fake')
 def test_icons(self):
  import xml.etree.ElementTree as ET
  with tempfile.TemporaryDirectory() as t:
   for icon in visuals.ICONS:
    p=Path(t)/(icon+'.svg');visuals.icon_export(icon,p)
    self.assertEqual(ET.parse(p).getroot().tag,'{http://www.w3.org/2000/svg}svg')
 def test_sfx_wav(self):
  import wave
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'sfx.wav';media.sfx(p,'whoosh',.2)
   with wave.open(str(p),'rb') as f:
    self.assertEqual(f.getnchannels(),1);self.assertGreater(f.getnframes(),4000)
 def test_extruded_text_and_arabic_arc(self):
  with tempfile.TemporaryDirectory() as t:
   path3d=Path(t)/'3d.png';arcp=Path(t)/'arc.png'
   visuals.extruded_text('OG TOOLS',path3d,width=480,height=240,size=70)
   visuals.arc_text('كلام بالعربي',arcp,width=480,height=240,size=41)
   with Image.open(path3d) as im:self.assertTrue(im.getbbox())
   with Image.open(arcp) as im:self.assertTrue(im.getbbox())
 def test_default_output_unique(self):
  from engine.core import output_path
  with tempfile.TemporaryDirectory() as t:
   source=Path(t)/'original.mp4';source.write_bytes(b'abc')
   a=Path(output_path(source,'silence','.mp4'));a.write_bytes(b'xyz')
   b=Path(output_path(source,'silence','.mp4'))
   self.assertNotEqual(a,b)
 def test_invalid_jobs(self):
  with self.assertRaises(NotImplementedError):execute({'tool':'web-assets'})
  with self.assertRaises(ValueError):execute({'tool':'bad'})
  with self.assertRaises(RuntimeError):media.render_intervals(__file__,__file__,[[0,2]])

if __name__=='__main__':unittest.main()
