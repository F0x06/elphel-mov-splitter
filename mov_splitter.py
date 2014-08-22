#!/usr/bin/env python
#
# elphel-mov-splitter - Elphel MOV to jp4 splitter using hachoir
#
# Copyright (c) 2013-2014 FOXEL SA - http://foxel.ch
# Please read <http://foxel.ch/license> for more information.
#
# Author(s):
#
#      Kevin Velickovic <k.velickovic@foxel.ch>
#
# This file is part of the FOXEL project <http://foxel.ch>.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
# Additional Terms:
#
#      You are required to preserve legal notices and author attributions in
#      that material or in the Appropriate Legal Notices displayed by works
#      containing it.
#
#      You are required to attribute the work as explained in the "Usage and
#      Attribution" section of <http://foxel.ch/license>.

import sys
import glob
import os
import exifread
import shutil
from datetime import datetime
from functools import wraps
from time import time


from hachoir_subfile.search import SearchSubfile
from hachoir_core.cmd_line import unicodeFilename
from hachoir_core.stream import FileInputStream

# Global variables
__Input__ = ""
__Output__ = ""
__Trash__ = ""

Total_Files = 0
Processed_Files = 0

Modules = []

# Function to moditor execution time of functions
def timed(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        if len(sys.argv) >= 5:
            start = time()

        result = f(*args, **kwds)

        if len(sys.argv) >= 5:
            elapsed = time() - start
            print "%s took %ds to finish" % (f.__name__, elapsed)
            
        return result
    return wrapper

# Function to disable __Output__ on function call
class suppress_stdout_stderr(object):

    def __init__(self):
        # Open a pair of null files
        self.null_fds =  [os.open(os.devnull,os.O_RDWR) for x in range(2)]

        # Save the actual stdout (1) and stderr (2) file descriptors.
        self.save_fds = (os.dup(1), os.dup(2))

    def __enter__(self):
        # Assign the null pointers to stdout and stderr.
        os.dup2(self.null_fds[0],1)
        os.dup2(self.null_fds[1],2)

    def __exit__(self, *_):
        # Re-assign the real stdout/stderr back to (1) and (2)
        os.dup2(self.save_fds[0],1)
        os.dup2(self.save_fds[1],2)

        # Close the null files
        os.close(self.null_fds[0])
        os.close(self.null_fds[1])

# Function to retrive each timestamps into an array of strings
@timed
def getTimeStamps():

    # local variable
    TimeStamps = []

    # Walk over jp4 files in the __Output__ folder
    for i in glob.glob("%s/*.jp4" % __Output__):

        # Retrive just the filename
        Fname = i.split('/')
        Fname = Fname[len(Fname) - 1]

        # Extract timestamp from filename
        TimeStamp = "%s_%s" % (Fname.split('_')[0], Fname.split('_')[1])

        # Insert to list if timestamp are not present
        if TimeStamp not in TimeStamps:
            TimeStamps.append(TimeStamp)

    # Return timestamp list
    return sorted(TimeStamps)

# Function to rename all images generated images by hachoir to a correct format (UnixTimeSTamp_SubSecTime_Module.jp4)
@timed
def renameImages(mn):

    # Walk over jp4 files in the __Output__ folder
    for fn in glob.glob("%s/%s" % (__Output__, "file-*.jpg")):

        # Read EXIF data from image
        f = open(fn, 'rb')
        tags = exifread.process_file(f)
        f.close()

        # Read date from EXIF data as date object
        date_object = datetime.strptime(str(tags["Image DateTime"]), '%Y:%m:%d %H:%M:%S')

        # Create destination file name
        OutName = "%s_%s_%s" % (date_object.strftime("%s"), tags["EXIF SubSecTimeOriginal"], mn)

        # Rename the file
        os.rename(fn, "%s/%s.jp4" % (__Output__, OutName))

# Function to move all incomplete sequences to __Trash__ folder, a complete sequence need to be 1-9
@timed
def filterImages():

    # Walk over timestamps
    for ts in getTimeStamps():

        # Walk over modules range 1-9
        for i in range(1, 9):

            # Calculate filename fro comparaison
            FileName = "%s/%s_%s.jp4" % (__Output__, ts, i)

            # Check if file exists
            if not(os.path.isfile(FileName)):

                # Move file to __Trash__ folder
                print "Incomplete timestamp %s" % ts
                os.system("mv %s/%s* %s" % (__Output__, ts, __Trash__))
                break
            else:

                # Continue walking
                continue
@timed
def subFileWrapper(sf):
    with suppress_stdout_stderr():
        sf.main()

# Program entry point function
@timed
def main():
    
    # Globalize variables
    global __Input__, __Output__, __Trash__

    # Arguments check
    if len(sys.argv) < 4:
        print "Usage: %s <Input folder> <Output folder> <Trash folder> [Debug 0/1]" % sys.argv[0]
        return

    # Remove last slash from paths
    __Input__ = sys.argv[1].rstrip('/')
    __Output__ = sys.argv[2].rstrip('/')
    __Trash__ = sys.argv[3].rstrip('/')

    # Get modules from inout folder
    Modules = sorted(os.listdir(__Input__))

    # Initialize module index indicator
    Module_Index = 1

    print "Extracting MOV files..."

    # Walk over modules
    for mn in Modules:
        print "Processing module %d/%d..." % (Module_Index, len(Modules))

        # Get list ov MOV files inside the module folder
        MovList = glob.glob("%s/%s/*.mov" % (__Input__, mn))
        Total_Files = len(MovList)

        # Initialize files index indicator
        Processed_Files = 1

        # Walk over file list
        for fn in MovList:
            print "Extracting (%d/%d): %s..." % (Processed_Files, Total_Files, fn)

            # Read the MOV file
            stream = FileInputStream(unicodeFilename(fn), real_filename=fn)

            # Configure Hachoir
            subfile = SearchSubfile(stream, 0, None)
            subfile.verbose = False
            subfile.setOutput(__Output__)
            subfile.loadParsers(categories=["images"], parser_ids=["jpeg"])

            # Run Hachoir
            subFileWrapper(subfile)

            print "Renaming images..."

            # Rename images
            renameImages(mn)

            # Increment files index indicator
            Processed_Files+=1

        # Increment modules index indicator
        Module_Index+=1

    print "Filtering images..."

    # Filter images see filterImages()
    filterImages()

# Program entry point
if __name__ == "__main__":
    main()
