## elphel-mov-splitter<br />Elphel MOV to jp4 splitter using hachoir.

>Elphel MOV to jp4 splitter using hachoir.

### Requirements

#### Details

1. [hachoir-subfile](https://bitbucket.org/haypo/hachoir/wiki/hachoir-subfile)
2. [python-pip](https://pypi.python.org/pypi/pip)
3. [exifread](https://pypi.python.org/pypi/ExifRead)

#### Installation

    sudo apt-get install hachoir-subfile python-pip
    sudo pip install exifread

### Usage
    Usage: mov_splitter.py <Input folder> <Output folder> <Trash Folder>

### Example usage scenario
    ./mov_splitter.py /data/footage/run1/mov /data/footage/run1/0 /data/footage/run1/trash
