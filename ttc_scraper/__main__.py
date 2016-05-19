import os
import argparse

from . import __version__
from .spider import ForumSpider



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('username', type=str, help='Your username')
    parser.add_argument('password', type=str, help='Your password')
    parser.add_argument('-V', '--version', dest='version', action='store_true',
                        help='Print the version number')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                        help='Print verbose output to the terminal')
    parser.add_argument('-d', '--database', dest='database', type=str,
                        help='Where to store the data scraped from the TTC forum')

    args = parser.parse_args()

    if args.version:
        print('{} v{}'.format(__package__, __version__))
        exit()

    spidey = ForumSpider(thread_number=2)

    spidey.database_location = os.path.abspath(args.database or 
            './records.sqlite')

    spidey.username = args.username
    spidey.password = args.password

    if args.verbose:
        spidey.debug = True
        spidey.log_file = 'stderr'
    else:
        spidey.debug = False
        spidey.log_file = 'crawler.log'

    spidey.run()

if __name__ == "__main__":
    main()
