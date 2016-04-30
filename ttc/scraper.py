from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
import re
import os
import errno
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor, as_completed, wait

from .utils import humansize, BrowserError, LoginError, mkdir
from . import logger


class Browser:
    base_url = 'http://sae.wsu.edu/ttc/'
    
    def __init__(self, username, password, save_folder=None, force=False, 
                 workers=15, be_courteous=False):
        logger.info('Initialising')
        
        self.username = username
        self.password = password
        self.save_folder = save_folder or os.path.abspath('./downloads')
        self.force = force
        self.workers = workers
        self.be_courteous = be_courteous
        
        mkdir(self.save_folder)
        
        self.session = requests.session()
        
    def login(self):
        """Logs into the TTC forum using the provided credentials."""
        logger.info('Logging in')
        
        r = self.session.get(self.base_url)
        soup = BeautifulSoup(r.text, 'html.parser')
            
        form = soup.find(class_='quick-login').parent
        href = urljoin(self.base_url, form['action'])
        
        payload = {
            'username': self.username,
            'password': self.password,
            'login': 'Login',
        }
        # Send the actual login POST request
        self.session.post(href, data=payload)
        
        # Now double check that we logged in successfully
        r = self.session.get(urljoin(self.base_url, 'index.php'))
        soup = BeautifulSoup(r.text, 'html.parser')
        
        forum_titles = [x.text for x in soup.find_all(class_='forumtitle')]
        if 'All Users Must Register' in forum_titles:
            logger.error('Login unsuccessful')
            raise LoginError('Login unsuccessful')
        else:
            logger.info('Login successful')
            
    def testing_rounds(self):
        """
        Get links to each of the testing rounds' individual forums.
        """
        logger.info('Getting links to each round')
        
        r = self.session.get(self.base_url + 'index.php')
        soup = BeautifulSoup(r.text, 'html.parser')
        
        forum_titles = soup.find_all(class_='forumtitle')
        for title in forum_titles:
            if 'Tire Testing' == title.text:
                testing_form = urljoin(self.base_url, title['href'])
                break
        else:
            raise BrowserError('Could not find the "Tire Testing" forum. Are you logged in?')
            
        r = self.session.get(testing_form)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        forum_titles = soup.find_all(class_='forumtitle')
        
        links = []
        for title in forum_titles:
            url = urljoin(self.base_url, title['href'])
            links.extend(self.get_data_links(url))
            
        logger.info('{} links found'.format(len(links)))
        for link in links:
            logger.debug(link)
        return links
            
    def get_data_links(self, forum_url):
        """
        From each testing round's forum, get each of the posts which
        contain testing data.
        """
        logger.debug('Getting posts for forum: {}'.format(forum_url))
        
        pattern = re.compile(r'Round (\d+) Data$')
        r = self.session.get(forum_url)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        topic_titles = soup.find_all(class_='topictitle')
        links = []
        for title in topic_titles:
            res = pattern.search(title.text)
            if res is not None:
                links.append(title)
               
        hrefs = [urljoin(self.base_url, x['href']) for x in links]
        for href in hrefs:
            logger.debug('Post found: {}'.format(href))
        return hrefs
    
    def scrape_round(self, round_url):
        """
        Given a testing round post's url, find all the downloadable files.
        """
        DownloadLink = namedtuple('DownloadLink', ['round', 'filename', 'link'])
        
        r = self.session.get(round_url)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        round_title = re.search(r'\d+', soup.find(id='page-body').h2.text).group()
        logger.info('Getting download links for round {}'.format(round_title))

        download_links = soup.find_all(href=re.compile(r'download'))
        links = []
        for link in download_links:
            temp = DownloadLink(round_title, 
                                link.text,
                                urljoin(self.base_url, link['href']))
            links.append(temp)
            
        for link in links:
            logger.debug('Download found: {}'.format(link))
        return links
    
    def download(self, download_link):
        """
        Given a DownloadLink namedtuple, create it's parent 
        folder and download it.
        
        Download the entire file and hold it in memory until the
        download is complete. This prevents us from having any
        incomplete downloads cluttering the filesystem.
        
        Note
        ----
        When run in parallel mode with a large number of worker
        threads this could potentially use a large amount of RAM.
        """
        logger.info('Downloading {}'.format(download_link))
        
        download_folder = os.path.join(self.save_folder, 
                              'Round_{}'.format(download_link.round))
        mkdir(download_folder)
        filename = os.path.join(download_folder, download_link.filename)
        
        if os.path.exists(filename) and not self.force:
            logger.info('File already exists: {}'.format(filename))
            return 0
        

        r = self.session.get(download_link.link)
        
        with open(filename, 'wb') as f:
            f.write(r.content)
        
        logger.info('{} downloaded for Round {}, {}'.format(
                humansize(len(r.content)),
                download_link.round,
                download_link.filename))
        return len(r.content)
    
    def _start_sequential(self):
        """
        Do all downloads and page scraping sequentially.
        
        This is good for rate limiting and when you are either
        testing something out or don't want to be mean to the
        TTC forum by hogging all its bandwidth.
        """
        logger.inf('Starting in  mode')
        
        self.login()
        round_links = b.testing_rounds()
        
        files = []
        for round_link in round_links:
            temp = self.scrape_round(round_link)
            files.extend(temp)
            
        total_downloads = 0
        for file in files:
            size = self.download(file)
            total_downloads += size
            
        return total_downloads
        
    def _start_concurrent(self):
        """
        Do all page scraping and downloads in parallel.
        
        This is the default download method, it's good if
        you have fast download speed and if you want to
        download everything as quickly as possible.
        """
        logger.info('Starting in concurrent mode')
        
        pool = ThreadPoolExecutor(max_workers=self.workers)
        self.login()
        round_links = b.testing_rounds()
        
        futures = []
        for link in round_links:
            fut = pool.submit(self.scrape_round, link)
            futures.append(fut)
            
        download_links = []
        for future in as_completed(futures):
            download_links.extend(future.result())
            
        futures = []
        for download_link in download_links:
            fut = pool.submit(self.download, download_link)
            futures.append(fut)
            
        total_bytes = 0
        for future in as_completed(futures):
            download_size = future.result()
            total_bytes += download_size
            print(download_size)
            
        logger.info('Total bytes downloaded: {}'.format(humansize(total_bytes)))
        return total_bytes

    def start(self):
        """
        A proxy for Browser._start_sequential or Browser._start_concurrent
        depending on the value of `be_courteous`.
        """
        if be_courteous:
            self.start = self._start_sequential
        else:
            self.start = self._start_concurrent
