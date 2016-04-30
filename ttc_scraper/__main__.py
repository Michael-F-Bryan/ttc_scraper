import argparse

from . import Browser


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--destination', dest='destination', type=str,
            default=None, help='Folder to save TTC data to (default: ./downloads)')
    parser.add_argument('-w', '--workers', dest='workers', type=int,
            default=10, help='Number of files to download in parallel (default: 10)')
    parser.add_argument('-f', '--force', dest='force', default=False, 
            action='store_true', help='Overwrite files if they already exist '
                   '(default: False)')
    parser.add_argument('-c', '--courteous', dest='courteous', default=False,
            action='store_true', help="Be nice to the TTC website and don't "
            'overload them with a heap of downloads all of a sudden '
            '(default: False, of course)')
    parser.add_argument('username', type=str,
            help='The username to log into the forum with')
    parser.add_argument('password', type=str,
            help='Your password for the TTC forum')

    args = parser.parse_args()

    b = Browser(
            username=args.username,
            password=args.password,
            save_folder=args.destination,
            force=args.force,
            workers=args.workers,
            be_courteous=args.courteous,
    )
    b.start()


if __name__ == "__main__":
    main()
