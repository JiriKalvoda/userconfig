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
print_head_pixels = 128

HEIGHT = 120

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

def label(img):
    min_width = 140

    print(f"Original size  {img.width}x{img.height} pt = {img.width//pixels_per_mm/10}x{img.height//pixels_per_mm/10} cm")

    img = to_size(img, (min_width, inf), HEIGHT)
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

def text(t, font_size=20, down=True):
    font = ImageFont.truetype(font_path, size=font_size)
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
    header_block = \
        hbox(
            text(name, 32*k),
            vbox(
                text(subdomain, 18*k),
                vskip(1),
                text(domain, 8*k),
                vskip((32*k-8*k)*2//9),
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
                    text(mac1, 8*k, down=False),
                    vskip(9),
                )
    else:
        return \
                vbox(
                    header_block,
                    text(ip, 12*k, down=False),
                    vskip(2),
                    text(mac1, 8*k, down=False),
                    vskip(2),
                    text(mac2, 8*k, down=False),
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

# label(vbox(
#        text("Krmení pro Bell"),
#        text("2 porce, jeden den"),
#        hbox(text("320", 75), text("g", 40))
#))


