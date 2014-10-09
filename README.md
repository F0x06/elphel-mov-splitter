## elphel-mov-splitter<br />Elphel MOV to jp4 splitter.

>Elphel MOV to jp4 splitter.

### Description
This tool split all MOV files created by the Elphel Eyesis 4π camera into JP4 files, and also generates a KML file

### Table of Contents
- [Elphel MOV to jp4 splitter.](#user-content-elphel-mov-splitterelphel-mov-to-jp4-splitter)
    - [Dependencies](#user-content-dependencies)
        - [Details](#user-content-details)
        - [Installation](#user-content-installation)
    - [Usage](#user-content-usage)
    - [Example usage scenario](#user-content-example-usage-scenario)
    - [Copyright](#user-content-copyright)
    - [License](#user-content-license)

### Dependencies

#### Details

1. [python-pip](https://pypi.python.org/pypi/pip)
2. [exifread](https://pypi.python.org/pypi/ExifRead)

#### Installation

    sudo apt-get install python-pip
    sudo pip install exifread

### Usage
    Usage: ./mov_splitter.py [OPTIONS]

    [Required arguments]
    -f --folder         Base working folder (where mov, jp4, trash are)
    [and/or]
    -i --input          Input MOV folder
    -o --output         Output JP4 folder
    -t --trash          JP4 trash folder

    [Optional arguments]
    -h --help           Prints this

    -c --count          Don't extract MOV files, just count images
    -m --maxfiles       Max JP4 files per folder, will create folders 0, 1, 2, 3 to place next files
    -k --kmlbase        KML base url
    -s --state          State files folder (to save/resume job)
    -l --logfile        Log file path
    -f --nofilter       Don't filter images (trashing)

    -d --debug          Debug mode
    -q --quiet          Quiet mode (Silent)
    -n --nocolors       Disable stdout colors



### Example usage scenarios
    ./mov_splitter.py -i data/footage/run1/mov -o /data/footage/run1/0 -t /data/footage/run1/trash
or

    ./mov_splitter.py -f data/footage/run1

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
