import argparse
from src.spreadred import main


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
