"""Original 2026 creator-caption motion presets for OG Tools.

Exports ASS events with word-level timing. This does NOT claim to generate
Premiere-native editable text keyframes or to contain third-party templates.
All looks are independently authored and are suitable for RTL/Arabic text.
"""
from __future__ import annotations
import math

PRESETS = {
    'active-spotlight': 'A full phrase; the spoken word lights up',
    'karaoke-trace': 'Continuous color sweep synchronized to words',
    'chip-stack': 'Individual words in editorial opaque chips',
    'hook-slam': 'One oversized punchline word with hard overshoot',
    'marker-glow': 'Highlighted spoken word with controlled luminous edge',
    'stagger-reveal': 'Words build one by one into the full sentence',
    'editorial-rail': 'Quiet left/right-aligned phrase with active accent',
    'boxed-podcast': 'Compact caption card for busy talking-head scenes',
    'micro-jolt': 'One spoken word with a brief rhythmic nudge',
    'contrast-flip': 'Editorial italic word with a fast angle correction',
    'sidecar-note': 'Minimal margin note / educational caption',
    'quiet-cinema': 'Small restrained phrase and an emphasized word',
}


def ass_time(seconds: float) -> str:
    centis = max(0, int(round(float(seconds) * 100)))
    return f'{centis // 360000}:{centis // 6000 % 60:02d}:{centis // 100 % 60:02d}.{centis % 100:02d}'


def ass_color(hex_rgb: str) -> str:
    rgb = str(hex_rgb).lstrip('#')
    if len(rgb) != 6 or any(c not in '0123456789ABCDEFabcdef' for c in rgb):
        raise ValueError('Expected a six-digit hex color')
    return f'&H{rgb[4:6]}{rgb[2:4]}{rgb[0:2]}&'


def safe_text(value: str) -> str:
    return str(value).replace('\\', '\\\\').replace('{', '\\{').replace('}', '\\}').replace('\r', ' ').replace('\n', ' ').replace(',', ',')


def _header(width, height, font, white, accent, background):
    if any(ch in font for ch in ',\r\n'):
        raise ValueError('Invalid font family')
    rgb, key, dark = map(ass_color, (white, accent, background))
    major = max(28, round(width * .124))
    minor = max(20, round(width * .082))
    huge = max(38, round(width * .205))
    format_line = 'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding'
    def style(name, size, primary, secondary, box=False, italic=False, outline=2, edge=None):
        edge = edge or dark
        return f'Style: {name},{font},{size},{primary},{secondary},{edge},&H50000000&,-1,{int(italic)},0,0,100,100,0,0,{3 if box else 1},{outline if not box else 4},0,5,40,40,40,1'
    return '\n'.join([
        '[Script Info]', 'Title: OG Tools original creator caption styles', 'ScriptType: v4.00+',
        'WrapStyle: 2', 'ScaledBorderAndShadow: yes', f'PlayResX: {width}', f'PlayResY: {height}',
        'YCbCr Matrix: TV.709', '', '[V4+ Styles]', format_line,
        style('Bold', major, rgb, key),
        style('Small', minor, rgb, key, outline=1),
        style('Glow', major, key, rgb, outline=3),
        style('Card', major, rgb, key, box=True),
        style('Chip', major, dark, rgb, box=True, edge=key),
        style('Huge', huge, key, rgb),
        style('Italic', major, rgb, key, italic=True),
        style('Karaoke', major, key, rgb),
        '', '[Events]',
        'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text', ''
    ]) + '\n'


def _line(a, b, style, tags, text):
    # ASS tag strings are constructed internally; caller text is escaped.
    return f'Dialogue: 0,{ass_time(a)},{ass_time(b)},{style},,0,0,0,,{{{tags}}}{text}\n'


def generate(groups, style, *, white='F7F5F0', accent='C9F36D', background='191A21',
             width=1080, height=1920, font=None, position=.69):
    """Build safe ASS with karaoke or timed active-word animation.

    `groups` is an iterable of ordered word dicts with start/end/text.
    Call `creator.group_words()` to group and validate raw ASR words first.
    """
    if style not in PRESETS:
        raise ValueError('Unknown creator style')
    if not 320 <= int(width) <= 4320 or not 180 <= int(height) <= 7680:
        raise ValueError('Invalid dimensions')
    if not math.isfinite(float(position)) or not .25 <= float(position) <= .90:
        raise ValueError('Invalid position')
    flat = [word for group in groups for word in group]
    if not flat:
        raise ValueError('No words supplied')
    is_ar = any('\u0600' <= c <= '\u08ff' for word in flat for c in str(word['text']))
    font = font or ('Noto Sans Arabic' if is_ar else 'Montserrat')
    out = [_header(width, height, font, white, accent, background)]
    x = width // 2
    y = round(height * float(position))
    color, marker = ass_color(white), ass_color(accent)
    muted = '&H8B8B8B&'
    # Approximate phrase width in screen px; avoid truncation on vertical video.
    def fit(group, scale=1.0):
        glyphs = sum(0.66 if c.isascii() else 0.68 for item in group for c in str(item['text']))
        glyphs += max(0, len(group)-1) * 0.35
        projected = glyphs * round(width * .124) * scale
        return max(54, min(100, round(100 * width * .83 / max(1.0, projected))))
    for group in groups:
        words = [safe_text(item['text']) for item in group]
        start, stop = float(group[0]['start']), float(group[-1]['end'])
        if not math.isfinite(start) or not math.isfinite(stop) or start < 0 or stop <= start:
            raise ValueError('Invalid timing')
        for idx, word in enumerate(group):
            if float(word['start']) < start or float(word['end']) > stop + .01 or float(word['end']) <= float(word['start']):
                raise ValueError('Invalid word ordering')
        if style == 'karaoke-trace':
            parts = []
            cursor = start
            for word, item in zip(words, group):
                gap = max(0, float(item['start']) - cursor)
                if gap >= .02:
                    parts.append(f'{{\\k{int(round(gap * 100))}}}')
                duration = max(1, int(round((float(item['end']) - float(item['start'])) * 100)))
                parts.append(f'{{\\kf{duration}}}{word}')
                parts.append(' ')
                cursor = float(item['end'])
            tags = f'\\an5\\pos({x},{y})\\fscx{fit(group)}\\c{marker}\\2c{muted}'
            out.append(_line(start, stop, 'Karaoke', tags, ''.join(parts).rstrip()))
            continue
        for idx, item in enumerate(group):
            a = float(item['start'])
            b = float(item['end'])
            if idx < len(group) - 1:
                b = max(b, float(group[idx + 1]['start']))
            if b <= a:
                b = a + .02
            if style == 'stagger-reveal':
                shown = words[:idx + 1]
                shown[-1] = f'{{\\c{marker}\\b1}}{shown[-1]}'
                content = ' '.join(shown)
                target = fit(group[:idx + 1]); initial = max(54, target - 4)
                tags = f'\\an5\\pos({x},{y})\\fad(50,30)\\fscx{initial}\\fscy96\\t(0,130,\\fscx{target}\\fscy100)'
                out.append(_line(a, b, 'Bold', tags, content))
                continue
            if style in ('active-spotlight', 'marker-glow', 'editorial-rail', 'boxed-podcast', 'sidecar-note', 'quiet-cinema'):
                shown = []
                for j, w in enumerate(words):
                    if j == idx:
                        add = f'{{\\c{marker}\\b1}}{w}'
                    else:
                        add = f'{{\\c{muted}\\b0}}{w}'
                    shown.append(add)
                content = ' '.join(shown)
                face = 'Small' if style in ('editorial-rail', 'sidecar-note', 'quiet-cinema') else 'Bold'
                if style == 'editorial-rail':
                    bx = round(width * (.90 if is_ar else .10))
                    tags = f'\\an{6 if is_ar else 4}\\pos({bx},{round(height * .60)})\\fad(50,50)\\fscx{fit(group,.66)}'
                elif style == 'sidecar-note':
                    bx = round(width * (.90 if is_ar else .10))
                    tags = f'\\an{6 if is_ar else 4}\\pos({bx},{round(height * .46)})\\fad(40,40)\\fscx{max(58,fit(group,.66)-6)}\\fscy88'
                elif style == 'marker-glow':
                    tags = f'\\an5\\pos({x},{y})\\bord3\\blur2.5\\fad(35,45)\\fscx{fit(group)}'
                elif style == 'boxed-podcast':
                    tags = f'\\an5\\pos({x},{y})\\bord2\\shad0\\fscx{fit(group)}'
                    face = 'Card'
                elif style == 'quiet-cinema':
                    tags = f'\\an5\\pos({x},{round(height * .72)})\\fad(110,100)\\fscx{fit(group,.66)}\\fscy92'
                else:
                    tags = f'\\an5\\pos({x},{y})\\fad(30,30)\\fscx{fit(group)}'
                out.append(_line(a, b, face, tags, content))
                continue
            if style == 'chip-stack':
                tags = f'\\an5\\pos({x},{y})\\c{ass_color(background)}\\fscx82\\fscy82\\t(0,140,\\fscx100\\fscy100)\\fad(25,50)'
                face = 'Chip'
            elif style == 'hook-slam':
                tags = f'\\an5\\pos({x},{round(height * .52)})\\fscx45\\fscy45\\frz-4\\t(0,100,\\fscx128\\fscy128\\frz2)\\t(100,230,\\fscx100\\fscy100\\frz0)'
                face = 'Huge'
            elif style == 'micro-jolt':
                tags = f'\\an5\\move({x-12},{y+17},{x},{y},0,115)\\fscx87\\fscy87\\t(0,160,\\fscx100\\fscy100)\\c{marker}'
                face = 'Bold'
            else:  # contrast-flip
                tags = f'\\an5\\pos({x},{y})\\frz-9\\fscx114\\fscy114\\t(0,170,\\frz0\\fscx100\\fscy100)\\c{marker}\\fad(40,50)'
                face = 'Italic'
            out.append(_line(a, b, face, tags, words[idx]))
    return ''.join(out)
