# -*- coding: utf-8 -*-

from core import httptools, scrapertools
from platformcode import logger
from lib import jsunpack


def get_video_url(page_url, url_referer=''):
    logger.info("url=" + page_url)
    video_urls = []

    data = httptools.downloadpage(page_url).data
    # ~ logger.debug(data)

    if 'File Not Found' in data or 'File is no longer available' in data:
        return 'El archivo ha sido eliminado o no existe'

    keys = ['op',  'id',  'fname', 'hash']
    post = {'usr_login': '', 'referer': '', 'imhuman': 'Proceed to video'}

    for k in keys:
        post[k] = scrapertools.find_single_match(data, 'input type="hidden" name="%s" value="([^"]+)"' % k)

    new_data = httptools.downloadpage(page_url.replace('.html', ''), post=post, headers={'referer': page_url}).data

    video_info = scrapertools.find_multiple_matches(new_data, r'{(file:.*?)}')
    subtitulo = scrapertools.find_single_match(new_data, r'tracks:\s*\[{file:"([^"]+)"')

    for info in video_info:
        video_url = scrapertools.find_single_match(info, r'file:"([^"]+)"')
        label = scrapertools.find_single_match(info, r'label:"([^"]+)"')

        if video_url == subtitulo:
            continue

        extension = scrapertools.get_filename_from_url(video_url)[-4:]

        video_urls.append([extension, url])

    return video_urls
