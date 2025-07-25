#!/usr/bin/env python3
import sys
import random
import os
import argparse
from PIL import Image, ImageDraw, ImageFont
font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf"

default_font_size = 19
default_spacing = 30
default_sticker_width = 128
default_sticker_height = 55

pixels_per_mm = 128/18
print_head_pixels = 128



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

	new_image.show()
	file=f"/tmp/label-{random.randrange(1000)}.png"
	new_image.save(file)
	x = input(f"Saved as {file}. Print? (y/n): ")
	if(x=="y"):
		print("Printing")
		os.system(f"./ptouch-print/build/ptouch-print --image {file}")
		

image = Image.new(mode="1", size=(200, 120), color=(1))
font = ImageFont.truetype(font_path, size=50)
draw = ImageDraw.Draw(image)

def text(t, font_size=20):
    image = Image.new(mode="1", size=(100,100), color=(1))
    draw = ImageDraw.Draw(image)
    bbox = draw.textbbox((0,0), t, font=font, anchor='ls')
    print(bbox, (bbox[2], -bbox[1]+bbox[3]))
    image = Image.new(mode="1", size=(bbox[2], -bbox[1]+bbox[3]), color=(1))
    draw = ImageDraw.Draw(image)
    draw.text((0,-bbox[1]+1), t, font=font, anchor='ls')
    return image

text("AA").show()
text("Aq").show()
