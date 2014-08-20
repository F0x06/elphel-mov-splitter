#!/bin/bash
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

if [ "$#" -ne 3 ]; then
    echo "Usage: $(basename $0) <Input folder> <Output folder> <Trash Folder>"
    exit
fi

# Remove slashs at the end of paths for a fancy output
input=${1%/}
output=${2%/}
trash=${3%/}

# Create destination directories
mkdir -p $output
mkdir -p $trash

# Statistics timer initializer
stats_start=$(date +%s.%N)

# Extracting jp4 files from MOV files
echo "Step 1 splitting MOV files..."
for d in $input/*
do
	dir=$(basename $d)

	if [ -d $d ]; then
		echo "Processing camera module $dir..."
		for f in $d/*.mov
		do
			filename=$(basename "$f")
			timestamp="${filename%.*}"
			if [ -f $f ]; then
				echo "Extracting $f..."
				hachoir-subfile --parser=jpeg $f $output &> /dev/null
				echo "Renaming files..."
				exiftool "-filename<\${DateTimeOriginal}_\${SubSecTimeOriginal}_$dir.jp4" -d %s -q -q -m $output/file-*
			fi
		done
	fi
done

# Filter jp4 images, move to trash folder all sequences with missing images (Need to have 9 images per-timestamp)
echo "Step 2 filtering jp4 files..."
for f in $output/*.jp4; do

	filename=$(basename $f)
	timestamp_full=${filename%.*}
	timestamp=$(echo $timestamp_full | cut -d'_' -f 1-2)

	if [ -f $f ]; then
		for i in $(seq 1 9); do
			filepath=`echo -e -n "$output/$timestamp" && echo -e -n "_$i.jp4"`

			if [ -f $filepath ]; then
				continue
			else
				echo "Incomplete timestamp $timestamp"
				mv $output/$timestamp* $trash/
				break
			fi
		done
	fi
done

# Display statistics
stats_end=$(date +%s.%N)
run_time=$(python -c "print '%02um:%02us' % ((${stats_end} - ${stats_start})/60, (${stats_end} - ${stats_start})%60)")

echo "Done in $run_time, $(find $output -type f -iname *.jp4 | wc -l) images splitted ($(du -sh $output | cut -f 1))," \
"$(find $trash -type f -iname *.jp4 | wc -l) images trashed ($(du -sh $trash | cut -f 1))"