#!/usr/bin/env python3

"""This migration reflects the 1.1 release of SpreadRED,
and adds a Description column to the torrent database.
"""

import os
import sys
import sqlite3

if len(sys.argv) != 2:
    exit('You must specify the .db directory as an argument.')
database_path = os.path.abspath(sys.argv[1])
if not os.path.exists(database_path):
    exit('{} does not exist, please verify that it is the correct'
         'path to the database.'.format(database_path))

conn = sqlite3.connect(database_path)
cursor = conn.cursor()
cursor.execute('ALTER TABLE Torrents ADD Column Description TEXT')
conn.commit()
conn.close()

print('Upgraded database to version 1.1')
