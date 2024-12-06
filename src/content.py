# Handle the content of eink
import json
import random
import urllib.request
from datetime import datetime
from logging import getLogger
from pathlib import Path
from time import time
from typing import Dict, List, Optional, Tuple

import requests
from html2image import Html2Image
from jinja2 import Environment, FileSystemLoader
from newsapi import NewsApiClient
from PIL import Image, ImageDraw

from constants import *

logger = getLogger(__name__)
file_loader = FileSystemLoader('media/templates')
env = Environment(loader=file_loader)

reminder_robot_msg = 'Hello! Have you taken your medicine?'
left_page_data = {}  # TODO move left page data to class attribute

class NewsClient(NewsApiClient):
    def __init__(self) -> None:
        super().__init__(api_key=API_KEY)
        self.top_headlines = self.fetch_top_headlines_title()
        self.remove_invalid_news()
        logger.debug(f'{len(top_headlines["articles"])}')

    def remove_invalid_news(self):
        """Some news urls doesn't contain .jpg .jpeg or None, which cannot fetch the image 
        """
        clean_top_headlines = []
        for headline in self.top_headlines:
            url = headline.url
            if isinstance(url, str):
                filename = Path(url).name
                if 'jpg' in filename or 'jpeg' in filename:
                    clean_top_headlines.append(headline)
        self.top_headlines = clean_top_headlines
    
    def remove_invalid_news_by_title(self, title):
        for headline in self.top_headlines:
            if headline.title == title:
                self.top_headlines.remove(headline)
                
                
    def get_random_headlines(self, num:int =2) -> List[News]:
        """get random headlines from the top_headlines fetched

        Args:
            num (int, optional): number of headlines wants to get. Defaults to 2.

        Returns:
            List[News]: a list of of headlines with length of specified num
        """        
        try:
            return random.sample(self.top_headlines, num)
        except ValueError as e:
            logger.error(e)
            

    def fetch_top_headlines_title(self) -> List[News]:
        top_headlines = self.get_top_headlines(category='general',
                                            language='en',  # zh
                                            country='us')  # hk
        return [News(top_headline['title'], top_headline['urlToImage']) for top_headline in top_headlines['articles']]
                                        

def clear_existing_page() -> None:
    """Delete all files in the folder that contain all right pages
    """    
    for path in saved_right_pages_path.iterdir():
        path.unlink()


def get_profile_photo_from_path(following_path: Path) -> Optional[Path]:
    """This is a helper function to get the profile photo from a given path

    Args:
        following_path (Path): a path of a folder that contain the photos from Instagram

    Returns:
        Optional[Path]: the path of the profile photo, which can be None if there is no profile photo
    """    
    profile_path = following_path / 'profile_photo.jpg'
    if profile_path.exists():
        return profile_path
    else:
        for path in following_path.glob('*.jpg'):
            if is_profile_photo(path):
                return path.rename(profile_path)
        else:
            # if no profile photo
            return None
                

def is_profile_photo(image_path: Path) -> bool:
    """Check is the image path is a profile photo

    Args:
        image_path (Path): Any possible path to a profile photo

    Returns:
        bool: Empty string means a profile photo, otherwise normal photo path
    """    
    return len(load_shortcode_from_path(image_path)) == 0
        

def load_shortcode_from_path(image_path: Path) -> str:
    """Photos downloaded using the instagram scraper will have a shortcode at the end of the filename

    Args:
        image_path (Path): Any possible path to a profile photo

    Returns:
        str: the string after _, can be ''
    """    
    return image_path.stem.split(sep="_", maxsplit=1)[1]


def load_caption(image_path: Path) -> str:
    """load caption from the json file of the owner of the image

    Args:
        image_path (Path): For getting the parent path and shortcode of the image

    Raises:
        e: a error that raise if the image path don't have [-2] position

    Returns:
        str: caption of that image
    """    
    try:
        shortcode = load_shortcode_from_path(image_path)
        json_path = image_path.parent / f'{image_path.parts[-2]}.json'
    except IndexError as e:
        logger.error('index error', e)
        raise e

    return load_caption_from_json(json_path, shortcode) 


def load_caption_from_json(json_path: Path, shortcode: str) -> str:
    """load specific caption from the given json_path and shortcode 

    Args:
        json_path (Path): path of the json file
        shortcode (str): shortcode for identifying which caption should be loaded 

    Returns:
        str: [description]
    """    
    with json_path.open(encoding='utf-8') as file:
        data = json.load(file)
        for graph in data['GraphImages']:
            if graph['shortcode'] == shortcode:
                return graph['edge_media_to_caption']['edges'][0]['node']['text'].replace('\n', '')
        else:
            logger.error('no match')


def load_existing_pages() -> List[Path]:
    """load existing pages that are within 24hour

    Returns:
        List[Path]: a list of the updated path of the pages images within 24 hours 
    """    
    pages = list_file_within_24_hour()
    update_pages_name(pages)
    return pages


def update_pages_name(files_list: List[Path]) -> None:
    """update the name of the pages by their order

    Args:
        files_list (List[Path]): a list of updated paths
    """    
    for key, file_path in enumerate(files_list):
        files_list[key] = file_path.rename(saved_right_pages_path / f'right_page_{key+1}.jpg')


def list_file_within_24_hour() -> List[Path]:
    """get the list of pages file within 24 hour

    Returns:
        List[Path]: a list of paths that is sorted and within 24 hour
    """   
    # todo fix the problem that modify date can repeatedly renew after changing name 
    pages = get_all_saved_right_pages()
    for page in pages:
        if not is_create_within_24_hour(page):
            page.unlink(missing_ok=True) 
            pages.remove(page)

    return sort_with_last_modify_time(pages)


def sort_with_last_modify_time(files_list: List[Path]) -> List[Path]:
    """sort the list of files by increasing last modification time

    Args:
        files_list (List[Path]): unsorted list of the pages paths

    Returns:
        List[Path]: sorted list of the pages paths
    """    
    return sorted(files_list, key=lambda file: file.stat().st_mtime)


def is_create_within_24_hour(file_path: Path) -> bool:
    """Check is the image created within 24 hour

    Args:
        file_path (Path): a path of the page image

    Returns:
        bool: True if the last modification time is within 24 hour
    """    
    return time() - file_path.stat().st_mtime < DAY_IN_SECONDS


def get_all_saved_right_pages() -> List[Path]:
    """Check any image in the folder that save the right pages

    Returns:
        List[Path]: a list of images of saved right pages
    """    
    return [p for p in saved_right_pages_path.glob('*.jpg')]


def get_updated_datetime() -> Dict:
    """get current time and date

    Returns:
        Dict: a dict containing the current time and date
    """    
    return {
        'time_str': datetime.now().strftime('%H:%M'),
        'date_str': datetime.now().strftime('%A %d %B %Y')
    }


def create_page_left_notify() -> Path:
    """create a page for the left screen for notifying there are updates

    Returns:
        Path: a jpg path of this page
    """
    return create_jpg_left_notify()    

def create_page_left_home(news_client) -> Path:
    """create a page for the left screen with the given news

    Args:
        news: a newsclient

    Returns:
        Path: a jpg path of this page
    """
    return create_jpg_left_home(news_client)    

def create_html_left_notify() -> str:
    """create a html raw string for the left screen with the updated robot's message(notify) and time

    Returns:
        str: a html raw string 
    """    
    left_page_data_notify_update()
    return env.get_template("home_L_base_chi.html").render(**left_page_data)


def create_html_left_home(news: List[News]) -> str:
    """create a html raw string for the left screen with random news and updated time and robot's message

    Args:
        news (List[News]): a list of News (2)

    Returns:
        str: a html raw string
    """    
    init_left_page_data(news)
    return env.get_template("home_L_base_chi.html").render(**left_page_data)


def init_left_page_data(news_client) -> None:
    """Initialize the global variable of the left page, e.g. News, robot's message, time

    Args:
        news: a news client

    Raises:
        ValueError: no news is feteched from the API, need to check the account
    """    
    if news_client is None:
        logger.error('news are not provided')
        raise ValueError

    left_page_data_time_update()
    left_page_data_news_update(news_client)
    left_page_data_msg_update()
    logger.debug(f'left_page_data: {left_page_data}')


def left_page_data_msg_update() -> None:
    """Unfinished function, which intended to generate some messages for the elderly for companion
    """    
    left_page_data.update({'robot_msg': reminder_robot_msg})


def left_page_data_notify_update() -> None:
    """Update the robot's message to notify there are updates
    """    
    left_page_data.update({'robot_msg': NEW_PHOTO_ROBOT_MSG})
    logger.debug(left_page_data)


def left_page_data_time_update() -> None:
    """Update the global dict with the current time
    """    
    left_page_data.update(get_updated_datetime())

def retrieve_image_from_news(url: str) -> Path:
    filename = Path(url).name
    if 'jpg' in filename:
        sub_str = '.jpg'
    elif 'jpeg' in filename:
        sub_str = '.jpeg'
    else:
        logger.error('invalid filename')
        
    new_filename = filename[:filename.index(sub_str) + len(sub_str)]
    saved_path = saved_news_image_path / new_filename
    
    if saved_path.exists():
        # downloaded before
        return saved_path
    try:
        urllib.request.urlretrieve(url, saved_path)
        
    except Exception as e:
        logger.error(e)
        return None
    
    return saved_path
        
def left_page_data_news_update(news_client: NewsClient) -> None:
    """Given the list of the news, update the global dict with the news title and photos 

    Args:
        news (List[News]): [description]
    """
    valid_news = []
    valid_news_photo_path = []
    while len(valid_news) != 2:
        news = news_client.get_random_headlines(num=1)
        # loop until we have 2 valid news
        news_photo_path = retrieve_image_from_news(news[0].url)
        if news_photo_path is not None:
            if len(valid_news) == 1:
                if news[0].title != valid_news[0].title:
                    # check repeat news
                    valid_news.append(news[0])
                    valid_news_photo_path.append(news_photo_path)
                    
                elif len(news_client.top_headlines) == 1:
                    # has one valid headline only and the loop 
                    break
            else:
                # the valid news list is empty 
                valid_news.append(news[0])
                valid_news_photo_path.append(news_photo_path)
        
        else:
            # remove from the headlines
            news_client.remove_invalid_news_by_title(title=news[0].title)
            
            if len(news_client.top_headlines) == 0:
                # no valid headline
                break
            
    if len(valid_news_photo_path) == 2:
        temp = {'news1_content': valid_news[0].title,
                    'news1_photo_url': valid_news_photo_path[0],
                    'news2_content': valid_news[1].title,
                    'news2_photo_url': valid_news_photo_path[1],      
            }
    elif len(valid_news_photo_path) == 1:
         temp = {'news1_content': valid_news[0].title,
                    'news1_photo_url': valid_news_photo_path[0],
                    'news2_content': None,
                    'news2_photo_url': None,      
            }
    else:
        temp = {'news1_content': None,
                    'news1_photo_url': None,
                    'news2_content': None,
                    'news2_photo_url': None,      
            }
        logger.debug('no valid news')
    left_page_data.update(temp)

def create_pages(updates: List[Update], exist_num_pages: int) -> List[Path]:
    """create a number of pages with the updates for the right screen

    Args:
        updates (List[Update]): a list of updates that contain the essential information to create a page
        exist_num_pages (int): the current length of the right pages

    Returns:
        List[Path]: a list of path that contain the new created pages
    """    
    num_update = len(updates)
    new_pages = []
    new_page_count = 0

    for i in range(0, num_update, 2):
        file_name = f'right_page_{exist_num_pages + new_page_count + 1}.jpg'
        if i + 1 != num_update:
            # check if there is more then one update remain
            page_jpg_path = html_to_jpg(create_html_two_updates(updates[i], updates[i+1]), file_name, saved_right_pages_path)

        else:
            # if only one update left
            page_jpg_path = html_to_jpg(create_html_one_update(updates[i]), file_name, saved_right_pages_path)

        new_pages.append(page_jpg_path)
        new_page_count += 1
    return new_pages


def create_html_two_updates(update_1: Update, update_2: Update) -> str:
    """create a html raw string with two updates on the same page

    Args:
        update_1 (Update): first update 
        update_2 (Update): second update

    Returns:
        str: a html raw string
    """    
    data = {
        'relationship_1': update_1.following.relationship,
        'image_1_path': update_1.path.as_uri(),
        'caption_1': load_caption(image_path=update_1.path),
        'profile_1': get_profile_photo_from_path(update_1.path.parents[0]), 
        'relationship_2': update_2.following.relationship,
        'image_2_path': update_2.path.as_uri(),
        'caption_2': load_caption(image_path=update_2.path),
        'profile_2': get_profile_photo_from_path(update_2.path.parents[0]), 
    }
    rendered = env.get_template("home_R_base_2.html").render(**data)
    return rendered


def create_html_one_update(update: Update) -> str:
    """create a html raw string with only one update on the same page

    Args:
        update (Update): the single update left

    Returns:
        str: a html raw string
    """    
    data = {
        'relationship_1': update.following.relationship,
        'image_1_path': update.path.as_uri(),
        'caption_1': update.path,
        'profile_1': get_profile_photo_from_path(update.path.parents[0]), 
    }
    # logger.debug(data)
    rendered = env.get_template("home_R_base_1.html").render(**data)
    return rendered


def html_to_jpg(html_str: str, file_name: str, output_path: Path) -> Path:
    """Convert a html raw string to a jpg 

    Args:
        html_str (str): html raw string of the page 
        file_name (str): file name of the jpg iamge
        output_path (Path): output path of the jpg file

    Returns:
        Path: a path to a jpg file
    """    
    if not output_path.exists():
        output_path.mkdir()

    file_path = output_path / file_name
    logger.debug(f'Making file_path:{file_path}')
    temp = Html2Image(output_path=str(output_path))
    temp.screenshot(html_str=html_str, size=EINK_SCREEN_SIZE, save_as=file_name)
    return file_path


def jpg_to_bmp(jpg_path: Path) -> Path:
    # duplicated
    if not jpg_path.exists():
        logger.debug(jpg_path)
        raise FileNotFoundError('No such jpg')
    logger.debug('Converting to bmp file')
    # mode L: 8-bit pixels bw
    img = Image.open(jpg_path)
    img_bmp_path = jpg_path.with_suffix('.bmp')
    img_bmp = img.convert('L')
    img_bmp.save(img_bmp_path)
    return img_bmp_path

def get_text_size(font: ImageFont.truetype, text):
    return font.getsize(text)

def write_text_box(draw: ImageDraw, x,y, text, box_width, font: ImageFont.truetype, color=(0,0,0)):
    lines = []
    line = []
    words = text.split()
    
    for word in words:
        new_line = ' '.join(line + [word])
        size = get_text_size(font, new_line)
        text_height = size[1]
        if size[0] <= box_width:
            line.append(word)
        else:
            lines.append(line)
            line = [word]
    if line:
        lines.append(line)
    lines = [' '.join(line) for line in lines if line]
    
    height = y
    for line in lines:
        draw.text((x,height), line, align='left', fill=color, font=font)
        height += text_height
        
def get_news_image(image_path) -> Image:
    # TODO handle exception if no this file
    return Image.open(image_path).resize(NEWS_IMAGE_SIZE)

def add_info_left_home(image):
    draw = ImageDraw.Draw(image)
    draw.text(BIG_TIME_START_CORNER, left_page_data['time_str'], align='left', fill='black', font=BIG_TIME_FONT)
    draw.text(DATE_START_CORNER, left_page_data['date_str'], align='left', fill='black', font=DATE_FONT)
    draw.text(ACTIVITY_1_CORNER, '14:00 Elderly center singing activity', align='left', fill='black', font=ACTIVITY_FONT)
    draw.text(ACTIVITY_2_CORNER, '15:30 Take pills', align='left', fill='black', font=ACTIVITY_FONT)
    draw.text(REMINDER_CORNER, left_page_data['robot_msg'], align='center', fill='black', font=REMINDER_FONT)
    if left_page_data['news1_photo_url'] is not None:
        image.paste(get_news_image(left_page_data['news1_photo_url']), NEWS_1_IMAGE_CORNER)
        write_text_box(draw, x=105, y=1544, text=left_page_data['news1_content'], box_width=478, font=NEWS_FONT)
        
    if left_page_data['news2_photo_url'] is not None:
        image.paste(get_news_image(left_page_data['news2_photo_url']), NEWS_2_IMAGE_CORNER)
        write_text_box(draw, x=747, y=1544,  text=left_page_data['news2_content'], box_width=478, font=NEWS_FONT)
    
def create_jpg_left_home(news_client) -> Path:
    init_left_page_data(news_client)
    base_image = Image.open(LEFT_HOME_BASE_IMAGE)
    add_info_left_home(base_image)
    base_image.save(save_left_home_path)  

    return save_left_home_path

def create_jpg_left_notify() -> Path:
    base_image = Image.open(LEFT_HOME_BASE_IMAGE)
    add_info_left_home(base_image)
    base_image.save(save_left_home_path)  

    return save_left_home_path
    
