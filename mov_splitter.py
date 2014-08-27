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

# Imports
import exifread
import glob
import os
import signal
import string
import sys
import traceback

from cStringIO import StringIO
from datetime import datetime
from functools import wraps
from time import time

# Global variables

# KML file header
KML_Header = \
"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://earth.google.com/kml/2.2">
<Document>"""

# KML file entry
KML_Entry = \
"""<PhotoOverlay>
    <Camera>
        <longitude>%f</longitude>
        <latitude>%f</latitude>
        <altitude>%s</altitude>
        <heading>%d</heading>
        <tilt>%d</tilt>
        <roll>%d</roll>
    </Camera>
    <Icon>
        <href>%s/%s</href>
    </Icon>
</PhotoOverlay>
"""

# KML file footer
KML_Footer = \
"""</Document>
</kml>"""

# Function to catch CTRL-C
def signal_handler(_signal, _frame):
    del _signal
    del _frame

    print('\nInterrupted!')
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

# Function to moditor execution time of functions
def timed(f):
    @wraps(f)
    def wrapper(*args, **kwds):

        # Check if debug mode is enabled
        _Enabled = len(sys.argv) >= 6 and int(sys.argv[5]) > 0

        # Start timer initialization
        if _Enabled:
            start = time()

        # Call original function
        result = f(*args, **kwds)

        # Show final result
        if _Enabled:
            elapsed = time() - start
            print "%s took %ds to finish" % (f.__name__, elapsed)

        return result
    return wrapper

# Function to determine if quiet mode is enabled
def quietEnabled():
    return (len(sys.argv) >= 7 and int(sys.argv[6]) > 0)

# Function to find all occurences of a given input
@timed
def find_all(a_str, sub):
    start = 0
    while True:
        # Find first element
        start = a_str.find(sub, start)

        # If no match found exit function
        if start == -1: return

        # If there is a match return it and process the next element
        yield start

        # Move pointer to next occurence
        start += len(sub)

# Function to extract JPEG images inside a MOV file
@timed
def extractMOV(InputFile, OutputFolder, ModuleName):

    # JPEG file header
    JPEGHeader = b'\xff\xd8\xff\xe1'

    # Open input MOV file
    mov = open(InputFile, 'rb')
    mov_data = mov.read()
    mov.close()

    # Search all JPEG files inside the MOV file
    JPEG_Offsets = list(find_all(mov_data, JPEGHeader))
    JPEG_Offsets_len = len(JPEG_Offsets)

    # Walk over JPEG files positions
    for _Index, _Offset in enumerate(JPEG_Offsets):

        # Display progress
        if not quietEnabled():
            sys.stdout.write("Extracting %d/%d\r" % (_Index, JPEG_Offsets_len - 1))
            sys.stdout.flush()

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
        Output_Name = "%s_%s_%s" % (date_object.strftime("%s"), EXIF_Tags["EXIF SubSecTimeOriginal"], ModuleName)

        # Save the file
        Output_Image = open('%s/%s.jp4' % (OutputFolder, Output_Name), 'wb')
        Output_Image.write(ImageData)
        Output_Image.close()

# Function to retrive each timestamps into an array of strings
@timed
def getTimeStamps(Output):

    # local variable
    TimeStamps = []

    # Walk over jp4 files in the __Output__ folder
    for i in glob.glob("%s/*.jp4" % Output):

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
def filterImages(Output, Trash):

    # Walk over timestamps
    for ts in getTimeStamps(Output):

        # Walk over modules range 1-9
        for i in range(1, 9):

            # Calculate filename fro comparaison
            FileName = "%s/%s_%s.jp4" % (Output, ts, i)

            # Check if file exists
            if not(os.path.isfile(FileName)):

                # Move file to __Trash__ folder
                if not quietEnabled():
                    print "Incomplete timestamp %s" % ts
                os.system("mv %s/%s* %s" % (Output, ts, Trash))
                break
            else:

                # Continue walking
                continue

# Function to convert a fractioned EXIF array into degrees
def array2degrees(dms):

    # Rounding factor
    _round=1000000

    # Splitting input values
    d = string.split(str(dms.values[0]), '/')
    m = string.split(str(dms.values[1]), '/')
    s = string.split(str(dms.values[2]), '/')

    # Variables padding
    if len(d) == 1:
        d.append(1)
    if len(m) == 1:
        m.append(1)
    if len(s) == 1:
        s.append(1)

    # Compute degrees
    rslt = float(d[0]) / float(d[1]) + (float(m[0]) / float(m[1])) / 60.0 + (float(s[0]) / float(s[1])) / 3600.0

    # Return result
    return round(_round*rslt)/_round

# Function to convert a fractioned EXIF altidute into meters
def parseAlt(alt):

    # Rounding factor
    _round=1000000

    # Splitting input values
    a = string.split(str(alt), '/')

    # Variables padding
    if len(a) == 1:
        a.append(1)

    # Compute altitude
    rslt = float(a[0]) / float(a[1])

    # Return result
    return round(_round*rslt)/_round


# Function to generate KML file
def generateKML(Input, BaseURL):

    # Open KML file for writing
    KML_File = open("%s/../map_points.kml" % Input, "wb")

    # Write header
    KML_File.write(KML_Header)

    # Walk over files
    for f in sorted(glob.glob("%s/*_1.jp4" % Input)):

        # Open image and extract EXIF data
        Image = open(f, "rb")
        EXIFData = exifread.process_file(Image)
        Image.close()

        # Compute GPS data
        Longitude = (-1 if (EXIFData['GPS GPSLongitudeRef']=="W") else 1) * array2degrees(EXIFData['GPS GPSLongitude'])
        Latitude = (-1 if (EXIFData['GPS GPSLatitudeRef']=="S") else 1) * array2degrees(EXIFData['GPS GPSLatitude'])
        Altitude = (-1 if (EXIFData['GPS GPSAltitudeRef']=="S") else 1) * parseAlt(EXIFData['GPS GPSAltitude'])

        Heading = 0
        Tilt = 90
        Roll = 0

        if 'GPS GPSImgDirection' in EXIFData:

            # Compute GPS data
            Heading = parseAlt(EXIFData['GPS GPSImgDirection'])
            Tilt = (-1 if (EXIFData['GPS GPSDestLatitudeRef'] =="S") else 1) * array2degrees(EXIFData['GPS GPSDestLatitude']) + 90.0

            if (Tilt < 0):
                Tilt = 0
            elif (Tilt > 180):
                Tilt = 180

            Roll = (-1 if (EXIFData['GPS GPSDestLongitudeRef']=="W") else 1) * array2degrees(EXIFData['GPS GPSDestLongitude'])

        # Write KML entry
        KML_File.write(KML_Entry % (Longitude, Latitude, "{0:.1f}".format(Altitude), Heading, Tilt, Roll, BaseURL, os.path.split(f)[1]))

    # Write KML footer
    KML_File.write(KML_Footer)

    # Close KML file
    KML_File.close()

# Program entry point function
@timed
def main():

    # Arguments check
    if len(sys.argv) < 5:
        print "Usage: %s <Input folder> <Output folder> <Trash folder> <KML base URL> [Debug 0/1] [Quiet 0/1]" % sys.argv[0]
        return

    # Remove last slash from paths
    __Input__ = sys.argv[1].rstrip('/')
    __Output__ = sys.argv[2].rstrip('/')
    __Trash__ = sys.argv[3].rstrip('/')
    __KMLBase__ = sys.argv[4].rstrip('/')

    # Get modules from input folder
    CameraModules = sorted(os.listdir(__Input__))

    # Initialize module index indicator
    Module_Index = 1

    if not quietEnabled():
        print "Extracting MOV files..."

    # Walk over modules
    for mn in CameraModules:
        if not quietEnabled():
            print "Processing module %d/%d..." % (Module_Index, len(CameraModules))

        # Get list ov MOV files inside the module folder
        MovList = glob.glob("%s/%s/*.mov" % (__Input__, mn))
        Total_Files = len(MovList)

        # Initialize files index indicator
        Processed_Files = 1

        # Walk over file list
        for fn in MovList:
            if not quietEnabled():
                print "Processing (%d/%d): %s..." % (Processed_Files, Total_Files, fn)

            # Extract MOV file
            try:
                extractMOV(fn, __Output__, mn)
            except (IOError, MemoryError):
                traceback.print_exc()

            # Increment files index indicator
            Processed_Files+=1

        # Increment modules index indicator
        Module_Index+=1

    if not quietEnabled():
        print "Filtering images..."

    # Filter images see filterImages()
    filterImages(__Output__, __Trash__)

    if not quietEnabled():
        print "Generating KML file..."

    # Generate KML file
    generateKML(__Output__, __KMLBase__)

# Program entry point
if __name__ == "__main__":
    main()
