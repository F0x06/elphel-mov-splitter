## elphel-mov-splitter<br />Elphel MOV to jp4 splitter using hachoir.

>Elphel MOV to jp4 splitter using hachoir.

### Requirements

#### Details

1. [hachoir-subfile](https://bitbucket.org/haypo/hachoir/wiki/hachoir-subfile)
2. [exiftool](http://www.sno.phy.queensu.ca/~phil/exiftool/)

#### Installation

    sudo apt-get install hachoir-subfile exiftool

### Usage
    Usage: mov_splitter.sh <Input folder> <Output folder> <Trash Folder>

### Example usage scenario
    ./mov_splitter.sh /data/footage/run1/mov /data/footage/run1/0 /data/footage/run1/trash
