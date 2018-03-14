#!/usr/bin/env python3

# -*- coding: utf-8 -*-

# SpreadRED - Create a database of torrent metadata from a Gazelle site
# Copyright (C) 2018  lights <lights@tutanota.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


"""Download a spreadsheet of metadata from a Gazelle tracker, utilizing a directory of torrents
obtained via collector feature (better solution to come if API improves).
"""

# TODO: Force update specific torrent ids or all
# TODO: Force a dev to write a snatched/uploaded API page, should be easy shit...

import re
import os
import sys
import json
import time
import html
import csv
import argparse
import sqlite3

from red import API, RequestException, LoginException

def main(args):
    """Download the metashit."""
    if not os.path.exists(os.path.join(sys.path[0], 'output')):
        os.mkdir(os.path.join(sys.path[0], 'output'))

    config = settings(args)  # Generate settings

    if args.export:
        export(config['export'])
        exit()

    try:
        red = API(config['username'], config['password'], config['session'])
    except LoginException as l_e:
        print('Failed to log in to RED. Please double check your credentials. {}'.format(l_e))
        exit()

    create_db()

    filelist = []
    torrentids = {}

    for root, _, files in os.walk(args.directory[0]):
        for tfile in files:
            if tfile.endswith('.torrent'):
                filelist.append(os.path.join(root, tfile))

    for file_ in filelist:
        result = re.search(r'\)-(\d+)\.torrent', file_,)
        if result:
            torrentids[file_] = result.group(1)

    for filename, torrentid in torrentids.items():
        # Check to see if torrent has already been indexed
        conn = sqlite3.connect(os.path.join(sys.path[0], 'output', 'SpreadRED.db'))
        cursor = conn.cursor()
        cursor.execute("""SELECT TorrentID FROM Torrents WHERE TorrentID = ?
                       UNION SELECT TorrentID FROM NonMusic WHERE TorrentID = ?""",
                       (torrentid, torrentid))
        if cursor.fetchone():
            continue

        try:
            info = red.get_torrent(torrentid)
        except RequestException:
            log('Failed to request torrent data for Torrent ID: {}, '
                'Filename: {}'.format(torrentid, filename))
            continue

        if not info or 'torrent' not in info or 'group' not in info:
            log('Could not fetch information for Torrent ID: {}, '
                'Filename: {}'.format(torrentid, filename))
            continue
        if info['group']['categoryId'] != 1:
            insert_non_music_db(info)
            log('Torrent ID {} (Filename: "{}") is not a music torrent, '
                'skipping...'.format(torrentid, filename))
            continue

        insert_db(info)

    log('Finished cataloguing releases.')
    export(config['export'])


def insert_db(info):
    """Insert information into the DB."""
    t = info['torrent']
    g = info['group']
    artistlist = []

    g['name'] = html.unescape(g['name'])

    if t['remastered']:
        ed_year, ed_title, label, catno = (t['remasterYear'], t['remasterTitle'],
                                           t['remasterRecordLabel'], t['remasterCatalogueNumber'])
    else:
        ed_year, ed_title, label, catno = (False, 'Original Release', g['recordLabel'], g['catalogueNumber'])

    conn = sqlite3.connect(os.path.join(sys.path[0], 'output', 'SpreadRED.db'))
    cursor = conn.cursor()
    cursor.execute('INSERT INTO Torrents VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                   (t['id'], g['name'], g['year'], ed_year, ed_title, label,
                    catno, t['size'], t['media'], t['format'], t['encoding'],
                    t['logScore'], t['hasCue'], t['infoHash']))

    for type_, alist in g['musicInfo'].items():
        for artist in alist:
            artist['name'] = html.unescape(artist['name'])
            cursor.execute('INSERT INTO ARTISTS VALUES (?, ?, ?, ?)',
                           (t['id'], artist['id'], type_, artist['name']))
            if type_ == 'artists':
                artistlist.append(artist['name'])

    for tag in g['tags']:
        cursor.execute('INSERT INTO Tags VALUES (?, ?)', (t['id'], tag))

    conn.commit()
    conn.close()

    log('Inserted Torrent ID {}: {} - {} ({}) [{}]'.format(t['id'], ', '.join(artistlist),
                                                            g['name'], g['year'], t['format']))


def insert_non_music_db(info):
    """Insert a non-music torrent ID into non-music DB."""
    conn = sqlite3.connect(os.path.join(sys.path[0], 'output', 'SpreadRED.db'))
    cursor = conn.cursor()
    cursor.execute('INSERT INTO NonMusic (TorrentID) VALUES (?)', (info['torrent']['id'],))
    conn.commit()
    conn.close()

def export(exportdir):
    """Export the database to a CSV file."""
    if os.path.exists(exportdir):
        os.remove(exportdir)

    with open(exportdir, 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='"')

        writer.writerow(['TorrentID', 'Artist(s)', 'Name', 'OriginalYear', 'EditionYear',
                         'EditionTitle', 'Label', 'CatalogNumber', 'Size', 'Source', 'Format',
                         'Encoding', 'Log', 'Cue', 'Tags', 'Infohash'])

        conn = sqlite3.connect(os.path.join(sys.path[0], 'output', 'SpreadRED.db'))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                TorrentID, Name, OriginalYear, EditionYear, EditionTitle, Label,
                CatalogNumber, Size, Source, Format, Encoding, Log, Cue, Infohash
            FROM Torrents
        """)
        torrents = cursor.fetchall()
        for t in torrents:
            cursor.execute('SELECT Name, Type FROM Artists WHERE TorrentID = ? AND '
                           '(Type = "artists" OR Type = "with")', (t['TorrentID'],))
            artists = cursor.fetchall()
            cursor.execute('SELECT GROUP_CONCAT(DISTINCT Name) AS Tag FROM Tags '
                           'WHERE TorrentID = ?', (t['TorrentID'],))
            t_row = cursor.fetchone()
            tags = t_row['Tag'] if t_row else ''

            main_artists = []
            guest_artists = []
            for artist in artists:
                if artist['Type'] == 'artists':
                    main_artists.append(artist['Name'])
                else:
                    guest_artists.append(artist['Name'])

            artists = ', '.join(main_artists)
            if guest_artists:
                artists += ' (feat. ' + ', '.join(guest_artists) + ')'

            edition_title = t['EditionTitle']
            label = t['Label']
            catalog_number = t['CatalogNumber']

            writer.writerow([t['TorrentID'], artists, t['Name'], t['OriginalYear'],
                             t['EditionYear'], edition_title, label, catalog_number,
                             t['Size'], t['Source'], t['Format'], t['Encoding'],
                             t['Log'], t['Cue'], tags, t['Infohash']])

        log('Exported DB to CSV')


def settings(args):
    """Get settings from config or arguments."""
    with open(os.path.join(sys.path[0], 'config.json'), 'r') as conf_file:
        config = json.load(conf_file)

    settings_ = {
        'username': args.username,
        'password': args.password,
        'session': args.session,
        'export': config['export'],
    }

    for key, value in settings_.items():
        if not value:
            if key == 'export':
                settings_[key] = os.path.join(sys.path[0], 'output', 'SpreadRED.csv')
            else:
                settings_[key] = config[key]

    if args.export:
        path = os.path.dirname(settings_['export'])
        if os.path.exists(path):
            return settings_
        print('{} does not exist, exiting...'.format(path))
        exit()

    if (not settings_['username'] or not settings_['password']) and not settings_['session']:
        print('Invalid login credentials.')
        exit()

    if not args.directory:
        print('A directory for .torrent files must be specified')
        exit()

    if not os.path.exists(args.directory[0]):
        print('Error: {} does not exist!'.format(args.directory[0]))
        exit()

    return settings_


def create_db():
    """Create the database to store the torrent metainfo."""
    conn = sqlite3.connect(os.path.join(sys.path[0], 'output', 'SpreadRED.db'))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Torrents (
            TorrentID INT PRIMARY KEY NOT NULL,
            Name TEXT NOT NULL,
            OriginalYear INT,
            EditionYear INT,
            EditionTitle TEXT,
            Label TEXT,
            CatalogNumber TEXT,
            Size INT NOT NULL,
            Source TEXT,
            Format TEXT NOT NULL,
            Encoding TEXT NOT NULL,
            Log TEXT,
            Cue BOOLEAN,
            Infohash TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Artists (
            TorrentID INT NOT NULL,
            ArtistID INT NOT NULL,
            Type TEXT NOT NULL,
            Name TEXT NOT NULL,
            PRIMARY KEY (TorrentID, ArtistID, Type)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Tags (
            TorrentID INT NOT NULL,
            Name TEXT NOT NULL,
            PRIMARY KEY (TorrentID, Name)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS NonMusic (
            TorrentID INT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def log(line):
    """Log a line to the log file and print it."""
    with open(os.path.join(sys.path[0], 'output', 'SpreadRED.log'), 'a') as logfile:
        logfile.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + line + '\n')
    print(line)


def parse_args():
    """Argument parser."""
    description = 'SpreadRED: Tool to create a database of metadata from seeding/snatched ' \
        'lists, using the Gazelle API and a folder of downloaded .torrents. By default, ' \
        'it will export a CSV file with the information.'

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('directory', help='Directory of .torrent files', nargs='?')
    parser.add_argument('-u', '--username', help='Username of Gazelle site', nargs=1)
    parser.add_argument('-p', '--password', help='Password to Gazelle site', nargs=1)
    parser.add_argument('-s', '--session', help='Session to Gazelle site', nargs=1)
    parser.add_argument('-e', '--export', help='Only export CSV of data, do not index torrents.', action="store_true")

    return parser.parse_args()

if __name__ == '__main__':
    main(parse_args())
