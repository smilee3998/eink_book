import logging
import sys
from argparse import ArgumentParser
from multiprocessing import Queue
from time import sleep, time

from PyQt5.QtWidgets import QApplication

import content
from book import Book, VirtualBook
from constants import log_file_path
from socialmedia_scraper.social_media_scraper import SocialMediaScraper

if not log_file_path.exists():
    log_file_path.touch(exist_ok=True)
    
logging.basicConfig(
                    # filename=str(log_file_path),
                    # filemode='w',
                    level=logging.INFO,
                    format='%(levelname)s - %(name)s - %(funcName)s - %(message)s',
                    datefmt='%H:%M:%S')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter(fmt='%(asctime)s - %(name)-12s - %(funcName)s: \t%(message)s', datefmt='%d-%b %H:%M:%S', )
console.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(console)


def eink_main():
    ##### Important if update this function, should also update VirtualBookUpdate.run #####
    # import content
    news = content.NewsClient()
    
    start_time = time()
    fetch_time = time()
    first = True
    
    while True:
        if first:
            book.add_left_home_page(content.create_page_left_home(news.get_random_headlines()))
            book.add_right_pages(content.load_existing_pages())
            book.show_home_page()  # display home page

        if book.fetch and (time() - fetch_time > 60*60 or first):
            book.logger.info('hi')
            # fetch from social media
            book.social_media_scraper.scrape()           
            fetch_time = time()
            # add pages and create notify when there are updates
            book.check_update()
        first = False

        if time() - start_time > 60:
            # update data on left page
            content.left_page_data_time_update()
            if book.get_current_showing_status():
                # Check is the book showing notification, put to notify page            
                book.logger.info(f'showing status: {book.get_current_showing_status()}')
                book.show_notify_page()
            
            else:
                book.add_left_home_page(content.create_page_left_home(news.get_random_headlines()))
                book.show_left_home_page()
            start_time = time()
            
        # book.check_update()
        sleep(30)
            
                       
                    
if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--novirtual', help='run program with eink display', action='store_true', default=False)
    parser.add_argument('-d', '--demo', help='Use demo photo', action='store_true', default=False)
    parser.add_argument('-f', '--fetch', help='Fetech photos from social media', action='store_true', default=False)
    parser.add_argument('-allclean', help='Clean start: clean all cache and pages', action='store_true', default=False)
    
    args = parser.parse_args()

    queue = Queue(maxsize=1)
    if args.allclean:
        content.clear_existing_page()

    social_media_scraper = SocialMediaScraper(args.fetch)

    if args.novirtual:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)

        book = Book(queue, demo=args.demo, 
                    social_media_scraper=social_media_scraper, 
                    fetch=args.fetch
                    )

        try:
            eink_main()
        finally:
            if args.fetch:
                social_media_scraper.logout()

    else:
        logger.info('Using virtual display')
        app = QApplication([])
        vbook = VirtualBook(args.demo, social_media_scraper, args.fetch)

        vbook.show()

        try:
            sys.exit(app.exec())
        except Exception as e:
            logger.error(e)
        finally:
            if args.fetch:
                social_media_scraper.logout()


