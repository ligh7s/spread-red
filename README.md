# SpreadRED

python3 tool to create a database of metadata from seeding/snatched lists,
using the Gazelle API and a folder of downloaded .torrents. By default, it
will export a CSV file with the information.

## Requirements
* python3
* requests module

## Config
* Username: Your Redacted username
* Password: Your Redacted password
* Session: Your Redacted session cookie _(Use to bypass 2FA, refer to 2FA block)_
* Export: Export directory for the csv _(optional)_

## How-To
* Download script ```git clone https://github.com/ligh7s/spread-red```
* Enter directory of script ```cd spread-red```
* Install requirements ```pip3 install --user -r requirements.txt```
* Rename ```config.json.txt``` to ```config.json```
* Configure credentials/settings per Config block
* Download .zip of torrents using Redacted's collector feature _(PU+ perk)_
* Extract .zip to folder
* Run script on folder ```python3 spreadred.py "~/Downloads/light's Seeding Torrents"``` _(remember: escape spaces)_
* Check output directory in spread-red folder for database, csv, and log when finished

## 2FA

You cannot log in normally with a username and password if 2FA is enabled. Therefore, you must copy
a session cookie from an already-logged in session (typically your browser RED session), and use
that in your config. If you are using the session cookie, leave the ```username``` and
```password``` values blank.

## Versions

### 1.2

Added --force-overwrite flag, usable to re-index every torrent the script comes across.  
Also added an except for unicode log/print errors, so the script doesn't crash when it
fails to write a strange character.

### 1.1

Added torrent description to database. To update from v1.0, run the `release-1.1.py` script in
`migrations/`, supplying the path of your database file (default: `output/SpreadRED.db`)
as an argument.

### 1.0

Initial release, most of what's described in the README was added here.

## Usage

    usage: spreadred.py [-h] [-u USERNAME] [-p PASSWORD] [-s SESSION] [-e]
                [directory]

    SpreadRED: Tool to create a database of metadata from seeding/snatched lists,
    using the Gazelle API and a folder of downloaded .torrents. By default, it
    will export a CSV file with the information.

    positional arguments:
      directory             Directory of .torrent files

    optional arguments:
      -h, --help            show this help message and exit
      -u USERNAME, --username USERNAME
                Username of Gazelle site
      -p PASSWORD, --password PASSWORD
                Password to Gazelle site
      -s SESSION, --session SESSION
                Session to Gazelle site
      -f, --force-update    Force update all torrents in the specified folder.
      -e, --export          Only export CSV of data, do not index torrents.
