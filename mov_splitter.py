#!/usr/bin/env python

import sys
import glob
import os
import exifread
import shutil
from datetime import datetime


from hachoir_subfile.search import SearchSubfile
from hachoir_core.cmd_line import unicodeFilename
from hachoir_core.stream import FileInputStream

Input = ""
Output = ""
Trash = ""

Total_Files = 0
Processed_Files = 0

Modules = []

sys.__stdout = sys.stdout
devnull = open(os.devnull, "w")

# Function to retrive each timestamps into an array of strings
def getTimeStamps():
	TimeStamps = []

	for i in glob.glob("%s/*.jp4" % Output):
		Fname = i.split('/')
		Fname = Fname[len(Fname) - 1]

		TimeStamp = "%s_%s" % (Fname.split('_')[0], Fname.split('_')[1])

		if TimeStamp not in TimeStamps:
			TimeStamps.append(TimeStamp)

	return sorted(TimeStamps)

# Function to rename all images generated images by hachoir to a correct format (UnixTimeSTamp_SubSecTime_Module.jp4)
def renameImages(mn):
	for fn in glob.glob("%s/%s" % (Output, "file-*.jpg")):
		f = open(fn, 'rb')
		tags = exifread.process_file(f)
		f.close()

		date_object = datetime.strptime(str(tags["Image DateTime"]), '%Y:%m:%d %H:%M:%S')
		OutName = "%s_%s_%s" % (date_object.strftime("%s"), tags["EXIF SubSecTimeOriginal"], mn)

		os.rename(fn, "%s/%s.jp4" % (Output, OutName))

# Function to move all incomplete sequences to Trash folder, a complete sequence need to be 1-9
def filterImages():
	for ts in getTimeStamps():

		for i in range(1, 10):
			FileName = "%s/%s_%s.jp4" % (Output, ts, i)

			if not(os.path.isfile(FileName)):
				os.system("mv %s/%s* %s" % (Output, ts, Trash))
				break
			else:
				continue

# Program entry point function
def main():
	global Input, Output, Trash

	if len(sys.argv) < 4:
		print "Usage: %s <Input folder> <Output folder> <Trash folder>" % sys.argv[0]
		return

	Input = sys.argv[1].rstrip('/')
	Output = sys.argv[2].rstrip('/')
	Trash = sys.argv[3].rstrip('/')

	Modules = sorted(os.listdir(Input))

	Module_Index = 1

	print "Extracting MOV files..."
	for mn in Modules:
		print "Processing module %d/%d..." % (Module_Index, len(Modules))

		MovList = glob.glob("%s/%s/*.mov" % (Input, mn))
		Total_Files = len(MovList)
		Processed_Files = 1

		for fn in MovList:
			print "Extracting %s (%d/%d)..." % (fn, Processed_Files, Total_Files)
			
			stream = FileInputStream(unicodeFilename(fn), real_filename=fn)
			
			subfile = SearchSubfile(stream, 0, None)
			subfile.verbose = False
			subfile.setOutput(Output)
			subfile.loadParsers(categories=["images"], parser_ids=["jpeg"])
			
			sys.stdout = devnull
			ok = subfile.main()
			sys.stdout = sys.__stdout

			print "Renaming images..."
			renameImages(mn)

			Processed_Files+=1

		Module_Index+=1 

	print "Filtering images..."
	filterImages()

# Program entry point
if __name__ == "__main__":
    main()