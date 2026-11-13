"""Functional tests for independently authored 2026 creator caption presets."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import subprocess
import shutil
import unittest
from engine import creator, trend_text, core

AR = [
    {'start': .10, 'end': .38, 'text': 'إزاي'},
    {'start': .42, 'end': .82, 'text': 'نخلي'},
    {'start': .85, 'end': 1.20, 'text': 'الفيديو'},
    {'start': 1.30, 'end': 1.70, 'text': 'أقوى'},
]
EN = [
    {'start': .10, 'end': .38, 'text': 'YOUR'},
    {'start': .42, 'end': .82, 'text': 'NEXT'},
    {'start': .85, 'end': 1.20, 'text': 'BIG'},
    {'start': 1.30, 'end': 1.70, 'text': 'IDEA'},
]

class CreatorTrendTests(unittest.TestCase):
    def test_inventory_is_exposed_in_creator_engine(self):
        self.assertEqual(len(trend_text.PRESETS), 12)
        self.assertEqual(len(creator.STYLES), 20)
        self.assertTrue(all(style in creator.STYLES for style in trend_text.PRESETS))

    def test_every_template_generates_arabic_and_english(self):
        for wordset in (AR, EN):
            for preset in trend_text.PRESETS:
                with self.subTest(preset=preset, language='ar' if wordset is AR else 'en'):
                    ass = creator.ass_from_groups(creator.group_words(wordset), preset,
                                                   width=540, height=960)
                    self.assertIn('Dialogue:', ass)
                    self.assertIn(wordset[0]['text'], ass)
                    self.assertIn('PlayResY: 960', ass)
                    self.assertTrue(ass.endswith('\n'))

    def test_karaoke_has_word_timing(self):
        ass = creator.ass_from_groups(creator.group_words(AR, max_words=4), 'karaoke-trace')
        self.assertIn('\\kf', ass)
        self.assertEqual(ass.count('Dialogue:'), 1)

    def test_no_hidden_breaking_ass_tags_from_user_text(self):
        sample = [{'start': .1, 'end': .5, 'text': 'hello{\\pos(1,1)}'},
                  {'start': .55, 'end': .9, 'text': 'world'}]
        ass = creator.ass_from_groups(creator.group_words(sample), 'hook-slam')
        self.assertIn('hello\\{\\\\pos(1,1)\\}', ass)

    def test_invalid_parameters_rejected(self):
        groups = creator.group_words(AR)
        with self.assertRaises(ValueError):trend_text.generate(groups, 'unknown')
        with self.assertRaises(ValueError):trend_text.generate(groups, 'hook-slam', font='Bad,Injection')
        with self.assertRaises(ValueError):trend_text.generate(groups, 'hook-slam', width=3)

    def test_tool_dispatch_exports_new_templates(self):
        with TemporaryDirectory() as d:
            out = Path(d) / 'caption.srt'
            response = core.execute({'tool':'creator-captions','source':'unused-source.mp4',
                                     'output':str(out),'words':AR,'caption_style':'hook-slam',
                                     'language':'ar'})
            self.assertEqual(Path(response['ass']).suffix,'.ass')
            self.assertIn('Dialogue:',Path(response['ass']).read_text('utf-8-sig'))
            self.assertTrue(out.exists())
            self.assertEqual(json.loads(Path(response['words_json']).read_text())['style'],'hook-slam')

    @unittest.skipUnless(shutil.which('ffmpeg'), 'ffmpeg not installed')
    def test_libass_renders_arabic_and_english_frames(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            for preset, words in [('hook-slam', AR), ('active-spotlight', EN),('karaoke-trace', AR)]:
                ass=root/(preset+'.ass'); frame=root/(preset+'.png')
                ass.write_text(creator.ass_from_groups(creator.group_words(words,max_words=4),preset,width=480,height=854), encoding='utf-8')
                command=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i',
                         'color=c=#252b34:s=480x854:r=25:d=1','-vf',f'ass={ass}',
                         '-ss','0.6','-frames:v','1',str(frame)]
                subprocess.run(command,check=True,capture_output=True)
                self.assertGreater(frame.stat().st_size,1000)

if __name__ == '__main__':unittest.main()
