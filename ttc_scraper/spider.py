import logging
from urllib.parse import urljoin
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from grab.spider import Spider, Task
from grab import Grab
from weblib.error import DataNotFound
from utils.misc import get_logger, humansize

from .models import Base, Forum, Post




class ForumSpider(Spider):
    initial_urls = ['http://sae.wsu.edu/ttc/']

    def create_grab_instance(self, **kwargs):
        """
        Because we're logging in, we need to set the user agent and copy
        across the cookies we were given on login.
        """
        g = super().create_grab_instance(**kwargs)
        g.setup(user_agent='ttc_scraper')

        cookies = getattr(self, 'cookies', None)
        if cookies:
            g.cookies = cookies

        return g

    def prepare(self):
        self.logger = get_logger(__name__, 'stderr')
        self.logger.setLevel(logging.DEBUG)
        self.base_url = 'http://sae.wsu.edu/ttc/'

        self.engine = create_engine('sqlite:///{}'.format(self.database_location))

        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)  
        self.session = self.Session()

    def task_initial(self, grab, task):
        self.logger.info('Logging in')

        g = Grab(user_agent='ttc_scraper')
        g.go(self.base_url)
        g.doc.set_input('username', 'kyleaurisch')
        g.doc.set_input('password', 'lancer12')
        g.doc.submit()

        elem = g.doc.select('//a[contains(text(), "All Users Must Register")]')

        if len(elem):
            self.logger.error('Login failed')
            raise RuntimeError('Login failed')
        else:
            self.cookies = g.cookies
            self.logger.info('Login successful')

        yield Task('forum', url=self.base_url, title='Main Forum')

    def task_forum(self, grab, task):
        self.logger.info('Checking forum page: {}'.format(task.title))

        # Check all the forums we find
        for elem in grab.doc.select('//a[@class="forumtitle"]'):
            new_forum_name = task.name + '/' + elem.text()
            link = urljoin(self.base_url, elem.attr('href'))
            self.logger.debug('Found forum: {}'.format(link))
            yield Task('forum', url=link, title=new_forum_name)

        # Check all the threads we find
        for elem in grab.doc.select('//a[@class="topictitle"]'):
            link = urljoin(self.base_url, elem.attr('href'))
            self.logger.debug('Found thread: {}'.format(link))
            yield Task('thread', url=link, title=elem.text(), forum=task.title)

    def task_thread(self, grab, task):
        self.logger.info('Checking thread "{}" from "{}"'.format(task.title, 
            task.forum))
