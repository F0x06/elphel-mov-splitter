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

mkdir -p $2
mkdir -p $3

echo "Step 1 extracting files..."
for d in $1/*
do
	dir=$(basename $d)

	if [ -d $d ]; then
		echo "Processing folder $dir..." 
		for f in $d/*.mov
		do
			filename=$(basename "$f")
			timestamp="${filename%.*}"
			if [ -f $f ]; then
				echo "Extracting $f..."
				hachoir-subfile --parser=jpeg $f $2 &> /dev/null
				echo "Renamming files..."
				exiftool "-filename<\${DateTimeOriginal}_\${SubSecTimeOriginal}_$dir.jp4" -d %s -q -q -m $2/file-*
			fi
		done
	fi
done

echo "Step 2 filtering files..."
for f in $2/*.jp4; do

	filename=$(basename $f)
	timestamp_full=${filename%.*}
	timestamp=$(echo $timestamp_full | cut -d'_' -f 1-2)

	if [ -f $f ]; then
		for i in $(seq 1 9); do 
			filepath=`echo -e -n "$2/$timestamp" && echo -e -n "_$i.jp4"`

			if [ -f $filepath ]; then
				continue
			else
				echo "Incomplete timestamp $timestamp"
				mv $2/$timestamp* $3/
				break
			fi
		done
	fi
done