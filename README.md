## elphel-mov-splitter<br />Elphel MOV to jp4 splitter.

>Elphel MOV to jp4 splitter.

### Description
This tool split all MOV files created by the Elphel Eyesis 4π camera into JP4 files, and also generates a KML file

### Dependencies

#### Details

1. [python-pip](https://pypi.python.org/pypi/pip)
2. [exifread](https://pypi.python.org/pypi/ExifRead)

#### Installation

    sudo apt-get install python-pip
    sudo pip install exifread

### Usage
    Usage: mov_splitter.py <Input folder> <Output folder> <Trash Folder> <KML base URL> [Debug 0/1] [Quiet 0/1]

### Example usage scenario
    ./mov_splitter.py data/footage/run1/mov /data/footage/run1/0 /data/footage/run1/trash "http://127.0.0.1/footage/run1/0/"

### Copyright

Copyright (c) 2014 FOXEL SA - [http://foxel.ch](http://foxel.ch)<br />
This program is part of the FOXEL project <[http://foxel.ch](http://foxel.ch)>.

Please read the [COPYRIGHT.md](COPYRIGHT.md) file for more information.


### License

This program is licensed under the terms of the
[GNU Affero General Public License v3](http://www.gnu.org/licenses/agpl.html)
(GNU AGPL), with two additional terms. The content is licensed under the terms
of the
[Creative Commons Attribution-ShareAlike 4.0 International](http://creativecommons.org/licenses/by-sa/4.0/)
(CC BY-SA) license.

Please read <[http://foxel.ch/license](http://foxel.ch/license)> for more
information.
