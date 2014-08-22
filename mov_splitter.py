#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
  elphel-mov-splitter - Elphel MOV to jp4 splitter
 
  Copyright (c) 2014 FOXEL SA - http://foxel.ch
  Please read <http://foxel.ch/license> for more information.
 
 
  Author(s):
 
       Kevin Velickovic <k.velickovic@foxel.ch>
 
 
  This file is part of the FOXEL project <http://foxel.ch>.
 
  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU Affero General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.
 
  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU Affero General Public License for more details.
 
  You should have received a copy of the GNU Affero General Public License
  along with this program.  If not, see <http://www.gnu.org/licenses/>.
 
 
  Additional Terms:
 
       You are required to preserve legal notices and author attributions in
       that material or in the Appropriate Legal Notices displayed by works
       containing it.
 
       You are required to attribute the work as explained in the "Usage and
       Attribution" section of <http://foxel.ch/license>.
"""

import sys
import signal
import glob
import os
import re
import exifread
from datetime import datetime
from functools import wraps
from time import time
from cStringIO import StringIO

# Global variables
__Input__ = ""
__Output__ = ""
__Trash__ = ""

Total_Files = 0
Processed_Files = 0

Modules = []

# Function to catch CTRL-C
def signal_handler(signal, frame):
        print('Interrupted!')
        sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

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

# Function to extract JPEG images inside a MOV file
@timed
def extractMOV(InputFile, OutputFolder):

    # JPEG file header
    JPEGHeader = b'\xff\xd8\xff\xe1'

    # Open input MOV file
    mov = open(InputFile, 'rb')
    mov_data = mov.read()
    mov.close()

    # Search all JPEG files inside the MOV file
    JPEG_Offsets = sorted([match.start() for match in re.finditer(JPEGHeader, mov_data)])

    # Walk over JPEG files positions
    for _Index, _Offset in enumerate(JPEG_Offsets):

        # Calculate the filesize for extraction
        if (_Index >= len(JPEG_Offsets) - 1):
            Size = len(mov_data) - _Offset
        else:
            Size = (JPEG_Offsets[_Index+1] - _Offset)

        # Extract JPEG from MOV file
        ImageData = mov_data[_Offset:(Size + _Offset if Size is not None else None)]

        # Extract EXIF data from JPEG file
        ImageData_File = StringIO(ImageData)
        EXIF_Tags = exifread.process_file(ImageData_File)
        ImageData_File.close()

        # Calculate the output filename
        date_object = datetime.strptime(str(EXIF_Tags["Image DateTime"]), '%Y:%m:%d %H:%M:%S')
        Output_Name = "%s_%s_%s" % (date_object.strftime("%s"), EXIF_Tags["EXIF SubSecTimeOriginal"], 1)

        # Save the file
        Output_Image = open('%s/%s.jp4' % (OutputFolder, Output_Name), 'wb')
        Output_Image.write(ImageData)
        Output_Image.close()

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

            # Extract MOV file
            extractMOV(fn, __Output__)

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
