import logging
from urllib.parse import urljoin
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, ProgrammingError, InvalidRequestError
from bs4 import BeautifulSoup

from grab.spider import Spider, Task
from grab import Grab
from weblib.error import DataNotFound
from utils.misc import get_logger, humansize, innerHTML

from .models import Base, Forum, Thread, Url, Post, Attachment



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
        self.base_url = 'http://sae.wsu.edu/ttc/'

        log_level = logging.DEBUG if getattr(self, 'debug', False) else logging.INFO
        self.logger = get_logger(__name__, 'stderr', log_level=log_level)

        self.engine = create_engine('sqlite:///{}'.format(self.database_location),
                connect_args={'check_same_thread':False})

        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)  
        self.session = self.Session()

        self.visited_urls = set()

    def task_initial(self, grab, task):
        self.logger.info('Logging in')

        g = Grab(user_agent='ttc_scraper')
        g.go(self.base_url)
        g.doc.set_input('username', self.username)
        g.doc.set_input('password', self.password)
        g.doc.submit()

        elem = g.doc.select('//a[contains(text(),"All Users Must Register")]')

        if len(elem):
            self.logger.error('Login failed')
            raise RuntimeError('Login failed')
        else:
            self.cookies = g.cookies
            self.logger.info('Login successful')

        if not self.already_checked(self.base_url):
            yield Task('forum', url=self.base_url, title='Main Forum')

    def task_forum(self, grab, task):
        if not hasattr(task, 'forum_id'):
            # Add the forum to our database
            parent_id = getattr(task, 'parent_id', None)
            new_forum = Forum(name=task.title, link=task.url, parent_id=parent_id)
            self.session.add(new_forum)
            self.session.commit()
            self.logger.debug('Forum created: {}'.format(new_forum))
        else:
            new_forum = self.session.query(Forum).filter(Forum.id ==
                    task.forum_id).first()

        self.logger.info('Reading forum: {} (page {})'.format(task.title,
                getattr(task, 'page', 1)))

        # Check all the forums we find
        for elem in grab.doc.select('//a[@class="forumtitle"]'):
            link = urljoin(self.base_url, elem.attr('href'))
            self.logger.debug('Found forum: {}'.format(link))

            if not self.already_checked(link):
                yield Task('forum', url=link, 
                        title=elem.text(), 
                        parent_id=new_forum.id)

        # Check all the threads we find
        for elem in grab.doc.select('//a[@class="topictitle"]'):
            link = urljoin(self.base_url, elem.attr('href'))
            self.logger.debug('Found thread: {}'.format(link))

            if not self.already_checked(link):
                yield Task('thread', 
                        url=link, 
                        title=elem.text(), 
                        forum=task.title,
                        forum_id=new_forum.id)

        # Now queue the other pages of this Forum
        pager = grab.doc.select('//div[@class="pagination"]')
        paginations = self.pagination_links(pager)

        for link, page in paginations:
            link = urljoin(task.url, link)

            if not self.already_checked(link):
                yield Task('forum', 
                        url=link, 
                        title=elem.text(), 
                        parent_id=parent_id,
                        forum_id=new_forum.id,
                        page=page)


    def task_thread(self, grab, task):
        if not hasattr(task, 'thread_id'):
            current_thread = Thread(
                    name=task.title,
                    link=task.url,
                    forum_id=task.forum_id)
            self.session.add(current_thread)
            self.session.commit()
            self.logger.debug('Thread created: {}'.format(current_thread))
        else:
            current_thread = self.session.query(Thread).filter(Thread.id ==
                    task.thread_id).first()

        self.logger.info('Checking thread: {} (page {})'.format(current_thread.name,
            getattr(task, 'page', 1)))

        soup = BeautifulSoup(grab.response.body, 'html.parser')

        # Iterate through the posts, saving them
        for elem in soup.find_all(class_='postbody'):
            author_tag = elem.find(class_='author')
            author = author_tag.strong.text
            created = author_tag.text.split('»')[-1].strip()
            content = innerHTML(elem.find(class_='content'))

            new_post = Post(
                   author=author,
                   created=created,
                   content=content,
                   thread_id=current_thread.id)

            self.session.add(new_post)
            self.session.commit()
            self.logger.debug('Post created: {}'.format(new_post))

            # look for inline attachments
            inline_attachments = soup.find_all('dl', class_='file'):
                for thing in inline_attachments:
                    # Do the appropriate thing for all possible types of
                    # inline attachment
                    if thing.dt['class'] == 'attach-image':
                        img = thing.dt.img
                        link = urljoin(task.url, img['href'])

                        new_attachment = Attachment(
                                name=img['alt'], 
                                link=link)
                        new_attachment.post_id = new_post.id
                        self.session.add(new_attachment)
                        self.session.commit()
                    else:
                        logger.error('Found new type of line attachment: {}'.format(
                            thing.dt['class']))
                        logger.error('\n\n{}\n\n'.format(thing.prettify()))

            # Check if there were any attachments
            attach_box = elem.find(class_='attachbox')
            if attach_box is not None:
                for thing in attach_box.find_all(class_='postlink'):
                    link = urljoin(task.url, thing['href'])
                    name = thing.text

                    new_attachment = Attachment(name=name, link=link)
                    new_attachment.post_id = new_post.id
                    self.session.add(new_attachment)
                    self.session.commit()

                    self.logger.info('Attachment found: {}'.format(new_attachment))

        # Now queue the other pages of this thread
        pager = grab.doc.select('//div[@class="pagination"]')
        paginations = self.pagination_links(pager)

        for link, page in paginations:
            link = urljoin(task.url, link)

            if not self.already_checked(link):
                yield Task('thread', 
                        url=link, 
                        title=task.title, 
                        forum=task.forum,
                        forum_id=task.forum_id,
                        thread_id=current_thread.id,
                        page=page)

    def already_checked(self, url):
        if url in self.visited_urls:
            return True
        else:
            try:
                new_url = Url(link=url)
                self.session.add(new_url)
                self.session.commit()
                self.visited_urls.add(url)
                return False
            except (IntegrityError, InvalidRequestError):
                self.session.rollback()
                return True

    def pagination_links(self, pagination_element):
        for elem in pagination_element.select('span/a'):
            yield (elem.attr('href'), elem.text())
