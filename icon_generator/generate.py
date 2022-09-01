import json
import random
import os
import glob
import numpy as np
import math
import PIL
from PIL import ImageOps
from PIL import ImageChops
from PIL import Image

currentDir = os.path.abspath('')
random.seed(0)

# folder inputs for masks
blueMasks = glob.glob(os.path.join(currentDir, "masks", "blue", "*.png"))
redMasks = glob.glob(os.path.join(currentDir, "masks", "red", "*.png"))
travelerMasks = glob.glob(os.path.join(currentDir, "masks", "traveler", "*.png"))

# output folder
generateDir = os.path.join(currentDir, "generated")

# sidelength of output images
sideLength = 100

# base textures
blueTex = PIL.Image.open(os.path.join(currentDir, "bases", "blue.png"))
redTex = PIL.Image.open(os.path.join(currentDir, "bases", "red.png"))
blueTex = blueTex.convert("RGBA")
redTex = redTex.convert("RGBA")
texSideLength = 295*2 # sidelength of sample from texture

def SelectPortionOfImage(im):
	# select a random square from within an image
	w, h = im.width, im.height
	w_offset, h_offset = random.randint(0,w-texSideLength), random.randint(0,h-texSideLength)
	im2 = im.copy()
	if random.random()>0.5:
		im2.transpose(PIL.Image.FLIP_LEFT_RIGHT)
	if random.random()>0.5:
		im2.transpose(PIL.Image.FLIP_TOP_BOTTOM)
	im2 = im2.crop((w_offset, h_offset, w_offset+texSideLength, h_offset+texSideLength))
	return im2

def ChopImageInHalf(im):
	w, h = im.width, im.height
	im = im.crop((0,0,w/2,h))
	return im

def ConcatImagesW(im1, im2):
	dst = Image.new('RGBA', (im1.width + im2.width, im1.height))
	dst.paste(im1, (0, 0))
	dst.paste(im2, (im1.width, 0))
	return dst

def FetchFilledPartOfImage(im):
	# crop the non-blank part (of a mask)
	im = im.convert("RGBA")
	data = np.asarray(im)
	alphas = data[:,:,3]
	nzRows = np.where(data.any(axis=0))[0]
	nzCols = np.where(data.any(axis=1))[0]
	l,r = nzRows[0], nzRows[-1]
	b,t = nzCols[0], nzCols[-1]
	o_x = (l+r)/2
	o_y = (t+b)/2
	o = max(r-l, t-b)/2
	o *= math.sqrt(2) * 1.08 # padding
	im = im.crop((o_x-o, o_y-o, o_x+o, o_y+o))
	im = im.resize((texSideLength,texSideLength), Image.ANTIALIAS)
	return im
   
def MakeIcon(color, maskPath):
	base = os.path.basename(maskPath)
	name = os.path.splitext(base)[0]
	
	# select base tex
	if color == "blue":
		baseTex = SelectPortionOfImage(blueTex)			
	elif color == "red":
		baseTex = SelectPortionOfImage(redTex)
	elif color == "traveler":
		_blueTex = ChopImageInHalf(SelectPortionOfImage(blueTex))
		_redTex = ChopImageInHalf(SelectPortionOfImage(redTex))
		baseTex = ConcatImagesW(_blueTex, _redTex)
	else:
		raise Exception("unknown color")

	# construct image
	rawMask = PIL.Image.open(maskPath) 
	mask = FetchFilledPartOfImage(rawMask)
	PIL.ImageChops.offset(mask, 0, int(-0.045*texSideLength)) # compensate for css/bra1ntool weirdness
	
	blank = PIL.Image.new("RGBA", (mask.width, mask.height), (0,0,0,0))
	icon = PIL.Image.composite(baseTex, blank, mask)
	icon = icon.resize((sideLength,sideLength), Image.ANTIALIAS)
	print(name)
	icon.save(os.path.join(generateDir, name.lower()+".png"))

def CleanDir (dir):
	files = glob.glob(os.path.join(dir, "*"))
	for file in files:
		os.remove(file)
	
if not os.path.exists(generateDir):
	os.makedirs(generateDir)
CleanDir(generateDir)

masks = {"red":[], "blue":[], "traveler":[]}
def AddMasksWithColor (color, files):
	for file in files:
		masks[color].append(file)
AddMasksWithColor("blue", blueMasks)
AddMasksWithColor("red", redMasks)
AddMasksWithColor("traveler", travelerMasks)

for color,paths in masks.items():
	for path in paths:
		MakeIcon(color, path)