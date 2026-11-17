#!/usr/bin/env python3
import sys
import random
import os
import argparse
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf"

d = Path("/".join(__file__.split("/")[:-1]))


pixels_per_mm = 128/18
#pixels_per_mm = 7.24
print_head_pixels = 128

HEIGHT18 = 120
HEIGHT12 = 76
HEIGHT = HEIGHT18

inf = float("inf")


def dottedborder(image, x, span=4):
	pixels = image.load()
	for y in range(0, image.size[1], 3):
		pixels[x,y] = 0

def create_label(textarr, sticker_width, sticker_height, font_size, spacing, print_head_pixels, line_margin=0, draw_box=True):
	num_labels = len(textarr)
	height_margin = (sticker_height-font_size)/2
	font = ImageFont.truetype(font_path, size=font_size)
	image = Image.new(mode="1", size=(int(sticker_width), int(int((sticker_height+spacing)*num_labels-2*spacing))), color=(1))
	draw = ImageDraw.Draw(image)
	for label_id in range(num_labels):
		input_text = textarr[label_id]
		#if args.endash: input_text = input_text.replace("-", "−") # emdash: —, endash: –, heavy (does not work with this font): ➖
		bbox = draw.textbbox((0,0), input_text, font=font)
		height = bbox[2]
		width = bbox[3]
		if(sticker_width-height < 0):
			print(f"WARNING: text of label {label_id} ({input_text.strip()}) is too long")
		y1 = label_id*(sticker_height+spacing)
		if label_id > 0:
			y1 = y1-spacing
		y2 = y1+sticker_height
		draw.text((int((sticker_width-height)/2), int(y1+height_margin)), input_text, font=font)
		if draw_box:
			draw.line([(int(line_margin), int(y1)), (int(sticker_width-line_margin-1), int(y1))], width=1, fill=(0))
			draw.line([(int(line_margin), int(y2)), (int(sticker_width-line_margin-1), int(y2))], width=1, fill=(0))
		
	#draw.line([(int(line_margin), 0), (int(line_margin), image.size[1])], width=1, fill=(0))
	#draw.line([(int(sticker_width-line_margin-1), 0), (int(sticker_width-line_margin-1), image.size[1])], width=1, fill=(0))
	dottedborder(image, int(line_margin))
	dottedborder(image, int(sticker_width-line_margin-1))
	image = image.rotate(90, expand=True)
	new_image = Image.new(mode="1", size=(image.size[0], print_head_pixels), color=(1))
	Image.Image.paste(new_image, image, (0, int((print_head_pixels-image.size[1])/2)))

	# if there is one line only 1px thick, make it 2px thick - mostly I and P letters are dufficult to print and read if they are only 1px thick
	#if args.profile == "cable_label":
	#	pixels = new_image.load()
	#	for col in range(new_image.size[0]):
	#		for row in range(1, new_image.size[1]-1):
	#			if pixels[col,row-1] == 1 and pixels[col,row] == 0 and pixels[col,row+1] == 1:
	#				pixels[col,row-1] = 0

def _getch(*question):
    import tty, termios
    print(*question, end="", flush=True)
    fd = sys.stdin.fileno()
    oldSettings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        answer = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, oldSettings)
    print()
    return answer

def to_size(img, width, height=HEIGHT):
    if not hasattr(width, '__len__'): width = width,width
    if not hasattr(height, '__len__'): height = height,height

    new_width = max(width[0], img.width)
    new_height = max(height[0], img.height)

    assert new_width <= width[1], f"Image width is {new_width}, but should be under {width[1]}"
    assert new_height <= height[1], f"Image height is {new_height}, but should be under {height[1]}"

    new_image = Image.new("1", (new_width, new_height), (1))

    new_image.paste(img, ((new_width-img.width)//2, (new_height-img.height)//2))

    return new_image

def label12(img):
    return label(img, height=HEIGHT12)
def label(img, height=HEIGHT):
    min_width = 140

    print(f"Original size  {img.width}x{img.height} pt = {img.width//pixels_per_mm/10}x{img.height//pixels_per_mm/10} cm")

    img = to_size(hbox(img, hskip(2)), (min_width, inf), height)
    assert img.height <= HEIGHT, img.height
    print(f"Printing label {img.width}x{img.height} pt = {img.width//pixels_per_mm/10}x{img.height//pixels_per_mm/10} cm")




    file=f"/tmp/label-{random.randrange(1000)}.png"
    img.save(file)

    import subprocess
    subprocess.run(["feh", file])

    while True:
        x = _getch(f"Saved as {file}. Print? (yes/No/repeat/edit/quit): ")
        if x=="y" or x=="r":
            if img.width//pixels_per_mm > 50:
                confirm_ok = str(int(img.width//pixels_per_mm//10))
                while True:
                    print(f"Long label. Write '{confirm_ok}' co continue: ", end='', flush=True)
                    inp = input()
                    if inp == confirm_ok: break
            print("Printing")
            p = subprocess.run(["root", "ptouch-print", "--chain", "--image", file])
            if p.returncode:
                continue
        if x=="e":
            exit(42)
        if x=="q":
            exit(0)
        if x!="r": break



image = Image.new(mode="1", size=(200, 120), color=(1))
font = ImageFont.truetype(font_path, size=50)
draw = ImageDraw.Draw(image)

class BitmapFont:
    """X bitmap font (PCF, BDF, OTB) made of one or more files, one file per
    pixel size, e.g. BitmapFont("/usr/share/fonts/misc/ter-x*b.pcf.gz").

    Glyphs are drawn pixel for pixel, so they stay sharp and symmetric.
    By default only the sizes stored in the files can be used, anything else
    is an error. Options (defaults for this font, text() can override them):
      scale     – allow integer multiples of the sizes (blockier);
                  True = any multiple, a number = at most that multiple
      tolerance – if the size is not available, use the closest available one
                  within this fraction of it (e.g. 0.15 = ±15 %)
      stretch   – as a last resort, enlarge the nearest smaller size by
                  a non-integer factor to exactly font_size (uneven strokes)
      outline   – path to a vector font (OTF/TTF) used instead for sizes
                  >= outline_min which are not native strikes; it takes
                  precedence over scale / tolerance / stretch"""

    def __init__(self, *patterns, scale=False, tolerance=0, stretch=False, outline=None, outline_min=30):
        import glob
        self.scale, self.tolerance, self.stretch = scale, tolerance, stretch
        self.outline, self.outline_min = outline, outline_min
        self.strikes = {}
        for pattern in patterns:
            for path in sorted(glob.glob(os.path.expanduser(str(pattern)))):
                for size in self._sizes(path):
                    self.strikes.setdefault(size, path)
        if not self.strikes:
            raise FileNotFoundError(f"No bitmap font found for {patterns}")

    @staticmethod
    def _sizes(path):
        # FreeType accepts only the pixel sizes stored in the file
        sizes = []
        for size in range(1, 129):
            try:
                ImageFont.truetype(path, size=size)
                sizes.append(size)
            except OSError:
                pass
        return sizes

    def sizes(self, scale=False, limit=HEIGHT):
        """Available font sizes; with scale also integer multiples up to limit
        (scale=N: at most N times)."""
        if not scale:
            return sorted(self.strikes)
        max_k = inf if scale is True else int(scale)
        return sorted({s*k for s in self.strikes for k in range(1, limit // s + 1) if k <= max_k})

    def pick(self, font_size, scale=None, tolerance=None, stretch=None):
        """Return (ImageFont, factor) for font_size: a native strike; else the
        outline font for big sizes; else with scale strike*k (scale=True any k,
        scale=N at most N), exactly or within tolerance, using the smallest k
        (= the most detailed strike); else with stretch a non-integer factor.
        Otherwise ValueError."""
        if font_size not in self.strikes and self.outline and font_size >= self.outline_min:
            return ImageFont.truetype(self.outline, size=font_size), 1
        scale = self.scale if scale is None else scale
        tolerance = self.tolerance if tolerance is None else tolerance
        stretch = self.stretch if stretch is None else stretch
        max_k = 1 if not scale else font_size if scale is True else int(scale)

        # (strike, k) within tolerance (0 = exact); the smallest k wins, then
        # the closest size, then the smaller one
        dist = lambda c: abs(c[0]*c[1] - font_size)
        candidates = [(s, k) for s in self.strikes for k in range(1, max_k + 1)
                      if dist((s, k)) <= tolerance * font_size]
        found = min(candidates, key=lambda c: (c[1], dist(c), c[0]*c[1]), default=None)
        if not found and stretch:
            below = [s for s in self.strikes if s <= font_size]
            size = max(below) if below else min(self.strikes)
            found = size, font_size / size
        if not found:
            raise ValueError(
                f"Font size {font_size} is not available; native sizes: {self.sizes()}"
                + ("" if scale else f"; with scale=True also: {sorted(set(self.sizes(True)) - set(self.sizes()))}")
                + "; or allow tolerance=0.15 / stretch=True"
                + (f"; outline font from size {self.outline_min}" if self.outline else ""))
        size, factor = found
        return ImageFont.truetype(self.strikes[size], size=size), factor

    def __repr__(self):
        outline = f", outline={self.outline!r} from {self.outline_min}" if self.outline else ""
        return f"BitmapFont({sorted(self.strikes)}{outline})"


def terminus(bold=True, **options):
    """Terminus bitmap font (packages terminus-font / xfonts-terminus);
    options as in BitmapFont (scale, tolerance, stretch)."""
    w = "b" if bold else "n"
    dirs = ["/usr/share/fonts/misc", "/usr/share/fonts/X11/misc",
            "/usr/share/fonts/terminus", "~/.local/share/fonts", "~/.fonts"]
    names = [f"ter-u*{w}.otb", f"ter-x*{w}.pcf.gz", f"ter-u*{w}_unicode.pcf.gz", f"ter-u*{w}.pcf.gz"]
    try:
        return BitmapFont(*(f"{dir}/{name}" for dir in dirs for name in names), **options)
    except FileNotFoundError:
        raise FileNotFoundError("Terminus font not found (install terminus-font / xfonts-terminus)") from None


def xfont(name, **options):
    """Proportional X core font from xorg-fonts-75dpi/100dpi (Debian:
    xfonts-75dpi/100dpi), both resolutions merged into one BitmapFont;
    options as in BitmapFont (scale, tolerance, stretch).
    With Czech: helvB/helvR (Helvetica), luBS/luRS (Lucida Sans),
    lubB/lubR (Lucida Bright), timB/timR (Times), ncenB/ncenR, UTB___/UTRG__."""
    dirs = ["/usr/share/fonts/100dpi", "/usr/share/fonts/75dpi",
            "/usr/share/fonts/X11/100dpi", "/usr/share/fonts/X11/75dpi"]
    try:
        return BitmapFont(*(f"{dir}/{name}[0-9][0-9].pcf.gz" for dir in dirs), **options)
    except FileNotFoundError:
        raise FileNotFoundError(f"X font {name} not found (install xorg-fonts-75dpi xorg-fonts-100dpi)") from None


def nimbus_sans(style="Bold"):
    """Path to URW Nimbus Sans (Helvetica clone, same metrics as the X helv
    bitmaps): packages gsfonts / fonts-urw-base35."""
    import glob
    dirs = ["/usr/share/fonts/gsfonts", "/usr/share/fonts/urw-base35",
            "/usr/share/fonts/opentype/urw-base35", "/usr/share/fonts/type1/urw-base35"]
    for dir in dirs:
        found = sorted(glob.glob(f"{dir}/NimbusSans-{style}.otf"))
        if found:
            return found[0]
    raise FileNotFoundError(f"Nimbus Sans {style} not found (install gsfonts / fonts-urw-base35)")


# Helvetica bitmaps, Nimbus Sans for bigger sizes without a bitmap; loaded lazily on first use
default_font = lambda: xfont("helvB", outline=nimbus_sans("Bold"))

def use_font(font):
    """Set the font used by text() when no font is given: a BitmapFont,
    a path to a TrueType font, or None for the TrueType font_path."""
    global default_font
    default_font = font

def get_default_font():
    global default_font
    if callable(default_font):
        default_font = default_font()
    return default_font


def _bitmap_width(f, t):
    return max(int(f.getlength(t)), f.getbbox(t, anchor='ls')[2], 1)


def bitmap_text(t, font_size, down, font, **options):
    f, factor = font.pick(font_size, **options)
    ascent, descent = f.getmetrics()
    ascent = max(ascent, -f.getbbox(t, anchor='ls')[1])  # accents on capitals may exceed the ascent
    image = Image.new(mode="1", size=(_bitmap_width(f, t), ascent + (descent if down else 1)), color=(1))
    ImageDraw.Draw(image).text((0, ascent), t, font=f, anchor='ls')
    kind = "outline" if f.path == font.outline else "bitmap"
    print(t, font_size, f"{kind} {f.size}px x{factor:g}")
    return image.resize((round(image.width*factor), round(image.height*factor)), Image.NEAREST)


def text_width(t, font_size=20, font=None, scale=None, tolerance=None, stretch=None):
    """Width of t in pixels as text() would draw it, without drawing it."""
    font = font or get_default_font()
    if isinstance(font, BitmapFont):
        f, factor = font.pick(font_size, scale, tolerance, stretch)
        return round(_bitmap_width(f, t) * factor)
    return ImageFont.truetype(font or font_path, size=font_size).getlength(t)


def text(t, font_size=20, down=True, font=None, scale=None, tolerance=None, stretch=None):
    """Text image. With a BitmapFont, font_size must be one of its sizes,
    unless scale / tolerance / stretch allow otherwise (see BitmapFont;
    None = the font's own setting)."""
    font = font or get_default_font()
    if isinstance(font, BitmapFont):
        return bitmap_text(t, font_size, down, font, scale=scale, tolerance=tolerance, stretch=stretch)
    font = ImageFont.truetype(font or font_path, size=font_size)
    image = Image.new(mode="1", size=(100,100), color=(1))
    draw = ImageDraw.Draw(image)
    bbox = draw.textbbox((0,0), t, font=font, anchor='ls')
    print(t, font_size, bbox, (bbox[2], -bbox[1]+bbox[3]))
    up_size = font_size * 7 // 9 + 1
    down_size = font_size * 2 // 9 + 1 if down else 1
    #image = Image.new(mode="1", size=(bbox[2], -bbox[1]+bbox[3]), color=(1))
    image = Image.new(mode="1", size=(bbox[2], up_size+down_size), color=(1))
    draw = ImageDraw.Draw(image)
    draw.text((0,up_size), t, font=font, anchor='ls')
    return image

def texts(t, font_size=20, down=True, split_after=None, font=None, **options):
    """Like text(), but returns a list of images instead of one, ready to be
    re-flowed with multiline() / multilinev().

    Splitting: by default on every run of whitespace (word by word). If
    split_after is given, the text is instead split after each of those
    characters, keeping the delimiter attached to the preceding chunk
    (e.g. split_after="," turns "a, b, c" into "a,", "b,", "c").

    Each chunk is rendered with a trailing space so neighbouring chunks that
    end up on the same line don't touch."""
    if split_after:
        parts, cur = [], ""
        for ch in t:
            cur += ch
            if ch in split_after:
                parts.append(cur)
                cur = ""
        if cur:
            parts.append(cur)
    else:
        parts = t.split()
    parts = [p.strip() for p in parts]
    parts = [p for p in parts if p]
    return [text(p + " ", font_size, down, font, **options) for p in parts]

from PIL import Image

def vbox(*images, align='c'):
    # Normalize alignment string
    if len(align) == 1:
        align = align * len(images)
    elif len(align) != len(images):
        raise ValueError("Alignment string must match number of images")

    valid_aligns = {'l', 'c', 'r'}
    if any(a not in valid_aligns for a in align):
        raise ValueError("Alignment must contain only 'l', 'c', or 'r'")

    max_width = max(img.width for img in images)
    total_height = sum(img.height for img in images)

    # White background
    combined = Image.new("1", (max_width, total_height), (1))

    y_offset = 0
    for img, a in zip(images, align):
        if a == 'l':
            x_offset = 0
        elif a == 'r':
            x_offset = max_width - img.width
        else:  # center
            x_offset = (max_width - img.width) // 2

        combined.paste(img, (x_offset, y_offset))
        y_offset += img.height

    return combined

def hbox(*images, align='b'):
    # Normalize alignment string
    if len(align) == 1:
        align = align * len(images)
    elif len(align) != len(images):
        raise ValueError("Alignment string must match number of images")

    valid_aligns = {'t', 'c', 'b'}
    if any(a not in valid_aligns for a in align):
        raise ValueError("Alignment must contain only 't', 'c', or 'b'")

    max_height = max(img.height for img in images)
    total_width = sum(img.width for img in images)

    # White background
    combined = Image.new("1", (total_width, max_height), (1))

    x_offset = 0
    for img, a in zip(images, align):
        if a == 't':
            y_offset = 0
        elif a == 'b':
            y_offset = max_height - img.height
        else:  # center
            y_offset = (max_height - img.height) // 2

        combined.paste(img, (x_offset, y_offset))
        x_offset += img.width

    return combined

def vskip(pt):
    return Image.new("1", (1, pt), (1))

def hskip(pt):
    return Image.new("1", (pt, 1), (1))

def black(x,y):
    return Image.new("1", (x, y), (0))





def machine(name, subdomain, domain, ip, mac1, mac2=None):
    k = 2
    small = 17  # 8*k=16 is not a native size; nearest native is 17
    header_block = \
        hbox(
            text(name, 32*k),
            vbox(
                text(subdomain, 18*k),
                vskip(1),
                text(domain, small),
                vskip((32*k-8*k)*2//9 - 1),  # -1: size 17 is 1px taller than 16 was
                align='l'
            )
        )
    if mac2 is None:
        return \
                vbox(
                    header_block,
                    vskip(2),
                    text(ip, 12*k, down=False),
                    vskip(6),
                    text(mac1, small, down=False),
                    vskip(9),
                )
    else:
        return \
                vbox(
                    header_block,
                    text(ip, 12*k, down=False),
                    vskip(1),
                    text(mac1, small, down=False),
                    vskip(1),
                    text(mac2, small, down=False),
                )

def network_card_with_speed(speed, *args):
    return hbox(
        machine(*args),
        hskip(3), black(1, 120),hskip(3),
        text("2.5", 60),
        vbox(text("Gb"), black(25,1), text("s")),
        align="c"
    )

def flash():
    from PIL import Image, ImageDraw
    return Image.open(d/"img"/"electric.png").convert('1')

def multiline(data, size):
    out = []
    current = []
    for x in data:
        if hbox(*current, x).width > size:
            out.append(hbox(*current))
            current = []
        current.append(x)
    if current:
        out.append(hbox(*current))
    return out


def multilinev(data, max_lines, align='c', box=True, gap=0):
    """Break a sequence of images into at most max_lines lines, choosing the
    smallest possible line width so the result is as narrow/even as possible.

    Objects keep their order (each line is a contiguous run) and are grouped
    with hbox. By default the lines are stacked with vbox and a single image is
    returned; pass box=False to get the raw list of per-line hboxes instead.
    gap adds that many pixels of vertical space between the lines."""
    data = list(data)
    if not data:
        return Image.new("1", (1, 1), (1)) if box else []
    widths = [x.width for x in data]

    def lines_needed(limit):
        # greedy pack into lines of width <= limit; inf if a single item is too wide
        count, cur = 1, 0
        for w in widths:
            if w > limit:
                return inf
            if cur and cur + w > limit:
                count += 1
                cur = w
            else:
                cur += w
        return count

    # smallest max-line-width that still keeps us within max_lines lines
    lo, hi = max(widths), sum(widths)
    while lo < hi:
        mid = (lo + hi) // 2
        if lines_needed(mid) <= max_lines:
            hi = mid
        else:
            lo = mid + 1

    lines = multiline(data, lo)
    if not box:
        return lines
    if gap:
        spaced = []
        for i, line in enumerate(lines):
            if i:
                spaced.append(vskip(gap))
            spaced.append(line)
        return vbox(*spaced, align=align)
    return vbox(*lines, align=align)


def net_switch(ports, port_order, port_size, big_vlans=False):
    out = []
    for i in port_order:
        p = ports[i]
        vlan_data = []
        vlan_data_long = []
        for vlan in p.vlans:
            vlan_data += [text(str(vlan.id), down=False, font_size=(20 if big_vlans else 15) if vlan.tag else (35 if big_vlans else 29)), hskip(5 if big_vlans else 4)]
            vlan_data_long += [
                    text(str(vlan.id), font_size=(20 if big_vlans else 15) if vlan.tag else (35 if big_vlans else 30)),
                    text(f"({vlan.name})"),
                    hskip(5 if big_vlans else 4),
            ]
        vlan_data = vlan_data[:-1]
        vlan_data_long = vlan_data_long[:-1]
        vlan_box = vbox(*multiline(vlan_data, port_size-1)) if hbox(*vlan_data_long).width > port_size-1 else hbox(*vlan_data_long)
        pair_box = vbox(*(text(pair.strip(), 20) for pair in str(p.pair).split("->")))
        vlan_box = to_size(vlan_box, port_size-1, (30, 80))
        pair_box = to_size(pair_box, port_size-1, (35, 80))
        port_box = vbox(
                vlan_box,
                vskip(HEIGHT - vlan_box.height - pair_box.height),
                pair_box,
                )
        out += [to_size(port_box , port_size-1, HEIGHT), black(1, HEIGHT)]
    return hbox(*out[:-1])

def poe(s, flash_count=1):
    return vbox(
            hbox(*(flash()  for _ in range(flash_count))),
            text(s, 30),
        )

poe_12p = lambda: poe("12V pPoE", flash_count=1)
poe_24p = lambda: poe("24V pPoE", flash_count=2)
poe_48p = lambda: poe("48V pPoE", flash_count=3)

def utp_label(left, right=None):
    if not right: right=left
    label(hbox(
        left,
        hskip(4),
        black(1, HEIGHT),
        hskip(int(7.5*pixels_per_mm)),
        black(1, HEIGHT),
        hskip(int(7.5*pixels_per_mm)),
        black(1, HEIGHT),
        hskip(4),
        right
    ))


def jk():
    return text('JK', 110)
def jk12():
    return text('JK', 75)

def majetek_jk():
    return vbox(text("majetek", 30), text('JK', 80))

# label(vbox(
#        text("Krmení pro Bell"),
#        text("2 porce, jeden den"),
#        hbox(text("320", 75), text("g", 40))
#))

def DS18B20_label(left, right=None):
    if not right: right=left
    label(hbox(
        left,
        hskip(4),
        black(1, HEIGHT),
        hskip(int(6*pixels_per_mm)),
        black(1, HEIGHT),
        hskip(int(6*pixels_per_mm)),
        black(1, HEIGHT),
        hskip(4),
        right
    ))

def DS18B20(id, name, text_size=60):
    DS18B20_label(vbox(text(name, text_size), vskip(70- text_size), text(id, 25)))

