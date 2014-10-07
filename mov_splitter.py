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
import datetime
import getopt
import glob
import os
import shutil
import signal
import string
import sys
import time
import traceback
from cStringIO import StringIO
from datetime import datetime
from functools import wraps

import exifread

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

# Config variables
DEBUG_MODE = 0
NO_COLORS  = 0
NO_FILTER  = 0
QUIET_MODE = 0
LOG_FILE   = ""

# MOV file container class
class MovFile:
    def __init__(self, path, modulename):
        self.path = path
        self.module = int(modulename)

# Function to print debug messages
def ShowMessage(Message, Type=0, Halt=0):

    # Flush stdout
    sys.stdout.flush()

    # Get current date
    DateNow = datetime.now().strftime("%H:%M:%S")

    # Write to log file
    if len(LOG_FILE) > 0:
        with open(LOG_FILE, "a+") as logFile:
            logFile.write("%s [INFO] %s\n" % (DateNow, Message))

    # Display proper message
    if Type == 0:
        if NO_COLORS:
            sys.stdout.write("%s [INFO] %s\n" % (DateNow, Message))
        else:
            sys.stdout.write("%s \033[32m[INFO]\033[39m %s\n" % (DateNow, Message))
    elif Type == 1:
        if NO_COLORS:
            sys.stdout.write("%s [WARNING] %s\n" % (DateNow, Message))
        else:
            sys.stdout.write("%s \033[33m[WARNING]\033[39m %s\n" % (DateNow, Message))
    elif Type == 2:
        if NO_COLORS:
            sys.stdout.write("%s [ERROR] %s\n" % (DateNow, Message))
        else:
            sys.stdout.write("%s \033[31m[ERROR]\033[39m %s\n" % (DateNow, Message))
    elif Type == 3:
        if NO_COLORS:
            sys.stdout.write("%s [DEBUG] %s\n" % (DateNow, Message))
        else:
            sys.stdout.write("%s \033[34m[DEBUG]\033[39m %s\n" % (DateNow, Message))

    # Flush stdout
    sys.stdout.flush()

    # Halt program if requested
    if Halt:
        sys.exit()

# Function to catch CTRL-C
def signal_handler(_signal, _frame):
    del _signal
    del _frame

    ShowMessage("Interrupted!", 2, 1)
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

# Function to moditor execution time of functions
def timed(f):
    @wraps(f)
    def wrapper(*args, **kwds):

        # Start timer initialization
        if DEBUG_MODE:
            start = time.time()

        # Call original function
        result = f(*args, **kwds)

        # Show final result
        if DEBUG_MODE:
            elapsed = time.time() - start
            ShowMessage("%s took %ds to finish" % (f.__name__, elapsed), 3)

        return result
    return wrapper

# Function to determine if quiet mode is enabled
def quietEnabled():
    return QUIET_MODE

# Read extracted MOV's from file
@timed
def LoadState(File):

    # Variables
    List = []

    # Open file and insert each entry into an array
    with open(File, 'r') as f:
        List = [line.rstrip('\n') for line in f]

    # Return the result
    return List

# Write extracted MOV's to a file
@timed
def SaveState(File, List, entry):

    # Insert MOV path into array if not present
    if not entry in List:
        List.append(entry)

    # Save array to file
    with open(File, 'w') as f:
        for s in List:
            f.write(s + '\n')

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
def extractMOV(InputFile, OutputFolder, TrashFolder, ModuleName, Results_back):

    # Local variables
    JPEGHeader    = b'\xff\xd8\xff\xe1'
    Results       = [0, []]

    # Open input MOV file
    if not quietEnabled():
        sys.stdout.flush()
        sys.stdout.write("Loading MOV file...\r")
        sys.stdout.flush()

    mov = open(InputFile, 'rb')
    mov_data = mov.read()
    mov.close()

    # Initialize results counter
    Results[0] = Results_back[0]
    Results[1] = Results_back[1]

    # Search all JPEG files inside the MOV file
    JPEG_Offsets     = list(find_all(mov_data, JPEGHeader))
    JPEG_Offsets_len = len(JPEG_Offsets)

    # Display message when no headers are found inside the MOV file
    if JPEG_Offsets_len == 0:
        ShowMessage("No JPEG headers found in MOV file %s" % InputFile, 1)

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

        # Output file variables
        Output_Name = ""
        Output_Image = None

        # Error handling
        if len(EXIF_Tags) <= 0:

            # Print error
            ShowMessage("Failed to read EXIF data", 1)

            # Calculate filename
            Output_Name = "fail_%d_exif" % (Results[0])

            # Open output file
            Output_Image = open('%s/%s.jp4' % (TrashFolder, Output_Name), 'wb')

            # Print error
            ShowMessage("Saving image to %s/%s.jp4" % (TrashFolder, Output_Name), 1)

            # Increment fail counter
            Results[0] += 1
        else:

            # Calculate the output filename
            date_object = datetime.strptime(str(EXIF_Tags["Image DateTime"]), '%Y:%m:%d %H:%M:%S')
            Output_Name = "%s_%s_%s" % (date_object.strftime("%s"), EXIF_Tags["EXIF SubSecTimeOriginal"], ModuleName)
            Results[1].append(Output_Name)

            # Open output file
            Output_Image = open('%s/%s.jp4' % (OutputFolder, Output_Name), 'wb')

        # write the file
        Output_Image.write(ImageData)
        Output_Image.close()

    return Results

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
def filterImages(Output, Trash, Results):

    # Get extracted JP4's list
    List = sorted(Results[1])

    # Initialize variable
    ListNoMod = []

    # Build timestamps list without module (_x)
    for item in List:
        ListNoMod.append(item[:-2])

    # Sort and remove duplicates from list
    ListNoMod = sorted(set(ListNoMod))

    # Walk over timestamps
    for ts in ListNoMod:

        # Missing modules array
        Missing_Modules = []

        # Walk over modules range 1-9
        for i in range(1, 10):

            # Calculate filename for comparaison
            FileName = "%s_%s" % (ts, i)

            # Check if file exists
            if not(FileName in List):

                # Append missing module to list
                Missing_Modules.append(i)

        # Check presense of missing modules
        if len(Missing_Modules) > 0:

            # Calculate modules to be removed
            ToRemove = [x for x in range(1, 10) if x not in Missing_Modules]

            # Move files to Trash folder
            for m in ToRemove:

                # Calculate paths
                SourceFile = "%s/%s_%s.jp4" % (Output, ts, m)
                DestFile   = "%s/%s_%s.jp4" % (Trash, ts, m)

                # Check if dest trash file exists, if exists remove it
                if os.path.isfile(DestFile):
                    os.remove(DestFile)

                # Move file
                shutil.move(SourceFile, DestFile)

            if not quietEnabled():
                ShowMessage("Incomplete timestamp %s (Missing module(s) %s)" % (ts, str(Missing_Modules)[1:-1]), 1)

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
@timed
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
        Longitude = (-1 if (EXIFData['GPS GPSLongitudeRef'] == "W") else 1) * array2degrees(EXIFData['GPS GPSLongitude'])
        Latitude  = (-1 if (EXIFData['GPS GPSLatitudeRef'] == "S") else 1)  * array2degrees(EXIFData['GPS GPSLatitude'])
        Altitude  = (-1 if (EXIFData['GPS GPSAltitudeRef'] == "S") else 1)  * parseAlt(EXIFData['GPS GPSAltitude'])

        Heading = 0
        Tilt    = 90
        Roll    = 0

        if 'GPS GPSImgDirection' in EXIFData:

            # Compute GPS data
            Heading = parseAlt(EXIFData['GPS GPSImgDirection'])
            Tilt    = (-1 if (EXIFData['GPS GPSDestLatitudeRef'] == "S") else 1) * array2degrees(EXIFData['GPS GPSDestLatitude']) + 90.0

            if (Tilt < 0):
                Tilt = 0
            elif (Tilt > 180):
                Tilt = 180

            Roll = (-1 if (EXIFData['GPS GPSDestLongitudeRef'] == "W") else 1) * array2degrees(EXIFData['GPS GPSDestLongitude'])

        # Write KML entry
        KML_File.write(KML_Entry % (Longitude, Latitude, "{0:.1f}".format(Altitude), Heading, Tilt, Roll, BaseURL, os.path.split(f)[1]))

    # Write KML footer
    KML_File.write(KML_Footer)

    # Close KML file
    KML_File.close()

# Usage display function
def _usage():
    print """
    Usage: %s [OPTIONS]

    [Required arguments]
    -i --input          Input MOV folder
    -o --output         Output JP4 folder
    -t --trash          JP4 trash folder

    [Optional arguments]
    -h --help           Prints this

    -k --kmlbase        KML base url
    -s --state          State file to save/resume job
    -l --logfile        Log file path
    -f --nofilter       Don't filter images (trashing)

    -d --debug          Debug mode
    -q --quiet          Quiet mode (Silent)
    -n --nocolors       Disable stdout colors

    """ % sys.argv[0]

# Program entry point function
# pylint: disable=W0603
def main(argv):

    # Arguments variables initialisation
    __Input__       = ""
    __Output__      = ""
    __Trash__       = ""
    __KMLBase__     = "__BASE__URL__"
    __State_File__  = ""

    # Scope variables initialisation
    __MOV_List__           = []
    __MOV_List_Optimized__ = []
    __Total_Files__        = 0
    __Processed_Files__    = 1
    __State_List__         = []
    __extractMOV_Results__ = [
        0, # Fail counter
        [] # Extracted files
    ]

    # Arguments parser
    try:
        opt, args = getopt.getopt(argv, "hi:o:t:k:s:dql:nf", ["help", "input=", "output=", "trash=", "kmlbase=", "state=", "debug", "quiet", "logfile=", "nocolors", "nofilter"])
        args = args
    except getopt.GetoptError, err:
        print str(err)
        _usage()
        sys.exit(2)
    for o, a in opt:
        if o in ("-h", "--help"):
            _usage()
            sys.exit()
        elif o in ("-i", "--input"):
            __Input__  = a.rstrip('/')
        elif o in ("-o", "--output"):
            __Output__  = a.rstrip('/')
        elif o in ("-t", "--trash"):
            __Trash__  = a.rstrip('/')
        elif o in ("-k", "--kmlbase"):
            __KMLBase__  = a.rstrip('/')
        elif o in ("-s", "--state"):
            __State_File__  = a
        elif o in ("-d", "--debug"):
            global DEBUG_MODE
            DEBUG_MODE = 1
        elif o in ("-q", "--quiet"):
            global QUIET_MODE
            QUIET_MODE = 1
        elif o in ("-l", "--logfile"):
            global LOG_FILE
            LOG_FILE  = a
        elif o in ("-n", "--nocolors"):
            global NO_COLORS
            NO_COLORS = 1
        elif o in ("-f", "--nofilter"):
            global NO_FILTER
            NO_FILTER  = 1
        else:
            assert False, "unhandled option"

    # Arguments check
    if len(argv) < 5:
        _usage()
        return

    # Create default directories
    if not os.path.isdir(__Output__):
        os.makedirs(__Output__)

    if not os.path.isdir(__Trash__):
        os.makedirs(__Trash__)

    # Check if state file exists, if exists load it
    if os.path.isfile(__State_File__):
        __State_List__ = LoadState(__State_File__)

    # Get modules from input folder
    CameraModules = sorted(os.listdir(__Input__))

    # Error handling
    if len(CameraModules) == 0:
        ShowMessage("No camera modules found in %s" % __Input__, 2, 1)

    # Insert all MOV files into a temporary array
    for mn in CameraModules:
        Movs = []
        for MOV in sorted(glob.glob("%s/%s/*.mov" % (__Input__, mn))):
            Movs.append( MovFile(MOV, mn) )
        __MOV_List__.append(Movs)

    # Sort MOV files
    while len(__MOV_List__) > 0:
        for MovArray in __MOV_List__:
            for MOV in MovArray:
                if not MOV.path in __State_List__:
                    __MOV_List_Optimized__.append(MOV)
                    __Total_Files__ += 1
                MovArray.pop(0)
                break
        if len(__MOV_List__[0]) <= 0:
            __MOV_List__.pop(0)

    # Debug output
    if not quietEnabled():
        ShowMessage("Extracting MOV files...")

    # Error handling
    if __Total_Files__ == 0:
        ShowMessage("No MOV files", 2)

    # Walk over file list
    for MOV in __MOV_List_Optimized__:
        if not quietEnabled():
            ShowMessage("Processing (%d/%d): %s..." % (__Processed_Files__, __Total_Files__, MOV.path))

        # Extract MOV file and catch exceptions
        try:

            # Extract mov file into jp4 and store failed images
            __extractMOV_Results__ = extractMOV(MOV.path, __Output__, __Trash__, MOV.module, __extractMOV_Results__)

            # Save state (used to resume process)
            if __State_File__:
                SaveState(__State_File__, __State_List__, MOV.path)

        except (IOError, MemoryError):
            ShowMessage("MOV extraction error", 2)
            traceback.print_exc()

        # Increment files index indicator
        __Processed_Files__ += 1

    # Filter check
    if not quietEnabled() and NO_FILTER == 0:
        # Debug output
        ShowMessage("Filtering images...")

        # Start image filtering
        filterImages(__Output__, __Trash__, __extractMOV_Results__)

    # Debug output
    if not quietEnabled():
        ShowMessage("Generating KML file...")

    # Generate KML file
    generateKML(__Output__, __KMLBase__)

    # Debug output
    ShowMessage("Done")

# Program entry point
if __name__ == "__main__":
    main(sys.argv[1:])
