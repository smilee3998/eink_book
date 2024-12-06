from collections import namedtuple
from pathlib import Path
from typing import NamedTuple

from PIL import ImageFont

cwd = Path().resolve()
saved_pages_path = cwd / 'media/pages'
save_left_home_path = saved_pages_path / 'left_page_home.jpg'
save_left_notify_path = saved_pages_path / 'left_page_notify.jpg'
saved_right_pages_path = saved_pages_path / 'right_pages'
saved_news_image_path = cwd / 'media/news'

if not saved_pages_path.exists():
    saved_pages_path.mkdir()

if not saved_right_pages_path.exists():
    saved_right_pages_path.mkdir()

if not saved_news_image_path.exists():
    saved_news_image_path.mkdir()
    
log_file_path = cwd / 'debug.log'

demo_pages_path = cwd / 'media/demo'
demo_left_page_path = demo_pages_path / 'left_home.jpg'
demo_right_page_1_path = demo_pages_path / 'demo_right_page1.jpg'
demo_right_page_2_path = demo_pages_path / 'demo_right_page2.jpg'
demo_right_page_3_path = demo_pages_path / 'demo_right_page3.jpg'
demo_right_pages_list = [demo_right_page_1_path, demo_right_page_2_path, demo_right_page_3_path]

Photo = namedtuple('Photo', ['path', 'date', 'time'])
Following = NamedTuple('Folloing', [('name', str), ('relationship', str)])
Update = NamedTuple('Update', [('following', Following), ('path', Path)])
News = NamedTuple('News', [('title', str), ('url', str)])

spi_pins = namedtuple('spi_pins', 'CS HRDY RESET')
spi0 = spi_pins(RESET=23, CS=8, HRDY=24)
spi1 = spi_pins(RESET=6, CS=18, HRDY=5)

HOME_PAGE_NUM = 0
NOTIFY_PAGE_NUM = 1
HALL_SWITCH_PIN = 26
YES_PIN = 14
NO_PIN = 15
RIGHT_BUTTON = YES_PIN
LEFT_BUTTON = NO_PIN

SHOW_HOME_PAGE_SIGNAL = 0
SHOW_LEFT_HOME_SIGNAL = 1
SHOW_RIGHT_HOME_SIGNAL = 2
SHOW_NOTIFY_PAGE_SIGNAL = 3

DAY_IN_SECONDS = 86400  # 60s*60min*24hour

EINK_SCREEN_SIZE = (1404, 1872)

NEW_PHOTO_ROBOT_MSG = 'New Photo! Press ‘Right’ button to update.'

API_KEY = '<YOUR_API_KEY>'

LEFT_HOME_BASE_IMAGE = 'media/templates/left_page_base.jpg'
BIG_TIME_RECT = (80,100,448,277)
BIG_TIME_START_CORNER = (80, 100)
FILL_WHITE = (255,255,255)
BIG_TIME_FONT = ImageFont.truetype("arial.ttf", 200)

DATE_RECT = (80, 313, 821, 391)
DATE_START_CORNER = (80,350)
DATE_FONT = ImageFont.truetype("arial.ttf", 60)

ACTIVITY_1_RECT = (208, 470, 990, 540)
ACTIVITY_1_CORNER = (208, 470)
ACTIVITY_2_RECT = (208, 584, 671, 651)
ACTIVITY_2_CORNER = (208, 584)
ACTIVITY_FONT = ImageFont.truetype("arial.ttf", 50)

REMINDER_RECT = (139, 842, 782, 933)
REMINDER_CORNER = (139, 842)
REMINDER_FONT = ACTIVITY_FONT

NEWS_1_IMAGE_RECT = (84, 1208, 624, 1511)
NEWS_1_IMAGE_CORNER = (84, 1208)
NEWS_1_TEXT_RECT = (103, 1535, 593, 1784)
NEWS_2_IMAGE_RECT = (728, 1208, 1262, 1511)
NEWS_2_IMAGE_CORNER = (728, 1208)
NEWS_2_TEXT_RECT = (738, 1534, 1241, 1784)
NEWS_FONT = ImageFont.truetype("arial.ttf", 40)
NEWS_IMAGE_SIZE = (534, 303)