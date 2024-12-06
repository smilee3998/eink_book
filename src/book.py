import os
from logging import getLogger
from multiprocessing import Queue
from pathlib import Path
from threading import Thread
from time import monotonic, sleep, time
from typing import List, Optional

from PIL import Image
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMainWindow

import content
from constants import *
from content import create_page_left_notify, create_pages
from flip_gui import Ui_MainWindow

try:
    import RPi.GPIO as GPIO
    from IT8951 import constants
    from IT8951.display import AutoEPDDisplay
except ModuleNotFoundError as e:
    print('Ignore this if running virtually')
    

class GeneralBook:
    """This class contain the functions that are useful for both book and virtual book
    """     
    def __init__(self) -> None:
        self.current_page = HOME_PAGE_NUM
        self.left_page_list = [None, None]
        self.right_page_list = []
        self.showing_notification = False

    def add_left_home_page(self, left_page_path: Path) -> None:
        """add the page to the first page of the left screen

        Args:
            left_page_path (Path): a path to the image of the left hoem page 
        """        
        self.left_page_list[HOME_PAGE_NUM] = left_page_path

    def has_next_page(self) -> bool:
        """a helper function to check if there is a next page available

        Returns:
            bool: is currently at the last page 
        """        
        return self.current_page != len(self.right_page_list) - 1 and not len(self.right_page_list) == 0

    def has_previous_page(self) -> bool:
        """a helper function to check if there is a previous page available

        Returns:
            bool: is currently at the first page
        """        
        return self.current_page != HOME_PAGE_NUM

    def add_right_pages(self, page: List[Path]) -> None: 
        """add a list of pages to the right page list

        Args:
            page (List[Path]): a list of pages to add 
        """               
        if len(page) != 0:
            self.right_page_list.extend(page)
            self.logger.info(f'now have {len(self.right_page_list)} pages')

    def next_page(self) -> None:
        """move to next page if there is next page
        """        
        self.logger.debug('Going to next page')
        if self.has_next_page():
            self.current_page += 1
            self.update_right_page()
            if not self.has_next_page():
                # check read all new pages
                if self.showing_notification:
                    self.showing_notification = False
                    self.show_left_home_page()

        self.logger.debug(f'Now in page{self.current_page}')

    def previous_page(self) -> None:
        """move to previous page if there is previous page
        """        
        self.logger.debug('Going to previous page')
        if self.has_previous_page():
            self.current_page -= 1
            self.update_right_page()
        self.logger.debug(f'Now in page{self.current_page}')

    def load_demo_pages(self) -> None:
        """load the demo pages
        """        
        self.add_left_home_page(demo_left_page_path)
        self.right_page_list = demo_right_pages_list
        self.show_home_page()

    def show_home_page(self) -> None:
        """show the first page of both left and right screen
        """        
        self.logger.debug('displaying home page')
        self.show_left_home_page()
        self.show_right_home_page()

    def show_notify_page(self):
        """show the notify page on the left screen
        """        
        self.left_page_list[NOTIFY_PAGE_NUM] = create_page_left_notify()
        self._show_notify_page()
        self.showing_notification = True



class Book(GeneralBook):
    def __init__(self, queue: Queue, demo: bool, social_media_scraper, fetch: bool):
        super().__init__()

        self.demo = demo
        self.queue = queue
        self.social_media_scraper = social_media_scraper
        self.logger = getLogger('Book')
        self.fetch = fetch

        self.set_display()
        self.set_gpio()
        self.check_user_option_thread = Thread(target=self.check_user_option, args=(self.queue,))

        # self.is_close = False    

        if self.demo:
            self.load_demo_pages()

    def set_display(self) -> None:
        """setup the eink displays using the 3rd party library
        """        
        self.left_display = AutoEPDDisplay(vcom=-1.45,
                                bus=0,
                                device=0,
                                rotate='CCW',
                                spi_hz=24000000,
                                reset_pin=spi0.RESET,
                                cs_pin=spi0.CS,
                                hrdy_pin=spi0.HRDY
                                )  # Left screen
    
        self.right_display = AutoEPDDisplay(vcom=-1.55,
                                            bus=1,
                                            device=0,
                                            rotate='CCW',
                                            spi_hz=24000000,
                                            reset_pin=spi1.RESET,
                                            cs_pin=spi1.CS,
                                            hrdy_pin=spi1.HRDY
                                            )  # Right screen

    def update_right_page(self) -> None:
        """display the current page on the eink screen
        """        
        self.display_image_8bpp(self.right_display, self.right_page_list[self.current_page])

    def clear_display(self, display):
        """display a blank page on the specified eink screen

        Args:
            display ([type]): a specified eink screen
        """        
        self.logger.info('Clearing display ....')
        display.clear()

    def display_image_8bpp(self, display, img_path: Path):
        """display the image from the img_path on the specified eink screen
           Note: it is mainly from the open-source code from github
        Args:
            display ([type]): a specified eink screen
            img_path (Path): a path to a image
        """        
        self.logger.info('Displaying "{}"...'.format(img_path))
        # todo hard code
        # clearing image to white
        display.frame_buf.paste(0xFF, box=(0, 0, display.width, display.height))

        img = Image.open(img_path)

        dims = (display.width, display.height)
        # self.logger.debug(f'dims: {dims} img: {img.size}')
        img.thumbnail(dims)
        paste_coords = [dims[i] - img.size[i] for i in (0, 1)]  # align image with bottom of display
        display.frame_buf.paste(img, paste_coords)

        display.draw_full(constants.DisplayModes.GC16)

    def partial_update(self, display, img_path: Path):
        """Partilly update the specified eink screen with a given image.
           However, acceptable size of image to this function has not yet been tested

        Args:
            display ([type]): a specified eink screen
            img_path (Path): a path of the image want to partially update on the specified position
        """        
        img = Image.open(img_path)
        display.frame_buf.paste(img, (0, 0))
        display.draw_partial(constants.DisplayModes.DU)

    def read_notification(self):
        """Play the pre-recorded sound using Raspberry Pi
        """        
        self.logger.info('<#######################################################>')
        self.logger.info('Playing notification sound')
        cmd = 'aplay /home/pi/mirror/src/book/notification_micky.wav'
        os.system(cmd)
        # process = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    def _show_notify_page(self):
        """show the notification page on the left screen
        """        
        self.display_image_8bpp(self.left_display, self.left_page_list[NOTIFY_PAGE_NUM])

    def show_right_home_page(self) -> None:
        """show the first page of the right screen
        """        
        try:
            self.display_image_8bpp(self.right_display, self.right_page_list[HOME_PAGE_NUM])
        except IndexError:
            self.logger.info('No page to show')
            self.clear_display(self.right_display)

    def show_left_home_page(self) -> None:
        """show the first page of the left screen
        """        
        # self.partial_update(self.left_display, self.left_page_list[HOME_PAGE_NUM])
        self.display_image_8bpp(self.left_display, self.left_page_list[HOME_PAGE_NUM])

    def __del__(self):
        self.logger.info('Cleaning up GPIO...')
        # GPIO.remove_event_detect(HALL_SWITCH_PIN)
        GPIO.cleanup()

    def set_gpio(self) -> None:
        GPIO.setup(YES_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(NO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        # GPIO.setup(HALL_SWITCH_PIN, GPIO.IN,
        #            pull_up_down=GPIO.PUD_DOWN)
        # GPIO.add_event_detect(HALL_SWITCH_PIN, GPIO.BOTH,
        #                       callback=self.hall_switch_callback)

    # def hall_switch_callback(self, channel):
    #     if GPIO.input(HALL_SWITCH_PIN):
    #         self.logger.debug("magnet detect")
    #         self.is_close = True
    #     else:
    #         self.logger.debug("magnet gone")
    #         self.is_close = False

    def add_check_user_option(self):
        #　duplicated
        if not self.check_user_option_thread.is_alive():
            self.check_user_option_thread.start()
        else:
            self.logger.debug('the thread is alive')
            
    def get_current_showing_status(self) -> bool:
        """return the current status of the book, either showing notification or normal left page

        Returns:
            bool: True if the book is showing notification
        """        
        self.logger.info(f'{self.showing_notification}')
        return self.showing_notification

    def check_user_option(self, queue: Queue) -> None:
        self.logger.debug('Checking user option')
        while True:
            if self.is_close:
                self.logger.debug('the book is close')
                # Do nothing when the book is close
                continue

            if GPIO.input(RIGHT_BUTTON):
                scrape = False
                start_time = monotonic()
                while GPIO.input(RIGHT_BUTTON) and not self.demo:
                    if monotonic() - start_time > 5:
                        # long press to update feeds
                        self.logger.info('Button long pressed')
                        if queue.empty():
                            queue.put(1)
                        scrape = True
                        break
                if not scrape and self.has_next_page():
                    self.logger.debug('Right button is pressed')
                    self.next_page()

                elif not scrape and not self.has_next_page():
                    self.logger.debug('Right button is pressed but no next page')

            # if not self.has_next_page() and not self.has_previous_page():
            #     return

            if GPIO.input(LEFT_BUTTON) and self.has_previous_page():
                self.logger.debug('Left button is pressed')
                self.previous_page()
                # return

            elif GPIO.input(LEFT_BUTTON) and not self.has_previous_page():
                self.logger.debug('Left button is pressed but no previous page')

            sleep(0.1)
            
    def check_update(self):
        """chcek any updates from followings and create pages for them
        """        
        updates = self.social_media_scraper.get_new_photos_from_followings()
        
        if len(updates) != 0:
            self.logger.info('There are some updates')
            # create pages for the updates
            pages = create_pages(updates, self.get_current_book_len())
            self.add_right_pages(pages)
            
            # display notification on left page
            self.show_notify_page()

    def get_current_book_len(self) -> int:
        """a helper function to get the length of the right screen page list 

        Returns:
            int: length of the right screen page list 
        """           
        return len(self.right_page_list)

            

class VirtualBookUpdate(QThread):
    """a helper class to handle virtual book updates
    """    
    add_left_home_page_signal = pyqtSignal(Path)
    show_page_signal = pyqtSignal(int)
    get_current_book_len_signal = pyqtSignal()
    get_current_showing_status_signal = pyqtSignal()
    add_right_pages_signal = pyqtSignal(list)
 

    def __init__(self, social_media_scraper, queue, fetch) -> None:
        super().__init__()
        self.social_media_scraper = social_media_scraper
        self.exiting = False
        self.queue = queue
        self.logger = getLogger('vBookUpdate')
        self.fetch = fetch
    
    def __del__(self):
        self.exiting = True
        self.wait()

    def get_current_book_len(self) -> int:
        """a helper function to get the length of the right screen page list 

        Returns:
            int: length of the right screen page list 
        """        
        self.get_current_book_len_signal.emit()
        return self.queue.get()
    
    def get_current_showing_status(self) -> bool:
        """return the current status of the book, either showing notification or normal left page

        Returns:
            bool: True if the book is showing notification
        """           
        self.get_current_showing_status_signal.emit()
        return self.queue.get()

    def check_update(self) -> None:
        """chcek any updates from followings and create pages for them
        """        
        updates = self.social_media_scraper.get_new_photos_from_followings()

        if len(updates) != 0:
            self.logger.info('There are some updates')
            pages = content.create_pages(updates, self.get_current_book_len())
            self.add_right_pages_signal.emit(pages)
            self.show_page_signal.emit(SHOW_NOTIFY_PAGE_SIGNAL)  # display notification on left page
    

    def run(self) -> None:
        """main function to run the virtual book backend update
        """        
        try:
            # init content of the virtual book
            news_client = content.NewsClient()
            # content.init_left_page_data(news)
            self.add_left_home_page_signal.emit(content.create_page_left_home(news_client))
            self.add_right_pages_signal.emit(content.load_existing_pages())
            self.show_page_signal.emit(SHOW_HOME_PAGE_SIGNAL)

            start_time = time()
            fetch_time = time()
            first = True

            while True and not self.exiting:
                if self.fetch and (time() - fetch_time > 60*60 or first):
                    # fetch from media from instagram
                    self.social_media_scraper.scrape()
        
                    fetch_time = time()
                    first = False

                if time() - start_time > 60:
                    # Update time
                    content.left_page_data_time_update()
                    if self.get_current_showing_status():                     
                        self.logger.info(f'{self.get_current_showing_status()=}')
                        self.show_page_signal.emit(SHOW_NOTIFY_PAGE_SIGNAL)
                    
                    else:
                        self.add_left_home_page_signal.emit(content.create_page_left_home(news_client))
                        self.show_page_signal.emit(SHOW_LEFT_HOME_SIGNAL)
                    start_time = time()

                # update right page content if have updates
                self.check_update()
                sleep(30)
                
        except Exception as e:
            self.logger.error(e)


class VirtualBook(QMainWindow, GeneralBook):
    def __init__(self, demo, social_media_scraper, fetch) -> None:
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.logger = getLogger('vBook')
        self.queue = Queue(maxsize=1)
        self.fetch = fetch

        self.ui.left_page.setScaledContents(True)
        self.ui.right_page.setScaledContents(True)
        
        self.ui.next_page_button.clicked.connect(self.next_page)
        self.ui.previous_page_button.clicked.connect(self.previous_page)
        self.ui.start_button.clicked.connect(self.start_update)
        
        if demo:
            # load the demo page only and will not perform any updates
            self.load_demo_pages()
            self.hide_start_button()
        else:
            # start the backend update class
            self.vbook_update = VirtualBookUpdate(social_media_scraper, self.queue, self.fetch)
            self.vbook_update.add_left_home_page_signal.connect(self.add_left_home_page)
            self.vbook_update.show_page_signal.connect(self.show_page)
            self.vbook_update.get_current_book_len_signal.connect(self.get_current_book_len)
            self.vbook_update.add_right_pages_signal.connect(self.add_right_pages)
            self.vbook_update.get_current_showing_status_signal.connect(self.get_current_showing_status)
            self.vbook_update.start()

    def get_current_showing_status(self) -> None:
        self.logger.info(f'{self.showing_notification}')
        self.queue.put(self.showing_notification)     

    def get_current_book_len(self) -> None:
        self.queue.put(len(self.right_page_list))

    def start_update(self) -> None:
        # self.vbook_update.start()
        self.hide_start_button()

    def hide_start_button(self) -> None:
        self.ui.start_button.hide()

    def show_page(self, signal: int) -> None:
        if signal == SHOW_HOME_PAGE_SIGNAL:
            self.show_home_page()
        elif signal == SHOW_LEFT_HOME_SIGNAL:
            self.show_left_home_page()
        elif signal == SHOW_RIGHT_HOME_SIGNAL:
            self.show_right_home_page()
        elif signal == SHOW_NOTIFY_PAGE_SIGNAL:
            self.show_notify_page()
        else:
            raise ValueError('Unknown signal number')
        
    def _show_notify_page(self) -> None:
        self.set_left_page(self.left_page_list[NOTIFY_PAGE_NUM])
    
    def show_left_home_page(self) -> None:
        self.set_left_page(self.left_page_list[HOME_PAGE_NUM])

    def show_right_home_page(self) -> None:
        if len(self.right_page_list) != 0:
            self.set_right_page(self.right_page_list[HOME_PAGE_NUM])

    def set_left_page(self, page_path: Path) -> None:
        self.ui.left_page.setPixmap(QPixmap(str(page_path)))

    def set_right_page(self, page_path: Path) -> None:
        self.ui.right_page.setPixmap(QPixmap(str(page_path)))

    def update_left_page(self) -> None:
        self.set_left_page(self.left_page_list[HOME_PAGE_NUM])

    def update_right_page(self) -> None:
        self.set_right_page(self.right_page_list[self.current_page])
