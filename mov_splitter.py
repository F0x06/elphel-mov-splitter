import sys
import glob
import os
import exifread
import shutil
from datetime import datetime


from hachoir_subfile.search import SearchSubfile
from hachoir_core.cmd_line import unicodeFilename
from hachoir_core.stream import FileInputStream

Input = "data/mov"
Output = "data/out"
Trash = "data/trash"

Modules = sorted(os.listdir(Input))

sys.__stdout = sys.stdout
devnull = open(os.devnull, "w")

def renameImages(mn, fn):
	for fn in glob.glob("%s/%s" % (Output, "file-*.jpg")):
		f = open(fn, 'rb')
		tags = exifread.process_file(f)
		f.close()

		date_object = datetime.strptime(str(tags["Image DateTime"]), '%Y:%m:%d %H:%M:%S')
		OutName = "%s_%s_%s" % (date_object.strftime("%s"), tags["EXIF SubSecTimeOriginal"], mn)

		os.rename(fn, "%s/%s.jp4" % (Output, OutName))

def filterImages():
	for fn in glob.glob("%s/%s" % (Output, "*.jp4")):

		for i in range(1, 10):
			FileName = "%s_%s.jp4" % ('_'.join(fn.split('_')[:-1]), i)

			if not(os.path.isfile(FileName)):
				os.system("mv %s* %s &> /dev/null" % ('_'.join(fn.split('_')[:-1]), Trash))
				break
			else:
				continue

for mn in Modules:
	for fn in glob.glob("%s/%s/*.mov" % (Input, mn)):
		print "Extracting %s..." % fn
		
		stream = FileInputStream(unicodeFilename(fn), real_filename=fn)
		
		subfile = SearchSubfile(stream, 0, None)
		subfile.verbose = False
		subfile.setOutput(Output)
		subfile.loadParsers(categories=["images"], parser_ids=["jpeg"])
		
		sys.stdout = devnull
		ok = subfile.main()
		sys.stdout = sys.__stdout

		print "Renaming files..."
		renameImages(mn, fn)
	# filterImages(mn)