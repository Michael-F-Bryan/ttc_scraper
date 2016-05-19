import os
from .spider import ForumSpider


def main():
    spidey = ForumSpider(thread_number=2)

    spidey.database_location = os.path.abspath('./records.sqlite')
    spidey.username = 'kyleaurisch'
    spidey.password =  'lancer12'

    spidey.run()

if __name__ == "__main__":
    main()
